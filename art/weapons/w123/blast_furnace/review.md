# Blast Furnace W127 semantic art

Original reference photo: `/tmp/destiny-weapons-w31/references/blast_furnace.jpg`.
Original FBX: `/tmp/destiny-weapons-w30/raw/blast_furnace/extracted/Blast Furnace/Blast Furnace.fbx`; original undyed BFFrame Diffuse inspected for panel
structure, vents, well stamp and magazine ribs. Paint rebuilt as Black Armory
black/graphite, red barrel+breech, subdued olive lower receiver and silver muzzle.
W115 highpatch artwork is reference only, not used as new design geometry.
Read-only shared helpers provide FBX parsing and offline cuboid rasterization.
No Blender process, game, GUI or native input used.

92 body + 5 moving magazine = 97
actual emitted opaque cuboids (582 explicit faces), no alpha shells,
no triangle-adapter expansion. Full is exactly body+magazine. Canonical 249 equals
W114 237+12; no canonical/reload delta. New geometry intentionally differs.

Large solid receiver, long fore-end roof with actual bilateral red-barrel slots,
red breech/metal lock, open stock window with inset rod, broad upper cheek pad,
sloped foregrip/grip and open trigger guard replace source-component patchwork.
Muzzle octagonal rim and bore walls retain about 0.6 model units of open depth
before the solid nose; original paired optic bases and hood retain an air aperture.
Clean continuous per-face islands carry panel seams, twin four-vent rows, lower
grid, fabric, well stamping, breech recesses, magazine channels and diagonal line.
582 independent islands, 407494 texels,
1024 RGBA, 2px edge dilation. Every emitted face samples fully opaque texels.

Canonical display is copied verbatim. X thin / -Z muzzle / Y up, source scale
30.010419887180735 and [8,8,8] carrier preserved. Magazine is never recentered.
Its exposed carrier occupies the W114 insertion envelope. Upper well collar stays
fixed; this retains W114 semantics rather than claiming a new perfect source-bone
partition. Independent bbmodel groups retain [8,8,8] origins and zero group rotation.

`comparison.png`: original photo + unchanged raw FBX reference recolor and new
textured geometry at matched side/front-quarter/rear-quarter/along-bore cameras.
Raw recolor is schematic region color, not recovered shader/paint evidence. Actual
photo establishes paint. `inspection.bbmodel` embeds UV/texture and split groups.

Known limits: faceted contours and small compound curves are approximations;
reverse-side markings inferred from grayscale source. No dynamic PBR/optical
refraction. Offline inspection only; master must verify native parsing/substitution,
first/third-person, ADS/inspect, twohand reload/seat, and 10-20 displays. No native
success, exact source silhouette match or performance acceptance is claimed.
