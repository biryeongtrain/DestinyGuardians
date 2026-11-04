"""Import gear-screen sample data from the read-only Downloads bundle.

Writes: armor/ghost icons as destiny:gui/hud/gear_<hash> item models (96 px), and
src/main/resources/destiny/gear/samples-ko.json (class armor sets, ghost shell, weapon flavour by Bungie hash).
"""
import json, shutil, pathlib, hashlib
SRC = pathlib.Path.home() / "Downloads/Destiny-Character-Gear-UI-KO-2026-11-04"
ROOT = pathlib.Path(__file__).resolve().parents[2]
RES = ROOT / "src/main/resources"
ASSETS = RES / "assets/destiny"
items = json.load(open(SRC / "data/items-ko.json"))
chars = json.load(open(RES / "destiny/weapons/w40-characteristics.json"))
ours = {e["bungieHash"] for e in chars}

SLOT = {"헬멧": "HELMET", "건틀릿": "GAUNTLETS", "가슴 방어구": "CHEST", "다리 방어구": "LEGS",
        "헌터 망토": "CLASS_ITEM", "타이탄 표식": "CLASS_ITEM", "워록 완장": "CLASS_ITEM"}
CLASS_SET = {"치솟는 분노": "HUNTER", "고귀한 상수": "TITAN", "자아의 발톱": "WARLOCK"}

def icon(row):
    name = f"gear_{row['id']}"
    tex = ASSETS / "textures/item/hud" / f"{name}.png"
    tex.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(SRC / "images/items" / f"{row['id']}.png", tex)
    model = {"gui_light": "front", "textures": {"layer0": f"destiny:item/hud/{name}"},
             "elements": [{"from": [0, 0, 8], "to": [16, 16, 8], "faces": {
                 f: {"texture": "#layer0", "uv": [0, 0, 16, 16], "tintindex": 0} for f in ("north", "south")}}]}
    (ASSETS / "models/gui/hud" / f"{name}.json").write_text(json.dumps(model, indent=2))
    item = {"model": {"type": "minecraft:model", "model": f"destiny:gui/hud/{name}",
                      "tints": [{"type": "minecraft:custom_model_data", "index": 0, "default": 16777215}]}}
    (ASSETS / "items/gui/hud" / f"{name}.json").write_text(json.dumps(item, indent=2))
    return name

def text(row):
    return {"name": row["name"]["ko"], "type": row["type"]["ko"],
            "flavour": (row.get("flavour") or {}).get("ko") or "", "rarity": row["rarity"].upper()}

armor = {"HUNTER": {}, "TITAN": {}, "WARLOCK": {}}
ghost = None
flavour = {}
for row in items:
    t = row["type"]["ko"]
    if t in SLOT:
        cls = next(c for k, c in CLASS_SET.items() if row["name"]["ko"].startswith(k))
        armor[cls][SLOT[t]] = {**text(row), "icon": icon(row), "hash": row["id"]}
    elif t == "고스트 의체":
        ghost = {**text(row), "icon": icon(row), "hash": row["id"]}
    elif row["id"] in ours and (row.get("flavour") or {}).get("ko"):
        flavour[str(row["id"])] = row["flavour"]["ko"]

out = RES / "destiny/gear/samples-ko.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps({"source": "Destiny-Character-Gear-UI-KO-2026-11-04 (Steam build 25932352)",
                           "armor": armor, "ghost": ghost, "weaponFlavour": flavour}, ensure_ascii=False, indent=2))
print("armor", {k: len(v) for k, v in armor.items()}, "ghost", bool(ghost), "flavour", len(flavour))
