# Direct reload audio — 2026-11-02

User requested treating the remote-server reload-silence report as a defect and using the same direct positional playback transport as weapon fire. Remote login investigation was stopped; no remote deployment or remote playback acceptance is claimed.

## Implementation

- ReloadAudio sends `ClientboundSoundPacket` directly to the owner and nearby eligible listeners at the starting eye position, through `DestinySounds.packet`. Category remains PLAYERS, volume 0.8, pitch 1. No temporary ItemDisplay, entity sound, spawn ordering or emitter tracking remains.
- Each of 64 existing timed/final-tail events has 32 vanilla event-reference aliases. These preserve the original OGGs, timing, definitions and existing subtitle keys. Concurrent same-clip owners reserve distinct aliases; cancellation sends only the captured alias's PLAYERS StopSound.
- All 32 channels occupied for one exact clip: further reloads still play the original direct event and finish naturally. These overflow clips cannot be individually cancelled; their shared event is never stopped. Channel reuse happens after retirement. Playback origin stays at the starting position, as for fire audio.
- Existing stack identity, deadline, death, disconnect, dimension and shotgun-tail lifetime checks remain. Ammo/gameplay code was not changed. Stops also reach captured connected listeners after dimension changes.

## Validation

- Real Java 25 Gradle `test --tests kim.biryeong.destiny.sound.* jar`: 46 sound tests pass; real JAR built. Resource audit reconstructs every expected alias and retains all older source pins.
- Fabric dedicated GameTest: 17/17 reload tests pass, including gameplay deadlines/credit, rejected starts, two simultaneous owners, cancellation, cleanup/death, skills, shotgun insert/final tail, motion without replay, codec, recipient eligibility, catalog coverage and 33 simultaneous exact-clip sessions with safe overflow/reuse.
- Whole JUnit: 2457 tests, 2451 pass, 6 pre-existing failures: GoldenGunHudW122AssetTest (2), WeaponSilhouetteW112AssetTest, InsertW179MindbenderTest, ReloadW168AustringerTest, WeaponSurfaceW115Test. These match the earlier batch baseline; full suite is not green.
- Initial test attempts exposed an incorrect filter, assumptions that bounded aliases were lifetime-unique across unrelated parallel fixtures, and far-coordinate float quantization in test comparisons. Assertions were corrected to isolate source positions and compare actual vanilla packet quantization. Final 17-test run passed. After that run only subtitle metadata/audit expectations changed; sound unit tests and real-client verification cover the final resource version.

## Actual client

`copper-golem-vision-client-fabric-26-3` workflow, local QA server 127.0.0.1:25600 and isolated copy of Danmo (1) in /tmp/destiny-reload-probe/run. General profile untouched. Read-only probe records SoundEngine acceptance; it does not change audio behavior. Resource pack generation completed and client joined destiny:tower.

- Vision native attack paid 8 rounds: 41 to 33. Reload was initiated using an RCON command, not native Q.
- `weapon.reload_w63.weapon.auto_rifle.reload.35.direct_0` reached the client as `SimpleSoundInstance`, `STARTED`, `canPlay=true`, `PLAYERS`. Natural stop after approximately 1.707 seconds; authoritative magazine returned to 41/41.
- A second reload followed by fixture `clear` stopped after approximately 0.301 seconds. See client-trace.txt.
- reload.png is the inspected actual framebuffer during reload. No speaker listening or online-server validation is claimed. Original remote failure cause remains unproven; the entity-bound dependency has been removed as requested.
- Cleanup captured leaseActive=false, heldKeys=[], pendingSteps=0 and neutral native movement. Owned client/server were stopped. Bounded awake coordinator used owned caffeinate PID 33916 (one-hour limit), then released; no security or general profile settings changed.

## Delivery

`build/libs/destiny-guardians-0.1.0+26.3.jar` — 252215719 bytes.
SHA-256: `c3ba4412c075255a0dc586638cb27795b1b3ff495f1faa9cc5266950d4a4bea2`.

Restart the server with this JAR so the generated resource pack includes the new aliases, then reconnect and allow the updated pack to load. No deployment was performed. Existing unrelated campaign changes in sounds.json and its audit helper are preserved unstaged; the commit contains only this batch's alias additions in those tracked files.
