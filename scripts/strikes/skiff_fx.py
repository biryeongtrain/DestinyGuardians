"""Approximate baked additive radiance with a separate straight-alpha FX texture.

Minecraft alpha blending is not additive blending: this preserves radiance over
black, but attenuates the background. Keep that limitation visible in review.
The separate texture prevents the opaque hull from sharing a translucent sprite.
"""
import base64
import copy
import io
import uuid

import numpy as np
from PIL import Image


def linear(rgb):
    s = np.asarray(rgb, dtype=np.float64) / 255.0
    return np.where(s <= .04045, s / 12.92, ((s + .055) / 1.055) ** 2.4)


def straight_alpha(rgba):
    """Preserve radiance above Minecraft 26.3's 0.1 translucent alpha cutoff.

    Raising alpha alone would brighten the effect. Divide RGB by the same alpha
    so color*alpha still reconstructs source energy (before 8-bit quantization).
    """
    energy = linear(rgba[..., :3])
    peak = energy.max(axis=-1)
    alpha = np.where(peak > 0, np.maximum(peak, 26 / 255), 0)
    color = np.divide(energy, alpha[..., None], out=np.zeros_like(energy), where=alpha[..., None] > 0)
    srgb = np.where(color <= .0031308, color * 12.92, 1.055 * color ** (1 / 2.4) - .055)
    result = np.zeros_like(rgba)
    result[..., :3] = np.rint(np.clip(srgb, 0, 1) * 255).astype(np.uint8)
    result[..., 3] = np.rint(alpha * rgba[..., 3]).astype(np.uint8)
    return result


def split_fx(model):
    """Return a copy; hull texels and all geometry/rig/motion are unchanged."""
    if len(model['textures']) != 1:
        raise ValueError('Expected one packed source atlas')
    result = copy.deepcopy(model)
    texture = result['textures'][0]
    source = np.asarray(Image.open(io.BytesIO(base64.b64decode(texture['source'].split(',', 1)[1]))).convert('RGBA'))
    hull = source.copy()
    fx = np.zeros_like(source)
    mask = np.zeros(source.shape[:2], bool)
    rectangles = []
    faces = 0
    for element in result['elements']:
        if '_glow_' not in element['name']:
            continue
        for face in element['faces'].values():
            if face['texture'] is None:
                continue
            x0, y0, x1, y1 = map(int, face['uv'])
            if not (0 <= x0 <= x1 <= source.shape[1] and 0 <= y0 <= y1 <= source.shape[0]):
                raise ValueError('Invalid FX UV rectangle')
            mask[y0:y1, x0:x1] = True
            face['texture'] = 1
            rectangles.append((face, (x0, y0, x1, y1)))
            faces += 1
    if not faces:
        raise ValueError('No source emission faces found')
    fx[mask] = straight_alpha(source[mask])
    hull[mask] = 0
    # Repack complete face rectangles losslessly, including their transparent pixels.
    # Duplicating a mostly empty 4096 sprite can overflow the game's shared atlas.
    ordered = sorted(rectangles, key=lambda item: (-(item[1][3]-item[1][1]), -(item[1][2]-item[1][0])))
    for size in (256, 512, 1024, 2048, 4096, 8192):
        sky = np.zeros(size, np.int32)
        placements = []
        for face, (x0, y0, x1, y1) in ordered:
            width, height = x1-x0, y1-y0
            if width+1 > size or height+1 > size:
                break
            windows = np.lib.stride_tricks.sliding_window_view(sky, width+1).max(1)
            x = int(np.argmin(windows)); y = int(windows[x])
            if y+height+1 > size:
                break
            sky[x:x+width+1] = y+height+1
            placements.append((face, (x0, y0, x1, y1), x, y))
        if len(placements) == len(ordered):
            break
    else:
        raise ValueError('FX face rectangles exceed maximum atlas size')
    packed = np.zeros((size, size, 4), np.uint8)
    for face, (x0, y0, x1, y1), x, y in placements:
        width, height = x1-x0, y1-y0
        packed[y:y+height, x:x+width] = fx[y0:y1, x0:x1]
        face['uv'] = [x, y, x+width, y+height]
    def encoded(array):
        stream = io.BytesIO()
        Image.fromarray(array).save(stream, format='PNG')
        return 'data:image/png;base64,' + base64.b64encode(stream.getvalue()).decode()
    texture['source'] = encoded(hull)
    extra = copy.deepcopy(texture)
    extra.update(name='skiff_source_emission.png', id='1',
                 uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, 'destiny:skiff:source-emission')),
                 width=size, height=size, uv_width=size, uv_height=size, source=encoded(packed))
    result['textures'].append(extra)
    return result, dict(faces=faces, atlas_size=size, translucent_texels=int(((fx[..., 3] > 0) & (fx[..., 3] < 255)).sum()),
                        opaque_texels=int((fx[..., 3] == 255).sum()),
                        method='linear radiance to straight alpha above 26.3 cutoff, separate FX sprite',
                        limitation='alpha blend approximates additive over black; background attenuation remains')
