# Patron of Lost Causes W130 art review

Reference: actual Bungie default photo `/tmp/destiny-weapons-w31/references/patron_of_lost_causes.jpg`, item 2723241847, sha256
`b1c9fea350e996789524e696854159f1e4a32bebe42389efe34cc03f50a43873`; W31 references.json entry verified.
Photo and raw neutral 46a6eb80_Diffuse.png actually opened with view_image.
The default has a long silver upper shell and silver optic, black lower and triangular
stock around a large aperture, exposed gold barrel and internal tube, small gold XIV,
and the forward underside curved hook. No alternate ornament or foreign identity.
The neutral diffuse is structural evidence, not finished default dye.

98 emitted filled solid cuboids, 588 individually authored face UV rectangles,
0 triangle adapters, 0 alpha body/contour elements. One full resource only.
Long opaque casing, receiver, grip, forearm, magazine and stock volumes carry clean
broad panels. Octagonal barrel and optic walls are actual thick solids around bores;
stock, trigger guard, ejection port and scope saddle contain physical air.
Scope glass is recessed inside both ends; the muzzle has a backstop 1.31 units behind
its tip. Vents, fasteners, ribs, seams and the small photo-side XIV use face paint.
No connected-component conversion, source polygon transplant, voxel transplant or
flat silhouette panels. Functional barrel/optic cross sections justify the tube walls.

Frame: [8+raw.X*s,8+raw.Z*s,8+raw.Y*s]; muzzle -Z, width X, up Y. Source scale 23.684066163425207, anchor [8,8,8].
All existing canonical full display transforms copied verbatim; original hand-region
and muzzle axis retained without recenter or rescale. Grip follows original wrist region.
Full only: existing ADS, generic reload graph, timing, sounds and registries unchanged.
Native substitution and master GUI integration have not run.

1024 RGBA atlas, aspect-proportional independent face islands, 2-pixel edge dilation.
Every face samples opaque texels. XIV only on the photo-evidenced side with its own UV.
Editable inspection.bbmodel embeds exact final solids, rotations, face UV and texture,
semantic groups with [8,8,8] origins and canonical display. No app was opened.

comparison.png includes the actual default photo plus clearly labeled, unchanged
canonical W30 full (241 cuboids) and existing W30 texture next to the new full model,
at matched side, front/rear oblique and axial depth cameras. Canonical is not the raw
FBX and neither comparison column is native evidence. Raw FBX was parsed read-only;
its source object set, original 29,158 triangles, scale and bounds are verified.
Read-only Beloved parser/vertices/raster and Halfdan UV packing/editable export
infrastructure are reused; this weapon's geometry and paint are authored here.

Practical limitations: faceted circular cross sections, simplified hook curve and local
wear; shallow vents/ribs/fasteners are painted. Opaque lens shading approximates albedo,
not refractive/PBR optics. Opposite-side decal detail is deliberately restrained.
Master still owns model-parser/pack loading, first/third-person hand contact, ADS
visibility, generic reload seating/timing/audio, ground/GUI placement and a brief
10-20 displayed-weapon observation. No native success or performance claim.
