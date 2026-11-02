# PvE damage tuning — 2026-11-02

User-requested Minecraft server balance: primary ammunition 1.5x, special 2.5x
(midpoint of requested 2–3x), and direct super damage 3x. These are local tuning
values, not DDC or original Destiny damage measurements. Heavy ammunition,
ordinary abilities, glaive melee and PvP retain their previous values.

`Combat.damage` applies `PveDamageBalance` once after existing outgoing weapon
buffs and before `hurtServer`. Attribution is captured by the attack, so switching
held weapons before impact cannot change its multiplier. Weapon hit feedback and
ammo rewards still use observed health loss. Existing super call sites pass SUPER,
including delayed Nova vortex pulses. This does not increase healing or buff
strength of support supers, or reclassify secondary status effects as super hits.

Targeted combat/campaign JUnit: 144 tests, zero failures. Real Java 25 Gradle
`test --tests kim.biryeong.destiny.combat.* --tests kim.biryeong.destiny.campaign.* jar`
build succeeded. No new client/Vision or live Dreg kill acceptance was performed.
Base Dreg health is 20 before difficulty scaling; the user's reported failure to
kill is not proven to be solely low damage (some existing super values exceed 20).

Artifact: `build/libs/destiny-guardians-0.1.0+26.3.jar`
SHA256: `372404dbb433ea1038f468fb42b0970ced1e6a92c4f05787d275a9ba875c4ce0`
No production server deployment.

Full JUnit: 2462 tests, 2456 passed, six baseline asset failures remain:
GoldenGunHudW122AssetTest (2), WeaponSilhouetteW112AssetTest,
InsertW179MindbenderTest, ReloadW168AustringerTest, WeaponSurfaceW115Test.
No new failures compared with the preceding pickup-height batch.
