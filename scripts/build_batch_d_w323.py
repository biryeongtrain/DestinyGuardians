#!/usr/bin/env python3
"""W323 batch D: sword/glaive guard traits + Turnabout + Master of Arms.

Inputs (read-only): /tmp/dg-loot/missing.json (Bungie manifest 245114.26.10.13.2000-1-bnet.66137
socket tuples), /tmp/dg-loot/ko-items.json (ko DestinyInventoryItemDefinition, same manifest) and
/tmp/dg-loot/ddc/weapon-perks.html (Destiny Data Compendium "Weapon Perks" tab, PvE base values).
Outputs: src/main/resources/destiny/weapons/w323-batch-d.json and w323-batch-d-ko.json.
"""
import html, json, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/destiny/weapons"
PERKS = [
    ("turnabout", "Turnabout", False),
    ("counterattack", "Counterattack", True),
    ("flash_counter", "Flash Counter", True),
    ("tilting_at_windmills", "Tilting at Windmills", False),
    ("valiant_charge", "Valiant Charge", False),
    ("duelists_trance", "Duelist's Trance", False),
    ("cold_steel", "Cold Steel", False),
    ("unstoppable_force", "Unstoppable Force", True),
    ("master_of_arms", "Master of Arms", True),
]
# DDC PvE base values ("↑" enhanced values ignored). "?" values carry an explicit local policy.
VALUES = {
    "turnabout": {"overshieldHp": 50, "durationTicks": 200},
    "counterattack": {"windowTicks": 10, "damageMultiplier": 1.5, "durationTicks": 40},
    "flash_counter": {"cooldownTicks": 50, "radius": 8.0, "localConeDegrees": 60.0,
                      "pointBlankFactor": 0.75, "maxFactor": 1.10, "disorientTicks": 100},
    "tilting_at_windmills": {"speedBonus": 0.25, "durationTicks": 80},
    "valiant_charge": {"lungeScale": 1.8, "windowTicks": 20},
    "duelists_trance": {"statBonus": 60, "localStatScale": 0.3},
    "cold_steel": {"pveSlowTicks": 85, "pvpSlowTicks": 30, "lightAmplifier": 0, "heavyAmplifier": 1},
    "unstoppable_force": {"damageMultiplier": 1.2, "durationTicks": 80},
    "master_of_arms": {"x1Multiplier": 1.15, "x1Ticks": 140, "x2Multiplier": 1.25, "x2Ticks": 80},
}
POLICY = {
    "turnabout": "Combatant elemental shield = absorption pool reaching 0; Guardian shield = HP above 100/230 crossing to <=100 while the target is in Super. 50 HP scaled by owner max health/230. Separate MAX_ABSORPTION layer; FIFO with other layers is approximated by one vanilla absorption pool.",
    "counterattack": "Window measured from the first guarding tick; only frontal PvE mob hits are guardable (existing guard rule). Buff applies to that sword's damage only.",
    "flash_counter": "DDC '~8?' m cone and '?' far range: local 8 block radius, 60 degree half cone, line of sight. Damage = sword base damage x (0.75 at point blank .. 1.10 at 8 blocks), DDC 75->110 per 100. Disorient = existing BLINDED status for 5 s. Triggered from blocked frontal PvE hits; resolved on the next server tick.",
    "tilting_at_windmills": "DDC '25?%': +25% movement speed (multiplicative attribute) while the glaive shield is up, 4 s after the last blocked hit; lowering the shield ends it.",
    "valiant_charge": "Next light swing within 1 s lunges with x1.8 acquisition range and distance (healing trigger not modelled: no ally-heal event while guarding).",
    "duelists_trance": "+60 stat points mapped locally to 30%: guard resistance (blocked damage x0.7), guard endurance (30% of guard drain refunded), charge rate (+30% regeneration). Guard efficiency has no system: guard hits never cost sword energy here.",
    "cold_steel": "Slow = vanilla Slowness: light x40 -> amplifier 0, heavy and Flash Counter x60 -> amplifier 1. DDC '4.25+?' PvE / '1.5+?' PvP seconds used as 85 / 30 ticks. Passive +10 ammo capacity/magazine not applied: no sword ammo-capacity stat path.",
    "unstoppable_force": "Glaive projectile damage x1.2 for 4 s after the last blocked hit (refreshes). DDC 'or until no longer blocking' is not used because glaive shots cannot be fired with the shield raised; the timer is the only expiry.",
    "master_of_arms": "Any weapon-runtime final blow by the owner counts. x1 refreshes to 7 s, a kill during x1 grants/refreshes x2 for 4 s; x2 expiry falls back to the running x1. Persists through stow; only applies to The Recluse damage with the trait selected.",
}

def ddc_rows():
    text = open("/tmp/dg-loot/ddc/weapon-perks.html", encoding="utf-8").read()
    rows = {}
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", text, re.S):
        cells = [html.unescape(re.sub("<[^>]+>", "", c)).strip() for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        cells = [c for c in cells if c]
        if len(cells) >= 3: rows[cells[1]] = (cells[0], cells[2])
    return rows

def main():
    missing = json.load(open("/tmp/dg-loot/missing.json"))
    ko = json.load(open("/tmp/dg-loot/ko-items.json"))
    ddc = ddc_rows()
    perks, labels = [], {}
    for pid, name, damage in PERKS:
        m = missing[name]
        row, text = ddc[name]
        rolls = [{k: r[k] for k in ("id", "hash", "socket", "perkHash", "plugSetHash")} for r in m["rolls"]]
        perks.append({"id": pid, "name": name, "hash": m["perkHash"], "ddcRow": int(row), "ddc": text,
                      "values": VALUES[pid], "localPolicy": POLICY[pid], "rolls": rolls})
        dp = ko[str(m["perkHash"])]["displayProperties"]
        labels[pid] = {"name": dp["name"], "description": dp["description"], "damage": damage, "hash": m["perkHash"]}
    data = {"stage": "W323", "manifestVersion": "245114.26.10.13.2000-1-bnet.66137",
            "ddcSource": "Destiny Data Compendium / Weapon Perks (PvE base)", "perks": perks}
    (OUT / "w323-batch-d.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT / "w323-batch-d-ko.json").write_text(json.dumps({
        "source": "Bungie ko DestinyInventoryItemDefinition",
        "manifestVersion": "245114.26.10.13.2000-1-bnet.66137",
        "descriptionScope": "원작 설명: Minecraft 구현의 모든 세부 효과/수치가 동일하다는 보증이 아님",
        "perks": labels}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

if __name__ == "__main__":
    main()
