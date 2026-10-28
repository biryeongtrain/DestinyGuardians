# W223 HUD worker return — first implementation, awaiting native feedback

Slot: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`.
Exact ownership: feature0 in `/private/tmp/destiny-w223-source/worktrees.json`.
All 13 owned files were absent before this worker's changes. No shared runtime, registries,
options, existing QA, build outputs, main checkout, commit, or push was changed by this worker.
No Gradle, Minecraft, Vision, OS/window input or lease controls were run here.

## Changed paths (all owned)

- `src/main/java/kim/biryeong/destiny/hud/WeaponHitState.java`
- `src/main/java/kim/biryeong/destiny/hud/WeaponHitHud.java`
- `src/test/java/kim/biryeong/destiny/hud/WeaponHitStateW223Test.java`
- `scripts/generate_hit_confirmation_w223.py`
- `art/hud/w223/SOURCE.md`
- `art/hud/w223/manifest.json`
- `docs/qa/2026-10-28/w223/worker-hud.md`
- `src/main/resources/assets/destiny/items/gui/hud/hit_confirmation_w223.json`
- `src/main/resources/assets/destiny/models/gui/hud/hit_confirmation_w223.json`
- `src/main/resources/assets/destiny/textures/item/hud/hit_confirmation_w223.png`
- `src/main/resources/assets/destiny/items/gui/hud/kill_confirmation_w223.json`
- `src/main/resources/assets/destiny/models/gui/hud/kill_confirmation_w223.json`
- `src/main/resources/assets/destiny/textures/item/hud/kill_confirmation_w223.png`

## API integration (master-owned)

`WeaponHitHud.confirm(ServerPlayer owner, float observedPositiveDamage, boolean killed)`:
call once per authoritative actual positive HP+absorption-loss transaction after damage resolves.
In `WeaponRuntime.apply`, the reviewed anchor is immediately after
`if (!Float.isFinite(actual) || actual <= 0) return 0;`, passing `actual` and the returned
`Combat.damage` killed boolean. Do not call from the precision/body damage-number split.
Master reports this hook and Dragonfly/Firefly secondary positive-transaction hooks now integrated;
the worker has not inspected or modified main.

`WeaponHitHud.update(ServerPlayer owner)`: call each CombatHud tick before the non-Guardian
ability early return. `WeaponHitHud.remove(ServerPlayer owner)`: call from CombatHud.remove,
including death, world transfer and disconnect. Master reports update/remove already integrated.
These are synchronous server-thread calls. No timer task should queue lifecycle removal against
a future incarnation of the same mutable player object.

**Additional shutdown hook required:** register exactly once alongside the master's lifecycle hooks:

```java
ServerLifecycleEvents.SERVER_STOPPING.register(WeaponHitHud::clearAll);
```

`clearAll(MinecraftServer server)` releases only sessions bound to that exact server, including
all stored owner/connection/level references; a late old-server cleanup cannot clear new-server state.
There is no autonomous event registration or shutdown timer in the adapter.

The stable node is `destiny:hit_confirmation_w223_glyph`; `MAX_NODES=1`.
The entire prefix is outside `destiny:hud_`, `destiny:reticle_w44_`, and scope prefixes.
Existing `removeAbilities` therefore cannot strip this cue; no reticle/scope cleanup defect is claimed.

## Temporal, aggregation and lifecycle contracts

- Only finite `observedPositiveDamage > 0` qualifies, even if killed=true. Miss/invulnerability/zero
  damage has no cue. The caller must provide actual observed loss; this presentation API cannot
  independently re-observe the target or authenticate a caller's supplied float.
- HIT lasts [tick,tick+4); KILL lasts [tick,tick+7). At nominal 20 TPS these are about 200/350ms;
  lag lengthens wall-clock visibility. Authored approximation, not measured Destiny timing.
- Same-tick events coalesce. Kill wins across pellet order and later ordinary hits during red.
  Ordinary hits during kill neither downgrade red nor extend it; they are deliberately discarded,
  so no delayed white tail appears. Another confirmed kill refreshes red.
- Immutable `cueAt` reads do not advance, consume, refresh or prune policy state. Adapter updates
  sample the server clock; rollback against the last adapter sample retires the entire session.
  A later positive event may start a fresh cue. Tick-counter wrap is treated as rollback.
- Binding uses exact player, connection, level and server objects. Confirm/update require the
  server player-list object to be the supplied player. An old same-UUID object's update/confirm
  cannot evict a replacement. Remove requires exact stored player identity.
- Retire first conditionally removes the exact session, then removes a node only when registry
  identity equals the exact stored HUD object. Stale cleanup cannot remove a replacement's HUD.
- Expiry removes the session and its node. Lifecycle remove and server-scoped clearAll prevent
  retained owner maps. Without the master's shutdown hook, static references could remain until
  expiry/lifecycle cleanup; wiring that hook is part of integration acceptance.
- Static placement and two discrete appearances bound traffic: spawn, optional HIT-to-KILL metadata
  transition, removal. Reconfirming the same appearance changes only temporal state, not HUD metadata.
  At most one session/node per UUID, no event queue, no target/gameplay mutation.

## Worker verification performed

- Seven pure policy tests passed via JDK25 JShell **in memory**, loading the actual policy and test
  source after removing package declarations and JUnit annotations/import. No .class/build output
  was written. These same seven methods are JUnit5 tests for central execution.
- Coverage: invalid/zero/nonfinite damage; tiny positive loss; exact expiry and white refresh;
  same-tick order and 32-pellet aggregation; later ordinary hits preserving but not extending kill;
  actual new kill refresh; pure reads/independent states; clock rollback/long overflow;
  exact identity rejection for player/connection/level/server replacements.
- Generator `--check` passed: six assets + manifest reproduce byte-for-byte. Masks have opaque
  stroke cores and a fully transparent central 14x14 square. JSON paths/tints use the provided schema.
- Full Minecraft adapter compilation and packet/render behavior remain central checks. Pure Binding
  tests validate identity comparison, not real connection replacement or server packet routing.

## Proposed central tests and native Vision cases

Run the integrated `WeaponHitStateW223Test` in the central build. Integration regressions should
prove old-player update/remove after a new same-UUID cue leaves the new node unchanged; level,
death, disconnect and SERVER_STOPPING remove exact bound state; rollback discards rather than
revives old cues; a render tick or presentation-status read never refreshes a cue. Include positive
absorption-only loss, mixed precision/body damage-number split, later ordinary pellets while kill
is alive, and positive Dragonfly/Firefly secondary damage. Verify zero/invulnerable secondary
transactions also stay silent. Inspect one-node cap and no repeated metadata on same appearance.

Master's planned FIRST and SECOND each cover seven native sequences:
glaive fire / reload / ADS, then Austringer non-Guardian hit / invulnerable / miss / kill.
Use iron_golem HP100 / Invulnerable / HP1 as reported by master. Capture native tick brackets;
4/7-tick cues need immediate capture, not a delayed screenshot mislabeled as visible feedback.
Owner must see compact white hit / red kill with open center, while observer sees no marker.
Check daylight and a dark background, native ADS/optic gap, hand overlap, and cleanup after expiry.

FIRST actual PNG/server feedback: pending master. Worker remains available to revise or explicitly
justify no change from that evidence before SECOND. SECOND acceptance remains pending; this
return does not claim in-game validation or final product acceptance.

References and approximation limits: `art/hud/w223/SOURCE.md` (explicit source URLs).


## FIRST actual native feedback — same-worker review, 2026-10-28

**Decision: retain the product unchanged for SECOND.** This append supersedes the earlier
FIRST-pending status; it does not grant final acceptance. Only this owned handoff document
was appended during feedback review. No Java, tests, generator, assets, manifest, source notes,
master source, build outputs, client, native input, OS/window or lease state was changed.
No tests/build were rerun for this documentation-only review.

Evidence root: `/private/tmp/destiny-w223-pass1-retry-native` (read-only).
Worker directly viewed `screenshots/hit-confirmation-review.png` and these full raw PNGs:
`frames/w223-hit-hit-sample-01.png`, `frames/w223-hit-kill-sample-01.png`,
`frames/w223-hit-protected-sample-01.png`, `frames/w223-hit-miss-sample-01.png`.
The sheet also supplies adjacent before/after samples for all four HUD cases. Worker read
`oracles/hit-{hit,protected,miss,kill}-timeline.json`, the hit/protected/miss after-oracles,
and each `sequences/w223-hit-{hit,protected,miss,kill}.json` result.

Visual assessment: the ordinary white split-X and more emphatic red kill split-X are visible
in sample01 of their respective raw captures. Both stay compact around the existing reticle,
leave the central aiming area open, and avoid covering the target or weapon with a filled block.
The longer/thicker kill strokes remain distinguishable without increasing the plane or adding
nodes. On these daylight frames the size and shape are suitable; no visual defect justifies
changing scale, geometry, colors or authored durations. The protected and miss raw samples
show no W223 split-X. Their large white/cyan weapon/world particles are independent effects,
not evidence of a false hit HUD. No changes to those effects are proposed here.

Server checks independently corroborate the actual model identity, rather than inferring a cue
from particles or merely counting namespace keys:

| Case | Presentation samples inspected | Nonempty W223 HUD samples | Sequence result |
| --- | --- | --- | --- |
| Hit | 13 | tick1605: `destiny:hit_confirmation_w223_glyph@destiny:gui/hud/hit_confirmation_w223`; empty by1609 | returncode0; completed, released, heldKeys=[], pendingSteps=0 |
| Protected | 15 | none, all `hitHud=[]` | returncode0; completed, released, heldKeys=[], pendingSteps=0 |
| Miss | 12 | none, all `hitHud=[]` | returncode0; completed, released, heldKeys=[], pendingSteps=0 |
| Kill | 11 | ticks1787/1790: `destiny:hit_confirmation_w223_glyph@destiny:gui/hud/kill_confirmation_w223`; later samples empty from1792 | **returncode1; cancelled, physical_user_input**, heldKeys=[], pendingSteps=0 |

Observed node maxima are hit1 / protected0 / miss0 / kill1. Hit after-oracle reports the golem
at93HP and no remaining glyph; protected after-oracle reports100HP and no glyph. The miss
after-oracle reports no entity and no glyph. These support the expected observed-positive versus
protected/miss distinction for these fixtures. They do not independently exercise absorption-only,
secondary perk transactions, stale reconnects or all lifecycle cases.

**FIRST kill sequence remains failed/incomplete.** Activation occurred and the red glyph/actual
kill are supported by the visible dying golem, sample01 and server model timeline. The sequence
record contains five successful captures, then cancellation with `physical_user_input` after
activation (appliedStartTick1244, releasedTick1263). Later server samples being empty are useful
observations, but are not a substitute for a completed native kill sequence and dedicated expiry
oracle. Do not label FIRST kill as a full pass or hide its returncode1. A later-listed frame file
alone does not upgrade the five recorded successful captures or cancellation status.

Sampling establishes visible/empty brackets, not an exact rendered lifespan measurement.
The policy remains authored HIT4/KILL7 server ticks (nominal200/350ms at20TPS), with no claim
of wall-clock precision, extracted Destiny artwork or original-game measured dimensions/timing.
These Minecraft screenshots validate our own approximation; they add no new evidence for
canonical Destiny marker colors. Source limitations in `art/hud/w223/SOURCE.md` still apply;
there is no precision-yellow marker claim.

Master reports positive-actual Runtime/Dragonfly/Firefly hooks, CombatHud update/remove,
AbilityService server-stop clearAll, and read-only `glyph@ITEM_MODEL` diagnostics are wired.
This worker did not edit or re-inspect master source, so those integration statements are
attributed to master. The earlier shutdown-hook integration requirement is reported addressed.

SECOND remains pending and should rerun all seven cases using fresh independent fixtures:
glaive fire/reload/ADS and Austringer non-Guardian hit/protected/miss/kill, including a completed
kill sequence and explicit expiry bracket. Current feedback review covers the HUD evidence
above; it does not certify the separate glaive sequences, dark-background readability, observer
isolation, Dragonfly/Firefly, absorption-only loss or reconnect/shutdown packet behavior.
Worker is available for SECOND feedback; no product revision is needed on the FIRST evidence.


## SECOND completed native feedback — worker closeout, 2026-10-28

**Outcome: no product change; HUD worker review complete, with the white-capture limitation
below retained explicitly.** This section supersedes the SECOND-pending status. FIRST's cancelled
kill remains in the historical record; SECOND supplies a separate completed kill/expiry run.
Only this owned document was appended. The other12 owned files, product timings and assets
are unchanged. No tests, build, native/client operations or master-source edits were performed.
The reusable worktree is preserved; no commit, push, cleanup, archive or deletion was performed.

Evidence root: `/private/tmp/destiny-w223-pass2-native` (read-only).
Worker viewed `screenshots/hit-confirmation-review.png`, **all eight** full raw
`frames/w223-hit-hit-sample-00.png` through `-07.png`, raw
`frames/w223-hit-kill-sample-01.png`, and raw hit/kill expired PNGs.
Worker read `native-validation.json`, all four HUD timeline/sequence records, each explicit
expired-before/after oracle, `postflight.json`, and `coordinator-progress.json`.

### Native completion, gameplay and server presentation

All seven sequence files return0: glaive fire/reload/ADS plus Austringer hit/protected/miss/kill.
`native-validation.json` reports7 sequences, no partial interrupts and neutralAfter=true.
The four HUD sequences independently show completed release, heldKeys=[] and pendingSteps=0;
postflight has no active lease, no held keys, no pending steps and all movement inputs false.
Coordinator records owned server/client wrapper exit codes0/0. This confirms the recorded clean
batch termination; exit codes alone do not prove heap/session-map internals were inspected.
The glaive sequence completion is recorded here, without claiming an additional worker review
of its animation frames.

| HUD case | Gameplay after native shot | Live model samples | Explicit empty expiry oracle ticks (before / after) |
| --- | --- | --- | --- |
| Hit | HP100 ->93; rounds11 ->10 | 1 at1580: `destiny:gui/hud/hit_confirmation_w223` | 1615 /1621 |
| Protected | HP100 unchanged; rounds11 ->10 | 0 | 1678 /1683 |
| Miss | no target after; rounds11 ->10 | 0 | 1739 /1744 |
| Kill | fixture target absent after kill; rounds11 ->10 | 3 at1766/1768/1770: `destiny:gui/hud/kill_confirmation_w223` | 1799 /1804 |

Every live entry uses the exact key `destiny:hit_confirmation_w223_glyph@` followed by the model
above. Sampled node maxima remain hit1 /protected0 /miss0 /kill1. The hit timeline is empty
again at1584; kill is empty at1772. All four explicit expiry before/after records have `hitHud=[]`.
Protected/miss have zero live samples throughout. These are sampled authoritative presentation
and gameplay oracles, not a measurement of every rendered frame or an exact cue duration.
SECOND kill sequence returncode0, eight captures, completed neutral release and dedicated expiry
records close FIRST's missing full kill/expiry validation for this scenario. They do not retroactively
turn FIRST's `physical_user_input` cancellation into a pass.

### Render assessment and honest sampling limit

Red kill split-X is clear in SECOND raw kill01, with compact strokes and the center gap intact;
the raw expired hit/kill frames show no W223 split-X. The negative rows on the sheet show no
confirmation cue; weapon/world particles remain separate from the HUD.

**SECOND's white hit glyph is not unambiguously resolved in any of the eight raw hit samples
reviewed.** In particular hit01 shows actual damage feedback but does not provide a second
clear white split-X image. Its capture bracket spans clientTick1093 ->1095, and the server has
only one sampled live hit-model entry. A multi-tick before/after capture bracket cannot assign
the framebuffer to the exact lifetime of that short cue. This is a sampling/render-evidence
limitation: the server's positive damage/model/expiry observations remain valid, but they alone
cannot prove the white glyph was visibly rendered in SECOND.

FIRST raw `w223-hit-hit-sample-01.png` remains the directly reviewed clear white-glyph capture.
Product bits were unchanged between passes; FIRST supplies the visual white evidence, while
SECOND supplies repeated positive-hit server/model/expiry behavior and completed kill validation.
**Do not claim white was clearly captured twice or that all render evidence was repeated.**
No lifetime, size or brightness was changed to improve capture success: HIT4/KILL7 remain authored
server-tick policy, nominal200/350ms at20TPS, with no wall-clock or original-game precision claim.
The observed evidence supplies no actual product defect requiring a change.

### Source boundaries and final scope

The gameplay oracles concern actual Minecraft damage/ammo and the presentation oracles concern
the exact generated item-model key. PNGs concern this Minecraft framebuffer. None of these
establishes pixel-exact Destiny geometry, canonical original-game timing or a newly verified
ordinary-marker palette. Original procedural-art and research limits in
`art/hud/w223/SOURCE.md` remain unchanged; white is our neutral readability choice, red kill has
community corroboration, and no precision-yellow indicator is claimed.

Current disposition: implementation and mandatory same-worker FIRST/SECOND feedback are
returned with no product revisions. The completed SECOND kill/expiry and negative cases support
closing this assigned worker task; the white repeat-capture limitation is explicit rather than
reported as an unobserved pass. Observer isolation, dark-background readability, absorption-only,
secondary perk damage and stale reconnect/shutdown packet routing were not newly demonstrated
by this four-case HUD evidence. Earlier pure-policy test results stand without a rerun.
Worktree remains available for master integration and preservation; worker is closed out.
