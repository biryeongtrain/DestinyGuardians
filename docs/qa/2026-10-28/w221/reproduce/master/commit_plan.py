"""Stage only accepted W221 paths relative to its saved dirty baseline."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w221'
assert json.loads((q/'visual-review.json').read_text())['accepted']
base=json.loads((r/'.git/worktrees/w221-ikelos_sg_v1_0_1/worktree-batch.json').read_text())['baseline']
paths=set()
for f in json.loads((q/'worktrees.json').read_text())['features']:paths.update(f['owned_paths'])
for row in json.loads((q/'integration-shared.json').read_text()):paths.add(row['path'])
paths.update(str(p.relative_to(r)) for p in (r/'art/weapons/w221').rglob('*') if p.is_file())
for row in json.loads((q/'generated-pass1.json').read_text()):paths.update(row['files'])
hands=json.loads((r/'art/weapons/w201/manifest.json').read_text())['sha256']
paths.update(p for p,s in hands.items() if base.get(p,{}).get('sha256')!=s)
paths.add('art/weapons/w201/manifest.json')
paths.add('docs/qa/worktree-pool.json')
qa_names=['README.md','step-log.md','selection.json','source-review.json','source-handling-evidence.json','assembled-budgets.json','visual-review.json','postflight-final.json','retained-shotgun-audio.json','build-pass1.json','build-pass2.json','review-first.json','integration-pass1.json','integration-pass2.json','seed.json','worktrees.json']
paths.update(str((q/name).relative_to(r)) for name in qa_names if (q/name).is_file())
paths.update(str(p.relative_to(r)) for p in (q/'reproduce/master').glob('*.py'))
paths.update(str(p.relative_to(r)) for p in (q/'source-sheets').glob('*.png'))
for phase in ('vision1','vision2'):
 for name in ('native-validation.json','final-neutral-before-stop.json'):paths.add(str((q/phase/name).relative_to(r)))
paths.add(str((q/'second-post-reload-review.png').relative_to(r)))
rows=[]
for rel in sorted(paths):
 p=r/rel
 assert p.is_file() and not p.is_symlink(),rel
 raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 if base.get(rel,{}).get('sha256')==sha:continue
 rows.append({'path':rel,'sha256':sha,'bytes':len(raw)})
assert rows
plan={'scope':'W221 changed files only; inherited dirty baseline remains uncommitted','files':rows,'count':len(rows),'bytes':sum(x['bytes'] for x in rows)}
(q/'commit-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
if '--stage' in sys.argv:
 assert not subprocess.check_output(['rtk','proxy','git','diff','--cached','--name-only'],cwd=r).strip(),'Existing staged changes'
 spec=Path('/private/tmp/destiny-w221-source/commit-paths.nul');spec.write_bytes(b''.join(x['path'].encode()+b'\0' for x in rows))
 subprocess.run(['rtk','proxy','git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],cwd=r,check=True)
 subprocess.run(['rtk','proxy','git','diff','--cached','--check'],cwd=r,check=True)
print({'files':len(rows),'bytes':plan['bytes'],'staged':'--stage' in sys.argv,'priorDirtyBaselinePreserved':True})
