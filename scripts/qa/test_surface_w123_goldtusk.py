#!/usr/bin/env python3
"""W141 Goldtusk targeted art regressions; inert CPU only, no native software."""
import base64
import io
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_goldtusk.py'))
CANONICAL_SHA='ca9d5e0f093983cf833417408fef8cb6a70a130fbb442938cb1b5a8d3be980f0'


def read(path):
    return json.loads((ROOT/path).read_bytes())


def inside(point,element):
    p=np.array(point,float);r=element.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@G['H']['rotation']({r['axis']:r['angle']})+o
    return bool(np.all(p>=np.array(element['from'])-1e-8) and np.all(p<=np.array(element['to'])+1e-8))


class GoldtuskArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.m=read(G['MODEL']);cls.d=read(G['ART']+'design.json');cls.man=read(G['ART']+'manifest.json')
        cls.bb=read(G['ART']+'inspection.bbmodel');cls.es={e['name']:e for e in cls.m['elements']}
        cls.px=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def test_budget_and_unique_native_cubes(self):
        n=len(self.m['elements'])
        self.assertEqual(n,len(self.es));self.assertLessEqual(n,1000)
        self.assertEqual(n,self.man['assembled_elements']);self.assertEqual(n,sum(self.man['groups'].values()))
        self.assertEqual(n*6,self.man['emitted_faces']);self.assertEqual(0,self.man['triangle_adapter_elements'])
        for e in self.es.values():
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'axis','angle','origin'},set(e['rotation']))
                self.assertIn(e['rotation']['axis'],'xyz')
        self.assertTrue(all(not n.startswith(('source_volume','triangle','voxel')) for n in self.es))

    def test_source_geometry_and_correct_goldtusk_basis(self):
        meshes,meta=G['source_meshes']()
        self.assertEqual(sorted(meta['source_objects']),sorted(m['name'] for m in meshes))
        self.assertEqual(8,len(meshes));self.assertEqual(3048,sum(len(m['faces']) for m in meshes))
        points=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([points.min(0),points.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
        self.assertEqual('anchor + scale * [-raw.Y, raw.Z, raw.X]',self.d['coordinate_policy']['mapping'])
        self.assertEqual([0,0,0],self.d['coordinate_policy']['fbx_translation_cm'])
        self.assertEqual('ceafb762e308610d741dc91e00a97b8b3aed6c473e781107cb39e7088790973e',meta['source_files']['Goldtusk.fbx'])

    def test_canonical_frame_display_and_proportions(self):
        self.assertEqual(CANONICAL_SHA,G['sha']((ROOT/G['BASE']).read_bytes()))
        self.assertEqual(read(G['BASE'])['display'],self.m['display'])
        self.assertEqual([8,5.213769490183353,8],self.man['source_anchor'])
        self.assertEqual(26.632478432940058,self.man['source_scale'])
        np.testing.assert_allclose(self.man['actual_bounds'],self.man['source_bounds'],atol=.06,rtol=0)
        self.assertEqual('+Y',self.d['coordinate_policy']['length'])
        self.assertTrue(inside(self.man['source_anchor'],self.es['palm_core']))
        self.assertEqual('sword',next(w for w in read('src/main/resources/destiny/weapons/w30.json') if w['id']=='goldtusk')['family'])

    def test_solid_blade_and_shaped_cross_sections(self):
        # One body center and pale shoulder point at representative long spans.
        for y,z in ((15.5,8.426),(19.5,8.394),(23,8.291),(27,8.044)):
            for zz in (z-.2,z+.32):
                self.assertTrue(any(inside([8,y,zz],e) for e in self.es.values()),(y,zz))
        for i in range(5):
            a,b,c=(self.es[f'blade_{role}_{i}'] for role in ('shoulder','bevel','edge'))
            widths=[e['to'][0]-e['from'][0] for e in (a,b,c)]
            self.assertGreater(widths[0],widths[1]);self.assertGreater(widths[1],widths[2])
            self.assertGreater(a['to'][1]-a['from'][1],3)
        # Thick grip and thin blade are filled volumes, with no shell-only center.
        for p in ([8,4,8.1],[8,6,8.1],[8,8,8.1]):
            self.assertTrue(any(inside(p,e) for e in self.es.values()),p)
        self.assertGreater(self.es['palm_core']['to'][0]-self.es['palm_core']['from'][0],.55)

    def test_curved_point_and_real_heel_bite(self):
        core=[self.es[f'point_shoulder_{i}']['rotation']['origin'] for i in range(4)]
        self.assertTrue(all(a[1]<b[1] and a[2]>b[2] for a,b in zip(core,core[1:])))
        self.assertLess(core[-1][2],7)
        # Pale edge is physically interrupted at heel, while its dark web remains.
        self.assertFalse(any(inside([8,11.5,8.85],e) for e in self.es.values()))
        self.assertTrue(any(inside([8,11.5,8.1],e) for e in self.es.values()))
        self.assertTrue(any(inside([8,11.9,8.85],e) for e in self.es.values()))
        self.assertTrue(any(inside([8,10.35,9.30],e) for e in self.es.values()))

    def test_opaque_face_atlas_and_extruded_nonoverlapping_uvs(self):
        self.assertEqual((1024,1024,4),self.px.shape);self.assertTrue((self.px[:,:,3]==255).all())
        cover=np.zeros((1024,1024),bool);seen=set()
        for r in self.d['atlas']['islands']:
            x,y,X,Y=r['pixels'];key=(r['element'],r['face']);self.assertNotIn(key,seen);seen.add(key)
            self.assertGreaterEqual(min(x,y),2);self.assertLessEqual(max(X,Y),1022)
            self.assertGreater(X,x);self.assertGreater(Y,y)
            self.assertFalse(cover[y-2:Y+2,x-2:X+2].any());cover[y-2:Y+2,x-2:X+2]=True
            f=self.es[r['element']]['faces'][r['face']]
            self.assertEqual('#0',f['texture']);np.testing.assert_allclose(f['uv'],np.array([x,y,X,Y])/64)
            self.assertNotIn('cullface',f)
            patch=self.px[y:Y,x:X]
            expected=np.pad(patch,((2,2),(2,2),(0,0)),mode='edge')
            np.testing.assert_array_equal(expected,self.px[y-2:Y+2,x-2:X+2])
        self.assertEqual(len(self.es)*6,len(seen));self.assertEqual(0,self.man['alpha_body_elements'])

    def test_default_paint_etching_and_grip_weave(self):
        self.assertEqual([165,139,68],G['PALETTE']['gold'])
        self.assertEqual([33,36,36],G['PALETTE']['dark'])
        def patch(name,face):
            r=next(r for r in self.d['atlas']['islands'] if r['element']==name and r['face']==face)
            x,y,X,Y=r['pixels'];return self.px[y:Y,x:X,:3]
        bevel=patch('blade_bevel_1','east');dark=patch('blade_shoulder_1','east')
        self.assertGreater(float(bevel.mean()),float(dark.mean())*3)
        self.assertLess(float(bevel.min()),100);self.assertGreater(float(bevel.max()),170)
        self.assertGreater(len(np.unique(patch('hilt_black_palm_pad','east').reshape(-1,3),axis=0)),3)
        self.assertGreater(max(bevel.shape[:2]),150)
        # Candidate paint succeeds without loading any ripped DDS pixels.
        source=Path(G['tile'].__code__.co_filename).read_text()
        tile_body=source[source.index('def tile('):source.index('def compile_model(')]
        self.assertNotIn('Image.open',tile_body);self.assertNotIn('RAW',tile_body)

    def test_editable_inspection_matches_native_geometry_uv_and_texture(self):
        self.assertEqual(set(self.es),{e['name'] for e in self.bb['elements']})
        self.assertEqual(len(self.es),len({e['uuid'] for e in self.bb['elements']}))
        self.assertEqual(len(self.es),sum(len(g['children']) for g in self.bb['outliner']))
        self.assertEqual((ROOT/G['TEXTURE']).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(self.m['display'],self.bb['display'])
        self.assertEqual(self.man['source_anchor'],self.bb['destiny_w141']['sourceAnchor'])
        for b in self.bb['elements']:
            native=self.es[b['name']]
            self.assertEqual(native['from'],b['from']);self.assertEqual(native['to'],b['to'])
            for face,f in b['faces'].items():np.testing.assert_allclose(f['uv'],np.array(native['faces'][face]['uv'])*64)

    def test_inputs_provenance_and_existing_swordframe_unchanged(self):
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in read('art/weapons/w31/references.json') if r['id']=='goldtusk')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        self.assertTrue(self.man['existing_native_swordframe_unchanged'])
        self.assertIn('src/main/resources/destiny/animation/sword_w140.animation.json',self.d['input_sha256'])
        # Aggregate migration is a downstream product, not an art input. Pinning
        # it would invalidate this design whenever another weapon is integrated.
        self.assertNotIn('src/main/resources/weapon_surface_w123/manifest.json',self.d['input_sha256'])
        self.assertFalse(read('src/main/resources/assets/destiny/items/weapon/goldtusk.json')['hand_animation_on_swap'])

    def test_exact_owned_scope_and_full_only_candidate(self):
        scope=next(f['owned_paths'] for f in read('docs/qa/2026-10-26/w141/batch.json')['features'] if f['name']=='w141-goldtusk')
        self.assertEqual(10,len(scope));self.assertTrue(all((ROOT/p).is_file() for p in scope))
        self.assertLess(sum((ROOT/p).stat().st_size for p in scope),25*1024*1024)
        for p,digest in self.man['output_sha256'].items():
            self.assertIn(p,scope);self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()))
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_goldtusk.py').read_bytes()))
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only'])
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/G['MODEL'].replace('.json','_magazine.json')).exists())

    def test_comparison_has_reference_and_matched_side_oblique_hilt_views(self):
        with Image.open(ROOT/G['ART']/'comparison.png') as im:
            self.assertEqual((1800,2470),im.size)
            rgb=np.asarray(im)
            for yy in (500,1285,2070):
                for xx in (0,600,1200):
                    self.assertGreater(len(np.unique(rgb[yy:yy+300,xx:xx+600].reshape(-1,3),axis=0)),30)
        review=(ROOT/G['ART']/'review.md').read_text()
        self.assertIn('Pending master:',review);self.assertIn('3048',review)

    def test_deterministic_all_generated_bytes(self):
        outputs=G['generate']()
        self.assertEqual(7,len(outputs))
        for p,data in outputs.items():self.assertEqual((ROOT/p).read_bytes(),data,p)


if __name__=='__main__':unittest.main(verbosity=2)
