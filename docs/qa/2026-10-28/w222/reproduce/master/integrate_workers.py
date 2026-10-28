from pathlib import Path
import concurrent.futures,hashlib,json,subprocess,shutil
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=repo/'docs/qa/2026-10-28/w222';features=json.loads((q/'worktrees.json').read_text())['features']
def inspect(f):
 work=f['destination'];bundle=Path('/private/tmp/destiny-w222-export-'+f['name']);manifest=bundle/'manifest.json'
 if manifest.exists():
  assert not (bundle/'INCOMPLETE').exists();d=json.loads(manifest.read_text());assert d['worktree']==work and d['status']=='exported'
 else:
  result=subprocess.run(['rtk','proxy','python3','scripts/qa/worktree_batch.py','export','--worktree',work,'--output',str(bundle)],cwd=repo,capture_output=True,text=True);assert result.returncode==0,(work,result.stderr);d=json.loads(result.stdout)
 assert not d['out_of_scope'] and len(d['files'])==3
 for item in d['files']:
  assert hashlib.sha256((Path(work)/item['path']).read_bytes()).hexdigest()==item['after']['sha256']
 return d
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:reports=list(pool.map(inspect,features))
for d in reports:
 work=Path(d['worktree'])
 for item in d['files']:
  rel=item['path'];target=repo/rel;assert item['operation']=='add' and item['before'] is None and not target.exists(),rel
  raw=(work/rel).read_bytes();assert hashlib.sha256(raw).hexdigest()==item['after']['sha256'];target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(raw)
(q/'integration-pass1.json').write_text(json.dumps(reports,indent=2)+'\n');print({'workers':len(reports),'files':sum(len(d['files']) for d in reports),'outOfScope':0})
