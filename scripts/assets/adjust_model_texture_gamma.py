"""Adjust one embedded bbmodel texture without changing alpha, geometry or animations."""
import argparse
import base64
import hashlib
import io
import json
from pathlib import Path

from PIL import Image


def adjust(model, index, gamma):
    if not 0 < gamma <= 4:
        raise ValueError("gamma must be in (0, 4]")
    texture = model["textures"][index]
    old = base64.b64decode(texture["source"].split(",", 1)[1])
    image = Image.open(io.BytesIO(old)).convert("RGBA")
    red, green, blue, alpha = image.split()
    lut = [round(255 * (value / 255) ** gamma) for value in range(256)]
    output = Image.merge("RGBA", (red.point(lut), green.point(lut), blue.point(lut), alpha))
    buffer = io.BytesIO()
    output.save(buffer, format="PNG")
    new = buffer.getvalue()
    texture["source"] = "data:image/png;base64," + base64.b64encode(new).decode()
    assert output.getchannel("A").tobytes() == alpha.tobytes()
    return {"texture": index, "gamma": gamma, "oldSha256": hashlib.sha256(old).hexdigest(),
            "newSha256": hashlib.sha256(new).hexdigest(), "alphaPreserved": True}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    parser.add_argument("--texture", type=int, required=True)
    parser.add_argument("--gamma", type=float, required=True)
    args = parser.parse_args()
    model = json.loads(args.source.read_text())
    result = adjust(model, args.texture, args.gamma)
    args.output.write_text(json.dumps(model, separators=(",", ":")))
    print(json.dumps(result, indent=2))
