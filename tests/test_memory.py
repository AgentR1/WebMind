"""Memory CLI regressions use temporary folders, never personal experience data."""

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'webmind_memory.py'


class MemoryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='webmind-memory-test-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()
        self.mem = self.root / 'Mem'

    def cli(self, *args, text=None, ok=True, mem=True, env=None):
        command = [sys.executable, '-B', str(SCRIPT), *args]
        if mem:
            command += ['--mem-path', str(self.mem)]
        command.append('--json')
        process = subprocess.run(command, input=text, capture_output=True, encoding='utf-8',
                                 timeout=10, env=env)
        self.assertEqual(process.returncode, 0 if ok else 1, process.stderr or process.stdout)
        output = json.loads(process.stdout)
        self.assertEqual(output['ok'], ok, output)
        return output

    def test_default_env_and_explicit_path_precedence_without_initialization(self):
        env = dict(os.environ)
        env.pop('WEBMIND_MEM', None)
        default = self.cli('self-check', mem=False, env=env)
        self.assertEqual(Path(default['mem_path']), Path.home() / '.local/share/webmind/Mem')
        env['WEBMIND_MEM'] = str(self.root / 'environment' / 'Mem')
        override = self.cli('self-check', mem=False, env=env)
        self.assertEqual(Path(override['mem_path']), self.root / 'environment' / 'Mem')
        explicit = self.cli('self-check', env=env)
        self.assertEqual(Path(explicit['mem_path']), self.mem)
        self.assertFalse(self.mem.exists())

    def test_init_check_and_rebuild_are_compatible_with_mem_layout(self):
        self.cli('init')
        self.assertTrue((self.mem / 'global.md').is_file())
        self.assertTrue((self.mem / 'content.md').is_file())
        self.cli('check')
        (self.mem / 'legacy-task').mkdir()
        (self.mem / 'legacy-task' / 'flow.md').write_text('# 已有流程\n观察、操作、验证。', encoding='utf-8')
        rebuilt = self.cli('rebuild-content')
        self.assertEqual(rebuilt['tasks'][0]['name'], 'legacy-task')
        self.assertIn('legacy-task', (self.mem / 'content.md').read_text(encoding='utf-8'))
        self.assertIn('已有流程', self.cli('read', '--task', 'legacy-task')['files'][0]['text'])

    def test_readonly_commands_do_not_create_missing_memory(self):
        for args in [('check',), ('list',), ('search', '--query', '任务'), ('read', '--scope', 'global')]:
            with self.subTest(args=args):
                self.cli(*args, ok=False)
                self.assertFalse(self.mem.exists())

    def test_check_can_explicitly_repair_index_without_replacing_global(self):
        self.cli('init')
        original = (self.mem / 'global.md').read_text(encoding='utf-8')
        (self.mem / 'content.md').unlink()
        self.cli('check', ok=False)
        self.assertFalse((self.mem / 'content.md').exists())
        self.cli('check', '--create-missing')
        self.assertTrue((self.mem / 'content.md').is_file())
        self.assertEqual((self.mem / 'global.md').read_text(encoding='utf-8'), original)

    def test_record_chinese_text_updates_index_and_search(self):
        text = '先等待正文元素出现，再读取完整内容。中文 🌐'
        record = self.cli('record', '--task', '网页阅读', '--title', '动态页面', '--stdin', text=text)
        self.assertEqual(record['relative_path'], '网页阅读/memory.md')
        read = self.cli('read', '--task', '网页阅读', '--file', 'memory.md')
        self.assertIn(text, read['files'][0]['text'])
        self.assertIn('status: candidate', read['files'][0]['text'])
        self.assertEqual(self.cli('list')['tasks'][0]['name'], '网页阅读')
        hits = self.cli('search', '--query', '正文元素')['matches']
        self.assertTrue(any(hit['relative_path'] == '网页阅读/memory.md' for hit in hits))
        self.assertIn('网页阅读', self.cli('read', '--scope', 'content')['files'][0]['text'])

    def test_global_record_appends_without_replacing_existing_memory(self):
        self.cli('init')
        before = (self.mem / 'global.md').read_text(encoding='utf-8')
        self.cli('record-global', '--title', '跨任务规则', '--stdin', text='完成操作后读取可观察结果。')
        after = self.cli('read', '--scope', 'global')['files'][0]['text']
        self.assertTrue(after.startswith(before))
        self.assertIn('完成操作后读取可观察结果。', after)

    def test_empty_record_input_does_not_create_directory(self):
        self.cli('record', '--task', 'empty', '--stdin', text='', ok=False)
        self.assertFalse(self.mem.exists())

    def test_record_metadata_requires_evidence_for_verified_claim(self):
        self.cli('record', '--task', 'page', '--status', 'verified', '--stdin', text='claim', ok=False)
        self.assertFalse(self.mem.exists())
        self.cli('record', '--task', 'page', '--status', 'verified', '--verified-on', '2026-09-05',
                 '--evidence', 'isolated fixture: read after click', '--expires-on', '2026-10-05',
                 '--stdin', text='Observable result checked.')
        text = self.cli('read', '--task', 'page')['files'][0]['text']
        self.assertIn('status: verified', text)
        self.assertIn('verified_on: 2026-09-05', text)
        self.assertIn('expires_on: 2026-10-05', text)

    def test_missing_requested_file_fails(self):
        self.cli('init')
        self.cli('record', '--task', 'page', '--stdin', text='candidate')
        self.cli('read', '--task', 'page', '--file', 'absent.md', ok=False)

    def test_task_and_file_traversal_are_rejected(self):
        self.cli('init')
        for task in ('../outside', '/absolute', '..', 'x/y', 'x\\y'):
            with self.subTest(task=task):
                self.cli('record', '--task', task, '--stdin', text='must stay inside', ok=False)
        for filename in ('../outside.md', '/outside.md', '..', 'sub/file.md', 'sub\\file.md'):
            with self.subTest(filename=filename):
                self.cli('record', '--task', 'safe', '--file', filename, '--stdin', text='no', ok=False)
        self.assertFalse((self.root / 'outside.md').exists())

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_global_file_cannot_be_read_or_written(self):
        self.cli('init')
        external = self.root / 'private.md'
        external.write_text('PRIVATE_CONTENT', encoding='utf-8')
        (self.mem / 'global.md').unlink()
        try:
            (self.mem / 'global.md').symlink_to(external)
        except OSError as exc:
            self.skipTest(f'symlinks unavailable: {exc}')
        self.cli('read', '--scope', 'global', ok=False)
        self.cli('record-global', '--stdin', text='must not append', ok=False)
        self.assertEqual(external.read_text(encoding='utf-8'), 'PRIVATE_CONTENT')

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_task_is_skipped_in_search_and_cannot_be_read_or_written(self):
        self.cli('init')
        external = self.root / 'outside'
        external.mkdir()
        (external / 'memory.md').write_text('SECRET_OUTSIDE', encoding='utf-8')
        try:
            (self.mem / 'escape').symlink_to(external, target_is_directory=True)
        except OSError as exc:
            self.skipTest(f'symlinks unavailable: {exc}')
        self.cli('read', '--task', 'escape', ok=False)
        self.cli('record', '--task', 'escape', '--stdin', text='must not append', ok=False)
        self.assertEqual(self.cli('search', '--query', 'SECRET_OUTSIDE')['matches'], [])
        self.assertEqual(self.cli('list')['tasks'], [])
        self.cli('rebuild-content')
        self.assertNotIn('escape/', (self.mem / 'content.md').read_text(encoding='utf-8'))
        self.assertEqual((external / 'memory.md').read_text(encoding='utf-8'), 'SECRET_OUTSIDE')

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_index_cannot_overwrite_an_external_file(self):
        self.mem.mkdir()
        external = self.root / 'outside-index.md'
        external.write_text('KEEP', encoding='utf-8')
        try:
            (self.mem / 'content.md').symlink_to(external)
        except OSError as exc:
            self.skipTest(f'symlinks unavailable: {exc}')
        self.cli('init', ok=False)
        self.assertEqual(external.read_text(encoding='utf-8'), 'KEEP')
        self.assertFalse((self.mem / 'global.md').exists())

    @unittest.skipUnless(hasattr(os, 'symlink'), 'symlinks unavailable')
    def test_symlink_file_inside_regular_task_cannot_leak_or_append(self):
        self.cli('init')
        task = self.mem / 'page'
        task.mkdir()
        external = self.root / 'private-task.md'
        external.write_text('PRIVATE_TASK_CONTENT', encoding='utf-8')
        try:
            (task / 'notes.md').symlink_to(external)
        except OSError as exc:
            self.skipTest(f'symlinks unavailable: {exc}')
        self.cli('read', '--task', 'page', '--file', 'notes.md', ok=False)
        self.cli('record', '--task', 'page', '--file', 'notes.md', '--stdin', text='no', ok=False)
        self.assertEqual(self.cli('read', '--task', 'page')['files'], [])
        self.assertEqual(self.cli('search', '--query', 'PRIVATE_TASK_CONTENT')['matches'], [])
        self.assertEqual(external.read_text(encoding='utf-8'), 'PRIVATE_TASK_CONTENT')


if __name__ == '__main__':
    unittest.main()
