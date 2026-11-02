# Audio mixer categories — 2026-11-02

- Activity BGM (tutorial, tower, match transitions): explicit `SoundSource.RECORDS` (Jukebox/Note Blocks). Both play and stop packets share the channel category.
- The existing MusicService API retains MUSIC as its default; the new overload accepts an explicit category. Destiny ActivityMusic opts into RECORDS.
- Vanilla background-music suppression still targets only built-in MUSIC events.
- ReloadAudio packet already uses PLAYERS. This covers normal/exotic timed reloads and shotgun finish emitters. Shotgun insertion and fallback reload cues go through DestinySounds.weapon -> at, also PLAYERS. No artificial reload behavior changes were needed.
- Validation: minigame-lib tests8/8, Destiny sound tests46/46, Gradle jar succeeded. Source routing inspected; no new live audio/slider or speaker-listening test performed.
- Existing unrelated working-tree edits preserved. Only this batch's ActivityMusic hunks staged; dependency commit updates the previously clean submodule.

JAR: `build/libs/destiny-guardians-0.1.0+26.3.jar`
SHA256: `f291a8bb42fa419f8f1ba24f382bb17ed72fa570a7e076ae2352035f5afa5483`
