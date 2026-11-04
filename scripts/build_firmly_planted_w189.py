#!/usr/bin/env python3
"""W189 base Firmly Planted. Offline, pinned, deterministic; --verify writes nothing.
Only four owned JSON outputs. Raw downloads/reports stay outside the source tree.
"""
import argparse, copy, hashlib, html, json, math, re, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
ART = "art/weapons/w189/firmly_planted/"
TARGET = "src/main/resources/destiny/weapons/w189-firmly_planted.json"
SCRIPT = "scripts/build_firmly_planted_w189.py"
BASE, ENHANCED, TRAIT = 280464955, 3920370755, 4241085061
VERSION = "245114.26.10.13.2000-1-bnet.66137"
KEYS = ("id", "hash", "socket", "perkHash", "plugSetHash")
PROFILES = {'demolitionist': 'w103-demolitionist.json', 'tracking_module': 'w104-tracking.json', 'feeding_frenzy': 'w108-feeding-frenzy.json', 'one_for_all': 'w109-one-for-all.json', 'surrounded': 'w109-surrounded.json', 'grave_robber': 'w110-grave-robber.json', 'swashbuckler': 'w110-swashbuckler.json', 'multikill_clip': 'w165-multikill-clip.json', 'subsistence': 'w167-subsistence.json', 'rapid_hit': 'w169-rapid-hit.json', 'perpetual_motion': 'w170-perpetual-motion.json', 'tap_the_trigger': 'w171-tap-the-trigger.json', 'frenzy': 'w172-frenzy.json', 'adrenaline_junkie': 'w173-adrenaline-junkie.json', 'focused_fury': 'w174-focused-fury.json', 'stats_for_all': 'w176-stats-for-all.json', 'heating_up': 'w177-heating-up.json', 'threat_detector': 'w178-threat-detector.json', 'vorpal_weapon': 'w181-vorpal.json', 'high_impact_reserves': 'w182-high_impact_reserves.json', 'surplus': 'w183-surplus.json', 'elemental_capacitor': 'w184-elemental_capacitor.json', 'quickdraw': 'w185-quickdraw.json', 'lead_from_gold': 'w187-lead_from_gold.json', 'zen_moment': 'w188-zen_moment.json', 'auto_loading_holster': 'w60-holster.json', 'kill_clip': 'w61-kill-clip.json', 'outlaw': 'w62-outlaw.json', 'rampage': 'w66-rampage.json', 'triple_tap': 'w67-precision-return.json', 'fourth_times_the_charm': 'w67-precision-return.json', 'archers_tempo': 'w73-archers-tempo.json', 'dragonfly': 'w77-dragonfly.json', 'explosive_payload': 'w80-payload.json', 'snapshot_sights': 'w68-snapshot.json'}
PINS = {'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w58-handling.json': '4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1', 'src/main/resources/destiny/weapons/w44-aim.json': '0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e', 'src/main/resources/destiny/weapons/w103-demolitionist.json': 'b7aa18096002f5a9a66892027c6fb57295e3a09864ff52a1f889d6f732c10905', 'src/main/resources/destiny/weapons/w104-tracking.json': 'c4ecf3805a1cc7c6529565f899cc45efbb811bf07c743558a40c76aadd3e789e', 'src/main/resources/destiny/weapons/w108-feeding-frenzy.json': '1ffbff575f0a29adc5a749d581f31c2f6dd67dfea20cf4a3484b6d2c1c522ce8', 'src/main/resources/destiny/weapons/w109-one-for-all.json': '65c25d83386071571beb012122f7d4834194812713152863575300537a881613', 'src/main/resources/destiny/weapons/w109-surrounded.json': '799f763f0f0882eec7b3a172592fdeb3f95e8fca1a95149274f3db82fac6f777', 'src/main/resources/destiny/weapons/w110-grave-robber.json': 'd8746295ed704fa6d5db254247baf000228655924629a3fd4cc4b067cd9a759b', 'src/main/resources/destiny/weapons/w110-swashbuckler.json': '0315293d63b74a8fd224772832dea879851151a6ec34998d47d268d170eec7b6', 'src/main/resources/destiny/weapons/w165-multikill-clip.json': 'f878e4d5c699bdc8d77fc8b86ee653caf8cb4dc4532c641b27d5f3c3be94f593', 'src/main/resources/destiny/weapons/w167-subsistence.json': 'abe5e37fb0632fb9da5a65f803b33349337d686523d4eef054bcb10742dc0835', 'src/main/resources/destiny/weapons/w169-rapid-hit.json': '3406dea192367d0f64406d473ab6996b5b6085dfaeb279c571209a84ec6dd8cd', 'src/main/resources/destiny/weapons/w170-perpetual-motion.json': 'e4155158bf1692797a3f1c1b0e49d80360c5494173b384a738c3a337fe47275f', 'src/main/resources/destiny/weapons/w171-tap-the-trigger.json': '94d8fb588f44eff1dd41c056fadd555d37c7266116e0c10311df906fd0bbd7e9', 'src/main/resources/destiny/weapons/w172-frenzy.json': '28a3722a9ea57dc7400a68ddcee80f6c661bf23a1abd0f4dc92dec9065120862', 'src/main/resources/destiny/weapons/w173-adrenaline-junkie.json': 'b2c0d5865d9d72f9ee4d1bd3439d940d52574d7d7539604a9b4fe1e82c3fbf65', 'src/main/resources/destiny/weapons/w174-focused-fury.json': 'bf8604f8758cf698b3d4307d682db54a98ba8afd0631855b8d253d53ca02d60c', 'src/main/resources/destiny/weapons/w176-stats-for-all.json': 'fbe3b8d75f696681e11e878c5a334567616351f07855fe9a07d3b211c47d3e9c', 'src/main/resources/destiny/weapons/w177-heating-up.json': '2a6995836e7aaecd7a7e2ce1af519e0fa34597998e59ad5ccf6483b5ebc44098', 'src/main/resources/destiny/weapons/w178-threat-detector.json': '8e593a1698dff17bb8260e40b9b1e3befe3efaca9fd54d990e89fdddf62cb4e4', 'src/main/resources/destiny/weapons/w181-vorpal.json': '221b1ba84382272dbc679684a9885e9cee8399ef98714a76f113bdbdd930d76e', 'src/main/resources/destiny/weapons/w182-high_impact_reserves.json': '0f428969fd69b7cc874171f875a963af9eac27a30974d111189ad7754626d5e1', 'src/main/resources/destiny/weapons/w183-surplus.json': '3a54d901e618b2472c8a2beff905ecb21d9aa0316628a0416adaf91242fccef6', 'src/main/resources/destiny/weapons/w184-elemental_capacitor.json': '254c688e41275e59e153238523a36e22a6b107945c0c8a48ed0ef0966fa5ff1c', 'src/main/resources/destiny/weapons/w185-quickdraw.json': 'c172eaef26e83b16f81586f4dd1e57cd5048600d019d08364e45e59103da94da', 'src/main/resources/destiny/weapons/w187-lead_from_gold.json': 'a643fb9241fe75dbed6dc8b786409f14ac9749bbe08b940343397b20970b9442', 'src/main/resources/destiny/weapons/w188-zen_moment.json': 'df64fed09aecc6dbdb0e4644a3a7f62e7ccc440aa26415a6065cc4c75d1c8532', 'src/main/resources/destiny/weapons/w60-holster.json': '78411445e481200481389df552b293be36a03643d753be9372ebb974cec953b6', 'src/main/resources/destiny/weapons/w61-kill-clip.json': 'fb3374e775b9313619f34c1dda5681d391577c15279aa140f9fdc59b2d2ebd9a', 'src/main/resources/destiny/weapons/w62-outlaw.json': '5188d73a271b0a5080eb99d47c50a6d37ccae11fe756ebd2893c70499f3637bc', 'src/main/resources/destiny/weapons/w66-rampage.json': 'd03a2518629ce36aac140837f92950083c1a546c14f6cd5ff3310cac1f08f6e0', 'src/main/resources/destiny/weapons/w67-precision-return.json': '5ff05d82bb3e17eecb4754acd0be6a18f29ef2d147e4b1d8ad6db721e4d21976', 'src/main/resources/destiny/weapons/w68-snapshot.json': '7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738', 'src/main/resources/destiny/weapons/w73-archers-tempo.json': '19a3f2d275846b512a62b9f4d090765f9c8efc35096ba77c823d509420708c85', 'src/main/resources/destiny/weapons/w77-dragonfly.json': '239e4fa48afebebd20ed765fc05b3e61bb34532bffea3a8cffdc536c867eab06', 'src/main/resources/destiny/weapons/w80-payload.json': '000fef1ccea2cdc653f723be8d8eeefb209255673dcc8189b3732c69173a03fc', 'art/weapons/w43/extraction.json': 'a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5', 'art/weapons/w46/weapon_formulas.json': 'fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d', 'art/weapons/w46/stat_calc.rs': '5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2', 'art/weapons/w46/rs_types.rs': 'faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90', 'art/weapons/w46/MIT-LICENSE': '50173139375c53459837abdeb7ad9f264eba4f0bc2bb2c676932991ce158778d', 'art/weapons/w46/UNLICENSE': '6b0382b16279f26ff69014300541967a356a666eb0b91b422f6862f6b7dad17e', 'inventory': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', 'plugsets': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', 'manifest': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', 'clarity': '881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384', 'ddc': 'eae6696dfc65d4cc195026df2abb015fd758b4f7e136ea16701ae5536eaac4cc'}
EXPECTED = [{'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 903350103}, {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 473189353}, {'id': 'distant_relation', 'hash': 2034817450, 'socket': 4, 'perkHash': 280464955, 'plugSetHash': 3824767299}, {'id': 'whispering_slab', 'hash': 211938782, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 1885424927}, {'id': 'bite_of_the_fox', 'hash': 1403800851, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 563442205}, {'id': 'beloved', 'hash': 3107853529, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 1196545279}, {'id': 'apostate', 'hash': 2164448701, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 1306932196}, {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 3, 'perkHash': 280464955, 'plugSetHash': 3785896921}]
EXPECTED_PAIRS = [{'id': 'whispering_slab', 'perk': 'demolitionist', 'roll': {'id': 'whispering_slab', 'hash': 211938782, 'socket': 4, 'perkHash': 3523296417, 'plugSetHash': 967526625}}, {'id': 'seventh_seraph_officer_revolver', 'perk': 'feeding_frenzy', 'roll': {'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 4, 'perkHash': 2779035018, 'plugSetHash': 3527094473}}, {'id': 'steelfeather_repeater', 'perk': 'surrounded', 'roll': {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 4, 'perkHash': 3708227201, 'plugSetHash': 2645685327}}, {'id': 'dream_breaker', 'perk': 'surrounded', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 3708227201, 'plugSetHash': 1206254527}}, {'id': 'steelfeather_repeater', 'perk': 'swashbuckler', 'roll': {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 4, 'perkHash': 4082225868, 'plugSetHash': 2645685327}}, {'id': 'whispering_slab', 'perk': 'swashbuckler', 'roll': {'id': 'whispering_slab', 'hash': 211938782, 'socket': 4, 'perkHash': 4082225868, 'plugSetHash': 967526625}}, {'id': 'seventh_seraph_officer_revolver', 'perk': 'multikill_clip', 'roll': {'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 4, 'perkHash': 2458213969, 'plugSetHash': 3527094473}}, {'id': 'steelfeather_repeater', 'perk': 'multikill_clip', 'roll': {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 4, 'perkHash': 2458213969, 'plugSetHash': 2645685327}}, {'id': 'apostate', 'perk': 'multikill_clip', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 2458213969, 'plugSetHash': 2826016044}}, {'id': 'apostate', 'perk': 'rapid_hit', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 247725512, 'plugSetHash': 2826016044}}, {'id': 'dream_breaker', 'perk': 'tap_the_trigger', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 1890422124, 'plugSetHash': 1206254527}}, {'id': 'dream_breaker', 'perk': 'frenzy', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 4104185692, 'plugSetHash': 1206254527}}, {'id': 'seventh_seraph_officer_revolver', 'perk': 'vorpal_weapon', 'roll': {'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 4, 'perkHash': 1546637391, 'plugSetHash': 3527094473}}, {'id': 'steelfeather_repeater', 'perk': 'vorpal_weapon', 'roll': {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 4, 'perkHash': 1546637391, 'plugSetHash': 2645685327}}, {'id': 'whispering_slab', 'perk': 'vorpal_weapon', 'roll': {'id': 'whispering_slab', 'hash': 211938782, 'socket': 4, 'perkHash': 1546637391, 'plugSetHash': 967526625}}, {'id': 'bite_of_the_fox', 'perk': 'vorpal_weapon', 'roll': {'id': 'bite_of_the_fox', 'hash': 1403800851, 'socket': 4, 'perkHash': 1546637391, 'plugSetHash': 2442672691}}, {'id': 'seventh_seraph_officer_revolver', 'perk': 'high_impact_reserves', 'roll': {'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 4, 'perkHash': 2213355989, 'plugSetHash': 3527094473}}, {'id': 'dream_breaker', 'perk': 'high_impact_reserves', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 2213355989, 'plugSetHash': 1206254527}}, {'id': 'steelfeather_repeater', 'perk': 'elemental_capacitor', 'roll': {'id': 'steelfeather_repeater', 'hash': 1251729046, 'socket': 4, 'perkHash': 3511092054, 'plugSetHash': 2645685327}}, {'id': 'beloved', 'perk': 'quickdraw', 'roll': {'id': 'beloved', 'hash': 3107853529, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 887157889}}, {'id': 'apostate', 'perk': 'quickdraw', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 2826016044}}, {'id': 'dream_breaker', 'perk': 'quickdraw', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 706527188, 'plugSetHash': 1206254527}}, {'id': 'distant_relation', 'perk': 'zen_moment', 'roll': {'id': 'distant_relation', 'hash': 2034817450, 'socket': 3, 'perkHash': 2387244414, 'plugSetHash': 1131958073}}, {'id': 'distant_relation', 'perk': 'auto_loading_holster', 'roll': {'id': 'distant_relation', 'hash': 2034817450, 'socket': 3, 'perkHash': 3300816228, 'plugSetHash': 1131958073}}, {'id': 'apostate', 'perk': 'kill_clip', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 1015611457, 'plugSetHash': 2826016044}}, {'id': 'distant_relation', 'perk': 'outlaw', 'roll': {'id': 'distant_relation', 'hash': 2034817450, 'socket': 3, 'perkHash': 1168162263, 'plugSetHash': 1131958073}}, {'id': 'beloved', 'perk': 'rampage', 'roll': {'id': 'beloved', 'hash': 3107853529, 'socket': 4, 'perkHash': 3425386926, 'plugSetHash': 887157889}}, {'id': 'dream_breaker', 'perk': 'rampage', 'roll': {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 4, 'perkHash': 3425386926, 'plugSetHash': 1206254527}}, {'id': 'distant_relation', 'perk': 'triple_tap', 'roll': {'id': 'distant_relation', 'hash': 2034817450, 'socket': 3, 'perkHash': 3400784728, 'plugSetHash': 1131958073}}, {'id': 'apostate', 'perk': 'snapshot_sights', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 957782887, 'plugSetHash': 2826016044}}, {'id': 'bite_of_the_fox', 'perk': 'explosive_payload', 'roll': {'id': 'bite_of_the_fox', 'hash': 1403800851, 'socket': 4, 'perkHash': 3038247973, 'plugSetHash': 2442672691}}, {'id': 'apostate', 'perk': 'explosive_payload', 'roll': {'id': 'apostate', 'hash': 2164448701, 'socket': 4, 'perkHash': 3038247973, 'plugSetHash': 2826016044}}]
EXPECTED_PAIRS.sort(key=lambda p:(p["id"],p["perk"],p["roll"]["socket"]))
CLARITY_PIN = {'commit': '039cfbc4732c33573568b28cc6335dd3332a9296', 'url': 'https://raw.githubusercontent.com/Database-Clarity/Live-Clarity-Database/039cfbc4732c33573568b28cc6335dd3332a9296/descriptions/clarity.json'}
PERK = {"id":"firmly_planted","hash":BASE,
 "ordinary":{"stabilityBonus":20,"handlingBonus":30,"accuracyScalar":0.6,"growthScalar":0.83,"yawScalar":0.2},
 "fusion":{"stabilityBonus":10,"handlingBonus":15,"accuracyScalar":0.8,"growthScalar":0.915,"yawScalar":0.6}}
POLICIES = {"condition":"ACTUAL_CROUCH_MASTER_OWNED_NO_PROC_HUD",
 "unsupported":"BONUS_ZERO_SCALAR_ONE_TIMING_THROWS",
 "timing":"TOTAL_BONUS_CAP_0_100_RAW_SECONDS_SCALAR_SINGLE_CEIL_20TPS",
 "stow":"HISTORICAL_STAT100_FLOOR", "snapshot":"EXACT_DISTINCT_PAIR_ENTER_ONLY_NO_EXIT_SCALAR",
 "yaw":"HORIZONTAL_ONLY_NOT_PITCH_OR_RECOIL_DIRECTION_STAT",
 "source":"CURRENT_DDC_BASE_PVE_PVP_UNSPLIT_ENHANCED_EXCLUDED_HISTORICAL_CURVES"}

def require(ok,why):
    if not ok: raise ValueError(why)
def digest(raw): return hashlib.sha256(raw).hexdigest()
def encode(x): return (json.dumps(x,indent=2,ensure_ascii=False,allow_nan=False)+"\n").encode()
def eligible(index,traits,field,pool,match,legendary,perk=BASE):
    return (legendary is True and index in traits and field=="randomizedPlugSetHash"
      and pool.get("isFakePlugSet") is False and type(match.get("plugItemHash")) is int
      and match["plugItemHash"]==perk and match.get("currentlyCanRoll") is True)
def solve(c,stat):
    require(set(c)=={"evpp","vpp","offset"} and all(type(v) in (int,float) and math.isfinite(v) for v in c.values()),"finite original curve")
    s=c["evpp"]*stat*stat+c["vpp"]*stat+c["offset"]
    require(math.isfinite(s) and 0<s<=60,"safe seconds")
    return s
def ticks(s):return max(1,math.ceil(s*20))
def evaluate(c,total=0,scalar=1.0,snapshot=False):
    require(type(total) is int and math.isfinite(scalar) and 0<scalar<=1,"total/scalar")
    require(not snapshot or c["snapshotScalar"] is not None,"distinct Snapshot required")
    h=min(100,max(0,c["baseHandlingStat"]+total))
    return {"readyTicks":ticks(solve(c["ready"],h)*scalar),
      "stowTicks":ticks(max(solve(c["stow"],h),solve(c["stow"],100))*scalar),
      "adsTicks":max(1 if snapshot else 2,min(20,ticks(solve(c["ads"],h)*(c["snapshotScalar"] if snapshot else 1))))}
def validate(r,curves):
    require(set(r)=={"stage","perk","policies","weapons","curves","coSelections"} and r["stage"]=="W189"
      and r["perk"]==PERK and r["policies"]==POLICIES,"strict schema/mechanics/policy")
    require(r["weapons"]==EXPECTED and r["coSelections"]==EXPECTED_PAIRS and r["curves"]==curves,"exact rolls/curves/distinct pairs")

def generate(a):
    paths={k:a.root/k for k in PINS if "/" in k}
    paths.update(inventory=a.inventory,plugsets=a.plugsets,manifest=a.manifest,clarity=a.clarity,ddc=a.ddc)
    data={};pins={}
    for k,path in paths.items():
        raw=path.read_bytes();require(digest(raw)==PINS[k],"source SHA mismatch: "+k)
        pins[k]={"sha256":digest(raw),"bytes":len(raw)}
        if path.suffix==".json":data[k]=json.loads(raw)
    prefix="src/main/resources/destiny/weapons/"
    selected=list(data[prefix+"w40-characteristics.json"]);catalog=list(data[prefix+"w30.json"])
    for f in ("w83-exotics.json","w84-exotics.json"):
        selected.extend(r["characteristics"] for r in data[prefix+f]);catalog.extend(r["catalog"] for r in data[prefix+f])
    require(len(selected)==len(catalog)==len({r["id"] for r in selected})==len({r["bungieHash"] for r in selected})==65,"exact current65")
    require({r["id"] for r in selected}=={r["id"] for r in catalog},"catalog characteristic coverage")
    manifest=data["manifest"]["Response"];require(manifest["version"]==VERSION,"official version")
    for component in ("DestinyInventoryItemDefinition","DestinyPlugSetDefinition"):
        require(manifest["jsonWorldComponentContentPaths"]["en"][component]=="/common/destiny2_content/json/en/"+component+"-e677f6ea-2a1e-48d4-a8c8-700a39a62585.json","official components")
    inv,pools=data["inventory"],data["plugsets"]
    for h in (BASE,ENHANCED):
        d=inv[str(h)];require(d["hash"]==h and d["itemType"]==19 and not d["redacted"] and not d["blacklisted"] and not d["plug"]["isDummyPlug"]
           and d["itemTypeDisplayName"]==("Trait" if h==BASE else "Enhanced Trait"),"exact official definition")
    rows=[];scans=[];proofs=[]
    for w in selected:
        d=inv[str(w["bungieHash"])];require(d["hash"]==w["bungieHash"] and d["itemType"]==3 and not d["redacted"] and not d["blacklisted"]
          and (d["inventory"]["tierType"]==6)==w["exotic"],"official catalog identity")
        if not w["exotic"]:require({k:v["value"] for k,v in d["stats"]["stats"].items()}==w["stats"],"official current stats")
        s=d["sockets"];traits={n for c in s["socketCategories"] if c["socketCategoryHash"]==TRAIT for n in c["socketIndexes"]}
        scan={"id":w["id"],"hash":d["hash"],"tier":d["inventory"]["tierType"],"exotic":w["exotic"],"traitIndexes":sorted(traits),"references":[]}
        for n,sock in enumerate(s["socketEntries"]):
            for field in ("randomizedPlugSetHash","reusablePlugSetHash"):
                ph=sock.get(field)
                if not ph:continue
                pool=pools[str(ph)];require(pool["hash"]==ph and not pool["redacted"] and not pool["blacklisted"],"official pool")
                matches=[m for m in pool["reusablePlugItems"] if m["plugItemHash"] in (BASE,ENHANCED)]
                scan["references"].append({"socket":n,"field":field,"plugSetHash":ph,"isFakePlugSet":pool["isFakePlugSet"],"matches":matches})
                for m in matches:
                    if eligible(n,traits,field,pool,m,d["inventory"]["tierType"]==5 and not w["exotic"]):
                        r=dict(zip(KEYS,(w["id"],d["hash"],n,BASE,ph)))
                        if r not in rows:rows.append(r)
                        proofs.append({**r,"socketCategoryHash":TRAIT,"socketEntry":sock,"matchingEntry":m})
        scans.append(scan)
    require(rows==EXPECTED,"exact base8 admission")
    pairs=[];audit=[]
    for name,file in PROFILES.items():
        x=data[prefix+file]
        if file=="w67-precision-return.json":rs=next(t["weapons"] for t in x["perks"] if t["id"]==name)
        else:rs=x.get("rolls",x.get("weapons"))
        accepted=[];denied=[]
        for arow in rows:
            for original in rs:
                if original["id"]!=arow["id"]:continue
                b={k:original[k] for k in KEYS}; d=inv[str(arow["hash"])];s=d["sockets"]
                traits={i for c in s["socketCategories"] if c["socketCategoryHash"]==TRAIT for i in c["socketIndexes"]}
                sock=s["socketEntries"][b["socket"]];ph=sock.get("randomizedPlugSetHash");pool=pools.get(str(ph),{})
                require(ph==b["plugSetHash"] and b["hash"]==arow["hash"] and any(eligible(b["socket"],traits,"randomizedPlugSetHash",pool,m,True,b["perkHash"]) for m in pool.get("reusablePlugItems",[])),"exact companion source: "+name)
                pair={"id":arow["id"],"perk":name,"roll":b}
                if b["socket"]!=arow["socket"]:pairs.append(pair);accepted.append(b)
                else:denied.append({"roll":b,"reason":"SAME_SOCKET"})
        audit.append({"perk":name,"profile":file,"accepted":accepted,"denied":denied})
    pairs.sort(key=lambda p:(p["id"],p["perk"],p["roll"]["socket"]))
    require(pairs==EXPECTED_PAIRS and len(PROFILES)==35,"all implemented exact32 distinct pairs")
    clarity=data["clarity"][str(BASE)];ct="\n".join(l.get("text","") for b in clarity["descriptions"]["en"] for l in b.get("linesContent",[]))
    require(clarity["hash"]==BASE and clarity["type"]=="Weapon Trait" and all(t in ct for t in ("While Crouched", "30 Handling and 20 Stability","-40%","-17%","-80%","halved on Fusion Rifles")),"current Clarity base")
    htmlraw=paths["ddc"].read_text();ddcrows=[r for r in re.findall(r"<tr\b[^>]*>.*?</tr>",htmlraw,re.S) if "Firmly Planted" in r]
    require(len(ddcrows)==1 and '1662574278R96' in ddcrows[0],"DDC actual row97")
    rowhtml=ddcrows[0];ddctext=html.unescape(re.sub('<[^>]+>',' ',rowhtml.replace('<br>','\n')))
    require(all(v in ddctext for v in ('+20','+30','-40%','-17%','-80%','[Fusion Rifles] 10','+15','-20%','-8.5%','-40%','↑+25','↑+35','↑+13','↑+18')),"DDC separate base/enhanced fusion values")
    mapping={m["id"]:m for m in data["art/weapons/w43/extraction.json"]["entries"]};formulas=data["art/weapons/w46/weapon_formulas.json"]
    byid={w["id"]:w for w in selected};idx=lambda f:{r["id"]:r for r in data[prefix+f]}
    handling,aim=idx("w58-handling.json"),idx("w44-aim.json");snap=data[prefix+"w68-snapshot.json"]
    curves=[];curveaudit=[];cases=[]
    for r in rows:
        id=r["id"];w=byid[id];m=mapping[id];raw=formulas[m["family"]]["cat"][m["category"]]["handling"]
        c={"id":id,"baseHandlingStat":w["stats"]["943549884"],"snapshotScalar":None}
        if any(b["id"]==id and b["perk"]=="snapshot_sights" for b in pairs):
            ammo=inv[str(w["bungieHash"])]["equippingBlock"]["ammoType"];require(ammo in (1,2),"Snapshot ammo")
            c["snapshotScalar"]=snap["primaryScalar" if ammo==1 else "specialScalar"]
        for k in ("ready","stow","ads"):c[k]={v:raw[k].get(v,0.0) for v in ("evpp","vpp","offset")}
        baseline=evaluate(c);h=handling[id]["profile"];ads=aim[id]["profile"]
        require(h["supported"] and baseline=={"readyTicks":h["readyTicks"],"stowTicks":h["stowTicks"],"adsTicks":ads["transitionTicks"]},"original/current raw baseline "+id)
        bonus=15 if id=="dream_breaker" else 30
        curves.append(c);curveaudit.append({"id":id,"mapping":m,"baseline":baseline,"crouched":evaluate(c,bonus)})
        options=[("planted",bonus,1.0,False)]
        for b in pairs:
            if b["id"]!=id:continue
            if b["perk"]=="elemental_capacitor":options.append(("planted_arc",bonus+50,1.0,False))
            if b["perk"]=="frenzy":options.append(("planted_frenzy",bonus+100,1.0,False))
            if b["perk"]=="quickdraw":options.append(("planted_quickdraw_ready",100,0.95,False));options.append(("planted_quickdraw_stow",100,1.0,False))
            if b["perk"]=="snapshot_sights":options.append(("planted_snapshot_enter",bonus,1.0,True))
        for label,total,scalar,snapshot in options:cases.append({"id":id,"case":label,"totalBonus":total,"scalar":scalar,"snapshotEntering":snapshot,"expected":evaluate(c,total,scalar,snapshot)})
    resource={"stage":"W189","perk":PERK,"policies":POLICIES,"weapons":rows,"curves":curves,"coSelections":pairs};validate(resource,curves)
    official={"version":VERSION,"definitions":[inv[str(BASE)],inv[str(ENHANCED)]],"selectedCount":65,"rolls":rows,"proofs":proofs,"scans":scans,"companionAudit":audit,
      "officialTraitPools":[{"id":r["id"],"socket":n,"socketEntry":s,"pool":pools[str(s["randomizedPlugSetHash"])]} for r in rows for n,s in enumerate(inv[str(r["hash"])]["sockets"]["socketEntries"]) if n in {i for c in inv[str(r["hash"])]["sockets"]["socketCategories"] if c["socketCategoryHash"]==TRAIT for i in c["socketIndexes"]} and s.get("randomizedPlugSetHash")]}
    source={"clarity":CLARITY_PIN,"clarityWholeSha256":PINS["clarity"],"baseEntry":clarity,"enhancedExcluded":ENHANCED,
      "ddcUrl":"https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278","ddcRow":97,"ddcFetchedDate":"2026-10-27","ddcWholeSha256":PINS["ddc"],"ddcRowHtml":rowhtml,"ddcRowText":ddctext,
      "mechanics":PERK,"pvePvp":"No mode split in row97; same base effects, no damage or flinch percentage invented.","uncertainty":"Original text retained verbatim including any question marks; enhanced arrows are excluded."}
    outputs={TARGET:resource,ART+"official-sockets.json":official,ART+"clarity-source.json":source}
    outputs[ART+"manifest.json"]={"stage":"W189","generator":SCRIPT,"generatorSha256":digest((a.root/SCRIPT).read_bytes()),"sourcePins":pins,"version":VERSION,"curveAudit":curveaudit,"timingCases":cases,"implementedTraitCount":len(PROFILES),"legalPairCount":len(pairs),"sameSocketDeniedCount":sum(len(x["denied"]) for x in audit),"outputs":{k:digest(encode(v)) for k,v in outputs.items()},
      "limitations":["Historical d2foundry oracle dcd0c7d302b056ffbb532edcb711d724a17ca8c1 raw curves; no new current-sandbox timing measurement.","Pure profile; master owns actual crouch/source authority, runtime, registry, gameplay integration and native batch.","No native/audio/gameplay footage verification claimed by this worker; numeric sources are data, not visual evidence."]}
    return outputs

def self_test(outputs):
    r=outputs[TARGET];curves=r["curves"];n=0
    def rejects(f):
        nonlocal n
        try:f()
        except (ValueError,KeyError,TypeError):n+=1;return
        raise AssertionError("unexpected acceptance")
    for key in r:
        x=copy.deepcopy(r);del x[key];rejects(lambda:validate(x,curves))
    for k,v in (("extra",True),("stage","W188"),("perk",{}),("policies",{}),("weapons",EXPECTED[:-1]),("coSelections",EXPECTED_PAIRS[:-1]),("curves",[])):
        x=copy.deepcopy(r);x[k]=v;rejects(lambda:validate(x,curves))
    for k,v in (("perkHash",ENHANCED),("socket",0),("plugSetHash",1),("hash",1),("id","ace_of_spades")):
        x=copy.deepcopy(r);x["weapons"][0][k]=v;rejects(lambda:validate(x,curves))
    args=[3,{3},"randomizedPlugSetHash",{"isFakePlugSet":False},{"plugItemHash":BASE,"currentlyCanRoll":True},True]
    require(eligible(*args),"positive exact predicate")
    for index,bad in ((0,4),(1,{4}),(2,"reusablePlugSetHash"),(2,"singleInitialItemHash"),(2,"reusablePlugItems"),(3,{"isFakePlugSet":True}),(3,{"isFakePlugSet":0}),(4,{"plugItemHash":BASE,"currentlyCanRoll":1}),(4,{"plugItemHash":ENHANCED,"currentlyCanRoll":True}),(5,False),(5,1)):
        x=copy.deepcopy(args);x[index]=bad;require(not eligible(*x),"negative official predicate");n+=1
    for c in curves:
        for bad in (float("nan"),float("inf"),0,-1,1.01):rejects(lambda:evaluate(c,scalar=bad))
        require(evaluate(c,2**31-1)==evaluate(c,100),"wide cap")
    return n

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",type=Path,default=ROOT)
    for key,path in {"inventory":"/tmp/destiny-weapons-w30/bungie-items.json","plugsets":"/tmp/destiny-weapons-w60/bungie-plugsets.json","manifest":"/tmp/destiny-weapons-w60/manifest.json","clarity":"/private/tmp/w189-planted-report/clarity.json","ddc":"/private/tmp/w189-planted-report/ddc-perks.html"}.items():p.add_argument("--"+key,type=Path,default=Path(path))
    p.add_argument("--verify",action="store_true");p.add_argument("--self-test",action="store_true");a=p.parse_args();outputs=generate(a)
    if a.self_test:
        n=self_test(outputs);require({k:encode(v) for k,v in outputs.items()}=={k:encode(v) for k,v in generate(a).items()},"deterministic repeat");print("bounded negative checks",n,"deterministic repeat PASS")
    for name,value in outputs.items():
        dest=a.root/name;raw=encode(value)
        if a.verify:require(dest.read_bytes()==raw,"output drift: "+name)
        else:dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(raw)
    print("W189 exact8 / selected65 / implemented35 / distinct32 / JSON4", "VERIFIED" if a.verify else "GENERATED")
if __name__=="__main__":main()
