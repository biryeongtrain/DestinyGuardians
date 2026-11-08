"""Regression for the map input that differs from the legacy preview GLBs."""
import importlib.util, json, math, struct, sys, tempfile, unittest
from pathlib import Path
import numpy as np

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/maps'))
import baked_source
spec=importlib.util.spec_from_file_location('rising_sampler',ROOT/'scripts/campaign/rising_maps.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


class BakedSourceTest(unittest.TestCase):
    def test_nonindexed_triangles_keep_source_axes_and_bake_uv(self):
        with tempfile.TemporaryDirectory() as tmp:
            pos=np.array([[10,20,-3],[11,20,-3],[10,21,-3]],'<f4')
            uv=np.array([[.2,.3],[.4,.3],[.2,.5]],'<f4');binary=pos.tobytes()+uv.tobytes()
            doc={'scenes':[{'nodes':[0]}], 'nodes':[{'rotation':[-math.sqrt(.5),0,0,math.sqrt(.5)],'children':[1]}, {'mesh':0,'translation':[5,6,7]}],
                 'meshes':[{'name':'terrain','extras':{'terrain':True},'primitives':[{'attributes':{'POSITION':0,'TEXCOORD_0':1},'material':0},{'attributes':{'POSITION':0,'TEXCOORD_0':1},'material':1}]}],
                 'accessors':[{'bufferView':0,'componentType':5126,'type':'VEC3','count':3,'min':[10,20,-3],'max':[11,21,-3]}, {'bufferView':1,'componentType':5126,'type':'VEC2','count':3}],
                 'bufferViews':[{'byteOffset':0},{'byteOffset':pos.nbytes}],
                 'materials':[{'extras':{'colorBakeQuality':'native_full_inputs'}},{'extras':{'colorBakeQuality':'forward_or_decal_requires_scene'}}]}
            js=json.dumps(doc).encode();js+=b' '*((-len(js))%4)
            path=Path(tmp)/'map.baked.glb';path.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)
            g=baked_source.load(path,m);prims=g.primitives(0)
            self.assertEqual(len(prims),1) # Effects do not become collision.
            np.testing.assert_array_equal(prims[0][2],[[0,1,2]])
            np.testing.assert_allclose(prims[0][1],uv)
            np.testing.assert_allclose(g.inst_min[0],[15,26,4]) # Root conversion was not applied twice.

    def test_baked_coverage_and_linear_color_sampling(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as tmp:
            path=Path(tmp)/'coverage.png'
            Image.fromarray(np.array([[[255,0,0,0],[128,64,32,255]]],np.uint8)).save(path)
            class G:
                nodes=[{'mesh':0}];inst_mat=[np.eye(4)];path=Path(tmp)/'map.glb'
                def primitives(self,mi):return [(np.array([[0,0,0],[1,0,0],[0,1,0]]),np.array([[0,0],[1,0],[1,0]]),np.array([[0,1,2]]),0)]
                def material_texture(self,mi):return 'coverage.png'
            pts,rgba,normals=baked_source.sample_instance(G(),0,np.array([-1,-1,-1]),np.array([2,2,2]),1,m)
            self.assertTrue(len(pts)>0)
            self.assertTrue((rgba[:,3]==1).all())
            np.testing.assert_allclose(rgba[:,:3],np.broadcast_to(baked_source.srgb_to_linear(np.array([128,64,32])/255),rgba[:,:3].shape),rtol=1e-5)
            self.assertTrue((normals==1).all())

    def test_linear_average_is_not_an_srgb_byte_average(self):
        self.assertAlmostEqual(float(baked_source.linear_to_srgb(.5)),.735356983,places=7)


if __name__=='__main__':unittest.main()
