from pathlib import Path
import json
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w222';m=json.loads((r/'art/weapons/w201/manifest.json').read_text());ids=['biting_winds', 'whispering_slab', 'long_arm', 'nezarec_s_whisper']
rows=[]
for id in ids:
 n=m['maxAssembledElements'][id];assert n<=1000 and id in m['upperArmWeapons'];rows.append({'weapon':id,'allRoutesMaximumIncludingArms':n,'limit':1000,'fullChain':True})
(q/'assembled-budgets.json').write_text(json.dumps({'rows':rows,'basis':'actual assembled alternative routes; max rather than sum across alternatives; arms included'},indent=2)+'\n');print(rows)
