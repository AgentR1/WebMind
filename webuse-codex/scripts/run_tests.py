#!/usr/bin/env python3
"""Run all code-only tests, or explicitly opt into isolated browser tests."""
from __future__ import annotations
import argparse
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--browser', action='store_true', help='Also launch a disposable headless local browser (no real accounts)')
    parser.add_argument('--report', type=Path, help='Optional JSON report path')
    args = parser.parse_args()
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    directories = sorted((ROOT/'components').glob('*/tests')) + [ROOT/'tests']
    if args.browser:
        directories += [ROOT/'components/webuse-cdp/tests/browser']
    for directory in directories:
        sys.path.insert(0, str(directory))
        # A fresh loader avoids unittest's sticky top-level directory setting.
        suite.addTests(unittest.TestLoader().discover(str(directory), 'test_*.py', str(directory)))
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {'successful': result.wasSuccessful(), 'tests_run': result.testsRun,
              'passed': result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),
              'failures': len(result.failures), 'errors': len(result.errors),
              'skipped': len(result.skipped), 'skip_reasons': [reason for _, reason in result.skipped],
              'browser_tests_requested': args.browser, 'platform': sys.platform,
              'python': sys.version, 'native_desktop_tested': False}
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    return 0 if result.wasSuccessful() else 1


if __name__ == '__main__':
    raise SystemExit(main())
