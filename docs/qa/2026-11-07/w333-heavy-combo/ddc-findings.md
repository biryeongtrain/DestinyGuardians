# W333 heavy-combo DDC findings

Read-only lookup, 2026-11-07 Asia/Seoul. Followed docs/design/162_수치_기준_Destiny_Data_Compendium.md. No repository edits/build/QA.

## Live sources and actual sheet rows
- [Arc tab, row 64](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=618967225&range=B64:N64): Arc Staff. HTML row number verified by htmlembed/sheet, not CSV record index.
- [Void tab, row 67](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B67:N67): Spectral Blades.
- Sheet index row22 says PvE damage is scaled to Shooting Range Elite combatants, 0 Weapons, Normal difficulty delta0; default Crucible for PvP. The sheet is user-designated community DDC, not an official Bungie balancing specification.

## Arc Staff
| attack | PvE raw damage | PvP raw damage | condition / range |
|---|---:|---|---|
| Ground or air light |864| ? |Up to8m; grounded light chain up to3 hits|
| Ground heavy |1264| ? |Approximately45-degree angle, up to8m|
| Air heavy |1264| ? |Blind; source wording says over7m away, does not clearly specify radius vs reach|
| Palm Strike |2950| ? |Light-Light-Heavy combo; blind, approx45-degree angle/up to8m|

Ratios DERIVED from DDC PvE numbers: ordinary heavy/light=1264/864=79/54=1.462962963; Palm/light=2950/864=3.414351852. Palm is a distinct third combo condition; do not grant its multiplier to every ordinary heavy. DDC does not establish a universally doubled heavy attack. PvP damage and heavy/light ratio remain unknown; do not replace ? with inferred PvE values.

Energy drain: light2.5%, grounded heavy8%; air heavy8%? remains uncertain. These are super-energy percentages, not attack cooldowns. User requested60ticks=3seconds at20TPS is a CUSTOM cooldown and must not be overwritten by these values.

## Minecraft boundary
Current Arc base param damage16/reach4.5/arc70 are local gameplay settings (HunterSuper.ArcStaff.strike uses damage16 default). Parent/runtime confirms existing PvE multiplier3. Mapping the PvE ordinary-heavy ratio onto local16 gives23.4074074 before x3, or70.2222222 after x3, versus light48. This is only an explicit derived Minecraft balance option, NOT DDC damage and NOT established PvP scaling. Existing light damage, PvP override, and local reach/angle must not silently be replaced by raw DDC units.

## Spectral
DDC Void67: light1107 PvE, heavy1620 PvE (ratio60/41≈1.463414634); both PvP ?. Heavy is uppercut, applies Weaken and grants Invisibility. Source energy drains light5?%, heavy15?%; retain uncertainty. Current src/main/resources/data/destiny/destiny_ability/hunter/spectral_blades.json has damage11, heavy_damage18 (localratio18/11≈1.63636), not the DDC ratio. Existing configured18 can be retained; do not report it as exact DDC. 60tick cooldown is user customization.

Evidence cached in this folder: ddc-Arc.csv, ddc-Void.csv, sheet-618967225.html, sheet-1907852650.html. Direct runtime-agent message could not deliver because melee_area_lunge was no longer in live agent inventory; findings sent to root.
