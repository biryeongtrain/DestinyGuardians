#!/usr/bin/env python3
"""Pinned offline W200 original Pulse Monitor. --verify compares bytes without writes."""
import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
ART = "art/weapons/w200/pulse-monitor/"
BASE = 972757866
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PINS = {'/tmp/destiny-weapons-w30/bungie-items.json': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c', '/tmp/destiny-weapons-w60/bungie-plugsets.json': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959', '/tmp/destiny-weapons-w60/manifest.json': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce', '/private/tmp/destiny-w190/ddc-perks.html': '8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'src/main/resources/destiny/weapons/w83-exotics.json': 'bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56', 'src/main/resources/destiny/weapons/w84-exotics.json': '481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e', 'art/weapons/w43/extraction.json': 'a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5', 'art/weapons/w46/weapon_formulas.json': 'fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d', 'src/main/resources/destiny/weapons/w58-handling.json': '4de7d346a93c822784fafa69b62ac66148d51cc11cf2da6706367682b414d3f1', 'src/main/resources/destiny/weapons/w44-aim.json': '0d0a38469c28a74c1a77489d346184eccef347a604c0c0c455d1c7c2e1a80fc8', 'src/main/resources/destiny/weapons/w68-snapshot.json': '7e824633be32953e6c75d3d856ce765223fbb1cbcc3b01affca3d83eb8fcb738'}
EXPECTED = [{'id': 'seventh_seraph_officer_revolver', 'hash': 3037520408, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 903350103}, {'id': 'cold_denial', 'hash': 1216130969, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 330841869}, {'id': 'dust_rock_blues', 'hash': 636912560, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 3511609070}, {'id': 'first_in_last_out', 'hash': 3616586446, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 267999755}, {'id': 'parcel_of_stardust_fell_to_earth', 'hash': 2217366863, 'socket': 4, 'perkHash': 972757866, 'plugSetHash': 3424940310}, {'id': 'dream_breaker', 'hash': 2931957300, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 3785896921}, {'id': 'coriolis_force', 'hash': 3512349612, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 2568674372}, {'id': 'edge_transit', 'hash': 218335759, 'socket': 3, 'perkHash': 972757866, 'plugSetHash': 447678063}]

COMPANIONS = {4071163871: "threat_detector", 957782887: "snapshot", 706527188: "quickdraw",
              1600092898: "backup_plan", 4104185692: "frenzy"}
NOTE = """# W200 original Pulse Monitor

DDC Weapon Perks row171, checked 2026-10-27: base threshold 30% Shield HP; fills
weapon; +50 Handling; .95 ready/stow duration; active while low and 1 second after
recovery; activates and persists while stowed. Yellow 35%? is enhanced uncertainty,
not a base threshold. No PvE/PvP split stated. Official manifest version
245114.26.10.13.2000-1-bnet.66137 supplies exact definition/socket/pool proof.

This port has native Minecraft HP only. Explicit local conversion is native
health/maxHealth <= .30, ignoring absorption; no separate Destiny shield claim.
20 TPS maps one second to 20 ticks. One refill decision per low-health episode,
including first bind already low; repeat damage, ticks and readers never refill
again until observed recovery and reentry. This is local policy because repeat
low-damage behavior is ambiguous. Full magazine/empty reserves consume that episode.

Only original canonical base hash972757866 is implemented: eight exact current
nonfake randomized tuples. Reissued same-name base205890336 is excluded, even on
shared weapon pools; enhanced1685378950 and320071920 are excluded. No default select.

Refill uses WeaponItems.magazine/save and existing WeaponMagazine.reload semantics:
Special/Heavy consume finite reserves/legacy overflow; Primary retains its existing
infinite-reserve supply. No finite-ammo generation, manual-reload
callbacks, Honed decomposition, cadence reset or changes to foreign components.
Only actual positive transfers cancel pending work via cancelForTraitRefill.

All timing/HUD queries are pure and source object/owner/level/data/runtime/class/
loadout/slot/count/entry/selected tuple checked. Stowing does not clear episodes.
changed is for real identity/equipment invalidation, not ordinary hotbar stow.
Main-thread update and actual positive native HP-loss dispatch are Master hooks.

Resource includes raw historical W46 ready/stow/ADS curves and pinned handling
baselines; current official stats verify base handling. Distinct-socket stat pairs:
Parcel Threat Detector OR Snapshot; Dust Rock Snapshot; Dream Breaker Quickdraw OR
Backup Plan OR Frenzy; Edge Transit Quickdraw. Same-socket alternatives are recorded as excluded. Multiply
Pulse .95 once with TD .9/.81 or QD ready-only .95 as actually active; BP has no
ready scalar. BP/Frenzy +100 and QD h100 cap at100. Sum raw bonuses before one stat
clamp; solve raw seconds, multiply once, ceil once. Snapshot affects ADS entry only.
ADS exit uses handling without Snapshot. Historical stow-at100 floor follows the
existing product curve policy. No numeric mirror tests are added.

Master owns shared registry/lifecycle/damage/handling/ADS/HUD and GameTest
registration. Owned GameTests are server automation, not native Vision evidence.
See pulse-report.md for checks actually run and remaining integration validation.
"""

def require(ok, detail):
    if not ok:
        raise ValueError(detail)

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def encode(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n").encode()

def plain(raw):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", raw)).split())

def generate(root):
    data, sources = {}, {}
    for name, pin in PINS.items():
        raw = (root / name).read_bytes()
        require(digest(raw) == pin, "pinned input drift: " + name)
        sources[name] = dict(sha256=pin, bytes=len(raw))
        data[name] = json.loads(raw) if name.endswith(".json") else raw.decode()
    inv = data["/tmp/destiny-weapons-w30/bungie-items.json"]
    pools = data["/tmp/destiny-weapons-w60/bungie-plugsets.json"]
    manifest = data["/tmp/destiny-weapons-w60/manifest.json"]["Response"]
    require(manifest["version"] == VERSION, "manifest version")
    definition = inv[str(BASE)]
    require(definition["hash"] == BASE and definition["displayProperties"]["name"] == "Pulse Monitor"
            and definition["itemTypeDisplayName"] == "Trait" and definition["itemType"] == 19
            and definition["plug"]["isDummyPlug"] is False and not definition.get("redacted")
            and not definition.get("blacklisted"), "original canonical non-dummy base trait")
    rows = [row for row in re.findall(r"<tr\b[^>]*>.*?</tr>", data["/private/tmp/destiny-w190/ddc-perks.html"], re.S)
            if any(plain(c) == "Pulse Monitor" for c in re.findall(r"<td\b[^>]*>(.*?)</td>", row, re.S))]
    require(len(rows) == 1 and 'id="1662574278R170"' in rows[0], "DDC row171 exact td")
    raw_row = rows[0]
    base_text = plain(re.sub(r'<span\b[^>]*style="[^"]*color:#ffd966;[^"]*"[^>]*>.*?</span>', '', raw_row, flags=re.S))
    require(all(v in base_text for v in ("30%", "Shield HP", "Refills Weapon", "+50 Handling",
        "0.95x Ready/Stow", "1 second", "activated while stowed", "persists through stow")), "base DDC text")
    stats = list(data[PREFIX + "w40-characteristics.json"])
    catalog = list(data[PREFIX + "w30.json"])
    for name in ("w83-exotics.json", "w84-exotics.json"):
        stats += [w["characteristics"] for w in data[PREFIX + name]]
        catalog += [w["catalog"] for w in data[PREFIX + name]]
    require(len(stats) == len(catalog) == len({w["id"] for w in stats}) == 65, "catalog65")
    found, proof, audit, pairs, companion_audit, reissued = [], [], [], [], [], []
    supported = {w["id"] for w in EXPECTED}
    for w in stats:
        item = inv[str(w["bungieHash"])]
        matches = []
        for cat in item.get("sockets", {}).get("socketCategories", []):
            if cat["socketCategoryHash"] != 4241085061:
                continue
            for index in cat["socketIndexes"]:
                socket = item["sockets"]["socketEntries"][index]
                ph = socket.get("randomizedPlugSetHash")
                pool = pools.get(str(ph), {})
                if pool.get("isFakePlugSet") is not False:
                    continue
                require(pool["hash"] == ph, "official pool hash")
                for plug in pool.get("reusablePlugItems", []):
                    h = plug["plugItemHash"]
                    d = inv.get(str(h), {})
                    if (plug.get("currentlyCanRoll") is not True or d.get("itemTypeDisplayName") != "Trait"
                            or d.get("plug", {}).get("isDummyPlug") is not False
                            or d.get("redacted") or d.get("blacklisted")):
                        continue
                    roll = dict(id=w["id"], hash=w["bungieHash"], socket=index, perkHash=h, plugSetHash=ph)
                    if h == 205890336:
                        reissued.append(roll)
                    if h == BASE:
                        require(not w["exotic"] and item["inventory"]["tierType"] == 5, "real legendary roll")
                        found.append(roll); matches.append(roll)
                        proof.append(dict(roll=roll, category=cat, socketEntry=socket, plugSet=pool, matchingPlug=plug))
                    if w["id"] in supported and h in COMPANIONS:
                        source = next(s for s in EXPECTED if s["id"] == w["id"])
                        allowed = source["socket"] != index
                        companion_audit.append(dict(perk=COMPANIONS[h], roll=roll, allowed=allowed))
                        if allowed:
                            pairs.append(dict(id=w["id"], perk=COMPANIONS[h], roll=roll))
        audit.append(dict(id=w["id"], hash=w["bungieHash"], matches=matches))
    require(found == EXPECTED, "exact exhaustive8 tuples")
    require({(p["id"], p["perk"]) for p in pairs} == {
        ("parcel_of_stardust_fell_to_earth", "threat_detector"), ("parcel_of_stardust_fell_to_earth", "snapshot"),
        ("dust_rock_blues", "snapshot"), ("dream_breaker", "quickdraw"),
        ("dream_breaker", "backup_plan"), ("dream_breaker", "frenzy"), ("edge_transit", "quickdraw")}, "exact7 handling/ADS companions")
    mapping = {w["id"]: w for w in data["art/weapons/w43/extraction.json"]["entries"]}
    formulas = data["art/weapons/w46/weapon_formulas.json"]
    baseline = {w["id"]: w["profile"] for w in data[PREFIX + "w58-handling.json"]}
    aim = {w["id"]: w["profile"] for w in data[PREFIX + "w44-aim.json"]}
    snapshots = data[PREFIX + "w68-snapshot.json"]
    curves, curve_proof = [], []
    for roll in found:
        w = next(w for w in stats if w["id"] == roll["id"])
        item = inv[str(roll["hash"])]
        m = mapping[w["id"]]
        raw = formulas[m["family"]]["cat"][m["category"]]["handling"]
        snap = next((p for p in pairs if p["id"] == w["id"] and p["perk"] == "snapshot"), None)
        c = dict(id=w["id"], baseHandlingStat=w["stats"]["943549884"],
                 snapshotScalar=snapshots["specialScalar"] if snap else None)
        require(c["baseHandlingStat"] == item["stats"]["stats"]["943549884"]["value"], "official handling")
        if snap:
            require(snap["roll"] in snapshots["rolls"] and snapshots["specialScalar"] == .8, "special Snapshot proof")
        for key in ("ready", "stow", "ads"):
            c[key] = {k: raw[key].get(k, 0.0) for k in ("evpp", "vpp", "offset")}
        def ticks(key):
            h = c["baseHandlingStat"]
            return math.ceil((c[key]["evpp"]*h*h + c[key]["vpp"]*h + c[key]["offset"])*20)
        require(ticks("ready") == baseline[w["id"]]["readyTicks"]
                and ticks("stow") == baseline[w["id"]]["stowTicks"]
                and max(2, min(20, ticks("ads"))) == aim[w["id"]]["transitionTicks"], "historical baseline")
        curves.append(c)
        curve_proof.append(dict(id=w["id"], mapping=m, handling=raw, baseline=baseline[w["id"]], ads=aim[w["id"]]))
    resource = dict(stage="W200", perk=dict(id="pulse_monitor", hash=BASE, healthThreshold=.30,
        handlingBonus=50, handlingScalar=.95, lingerTicks=20), weapons=found, curves=curves, coSelections=pairs)
    source = dict(stage="W200", checked="2026-10-27", manifestVersion=VERSION, sourcePins=sources,
        generatorSHA256=digest(Path(__file__).read_bytes()), resourceSHA256=digest(encode(resource)),
        manifestComponents={k: manifest["jsonWorldComponentContentPaths"]["en"][k] for k in
                            ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
        baseDefinition=definition, excludedDefinitions=[inv[str(h)] for h in (205890336,1685378950,320071920)],
        excludedReissuedRolls=reissued, catalogScan=audit, socketProofs=proof, companionAudit=companion_audit,
        coSelections=pairs, curveProofs=curve_proof,
        ddc=dict(row=171, tab="Weapon Perks", rawHTML=raw_row, baseText=base_text,
            url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278"),
        policies=dict(nativeHealthConversion="health/maxHealth<=.30; absorption excluded; no separate shields",
            episode="one decision per observed low episode; initial low bind allowed; repeat low damage does not refill",
            reserves="existing Primary infiniteReserve semantics; Special/Heavy conserve finite reserve/legacy overflow",
            timing="20TPS local mapping; 20 ticks from first observed recovery; readers never extend",
            integration="Master shared registry/runtime/lifecycle/damage/handling/ADS/HUD/GameTest registration"))
    return {PREFIX + "w200-pulse-monitor.json": encode(resource), ART + "source.json": encode(source), ART + "SOURCE.md": NOTE.encode()}

def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--verify", action="store_true")
    args = p.parse_args()
    for name, raw in generate(args.root.resolve()).items():
        path = args.root / name
        if args.verify:
            require(path.read_bytes() == raw, "generated drift: " + name)
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
        print(("verified " if args.verify else "wrote ") + name)

if __name__ == "__main__":
    main()
