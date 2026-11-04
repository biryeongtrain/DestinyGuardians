# W46 base weapon timing (data/API only)

Offline deterministic generation and verification:

```sh
rtk proxy python3 scripts/extract_weapon_timing_w46.py
rtk proxy python3 scripts/extract_weapon_timing_w46.py --verify
# Additional audit against the original full official cache (not committed):
rtk proxy python3 scripts/extract_weapon_timing_w46.py --verify --inventory /tmp/destiny-weapons-w30/bungie-items.json
```

## Sources and trust boundaries

63 exact W30 selected hashes use W40's pinned Oct13 Bungie inventory snapshot.
The underlying cache above SHA-matches W40 provenance and every selected stat
was checked against it. `official-item-evidence.json` retains the 63 selected
names/hashes/stat maps. `stat-definitions.json` is the actual official full stat
definition response from **the same manifest version/path suffix**; SHA and URL
are recorded in `extraction.json`. The charge and draw descriptions explicitly
say milliseconds. Magazine and RPM are exact positive base display stats, not
perk-modified values. Missing bow magazine remains absent; no inferred 1.
Sword magazine values are ammo capacity, not reloadable magazines; swords have
`supported=false` and no timing overrides.

Oracle Engine source is copied verbatim at the W43-pinned commit, with MIT / 
UNLICENSE attribution. `build.rs` divides firing delays by **30**, confirming
30-fps source frames, not Minecraft ticks. `stat_calc.rs` uses end delay plus
`(burst_size-1)*inner_delay`, adds 0.45s fusion / 0.95s LFR recovery and computes
effective RPM. `rs_types.rs` verifies quadratic evaluation, and `d2_enums.rs`
defines `Seconds = f64`. Historical community curves are **not official exact
current sandbox timings**; reload source explicitly calls them approximate.

## Exact helper API / scheduler contract

`WeaponTiming.forEntry(entry)` and alias `of(entry)` return immutable `Timing`:

- `supported()` boolean: 58 ranged entries true, 5 swords false.
- `magazine()`, `rpm()`, `chargeMillis()`, `drawMillis()`: `OptionalInt`.
- `cadenceTicks()`, `burstSpacingTicks()`: `OptionalDouble`, fractional 20 Hz.
- `burstSize()` int; `sharedBurstAmmo()` boolean (fusion/LFR only).
- `chargeTicks()`, `drawTicks()`, `reloadTicks()`: `OptionalInt`.
- `shellReload()` boolean; `reloadPerRoundTicks()`, `reloadInitialTicks()`:
  `OptionalInt`.

**Cadence is firing lockout AFTER the first bolt, excluding a subsequent charge.**
For normal single-shot guns/pellet shotguns: `1200/officialRPM`. For true pulse /
sidearm bursts: `(endFrames+(N-1)*innerFrames)*20/30`. For fusion/LFR:
`((N-1)*innerFrames/30+fixedRecoverySeconds)*20`; official charge ticks apply
separately. Do NOT add Oracle's charge-like end delay too. The provenance retains
the full historical Oracle period for comparison, not as the runtime lockout.
Charge/draw ticks are `ceil(officialMilliseconds/50)`. Bow/glaive/sword reused
Charge Time hash values (60/80, 41, 20/50) are **not** interpreted as milliseconds.
Fusion bolts 5/7/9 and LFR 3 preserve fractional within-burst spacing. Coriolis
Force's 7 bolts are simultaneous (spacing 0). Pulse/sidearm ammo is per bullet;
fusion/LFR ammo is once per burst. Shotgun Oracle `burst_size=12`, spacing 0
means simultaneous pellets: API queue burst is **1**, leave pellet geometry alone.

Reload: `ceil((evpp*x*x+vpp*x+offset)*20)`, x is official Reload Speed (a stat,
NOT seconds); bow x clamps to 85 as source specifies. No perks/frame animation
modifiers are included. Only the five shotguns are classified for a
**per-shell/per-round** model, `shellReload=true`, `reloadTicks=empty`; consumers use
`reloadPerRoundTicks`, NOT an entire magazine in one insert. Shell classification
is a gameplay assumption **not independently verified by a direct source**:
the Oracle quadratic does not encode reload granularity or entry delay. Initial
delay deliberately remains empty (not guessed zero). Long Arm's original
two-round loading is not reconstructed: without a verified per-insert curve it
keeps `shellReload=false`, absent per-round timing, and the default scout
whole-magazine reload approximation (~42 ticks), not that duration per cartridge.
This API does not override existing shotgun pellet count: Oracle's 12 is evidence
only, and retaining the existing 8-pellet runtime is not an exact-12 claim.

Warnings in each extraction row call out absent/weird stats, raw official RPM vs
Oracle mismatches, historical charge differences, and shell/pellet semantics.
Only known values should override existing policy; null means **unknown**, not
zero. No gameplay, registration, Gradle or runtime integration is performed here.

## Consumer integration / verification
The generator/helper above stays data-only. Its actual consumer is now
`WeaponProfile.forEntry`, `WeaponCycle`, and `WeaponRuntime` (W46), with immutable
ammo snapshots driving `AmmoHud`. Final integration evidence is in
`docs/qa/2026-10-24/w46/README.md`:291GameTests/244JUnit/native16.
Main research independently opened Bungie Update2.1.0 article47462 to confirm
shotgun shell-granularity exists. This does not establish exact insert durations,
first-insert delay or current frame modifiers; the generated conservative warnings
remain valid. Operational legacy-overflow migration and original reload animation
remain incomplete. Overall weapon goal remains active.
