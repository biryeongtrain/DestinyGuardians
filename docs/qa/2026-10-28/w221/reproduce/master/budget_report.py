from pathlib import Path
import json
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');q=r/'docs/qa/2026-10-28/w221';m=json.loads((r/'art/weapons/w201/manifest.json').read_text());ids=['ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth', 'pyroclastic_flow', 'seventh_seraph_officer_revolver']
rows=[]
for id in ids:
 n=m['maxAssembledElements'][id];assert n<=1000 and id in m['upperArmWeapons'];rows.append({'weapon':id,'allRoutesMaximumIncludingArms':n,'limit':1000,'fullChain':True})
(q/'assembled-budgets.json').write_text(json.dumps({'rows':rows,'basis':'actual assembled alternative routes; max rather than sum across alternatives; arms included'},indent=2)+'\n');print(rows)
