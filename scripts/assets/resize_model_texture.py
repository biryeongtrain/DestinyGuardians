"""Downsample an embedded cuboid texture while preserving normalized UVs and the rig."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path
from PIL import Image


def resize(model, index, size):
    texture = model["textures"][index]
    original = base64.b64decode(texture["source"].split(",", 1)[1])
    image = Image.open(io.BytesIO(original)).convert("RGBA")
    width, height = image.size
    if size < 1 or size >= max(width, height):
        raise ValueError("Target must be a positive downscale")
    if any(e.get("type", "cube") != "cube" or e.get("box_uv", False) for e in model["elements"]):
        raise ValueError("Only explicit cuboid face UVs are supported")
    factor = size / max(width, height)
    target = (max(1, round(width * factor)), max(1, round(height * factor)))
    old_uv = (texture.get("uv_width", model["resolution"]["width"]),
              texture.get("uv_height", model["resolution"]["height"]))
    new_uv = (old_uv[0] * target[0] / width, old_uv[1] * target[1] / height)
    if any(v != int(v) for v in new_uv):
        raise ValueError("Target UV dimensions must be integral")
    # Premultiplied alpha prevents transparent atlas gutters from darkening edge RGB.
    output = image.convert("RGBa").resize(target, Image.Resampling.LANCZOS).convert("RGBA")
    cutout = set(image.getchannel("A").tobytes()) <= {0, 255}
    if cutout:
        # Introducing fractional alpha changes opaque cutout models into blended surfaces.
        # Keep their discrete coverage, while filtering RGB in premultiplied space.
        output.putalpha(image.getchannel("A").resize(target, Image.Resampling.NEAREST))
    buffer = io.BytesIO()
    output.save(buffer, format="PNG", optimize=True)
    data = buffer.getvalue()
    for element in model["elements"]:
        for face in element.get("faces", {}).values():
            if face.get("texture") == index:
                before = face["uv"]
                face["uv"] = [v * new_uv[i % 2] / old_uv[i % 2] for i, v in enumerate(before)]
                assert all(a / old_uv[i % 2] == b / new_uv[i % 2]
                           for i, (a, b) in enumerate(zip(before, face["uv"])))
    # Every texture keeps an explicit logical UV size, including unchanged companion textures.
    for t in model["textures"]:
        t.setdefault("uv_width", model["resolution"]["width"])
        t.setdefault("uv_height", model["resolution"]["height"])
    texture.update(source="data:image/png;base64," + base64.b64encode(data).decode(),
                   width=target[0], height=target[1], uv_width=int(new_uv[0]), uv_height=int(new_uv[1]))
    if index == 0:
        model["resolution"] = {"width": int(new_uv[0]), "height": int(new_uv[1])}
    return {"texture": index, "cutoutAlphaPreserved": cutout, "before": [width, height], "after": list(target),
            "beforeBytes": len(original), "afterBytes": len(data),
            "oldSha256": hashlib.sha256(original).hexdigest(), "newSha256": hashlib.sha256(data).hexdigest()}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("model", type=Path)
    parser.add_argument("--texture", type=int, default=0)
    parser.add_argument("--size", type=int, required=True)
    args = parser.parse_args()
    model = json.loads(args.model.read_text())
    report = resize(model, args.texture, args.size)
    args.model.write_text(json.dumps(model, separators=(",", ":")) + "\n")
    print(json.dumps(report, indent=2))
