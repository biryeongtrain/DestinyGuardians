# Ammit AR2 W126 semantic redesign

Implemented in the isolated w126-ammit_ar2 worktree. Reference: original
`/tmp/destiny-weapons-w31/references/ammit_ar2.jpg`, raw Ammit FBX and its
original W30 basis/anchor, original Main/Inner OMOLON glyph meshes. Raw grip
Diffuse was inspected for dot texture and the unpainted magazine Diffuse was
inspected to avoid using it as finished paint. A separate Blender --background --factory-startup --disable-autoexec process
read the original .blend material links only; no GUI or source save was used.
The Inner Omolon Logo quad uses beb2eb80 Diffuse and c0b2eb80 GStack; the
actual letter mask is its GStack blue channel, not its rectangle geometry.

Body 121 + moving magazine 5 = 126
actual emitted opaque cuboids, 756 faces, zero alpha elements,
zero triangle-adapter elements. Full and split are alternative representations.
Even two simultaneously displayed magazines total 131.

The former 960-element component-profile caps/walls are replaced by authored
functional solids. Open upper channel surrounds a faceted teal tube; long
blue/navy fore-end and silver rod retain the real inter-frame gap. Sloped grip,
trigger guard and rear stock surround real air. A physical open peep and
muzzle collar preserve bore depth. The receiver logo is lowered 0.20 units within its new side face to stay clear
of the top chamfer; the original inner mark is visible on the lower receiver
face. Each fluid window has eight solid rim bars,
three filled opaque cores and a backing mount. No whole body side plates.

1024 RGBA face atlas: 756 independent islands with 2px
edge dilation; 432884 face texels. Large continuous faces
use proportional UV; dots, vents, shallow seams and source glyphs use texture.
Main OMOLON strokes come from raw glyph triangles and inner letters from the
original GStack B mask via UV0, independently for both sides;
fluid rings/three-arm pattern are redrawn from the original photo. Paint uses
clean blue alloy/navy/steel/teal/orange, not undyed diffuse RGB or noisy full
surface reprojection. Static opaque fluid does not reproduce PBR/refraction.

`comparison.png` renders unchanged 20,225-triangle FBX versus new textured solids
in matched side/front-quarter/rear-quarter/along-bore views, with original photo.
Raw is explicitly reference recolored. `inspection.bbmodel` embeds the new atlas,
body/magazine groups and face UV. Offline inspection is separate from native QA.

Canonical display copied exactly; W30 scale, world basis, [8,8,8] anchor and
magazine insertion frame retained. Cuboid approximation is an intentional new
shape, not a promise of old W124 geometry hash equality. Shared packs, Java,
helpers, animation graphs, source assets and sealed historical QA are unchanged.

Master TODO: pack substitution and native parsing; first/third person + ADS,
inspect and twohand; detached magazine and re-insertion through existing reload
coordinates; 10-20 simultaneous display observations. Reverse-side original paint
and true source first-person references remain unavailable in the supplied photo.
