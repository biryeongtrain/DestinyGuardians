#!/usr/bin/env python3
"""Read-only W75 ADS movement and cleanup compatibility; no sound dispatcher changes.
The only Runtime delta adds cleanup of ADS-only sessions. Not acoustic evidence.
Previous audit files/pins remain historical and are not edited.
"""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PARENT='scripts/qa/verify_bow_window_audio_w74.py'
PARENT_SHA='685a2590810779359e9ace9ca2687931b33a1c6d86141761bd05cb039dfbf113'
REVIEWED={'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java': '1bd8902c9964e79cbad9af2df396894eb8df85506faba361aa3908a39aa194be', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '1fd3912a41b7889dfb5b8afb93b61acc3e1cf0d019743dd55dab0dd308cf6714', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimMovement.java': '9fc5b0b0fc07a49399885da5dd45d8d319ce28cbaa7315ed702c7ee1a8330c8c', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimMovementProfile.java': '39c9763e7c0241dd2545dbca223cee95117f8ca146df3b1ea023f08c5285d9a0'}

def audit():
    sha=lambda p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest()
    assert sha(PARENT)==PARENT_SHA
    for p,h in REVIEWED.items(): assert sha(p)==h, "W75 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/PARENT))
    prior["audit"].__globals__["REVIEWED"]={**prior["REVIEWED"],**REVIEWED}
    report=prior["audit"]()
    report.update(stage="W75",baseAuditStage="W74/W73/W71",priorAuditModifiedOnDisk=False,
                  w75ReviewedSourcePins=REVIEWED,pairedAimAttributesAndAdsOnlyCleanup=True,
                  newAudioEvents=0,chargeSoundDurationResampled=False,acousticListening=False)
    return report

if __name__=="__main__":
    p=argparse.ArgumentParser();p.add_argument("--out",type=Path);a=p.parse_args();report=audit()
    if a.out:a.out.write_text(json.dumps(report,indent=2)+"\n")
    print(json.dumps(dict(stage=report["stage"],status=report["status"],acousticListening=False)))
