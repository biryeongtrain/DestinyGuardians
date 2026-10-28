from pathlib import Path
import hashlib,json,subprocess
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=repo/'docs/qa/2026-10-28/w225'
before=json.loads(subprocess.check_output(['git','show','fe4205c1:art/weapons/w201/manifest.json'],cwd=repo))['sha256'];m=json.loads((repo/'art/weapons/w201/manifest.json').read_text());after=m['sha256']
assert set(before)==set(after),'Unexpected geometry/file set change'
changed=[p for p in after if before[p]!=after[p]]
assert len(changed)==290,len(changed)
for rel in changed:
 assert rel.startswith('src/main/resources/assets/destiny/items/weapon_hands_w201/'),rel
 raw=(repo/rel).read_bytes();assert hashlib.sha256(raw).hexdigest()==after[rel]
 d=json.loads(raw);assert d['hand_animation_on_swap'] is False and d['swap_animation_scale']==0
 del d['swap_animation_scale']
 old=(json.dumps(d,ensure_ascii=False,separators=(',',':'),allow_nan=False)+'\n').encode()
 assert hashlib.sha256(old).hexdigest()==before[rel],'Change beyond one root scale: '+rel
routes=json.loads((repo/'src/main/resources/destiny/weapons/w201-first-person-hands.json').read_text())['models']
for target in routes.values():
 ns,key=target.split(':');d=json.loads((repo/'src/main/resources/assets'/ns/'items'/(key+'.json')).read_text())
 assert d['hand_animation_on_swap'] is False and d['swap_animation_scale']==0
report={'changedRoots':len(changed),'mappedRoots':len(routes),'allMappedRootsFalseAndZero':True,'changedBeyondRootMetadata':False,'geometryAndPoseHashesUnchanged':True,'unchangedGeneratedFiles':len(before)-len(changed),'addedFiles':0,'removedFiles':0,'changed':changed}
(q/'generated-delta.json').write_text(json.dumps(report,indent=2)+'\n');print({k:v for k,v in report.items() if k!='changed'})
