#!/usr/bin/env python3
"""Small Chrome DevTools Protocol client for webmind-claudecode tasks."""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import math
import os
import platform
import plistlib
import re
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_DEBUG_ADDRESS = "127.0.0.1"
LOCAL_CDP_HOSTS = {"127.0.0.1", "localhost", "::1"}
CURSOR_WORLD = "webmind-cdp-cursor-v1"
MAX_WEBSOCKET_MESSAGE_BYTES = 64 * 1024 * 1024
MAX_STDIN_CHARS = 1_000_000
MEM_NAME_RE = re.compile(r"^(?P<prefix>[a-z]{1,8})-(?P<number>[1-9][0-9]{0,2})-mem$")
PROFILE_METADATA_FILE = "webmind-profile.json"
LOCATION_SCHEMA_VERSION = 1
PROFILE_SCHEMA_VERSION = 2
CDP_SKILL_ROOT = Path(__file__).resolve().parents[1]
MEM_SKILL_ROOT = CDP_SKILL_ROOT.parent / "webmind-mem"
LOCATION_FILE = Path(os.environ.get("WEBMIND_MEM_LOCATION_FILE", str(MEM_SKILL_ROOT / "mem-location.json"))).expanduser()


def _read_json_object(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected: {path}")
    return data


def _parse_mem_name(name: str) -> Dict[str, Any]:
    match = MEM_NAME_RE.fullmatch(name)
    if not match:
        raise ValueError(
            "selected Mem folder name is invalid; expected xxx-yyy-mem with 1-8 lowercase letters and yyy in 1-999"
        )
    number = int(match.group("number"))
    return {
        "debug_port": 9000 + number,
        "profile_name": f"{name}-Profile",
    }


def load_browser_configuration() -> Dict[str, Any]:
    if not LOCATION_FILE.is_file():
        raise RuntimeError(
            "webmind is not initialized: no selected Mem location is stored. Complete the initialization flow first."
        )
    location = _read_json_object(LOCATION_FILE)
    if location.get("schema_version") != LOCATION_SCHEMA_VERSION:
        raise RuntimeError("stored Mem location schema is invalid; re-enter initialization")
    raw_mem_path = location.get("mem_path")
    if not isinstance(raw_mem_path, str) or not raw_mem_path.strip():
        raise RuntimeError("stored Mem location is invalid; re-enter initialization")
    mem_path = Path(raw_mem_path).expanduser().resolve()
    info = _parse_mem_name(mem_path.name)
    if location.get("mem_name") != mem_path.name:
        raise RuntimeError("stored Mem name/path mismatch; re-enter initialization")
    profile_dir = (mem_path / info["profile_name"]).resolve()
    metadata_path = profile_dir / PROFILE_METADATA_FILE
    if not profile_dir.is_dir() or profile_dir.is_symlink():
        raise RuntimeError(f"selected browser profile folder is missing or invalid: {profile_dir}")
    if not metadata_path.is_file():
        raise RuntimeError(f"browser profile metadata is missing: {metadata_path}; re-enter initialization")
    metadata = _read_json_object(metadata_path)
    expected_endpoint = f"http://127.0.0.1:{info['debug_port']}"
    expected = {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "mem_name": mem_path.name,
        "profile_name": info["profile_name"],
        "profile_path": str(profile_dir),
        "debug_address": "127.0.0.1",
        "debug_port": info["debug_port"],
        "endpoint": expected_endpoint,
    }
    mismatches = [key for key, value in expected.items() if metadata.get(key) != value]
    if mismatches:
        raise RuntimeError(
            f"browser profile metadata is inconsistent with the selected Mem folder ({', '.join(mismatches)}): {metadata_path}. "
            "Re-enter initialization before launching the browser."
        )
    return {
        **expected,
        "mem_path": str(mem_path),
        "profile_metadata": str(metadata_path),
        "location_file": str(LOCATION_FILE),
    }


def apply_browser_configuration(args: argparse.Namespace) -> Dict[str, Any]:
    config = load_browser_configuration()
    requested_endpoint = getattr(args, "endpoint", None)
    if requested_endpoint and requested_endpoint.rstrip("/") != config["endpoint"]:
        raise RuntimeError(
            f"--endpoint does not match the initialized browser profile ({config['endpoint']}). "
            "To change ports, select or create a different xxx-yyy-mem folder through initialization."
        )
    requested_profile = getattr(args, "user_data_dir", None)
    if requested_profile and not same_path(Path(requested_profile).expanduser().resolve(), Path(config["profile_path"])):
        raise RuntimeError(
            f"--user-data-dir does not match the initialized browser profile: {config['profile_path']}. "
            "To switch profiles, re-enter initialization."
        )
    args.endpoint = config["endpoint"]
    args.user_data_dir = config["profile_path"]
    args.port = config["debug_port"]
    args.browser_config = config
    return config



def configure_utf8_stdio() -> None:
    """Make CLI text I/O independent of the host console code page."""
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name)
        reconfigure = getattr(stream, "reconfigure", None)
        if not callable(reconfigure):
            continue
        try:
            reconfigure(encoding="utf-8", errors="strict")
        except (OSError, ValueError):
            pass


def json_print(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def fail(message: str, json_mode: bool = False, **extra: Any) -> None:
    if json_mode:
        payload = {"ok": False, "error": message}
        payload.update(extra)
        json_print(payload)
    else:
        print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def argument_or_stdin(value: Optional[str], use_stdin: bool, label: str) -> str:
    if not use_stdin:
        if value is None:
            raise ValueError(f"{label} is required")
        return value
    if sys.stdin.isatty():
        raise ValueError(f"{label} stdin mode requires piped input")
    text = sys.stdin.read(MAX_STDIN_CHARS + 1)
    if len(text) > MAX_STDIN_CHARS:
        raise ValueError(f"{label} stdin exceeds the 1,000,000 character safety limit")
    return text


def endpoint_url(endpoint: str, path: str) -> str:
    return endpoint.rstrip("/") + path


def http_json(url: str, timeout: float = 5.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "webmind_cdp/1.0"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:  # noqa: S310 - local/user-provided CDP endpoint
        return json.loads(response.read().decode("utf-8"))


def endpoint_parts(endpoint: str) -> tuple[str, int]:
    if not endpoint:
        raise RuntimeError("CDP endpoint is unavailable until webmind initialization is complete")
    parsed = urllib.parse.urlparse(endpoint)
    host = parsed.hostname or DEFAULT_DEBUG_ADDRESS
    if parsed.port is None:
        raise ValueError(f"CDP endpoint must include an explicit port: {endpoint}")
    return host, parsed.port


def is_local_endpoint(endpoint: str) -> bool:
    host, _ = endpoint_parts(endpoint)
    return host.lower() in LOCAL_CDP_HOSTS


def default_profile_dir() -> Path:
    return Path(load_browser_configuration()["profile_path"]).resolve()


def same_path(left: Path, right: Path) -> bool:
    """Compare existing paths by identity and otherwise by platform semantics."""
    try:
        if left.exists() and right.exists():
            return os.path.samefile(left, right)
    except OSError:
        pass
    left_text = os.path.normpath(os.path.realpath(str(left)))
    right_text = os.path.normpath(os.path.realpath(str(right)))
    return left_text == right_text


def resolve_profile_dir(raw_path: Optional[str]) -> Path:
    stored = default_profile_dir()
    if raw_path:
        requested = Path(raw_path).expanduser().resolve()
        if not same_path(requested, stored):
            raise RuntimeError(f"requested profile does not match initialized profile: {stored}")
    return stored


def macos_chrome_executable(raw_path: str) -> str:
    """Resolve either an app bundle or its real executable for LaunchServices."""
    path = Path(raw_path).expanduser().resolve()
    if path.suffix.lower() == ".app" and path.is_dir():
        try:
            with (path / "Contents" / "Info.plist").open("rb") as stream:
                metadata = plistlib.load(stream)
                executable = metadata.get("CFBundleExecutable") if isinstance(metadata, dict) else None
        except (OSError, ValueError, plistlib.InvalidFileException) as exc:
            raise RuntimeError(f"Cannot read Chrome app bundle: {path}") from exc
        if not isinstance(executable, str) or not executable or Path(executable).name != executable:
            raise RuntimeError(f"Invalid CFBundleExecutable in app bundle: {path}")
        path = path / "Contents" / "MacOS" / executable
    bundle = path.parent.parent.parent
    if (bundle.suffix.lower() != ".app" or path.parent.name != "MacOS"
            or path.parent.parent.name != "Contents" or not bundle.is_dir()
            or not path.is_file() or not os.access(path, os.X_OK)):
        raise RuntimeError(
            "macOS CDP requires an executable inside a Chrome/Chromium/Edge .app bundle. "
            "Set --chrome-path or WEBMIND_CDP_CHROME to the .app or its Contents/MacOS executable."
        )
    return str(path)


def find_macos_chrome_executable(explicit_path: Optional[str] = None) -> str:
    """Find a supported browser app bundle on macOS."""
    requested = explicit_path or os.environ.get("WEBMIND_CDP_CHROME")
    if requested:
        return macos_chrome_executable(requested)
    app_names = (
        "Google Chrome", "Google Chrome Beta", "Google Chrome Canary",
        "Microsoft Edge", "Chromium",
    )
    candidates = [
        str(root / f"{name}.app" / "Contents" / "MacOS" / name)
        for root in (Path("/Applications"), Path.home() / "Applications")
        for name in app_names
    ]
    for command in ("google-chrome", "google-chrome-stable", "chromium", "chrome", "msedge"):
        found = shutil.which(command)
        if found:
            candidates.append(found)
    for candidate in candidates:
        try:
            return macos_chrome_executable(candidate)
        except RuntimeError:
            continue
    raise RuntimeError("Chrome app bundle not found. Set --chrome-path or WEBMIND_CDP_CHROME.")


def launch_macos_chrome(command: List[str], profile_dir: Path,
                        timeout: float, has_url: bool) -> Dict[str, Any]:
    """Use the supplied script's open -na strategy, not a child Chrome process.

    Endpoint polling and profile verification belong to ensure_endpoint. A zero
    exit from open only means LaunchServices accepted the launch request.
    """
    if not math.isfinite(timeout) or timeout <= 0:
        raise ValueError("macOS launch timeout must be a positive finite number")
    chrome = macos_chrome_executable(command[0])
    bundle = Path(chrome).parent.parent.parent
    helper = Path(__file__).resolve().with_name("launch_chrome_macos.sh")
    if not helper.is_file():
        raise RuntimeError(f"Missing macOS launch helper: {helper}. Reinstall the complete package.")
    flags = list(command[1:-1] if has_url else command[1:])
    for flag in ("--enable-automation", "--noerrdialogs", "--disable-crash-reporter"):
        if flag not in flags:
            flags.append(flag)
    flags.append(command[-1] if has_url else "about:blank")
    # An exclusive, per-launch 0600 file avoids overwriting or following a log
    # symlink. Do not print the log body: open may include a supplied URL in it.
    descriptor, log_name = tempfile.mkstemp(
        prefix="cdp-launch-", suffix=".log", dir=str(profile_dir.parent)
    )
    hint = (
        f"LaunchServices log: {log_name}. Check the local GUI session and app bundle. "
        "If the host denies this operation, request approval for the specific CDP "
        "launch command; do not disable the sandbox or macOS privacy protections."
    )
    try:
        with os.fdopen(descriptor, "wb") as log:
            result = subprocess.run(
                ["/bin/bash", str(helper), str(bundle), *flags],
                stdin=subprocess.DEVNULL, stdout=log, stderr=subprocess.STDOUT,
                close_fds=True, start_new_session=True,
                timeout=min(timeout, 15.0), check=False,
            )
    except subprocess.TimeoutExpired:
        raise RuntimeError(f"macOS open launch request timed out. {hint}") from None
    except OSError:
        raise RuntimeError(f"macOS open launch request could not run. {hint}") from None
    if result.returncode != 0:
        raise RuntimeError(f"macOS open launch failed (exit {result.returncode}). {hint}")
    reported_flags = flags[:-1] + ["<redacted-url>"] if has_url else flags
    return {
        "pid": None,  # open's PID is not the browser PID; do not misreport it.
        "chrome": chrome,
        "chrome_app": str(bundle),
        "launcher": "macos-open",
        "launch_log": log_name,
        "command": ["/usr/bin/open", "-na", str(bundle), "--args", *reported_flags],
    }


def find_chrome_executable(explicit_path: Optional[str] = None) -> str:
    return find_macos_chrome_executable(explicit_path)


def launch_chrome(args: argparse.Namespace) -> Dict[str, Any]:
    apply_browser_configuration(args)
    endpoint = args.endpoint
    endpoint_host, endpoint_port = endpoint_parts(endpoint)
    if not is_local_endpoint(endpoint):
        raise RuntimeError(f"refusing to auto-launch Chrome for non-local endpoint: {endpoint}")

    debug_address = getattr(args, "debug_address", None) or DEFAULT_DEBUG_ADDRESS
    port = endpoint_port
    profile_dir = resolve_profile_dir(getattr(args, "user_data_dir", None))
    profile_dir.mkdir(parents=True, exist_ok=True)
    chrome = find_chrome_executable(getattr(args, "chrome_path", None))
    url = getattr(args, "url", None)

    command = [
        chrome,
        f"--remote-debugging-address={debug_address}",
        f"--remote-debugging-port={port}",
        f"--user-data-dir={profile_dir}",
        "--no-first-run",
        "--no-default-browser-check",
        "--proxy-bypass-list=<-loopback>;localhost;127.0.0.1;::1",
    ]
    command.append("--enable-automation")
    if getattr(args, "new_window", False):
        command.append("--new-window")
    if url:
        command.append(url)

    if debug_address.lower() not in LOCAL_CDP_HOSTS:
        raise RuntimeError("CDP debug address must be loopback-only")
    if not 1 <= port <= 65535:
        raise ValueError("CDP port must be in 1..65535")
    launch_info = launch_macos_chrome(
        command, profile_dir, getattr(args, "launch_timeout", 60.0), bool(url)
    )
    return {
        **launch_info,
        "endpoint": f"http://{endpoint_host}:{port}",
        "debug_address": debug_address,
        "debug_port": port,
        "user_data_dir": str(profile_dir),
    }



def wait_for_endpoint(endpoint: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        try:
            http_json(endpoint_url(endpoint, "/json/version"), timeout=min(1.0, remaining))
            return True
        except Exception:
            time.sleep(min(0.25, max(0.0, deadline - time.monotonic())))





def profile_from_browser_arguments(arguments: List[str]) -> Path:
    """Require an explicit, unambiguous absolute user-data directory."""
    if not isinstance(arguments, list) or not all(isinstance(arg, str) for arg in arguments):
        raise ValueError("browser did not report a valid argument list")
    profiles = []
    prefixes = ("--", "-")
    index = 1  # argv[0] is the executable, not a switch.
    while index < len(arguments):
        argument = arguments[index]
        if argument == "--":
            break
        for prefix in prefixes:
            switch, separator, value = argument.partition("=")
            if switch == prefix + "user-data-dir":
                # Chromium switches use '='; a separate following argument is
                # not the value of this switch.
                if not separator:
                    raise ValueError("browser reported --user-data-dir without a value")
                profiles.append(value)
                break
        index += 1
    if len(profiles) != 1 or not profiles[0]:
        raise ValueError("browser must report exactly one explicit --user-data-dir")
    profile = Path(profiles[0])
    if not profile.is_absolute():
        # The browser's working directory may differ from this CLI's directory.
        raise ValueError("browser reported a relative --user-data-dir; cannot establish its actual path")
    return profile.resolve()


def verify_endpoint_profile(args: argparse.Namespace, version: Dict[str, Any]) -> str:
    """Read identity from the browser endpoint; never infer it from an open port."""
    expected = resolve_profile_dir(getattr(args, "user_data_dir", None))
    client = None
    try:
        ws_url = version.get("webSocketDebuggerUrl")
        if not isinstance(ws_url, str) or not ws_url:
            raise ValueError("endpoint did not report a browser WebSocket URL")
        client = CDPClient(ws_url, timeout=getattr(args, "cdp_timeout", 10.0))
        try:
            # Available for browsers started with --enable-automation.
            arguments = client.call("Browser.getBrowserCommandLine")["arguments"]
        except (RuntimeError, KeyError):
            raise ValueError("browser must expose Browser.getBrowserCommandLine on POSIX")
            # Existing webmind-claudecode browsers do not need to be restarted with a new flag.
        actual = profile_from_browser_arguments(arguments)
    except Exception as exc:
        # Do not echo the full browser command line (it may contain private URLs).
        raise RuntimeError(
            f"cannot verify CDP profile at {args.endpoint}; expected {expected}. "
            "Refusing to reuse this endpoint because its explicit absolute "
            "--user-data-dir could not be established. Use a verifiable browser "
            "with the requested profile (on POSIX, start it with --enable-automation) "
            "or re-enter initialization with the intended Mem/profile."
        ) from exc
    finally:
        if client is not None:
            client.close()
    if not same_path(actual, expected):
        raise RuntimeError(
            f"CDP profile mismatch at {args.endpoint}: expected {expected}, actual {actual}. "
            "Refusing to reuse this browser. Re-enter initialization with the intended Mem/profile."
        )
    return str(actual)


def ensure_endpoint(args: argparse.Namespace, *, launch_if_missing: Optional[bool] = None) -> Dict[str, Any]:
    apply_browser_configuration(args)
    launch_info = None
    try:
        version = get_version(args.endpoint)
    except Exception:
        if not (getattr(args, "auto_launch", True) if launch_if_missing is None else launch_if_missing):
            raise
        launch_info = launch_chrome(args)
        timeout = getattr(args, "launch_timeout", 60.0)
        if not wait_for_endpoint(args.endpoint, timeout):
            detail = ""
            if launch_info.get("launcher") == "macos-open":
                detail = (
                    f"; LaunchServices accepted the request, but Chrome is not ready. "
                    f"LaunchServices log: {launch_info['launch_log']}. "
                    "Check host approval, profile locks, and port conflicts; "
                    "do not delete the profile or terminate another browser."
                )
            raise RuntimeError(f"launched Chrome but CDP endpoint was not ready after {timeout} seconds: {args.endpoint}{detail}")
        version = get_version(args.endpoint)
    # Keep verification outside the launch fallback: mismatch/unknown identity
    # must never cause a second launch, and a newly reachable port also needs proof.
    profile = verify_endpoint_profile(args, version)
    return {"launch": launch_info, "profile": profile}


def get_version(endpoint: str) -> Dict[str, Any]:
    return http_json(endpoint_url(endpoint, "/json/version"))


def get_tabs(endpoint: str) -> List[Dict[str, Any]]:
    tabs = http_json(endpoint_url(endpoint, "/json/list"))
    if not isinstance(tabs, list):
        raise RuntimeError("/json/list did not return a tab list")
    return tabs


def select_tab_from_tabs(args: argparse.Namespace, tabs: List[Dict[str, Any]]) -> Dict[str, Any]:
    page_tabs = [tab for tab in tabs if tab.get("type") == "page" and tab.get("webSocketDebuggerUrl")]
    candidates = page_tabs or [tab for tab in tabs if tab.get("webSocketDebuggerUrl")]

    target_id = getattr(args, "target_id", None)
    if not target_id:
        raise RuntimeError(
            "--target-id is required for commands that operate on an existing tab; "
            "run tabs --json first and use the exact target id"
        )
    for tab in candidates:
        if tab.get("id") == target_id:
            return tab
    raise RuntimeError(f"no CDP tab found with id: {target_id}")


def select_tab(args: argparse.Namespace) -> Dict[str, Any]:
    ensure_endpoint(args)
    return select_tab_from_tabs(args, get_tabs(args.endpoint))


class WebSocket:
    def __init__(self, url: str, timeout: float = 10.0) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"ws", "wss"}:
            raise ValueError(f"unsupported websocket scheme: {parsed.scheme}")
        self.url = url
        self.parsed = parsed
        self.timeout = timeout
        self._recv_buffer = bytearray()
        self._fragment_opcode: Optional[int] = None
        self._fragment_payload = bytearray()
        self._close_sent = False
        self._closed = False
        self.sock = self._connect()

    def _connect(self) -> socket.socket:
        host = self.parsed.hostname
        if not host:
            raise ValueError("websocket URL is missing host")
        port = self.parsed.port or (443 if self.parsed.scheme == "wss" else 80)
        raw = socket.create_connection((host, port), timeout=self.timeout)
        if self.parsed.scheme == "wss":
            raw = ssl.create_default_context().wrap_socket(raw, server_hostname=host)
        raw.settimeout(self.timeout)

        path = self.parsed.path or "/"
        if self.parsed.query:
            path += "?" + self.parsed.query
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        host_header = f"{host}:{port}"
        request = (
            f"GET {path} HTTP/1.1\r\n"
            f"Host: {host_header}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n"
            "\r\n"
        )
        raw.sendall(request.encode("ascii"))
        response = bytearray()
        while b"\r\n\r\n" not in response:
            chunk = raw.recv(4096)
            if not chunk:
                break
            response.extend(chunk)
            if len(response) > 65536:
                raw.close()
                raise RuntimeError("websocket handshake failed: response headers are too large")
        delimiter = response.find(b"\r\n\r\n")
        if delimiter < 0:
            raw.close()
            raise RuntimeError("websocket handshake failed: incomplete HTTP response")
        header_bytes = bytes(response[:delimiter])
        self._recv_buffer.extend(response[delimiter + 4:])
        header_text = header_bytes.decode("iso-8859-1", errors="replace")
        lines = header_text.split("\r\n")
        status_parts = lines[0].split(None, 2)
        if len(status_parts) < 2 or status_parts[1] != "101":
            raw.close()
            raise RuntimeError("websocket handshake failed: " + lines[0])
        headers: Dict[str, List[str]] = {}
        for line in lines[1:]:
            if ":" not in line:
                raw.close()
                raise RuntimeError("websocket handshake failed: malformed response header")
            name, value = line.split(":", 1)
            headers.setdefault(name.strip().lower(), []).append(value.strip())
        upgrade = ",".join(headers.get("upgrade", [])).lower()
        connection_tokens = {
            token.strip().lower()
            for value in headers.get("connection", [])
            for token in value.split(",")
        }
        if upgrade != "websocket" or "upgrade" not in connection_tokens:
            raw.close()
            raise RuntimeError("websocket handshake failed: missing Upgrade/Connection headers")
        expected = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
        accepts = headers.get("sec-websocket-accept", [])
        if len(accepts) != 1 or accepts[0] != expected:
            raw.close()
            raise RuntimeError("websocket handshake failed: invalid Sec-WebSocket-Accept")
        return raw

    def close(self) -> None:
        if not self._closed:
            try:
                self._send_frame(0x8, struct.pack("!H", 1000))
                self._close_sent = True
            except OSError:
                pass
        try:
            self.sock.close()
        except OSError:
            pass
        self._closed = True

    def _send_frame(self, opcode: int, payload: bytes = b"") -> None:
        if self._closed:
            raise RuntimeError("websocket is closed")
        header = bytearray([0x80 | opcode])
        length = len(payload)
        if length < 126:
            header.append(0x80 | length)
        elif length < 65536:
            header.append(0x80 | 126)
            header.extend(struct.pack("!H", length))
        else:
            header.append(0x80 | 127)
            header.extend(struct.pack("!Q", length))
        mask = os.urandom(4)
        masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
        self.sock.sendall(bytes(header) + mask + masked)

    def send_text(self, text: str) -> None:
        self._send_frame(0x1, text.encode("utf-8"))

    def _ensure_buffer(self, length: int) -> None:
        while len(self._recv_buffer) < length:
            chunk = self.sock.recv(max(4096, length - len(self._recv_buffer)))
            if not chunk:
                self._closed = True
                raise RuntimeError("websocket connection closed")
            self._recv_buffer.extend(chunk)

    def _recv_frame(self) -> tuple[bool, int, bytes]:
        """Receive one complete RFC 6455 frame without losing partial reads."""
        self._ensure_buffer(2)
        first, second = self._recv_buffer[0], self._recv_buffer[1]
        fin = bool(first & 0x80)
        if first & 0x70:
            raise RuntimeError("websocket protocol error: unexpected RSV bits")
        opcode = first & 0x0F
        if opcode not in {0x0, 0x1, 0x2, 0x8, 0x9, 0xA}:
            raise RuntimeError(f"websocket protocol error: unsupported opcode {opcode}")
        if second & 0x80:
            raise RuntimeError("websocket protocol error: server frames must not be masked")

        length = second & 0x7F
        header_length = 2
        if length == 126:
            self._ensure_buffer(4)
            length = struct.unpack("!H", self._recv_buffer[2:4])[0]
            header_length = 4
            if length < 126:
                raise RuntimeError("websocket protocol error: non-minimal payload length")
        elif length == 127:
            self._ensure_buffer(10)
            encoded_length = bytes(self._recv_buffer[2:10])
            if encoded_length[0] & 0x80:
                raise RuntimeError("websocket protocol error: invalid 64-bit payload length")
            length = struct.unpack("!Q", encoded_length)[0]
            header_length = 10
            if length < 65536:
                raise RuntimeError("websocket protocol error: non-minimal payload length")

        is_control = opcode >= 0x8
        if is_control and (not fin or length > 125):
            raise RuntimeError("websocket protocol error: invalid control frame")
        if length > MAX_WEBSOCKET_MESSAGE_BYTES:
            raise RuntimeError(
                f"websocket message exceeds {MAX_WEBSOCKET_MESSAGE_BYTES} byte safety limit"
            )

        frame_length = header_length + length
        self._ensure_buffer(frame_length)
        payload = bytes(self._recv_buffer[header_length:frame_length])
        del self._recv_buffer[:frame_length]
        return fin, opcode, payload

    @staticmethod
    def _decode_text(payload: bytes) -> str:
        try:
            return payload.decode("utf-8", errors="strict")
        except UnicodeDecodeError as exc:
            raise RuntimeError("websocket protocol error: invalid UTF-8 text message") from exc

    def recv_message(self, timeout: Optional[float] = None) -> Optional[Any]:
        """Receive one complete text or binary message, including fragments."""
        old_timeout = self.sock.gettimeout()
        deadline = time.monotonic() + timeout if timeout is not None else None
        try:
            while True:
                if deadline is not None:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0:
                        return None
                    self.sock.settimeout(remaining)
                try:
                    fin, opcode, payload = self._recv_frame()
                except socket.timeout:
                    return None

                if opcode == 0x8:
                    if len(payload) == 1:
                        raise RuntimeError("websocket protocol error: malformed close frame")
                    code = struct.unpack("!H", payload[:2])[0] if payload else None
                    if len(payload) > 2:
                        self._decode_text(payload[2:])
                    if not self._close_sent:
                        self._send_frame(0x8, payload)
                        self._close_sent = True
                    self._closed = True
                    suffix = f" (code {code})" if code is not None else ""
                    raise RuntimeError("websocket closed by remote" + suffix)
                if opcode == 0x9:
                    self._send_frame(0xA, payload)
                    continue
                if opcode == 0xA:
                    continue

                if opcode == 0x0:
                    if self._fragment_opcode is None:
                        raise RuntimeError("websocket protocol error: unexpected continuation frame")
                    if len(self._fragment_payload) + len(payload) > MAX_WEBSOCKET_MESSAGE_BYTES:
                        raise RuntimeError(
                            f"websocket message exceeds {MAX_WEBSOCKET_MESSAGE_BYTES} byte safety limit"
                        )
                    self._fragment_payload.extend(payload)
                    if not fin:
                        continue
                    message_opcode = self._fragment_opcode
                    complete = bytes(self._fragment_payload)
                    self._fragment_opcode = None
                    self._fragment_payload.clear()
                else:
                    if self._fragment_opcode is not None:
                        raise RuntimeError(
                            "websocket protocol error: new data frame before fragmented message completed"
                        )
                    if not fin:
                        self._fragment_opcode = opcode
                        self._fragment_payload.extend(payload)
                        continue
                    message_opcode = opcode
                    complete = payload

                if message_opcode == 0x1:
                    return self._decode_text(complete)
                return complete
        finally:
            self.sock.settimeout(old_timeout)

    def recv_text(self, timeout: Optional[float] = None) -> Optional[str]:
        message = self.recv_message(timeout=timeout)
        if message is None or isinstance(message, str):
            return message
        raise RuntimeError("websocket protocol error: unexpected binary message")


class CDPClient:
    def __init__(self, ws_url: str, timeout: float = 10.0) -> None:
        self.ws = WebSocket(ws_url, timeout=timeout)
        self.timeout = timeout
        self.next_id = 1
        self.events: List[Dict[str, Any]] = []

    def close(self) -> None:
        self.ws.close()

    def call(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: Optional[float] = None) -> Dict[str, Any]:
        msg_id = self.next_id
        self.next_id += 1
        payload = {"id": msg_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.ws.send_text(json.dumps(payload, ensure_ascii=False))
        deadline = time.time() + (timeout if timeout is not None else self.timeout)
        while True:
            remaining = max(0.05, deadline - time.time())
            if time.time() > deadline:
                raise TimeoutError(f"timeout waiting for CDP response to {method}")
            text = self.ws.recv_text(timeout=remaining)
            if text is None:
                continue
            message = json.loads(text)
            if message.get("id") == msg_id:
                if "error" in message:
                    raise RuntimeError(f"{method} failed: {message['error']}")
                return message.get("result", {})
            self.events.append(message)

    def drain_events(self, seconds: float = 0.5) -> List[Dict[str, Any]]:
        deadline = time.time() + seconds
        while time.time() < deadline:
            text = self.ws.recv_text(timeout=max(0.01, deadline - time.time()))
            if text is None:
                break
            self.events.append(json.loads(text))
        events = self.events[:]
        self.events.clear()
        return events


def runtime_evaluate(client: CDPClient, expression: str, timeout: Optional[float] = None,
                     context_id: Optional[int] = None) -> Any:
    params: Dict[str, Any] = {
        "expression": expression, "awaitPromise": True,
        "returnByValue": True, "userGesture": True,
    }
    if context_id is not None:
        params["contextId"] = context_id
    result = client.call(
        "Runtime.evaluate",
        params,
        timeout=timeout,
    )
    if "exceptionDetails" in result:
        details = result["exceptionDetails"]
        text = details.get("text") or details.get("exception", {}).get("description") or "JavaScript exception"
        raise RuntimeError(text)
    remote = result.get("result", {})
    if "value" in remote:
        return remote["value"]
    if "description" in remote:
        return remote["description"]
    return None


def js_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def cursor_context(client: CDPClient) -> int:
    frame_id = client.call("Page.getFrameTree")["frameTree"]["frame"]["id"]
    return client.call("Page.createIsolatedWorld", {
        "frameId": frame_id, "worldName": CURSOR_WORLD,
    })["executionContextId"]


def move_cdp_pointer(client: CDPClient, x: float, y: float) -> Dict[str, Any]:
    if not math.isfinite(x) or not math.isfinite(y):
        raise ValueError("pointer coordinates must be finite numbers")
    context = cursor_context(client)
    viewport = runtime_evaluate(client, "({width: innerWidth, height: innerHeight})", context_id=context)
    if not (0 <= x < viewport["width"] and 0 <= y < viewport["height"]):
        raise ValueError("pointer coordinates must be inside the page viewport (CSS pixels)")
    client.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
    pointer = {"x": x, "y": y, "source": "cdp", "coordinate_space": "viewport-css-pixels"}
    # This isolated world's state survives CLI reconnects, but not document
    # navigation, and cannot be confused with another tab's pointer.
    runtime_evaluate(client, f"globalThis.webmindPointer = {json.dumps(pointer)}", context_id=context)
    return pointer


def read_cdp_pointer(client: CDPClient, context: int) -> Dict[str, Any]:
    script = r"""
(() => {
  const point = globalThis.webmindPointer;
  if (!point) return {drawn:false, source:'cdp', reason:'unknown-position'};
  if (point.x < 0 || point.y < 0 || point.x >= innerWidth || point.y >= innerHeight)
    return {...point, drawn:false, reason:'outside-viewport'};
  return {...point, drawn:false, viewport:{width:innerWidth, height:innerHeight}};
})()
"""
    return runtime_evaluate(client, script, context_id=context)


def annotate_cdp_screenshot(png: bytes, cursor: Dict[str, Any]) -> tuple[bytes, Dict[str, Any]]:
    """Composite an explicitly labelled CDP marker; never mutate the page DOM."""
    if cursor.get("reason"):
        return png, cursor
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:
        raise RuntimeError("CDP cursor screenshots require Pillow: install -r requirements.txt, or use --no-cursor") from exc
    with Image.open(io.BytesIO(png)) as original:
        image = original.convert("RGBA")
    viewport = cursor["viewport"]
    scale_x = image.width / viewport["width"]
    scale_y = image.height / viewport["height"]
    if not math.isclose(scale_x, scale_y, rel_tol=0.01):
        return png, {**cursor, "drawn": False, "reason": "viewport-size-mismatch"}
    x, y = round(cursor["x"] * scale_x), round(cursor["y"] * scale_y)
    # Supersample the arrow so both fractional zoom and HiDPI output stay clear.
    sample = 4
    marker = Image.new("RGBA", (36 * sample, 48 * sample), (0, 0, 0, 0))
    draw = ImageDraw.Draw(marker)
    points = [(0, 0), (0, 23), (7, 17), (12, 28), (17, 26), (12, 15), (22, 15)]
    points = [(px * sample, py * sample) for px, py in points]
    draw.polygon(points, fill="#111827")
    draw.line(points + [points[0]], fill="white", width=2 * sample, joint="curve")
    draw.rounded_rectangle((0, 32 * sample, 30 * sample, 46 * sample), radius=3 * sample, fill="#2563eb")
    draw.text((15 * sample, 39 * sample), "CDP", fill="white", anchor="mm",
              font=ImageFont.load_default(size=10 * sample))
    marker = marker.resize((max(1, round(36 * scale_x)), max(1, round(48 * scale_y))), Image.Resampling.LANCZOS)
    # alpha_composite clips the marker at the screenshot's right/bottom edges.
    image.alpha_composite(marker, (x, y))
    output = io.BytesIO()
    image.save(output, format="PNG")
    return output.getvalue(), {**cursor, "drawn": True, "kind": "operation-marker",
                               "image_point": {"x": x, "y": y}}


def selector_center_script(selector: str, visible: bool = True) -> str:
    visibility_check = (
        "const style = getComputedStyle(el);"
        "const visible = rect.width > 0 && rect.height > 0 && style.visibility !== 'hidden' && style.display !== 'none';"
        "if (!visible) return {ok:false,error:'selector found but element is not visible'};"
        if visible
        else ""
    )
    return f"""
(() => {{
  const selector = {js_string(selector)};
  const el = document.querySelector(selector);
  if (!el) return {{ok:false,error:'selector not found',selector}};
  el.scrollIntoView({{block:'center', inline:'center'}});
  const rect = el.getBoundingClientRect();
  {visibility_check}
  return {{
    ok: true,
    selector,
    tag: el.tagName,
    text: (el.innerText || el.value || el.getAttribute('aria-label') || '').slice(0, 300),
    rect: {{x: rect.x, y: rect.y, width: rect.width, height: rect.height}},
    point: {{x: rect.left + rect.width / 2, y: rect.top + rect.height / 2}}
  }};
}})()
"""


def fill_script(selector: str, text: str) -> str:
    return f"""
(() => {{
  const selector = {js_string(selector)};
  const text = {js_string(text)};
  const el = document.querySelector(selector);
  if (!el) return {{ok:false,error:'selector not found',selector}};
  el.scrollIntoView({{block:'center', inline:'center'}});
  el.focus();
  if (el.isContentEditable) {{
    el.textContent = text;
    el.dispatchEvent(new InputEvent('input', {{bubbles:true, inputType:'insertText', data:text}}));
    return {{ok:true,mode:'contenteditable',selector,tag:el.tagName}};
  }}
  if ('value' in el) {{
    const proto = Object.getPrototypeOf(el);
    const descriptor = Object.getOwnPropertyDescriptor(proto, 'value');
    if (descriptor && descriptor.set) descriptor.set.call(el, text);
    else el.value = text;
    el.dispatchEvent(new Event('input', {{bubbles:true}}));
    el.dispatchEvent(new Event('change', {{bubbles:true}}));
    return {{ok:true,mode:'value',selector,tag:el.tagName}};
  }}
  return {{ok:false,error:'element is not fillable',selector,tag:el.tagName}};
}})()
"""


def key_info(key: str) -> Dict[str, Any]:
    aliases = {
        "enter": ("Enter", 13),
        "tab": ("Tab", 9),
        "escape": ("Escape", 27),
        "esc": ("Escape", 27),
        "backspace": ("Backspace", 8),
        "delete": ("Delete", 46),
        "arrowleft": ("ArrowLeft", 37),
        "arrowright": ("ArrowRight", 39),
        "arrowup": ("ArrowUp", 38),
        "arrowdown": ("ArrowDown", 40),
        "home": ("Home", 36),
        "end": ("End", 35),
        "pageup": ("PageUp", 33),
        "pagedown": ("PageDown", 34),
        "space": (" ", 32),
    }
    normalized = key.lower().replace(" ", "")
    if normalized in aliases:
        name, code = aliases[normalized]
        return {"key": name, "code": name if name != " " else "Space", "windowsVirtualKeyCode": code}
    if len(key) == 1:
        return {"key": key, "text": key, "code": "Key" + key.upper() if key.isalpha() else "", "windowsVirtualKeyCode": ord(key.upper())}
    return {"key": key, "code": key, "windowsVirtualKeyCode": 0}


def handle_js_dialogs(client: CDPClient, accept: bool = True, prompt_text: Optional[str] = None, timeout: float = 0.5) -> List[Dict[str, Any]]:
    handled: List[Dict[str, Any]] = []
    for event in client.drain_events(timeout):
        if event.get("method") == "Page.javascriptDialogOpening":
            params = event.get("params", {})
            call_params: Dict[str, Any] = {"accept": accept}
            if prompt_text is not None:
                call_params["promptText"] = prompt_text
            client.call("Page.handleJavaScriptDialog", call_params)
            handled.append(params)
    return handled


def maybe_accept_js_dialogs(client: CDPClient, args: argparse.Namespace) -> List[Dict[str, Any]]:
    if not getattr(args, "accept_js_dialogs", False):
        return []
    return handle_js_dialogs(client, accept=True, timeout=args.dialog_drain)

def connect_target(args: argparse.Namespace) -> tuple[CDPClient, Dict[str, Any]]:
    tab = select_tab(args)
    client = CDPClient(tab["webSocketDebuggerUrl"], timeout=args.cdp_timeout)
    client.call("Runtime.enable")
    client.call("Page.enable")
    return client, tab


def command_self_check(args: argparse.Namespace) -> Dict[str, Any]:
    config = apply_browser_configuration(args)
    payload: Dict[str, Any] = {
        "ok": True,
        "action": "self-check",
        "endpoint": args.endpoint,
        "debug_address": args.debug_address,
        "expected_profile": str(resolve_profile_dir(args.user_data_dir)),
        "profile": None,
        "profile_verified": False,
        "local_proxy_bypass": True,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "mem_path": config["mem_path"],
        "profile_metadata": config["profile_metadata"],
        "debug_port": config["debug_port"],
    }
    try:
        payload["version"] = get_version(args.endpoint)
        payload["profile"] = verify_endpoint_profile(args, payload["version"])
        payload["profile_verified"] = True
        tabs = get_tabs(args.endpoint)
        payload["tab_count"] = len(tabs)
        payload["page_count"] = len([tab for tab in tabs if tab.get("type") == "page"])
    except Exception as exc:  # noqa: BLE001
        payload["ok"] = False
        payload["error"] = str(exc)
    return payload


def command_launch(args: argparse.Namespace) -> Dict[str, Any]:
    apply_browser_configuration(args)
    if getattr(args, "url_stdin", False):
        args.url = argument_or_stdin(None, True, "URL").strip()

    endpoint_info = ensure_endpoint(args, launch_if_missing=True)
    launch_info = endpoint_info["launch"]

    tabs = get_tabs(args.endpoint)
    return {
        "ok": True,
        "action": "launch",
        "endpoint": args.endpoint,
        "already_running": launch_info is None,
        "launch": launch_info,
        "profile": endpoint_info["profile"],
        "profile_verified": True,
        "tab_count": len(tabs),
        "page_count": len([tab for tab in tabs if tab.get("type") == "page"]),
    }


def command_tabs(args: argparse.Namespace) -> Dict[str, Any]:
    endpoint_info = ensure_endpoint(args)
    tabs = get_tabs(args.endpoint)
    slim = [
        {
            "id": tab.get("id"),
            "type": tab.get("type"),
            "title": tab.get("title"),
            "url": tab.get("url"),
            "webSocketDebuggerUrl": bool(tab.get("webSocketDebuggerUrl")),
        }
        for tab in tabs
    ]
    return {
        "ok": True, "action": "tabs", "endpoint": args.endpoint,
        "auto_launch": endpoint_info["launch"], "profile": endpoint_info["profile"],
        "profile_verified": True, "tabs": slim,
    }


def command_new_tab(args: argparse.Namespace) -> Dict[str, Any]:
    if getattr(args, "url_stdin", False):
        url = argument_or_stdin(None, True, "URL").strip()
    else:
        url = (getattr(args, "url", None) or "about:blank").strip()
    if not url:
        raise ValueError("URL cannot be empty")

    endpoint_info = ensure_endpoint(args)
    version = get_version(args.endpoint)
    ws_url = version.get("webSocketDebuggerUrl")
    if not isinstance(ws_url, str) or not ws_url:
        raise RuntimeError("endpoint did not report a browser WebSocket URL")

    client = CDPClient(ws_url, timeout=args.cdp_timeout)
    try:
        result = client.call(
            "Target.createTarget",
            {"url": url, "background": bool(args.background)},
            timeout=args.cdp_timeout,
        )
        target_id = result.get("targetId")
        if not isinstance(target_id, str) or not target_id:
            raise RuntimeError("Target.createTarget did not return a targetId")
        return {
            "ok": True,
            "action": "new-tab",
            "endpoint": args.endpoint,
            "already_running": endpoint_info["launch"] is None,
            "launch": endpoint_info["launch"],
            "profile": endpoint_info["profile"],
            "profile_verified": True,
            "target_id": target_id,
            "url": "<provided via stdin>" if args.url_stdin else url,
            "background": bool(args.background),
        }
    finally:
        client.close()


def browser_websocket_url(args: argparse.Namespace, endpoint_info: Dict[str, Any]) -> str:
    version = endpoint_info.get("version")
    if not isinstance(version, dict):
        version = get_version(args.endpoint)
    ws_url = version.get("webSocketDebuggerUrl")
    if not isinstance(ws_url, str) or not ws_url:
        raise RuntimeError("CDP endpoint did not report a browser WebSocket URL")
    return ws_url


def command_switch_tab(args: argparse.Namespace) -> Dict[str, Any]:
    endpoint_info = ensure_endpoint(args)
    tabs = get_tabs(args.endpoint)
    tab = select_tab_from_tabs(args, tabs)
    target_id = tab.get("id")
    if not isinstance(target_id, str) or not target_id:
        raise RuntimeError("selected CDP tab did not report a target id")

    client = CDPClient(browser_websocket_url(args, endpoint_info), timeout=args.cdp_timeout)
    try:
        client.call("Target.activateTarget", {"targetId": target_id}, timeout=args.cdp_timeout)
        return {
            "ok": True,
            "action": "switch-tab",
            "endpoint": args.endpoint,
            "profile": endpoint_info["profile"],
            "profile_verified": True,
            "target": summarize_tab(tab),
            "activated": True,
        }
    finally:
        client.close()


def command_close_tab(args: argparse.Namespace) -> Dict[str, Any]:
    endpoint_info = ensure_endpoint(args)
    tabs = get_tabs(args.endpoint)
    tab = select_tab_from_tabs(args, tabs)
    target_id = tab.get("id")
    if not isinstance(target_id, str) or not target_id:
        raise RuntimeError("selected CDP tab did not report a target id")

    page_tabs = [tab for tab in tabs if tab.get("type") == "page" and tab.get("webSocketDebuggerUrl")]
    if tab.get("type") == "page" and len(page_tabs) <= 1:
        raise RuntimeError("refusing to close the last page tab because that could close the browser window")

    client = CDPClient(browser_websocket_url(args, endpoint_info), timeout=args.cdp_timeout)
    try:
        result = client.call("Target.closeTarget", {"targetId": target_id}, timeout=args.cdp_timeout)
        if result.get("success") is False:
            raise RuntimeError("Target.closeTarget reported that the tab was not closed")
        return {
            "ok": True,
            "action": "close-tab",
            "endpoint": args.endpoint,
            "profile": endpoint_info["profile"],
            "profile_verified": True,
            "target": summarize_tab(tab),
            "closed": True,
        }
    finally:
        client.close()


def command_eval(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        value = runtime_evaluate(client, args.expression, timeout=args.cdp_timeout)
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "eval", "target": summarize_tab(tab), "value": value, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_navigate(args: argparse.Namespace) -> Dict[str, Any]:
    url = argument_or_stdin(args.url, args.url_stdin, "URL").strip()
    if not url:
        raise ValueError("URL cannot be empty")
    client, tab = connect_target(args)
    try:
        result = client.call("Page.navigate", {"url": url})
        error_text = result.get("errorText")
        if error_text:
            return {
                "ok": False,
                "action": "navigate",
                "target": summarize_tab(tab),
                "url": "<provided via stdin>" if args.url_stdin else url,
                "result": result,
                "error": f"navigation failed: {error_text}",
                "load_event_seen": False,
                "handled_js_dialogs": [],
            }
        load_seen = False
        if args.wait_load:
            deadline = time.time() + args.timeout
            while time.time() < deadline:
                for event in client.drain_events(0.25):
                    if event.get("method") == "Page.loadEventFired":
                        load_seen = True
                        break
                if load_seen:
                    break
        handled = maybe_accept_js_dialogs(client, args)
        return {
            "ok": True,
            "action": "navigate",
            "target": summarize_tab(tab),
            "url": "<provided via stdin>" if args.url_stdin else url,
            "result": result,
            "load_event_seen": load_seen,
            "handled_js_dialogs": handled,
        }
    finally:
        client.close()


def command_wait_for_selector(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        deadline = time.time() + args.timeout
        last_value: Any = None
        while time.time() < deadline:
            last_value = runtime_evaluate(client, selector_center_script(args.selector, visible=args.visible), timeout=args.cdp_timeout)
            if isinstance(last_value, dict) and last_value.get("ok"):
                return {"ok": True, "action": "wait-for-selector", "target": summarize_tab(tab), "match": last_value}
            time.sleep(args.interval)
        return {
            "ok": False,
            "action": "wait-for-selector",
            "target": summarize_tab(tab),
            "selector": args.selector,
            "timeout": args.timeout,
            "last": last_value,
        }
    finally:
        client.close()


def command_move(args: argparse.Namespace) -> Dict[str, Any]:
    if args.selector is None and (args.x is None or args.y is None):
        raise ValueError("move requires --selector or both --x and --y")
    if args.selector is not None and (args.x is not None or args.y is not None):
        raise ValueError("use either --selector or --x/--y, not both")
    client, tab = connect_target(args)
    try:
        if args.selector is not None:
            info = runtime_evaluate(client, selector_center_script(args.selector), timeout=args.cdp_timeout)
            if not isinstance(info, dict) or not info.get("ok"):
                return {"ok": False, "action": "move", "target": summarize_tab(tab), "result": info}
            x, y = float(info["point"]["x"]), float(info["point"]["y"])
        else:
            x, y = args.x, args.y
        pointer = move_cdp_pointer(client, x, y)
        return {"ok": True, "action": "move", "target": summarize_tab(tab), "cursor": pointer}
    finally:
        client.close()


def command_click(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        info = runtime_evaluate(client, selector_center_script(args.selector, visible=True), timeout=args.cdp_timeout)
        if not isinstance(info, dict) or not info.get("ok"):
            return {"ok": False, "action": "click", "target": summarize_tab(tab), "result": info}
        point = info["point"]
        x = float(point["x"])
        y = float(point["y"])
        move_cdp_pointer(client, x, y)
        client.call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
        client.call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "click", "target": summarize_tab(tab), "element": info, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_fill(args: argparse.Namespace) -> Dict[str, Any]:
    text = argument_or_stdin(args.text, args.text_stdin, "text")
    client, tab = connect_target(args)
    try:
        result = runtime_evaluate(client, fill_script(args.selector, text), timeout=args.cdp_timeout)
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": bool(isinstance(result, dict) and result.get("ok")), "action": "fill", "target": summarize_tab(tab), "result": result, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_insert_text(args: argparse.Namespace) -> Dict[str, Any]:
    text = argument_or_stdin(args.text, args.text_stdin, "text")
    client, tab = connect_target(args)
    try:
        focus_result = runtime_evaluate(client, selector_center_script(args.selector, visible=True), timeout=args.cdp_timeout)
        if not isinstance(focus_result, dict) or not focus_result.get("ok"):
            return {"ok": False, "action": "insert-text", "target": summarize_tab(tab), "result": focus_result}
        runtime_evaluate(client, f"document.querySelector({js_string(args.selector)}).focus()", timeout=args.cdp_timeout)
        client.call("Input.insertText", {"text": text})
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "insert-text", "target": summarize_tab(tab), "element": focus_result, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_press(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        info = key_info(args.key)
        down = {"type": "rawKeyDown", **info}
        up = {"type": "keyUp", **{k: v for k, v in info.items() if k != "text"}}
        client.call("Input.dispatchKeyEvent", down)
        client.call("Input.dispatchKeyEvent", up)
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "press", "target": summarize_tab(tab), "key": args.key, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_screenshot(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    context = None
    cursor: Dict[str, Any] = {"drawn": False, "source": "cdp", "reason": "disabled"}
    warnings: List[str] = []
    try:
        if not getattr(args, "no_cursor", False):
            context = cursor_context(client)
            cursor = read_cdp_pointer(client, context)
        params = {"format": "png", "fromSurface": True}
        result = client.call("Page.captureScreenshot", params, timeout=args.cdp_timeout)
        data = result.get("data")
        if not data:
            raise RuntimeError("Page.captureScreenshot did not return image data")
        png = base64.b64decode(data)
        if context is not None:
            # Avoid drawing coordinates sampled from a different viewport/state
            # if another command or a resize occurred during capture.
            if read_cdp_pointer(client, context) != cursor:
                cursor = {"drawn": False, "source": "cdp", "reason": "pointer-or-viewport-changed"}
            png, cursor = annotate_cdp_screenshot(png, cursor)
            if not cursor.get("drawn"):
                warnings.append("CDP pointer not drawn: " + cursor.get("reason", "unavailable") +
                                ". Use move --selector or move --x/--y on this document, then capture again.")
        output = Path(args.output or "cdp_screenshot.png")
        if output.suffix.lower() != ".png":
            output = output.with_suffix(".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(png)
        return {"ok": True, "action": "screenshot", "target": summarize_tab(tab),
                "output": str(output.resolve()), "cursor": cursor, "warnings": warnings}
    finally:
        client.close()


def command_handle_js_dialog(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        deadline = time.time() + args.timeout
        handled: List[Dict[str, Any]] = []
        while time.time() < deadline:
            handled.extend(handle_js_dialogs(client, accept=args.accept, prompt_text=args.prompt_text, timeout=0.25))
            if handled:
                break
        return {"ok": bool(handled), "action": "handle-js-dialog", "target": summarize_tab(tab), "handled_js_dialogs": handled}
    finally:
        client.close()


def summarize_tab(tab: Dict[str, Any]) -> Dict[str, Any]:
    return {"id": tab.get("id"), "title": tab.get("title"), "url": tab.get("url"), "type": tab.get("type")}


def add_target_args(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--target-id",
        required=True,
        help="required exact CDP target id from the tabs command",
    )
    parser.add_argument("--cdp-timeout", type=float, default=10.0, help="CDP command timeout in seconds")
    parser.add_argument("--accept-js-dialogs", action="store_true", help="accept JavaScript dialogs observed after the command")
    parser.add_argument("--dialog-drain", type=float, default=0.5, help="seconds to look for JavaScript dialogs after a command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Operate Chrome tabs through the Chrome DevTools Protocol.")
    parser.add_argument("--endpoint", help="optional expected endpoint; must match the selected Mem profile metadata")
    parser.add_argument("--chrome-path", help="Chrome/Edge executable path (also accepts a .app bundle on macOS). Defaults to common system locations.")
    parser.add_argument(
        "--user-data-dir",
        help="optional expected profile path; must match the selected Mem profile metadata",
    )
    parser.add_argument("--debug-address", default=DEFAULT_DEBUG_ADDRESS, help="address Chrome binds for remote debugging")
    parser.add_argument("--launch-timeout", type=float, default=60.0, help="seconds to wait after launching Chrome (default: 60)")
    parser.add_argument("--no-auto-launch", dest="auto_launch", action="store_false", help="do not launch Chrome when the local CDP endpoint is down")
    parser.set_defaults(auto_launch=True)
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON where supported")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("self-check", help="check whether the CDP endpoint responds")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p.set_defaults(func=command_self_check)

    p = sub.add_parser("tabs", help="list CDP targets/tabs")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p.set_defaults(func=command_tabs)

    p = sub.add_parser("switch-tab", help="activate an existing tab and bring it to the front")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.set_defaults(func=command_switch_tab)

    p = sub.add_parser("close-tab", help="close an existing tab without closing the browser")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.set_defaults(func=command_close_tab)

    p = sub.add_parser("new-tab", help="create a new tab in the verified CDP browser")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    new_tab_url = p.add_mutually_exclusive_group()
    new_tab_url.add_argument("--url", help="optional non-sensitive URL; defaults to about:blank")
    new_tab_url.add_argument("--url-stdin", action="store_true", help="read the optional URL from stdin")
    p.add_argument("--background", action="store_true", help="create the tab without bringing it to the foreground")
    p.add_argument("--cdp-timeout", type=float, default=10.0, help="CDP command timeout in seconds")
    p.set_defaults(func=command_new_tab)

    p = sub.add_parser("launch", help="launch the initialized Mem-bound CDP Chrome profile if it is not already running")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    launch_url = p.add_mutually_exclusive_group()
    launch_url.add_argument("--url", help="optional non-sensitive URL to open after launch")
    launch_url.add_argument("--url-stdin", action="store_true", help="read the optional URL from stdin")
    p.add_argument("--new-window", action="store_true", help="open URL in a new Chrome window")
    p.set_defaults(func=command_launch)

    p = sub.add_parser("eval", help="evaluate JavaScript in a target tab")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--expression", required=True, help="JavaScript expression to evaluate")
    p.set_defaults(func=command_eval)

    p = sub.add_parser("navigate", help="navigate a target tab")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    navigate_url = p.add_mutually_exclusive_group(required=True)
    navigate_url.add_argument("--url", help="non-sensitive URL to navigate to")
    navigate_url.add_argument("--url-stdin", action="store_true", help="read the URL from stdin")
    p.add_argument("--wait-load", action="store_true", help="wait for Page.loadEventFired")
    p.add_argument("--timeout", type=float, default=15.0, help="load wait timeout in seconds")
    p.set_defaults(func=command_navigate)

    p = sub.add_parser("wait-for-selector", help="wait until a selector exists")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    p.add_argument("--visible", action="store_true", help="require nonzero visible layout box")
    p.add_argument("--timeout", type=float, default=10.0, help="wait timeout in seconds")
    p.add_argument("--interval", type=float, default=0.25, help="poll interval in seconds")
    p.set_defaults(func=command_wait_for_selector)

    p = sub.add_parser("move", help="move the CDP pointer without clicking (viewport CSS pixels)")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", help="move to the center of this CSS selector")
    p.add_argument("--x", type=float, help="viewport x coordinate in CSS pixels")
    p.add_argument("--y", type=float, help="viewport y coordinate in CSS pixels")
    p.set_defaults(func=command_move)

    p = sub.add_parser("click", help="click the center of a selector with CDP mouse events")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    p.set_defaults(func=command_click)

    p = sub.add_parser("fill", help="set a selector's text/value and dispatch input/change")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    fill_text = p.add_mutually_exclusive_group(required=True)
    fill_text.add_argument("--text", help="non-sensitive text to place in the element")
    fill_text.add_argument("--text-stdin", action="store_true", help="read text from stdin")
    p.set_defaults(func=command_fill)

    p = sub.add_parser("insert-text", help="focus a selector and insert text via CDP Input.insertText")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    insert_text = p.add_mutually_exclusive_group(required=True)
    insert_text.add_argument("--text", help="non-sensitive text to insert")
    insert_text.add_argument("--text-stdin", action="store_true", help="read text from stdin")
    p.set_defaults(func=command_insert_text)

    p = sub.add_parser("press", help="dispatch a key press to the focused page")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--key", required=True, help="key name such as Enter, Tab, Escape, ArrowDown, or a single character")
    p.set_defaults(func=command_press)

    p = sub.add_parser("screenshot", help="capture the page viewport through CDP")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--output", "-o", help="output PNG path")
    p.add_argument("--no-cursor", action="store_true", help="omit the CDP operation pointer marker")
    p.set_defaults(func=command_screenshot)

    p = sub.add_parser("handle-js-dialog", help="accept or dismiss a JavaScript dialog")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--accept", action="store_true", help="accept the JavaScript dialog")
    group.add_argument("--dismiss", action="store_true", help="dismiss the JavaScript dialog")
    p.add_argument("--prompt-text", help="text for prompt dialogs when accepting")
    p.add_argument("--timeout", type=float, default=3.0, help="dialog wait timeout in seconds")
    p.set_defaults(func=command_handle_js_dialog)

    return parser


def main() -> int:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "dismiss") and args.dismiss:
        args.accept = False
    try:
        if platform.system() != 'Darwin':
            raise RuntimeError('Browser control in this edition requires native macOS.')
        result = args.func(args)
    except urllib.error.URLError as exc:
        fail(f"cannot reach CDP endpoint {args.endpoint}: {exc}", getattr(args, "json", False))
    except Exception as exc:  # noqa: BLE001 - user-facing CLI should stay concise
        fail(str(exc), getattr(args, "json", False))

    if getattr(args, "json", False):
        json_print(result)
    else:
        print(f"{result.get('action', args.command)}: {'ok' if result.get('ok') else 'not ok'}")
        if result.get("error"):
            print(f"error: {result['error']}", file=sys.stderr)
        if "output" in result:
            print(f"output: {result['output']}")
        if "value" in result:
            print(result["value"])
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
