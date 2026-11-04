#!/usr/bin/env python3
"""W73 read-only audio path compatibility. Prior stage audits/pins remain historical on disk.

Reviewed delta: bow draw duration snapshot and positive-precision Tempo callback only.
Charge/playFire/impact/nock dispatch remains unchanged. Actual non-Guardian offhand stow
cancels the owned bow nock/audio session immediately. This is not listening evidence.
"""
import argparse,hashlib,json,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
REVIEWED = {'scripts/qa/verify_reload_audio_w70.py': '0b48ee032dc0d1a3facca705b40060b6d6b23c0f723a7878948e0928be8c7753', 'scripts/qa/verify_reload_audio_w71.py': 'd0661fda40947d040ad6fe70144bbe12df8797641bb89c7a47d58ebdcb2debda', 'src/main/java/kim/biryeong/destiny/input/InputRouter.java': '17f5cbb7829b932f4fda997372bfd0cc2c121c8cb810510f779611a2ca76dbf6', 'src/main/java/kim/biryeong/destiny/weapon/ArcherTempoProfile.java': '1b0220d3060432d8925b855469720d383e7882f7bf6a9e183661c4e171ad5cb3', 'src/main/java/kim/biryeong/destiny/weapon/PrecisionReturnCycle.java': 'dcfdf80b7f9123f1334e4037a6f53ab545d78319df425a702c6ba6d8f29fb532', 'src/main/java/kim/biryeong/destiny/weapon/PrecisionReturnProfile.java': 'd1a62793f66928f5fce2fd566c6e1a0541f0bc937f19c404b7cfda35d4e4ce5e', 'src/main/java/kim/biryeong/destiny/weapon/RampageCycle.java': 'b09bbbe8b00aff6e387cebc1925b08fd661b39dd2e7e9896cd23368fd2ca3272', 'src/main/java/kim/biryeong/destiny/weapon/RampageProfile.java': '596d5fd6f3bc1f7323ef17daa1747eb46de75660fb0d00e742dbd231b0946078', 'src/main/java/kim/biryeong/destiny/weapon/ReloadCreditProfile.java': '19cfffb608cb6895bed1994997514a42e0ff1de8b84153b769c91eddc4a2c7ef', 'src/main/java/kim/biryeong/destiny/weapon/SnapshotAimProfile.java': '1c264599c7bc273219bbe9727238d891bb65dc223cc27277b381c6846bd66095', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimPresentation.java': '40aff10c8dfdc8bcde0bc7d2380318339d3ce47085e7f84b15bc05158e66c2cf', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAimState.java': 'df74191b25e9c387c06708b1f8d81d64c94d0f047cf3f448bd9ae24c77247290', 'src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java': '6d6cb81e4c49a459616e1d69c4011f8231c943c4b487ffcb01635e6b46db7119', 'src/main/java/kim/biryeong/destiny/weapon/WeaponArcherTempo.java': '108695c0c6b0fc1daee5a0b606822ea4da624c2f7a0ace82be8ed39913bf747d', 'src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java': '1b05ba5b03b257a4b7c907ac133b2d1ceafe860f31b2152850d81657cd259dc6', 'src/main/java/kim/biryeong/destiny/weapon/WeaponCycle.java': 'ab2f47e9a5ecea3d4565bb48ac0a3ced61ed3d93004936c6f737ce3f2e61b233', 'src/main/java/kim/biryeong/destiny/weapon/WeaponInsertPresentation.java': '7d0165f7f926aac60a894850e926d5246d40f3f91c7994aeda37b5cb7c78f6f8', 'src/main/java/kim/biryeong/destiny/weapon/WeaponMagazine.java': '050ec3b45e367febad7c9c8b1a4fd283167270e6469b895e7465ebf702822b27', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerkCommands.java': 'f080e47d636a794e986ff95b336deb964bbc5bbad1342fdabe834d598ec3cfca', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java': '0c18ac0a867fe8b75793e2b47e612a0a20002ca6bb758d0daf5ef34d5c599881', 'src/main/java/kim/biryeong/destiny/weapon/WeaponPrecisionReturn.java': '0f5249bfb9aa74797570a8e0e45de1d588beb05609193587ac1029f2d0d45047', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRampage.java': 'ecd6ff3dbc597d3c9a7a6e210ed05b584cd9f187610cd90ab1749feda70945bb', 'src/main/java/kim/biryeong/destiny/weapon/WeaponReloadPresentation.java': '91c34cb12c51b8b4895c1f94fd6655a3665079ae6f3781782e6b28e39053149b', 'src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java': 'cdebba883163401115f05af814ab8fb708f2a79d89f7feae3602465f31655279', 'src/main/resources/destiny/weapons/w65-reload-credit.json': '6ad811c0d0dd9600c8cb4d6a2defa9449425847c8742f5dd50d518e43246bea4'}

def audit():
    for p,h in REVIEWED.items():
        assert hashlib.sha256((ROOT/p).read_bytes()).hexdigest()==h, "W73 reviewed source drift: "+p
    prior=runpy.run_path(str(ROOT/'scripts/qa/verify_reload_audio_w71.py'))
    prior['audit'].__globals__['REVIEWED']={**prior['REVIEWED'],**REVIEWED}
    report=prior['audit']()
    report.update(stage='W73',baseAuditStage='W71',priorAuditModifiedOnDisk=False,w73ReviewedSourcePins=REVIEWED,
                  chargeSoundDurationResampled=False,acousticListening=False)
    return report

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path);a=p.parse_args();report=audit()
    if a.out:a.out.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(dict(stage=report['stage'],status=report['status'],acousticListening=False)))
