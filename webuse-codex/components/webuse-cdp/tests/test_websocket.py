"""RFC 6455 receive-path regression tests for the bundled WebSocket client."""

import base64
import hashlib
import socket
import struct
import unittest
from unittest.mock import patch

from test_profile_verification import cdp


def server_frame(opcode, payload=b"", *, fin=True, masked=False):
    first = (0x80 if fin else 0) | opcode
    length = len(payload)
    header = bytearray([first])
    mask_bit = 0x80 if masked else 0
    if length < 126:
        header.append(mask_bit | length)
    elif length < 65536:
        header.append(mask_bit | 126)
        header.extend(struct.pack("!H", length))
    else:
        header.append(mask_bit | 127)
        header.extend(struct.pack("!Q", length))
    if masked:
        mask = b"\x01\x02\x03\x04"
        header.extend(mask)
        payload = bytes(value ^ mask[index % 4] for index, value in enumerate(payload))
    return bytes(header) + payload


def decode_client_frame(data):
    first, second = data[0], data[1]
    length = second & 0x7F
    index = 2
    if length == 126:
        length = struct.unpack("!H", data[index:index + 2])[0]
        index += 2
    elif length == 127:
        length = struct.unpack("!Q", data[index:index + 8])[0]
        index += 8
    if not second & 0x80:
        raise AssertionError("client frame was not masked")
    mask = data[index:index + 4]
    index += 4
    payload = bytes(data[index + offset] ^ mask[offset % 4] for offset in range(length))
    return bool(first & 0x80), first & 0x0F, payload


class FakeHandshakeSocket:
    def __init__(self):
        self.timeout = 1.0
        self.pending = bytearray()
        self.recv_calls = 0
        self.closed = False

    def settimeout(self, timeout):
        self.timeout = timeout

    def gettimeout(self):
        return self.timeout

    def sendall(self, data):
        if not data.startswith(b"GET "):
            return
        request = data.decode("ascii")
        key = next(
            line.split(":", 1)[1].strip()
            for line in request.split("\r\n")
            if line.lower().startswith("sec-websocket-key:")
        )
        accept = base64.b64encode(
            hashlib.sha1((key + cdp.GUID).encode("ascii")).digest()
        ).decode("ascii")
        response = (
            "HTTP/1.1 101 Switching Protocols\r\n"
            "Upgrade: websocket\r\n"
            "Connection: keep-alive, Upgrade\r\n"
            f"Sec-WebSocket-Accept: {accept}\r\n\r\n"
        ).encode("ascii")
        self.pending.extend(response + server_frame(0x1, b"first message"))

    def recv(self, count):
        self.recv_calls += 1
        if not self.pending:
            raise socket.timeout()
        data = bytes(self.pending[:count])
        del self.pending[:count]
        return data

    def close(self):
        self.closed = True


class WebSocketReceiveTests(unittest.TestCase):
    def make_websocket(self):
        client, server = socket.socketpair()
        client.settimeout(0.2)
        server.settimeout(0.2)
        websocket = cdp.WebSocket.__new__(cdp.WebSocket)
        websocket.url = "ws://local.test/socket"
        websocket.parsed = None
        websocket.timeout = 0.2
        websocket._recv_buffer = bytearray()
        websocket._fragment_opcode = None
        websocket._fragment_payload = bytearray()
        websocket._close_sent = False
        websocket._closed = False
        websocket.sock = client
        self.addCleanup(server.close)
        self.addCleanup(client.close)
        return websocket, server

    def test_fragmented_text_with_interleaved_ping(self):
        websocket, server = self.make_websocket()
        server.sendall(
            server_frame(0x1, b"hello ", fin=False)
            + server_frame(0x9, b"check")
            + server_frame(0x0, "世界".encode("utf-8"), fin=True)
        )

        self.assertEqual(websocket.recv_text(timeout=0.2), "hello 世界")
        fin, opcode, payload = decode_client_frame(server.recv(1024))
        self.assertTrue(fin)
        self.assertEqual(opcode, 0xA)
        self.assertEqual(payload, b"check")

    def test_partial_frame_survives_timeout(self):
        websocket, server = self.make_websocket()
        frame = server_frame(0x1, b"partial message")
        server.sendall(frame[:5])

        self.assertIsNone(websocket.recv_text(timeout=0.01))
        self.assertEqual(bytes(websocket._recv_buffer), frame[:5])

        server.sendall(frame[5:])
        self.assertEqual(websocket.recv_text(timeout=0.2), "partial message")

    def test_extended_payload_length(self):
        websocket, server = self.make_websocket()
        message = "x" * 500
        server.sendall(server_frame(0x1, message.encode("utf-8")))
        self.assertEqual(websocket.recv_text(timeout=0.2), message)

    def test_binary_message_is_available_but_rejected_by_recv_text(self):
        websocket, server = self.make_websocket()
        server.sendall(server_frame(0x2, b"\x00\x01\xff"))
        self.assertEqual(websocket.recv_message(timeout=0.2), b"\x00\x01\xff")

        websocket, server = self.make_websocket()
        server.sendall(server_frame(0x2, b"binary"))
        with self.assertRaisesRegex(RuntimeError, "unexpected binary message"):
            websocket.recv_text(timeout=0.2)

    def test_masked_server_frame_is_rejected(self):
        websocket, server = self.make_websocket()
        server.sendall(server_frame(0x1, b"invalid", masked=True))
        with self.assertRaisesRegex(RuntimeError, "must not be masked"):
            websocket.recv_text(timeout=0.2)

    def test_invalid_utf8_is_rejected(self):
        websocket, server = self.make_websocket()
        server.sendall(server_frame(0x1, b"\xff"))
        with self.assertRaisesRegex(RuntimeError, "invalid UTF-8"):
            websocket.recv_text(timeout=0.2)

    def test_close_frame_is_acknowledged(self):
        websocket, server = self.make_websocket()
        close_payload = struct.pack("!H", 1000) + b"done"
        server.sendall(server_frame(0x8, close_payload))

        with self.assertRaisesRegex(RuntimeError, "code 1000"):
            websocket.recv_text(timeout=0.2)
        fin, opcode, payload = decode_client_frame(server.recv(1024))
        self.assertTrue(fin)
        self.assertEqual(opcode, 0x8)
        self.assertEqual(payload, close_payload)

    def test_handshake_preserves_first_frame_in_same_packet(self):
        fake_socket = FakeHandshakeSocket()
        with patch.object(cdp.socket, "create_connection", return_value=fake_socket):
            websocket = cdp.WebSocket("ws://local.test/socket")

        calls_after_handshake = fake_socket.recv_calls
        self.assertEqual(websocket.recv_text(timeout=0.2), "first message")
        self.assertEqual(fake_socket.recv_calls, calls_after_handshake)


if __name__ == "__main__":
    unittest.main()
