#!/usr/bin/env python3
"""Build exact base-trait additions from the pinned manifest and reviewed runtime allowlist."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

NEW = {
    "keep_away": ("Keep Away", "15블록 안에 적이 없으면 사거리 +10, 재장전 속도 +30."),
    "lone_wolf": ("Lone Wolf", "조준 전환이 빨라지고 공중 효율이 증가합니다. 15블록 안에 아군이 없으면 효과가 강화됩니다."),
    "enlightened_action": ("Enlightened Action", "직접 명중하면 2초 동안 핸들링과 재장전 속도가 증가합니다. 최대 12중첩, 합계 +50."),
    "eddy_current": ("Eddy Current", "1.5초 질주하면 3초 동안 재장전 속도와 무기 전환 속도가 향상됩니다. 증폭 중에는 재장전 보너스가 강화됩니다."),
    "perfect_float": ("Perfect Float", "피해를 주거나 받으며 6초 동안 전투를 유지하면 10초 동안 공중 효율 +30, 피격 흔들림 35% 감소."),
    "offhand_strike": ("Offhand Strike", "무기 처치 후 7초 동안 비조준 사격의 피해 감쇠 거리가 1.45배, 안정성이 +30 증가합니다. 수납 시 해제됩니다."),
    "rewind_rounds": ("Rewind Rounds", "탄창을 충분히 발사한 뒤 비우면 직접 명중 횟수에 따라 예비 탄약에서 일부를 다시 채웁니다."),
    "reconstruction": ("Reconstruction", "6초 동안 발사하지 않으면 6초마다 예비 탄약에서 탄창의 25%를 채웁니다. 최대 기본 탄창의 2배."),
    "precision_instrument": ("Precision Instrument", "직접 명중을 이어 가면 정밀 피해가 최대 25% 증가합니다. 최대 6중첩이며 빗나가면 초기화됩니다."),
    "successful_warm_up": ("Successful Warm-Up", "무기 처치 후 충전·당기기 시간이 37.5% 감소합니다. 6초 지속, 추가 처치마다 4초 연장되며 최대 20초. 수납 시 해제됩니다."),
    "dual_loader": ("Dual Loader", "산탄총의 탄약 삽입 한 번당 예비 탄약에서 탄약을 1발 더 장전합니다."),
    "desperate_measures": ("Desperate Measures", "무기 처치로 7초 동안 피해 +10%. 수류탄·근접 공격 처치는 +20%, 추가 능력 처치는 +30%로 강화하며 무기 처치로 지속 시간을 갱신합니다."),
    "loose_change": ("Loose Change", "적에게 원소 약화를 적용하면 9초 동안 재장전 속도 +50, 조준 중 이동 속도 페널티 20% 감소."),
    "heal_clip": ("Heal Clip", "무기 처치 후 짧은 시간 안에 재장전을 완료하면 자신에게 치유 ×2, 15블록 안의 아군에게 치유 ×1을 부여합니다."),
    "headstone": ("Headstone", "정밀 처치 지점에 시공 수정을 생성합니다. 강력한 적과 수호자는 더 큰 수정을 생성합니다."),
    "repulsor_brace": ("Repulsor Brace", "공허 약화가 적용된 적을 무기로 처치하면 8초 동안 공허 보호막을 얻습니다."),
    "strategist": ("Strategist", "무기 처치 시 직업 능력 에너지 10%를 얻습니다. 융합 소총·월도·산탄총·저격총은 20%."),
    "permeability": ("Permeability", "직업 능력을 사용하면 수납할 때까지 무기 속성이 현재 궁극기 속성으로 바뀝니다. 수납 전 한 번, 예비 탄약에서 탄창의 50%를 채웁니다."),
}
EXPANDED = {"frenzy": 4104185692, "outlaw": 1168162263, "demolitionist": 3523296417,
            "subsistence": 1820235745, "ambitious_assassin": 2010801679,
            "clown_cartridge": 2284787283, "overflow": 3643424744, "elemental_capacitor": 3511092054, "feeding_frenzy": 2779035018}
DAMAGE = {"rampage", "kill_clip", "dragonfly", "explosive_payload", "frenzy", "precision_instrument",
          "desperate_measures", "target_lock", "harmony", "under_over", "golden_tricorn", "lasting_impression",
          "timed_payload", "reservoir_burst", "explosive_head", "cluster_bomb", "chain_reaction",
          "disruption_break", "incandescent", "adaptive_munitions", "redirection", "one_two_punch"}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest-dir", type=Path, required=True)
    parser.add_argument("--registry", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    items = json.loads((args.manifest_dir / "items.json").read_text())
    korean = json.loads((args.manifest_dir / "items-ko.json").read_text())
    pools = json.loads((args.manifest_dir / "plugsets.json").read_text())
    registry = json.loads(args.registry.read_text())
    audit = json.loads(args.audit.read_text())
    resources = root / "src/main/resources/destiny/weapons"
    allow = dict(EXPANDED)
    for row in audit["perWeapon"]:
        for trait in row["staticSafeExistingTraits"]:
            allow[trait["id"]] = trait["perkHash"]
    for name in ("w321-batch-b.json", "w322-batch-c.json"):
        data = json.loads((resources / name).read_text())["perks"]
        if isinstance(data, dict): allow.update({k: v["hash"] for k, v in data.items()})
        else: allow.update({v["id"]: v["hash"] for v in data})
    safe_rows = {(w["id"], t["id"], t["socket"], t["perkHash"], t["plugSetHash"])
                 for w in audit["perWeapon"] for t in w["staticSafeExistingTraits"]}
    safe_ids = {p for row in audit["safeWithSupplementalRows"] for p in row["perks"]}
    new_by_name = {name: id for id, (name, _) in NEW.items()}
    by_hash = {h: id for id, h in allow.items()}
    traits = {}
    coverage = defaultdict(lambda: defaultdict(list))
    for weapon in registry:
        wid, wh = weapon["id"], weapon["bungie_hash"]
        sockets = items[str(wh)]["sockets"]
        trait_indexes = {i for category in sockets["socketCategories"]
                         if category["socketCategoryHash"] == 4241085061 for i in category["socketIndexes"]}
        for index, socket in enumerate(sockets["socketEntries"]):
            if index not in trait_indexes: continue
            pool_hash = socket.get("randomizedPlugSetHash")
            pool = pools.get(str(pool_hash), {})
            if not pool_hash or pool.get("isFakePlugSet", False): continue
            for option in pool.get("reusablePlugItems", []):
                ph = option["plugItemHash"]
                item = items[str(ph)]
                if not option.get("currentlyCanRoll") or item.get("itemTypeDisplayName") != "Trait": continue
                id = by_hash.get(ph) or new_by_name.get(item["displayProperties"]["name"])
                if id is None: continue
                if id in safe_ids and (wid, id, index, ph, pool_hash) not in safe_rows: continue
                if id == "dual_loader" and weapon["family"] != "shotgun": continue
                ko = korean[str(ph)]["displayProperties"]
                row = traits.setdefault(id, dict(id=id, hash=ph, name=ko["name"],
                    description=NEW[id][1] if id in NEW else ko["description"],
                    damage=id in DAMAGE, added=id in NEW, rolls=[]))
                if row["hash"] != ph: raise ValueError(f"Conflicting base hash for {id}")
                roll = dict(id=wid, hash=wh, socket=index, perkHash=ph, plugSetHash=pool_hash)
                if roll not in row["rolls"]: row["rolls"].append(roll)
                coverage[wid][index].append(id)
    gaps = [{"id": w["id"], "emptySockets": [s for s in (3, 4) if not coverage[w["id"]][s]]}
            for w in registry if any(not coverage[w["id"]][s] for s in (3, 4))]
    missing = sorted(set(NEW) - traits.keys())
    output = resources / "w327-traits.json"
    result = {"stage": "W327", "manifestVersion": "245114.26.10.13.2000-1-bnet.66137",
              "source": "Exact selected DestinyInventoryItemDefinition randomized nonfake currentlyCanRoll base Trait pools",
              "traits": [traits[id] for id in sorted(traits)]}
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    report = dict(traits=len(traits), newTraits=len(set(NEW) & traits.keys()),
                  rolls=sum(len(t["rolls"]) for t in traits.values()), gaps=gaps, missingNew=missing,
                  coverage=coverage, sha256=hashlib.sha256(output.read_bytes()).hexdigest())
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "coverage"}, ensure_ascii=False))
    if gaps or missing: raise SystemExit(2)

if __name__ == "__main__": main()
