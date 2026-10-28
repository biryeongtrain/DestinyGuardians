from pathlib import Path
import socket,json,subprocess,datetime
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w222';ports={}
for port in (8102,25611):
 with socket.socket() as s:ports[port]=s.connect_ex(('127.0.0.1',port))!=0
assert all(ports.values())
session=json.loads(Path('/Users/qf/.codex/tmp/destiny-awake-48h-20261028/session.json').read_text());p=subprocess.run(['rtk','proxy','ps','-p',str(session['pid']),'-o','command='],capture_output=True,text=True);cmd=p.stdout.strip();assert p.returncode==0 and 'caffeinate' in cmd and '-dimsu' in cmd and '172800' in cmd
w=subprocess.run(['rtk','proxy','git','-C',str(r),'worktree','list','--porcelain'],capture_output=True,text=True,check=True).stdout
retained=[f['path'] for f in json.loads((r/'docs/qa/worktree-pool.json').read_text())['slots']];assert len(retained)==5
assert all(Path(p).is_dir() and ('worktree '+p+'\n') in w for p in retained)
assert r.is_dir() and (r/'.git').is_dir() and ('worktree '+str(r)+'\n') in w
for phase in ('vision1','vision2'):
 d=json.loads((q/phase/'final-neutral-before-stop.json').read_text());assert not d['leaseActive'] and not d['heldKeys'] and not d['pendingSteps'] and not any(d['nativeInput'].values())
d={'at':datetime.datetime.now().astimezone().isoformat(),'mainPreserved':True,'awake48hRetained':True,'awakePid':session['pid'],'awakeExpires':session['expires'],'qaPortsFree':True,'ports':ports,'bothPassesNeutral':True,'retainedSlots':retained,'removedWorkers':0,'registeredWorktrees':w}
(q/'postflight-final.json').write_text(json.dumps(d,indent=2)+'\n');print(d)
