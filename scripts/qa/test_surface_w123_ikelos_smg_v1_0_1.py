#!/usr/bin/env python3
"""Light offline regression for W142 IKELOS_SMG_v1.0.1; no native art gate."""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_ikelos_smg_v1_0_1.py'))
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
        es=self.m['elements'];self.assertLessEqual(len(es),1000);self.assertGreater(len(es),0)
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
        for name,point in [('carbon_receiver',[8,12.16,2]),('upper_action',[8,12.02,7]),
                           ('magazine',[8,4.5,8.26]),('ribbed_foregrip',[8,8.94,3.41])]:
            self.assertTrue(inside(point,self.names[name]),name)
        self.assertAlmostEqual(1.39,self.names['carbon_receiver']['to'][0]-self.names['carbon_receiver']['from'][0])
        self.assertAlmostEqual(1.18,self.names['upper_action']['to'][0]-self.names['upper_action']['from'][0])
        for side in (-1,1):
            for i in range(4):
                e=self.names[f'cell_{i}_{side}'];self.assertTrue(np.all(np.array(e['to'])-e['from']>0))
                self.assertTrue(inside((np.array(e['to'])+e['from'])/2,e))
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

    def test_05_source_frame_display_and_provenance(self):
        source=load('art/blockbench/weapons/w30/ikelos_smg_v1_0_1.bbmodel')['destiny_w30']
        self.assertEqual(load(G['BASE'])['display'],self.m['display'])
        self.assertEqual(source,self.d['source']);self.assertEqual(source['scale'],self.man['source_scale'])
        self.assertEqual(source['anchor'],self.man['source_anchor']);self.assertEqual(source['model_bounds'],self.man['source_bounds'])
        self.assertEqual(31768,self.man['w30_blend_triangles']);self.assertEqual(38980,self.man['source_triangles'])
        np.testing.assert_allclose(np.array(self.man['actual_bounds'])[:,2],np.array(source['model_bounds'])[:,2],atol=1e-8,rtol=0)
        self.assertTrue(inside([8,4.5,8.26],self.names['magazine']))
        self.assertTrue(inside([8,8,7.79],self.names['grip_front_rail']))
        self.assertEqual('submachine_gun',self.d['catalogue']['family'])
        for p,digest in self.d['input_sha256'].items():
            self.assertNotIn('manifest',p);self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(digest,G['sha'](Path(p).read_bytes()),p)
        ref=next(r for r in load('art/weapons/w31/references.json') if r['id']=='ikelos_smg_v1_0_1')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()));self.assertEqual(ref,self.d['reference'])
        for f,digest in source['source_files'].items():self.assertEqual(digest,G['sha']((G['RAW']/f).read_bytes()))
        meshes,meta=G['source_meshes']();self.assertEqual(source,meta)
        self.assertEqual(sorted(source['source_objects']),sorted(m['name'] for m in meshes))
        self.assertEqual(38980,sum(len(m['faces']) for m in meshes))
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],source['model_bounds'],atol=1e-5,rtol=0)
        self.assertLess(self.d['source_alignment']['max_bounds_residual'],1e-5)
        self.assertEqual('native X=FBX Y, Y=FBX Z, Z=-FBX X; baked identity transforms; muzzle -Z',self.d['coordinate_policy']['basis'])

    def assert_air(self,points):
        for p in points:
            self.assertEqual([],[e['name'] for e in self.m['elements'] if inside(p,e)],str(p))

    def test_06_real_octagonal_bore_full_model(self):
        # Sample the passage in the entire assembly, not an isolated muzzle render.
        self.assert_air([[8+dx,11.68+dy,float(z)] for dx in (-.12,0,.12) for dy in (-.12,0,.12) for z in np.linspace(-1.59,-.87,9)])
        self.assertTrue(inside([8,11.68,-.78],self.names['bore_stop']))
        for i in range(8):
            theta=i*np.pi/4
            self.assertTrue(inside([8+np.sin(theta)*.38,11.68+np.cos(theta)*.38,-1.22],self.names['muzzle_wall_'+str(i)]))

    def test_07_actual_guard_stock_sight_grip_and_foreframe_air(self):
        for y,z in ((9.8,7.38),(9.6,12.3),(9.4,8.1),(8.3,8.5),(10.6,.2)):
            self.assert_air([[float(x),y,z] for x in np.linspace(6.4,9.6,17)])
        self.assert_air([[8,y,z] for y,z in ((13.8,3.5),(14.1,3.16),(14.5,2.74))])
        # Structure surrounds the air and has real depth.
        self.assertTrue(inside([8,9.42,7.2],self.names['guard_floor']))
        self.assertTrue(inside([8,14.90,2.30],self.names['sight_top_bridge']))
        self.assertTrue(inside([8,10.19,1],self.names['frame_front_crossbar']) is False)
        self.assertTrue(inside([8.56,10.19,1],self.names['frame_floor_1']))
        self.assertTrue(inside([8,7.05,8.79],self.names['stock_diagonal_tube']))
        self.assertTrue(inside([8,6.22,9.24],self.names['lower_swivel_cross_y']))

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
        self.assertEqual(self.man['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_ikelos_smg_v1_0_1.py').read_bytes()))
        for p,digest in self.man['output_sha256'].items():self.assertEqual(digest,G['sha']((ROOT/p).read_bytes()),p)
        with Image.open(ROOT/(ART+'comparison.png')) as im:self.assertEqual((2700,2470),im.size)
        self.assertLess(sum((ROOT/p).stat().st_size for p in G['OWNED'] if (ROOT/p).exists()),25*1024*1024)

    def test_10_deterministic_regeneration(self):
        generated=G['generate'](include_comparison=False)
        for p,data in generated.items():
            if p!=ART+'manifest.json':self.assertEqual(data,(ROOT/p).read_bytes(),p)

    def test_11_convex_filled_disc_and_swivel(self):
        for prefix,y,z,r in (('rear_disc',12.08,11.70,1.10),('lower_swivel',6.22,9.24,.39)):
            solids=[e for n,e in self.names.items() if n.startswith(prefix+'_') and 'cap' not in n]
            self.assertEqual(6,len(solids));a=r*(np.sqrt(2)-1)
            for e in solids:
                yz=np.abs(G['vertices'](e)[:,1:]-[y,z])
                self.assertLessEqual(float(yz.max()),r+1e-6)
                self.assertTrue(np.all(yz.sum(1)<=r+a+1e-6))
            for dy in np.linspace(-r+.002,r-.002,13):
                for dz in np.linspace(-r+.002,r-.002,13):
                    if abs(dy)+abs(dz)<r+a-.002:
                        self.assertTrue(any(inside([8,y+dy,z+dz],e) for e in solids))

    def test_12_batch_scope_and_atlas_detail_roles(self):
        feature=next(f for f in load('docs/qa/2026-10-26/w142/batch.json')['features'] if f['name']=='w142-ikelos_smg_v1_0_1')
        self.assertEqual(set(feature['owned_paths']),set(G['OWNED']))
        # Run the same art regression in the isolated worker and after exact-
        # scope integration into its source repository. The batch destination
        # names only the former; it is not the product's installed root.
        worker=Path(feature['destination'])
        self.assertIn(ROOT,{worker,worker.parent.parent/'DestinyGuardians'})
        self.assertEqual(133,len(self.names))
        # Painted detail must survive atlas packing without geometry proxies or alpha.
        for part,face in [('carbon_receiver','west'),('cell_0_-1','west'),('magazine','west'),('stock_coil','up')]:
            island=next(i for i in self.d['atlas']['islands'] if i['element']==part and i['face']==face)
            x0,y0,x1,y1=island['pixels'];pixels=self.pixels[y0:y1,x0:x1,:3]
            self.assertGreater(len(np.unique(pixels.reshape(-1,3),axis=0)),1,part)

if __name__=='__main__':unittest.main(verbosity=2)
