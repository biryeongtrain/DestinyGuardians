#!/usr/bin/env python3
"""Deterministically generate W194 base Killing Tally; --verify is read-only."""
NAME, SLUG, BASE, ENHANCED, ROW = "Killing Tally", "killing-tally", 557221067, 2896748467, 134
EXPECTED = [dict(id="fixed_odds", hash=2194955522, socket=4, perkHash=BASE, plugSetHash=1686775256)]
DDC_TEXT = ("up to 3 stacks", "Stacks are removed on stow or reload.", "10% | 20% | 30%", "5% | 10% | 15%")
MECHANICS = dict(id="killing_tally", hash=BASE, maxStacks=3,
                 pveMultipliers=[1, 1.1, 1.2, 1.3], pvpMultipliers=[1, 1.05, 1.1, 1.15],
                 clearsOnStow=True, clearsOnReload=True)
NOTE = "# W194 Killing Tally\n\nBase Trait 557221067 only. DDC Weapon Perks row 134, exact td name Killing Tally.\nPinned HTML SHA256: 8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437.\nsource.json retains the complete rawHTML row, including yellow enhanced-only +10 Magazine.\nBase: actual weapon final blows grant up to three stacks; PvE +10/20/30%, PvP +5/10/15%.\nStow or reload removes stacks. No duration or invented remaining timer. Enhanced\n2896748467 and older Trait 2782457288 are excluded. No default selected trait.\n\nAll 65 canonical entries scanned against Bungie manifest 245114.26.10.13.2000-1-bnet.66137:\nonly Fixed Odds 2194955522 / socket4 / real randomized plugset1686775256,\ncurrentlyCanRoll=true and exact itemTypeDisplayName Trait. Full scan, pool proofs,\nofficial definition and input hashes are in source.json.\n\n## Reset research and local policy\n\nDDC establishes stow/reload reset, without specifying refill mechanisms or reset timing.\nFirst-hand community tests report Marksman Dodge clears Killing Tally, while\nDemolitionist refreshes the magazine without resetting it:\nhttps://www.reddit.com/r/DestinyTheGame/comments/1q8bcz1/a_very_brief_breakdown_of_all_the_ways_to_reload/\nAdditional first-hand discussion:\nhttps://www.reddit.com/r/DestinyTheGame/comments/186qfne/\nThese are community observations, not an exhaustive official current refill matrix.\nBungie's generic perk description does not settle these exceptions. No Destiny\nruntime measurement was performed here.\n\nLocal explicit policy: accepted manual reload resets immediately at acceptance, even\nif later cancelled. Positive actual Marksman ammo refill resets; a no-credit Dodge\ndoes not call the hook. Demolitionist, Subsistence, Overflow and other reserve-only\nmagazine credits do not call reloadStarted. Holster itself has no reload proc;\nthe earlier stow already cleared stacks. Fixed Odds cannot co-select Demolitionist,\nHolster or Overflow in its actual pinned socket pool. Do not broaden its rolls.\n\n## Settled integration API\n\n- Register KillingTallyProfile.ID/HASH/rolls in master WeaponPerks; no default/enhanced.\n- capture(p) returns WeaponKillingTally.Token AFTER successful ammo payment and BEFORE\n  any own direct/splash damage/final-blow callback. Share ONE token per emission.\n- multiplier(p, token, target) is a pure immutable pre-kill stack snapshot:\n  ServerPlayer targets use PvP, other LivingEntity targets PvE. Master applies once\n  in DamageTraits, never also in the firing profile. Ordinary stow/reload clears\n  live stacks but paid scalars survive; lifecycle/source edits revoke the token.\n- killed(p, token, target) only AFTER positive actual HP/absorption loss AND a confirmed\n  attributable eligible enemy final blow. No ability/melee/unpaid callbacks.\n  Live stacks cap at three; the killing emission retains its pre-own-kill scalar.\n- stacks(p) is a pure held-source probe, no binding/update/attachment creation.\n- reloadStarted(p, stack) at accepted manual reload, and positive Marksman credit only.\n- update(p) in server tick; stowing(p, outgoing) at accepted selection BEFORE vanilla\n  changes slots, including same-tick away/back. Delayed pre-reset final blows consume\n  dedup credit but cannot re-bank live stacks after reset (explicit local policy).\n- edited(stack) on every successful selection edit/clear including away/back;\n  changed(p, originalStack) for loss/replacement/move; cleanup(p) on death/disconnect,\n  respawn, dimension/class/super changes; clear() at shutdown. These revoke source epochs.\n  Ordinary stow must use stowing, not changed/cleanup. Old-player cleanup cannot\n  clear replacement-player state. Exact stack/count1, hotbar slot, loadout mode,\n  canonical entry/roll, owner object, level, GuardianData/runtime/class are revalidated.\n\nCorpse identity ledger is capped at256 per paid emission; at saturation it fails\nclosed without eviction. Caller owns actual-damage/enemy/final-blow attribution across\ndifferent emissions. Local bounds are not DDC values. No shared ammo mutation.\n\nRegenerate: rtk proxy python3 scripts/build_killing_tally_w194.py\nVerify: same command with --verify (byte-identical resource, source.json, SOURCE.md).\nFocused cycle tests cover event ordering, cap, dedup, pure probes, reset vs revocation,\nforeign epochs and rollback. No numeric mirror tests, fullgate, Vision or animation work.\nMaster owns registry, DamageTraits, lifecycle wiring and scoped server integration tests.\n"

def extra(root, data, stats, inventory, companions, resource, source):
    source["resetResearch"] = [
        dict(url="https://www.reddit.com/r/DestinyTheGame/comments/1q8bcz1/a_very_brief_breakdown_of_all_the_ways_to_reload/",
             retrieved="2026-10-27", authority="First-hand community test report, not developer documentation",
             observation="Reports Marksman Dodge removes KT; Demolitionist magazine refresh retains KT."),
        dict(url="https://www.reddit.com/r/DestinyTheGame/comments/186qfne/",
             retrieved="2026-10-27", authority="Community player discussion",
             observation="Discussion corroborates Demo refill does not count as a KT-reset reload.")]
    source["localPolicies"] = dict(reset="Accepted manual reload immediately, or positive Marksman credit. No reserve-only refill reset; holster stow already clears.",
        delayed="Paid scalar survives live reset; pre-reset kills cannot re-bank; source/lifecycle edits revoke.",
        dedup="256 corpse identities per emission, no eviction. Master verifies actual damage and final-blow ownership.")

import argparse
import hashlib
import html
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PREFIX = "src/main/resources/destiny/weapons/"
VERSION = "245114.26.10.13.2000-1-bnet.66137"
PINS = {
    "art/weapons/w46/stat_calc.rs": "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
    "/tmp/destiny-weapons-w30/bungie-items.json": "b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c",
    "/tmp/destiny-weapons-w60/bungie-plugsets.json": "8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959",
    "/tmp/destiny-weapons-w60/manifest.json": "bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce",
    "/private/tmp/destiny-w190/ddc-perks.html": "8b8109ecd80601965edcfc9559a784bd17cfc0e2e84419385ab68788fd376437",
    "src/main/resources/destiny/weapons/w30.json": "2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a",
    "src/main/resources/destiny/weapons/w40-characteristics.json": "5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1",
    "src/main/resources/destiny/weapons/w46-timing.json": "e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07",
    "src/main/resources/destiny/weapons/w83-exotics.json": "bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56",
    "src/main/resources/destiny/weapons/w84-exotics.json": "481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e",
    "src/main/resources/destiny/weapons/w108-feeding-frenzy.json": "1ffbff575f0a29adc5a749d581f31c2f6dd67dfea20cf4a3484b6d2c1c522ce8",
    "src/main/resources/destiny/weapons/w169-rapid-hit.json": "3406dea192367d0f64406d473ab6996b5b6085dfaeb279c571209a84ec6dd8cd",
    "src/main/resources/destiny/weapons/w178-threat-detector.json": "8e593a1698dff17bb8260e40b9b1e3befe3efaca9fd54d990e89fdddf62cb4e4",
    "src/main/resources/destiny/weapons/w183-surplus.json": "3a54d901e618b2472c8a2beff905ecb21d9aa0316628a0416adaf91242fccef6",
    "src/main/resources/destiny/weapons/w193-overflow.json": "8cd3a8a034557bc79cd83ec801edf105eff66870900689fdd09edfce3dd17cb6",
    "src/main/resources/destiny/weapons/w193-ambitious-assassin.json": "e6a43a3555a75e27a27db1b816da61c56018d489738e3a716d65bfd7bfff1810",
    "src/main/resources/destiny/weapons/w193-clown-cartridge.json": "067b387162883830199e37519a3bc40a7616aed9820f170f7ed4058ef1ed8698",
    "src/main/resources/destiny/weapons/w193-adagio.json": "09608e3e38518dcfb8d01ce3828c16b3fc4e61a8b387560a7262f7ebefd26e31",
    "src/main/resources/destiny/weapons/w193-impulse-amplifier.json": "bcd0afc1496850eddf1fb525f311ba7c8bb15476eee378396267f71a23838584",
    "art/weapons/w43/extraction.json": "a133082c322a07e81837d0409caf09596dfad4fd9889904d1bdae7acd471d9d5",
    "art/weapons/w46/weapon_formulas.json": "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
    "src/main/java/kim/biryeong/destiny/weapon/AdagioProfile.java": "2d281ec595b74e66126f701577f2d7c44e06a18396eac26e4b6e179de317a4c5",
    "src/main/java/kim/biryeong/destiny/weapon/AdrenalineJunkieProfile.java": "5afbc8a14feb77e87a9434fadccff508c58b23c3d3b3354b4754de8f08d750e1",
    "src/main/java/kim/biryeong/destiny/weapon/AmbitiousAssassinProfile.java": "1aaf5d13cf25e39c8c168b3acde566c89c2c3bf4881a02f1393fabf0a1adbe10",
    "src/main/java/kim/biryeong/destiny/weapon/ArcherTempoProfile.java": "1b0220d3060432d8925b855469720d383e7882f7bf6a9e183661c4e171ad5cb3",
    "src/main/java/kim/biryeong/destiny/weapon/BackupPlanProfile.java": "14bc91bcee743235fab84f1c3b9bcf28fa335e744fca981f7d97b36d7ed59432",
    "src/main/java/kim/biryeong/destiny/weapon/ClownCartridgeProfile.java": "d256730410dcc08d778512a674cec46344556d264f2417b1a3f65edf3138b286",
    "src/main/java/kim/biryeong/destiny/weapon/CompulsiveReloaderProfile.java": "e529960181b52df04a8e1f42bec632aa7cbc5c112138170976e8cd2d2e7ebb1c",
    "src/main/java/kim/biryeong/destiny/weapon/DemolitionistProfile.java": "0a71d0f67ce0786038f37ec0c2c661677680c7e53edf184b4eed6c2c50414860",
    "src/main/java/kim/biryeong/destiny/weapon/DragonflyProfile.java": "b1b7f33ac5a4d1f0a28acccbd9628bb3ad4c08c7910658737dffe295cfdb32f1",
    "src/main/java/kim/biryeong/destiny/weapon/ElementalCapacitorProfile.java": "03d85d5d3d784eafe9d845abdd7c355338729d6893c06629654e38510bb95a0b",
    "src/main/java/kim/biryeong/destiny/weapon/EncoreProfile.java": "5a200b29748bea2522e426e665c0528b0fc8bab529facb3bf0a8aae23d3a6bb1",
    "src/main/java/kim/biryeong/destiny/weapon/EnsembleProfile.java": "9d47ee9a2717b2ae2535c53bfe9b6f6919c74a504aab316551989570bec15373",
    "src/main/java/kim/biryeong/destiny/weapon/FeedingFrenzyProfile.java": "80ca49c795261016527886616c070ab29139e41f28480325ac441af2ca2ffd93",
    "src/main/java/kim/biryeong/destiny/weapon/FiringLineProfile.java": "1aadf895363c737f1f20695916d19b34b80bb9a7accf8655f07a34c2619a80b1",
    "src/main/java/kim/biryeong/destiny/weapon/FirmlyPlantedProfile.java": "51ea9e899be86c1d5ce2ade8e884a85d6877a1e1d8ab0a2adb58f7c27919c6dc",
    "src/main/java/kim/biryeong/destiny/weapon/FocusedFuryProfile.java": "6ecef406531ea692d21b150bba5ae7778107ca27d638d31fc5d0f71ad6de82fa",
    "src/main/java/kim/biryeong/destiny/weapon/FrenzyProfile.java": "8fb757b26d5b7f67d8ebd3998374b20257e5b299a24c65e0c9463466c4605d7d",
    "src/main/java/kim/biryeong/destiny/weapon/FullAutoProfile.java": "35b83f0c5760d2817dab54850107cfbe9694a54e360162274885c5642db535ed",
    "src/main/java/kim/biryeong/destiny/weapon/GraveRobberProfile.java": "bc3eecc78812fefe28c8d9ffe80d5e540024d83f08f4e3c5802acef0606e9c04",
    "src/main/java/kim/biryeong/destiny/weapon/HeatingUpProfile.java": "fa16848af932c8ea69aa4417308d4c7489edb99b6a7623febfce79bd9608eb1f",
    "src/main/java/kim/biryeong/destiny/weapon/HighImpactReservesProfile.java": "1cefeb043a6360b0f6140a1578f0a2810e518609730dd11468458176558e15d3",
    "src/main/java/kim/biryeong/destiny/weapon/ImpulseAmplifierProfile.java": "6066018664e3ff8948836420a775a9d66e1e71e5e17a5b730bd682b9886a9d43",
    "src/main/java/kim/biryeong/destiny/weapon/IronReachProfile.java": "808ae9fd573911f9d3d9c00c7d73b62d7228ffb65380c2e0c931c5ee06a5b4db",
    "src/main/java/kim/biryeong/destiny/weapon/KillClipProfile.java": "b9348cb37e7976e8465589aadfdb0d59eb46119528eb6061e079c1a26673b0a3",
    "src/main/java/kim/biryeong/destiny/weapon/LeadFromGoldProfile.java": "0b6d91bb1add58a23adedb0a3e01ad9c55adc2157410c20fd2f1937a0e146875",
    "src/main/java/kim/biryeong/destiny/weapon/MultikillClipProfile.java": "985c7b1eb05ef0c58949185d7817972cb151d4f7d6356a6f9f72e7780b539671",
    "src/main/java/kim/biryeong/destiny/weapon/OneForAllProfile.java": "86e987676d79e8612bc4c0f845550743793f4349dfc09d6ebd49301d2b848a61",
    "src/main/java/kim/biryeong/destiny/weapon/OutlawProfile.java": "6974b20c2beed782c312153efab8fbe21683291f2248e37502a9f381bd5b1c13",
    "src/main/java/kim/biryeong/destiny/weapon/OverflowProfile.java": "365dbbcae847981f9197b27576735e0a76c05796397707f2b7560d8ca883a99c",
    "src/main/java/kim/biryeong/destiny/weapon/PayloadProfile.java": "40222146be465813aac723aa0f53fb738dbb508d6a6f19b4e27ff73f19f5a6f1",
    "src/main/java/kim/biryeong/destiny/weapon/PerpetualMotionProfile.java": "b1e705b9caced35e8cf52d0504a8231da72115377bc42a472e2b7124fbccc694",
    "src/main/java/kim/biryeong/destiny/weapon/PrecisionReturnProfile.java": "d1a62793f66928f5fce2fd566c6e1a0541f0bc937f19c404b7cfda35d4e4ce5e",
    "src/main/java/kim/biryeong/destiny/weapon/PugilistProfile.java": "c8e6fdbc931edd7823f37a36f9481719d28fe01763af7cbb338ff9c8247dc531",
    "src/main/java/kim/biryeong/destiny/weapon/QuickdrawProfile.java": "fa045cba27ab21920ddc1bab567a1f918f00afb00d6e3e6e750874df4f2aba35",
    "src/main/java/kim/biryeong/destiny/weapon/RampageProfile.java": "596d5fd6f3bc1f7323ef17daa1747eb46de75660fb0d00e742dbd231b0946078",
    "src/main/java/kim/biryeong/destiny/weapon/RangefinderProfile.java": "948112cab47d000c0f1a9fecf4414c04c506705ec2591e01cd1868d025774df0",
    "src/main/java/kim/biryeong/destiny/weapon/RapidHitProfile.java": "fff24015cb3a0f1fbf9c0a45d9bcf0b718478f4a35004596e68812ec49354758",
    "src/main/java/kim/biryeong/destiny/weapon/SnapshotAimProfile.java": "b24e7bebae14357af03696ba840baa33f2f835aad96c50e602a0eb3f5031e2dc",
    "src/main/java/kim/biryeong/destiny/weapon/StatsForAllProfile.java": "408cfa88745f35a8d2036a59c6ca921877245bb3ae13211c327c229b62c46abe",
    "src/main/java/kim/biryeong/destiny/weapon/SubsistenceProfile.java": "41637a37152beb773bb0862040d86dd3aeef21c116fb73cf0a59b6da33a38edb",
    "src/main/java/kim/biryeong/destiny/weapon/SurplusProfile.java": "9e05f52d8db2dade6cdaf69df93c8f927126376544e52a73765c62e302194865",
    "src/main/java/kim/biryeong/destiny/weapon/SurroundedProfile.java": "871c4ffa67fb7bb16d679064194ec9ae4d3f6b8910381634a0fdcb80e0440cb6",
    "src/main/java/kim/biryeong/destiny/weapon/SwashbucklerProfile.java": "243b2bfbe049b36aac2358bb3549dcc68e742328d987762ac502e6f8bd062fc0",
    "src/main/java/kim/biryeong/destiny/weapon/TapTheTriggerProfile.java": "1518feafc8b2db428108d98ade19c6059a89a96ef3b54b5640bfe6b871325551",
    "src/main/java/kim/biryeong/destiny/weapon/ThreatDetectorProfile.java": "d30ee96d464686063603193b2ecd0d62d85c5c2269a56eac7b7b7bea97e8b51d",
    "src/main/java/kim/biryeong/destiny/weapon/ThreshProfile.java": "06dc91a5cf2aa6aecbef85599f640403e117130f47052322955385236ad57fea",
    "src/main/java/kim/biryeong/destiny/weapon/TrackingProfile.java": "125bb22a77d140d2d8bfc8888a212e0387676602e244b4192612e54f25289b5a",
    "src/main/java/kim/biryeong/destiny/weapon/UnderPressureProfile.java": "cdd593b13ca6ba8f600cce33cfa30cb334642e6ad1e1ca03c159f358c7c2df8c",
    "src/main/java/kim/biryeong/destiny/weapon/VorpalProfile.java": "6a952c89805d424c0542902d7e7140f5e8a4125024d2e03a778be133b405a008",
    "src/main/java/kim/biryeong/destiny/weapon/WellRoundedProfile.java": "ab9f4cccb4079da601ae3121039c21c8fb1a337cd9e9e53bd0711142b5aaa824",
    "src/main/java/kim/biryeong/destiny/weapon/WellspringProfile.java": "ece5a4ed6451694ccedad477125dadd4f40e44884e87401461dcfa33649a2633",
    "src/main/java/kim/biryeong/destiny/weapon/ZenMomentProfile.java": "b718650a41170ab2ab57173c69bc9fa3862d8ece362a954d4a0408252c00cde0",
    "art/weapons/w46/rs_types.rs": "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90"
}
REVIEWED_SHARED_SNAPSHOT = {
    "src/main/java/kim/biryeong/destiny/weapon/WeaponPerks.java": "d1fee9f04f54a76907b3cc1792811a96c5526a1468a36b72373b58e46a8dc50e",
    "src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java": "8787147bf6161b33c960ee888e9208012a01c80751f786ecb3adebb65df34ea3"
}
RELOAD_HASHES = {
    1168162263: "outlaw", 2779035018: "feeding_frenzy", 247725512: "rapid_hit",
    4071163871: "threat_detector", 3436462433: "surplus", 4104185692: "frenzy",
    1428297954: "perpetual_motion", 1583705720: "stats_for_all",
    3511092054: "elemental_capacitor", 2621346526: "ensemble",
    671806388: "compulsive_reloader", 951095735: "impulse_amplifier",
    2869569095: "field_prep",
}


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
        path = root / name
        raw = path.read_bytes()
        require(digest(raw) == pin, "Pinned input drift: " + name)
        inputs[name] = dict(sha256=pin, bytes=len(raw))
        data[name] = json.loads(raw) if path.suffix == ".json" else raw.decode()
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
    found, proofs, scan, all_traits = [], [], [], []
    supported_ids = {r["id"] for r in EXPECTED}
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
                if plug.get("currentlyCanRoll") is not True or definition.get("itemTypeDisplayName") != "Trait":
                    continue
                roll = dict(id=weapon["id"], hash=weapon["bungieHash"], socket=index,
                            perkHash=plug["plugItemHash"], plugSetHash=ph)
                if weapon["id"] in supported_ids:
                    all_traits.append(dict(name=definition["displayProperties"]["name"], roll=roll))
                if plug["plugItemHash"] != BASE:
                    continue
                require(not weapon["exotic"] and item["inventory"]["tierType"] == 5, "legendary real pool")
                found.append(roll)
                matches.append(roll)
                proofs.append(dict(roll=roll, socketCategories=categories, socketEntry=socket,
                                   plugSet=pool, matchingPlug=plug))
        scan.append(dict(id=weapon["id"], hash=weapon["bungieHash"], exotic=weapon["exotic"], matches=matches))
    require(found == EXPECTED and all(r["socket"] == 4 for r in found), "exhaustive exact socket4 pool")

    # Every existing registry profile (54 IDs, including W193) is checked against every
    # actual base Trait on the supported weapons. No presumed cross-column compatibility.
    implemented = {"auto_loading_holster": 3300816228, "triple_tap": 3400784728, "fourth_times_the_charm": 1354429876, "full_auto_trigger_system": [4267945040, 2117683199]}
    for path, text in data.items():
        if not path.endswith("Profile.java"):
            continue
        id_match = re.search(r'public static final String ID\s*=\s*"([^"]+)"', text)
        hash_match = re.search(r'public static final long HASH\s*=\s*(\d+)L', text)
        if id_match and hash_match:
            implemented[id_match[1]] = int(hash_match[1])
    require(len(implemented) == 54, "reviewed WeaponPerks54 implementation inventory")
    implemented_audit = []
    for id_, hash_ in sorted(implemented.items()):
        hashes = hash_ if isinstance(hash_, list) else [hash_]
        legal = [r["roll"] for r in all_traits if r["roll"]["perkHash"] in hashes and r["roll"]["socket"] != 4]
        implemented_audit.append(dict(id=id_, hashes=hashes, colegalRolls=legal,
                                      reloadStatOrScalarProvider=any(h in RELOAD_HASHES for h in hashes)))
    reload_audit = [dict(**r, perk=RELOAD_HASHES[r["roll"]["perkHash"]],
                        distinctSocket=r["roll"]["socket"] != 4)
                    for r in all_traits if r["roll"]["perkHash"] in RELOAD_HASHES]
    companions = [dict(id=r["roll"]["id"], perk=r["perk"], roll=r["roll"])
                  for r in reload_audit if r["distinctSocket"]]
    source = dict(stage="W194", checked="2026-10-27", manifestVersion=VERSION, sourcePins=inputs,
                  reviewedSharedSnapshot=REVIEWED_SHARED_SNAPSHOT,
                  generatorSHA256=digest(Path(__file__).read_bytes()),
                  manifestComponents={k: manifest["jsonWorldComponentContentPaths"]["en"][k] for k in
                                      ("DestinyInventoryItemDefinition", "DestinyPlugSetDefinition")},
                  perkDefinition=perk, enhancedExcludedHash=ENHANCED,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                           tab="Weapon Perks", row=ROW, name=NAME, rawHTML=raw_row, text=description),
                  catalogScan=scan, socketProofs=proofs, allBaseTraitsOnSupportedWeapons=all_traits,
                  implemented54Audit=implemented_audit, reloadCompanionAudit=reload_audit)
    resource = dict(stage="W194", perk=MECHANICS, weapons=found)
    extra(root, data, stats, inventory, companions, resource, source)
    resource_raw = encode(resource)
    source["resourceSHA256"] = digest(resource_raw)
    return {PREFIX + "w194-" + SLUG + ".json": resource_raw,
            "art/weapons/w194/" + SLUG + "/source.json": encode(source),
            "art/weapons/w194/" + SLUG + "/SOURCE.md": NOTE.encode()}


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
