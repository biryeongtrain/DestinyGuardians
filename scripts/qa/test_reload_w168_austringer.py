#!/usr/bin/env python3
"""W168 asset-only regression; no assumptions about master runtime support."""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w168_austringer.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(angles):
    # Independent axis-angle oracle, assembled explicitly in JOML order.
    x,y,z=np.radians(angles)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW168AustringerTest(unittest.TestCase):
    def test_01_exact_geometry_uv_partition(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_moving.json')
        self.assertEqual(source['elements'][32:44],moving['elements'])
        self.assertEqual(source['elements'][:32]+source['elements'][44:],body['elements'])
        self.assertEqual((114,12),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertEqual(126,len(body['elements'])+len(moving['elements']))
        self.assertEqual(list(G['NAMES']),[e['name'] for e in moving['elements']])
        fixed={'Cylinder_lower_frame','Breech','Top_frame','Top_gold_rod'}
        self.assertTrue(fixed <= {e['name'] for e in body['elements']})
        self.assertFalse(fixed & {e['name'] for e in moving['elements']})
        design=read(Path('art/weapons/w123/austringer/design.json'))
        self.assertEqual([p['geometry'] for p in design['parts']],source['elements'])
        # Shared receiver label cannot be used as the moving group wholesale.
        self.assertEqual({'receiver'},{design['parts'][i]['group'] for i in range(32,48)})
    def test_02_exact_hip_endpoints_all_contexts(self):
        for grip,src in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            expected=read(src)['display']
            for i in (0,20):
                for part in ('body','moving'):
                    m=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual(expected,m['display']);self.assertEqual({'parent','display'},set(m))
    def test_03_graph_fallbacks_and_all_references(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual({k:v for k,v in canonical.items() if k!='model'},{k:v for k,v in wrapper.items() if k!='model'})
        self.assertEqual(list(FP),graph['cases'][0]['when'])
        dispatch=graph['cases'][0]['model'];self.assertEqual(1,dispatch['index']);self.assertEqual(canonical['model'],dispatch['fallback'])
        self.assertEqual(21,len(dispatch['entries']))
        for i,e in enumerate(dispatch['entries']):
            self.assertEqual(i/20,e['threshold']);c=e['model'];self.assertEqual(0,c['index'])
            for branch,grip in [('on_true','twohand'),('on_false','native')]:
                composite=c[branch];self.assertEqual('minecraft:composite',composite['type']);self.assertEqual(2,len(composite['models']))
                for part,m in zip(('body','moving'),composite['models']):
                    self.assertEqual(f'destiny:{KEY}_{i:02}_{part}_{grip}',m['model'])
                    child=read(A/('models/'+m['model'].split(':')[1]+'.json'))
                    self.assertEqual(f'destiny:{KEY}_{part}',child['parent'])
        # Negative/inactive selects fallback; exact 0 and 1 select assembled HIP.
        for progress,expected in [(-1,None),(0,0),(.049,0),(.05,1),(.999,19),(1,20)]:
            matches=[i for i,e in enumerate(dispatch['entries']) if progress>=e['threshold']]
            self.assertEqual(expected,matches[-1] if matches else None)
    def test_04_independent_cylinder_transform_point_oracle(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display']
        hinge=np.array(G['HINGE']);pivot=np.array(G['GRIP'])
        points=[hinge,np.array([8,12.43,4.34]),np.array([7,12,2.82])]
        for i in range(1,20):
            angles,shift,cylinder=G['sample'](i/20);b=matrix(angles);c=matrix(cylinder)
            for grip in ('native','twohand'):
                moving=read(A/f'models/{KEY}_{i:02}_moving_{grip}.json')['display']
                body=read(A/f'models/{KEY}_{i:02}_body_{grip}.json')['display']
                for hand in FP:
                    idle=source[hand];r=matrix(idle['rotation']);scale=idle['scale'][0]
                    comp=np.eye(3) if grip=='native' else matrix(two[hand]['rotation'])@r.T
                    carrier=np.zeros(3) if grip=='native' else np.array(two[hand]['translation'])-comp@np.array(idle['translation'])
                    for point in points:
                        local=c@(point-hinge)+hinge
                        local=b@(local-pivot)+pivot
                        expected=comp@(np.array(idle['translation'])+shift+r@(scale*(local-8)))+carrier
                        actual=np.array(moving[hand]['translation'])+matrix(moving[hand]['rotation'])@(scale*(point-8))
                        np.testing.assert_allclose(actual,expected,atol=3e-9)
                    np.testing.assert_allclose(matrix(moving[hand]['rotation']),comp@r@b@c,atol=3e-10)
                    if .1<=i/20<=.75:
                        self.assertNotEqual(body[hand]['rotation'],moving[hand]['rotation'])
        self.assertGreater(G['sample'](.35)[0][0],60)
        self.assertEqual([0,0,78],G['sample'](.35)[2])
        self.assertEqual([0,0,0],G['sample'](.90)[2])
    def test_05_grip_pivot_preserved_and_nonfp_unchanged(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display'];h=np.array(G['GRIP'])-8
        for grip,accepted in [('native',source),('twohand',two)]:
            for p in (.1,.45,.75,.95):
                display=G['pose_display'](source,two,p,'body',grip)
                _,shift,_=G['sample'](p)
                for hand in FP:
                    idle=source[hand];r=matrix(idle['rotation']);s=idle['scale'][0]
                    expected=np.array(idle['translation'])+r@(s*h)+shift
                    if grip=='twohand':
                        c=matrix(two[hand]['rotation'])@r.T
                        expected=c@expected+np.array(two[hand]['translation'])-c@np.array(idle['translation'])
                    actual=np.array(display[hand]['translation'])+matrix(display[hand]['rotation'])@(s*h)
                    np.testing.assert_allclose(actual,expected,atol=2e-9)
                for context in set(accepted)-set(FP): self.assertEqual(accepted[context],display[context])
    def test_06_reference_pins_and_honest_limits(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('TPWRjqb_O5U',ref['url'])
        self.assertEqual([11.7,13.4],ref['selectedSeconds'])
        self.assertIn('swing-out cylinder',ref['mechanism']['layout'])
        self.assertTrue(ref['authoredApproximation'])
        self.assertIn('occluded',ref['observations'][2]['fact']);self.assertEqual([],ref['pendingReferenceSlots'])
        self.assertEqual(12,len(set(f['sha256'] for f in ref['frames'])))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        from PIL import Image
        for f in ref['frames']:
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im: self.assertEqual((960,540),im.size)
        manifest=read(ART/'manifest.json');self.assertFalse(manifest['nativeGameplayVerified']);self.assertFalse(manifest['handIK'])
        self.assertEqual(126,manifest['maxAssembledElements'])
        self.assertLessEqual(manifest['maxAssembledElements'],1000)
        self.assertEqual(hashlib.sha256((ROOT/G['SOURCE']).read_bytes()).hexdigest(),manifest['sourceGeometryFileSha256'])
        self.assertEqual(G['sha'](G['encode'](read(G['SOURCE'])['elements'])),manifest['sourceElementsAndUVSha256'])
        for part in ('body','moving'):
            self.assertEqual(G['sha'](G['encode'](read(A/f'models/{KEY}_{part}.json')['elements'])),manifest['partElementsAndUVSha256'][part])
        for p,digest in manifest['sourceSha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_07_output_hashes_and_pack_count(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(87,len([p for p in paths if p.startswith(str(A))]))
        for p,digest in m['sha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_08_read_only_deterministic_verify(self):
        paths=G['expected_output_paths']();before={p:((ROOT/p).stat().st_mtime_ns,(ROOT/p).read_bytes()) for p in paths}
        generated=G['generate']();self.assertEqual(paths,set(generated))
        for p,data in generated.items():
            self.assertEqual(before[p][1],data,str(p));self.assertEqual(before[p][0],(ROOT/p).stat().st_mtime_ns,str(p))
        for bad in (float('nan'),float('inf'),-.1,1.1):
            with self.assertRaises(ValueError): G['sample'](bad)
    def test_09_open_cylinder_clearance_from_fixed_lower_frame(self):
        source=read(G['SOURCE'])['elements'];hinge=np.array(G['HINGE'])
        c=matrix(G['sample'](.35)[2]);xs=[]
        for e in source[32:44]:
            center=np.array(e['rotation']['origin']);rot=matrix([e['rotation'][axis] for axis in 'xyz'])
            for x in (e['from'][0],e['to'][0]):
                for y in (e['from'][1],e['to'][1]):
                    for z in (e['from'][2],e['to'][2]):
                        point=rot@(np.array([x,y,z])-center)+center
                        xs.append((c@(point-hinge)+hinge)[0])
        self.assertLess(max(xs),source[44]['from'][0])
        self.assertGreater(source[44]['from'][0]-max(xs),.10)
    def test_10_geometry_budget_resolves_every_assembled_sample(self):
        for i in range(21):
            for grip in ('native','twohand'):
                count=0
                for part in ('body','moving'):
                    child=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertNotIn('elements',child)
                    parent=read(A/('models/'+child['parent'].split(':')[1]+'.json'))
                    count+=len(parent['elements'])
                self.assertEqual(126,count);self.assertLessEqual(count,1000)
if __name__=='__main__': unittest.main(verbosity=2)
