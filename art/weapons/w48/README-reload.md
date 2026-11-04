# W48 — Long Arm pair inserts

Selected **Long Arm 8293111** only; not the 2025 reissue or every aggressive scout.

## Actually viewed reference

[EndgameXpress, 2022-12-18](https://www.youtube.com/watch?v=XPB6leAQKuQ),
*How to get Long Arm (Spire of the Watcher Scout Rifle) plus god roll guide in Destiny 2*.
The opening segment shows the Long Arm rifle being reloaded. Download format230,
640×360,25fps. Full video stays gitignored. SHA pins and source-frame observations
are in `reload-policy-evidence.json`; small HUD excerpts in QA/w48.

Manually inspected frame264(10.56s):3;265(10.60s):5;
280(11.20s):5;281(11.24s):7. Thus each observed insert transfers **two** cartridges.
Visible update gap is0.64s at0.04s frame resolution. Broader7–16s contact sheet
also shows later9/11/13/15 and final16. Do not copy the clip's16-round capacity:
the selected exact official definition remains **14**.

## Runtime policy, NOT an official timing measurement

First deadline **20ticks/1.0s**, subsequent **13ticks/0.65s**, batch **2**.
The first delay is authored: physical reload keypress is not observable. Repeat
delay is reference-informed tick quantization, not an exact base-sandbox curve.
Roll/perks/buffs are not established; later gaps can vary. No claim of current
official or unmodified reload timing. These knobs remain isolated in
`WeaponReloadPolicy`; W46's42tick generic whole-magazine curve remains unchanged
for provenance, but no longer drives this selected weapon's live reload.

Each deadline atomically transfers min(batch,space,available finite ammo).
Late callbacks transfer one pair only and start the next phase from actual now.
Final missing slot transfers one round. Primary retains infinite reserves, not
an infinite magazine. Fresh trigger can interrupt; continuing held-empty
heartbeats cannot spend newly inserted rounds. Cancel/swap/skill preserves prior
inserts and stops future ones. HUD reads actual first/repeat phase duration and
saved counts without prediction or mutation. This is an extension of the existing
Destiny-inspired custom HUD, **not** a claim of pixel-exact original HUD copying.

Finite/overflow invariants are additionally tested using synthetic finite profiles;
this does not turn Long Arm into a Special weapon. Existing shotguns remain batch1,
others whole-magazine. No Long Arm animation, hand IK, base-stat modifier/perk
simulation or full-auto accessibility setting is implemented here.
