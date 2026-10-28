from pathlib import Path
import json,subprocess,hashlib,sys
r=Path("/Users/qf/IdeaProjects/DestinyGuardians");q=r/"docs/qa/2026-10-28/w223";s=Path(__file__).parent
assert json.loads((q/"review-second.json").read_text())["accepted"]
owned=json.loads((s/"hands-owned-delta.json").read_text()); removals=set(owned["trackedRemovals"])
paths=set(owned["newOrChanged"])|removals
for f in json.loads((q/"worktrees.json").read_text())["features"]:paths.update(f["owned_paths"])
for row in json.loads((q/"master-integration.json").read_text()):paths.add(row["path"])
paths.update(["art/weapons/w201/manifest.json","art/weapons/w222/nezarec_s_whisper/manifest.json","docs/design/194_W223_월도_팔과_적중_HUD.md","docs/qa/worktree-pool.json"])
paths.update(str(p.relative_to(r)) for p in q.rglob("*") if p.is_file() and p.suffix in (".json",".md",".py",".mjs",".gradle",".png",".patch",".xml") and p.name!="commit-plan.json")
head={}
for e in subprocess.check_output(["rtk","proxy","git","ls-tree","-r","-z","HEAD"],cwd=r).split(b"\0"):
 if e:meta,name=e.split(b"\t",1);head[name.decode()]=meta.split()[2].decode()
rows=[]
for rel in sorted(paths):
 p=r/rel
 if not p.exists():
  assert rel in removals and rel in head,rel
  rows.append({"path":rel,"sha256":None,"bytes":0,"deleted":True});continue
 assert p.is_file() and not p.is_symlink(),rel
 raw=p.read_bytes();oid=hashlib.sha1(b"blob "+str(len(raw)).encode()+b"\0"+raw).hexdigest()
 if head.get(rel)==oid:continue
 rows.append({"path":rel,"sha256":hashlib.sha256(raw).hexdigest(),"bytes":len(raw)})
plan={"scope":"Accepted W223 file snapshots only; per-file exact new integration in master-integration.patch. Relevant shared Java files include pre-existing implementation bytes; not a clean-checkout completeness certification.","files":rows,"count":len(rows),"bytes":sum(x["bytes"] for x in rows)}
(q/"commit-plan.json").write_text(json.dumps(plan,indent=2)+"\n")
if "--stage" in sys.argv:
 assert not subprocess.check_output(["rtk","proxy","git","diff","--cached","--name-only"],cwd=r).strip()
 spec=s/"commit-paths.nul";spec.write_bytes(b"".join(x["path"].encode()+b"\0" for x in rows))
 subprocess.run(["rtk","proxy","git","add","--pathspec-from-file="+str(spec),"--pathspec-file-nul"],cwd=r,check=True)
 subprocess.run(["rtk","proxy","git","diff","--cached","--check"],cwd=r,check=True)
print({"files":len(rows),"bytes":plan["bytes"],"staged":"--stage" in sys.argv})
