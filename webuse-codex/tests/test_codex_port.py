"""Portable regression tests for the Codex adapter and installer."""
from __future__ import annotations
import contextlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'scripts'))
import runtime
import install
import webuse
import webuse_wait


def module(name: str, relative: str):
    spec = importlib.util.spec_from_file_location(name, ROOT/relative)
    loaded = importlib.util.module_from_spec(spec)
    sys.modules[name] = loaded
    spec.loader.exec_module(loaded)
    return loaded


cdp = module('codex_port_cdp', 'components/webuse-cdp/scripts/webuse_cdp.py')
screenshot = module('codex_port_screenshot', 'components/webuse-screenshot/scripts/webuse_screenshot.py')


class RuntimeTests(unittest.TestCase):
    def test_windows_default_data_path(self):
        with patch.dict(os.environ, {'LOCALAPPDATA': '/users/example/local'}, clear=True), patch.object(runtime.platform, 'system', return_value='Windows'):
            self.assertEqual(runtime.default_data_dir(), Path('/users/example/local/WebUseCodex'))

    def test_macos_default_data_path(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(runtime.platform, 'system', return_value='Darwin'), patch.object(Path, 'home', return_value=Path('/Users/example')):
            self.assertEqual(runtime.default_data_dir(), Path('/Users/example/Library/Application Support/WebUseCodex'))

    def test_new_override_beats_legacy(self):
        with patch.dict(os.environ, {'WEBUSE_CODEX_DATA_DIR': '/new', 'WEBUSE_DATA_DIR': '/legacy'}):
            self.assertEqual(runtime.default_data_dir(), Path('/new').resolve())

    def test_custom_install_data_dir_persists(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            root = Path(temp)
            (root/runtime.INSTALL_MARKER).write_text(json.dumps({'name': 'webuse-codex', 'data_dir': str(root/'data')}))
            self.assertEqual(runtime.data_dir(root), root/'data')

    def test_bad_metadata_fails_closed(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/runtime.INSTALL_MARKER).write_text('{"name":"other"}')
            with self.assertRaises(ValueError):
                runtime.load_settings(root)

    def test_venv_paths_match_host(self):
        for system, suffix in [('Windows', 'Scripts/python.exe'), ('Darwin', 'bin/python')]:
            with self.subTest(system=system), patch.object(runtime.platform, 'system', return_value=system):
                self.assertEqual(runtime.venv_python(Path('/data')), Path('/data/.venv')/suffix)

    def test_wsl_is_rejected_with_native_guidance(self):
        with patch.object(runtime.platform, 'system', return_value='Linux'), patch.object(runtime.platform, 'release', return_value='microsoft-standard-WSL2'):
            with self.assertRaisesRegex(RuntimeError, 'native Windows PowerShell'):
                runtime.require_native_host()

    def test_private_windows_desktop_is_rejected(self):
        status = {'interactive_default_desktop': False, 'window_station': 'Sandbox', 'desktop': 'Private', 'help': 'Request approval.'}
        with patch.object(runtime, 'require_native_host'), patch.object(runtime.platform, 'system', return_value='Windows'), patch.object(runtime, 'windows_desktop', return_value=status):
            with self.assertRaisesRegex(RuntimeError, 'interactive Windows desktop'):
                runtime.gui_preflight('mouse')

    def test_macos_capture_and_input_permissions_are_separate(self):
        status = {'screen_recording': False, 'accessibility': True, 'help': 'Grant in settings.'}
        with patch.object(runtime, 'require_native_host'), patch.object(runtime.platform, 'system', return_value='Darwin'), patch.object(runtime, 'macos_permissions', return_value=status):
            runtime.gui_preflight('typing')
            with self.assertRaisesRegex(RuntimeError, 'screen_recording'):
                runtime.gui_preflight('screenshot')

    def test_macos_native_geometry_uses_points_and_negative_origin(self):
        bounds = {1: SimpleNamespace(origin=SimpleNamespace(x=0, y=0), size=SimpleNamespace(width=1440, height=900)),
                  2: SimpleNamespace(origin=SimpleNamespace(x=-1920, y=-100), size=SimpleNamespace(width=1920, height=1080))}
        quartz = SimpleNamespace(CGGetActiveDisplayList=lambda *a: (0, [1, 2], 2), CGDisplayBounds=lambda i: bounds[i])
        with patch.dict(sys.modules, {'Quartz': quartz}), patch.object(runtime.platform, 'system', return_value='Darwin'):
            result = runtime.native_desktop_geometry()
        self.assertEqual(result['rect'], {'left': -1920, 'top': -100, 'width': 3360, 'height': 1080})
        self.assertEqual(result['coordinate_space'], 'macos-logical-points')


class InstallerTests(unittest.TestCase):
    def make_source(self, base: Path) -> Path:
        source = base/'source'
        source.mkdir()
        (source/'SKILL.md').write_text('---\nname: webuse-codex\ndescription: local desktop\n---\n')
        (source/'script.py').write_text('print(1)\n')
        (source/'__pycache__').mkdir()
        (source/'__pycache__'/'x.pyc').write_bytes(b'cache')
        return source

    def test_copy_is_complete_and_caches_excluded(self):
        with tempfile.TemporaryDirectory() as temp:
            base = Path(temp)
            source = self.make_source(base)
            destination = base/'install'/'webuse-codex'
            install.install_copy(source, destination, {'name': 'webuse-codex'})
            self.assertTrue((destination/'SKILL.md').is_file())
            self.assertTrue((destination/'script.py').is_file())
            self.assertFalse((destination/'__pycache__').exists())
            self.assertTrue((source/'script.py').is_file())

    def test_unmanaged_directory_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); source=self.make_source(base); destination=base/'target'; destination.mkdir()
            (destination/'personal.txt').write_text('keep')
            with self.assertRaisesRegex(ValueError, 'unmanaged'):
                install.install_copy(source, destination, {'name': 'webuse-codex'})
            self.assertEqual((destination/'personal.txt').read_text(), 'keep')

    def test_upgrade_backup_is_outside_skills(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp); source=self.make_source(base); destination=base/'.agents/skills/webuse-codex'
            install.install_copy(source, destination, {'name': 'webuse-codex'})
            (destination/'personal.txt').write_text('keep')
            result=install.install_copy(source, destination, {'name': 'webuse-codex'})
            backup=Path(result['backup'])
            self.assertFalse(backup.is_relative_to(destination.parent))
            self.assertEqual((backup/'personal.txt').read_text(), 'keep')

    def test_in_place_install_does_not_erase_source(self):
        with tempfile.TemporaryDirectory() as temp:
            source=self.make_source(Path(temp))
            result=install.install_copy(source, source, {'name': 'webuse-codex'})
            self.assertTrue(result['in_place'])
            self.assertTrue((source/'script.py').is_file())

    def test_user_and_project_locations(self):
        with patch.object(Path, 'home', return_value=Path('/home/example')):
            self.assertEqual(install.target_path('user', None, None), Path('/home/example/.agents/skills/webuse-codex'))
        self.assertEqual(install.target_path('project', Path('/project'), None), Path('/project/.agents/skills/webuse-codex').resolve())

    def test_project_path_is_required(self):
        with self.assertRaises(ValueError):
            install.target_path('project', None, None)

    def test_opt_in_rules_preserve_existing_text_and_are_idempotent(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'AGENTS.md'; path.write_text('# Personal rules\nKeep this.\n')
            first=install.update_agent_rules(path, Path(temp)/'skill')
            first_text=path.read_text()
            second=install.update_agent_rules(path, Path(temp)/'skill')
            self.assertIn('Keep this.', first_text)
            self.assertEqual(path.read_text(), first_text)
            self.assertIsNotNone(first['backup'])
            self.assertIsNone(second['backup'])
            self.assertEqual(first_text.count(install.BEGIN), 1)

    def test_malformed_rules_are_never_rewritten(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'AGENTS.md'; old=install.BEGIN+'\nUnclosed'; path.write_text(old)
            with self.assertRaisesRegex(ValueError, 'Malformed'):
                install.update_agent_rules(path, Path('/skill'))
            self.assertEqual(path.read_text(), old)

    def test_install_dry_run_makes_no_destination(self):
        with tempfile.TemporaryDirectory() as temp, contextlib.redirect_stdout(io.StringIO()):
            parent=Path(temp)/'new'
            code=install.main(['--skills-dir',str(parent),'--dry-run','--skip-deps'])
            self.assertEqual(code,0)
            self.assertFalse(parent.exists())

    def test_upgrade_keeps_recorded_runtime_path(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {}, clear=True):
            base=Path(temp); destination=base/'skills'/'webuse-codex'
            destination.mkdir(parents=True)
            data=base/'existing data'
            (destination/runtime.INSTALL_MARKER).write_text(json.dumps({'name':'webuse-codex','data_dir':str(data)}),encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()) as output:
                code=install.main(['--skills-dir',str(destination.parent),'--skip-deps','--dry-run'])
            self.assertEqual(code,0)
            self.assertEqual(json.loads(output.getvalue())['data_dir'],str(data))
            self.assertFalse(data.exists())

    def test_real_file_only_install_and_unicode_launcher(self):
        with tempfile.TemporaryDirectory() as temp:
            base=Path(temp)/'spaces \u4e2d\u6587'
            skills=base/'skills'; data=base/'data'
            result=subprocess.run([sys.executable,'-B',str(ROOT/'scripts/install.py'),'--skip-deps','--skills-dir',str(skills),'--data-dir',str(data)],capture_output=True,text=True,encoding='utf-8',timeout=30)
            self.assertEqual(result.returncode,0,result.stderr)
            destination=skills/'webuse-codex'
            self.assertEqual(len(list(destination.rglob('SKILL.md'))),1)
            env=os.environ.copy()
            env.pop('WEBUSE_DATA_DIR',None); env.pop('WEBUSE_CODEX_DATA_DIR',None)
            bootstrap=destination/'scripts/bootstrap.py'
            result=subprocess.run([sys.executable,'-B',str(bootstrap),'mem','init','--json'],cwd=base,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertTrue((data/'Mem/global.md').is_file())
            note=base/'note.txt'; note.write_text('# Reusable\n\u4e2d\u6587\u7ecf\u9a8c\n',encoding='utf-8')
            result=subprocess.run([sys.executable,'-B',str(bootstrap),'mem','record','--task','Demo','--input-file',str(note),'--json'],cwd=base,env=env,capture_output=True,text=True,encoding='utf-8',timeout=30)
            self.assertEqual(result.returncode,0,result.stdout+result.stderr)
            self.assertIn('\u4e2d\u6587\u7ecf\u9a8c',(data/'Mem/Demo/memory.md').read_text(encoding='utf-8'))
            self.assertFalse((destination/'Mem').exists())


class InputAndDispatchTests(unittest.TestCase):
    def test_utf8_input_file_with_bom_is_decoded_without_loss(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'input.txt'; path.write_text('\u4e2d\u6587\n"quoted"',encoding='utf-8-sig')
            arguments,content=webuse.prepare_input('cdp',['fill','--selector','#message','--input-file',str(path)])
            self.assertIn('--text-stdin',arguments)
            self.assertNotIn('--input-file',arguments)
            self.assertEqual(content.decode(),'\u4e2d\u6587\n"quoted"')

    def test_cdp_global_option_values_are_not_subcommands(self):
        self.assertEqual(webuse._cdp_command(['--user-data-dir','fill','--no-auto-launch','eval']), 'eval')
        self.assertEqual(webuse._cdp_command(['--endpoint=http://127.0.0.1:9223','eval']), 'eval')

    def test_conflicting_stdin_and_file_are_rejected(self):
        with self.assertRaisesRegex(ValueError,'not both'):
            webuse.prepare_input('mem',['record','--stdin','--input-file','missing.txt'])

    def test_unsupported_input_command_is_rejected(self):
        with self.assertRaises(ValueError):
            webuse.prepare_input('mouse',['move-to','--input-file','missing.txt'])

    def test_missing_filename_is_rejected(self):
        with self.assertRaisesRegex(ValueError,'requires'):
            webuse.prepare_input('cdp',['eval','--input-file'])

    def test_cdp_stdin_expression_is_evaluated(self):
        args=cdp.build_parser().parse_args(['eval','--expression-stdin'])
        fake=SimpleNamespace(close=lambda:None)
        with patch.object(cdp,'connect_target',return_value=(fake,{'id':'test'})), patch.object(cdp.sys,'stdin',io.StringIO('1 + 2')), patch.object(cdp,'runtime_evaluate',return_value=3) as evaluate, patch.object(cdp,'maybe_accept_js_dialogs',return_value=[]):
            result=cdp.command_eval(args)
        self.assertEqual(result['value'],3)
        self.assertEqual(evaluate.call_args.args[1],'1 + 2')

    def test_two_second_wait_is_bounded(self):
        with patch.object(webuse_wait.time,'sleep') as sleep, contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(webuse_wait.main(['--json']),0)
            sleep.assert_called_once_with(2.0)

    def test_native_guard_errors_are_structured(self):
        stdout=io.StringIO()
        with patch.object(webuse,'require_native_host',side_effect=RuntimeError('native host required')), contextlib.redirect_stdout(stdout):
            code=webuse.main(['cdp','tabs','--json'])
        self.assertEqual(code,1)
        self.assertEqual(json.loads(stdout.getvalue()),{'ok':False,'error':'native host required'})

    def test_macos_browser_in_user_applications_is_found(self):
        wanted=Path('/Users/example/Applications/Google Chrome.app/Contents/MacOS/Google Chrome')
        with patch.dict(os.environ,{},clear=True), patch.object(cdp.platform,'system',return_value='Darwin'), patch.object(Path,'home',return_value=Path('/Users/example')), patch.object(cdp.shutil,'which',return_value=None), patch.object(Path,'is_file',lambda self:self==wanted):
            self.assertEqual(cdp.find_chrome_executable(),str(wanted))

    def test_browser_launch_refuses_nonloopback_bind(self):
        args=cdp.build_parser().parse_args(['--debug-address','0.0.0.0','launch'])
        with self.assertRaisesRegex(RuntimeError,'loopback'):
            cdp.launch_chrome(args)

    def test_retina_screenshot_reports_image_to_point_scale(self):
        from PIL import Image
        geometry=screenshot.DesktopInfo('mss',screenshot.Rect(-100,0,200,100),[])
        def capture(region,path,**kwargs):
            Image.new('RGB',(region.width*2,region.height*2)).save(path)
            return 'mss',False
        with tempfile.TemporaryDirectory() as temp, patch.object(screenshot.platform,'system',return_value='Darwin'), patch.object(screenshot,'read_resolution',return_value=geometry), patch.object(screenshot,'capture_rect',side_effect=capture), contextlib.redirect_stdout(io.StringIO()) as output:
            code=screenshot.main(['full','--no-cursor','--output',str(Path(temp)/'retina.png'),'--json'])
            result=json.loads(output.getvalue())
        self.assertEqual(code,0)
        self.assertEqual(result['image']['scale_x'],2)
        self.assertEqual(result['image']['scale_y'],2)
        self.assertEqual(result['desktop_coordinate_space'],'macos-logical-points')
        self.assertEqual(result['region']['left']+100/result['image']['scale_x'],-50)


class PackagingTests(unittest.TestCase):
    def test_exactly_one_discoverable_skill_and_no_legacy_plugin(self):
        self.assertEqual(list(ROOT.rglob('SKILL.md')),[ROOT/'SKILL.md'])
        self.assertFalse((ROOT/'.claude-plugin').exists())
        self.assertTrue((ROOT/'agents/openai.yaml').is_file())
        self.assertEqual(len(list((ROOT/'components').glob('*/GUIDE.md'))),6)

    def test_all_text_sources_use_utf8_and_lf(self):
        for path in ROOT.rglob('*'):
            if path.is_file() and path.suffix.lower() in {'.md','.py','.sh','.ps1','.yml','.yaml','.txt','.json'}:
                with self.subTest(path=str(path.relative_to(ROOT))):
                    data=path.read_bytes(); data.decode('utf-8')
                    self.assertFalse(data.startswith(b'\xef\xbb\xbf'))
                    self.assertNotIn(b'\r',data)
                    self.assertTrue(data.endswith(b'\n'))


if __name__ == '__main__':
    unittest.main()
