#!/usr/bin/env python3
"""W164 asset-only regression; no assumptions about master runtime support."""
import copy
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w164_gnawing_hunger.py'))
A=G['A'];KEY=G['KEY'];ART=G['ART'];FP=G['FP']
def read(p): return json.loads((ROOT/p).read_bytes())
def matrix(angles):
    # Independent axis-angle oracle, assembled explicitly in JOML order.
    x,y,z=np.radians(angles)
    rx=np.array([[1,0,0],[0,np.cos(x),-np.sin(x)],[0,np.sin(x),np.cos(x)]])
    ry=np.array([[np.cos(y),0,np.sin(y)],[0,1,0],[-np.sin(y),0,np.cos(y)]])
    rz=np.array([[np.cos(z),-np.sin(z),0],[np.sin(z),np.cos(z),0],[0,0,1]])
    return rx@ry@rz
class ReloadW164GnawingHungerTest(unittest.TestCase):
    def test_01_exact_geometry_uv_partition(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');moving=read(A/f'models/{KEY}_moving.json')
        self.assertEqual([source['elements'][i] for i in range(54,59)],moving['elements'])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in range(54,59)],body['elements'])
        self.assertEqual((109,5),(len(body['elements']),len(moving['elements'])))
        self.assertEqual(source['textures'],body['textures']);self.assertEqual(source['textures'],moving['textures'])
        self.assertEqual(114,len(body['elements'])+len(moving['elements']))
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
        self.assertGreater(np.linalg.norm(G['sample'](.45)[2]),5)
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
        self.assertIn('3XU0AygDiKI',ref['url'])
        from PIL import Image
        for f in ref['frames']:
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            with Image.open(ROOT/f['path']) as im: self.assertEqual((960,540),im.size)
        manifest=read(ART/'manifest.json');self.assertFalse(manifest['nativeGameplayVerified']);self.assertFalse(manifest['handIK'])
        self.assertEqual(114,manifest['maxAssembledElements'])
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
if __name__=='__main__': unittest.main(verbosity=2)
