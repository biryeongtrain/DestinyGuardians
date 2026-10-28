"""Tiny offline fixtures only. Run: python3 -B -m unittest discover -s scripts/tower -p test_voxelize.py -v"""
import gzip
import io
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest
import numpy as np
from PIL import Image
from tower_mesh import GLB, node_matrix, transform_bounds
from voxelize_courtyard import (main, voxelize, surface_cells, triangle_box_mask,
                                sample_uv, Materials, DEFAULT_PALETTE)
from export_schematic import read_vox, write_vox, write_schematic


def fixture(path, points=None, nodes=None, materials=None, uv=None, image=None, stride=False):
    points = np.asarray(points if points is not None else [[0,0,0],[4,0,0],[0,0,4]], dtype="<f4")
    index = np.arange(len(points), dtype="<u4")
    chunks, views, accessors = [], [], []
    def accessor(values, kind, component, bounds=False):
        offset = sum(map(len, chunks))
        if stride and kind == "VEC3":
            padded = np.zeros((len(values),4), dtype="<f4")
            padded[:,:3] = values
            data = padded.tobytes()
        else:
            data = values.tobytes()
        view = {"buffer":0,"byteOffset":offset,"byteLength":len(data)}
        if stride and kind == "VEC3":
            view["byteStride"] = 16
        views.append(view)
        chunks.append(data)
        acc = {"bufferView":len(views)-1,"componentType":component,"count":len(values),"type":kind}
        if bounds:
            acc.update(min=values.min(axis=0).tolist(),max=values.max(axis=0).tolist())
        accessors.append(acc)
        return len(accessors)-1
    pos = accessor(points,"VEC3",5126,True)
    idx = accessor(index,"SCALAR",5125)
    primitive = {"attributes":{"POSITION":pos},"indices":idx,"material":0}
    if uv is not None:
        primitive["attributes"]["TEXCOORD_0"] = accessor(np.asarray(uv,dtype="<f4"),"VEC2",5126)
    document = {"asset":{"version":"2.0"},"scene":0,"scenes":[{"nodes":[0]}],
                "nodes":nodes if nodes is not None else [{"mesh":0,"name":"fixture"}],
                "meshes":[{"name":"fixture_mesh","primitives":[primitive]}],
                "materials":materials if materials is not None else [{"name":"floor",
                    "pbrMetallicRoughness":{"baseColorFactor":[.2,.2,.2,1]}}],
                "buffers":[{"byteLength":sum(map(len,chunks))}],"bufferViews":views,"accessors":accessors}
    if image is not None:
        Image.fromarray(np.asarray(image,dtype=np.uint8)).save(path.parent/"texture.png")
        document.update(images=[{"uri":"texture.png"}],textures=[{"source":0}])
    body = json.dumps(document).encode()
    body += b" "*((-len(body))%4)
    binary = b"".join(chunks)
    binary += b"\0"*((-len(binary))%4)
    path.write_bytes(struct.pack("<4sII",b"glTF",2,12+8+len(body)+8+len(binary))+
                     struct.pack("<II",len(body),0x4e4f534a)+body+
                     struct.pack("<II",len(binary),0x004e4942)+binary)
    return path


def nbt_read(raw):
    stream = io.BytesIO(raw)
    def unpack(fmt):
        return struct.unpack(fmt,stream.read(struct.calcsize(fmt)))
    def string():
        n, = unpack(">H")
        return stream.read(n).decode()
    def payload(kind):
        if kind == 2: return unpack(">h")[0]
        if kind == 3: return unpack(">i")[0]
        if kind == 7:
            n, = unpack(">i")
            return stream.read(n)
        if kind == 9:
            subtype,n = unpack(">bi")
            return [payload(subtype) for _ in range(n)]
        if kind == 10:
            out = {}
            while True:
                subtype, = unpack(">b")
                if subtype == 0: return out
                name = string()
                out[name] = payload(subtype)
        if kind == 11:
            n, = unpack(">i")
            return list(unpack(">"+"i"*n))
        raise AssertionError(kind)
    kind, = unpack(">b")
    name = string()
    result = payload(kind)
    assert stream.read() == b""
    return name,result


class ConverterTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
    def tearDown(self):
        self.temp.cleanup()

    def test_hierarchy_root_axis_and_shared_instances(self):
        nodes = [{"rotation":[-math.sqrt(.5),0,0,math.sqrt(.5)],"children":[1,3]},
                 {"translation":[1,2,3],"children":[2]},
                 {"mesh":0,"scale":[2,2,2]}, {"mesh":0,"translation":[20,0,0]}]
        glb = GLB(fixture(self.root/"f.glb",nodes=nodes,stride=True))
        instances = list(glb.world_instances())
        self.assertEqual(len(instances),2)
        np.testing.assert_allclose(instances[0][2][:3,3],[1,3,-2],atol=1e-12)
        point = np.array([0,0,1,1])
        np.testing.assert_allclose((instances[0][2]@point)[:3],[1,5,-2],atol=1e-12)
        np.testing.assert_allclose(glb.accessor(0)[2],[0,0,4])
        xyz,_,_,stats,_ = voxelize(glb,[-1,-1,-12],[12,12,1],1,[0,0,0],progress=False)
        self.assertEqual(stats["instancesCulled"],1)
        self.assertLess(xyz[:,0].max(),12)

    def test_matrix_column_major_and_nonuniform_scale(self):
        expected = np.array([[2,0,0,7],[0,3,0,8],[0,0,4,9],[0,0,0,1]],dtype=float)
        actual = node_matrix({"matrix":expected.flatten(order="F").tolist()})
        np.testing.assert_equal(actual,expected)
        lo,hi = transform_bounds([0,0,0],[1,1,1],actual)
        np.testing.assert_equal(lo,[7,8,9]); np.testing.assert_equal(hi,[9,11,13])

    def test_large_floor_has_no_holes(self):
        t = np.array([[[0,2,0],[12,2,0],[0,2,12]],[[12,2,12],[0,2,12],[12,2,0]]],dtype=float)
        pieces = list(surface_cells(t,np.array([0,0,0]),np.array([11,5,11]),candidate_budget=20))
        cells = set(map(tuple,np.concatenate([p[0] for p in pieces])))
        self.assertEqual(cells,{(x,2,z) for x in range(12) for z in range(12)})

    def test_slivers_and_steep_triangles_match_bruteforce(self):
        triangles = np.array([[[.01,.1,.1],[4.9,4.8,4.7],[4.8,4.75,4.72]],
                              [[.2,.3,.4],[.3,4.6,.8],[4.7,2.2,4.8]],
                              [[1.01,.01,.01],[1.02,4.9,.02],[1.01,.02,4.9]]])
        all_cells = np.array([[x,y,z] for x in range(5) for y in range(5) for z in range(5)])
        for triangle in triangles:
            expected = set(map(tuple,all_cells[triangle_box_mask(np.repeat(triangle[None],len(all_cells),axis=0),all_cells)]))
            parts = list(surface_cells(triangle[None],np.array([0,0,0]),np.array([4,4,4]),candidate_budget=8))
            actual = set(map(tuple,np.concatenate([p[0] for p in parts])))
            self.assertEqual(actual,expected)

    def test_canopy_retains_hollow_space(self):
        # Floor + canopy + two pillars: the opening stays air at y=1..4.
        triangles = []
        for y in (0,5):
            triangles.extend([[[0,y,0],[6,y,0],[0,y,6]],[[6,y,6],[0,y,6],[6,y,0]]])
        for x in (0,5):
            triangles.extend([[[x,0,0],[x,5,0],[x,0,6]],[[x,5,6],[x,0,6],[x,5,0]]])
        p = fixture(self.root/"canopy.glb",points=np.asarray(triangles).reshape(-1,3))
        xyz,_,_,_,_ = voxelize(GLB(p),[0,0,0],[6,7,6],1,[0,0,0],progress=False)
        cells = set(map(tuple,xyz))
        self.assertIn((3,5,3),cells);self.assertIn((3,0,3),cells)
        for y in range(1,5):self.assertNotIn((3,y,3),cells)

    def test_crop_and_scale_offset_and_skip(self):
        nodes = [{"children":[1,2]}, {"mesh":0}, {"mesh":0,"translation":[9999,0,0]}]
        glb = GLB(fixture(self.root/"f.glb",nodes=nodes))
        xyz,_,palette,stats,_ = voxelize(glb,[0,-1,0],[2,1,2],2,[0,40,0],
            {"materials":{"floor":{"block":"minecraft:iron_block"}}},progress=False)
        self.assertTrue(np.all(xyz[:,0]<4));self.assertTrue(np.all(xyz[:,2]<4))
        self.assertEqual(set(xyz[:,1]),{40});self.assertEqual(stats["instancesCulled"],1)
        self.assertEqual(palette,["minecraft:iron_block"])
        with self.assertRaisesRegex(ValueError,"no surface"):
            voxelize(glb,[0,-1,0],[2,1,2],1,[0,0,0],{"materials":{"floor":{"skip":True}}},progress=False)

    def test_uv_orientation_and_wrap(self):
        image = np.array([[[255,0,0,255],[0,255,0,255]],[[0,0,255,255],[255,255,255,255]]],dtype=np.uint8)
        rgba = sample_uv([[.1,.1],[.1,.9],[1.1,.1],[-.1,.1]],image,{})
        np.testing.assert_equal(rgba[:,:3],[[1,0,0],[0,0,1],[1,0,0],[0,1,0]])
        np.testing.assert_equal(sample_uv([[1.1,.1]],image,{"wrapS":33071})[0,:3],[0,1,0])

    def test_alpha_mask_and_texture_median(self):
        image = np.zeros((2,2,4),dtype=np.uint8)
        image[:,:,:3] = [161,39,34]
        image[:,:,3] = [[255,0],[255,0]]
        materials = [{"name":"cloth","alphaMode":"MASK","alphaCutoff":.5,
                      "pbrMetallicRoughness":{"baseColorTexture":{"index":0}}}]
        p = fixture(self.root/"t.glb",materials=materials,uv=[[0,0],[1,0],[0,1]],image=image)
        scene = GLB(p)
        xyz,_,palette,_,report = voxelize(scene,[0,-1,0],[4,1,4],1,[0,0,0],progress=False)
        self.assertEqual(palette,["minecraft:red_wool"])
        self.assertTrue(np.all(xyz[:,0]<2))
        np.testing.assert_allclose(next(iter(report.values()))["medianRGB"],[161,39,34])

    def test_binary_contract_and_deterministic_bytes(self):
        xyz = np.array([[-170,-56,-250],[219,179,89]],dtype=np.int32)
        ids = np.array([1,0],dtype=np.uint16)
        palette = ["minecraft:stone","minecraft:red_wool"]
        a,b = self.root/"a.gz",self.root/"b.gz"
        write_vox(a,xyz,ids,palette);write_vox(b,xyz,ids,palette)
        self.assertEqual(a.read_bytes(),b.read_bytes())
        raw = gzip.decompress(a.read_bytes())
        self.assertEqual(raw[:8],b"DGTWR001")
        offset = 12
        self.assertEqual(struct.unpack_from(">i",raw,8),(2,))
        for state in palette:
            size, = struct.unpack_from(">H",raw,offset);offset += 2
            self.assertEqual(raw[offset:offset+size].decode(),state);offset += size
        self.assertEqual(struct.unpack_from(">i",raw,offset),(2,));offset += 4
        self.assertEqual(struct.unpack_from(">iiiH",raw,offset),(-170,-56,-250,1))
        actual_xyz,actual_ids,actual_palette = read_vox(a)
        np.testing.assert_equal(actual_xyz,xyz);np.testing.assert_equal(actual_ids,ids)
        self.assertEqual(actual_palette,palette)

    def test_sponge_nbt_order_air_and_multibyte_varints(self):
        palette = [f"minecraft:stone[fixture={i}]" for i in range(130)]
        xyz = np.array([[-2,40,-3],[-1,41,-2]],dtype=np.int32)
        ids = np.array([0,129],dtype=np.uint16)
        path = self.root/"f.schem"
        write_schematic(path,xyz,ids,palette)
        name,doc = nbt_read(gzip.decompress(path.read_bytes()))
        self.assertEqual(name,"Schematic");self.assertEqual(doc["Version"],2)
        self.assertEqual((doc["Width"],doc["Height"],doc["Length"]),(2,2,2))
        self.assertEqual(doc["Palette"]["minecraft:air"],0)
        self.assertEqual(doc["Offset"],[-2,40,-3])
        self.assertEqual(doc["Metadata"],{"WEOffsetX":-2,"WEOffsetY":40,"WEOffsetZ":-3})
        values=[];value=0;shift=0
        for byte in doc["BlockData"]:
            value |= (byte&127)<<shift
            if byte&128:shift += 7
            else:values.append(value);value=shift=0
        self.assertEqual(values,[1,0,0,0,0,0,0,130])
        self.assertEqual(doc["BlockEntities"],[])

    def test_cli_manifest_and_outputs(self):
        p = fixture(self.root/"f.glb")
        cfg = self.root/"config.json"
        cfg.write_text(json.dumps({"materials":{"floor":"minecraft:smooth_quartz"}}))
        out = self.root/"out"
        main(["--input",str(p),"--output",str(out),"--crop-min","0","-1","0",
              "--crop-max","4","1","4","--scale","2","--offset","0","40","0",
              "--config",str(cfg),"--quiet"])
        manifest = json.loads((out/"courtyard.json").read_text())
        xyz,_,palette = read_vox(out/"courtyard.vox.gz")
        self.assertEqual(manifest["blockCount"],len(xyz));self.assertFalse(manifest["spawnFinalized"])
        self.assertEqual(manifest["provenance"]["transform"],{"scale":2,"offset":[0,40,0]})
        self.assertEqual(palette,["minecraft:smooth_quartz"])
        self.assertTrue((out/"courtyard.schem").exists());self.assertTrue((out/"materials.json").exists())

    def test_explicit_override_preserves_alpha_mask(self):
        image = np.zeros((2,2,4),dtype=np.uint8)
        image[:,:,:3] = 255
        image[:,:,3] = [[255,0],[255,0]]
        mat = [{"name":"cloth","alphaMode":"MASK",
                "pbrMetallicRoughness":{"baseColorTexture":{"index":0}}}]
        scene = GLB(fixture(self.root/"t.glb",materials=mat,uv=[[0,0],[1,0],[0,1]],image=image))
        config = {"materials":{"cloth":{"block":"minecraft:iron_block"}}}
        xyz,_,palette,_,_ = voxelize(scene,[0,-1,0],[4,1,4],1,[0,0,0],config,progress=False)
        self.assertTrue(np.all(xyz[:,0]<2));self.assertEqual(palette,["minecraft:iron_block"])
        config["materials"]["cloth"]["ignore_alpha"] = True
        full,_,_,_,_ = voxelize(scene,[0,-1,0],[4,1,4],1,[0,0,0],config,progress=False)
        self.assertGreater(len(full),len(xyz))

    def test_sample_mode_palette_and_prioritized_instance_rules(self):
        image = np.zeros((2,2,4),dtype=np.uint8)
        image[:,:,:3] = [[[255,0,0],[0,0,255]],[[255,0,0],[0,0,255]]]
        image[:,:,3] = 255
        nodes = [{"children":[1,2]},{"name":"top_priority","mesh":0},
                 {"name":"later_low_priority","mesh":0}]
        mat = [{"name":"atlas","pbrMetallicRoughness":{"baseColorTexture":{"index":0}}}]
        scene = GLB(fixture(self.root/"t.glb",nodes=nodes,materials=mat,uv=[[0,0],[1,0],[0,1]],image=image))
        config = {"texture_mode":"sample", "palette":[
                    {"block":"minecraft:red_wool","rgb":[255,0,0]},
                    {"block":"minecraft:blue_concrete","rgb":[0,0,255]}]}
        xyz,ids,palette,_,_ = voxelize(scene,[0,-1,0],[4,1,4],1,[0,0,0],config,progress=False)
        self.assertEqual(set(palette),{"minecraft:red_wool","minecraft:blue_concrete"})
        blocks = {tuple(cell):palette[int(i)] for cell,i in zip(xyz,ids)}
        self.assertEqual(blocks[(0,0,0)],"minecraft:red_wool")
        self.assertEqual(blocks[(2,0,0)],"minecraft:blue_concrete")
        config["rules"] = [{"node":"top_*","block":"minecraft:smooth_quartz","priority":10},
                           {"node":"later_*","block":"minecraft:stone","priority":0}]
        _,_,palette,_,_ = voxelize(scene,[0,-1,0],[4,1,4],1,[0,0,0],config,progress=False)
        self.assertEqual(palette,["minecraft:smooth_quartz"])

    def test_tiny_shortcut_and_single_triangle_tiling(self):
        tri = np.array([[[.1,.1,.1],[.2,.1,.1],[.1,.2,.1]]])
        parts = list(surface_cells(tri,np.array([0,0,0]),np.array([0,0,0])))
        np.testing.assert_equal(parts[0][0],[[0,0,0]])
        # A projection row wider than the budget must tile in both dimensions.
        tri = np.array([[[0,2,0],[2,2,0],[0,2,50]]],dtype=float)
        parts = list(surface_cells(tri,np.array([0,0,0]),np.array([1,4,49]),candidate_budget=8))
        cells = set(map(tuple,np.concatenate([p[0] for p in parts])))
        self.assertIn((0,2,0),cells);self.assertIn((0,2,24),cells)
        self.assertNotIn((1,2,49),cells)

    def test_grid_limits_fail_before_allocation(self):
        scene = GLB(fixture(self.root/"f.glb"))
        with self.assertRaisesRegex(ValueError,"max-grid-cells"):
            voxelize(scene,[-1000]*3,[1000]*3,2,[0,40,0],max_grid_cells=10,progress=False)
        with self.assertRaisesRegex(ValueError,"positive"):
            voxelize(scene,[0,0,0],[1,1,1],0,[0,0,0],progress=False)


if __name__ == "__main__":
    unittest.main()
