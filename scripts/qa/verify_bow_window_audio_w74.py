#!/usr/bin/env python3
"""Read-only W74 compatibility: runtime adds only a pure bow HUD query.
No new sound event, fire/reload dispatcher or charge resampling; not listening evidence.
Prior-stage reviewed pins remain historical on disk.
"""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PARENT="scripts/qa/verify_archers_tempo_audio_w73.py"
PARENT_SHA="25c716ce3ce80163bfd152f85ab0ebdab5f34134d7e36e9e22f08b32f78db48e"
REVIEWED={"src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java":"88d77ec281d6c969f5995c4eb07e4fe09cda0ffbdc5808a4683209ce99812ce9"}

def audit():
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    assert sha(PARENT)==PARENT_SHA
    for p,h in REVIEWED.items(): assert sha(p)==h, "W74 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/PARENT))
    prior["audit"].__globals__["REVIEWED"]={**prior["REVIEWED"],**REVIEWED}
    report=prior["audit"]()
    report.update(stage="W74",baseAuditStage="W73/W71",priorAuditModifiedOnDisk=False,
                  w74ReviewedSourcePins=REVIEWED,pureBowQueryOnly=True,
                  newAudioEvents=0,chargeSoundDurationResampled=False,acousticListening=False)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path);a=p.parse_args();report=audit()
    if a.out:a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(stage=report["stage"],status=report["status"],acousticListening=False)))
