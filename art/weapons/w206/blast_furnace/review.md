# Blast Furnace — W206 first-person calibration

The W205 pulse family uses HIP translation `[-0.65,0.6,0]`, rotation `[-1,2,0]`, scale `0.98`. It has no forward camera-space displacement. Its non-bow rig path also replaces the remodeled foregrip contact with source wrist separation at idle/ADS. This conflicts with treating the remodeled weapon and ordinary fingerless skin forearms as one assembly: preserve the actual grip, then use source elbow/wrist direction, twist and length. No current W206 native image was produced here.

The exact associated rig is `art/weapons/w205/rigs/pulse_rifle_b4d01502.json`, explicit `blast_furnace` membership and `fallback=false`, idle `80A8A422`, ADS `80A8A330`. It supplies evaluated joints; `cameraExported=false`. All presentation values below are **authored calibration**, not a recovered Destiny camera. The initial idle elbow-to-wrist length is approximately 8.1414 model units on either arm under the existing ×32 conversion; no length multiplier or continuation geometry is added.

## Concrete configuration

- HIP translation becomes `[-0.85,0.35,6.0]`: +6 model units in Z brings gun, moving parts and contact frames toward the camera. The additional inward X shift is small; Y rises less than the family default to keep the broad bullpup stock from becoming the framing focus. These are provisional composition choices, not measured screen-to-model recovery.
- HIP rotation `[-1,2,0]` and scale `0.98` retain the existing pulse calibration. Translation/rotation/scale fade to identity at full ADS. `cameraDepth` is omitted so the accepted full-ADS weapon matrices remain unchanged.
- `sourceViewRotation:[12,0,0]` modestly pitches the source arm approach downward toward the viewport edge. It changes arm direction, not gun geometry/camera or forearm length. Both idle and ADS clearance need native review.
- `keepMeshSupport:true` preserves the remodeled lower-foregrip contact in idle/ADS rather than copying source wrist separation. Direction/twist/length still come from the exact rig. `hideSupportAtRest:false` retains the pulse rifle's support arm. Integration depends on the master's W206 loader and keepMeshSupport implementation.
- `rightWristRoll:28` and `leftRotation:[15,35,-35]` explicitly retain family fallbacks; exact rig orientation takes priority.
- `contacts:{}` inherits W201 unchanged: trigger palm `[8,8.4,8.27]`, foregrip `[7.8,9.45,-0.5]`, reload `[7.4,8,11.78]`, reload rotation `[-8,0,0]`, magazine policy/part hint. The rear magazine contact is behind the trigger grip; it must not move to the front foregrip. No mesh evidence warranted changing these positions.

## References inspected

Repository paths below are relative to `/Users/qf/IdeaProjects/DestinyGuardians`; the private seeded worktree contains product inputs. The historical W152 native PNGs remain in the read-only main QA archive and are recorded with absolute paths in profile.json because those screenshots were excluded from the seed.

- `art/weapons/w123/blast_furnace/comparison.png` — actual PNG opened, original/reference recolor and remodeled side/oblique views. Mesh identity is the long black/graphite receiver, red barrel/breech, subdued olive lower receiver, open stock window, lower foregrip and rear box magazine. Photo/raw recolor is not first-person camera evidence.
- [KackisHD, Blast Furnace gameplay](https://www.youtube.com/watch?v=SRNv0YDgYBM): actual `art/weapons/w114/blast_furnace/reference-00.png` (38.70s ADS) and `reference-09.png` (40.05s magazine seating) opened. `gameplay-provenance.json` supplies frame seeks and hashes. BRAVE reissue/shader differs; use handling/optic visibility only, not its appearance or exact bone/camera values.
- `reference-15.png` was also opened; the late recovery/ability-adjacent view has strong occlusion and is excluded as a settled idle target. The available clip could not be decoded into additional stills because ffmpeg is unavailable; no new settled-hip evidence is claimed.
- `docs/qa/2026-10-26/w152/native/frames/blast-hip-after.png` and `w152-blast-ads-sample-13.png` — actual historical native PNGs opened. HIP establishes the long receiver's right/bottom framing, but predates skin arms. Full ADS shows the upper optic aperture and red front tip clear above the stock. `w152-blast-ads-sample-30.png` is recovery/HIP and is not used as the ADS target.
- `docs/qa/2026-10-26/w152/README.md`, `scripts/generate_sight_bodies_w151_pulse.py` — retain restored Optic parts, existing ADS anchor `[8,14.73,8.065]`, eye relief `0.32`, and uncut stock. W206 does not replace that correction.
- `art/weapons/w201/contacts.json`, `art/weapons/w123/blast_furnace/design.json`, `scripts/rig_arms_w205.py`, `scripts/first_person_framing_w205.py`, `scripts/build_first_person_hands_w201.py`, `scripts/skin_arm_models_w204.py` — read for mesh contact, reload routing, arm retargeting and HIP/ADS behavior. The weapon-art skill and its Ace/Izanagi study were read; this pass adds no surface elements.

## Geometry and integrity

Canonical assembly remains **92 body + 5 magazine = 97 opaque cuboids**, no triangle expansion. Existing ADS sight body is **99 cubes** including its two front-sight elements. Full and split assembly are alternative representations, not summed twice. No elements/UV/textures or stock/sight geometry are edited; two classic skin arms use the existing 112 elements each (97+224=321, or 99+224=323 for the sight assembly).

Checks performed: profile JSON parses with schemaVersion 1, weapon identity and supported finite framing values; every evidence path resolves in the seeded worktree or the explicitly recorded read-only main QA archive. Seeded rig/contacts/canonical full/body/magazine hashes match the read-only inputs; canonical full equals body plus magazine. Only the two owned W206 files are written after private worktree status is ready. No generator, build, game, server, live DCC, CU or Vision run was performed. Source checks do not establish native visual acceptance.

## Pending consolidated master native checklist

- HIP, classic and slim skin: weapon/parts/palms move together; right palm stays on trigger grip, support palm under lower foregrip; both ordinary forearms continue into viewport edge or natural occlusion. Check near clipping at +6 Z, no floating elbow end, no elongated or doubled arm, correct skin/sleeve tint.
- HIP to ADS and back: smooth fade of HIP transform, no support-contact jump at either endpoint; check intermediate hand/receiver clearance and mirrored first-person contexts.
- Full ADS: compare W152 sample13; upper aperture and red front tip remain visible, stock stays below the sight, palms do not enter the opening. Accepted weapon matrix/anchor/eye relief must remain unchanged; arm pitch is separately provisional.
- Reload: support leaves foregrip, handles the rear bullpup magazine during extraction/reseat, releases before recovery and returns to foregrip. Check both magazine contact and hand occlusion throughout the muzzle-up turn; no hand snapping to forward magazine location. Check interruption/ADS return using the existing route.
- Representative third-person/inspect and split parts retain their accepted geometry/poses. Master owns consolidated native verification; this worker claims no native pass or final visual acceptance.
