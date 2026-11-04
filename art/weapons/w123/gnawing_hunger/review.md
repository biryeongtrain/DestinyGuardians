# Gnawing Hunger W128 art review

114 emitted opaque cuboids / 684 faces; FULL ONLY, no reload split.
Semantic groups: {"barrel": 3, "bindings": 13, "cage": 8, "collar": 4, "foreend": 28, "grip": 6, "magazine": 5, "muzzle": 9, "optic": 11, "receiver": 10, "stock": 12, "trigger": 5}. Maximum assembled 1000.

Long receiver, true solid curved magazine and grip, skeleton stock with two air
windows, offset protective cage and round sight are authored from broad volumes.
The long muzzle is eight continuous tangent staves surrounding a deep bore with a
recessed backstop. There are real gaps in the stock, trigger guard and sight, and
clearance under the lateral cage. Per-face UV uses independent aspect-proportional
islands and two-pixel bleed. No source mesh conversion, connected-island fitting,
alpha body plates, opaque silhouette box, or source triangles are emitted.

Default paint comes from the supplied W31 photo / reference 821154603: charcoal
steel and stock, warm-white mottled binding and brown brass twin fore-end rows.
W31 has no palette override for this weapon. Body_Diffuse provides an actual
cloth-pattern crop; Barrel_Diffuse supplies the actual quatrefoil stencil. These
are repainted/repacked on deliberate face islands, not treated as finished dyes.
Tiny floral perforations are opaque painted ornament on panels set .25 units
behind the broad brass frame. The recess is physical; individual petals are not
through holes. No invented lettering, alternate shader palette or decorative
screw geometry. Small fasteners and pressed channels are face artwork.

The original [8,8,8] carrier, scale 25.30395118440936, (X,Z,Y) source mapping,
-Z muzzle, hand-contact region and all canonical display transforms are preserved.
No canonical JSON, historical W30/W31, gameplay, sounds, timing, shared manifest,
Java, graphs or ADS are changed. Generic graphs / ADS can inherit this full
replacement through master's integration. The magazine group has no invented
moving split; inspection groups organize art only.

comparison.png contains actual raw FBX (undyed), unchanged canonical W31 paint,
and new output at a matched side camera and two oblique cameras, plus independent
muzzle/sight/stock/fore-end depth close-ups. It embeds the actual default photo.
The generated PNG must be inspected via view_image; offline raster does not prove
native acceptance. inspection.bbmodel embeds the complete new opaque atlas.

Limitations: Faceted solid reinterpretation; rounded cloth folds and compound bends simplified. Quatrefoil microperforations are opaque artwork on physically recessed panels; not individual through holes. White binding uses actual diffuse cloth crop; shader reflections and exact folds are not recreated. Single supplied default photo establishes paint; opposite side conservatively follows source diffuse. Offline Python inspection only; native pack/parser, first/third person, ADS, generic reload and 10-20 displays pending master.
