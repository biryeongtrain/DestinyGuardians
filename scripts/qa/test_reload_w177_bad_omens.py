#!/usr/bin/env python3
"""Focused W177 Bad Omens asset checks; no runtime or native execution."""
import hashlib,json,math,runpy,unittest
from pathlib import Path
from PIL import Image
import numpy as np
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_reload_w177_bad_omens.py'))
A,KEY,ART,FP=(G[k] for k in ('A','KEY','ART','FP'))
def read(p):return json.loads((ROOT/p).read_bytes())
class ReloadW177BadOmensTest(unittest.TestCase):
    def test_canonical_geometry_uv_paint_and_catalog_audio_unchanged(self):
        s=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');rocket=read(A/f'models/{KEY}_magazine.json')
        self.assertEqual(s,body);self.assertEqual(117,len(body['elements']))
        self.assertEqual(s['textures'],rocket['textures']);self.assertEqual(12,len(rocket['elements']))
        self.assertEqual(129,len(body['elements'])+len(rocket['elements']))
        self.assertLessEqual(129,1000)
        for p,h in G['PINS'].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        timing=next(x['timing'] for x in read(Path('src/main/resources/destiny/weapons/w46-timing.json')) if x['id']=='bad_omens')
        self.assertEqual((1,59,25,48.),tuple(timing[k] for k in ('magazine','reloadTicks','rpm','cadenceTicks')))
    def test_rocket_is_a_connected_volume_with_attached_nose_and_tail(self):
        es=read(A/f'models/{KEY}_magazine.json')['elements']
        self.assertTrue(all(e['name'].startswith('authored_rocket_') for e in es))
        spans={}
        source=read(G['SOURCE'])
        for e in es:
            dims=np.array(e['to'])-e['from'];self.assertTrue(np.all(dims>.1));self.assertEqual(6,len(e['faces']))
            self.assertIn(e['faces'],[source['elements'][i]['faces'] for i in (32,40)])
            spans.setdefault(e['name'].rsplit('_',1)[0],(e['from'][2],e['to'][2]))
            self.assertEqual([8,12.2245],e['rotation']['origin'][:2])
        chain=[spans['authored_rocket_'+n] for n in ('tip','nose','shoulder','body','tail_band','tail_plug')]
        for a,b in zip(chain,chain[1:]):self.assertGreater(a[1],b[0])
        self.assertGreater(chain[-1][1]-chain[0][0],8)
        self.assertGreater(es[0]['to'][0]-es[0]['from'][0],.8)
    def test_fp_only_graph_progress_boundaries_grips_and_exact_ads_inspect(self):
        canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model']
        self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
        self.assertEqual('minecraft:display_context',graph['property']);self.assertEqual(canonical['model'],graph['fallback'])
        self.assertEqual(['ads','inspect'],[c['when'] for c in graph['fallback']['cases']])
        c=graph['cases'][0];self.assertEqual(list(FP),c['when']);rg=c['model'];self.assertEqual(1,rg['index']);self.assertEqual(canonical['model'],rg['fallback'])
        self.assertEqual(21,len(rg['entries']))
        for i,e in enumerate(rg['entries']):
            self.assertEqual(i/20,e['threshold']);self.assertEqual(0,e['model']['index'])
            for branch,grip in [('on_true','twohand'),('on_false','native')]:
                self.assertEqual([f'destiny:{KEY}_{i:02}_{p}_{grip}' for p in ('body','magazine')],[m['model'] for m in e['model'][branch]['models']])
        for p,want in [(-1,None),(-.001,None),(0,0),(.049,0),(.05,1),(.999,19),(1,20)]:
            matches=[i for i,e in enumerate(rg['entries']) if p>=e['threshold']];self.assertEqual(want,matches[-1] if matches else None)
    def test_body_endpoints_exact_payload_hidden_nonfp_displays_preserved(self):
        for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
            accepted=read(path)['display']
            for i in range(21):
                for part in ('body','magazine'):
                    child=read(A/f'models/{KEY}_{i:02}_{part}_{grip}.json');self.assertEqual({'parent','display'},set(child))
                    self.assertEqual(f'destiny:{KEY}_{part}',child['parent'])
                    for ctx in set(accepted)-set(FP):self.assertEqual(accepted[ctx],child['display'][ctx])
                    for ctx in FP:
                        d=child['display'][ctx]
                        self.assertTrue(all(math.isfinite(v) for arr in d.values() for v in arr))
                        if i in (0,20):
                            self.assertEqual(accepted[ctx]['rotation'],d['rotation']);self.assertEqual(accepted[ctx]['translation'],d['translation'])
                            self.assertEqual(accepted[ctx]['scale'] if part=='body' else [0,0,0],d['scale'])
        self.assertEqual(0,G['payload_visibility'](0));self.assertEqual(0,G['payload_visibility'](1));self.assertEqual(1,G['payload_visibility'](.4))
    def test_bespoke_two_lift_rear_load_motion_and_approach(self):
        sample=G['sample']
        self.assertGreater(sample(.18)[0][0],70);self.assertLess(sample(.4)[0][0],35);self.assertGreater(sample(.64)[0][0],70)
        self.assertGreater(sample(.4)[2][2],8);self.assertEqual([0,0,0],sample(.64)[2]);self.assertEqual([0,0,0],sample(1)[0])
        # +Z approach from aft, then -Z insertion; never a downward box-mag exchange.
        self.assertGreater(sample(.4)[2][2],sample(.48)[2][2]);self.assertGreater(sample(.48)[2][2],sample(.58)[2][2])
        for bad in (-.01,1.01,float('inf'),float('nan')):
            with self.assertRaises(ValueError):sample(bad)
    def test_twelve_inspected_actual_same_weapon_frames(self):
        ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertTrue(ref['authoredApproximation'])
        self.assertEqual('https://www.youtube.com/watch?v=fLyWxsBImP8',ref['url']);self.assertEqual('Mudcat',ref['creator']);self.assertEqual([28.8,31.4],ref['selectedSeconds'])
        self.assertIn('Bad Omens',ref['identityVerification']['evidence']);self.assertEqual(12,len(ref['frames']));self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
        for f in ref['frames']:
            self.assertEqual(f['sourceFrameIndex']/30,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL']);self.assertTrue(f['observation'])
            self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
            with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
    def test_manifest_hashes_ownership_and_honest_boundary(self):
        m=read(ART/'manifest.json');self.assertEqual(129,m['maxAssembledElements']);self.assertEqual(90,len(G['expected_output_paths']()))
        for field in ('sourceSha256','sha256','canonicalSha256'):
            for p,h in m[field].items():self.assertEqual(h,hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),p)
        for field in ('nativeGameplayVerified','thirdPersonReloadClaimed','handIK','extractedBones','mechanicsOrAudioChanged'):self.assertFalse(m[field])
        self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertTrue(m['integration']['masterOwnsRegistryRuntime'])
        owned=set(next(f['owned_paths'] for f in json.loads(Path('/private/tmp/w177-manifest.json').read_bytes())['features'] if f['name']=='w177-bad-omens-reload'))
        self.assertTrue({str(p) for p in G['expected_output_paths']()}<=owned)
        for p in ('comparison.png','storyboard.png'):
            with Image.open(ROOT/ART/p) as im:self.assertGreater(im.width,1000);self.assertGreater(im.height,1000)
if __name__=='__main__':unittest.main(verbosity=2)
