"""Shell camera framing must remain continuous across repeated insert phases."""
from pathlib import Path
import sys
import unittest
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from first_person_framing_w205 import reload_camera_lift


class ShellReloadFraming(unittest.TestCase):
    def test_repeated_shells_keep_the_same_visible_handling_height(self):
        settings = {'reloadCameraLift': 7}
        height = reload_camera_lift(settings, 1, 'initial')
        self.assertGreater(height, 0)
        for phase, p in [('loop', 0), ('loop', .5), ('loop', 1), ('return', 0)]:
            self.assertEqual(height, reload_camera_lift(settings, p, phase))

    def test_enter_and_return_join_canonical_without_height_pop(self):
        settings = {'reloadCameraLift': 7}
        for phase, p in [('initial', 0), ('return', 1)]:
            self.assertEqual(0, reload_camera_lift(settings, p, phase))
        for phase, p in [('initial', 1e-7), ('return', 1-1e-7)]:
            self.assertLess(abs(reload_camera_lift(settings, p, phase)), 1e-9)

    def test_idle_ads_and_non_opted_in_weapons_stay_unchanged(self):
        for phase in (None, 'initial', 'loop', 'return'):
            self.assertEqual(0, reload_camera_lift({}, .5, phase))
            self.assertEqual(0, reload_camera_lift({'reloadCameraLift': 7}, None, phase))


if __name__ == '__main__':
    unittest.main()
