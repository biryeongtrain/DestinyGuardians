"""Deterministic orthographic source-triangle rasterization for depth slices.

Sample at texel centers before depth quantization. Coverage is evaluated before
selecting the nearest surface, so a cutout can reveal geometry behind it.
"""
import numpy as np


def uncovered_cells(reference_i, reference_j, raster_i, raster_j):
    """Keep subtexel source coverage where no texel-center ray hits a triangle."""
    occupied = set(zip(raster_i.tolist(), raster_j.tolist()))
    return np.fromiter(((i, j) not in occupied for i, j in zip(reference_i, reference_j)),
                       dtype=bool, count=len(reference_i))


def raster_face(triangles, uvs, pitch, axes, sample):
    """sample(triangle index, Nx2 UV) returns Nx3 colors and N coverage bools."""
    if not np.isfinite(pitch) or pitch <= 0:
        raise ValueError('Positive finite texel pitch required')
    da, near, (ua, va), _, _ = axes
    cells, depths, colors, sources = [], [], [], []
    for index, triangle in enumerate(triangles):
        p = triangle[:, [ua, va]] / pitch
        ab, ac = p[1]-p[0], p[2]-p[0]
        den = ab[0]*ac[1]-ab[1]*ac[0]
        if abs(den) < 1e-12:
            continue
        low = np.ceil(p.min(0)-.5).astype(int)
        high = np.floor(p.max(0)-.5).astype(int)
        if np.any(high < low):
            continue
        # Bound temporary grids for long, narrow source triangles.
        for row in range(low[1], high[1]+1, 64):
            ii, jj = np.meshgrid(np.arange(low[0], high[0]+1),
                                 np.arange(row, min(row+64, high[1]+1)))
            q = np.stack([ii.ravel()+.5, jj.ravel()+.5], axis=1)-p[0]
            b = (q[:, 0]*ac[1]-q[:, 1]*ac[0])/den
            c = (ab[0]*q[:, 1]-ab[1]*q[:, 0])/den
            inside = (b >= -1e-9) & (c >= -1e-9) & (b+c <= 1+1e-9)
            if not inside.any():
                continue
            weights = np.stack([1-b[inside]-c[inside], b[inside], c[inside]], axis=1)
            rgb, covered = sample(index, weights @ uvs[index])
            if not covered.any():
                continue
            cells.append(np.stack([ii.ravel()[inside][covered], jj.ravel()[inside][covered]], axis=1))
            depths.append((weights @ triangle[:, da])[covered])
            colors.append(rgb[covered])
            sources.append(np.full(int(covered.sum()), index, np.int32))
    if not cells:
        return None
    cell, depth, rgb, source = map(np.concatenate, (cells, depths, colors, sources))
    signed = depth if near == 'min' else -depth
    # Stable source index breaks exactly coplanar ties deterministically.
    order = np.lexsort((source, signed, cell[:, 1], cell[:, 0]))
    sorted_cells = cell[order]
    first = np.ones(len(order), bool)
    first[1:] = np.any(sorted_cells[1:] != sorted_cells[:-1], axis=1)
    winner = order[first]
    return dict(gi=cell[winner, 0], gj=cell[winner, 1], depth=depth[winner],
                rgb=rgb[winner], triangle=source[winner])
