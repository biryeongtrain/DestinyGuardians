#!/usr/bin/env python3
"""W171 asset-only regression; no assumptions about master runtime support."""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w171_aishas_embrace.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(angles):
    # Independent axis-angle oracle, assembled explicitly in JOML order.
    x,y,z=np.radians(angles)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW171AishasEmbraceTest(unittest.TestCase):
    def test_01_exact_geometry_uv_partition(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_moving.json')
        self.assertEqual([source['elements'][i] for i in range(56,60)],moving['elements'])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in range(56,60)],body['elements'])
        self.assertEqual((88,4),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertEqual(92,len(body['elements'])+len(moving['elements']))
        self.assertEqual(list(G['NAMES']),[e['name'] for e in moving['elements']])
        self.assertTrue(set(G['FIXED_NAMES']) <= {e['name'] for e in body['elements']})
        self.assertFalse(set(G['FIXED_NAMES']) & {e['name'] for e in moving['elements']})
        design=read(Path('art/weapons/w123/aishas_embrace/design.json'))
        group=[p['geometry']['name'] for p in design['parts'] if p['group']=='magazine']
        self.assertEqual([e['name'] for e in source['elements'][56:60]],group)
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
        # Actual rear-magazine source axis: rotated negative feed Y, not
        # a guessed front box, receiver, stock or underbarrel module.
        self.assertGreater(G['sample'](.3)[0][0],55)
        self.assertGreater(G['sample'](.3)[0][2],20)
        geo=read(G['SOURCE'])['elements']
        self.assertGreater(np.mean([geo[i]['rotation']['origin'][2] for i in G['MOVING']]),G['GRIP'][2])
        offset=np.array(G['sample'](.35)[2])
        axis=matrix([31.578165,0,0])@np.array([0,-1,0])
        np.testing.assert_allclose(offset/np.linalg.norm(offset),axis,atol=1e-9)
        self.assertEqual([0,0,0],G['sample'](.54)[2])
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
                self.assertEqual(92,count);self.assertLessEqual(count,1000)
        # Existing semantic anchors, feed rotation and fixed underbarrel module.
        self.assertEqual([0,0,0],G['sample'](.78)[2])
        self.assertNotEqual(G['sample'](.54)[0],G['sample'](.78)[0])
        self.assertAlmostEqual(31.578165,parents['moving']['elements'][0]['rotation']['x'])
        self.assertIn('underbarrel_module',[e['name'] for e in parents['body']['elements']])
        self.assertEqual(read(G['SOURCE'])['elements'][45]['rotation']['origin'],list(G['GRIP']))
        self.assertEqual(read(G['SOURCE'])['elements'][56]['rotation']['origin'],list(G['MAG_ANCHOR']))
        self.assertEqual(read(G['SOURCE'])['elements'][59]['rotation']['origin'],[8.,5.62,10.25])
    def test_07_reference_pins_and_honest_limits(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
        self.assertIn('ytb7f7nyrl8',ref['url'])
        self.assertEqual([84.6,86.4],ref['selectedSeconds'])
        self.assertIn('Rear underslung',ref['mechanism']['layout'])
        self.assertTrue(ref['authoredApproximation'])
        self.assertIn('Replacement magazine',ref['observations'][2]['fact']);self.assertIn('occluded',ref['observations'][3]['fact'])
        self.assertEqual(12,len(set(f['sha256'] for f in ref['frames'])))
        self.assertEqual(sorted(f['timestampSeconds'] for f in ref['frames']),[f['timestampSeconds'] for f in ref['frames']])
        from PIL import Image
        for f in ref['frames']:
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['confidence'])
            with Image.open(ROOT/f['path']) as im: self.assertEqual((1280,720),im.size)
        manifest=read(ART/'manifest.json');self.assertFalse(manifest['nativeGameplayVerified']);self.assertFalse(manifest['handIK'])
        self.assertEqual(92,manifest['maxAssembledElements'])
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
    def test_10_magazine_clearance_source_mapping_and_integration_boundary(self):
        geo=read(G['SOURCE'])['elements']; offset=np.array(G['sample'](.35)[2])
        def corners(e):
            rot=e.get('rotation',{}); origin=np.array(rot.get('origin',[0,0,0])); rr=matrix([rot.get(k,0) for k in 'xyz'])
            return [rr@(np.array([x,y,z])-origin)+origin for x in (e['from'][0],e['to'][0]) for y in (e['from'][1],e['to'][1]) for z in (e['from'][2],e['to'][2])]
        points=np.array([v+offset for i in G['MOVING'] for v in corners(geo[i])])
        housing=np.array([v for i in G['FIXED_HOUSING'] for v in corners(geo[i])])
        self.assertLess(points[:,1].max(),housing[:,1].min()-1)
        moving=read(A/f'models/{KEY}_moving.json')['elements']
        self.assertTrue(all(e['name'].startswith('magazine_') for e in moving))
        manifest=read(ART/'manifest.json')
        self.assertFalse(manifest['extractedBones']);self.assertFalse(manifest['integration']['workerRuntimeEdited'])
        self.assertTrue(manifest['integration']['requiresNewMasterRoute']);self.assertEqual(15,manifest['integration']['expectedExistingRouteCount'])
        self.assertIn('guess',manifest['limitations'][0])
        self.assertEqual('destiny:'+KEY,manifest['integration']['requiredMasterModel'])
        rule=next(r for r in read(Path('src/main/resources/weapon_surface_w123/manifest.json'))['targets'] if r['path']=='assets/destiny/models/weapon/scout_rifle/aishas_embrace.json')
        self.assertEqual('assets/destiny/models/weapon_surface_w123/aishas_embrace.json',rule['replacement'])
        self.assertEqual(G['SOURCE_SHA256'],rule['replacementSha256'])
if __name__=='__main__': unittest.main(verbosity=2)
