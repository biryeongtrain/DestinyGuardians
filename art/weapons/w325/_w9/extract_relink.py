"""W325 worker-9 wrapper around scripts/art/w325/extract_projection_cache.py (unchanged): before extracting, relink
images the rip archive does not ship (generic Bungie detail textures such as 327503503_digital_camo_2_diffuse.png) by
file name from the other read-only rips under /tmp/w325-rips. Missing images otherwise bake as Blender magenta.
Usage: Blender -b <blend> --python extract_relink.py -- <outdir> <ppm>   (never saves the .blend)"""
import bpy, os
here = os.path.dirname(os.path.abspath(__file__))
kit = os.path.join(here, '..', '..', '..', '..', 'scripts', 'art', 'w325', 'extract_projection_cache.py')
idx = {}
for d, _, fs in os.walk('/tmp/w325-rips'):
    for f in fs:
        idx.setdefault(f.lower(), os.path.join(d, f)); idx.setdefault(f.lower().replace(' ', '_'), os.path.join(d, f))
fixed = []
for im in bpy.data.images:
    if im.source != 'FILE' or os.path.exists(bpy.path.abspath(im.filepath)): continue
    name = os.path.basename(im.filepath.replace('\\', '/')).lower()
    hit = idx.get(name) or idx.get(name.replace(' ', '_'))
    if hit:
        im.filepath = hit; im.reload(); fixed.append((im.name, hit))
print('W9 relinked', len(fixed)); [print('  ', a, '->', b) for a, b in fixed]
exec(compile(open(kit).read(), kit, 'exec'))
