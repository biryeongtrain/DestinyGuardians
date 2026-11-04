#!/usr/bin/env python3
"""Focused Bite of the Fox asset checks; runtime/native integration belongs to master."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w177_bite_of_the_fox.py'))
A,KEY,ART,FP=(G[k] for k in ('A','KEY','ART','FP'))
def read(p):return json.loads((ROOT/p).read_bytes())
class ReloadW177BiteOfTheFoxTest(unittest.TestCase):
    def test_existing_semantic_connected_box_magazine_and_exact_uv(self):
        source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');mag=read(A/f'models/{KEY}_magazine.json')
        self.assertEqual([source['elements'][i] for i in (51,52,53)],mag['elements'])
        self.assertEqual([e for i,e in enumerate(source['elements']) if i not in (51,52,53)],body['elements'])
        self.assertEqual((109,3),(len(body['elements']),len(mag['elements'])))
        for p in (body,mag):self.assertEqual(source['textures'],p['textures'])
        design=read(Path('art/weapons/w123/bite_of_the_fox/design.json'))
        self.assertEqual(list(G['NAMES']),[p['geometry']['name'] for p in design['parts']['full'] if p['group']=='magazine'])
        box,floor,catch=mag['elements']
        # Real volume and overlapping connection of floor/catch to the box.
        self.assertTrue(all(b-a>.5 for a,b in zip(box['from'],box['to'])))
        for e in (floor,catch):
            self.assertTrue(all(min(box['to'][k],e['to'][k])>max(box['from'][k],e['from'][k]) for k in range(3)))
        self.assertTrue({'bolt_shaft','bolt_knob','receiver','pistol_grip','guard_lower','stock_comb'}<={e['name'] for e in body['elements']})
        self.assertEqual(112,len(body['elements'])+len(mag['elements']))
    def test_exact_endpoints_both_grips_and_unmodified_nonfp_children(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            display=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    child=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json')
                    self.assertEqual({'parent','display'},set(child));self.assertEqual('destiny:'+KEY+'_'+part,child['parent'])
                    if i in (0,20):self.assertEqual(display,child['display'])
                    for ctx in set(display)-set(FP):self.assertEqual(display[ctx],child['display'][ctx])
                    for ctx in FP:
                        self.assertEqual(display[ctx]['scale'],child['display'][ctx]['scale'])
                        self.assertTrue(all(math.isfinite(v) for key in ('rotation','translation','scale') for v in child['display'][ctx][key]))
    def test_fp_progress_float1_grip_flag0_canonical_fallback(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model'];dispatch=graph['cases'][0]['model']
        self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(canonical['model'],dispatch['fallback'])
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual(['ads','inspect'],[c['when'] for c in graph['fallback']['cases']])
        self.assertEqual(list(FP),graph['cases'][0]['when']);self.assertEqual(1,dispatch['index'])
        self.assertEqual(21,len(dispatch['entries']))
        for i,e in enumerate(dispatch['entries']):
            self.assertEqual(i/20,e['threshold']);cond=e['model'];self.assertEqual(0,cond['index'])
            for branch,grip in [('on_true','twohand'),('on_false','native')]:
                self.assertEqual('minecraft:composite',cond[branch]['type'])
                self.assertEqual([f'destiny:{KEY}_{i:02}_{part}_{grip}' for part in ('body','magazine')],[m['model'] for m in cond[branch]['models']])
        for p,want in [(-1,None),(-.001,None),(0,0),(.049,0),(.05,1),(.999,19),(1,20)]:
            ids=[i for i,e in enumerate(dispatch['entries']) if p>=e['threshold']];self.assertEqual(want,ids[-1] if ids else None)
    def test_bespoke_receiver_well_exchange_and_seated_action_roll(self):
        self.assertEqual((51,52,53),G['MOVING']);self.assertLess(G['MAG_ANCHOR'][2],G['GRIP'][2])
        self.assertLess(G['sample'](.32)[2][1],-3)
        mag=read(A/f'models/{KEY}_magazine.json')['elements']
        lower=read(G['SOURCE'])['elements'][48]
        self.assertLess(max(e['to'][1] for e in mag)+G['sample'](.32)[2][1],lower['from'][1]-.5)
        self.assertLess(G['sample'](.32)[0][2],-30);self.assertGreater(G['sample'](.62)[0][2],20)
        for p in (.46,.54,.62,.72,.80,.88,.95,1):self.assertEqual([0,0,0],G['sample'](p)[2])
        self.assertLess(max(k[1][0] for k in G['KEYS']),30) # long rifle lift, not 46deg pistol curve
    def test_actual_nameplate_and_eleven_reload_frames(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
        self.assertEqual('https://www.youtube.com/watch?v=moebSjSRyoE',ref['url']);self.assertEqual('Nexas Gaming',ref['creator'])
        self.assertEqual(32.,ref['identityVerification']['identityFrameSeconds']);self.assertIn('BITE OF THE FOX',ref['identityVerification']['evidence'])
        self.assertEqual([158.8,161.4],ref['selectedSeconds']);self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/60,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL'])
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest());self.assertTrue(f['observation'])
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
    def test_manifest_hashes_counts_and_honest_scope(self):
        m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
        self.assertEqual({str(p) for p in G['expected_output_paths']()},paths);self.assertEqual(90,len(paths))
        self.assertEqual(87,sum(p.startswith(str(A)) for p in paths));self.assertEqual(112,m['maxAssembledElements']);self.assertEqual(0,m['addedElements'])
        for mapping in (m['sha256'],m['sourceSha256'],m['canonicalSha256']):
            for p,digest in mapping.items():self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for flag in ('nativeGameplayVerified','handIK','extractedBones','thirdPersonReloadClaim','mechanicsOrAudioChanged'):self.assertFalse(m[flag])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual(21,m['integration']['masterRoute'])
        self.assertEqual([],m['authoredHiddenDetails'])
    def test_canonical_mechanics_and_existing_audio_pins(self):
        for p,digest in G['PINS'].items():self.assertEqual(digest,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='bite_of_the_fox')
        self.assertEqual((3,67,72),(timing['magazine'],timing['reloadTicks'],timing['rpm']))
    def test_sample_domain_and_owned_output_contract(self):
        for bad in (float('nan'),float('inf'),-.01,1.01):
            with self.assertRaises(ValueError):G['sample'](bad)
        for p in (0,1):self.assertEqual(([0,0,0],[0,0,0],[0,0,0]),G['sample'](p))
        self.assertEqual(90,len(G['expected_output_paths']()))
        scope=Path('/private/tmp/w177-manifest.json')
        if scope.exists():
            owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w177-bite-of-the-fox-reload'))
            self.assertEqual(106,len(owned));self.assertTrue({str(p) for p in G['expected_output_paths']()}<=owned)
    def test_offline_evidence_images_present(self):
        for name,size in [('comparison.png',(1440,1410)),('storyboard.png',(1600,1620))]:
            with Image.open(ROOT/ART/name) as im:self.assertEqual(size,im.size)
if __name__=='__main__':unittest.main(verbosity=2)
