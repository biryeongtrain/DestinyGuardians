# W350 energy models revision 2 — offline candidate

User rejected the initial R1 rectangular drafts. Those proof images and manifests remain in each weapon rejected-r1 folder. R2 source-proportioned closed lofts/profiles replace them, using the accepted W327 group3_v3 semantic authoring and group3_optimize native polygon union. No source mesh vertices are exported.

| Weapon | Body | Moving assembly | Total native elements | Atlas |
|---|---:|---:|---:|---|
| Sunshot |384|101|485|1024 x 1024|
| Graviton Lance |563|14|577|2048 x 2048|
| Jotunn |815|17|832|2048 x 2048|

Sunshot now has continuous crowned blade jaws, continuous web around actual diamond holes, a rounded independent cylinder/crane, stepped dark receiver shoulder, inset panels, source etching and sculpted ivory grip. Master review identified disconnected initial vent capsules and noisy gold; both were corrected. Diamond-center rays miss all authored solids, while the connecting web ray intersects twice. Graviton has a deep open muzzle, long faceted bore, real U conductor and stock aperture, finger-shaped grip and sloped magazine. Jotunn has a deep hollow furnace, compound swept cheek, closed continuous faceted protective pipes, cable cutaway and retained source Armory mark.

Actual exported native JSON + PNG were rendered from side, oblique, opposing obliques, top and muzzle. Each r2/source_vs_native.png compares source neutral .blend proof to native material. Owned renderer follows accepted W327 practice: omit the coincident reverse plane only in Blender, keep both mirrored faces in the runtime model. Cycles avoids EEVEE duplicate-plane/shadow artifacts. Source diffuse does not establish canonical finish; pinned Bungie base icons and role palettes guide materials.

Read-only source SHA remains unchanged for all three .blend files. Sources have no weapon/player reload actions: Sunshot actions empty, Graviton action is UV-only, Jotunn shader-node channels only. All 61 reload and 21 aim samples are authored approximations, with revised geometry-relative grip/sight/moving-part anchors. No source wrist/elbow animation or continuous 60fps playback is claimed.

Validation: standard native fields, unique names, native bounds and UVs, full==body+mag, source hashes, 61 endpoint restoration, 555 parsed JSON files and 1429 resolved model references per weapon pass. Scripts: energy_r2.py build/render; energy_r2_validate.py. Source 6-view albedo/depth projection was refreshed read-only at 2000–2200 px/metre.

No client/server/CU, build, shared Java, shared registries or sounds were touched. No commit/push. Master first Vision -> delegated fixes/review -> second Vision remains mandatory. Actual pack load, grip/ADS/third person/reload contact, firing and 10–20 item observation are unverified. Element count and offline art checks are not art acceptance or native performance results.
