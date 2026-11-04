#!/usr/bin/env python3
"""Generate/check exact base Moving Target sockets and bounded DDC source evidence."""
import argparse
import hashlib
import html
import json
import re
from pathlib import Path

BASE = 588594999
ENHANCED = 2717805783
TRAIT_CATEGORY = 4241085061
EXPECTED = [
    ("duke_mk_44", 2112909414, 4, 3815727680),
    ("distant_relation", 2034817450, 4, 3824767299),
    ("bug_out_bag", 2744715540, 4, 575371383),
    ("farewell", 541188001, 3, 284168234),
    ("dead_man_walking_xx7463", 3751622019, 3, 3268663985),
    ("biting_winds", 1621657423, 3, 3968704963),
    ("bite_of_the_fox", 1403800851, 4, 2442672691),
    ("beloved", 3107853529, 4, 887157889),
    ("apostate", 2164448701, 3, 1306932196),
    ("dust_rock_blues", 636912560, 3, 3511609070),
    ("parcel_of_stardust_fell_to_earth", 2217366863, 4, 3424940310),
    ("ikelos_sg_v1_0_1", 1887808042, 4, 1324),
    ("dream_breaker", 2931957300, 3, 3785896921),
    ("coriolis_force", 3512349612, 3, 2568674372),
    ("line_in_the_sand", 946443267, 3, 1503774254),
    ("deafening_whisper", 981718087, 3, 3110206796),
    ("bellowing_giant", 2186258845, 4, 1722393382),
    ("pyroclastic_flow", 1289324202, 4, 3838086002),
]


def load(path):
    return json.loads(path.read_text())


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--check", action="store_true", help="verify generated outputs without writing")
    args = parser.parse_args()
    root = args.root.resolve()
    inventory = Path("/tmp/destiny-weapons-w30/bungie-items.json")
    plugsets = Path("/tmp/destiny-weapons-w60/bungie-plugsets.json")
    manifest = Path("/tmp/destiny-weapons-w60/manifest.json")
    ddc = Path("/private/tmp/destiny-w190/ddc-perks.html")
    characteristics = root / "src/main/resources/destiny/weapons/w40-characteristics.json"
    catalog = root / "src/main/resources/destiny/weapons/w30.json"
    inv, pools = load(inventory), load(plugsets)
    canonical = {entry["id"]: entry for entry in load(catalog)}
    rolls, proofs = [], []
    for weapon in load(characteristics):
        item = inv[str(weapon["bungieHash"])]
        if weapon["exotic"] or item["inventory"]["tierType"] != 5:
            continue
        assert item["hash"] == weapon["bungieHash"]
        sockets = item["sockets"]
        indices = sorted({n for category in sockets["socketCategories"]
                          if category["socketCategoryHash"] == TRAIT_CATEGORY
                          for n in category["socketIndexes"]})
        for index in indices:
            socket = sockets["socketEntries"][index]
            # W320 follow-up: curated fixed-roll legendaries expose their trait column as reusablePlugSetHash with isFakePlugSet true.
            pool_hash = socket.get("randomizedPlugSetHash") or socket.get("reusablePlugSetHash")
            pool = pools.get(str(pool_hash), {})
            if pool.get("isFakePlugSet") is not ("randomizedPlugSetHash" not in socket):
                continue
            matches = [plug for plug in pool.get("reusablePlugItems", [])
                       if plug.get("plugItemHash") == BASE and plug.get("currentlyCanRoll") is True]
            if not matches:
                continue
            assert len(matches) == 1 and pool["hash"] == pool_hash
            roll = dict(id=weapon["id"], hash=weapon["bungieHash"], socket=index,
                        perkHash=BASE, plugSetHash=pool_hash)
            rolls.append(roll)
            proofs.append(dict(roll=roll, traitCategory=TRAIT_CATEGORY,
                               itemName=item["displayProperties"]["name"], tierType=5,
                               exotic=False, isFakePlugSet=pool["isFakePlugSet"], socket=socket,
                               matchingPlug=matches[0], canonicalEntry=canonical[weapon["id"]]))
    assert [(r["id"], r["hash"], r["socket"], r["plugSetHash"]) for r in rolls] == EXPECTED
    # Select one bounded row by the export's zero-based anchor, not a huge HTML dump.
    document = ddc.read_text()
    anchor = document.index('id="1662574278R148"')
    start = document.rfind("<tr", max(0, anchor - 1024), anchor)
    end = document.find("</tr>", anchor, anchor + 32768)
    assert start >= 0 and end >= 0
    row = document[start:end + len("</tr>")]
    text = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", row))).strip()
    assert re.search(r">149</div>", row) and "Moving Target" in text
    assert "+10" in text and "Aim Assist" in text and "10% Decreased ADS Movement Speed Penalty" in text
    assert "While" in text and "ADS" in text and "+11?" in text and "unknown amount" in text
    assert inv[str(BASE)]["displayProperties"]["name"] == "Moving Target"
    assert inv[str(ENHANCED)]["hash"] == ENHANCED
    resource = dict(stage="W203", perk=dict(id="moving_target", hash=BASE,
                    adsMovementPenaltyScalar=0.9, sourceAimAssistBonus=10, aimAssistImplemented=False), weapons=rolls)
    inputs = (inventory, plugsets, manifest, ddc, characteristics, catalog)
    source = dict(date="2026-10-27", perkDefinition=inv[str(BASE)],
                  officialManifest=load(manifest)["Response"]["version"],
                  inputs={str(path) if not path.is_relative_to(root) else str(path.relative_to(root)): sha(path)
                          for path in inputs}, socketProofs=proofs,
                  ddc=dict(url="https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?gid=1662574278",
                           row=149, exportAnchor="1662574278R148", text=text, html=row),
                  baseValuesVerifiedFromDDC=True, enhancedExcluded=dict(hash=ENHANCED,
                  reason="Base only; enhanced +11? aim assist is uncertain and is not simulated."),
                  movementMapping="Caller accepts owned ADS; 1-(1-baseScalar)*0.9 composes the remaining penalty, including intrinsic precision-HC baseline .775. No additive .10 speed.",
                  limitations=["Source +10 aim assist stored only; no simulated aim assist or target acquisition.",
                               "No native attributes or WeaponAiming calls in helper; coordinator owns registry, ADS acceptance, modifier refresh and lifecycle.",
                               "Exact 17 curated legendary hashes only; no same-name reissue, enhanced, fake pool or unavailable plug fallback."])
    outputs = {"src/main/resources/destiny/weapons/w203-moving-target.json": resource,
               "art/weapons/w203/moving-target/source.json": source}
    for name, value in outputs.items():
        dest = root / name
        encoded = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
        if args.check:
            assert dest.read_text() == encoded, f"stale output: {name}"
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(encoded)
    print(f"Moving Target: 17 exact base sockets; DDC row149; penalty x0.9; +10AA source-only; enhanced excluded; {'checked' if args.check else 'generated'}.")


if __name__ == "__main__":
    main()
