# W200 original Pulse Monitor

DDC Weapon Perks row171, checked 2026-10-27: base threshold 30% Shield HP; fills
weapon; +50 Handling; .95 ready/stow duration; active while low and 1 second after
recovery; activates and persists while stowed. Yellow 35%? is enhanced uncertainty,
not a base threshold. No PvE/PvP split stated. Official manifest version
245114.26.10.13.2000-1-bnet.66137 supplies exact definition/socket/pool proof.

This port has native Minecraft HP only. Explicit local conversion is native
health/maxHealth <= .30, ignoring absorption; no separate Destiny shield claim.
20 TPS maps one second to 20 ticks. One refill decision per low-health episode,
including first bind already low; repeat damage, ticks and readers never refill
again until observed recovery and reentry. This is local policy because repeat
low-damage behavior is ambiguous. Full magazine/empty reserves consume that episode.

Only original canonical base hash972757866 is implemented: eight exact current
nonfake randomized tuples. Reissued same-name base205890336 is excluded, even on
shared weapon pools; enhanced1685378950 and320071920 are excluded. No default select.

Refill uses WeaponItems.magazine/save and existing WeaponMagazine.reload semantics:
Special/Heavy consume finite reserves/legacy overflow; Primary retains its existing
infinite-reserve supply. No finite-ammo generation, manual-reload
callbacks, Honed decomposition, cadence reset or changes to foreign components.
Only actual positive transfers cancel pending work via cancelForTraitRefill.

All timing/HUD queries are pure and source object/owner/level/data/runtime/class/
loadout/slot/count/entry/selected tuple checked. Stowing does not clear episodes.
changed is for real identity/equipment invalidation, not ordinary hotbar stow.
Main-thread update and actual positive native HP-loss dispatch are Master hooks.

Resource includes raw historical W46 ready/stow/ADS curves and pinned handling
baselines; current official stats verify base handling. Distinct-socket stat pairs:
Parcel Threat Detector OR Snapshot; Dust Rock Snapshot; Dream Breaker Quickdraw OR
Backup Plan OR Frenzy; Edge Transit Quickdraw. Same-socket alternatives are recorded as excluded. Multiply
Pulse .95 once with TD .9/.81 or QD ready-only .95 as actually active; BP has no
ready scalar. BP/Frenzy +100 and QD h100 cap at100. Sum raw bonuses before one stat
clamp; solve raw seconds, multiply once, ceil once. Snapshot affects ADS entry only.
ADS exit uses handling without Snapshot. Historical stow-at100 floor follows the
existing product curve policy. No numeric mirror tests are added.

Master owns shared registry/lifecycle/damage/handling/ADS/HUD and GameTest
registration. Owned GameTests are server automation, not native Vision evidence.
See pulse-report.md for checks actually run and remaining integration validation.
