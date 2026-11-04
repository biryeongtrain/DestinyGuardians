#!/usr/bin/env python3
"""W71 read-only full-phase audio compatibility, not playback evidence."""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w70.py': '0b48ee032dc0d1a3facca705b40060b6d6b23c0f723a7878948e0928be8c7753', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '60bd75d8a3d866a505d3dd03392ed9d525e9b70194ffd5e445f4a55266107052', 'src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java': '1b05ba5b03b257a4b7c907ac133b2d1ceafe860f31b2152850d81657cd259dc6', 'src/main/java/kim/biryeong/destiny/weapon/WeaponInsertPresentation.java': '7d0165f7f926aac60a894850e926d5246d40f3f91c7994aeda37b5cb7c78f6f8', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimPresentation.java': '40aff10c8dfdc8bcde0bc7d2380318339d3ce47085e7f84b15bc05158e66c2cf'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W71 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w70.py'))
    combined={**prior['REVIEWED'],**REVIEWED}
    prior['audit'].__globals__['REVIEWED']=combined
    report=prior['audit']()
    report.update(stage='W71',baseAuditStage='W70',priorAuditModifiedOnDisk=False,
                  w71ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
