# W207 Dust Rock Blues — actual one-shell presentation generator

## Change

Human feedback is correct: `WeaponInsertPresentation.supports` only supported
Long Arm, First In Last Out and Mindbender at inspection time. The W206 hip
profile alone could not supply Dust Rock Blues reload animation.

`scripts/generate_insert_w207_dust_rock_blues.py` now implements
`generate() -> dict[absolute Path, bytes]`, with standard-library dependencies
only. Import and generation write no files. Master writes the returned mapping
and owns Java support, model routing, 60-interval quantization and shared skin
hand phase selectors. No generated assets were written by this worker.

Item route: `destiny:weapon_insert_w207_dust_rock_blues/dust_rock_blues`.
Generated asset names live exclusively under that new namespace, plus
`art/weapons/w207/dust_rock_blues/manifest.json`.

- CMD float 4: initial `0..1`, repeat `2..3`, cosmetic return `4..5`.
- 61 poses per phase, `i/60`; flag 0 selects accepted native/twohand transforms.
- 732 display children, 3 geometry parents (body, shell, empty hidden shell),
  1 item and 1 manifest: **737 generated outputs**, all JSON.
- **97 unchanged body cuboids + 12 shell cuboids = 109**. Including both
  112-face classic arms: **333**, below the 1,000 limit. No new arm/finger
  geometry, stretched arms, textures or surface edits.

## Motion and contacts

The source W123 geometry and complete face UVs remain intact, including long
red shroud, ivory stock/grip, silver six-rib pump, lamp, muzzle and open sight.
Body parent copies the current 97 elements. Inputs are read live; the manifest
records current hashes rather than enforcing unrelated historical pins.

The body lifts/rolls once over the first 30% of initial, then stays held through
repeated inserts. Held local rotation `[22,-6,-32]` degrees and local translation
`[-0.2,0.65,0.15]` model units expose the receiver underside. All motion rotates
rigidly around the existing right-grip contact `[8,7.9,11.42]`, then applies the
accepted native or twohand transform and its scale exactly once. A small smooth
periodic held response accompanies insertion; repeated loops never reset to hip.
The six-tick return remains cosmetic and returns to the exact accepted idle.
W206 framing is intentionally left to the shared pipeline once, not baked twice.

The shell geometry is centered around W201 loading-port contact
`[7.3,9.15,7.1]`, with longitudinal Z axis. Its display moves that exact contact,
so master can attach the left skin-hand contact using the same display.
Pickup offset `[-1.1,-2.4,1.35]` brings the shell from below/left. It approaches
beneath the floor, then moves to seated offset `[0.7,0.45,-0.55]`. The offset in X
centers it inside the receiver even though the W201 hand landmark is on its
left edge. The fixed `loading_port`/`shell` policy and idle pump contact
`[7.8,8.52,0.7]` remain unchanged.

Cubic Hermite interpolation carries nonzero shared tangents through the bring
and approach knots; it does not ease to zero at every intermediate key.
Prepare/return use one quintic span each; the held response is periodic.
Initial-end = loop-start = loop-end = return-start for both body and shell
transforms, with zero seam velocity. The shell recycles below the receiver
while hidden at the end of each insert. It is visible at full size during the
approach, then switches to an empty parent after seating. Its display **keeps
ordinary scale even while hidden**, so shared skin hands do not disappear or
shrink when following the shell. Return shell geometry stays empty throughout.

The shell uses Dust's own red shroud texel for case and silver pump texel for
head/rim, in 12 connected octagonal-section solids. This is an authored prop,
not a claim about recovered ammunition materials or extracted animation.

ADS/inspect and all non-firstperson contexts select the exact existing canonical
item graph. Initial body pose 0 and final return body pose 60 use byte-equivalent
accepted display records for native/twohand. Weapon geometry, ADS/scope geometry,
third-person, audio and actual per-shell ammunition timings remain unchanged.

## References actually inspected

- `art/weapons/w123/dust_rock_blues/comparison.png`: actual reference photo and
  source/remodel side, oblique and bore PNG comparisons. Default-paint source:
  https://www.bungie.net/common/destiny2_content/screenshots/636912560.jpg
- `art/weapons/w178/first_in_last_out/reference-06.png`: actual esbeekay
  First In, Last Out gameplay at 27.6667s; raised/canted shotgun and underside
  shell handling. Video https://www.youtube.com/watch?v=5IZfs2bjrYY and local
  provenance `art/weapons/w178/first_in_last_out/motion-reference.json`.
  This is a related shotgun, not Dust Rock Blues. It supports the held gesture
  and shell-by-shell handling only. Exact Dust path, camera and timings remain
  authored; no source camera or finger IK is recovered.
- Read both `generate_insert_w178_first_in_last_out.py` and
  `generate_insert_w179_mindbender_s_ambition_adept.py` as interface/rigid-matrix
  patterns. Their unrelated surfaces, historical pins, 21-pose sampling,
  stop-at-every-key interpolation and preview/audit machinery were not copied.
- Read W201 contacts and W123 design/model for `Loading_floor`,
  `Loading_housing`, grip and pump. The existing housing remains solid;
  insertion disappears into it without cutting a new chamber.

## Checks completed in memory

The new generator ran successfully without writing assets. All returned JSON
parsed; output paths are absolute and restricted to the new namespace/manifest;
repeated generation produced identical bytes. Held phase joins matched exactly,
accepted initial/return idle displays matched exactly in both grips, and body
elements/UVs matched the input. The 183 item thresholds are strictly ordered;
canonical ADS/inspect/non-firstperson fallback graphs matched their input.

One-sided velocity checks at authored spline knots and phase ends confirmed
C1 continuity and nonzero moving tangents. All pose scales/transforms remained
finite; hidden shells kept normal hand-compatible scale. At approach, shell top
Y `8.89` is below loading-floor underside Y `9.18` (0.29 model-unit clearance).
The seated shell bounds `[7.74,9.34,5.87]..[8.26,9.86,7.23]` lie inside the existing
`Loading_housing` bounds `[7.29,9.305,4.63]..[8.71,10.035,9.35]` before visibility
ends. These are source-space checks, not native screen/skin-hand acceptance.

## Pending master integration/native verification

- Add Dust support/model route and interval 60 for Dust only; regenerate the new
  assets and shared skin-hand selectors with initial idle->shell, loop following
  normal shell display, return shell->idle. Existing ammo accounting remains
  authoritative; no per-shell timing or six-tick return policy change here.
- Native hip -> initial -> several paid shell loops -> return in native/twohand
  and both supported first-person contexts: no repeated lift, endpoint snap,
  visible hidden recycle, floating palm, pump/receiver penetration or shrunken arm.
- Check underside contact and visibility with player skin at working FOV; shell
  may be naturally occluded by left palm. Near-camera clipping and the authored
  cant/path need actual PNG review; source bounds cannot establish screen quality.
- Interrupt after a paid shell, cancel/restart, reserve exhaustion/full magazine,
  fire during cosmetic return, ADS/inspect/equip/swap restoration. Keep accepted
  ADS sight alignment and third-person presentation.

No build, global generator, server, CU, Vision, DCC or child agent was used.
No native verification is claimed. Only the two assigned source/review files
were written after metadata confirmed `refreshRevision=W207`, `status=ready`.
