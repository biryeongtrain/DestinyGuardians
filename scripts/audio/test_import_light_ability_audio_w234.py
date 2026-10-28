#!/usr/bin/env python3
"""Regression for replacing an ability clip without dropping accessibility metadata."""
import importlib.util
from pathlib import Path
import unittest

spec=importlib.util.spec_from_file_location("light_import",Path(__file__).with_name("import_light_ability_audio.py"))
module=importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

class LightAudioMetadataTest(unittest.TestCase):
    def test_replacement_preserves_subtitle_and_does_not_mutate_previous(self):
        old={"subtitle":"subtitles.destiny.hunter.arc.super.fire","sounds":[{"name":"destiny:old"}]}
        result=module.sound_definition("light_w233/80d643e7",old)
        self.assertEqual(old["subtitle"],result["subtitle"])
        self.assertEqual("destiny:light_w233/80d643e7",result["sounds"][0]["name"])
        self.assertEqual("destiny:old",old["sounds"][0]["name"])
        self.assertFalse(result["sounds"][0]["stream"])
        self.assertEqual(32,result["sounds"][0]["attenuation_distance"])

    def test_new_event_needs_no_invented_subtitle(self):
        self.assertEqual({"sounds":[{"name":"destiny:light_w233/example","stream":False,"attenuation_distance":32}]},module.sound_definition("light_w233/example",None))

if __name__=="__main__":unittest.main()
