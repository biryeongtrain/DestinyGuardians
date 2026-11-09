package kim.biryeong.destiny.weapon;

/** Local PvE damage/physics with separately sourced base weapon timing; modifiers/perks remain incomplete. */
public record WeaponProfile(Mode mode, float damage, int intervalTicks, int magazine,
                            int reserve, int reloadTicks, double range, int chargeTicks,
                            int burst, int pellets, double spread, double speed,
                            double gravity, double blastRadius, boolean automatic, boolean infiniteReserve,
                            double cadenceTicks, double burstSpacingTicks, boolean sharedBurstAmmo, boolean shellReload,
                            int firstReloadTicks, int roundsPerInsert) {
    public enum Mode { HITSCAN, PROJECTILE, MELEE }
    /** W46 compatibility: whole magazines, or one shell at identical first/subsequent deadlines. */
    public WeaponProfile(Mode mode,float damage,int intervalTicks,int magazine,int reserve,int reloadTicks,
                         double range,int chargeTicks,int burst,int pellets,double spread,double speed,
                         double gravity,double blastRadius,boolean automatic,boolean infiniteReserve,
                         double cadenceTicks,double burstSpacingTicks,boolean sharedBurstAmmo,boolean shellReload) {
        this(mode,damage,intervalTicks,magazine,reserve,reloadTicks,range,chargeTicks,burst,pellets,spread,speed,
                gravity,blastRadius,automatic,infiniteReserve,cadenceTicks,burstSpacingTicks,sharedBurstAmmo,shellReload,
                reloadTicks,shellReload?1:0);
    }
    public WeaponProfile(Mode mode,float damage,int intervalTicks,int magazine,int reserve,int reloadTicks,
                         double range,int chargeTicks,int burst,int pellets,double spread,double speed,
                         double gravity,double blastRadius,boolean automatic) {
        this(mode,damage,intervalTicks,magazine,reserve,reloadTicks,range,chargeTicks,burst,pellets,spread,
                speed,gravity,blastRadius,automatic,false);
    }

    /** Compatibility profiles retain the old integer cadence and per-bullet ammunition policy. */
    public WeaponProfile(Mode mode,float damage,int intervalTicks,int magazine,int reserve,int reloadTicks,
                         double range,int chargeTicks,int burst,int pellets,double spread,double speed,
                         double gravity,double blastRadius,boolean automatic,boolean infiniteReserve) {
        this(mode,damage,intervalTicks,magazine,reserve,reloadTicks,range,chargeTicks,burst,pellets,spread,
                speed,gravity,blastRadius,automatic,infiniteReserve,Math.max(intervalTicks,burst*2),2,false,false);
    }

    public WeaponProfile {
        if (damage <= 0 || intervalTicks < 1 || magazine < 1 || reserve < 0 || reloadTicks < 1
                || range <= 0 || range > 96 || chargeTicks < 0 || burst < 1 || burst > 9
                || !Double.isFinite(cadenceTicks) || cadenceTicks < 1 || cadenceTicks > 1200
                || !Double.isFinite(burstSpacingTicks) || burstSpacingTicks < 0 || burstSpacingTicks > 100
                || cadenceTicks + 1e-6 < (burst - 1) * burstSpacingTicks
                || pellets < 1 || pellets > 12 || speed < 0 || blastRadius < 0 || blastRadius > 5
                || firstReloadTicks < 1 || roundsPerInsert < 0 || roundsPerInsert > 3
                || shellReload != (roundsPerInsert > 0))
            throw new IllegalArgumentException("Unsafe weapon profile");
    }

    public static WeaponProfile forEntry(WeaponCatalog.Entry entry) {
        WeaponProfile base = switch (entry.family()) {
            case "hand_cannon" -> gun(7, 10, 10, 70, 36, 42, false);
            case "auto_rifle" -> gun(3, 3, 30, 180, 38, 48, true);
            case "pulse_rifle" -> burst(gun(2.5f, 12, 30, 180, 38, 52, false), 3);
            case "scout_rifle" -> gun(5, 7, 16, 96, 36, 72, false);
            case "submachine_gun" -> gun(2.5f, 2, 30, 180, 32, 26, true);
            case "sidearm" -> gun(3.5f, 5, 15, 105, 28, 28, false);
            case "bow" -> projectile(11, 16, 1, 40, 12, 64, 16, 3.0, 0.025, 0);
            case "sniper_rifle" -> gun(16, 20, 4, 20, 48, 96, false);
            case "shotgun" -> pellets(gun(2, 18, 5, 25, 48, 16, false), 8, 0.12);
            case "fusion_rifle" -> pellets(charge(gun(3, 22, 6, 30, 44, 32, false), 16), 5, 0.055);
            case "linear_fusion_rifle" -> charge(gun(18, 24, 5, 20, 48, 88, false), 20);
            case "trace_rifle" -> gun(2.5f, 2, 60, 240, 42, 56, true);
            case "grenade_launcher" -> projectile(15, 24, 1, 16, 40, 48, 0, 1.5, 0.045, 3);
            case "heavy_grenade_launcher" -> projectile(16, 14, 6, 18, 56, 48, 0, 1.6, 0.045, 3.5);
            case "rocket_launcher" -> projectile(28, 30, 1, 6, 60, 80, 0, 2.2, 0, 4);
            case "machine_gun" -> gun(4, 4, 45, 135, 60, 56, true);
            case "sword" -> new WeaponProfile(Mode.MELEE, 10, 12, 30, 60, 40, 3.5, 0, 1, 1, 0, 0, 0, 0, false);
            case "glaive" -> projectile(12, 18, 6, 30, 44, 40, 0, 2.0, 0, 0);
            default -> throw new IllegalArgumentException("Unimplemented weapon family: " + entry.family());
        };
        if (entry.family().equals("shotgun") && entry.frame().equals("pinpoint_slug"))
            base = pellets(gun(13, 18, 5, 25, 48, 24, false), 1, 0);
        if (entry.family().equals("pulse_rifle") && entry.frame().equals("aggressive_burst")) base = burst(base, 4);
        if ((entry.family().equals("sidearm") || entry.family().equals("linear_fusion_rifle")) && entry.frame().contains("burst"))
            base = burst(base, entry.frame().equals("heavy_burst") ? 2 : 3);
        WeaponProfile tuned = switch (entry.frame()) {
            case "aggressive", "high_impact", "heavy_burst" -> scale(base, 1.15f, 1.15);
            case "rapid_fire" -> scale(base, 0.85f, 0.8);
            case "lightweight" -> scale(base, 0.95f, 0.9);
            default -> base;
        };
        boolean infinite=WeaponCharacteristics.of(entry).ammo()==WeaponAmmoType.PRIMARY;
        var timing=WeaponTiming.forEntry(entry);
        int magazine=timing.magazine().orElse(tuned.magazine);
        int charge=timing.chargeTicks().orElse(timing.drawTicks().orElse(tuned.chargeTicks));
        int reload=timing.shellReload()?timing.reloadPerRoundTicks().orElse(tuned.reloadTicks)
                :timing.reloadTicks().orElse(tuned.reloadTicks);
        var reloadPlan=WeaponReloadPolicy.forEntry(entry,reload,timing.shellReload());
        // A bow has draw + nock/reload, not an invented extra sixteen-tick post-shot lockout.
        double cadence=timing.cadenceTicks().orElse(entry.family().equals("bow")?1:tuned.cadenceTicks);
        double spacing=timing.burstSpacingTicks().orElse(tuned.burstSpacingTicks);
        int burst=timing.supported()?timing.burstSize():tuned.burst;
        int pellets=tuned.pellets;
        float damage=tuned.damage;
        int shotgunPellets=ShotgunPatternProfile.pellets(entry);
        if(shotgunPellets>1) {
            // Adopt historical twelve-pellet frame identity, preserving the existing local total HP budget.
            damage=damage*pellets/shotgunPellets;
            pellets=shotgunPellets;
        }
        if(entry.family().equals("fusion_rifle")) {
            // Convert the old simultaneous five-pellet transaction to 5/7/9 timed bolts,
            // preserving its local per-charge damage instead of inventing original Destiny damage.
            damage=damage*pellets/burst;
            pellets=1;
        }
        return ExoticProfilesW350.adjust(entry, new WeaponProfile(tuned.mode,damage,(int)Math.ceil(cadence),magazine,
                infinite||entry.family().equals("sword")?0:tuned.reserve,reloadPlan.intervalTicks(),tuned.range,charge,burst,
                pellets,tuned.spread,tuned.speed,tuned.gravity,tuned.blastRadius,WeaponFirePolicy.supportsAutomatic(entry),infinite,
                cadence,spacing,timing.sharedBurstAmmo(),reloadPlan.incremental(),
                reloadPlan.firstTicks(),reloadPlan.roundsPerInsert()));
    }

    private static WeaponProfile gun(float d, int t, int m, int r, int reload, double range, boolean auto) {
        return new WeaponProfile(Mode.HITSCAN, d, t, m, r, reload, range, 0, 1, 1, 0, 0, 0, 0, auto);
    }
    private static WeaponProfile projectile(float d, int t, int m, int r, int reload, double range,
                                             int charge, double speed, double gravity, double blast) {
        return new WeaponProfile(Mode.PROJECTILE, d, t, m, r, reload, range, charge, 1, 1, 0, speed, gravity, blast, false);
    }
    private static WeaponProfile charge(WeaponProfile p, int ticks) { return copy(p, ticks, p.burst, p.pellets, p.spread, p.damage, p.intervalTicks); }
    private static WeaponProfile burst(WeaponProfile p, int shots) { return copy(p, p.chargeTicks, shots, p.pellets, p.spread, p.damage, p.intervalTicks); }
    private static WeaponProfile pellets(WeaponProfile p, int count, double spread) { return copy(p, p.chargeTicks, p.burst, count, spread, p.damage, p.intervalTicks); }
    private static WeaponProfile scale(WeaponProfile p, float damage, double interval) {
        return copy(p, p.chargeTicks == 0 ? 0 : Math.max(8, (int)Math.round(p.chargeTicks * interval)),
                p.burst, p.pellets, p.spread, p.damage * damage, Math.max(2, (int)Math.round(p.intervalTicks * interval)));
    }
    private static WeaponProfile copy(WeaponProfile p, int charge, int burst, int pellets, double spread, float damage, int interval) {
        return new WeaponProfile(p.mode, damage, interval, p.magazine, p.reserve, p.reloadTicks, p.range,
                charge, burst, pellets, spread, p.speed, p.gravity, p.blastRadius, p.automatic);
    }
}
