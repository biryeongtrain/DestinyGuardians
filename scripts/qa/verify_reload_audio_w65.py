#!/usr/bin/env python3
"""Read-only W65 compatibility audit of preserved W63 full-duration audio.

W63 phase-method provenance is historical after the new overload. Do not rewrite
that manifest or silently accept current source drift. Pin the reviewed W65
cycle/runtime/profile, compare every other original consumed input, then rebuild
historical metadata in memory only to verify every unchanged PCM/Ogg asset.
This is not native playback evidence.
"""
import argparse
import copy
import hashlib
import json
import runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
CURRENT_FILES={'src/main/java/kim/biryeong/destiny/weapon/WeaponCycle.java': 'ab2f47e9a5ecea3d4565bb48ac0a3ced61ed3d93004936c6f737ce3f2e61b233', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': '75d94579a4c784b90ce1390b87b01523aabebfd1f9f40880e047a3ef2b367bb5', 'src/main/java/kim/biryeong/destiny/weapon/ReloadCreditProfile.java': '19cfffb608cb6895bed1994997514a42e0ff1de8b84153b769c91eddc4a2c7ef', 'src/main/resources/destiny/weapons/w65-reload-credit.json': '6ad811c0d0dd9600c8cb4d6a2defa9449425847c8742f5dd50d518e43246bea4'}
HISTORICAL_PHASE={'path': 'src/main/java/kim/biryeong/destiny/weapon/WeaponCycle.java', 'selector': 'public boolean startReload(long tick, WeaponProfile p, WeaponMagazine magazine, WeaponReloadPolicy.Plan plan)', 'sha256': 'ff513b02da8081b2178e641f0d523fd50208145a252f34fb73a5d37bd669f576'}


def audit():
    for path,expected in CURRENT_FILES.items():
        assert hashlib.sha256((ROOT/path).read_bytes()).hexdigest()==expected, "W65 reviewed source drift: "+path
    legacy=runpy.run_path(str(ROOT/'scripts/audio/build_reload_sounds_w63.py'))
    saved=json.loads((ROOT/'art/weapons/w63/audio-manifest.json').read_text())
    data=legacy['inputs']()
    before=copy.deepcopy(data['consumed'])
    assert saved['consumedSources']['javaMethods'][1]==HISTORICAL_PHASE
    expected=copy.deepcopy(saved['consumedSources'])
    # Only the legacy overload's source digest differs. Full ticks/event/source
    # selection are still independently reconstructed by the original generator.
    expected['javaMethods'][1]=before['javaMethods'][1]
    assert before==expected, "Other W63 input or full-phase selection changed"
    assert before['javaMethods'][1]['path']==HISTORICAL_PHASE['path']
    assert before['javaMethods'][1]['selector']==HISTORICAL_PHASE['selector']
    data['consumed']=copy.deepcopy(saved['consumedSources'])
    ffmpeg=legacy['tool'](None)
    counts=legacy['verify'](data,ffmpeg)
    return {'stage':'W65','status':'PASS','currentReviewedFilePins':CURRENT_FILES,
            'historicalPhaseMethod':HISTORICAL_PHASE,'currentLegacyOverload':before['javaMethods'][1],
            'allOtherConsumedPinsExact':True,'historicalManifestRewritten':False,
            'counts':counts,'verification':'Unchanged full-phase Ogg/PCM/source mapping; separate current source review pins, not native playback'}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--out',type=Path);a=p.parse_args()
    result=audit()
    if a.out:a.out.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,sort_keys=True))
