#!/usr/bin/env python3
"""WebMind: a Chrome DevTools Protocol client for coding-agent skills."""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import platform
import shutil
import socket
import ssl
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional


GUID = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11"
DEFAULT_DEBUG_ADDRESS = "127.0.0.1"
DEFAULT_DEBUG_PORT = 9222
DEFAULT_ENDPOINT = "http://127.0.0.1:9222"
DEFAULT_PROFILE_DIR = Path(__file__).resolve().parents[1] / "chrome-profile"
LOCAL_CDP_HOSTS = {"127.0.0.1", "localhost", "::1"}


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


def endpoint_url(endpoint: str, path: str) -> str:
    return endpoint.rstrip("/") + path


def http_json(url: str, timeout: float = 5.0) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": "WebMind/1.0"})
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(request, timeout=timeout) as response:  # noqa: S310 - local/user-provided CDP endpoint
        return json.loads(response.read().decode("utf-8"))


def endpoint_parts(endpoint: str) -> tuple[str, int]:
    parsed = urllib.parse.urlparse(endpoint)
    host = parsed.hostname or DEFAULT_DEBUG_ADDRESS
    port = parsed.port or DEFAULT_DEBUG_PORT
    return host, port


def is_local_endpoint(endpoint: str) -> bool:
    host, _ = endpoint_parts(endpoint)
    return host.lower() in LOCAL_CDP_HOSTS


def default_profile_dir() -> Path:
    return DEFAULT_PROFILE_DIR


def resolve_profile_dir(raw_path: Optional[str]) -> Path:
    if raw_path:
        return Path(raw_path).expanduser().resolve()
    return default_profile_dir().resolve()


def find_chrome_executable(explicit_path: Optional[str] = None) -> str:
    if explicit_path:
        path = Path(explicit_path).expanduser()
        if path.exists():
            return str(path)
        raise RuntimeError(f"Chrome executable not found: {explicit_path}")

    env_path = os.environ.get("WEBMIND_CHROME")
    if env_path:
        path = Path(env_path).expanduser()
        if path.exists():
            return str(path)
        raise RuntimeError(f"WEBMIND_CHROME does not exist: {env_path}")

    candidates: List[str] = []
    if platform.system() == "Windows":
        for key in ("PROGRAMFILES", "PROGRAMFILES(X86)", "LOCALAPPDATA"):
            root = os.environ.get(key)
            if root:
                candidates.append(str(Path(root) / "Google" / "Chrome" / "Application" / "chrome.exe"))
                candidates.append(str(Path(root) / "Microsoft" / "Edge" / "Application" / "msedge.exe"))
    elif platform.system() == "Darwin":
        candidates.extend(
            [
                "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
                "/Applications/Chromium.app/Contents/MacOS/Chromium",
            ]
        )

    for command in ("chrome", "chrome.exe", "google-chrome", "google-chrome-stable", "chromium", "chromium-browser", "msedge", "msedge.exe"):
        found = shutil.which(command)
        if found:
            return found

    for candidate in candidates:
        if Path(candidate).exists():
            return candidate

    raise RuntimeError("Chrome executable not found. Set --chrome-path or WEBMIND_CHROME.")


def launch_chrome(args: argparse.Namespace) -> Dict[str, Any]:
    endpoint = args.endpoint
    endpoint_host, endpoint_port = endpoint_parts(endpoint)
    if not is_local_endpoint(endpoint):
        raise RuntimeError(f"refusing to auto-launch Chrome for non-local endpoint: {endpoint}")

    debug_address = getattr(args, "debug_address", None) or DEFAULT_DEBUG_ADDRESS
    port = getattr(args, "port", None) or endpoint_port
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
    if getattr(args, "new_window", False):
        command.append("--new-window")
    if url:
        command.append(url)

    creationflags = 0
    if platform.system() == "Windows":
        creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.DETACHED_PROCESS  # type: ignore[attr-defined]

    process = subprocess.Popen(  # noqa: S603 - command is assembled from explicit executable and flags
        command,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
        close_fds=True,
        creationflags=creationflags,
    )
    return {
        "pid": process.pid,
        "chrome": chrome,
        "endpoint": f"http://{endpoint_host}:{port}",
        "debug_address": debug_address,
        "debug_port": port,
        "user_data_dir": str(profile_dir),
        "command": command,
    }


def wait_for_endpoint(endpoint: str, timeout: float) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            get_version(endpoint)
            return True
        except Exception:
            time.sleep(0.25)
    return False


def ensure_endpoint(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    try:
        get_version(args.endpoint)
        return None
    except Exception:
        if not getattr(args, "auto_launch", True):
            raise
        launch_info = launch_chrome(args)
        timeout = getattr(args, "launch_timeout", 10.0)
        if not wait_for_endpoint(args.endpoint, timeout):
            raise RuntimeError(f"launched Chrome but CDP endpoint was not ready after {timeout} seconds: {args.endpoint}")
        return launch_info


def get_version(endpoint: str) -> Dict[str, Any]:
    return http_json(endpoint_url(endpoint, "/json/version"))


def get_tabs(endpoint: str) -> List[Dict[str, Any]]:
    tabs = http_json(endpoint_url(endpoint, "/json/list"))
    if not isinstance(tabs, list):
        raise RuntimeError("/json/list did not return a tab list")
    return tabs


def select_tab(args: argparse.Namespace) -> Dict[str, Any]:
    ensure_endpoint(args)
    tabs = get_tabs(args.endpoint)
    page_tabs = [tab for tab in tabs if tab.get("type") == "page" and tab.get("webSocketDebuggerUrl")]
    candidates = page_tabs or [tab for tab in tabs if tab.get("webSocketDebuggerUrl")]

    if args.target_id:
        for tab in candidates:
            if tab.get("id") == args.target_id:
                return tab
        raise RuntimeError(f"no CDP tab found with id: {args.target_id}")

    if args.url_contains:
        needle = args.url_contains.lower()
        for tab in candidates:
            if needle in str(tab.get("url", "")).lower():
                return tab
        raise RuntimeError(f"no CDP tab URL contains: {args.url_contains}")

    if args.title_contains:
        needle = args.title_contains.lower()
        for tab in candidates:
            if needle in str(tab.get("title", "")).lower():
                return tab
        raise RuntimeError(f"no CDP tab title contains: {args.title_contains}")

    if not candidates:
        raise RuntimeError("no page targets with webSocketDebuggerUrl are available")
    return candidates[0]


def _read_exact(sock: socket.socket, length: int) -> bytes:
    chunks: List[bytes] = []
    remaining = length
    while remaining:
        chunk = sock.recv(remaining)
        if not chunk:
            raise RuntimeError("websocket connection closed")
        chunks.append(chunk)
        remaining -= len(chunk)
    return b"".join(chunks)


class WebSocket:
    def __init__(self, url: str, timeout: float = 10.0) -> None:
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"ws", "wss"}:
            raise ValueError(f"unsupported websocket scheme: {parsed.scheme}")
        self.url = url
        self.parsed = parsed
        self.timeout = timeout
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
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = raw.recv(4096)
            if not chunk:
                break
            response += chunk
        header_text = response.decode("iso-8859-1", errors="replace")
        if " 101 " not in header_text.split("\r\n", 1)[0]:
            raise RuntimeError("websocket handshake failed: " + header_text.split("\r\n", 1)[0])
        expected = base64.b64encode(hashlib.sha1((key + GUID).encode("ascii")).digest()).decode("ascii")
        if expected not in header_text:
            raise RuntimeError("websocket handshake failed: invalid Sec-WebSocket-Accept")
        return raw

    def close(self) -> None:
        try:
            self.sock.close()
        except OSError:
            pass

    def send_text(self, text: str) -> None:
        payload = text.encode("utf-8")
        header = bytearray([0x81])
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

    def recv_text(self, timeout: Optional[float] = None) -> Optional[str]:
        old_timeout = self.sock.gettimeout()
        if timeout is not None:
            self.sock.settimeout(timeout)
        try:
            while True:
                try:
                    first = _read_exact(self.sock, 2)
                except socket.timeout:
                    return None
                opcode = first[0] & 0x0F
                masked = bool(first[1] & 0x80)
                length = first[1] & 0x7F
                if length == 126:
                    length = struct.unpack("!H", _read_exact(self.sock, 2))[0]
                elif length == 127:
                    length = struct.unpack("!Q", _read_exact(self.sock, 8))[0]
                mask = _read_exact(self.sock, 4) if masked else b""
                payload = _read_exact(self.sock, length) if length else b""
                if masked:
                    payload = bytes(payload[i] ^ mask[i % 4] for i in range(length))
                if opcode == 8:
                    raise RuntimeError("websocket closed by remote")
                if opcode == 9:
                    self._send_pong(payload)
                    continue
                if opcode in {1, 2}:
                    return payload.decode("utf-8", errors="replace")
        finally:
            if timeout is not None:
                self.sock.settimeout(old_timeout)

    def _send_pong(self, payload: bytes) -> None:
        header = bytearray([0x8A])
        length = len(payload)
        if length > 125:
            payload = payload[:125]
            length = len(payload)
        header.append(0x80 | length)
        mask = os.urandom(4)
        masked = bytes(payload[i] ^ mask[i % 4] for i in range(length))
        self.sock.sendall(bytes(header) + mask + masked)


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


def runtime_evaluate(client: CDPClient, expression: str, timeout: Optional[float] = None) -> Any:
    result = client.call(
        "Runtime.evaluate",
        {
            "expression": expression,
            "awaitPromise": True,
            "returnByValue": True,
            "userGesture": True,
        },
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
    return {{ok:true,mode:'value',selector,tag:el.tagName,value:el.value}};
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
    payload: Dict[str, Any] = {
        "ok": True,
        "action": "self-check",
        "endpoint": args.endpoint,
        "debug_address": args.debug_address,
        "profile": str(resolve_profile_dir(args.user_data_dir)),
        "local_proxy_bypass": True,
        "python": sys.version.split()[0],
        "platform": platform.platform(),
    }
    try:
        payload["version"] = get_version(args.endpoint)
        tabs = get_tabs(args.endpoint)
        payload["tab_count"] = len(tabs)
        payload["page_count"] = len([tab for tab in tabs if tab.get("type") == "page"])
    except Exception as exc:  # noqa: BLE001
        payload["ok"] = False
        payload["error"] = str(exc)
    return payload


def command_launch(args: argparse.Namespace) -> Dict[str, Any]:
    if args.port:
        endpoint_host, _ = endpoint_parts(args.endpoint)
        args.endpoint = f"http://{endpoint_host}:{args.port}"

    already_running = False
    try:
        get_version(args.endpoint)
        already_running = True
        launch_info = None
    except Exception:
        launch_info = launch_chrome(args)
        timeout = getattr(args, "launch_timeout", 10.0)
        if not wait_for_endpoint(args.endpoint, timeout):
            raise RuntimeError(f"launched Chrome but CDP endpoint was not ready after {timeout} seconds: {args.endpoint}")

    tabs = get_tabs(args.endpoint)
    return {
        "ok": True,
        "action": "launch",
        "endpoint": args.endpoint,
        "already_running": already_running,
        "launch": launch_info,
        "profile": str(resolve_profile_dir(args.user_data_dir)),
        "tab_count": len(tabs),
        "page_count": len([tab for tab in tabs if tab.get("type") == "page"]),
    }


def command_tabs(args: argparse.Namespace) -> Dict[str, Any]:
    launch_info = ensure_endpoint(args)
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
    return {"ok": True, "action": "tabs", "endpoint": args.endpoint, "auto_launch": launch_info, "tabs": slim}


def command_eval(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        value = runtime_evaluate(client, args.expression, timeout=args.cdp_timeout)
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "eval", "target": summarize_tab(tab), "value": value, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_navigate(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        result = client.call("Page.navigate", {"url": args.url})
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
            "url": args.url,
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


def command_click(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        info = runtime_evaluate(client, selector_center_script(args.selector, visible=True), timeout=args.cdp_timeout)
        if not isinstance(info, dict) or not info.get("ok"):
            return {"ok": False, "action": "click", "target": summarize_tab(tab), "result": info}
        point = info["point"]
        x = float(point["x"])
        y = float(point["y"])
        client.call("Input.dispatchMouseEvent", {"type": "mouseMoved", "x": x, "y": y})
        client.call("Input.dispatchMouseEvent", {"type": "mousePressed", "x": x, "y": y, "button": "left", "clickCount": 1})
        client.call("Input.dispatchMouseEvent", {"type": "mouseReleased", "x": x, "y": y, "button": "left", "clickCount": 1})
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": True, "action": "click", "target": summarize_tab(tab), "element": info, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_fill(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        result = runtime_evaluate(client, fill_script(args.selector, args.text), timeout=args.cdp_timeout)
        handled = maybe_accept_js_dialogs(client, args)
        return {"ok": bool(isinstance(result, dict) and result.get("ok")), "action": "fill", "target": summarize_tab(tab), "result": result, "handled_js_dialogs": handled}
    finally:
        client.close()


def command_insert_text(args: argparse.Namespace) -> Dict[str, Any]:
    client, tab = connect_target(args)
    try:
        focus_result = runtime_evaluate(client, selector_center_script(args.selector, visible=True), timeout=args.cdp_timeout)
        if not isinstance(focus_result, dict) or not focus_result.get("ok"):
            return {"ok": False, "action": "insert-text", "target": summarize_tab(tab), "result": focus_result}
        runtime_evaluate(client, f"document.querySelector({js_string(args.selector)}).focus()", timeout=args.cdp_timeout)
        client.call("Input.insertText", {"text": args.text})
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
    try:
        params = {"format": "png", "fromSurface": True}
        result = client.call("Page.captureScreenshot", params, timeout=args.cdp_timeout)
        data = result.get("data")
        if not data:
            raise RuntimeError("Page.captureScreenshot did not return image data")
        output = Path(args.output or "cdp_screenshot.png")
        if output.suffix.lower() != ".png":
            output = output.with_suffix(".png")
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(base64.b64decode(data))
        return {"ok": True, "action": "screenshot", "target": summarize_tab(tab), "output": str(output.resolve())}
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
    parser.add_argument("--target-id", help="CDP target id from the tabs command")
    parser.add_argument("--url-contains", help="select first tab whose URL contains this text")
    parser.add_argument("--title-contains", help="select first tab whose title contains this text")
    parser.add_argument("--cdp-timeout", type=float, default=10.0, help="CDP command timeout in seconds")
    parser.add_argument("--accept-js-dialogs", action="store_true", help="accept JavaScript dialogs observed after the command")
    parser.add_argument("--dialog-drain", type=float, default=0.5, help="seconds to look for JavaScript dialogs after a command")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WebMind: operate Chrome tabs through the Chrome DevTools Protocol.")
    parser.add_argument("--endpoint", default=DEFAULT_ENDPOINT, help="Chrome debugging endpoint, e.g. http://127.0.0.1:9222")
    parser.add_argument("--chrome-path", help="Chrome/Edge executable path. Defaults to common system locations.")
    parser.add_argument(
        "--user-data-dir",
        default=os.environ.get("WEBMIND_PROFILE"),
        help=f"persistent CDP browser profile directory. Defaults to {DEFAULT_PROFILE_DIR}",
    )
    parser.add_argument("--debug-address", default=DEFAULT_DEBUG_ADDRESS, help="address Chrome binds for remote debugging")
    parser.add_argument("--launch-timeout", type=float, default=10.0, help="seconds to wait after launching Chrome")
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

    p = sub.add_parser("launch", help="launch the fixed CDP Chrome profile if it is not already running")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    p.add_argument("--url", help="optional URL to open after launch")
    p.add_argument("--new-window", action="store_true", help="open URL in a new Chrome window")
    p.add_argument("--port", type=int, help="debugging port. Defaults to the port from --endpoint.")
    p.set_defaults(func=command_launch)

    p = sub.add_parser("eval", help="evaluate JavaScript in a target tab")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--expression", required=True, help="JavaScript expression to evaluate")
    p.set_defaults(func=command_eval)

    p = sub.add_parser("navigate", help="navigate a target tab")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--url", required=True, help="URL to navigate to")
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

    p = sub.add_parser("click", help="click the center of a selector with CDP mouse events")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    p.set_defaults(func=command_click)

    p = sub.add_parser("fill", help="set a selector's text/value and dispatch input/change")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    p.add_argument("--text", required=True, help="text to place in the element")
    p.set_defaults(func=command_fill)

    p = sub.add_parser("insert-text", help="focus a selector and insert text via CDP Input.insertText")
    p.add_argument("--json", action="store_true", default=argparse.SUPPRESS)
    add_target_args(p)
    p.add_argument("--selector", required=True, help="CSS selector")
    p.add_argument("--text", required=True, help="text to insert")
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
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "dismiss") and args.dismiss:
        args.accept = False
    try:
        result = args.func(args)
    except urllib.error.URLError as exc:
        fail(f"cannot reach CDP endpoint {args.endpoint}: {exc}", getattr(args, "json", False))
    except Exception as exc:  # noqa: BLE001 - user-facing CLI should stay concise
        fail(str(exc), getattr(args, "json", False))

    if getattr(args, "json", False):
        json_print(result)
    else:
        print(f"{result.get('action', args.command)}: {'ok' if result.get('ok') else 'not ok'}")
        if "output" in result:
            print(f"output: {result['output']}")
        if "value" in result:
            print(result["value"])
    return 0 if result.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
