from pathlib import Path
import hashlib,json
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w222';initial=json.loads((q/'integration-pass1.json').read_text());rows=[]
for worker in initial:
 work=Path(worker['worktree'])
 for item in worker['files']:
  rel=item['path'];target=r/rel;before=hashlib.sha256(target.read_bytes()).hexdigest();assert before==item['after']['sha256'],rel
  raw=(work/rel).read_bytes();after=hashlib.sha256(raw).hexdigest()
  if before!=after:target.write_bytes(raw)
  rows.append({'path':rel,'before':before,'after':after,'changed':before!=after})
(q/'integration-pass2.json').write_text(json.dumps(rows,indent=2)+'\n');print({'files':len(rows),'changes':[x['path'] for x in rows if x['changed']]})
