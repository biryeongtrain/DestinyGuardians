#!/usr/bin/env python3
"""W70 read-only full-phase audio compatibility, not playback evidence."""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w69.py': '18ee957c87f017c7e2093661a1a9bd3837eebe80167c597fdd9bf69fe0b2f2c5', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java': '6d6cb81e4c49a459616e1d69c4011f8231c943c4b487ffcb01635e6b46db7119', 'src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java': '5031ad3200513be83bc1d56638f413b4768cb51dc3e8b3802809751e54d46126', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimPresentation.java': '715dae598cda5d3f52d53e6641cccd9f89be49f7c06b4d4f438e0f3e98edcf2d'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W70 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w69.py'))
    combined={**prior['REVIEWED'],**REVIEWED}
    prior['audit'].__globals__['REVIEWED']=combined
    report=prior['audit']()
    report.update(stage='W70',baseAuditStage='W69',priorAuditModifiedOnDisk=False,
                  w70ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
