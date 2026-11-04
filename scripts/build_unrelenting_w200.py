#!/usr/bin/env python3
"""Deterministically generate W200 Unrelenting; --verify is read-only."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
NAME, SLUG, BASE, ENHANCED, ROW = "Unrelenting", "unrelenting", 3108830275, 855168139, 241
EXPECTED = [{'id': 'cold_denial', 'hash': 1216130969, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 720537379}, {'id': 'aishas_embrace', 'hash': 2638190703, 'socket': 3, 'perkHash': 3108830275, 'plugSetHash': 7997267}, {'id': 'farewell', 'hash': 541188001, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 3819615926}, {'id': 'high_albedo', 'hash': 1197486957, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 718633408}, {'id': 'biting_winds', 'hash': 1621657423, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 2763203653}, {'id': 'whispering_slab', 'hash': 211938782, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 967526625}, {'id': 'hollow_words', 'hash': 607191995, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 1485010760}, {'id': 'coriolis_force', 'hash': 3512349612, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 753624012}, {'id': 'deafening_whisper', 'hash': 981718087, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 3588287812}, {'id': 'canis_major', 'hash': 2066434718, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 2791121719}, {'id': 'dimensional_hypotrochoid', 'hash': 1311684613, 'socket': 3, 'perkHash': 3108830275, 'plugSetHash': 3235863202}, {'id': 'code_duello', 'hash': 2496242052, 'socket': 4, 'perkHash': 3108830275, 'plugSetHash': 147528717}, {'id': 'goldtusk', 'hash': 3371413057, 'socket': 3, 'perkHash': 3108830275, 'plugSetHash': 1162279549}]
MECHANICS = {'id': 'unrelenting', 'hash': 3108830275, 'windowTicks': 100, 'rankAndFileProgress': 34, 'powerfulProgress': 100, 'guardianProgress': 67, 'healHP': 65, 'localHealMaxHealthFraction': 0.325, 'destinyRegenerationRate': 'unknown', 'localRegenerationMaxHealthPerTick': 0.01}
DDC_TEXT = ['100% Counter Progress', 'within 5 seconds', 'Rank-And-File = 34%', 'Elites/Minibosses/Bosses = 100%', 'Guardians = 67%', 'Begins Health Regeneration and restores 65']
PINS = {'/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', '/private/tmp/destiny-w190/ddc-perks.html': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e'}
NOTE = "# W200 Unrelenting\n\nBase Trait 3108830275 only; Enhanced Trait 855168139 excluded. No default selection.\nDDC Weapon Perks row 241: weapon final blows within five seconds of each other add\n34% rank-and-file, 100% elites/minibosses/bosses, 67% Guardians. Reaching 100 resets\nprogress, restores 65 HP and begins Health Regeneration. Enhanced 70 HP excluded.\nThe raw HTML row and full official base definition, manifest/input SHA256 pins,\n65-entry catalog scan and 13 exact real currentlyCanRoll randomized socket proofs\nare retained in source.json. Regenerate with scripts/build_unrelenting_w200.py;\n--verify checks without writes. Source HTML SHA256:\n8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.\n\nThe user's saved DDC perk row/table supplies no defensible regeneration rate.\nDestiny regeneration rate stays UNKNOWN. Explicit local Minecraft mapping:\n65/200 * maxHealth instant healing (.325; 6.5 at native 20 maximum health), then\n1% maxHealth each server tick (20%/second). No separate shield, absorption grant,\nvanilla potion, potion removal, duration timer or invented five-second expiry.\nRegeneration ends at full HP, positive actual damage or source/owner invalidation.\nNormal original-source stow retains paid in-flight authority and regeneration,\nmatching WeaponEnergyPerks/AssassinsBlade ownership policy; no transfer to a copy.\n\nLocal target mapping follows explicit product tags, never HP/name heuristics:\nPlayer -> Guardian; WitherBoss/EnderDragon or Mob with destiny_boss or\ndestiny_vehicle -> powerful; other Mob -> rank-and-file.\nArmor stands/non-Mob decorative entities excluded. Product PvP filtering remains\nin the actual caller; this helper does not authorize otherwise forbidden PvP.\n\nIntegration (shared files owned by master):\n- Register UnrelentingProfile.ID/HASH/rolls with WeaponPerks; exact 13 tuples only.\n- WeaponUnrelenting.capture(p) AFTER paid ranged/charged/projectile/sword emission,\n  BEFORE own damage. Carry SAME Token through direct/payload/cleave callbacks.\n- killed(p,token,target) ONLY after positive actual HP/absorption loss and an\n  attributable eligible enemy final blow. Never ability/ambient/dry-fire/glaive melee.\n- update(p) once per server tick, even with source stowed. active(p) is a pure\n  own-regeneration HUD observer; does not bind, heal or inspect vanilla potions.\n- damaged(p,actualLoss) AFTER actual positive HP/absorption loss, never attempts.\n- changed(p,stack)/edited(stack) revoke source epochs and regeneration immediately;\n  ordinary held-slot switch MUST NOT call changed. cleanup(p)/clear() on lifecycle.\n- Register UnrelentingW200GameTests in existing GameTest entrypoint.\n"

def require(ok, detail):
    if not ok:
        raise ValueError(detail)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()

def plain(raw):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())

def build(root):
    data, inputs = {}, {}
    for name, pin in PINS.items():
        raw = (root / name).read_bytes()
        require(digest(raw) == pin, "Pinned input drift: " + name)
        inputs[name] = dict(sha256=pin, bytes=len(raw))
        data[name] = json.loads(raw) if name.endswith(".json") else raw.decode()
    inventory = data["/tmp/destiny-weapons-w30/bungie-items.json"]
    pools = data["/tmp/destiny-weapons-w60/bungie-plugsets.json"]
    manifest = data["/tmp/destiny-weapons-w60/manifest.json"]["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    perk = inventory[str(BASE)]
    require(perk["hash"] == BASE and perk["displayProperties"]["name"] == NAME
            and perk["itemTypeDisplayName"] == "Trait" and perk["itemType"] == 19
            and perk["plug"]["isDummyPlug"] is False and not perk.get("redacted")
            and not perk.get("blacklisted"), "exact usable base Trait")
    require(inventory[str(ENHANCED)]["itemTypeDisplayName"] == "Enhanced Trait", "enhanced exclusion")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(cell) == NAME for cell in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1 and f'id="1662574278R{ROW-1}"' in rows[0], "unique exact DDC td name/row")
    raw_row = rows[0]
    description = plain(re.findall(r"<td\b[^>]*>(.*?)</td>", raw_row, re.S)[-1])
    require(all(value in description for value in DDC_TEXT), "base DDC mechanics")
    require("#ffd966" in raw_row, "retain yellow enhanced distinction")
    stats = list(data[PREFIX + "w40-characteristics.json"])
    catalog = list(data[PREFIX + "w30.json"])
    for name in ("w83-exotics.json", "w84-exotics.json"):
        stats.extend(e["characteristics"] for e in data[PREFIX + name])
        catalog.extend(e["catalog"] for e in data[PREFIX + name])
    require(len(stats) == len(catalog) == len({w["id"] for w in stats}) == 65, "canonical catalog65")
    require({w["id"] for w in catalog} == {w["id"] for w in stats}, "catalog/stats identity")
    found, proofs, scan = [], [], []
    for weapon in stats:
        item = inventory[str(weapon["bungieHash"])]
        sockets = item["sockets"]
        categories = [c for c in sockets["socketCategories"] if c["socketCategoryHash"] == 4241085061]
        matches = []
        for index in sorted({i for c in categories for i in c["socketIndexes"]}):
            socket = sockets["socketEntries"][index]
            ph = socket.get("randomizedPlugSetHash")
            pool = pools.get(str(ph), {})
            if pool.get("isFakePlugSet") is not False:
                continue
            for plug in pool.get("reusablePlugItems", []):
                definition = inventory.get(str(plug["plugItemHash"]), {})
                if (plug.get("currentlyCanRoll") is not True
                    or definition.get("itemTypeDisplayName") != "Trait" or plug["plugItemHash"] != BASE):
                    continue
                require(not weapon["exotic"] and item["inventory"]["tierType"] == 5, "legendary real pool")
                roll = dict(id=weapon["id"], hash=weapon["bungieHash"], socket=index,
                            perkHash=BASE, plugSetHash=ph)
                found.append(roll)
                matches.append(roll)
                proofs.append(dict(roll=roll, socketCategories=categories, socketEntry=socket,
                                   plugSet=pool, matchingPlug=plug))
        scan.append(dict(id=weapon["id"], hash=weapon["bungieHash"], exotic=weapon["exotic"], matches=matches))
    require(found == EXPECTED, "exhaustive exact canonical pool")
    resource = dict(stage="W200", perk=MECHANICS, weapons=found)
    resource_raw = encode(resource)
    source = dict(stage="W200", checked="2026-10-27", manifestVersion=VERSION, sourcePins=inputs,
                  generatorSHA256=digest(Path(__file__).read_bytes()), resourceSHA256=digest(resource_raw),
                  manifestComponents={k: manifest["jsonWorldComponentContentPaths"]["en"][k] for k in
                                      ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  perkDefinition=perk, enhancedExcludedHash=ENHANCED,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                           tab="Weapon Perks", row=ROW, name=NAME, rawHTML=raw_row, text=description),
                  catalogScan=scan, socketProofs=proofs)
    return {PREFIX + "w200-" + SLUG + ".json": resource_raw,
            "art/weapons/w200/" + SLUG + "/source.json": encode(source),
            "art/weapons/w200/" + SLUG + "/SOURCE.md": NOTE.encode()}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()
    for name, raw in build(args.root.resolve()).items():
        path = args.root / name
        if args.verify:
            require(path.read_bytes() == raw, "Generated output drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)

if __name__ == "__main__":
    main()
