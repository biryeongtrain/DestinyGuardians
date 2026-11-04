#!/usr/bin/env python3
"""Locally authored W89 critical wash. --verify reconstructs bytes read-only.
No runtime/build/native/shader changes. Requires Pillow; use destiny-hud-venv.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path
import PIL
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/hud/w89/assets"
ASSETS = ROOT / "src/main/resources/assets"
RES = ASSETS / "destiny"
LEVELS = (.48, .55, .63, .70, .78, .85, .93, 1.0)
PREFIX = "incoming_w89_critical_"
INPUTS = ("scripts/generate_critical_hud_w89.py", "scripts/generate_damage_hud_w86.py",
          "docs/qa/2026-10-25/w88/critical-analysis.md", "art/hud/w86/reference-notes.md",
          "art/hud/w86/references/gameplay-yZnltegf48g-maxres3.jpg")


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def key(p):
    return p.relative_to(ROOT).as_posix()


def encode(obj):
    return (json.dumps(obj, indent=2, sort_keys=True) + "\n").encode()


def png(im):
    buf = io.BytesIO()
    im.save(buf, format="PNG", compress_level=9)
    return buf.getvalue()


def owned_resource(p):
    return any(p == RES / folder / (PREFIX + str(i) + suffix)
               for i in range(8) for folder, suffix in (
                   ("textures/item/hud", ".png"), ("textures/item/hud", ".png.mcmeta"),
                   ("models/gui/hud", ".json"), ("items/gui/hud", ".json")))


def smooth(lo, hi, x):
    t = min(1.0, max(0.0, (x-lo)/(hi-lo)))
    return t*t*(3-2*t)


def mask():
    """Soft low-frequency edge wisps, no droplets or sampled game pixels."""
    values = []
    for y in range(288):
        for x in range(512):
            nx, ny = (x+.5-256)/256, (y+.5-144)/144
            r, theta = math.hypot(nx, ny), math.atan2(ny, nx)
            if r <= .60:
                values.append(0.0)
                continue
            onset = .64 + .025*math.sin(theta*5+.7) + .018*math.cos(theta*9)
            body = smooth(onset, 1.12, r)
            # Broad perimeter includes the four edge midpoints, not only corners.
            lip = .12*smooth(.80, 1.0, max(abs(nx), abs(ny)))
            cloud = .86 + .085*math.sin(x*.025+y*.041) + .045*math.cos(x*.051-y*.019)
            ripple = 1 + .045*math.sin(theta*11 + r*19 + math.sin(theta*3))
            values.append(min(1.0, body+lip)*cloud*ripple)
    peak = max(values)
    return [round(160*v/peak) for v in values]


def check(images):
    stats, previous = [], None
    center = [math.hypot((x+.5-256)/256, (y+.5-144)/144) <= .60
              for y in range(288) for x in range(512)]
    for i, im in enumerate(images):
        a = list(im.getchannel("A").tobytes())
        require(im.mode == "RGBA" and im.size == (512,288), "RGBA dimensions")
        require(all(im.getchannel(c).getextrema() == (255,255) for c in "RGB"), "White RGB")
        require(all(v == 0 for v,c in zip(a,center) if c), "Center ellipse must be clear")
        require(0 < max(a) <= 170, "All frames active; opacity cap")
        require(sum(v >= 26 for v in a) >= math.ceil(.20*len(a)), "Cutoff coverage below 20%")
        require(previous is None or all(v >= p for v,p in zip(a,previous)), "Nonmonotone gain")
        edges = dict(top=(192,0,320,36), bottom=(192,252,320,288),
                     left=(0,108,64,180), right=(448,108,512,180))
        edge_counts = {n:sum(v >= 26 for v in im.getchannel("A").crop(b).tobytes()) for n,b in edges.items()}
        require(all(v > 0 for v in edge_counts.values()), "Perimeter missing an edge midpoint")
        stats.append(dict(frame=i, gain=LEVELS[i], texels=len(a), alphaMax=max(a),
                          transparent=sum(v == 0 for v in a), partial=sum(0 < v < 255 for v in a),
                          opaque=sum(v == 255 for v in a), alphaAtLeast26=sum(v >= 26 for v in a),
                          cutoffCoverage=sum(v >= 26 for v in a)/len(a), edgeMidpointCounts=edge_counts))
        previous = a
    require(72 <= stats[0]["alphaMax"] <= 80, "First alpha near 75")
    require(150 <= stats[-1]["alphaMax"] <= 165, "Final alpha 150..165")
    return stats


def preview(images):
    sheet = Image.new("RGB", (1024,640), "#172530")
    d = ImageDraw.Draw(sheet)
    d.text((14,10), "W89 OFFLINE SCHEMATIC / NOT NATIVE PROOF / LOCAL ART, NOT D2-EXACT", fill="white")
    for i, im in enumerate(images):
        scene = Image.new("RGBA", (512,288), "#607580")
        s = ImageDraw.Draw(scene)
        s.polygon([(0,288),(210,138),(302,138),(512,288)], fill="#303e48")
        s.rectangle((220,100,292,194), fill="#a4aaa4")
        s.line((256,139,256,149), fill="white")
        s.line((251,144,261,144), fill="white")
        tint = Image.new("RGBA", im.size, (225,32,43,0))
        tint.putalpha(im.getchannel("A"))
        scene.alpha_composite(tint)
        # Show shader-cutoff survival in the bottom row; full author alpha above.
        if i >= 4:
            tint.putalpha(im.getchannel("A").point(lambda a: a if a >= 26 else 0))
            scene = Image.new("RGBA", im.size, "#607580")
            scene.alpha_composite(tint)
        x, y = (i%4)*256, 42+(i//4)*294
        sheet.paste(scene.convert("RGB").resize((256,144)), (x,y))
        d.text((x+8,y+154), f"ACTIVE {i} / gain {LEVELS[i]:.2f}", fill="white")
        d.text((x+8,y+170), "offline red tint; white runtime PNG", fill="#c5d4dc")
        d.text((x+8,y+186), "alpha >= 26 shown" if i>=4 else "authored alpha shown", fill="#c5d4dc")
    return sheet


def generate():
    old = {key(p):sha(p.read_bytes()) for p in sorted(ASSETS.rglob("*")) if p.is_file() and not owned_resource(p)}
    require(len(old) == 6588, f"Protected inventory expected 6588, got {len(old)}")
    protected = encode(dict(count=len(old), sha256=old))
    baseline = ART / "protected-assets.json"
    if baseline.exists():
        require(baseline.read_bytes() == protected, "Protected legacy asset bytes/inventory changed")
    base = mask()
    images = []
    for level in LEVELS:
        im = Image.new("RGBA", (512,288), (255,255,255,0))
        im.putalpha(bytes_to_mask([round(v*level) for v in base]))
        images.append(im)
    stats = check(images)
    outputs = {baseline:protected}
    for i, im in enumerate(images):
        name = PREFIX + str(i)
        texture = "destiny:item/hud/" + name
        outputs[RES / f"textures/item/hud/{name}.png"] = png(im)
        outputs[RES / f"textures/item/hud/{name}.png.mcmeta"] = encode({"texture":{"mipmap_strategy":"mean"}})
        outputs[RES / f"models/gui/hud/{name}.json"] = encode({
            "gui_light":"front", "ambientocclusion":False,
            "textures":{"layer0":texture,"particle":texture},
            "elements":[{"from":[0,0,8],"to":[16,16,8],"shade":False,
                         "faces":{f:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0}
                                  for f in ("north","south")}}]})
        outputs[RES / f"items/gui/hud/{name}.json"] = encode({"model":{
            "type":"minecraft:model", "model":"destiny:gui/hud/"+name,
            "tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}})
    outputs[ART / "offline-preview.png"] = png(preview(images))
    inputs = {p:sha((ROOT/p).read_bytes()) for p in INPUTS}
    manifest = dict(stage="W89", schema=1, pillowVersion=PIL.__version__,
        inputCount=len(inputs), inputSha256=inputs, outputCount=len(outputs)+1,
        outputHashes={key(p):sha(v) for p,v in outputs.items()},
        outputHashNote="Manifest excludes its own hash; all other generated outputs hashed.",
        currentAssetCount=32, currentAssetHashes={key(p):sha(v) for p,v in outputs.items() if owned_resource(p)},
        protectedAssetCount=len(old), protectedAssetHashesFile=key(baseline),
        banks={"critical":dict(frameCount=8, frames=stats)},
        contract=dict(size=[512,288], centerEllipseClearRadius=.60, whiteTintable=True,
            alphaEnvelope=LEVELS, alphaCutoff=26, minimumCoverage=.20, maximumAlpha=170,
            geometry="Two-sided full-UV 16x16 plane", tint="CMD colors index 0",
            mipmapStrategy="mean", runtimeFrameRange=[0,7], allFramesActive=True),
        authorship="Locally authored broad irregular peripheral wash; no blood splatter or copied source pixels; no exact D2 claim.",
        reference="W86 qualitative broad red periphery; opacity envelope addresses W88 native item alpha cutoff 0.1.",
        preview="OFFLINE schematic red-tinted preview only; not native evidence.",
        limits="Native visibility, filtering, placement, tint, layering and recovery remain parent validation. No runtime/library/shader edits.",
        checks=dict(centerClear=True, monotonePerTexel=True, whiteRGB=True, eachFrameCoverageAtLeast20Percent=True,
                    allFourEdgeMidpointsVisible=True, legacyAssetsByteExact=True), nativeVerified=False)
    outputs[ART / "manifest.json"] = encode(manifest)
    return outputs


def bytes_to_mask(values):
    return Image.frombytes("L", (512,288), bytes(values))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Reconstruct and compare byte-exact, without writes")
    args = parser.parse_args()
    outputs = generate()
    for p, raw in outputs.items():
        require(p.is_relative_to(ART) or owned_resource(p), "Ownership violation: "+key(p))
        if args.verify:
            require(p.is_file() and p.read_bytes() == raw, "Output drift: "+key(p))
        else:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(raw)
    actual = {p for d in ("textures/item/hud","models/gui/hud","items/gui/hud")
              for p in (RES/d).glob(PREFIX+"*") if p.is_file()}
    require(actual == {p for p in outputs if owned_resource(p)}, "Unexpected W89 resource inventory")
    require({p for p in ART.rglob("*") if p.is_file()} == {p for p in outputs if p.is_relative_to(ART)}, "Unexpected W89 art inventory")
    print(json.dumps(dict(stage="W89", verified=args.verify, generatedFiles=len(outputs),
                         resourceFiles=len(actual), protectedAssets=6588, nativeVerified=False)))


if __name__ == "__main__":
    main()
