"""Commit deliberate accepted W222 scope, preserving inherited dirty files."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w222'
assert json.loads((q/'visual-review.json').read_text())['accepted']
base=json.loads((r/'.git/worktrees/w221-ikelos_sg_v1_0_1/worktree-batch.json').read_text())['baseline']
paths=set()
for f in json.loads((q/'worktrees.json').read_text())['features']:paths.update(f['owned_paths'])
for row in json.loads((q/'integration-shared.json').read_text()):paths.add(row['path'])
paths.update(str(p.relative_to(r)) for p in (r/'art/weapons/w222').rglob('*') if p.is_file())
generated=q/('generated-pass2.json' if (q/'generated-pass2.json').exists() else 'generated-pass1.json')
for row in json.loads(generated.read_text()):paths.update(row['files'])
hands=json.loads((r/'art/weapons/w201/manifest.json').read_text())['sha256']
paths.update(p for p,s in hands.items() if base.get(p,{}).get('sha256')!=s)
paths.update(['art/weapons/w201/manifest.json','docs/qa/WORKTREE_POOL.md','docs/qa/worktree-pool.json','scripts/qa/test_bow_contacts_w222.py','scripts/qa/test_source_registration_w222.py'])
paths.update(str(p.relative_to(r)) for p in q.iterdir() if p.is_file() and p.suffix in ('.md','.json') and p.name!='commit-plan.json')
paths.update(str(p.relative_to(r)) for p in (q/'reproduce/master').glob('*.py'))
paths.update(str(p.relative_to(r)) for p in (q/'source-sheets').glob('*.png'))
for phase in ('vision1','vision2'):
 for name in ('native-validation.json','final-neutral-before-stop.json'):paths.add(str((q/phase/name).relative_to(r)))
paths.add(str((q/'second-post-reload-review.png').relative_to(r)))
rows=[]
head_blobs={}
for entry in subprocess.check_output(['rtk','proxy','git','ls-tree','-r','-z','HEAD'],cwd=r).split(b'\0'):
 if entry:
  meta,name=entry.split(b'\t',1);head_blobs[name.decode()]=meta.split()[2].decode()
for rel in sorted(paths):
 p=r/rel;assert p.is_file() and not p.is_symlink(),rel
 raw=p.read_bytes();sha=hashlib.sha256(raw).hexdigest()
 # W222 inputs predate slot refresh, so equality to that baseline is NOT
 # grounds to omit untracked W222 source caches or deliberate QA reports.
 blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
 if head_blobs.get(rel)==blob:continue
 rows.append({'path':rel,'sha256':sha,'bytes':len(raw)})
assert rows
plan={'scope':'Accepted W222 paths only; inherited dirty baseline remains uncommitted','files':rows,'count':len(rows),'bytes':sum(x['bytes'] for x in rows)}
(q/'commit-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
if '--stage' in sys.argv:
 assert not subprocess.check_output(['rtk','proxy','git','diff','--cached','--name-only'],cwd=r).strip(),'Existing staged changes'
 spec=Path('/private/tmp/destiny-w222-source/commit-paths.nul');spec.write_bytes(b''.join(x['path'].encode()+b'\0' for x in rows))
 subprocess.run(['rtk','proxy','git','add','--pathspec-from-file='+str(spec),'--pathspec-file-nul'],cwd=r,check=True)
 subprocess.run(['rtk','proxy','git','diff','--cached','--check'],cwd=r,check=True)
print({'files':len(rows),'bytes':plan['bytes'],'staged':'--stage' in sys.argv})
