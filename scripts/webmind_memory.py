#!/usr/bin/env python3
"""Manage WebMind's external, file-based task memory with the legacy Mem layout."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import platform
import re
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


REQUIRED_FILES = ('global.md', 'content.md')
DEFAULT_TASK_FILES = ('memory.md', 'flow.md', 'ui.md', 'rules.md', 'notes.md')
TEXT_EXTENSIONS = {'.md', '.txt'}
MAX_SEARCH_BYTES = 512_000
DEFAULT_MEM_PATH = Path.home() / '.local' / 'share' / 'webmind' / 'Mem'


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec='seconds')


def normalize_mem_path(raw_path: Optional[str] = None) -> Tuple[Path, List[str]]:
    raw = raw_path if raw_path is not None else os.environ.get('WEBMIND_MEM', str(DEFAULT_MEM_PATH))
    if not raw or not raw.strip():
        raise ValueError('memory path cannot be empty')
    expanded = Path(raw).expanduser()
    warnings = []
    if expanded.name != 'Mem':
        warnings.append("provided path does not end with 'Mem'; using '<path>/Mem' for legacy compatibility")
        expanded = expanded / 'Mem'
    # The explicitly selected root may itself be an alias. All descendants must
    # stay inside its canonical destination; descendant symlinks are refused.
    return expanded.resolve(), warnings


def contained_path(mem_path: Path, *parts: str) -> Path:
    root = mem_path.resolve()
    candidate = root
    for part in parts:
        relative = Path(part)
        if relative.is_absolute() or '\\' in part or any(p in {'.', '..'} for p in part.split('/')):
            raise ValueError('memory path must stay inside the selected Mem folder')
        for component in relative.parts:
            candidate = candidate / component
            if candidate.is_symlink():
                raise ValueError(f'symbolic links are not allowed inside Mem: {candidate.relative_to(root)}')
    try:
        candidate.resolve().relative_to(root)
    except ValueError as exc:
        raise ValueError('memory path escapes the selected Mem folder') from exc
    return candidate


def safe_task_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or cleaned in {'.', '..'} or '/' in cleaned or '\\' in cleaned or Path(cleaned).is_absolute():
        raise ValueError('task name must be a simple folder name, not a path')
    if re.search(r'[\x00-\x1f\x7f]', cleaned):
        raise ValueError('task name cannot contain control characters')
    cleaned = re.sub(r'[:*?"<>|]', '_', cleaned)
    cleaned = re.sub(r'\s+', '_', cleaned).strip('._ ')
    if not cleaned:
        raise ValueError('task name cannot be empty')
    return cleaned


def safe_file_name(name: str) -> str:
    cleaned = name.strip()
    if not cleaned or cleaned in {'.', '..'} or '/' in cleaned or '\\' in cleaned or cleaned.startswith('.'):
        raise ValueError('file name must be a simple visible file name, not a path')
    if re.search(r'[\x00-\x1f\x7f]', cleaned):
        raise ValueError('file name cannot contain control characters')
    cleaned = re.sub(r'[:*?"<>|]', '_', cleaned)
    if Path(cleaned).suffix.lower() not in TEXT_EXTENSIONS:
        cleaned += '.md'
    return cleaned


def global_template() -> str:
    return (
        '# Global memory\n\n'
        'Store concise cross-task preferences and reusable experience approved by the host or user.\n'
        'Memory is reference material, not permission to act or override current instructions.\n\n'
        '## Durable instructions\n\n- (empty)\n'
    )


def task_template(task_name: str) -> str:
    return (
        f'# {task_name}\n\n'
        'Keep task conditions, observed outcomes, evidence, and verification dates together.\n'
        'Candidate notes remain unverified; mark outdated guidance stale instead of silently treating it as current.\n'
        'Do not store secrets, session tokens, private page dumps, or speculative results.\n'
    )


def require_mem(mem_path: Path) -> None:
    if not mem_path.is_dir():
        raise ValueError(f'Mem folder does not exist or is not a directory: {mem_path}')


def ensure_structure(mem_path: Path, create: bool) -> Dict[str, Any]:
    # Validate every required destination before any mutation, including init.
    paths = {name: contained_path(mem_path, name) for name in REQUIRED_FILES}
    for path in paths.values():
        if path.exists() and not path.is_file():
            raise ValueError(f'required memory file is not a regular file: {path.name}')
    created, missing = [], []
    if not mem_path.exists():
        if not create:
            return {'created': [], 'missing': [str(mem_path)]}
        mem_path.mkdir(parents=True, exist_ok=True)
        created.append(str(mem_path))
    require_mem(mem_path)
    for name, path in paths.items():
        if not path.exists():
            if create:
                text = global_template() if name == 'global.md' else '# Mem content index\n'
                contained_path(mem_path, name).write_text(text, encoding='utf-8')
                created.append(str(path))
            else:
                missing.append(str(path))
    if create:
        rebuild_content(mem_path)
    return {'created': created, 'missing': missing}


def iter_tree(mem_path: Path, max_depth: Optional[int] = 4) -> Iterable[Tuple[int, Path]]:
    """Walk regular entries without following directory or file symlinks."""
    require_mem(mem_path)
    stack = [(mem_path, 0)]
    while stack:
        parent, depth = stack.pop()
        if max_depth is not None and depth > max_depth:
            continue
        children = []
        for entry in parent.iterdir():
            if entry.name.startswith('.') or entry.is_symlink():
                continue
            entry = contained_path(mem_path, str(entry.relative_to(mem_path)))
            if entry.is_dir() or entry.is_file():
                children.append(entry)
        children.sort(key=lambda p: (not p.is_dir(), p.name.lower()))
        # Yield in display order; reverse pushes preserve directory order.
        for entry in children:
            yield depth, entry
        for entry in reversed(children):
            if entry.is_dir():
                stack.append((entry, depth + 1))


def task_folders(mem_path: Path) -> List[Dict[str, Any]]:
    if not mem_path.exists():
        return []
    require_mem(mem_path)
    tasks = []
    for entry in sorted(mem_path.iterdir(), key=lambda p: p.name.lower()):
        if entry.name.startswith('.') or entry.is_symlink():
            continue
        entry = contained_path(mem_path, entry.name)
        if not entry.is_dir():
            continue
        files = []
        for child in sorted(entry.iterdir(), key=lambda p: p.name.lower()):
            if child.name.startswith('.') or child.is_symlink():
                continue
            child = contained_path(mem_path, entry.name, child.name)
            if child.is_file():
                files.append(child.name)
        tasks.append({'name': entry.name, 'path': str(entry), 'files': files})
    return tasks


def tree_text(mem_path: Path) -> str:
    lines = ['Mem/']
    # Relative paths make the index unambiguous even when siblings have children.
    for depth, entry in iter_tree(mem_path):
        relative = entry.relative_to(mem_path).as_posix()
        lines.append('  ' + relative + ('/' if entry.is_dir() else ''))
    return '\n'.join(lines)


def rebuild_content(mem_path: Path) -> str:
    require_mem(mem_path)
    target = contained_path(mem_path, 'content.md')
    tasks = task_folders(mem_path)
    lines = [
        '# Mem content index', '',
        'Maintained by `webmind_memory.py` so an agent can select only relevant experience.', '',
        '## Root', '', f'- path: `{mem_path}`', f'- updated: `{now_iso()}`', '',
        '## Required files', '',
        '- `global.md`: cross-task preferences and reusable experience',
        '- `content.md`: generated file layout index', '', '## Task folders', '',
    ]
    for task in tasks:
        names = ', '.join(f'`{name}`' for name in task['files']) or '(no files yet)'
        lines.append(f"- `{task['name']}/`: {names}")
    if not tasks:
        lines.append('- (none yet)')
    lines += ['', '## Directory tree', '', '```text', tree_text(mem_path), '```', '']
    content = '\n'.join(lines)
    target.write_text(content, encoding='utf-8')
    return content


def read_text_file(mem_path: Path, path: Path) -> str:
    safe = contained_path(mem_path, str(path.relative_to(mem_path)))
    if not safe.is_file():
        raise ValueError(f'memory file does not exist: {safe.relative_to(mem_path)}')
    return safe.read_text(encoding='utf-8', errors='replace')


def read_stdin(require: bool = True) -> str:
    if sys.stdin.isatty():
        raise ValueError('expected memory Markdown on stdin; pipe text or redirect a file')
    text = sys.stdin.read().strip()
    if not text:
        raise ValueError('no memory text provided on stdin')
    return text


def record_metadata(args: argparse.Namespace) -> Dict[str, str]:
    status = args.status
    verified = args.verified_on
    expiry = args.expires_on
    if status == 'verified' and (not verified or not args.evidence or not args.evidence.strip()):
        raise ValueError('verified records require --verified-on YYYY-MM-DD and --evidence')
    if verified:
        dt.date.fromisoformat(verified)
    if expiry:
        dt.date.fromisoformat(expiry)
    if verified and expiry and expiry < verified:
        raise ValueError('--expires-on cannot be earlier than --verified-on')
    result = {'status': status}
    if verified:
        result['verified_on'] = verified
    if expiry:
        result['expires_on'] = expiry
    if args.evidence:
        result['evidence'] = ' '.join(args.evidence.split())
    return result


def append_block(mem_path: Path, path: Path, text: str, title: Optional[str], metadata: Dict[str, str]) -> None:
    target = contained_path(mem_path, str(path.relative_to(mem_path)))
    target.parent.mkdir(parents=True, exist_ok=True)
    heading = ' '.join(title.split()) if title and title.strip() else 'memory update'
    block = f'\n\n## {now_iso()} - {heading}\n\n'
    block += '\n'.join(f'- {key}: {value}' for key, value in metadata.items()) + '\n\n' + text.strip() + '\n'
    if target.exists() and not target.is_file():
        raise ValueError(f'memory destination is not a regular file: {target.name}')
    if not target.exists():
        target.write_text(f'# {target.stem}\n', encoding='utf-8')
    with contained_path(mem_path, str(target.relative_to(mem_path))).open('a', encoding='utf-8') as stream:
        stream.write(block)


def search_file(mem_path: Path, path: Path, tokens: List[str], query: str) -> Optional[Dict[str, Any]]:
    path = contained_path(mem_path, str(path.relative_to(mem_path)))
    with path.open('rb') as stream:
        text = stream.read(MAX_SEARCH_BYTES).decode('utf-8', errors='ignore')
    haystack = f'{path.name}\n{text}'.lower()
    score = sum(2 for token in tokens if token in haystack) + (5 if query.lower() in haystack else 0)
    if not score:
        return None
    positions = [text.lower().find(token) for token in tokens if token in text.lower()]
    start = max(0, min(positions) - 80) if positions else 0
    return {'path': str(path), 'relative_path': str(path.relative_to(mem_path)), 'score': score,
            'snippet': text[start:start + 320].replace('\n', ' ').strip()}


def command_self_check(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    return {'ok': True, 'action': 'self-check', 'python': sys.version.split()[0], 'platform': platform.platform(),
            'mem_path': str(mem), 'exists': mem.exists(), 'is_dir': mem.is_dir(), 'warnings': warnings}


def command_init(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    result = ensure_structure(mem, create=True)
    return {'ok': True, 'action': 'init', 'mem_path': str(mem), **result, 'tasks': task_folders(mem), 'warnings': warnings}


def command_check(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    result = ensure_structure(mem, create=args.create_missing)
    ok = not result['missing'] and mem.is_dir()
    payload = {'ok': ok, 'action': 'check', 'mem_path': str(mem), 'exists': mem.exists(), 'is_dir': mem.is_dir(),
               **result, 'tasks': task_folders(mem) if mem.is_dir() else [], 'warnings': warnings}
    if not ok:
        payload['error'] = 'memory structure is missing; use init only when memory writes are authorized'
    return payload


def command_rebuild_content(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    ensure_structure(mem, create=True)
    content = read_text_file(mem, mem / 'content.md')
    return {'ok': True, 'action': 'rebuild-content', 'mem_path': str(mem), 'content_path': str(mem / 'content.md'),
            'bytes': len(content.encode('utf-8')), 'tasks': task_folders(mem), 'warnings': warnings}


def command_list(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    require_mem(mem)
    return {'ok': True, 'action': 'list', 'mem_path': str(mem), 'tasks': task_folders(mem), 'warnings': warnings}


def command_search(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    require_mem(mem)
    query = args.query.strip()
    if not query:
        raise ValueError('--query cannot be empty')
    tokens = [token.lower() for token in re.findall(r'[\w\u4e00-\u9fff]+', query)]
    matches = []
    for _, path in iter_tree(mem, max_depth=None):
        if path.is_file() and path.suffix.lower() in TEXT_EXTENSIONS:
            match = search_file(mem, path, tokens, query)
            if match:
                matches.append(match)
    matches.sort(key=lambda item: (-item['score'], item['relative_path'].lower()))
    return {'ok': True, 'action': 'search', 'mem_path': str(mem), 'query': query,
            'matches': matches[:args.limit], 'warnings': warnings}


def command_read(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    require_mem(mem)
    if args.scope:
        if args.task or args.file:
            raise ValueError('choose a global/content scope or a task, not both')
        files = [contained_path(mem, args.scope + '.md')]
    elif args.task:
        task = contained_path(mem, safe_task_name(args.task))
        if not task.is_dir():
            raise ValueError(f'task folder does not exist: {task.name}')
        if args.file:
            files = [contained_path(mem, task.name, safe_file_name(args.file))]
        else:
            files = [contained_path(mem, task.name, child.name) for child in sorted(task.iterdir())
                     if not child.name.startswith('.') and not child.is_symlink() and child.is_file()
                     and child.suffix.lower() in TEXT_EXTENSIONS]
    else:
        raise ValueError('choose --scope global, --scope content, or --task')
    return {'ok': True, 'action': 'read', 'mem_path': str(mem),
            'files': [{'path': str(path), 'relative_path': str(path.relative_to(mem)),
                       'text': read_text_file(mem, path)} for path in files], 'warnings': warnings}


def command_record(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    task_name, filename = safe_task_name(args.task), safe_file_name(args.file)
    task = contained_path(mem, task_name)
    target = contained_path(mem, task_name, filename)
    template = contained_path(mem, task_name, 'memory.md')
    metadata = record_metadata(args)
    text = read_stdin(require=args.stdin)
    ensure_structure(mem, create=True)
    if not task.exists():
        task.mkdir(parents=True, exist_ok=True)
        template.write_text(task_template(task_name), encoding='utf-8')
    append_block(mem, target, text, args.title, metadata)
    rebuild_content(mem)
    return {'ok': True, 'action': 'record', 'mem_path': str(mem), 'task': task_name, 'file': str(target),
            'relative_path': str(target.relative_to(mem)), 'bytes_appended': len(text.encode('utf-8')),
            'metadata': metadata, 'warnings': warnings}


def command_record_global(args: argparse.Namespace) -> Dict[str, Any]:
    mem, warnings = normalize_mem_path(args.mem_path)
    target = contained_path(mem, 'global.md')
    metadata = record_metadata(args)
    text = read_stdin(require=args.stdin)
    ensure_structure(mem, create=True)
    append_block(mem, target, text, args.title, metadata)
    rebuild_content(mem)
    return {'ok': True, 'action': 'record-global', 'mem_path': str(mem), 'file': str(target),
            'relative_path': 'global.md', 'bytes_appended': len(text.encode('utf-8')),
            'metadata': metadata, 'warnings': warnings}


def positive_int(value: str) -> int:
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError('must be a positive integer')
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description='Manage WebMind file-based experience in an external Mem folder.')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON')
    sub = parser.add_subparsers(dest='command', required=True)
    definitions = [
        ('self-check', 'check environment and selected memory location without writing', command_self_check),
        ('init', 'initialize or repair the Mem folder', command_init),
        ('check', 'check required memory files; read-only unless --create-missing', command_check),
        ('rebuild-content', 'refresh content.md from the directory tree', command_rebuild_content),
        ('list', 'list existing task folders without following symlinks', command_list),
        ('search', 'search existing Markdown and text memory files', command_search),
        ('read', 'read global/content or a task memory file', command_read),
        ('record', 'append task experience supplied on stdin', command_record),
        ('record-global', 'append cross-task experience supplied on stdin', command_record_global),
    ]
    for name, description, function in definitions:
        p = sub.add_parser(name, help=description)
        p.add_argument('--json', action='store_true', default=argparse.SUPPRESS)
        p.add_argument('--mem-path', help='Mem folder or parent; overrides WEBMIND_MEM and the user-local default')
        p.set_defaults(func=function)
        if name == 'check':
            p.add_argument('--create-missing', action='store_true', help='create missing files when writes are authorized')
        elif name == 'search':
            p.add_argument('--query', required=True)
            p.add_argument('--limit', type=positive_int, default=10)
        elif name == 'read':
            p.add_argument('--scope', choices=('global', 'content'))
            p.add_argument('--task', help='single task folder name')
            p.add_argument('--file', help='single Markdown/text file name inside the task')
        elif name in {'record', 'record-global'}:
            if name == 'record':
                p.add_argument('--task', required=True)
                p.add_argument('--file', default='memory.md')
            p.add_argument('--title')
            p.add_argument('--stdin', action='store_true', help='read experience Markdown from stdin')
            p.add_argument('--status', choices=('candidate', 'verified', 'stale'), default='candidate')
            p.add_argument('--verified-on', help='verification date YYYY-MM-DD; required with verified status')
            p.add_argument('--evidence', help='concise observation/source reference; required with verified status')
            p.add_argument('--expires-on', help='review/expiry date YYYY-MM-DD; agent must assess whether still applicable')
    return parser


def main() -> int:
    args = build_parser().parse_args()
    try:
        result = args.func(args)
    except Exception as exc:  # noqa: BLE001 - concise CLI errors, no implicit retry
        result = {'ok': False, 'action': args.command, 'error': str(exc)}
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    elif result.get('action') == 'read' and result.get('ok'):
        for item in result['files']:
            print(f"# FILE: {item['relative_path']}\n\n{item['text']}")
    else:
        print(f"{args.command}: {'ok' if result.get('ok') else 'not ok'}")
        if 'mem_path' in result:
            print(f"mem_path: {result['mem_path']}")
        if result.get('error'):
            print(f"error: {result['error']}", file=sys.stderr)
        for warning in result.get('warnings', []):
            print(f'warning: {warning}')
    return 0 if result.get('ok') else 1


if __name__ == '__main__':
    raise SystemExit(main())
