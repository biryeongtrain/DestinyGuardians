#!/usr/bin/env python3
"""Targeted offline contracts for W128 Gnawing Hunger, no game/DCC/build."""
import base64
import hashlib
import io
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
ART=ROOT/'art/weapons/w123/gnawing_hunger'
ASSET=ROOT/'src/main/resources/assets/destiny'

def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def turn(r):
    x,y,z=np.radians([r.get(a,0) for a in 'xyz']);cx,sx,cy,sy,cz,sz=np.cos(x),np.sin(x),np.cos(y),np.sin(y),np.cos(z),np.sin(z)
    return np.array([[cz,-sz,0],[sz,cz,0],[0,0,1]])@np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])@np.array([[1,0,0],[0,cx,-sx],[0,sx,cx]])
def cube_points(e):
    ps=np.array([[e['to' if mask>>i&1 else 'from'][i] for i in range(3)] for mask in range(8)])
    o=np.array(e['rotation']['origin']);return (ps-o)@turn(e['rotation']).T+o

def occupied(p,e):
    o=np.array(e['rotation']['origin']);p=(np.array(p)-o)@turn(e['rotation'])+o
    return bool(np.all(p>np.array(e['from'])+1e-5) and np.all(p<np.array(e['to'])-1e-5))

def ray_hits(start,end,e):
    o=np.array(e['rotation']['origin']);r=turn(e['rotation'])
    a=(np.array(start)-o)@r+o;b=(np.array(end)-o)@r+o;d=b-a
    lo,hi=np.array(e['from']),np.array(e['to']);t0,t1=0.,1.
    for k in range(3):
        if abs(d[k])<1e-9:
            if a[k]<lo[k]+1e-6 or a[k]>hi[k]-1e-6:return False
        else:
            q=sorted(((lo[k]-a[k])/d[k],(hi[k]-a[k])/d[k]));t0=max(t0,q[0]);t1=min(t1,q[1])
            if t1-t0<1e-7:return False
    return True

class GnawingHunger(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model=json.loads((ASSET/'models/weapon_surface_w123/gnawing_hunger.json').read_bytes())
        cls.canonical=json.loads((ASSET/'models/weapon/auto_rifle/gnawing_hunger.json').read_bytes())
        cls.design=json.loads((ART/'design.json').read_bytes());cls.manifest=json.loads((ART/'manifest.json').read_bytes())
        cls.bb=json.loads((ART/'inspection.bbmodel').read_bytes());cls.elements=cls.model['elements']
        cls.atlas=Image.open(ASSET/'textures/item/weapon/w123/gnawing_hunger.png').convert('RGBA')

    def test_full_only_budget_and_broad_solids(self):
        self.assertEqual(self.manifest['counts'],{'full':len(self.elements)})
        self.assertLessEqual(len(self.elements),1000);self.assertTrue(self.manifest['full_only'])
        self.assertEqual(self.manifest['emitted_faces'],len(self.elements)*6)
        self.assertEqual(self.manifest['triangle_adapter_elements'],0)
        self.assertEqual(self.manifest['alpha_body_plates'],0)
        self.assertGreater(sum(np.max(np.array(e['to'])-e['from'])>2 for e in self.elements),25)
        for e in self.elements:
            self.assertEqual(set(e),{'name','from','to','rotation','faces'})
            self.assertEqual(set(e['faces']),{'north','south','east','west','up','down'})
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(cube_points(e)).all())
        for suffix in ('_body','_magazine','_cover'):
            self.assertFalse((ASSET/f'models/weapon_surface_w123/gnawing_hunger{suffix}.json').exists())

    def test_canonical_frame_display_and_contact_region(self):
        self.assertEqual(self.model['display'],self.canonical['display'])
        frame=self.design['frame'];self.assertEqual(frame['anchor'],[8,8,8]);self.assertEqual(frame['muzzle'],'-Z')
        bb=json.loads((ROOT/'art/blockbench/weapons/w30/gnawing_hunger.bbmodel').read_bytes())
        self.assertEqual(frame['scale'],bb['destiny_w30']['scale'])
        ps=np.concatenate([cube_points(e) for e in self.elements]);source=np.array(bb['destiny_w30']['model_bounds'])
        self.assertTrue(np.all(np.abs(ps.min(0)-source[0])<.35))
        self.assertTrue(np.all(np.abs(ps.max(0)-source[1])<.35))
        grip=next(e for e in self.elements if e['name']=='grip/core')
        self.assertTrue(occupied([8,8.60,8.28],grip))
        self.assertLess(abs(cube_points(grip)[:,0].mean()-8),1e-6)

    def test_openings_are_clear_through_geometry(self):
        for name,p in self.design['required_air_probes'].items():
            self.assertFalse(any(occupied(p,e) for e in self.elements),name)
        for name in ('stock_large','stock_rear','trigger_guard'):
            _,y,z=self.design['required_air_probes'][name]
            self.assertFalse(any(ray_hits([6,y,z],[10,y,z],e) for e in self.elements),name)
        self.assertFalse(any(ray_hits([8,12.95,-12],[8,12.95,16],e) for e in self.elements),'sight axis')
        # Verify a positive boundary too: no missing stock or muzzle wall.
        self.assertTrue(any(occupied([8,8.44,13.63],e) for e in self.elements))
        self.assertTrue(any(occupied([8.34,10.87,-8.5],e) for e in self.elements))

    def test_muzzle_has_deep_bore_and_recessed_stop(self):
        self.assertFalse(any(ray_hits([8,10.87,-9.55],[8,10.87,-6.5],e) for e in self.elements))
        stops=[e for e in self.elements if ray_hits([8,10.87,-6.5],[8,10.87,-6.35],e)]
        self.assertEqual([e['name'] for e in stops],['muzzle/bore-backstop'])

    def test_atlas_uvs_opaque_padded_and_nonoverlapping(self):
        self.assertEqual(self.atlas.size,(1024,1024));a=np.array(self.atlas);coverage=np.zeros((1024,1024),np.uint8)
        self.assertEqual(len(self.design['uv']['islands']),6*len(self.elements))
        lookup={e['name']:e for e in self.elements}
        for island in self.design['uv']['islands']:
            x,y,xx,yy=island['pixels'];self.assertGreaterEqual(x,2);self.assertGreaterEqual(y,2)
            self.assertLessEqual(xx+2,1024);self.assertLessEqual(yy+2,1024)
            coverage[y-2:yy+2,x-2:xx+2]+=1
            self.assertTrue((a[y-2:yy+2,x-2:xx+2,3]==255).all(),island)
            f=lookup[island['element']]['faces'][island['face']]
            self.assertEqual(f['texture'],'#0');self.assertEqual(f['uv'],[v/64 for v in (x,y,xx,yy)])
        self.assertEqual(int(coverage.max()),1)

    def test_default_paint_evidence_and_distinct_materials(self):
        refs=json.loads((ROOT/'art/weapons/w31/references.json').read_bytes());ref=next(r for r in refs if r['id']=='gnawing_hunger')
        self.assertEqual(ref['sha256'],self.design['raw_input_sha256']['/tmp/destiny-weapons-w31/references/gnawing_hunger.jpg'])
        overrides=json.loads((ROOT/'art/weapons/w31/palette-overrides.json').read_bytes());self.assertNotIn('gnawing_hunger',overrides)
        a=np.array(self.atlas)[:,:,:3].astype(int)
        self.assertGreater(np.count_nonzero((a[:,:,0]>a[:,:,2]*1.4)&(a[:,:,0]>90)),1000)
        self.assertGreater(np.count_nonzero((a.min(2)>150)&(a.max(2)-a.min(2)<35)),1000)
        self.assertGreater(np.count_nonzero((a.max(2)<55)&(np.array(self.atlas)[:,:,3]==255)),1000)

    def test_inspection_matches_native_geometry_and_texture(self):
        self.assertEqual(len(self.bb['elements']),len(self.elements));self.assertEqual(self.bb['display'],self.model['display'])
        for native,b in zip(self.elements,self.bb['elements']):
            self.assertEqual(b['type'],'cube');self.assertEqual(b['from'],native['from']);self.assertEqual(b['to'],native['to'])
            self.assertEqual(b['origin'],native['rotation']['origin'])
            self.assertEqual(b['rotation'],[native['rotation'][a] for a in 'xyz'])
            for face,f in native['faces'].items():self.assertEqual(b['faces'][face]['uv'],[x*64 for x in f['uv']])
        ids={e['uuid'] for e in self.bb['elements']}
        self.assertEqual(len(ids),len(self.elements));self.assertEqual(ids,{u for g in self.bb['outliner'] for u in g['children']})
        data=base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]);embedded=Image.open(io.BytesIO(data)).convert('RGBA')
        self.assertTrue(np.array_equal(np.array(embedded),np.array(self.atlas)))

    def test_provenance_and_dirty_seed_beforehash(self):
        gitdir=Path((ROOT/'.git').read_text().strip().split(': ',1)[1]);state=json.loads((gitdir/'worktree-batch.json').read_bytes())
        self.assertEqual(state['name'],'w128-gnawing_hunger')
        for p,h in self.design['input_sha256'].items():
            self.assertEqual(sha(ROOT/p),h,p);self.assertEqual(h,state['baseline'][p]['sha256'],p)
        for p,h in self.design['raw_input_sha256'].items():self.assertEqual(sha(Path(p)),h,p)
        for p,h in self.manifest['output_sha256'].items():self.assertEqual(sha(ROOT/p),h,p)
        self.assertEqual(sha(ROOT/'scripts/generate_surface_w123_gnawing_hunger.py'),self.manifest['generator_sha256'])
        owned=set(state['owned_paths']);generated=set(self.manifest['output_sha256'])|{'art/weapons/w123/gnawing_hunger/manifest.json'}
        self.assertTrue(generated<=owned);self.assertEqual(len(owned),10)

    def test_actual_fbx_is_reference_only(self):
        g=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_gnawing_hunger.py'));meshes,meta=g['source_meshes']()
        self.assertEqual(sum(len(m['faces']) for m in meshes),27436)
        self.assertEqual(set(m['name'] for m in meshes),set(meta['source_objects']))
        self.assertTrue(all(e['name'].split('/')[0] in self.design['groups'] for e in self.elements))
        self.assertFalse(self.design['source_component_tessellation'])

    def test_comparison_artifact_and_offline_scope(self):
        im=Image.open(ART/'comparison.png');self.assertEqual(im.size,(2640,1840))
        # All source/canonical/new panels contain a meaningful rendered object.
        for col in range(3):
            for row in range(3):
                a=np.array(im.crop((col*880+40,505+row*330+35,(col+1)*880-40,505+(row+1)*330-20)))
                self.assertGreater(np.count_nonzero(np.max(np.abs(a.astype(int)-[32,39,48]),axis=2)>20),1500)
        self.assertFalse(self.manifest['native_accepted'])
        self.assertEqual(self.manifest['validation']['native'],'pending master')

if __name__=='__main__':unittest.main(verbosity=2)
