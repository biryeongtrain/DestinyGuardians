# Music linkage and attack cadence — 2026-11-04

User delivery: `/Users/qf/Downloads/Devils-Lair-Music-Linkage-2026-11-04` (read-only).
All 147 manifest entries verified; 41 media mappings now source-confirmed. The old pending/inferred inventory is historical and is superseded by this delivery, not retroactively rewritten.

49 bank segments rendered through wwiser v20260808 and vgmstream r2168 into float PCM, then Vorbis through libsndfile. All use the same 0.3 headroom gain (no per-track normalization), preserving clip overlap, source trims and automation emitted by wwiser. Original WEM/OGG files remain unchanged. Generated runtime audio totals approximately 59 MB. `import.json` records input and output hashes. The importer rejects non-finite PCM and peaks exceeding the chosen headroom.

`DevilsMusic` is owned by each session and routes RECORDS only to ready participants in its dimension. Generation cancellation, leaving, disconnect and close stop owned handles. ActivityMusic retains the descent cue; combat begins after briefing. Playlist trees are interpreted lazily, preserving finite/infinite loops, sequential children and weighted random/no-repeat selection. Normal Sepiks uses intro -> eight body repetitions -> outro; its completion selects item 328849011. Metal assets are retained but variant selection is not enabled without its gameplay rule.

Phase mapping: RY + RF entry = section00; device = 01; hack/first defense = 02; first intermission/second defense = 03; second intermission/third defense = 04; RF clear/Blast battle = 05; Walker clear/preboss = 06; all Sepiks combat phases = 07; completion = 09. In particular Walker battle is NOT section06. Section01/06 are source silence. Transition segments 829866489 and 1835101 are dispatched when leaving section02/03.

## Acceptance limits

This is a Minecraft adaptation, not a Wwise engine. Current transport has no in-flight gain or seek API. Thus the source 12-second fade to silence and overlapping tails are not reproduced; transitions stop the old event. The initial implementation waited for rendered segment ends and left late listeners silent; this is superseded by the timeline follow-up below. The engagement inactive trigger, missing global bus, random long-run auditory acceptance and speaker mix remain unverified. These are open music-quality work, not passed gates.

## Attack tuning

User-requested provisional Minecraft tuning, not source-confirmed Destiny values:
- Every primary attack recovery: former period * 1.5.
- Burst gap: ordinary 4 -> 7 ticks, Sepiks 6 -> 10 ticks.
- Walker/Brig secondary gap: 4 -> 7 ticks.
- Secondary recovery: Brig 70 -> 105 ticks, Walker 50 -> 75 ticks.
- Damage, caps, movement, windup and target priority unchanged.

Validation: new playlist tests cover Sepiks intro/body/outro, refinery paired intro and no-repeat infinite loop, phase mapping and resource resolution. Broad targeted 126 tests: 117 pass, nine known baseline audio-evidence failures. Full 2554 tests: 16 failures, all matching the previous baseline; jar task succeeds under --continue. See regression.json. Native/actor evidence is recorded separately below; no completion commit while quality gaps remain.

Live verification: actor GameTests 13/13 passed. The isolated server published its resource pack and Vision connected with no screen/overlay. The actual entry framebuffer was inspected (`entry.png`); section00 segment546249760 was dispatched to one ready listener at 03:02:50 KST after the descent cue ended. This is server playback/pack/framebuffer evidence, not speaker acceptance or full-route listening. The first entry attempt was correctly refused because the QA account auto-entered the legacy tutorial; the fixture exited the tutorial before retrying.

## Timeline follow-up

The per-session transport now keeps a separate pure score timeline per eligible ServerPlayer. A reconnect/newly ready listener starts the current encounter section immediately, while existing listeners keep their own current clip. This is independent personal music, not a claim of sample-synchronized fireteam playback. On disconnect/pack unreadiness the listener handle is stopped and removed; no long silent wait for a teammate segment boundary.

Transitions use the last matching source bank rule, including segment-specific silence overrides and destination-specific priority. NextMarker uses internal marker timestamps, NextBar uses source tempo/time signature, NextGrid uses source period/offset, and Immediate remains immediate. Music playlist jumps follow source uJumpToID, preserving ancestor traversal: direct entry at Walker skips the completed intro, normal/metal victory choose distinct endings, and reconnect after completion selects the source silence entry. Meter fields are read from the verified banks.xml, not assumed four-four defaults.

Random shuffle now consumes a weighted bag and refills it for each cycle while respecting the avoid-repeat boundary. The prior N-1 sliding exclusion accidentally repeated the first shuffle permutation forever; a second-cycle regression covers this.

Transport limitations still apply: dynamic fade/seek, overlapping post-exit tails and sample-accurate packet scheduling are not implemented. Natural segment advancement still uses rendered duration. Actual audible seams and mix require listening acceptance. The metal variant has timeline support and assets but its gameplay selection remains disabled.

Final timeline regression: 2561 JUnit cases, 16 failures with exactly the prior failure identities, no new failure. Music suites 11/11 pass, including internal markers, rule priority, immediate silence exits, grid/bar timing, ordinary/metal/direct-entry victory jumps, per-listener late join and pending-transition cancellation. An additional full run was justified by the shuffle-cycle defect found after the first timeline run. The final JAR hash and XML are in timeline-regression.json.

Native reconnect verification: the same strike dimension 91273abf-95a0-4059-bb46-854554a81676 survived the owned client shutdown at 03:14:52 KST. The client rejoined at 03:15:25, and section00 segment546249760 was dispatched at 03:15:26, without replaying the briefing. Before/after actual framebuffers and states are saved; the HUD/objective remained visible. This proves single-client reconnect and prompt server dispatch. Two-player independence is pure timeline regression evidence, not a two-client runtime test. Speaker audibility remains unverified.
