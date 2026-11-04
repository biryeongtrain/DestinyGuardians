# W84 Izanagi's Burden model sidecar

Model-only direct conversion of the user-supplied `izanagi.bbmodel`: 79/256 cubes,
474 original face UVs, 30 original rotated cubes, and all three embedded RGBA
PNGs survive. The 128px lens and both 512px atlases are copied byte-for-byte,
without repainting, combining, resizing or sampling new art. All source parts,
including the two zero-thickness scope lens planes, survive. No silhouette proxy.

`source/izanagi.bbmodel` pins the complete original bytes, including embedded
atlases and source metadata, as explicitly requested. The original in Downloads
is read-only and unchanged. The raw copy retains the author's Windows texture
path strings. Author/asset license was not supplied; this local material does
not grant redistribution rights. The weapon design belongs to Bungie.

## Reproduce / verify (no game/editor needed)

    rtk proxy python3 -B scripts/art/build_izanagi_w84.py
    rtk proxy python3 -B scripts/art/build_izanagi_w84.py --verify
    rtk proxy python3 -B scripts/art/build_izanagi_w84.py --source /Users/qf/Downloads/izanagi.bbmodel --verify

Python standard library only. The default input is the pinned raw copy, falling
back to Downloads for first generation. --verify reconstructs everything in
memory, checks exact output bytes/hashes and unexpected owned paths, and writes
nothing. Source SHA mismatch fails before writes. No absolute machine paths or
timestamps are generated except the explicitly preserved raw source metadata.
manifest.json hashes all other outputs and the self-contained generator plus its
W30/W70/W83 convention references. Those earlier files are read, never edited.

## Native model contract

- ID `izanagis_burden`, family `sniper_rifle`, expected runtime grip `TWO_HAND`.
- `destiny:weapon/izanagis_burden`: CMD string0 selects hip/ads/inspect/scope;
  unknown/missing falls back to hip. Every state has boolean0 native/twohand
  branches. Parent registers the model and sets boolean0 for the default grip.
- `destiny:weapon_aim_w70/izanagis_burden`: first-person W70 float3 range dispatch,
  21 exact thresholds0,.05,...,1, with native/twohand branches in every sample.
  Right/left contexts are both present. Inspect wins over stale positive progress.
  Hip/ads/scope strings otherwise use the sampled HIP-to-optic-ADS path; outside
  first person the original static pose selector applies. At1, ADS/scope coincide.
- All model references are internal to these new W84 assets. There is no new
  weapon_scope_w45 dependency, HUD overlay, audio, Java/data or catalog change.
- Rotations use native26.3 `origin` + scalar `x/y/z` + `rescale`; item display
  rotations remain arrays. Native parser was inspected with read-only javap.
  All from/to coordinates stay within [-16,32]. Zero-thickness planes are allowed
  by the native position parser. Full client codec/bake execution is for parent.

## Fidelity / poses / source issues

The native Java authoring model uses the PROJECT64x64 UV space for every atlas,
not the lens's stale per-texture4x4 metadata. Blockbench installed bundle was
read offline: getUVWidth() selects Project.texture_width when the format does
not enable per_texture_uv_size; java_block does not enable that option. Thus
every face UV is divided by4, even the128px lens's [0,32,20.5,52] rear-art region.
The rear-facing south lens has an opaque red reticle ring and a transparent
central aperture; its opposing north artwork is entirely transparent. This is
original art, not a new optical overlay. Source filenames
iza_512/iza_128 disagree with actual PNG dimensions; PNG headers are authoritative.

The rotated center of source element53 (pistol grip) becomes [8,8,8]. All elements
and pivots receive one uniform5/8 scale and translation, needed to retain the
entire long rifle within native coordinate bounds. Relative shapes, rotations,
and UVs are unchanged. The three source groups have identity transforms.

ADS/scope align the centers of the ACTUAL front/rear lens planes (78/43) on the
central idle camera ray. The muzzle axis is parallel, with the physical scope
height above bore retained (not incorrectly pretending both axes coincide).
Hip solves the original muzzle collar's bore intersection with the camera center
ray four blocks ahead. Both hands use native X/YZ reflection, not guessed mirrored
JSON translation. TWO_HAND applies the inverse idle crossbow carrier; it is not
support-hand IK. Both native and twohand third-person transforms cancel the
complete held-item Rx(-90) Ry(180) base, including crossbow arm pose in TWO_HAND,
preserving upright +Y and muzzle -Z on both hands. Native/fullcodec visual tests,
camera bob, swing/reload, active-use/sprint and arm animation remain unverified.

The existing red reticle ring and transparent lens center provide the real
source-authored scope fallback at full ADS/scope. No claim of magnification,
native zoom-shader behavior, or final gameplay verification.

offline-preview.png: top-left side, top-right three-quarter, bottom-left hip,
bottom-right ADS. Exact multi-atlas software z-buffer with front-face culling,
70-degree square camera for lower panels; center marks are red. No native game
renderer, hand mesh, zoom shader, atlas stitching or animated transforms.
pose-checks.json: independent source/native vertex and UV fidelity, atlas bytes,
both-hand optic center and four-block hip zero, source-space scope-center ray
clearance through all77 solid parts, both-grip carrier inverses,
third-person basis axes, all sample routes and IEEE754 float32 offset handling.
