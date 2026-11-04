# Iron Reach — W190

User DDC Weapon Perks gid1662574278, row129, fetched2026-10-27: base **+20Range/-20Stability**. Enhanced -15 is excluded. No mode split is present in this row.

The generator records the exact official randomized trait socket for the currently selected Allied Demand hash1532276803; no other weapon is admitted. See source.json for the original definition, socket/plug proof and source file hashes. Source cache paths are local build inputs, not runtime requirements.

Range is evaluated once at clamp(base+20,0,100) with existing W43 hip-fire coefficients; ADS scaling follows afterward. The unchanged metres→blocks mapping and historical curve are Minecraft adaptation, not a verified current Destiny falloff measurement. Stability applies the -20 penalty in the existing recoil/bloom/flinch calculation, clamped together with active positive bonuses.

No perk-specific tests or Vision run: user requested source-and-application-path verification for simple stat traits. Master performs compilation after integration.
