# Dust Rock Blues W128

97 actual emitted solid cuboids, 582 explicit face UVs, 0 triangle adapters,
0 alpha silhouette elements. Functional groups: {"shroud": 12, "receiver": 7, "stock": 7, "grip": 6, "trigger": 2, "butt": 5, "foreend": 21, "muzzle": 25, "lamp": 6, "sights": 6}.
One full model only. No body/magazine files, animation graph, Java, sound or
timing edits. Existing generic graph/ADS inheritance remains master-owned.

Photo: https://www.bungie.net/common/destiny2_content/screenshots/636912560.jpg
The actual local W31 photo, raw undyed DRBFrame_Diffuse, DRBDecals and binary FBX
were inspected. W31 records default dyes 449377312/313/314, no palette override.
The red long shroud, ivory stock/grip, red butt, silver six-rib fore-end and dark
inserts follow that photo. Diffuse alone is not the finished paint.

Broad deep volumes replace the 235-element W30 voxel model. Shroud crown,
lower nose drop, ivory comb/heel and swept grip define silhouette. Six metal
wrap ribs have physical depth and channels. Muzzle lip + bore walls enclose a
real opening to a recessed backstop; twin sight ears leave an open notch.
The source has an exposed trigger: no guard or stock window was invented.
Panel lines, restricted edge chips, 90/triple wedges, stock perforation grids,
rubber ribs and sleeve grooves are authored into continuous face islands.
1024 RGBA atlas, 582 unique face rectangles, 2-pixel edge dilation.

Exact W30 carrier [8,8,8], scale 27.595219964806475, -Z muzzle and canonical display
are retained. FBX translation was applied before axis conversion and source
bounds match W30 within 1e-5. Grip is authored in the original contact region;
no recenter, axis swap, or display adjustment was applied to fit the new art.
Inspection bbmodel embeds the atlas and full-model semantic groups with neutral
group transforms. Source meshes remain read-only comparison references.

comparison.png includes the actual reference photo and four matched-camera
source/new pairs: side, front oblique, rear oblique, and bore depth. Source FBX
triangles are unchanged; source colors are clearly schematic, not shader proof.

Limits: compound curves are faceted; some small relief is UV; reverse markings
are inferred from the source; no PBR/dynamic lamp. Native parser/resource pack,
held first/third-person, ADS/inspect, generic reload, and 10-20 simultaneous
displays remain pending master. Offline render is not native acceptance.
