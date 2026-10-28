from pathlib import Path
import subprocess,json,time,sys
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w223'
phase=sys.argv[1] if len(sys.argv)>1 else 'pass1'
assert phase in ('pass1','pass2')
cmd=['rtk','proxy','/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','-B','scripts/build_first_person_hands_w201.py']
start=time.time()
with (q/('hands-'+phase+'.log')).open('x') as log:result=subprocess.run(cmd,cwd=r,stdout=log,stderr=subprocess.STDOUT)
assert result.returncode==0,result.returncode
manifest=json.loads((r/'art/weapons/w201/manifest.json').read_text())
ids=['nezarec_s_whisper']
assert all(x in manifest['upperArmWeapons'] for x in ids)
report={'exit':0,'elapsedSeconds':time.time()-start,'command':cmd,'actualAssembledElementsIncludingArms':{x:manifest['maxAssembledElements'][x] for x in ids}}
(q/('hands-'+phase+'.json')).write_text(json.dumps(report,indent=2)+'\n');print(report)
