# Fireteam down / revive integration — 2026-11-03

Devils’ Lair development remains paused except for the requested shared revival integration.

- Delivered Korean down announcement uses explicit activity roster, excludes fallen player and outsiders, direct PLAYERS sound packets.
- Delivered 3.024-second progress cue starts once per helper attempt, stops on helper change/cancel/success/scene teardown. 64 unique simultaneous stop channels; overflow naturally finishes and is never globally stopped.
- Successful revive presents original 1.6-second source motion plus 4 ticks of pose exit blending. Position and starting yaw are anchored; head pitch does not follow user aim. Successful gameplay callback is delayed until the lock ends. Owned cancellation never invokes it.
- Legacy transmat/revive effects remain; handoff lifecycle candidates are not claimed as confirmed completion sounds.
- Original 72-bone .blend evaluated read-only and retargeted to existing segmented skin rig. See motion/README.md and hashes. Full rig replacement is not included.

Validation so far: four filtered actual server GameTests pass (ownership, recovery, immobility/facing during motion, successful callback timing, direct team audio and independent/idempotent cancellation). Full JUnit run had 2535 tests / 17 failures: one expected model-version assertion updated after version bump and targeted rerun passed; the remaining 16 concern unrelated existing asset/provenance/geometry expectations. Those are not claimed passing or proven baseline. Final Gradle jar and relevant unit checks passed. Build initially invoked unfiltered GameTests; that owned run was stopped before tests and rerun with the explicit revival filter.

Live client visual/audio acceptance pending. User explicitly requested being asked before launch and approved the launch. Isolated existing fixture /tmp/destiny-devils-qa-20261103, master bounded awake /tmp/destiny-revive-master-20261103; no production server or ordinary Minecraft profile changed.

## First live review and user timing correction

First live 24-frame capture confirms source pose changes and return to gameplay. User reported the motion/audio generally acceptable. Frame inspection found the stationary ghost obstructing the reforming body. User requested no revival dialogue and total rescue duration matching the supplied sound.

Revised timeline: sound begins at rescue start; 25 ticks of ghost progress overlap into 32 ticks of source animation + 4 ticks of return blending, total 61 ticks (3.05 s, server-tick ceiling of 3.024 s). Ally progress starts the motion preview during the hold; the full original uninterrupted 60-tick proximity requirement still authorizes gameplay revival, and the final motion tail completes within the sound-aligned deadline. A lost/changed helper cancels preview and restores the downed ghost/camera without successful callback. All revival voice playback removed; teammate-down announcement remains. Ghost fades as the player reforms. Final revised live acceptance pending.


## Class ability playback parity (2026-11-03)

Second live review captured in `live-revised/`: Ghost fades before the visible body motion and first-person return is visible. User requested smoother motion, then explicitly selected the class-ability settings as the reference.

GCB-mod main f18db83bfe9abff98c57baf96a8bd141a1fa4a69 (4.2.0, Minecraft 26.3) reviewed: BulkReceiver preserves vanilla display interpolation with bundled transforms; MountPrediction only predicts a ridden server-authoritative Mob. Neither is a drop-in replacement for stationary BetterModel revival pose playback. No new GCB interpolation integration is claimed.

Removed the revival-only modifier and reused `Modifiers.ONCE`, exactly as class abilities do: start=1 tick, end=0, priority=20, PLAY_ONCE. Both already use SourceAnimationGrid's 25ms compilation, two server-clock evaluations per tick, one final pose publication and one-tick display interpolation. The proposed two-tick smoothing experiment was reverted after user steering and is not in the final code.

Revival allocation is now 28 ticks of light gathering plus 33 ticks of motion (32 source + 1 entry), preserving the 61-tick sound-aligned total. Ally preview starts on held tick29 and still requires gameplay authorization. The earlier 25+36 timing notes describe the previous revision.

This aligns playback settings; it does not prove equal perceived smoothness across different source clips or camera transitions. New native visual acceptance remains pending; no blanket change to unrelated animation data or combat timing.

Class parity validation: targeted pose tests, five actual server GameTests and Gradle jar passed. Approved client launched; live-class-parity contains 24 framebuffer captures. Body motion, Ghost absence during body phase and first-person return inspected. User smoothness/audio feedback pending; no native movement-input verification claimed for this run.

## Two-tick revival smoothing (latest user request)

User judged the class-ability parity demo less smooth and requested two ticks. Revival alone now uses a scoped 2-tick (100ms) display transform interpolation duration. Class-ability playback modifier remains start=1/end=0 and the 28+33=61 tick timeline is unchanged. Other clips retain one-tick smoothing. Scope restoration on exceptions/nesting is covered by the targeted sampling test; immediate/skip-interpolation frames retain their native zero duration. This is vanilla display interpolation, not a new GCB API. Actual improved smoothness awaits user review after a separately approved Vision launch.

Two-tick approved live demonstration: 24 screenshots in live-two-tick; server confirmed revival and framebuffer confirmed body motion plus first-person return. User smoothness acceptance pending. Client left open for review.

## Supplied completion variants

User supplied four Transmat Basic Respawn MP3s and authorized autonomous future Vision verification. Added full-length mono Vorbis variants respawn_complete_1..4 with source/output SHA-256 and decoded lengths in destiny/down/respawn-audio-provenance.json. Successful finish selects one server-side uniform variant for the revived owner and eligible same-world fireteam, sent directly in PLAYERS category after the success callback. No revival dialogue restored. Progress audio, 61-tick deadline and accepted two-tick motion interpolation retained. Initial added cancellation assertion incorrectly counted a drained outbound queue; corrected expectation to zero newly emitted completion packets after cancellation.

Completion QA: five server tests passed, including exactly one completion packet on success and zero new completion packets after cancellation. Actual PNG sequence inspected, four events/files verified in generated pack, and four isolated playsound commands completed without client sound-load warnings. Command delivery and absence of warnings do not establish physical speaker listening; that remains unverified.
