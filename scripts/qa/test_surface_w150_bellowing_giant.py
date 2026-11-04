#!/usr/bin/env python3
"""Practical W150 Bellowing Giant art regression. Offline only; no native claims."""
import base64
import copy
import io
import json
from pathlib import Path
import sys
import unittest
import numpy as np
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import generate_surface_w123_bellowing_giant as g
import worktree_batch as batch

BASELINE='a3fe155824ed51805b47a7a6d1012346fa3a9a3f3e3fe8ed98c99994aa32a5b1'
WORKER='docs/qa/2026-10-26/w150/bellowing_giant-worker.md'

def read(path):return json.loads((g.ROOT/path).read_bytes())
def baseline_state():
    if batch.state_path(g.ROOT).is_file():return batch.load(g.ROOT)[1]
    # Main checkout is not a worker: use the source-pinned integration ledger,
    # never require a foreign .git worktree state in the production repository.
    return read('docs/qa/2026-10-26/w150/bellowing-baseline-inputs.json')
def local(e,p):
    p=np.asarray(p,float);r=e.get('rotation')
    if r:
        o=np.array(r['origin']);p=(p-o)@g.H.rotation({r['axis']:r['angle']})+o
    return p

def contains(e,p):
    p=local(e,p)
    return bool(np.all(p>np.array(e['from'])+1e-7) and np.all(p<np.array(e['to'])-1e-7))

def segment_hits(e,start,end):
    a=local(e,start);b=local(e,end);d=b-a;t0=0.;t1=1.
    for i,(lo,hi) in enumerate(zip(e['from'],e['to'])):
        if abs(d[i])<1e-12:
            if not lo+1e-7<a[i]<hi-1e-7:return False
            continue
        near,far=sorted(((lo-a[i])/d[i],(hi-a[i])/d[i]));t0=max(t0,near);t1=min(t1,far)
        if t1-t0<1e-7:return False
    return True

class BellowingGiantW150(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d=read(g.ART+'design.json');cls.m=read(g.MODEL);cls.man=read(g.ART+'manifest.json')
        cls.bb=read(g.ART+'inspection.bbmodel');cls.es=cls.m['elements']
        cls.tex=Image.open(g.ROOT/g.TEXTURE).convert('RGBA');cls.named={e['name']:e for e in cls.es}

    def assert_air(self,start,end):
        self.assertEqual([], [e['name'] for e in self.es if segment_hits(e,start,end)])

    def test_01_parse_budget_and_closed_solids(self):
        self.assertLessEqual(len(self.es),1000);self.assertGreaterEqual(len(self.es),80)
        self.assertEqual(len(self.es),len(self.named));self.assertEqual(self.man['assembled_elements'],len(self.es))
        for e in self.es:
            self.assertEqual(set(e),{'name','from','to','faces'}|({'rotation'} if 'rotation' in e else set()))
            self.assertEqual(set(e['faces']),set(g.FACES));self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertTrue(np.isfinite(g.vertices(e)).all())
            if 'rotation' in e:
                self.assertEqual(set(e['rotation']),{'origin','axis','angle'})
                self.assertIn(e['rotation']['axis'],'xyz');self.assertTrue(np.isfinite(e['rotation']['angle']))

    def test_02_independent_uv_opaque_gutters(self):
        alpha=np.array(self.tex)[:,:,3];self.assertTrue(np.all(alpha==255));rects=[]
        ledger=self.d['atlas']['islands'];self.assertEqual(len(ledger),len(self.es)*6)
        self.assertEqual(self.tex.size,(g.EDGE,g.EDGE))
        for island in ledger:
            x,y,X,Y=island['rect'];self.assertTrue(2<=x<X<=g.EDGE-2 and 2<=y<Y<=g.EDGE-2)
            f=self.named[island['element']]['faces'][island['face']]
            self.assertEqual(f['texture'],'#0');np.testing.assert_allclose(np.array(f['uv'])*g.EDGE/16,[x,y,X,Y])
            self.assertTrue(np.all(alpha[y-2:Y+2,x-2:X+2]==255));rects.append((x-2,y-2,X+2,Y+2))
        for i,a in enumerate(rects):
            for b in rects[i+1:]:self.assertFalse(a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3])

    def test_03_source_hashes_and_protected_inputs(self):
        for p,digest in self.d['raw_input_sha256'].items():self.assertEqual(g.sha(Path(p).read_bytes()),digest,p)
        state=baseline_state();self.assertEqual(state['baseline_sha256'],BASELINE)
        for p,digest in self.d['input_sha256'].items():
            self.assertEqual(g.sha((g.ROOT/p).read_bytes()),digest,p)
            self.assertEqual(state['baseline'][p]['sha256'],digest,p)
        self.assertEqual(g.sha((g.ROOT/g.GENERATOR).read_bytes()),self.man['generator_sha256'])

    def test_04_actual_fbx_blend_basis_and_bounds(self):
        meshes,meta=g.source_meshes();self.assertEqual(sum(len(m['faces']) for m in meshes),18468)
        self.assertEqual(sorted(m['name'] for m in meshes),sorted(meta['source_objects']))
        p=np.concatenate([m['canonical'] for m in meshes]);np.testing.assert_allclose([p.min(0),p.max(0)],meta['model_bounds'],atol=4e-6,rtol=0)
        # Verify correction around original hand anchor, not a fresh center/scale.
        for m in meshes:
            np.testing.assert_allclose(m['vertices'][:,:2],m['canonical'][:,:2])
            np.testing.assert_allclose(m['vertices'][:,2],16-m['canonical'][:,2])

    def test_05_real_deep_bore_and_thick_walls(self):
        for x in (7.85,8,8.15):
            for y in (11.90,12.05,12.20):self.assert_air([x,y,-5.7],[x,y,-3.02])
        self.assertTrue(contains(self.named['Recessed_throat_end'],[8,12.05,-2.82]))
        for x,y in ((8,12.66),(8,11.44),(7.39,12.05),(8.61,12.05)):
            self.assertTrue(any(contains(e,[x,y,-4.0]) for e in self.es))

    def test_06_real_grip_stock_and_forearm_openings(self):
        for name in ('forearm_bridge','grip_separation','trigger_loop','stock_strut'):
            p=self.d['air_probes'][name];self.assert_air([6.4,p[1],p[2]],[10.6,p[1],p[2]])
        for name,p in [('Foregrip_body',[8,8.99,2.17]),('Pistol_grip',[8,8.29,7.86]),('Stock_lower_strut',[8,10.22,11.0])]:
            self.assertTrue(contains(self.named[name],p))

    def test_07_open_optic_ray_and_physical_pin(self):
        sight=self.d['ads_sight'];self.assertEqual(sight['style'],'optic');self.assertEqual(sight['plane'],'XY');self.assertEqual(sight['eyeSide'],'+Z')
        c=np.array(sight['sightCenter']);np.testing.assert_allclose(sight['forwardPoint'],c+[0,0,-2])
        for dx in (-.035,0,.035):
            for dy in (-.035,0,.035):self.assert_air([c[0]+dx,c[1]+dy,22],[c[0]+dx,c[1]+dy,-6])
        pin=self.named['Sight_pin_tip'];self.assertLess(np.max(g.vertices(pin)[:,1]),c[1]-.05)
        self.assertTrue(contains(pin,[9.55,12.005,5.11]))
        for dx,dy in ((.49,0),(-.49,0),(0,.49),(0,-.49)):
            self.assertTrue(any(contains(e,[c[0]+dx,c[1]+dy,5.13]) for e in self.es if e['name'].startswith('Open_ring_sight')))

    def test_08_original_scale_anchor_bounds(self):
        meta=self.d['source'];self.assertEqual(self.d['frame']['anchor'],meta['anchor']);self.assertEqual(self.d['frame']['scale'],meta['scale'])
        p=np.concatenate([g.vertices(e) for e in self.es]);bounds=np.array([p.min(0),p.max(0)])
        self.assertLess(float(np.max(np.abs(bounds-np.array(meta['model_bounds'])))),.20)
        np.testing.assert_allclose(bounds[:,2],np.array(meta['model_bounds'])[:,2],atol=1e-6,rtol=0)
        self.assertTrue(np.all(bounds[0]>=-16) and np.all(bounds[1]<=32));self.assertEqual(self.d['frame']['muzzle_axis'],'-Z')

    def test_09_full_original_display_and_reload_preserved(self):
        self.assertEqual(self.m['display'],read(g.BASE)['display']);self.assertEqual(self.bb['display'],self.m['display'])
        self.assertTrue(self.d['full_only']);self.assertTrue(self.man['full_only']);self.assertEqual(set(self.man['counts']),{'full'})
        # Immutable canonical/aim/state hashes are checked against the dirty seed.
        self.assertGreaterEqual(sum('rocket_launcher/' in p for p in self.d['input_sha256']),6)
        self.assertNotIn('parent',self.m)

    def test_10_blockbench_native_uv_texture_parity(self):
        self.assertEqual(len(self.bb['elements']),len(self.es));self.assertEqual(self.bb['destiny_w150']['ads_sight'],self.d['ads_sight'])
        embedded=base64.b64decode(self.bb['textures'][0]['source'].split(',')[1]);self.assertEqual(embedded,(g.ROOT/g.TEXTURE).read_bytes())
        for e,b in zip(self.es,self.bb['elements']):
            for k in ('name','from','to'):self.assertEqual(e[k],b[k])
            r=e.get('rotation');self.assertEqual(b['origin'],r['origin'] if r else [8,8,8])
            self.assertEqual(b['rotation'],[r['angle'] if r and r['axis']==a else 0 for a in 'xyz'])
            for f in g.FACES:np.testing.assert_allclose(np.array(b['faces'][f]['uv'])*16/g.EDGE,e['faces'][f]['uv'])
        exported=[child for group in self.bb['outliner'] for child in group['children']]
        self.assertEqual(set(exported),{e['uuid'] for e in self.bb['elements']});self.assertEqual(len(exported),len(self.es))

    def test_11_deterministic_seven_artifacts(self):
        outputs=g.generate();self.assertEqual(len(outputs),7)
        for p,data in outputs.items():self.assertEqual((g.ROOT/p).read_bytes(),data,p)

    def test_12_output_manifest_hashes_and_comparison(self):
        self.assertEqual(len(self.man['output_sha256']),6)
        for p,digest in self.man['output_sha256'].items():self.assertEqual(g.sha((g.ROOT/p).read_bytes()),digest,p)
        with Image.open(g.ROOT/(g.ART+'comparison.png')) as im:self.assertEqual(im.size,(2400,1835))
        self.assertFalse(self.man['native_accepted']);self.assertEqual(self.man['validation']['performance'],'not measured')

    def test_13_default_dye_and_substantial_filled_volumes(self):
        red=np.array(self.d['palette']['red']);graphite=np.array(self.d['palette']['graphite']);self.assertGreater(red[0]-red[1],100)
        self.assertLess(np.max(graphite)-np.min(graphite),20)
        for name,p in [('Launch_chamber_heart',[8,12.05,3]),('Stock_filled_heart',[8,12.03,15])]:
            e=self.named[name];self.assertTrue(contains(e,p));self.assertGreater(np.min(np.array(e['to'])-e['from']),1.2)
        for mat in ('red','graphite','rubber','steel'):
            s=next(s for s in self.d['solids'] if s['material']==mat)
            rect=next(i['rect'] for i in self.d['atlas']['islands'] if i['element']==s['geometry']['name'])
            crop=np.asarray(self.tex.crop(rect));self.assertGreater(float(crop[:,:,:3].mean()),10)

    def test_14_exact_ten_new_owned_paths(self):
        feature=next(f for f in read('docs/qa/2026-10-26/w150/batch.json')['features'] if f['name']=='w150-'+g.ID)
        expected=set(self.man['output_sha256'])|{g.ART+'manifest.json',g.GENERATOR,g.TEST,WORKER}
        self.assertEqual(set(feature['owned_paths']),expected);self.assertEqual(len(expected),10)
        state=baseline_state();self.assertEqual(set(state['owned_paths']),expected)
        for p in expected:self.assertNotIn(p,state['baseline']);self.assertTrue((g.ROOT/p).is_file(),p)

if __name__=='__main__':unittest.main(verbosity=2)
