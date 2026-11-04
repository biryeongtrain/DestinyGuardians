#!/usr/bin/env python3
"""W69 read-only full-phase audio compatibility, not playback evidence."""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w68.py': 'e426a53b91eae2cf20651cc2ca877c056783835d05dad49b00cdd3f31adb4e03', 'src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java': '91c34cb12c51b8b4895c1f94fd6655a3665079ae6f3781782e6b28e39053149b'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W69 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w68.py'))
    combined={**prior['REVIEWED'],**REVIEWED}
    prior['audit'].__globals__['REVIEWED']=combined
    report=prior['audit']()
    report.update(stage='W69',baseAuditStage='W68',priorAuditModifiedOnDisk=False,
                  w69ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
