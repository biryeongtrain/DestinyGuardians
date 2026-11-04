#!/usr/bin/env python3
"""Focused W178 phased shotgun asset verification; no server/native execution."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_insert_w178_first_in_last_out.py'))
A,KEY,ART,FP=(G[k] for k in ('A','KEY','ART','FP'))
def read(p):return json.loads((ROOT/p).read_bytes())
def child(phase,i,part,grip):return read(A/f'models/{KEY}_{phase}_{i:02}_{part}_{grip}.json')
def resolve(node,context,progress,grip=False,mode=''):
 kind=node['type']
 if kind=='minecraft:model':return [node['model']]
 if kind=='minecraft:composite':return sum((resolve(m,context,progress,grip,mode) for m in node['models']),[])
 if kind=='minecraft:condition':return resolve(node['on_true' if grip else 'on_false'],context,progress,grip,mode)
 if kind=='minecraft:select':
  value=context if node['property']=='minecraft:display_context' else mode
  for case in node['cases']:
   if value in (case['when'] if isinstance(case['when'],list) else [case['when']]):return resolve(case['model'],context,progress,grip,mode)
  return resolve(node['fallback'],context,progress,grip,mode)
 if kind=='minecraft:range_dispatch':
  matches=[e for e in node['entries'] if e['threshold']<=progress]
  return resolve(matches[-1]['model'] if matches else node['fallback'],context,progress,grip,mode)
 raise AssertionError(kind)
class InsertW178FirstInLastOutTest(unittest.TestCase):
 def test_exact_canonical_geometry_uv_atlas_and_109_element_budget(self):
  source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');shell=read(A/f'models/{KEY}_shell.json')
  self.assertEqual(source,body);self.assertEqual((97,12),(len(body['elements']),len(shell['elements'])))
  self.assertEqual(source['textures'],shell['textures'])
  for e in shell['elements']:
   self.assertTrue(all(b-a>0 for a,b in zip(e['from'],e['to'])))
   self.assertGreater(min(e['to'][k]-e['from'][k] for k in range(2)),.2)
   uvindex=34 if 'case' in e['name'] else 58
   uv=source['elements'][uvindex]['faces']['east']['uv'];u=(uv[0]+uv[2])/2;v=(uv[1]+uv[3])/2
   for face in e['faces'].values():self.assertEqual([u,v,u,v],face['uv'])
  for a,b in zip(shell['elements'][::4],shell['elements'][4::4]):
   self.assertTrue(all(min(a['to'][k],b['to'][k])>max(a['from'][k],b['from'][k]) for k in range(3)))
  rules=read(Path('src/main/resources/weapon_surface_w123/manifest.json'))['targets']
  rule=next(r for r in rules if r['path'].endswith('weapon/shotgun/first_in_last_out.json'))
  self.assertEqual(str(G['SOURCE']).removeprefix('src/main/resources/'),rule['replacement'])
  self.assertEqual(G['PINS'][str(G['SOURCE'])],rule['replacementSha256'])
  self.assertLessEqual(len(body['elements'])+len(shell['elements']),1000)
 def test_exact_hip_endpoints_and_held_body_phase_seams(self):
  for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
   expected=read(path)['display']
   self.assertEqual(expected,child('initial',0,'body',grip)['display'])
   self.assertEqual(expected,child('return',20,'body',grip)['display'])
   held=[child(phase,i,'body',grip)['display'] for phase,i in [('initial',20),('loop',0),('loop',20),('return',0)]]
   self.assertTrue(all(d==held[0] for d in held))
   self.assertNotEqual(expected,held[0])
   for phase,i in [('initial',0),('initial',20),('loop',0),('loop',20),('return',0),('return',20)]:
    for hand in FP:self.assertEqual([0,0,0],child(phase,i,'shell',grip)['display'][hand]['scale'])
 def test_all_252_children_parent_reference_finite_rigid_and_nonfp_scope(self):
  for phase in G['PHASES']:
   for i in range(21):
    for part in G['PARTS']:
     for grip,path in [('native',G['SOURCE']),('twohand',G['TWOHAND'])]:
      c=child(phase,i,part,grip);expected=read(path)['display']
      self.assertEqual({'parent','display'},set(c));self.assertEqual('destiny:'+KEY+'_'+part,c['parent'])
      for ctx,d in c['display'].items():
       for key in ('rotation','translation','scale'):self.assertTrue(all(math.isfinite(v) for v in d[key]))
       if ctx not in FP:
        if part=='body':self.assertEqual(expected[ctx],d)
        else:self.assertEqual([0,0,0],d['scale'])
       else:self.assertEqual(expected[ctx]['scale'] if part=='body' or G['shell_visible'](phase,i/20) else [0,0,0],d['scale'])
 def test_float4_63_samples_flag0_and_canonical_mode_priority(self):
  canonical=read(G['ITEM']);wrapper=read(A/f'items/{KEY}.json');graph=wrapper['model'];context=graph['cases'][0]
  self.assertEqual(canonical['model'],graph['fallback']);self.assertEqual(list(FP),context['when'])
  modes=context['model'];self.assertEqual(['ads','inspect'],[c['when'] for c in modes['cases']])
  for c in modes['cases']:self.assertEqual(canonical['model'],c['model'])
  dispatch=modes['fallback'];self.assertEqual(4,dispatch['index']);self.assertEqual(63,len(dispatch['entries']))
  self.assertEqual(canonical['model'],dispatch['fallback']);self.assertEqual(canonical['hand_animation_on_swap'],wrapper['hand_animation_on_swap'])
  for phaseindex,phase in enumerate(G['PHASES']):
   for i in range(21):
    entry=dispatch['entries'][phaseindex*21+i];self.assertEqual(phaseindex*2+i/20,entry['threshold'])
    self.assertEqual(0,entry['model']['index'])
    # Existing transport may add .001 for an owned float collision; no new offset policy.
    for delta in (0,.001):
     for grip in (False,True):
      ids=resolve(graph,FP[0],phaseindex*2+i/20+delta,grip)
      self.assertEqual([f'destiny:{KEY}_{phase}_{i:02}_{part}_{"twohand" if grip else "native"}' for part in G['PARTS']],ids)
  for ctx in (*FP,'thirdperson_righthand','thirdperson_lefthand','gui','ground','fixed','head'):
   for mode in ('','ads','inspect'):
    for grip in (False,True):
     for progress in (-1,0,2.55,5):
      if ctx not in FP or mode or progress<0:self.assertEqual(resolve(canonical['model'],ctx,progress,grip,mode),resolve(graph,ctx,progress,grip,mode))
 def test_one_shell_below_receiver_and_hidden_only_after_seating(self):
  self.assertEqual(G['HOLD'][0],tuple(G['sample']('loop',0)[0]))
  for i in range(21):
   angles=G['sample']('loop',i/20)[0]
   self.assertLess(max(abs(a-b) for a,b in zip(angles,G['HOLD'][0])),1.01)
  for phase,approach,contact,seat in [('initial',.4,.7,.87),('loop',.15,.55,.8)]:
   a=G['sample'](phase,approach)[2];b=G['sample'](phase,contact)[2];c=G['sample'](phase,seat)[2]
   self.assertLess(a[1],-2);self.assertLess(b[1],0);self.assertEqual(0,c[1]);self.assertLess(c[2],b[2])
   self.assertTrue(G['shell_visible'](phase,approach));self.assertTrue(G['shell_visible'](phase,contact));self.assertFalse(G['shell_visible'](phase,seat))
   # Entire cartridge has entered the canonical lower magazine / sleeve volume in Z.
   shell=read(A/f'models/{KEY}_shell.json')['elements']
   self.assertLess(max(e['to'][2]+c[2] for e in shell),3.38)
  self.assertTrue(all(not G['shell_visible']('return',i/20) for i in range(21)))
 def test_actual_twelve_full_frames_identity_hashes_and_observations(self):
  ref=read(ART/'motion-reference.json');self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
  self.assertEqual('https://www.youtube.com/watch?v=5IZfs2bjrYY',ref['url']);self.assertEqual('esbeekay',ref['creator'])
  self.assertIn('FIRST IN, LAST OUT',ref['identityVerification']['evidence']);self.assertEqual(46.,ref['identityVerification']['identityFrameSeconds'])
  self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
  for f in ref['frames']:
   self.assertEqual(f['sourceFrameIndex']/30,f['timestampSeconds']);self.assertEqual(ref['url'],f['sourceURL'])
   self.assertTrue(f['observation']);self.assertEqual(f['sha256'],hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest())
   with Image.open(ROOT/f['path']) as im:self.assertEqual((1280,720),im.size)
  self.assertFalse(ref['authorship']['extractedBones']);self.assertFalse(ref['authorship']['handIK'])
 def test_manifest_exact_ownership_hashes_and_honest_scope(self):
  m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
  self.assertEqual({str(p) for p in G['expected_output_paths']()},paths);self.assertEqual(258,len(paths));self.assertEqual(255,sum(p.startswith(str(A)) for p in paths))
  scope=Path('/private/tmp/w178-manifest.json')
  if scope.exists():
   owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w178-first-in-last-out-insert'))
   self.assertEqual(274,len(owned));self.assertTrue(paths<=owned)
  for mapping in (m['sha256'],m['canonicalSha256'],m['sourceSha256']):
   for path,digest in mapping.items():self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
  self.assertEqual(109,m['maxAssembledElements']);self.assertEqual(6,m['returnTicks']);self.assertFalse(m['returnBlocksGameplay'])
  for key in ('nativeGameplayVerified','handIK','extractedBones','thirdPersonReloadClaim','mechanicsOrAudioChanged'):self.assertFalse(m[key])
  self.assertFalse(m['integration']['workerRuntimeEdited'])
 def test_invalid_phase_progress_and_offline_evidence(self):
  for phase,p in [('bad',0),('initial',-.1),('loop',float('nan')),('return',float('inf')),('loop',1.1)]:
   with self.assertRaises(ValueError):G['sample'](phase,p)
  for name,size in [('comparison.png',(1600,1610)),('storyboard.png',(1600,1630))]:
   with Image.open(ROOT/ART/name) as im:self.assertEqual(size,im.size)
if __name__=='__main__':unittest.main(verbosity=2)
