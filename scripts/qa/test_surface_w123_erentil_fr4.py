#!/usr/bin/env python3
"""Practical offline regression for the W130 Erentil full-only art candidate.
Run with the bundled numpy/Pillow Python and -B; no native/client claims.
"""
import base64
import json
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_erentil_fr4.py'))

def read(path):return json.loads((ROOT/path).read_bytes())

def inside(point,e):
    r=e.get('rotation',{'origin':[8,8,8]});o=np.array(r['origin']);R=G['helper']()['rotation'](r)
    p=(np.array(point)-o)@R+o
    return bool(np.all(p>np.array(e['from'])+1e-5) and np.all(p<np.array(e['to'])-1e-5))

class ErentilSurfaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=read(G['MODEL']);cls.d=read(G['ART']+'design.json')
        cls.manifest=read(G['ART']+'manifest.json');cls.bb=read(G['ART']+'inspection.bbmodel')
        cls.elements=cls.model['elements']

    def test_full_schema_and_resource_reference(self):
        self.assertEqual(set(self.model),{'credit','textures','elements','display'})
        texture='destiny:item/weapon/w123/erentil_fr4'
        self.assertEqual(self.model['textures'],{'0':texture,'particle':texture})
        self.assertTrue((ROOT/G['TEXTURE']).is_file())
        self.assertEqual(self.manifest['model'],'destiny:weapon_surface_w123/erentil_fr4')
        self.assertTrue(self.manifest['full_only']);self.assertFalse(self.manifest['native_accepted'])
        for e in self.elements:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertEqual(set(e['rotation']),{'origin','x','y','z'})
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(G['vertices'](e)).all())

    def test_actual_assembled_budget_and_semantic_parts(self):
        n=len(self.elements);self.assertLessEqual(n,1000)
        self.assertEqual(n,len(self.d['parts']));self.assertEqual(n,len(self.bb['elements']))
        self.assertEqual(self.manifest['counts'],{'full':n,'cubes':n,'triangle_adapter_elements':0,'assembled_emitted':n,'faces':n*6})
        self.assertEqual(sum(self.d['groups'].values()),n)
        self.assertEqual(len({e['name'] for e in self.elements}),n)
        self.assertTrue(all(s['kind']=='filled_solid' for s in self.d['parts']))
        self.assertTrue({'frame','stock','grip','guard','rails','muzzle','chamber','capacitor','hoses','sight'}<=set(self.d['groups']))

    def test_opaque_atlas_explicit_uv_and_gutters(self):
        with Image.open(ROOT/G['TEXTURE']) as im:
            self.assertEqual(im.size,(1024,1024));self.assertEqual(im.mode,'RGBA')
            self.assertEqual(im.getchannel('A').getextrema(),(255,255))
        occupied=np.zeros((1024,1024),bool);ledger=self.d['atlas']['islands']
        self.assertEqual(len(ledger),len(self.elements)*6)
        lookup={e['name']:e for e in self.elements}
        for entry in ledger:
            x0,y0,x1,y1=entry['pixels'];self.assertTrue(2<=x0<x1<=1022 and 2<=y0<y1<=1022)
            region=occupied[y0-2:y1+2,x0-2:x1+2]
            self.assertFalse(region.any(),f"UV/gutter collision {entry['element']} {entry['face']}")
            region[:]=True
            face=lookup[entry['element']]['faces'][entry['face']]
            self.assertEqual(face['texture'],'#0')
            self.assertEqual(face['uv'],[v/64 for v in entry['pixels']])
        # Both logo faces own readable paint, rather than mirror the same island.
        logo=lookup['Omolon_receiver']['faces']
        self.assertNotEqual(logo['west']['uv'],logo['east']['uv'])

    def test_reference_provenance_and_product_hashes(self):
        for path,pin in self.d['input_sha256'].items():
            self.assertEqual(G['sha']((ROOT/path).read_bytes()),pin,path)
        for path,pin in self.d['raw_input_sha256'].items():
            self.assertEqual(G['sha'](Path(path).read_bytes()),pin,path)
        ref=self.d['reference'];self.assertEqual(ref['bungie_hash'],'2398848320')
        self.assertEqual(ref['sha256'],G['sha'](G['PHOTO'].read_bytes()))
        self.assertEqual(ref['sha256'],'2e018c1643cb9851ca6580470db4d670d50f1a5cb44ccec846cdb7478301a58c')
        meshes,meta,actual=G['source_meshes']()
        self.assertEqual(actual,ref);self.assertEqual(meta['raw_fbx_triangles'],38969)
        self.assertEqual(sum(len(m['faces']) for m in meshes),38969)
        for path,pin in self.manifest['outputs'].items():
            self.assertEqual(G['sha']((ROOT/path).read_bytes()),pin,path)

    def test_frame_display_and_hand_contact(self):
        source=read(G['BB'])['destiny_w30'];canonical=read(G['BASE'])
        self.assertEqual(self.d['anchor'],source['anchor'])
        self.assertEqual(self.d['scale'],source['scale'])
        self.assertEqual(self.model['display'],canonical['display'])
        for name,p in self.d['contact_probes'].items():
            self.assertTrue(any(inside(p,e) for e in self.elements),name)
        # Grip remains in the old hand region, with negative-Z muzzle and old scale.
        self.assertTrue(any(inside([8,8.15,2.88],e) for e in canonical['elements']))
        points=np.concatenate([G['vertices'](e) for e in self.elements])
        lo,hi=points.min(0),points.max(0)
        self.assertAlmostEqual(lo[2],source['model_bounds'][0][2],delta=.25)
        self.assertAlmostEqual(hi[2],source['model_bounds'][1][2],delta=.25)
        self.assertLess(hi[0]-lo[0],3.0);self.assertGreater(hi[0]-lo[0],1.8)
        for view in self.d['comparison_views']:
            cam=np.array(view['camera'],float);cam/=np.linalg.norm(cam)
            right=np.cross([0,1,0],cam);right/=np.linalg.norm(right);up=np.cross(cam,right)
            p=(np.c_[points@right,points@up]-view['center'])*view['scale']
            self.assertTrue(np.all(abs(p)<np.array(view['viewport'])/2-10),view['name'])

    def test_unique_real_openings_and_bore_depth(self):
        for name,p in self.d['required_air_probes'].items():
            self.assertFalse(any(inside(p,e) for e in self.elements),name)
        # Through-air checks over a few useful samples, not a mathematical art gate.
        for x in (6.7,7.4,8.0,8.6,9.3):
            self.assertFalse(any(inside([x,7.35,5.50],e) for e in self.elements),'triangular stock')
        for z in (2.0,2.4,2.8,3.1):
            self.assertFalse(any(inside([8,14.60,z],e) for e in self.elements),'open reflex')
        for z in (-9.38,-9.15,-8.95):
            self.assertFalse(any(inside([8,12.72,z],e) for e in self.elements),'recessed upper bore')
        self.assertTrue(any(inside([8,12.72,-8.74],e) for e in self.elements),'bore backstop')
        self.assertTrue(any(inside([8.49,12.72,-9.1],e) for e in self.elements),'bore rim')

    def test_editable_inspection_and_comparison(self):
        self.assertEqual(self.bb['display'],self.model['display'])
        self.assertEqual(self.bb['resolution'],{'width':1024,'height':1024})
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',',1)[1])
        self.assertEqual(embedded,(ROOT/G['TEXTURE']).read_bytes())
        for b,e in zip(self.bb['elements'],self.elements):
            self.assertEqual(b['type'],'cube');self.assertEqual(b['name'],e['name'])
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            self.assertEqual(b['rotation'],[e['rotation'][a] for a in 'xyz'])
            for f in G['FACES']:
                self.assertEqual(b['faces'][f]['uv'],[v*64 for v in e['faces'][f]['uv']])
        self.assertEqual({u for g in self.bb['outliner'] for u in g['children']},{e['uuid'] for e in self.bb['elements']})
        with Image.open(ROOT/G['ART']/'comparison.png') as im:
            self.assertEqual(im.size,(2000,2030));self.assertGreater(np.array(im).std(),15)
        self.assertEqual(len(self.d['comparison_views']),3)

if __name__=='__main__':unittest.main()
