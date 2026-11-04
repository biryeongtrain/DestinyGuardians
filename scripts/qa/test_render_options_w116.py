import importlib.util
import unittest
import hashlib,json,tempfile
from unittest.mock import patch
from pathlib import Path

spec=importlib.util.spec_from_file_location('render_options',Path(__file__).with_name('configure_render_options_w116.py'))
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
SOURCE='version:5023\nenableVsync:false\nmaxFps:120\ninactivityFpsLimit:"afk"\nkey_key.use:key.mouse.right\n'

class RenderOptionsTests(unittest.TestCase):
    def test_only_the_intended_idle_setting_changes_for_saved_profile(self):
        self.assertEqual(SOURCE.replace('"afk"','"minimized"'),m.controlled_options(SOURCE))
    def test_other_controls_and_render_settings_are_preserved(self):
        text=SOURCE+'gamma:0.5\nfov:0.0\nrenderDistance:4\n'
        self.assertEqual(text.replace('"afk"','"minimized"'),m.controlled_options(text))
    def test_fixed_fps_and_vsync_are_explicit(self):
        text=SOURCE.replace('maxFps:120','maxFps:260').replace('enableVsync:false','enableVsync:true')
        self.assertEqual(SOURCE.replace('"afk"','"minimized"'),m.controlled_options(text))
    def test_no_trailing_newline_or_crlf_rewrite(self):
        for text in (SOURCE.rstrip('\n'),SOURCE.replace('\n','\r\n')):
            self.assertEqual(text.replace('"afk"','"minimized"'),m.controlled_options(text))
    def test_missing_or_duplicate_controlled_keys_fail(self):
        for key in m.VALUES:
            line=next(x for x in SOURCE.splitlines(keepends=True) if x.startswith(key+':'))
            for text in (SOURCE.replace(line,''),SOURCE+line):
                with self.assertRaises(ValueError):m.controlled_options(text)
    def test_invalid_or_wrong_typed_values_fail(self):
        for value in ('true','"120"','0','null'):
            with self.assertRaises(ValueError):m.controlled_options(SOURCE.replace('maxFps:120','maxFps:'+value))
        with self.assertRaises(ValueError):m.controlled_options(SOURCE.replace('"afk"','"unknown"'))
        with self.assertRaises(ValueError):m.controlled_options(SOURCE.replace('enableVsync:false','enableVsync:"false"'))
    def test_both_real_vanilla_enum_values_are_supported(self):
        text=SOURCE.replace('"afk"','"minimized"')
        self.assertEqual(text,m.controlled_options(text))
    def test_nul_rejected(self):
        with self.assertRaises(ValueError):m.controlled_options(SOURCE+'\0')

class RenderOptionsFileTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.root=Path(self.temp.name).resolve()
        self.source=self.root/'saved/options.txt';self.source.parent.mkdir();self.source.write_text(SOURCE)
        (self.source.parent/'SHA256SUMS.json').write_text(json.dumps({'options.txt':hashlib.sha256(self.source.read_bytes()).hexdigest()}))
        self.destination=self.root/'owned/client-run/options.txt';self.destination.parent.mkdir(parents=True)
        self.marker=self.root/'owned/OWNER.json';self.marker.write_text('{"stage":"W116"}')
        self.mock=patch.multiple(m,SOURCE=self.source,DESTINATION=self.destination);self.mock.start()
    def tearDown(self):
        self.mock.stop();self.temp.cleanup()
    def test_prepares_new_profile_without_changing_saved_options(self):
        old=self.source.read_bytes();result=m.prepare()
        self.assertEqual(old,self.source.read_bytes())
        self.assertEqual(m.controlled_options(SOURCE),self.destination.read_text())
        self.assertEqual(hashlib.sha256(self.destination.read_bytes()).hexdigest(),result['sha256'])
    def test_existing_profile_is_never_overwritten(self):
        self.destination.write_text('user content')
        with self.assertRaises(FileExistsError):m.prepare()
        self.assertEqual('user content',self.destination.read_text())
    def test_saved_source_hash_drift_is_rejected(self):
        self.source.write_text(SOURCE+'new_option:1\n')
        with self.assertRaises(ValueError):m.prepare()
        self.assertFalse(self.destination.exists())
    def test_source_symlink_is_rejected(self):
        real=self.source.with_name('real.txt');self.source.rename(real);self.source.symlink_to(real)
        with self.assertRaises(ValueError):m.prepare()
        self.assertFalse(self.destination.exists())
    def test_marker_and_its_stage_are_required(self):
        for text in ('{}','{"stage":"W115"}'):
            self.marker.write_text(text)
            with self.assertRaises(ValueError):m.prepare()
        self.marker.unlink()
        with self.assertRaises(ValueError):m.prepare()
    def test_symlinked_destination_parent_and_marker_are_rejected(self):
        elsewhere=self.root/'elsewhere';elsewhere.mkdir();self.destination.parent.rmdir();self.destination.parent.symlink_to(elsewhere,target_is_directory=True)
        with self.assertRaises(ValueError):m.prepare()
        self.assertEqual([],list(elsewhere.iterdir()))
        self.destination.parent.unlink();self.destination.parent.mkdir()
        real=self.marker.with_name('other-owner.json');self.marker.rename(real);self.marker.symlink_to(real)
        with self.assertRaises(ValueError):m.prepare()

if __name__=='__main__':unittest.main(verbosity=2)
