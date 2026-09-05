"""Offline navigation, targeting, and action-result regressions (no browser launch)."""

import importlib.util
import io
import json
from pathlib import Path
import unittest
from unittest import mock


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'webmind.py'
spec = importlib.util.spec_from_file_location('webmind_navigation', SCRIPT)
webmind = importlib.util.module_from_spec(spec)
spec.loader.exec_module(webmind)
TAB = {'id': 'page', 'type': 'page', 'url': 'https://example.test/old',
       'title': 'Example', 'webSocketDebuggerUrl': 'ws://local/page'}


class FakeClient:
    def __init__(self, result, batches=(), same_document=None):
        self.result = result
        self.batches = list(batches)
        self.same_document = same_document
        self.navigated = False
        self.closed = False
        self.calls = []

    def call(self, method, params=None, timeout=None):
        self.calls.append((method, params))
        if method == 'Page.navigate':
            self.navigated = True
            return self.result
        if method == 'Runtime.evaluate':
            return {'result': {'value': self.same_document}}
        return {}

    def drain_events(self, seconds=0.5):
        if not self.navigated:
            return []
        return self.batches.pop(0) if self.batches else []

    def close(self):
        self.closed = True


def lifecycle(frame='frame', loader='new', name='load'):
    return {'method': 'Page.lifecycleEvent', 'params': {
        'frameId': frame, 'loaderId': loader, 'name': name,
    }}


class NavigationTests(unittest.TestCase):
    def test_cli_navigation_protocol_failures_preserve_status_and_exit_nonzero(self):
        for exc, status in [(TimeoutError('CDP response timed out'), 'timeout'),
                            (RuntimeError('Page.navigate protocol error'), 'failed')]:
            with self.subTest(status=status):
                client = FakeClient({})
                argv = ['webmind.py', '--json', 'navigate', '--target-id', 'page',
                        '--url', 'https://example.test/new']
                with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)), \
                        mock.patch.object(client, 'call', side_effect=exc), \
                        mock.patch('sys.argv', argv), \
                        mock.patch('sys.stdout', new_callable=io.StringIO) as stdout:
                    exit_code = webmind.main()
                output = json.loads(stdout.getvalue())
                self.assertEqual(exit_code, 1)
                self.assertFalse(output['ok'])
                self.assertEqual(output['action'], 'navigate')
                self.assertEqual(output['status'], status)
                self.assertEqual(output['url'], 'https://example.test/new')
                self.assertFalse(output['outcome_verified'])
                self.assertFalse(output['load_event_seen'])
                self.assertTrue(client.closed)

    def test_same_document_url_check_timeout_keeps_navigation_result(self):
        client = FakeClient({'frameId': 'frame'})
        args = webmind.build_parser().parse_args([
            'navigate', '--target-id', 'page', '--url', 'https://example.test/new', '--wait-load',
        ])
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)), \
                mock.patch.object(webmind, 'runtime_evaluate', side_effect=TimeoutError('URL check timed out')):
            output = webmind.command_navigate(args)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'timeout')
        self.assertEqual(output['result'], {'frameId': 'frame'})
        self.assertIn('URL check', output['error'])

    def navigate(self, result, batches=(), wait=True, same_document=None):
        client = FakeClient(result, batches, same_document)
        argv = ['navigate', '--target-id', 'page', '--url', 'https://example.test/new',
                '--timeout', '0.01']
        if wait:
            argv.append('--wait-load')
        args = webmind.build_parser().parse_args(argv)
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)):
            output = webmind.command_navigate(args)
        self.assertTrue(client.closed)
        return output, client

    def test_navigation_error_is_failure_even_without_wait(self):
        output, _ = self.navigate({'frameId': 'frame', 'errorText': 'net::ERR_NAME_NOT_RESOLVED'}, wait=False)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'failed')
        self.assertIn('ERR_NAME_NOT_RESOLVED', output['error'])

    def test_download_is_not_successful_page_navigation(self):
        output, _ = self.navigate({'frameId': 'frame', 'isDownload': True}, wait=False)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'download')

    def test_unrelated_old_and_subframe_load_events_do_not_pass(self):
        output, _ = self.navigate({'frameId': 'frame', 'loaderId': 'new'}, [[
            {'method': 'Page.loadEventFired', 'params': {}},
            lifecycle(loader='old'), lifecycle(frame='child'),
        ]])
        self.assertFalse(output['ok'])
        self.assertFalse(output['load_event_seen'])
        self.assertEqual(output['status'], 'timeout')
        self.assertIn('error', output)

    def test_this_navigation_load_event_passes(self):
        output, client = self.navigate({'frameId': 'frame', 'loaderId': 'new'}, [[lifecycle()]])
        self.assertTrue(output['ok'])
        self.assertTrue(output['load_event_seen'])
        self.assertEqual(output['status'], 'loaded')
        self.assertFalse(output['outcome_verified'])
        self.assertIn(('Page.setLifecycleEventsEnabled', {'enabled': True}), client.calls)

    def test_no_wait_only_confirms_dispatch(self):
        output, _ = self.navigate({'frameId': 'frame', 'loaderId': 'new'}, wait=False)
        self.assertTrue(output['ok'])
        self.assertEqual(output['status'], 'dispatched')
        self.assertFalse(output['outcome_verified'])
        self.assertFalse(output['load_event_seen'])

    def test_same_document_navigation_checks_current_url(self):
        current = {'href': 'https://example.test/new', 'requested': 'https://example.test/new'}
        output, _ = self.navigate({'frameId': 'frame'}, same_document=current)
        self.assertTrue(output['ok'])
        self.assertEqual(output['status'], 'same-document')
        self.assertFalse(output['load_event_seen'])

    def test_missing_loader_and_wrong_url_do_not_claim_loaded(self):
        output, _ = self.navigate({'frameId': 'frame'}, same_document={
            'href': 'https://example.test/old', 'requested': 'https://example.test/new'})
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'timeout')


class TargetingTests(unittest.TestCase):
    def select(self, tabs, *filters):
        args = webmind.build_parser().parse_args(['eval', '--expression', '1', *filters])
        with mock.patch.object(webmind, 'ensure_endpoint'):
            with mock.patch.object(webmind, 'get_tabs', return_value=tabs):
                return webmind.select_tab(args)

    def test_never_falls_back_to_worker(self):
        with self.assertRaisesRegex(RuntimeError, 'page'):
            self.select([dict(TAB, type='service_worker')])

    def test_multiple_pages_require_disambiguation(self):
        with self.assertRaisesRegex(RuntimeError, 'ambiguous.*page.*second'):
            self.select([TAB, dict(TAB, id='second')])

    def test_multiple_url_matches_require_disambiguation(self):
        with self.assertRaisesRegex(RuntimeError, 'ambiguous'):
            self.select([TAB, dict(TAB, id='second')], '--url-contains', 'example')

    def test_url_and_title_filters_are_combined(self):
        selected = self.select([TAB, dict(TAB, id='second', title='Wanted')],
                               '--url-contains', 'EXAMPLE', '--title-contains', 'wanted')
        self.assertEqual(selected['id'], 'second')

    def test_nonmatching_combined_filters_fail(self):
        with self.assertRaisesRegex(RuntimeError, 'no page'):
            self.select([TAB, dict(TAB, id='second', url='https://other.test/', title='Wanted')],
                        '--url-contains', 'example', '--title-contains', 'wanted')


class ActionResultTests(unittest.TestCase):
    def test_insert_text_does_not_type_when_target_cannot_receive_focus(self):
        args = webmind.build_parser().parse_args([
            'insert-text', '--target-id', 'page', '--selector', '#disabled', '--text', 'must not leak',
        ])
        client = FakeClient({})
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)):
            with mock.patch.object(webmind, 'runtime_evaluate', side_effect=[
                {'ok': True, 'point': {'x': 10, 'y': 20}},
                {'ok': False, 'error': 'target did not receive focus'},
            ]):
                output = webmind.command_insert_text(args)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'failed')
        self.assertIn('focus', output['error'])
        self.assertFalse(any(method == 'Input.insertText' for method, _ in client.calls))

    def test_successful_mouse_dispatch_is_not_verified_outcome(self):
        args = webmind.build_parser().parse_args(['click', '--target-id', 'page', '--selector', '#submit'])
        client = FakeClient({})
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)):
            with mock.patch.object(webmind, 'runtime_evaluate', return_value={'ok': True, 'point': {'x': 10, 'y': 20}}):
                output = webmind.command_click(args)
        self.assertEqual(output['status'], 'dispatched')
        self.assertFalse(output['outcome_verified'])

    def test_rejected_click_does_not_send_mouse_events(self):
        args = webmind.build_parser().parse_args(['click', '--target-id', 'page', '--selector', '#submit'])
        client = FakeClient({})
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)):
            with mock.patch.object(webmind, 'runtime_evaluate', return_value={'ok': False, 'error': 'element is covered'}):
                output = webmind.command_click(args)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'failed')
        self.assertIn('covered', output['error'])
        self.assertFalse(any(method.startswith('Input.') for method, _ in client.calls))

    def test_failed_fill_verification_is_not_success(self):
        args = webmind.build_parser().parse_args(['fill', '--target-id', 'page', '--selector', '#query', '--text', 'x'])
        client = FakeClient({})
        with mock.patch.object(webmind, 'connect_target', return_value=(client, TAB)):
            with mock.patch.object(webmind, 'runtime_evaluate', return_value={
                'ok': False, 'error': 'field value did not match', 'immediate_value_verified': False}):
                output = webmind.command_fill(args)
        self.assertFalse(output['ok'])
        self.assertEqual(output['status'], 'failed')
        self.assertFalse(output['outcome_verified'])
        self.assertIn('error', output)


class ReadPageTests(unittest.TestCase):
    def test_read_page_exposes_bounded_extraction_options(self):
        args = webmind.build_parser().parse_args([
            'read-page', '--target-id', 'page', '--selector', 'article',
            '--wait-selector', 'article.loaded', '--max-chars', '700', '--max-links', '0',
        ])
        self.assertEqual(args.max_chars, 700)
        self.assertEqual(args.max_links, 0)
        self.assertEqual(args.wait_selector, 'article.loaded')

    def test_read_page_rejects_nonpositive_limits_and_timeout(self):
        for arguments in (['--max-chars', '0'], ['--max-links', '-1'], ['--timeout', '0'],
                          ['--timeout', 'nan'], ['--timeout', 'inf']):
            with self.subTest(arguments=arguments), mock.patch('sys.stderr', new_callable=io.StringIO), self.assertRaises(SystemExit):
                webmind.build_parser().parse_args(['read-page', '--target-id', 'page', *arguments])


if __name__ == '__main__':
    unittest.main()
