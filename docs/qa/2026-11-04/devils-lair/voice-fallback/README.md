# Unavailable voice: authored text-only notice

Known but missing/bad-header OGG clips and unknown catalog line IDs now show an authored Korean objective notice for the director's 60-tick fallback. The speaker label is `임무 안내`, never Ghost/Zavala attribution. Source subtitle JSON, original OGG bytes, sound event mappings, normal clip durations and PLAYERS category are unchanged.

The packaged-clip check verifies presence and OggS header only, not complete decoder validity or client volume/mute state. Malformed catalog metadata remains a separate asset failure; this work does not claim to recover every resource corruption.

Text-only playback returns unavailable to the director, sends no audio/stop packets and never invokes a successful voice callback. Audience replacement receives the existing remaining caption, not a fresh 60 ticks. Cancel/close removes only owned subtitle rows. Session now suspends voice and progress clocks together when no audience is ready. Director fallback expiry explicitly closes the presentation before continuation, preventing a queued cue from colliding with a text-only playback that started one clock phase later.

## Evidence

11 server GameTests pass: the existing 9 actor cases plus actual HUD/packet fallback lifecycle and original speech packet/duration cases. The audio-unavailable condition is injected through a package-private predicate; normal playback uses the packaged OGG header check. These tests inspect server HUD ownership and emitted packets with manually advanced playback ticks. They do not establish rendered glyph appearance, client audio decoding, or speaker listening.

Native visual acceptance remains pending due to the previously observed Mac lock. No completion commit is claimed.

Final JUnit: 2550 tests / 16 failures / 0 errors. Failure identities match prior baseline: True. Existing failures remain unresolved. Gradle --continue completed jar; combined exit is failure due to tests. JAR SHA256 `8835cb7299a4d4faa611a37234ab2aca9b0429a7e15c09a4ad678f27eb7d3f10`. The final director fallback cleanup hook is covered by the added JUnit ordering test; the earlier 11-case GameTest run covers playback itself.
