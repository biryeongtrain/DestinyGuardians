import base64
import io
import unittest

import numpy as np
from PIL import Image

from skiff_fx import linear, split_fx, straight_alpha


class SkiffFxTest(unittest.TestCase):
    def test_radiance_survives_quantization_over_black(self):
        random = np.random.default_rng(26)
        source = random.integers(0, 256, (4096, 4), dtype=np.uint8)
        source[:, 3] = 255
        result = straight_alpha(source)
        reconstructed = linear(result[:, :3]) * result[:, 3, None] / 255
        self.assertLess(np.max(np.abs(reconstructed - linear(source[:, :3]))), .007)
        self.assertTrue(np.any((result[:, 3] > 0) & (result[:, 3] < 255)))
        np.testing.assert_array_equal(straight_alpha(np.zeros((2, 4), np.uint8)), 0)

    def test_dim_emission_survives_native_alpha_cutoff_without_brightening(self):
        source = np.array([[17, 1, 0, 255], [32, 12, 3, 255], [0, 0, 0, 255]], np.uint8)
        converted = straight_alpha(source)
        self.assertTrue(np.all(converted[:2,3] / 255 > .1))
        self.assertEqual(converted[2,3], 0)
        reconstructed = linear(converted[:2,:3]) * converted[:2,3,None] / 255
        np.testing.assert_allclose(reconstructed, linear(source[:2,:3]), atol=.0005)

    def test_fx_split_preserves_hull_and_input(self):
        pixels = np.array([[[12, 42, 90, 255], [200, 100, 30, 255]]], np.uint8)
        buf = io.BytesIO()
        Image.fromarray(pixels).save(buf, format='PNG')
        texture = dict(source='data:image/png;base64,' + base64.b64encode(buf.getvalue()).decode(), width=2, height=1)
        model = dict(textures=[texture], elements=[
            dict(name='hull_north_0', faces={'north': dict(uv=[0, 0, 1, 1], texture=0)}),
            dict(name='lamp_glow_north_0', faces={'north': dict(uv=[1, 0, 2, 1], texture=0)})])
        result, report = split_fx(model)
        def decode(t):
            return np.asarray(Image.open(io.BytesIO(base64.b64decode(t['source'].split(',')[1]))))
        np.testing.assert_array_equal(decode(result['textures'][0])[0, 0], pixels[0, 0])
        np.testing.assert_array_equal(decode(result['textures'][0])[0, 1], 0)
        fx = decode(result['textures'][1])
        x0,y0,x1,y1 = result['elements'][1]['faces']['north']['uv']
        np.testing.assert_array_equal(fx[y0:y1,x0:x1], straight_alpha(pixels[:,1:2]))
        self.assertEqual(np.count_nonzero(fx[...,3]), 1)
        np.testing.assert_array_equal(decode(model['textures'][0]), pixels)
        self.assertEqual(result['elements'][1]['faces']['north']['texture'], 1)
        self.assertEqual(model['elements'][1]['faces']['north']['texture'], 0)
        self.assertEqual(report['faces'], 1)


if __name__ == '__main__':
    unittest.main()
