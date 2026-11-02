# Korean objective HUD — 2026-11-02

## Scope and provenance

Continues chat `01a19b63-965e-76c1-a2e2-f10aa1e80b2c` and its unfinished W303 objective tracker.
Source: `/Users/qf/Downloads/Rising-Guardian-Objective-HUD-KO-2026-11-02` (read-only).
All 41 source manifest hashes checked. Header, guide, checkbox and badge copied byte-for-byte.
The supplied README identifies badge and OTF fonts as original extraction; bar tint/alpha,
placement, guide and checkbox are video-derived reconstructions. No claim of exact Destiny runtime
animation, perspective or color matching. Original font licenses and evidence are in `art/hud/objective-ko/source`.

## Implementation

- Source layout: 512×116; left edge anchored at x=0, top=220 in 1920×1080 reference pixels.
- Title (116,15), body (116,65), 60px badge (48,0), 12px checkbox (73,66).
- Noto Sans KR Bold/Medium rasterized at 20px into bitmap font pages; all 11,172 modern Korean
  syllables plus Latin/jamo/punctuation. Exact bitmap advances replace estimated Korean/ASCII widths.
- Body wraps to 380px. Progress and native key labels extend below the reference card.
  Long key combinations move their action to another row. Keycap and completed check are Minecraft adaptations.
- Existing mission data, subtitle lane, hidden-state cleanup and stage transitions retained.
- UI displays render above the first-person hand. No per-tick font rasterization or image transfer.

## Verification

- Targeted campaign tests before final adjustments: 134 passed; Gradle compilation successful.
- `assets-validation.json`: 22,726 bitmap glyph advances checked against pixel bounds; four layer hashes identical.
- First Vision PNG exposed text baseline ~10 reference pixels too low and weak key contrast on sky;
  corrected baseline, shadow and dark keycap before second pass.
- Full regression run: 2,454 tests, 2,448 passed, 6 failed (0 errors/skips). New font tests passed.
  The six failures target files untouched by this HUD change: GoldenGunHudW122AssetTest (2),
  WeaponSilhouetteW112AssetTest, InsertW179MindbenderTest, ReloadW168AustringerTest,
  WeaponSurfaceW115Test. The complete build did **not** pass. See `full-test-result.json` and `full-build.txt`.
  A pre-HUD full run was not performed, so these are out-of-scope failures, not a proven clean-baseline comparison.
- Second Vision pass: aligned title/body; progress changed 0% to 4% after one fixture enemy was killed
  by RCON (not proof of a native gameplay kill). Source uses total encounter count, not only the current wave.
  Long-key action wrapped its final syllable alone; fixed by measuring the entire action before choosing
  same-row/below-key layout and preferring word boundaries for wrapping.
- Native right input sequence completed and released. `native-neutral.json` confirms no lease,
  no held keys/pending steps, and neutral native movement. It does not establish combat correctness.
- Actual framebuffer size: 2560×1440. HUD visible throughout; no normalized-view capture used.
- No speaker listening, complete campaign playthrough, multi-resolution certification or sustained FPS benchmark.
  FPS fields are snapshots only. Existing `destiny:profile_arm` missing-texture warning is recorded for follow-up.

## QA isolation

Reused the linked chat's isolated `/private/tmp/destiny-w300-server` and
`/private/tmp/destiny-w300-vision/run`, not a personal Minecraft profile/world.
Server loopback 25600, RCON 25602, Vision 8102. Background QA was explicitly authorized in the linked chat.
The CU preflight reported locked; user said unlocked. Live Vision framebuffer subsequently rendered normally.
Bounded master awake wrapper (3 hours, caffeinate PID 63837) covers rebuild/restart gaps; owns only this assertion.

## Final acceptance

- Final targeted campaign/HUD tests: **137 passed**, including three new typography tests.
- `./gradlew test --tests 'kim.biryeong.destiny.campaign.*' jar` completed successfully.
  This is a real Gradle JAR, not the historical fallback package. The complete test suite still has
  the six out-of-scope failures above; do not label the entire project green.
- Final runtime served pack: 99 font/texture/metric files matched source bytes. Polymer transforms
  model JSON, so raw model byte equality is not asserted for the served pack.
- `final-long-key.png`: full action stays on one line below the long binding; no lone final syllable,
  no key/label overlap, title/body share the same x=116 reference edge.
- `final-gateway.png`: short movement binding shares a row; visible against bright sky; progress row
  from the previous combat stage is removed. Source badge and source guide remain at their supplied offsets.
- `final-cleared.png`: tracker removed after campaign abort; server reports zero campaign sessions.
- `preview.png` is an unscaled crop of `final-long-key.png`, not a mockup.
- Final neutral state saved before shutdown. Owned server/client sessions ended, ports released,
  and only the owned caffeinate assertion was released (`cleanup.json`).

Only the objective renderer, typography, imported assets, importer, tests and this QA evidence are
included in this change. The checkout already contains extensive uncommitted campaign, weapon and other
work; those unrelated paths remain unchanged by this task. See `BUGS.md` for the next repair batch.
