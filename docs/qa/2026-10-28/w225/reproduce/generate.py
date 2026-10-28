from pathlib import Path
import subprocess,time,json
repo=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=repo/'docs/qa/2026-10-28/w225'
start=time.time()
with (q/'hands-generation.log').open('x') as log:
 p=subprocess.run(['rtk','proxy','/Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3','-B','scripts/build_first_person_hands_w201.py'],cwd=repo,stdout=log,stderr=subprocess.STDOUT)
(q/'hands-generation.json').write_text(json.dumps({'returncode':p.returncode,'elapsedSeconds':time.time()-start},indent=2)+'\n')
raise SystemExit(p.returncode)
