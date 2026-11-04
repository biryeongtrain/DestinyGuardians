#!/usr/bin/env python3
"""W170 asset-only regression; no assumptions about master runtime support."""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w170_retraced_path.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(angles):
    # Independent axis-angle oracle, assembled explicitly in JOML order.
    x,y,z=np.radians(angles)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW170RetracedPathTest(unittest.TestCase):
    def test_01_exact_geometry_uv_partition(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_moving.json')
        self.assertEqual([source['elements'][i] for i in range(78,82)],moving['elements'])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in range(78,82)],body['elements'])
        self.assertEqual((95,4),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertEqual(99,len(body['elements'])+len(moving['elements']))
        self.assertEqual(list(G['NAMES']),[e['name'] for e in moving['elements']])
        self.assertTrue(set(G['FIXED_NAMES']) <= {e['name'] for e in body['elements']})
        self.assertFalse(set(G['FIXED_NAMES']) & {e['name'] for e in moving['elements']})
        design=read(Path('art/weapons/w123/retraced_path/design.json'))
        group=[p['geometry']['name'] for p in design['parts'] if p['group']=='magazine']
        self.assertEqual([e['name'] for e in source['elements'][78:82]],group)
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
    def test_04_composed_rotated_magazine_offset_oracle(self):
        source=read(G['SOURCE'])['display'];two=read(G['TWOHAND'])['display']
        for i in range(1,20):
            angles,shift,offset=G['sample'](i/20);b=matrix(angles)
            for grip in ('native','twohand'):
                body=read(A/f'models/{KEY}_{i:02}_body_{grip}.json')['display']
                moving=read(A/f'models/{KEY}_{i:02}_moving_{grip}.json')['display']
                for hand in FP:
                    r=matrix(source[hand]['rotation']);comp=np.eye(3) if grip=='native' else matrix(two[hand]['rotation'])@r.T
                    expected=comp@r@b@(np.array(offset)*source[hand]['scale'][0])
                    actual=np.array(moving[hand]['translation'])-np.array(body[hand]['translation'])
                    np.testing.assert_allclose(actual,expected,atol=2e-9)
                    np.testing.assert_allclose(matrix(body[hand]['rotation']),comp@r@b,atol=3e-10)
                    self.assertEqual(body[hand]['rotation'],moving[hand]['rotation'])
        # Source pack is forward of pistol grip; the upward side-roll differs
        # from the muzzle-vertical Bygones curve. Hidden travel remains authored.
        self.assertLess(G['sample'](.09)[0][0],0)
        self.assertGreater(G['sample'](.4)[0][0],35)
        self.assertLess(G['sample'](.4)[0][0],45)
        self.assertGreater(G['sample'](.4)[0][2],20)
        geo=read(G['SOURCE'])['elements']
        self.assertLess(max(geo[i]['to'][2] for i in G['MOVING']),G['GRIP'][2])
        offset=np.array(G['sample'](.4)[2])
        axis=np.array([0,-3.78,.87]); axis/=np.linalg.norm(axis)
        np.testing.assert_allclose(offset/np.linalg.norm(offset),axis,atol=1e-9)
        self.assertEqual([0,0,0],G['sample'](.70)[2])
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
    def test_06_all_assembled_samples_within_budget_and_exact_nonfp(self):
        parents={part:read(A/f'models/{KEY}_{part}.json') for part in ('body','moving')}
        for grip,src in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            display=read(src)['display']
            for i in range(21):
                count=0
                for part in ('body','moving'):
                    m=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertNotIn('elements',m)
                    count+=len(parents[part]['elements'])
                    for ctx in set(display)-set(FP):self.assertEqual(display[ctx],m['display'][ctx])
                    for hand in FP:
                        for k in ('rotation','translation','scale'):self.assertTrue(all(math.isfinite(v) for v in m['display'][hand][k]))
                self.assertEqual(99,count);self.assertLessEqual(count,1000)
        self.assertEqual([0,0,0],G['sample'](.76)[2])
        self.assertNotEqual(G['sample'](.70)[0],G['sample'](.76)[0])  # visible base-press beat
        # Preserve actual slot/UV geometry, not a freshly invented magwell or legacy rip.
        self.assertAlmostEqual(77.03859814900798,parents['moving']['elements'][0]['rotation']['angle'])
        self.assertEqual(24,len([e for e in parents['body']['elements'] if e['name'].startswith('power_disc_')]))
        self.assertEqual([8,9.145,9.61],list(G['GRIP']))
        self.assertEqual(read(G['SOURCE'])['elements'][76]['rotation']['origin'],list(G['GRIP']))
    def test_07_reference_pins_and_honest_limits(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('Y8qyeBBXBgA',ref['url'])
        self.assertEqual([247.15,248.85],ref['selectedSeconds'])
        self.assertIn('Underslung',ref['mechanism']['layout'])
        self.assertTrue(ref['authoredApproximation'])
        self.assertIn('occluded',ref['observations'][2]['fact']);self.assertIn('Replacement edge',ref['observations'][3]['fact'])
        self.assertEqual(12,len(set(f['sha256'] for f in ref['frames'])))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        from PIL import Image
        for f in ref['frames']:
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im: self.assertEqual((1280,720),im.size)
        manifest=read(ART/'manifest.json');self.assertFalse(manifest['nativeGameplayVerified']);self.assertFalse(manifest['handIK'])
        self.assertEqual(99,manifest['maxAssembledElements'])
        self.assertLessEqual(manifest['maxAssembledElements'],1000)
        self.assertEqual(hashlib.sha256((ROOT/G['SOURCE']).read_bytes()).hexdigest(),manifest['sourceGeometryFileSha256'])
        self.assertEqual(G['sha'](G['encode'](read(G['SOURCE'])['elements'])),manifest['sourceElementsAndUVSha256'])
        for part in ('body','moving'):
            self.assertEqual(G['sha'](G['encode'](read(A/f'models/{KEY}_{part}.json')['elements'])),manifest['partElementsAndUVSha256'][part])
        for p,digest in manifest['sourceSha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_08_output_hashes_and_pack_count(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths)
        self.assertEqual(87,len([p for p in paths if p.startswith(str(A))]))
        for p,digest in m['sha256'].items(): self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
    def test_09_read_only_deterministic_verify(self):
        paths=G['expected_output_paths']();before={p:((ROOT/p).stat().st_mtime_ns,(ROOT/p).read_bytes()) for p in paths}
        generated=G['generate']();self.assertEqual(paths,set(generated))
        for p,data in generated.items():
            self.assertEqual(before[p][1],data,str(p));self.assertEqual(before[p][0],(ROOT/p).stat().st_mtime_ns,str(p))
        for bad in (float('nan'),float('inf'),-.1,1.1):
            with self.assertRaises(ValueError): G['sample'](bad)
    def test_10_pack_clearance_uses_rotated_source_solids_and_fixed_disc(self):
        geo=read(G['SOURCE'])['elements']; offset=np.array(G['sample'](.4)[2])
        def corners(e):
            rot=e.get('rotation',{}); origin=np.array(rot.get('origin',[0,0,0])); angles=[0,0,0]
            if 'axis' in rot: angles['xyz'.index(rot['axis'])]=rot['angle']
            rr=matrix(angles)
            return [rr@(np.array([x,y,z])-origin)+origin for x in (e['from'][0],e['to'][0]) for y in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]
        points=np.array([v+offset for i in G['MOVING'] for v in corners(geo[i])])
        receiver=np.array(corners(geo[49]))
        self.assertLess(points[:,1].max(),receiver[:,1].min()-1)
        moving=read(A/f'models/{KEY}_moving.json')['elements']
        self.assertFalse(any(e['name'].startswith(('power_disc_','receiver_','upper_rail','lower_rail')) for e in moving))
        manifest=read(ART/'manifest.json')
        self.assertFalse(manifest['extractedBones']);self.assertFalse(manifest['integration']['workerRuntimeEdited'])
        self.assertTrue(manifest['integration']['requiresNewMasterRoute']);self.assertEqual(14,manifest['integration']['expectedExistingRouteCount'])
        self.assertIn('guess',manifest['limitations'][0])
if __name__=='__main__': unittest.main(verbosity=2)
