#!/usr/bin/env python3
"""One bounded wait; the agent must inspect state before invoking again."""
from __future__ import annotations
import argparse
import json
import time


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Wait exactly two seconds, then inspect the actual state before repeating.')
    parser.add_argument('--json', action='store_true')
    args = parser.parse_args(argv)
    time.sleep(2.0)
    result = {'ok': True, 'waited_seconds': 2.0, 'next': 'Inspect the page or GUI state; do not assume the task has finished.'}
    print(json.dumps(result) if args.json else result['next'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
