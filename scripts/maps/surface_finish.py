"""Shared helpers for deterministic, collision-preserving template art passes."""
import numpy as np


def palette_id(states, state):
    state = state if ':' in state else 'minecraft:' + state
    if state not in states:
        states.append(state)
    return states.index(state)


def replace_shape(state, full, slab=None):
    """Keep the original half/double slab and all its block-state properties."""
    if '_slab[' in state:
        if slab is None:
            return state
        return 'minecraft:' + slab + '[' + state.split('[', 1)[1]
    if '[' in state:  # rails, walls and chains have independent collision shapes
        return state
    return 'minecraft:' + full


def roof_opacity(states):
    """Conservative sky occluders for template light placement, not thin decor."""
    names=[s.split(':',1)[-1].split('[',1)[0] for s in states]
    return np.array([n not in ('air','light','iron_bars','iron_chain')
                     and 'glass' not in n and not n.endswith(('_wall','_leaves')) for n in names])


def has_roof(world, opaque, x, feet_y, z):
    """Use the full authored height so tall chambers do not become outdoor sky."""
    return bool(opaque[world[feet_y+3:,z,x]].any())


def place_floor_lights(world, states, low, high, spacing=6, level=15):
    """Non-colliding fill above each usable deck in a bounded, multi-level arena."""
    light = palette_id(states, f'light[level={level},waterlogged=false]')
    is_open = np.array([s == 'minecraft:air' or s.startswith('minecraft:light[') for s in states])
    support = np.array([('[' not in s or '_slab[' in s) and not is_open[i]
                        and 'glass' not in s and not s.endswith(('_grass', '_bush')) for i, s in enumerate(states)])
    placed = 0
    for z in range(((low[2]+spacing-1)//spacing)*spacing, high[2]+1, spacing):
        for x in range(((low[0]+spacing-1)//spacing)*spacing, high[0]+1, spacing):
            for y in range(max(1, low[1]), min(world.shape[0]-3, high[1])+1):
                if support[world[y-1,z,x]] and is_open[world[y:y+3,z,x]].all():
                    if world[y+2,z,x] != light:
                        world[y+2,z,x] = light
                        placed += 1
    return placed


def patch_field(x, z):
    """Broad continuous patches, rather than independent salt-and-pepper voxels."""
    return (np.sin(x * .047 + np.sin(z * .021) * 1.4)
            + .65 * np.sin(z * .071 + x * .012)
            + .3 * np.sin(x * .13 - z * .08)) / 1.95


def protected_columns(shape, route, markers, route_radius=4, marker_radius=6):
    protected = np.zeros((shape[1], shape[2]), bool)
    points = [(int(x), int(z), route_radius) for x, _, z in route]
    points += [(int(m['pos'][0]), int(m['pos'][2]), marker_radius) for m in markers]
    for x, z, radius in points:
        a, b = max(0, x-radius), min(shape[2], x+radius+1)
        c, d = max(0, z-radius), min(shape[1], z+radius+1)
        zz, xx = np.ogrid[c:d, a:b]
        protected[c:d, a:b] |= (xx-x)**2 + (zz-z)**2 <= radius**2
    return protected
