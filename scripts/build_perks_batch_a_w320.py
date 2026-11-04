#!/usr/bin/env python3
"""W320 batch A trait data: exact pinned Bungie sockets (manifest 245114.26.10.13.2000-1-bnet.66137),
DDC Weapon Perks rows (PvE base, non-enhanced) and per-weapon original stat curves for ratio scaling.

Inputs (read-only): /tmp/dg-loot/{missing,items,items-ko,plugsets}.json, /tmp/dg-loot/ddc/weapon-perks.html,
art/weapons/w46/weapon_formulas.json, art/weapons/w43/extraction.json.
"""
import html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOOT = Path("/tmp/dg-loot")
OUT = ROOT / "src/main/resources/destiny/weapons"
VERSION = "245114.26.10.13.2000-1-bnet.66137"

def require(ok, msg):
    if not ok: sys.exit("W320 batch A: " + msg)

LOCAL = "LOCAL_POLICY"
PERKS = [
  # name, id, slug, damage, params, policies, ddc numeric tokens that must appear in the row
  ("Field Prep", "field_prep", "field-prep", False,
   {"ammoGenerationBonus": 20, "crouchReloadBonus": 50, "crouchReloadScalar": 0.8, "crouchHandlingScalar": 0.8},
   {"crouch": "server-authoritative Player#isCrouching; shift also drives ADS input in this port",
    "ammoGeneration": "added to this weapon's AmmoGeneration stat at emission (clamped 0..100)",
    "reloadComposition": "stat curve ratio at +50 Reload, then x0.8, applied to the incoming plan"},
   ["+20", "+50", "0.8x Reload Duration", "0.8x Ready/Stow"]),
  ("Slideways", "slideways", "slideways", False,
   {"refillFraction": 0.15, "stabilityBonus": 15, "handlingBonus": 30, "durationTicks": 60, "cooldownTicks": 10, "removedOnStow": True},
   {"slide": LOCAL + ": vanilla has no slide; sprint->crouch on ground at >=0.2 blocks/tick is a slide",
    "stabilityBonus": LOCAL + ": DDC base value is marked '?'; +15 used as written but unconfirmed",
    "handlingBonus": LOCAL + ": DDC base value is marked '?'; +30 used as written but unconfirmed",
    "refillRounding": LOCAL + ": ceil(15% of magazine), at least one round, from reserve",
    "heat": "no weapon heat system in this port; magazine refill only"},
   ["15% of Magazine", "+15", "+30", "3 seconds", "0.5 seconds"]),
  ("Slideshot", "slideshot", "slideshot", False,
   {"refillFraction": 0.15, "rangeBonus": 20, "stabilityBonus": 20, "durationTicks": 50, "cooldownTicks": 6, "firstShotOnly": True, "removedOnStow": True},
   {"slide": LOCAL + ": same server slide detector as Slideways",
    "stabilityBonus": LOCAL + ": DDC base value is marked '?'; +20 used as written but unconfirmed",
    "refillRounding": LOCAL + ": ceil(15% of magazine), at least one round, from reserve",
    "firstShot": "range/stability end after the first paid emission (pulse burst: first bullet)"},
   ["15% of Magazine", "+20", "2.5 seconds", "0.3 seconds"]),
  ("Eye of the Storm", "eye_of_the_storm", "eye-of-the-storm", False,
   {"triggerShield": 40, "fullShield": 80, "handlingBonus": 30, "coneScalar": 0.6, "growthScalar": 0.83},
   {"shield": "shield HP = scaled Minecraft health minus Guardian health pool (PvE 200=70+130, Crucible 230=100+130)",
    "scaling": "activates at <=40 shield HP; effect=(80-shield)/80 linear; ends when shield >=80",
    "handling": "fractional +30 handling evaluated on the original stat curve without rounding the stat"},
   ["40 Shield HP", "+30", "-40%", "-17%", "80 Shield HP"]),
  ("Killing Wind", "killing_wind", "killing-wind", False,
   {"rangeBonus": 20, "mobilityBonus": 50, "handlingBonus": 40, "falloffScalar": 1.05, "durationTicks": 100, "extendTicks": 100, "maxTicks": 160, "removedOnStow": True},
   {"mobility": LOCAL + ": no Mobility stat; WeaponPerkMovement maps 100 Mobility to x1.4 walking, so +50 = +20% movement speed",
    "falloff": "range falloff start/end x1.05 after summed Range"},
   ["+20 Range", "+50 Mobility", "+40 Handling", "5%", "+5 seconds", "8 seconds"]),
  ("Air Assault", "air_assault", "air-assault", False,
   {"passiveAirborne": 10, "airbornePerStack": 30, "maxStacks": 2, "airborneKillStacks": 2, "durationTicks": 100, "removedOnStow": True},
   {"airborneKill": "WeaponAccuracy.airborne(owner) at the confirmed final blow"},
   ["+10", "+30", "5 seconds", "2 stacks"]),
  ("Tunnel Vision", "tunnel_vision", "tunnel-vision", False,
   {"killWindowTicks": 72, "durationTicks": 100, "aimAssistBonus": 20, "growthScalar": 0.85, "adsScalar": 0.8},
   {"aimAssist": "source-only; this port has no aim assist simulation",
    "growthScalar": LOCAL + ": DDC '-?%' cone growth; 0.85 is a local placeholder, not a Destiny value",
    "adsScalar": LOCAL + ": DDC '+?' ADS handling; x0.8 ADS duration is a local placeholder, not a Destiny value",
    "trigger": "reload completion of this weapon within 3.6s of this weapon's final blow"},
   ["3.6 seconds", "+20 Aim Assist", "5"]),
  ("Fragile Focus", "fragile_focus", "fragile-focus", False,
   {"rangeBonus": 20, "reactivateTicks": 20},
   {"shield": "same shield model as Eye of the Storm; shields active means shield HP > 0",
    "reactivation": "re-enabled 1s after shield HP returns to full (130)"},
   ["+20 Range", "Critical Health", "1"]),
  ("Kickstart", "kickstart", "kickstart", True,
   {"sprintTicks": 30, "damageMultiplier": 1.15, "chargeScalar": 0.8, "durationTicks": 40},
   {"slide": LOCAL + ": same server slide detector; sprint streak measured before the crouch",
    "duration": LOCAL + ": DDC duration is '?'; 2 seconds is a local placeholder",
    "damage": "captured at paid emission, applies to this weapon's bolts"},
   ["1.5 seconds", "15%", "0.8x Charge Time"]),
  ("Shot Swap", "shot_swap", "shot-swap", False,
   {"stacksPerKill": 2, "maxStacks": 6, "handlingBonus": 100, "durationScalar": 0.7},
   {"consume": "one stack per real stow transaction of this weapon; ready uses stacks without consuming"},
   ["2 stacks", "6 stacks", "+100", "0.7x"]),
  ("Bait and Switch", "bait_and_switch", "bait-and-switch", True,
   {"chainTicks": 140, "damageMultiplier": 1.3, "durationTicks": 200, "persistsThroughStow": True},
   {"equipped": "loadout equipped weapons, or hotbar weapons in standalone mode",
    "chain": "each weapon damage instance must follow the previous one within 7s; timer disabled while active",
    "damage": "captured at emission; projectiles keep the buff they were fired with"},
   ["7 seconds", "30%", "10"]),
]

def main():
    missing = json.loads((LOOT / "missing.json").read_text())
    items = json.loads((LOOT / "items.json").read_text())
    ko = json.loads((LOOT / "items-ko.json").read_text())
    plugsets = json.loads((LOOT / "plugsets.json").read_text())
    ddc_html = (LOOT / "ddc/weapon-perks.html").read_text()
    rows = re.findall(r"<tr\b[^>]*>.*?</tr>", ddc_html, re.S)
    stats = {r["id"]: r for r in json.loads((OUT / "w40-characteristics.json").read_text())}
    catalog = {r["id"]: r for r in json.loads((OUT / "w30.json").read_text())}
    formulas = json.loads((ROOT / "art/weapons/w46/weapon_formulas.json").read_text())
    mapping = {e["id"]: e for e in json.loads((ROOT / "art/weapons/w43/extraction.json").read_text())["entries"]}
    labels = {}
    weapons = set()
    for name, pid, slug, damage, params, policies, tokens in PERKS:
        entry = missing[name]
        ph = entry["perkHash"]
        item = items[str(ph)]
        require(item["displayProperties"]["name"] == name, "perk identity " + name)
        hits = [r for r in rows if re.search(r">\s*" + re.escape(name) + r"\s*<", r)]
        require(len(hits) == 1, "one DDC row " + name)
        text = html.unescape(re.sub(r"<[^>]+>", " ", hits[0].replace("<br>", "\n")))
        text = re.sub(r"\s+", " ", text).strip()
        for t in tokens: require(t in text, f"DDC token {t!r} in {name}")
        rid = re.search(r'id="([^"]+)"', hits[0])
        rolls = []
        for r in entry["rolls"]:
            require(r["perkHash"] == ph and r["id"] in stats and stats[r["id"]]["bungieHash"] == r["hash"], "roll identity " + str(r))
            require(not stats[r["id"]]["exotic"], "exotic " + r["id"])
            weapon = items[str(r["hash"])]
            sock = weapon["sockets"]["socketEntries"][r["socket"]]
            require(sock.get("randomizedPlugSetHash") == r["plugSetHash"], "plugset " + str(r))
            require(any(p["plugItemHash"] == ph for p in plugsets[str(r["plugSetHash"])]["reusablePlugItems"]), "pool membership " + str(r))
            rolls.append({k: r[k] for k in ("id", "hash", "socket", "perkHash", "plugSetHash")})
            weapons.add(r["id"])
        require(len({(r["id"], r["socket"]) for r in rolls}) == len(rolls), "unique sockets " + name)
        doc = {"stage": "W320", "perk": {"id": pid, "hash": ph, **params}, "policies": policies,
               "source": {"manifest": VERSION, "officialDescription": item["displayProperties"]["description"],
                          "ddcSheet": "Weapon Perks", "ddcRow": rid.group(1) if rid else None, "ddcText": text,
                          "scope": "PvE base (non-enhanced); '?' values are not facts, see policies"},
               "weapons": rolls}
        (OUT / f"w320-{slug}.json").write_text(json.dumps(doc, ensure_ascii=False, indent=1) + "\n")
        kp = ko[str(ph)]["displayProperties"]
        labels[pid] = {"name": kp["name"], "description": kp["description"], "damage": damage, "hash": ph}
    curves = []
    for wid in sorted(weapons):
        m = mapping[wid]; c = formulas[m["family"]]["cat"][m["category"]]
        s = stats[wid]["stats"]
        q = lambda d: {k: d.get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        curves.append({"id": wid, "hash": stats[wid]["bungieHash"], "family": catalog[wid]["family"],
                       "baseHandlingStat": s["943549884"], "baseReloadStat": s["4188031367"],
                       "reload": q(c["reload"]), "ready": q(c["handling"]["ready"]),
                       "stow": q(c["handling"]["stow"]), "ads": q(c["handling"]["ads"])})
    (OUT / "w320-batch-a-curves.json").write_text(json.dumps({"stage": "W320", "source": "art/weapons/w46/weapon_formulas.json via w43 mapping; base stats w40", "curves": curves}, indent=1) + "\n")
    (OUT / "w320-perks-ko-a.json").write_text(json.dumps({"source": "Bungie ko DestinyInventoryItemDefinition", "manifestVersion": VERSION, "perks": labels}, ensure_ascii=False, indent=1) + "\n")
    print("perks", len(PERKS), "weapons", len(weapons))

main()
