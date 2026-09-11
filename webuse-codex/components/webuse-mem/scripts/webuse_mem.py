#!/usr/bin/env python3
"""Manage an external Mem folder for Codex WebUse task memory."""

from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import platform
import re
import stat
import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

REQUIRED_FILES = ("global.md", "content.md")
DEFAULT_TASK_FILES = ("memory.md", "flow.md", "ui.md", "rules.md", "notes.md")
TEXT_EXTENSIONS = {".md", ".txt"}
MAX_SEARCH_BYTES = 512_000
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


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


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


def default_data_dir() -> Path:
    override = os.environ.get("WEBUSE_CODEX_DATA_DIR") or os.environ.get("WEBUSE_DATA_DIR")
    if override:
        return Path(override).expanduser()
    system = platform.system()
    if system == "Windows":
        root = os.environ.get("LOCALAPPDATA")
        return (Path(root) if root else Path.home() / "AppData" / "Local") / "WebUseCodex"
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "WebUseCodex"
    root = os.environ.get("XDG_DATA_HOME")
    return (Path(root).expanduser() if root else Path.home() / ".local" / "share") / "webuse-codex"


def normalize_mem_path(raw_path: Optional[str]) -> Tuple[Path, List[str]]:
    expanded = Path(raw_path).expanduser() if raw_path and raw_path.strip() else default_data_dir() / "Mem"
    warnings: List[str] = []
    name_matches = expanded.name == "Mem" or (
        platform.system() == "Windows" and expanded.name.casefold() == "mem"
    )
    if not name_matches:
        warnings.append(
            "provided path does not end with 'Mem'; treating it as a parent directory and using '<path>/Mem'"
        )
        expanded = expanded / "Mem"
    return expanded.resolve(), warnings


def json_print(obj: Dict[str, Any]) -> None:
    print(json.dumps(obj, ensure_ascii=False, indent=2, sort_keys=False))


def fail(message: str, json_mode: bool = False, **extra: Any) -> None:
    if json_mode:
        payload = {"ok": False, "error": message}
        payload.update(extra)
        json_print(payload)
    else:
        print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


def safe_task_name(name: str) -> str:
    cleaned = name.strip()
    cleaned = cleaned.replace("/", "_").replace("\\", "_")
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[:*?\"<>|]", "_", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned)
    cleaned = cleaned.strip("._ ")
    cleaned = cleaned or "task"
    if cleaned.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        cleaned += "_"
    return cleaned


def safe_file_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned:
        raise ValueError("file name cannot be empty")
    if "/" in cleaned or "\\" in cleaned or cleaned in {".", ".."}:
        raise ValueError("file name must be a simple file name, not a path")
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[:*?\"<>|]", "_", cleaned)
    if not cleaned.endswith(".md") and not cleaned.endswith(".txt"):
        cleaned += ".md"
    if Path(cleaned).stem.split(".", 1)[0].upper() in WINDOWS_RESERVED_NAMES:
        cleaned = "_" + cleaned
    return cleaned


def safe_child(parent: Path, name: str) -> Path:
    """Resolve a child while rejecting symlink/path traversal outside parent."""
    parent_resolved = parent.resolve()
    candidate = (parent / name).resolve()
    try:
        candidate.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError(f"memory path escapes its parent directory: {name}") from exc
    return candidate


def global_template() -> str:
    return (
        "# Global memory\n\n"
        "Record only durable instructions and reusable cross-task memory that should apply to many Codex WebUse tasks.\n\n"
        "## Durable instructions\n\n"
        "- (empty)\n"
    )


def task_template(task_name: str) -> str:
    return (
        f"# {task_name}\n\n"
        "Record concise, stable, reusable memory for this task category.\n"
        "Avoid secrets, one-time output, speculative failures, and unrelated information.\n"
    )


def ensure_structure(mem_path: Path, create: bool) -> Dict[str, Any]:
    created: List[str] = []
    missing: List[str] = []

    if not mem_path.exists():
        if not create:
            missing.append(str(mem_path))
            return {"created": created, "missing": missing}
        mem_path.mkdir(parents=True, exist_ok=True)
        created.append(str(mem_path))

    if not mem_path.is_dir():
        raise ValueError(f"mem path is not a directory: {mem_path}")

    global_file = safe_child(mem_path, "global.md")
    if not global_file.exists():
        if create:
            global_file.write_text(global_template(), encoding="utf-8", newline="\n")
            created.append(str(global_file))
        else:
            missing.append(str(global_file))

    content_file = safe_child(mem_path, "content.md")
    if not content_file.exists():
        if create:
            content_file.write_text("# Mem content index\n", encoding="utf-8", newline="\n")
            created.append(str(content_file))
        else:
            missing.append(str(content_file))

    if create:
        rebuild_content(mem_path)

    return {"created": created, "missing": missing}


def iter_tree(mem_path: Path, max_depth: int = 4) -> Iterable[Tuple[int, Path]]:
    def walk(path: Path, depth: int) -> Iterable[Tuple[int, Path]]:
        if depth > max_depth:
            return
        try:
            entries = sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower()))
        except OSError:
            return
        for entry in entries:
            if entry.name.startswith("."):
                continue
            yield depth, entry
            if entry.is_dir() and not entry.is_symlink():
                yield from walk(entry, depth + 1)

    yield from walk(mem_path, 0)


def tree_text(mem_path: Path) -> str:
    lines = ["Mem/"]
    for depth, entry in iter_tree(mem_path):
        rel = entry.relative_to(mem_path)
        if rel.name == "content.md":
            pass
        indent = "  " * (depth + 1)
        suffix = "/" if entry.is_dir() else ""
        lines.append(f"{indent}{entry.name}{suffix}")
    return "\n".join(lines)


def task_folders(mem_path: Path) -> List[Dict[str, Any]]:
    if not mem_path.exists():
        return []
    tasks: List[Dict[str, Any]] = []
    for entry in sorted(mem_path.iterdir(), key=lambda p: p.name.lower()):
        if entry.name.startswith(".") or entry.is_symlink() or not entry.is_dir():
            continue
        files = []
        for child in sorted(entry.iterdir(), key=lambda p: p.name.lower()):
            if child.is_file() and not child.is_symlink() and not child.name.startswith("."):
                files.append(child.name)
        tasks.append({"name": entry.name, "path": str(entry), "files": files})
    return tasks


def rebuild_content(mem_path: Path) -> str:
    tasks = task_folders(mem_path)
    lines: List[str] = [
        "# Mem content index",
        "",
        "This file is maintained by `webuse-mem`. It records the current architecture of this `Mem` folder so Codex can choose only relevant memories.",
        "",
        "## Root",
        "",
        f"- path: `{mem_path}`",
        f"- updated: `{now_iso()}`",
        "",
        "## Required files",
        "",
        "- `global.md`: global instructions and durable cross-task memory",
        "- `content.md`: this architecture/index file",
        "",
        "## Task folders",
        "",
    ]
    if tasks:
        for task in tasks:
            file_list = ", ".join(f"`{name}`" for name in task["files"]) or "(no files yet)"
            lines.append(f"- `{task['name']}/`: {file_list}")
    else:
        lines.append("- (none yet)")
    lines.extend(["", "## Directory tree", "", "```text", tree_text(mem_path), "```", ""])
    content = "\n".join(lines)
    safe_child(mem_path, "content.md").write_text(content, encoding="utf-8", newline="\n")
    return content


def read_text_file(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="strict")


def read_stdin(require: bool = True) -> str:
    if sys.stdin.isatty():
        if require:
            raise ValueError("expected markdown content on stdin")
        return ""
    return sys.stdin.read().strip()


def append_block(path: Path, text: str, title: Optional[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    heading = title.strip() if title and title.strip() else "memory update"
    block = f"\n\n## {now_iso()} - {heading}\n\n{text.strip()}\n"
    if not path.exists():
        path.write_text(f"# {path.stem}\n", encoding="utf-8", newline="\n")
    with path.open("a", encoding="utf-8", newline="\n") as f:
        f.write(block)


def validate_rewrite_text(path: Path, text: str) -> str:
    normalized = text.strip()
    if not normalized:
        raise ValueError("rewritten memory cannot be empty")
    if path.suffix.lower() == ".md":
        first_line = next((line.strip() for line in normalized.splitlines() if line.strip()), "")
        if not first_line.startswith("# "):
            raise ValueError("rewritten markdown must start with one level-1 heading ('# ...')")
    return normalized + "\n"


def rewrite_file_atomic(path: Path, text: str, expected_sha256: Optional[str] = None) -> Dict[str, Any]:
    if not path.exists() or not path.is_file():
        raise ValueError(f"memory file does not exist: {path}")

    old_bytes = path.read_bytes()
    old_sha256 = hashlib.sha256(old_bytes).hexdigest()
    if expected_sha256 and expected_sha256.lower() != old_sha256:
        raise ValueError(
            "memory file changed since it was read; refusing to overwrite because --expected-sha256 does not match"
        )

    normalized = validate_rewrite_text(path, text)
    new_bytes = normalized.encode("utf-8")
    new_sha256 = hashlib.sha256(new_bytes).hexdigest()
    if new_sha256 == old_sha256:
        return {
            "changed": False,
            "old_sha256": old_sha256,
            "new_sha256": new_sha256,
            "old_bytes": len(old_bytes),
            "new_bytes": len(new_bytes),
        }

    temp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="wb",
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
            delete=False,
        ) as temp_file:
            temp_file.write(new_bytes)
            temp_file.flush()
            os.fsync(temp_file.fileno())
            temp_name = temp_file.name
        os.chmod(temp_name, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except OSError:
                pass

    return {
        "changed": True,
        "old_sha256": old_sha256,
        "new_sha256": new_sha256,
        "old_bytes": len(old_bytes),
        "new_bytes": len(new_bytes),
    }


def search_file(path: Path, tokens: List[str], query: str) -> Optional[Dict[str, Any]]:
    try:
        data = path.read_bytes()[:MAX_SEARCH_BYTES]
    except OSError:
        return None
    # A byte limit can split the final UTF-8 code point. Ignore only that
    # incomplete suffix while still rejecting malformed UTF-8 elsewhere.
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        if exc.end == len(data) and exc.reason == "unexpected end of data":
            text = data[: exc.start].decode("utf-8", errors="strict")
        else:
            raise
    haystack = f"{path.name}\n{text}".lower()
    score = 0
    for token in tokens:
        if token and token in haystack:
            score += 2
    if query.lower() in haystack:
        score += 5
    if score <= 0:
        return None

    snippet = ""
    lower_text = text.lower()
    first_positions = [lower_text.find(token) for token in tokens if token and lower_text.find(token) >= 0]
    if first_positions:
        start = max(0, min(first_positions) - 80)
        end = min(len(text), start + 320)
        snippet = text[start:end].replace("\n", " ").strip()
    else:
        snippet = text[:320].replace("\n", " ").strip()
    return {"path": str(path), "score": score, "snippet": snippet}


def command_self_check(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    payload: Dict[str, Any] = {
        "ok": True,
        "action": "self-check",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "mem_path": str(mem_path),
        "exists": mem_path.exists(),
        "is_dir": mem_path.is_dir(),
        "warnings": warnings,
    }
    return payload


def command_init(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    result = ensure_structure(mem_path, create=True)
    return {
        "ok": True,
        "action": "init",
        "mem_path": str(mem_path),
        "created": result["created"],
        "missing": result["missing"],
        "tasks": task_folders(mem_path),
        "warnings": warnings,
    }


def command_check(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    result = ensure_structure(mem_path, create=args.create_missing)
    ok = not result["missing"] and mem_path.exists() and mem_path.is_dir()
    return {
        "ok": ok,
        "action": "check",
        "mem_path": str(mem_path),
        "exists": mem_path.exists(),
        "is_dir": mem_path.is_dir(),
        "created": result["created"],
        "missing": result["missing"],
        "tasks": task_folders(mem_path) if mem_path.exists() and mem_path.is_dir() else [],
        "warnings": warnings,
    }


def command_rebuild_content(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    content = rebuild_content(mem_path)
    return {
        "ok": True,
        "action": "rebuild-content",
        "mem_path": str(mem_path),
        "content_path": str(mem_path / "content.md"),
        "bytes": len(content.encode("utf-8")),
        "tasks": task_folders(mem_path),
        "warnings": warnings,
    }


def command_list(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    if not mem_path.is_dir():
        fail(f"Mem folder does not exist: {mem_path}", args.json)
    return {
        "ok": True,
        "action": "list",
        "mem_path": str(mem_path),
        "tasks": task_folders(mem_path),
        "warnings": warnings,
    }


def command_search(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    if not mem_path.is_dir():
        fail(f"Mem folder does not exist: {mem_path}", args.json)
    query = args.query.strip()
    if not query:
        fail("--query cannot be empty", args.json)
    tokens = [token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]+", query) if token]
    matches: List[Dict[str, Any]] = []
    for path in sorted(mem_path.rglob("*"), key=lambda p: str(p).lower()):
        if path.is_symlink() or not path.is_file() or path.name.startswith("."):
            continue
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        result = search_file(path, tokens, query)
        if result:
            result["relative_path"] = str(path.relative_to(mem_path))
            matches.append(result)
    if args.limit <= 0:
        fail("--limit must be a positive integer", args.json)
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {
        "ok": True,
        "action": "search",
        "mem_path": str(mem_path),
        "query": query,
        "matches": matches[: args.limit],
        "warnings": warnings,
    }


def command_read(args: argparse.Namespace) -> Optional[Dict[str, Any]]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    if not mem_path.is_dir():
        fail(f"Mem folder does not exist: {mem_path}", args.json)

    files: List[Path] = []
    if args.scope == "global":
        files = [safe_child(mem_path, "global.md")]
    elif args.scope == "content":
        files = [safe_child(mem_path, "content.md")]
    elif args.task:
        task_dir = safe_child(mem_path, safe_task_name(args.task))
        if not task_dir.is_dir():
            fail(f"task folder does not exist: {task_dir}", args.json)
        if args.file:
            files = [safe_child(task_dir, safe_file_name(args.file))]
        else:
            files = [p for p in sorted(task_dir.iterdir(), key=lambda p: p.name.lower()) if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS]
    else:
        fail("choose --scope global, --scope content, or --task", args.json)

    readable = []
    for file_path in files:
        if file_path.exists() and file_path.is_file():
            readable.append(file_path)

    if args.json:
        file_payloads = []
        for path in readable:
            data = path.read_bytes()
            file_payloads.append(
                {
                    "path": str(path),
                    "relative_path": str(path.relative_to(mem_path)),
                    "sha256": hashlib.sha256(data).hexdigest(),
                    "text": data.decode("utf-8", errors="strict"),
                }
            )
        return {
            "ok": True,
            "action": "read",
            "mem_path": str(mem_path),
            "files": file_payloads,
            "warnings": warnings,
        }

    for idx, path in enumerate(readable):
        if idx:
            print("\n" + "=" * 80 + "\n")
        print(f"# FILE: {path.relative_to(mem_path)}\n")
        print(read_text_file(path))
    return None


def command_record(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    task_name = safe_task_name(args.task)
    file_name = safe_file_name(args.file)
    text = read_stdin(require=args.stdin)
    if not text:
        fail("no memory text provided on stdin", args.json)
    task_dir = safe_child(mem_path, task_name)
    if not task_dir.exists():
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "memory.md").write_text(
            task_template(task_name), encoding="utf-8", newline="\n"
        )
    target = safe_child(task_dir, file_name)
    append_block(target, text, args.title)
    rebuild_content(mem_path)
    return {
        "ok": True,
        "action": "record",
        "mem_path": str(mem_path),
        "task": task_name,
        "file": str(target),
        "relative_path": str(target.relative_to(mem_path)),
        "bytes_appended": len(text.encode("utf-8")),
        "warnings": warnings,
    }


def command_rewrite(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    structure = ensure_structure(mem_path, create=False)
    if structure["missing"]:
        fail(f"Mem folder is incomplete: {', '.join(structure['missing'])}", args.json)
    task_name = safe_task_name(args.task)
    file_name = safe_file_name(args.file)
    task_dir = safe_child(mem_path, task_name)
    target = safe_child(task_dir, file_name)
    if not target.exists():
        fail(
            f"memory file does not exist: {target}; use record for new memory files",
            args.json,
        )
    text = read_stdin(require=True)
    result = rewrite_file_atomic(target, text, args.expected_sha256)
    if result["changed"]:
        rebuild_content(mem_path)
    return {
        "ok": True,
        "action": "rewrite",
        "mem_path": str(mem_path),
        "task": task_name,
        "file": str(target),
        "relative_path": str(target.relative_to(mem_path)),
        **result,
        "warnings": warnings,
    }


def command_record_global(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    text = read_stdin(require=args.stdin)
    if not text:
        fail("no global memory text provided on stdin", args.json)
    target = safe_child(mem_path, "global.md")
    append_block(target, text, args.title)
    rebuild_content(mem_path)
    return {
        "ok": True,
        "action": "record-global",
        "mem_path": str(mem_path),
        "file": str(target),
        "relative_path": "global.md",
        "bytes_appended": len(text.encode("utf-8")),
        "warnings": warnings,
    }


def command_rewrite_global(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    structure = ensure_structure(mem_path, create=False)
    if structure["missing"]:
        fail(f"Mem folder is incomplete: {', '.join(structure['missing'])}", args.json)
    target = safe_child(mem_path, "global.md")
    text = read_stdin(require=True)
    result = rewrite_file_atomic(target, text, args.expected_sha256)
    if result["changed"]:
        rebuild_content(mem_path)
    return {
        "ok": True,
        "action": "rewrite-global",
        "mem_path": str(mem_path),
        "file": str(target),
        "relative_path": "global.md",
        **result,
        "warnings": warnings,
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage a Codex WebUse Mem folder.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON where supported")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_json_flag(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit machine-readable JSON")

    p = sub.add_parser("self-check", help="check Python environment and optionally a Mem path")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder, or a parent directory containing Mem")
    p.set_defaults(func=command_self_check)

    p = sub.add_parser("init", help="initialize or repair the Mem folder")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.set_defaults(func=command_init)

    p = sub.add_parser("check", help="check the Mem folder structure")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--create-missing", action="store_true", help="create missing required files after path confirmation")
    p.set_defaults(func=command_check)

    p = sub.add_parser("rebuild-content", help="refresh content.md from the actual directory tree")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.set_defaults(func=command_rebuild_content)

    p = sub.add_parser("list", help="list task folders")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.set_defaults(func=command_list)

    p = sub.add_parser("search", help="search markdown/text memory files")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--query", required=True, help="search query for a clear concrete task")
    p.add_argument("--limit", type=int, default=10, help="maximum matches to return")
    p.set_defaults(func=command_search)

    p = sub.add_parser("read", help="read global/content memory or one task folder")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--scope", choices=("global", "content"), help="read global.md or content.md")
    p.add_argument("--task", help="task folder name to read")
    p.add_argument("--file", help="single file inside the task folder")
    p.set_defaults(func=command_read)

    p = sub.add_parser("record", help="append task memory from stdin")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--task", required=True, help="task folder name")
    p.add_argument("--file", default="memory.md", help="markdown file inside the task folder")
    p.add_argument("--title", help="heading for this memory block")
    p.add_argument("--stdin", action="store_true", help="read memory markdown from stdin")
    p.set_defaults(func=command_record)

    p = sub.add_parser("rewrite", help="atomically replace one existing task memory file with a reconciled version")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--task", required=True, help="existing task folder name")
    p.add_argument("--file", default="memory.md", help="existing markdown/text file inside the task folder")
    p.add_argument(
        "--expected-sha256",
        help="optional SHA-256 from the last read; refuse the rewrite if the file changed",
    )
    p.add_argument("--stdin", action="store_true", help="read the complete reconciled file from stdin")
    p.set_defaults(func=command_rewrite)

    p = sub.add_parser("record-global", help="append global memory from stdin")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument("--title", help="heading for this global memory block")
    p.add_argument("--stdin", action="store_true", help="read memory markdown from stdin")
    p.set_defaults(func=command_record_global)

    p = sub.add_parser("rewrite-global", help="atomically replace global.md with a reconciled version")
    add_json_flag(p)
    p.add_argument("--mem-path", help="path to Mem folder; defaults to the per-user WebUse data directory")
    p.add_argument(
        "--expected-sha256",
        help="optional SHA-256 from the last read; refuse the rewrite if the file changed",
    )
    p.add_argument("--stdin", action="store_true", help="read the complete reconciled global.md from stdin")
    p.set_defaults(func=command_rewrite_global)

    return parser


def main() -> None:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.func(args)
    except Exception as exc:  # noqa: BLE001 - user-facing CLI should report concise errors
        fail(str(exc), getattr(args, "json", False))
    if result is None:
        return
    if getattr(args, "json", False):
        json_print(result)
    else:
        action = result.get("action", args.command)
        ok = result.get("ok", False)
        print(f"{action}: {'ok' if ok else 'not ok'}")
        if "mem_path" in result:
            print(f"mem_path: {result['mem_path']}")
        if result.get("warnings"):
            for warning in result["warnings"]:
                print(f"warning: {warning}")


if __name__ == "__main__":
    main()
