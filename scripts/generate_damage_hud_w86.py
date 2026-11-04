#!/usr/bin/env python3
"""Author W86 white/tintable damage HUD quads and an offline full-HUD composite.

--verify reconstructs all bytes in memory and never creates files/directories.
No build, editor, client, server or custom shader is invoked.
"""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

import PIL
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "art/hud/w86/assets"
RES = ROOT / "src/main/resources/assets/destiny"
REF = ROOT / "art/hud/w86/references"
FONT = Path("/System/Library/Fonts/Supplemental/Arial Narrow Bold.ttf")
ARC_LEVELS = (1.0, .78, .60, .44, .29, .17, .07, 0.0)
CRITICAL_LEVELS = (0.0, .10, .18, .28, .40, .55, .73, 1.0)
REFERENCES = ("gameplay-coolguy-direction-L2-M0.jpg", "gameplay-coolguy-resistance-L2-M3.jpg")
WEDGE_REFERENCE = "gameplay-yZnltegf48g-maxres3.jpg"
HUD_INPUTS = ("ammo_panel.png", "ammo_sniper_rifle.png", "perk_no_distractions_w85.png")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encode(value):
    return (json.dumps(value, indent=2) + "\n").encode()


def png(im):
    stream = io.BytesIO()
    im.save(stream, format="PNG", compress_level=9)
    return stream.getvalue()


def smooth(a, b, value):
    t = max(0.0, min(1.0, (value-a)/(b-a)))
    return t*t*(3-2*t)


def arc_mask():
    """Compact solid tapered wedge, locally adapted from the inspected still.

    arc remains the runtime bank name, not a claim about the current silhouette.
    No isolated source alpha, exact bearing or radius was measured.
    """
    scale = 4
    high = Image.new("L", (256*scale, 256*scale))
    points = [(128,36), (151,48), (128,55), (105,48)]
    ImageDraw.Draw(high).polygon([(x*scale,y*scale) for x,y in points], fill=232)
    high = high.filter(ImageFilter.GaussianBlur(.45*scale))
    mask = high.resize((256,256), Image.Resampling.LANCZOS)
    # Exact geometric center at x128; remove rasterizer endpoint bias.
    for y in range(256):
        for x in range(128):
            alpha = round((mask.getpixel((x,y))+mask.getpixel((255-x,y)))/2)
            mask.putpixel((x,y),alpha)
            mask.putpixel((255-x,y),alpha)
    return mask


def critical_mask():
    """Low-opacity, irregular perimeter; center ellipse radius <=.60 is clear."""
    mask = Image.new("L", (512, 288))
    pixels = []
    for y in range(288):
        for x in range(512):
            nx, ny = (x+.5-256)/256, (y+.5-144)/144
            r = math.hypot(nx, ny)
            theta = math.atan2(ny, nx)
            edge = .77+.025*math.sin(theta*13)+.015*math.cos(theta*23)
            veil = smooth(edge, 1.40, r)
            # Broad irregular wisps and tiny fixed grain, not blood splatter.
            wave = .91+.06*math.sin(x*.071+y*.113)+.03*math.cos(x*.191-y*.049)
            noise = (((x*73856093) ^ (y*19349663) ^ 0x86A7) & 255)/255
            grain = .93+.07*noise
            lip = .16*smooth(.94, 1.02, max(abs(nx), abs(ny)))
            value = round(104*min(1, veil+lip)*wave*grain) if r > .60 else 0
            pixels.append(value)
    mask.putdata(pixels)
    return mask


def white(mask, amount):
    im = Image.new("RGBA", mask.size, (255, 255, 255, 0))
    im.putalpha(mask.point([round(i*amount) for i in range(256)]))
    return im


def tint(im, color):
    result = Image.new("RGBA", im.size, color+(0,))
    result.putalpha(im.getchannel("A"))
    return result


def inspection():
    result = Image.new("RGB", (1280, 1080), "#181818")
    # Actual numbered still, not a synthesized source or guessed timestamp.
    result.paste(Image.open(REF/WEDGE_REFERENCE).convert("RGB").resize((1280,720)), (0,0))
    for i, (ref, tile) in enumerate(((REFERENCES[0], 8), (REFERENCES[0], 9),
                                    (REFERENCES[1], 8), (REFERENCES[1], 9))):
        src = Image.open(REF/ref).convert("RGB")
        x, y = tile % 5*160, tile//5*90
        crop = src.crop((x, y, x+160, y+90)).resize((320, 180), Image.Resampling.NEAREST)
        result.paste(crop, (i*320, 720))
    # Enlarged marker context; the higher outgoing red X is not copied as a cue.
    still = Image.open(REF/WEDGE_REFERENCE).convert("RGB")
    result.paste(still.crop((580,410,740,490)).resize((360,180),Image.Resampling.NEAREST),(460,900))
    return result


def preview(arc, critical):
    """Original schematic scene + actual existing HUD glyphs, not a framebuffer."""
    scene = Image.new("RGBA", (1920, 1080), "#26353f")
    d = ImageDraw.Draw(scene)
    # Authored perspective scene makes visibility judgeable on light and dark areas.
    d.rectangle((0, 0, 1919, 490), fill="#516774")
    d.polygon([(0, 640), (700, 460), (1220, 460), (1920, 640), (1920, 1080), (0, 1080)], fill="#323c42")
    d.polygon([(0, 180), (610, 380), (610, 720), (0, 960)], fill="#65777d")
    d.polygon([(1920, 180), (1310, 380), (1310, 720), (1920, 960)], fill="#1c272e")
    for x in range(-900, 3000, 180):
        d.line((960, 460, x, 1080), fill="#49575c", width=2)
    for y in (560, 670, 820, 1020):
        d.line((0, y, 1920, y), fill="#49575c", width=2)
    d.rectangle((825, 350, 1095, 640), fill="#7a8886", outline="#b3bab4", width=3)
    d.rectangle((925, 405, 995, 580), fill="#35434a")
    # Schematic weapon, not a copied game model/render.
    d.polygon([(1235,1080),(1130,795),(1080,725),(1130,685),(1240,735),(1460,1080)], fill="#18252d")
    d.line((1110,715,1320,1040), fill="#71838a", width=9)
    # Existing native HUD pieces are read-only inputs, not recreated source assets.
    for filename, box in ((HUD_INPUTS[0], (80,875,420,980)), (HUD_INPUTS[1], (100,895,205,955)),
                          (HUD_INPUTS[2], (80,815,316,863))):
        src = Image.open(RES/"textures/item/hud"/filename).convert("RGBA")
        scene.alpha_composite(src.resize((box[2]-box[0], box[3]-box[1]), Image.Resampling.NEAREST), box[:2])
    font = ImageFont.truetype(str(FONT), 28)
    d = ImageDraw.Draw(scene)
    d.text((240,904), "4  /  16", font=font, fill="#eeeeee")
    d.rectangle((744,62,1176,69), fill="#233039")
    d.rectangle((744,62,856,69), fill="#e0e8eb")
    d.ellipse((80,65,210,195), outline="#bbcbd0", width=2)
    d.line((145,65,145,195), fill="#7b919b", width=1)
    d.line((80,130,210,130), fill="#7b919b", width=1)
    for bx in (80,142,204):
        d.rectangle((bx,998,bx+48,1046), outline="#cfdddd", width=2)
    # Composite critical behind arc; runtime quads themselves remain white.
    scene.alpha_composite(tint(critical[-1], (232, 39, 45)).resize(scene.size, Image.Resampling.BILINEAR))
    scene.alpha_composite(tint(arc[0], (255, 84, 65)).resize((320,320), Image.Resampling.BILINEAR), (800,380))
    d = ImageDraw.Draw(scene)
    d.ellipse((957,537,963,543), fill="#efffff")
    d.line((940,540,948,540), fill="#efffff", width=2)
    d.line((972,540,980,540), fill="#efffff", width=2)
    d.text((600,1015), "OFFLINE SCHEMATIC COMPOSITE - NOT NATIVE PROOF", font=font, fill="#f6e5ce")
    return scene.convert("RGB")


def contact_sheet(arc, critical):
    sheet = Image.new("RGB", (1024, 640), "#24323b")
    d = ImageDraw.Draw(sheet)
    font = ImageFont.truetype(str(FONT), 18)
    for i in range(8):
        x, y = i % 4*256, i//4*320
        a = tint(arc[i], (255,84,65)).resize((192,192))
        c = tint(critical[i], (232,39,45)).resize((256,144))
        sheet.paste(a, (x+32,y+14), a)
        sheet.paste(c, (x,y+172), c)
        d.text((x+8,y+4), f"{i}: ARC FADE / CRITICAL GAIN", font=font, fill="white")
    return sheet


def geometry_checks(arc, critical):
    for i, im in enumerate(arc):
        require(im.size == (256,256), "Arc dimensions")
        a = im.getchannel("A")
        require(a.tobytes() == a.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(), "Arc not centered/symmetric")
        require(a.crop((96,96,160,160)).getbbox() is None, "Arc obscures reticle")
        require(a.crop((0,128,256,256)).getbbox() is None, "Arc spills below center")
        if i:
            require(all(b <= p for b,p in zip(a.tobytes(),arc[i-1].getchannel("A").tobytes())), "Arc fade not monotone")
    require(arc[-1].getchannel("A").getbbox() is None, "Final arc must be transparent")
    for i, im in enumerate(critical):
        a = im.getchannel("A")
        require(a.crop((192,108,320,180)).getbbox() is None, "Critical obscures aim center")
        require(a.getextrema()[1] <= 104, "Critical opacity too high")
        if i:
            require(all(b >= p for b,p in zip(a.tobytes(),critical[i-1].getchannel("A").tobytes())), "Critical gain not monotone")
    require(critical[0].getchannel("A").getbbox() is None, "Critical zero must be transparent")
    for im in arc+critical:
        require(all(im.getchannel(c).getextrema() == (255,255) for c in "RGB"), "Texture not white/tintable")
    return dict(whiteRgb=True, arcHorizontalSymmetry=True, transparentAimCenter=True,
                arcFadeMonotone=True, criticalGainMonotone=True, criticalMaxAlpha=critical[-1].getchannel("A").getextrema()[1])


def generate():
    wedge = arc_mask()
    arc = [white(wedge, level) for level in ARC_LEVELS]
    base = critical_mask()
    critical = [white(base, level) for level in CRITICAL_LEVELS]
    checks = geometry_checks(arc, critical)
    outputs = {}
    for family, images in (("arc",arc),("critical",critical)):
        for i, im in enumerate(images):
            name = f"incoming_w86_{family}_{i}"
            outputs[RES/f"textures/item/hud/{name}.png"] = png(im)
            outputs[RES/f"models/gui/hud/{name}.json"] = encode({
                "gui_light":"front", "ambientocclusion":False,
                "textures":{"layer0":f"destiny:item/hud/{name}"},
                "elements":[{"from":[0,0,8],"to":[16,16,8],"shade":False,
                    "faces":{face:{"texture":"#layer0","uv":[0,0,16,16],"tintindex":0} for face in ("north","south")}}]})
            outputs[RES/f"items/gui/hud/{name}.json"] = encode({"model":{
                "type":"minecraft:model", "model":f"destiny:gui/hud/{name}",
                "tints":[{"type":"minecraft:custom_model_data","index":0,"default":16777215}]}})
    outputs[ART/"reference-inspection.png"] = png(inspection())
    outputs[ART/"offline-full-hud.png"] = png(preview(arc,critical))
    outputs[ART/"levels-preview.png"] = png(contact_sheet(arc,critical))
    inputs = [Path(__file__).resolve(), FONT, ROOT/"art/hud/w86/reference-notes.md"]+[REF/name for name in REFERENCES+(WEDGE_REFERENCE,)]
    inputs += [RES/"textures/item/hud"/name for name in HUD_INPUTS]
    key = lambda p: p.relative_to(ROOT).as_posix() if p.is_relative_to(ROOT) else str(p)
    manifest = dict(stage="W86", schema=1, generator=key(Path(__file__).resolve()), pillowVersion=PIL.__version__,
        inputSha256={key(p):digest(p.read_bytes()) for p in inputs},
        outputs={key(p):digest(raw) for p,raw in outputs.items()},
        contract=dict(itemPrefix="destiny:gui/hud/incoming_w86_", tint="CMD colors index0, default white",
            geometry="Two-sided 16x16 plane, full UV; runtime sets independent X/Y scale and in-plane rotation",
            arc=dict(ids=[f"destiny:gui/hud/incoming_w86_arc_{i}" for i in range(8)], textureSize=[256,256],
                symmetryCenter=[128,128], topIsBearingZero=True, alphaEnvelope=list(ARC_LEVELS),
                referenceQuadAt1920x1080=dict(center=[960,540],size=[320,320]),
                silhouette="compact filled tapered wedge; arc retained only as bank identifier",
                authoredVerticesTexturePixels=[[128,36],[151,48],[128,55],[105,48]],
                recommendedLayer="Above critical vignette, behind reticle"),
            critical=dict(ids=[f"destiny:gui/hud/incoming_w86_critical_{i}" for i in range(8)], textureSize=[512,288],
                alphaEnvelope=list(CRITICAL_LEVELS), referenceQuadAt1920x1080=dict(center=[960,540],size=[1920,1080]),
                maximumTextureAlpha=104, recommendedLayer="Behind directional arc and HUD text")),
        policy=dict(authorship="Original filled tapered wedge and grain-modulated peripheral mask; no reference pixels in runtime textures",
            referenceBasis="Final W86 notes and actual gameplay-yZnltegf48g-maxres3.jpg visually inspected: compact red/orange filled wedge near aim area, separate broad red periphery. Storyboards remain qualitative context.",
            referenceLimitation="Numbered still timestamp unknown; marker overlaps target. Exact isolated silhouette, geometry, bearing, alpha, timing and critical HP threshold not measured. Higher red X is outgoing hitmarker, not incoming cue.",
            arcShape="Compact filled tapered wedge with lightly softened edges; not broad crescent or generic shaft arrow. Top convention and geometry are local adaptations, not D2-exact.",
            timing="Eight discrete authored alpha levels only; duration/fade curve/pulse runtime-owned and unmeasured",
            threshold="Actual HP fraction and critical threshold runtime-owned; not inferred from thumbnails",
            orientation="Top-centered source; runtime rotates around quad center for attacker bearing; sign/native orientation requires parent native verification",
            preview="Offline 1920x1080 schematic composite with existing HUD glyphs; not a screenshot or native proof",
            limitations="No native blend/layer/near-plane/GUI-scale certification; no custom-client code, shaders, fonts or copied game textures"),
        checks=checks, nativeVerified=False)
    outputs[ART/"manifest.json"] = encode(manifest)
    return outputs


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify", action="store_true", help="Reconstruct and compare only; no writes")
    args = parser.parse_args()
    outputs = generate()
    for path, raw in outputs.items():
        allowed = path.is_relative_to(ART) or (path.parent in {RES/"textures/item/hud",RES/"models/gui/hud",RES/"items/gui/hud"}
                                               and path.name.startswith("incoming_w86_"))
        require(allowed, "Output escapes W86 ownership: "+str(path))
        if args.verify:
            require(path.is_file() and path.read_bytes() == raw, "Generated output drift: "+str(path.relative_to(ROOT)))
        else:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(raw)
    actual = {p for folder in (RES/"textures/item/hud",RES/"models/gui/hud",RES/"items/gui/hud") for p in folder.glob("incoming_w86_*") if p.is_file()}
    require(actual == {p for p in outputs if p.is_relative_to(RES)}, "Unexpected incoming_w86 resource inventory")
    print(json.dumps(dict(stage="W86", verified=args.verify, files=len(outputs), nativeVerified=False)))


if __name__ == "__main__":
    main()
