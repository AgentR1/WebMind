#!/usr/bin/env python3
"""Manage the selected external Mem folder and its browser profile."""

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

HOST_DISPLAY = "Claude Code"
EDITION_ID = "webmind-claudecode"
REQUIRED_FILES = ("global.md", "content.md")
DEFAULT_TASK_FILES = ("memory.md", "flow.md", "ui.md", "rules.md", "notes.md")
TEXT_EXTENSIONS = {".md", ".txt"}
MAX_SEARCH_BYTES = 512_000
MEM_NAME_RE = re.compile(r"^(?P<prefix>[a-z]{1,8})-(?P<number>[1-9][0-9]{0,2})-mem$")
PROFILE_METADATA_FILE = "webmind-profile.json"
LOCATION_SCHEMA_VERSION = 1
PROFILE_SCHEMA_VERSION = 2
SKILL_ROOT = Path(__file__).resolve().parents[1]
PACKAGE_ROOT = Path(__file__).resolve().parents[3]
LOCATION_FILE = Path(os.environ.get("WEBMIND_MEM_LOCATION_FILE", str(SKILL_ROOT / "mem-location.json"))).expanduser()
BASIC_RULES_FILE = SKILL_ROOT / "basic-rules.md"
WINDOWS_RESERVED_NAMES = {
    "CON", "PRN", "AUX", "NUL",
    *(f"COM{index}" for index in range(1, 10)),
    *(f"LPT{index}" for index in range(1, 10)),
}


class InitializationRequired(RuntimeError):
    pass


def configure_utf8_stdio() -> None:
    for name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, name)
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="strict")
            except (OSError, ValueError):
                pass


def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


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


def same_path(left: Path, right: Path) -> bool:
    try:
        if left.exists() and right.exists():
            return os.path.samefile(left, right)
    except OSError:
        pass
    left_text = os.path.normpath(os.path.realpath(str(left)))
    right_text = os.path.normpath(os.path.realpath(str(right)))
    if os.name == "nt":
        left_text = os.path.normcase(left_text)
        right_text = os.path.normcase(right_text)
    return left_text == right_text


def is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
        return True
    except ValueError:
        return False


def parse_mem_name(name: str) -> Dict[str, Any]:
    match = MEM_NAME_RE.fullmatch(name)
    if not match:
        raise ValueError(
            "Mem folder name must match xxx-yyy-mem: xxx is 1-8 lowercase English letters; "
            "yyy is 1-999 with no leading zero; -mem is required"
        )
    number = int(match.group("number"))
    return {
        "name": name,
        "prefix": match.group("prefix"),
        "number": number,
        "debug_port": 9000 + number,
        "profile_name": f"{name}-Profile",
    }


def skill_related_ancestor(path: Path) -> Optional[Path]:
    """Return a skill/plugin ancestor that must not contain active Mem data."""
    resolved = path.expanduser().resolve()
    ancestors = (resolved, *resolved.parents)
    for ancestor in ancestors:
        if same_path(ancestor, PACKAGE_ROOT):
            return ancestor
        if (ancestor / "SKILL.md").is_file():
            return ancestor
        if (ancestor / ".claude-plugin" / "plugin.json").is_file():
            return ancestor
    normalized_parts = [part.casefold() for part in resolved.parts]
    forbidden_pairs = {(".agents", "skills"), (".claude", "skills"), (".claude", "plugins")}
    for index in range(len(normalized_parts) - 1):
        if (normalized_parts[index], normalized_parts[index + 1]) in forbidden_pairs:
            return Path(*resolved.parts[: index + 2])
    return None


def validate_external_mem_path(mem_path: Path) -> Path:
    mem_path = mem_path.expanduser().resolve()
    parse_mem_name(mem_path.name)
    forbidden = skill_related_ancestor(mem_path)
    if forbidden is not None:
        raise ValueError(
            f"Mem must be outside every skill/plugin folder; rejected ancestor: {forbidden}. "
            "Choose a normal user folder such as Downloads, Desktop, Documents, or another explicit location."
        )
    return mem_path


def recommended_parent_paths() -> List[str]:
    candidates = [Path.home() / "Downloads", Path.home() / "Desktop", Path.home() / "Documents"]
    result: List[str] = []
    for path in candidates:
        try:
            if path.is_dir() and not is_within(path, PACKAGE_ROOT):
                result.append(str(path.resolve()))
        except OSError:
            continue
    if not result:
        result.append(str(Path.home().resolve()))
    return result


def _read_json(path: Path) -> Dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"JSON object expected: {path}")
    return data


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=False) + "\n").encode("utf-8")
    temp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as temp:
            temp.write(data)
            temp.flush()
            os.fsync(temp.fileno())
            temp_name = temp.name
        if os.name != "nt":
            os.chmod(temp_name, 0o600)
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except OSError:
                pass


def load_location_config(required: bool = False) -> Optional[Dict[str, Any]]:
    if not LOCATION_FILE.is_file():
        if required:
            raise InitializationRequired(
                "webmind is not initialized. Select an external Mem folder through the initialization flow first."
            )
        return None
    try:
        data = _read_json(LOCATION_FILE)
        if data.get("schema_version") != LOCATION_SCHEMA_VERSION:
            raise ValueError("unsupported location schema")
        raw_path = data.get("mem_path")
        if not isinstance(raw_path, str) or not raw_path.strip():
            raise ValueError("mem_path is missing")
        mem_path = validate_external_mem_path(Path(raw_path))
        if data.get("mem_name") != mem_path.name:
            raise ValueError("mem_name does not match mem_path")
        return {**data, "mem_path": str(mem_path)}
    except Exception as exc:
        if required:
            raise InitializationRequired(
                f"stored Mem selection is invalid: {exc}. Re-enter the initialization flow."
            ) from exc
        return {"invalid": True, "error": str(exc)}


def save_location_config(mem_path: Path) -> None:
    mem_path = validate_external_mem_path(mem_path)
    payload = {
        "schema_version": LOCATION_SCHEMA_VERSION,
        "edition": EDITION_ID,
        "mem_name": mem_path.name,
        "mem_path": str(mem_path),
        "selected_at": now_iso(),
    }
    _write_json_atomic(LOCATION_FILE, payload)


def normalize_mem_path(raw_path: Optional[str]) -> Tuple[Path, List[str]]:
    selected = load_location_config(required=True)
    assert selected is not None
    selected_path = Path(selected["mem_path"]).resolve()
    if raw_path and raw_path.strip():
        requested = validate_external_mem_path(Path(raw_path))
        if not same_path(requested, selected_path):
            raise ValueError(
                f"requested Mem path is not the initialized Mem folder: {requested}. "
                "To switch Mem/profile, re-enter initialization instead of overriding a normal command."
            )
    return selected_path, []


def safe_task_name(name: str) -> str:
    cleaned = name.strip().replace("/", "_").replace("\\", "_")
    cleaned = re.sub(r"[\x00-\x1f\x7f]", "", cleaned)
    cleaned = re.sub(r"[:*?\"<>|]", "_", cleaned)
    cleaned = re.sub(r"\s+", "_", cleaned).strip("._ ") or "task"
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
    parent_resolved = parent.resolve()
    candidate = (parent / name).resolve()
    try:
        candidate.relative_to(parent_resolved)
    except ValueError as exc:
        raise ValueError(f"memory path escapes its parent directory: {name}") from exc
    return candidate


def basic_rules_text() -> str:
    if not BASIC_RULES_FILE.is_file():
        raise RuntimeError(f"bundled basic-rules.md is missing: {BASIC_RULES_FILE}")
    return BASIC_RULES_FILE.read_text(encoding="utf-8", errors="strict").rstrip() + "\n"


def expected_profile(mem_path: Path) -> Dict[str, Any]:
    info = parse_mem_name(mem_path.name)
    profile_path = (mem_path / info["profile_name"]).resolve()
    return {
        "schema_version": PROFILE_SCHEMA_VERSION,
        "mem_name": mem_path.name,
        "profile_name": info["profile_name"],
        "profile_path": str(profile_path),
        "debug_address": "127.0.0.1",
        "debug_port": info["debug_port"],
        "endpoint": f"http://127.0.0.1:{info['debug_port']}",
    }


def legacy_profile(mem_path: Path) -> Dict[str, Any]:
    """Return the exact schema-1 profile generated by the former 1000+yyy rule."""
    expected = expected_profile(mem_path)
    old_port = 1000 + parse_mem_name(mem_path.name)["number"]
    return {**expected, "schema_version": 1, "debug_port": old_port,
            "endpoint": f"http://127.0.0.1:{old_port}"}


def ensure_profile(mem_path: Path, create: bool, migrate_legacy: bool = False) -> Dict[str, Any]:
    expected = expected_profile(mem_path)
    profile_dir = Path(expected["profile_path"])
    metadata_path = profile_dir / PROFILE_METADATA_FILE
    created: List[str] = []
    missing: List[str] = []
    migrated: List[str] = []

    if not profile_dir.exists():
        if not create:
            missing.append(str(profile_dir))
            return {"created": created, "missing": missing, "migrated": migrated, "profile": expected, "metadata_path": str(metadata_path)}
        profile_dir.mkdir(parents=False, exist_ok=False)
        created.append(str(profile_dir))
    if not profile_dir.is_dir() or profile_dir.is_symlink():
        raise ValueError(f"browser profile path must be a real directory: {profile_dir}")

    if metadata_path.is_file():
        try:
            existing = _read_json(metadata_path)
        except Exception as exc:
            raise ValueError(f"invalid browser profile metadata: {metadata_path}: {exc}") from exc
        mismatches = [key for key, value in expected.items() if existing.get(key) != value]
        if mismatches:
            legacy = legacy_profile(mem_path)
            legacy_matches = all(existing.get(key) == value for key, value in legacy.items())
            if migrate_legacy and legacy_matches:
                payload = {**expected, "created_at": existing.get("created_at", now_iso()),
                           "updated_at": now_iso(), "migrated_from_endpoint": legacy["endpoint"]}
                _write_json_atomic(metadata_path, payload)
                migrated.append(str(metadata_path))
            else:
                raise ValueError(
                    f"browser profile metadata does not match this Mem folder ({', '.join(mismatches)}): {metadata_path}. "
                    "Do not repair or overwrite it implicitly; inspect the selected Mem and re-enter initialization deliberately."
                )
    elif create:
        payload = {**expected, "created_at": now_iso(), "updated_at": now_iso()}
        _write_json_atomic(metadata_path, payload)
        created.append(str(metadata_path))
    else:
        missing.append(str(metadata_path))

    return {"created": created, "missing": missing, "migrated": migrated, "profile": expected, "metadata_path": str(metadata_path)}


def task_template(task_name: str) -> str:
    return (
        f"# {task_name}\n\n"
        "Record concise, stable, reusable memory for this task category.\n"
        "Avoid secrets, one-time output, speculative failures, and unrelated information.\n"
    )


def profile_dir_name(mem_path: Path) -> str:
    return parse_mem_name(mem_path.name)["profile_name"]


def task_folders(mem_path: Path) -> List[Dict[str, Any]]:
    if not mem_path.exists():
        return []
    profile_name = profile_dir_name(mem_path)
    tasks: List[Dict[str, Any]] = []
    for entry in sorted(mem_path.iterdir(), key=lambda p: p.name.lower()):
        if entry.name.startswith(".") or entry.name == profile_name or entry.is_symlink() or not entry.is_dir():
            continue
        files = [
            child.name for child in sorted(entry.iterdir(), key=lambda p: p.name.lower())
            if child.is_file() and not child.is_symlink() and not child.name.startswith(".")
        ]
        tasks.append({"name": entry.name, "path": str(entry), "files": files})
    return tasks


def tree_text(mem_path: Path) -> str:
    lines = [f"{mem_path.name}/"]
    for required in REQUIRED_FILES:
        if (mem_path / required).exists():
            lines.append(f"  {required}")
    profile_name = profile_dir_name(mem_path)
    if (mem_path / profile_name).is_dir():
        lines.append(f"  {profile_name}/  [browser profile; contents intentionally omitted]")
    for task in task_folders(mem_path):
        lines.append(f"  {task['name']}/")
        for file_name in task["files"]:
            lines.append(f"    {file_name}")
    return "\n".join(lines)


def rebuild_content(mem_path: Path) -> str:
    tasks = task_folders(mem_path)
    profile_name = profile_dir_name(mem_path)
    lines: List[str] = [
        "# Mem content index",
        "",
        f"This file is maintained by `webmind-mem`. It records the current architecture of this external Mem folder so {HOST_DISPLAY} can load only relevant memory.",
        "",
        "## Root",
        "",
        f"- folder: `{mem_path.name}/`",
        "- location is stored by the webmind-mem skill and is intentionally not duplicated here",
        f"- updated: `{now_iso()}`",
        "",
        "## Required files",
        "",
        "- `global.md`: global instructions initialized from bundled `basic-rules.md`",
        "- `content.md`: this architecture/index file",
        f"- `{profile_name}/`: dedicated browser profile; its contents are never indexed or searched by webmind-mem",
        f"- `{profile_name}/{PROFILE_METADATA_FILE}`: browser profile path and CDP port source of truth",
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


def ensure_structure(mem_path: Path, create: bool, migrate_legacy: bool = False) -> Dict[str, Any]:
    mem_path = validate_external_mem_path(mem_path)
    created: List[str] = []
    missing: List[str] = []
    migrated: List[str] = []
    if not mem_path.exists():
        if not create:
            missing.append(str(mem_path))
            return {"created": created, "missing": missing, "migrated": migrated}
        if not mem_path.parent.is_dir():
            raise ValueError(f"selected parent directory does not exist: {mem_path.parent}")
        mem_path.mkdir()
        created.append(str(mem_path))
    if not mem_path.is_dir() or mem_path.is_symlink():
        raise ValueError(f"Mem path must be a real directory: {mem_path}")

    global_file = safe_child(mem_path, "global.md")
    if not global_file.exists():
        if create:
            global_file.write_text(basic_rules_text(), encoding="utf-8", newline="\n")
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

    profile_result = ensure_profile(mem_path, create=create, migrate_legacy=migrate_legacy)
    created.extend(profile_result["created"])
    missing.extend(profile_result["missing"])
    migrated.extend(profile_result["migrated"])
    if create:
        rebuild_content(mem_path)
    return {"created": created, "missing": missing, "migrated": migrated, "profile": profile_result["profile"], "metadata_path": profile_result["metadata_path"]}


def initialization_status() -> Dict[str, Any]:
    base: Dict[str, Any] = {
        "ok": True,
        "action": "init-status",
        "initialized": False,
        "location_file": str(LOCATION_FILE),
        "recommended_parent_paths": recommended_parent_paths(),
        "name_rule": "xxx-yyy-mem; xxx=1-8 lowercase English letters; yyy=1-999 without leading zero; port=9000+yyy; range=9001-9999",
        "uniqueness_rule": "During initialization, explicitly tell the user that XXX (xxx) and YYY (yyy) must each be unique among different Mems on the same computer.",
        "tutorial_first": True,
        "tutorial_files": ["User Guide.md", "Safety Instructions.md", "使用教程.md", "安全须知.md"],
        "risk_acceptance_required": True,
        "risk_warning": "WebMind still has security and operational risks; continuing means the user accepts those risks.",
    }
    config = load_location_config(required=False)
    if config is None:
        return {**base, "configured": False, "reason": "no Mem folder has been selected yet"}
    if config.get("invalid"):
        return {**base, "configured": True, "reason": config.get("error", "invalid location file")}
    mem_path = Path(config["mem_path"])
    try:
        result = ensure_structure(mem_path, create=False)
        if result["missing"]:
            return {**base, "configured": True, "mem_path": str(mem_path), "mem_name": mem_path.name, "reason": "selected Mem folder is incomplete", "missing": result["missing"]}
        profile = result["profile"]
        return {
            **base,
            "configured": True,
            "initialized": True,
            "mem_path": str(mem_path),
            "mem_name": mem_path.name,
            "profile_path": profile["profile_path"],
            "debug_port": profile["debug_port"],
            "endpoint": profile["endpoint"],
            "profile_metadata": result["metadata_path"],
        }
    except Exception as exc:
        return {**base, "configured": True, "mem_path": str(mem_path), "mem_name": mem_path.name, "reason": str(exc)}


def iter_memory_files(mem_path: Path) -> Iterable[Path]:
    for name in REQUIRED_FILES:
        path = mem_path / name
        if path.is_file() and not path.is_symlink():
            yield path
    for task in task_folders(mem_path):
        task_dir = mem_path / task["name"]
        for path in sorted(task_dir.rglob("*"), key=lambda p: str(p).lower()):
            if path.is_symlink() or not path.is_file() or path.name.startswith("."):
                continue
            if path.suffix.lower() in TEXT_EXTENSIONS:
                yield path


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
    with path.open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(block)


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
        raise ValueError("memory file changed since it was read; refusing to overwrite because --expected-sha256 does not match")
    normalized = validate_rewrite_text(path, text)
    new_bytes = normalized.encode("utf-8")
    new_sha256 = hashlib.sha256(new_bytes).hexdigest()
    if new_sha256 == old_sha256:
        return {"changed": False, "old_sha256": old_sha256, "new_sha256": new_sha256, "old_bytes": len(old_bytes), "new_bytes": len(new_bytes)}
    temp_name: Optional[str] = None
    try:
        with tempfile.NamedTemporaryFile(mode="wb", prefix=f".{path.name}.", suffix=".tmp", dir=path.parent, delete=False) as temp:
            temp.write(new_bytes)
            temp.flush()
            os.fsync(temp.fileno())
            temp_name = temp.name
        os.chmod(temp_name, stat.S_IMODE(path.stat().st_mode))
        os.replace(temp_name, path)
        temp_name = None
    finally:
        if temp_name:
            try:
                Path(temp_name).unlink()
            except OSError:
                pass
    return {"changed": True, "old_sha256": old_sha256, "new_sha256": new_sha256, "old_bytes": len(old_bytes), "new_bytes": len(new_bytes)}


def search_file(path: Path, tokens: List[str], query: str) -> Optional[Dict[str, Any]]:
    try:
        data = path.read_bytes()[:MAX_SEARCH_BYTES]
    except OSError:
        return None
    try:
        text = data.decode("utf-8", errors="strict")
    except UnicodeDecodeError as exc:
        if exc.end == len(data) and exc.reason == "unexpected end of data":
            text = data[: exc.start].decode("utf-8", errors="strict")
        else:
            raise
    haystack = f"{path.name}\n{text}".lower()
    score = sum(2 for token in tokens if token and token in haystack)
    if query.lower() in haystack:
        score += 5
    if score <= 0:
        return None
    lower_text = text.lower()
    positions = [lower_text.find(token) for token in tokens if token and lower_text.find(token) >= 0]
    start = max(0, min(positions) - 80) if positions else 0
    snippet = text[start : min(len(text), start + 320)].replace("\n", " ").strip()
    return {"path": str(path), "score": score, "snippet": snippet}


def command_init_status(args: argparse.Namespace) -> Dict[str, Any]:
    return initialization_status()


def command_scan(args: argparse.Namespace) -> Dict[str, Any]:
    parent = Path(args.parent).expanduser().resolve()
    if not parent.is_dir():
        raise ValueError(f"parent directory does not exist: {parent}")
    if is_within(parent, PACKAGE_ROOT):
        raise ValueError("initialization parent must be outside the installed skill/plugin folder")
    found: List[Dict[str, Any]] = []
    for entry in sorted(parent.iterdir(), key=lambda p: p.name.lower()):
        if entry.is_symlink() or not entry.is_dir():
            continue
        match = MEM_NAME_RE.fullmatch(entry.name)
        if not match:
            continue
        info = parse_mem_name(entry.name)
        found.append({"name": entry.name, "path": str(entry.resolve()), "debug_port": info["debug_port"], "profile_name": info["profile_name"]})
    return {"ok": True, "action": "scan", "parent": str(parent), "direct_children_only": True, "mem_folders": found, "uniqueness_rule": "XXX (xxx) and YYY (yyy) must each be unique among different Mems on the same computer; this scan checks only direct children of the selected parent."}


def command_name_info(args: argparse.Namespace) -> Dict[str, Any]:
    info = parse_mem_name(args.name)
    return {"ok": True, "action": "name-info", **info, "uniqueness_rule": "Format validation does not prove uniqueness. During initialization, choose both an XXX (xxx) and a YYY (yyy) not used by another Mem on this computer."}


def command_self_check(args: argparse.Namespace) -> Dict[str, Any]:
    status = initialization_status()
    payload: Dict[str, Any] = {
        "ok": True,
        "action": "self-check",
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "cwd": os.getcwd(),
        "initialization": status,
    }
    if args.mem_path:
        candidate = validate_external_mem_path(Path(args.mem_path))
        payload["candidate"] = {"mem_path": str(candidate), "exists": candidate.exists(), "is_dir": candidate.is_dir()}
    return payload


def command_init(args: argparse.Namespace) -> Dict[str, Any]:
    if not args.accept_risk:
        raise ValueError(
            "initialization requires explicit risk acceptance. Recommend reading the usage tutorial and safety notice first; "
            "if the user chooses to continue, rerun with --accept-risk"
        )
    mem_path = validate_external_mem_path(Path(args.mem_path))
    parent = mem_path.parent
    if not parent.is_dir():
        raise ValueError(f"selected parent directory does not exist: {parent}")
    existed = mem_path.exists()
    result = ensure_structure(mem_path, create=True, migrate_legacy=True)
    save_location_config(mem_path)
    profile = result["profile"]
    return {
        "ok": True,
        "action": "init",
        "mode": "attached" if existed else "created",
        "mem_path": str(mem_path),
        "mem_name": mem_path.name,
        "created": result["created"],
        "migrated": result["migrated"],
        "tasks": task_folders(mem_path),
        "profile_path": profile["profile_path"],
        "profile_name": profile["profile_name"],
        "debug_port": profile["debug_port"],
        "endpoint": profile["endpoint"],
        "profile_metadata": result["metadata_path"],
        "location_file": str(LOCATION_FILE),
        "uniqueness_rule": "XXX (xxx) and YYY (yyy) must each be unique among different Mems on the same computer.",
        "reminder": "Remember this Mem folder name and location. A skill update may require selecting it again. To switch Mem/profile, re-enter initialization before or after a task. When creating another Mem, choose a new unique XXX (xxx) and YYY (yyy).",
    }


def command_check(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    result = ensure_structure(mem_path, create=args.create_missing)
    ok = not result["missing"] and mem_path.exists() and mem_path.is_dir()
    return {"ok": ok, "action": "check", "mem_path": str(mem_path), "created": result["created"], "missing": result["missing"], "tasks": task_folders(mem_path) if mem_path.is_dir() else [], "profile": result.get("profile"), "warnings": warnings}


def command_rebuild_content(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    content = rebuild_content(mem_path)
    return {"ok": True, "action": "rebuild-content", "mem_path": str(mem_path), "content_path": str(mem_path / "content.md"), "bytes": len(content.encode("utf-8")), "tasks": task_folders(mem_path), "warnings": warnings}


def command_list(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    if not mem_path.is_dir():
        fail(f"Mem folder does not exist: {mem_path}", args.json)
    return {"ok": True, "action": "list", "mem_path": str(mem_path), "tasks": task_folders(mem_path), "warnings": warnings}


def command_search(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    if not mem_path.is_dir():
        fail(f"Mem folder does not exist: {mem_path}", args.json)
    query = args.query.strip()
    if not query:
        fail("--query cannot be empty", args.json)
    if args.limit <= 0:
        fail("--limit must be a positive integer", args.json)
    tokens = [token.lower() for token in re.findall(r"[\w\u4e00-\u9fff]+", query) if token]
    matches: List[Dict[str, Any]] = []
    for path in iter_memory_files(mem_path):
        result = search_file(path, tokens, query)
        if result:
            result["relative_path"] = str(path.relative_to(mem_path))
            matches.append(result)
    matches.sort(key=lambda item: item["score"], reverse=True)
    return {"ok": True, "action": "search", "mem_path": str(mem_path), "query": query, "matches": matches[: args.limit], "warnings": warnings}


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
        task_name = safe_task_name(args.task)
        if task_name == profile_dir_name(mem_path):
            fail("browser profile contents are not memory and cannot be read through webmind-mem", args.json)
        task_dir = safe_child(mem_path, task_name)
        if not task_dir.is_dir():
            fail(f"task folder does not exist: {task_dir}", args.json)
        if args.file:
            files = [safe_child(task_dir, safe_file_name(args.file))]
        else:
            files = [p for p in sorted(task_dir.iterdir(), key=lambda p: p.name.lower()) if p.is_file() and p.suffix.lower() in TEXT_EXTENSIONS]
    else:
        fail("choose --scope global, --scope content, or --task", args.json)
    readable = [path for path in files if path.exists() and path.is_file()]
    if args.json:
        payloads = []
        for path in readable:
            data = path.read_bytes()
            payloads.append({"path": str(path), "relative_path": str(path.relative_to(mem_path)), "sha256": hashlib.sha256(data).hexdigest(), "text": data.decode("utf-8", errors="strict")})
        return {"ok": True, "action": "read", "mem_path": str(mem_path), "files": payloads, "warnings": warnings}
    for index, path in enumerate(readable):
        if index:
            print("\n" + "=" * 80 + "\n")
        print(f"# FILE: {path.relative_to(mem_path)}\n")
        print(read_text_file(path))
    return None


def command_record(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    task_name = safe_task_name(args.task)
    if task_name == profile_dir_name(mem_path):
        fail("task name collides with the reserved browser profile folder", args.json)
    file_name = safe_file_name(args.file)
    text = read_stdin(require=args.stdin)
    if not text:
        fail("no memory text provided on stdin", args.json)
    task_dir = safe_child(mem_path, task_name)
    if not task_dir.exists():
        task_dir.mkdir(parents=True, exist_ok=True)
        (task_dir / "memory.md").write_text(task_template(task_name), encoding="utf-8", newline="\n")
    target = safe_child(task_dir, file_name)
    append_block(target, text, args.title)
    rebuild_content(mem_path)
    return {"ok": True, "action": "record", "mem_path": str(mem_path), "task": task_name, "file": str(target), "relative_path": str(target.relative_to(mem_path)), "bytes_appended": len(text.encode("utf-8")), "warnings": warnings}


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
        fail(f"memory file does not exist: {target}; use record for new memory files", args.json)
    text = read_stdin(require=True)
    result = rewrite_file_atomic(target, text, args.expected_sha256)
    if result["changed"]:
        rebuild_content(mem_path)
    return {"ok": True, "action": "rewrite", "mem_path": str(mem_path), "task": task_name, "file": str(target), "relative_path": str(target.relative_to(mem_path)), **result, "warnings": warnings}


def command_record_global(args: argparse.Namespace) -> Dict[str, Any]:
    mem_path, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem_path, create=True)
    text = read_stdin(require=args.stdin)
    if not text:
        fail("no global memory text provided on stdin", args.json)
    target = safe_child(mem_path, "global.md")
    append_block(target, text, args.title)
    rebuild_content(mem_path)
    return {"ok": True, "action": "record-global", "mem_path": str(mem_path), "file": str(target), "relative_path": "global.md", "bytes_appended": len(text.encode("utf-8")), "warnings": warnings}


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
    return {"ok": True, "action": "rewrite-global", "mem_path": str(mem_path), "file": str(target), "relative_path": "global.md", **result, "warnings": warnings}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=f"Manage the initialized external {EDITION_ID} Mem folder.")
    parser.add_argument("--json", action="store_true", help="emit machine-readable JSON where supported")
    sub = parser.add_subparsers(dest="command", required=True)

    def add_json_flag(subparser: argparse.ArgumentParser) -> None:
        subparser.add_argument("--json", action="store_true", default=argparse.SUPPRESS, help="emit machine-readable JSON")

    p = sub.add_parser("init-status", help="check whether this installed skill has a valid selected external Mem folder")
    add_json_flag(p)
    p.set_defaults(func=command_init_status)

    p = sub.add_parser("scan", help="list only direct child Mem folders under a confirmed parent directory")
    add_json_flag(p)
    p.add_argument("--parent", required=True, help="confirmed parent directory; scan never recurses")
    p.set_defaults(func=command_scan)

    p = sub.add_parser("name-info", help="validate an xxx-yyy-mem name and show its derived browser port/profile name")
    add_json_flag(p)
    p.add_argument("--name", required=True)
    p.set_defaults(func=command_name_info)

    p = sub.add_parser("self-check", help="check Python environment and initialization state")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional candidate path to validate without selecting it")
    p.set_defaults(func=command_self_check)

    p = sub.add_parser("init", help="create/attach an external Mem folder and make it the selected Mem/profile")
    add_json_flag(p)
    p.add_argument("--mem-path", required=True, help="exact external Mem path named xxx-yyy-mem")
    p.add_argument("--accept-risk", action="store_true", help="confirm the user chose to continue after the safety warning")
    p.set_defaults(func=command_init)

    p = sub.add_parser("check", help="check the selected Mem folder structure")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--create-missing", action="store_true", help="repair missing required files/profile after path selection")
    p.set_defaults(func=command_check)

    p = sub.add_parser("rebuild-content", help="refresh content.md from memory files while excluding the browser profile")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.set_defaults(func=command_rebuild_content)

    p = sub.add_parser("list", help="list task folders, excluding the browser profile")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.set_defaults(func=command_list)

    p = sub.add_parser("search", help="search markdown/text memory files, never browser profile data")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--query", required=True, help="search query for a clear concrete task")
    p.add_argument("--limit", type=int, default=10, help="maximum matches to return")
    p.set_defaults(func=command_search)

    p = sub.add_parser("read", help="read global/content memory or one task folder")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--scope", choices=("global", "content"), help="read global.md or content.md")
    p.add_argument("--task", help="task folder name to read")
    p.add_argument("--file", help="single file inside the task folder")
    p.set_defaults(func=command_read)

    p = sub.add_parser("record", help="append task memory from stdin")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--task", required=True, help="task folder name")
    p.add_argument("--file", default="memory.md", help="markdown file inside the task folder")
    p.add_argument("--title", help="heading for this memory block")
    p.add_argument("--stdin", action="store_true", help="read memory markdown from stdin")
    p.set_defaults(func=command_record)

    p = sub.add_parser("rewrite", help="atomically replace one existing task memory file with a reconciled version")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--task", required=True, help="existing task folder name")
    p.add_argument("--file", default="memory.md", help="existing markdown/text file inside the task folder")
    p.add_argument("--expected-sha256", help="optional SHA-256 from the last read; refuse overwrite if the file changed")
    p.add_argument("--stdin", action="store_true", help="read the complete reconciled file from stdin")
    p.set_defaults(func=command_rewrite)

    p = sub.add_parser("record-global", help="append global memory from stdin")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--title", help="heading for this global memory block")
    p.add_argument("--stdin", action="store_true", help="read memory markdown from stdin")
    p.set_defaults(func=command_record_global)

    p = sub.add_parser("rewrite-global", help="atomically replace global.md with a reconciled version")
    add_json_flag(p)
    p.add_argument("--mem-path", help="optional exact selected Mem path; must match initialization")
    p.add_argument("--expected-sha256", help="optional SHA-256 from the last read; refuse overwrite if the file changed")
    p.add_argument("--stdin", action="store_true", help="read the complete reconciled global.md from stdin")
    p.set_defaults(func=command_rewrite_global)
    return parser


def main() -> None:
    configure_utf8_stdio()
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = args.func(args)
    except Exception as exc:
        fail(str(exc), getattr(args, "json", False))
    if result is None:
        return
    if getattr(args, "json", False):
        json_print(result)
    else:
        action = result.get("action", args.command)
        print(f"{action}: {'ok' if result.get('ok', False) else 'not ok'}")
        if "mem_path" in result:
            print(f"mem_path: {result['mem_path']}")
        for warning in result.get("warnings", []):
            print(f"warning: {warning}")


if __name__ == "__main__":
    main()
