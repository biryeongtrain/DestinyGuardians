# W343 species-specific precision-death headburst SFX

Source: the user's read-only `Downloads/Destiny-Enemy-Headburst-SFX-2026-11-08` delivery. All 40 original WAV/OGG pairs match its supplied SHA-256 list. No external fetch or modification of the delivery was used. Event, bank, WEM, media-id, package/patch and extraction limitations are retained under `art/audio/enemy-headburst-w343/`.

## Runtime behavior

The central weapon damage transaction calls `EnemyHeadburstSounds.confirmed` only after observed positive damage. It additionally requires a positive precision component, an observed final blow, and an actually dead recipient. It emits one positional hostile sound event at the precision contact with gain **0.35**, pitch **1.0**, radius **24 blocks**, to loaded listeners in that level. Existing death vocals remain a separate layer. Mixed pellets use the existing weapon precision-credit policy; no new per-pellet lethal ordering is invented. There are no timers, mutable global dedup caches, delayed entity lookups or changes to gameplay damage.

| Actual target | Delivered event | Variants |
| --- | --- | ---: |
| Campaign / strike Dreg | ether_escape_dreg | 5 |
| Campaign / strike Vandal | ether_escape_vandal | 6 |
| Campaign / strike Captain | ether_escape_captain | 5 |
| Strike Marauder | Vandal-family reuse, explicitly approximate | same 6 |
| Cabal-tagged future actors | cabal_headshot_death | 24 |

The current authored enemies have no Cabal actor. The Cabal event/files are shipped with the empty `destiny:headburst_cabal` entity-type tag hook; a real future Cabal type also needs the existing weapon humanoid precision classification. The delivery contains no Hive headburst event, so Hive and unrelated vanilla species receive no substituted Fallen/Cabal headburst. Players, body kills, ability kills, nonlethal precision hits, shielded body classifications and repeated damage to a dead target do not trigger this layer.

## Audio conversion and pack impact

`python3 scripts/audio/build_enemy_headburst_w343.py` imports from the delivery without changing it. Its existing project FFmpeg/libvorbis tool generates complete-duration mono derivatives at the original rate (`0.5*L + 0.5*R`, Vorbis q5, one thread, stripped metadata, bitexact flags). Each is fully decoded and checked against original frame count (<=256-sample codec tolerance) and mono headers. No trimming, resampling, pitch change or normalization is applied. The 40 OGG derivatives total **1,750,952 bytes**. `--verify` rechecks source WAV/OGG hashes and output hashes. Minecraft chooses one equal-weight variant from the appropriate event; original Wwise random weights/history and final layered bus mixing are not reconstructed.

## Verification boundaries

Targeted units validate 4 events / 40 variants, bundled mono OGGs, retained duration/provenance, and previous death routes. The server batch uses a real auto trigger for nonlethal -> lethal precision shots, the actual central weapon transaction for both campaign/strike family selection, and negative body/ability/shield/unmapped/dead-target cases. Packet assertions cover event identity, position, gain, pitch and range. This is headless server/packet validation, not native aim-input, framebuffer, speaker listening or an original-game A/B mix certification.

The first server fixture forgot to insert embedded listeners into `ServerLevel.players()`; actual damage succeeded but positional sound recipients were absent. The retained initial failure XML records that fixture error. Listeners now join/leave the real level membership; production playback was not broadened to arbitrary global players to pass the test.

Build, server results, matching prebuilt cache and artifact hashes are recorded beside this file. Unrelated existing weapon/perk edits remain outside the scoped commit.

Final validation: **12 targeted unit tests and 4 actual server GameTests passed**. The real auto trigger produced no cue on the first, nonlethal headshot, exactly one Dreg event on the lethal second shot, and no repeated dead-target or distant-listener cue. Campaign and strike family routes, body/ability/shielded/unmapped exclusions, and outgoing 0.35-gain / 1.0-pitch positional packets passed. Actual speaker loudness and a native client A/B mix remain unverified.

Gradle assembled the W343 JAR. A matching normal-server cache was generated once (114.5 s readiness), then restored on restart without generation (13.1 s readiness, 1738 ms restore). Both owned servers exited 0 and port 25630 closed. The actual client ZIP is **189,966,981 bytes**, below 250,000,000; all 40 headburst OGGs were verified byte-for-byte and the event JSON is semantically identical after Polymer formatting. Extract the matching W343 companion cache into the server root.
