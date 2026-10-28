from pathlib import Path
import sys,json,hashlib
sys.dont_write_bytecode=True
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');s=Path(__file__).parent
sys.path.insert(0,str(r/'scripts/qa'));import worktree_batch as b
m=json.loads((s/'worktrees.json').read_text());phase=sys.argv[1];which=sys.argv[2:];records=[]
q=r/'docs/qa/2026-10-28/w223';accepted={}
# Explicit integration history, not lexicographic filename order.
for previous in [q/('integration-'+name+'.json') for name in ['first-glaive','first-hud','feedback','second-docs'] if (q/('integration-'+name+'.json')).exists()]:
 for task in json.loads(previous.read_text()):
  for change in task['changes']:accepted[change['path']]=change['after']
for f in m['features']:
 if which and f['name'] not in which:continue
 w,state=b.load(f['destination']);rows=[]
 for rel in state['owned_paths']:
  p=w/rel;dest=r/rel;before=state['baseline'].get(rel);after=b.read_file(p)[0] if p.exists() else None
  if before==after:continue
  actual=b.read_file(dest)[0] if dest.exists() else None
  if actual==after:continue
  assert actual==accepted.get(rel,before),(rel,'main drift')
  assert p.exists(),(rel,'deletion not expected')
  dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(p.read_bytes())
  rows.append({'path':rel,'baseline':before,'after':after})
 records.append({'task':f['name'],'slot':str(w),'changes':rows})
q=r/'docs/qa/2026-10-28/w223';(q/('integration-'+phase+'.json')).write_text(json.dumps(records,indent=2)+'\n');print(json.dumps(records,indent=2))
