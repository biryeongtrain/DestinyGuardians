# Bellowing Giant W150 art review

Actual opened photo: `/tmp/destiny-weapons-w31/references/bellowing_giant.jpg`. Source: nested Bellowing Giant folder, inert
Blender 3.3 SDNA and FBX 7400 arrays; original hashes pinned for every raw file.
Retained .00.001 and .01.000: 18,468 triangles; .02.001 reticle excluded.
BLEND matrices are identity; FBX rotation -90 X and 100 scale convert back to
Blender raw coordinates. Vertex agreement and W30 source/native bounds checked.

114 closed cuboids, 684 independent opaque faces, 0 triangle adapters/cards.
Red thick octagonal launch jacket and filled chamber, deep silver throat, broad
continuous graphite blades, filled long graphite stock, paired grips and open
underarm/stock bridges preserve photo identity. Fine paired vents, topographic
engraving, action fasteners and Armory fork emblem use authored face UV.
The basic red/graphite/olive dye follows the photo, not neutral raw albedo.
Each face owns a separate proportionate island and opaque two-pixel gutter.
Visual revision: replaced the overly red upper plane with a broad continuous
graphite roof and added the photo's silver optic lining, then re-opened the final
comparison. Geometry remains substantial.

Axis caveat discovered in actual data: W30 picks muzzle_sign=+1 only because
world Y max .568299 exceeds abs(min -.564103). Its [X,Z,-Y] mapping therefore
places the photo's front (thicker muzzle beside foregrip at raw -Y) toward +Z.
We reproduce those exact W30 bounds for provenance, then design the functional
muzzle at native -Z using [X,Z,Y]. Original anchor [8.0, 8.0, 8.0] and
scale 23.843122789404013 are unchanged, all complete display contexts copied
exactly. Authored endpoints deliberately match W30 native length bounds; no
model-wide rescale/recenter. This corrects semantic direction, not runtime data.
Parent must verify native muzzle/hand fit in its single session.

Functional sight: offset open octagonal ring at X9.55/Y12.10/Z5.13, eye +Z,
plane XY, forward point Z3.13. Clear ray through the whole assembly toward -Z;
physical red pin tip stops below center. No opaque lens blocks it. Underrail,
trigger bow, separated grips and lower-stock strut have true geometric air.

Comparison includes actual default photo; unmodified old canonical; actual
textured source adapted to functional front; authored side and both quarters;
final bore, grip/bridge, stock and optic closeups. CPU-only diagnostic.
Original full-only generic reload, timing, audio and shared registrations are
untouched. Seven artifacts only; parent owns shared integration and tests.

Limitations: faceted octagons; simplified UV engraving and authored matte dye,
not exact reflective shader reconstruction. Native parser/pack, first/third
person, ADS, generic reload/muzzle alignment, audio and 10-20 display checks
remain parent-owned and unverified here.
