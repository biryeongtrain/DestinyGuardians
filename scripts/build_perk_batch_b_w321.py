#!/usr/bin/env python3
"""Generate W321 batch-B trait pools (12 traits) from pinned shared inputs; --verify is read-only.

Inputs (manifest 245114.26.10.13.2000-1-bnet.66137):
  /tmp/dg-loot/missing.json      exact official rolls per trait
  /tmp/dg-loot/items-ko.json     Bungie ko DestinyInventoryItemDefinition (names/descriptions)
  /tmp/dg-loot/ddc/weapon-perks.html  DDC "Weapon Perks" tab (numeric source, PvE base values)
"""
import argparse, hashlib, html, json, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "src/main/resources/destiny/weapons/w321-batch-b.json"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
DDC_URL = "https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4"

# id, English name, damage classification, mechanics (Minecraft units), local policy notes.
PERKS = [
  ("target_lock", "Target Lock", True,
   dict(hitGapTicks=4, startFraction=0.125, endFraction=1.1033, pveStart=0.167, pveEnd=0.40, pvpStart=0.1046, pvpEnd=0.25),
   "Counter = consecutive confirmed direct hits within 0.2s (4 ticks) as a fraction of base magazine; linear ramp between DDC start/end values. Any 4-tick gap, stow or edit resets. Applies to direct damage only."),
  ("envious_assassin", "Envious Assassin", False,
   dict(primaryPerKill=0.10, specialPerKill=0.20, perActivationCap=1.0, totalCapMagazines=3.0),
   "Kills with another equipped weapon while this one is stowed are counted per item. On ready: rounds += ceil(magazine*min(kills*perKill,1)), capped at 3x magazine (DDC up to +200%), funded only from reserves."),
  ("envious_arsenal", "Envious Arsenal", False,
   dict(requiredOtherWeapons=2),
   "Positive actual damage from both other equipped weapons while this one is stowed; on ready refills the magazine to base capacity from reserves. Enhanced +10 Ammo Generation excluded (base trait)."),
  ("harmony", "Harmony", True,
   dict(windowTicks=60, durationTicks=140, damageMultiplier=1.20, handlingBonus=15),
   "Ready within 3s of a final blow with a different weapon grants +20% damage for 7s; persists through stow. +15 Handling is NOT applied: no sourced handling curve exists for retraced_path/goldtusk in this repo."),
  ("under_over", "Under-Over", True,
   dict(combatantShieldMultiplier=1.50, guardianOvershieldMultiplier=1.20),
   "Minecraft combatant shields are absorption; elemental shield and overshield cannot be distinguished, so all combatant absorption uses the DDC elemental-shield +50%. Guardian absorption uses DDC Guardian overshield +20%. Whole direct transaction scaled while shield is up; explosive/perk splash excluded."),
  ("golden_tricorn", "Golden Tricorn", True,
   dict(weaponKillMultiplier=1.15, weaponKillTicks=140, abilityKillMultiplier=1.50, abilityKillTicks=200),
   "Ability kill = any Combat.damage kill attributed ABILITY (grenade/melee/class ability are not distinguished by the runtime) whose element equals the weapon element. Stow clears."),
  ("lasting_impression", "Lasting Impression", True,
   dict(delayTicks=60, damageMultiplier=1.35, blastRadiusScale=1.15),
   "Rocket blast is deferred 3s and follows the struck entity. DDC +50 Blast Radius stat has no stat->meter curve here; local radius x1.15."),
  ("timed_payload", "Timed Payload", True,
   dict(payloadFraction=0.55, payloadBonusPve=0.30, delayTicks=12, radius=1.5, splashFloor=0.5),
   "55% of body-equivalent impact damage is moved into a payload detonating after 0.6s at the struck target (PvE +30%, PvP no bonus); precision damage keeps (mult-0.55) body units. Radius '?' in DDC: local 1.5 blocks, others 50%."),
  ("reservoir_burst", "Reservoir Burst", True,
   dict(damageMultiplier=1.30, burstLatchTicks=10, explosionFraction=1.0, radius=3.0),
   "Full magazine observed at the last server tick latches +30% for the next burst (10-tick bolt window). Direct kills explode for 1.0x weapon local per-bolt damage within 3 blocks (DDC radius '?'). +30 Magazine stat not applied (no fusion magazine stat curve)."),
  ("explosive_head", "Explosive Head", True,
   dict(payloadFraction=0.50, payloadBonusPve=0.30, radius=3.0, minDelayTicks=4, maxDelayTicks=16, ticksPerBlock=0.25),
   "50% of body-equivalent arrow impact damage becomes a payload (PvE +30%) detonating after a distance-based delay clamp(4+0.25*blocks,4,16) ticks within 3 blocks; arrows striking terrain also detonate there."),
  ("cluster_bomb", "Cluster Bomb", True,
   dict(bombs=8, fractionEach=0.04, radius=1.5, spread=3.0, minDelayTicks=6, maxDelayTicks=14),
   "8 bomblets scatter up to 3 blocks from the rocket detonation and explode 6-14 ticks later; each 4% of rocket local damage (DDC 150 vs ~3.7k rocket blast ratio, local), no falloff within 1.5 blocks."),
  ("chain_reaction", "Chain Reaction", True,
   dict(fraction=0.15, specialFullRadius=2.4, specialMaxRadius=6.0, powerFullRadius=3.0, powerMaxRadius=7.0, maxDepth=8),
   "On final blow (including its own explosions, depth<=8) explode for 15% of weapon local damage with DDC radii (full to 2.4/3m, linear to 0 at 6/7m). Absolute DDC values are Destiny units; fraction is local. Sword guard +20 is enhanced only."),
]

def ddc_rows(path):
    t = Path(path).read_text(encoding="utf-8")
    out = {}
    for r in re.findall(r"<tr[^>]*>(.*?)</tr>", t, re.S):
        cells = [re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", c))).strip()
                 for c in re.findall(r"<t[dh][^>]*>(.*?)</t[dh]>", r, re.S)]
        cells = [c for c in cells if c]
        if len(cells) >= 3 and cells[1] not in out:
            out[cells[1]] = dict(row=int(cells[0]) if cells[0].isdigit() else -1, text=" | ".join(cells[2:]))
    return out, hashlib.sha256(t.encode()).hexdigest()

def build():
    missing = json.loads(Path("/tmp/dg-loot/missing.json").read_text())
    ko = json.loads(Path("/tmp/dg-loot/items-ko.json").read_text())
    rows, ddc_sha = ddc_rows("/tmp/dg-loot/ddc/weapon-perks.html")
    perks, weapons = {}, []
    for pid, name, dmg, mech, policy in PERKS:
        m = missing[name]
        h = m["perkHash"]
        dp = ko[str(h)]["displayProperties"]
        row = rows[name]
        perks[pid] = dict(hash=h, name=name, koName=dp["name"], koDescription=dp["description"],
                          description=m["description"], damage=dmg, mechanics=mech,
                          source=dict(authority="DDC Weapon Perks (PvE base, non-enhanced)", url=DDC_URL,
                                      row=row["row"], text=row["text"], htmlSha256=ddc_sha),
                          localPolicy=policy)
        for r in m["rolls"]:
            weapons.append(dict(perk=pid, id=r["id"], hash=r["hash"], socket=r["socket"],
                                perkHash=r["perkHash"], plugSetHash=r["plugSetHash"]))
    return dict(stage="W321", manifestVersion=VERSION, perks=perks, weapons=weapons)

def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--verify", action="store_true"); a = ap.parse_args()
    text = json.dumps(build(), ensure_ascii=False, indent=2) + "\n"
    if a.verify:
        ok = OUT.exists() and OUT.read_text(encoding="utf-8") == text
        print("OK" if ok else "MISMATCH"); sys.exit(0 if ok else 1)
    OUT.write_text(text, encoding="utf-8"); print(OUT)

if __name__ == "__main__":
    main()
