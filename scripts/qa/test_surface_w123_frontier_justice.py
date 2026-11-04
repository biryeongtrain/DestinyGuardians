#!/usr/bin/env python3
"""Small offline regression suite for the full-only W138 FrontierJustice candidate."""
import base64
import json
from pathlib import Path
import runpy
import unittest

import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_surface_w123_frontier_justice.py'))


class FrontierJusticeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.design=json.loads((ROOT/(G['ART']+'design.json')).read_bytes())
        cls.manifest=json.loads((ROOT/(G['ART']+'manifest.json')).read_bytes())
        cls.model=json.loads((ROOT/G['MODEL']).read_bytes())
        cls.bb=json.loads((ROOT/(G['ART']+'inspection.bbmodel')).read_bytes())
        cls.atlas=np.asarray(Image.open(ROOT/G['TEXTURE']).convert('RGBA'))

    def inside(self,points):
        points=np.asarray(points,float); occupied=np.zeros(len(points),bool)
        for e in self.model['elements']:
            local=points.copy()
            if 'rotation' in e:
                r=e['rotation'];o=np.array(r['origin']);R=G['H']['rotation']({r['axis']:r['angle']})
                local=(local-o)@R+o
            occupied|=np.all((local>np.array(e['from'])+1e-6)&(local<np.array(e['to'])-1e-6),axis=1)
        return occupied

    def test_schema_and_combined_budget(self):
        es=self.model['elements'];m=self.manifest
        self.assertTrue(0<len(es)<=1000)
        self.assertEqual(len(es),m['assembled_elements'])
        self.assertEqual(len(es),m['opaque_cuboids'])
        self.assertEqual(sum(m['groups'].values()),len(es))
        self.assertEqual(m['emitted_faces'],6*len(es))
        self.assertEqual(m['triangle_adapter_elements']+m['contour_elements']+m['alpha_body_elements'],0)
        self.assertTrue(m['full_only']);self.assertFalse(m['native_accepted'])
        self.assertEqual(len({e['name'] for e in es}),len(es))
        for e in es:
            self.assertTrue(np.all(np.array(e['to'])>e['from']))
            self.assertEqual(set(e['faces']),set(G['FACES']))
            self.assertNotIn('vertices',e);self.assertNotIn('triangles',e)
            if 'rotation' in e:
                r=e['rotation'];self.assertEqual(set(r),{'origin','axis','angle'})
                self.assertIn(r['axis'],'xyz');self.assertTrue(np.isfinite(r['angle']))
        json.dumps(self.model,allow_nan=False)

    def test_original_frame_display_and_muzzle(self):
        base=json.loads((ROOT/G['BASE']).read_bytes())
        self.assertEqual(self.model['display'],base['display'])
        self.assertEqual(self.bb['display'],base['display'])
        meta=json.loads((ROOT/G['SOURCE']).read_bytes())['destiny_w30']
        self.assertEqual(self.design['frame']['mapping'],'[8-world.Y*s,8+world.Z*s,8-world.X*s]')
        self.assertEqual(self.design['frame']['anchor'],meta['anchor'])
        self.assertEqual(self.design['frame']['scale'],meta['scale'])
        self.assertEqual(self.design['frame']['hand_origin'],[8,8,8])
        points=np.concatenate([G['vertices'](e) for e in self.model['elements']])
        self.assertAlmostEqual(points[:,2].min(),meta['model_bounds'][0][2],places=6)
        self.assertAlmostEqual(points[:,2].max(),meta['model_bounds'][1][2],places=6)
        self.assertLess(abs(points[:,1].min()-meta['model_bounds'][0][1]),.08)
        self.assertAlmostEqual(points[:,1].max(),meta['model_bounds'][1][1],places=6)
        meshes,_=G['source_meshes']();pts=np.concatenate([m['vertices'] for m in meshes])
        terminal=pts[np.isclose(pts[:,2],pts[:,2].min(),atol=1e-7,rtol=0)]
        np.testing.assert_allclose(self.design['frame']['muzzle_bore_center'],((terminal.min(0)+terminal.max(0))/2)[:2],atol=1e-10)
        self.assertEqual(self.model['textures']['0'],'destiny:item/weapon/w123/frontier_justice')

    def test_representative_real_holes(self):
        for hole in self.design['holes']:
            with self.subTest(hole=hole['name']):
                pts=np.tile(hole['point'],(101,1)).astype(float)
                pts[:,'xyz'.index(hole['ray_axis'])]=np.linspace(*hole['range'],101)
                self.assertFalse(self.inside(pts).any(),hole['name']+' blocked by solid geometry')

    def test_major_parts_are_filled_with_depth(self):
        # Sample short 3-D columns across major volumes, not just two side sheets.
        for y,z in [(11,1),(10.15,0),(11.4,6),(11,14),(7,12),(8.425,7.755)]:
            pts=[[x,y,z] for x in np.linspace(7.7,8.3,7)]
            self.assertTrue(self.inside(pts).all(),(y,z))
        specs={s['geometry']['name']:s for s in self.design['parts']}
        for name in ['rear_receiver','stock_rear_mass','grip_core','forearm_core','magazine']:
            size=np.subtract(specs[name]['geometry']['to'],specs[name]['geometry']['from'])
            self.assertGreater(min(size),.7,name)

    def test_face_uv_opacity_gutters_and_nonoverlap(self):
        self.assertEqual(self.atlas.shape,(1024,1024,4))
        ledger=self.design['atlas']['islands'];self.assertEqual(len(ledger),6*len(self.model['elements']))
        es={e['name']:e for e in self.model['elements']};coverage=np.zeros((1024,1024),np.uint8)
        for island in ledger:
            x,y,x1,y1=island['pixels'];self.assertTrue(x>=2 and y>=2 and x1<=1022 and y1<=1022)
            face=es[island['element']]['faces'][island['face']]
            self.assertEqual(face['texture'],'#0')
            self.assertTrue(np.allclose(np.array(face['uv'])*64,[x,y,x1,y1]))
            tile=self.atlas[y:y1,x:x1]
            self.assertTrue(np.all(tile[:,:,3]==255))
            expected=np.pad(tile,((2,2),(2,2),(0,0)),mode='edge')
            self.assertTrue(np.array_equal(expected,self.atlas[y-2:y1+2,x-2:x1+2]))
            region=coverage[y-2:y1+2,x-2:x1+2];self.assertFalse(region.any());region[:]=1
        # Authored face materials have actual variation, not a flat palette atlas.
        for name,face in [('stock_rear_mass','east'),('rear_receiver','west'),('upper_lower_spine','west')]:
            island=next(a for a in ledger if a['element']==name and a['face']==face)
            x,y,x1,y1=island['pixels'];self.assertGreater(self.atlas[y:y1,x:x1,:3].std(),8)

    def test_reference_input_and_output_hashes(self):
        m=self.manifest
        for rel,expected in m['input_sha256'].items():self.assertEqual(G['sha']((ROOT/rel).read_bytes()),expected,rel)
        for path,expected in m['raw_input_sha256'].items():self.assertEqual(G['sha'](Path(path).read_bytes()),expected,path)
        for rel,expected in m['output_sha256'].items():self.assertEqual(G['sha']((ROOT/rel).read_bytes()),expected,rel)
        ref=next(r for r in json.loads((ROOT/G['REFS']).read_bytes()) if r['id']=='frontier_justice')
        self.assertEqual(m['default_photo_sha256'],ref['sha256'])
        self.assertEqual(G['sha'](G['PHOTO'].read_bytes()),ref['sha256'])
        self.assertEqual(m['generator_sha256'],G['sha']((ROOT/'scripts/generate_surface_w123_frontier_justice.py').read_bytes()))
        self.assertEqual(m['test_sha256'],G['sha'](Path(__file__).read_bytes()))
        self.assertLess(sum((ROOT/p).stat().st_size for p in m['output_sha256']),25*1024*1024)

    def test_original_source_matching(self):
        meshes,meta=G['source_meshes']()
        self.assertEqual(sorted(m['name'] for m in meshes),sorted(meta['source_objects']))
        self.assertEqual(sum(len(m['faces']) for m in meshes),14977)
        pts=np.concatenate([m['vertices'] for m in meshes])
        np.testing.assert_allclose([pts.min(0),pts.max(0)],meta['model_bounds'],atol=2e-6,rtol=0)
        self.assertNotIn('Frontier-Justice.07.000 ATD RAPTOR',[m['name'] for m in meshes])

    def test_recess_back_visible_before_bright_collar(self):
        # Ray sampling catches the bright collar occlusion found in CPU review.
        specs={s['geometry']['name']:s for s in self.design['parts']}
        for name,x,y,start,end in [('bore_deep_back',*self.design['frame']['muzzle_bore_center'],self.design['frame']['muzzle_tip_z'],-6.7),
                                  ('lower_lens',8,10.26,-5.24,-4.8)]:
            zs=np.linspace(start,end,1000);pts=np.c_[np.full(len(zs),x),np.full(len(zs),y),zs]
            occupied=self.inside(pts);self.assertTrue(occupied.any())
            first=pts[np.flatnonzero(occupied)[0]];e=specs[name]['geometry']
            self.assertTrue(np.all(first>=e['from']) and np.all(first<=e['to']),name)
            self.assertEqual(specs[name]['material'],'recess')
            island=next(a for a in self.design['atlas']['islands'] if a['element']==name and a['face']=='north')
            a,b,c,d=island['pixels'];self.assertLess(self.atlas[b:d,a:c,:3].mean(),30)

    def test_editable_inspection_parity(self):
        bb=self.bb;self.assertEqual(bb['resolution'],dict(width=1024,height=1024))
        self.assertEqual(base64.b64decode(bb['textures'][0]['source'].split(',',1)[1]),(ROOT/G['TEXTURE']).read_bytes())
        es={e['name']:e for e in bb['elements']}
        self.assertEqual(set(es),{e['name'] for e in self.model['elements']})
        grouped=[u for g in bb['outliner'] for u in g['children']]
        self.assertEqual(sorted(grouped),sorted(e['uuid'] for e in es.values()))
        for e in self.model['elements']:
            b=es[e['name']];self.assertEqual(b['type'],'cube');self.assertFalse(b['box_uv'])
            self.assertEqual(b['from'],e['from']);self.assertEqual(b['to'],e['to'])
            r=e.get('rotation');expected=[r['angle'] if r and r['axis']==a else 0 for a in 'xyz']
            self.assertEqual(b['rotation'],expected)
            self.assertEqual(b['origin'],r['origin'] if r else [8,8,8])
            for f,v in e['faces'].items():
                self.assertEqual(b['faces'][f]['texture'],0)
                np.testing.assert_allclose(b['faces'][f]['uv'],np.array(v['uv'])*64)

    def test_exact_owned_scope_and_portability(self):
        # This reads the immutable batch contract, not worktree metadata or main git state.
        batch=json.loads((ROOT/'docs/qa/2026-10-26/w138/batch.json').read_bytes())
        feature=next(f for f in batch['features'] if f['name']=='w138-frontier_justice')
        self.assertEqual(set(feature['owned_paths']),G['OWNED'])
        self.assertEqual(len(G['OWNED']),10)
        self.assertTrue(np.all(self.atlas[:,:,3]==255))
        self.assertLess(sum((ROOT/p).stat().st_size for p in G['OWNED'] if (ROOT/p).exists()),25*1024*1024)

    def test_deterministic_regeneration(self):
        outputs=G['generate']()
        self.assertEqual(len(outputs),7)
        self.assertTrue(set(outputs)<=G['OWNED'])
        for rel,data in outputs.items():self.assertEqual((ROOT/rel).read_bytes(),data,rel)


if __name__=='__main__':unittest.main(verbosity=2)
