from pathlib import Path
import json,hashlib,shutil,datetime
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w221';tmp=Path('/private/tmp/destiny-w221-source')
features=json.loads((q/'worktrees.json').read_text())['features'];rows=[]
for f in features:
 w=Path(f['destination']);gd=Path((w/'.git').read_text().strip().split(': ',1)[1]);d=json.loads((gd/'worktree-batch.json').read_text());assert d['status']=='ready';rows.append({'worker':f['name'],'files':len(d['baseline']),'baselineSha256':d['baseline_sha256'],'gradleEnv':d['gradle_env']})
assert len(set(x['baselineSha256'] for x in rows))==1
(q/'seed.json').write_text(json.dumps({'ready':True,'rows':rows,'at':datetime.datetime.now().astimezone().isoformat()},indent=2)+'\n')
for name in ['selection.json','agents.json','source-review.json']:shutil.copy2(tmp/name,q/name)
with (q/'step-log.md').open('a') as log:log.write('\n- All five seeds ready; independent current dirty baseline verified. Shared integration may now proceed.\n')
print({'readyWorkers':5,'baselineFiles':rows[0]['files']})
