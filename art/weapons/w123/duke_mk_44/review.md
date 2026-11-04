# Duke Mk.44 W127 implemented art

147 actual emitted solid cuboids = 78 fixed body +
69 moving cylinder/yoke. Full is exactly body+cylinder, alternative
representations counted once. All 882 faces have independent opaque
UV islands. Zero alpha side plates, triangle adapters, arbitrary meshes or source
component extrusion. Atlas: 1024 RGBA, 882 face islands,
306301 face texels, 2px dilation.

The tall stepped shroud is made from broad solid volumes with a raked nose and
continuous top strap. Muzzle, front housing aperture, underbarrel lug, trigger
guard, rear notch and hammer loop have real air/depth. The grip curves through
three solid grip masses and a separate dark backstrap/heel. Metal panel seams,
two shallow barrel vents, grip grain/checkering, fasteners and cylinder flutes
belong to UV. Fine original bevels are simplified.

The twelve exterior cylinder staves surround six full-length octagonal chamber
tubes, six solid inter-chamber webs and a spindle. Both end faces show six actual
empty drilled bores; no painted black chamber dots or alpha cap. Outer facets
carry the blue lacquer; inside bores are dark steel. Two reauthored W64 yoke
links remain in the moving group with the original lower pivot attachment and
Z frame. The vertical link's top is shortened from Y=12.25 to 11.72; the arm is
lowered from Y=12.05..12.45 to 11.50..11.80 to meet the new shell below the bottom
chamber. This shape adjustment keeps all six bores open without changing pivot.

Coordinate mapping is [8-source.Y*s, 8+source.Z*s, 8-source.X*s], s =
40.55098717904924. Length/muzzle -Z, thickness X, up Y. Original [8,8,8]
anchor, held frame and canonical display are preserved; parts have no display.
Cylinder is not recentered. The W64 swing pivot remains [8,10.2,5.17]. No reload
timings, wrappers, animation graphs or shared manifests are edited.

Historical reconciliation: canonical 232; W64 211 body + 21 original cylinder +
2 added yoke = 234. This is an existing reload feature delta. New canonical full
deliberately includes the new yoke and equals its own body+cylinder, so the shared
migration has one coherent assembly. It does not pretend 232 equals 234.

Source evidence actually inspected: supplied /tmp/destiny-weapons-w31/references/
duke_mk_44.jpg (blue exterior/black grip variant), extracted neutral barrel/cylinder
diffuse sheets, original 7,960-triangle FBX in the W30 coordinate mapping.

Paint evidence correction: `art/weapons/w31/palette-overrides.json` explicitly
sets Duke barrel/cylinder dye to linear [0.12,0.22,0.65,1] for blue lacquer and
[0.012,0.015,0.022,1] for dark steel. `art/weapons/w31/references.json` identifies
the blue/black screenshot for item 2112909414 (SHA-256
6b0aafe4f3abda9cacc7eee0a0f8106218813c0a427ab02b6fae3f8c1c572067).
The existing W30 Duke atlas was also viewed and is visibly blue/dark. The master
rejected the initial unsupported yellow/wood alternate and repainted the actual
final atlas blue/dark to match this evidence. Legacy material keys in the
source generator remain for stable geometry/UV identifiers, not as color claims.
Neutral raw diffuse cannot establish finished RGB; reverse-side markings and
dynamic PBR are not recovered. No invented lettering was added.

comparison.png shows the original photo, unchanged reference-recolored raw FBX
beside new face-textured solids in side, front/rear oblique and bore-axis views,
plus detached cylinder end/oblique details. inspection.bbmodel embeds the atlas,
body/cylinder groups and original group pivot. The renderer is a CPU rasterizer;
these images are not native gameplay screenshots and do not certify performance.

Master native follow-up: migrate the three model references; pack/parser check;
representative first/third person, ADS and twohand; swing-out W64 reload and return
to full; 10-20 simultaneous display observation. No GUI, client, Blender process,
Gradle or native inputs were used by this worker.
