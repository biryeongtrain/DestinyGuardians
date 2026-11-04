#!/usr/bin/env python3
"""Read-only pinned W78 ground-wave identity/data verification; no downloads or cache repair."""
import sys
sys.dont_write_bytecode=True
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
PINS={'src/main/resources/destiny/weapons/w78-wave.json': '34c3fd6dacdc8c9f61be2428485b69e27074a3767911127ac5f30f7b923c21d8', 'src/main/resources/destiny/weapons/w30.json': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a', 'src/main/resources/destiny/weapons/w40-characteristics.json': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1', 'art/weapons/w40/provenance.json': '281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42', 'art/weapons/w78/references/cached-source-index.json': '306dec612eb49a2f923f55a7487f2412e38e597de63bac544e343fd45f18bc20', 'art/weapons/w78/references/community-observations.json': '4b78e703054d53222be15081eb0d4668c3b3818298c8fc3a768aee9759dc2e96', 'art/weapons/w78/references/official-changes.json': '71fbc0bdd4595029af59d178a150778e3e7812f7bfc310bf6f1cfdbc071f9412', 'art/weapons/w78/references/pinned-identities.json': 'c5a368bf0e3b7b7b72c27b380a364bd902972ad78e73e4fd667bfa21ecf400c0', 'art/weapons/w78/references/research-boundary.json': '7e39363e65f2d1cb9b958805a6d82727b9ee4395c8b91371c862797c12235b8c'}
def check(ok,message):
    if not ok:raise ValueError(message)
def verify(root,sources):
    values={}
    for name,digest in PINS.items():
        raw=(root/name).read_bytes();check(hashlib.sha256(raw).hexdigest()==digest,"Pinned data drift: "+name);values[name]=json.loads(raw)
    refs="art/weapons/w78/references/"
    index=values[refs+"cached-source-index.json"]
    # Read all ten indexed caches. Six historical bow/HTML records are preservation only, never wave evidence.
    for row in index["files"]:
        name=row["path"]
        path=sources/Path(name).relative_to("run/private-sources/w73") if name.startswith("run/private-sources/w73/") else root/name
        raw=path.read_bytes();check(len(raw)==row["bytes"] and hashlib.sha256(raw).hexdigest()==row["sha256"],"Source SHA drift: "+name)
    manifest=json.loads((sources/"manifest.json").read_bytes())
    identity=values[refs+"pinned-identities.json"]
    check(manifest["ErrorCode"]==1 and manifest["Response"]["version"]==identity["manifestVersion"],"Manifest mismatch")
    inv=json.loads((sources/"bungie-items.json").read_bytes());plugs=json.loads((sources/"bungie-plugsets.json").read_bytes())
    chars={e["id"]:e for e in values["src/main/resources/destiny/weapons/w40-characteristics.json"]}
    catalog=values["src/main/resources/destiny/weapons/w30.json"]
    data=values["src/main/resources/destiny/weapons/w78-wave.json"]
    check(data["stage"]=="W78" and len(data["weapons"])==2,"Incomplete wave data")
    profiles={p["id"]:p for p in data["weapons"]}
    check(set(profiles)=={"deafening_whisper","dimensional_hypotrochoid"},"Unreviewed wave identity")
    for proof in identity["weapons"]:
        key=proof["localId"];profile=profiles[key];weapon=inv[str(proof["weaponHash"])];frame=inv[str(proof["frameHash"])];meta=chars[key]
        check(profile["hash"]==weapon["hash"]==meta["bungieHash"] and profile["intrinsicHash"]==frame["hash"],"Identity mismatch: "+key)
        check(weapon["sockets"]["socketEntries"][0]["singleInitialItemHash"]==frame["hash"] and frame["displayProperties"]["name"]==proof["frameName"],"Frame socket mismatch")
        check("ground" in frame["displayProperties"]["description"].lower(),"Ground contact trigger changed")
        check(weapon["equippingBlock"]["ammoType"]==proof["ammoType"] and weapon["defaultDamageType"]==proof["damageTypeEnum"],"Ammo/element mismatch")
        check(meta["ammo"]==proof["ammo"] and meta["damage"]==proof["damageType"],"Runtime metadata mismatch")
        check(any(p["plugItemHash"]==frame["hash"] for p in plugs[str(proof["frameReusablePlugSetHash"])]["reusablePlugItems"]),"Frame plug set mismatch")
        for field in proof["baseStats"].values():
            check(weapon["stats"]["stats"][str(field["statHash"])]["value"]==field["value"]==meta["stats"][str(field["statHash"])],"Definition stat mismatch")
    # Scan the whole selected catalog instead of trusting only a prefiltered pair.
    found=set()
    for entry in catalog:
        weapon=inv[str(chars[entry["id"]]["bungieHash"])];frame=weapon["sockets"]["socketEntries"][0]["singleInitialItemHash"]
        if frame in {1395789926,2571259936}:found.add(entry["id"])
    check(found==set(profiles),"Selected wave catalog expanded without implementation review")
    return dict(stage="W78",readOnly=True,sourceCacheFiles=len(index["files"]),pinnedDataFiles=len(PINS),selectedWeapons=len(catalog),exactWaveWeapons=sorted(profiles),specialPublishedLengthMeters=15,heavyLengthAuthoredBlocks=12,geometrySpeedDamageAuthored=True,profiles=list(profiles.values()),currentSandboxExhaustivelyAudited=False)
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument("--root",type=Path,default=ROOT);p.add_argument("--sources-dir",type=Path);p.add_argument("--verify",action="store_true");p.add_argument("--inspect-source",action="store_true");a=p.parse_args()
    check(not(a.verify and a.inspect_source),"Choose one verification mode")
    report=verify(a.root.resolve(),(a.sources_dir or a.root/"run/private-sources/w73").resolve());print(json.dumps(report,indent=2))
if __name__=="__main__":main()
