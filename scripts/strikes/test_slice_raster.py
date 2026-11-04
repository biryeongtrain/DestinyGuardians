import unittest
import numpy as np
from slice_raster import raster_face, uncovered_cells


class SliceRasterTest(unittest.TestCase):
    def setUp(self):
        self.triangles = np.array([[[0, 0, 1], [2, 0, 3], [0, 2, 5]]], float)
        self.uvs = self.triangles[..., :2]/2
        self.axes = (2, 'min', (0, 1), -1, -1)

    def sample(self, index, uv):
        return np.column_stack([uv*100, np.full(len(uv), index)]), np.ones(len(uv), bool)

    def test_affine_depth_and_uv_at_exact_texel_centers(self):
        result = raster_face(self.triangles, self.uvs, 1, self.axes, self.sample)
        np.testing.assert_array_equal(result['gi'], [0, 0, 1])
        np.testing.assert_array_equal(result['gj'], [0, 1, 0])
        np.testing.assert_allclose(result['depth'], [2.5, 4.5, 3.5])
        np.testing.assert_allclose(result['rgb'][:, :2], [[25, 25], [25, 75], [75, 25]])

    def test_nearer_cutout_reveals_far_surface(self):
        near = self.triangles.copy(); near[..., 2] -= 10
        triangles = np.concatenate([near, self.triangles])
        uv = np.concatenate([self.uvs, self.uvs])
        def sample(index, uv):
            rgb, covered = self.sample(index, uv)
            if index == 0: covered &= uv[:, 0] > .5
            return rgb, covered
        result = raster_face(triangles, uv, 1, self.axes, sample)
        np.testing.assert_array_equal(result['triangle'], [1, 1, 0])
        np.testing.assert_allclose(result['depth'], [2.5, 4.5, -6.5])
        back = raster_face(triangles, uv, 1, (2, 'max', (0, 1), 1, -1), sample)
        np.testing.assert_array_equal(back['triangle'], [1, 1, 1])

    def test_shared_edge_and_coplanar_ties_are_deterministic(self):
        result = raster_face(np.repeat(self.triangles, 2, axis=0), np.repeat(self.uvs, 2, axis=0),
                             1, self.axes, self.sample)
        self.assertEqual(len(result['depth']), 3)
        np.testing.assert_array_equal(result['triangle'], 0)

    def test_degenerate_projection_is_empty(self):
        triangle = self.triangles.copy(); triangle[..., 1] = 0
        self.assertIsNone(raster_face(triangle, self.uvs, 1, self.axes, self.sample))

    def test_subtexel_fallback_does_not_replace_exact_center_hits(self):
        keep = uncovered_cells(np.array([0, 1, 2]), np.array([0, 0, -1]),
                               np.array([1, 2]), np.array([0, 0]))
        np.testing.assert_array_equal(keep, [True, False, True])


if __name__ == '__main__':
    unittest.main()
