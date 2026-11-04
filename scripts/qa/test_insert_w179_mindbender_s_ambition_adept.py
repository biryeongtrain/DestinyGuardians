#!/usr/bin/env python3
"""Focused W179 phased shotgun asset verification; no server/native execution."""
import hashlib
import json
import math
from pathlib import Path
import runpy
import unittest
from PIL import Image
ROOT=Path(__file__).resolve().parents[2]
G=runpy.run_path(str(ROOT/'scripts/generate_insert_w179_mindbender_s_ambition_adept.py'))
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
class InsertW179MindbenderTest(unittest.TestCase):
 def test_exact_canonical_geometry_uv_atlas_and_116_element_budget(self):
  source=read(G['SOURCE']);body=read(A/f'models/{KEY}_body.json');shell=read(A/f'models/{KEY}_shell.json')
  self.assertEqual(source,body);self.assertEqual((104,12),(len(body['elements']),len(shell['elements'])))
  self.assertEqual(source['textures'],shell['textures'])
  for e in shell['elements']:
   self.assertTrue(all(b-a>0 for a,b in zip(e['from'],e['to'])))
   self.assertGreater(min(e['to'][k]-e['from'][k] for k in range(2)),.2)
   donor='loading_tray' if 'case' in e['name'] else 'barrel_silver_collar_0'
   uv=next(x for x in source['elements'] if x['name']==donor)['faces']['east']['uv'];u=(uv[0]+uv[2])/2;v=(uv[1]+uv[3])/2
   for face in e['faces'].values():self.assertEqual([u,v,u,v],face['uv'])
  for a,b in zip(shell['elements'][::4],shell['elements'][4::4]):
   self.assertTrue(all(min(a['to'][k],b['to'][k])>max(a['from'][k],b['from'][k]) for k in range(3)))
  rules=read(Path('src/main/resources/weapon_surface_w123/manifest.json'))['targets']
  rule=next(r for r in rules if r['path'].endswith('weapon/shotgun/mindbender_s_ambition_adept.json'))
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
 def test_longitudinal_cartridge_contact_and_occluded_seat(self):
  source=read(G['SOURCE']);shell=read(A/f'models/{KEY}_shell.json')['elements']
  case,head,rim=shell[0],shell[4],shell[8]
  self.assertGreater(case['to'][2]-case['from'][2],3*(case['to'][0]-case['from'][0]))
  self.assertLess(case['from'][2],head['from'][2]);self.assertLess(head['from'][2],rim['from'][2])
  self.assertTrue(all(e.get('rotation',{}).get('axis','z')=='z' for e in shell))
  self.assertEqual((0.,.96,-1.90),G['SEATED'])
  tray=next(e for e in source['elements'] if e['name']=='loading_tray')
  receiver=next(e for e in source['elements'] if e['name']=='action_solid')
  for phase,approach,contact,seat in [('initial',.38,.72,.90),('loop',.10,.57,.84)]:
   a=G['sample'](phase,approach)[2];b=G['sample'](phase,contact)[2];c=G['sample'](phase,seat)[2]
   self.assertLess(a[1],-1.6)
   for expected,actual in zip(G['CONTACT'],b):self.assertAlmostEqual(expected,actual)
   for expected,actual in zip(G['SEATED'],c):self.assertAlmostEqual(expected,actual)
   self.assertTrue(G['shell_visible'](phase,approach));self.assertTrue(G['shell_visible'](phase,contact));self.assertFalse(G['shell_visible'](phase,seat))
   # At contact the full shell is below the existing loading tray, parallel -Z.
   self.assertLess(G['SHELL_ANCHOR'][1]+b[1]+.29,tray['from'][1])
   self.assertLess(G['SHELL_ANCHOR'][2]+b[2]+.77,5.6)
   # Conservative rotated-section radius encloses all 12 bars; the whole seated
   # cartridge lies inside canonical solid action, forward of tray and guard.
   center=[G['SHELL_ANCHOR'][k]+c[k] for k in range(3)]
   for k,radius in enumerate((.29,.29,.77)):
    self.assertGreater(center[k]-radius,receiver['from'][k]);self.assertLess(center[k]+radius,receiver['to'][k])
   self.assertLess(center[2]+.77,tray['from'][2])
  held=G['HOLD'][0]
  for i in range(21):
   self.assertLess(max(abs(a-b) for a,b in zip(G['sample']('loop',i/20)[0],held)),.71)
   self.assertFalse(G['shell_visible']('return',i/20))

 def test_same_weapon_source_frames_observations_and_authorship(self):
  ref=read(ART/'manifest.json')['reference']
  self.assertTrue(ref['inspectedActualFrames']);self.assertEqual(12,len(ref['frames']))
  self.assertEqual('https://www.youtube.com/watch?v=w6nyc_h7h2A',ref['url'])
  self.assertEqual('PureChiLL',ref['creator']);self.assertIn('Mindbenders',ref['title'])
  self.assertFalse(ref['adeptVariantVerified']);self.assertFalse(ref['extractedBones']);self.assertFalse(ref['handIK'])
  self.assertEqual(12,len({f['sha256'] for f in ref['frames']}))
  for f in ref['frames']:
   self.assertAlmostEqual(f['sourceFrameIndex']/30,f['timestampSeconds'])
   self.assertTrue(f['observation']);self.assertEqual(64,len(f['sha256']))
   self.assertIn(f['authoredPhase'],G['PHASES'])
  source=(ROOT/ART/'SOURCE.md').read_text()
  for text in ('Observed','Authored','w6nyc_h7h2A','native','Adept'):self.assertIn(text,source)
 def test_manifest_exact_ownership_hashes_and_honest_scope(self):
  m=read(ART/'manifest.json');paths=set(m['sha256'])|{str(ART/'manifest.json')}
  self.assertEqual({str(p) for p in G['expected_output_paths']()},paths);self.assertEqual(258,len(paths));self.assertEqual(255,sum(p.startswith(str(A)) for p in paths))
  scope=Path('/private/tmp/w179-manifest.json')
  if scope.exists():
   owned=set(next(f['owned_paths'] for f in json.loads(scope.read_bytes())['features'] if f['name']=='w179-mindbender-s-ambition-adept'))
   self.assertEqual(262,len(owned));self.assertTrue(paths<=owned)
  for mapping in (m['sha256'],m['canonicalSha256'],m['sourceSha256']):
   for path,digest in mapping.items():self.assertEqual(digest,hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),path)
  self.assertEqual(116,m['maxAssembledElements']);self.assertEqual(6,m['returnTicks']);self.assertFalse(m['returnBlocksGameplay'])
  for key in ('nativeGameplayVerified','handIK','extractedBones','thirdPersonReloadClaim','mechanicsOrAudioChanged'):self.assertFalse(m[key])
  self.assertFalse(m['integration']['workerRuntimeEdited']);self.assertEqual(0,m['triangleAdapterElements'])
 def test_invalid_phase_progress_and_offline_evidence(self):
  for phase,p in [('bad',0),('initial',-.1),('loop',float('nan')),('return',float('inf')),('loop',1.1)]:
   with self.assertRaises(ValueError):G['sample'](phase,p)
  for name,size in [('comparison.png',(1600,1610)),('storyboard.png',(1600,1630))]:
   with Image.open(ROOT/ART/name) as im:self.assertEqual(size,im.size)
if __name__=='__main__':unittest.main(verbosity=2)
