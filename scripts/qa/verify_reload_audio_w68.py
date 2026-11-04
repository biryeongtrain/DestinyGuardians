#!/usr/bin/env python3
"""W68 read-only full-phase audio compatibility, not playback evidence."""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w67.py': '3653d2ae2e3f3b2bea23a1e2473223b5c30f662e3c88cc24dce2b601f8791320', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java': '8bc4c8bc7bab67cadce98a2c1ad45f398044c23431d7a9b98cec7350cf187507', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java': 'f3ca0c2998b0057ad883d3ac48fccc83b431ed772e3d51a3dd8eadf2e36abb8c', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimState.java': 'df74191b25e9c387c06708b1f8d81d64c94d0f047cf3f448bd9ae24c77247290', 'src/main/java/kim/biryeong/destiny/weapon/SnapshotAimProfile.java': '1c264599c7bc273219bbe9727238d891bb65dc223cc27277b381c6846bd66095', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerkCommands.java': '606e8cd15a37023ace55590c65c95ef6a94c21e0d33a6f8374b0e81eedb4f631'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W68 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w67.py'))
    combined={**prior['REVIEWED'],**REVIEWED}
    prior['audit'].__globals__['REVIEWED']=combined
    report=prior['audit']()
    report.update(stage='W68',baseAuditStage='W67',priorAuditModifiedOnDisk=False,
                  w68ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
