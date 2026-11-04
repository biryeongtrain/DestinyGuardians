#!/usr/bin/env python3
"""W67 read-only preserved full-phase audio; explicit current precision-return source review.
Past W66/W65/W63 checkers and manifests stay untouched. This is not native playback.
"""
import argparse, hashlib, json, runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w66.py': '77fa54304ad1b219a44b9db24381671617052dce35b9b567b046cc9f771333bf', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '25d7b54eeaab0eef7a3d3f48e2e872120808e5f37a800e67ed73e0a369e8f1e9', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java': '107095aad79dbbe36a37c0347b37810f23fea26540d09af7d6cb4aea50c95385', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerkCommands.java': 'cbe449449e86921738acbaaa403b3d527f4e00374606e0525781a766379450dd', 'src/main/java/kim/biryeong/destiny/weapon/WeaponMagazine.java': '050ec3b45e367febad7c9c8b1a4fd283167270e6469b895e7465ebf702822b27', 'src/main/java/kim/biryeong/destiny/weapon/PrecisionReturnCycle.java': 'dcfdf80b7f9123f1334e4037a6f53ab545d78319df425a702c6ba6d8f29fb532', 'src/main/java/kim/biryeong/destiny/weapon/PrecisionReturnProfile.java': 'd1a62793f66928f5fce2fd566c6e1a0541f0bc937f19c404b7cfda35d4e4ce5e', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPrecisionReturn.java': '0f5249bfb9aa74797570a8e0e45de1d588beb05609193587ac1029f2d0d45047'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W67 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w66.py'))
    # Only this private invocation changes review guards; never rewrite historical files.
    combined={**prior['REVIEWED'],**REVIEWED}
    prior['audit'].__globals__['REVIEWED']=combined
    report=prior['audit']()
    report.update(stage='W67',baseAuditStage='W66',priorAuditModifiedOnDisk=False,
                  w67ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
