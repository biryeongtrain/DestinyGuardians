#!/usr/bin/env python3
"""W66 read-only full-phase audio regression with separately reviewed current runtime.
W65/W63 historical manifests/checkers remain unchanged. W66 changes only damage
traits, not reload admission/timing/event selection. No native playback proof.
"""
import argparse,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w65.py': '59c1cd4302b3d4160278f471508e3fd6c11b3a89ea11bda722e4cdf2f04a981a', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': 'd29ec610de67225c96486fe855b6b2280b189e8cae290a9efa2f6874ce43fb85', 'src/main/java/kim/biryeong/destiny/weapon/RampageCycle.java': 'b09bbbe8b00aff6e387cebc1925b08fd661b39dd2e7e9896cd23368fd2ca3272', 'src/main/java/kim/biryeong/destiny/weapon/RampageProfile.java': '596d5fd6f3bc1f7323ef17daa1747eb46de75660fb0d00e742dbd231b0946078', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRampage.java': 'ecd6ff3dbc597d3c9a7a6e210ed05b584cd9f187610cd90ab1749feda70945bb', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java': '5f8523be9a2f1ae3838d0a4d316fc2894b47d65a50300264a77021c18c91b232', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerkCommands.java': 'b81aaa05e0422561b6f7486910d25f115152d39dd2d11db8812e6e70b396c6ef'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h,"W66 reviewed source drift: "+p
    legacy=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w65.py'))
    old=legacy['CURRENT_FILES']
    current={**old,**{p:h for p,h in REVIEWED.items() if p.startswith('src/')}}
    # Change review pins in this private invocation only, never the original file.
    legacy['audit'].__globals__['CURRENT_FILES']=current
    report=legacy['audit']()
    report.update(stage='W66',baseAuditStage='W65',priorAuditModifiedOnDisk=False,
                  w66ReviewedSourcePins=REVIEWED)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
