#!/usr/bin/env python3
"""Light offline regression for W136 IKELOS_SG_v1.0.1; no native art gate."""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_ikelos_sg_v1_0_1.py'))
ART=G['ART'];MODEL=G['MODEL'];TEXTURE=G['TEXTURE']


def load(p):return json.loads((ROOT/p).read_bytes())


def inside(point,e):
    p=np.array(point,float)
    if 'rotation' in e:
        r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']})
        p=(p-o)@R+o
    return bool(np.all(p>=np.array(e['from'])-1e-7) and np.all(p<=np.array(e['to'])+1e-7))


class IkelosArt(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=load(ART+'design.json');cls.m=load(MODEL);cls.man=load(ART+'manifest.json');cls.bb=load(ART+'inspection.bbmodel')
        cls.atlas=Image.open(ROOT/TEXTURE).convert('RGBA');cls.pixels=np.asarray(cls.atlas)
        cls.names={e['name']:e for e in cls.m['elements']}

    def test_01_exclusive_full_only_scope(self):
        self.assertEqual(10,len(set(G['OWNED'])))
        self.assertEqual([MODEL],[p for p in G['OWNED'] if '/models/' in p])
        self.assertTrue(all((ROOT/p).is_file() for p in G['OWNED'] if p!=G['REPORT']))
        self.assertFalse((ROOT/MODEL.replace('.json','_body.json')).exists())
        self.assertFalse((ROOT/MODEL.replace('.json','_magazine.json')).exists())

    def test_02_schema_and_combined_count(self):
        es=self.m['elements'];self.assertLessEqual(len(es),1000);self.assertGreater(len(es),75)
        self.assertEqual(len(es),self.man['assembled_elements']);self.assertEqual(len(es)*6,self.man['emitted_faces'])
        self.assertEqual(len(es),sum(self.man['groups'].values()));self.assertEqual(0,self.man['alpha_body_elements'])
        self.assertEqual(0,self.man['triangle_adapter_elements']);self.assertEqual(len(es),len(self.names))
        for e in es:
            self.assertTrue(set(e)<={'name','from','to','rotation','faces'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.all(np.isfinite(G['vertices'](e))))
            self.assertEqual(set(G['FACES']),set(e['faces']))
            if 'rotation' in e:
                self.assertEqual({'origin','axis','angle'},set(e['rotation']));self.assertIn(e['rotation']['axis'],'xyz')

    def test_03_filled_semantic_depth(self):
        for name in ('shroud_core','lower_receiver','foregrip_core'):
            size=np.array(self.names[name]['to'])-self.names[name]['from']
            self.assertGreater(size[0],1.2);self.assertGreater(size[1],1);self.assertGreater(size[2],5)
        self.assertTrue(inside([8,12.2,0],self.names['shroud_core']))
        self.assertTrue(inside([8,11.0,0],self.names['lower_receiver']))
        self.assertTrue(inside([8,9.9,-3],self.names['foregrip_core']))
        for side in (-1,1):
            for i in range(4):
                e=self.names[f'capacitor_{i}_{side}'];size=np.array(e['to'])-e['from']
                self.assertGreater(np.prod(size),.6)
        # Geometry has semantic roles, no voxel/island-derived construction units.
        self.assertEqual(111,len(self.names))
        self.assertTrue(all(not n.startswith(('source_volume','voxel','triangle')) for n in self.names))

    def test_04_face_uv_alpha_and_gutters(self):
        self.assertEqual((1024,1024),self.atlas.size)
        ledger=self.d['atlas']['islands'];self.assertEqual(len(self.m['elements'])*6,len(ledger))
        coverage=np.zeros((1024,1024),np.uint8)
        for v in ledger:
            x0,y0,x1,y1=v['pixels'];self.assertGreater(x1,x0);self.assertGreater(y1,y0)
            self.assertGreaterEqual(min(x0,y0),2);self.assertLessEqual(max(x1,y1),1022)
            rect=self.pixels[y0-2:y1+2,x0-2:x1+2]
            self.assertTrue(np.all(rect[:,:,3]==255))
            self.assertTrue(np.all(rect[:2,2:-2]==rect[2:3,2:-2]));self.assertTrue(np.all(rect[2:-2,:2]==rect[2:-2,2:3]))
            uv=self.names[v['element']]['faces'][v['face']]['uv']
            self.assertTrue(np.allclose(uv,np.array([x0,y0,x1,y1])*16/1024))
            self.assertTrue(np.all(coverage[y0-2:y1+2,x0-2:x1+2]==0));coverage[y0-2:y1+2,x0-2:x1+2]=1
            self.assertEqual('#0',self.names[v['element']]['faces'][v['face']]['texture'])
        self.assertGreater(len(np.unique(self.pixels[coverage>0,:3],axis=0)),100)

    def test_05_source_frame_display_and_default_photo_hash(self):
        source=load('art/blockbench/weapons/w30/ikelos_sg_v1_0_1.bbmodel')['destiny_w30']
        self.assertEqual(load(G['BASE'])['display'],self.m['display'])
        self.assertEqual(source['scale'],self.man['source_scale']);self.assertEqual(source['anchor'],self.man['source_anchor'])
        self.assertEqual(source['model_bounds'],self.man['source_bounds'])
        self.assertEqual(31852,self.man['w30_blend_triangles']);self.assertEqual(39273,self.man['source_triangles'])
        self.assertEqual(source,self.d['source'])
        self.assertAlmostEqual(source['model_bounds'][0][2],self.man['actual_bounds'][0][2],delta=1e-8)
        self.assertEqual(source['model_bounds'][1][2],self.man['actual_bounds'][1][2])
        # Absolute grip endpoints catch mirrored/recentered/rescaled hand frames.
        grip=self.names['grip_front'];points=G['vertices'](grip)
        self.assertTrue(inside([8,8.65,8.455],grip))
        self.assertTrue(np.allclose(grip['rotation']['origin'],[8,8.65,8.455]))
        self.assertGreater(points[:,1].min(),6.9);self.assertLess(points[:,1].max(),10.3)
        self.assertAlmostEqual(13.588837988866725,self.names['sight_tip_-1']['to'][1])
        self.assertEqual('shotgun',self.d['catalogue']['family'])
        self.assertEqual('rapid_fire',self.d['catalogue']['frame'])
        for p,digest in self.d['input_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        refs=load('art/weapons/w31/references.json');ref=next(r for r in refs if r['id']=='ikelos_sg_v1_0_1')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()));self.assertEqual(ref,self.d['reference'])
        self.assertEqual(self.man['default_photo_sha256'],ref['sha256'])
        for f,digest in source['source_files'].items():self.assertEqual(digest,G['sha']((G['RAW']/f).read_bytes()))
        meshes,meta=G['source_meshes']()
        self.assertEqual(source,meta);self.assertEqual(sorted(source['source_objects']),sorted(m['name'] for m in meshes))
        self.assertEqual(39273,sum(len(m['faces']) for m in meshes))
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],source['model_bounds'],atol=1e-5,rtol=0)
        self.assertLess(self.d['source_alignment']['max_bounds_residual'],1e-5)
        self.assertEqual('native X=-FBX Y, Y=FBX Z, Z=-FBX X; identity model transforms; muzzle -Z',self.d['coordinate_policy']['basis'])

    def assert_air(self,points):
        for p in points:
            self.assertEqual([],[e['name'] for e in self.m['elements'] if inside(p,e)],str(p))

    def test_06_real_bore_and_stop(self):
        self.assert_air([[8,11.15,float(z)] for z in np.linspace(-10.08,-8.49,24)])
        self.assertTrue(inside([8,11.15,-8.40],self.names['bore_depth_stop']))
        for x in (7.45,8.55):self.assertTrue(any(inside([x,11.15,-9.3],e) for e in self.m['elements']))
        for y in (10.65,11.60):self.assertTrue(any(inside([8,y,-9.3],e) for e in self.m['elements']))

    def test_07_actual_grip_guard_stock_sight_air(self):
        # Through-air across the weapon's full thickness, not alpha silhouette cutouts.
        self.assert_air([[float(x),10.1,12.8] for x in np.linspace(6.6,9.4,17)])
        self.assert_air([[float(x),7.8,9.48] for x in np.linspace(6.6,9.4,17)])
        self.assert_air([[float(x),9.55,6.95] for x in np.linspace(6.6,9.4,17)])
        self.assert_air([[8,13.4,float(z)] for z in np.linspace(3.75,4.03,7)])
        self.assertTrue(inside([8,9.16,7.06],self.names['trigger_guard_floor']))
        self.assertTrue(inside([8,10.31,11.08],self.names['stock_lower_strut']))

    def test_08_editable_inspection_parity(self):
        self.assertEqual(len(self.names),len(self.bb['elements']));self.assertEqual(self.m['display'],self.bb['display'])
        self.assertEqual((ROOT/TEXTURE).read_bytes(),base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1]))
        self.assertEqual(set(self.names),{e['name'] for e in self.bb['elements']})
        for b in self.bb['elements']:
            e=self.names[b['name']];self.assertEqual(e['from'],b['from']);self.assertEqual(e['to'],b['to'])
            self.assertFalse(b['box_uv']);self.assertEqual('cube',b['type'])
            for f in G['FACES']:self.assertTrue(np.allclose(np.array(e['faces'][f]['uv'])*64,b['faces'][f]['uv']))
            r=e.get('rotation');self.assertEqual([r['angle'] if r and r['axis']==a else 0 for a in 'xyz'],b['rotation'])
            if r:self.assertEqual(r['origin'],b['origin'])
        children=[v for g in self.bb['outliner'] for v in g['children']]
        self.assertEqual(len(children),len(set(children)));self.assertEqual(len(self.names),len(children))

    def test_09_manifest_hashes_and_native_pending(self):
        self.assertFalse(self.man['native_accepted']);self.assertTrue(self.man['full_only']);self.assertTrue(self.man['generic_reload_ADS_unchanged'])
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_ikelos_sg_v1_0_1.py').read_bytes()))
        for p,digest in self.man['output_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual((2700,2070),im.size)
        self.assertLess(sum((ROOT/p).stat().st_size for p in G['OWNED'] if (ROOT/p).exists()),25*1024*1024)

    def test_10_deterministic_regeneration(self):
        generated=G['generate'](include_comparison=False)
        for p,data in generated.items():
            if p!=ART+'manifest.json':self.assertEqual(data,(ROOT/p).read_bytes(),p)

    def test_11_hub_convex_octagons_are_filled_not_cogs(self):
        for prefix,y,z,r in (('front',11.52,7.32,.73),('rear',9.20,13.83,.70)):
            solids=[e for n,e in self.names.items() if n.startswith(prefix+'_hub_') and 'cap' not in n]
            self.assertEqual(6,len(solids));a=r*(np.sqrt(2)-1)
            for e in solids:
                yz=np.abs(G['vertices'](e)[:,1:]-[y,z])
                self.assertLessEqual(float(yz.max()),r+1e-6)
                self.assertTrue(np.all(yz.sum(1)<=r+a+1e-6))
            for dy in np.linspace(-r+.002,r-.002,13):
                for dz in np.linspace(-r+.002,r-.002,13):
                    if abs(dy)+abs(dz)<r+a-.002:
                        self.assertTrue(any(inside([8,y+dy,z+dz],e) for e in solids))

if __name__=='__main__':unittest.main(verbosity=2)
