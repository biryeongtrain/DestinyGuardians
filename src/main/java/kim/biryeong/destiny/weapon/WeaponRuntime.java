package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.sound.DestinySounds;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.event.player.UseEntityCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.core.BlockPos;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.TamableAnimal;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** All inputs, ammunition, delayed bursts, collision and damage execute on the server thread. */
public final class WeaponRuntime {
    private static final Map<UUID, State> STATES = new HashMap<>();
    private static final List<Shot> SHOTS = new ArrayList<>();
    public static final int MAX_PROJECTILES_PER_PLAYER = 16;
    public static final int HEARTBEAT_LEASE_TICKS = 6;
    private static boolean initialized;
    private WeaponRuntime() {}

    private static final class State {
        final ServerPlayer owner;
        final WeaponCycle cycle = new WeaponCycle();
        final WeaponCadenceBank cadence = new WeaponCadenceBank();
        final GlaiveCycle glaive = new GlaiveCycle();
        final SwordCycle sword = new SwordCycle();
        final kim.biryeong.destiny.sound.SwordGuardAudio swordGuardAudio = new kim.biryeong.destiny.sound.SwordGuardAudio();
        ItemStack stack = ItemStack.EMPTY;
        ServerLevel level;
        boolean swordBound;
        SwordContact swordContact;
        WeaponProfile acceptedBowDraw;
        WeaponCatalog.Entry chargeEntry;
        WeaponProfile acceptedCharge;
        Shot remoteShot;
        WeaponHighImpactReserves.Token paidHighImpact = WeaponHighImpactReserves.Token.NONE;
        WeaponClownCartridge.Token clownReload = WeaponClownCartridge.Token.NONE;
        WeaponAmbitiousAssassin.ReloadToken assassinReload = WeaponAmbitiousAssassin.ReloadToken.NONE;
        WeaponSympatheticArsenal.ReloadToken arsenalReload = WeaponSympatheticArsenal.ReloadToken.NONE;
        boolean holding;
        boolean fired;
        boolean emptyReloadPending;
        boolean reloadAllowsHeldInput;
        boolean heartbeatNeedsFreshPress;
        long heldUntil = -1;
        long lastHeartbeat = Long.MIN_VALUE / 2;
        State(ServerPlayer owner) { this.owner = owner; }
        void releaseHold() { WeaponDynamicSway.released(owner,stack); WeaponTapTheTrigger.released(owner,stack); holding = false; fired = false; heldUntil = -1; cycle.cancelCharge(); acceptedBowDraw=null; }
        void cancel() { cancel(false); }
        void cancel(boolean preserveFundedIzanagiCue) {
            WeaponClownCartridge.changed(owner,stack);
            WeaponSympatheticArsenal.reloadCancelled(owner,stack);
            arsenalReload=WeaponSympatheticArsenal.ReloadToken.NONE;
            clownReload=WeaponClownCartridge.Token.NONE;
            assassinReload=WeaponAmbitiousAssassin.ReloadToken.NONE;
            WeaponAce.cancelReload(owner);
            WeaponIzanagi.cancelReload(owner);
            detachRemote(this);
            kim.biryeong.destiny.sound.ReloadAudio.stop(owner);
            swordContact=null;
            swordGuardAudio.release();
            kim.biryeong.destiny.fx.SwordPresentation.cleanup(owner);
            if (swordBound) SwordItems.save(stack,sword.energy(),sword.rechargeRemaining(now(owner)));
            swordBound=false;
            sword.stop();
            cycle.cancelPending(); releaseHold();
            emptyReloadPending=false; reloadAllowsHeldInput=false;
            heartbeatNeedsFreshPress=false;
            chargeEntry=null; acceptedCharge=null;
            paidHighImpact=WeaponHighImpactReserves.Token.NONE;
            WeaponReloadPresentation.clear(owner,stack);
            if (!preserveFundedIzanagiCue || WeaponIzanagi.charge(stack) < 2)
                WeaponIzanagiPresentation.clear(owner,stack);
            WeaponInsertPresentation.clear(owner,stack);
            WeaponBowPresentation.clear(owner,stack);
        }
    }
    /** Immutable accepted cost/power; live geometry is acquired only at contact.
     * Never stores a target, future inventory payment or wall-clock callback. */
    private static final class SwordContact {
        final WeaponCatalog.Entry entry;
        final WeaponProfile base;
        final SwordProfile profile;
        final boolean heavy, empty, grounded;
        final float damage;
        final long acceptedAt;
        final long visualFrames;
        final int delay;
        final DamageTraits damageTraits;
        Vec3 previous;
        SwordContact(ServerPlayer player,WeaponCatalog.Entry entry,WeaponProfile base,SwordProfile profile,
                     boolean heavy,boolean empty,float damage,int combo,boolean visual) {
            this.entry=entry;this.base=base;this.profile=profile;this.heavy=heavy;this.empty=empty;this.damage=damage;
            grounded=player.onGround();
            damageTraits=empty?DamageTraits.NONE:DamageTraits.capture(player);
            acceptedAt=now(player);delay=SwordTiming.contactTicks(profile.shape(),heavy,combo);previous=player.position();
            visualFrames=visual?kim.biryeong.destiny.fx.PlayerAnimations.serverFrames(player):-1;
        }
    }
    /** Snapshot once per paid emission/contact; the third target does not buff that same emission. */
    private record DamageTraits(WeaponOneForAll.Token oneForAll, WeaponSurrounded.Token surrounded, WeaponSwashbuckler.Token swashbuckler, WeaponMultikillClip.Token multikillClip, WeaponSubsistence.Token subsistence, WeaponRapidHit.Token rapidHit, WeaponFrenzy.Token frenzy, WeaponAdrenalineJunkie.Token adrenalineJunkie, WeaponFocusedFury.Token focusedFury, WeaponStatsForAll.Token statsForAll, WeaponHeatingUp.Token heatingUp, WeaponVorpal.Token vorpal, WeaponHighImpactReserves.Token highImpact, WeaponZenMoment.Token zenMoment, WeaponEnergyPerks.Token energy, WeaponPugilist.Token pugilist, WeaponFiringLine.Token firingLine, WeaponEncore.Token encore, WeaponAmbitiousAssassin.Token assassin, WeaponAdagio.Token adagio, WeaponKillingTally.Token tally, WeaponSympatheticArsenal.PaidToken arsenal, WeaponRelentlessStrikes.Token relentless, WeaponTirelessBlade.Token tireless, WeaponWhirlwindBlade.Token whirlwind, WeaponEnGarde.Token enGarde, WeaponAssassinsBlade.Token assassins, WeaponUnrelenting.Token unrelenting, WeaponShotTraits.Snapshot shotTraits) {
        static final DamageTraits NONE = new DamageTraits(WeaponOneForAll.Token.NONE, WeaponSurrounded.Token.NONE, WeaponSwashbuckler.Token.NONE, WeaponMultikillClip.Token.NONE, WeaponSubsistence.Token.NONE, WeaponRapidHit.Token.NONE, WeaponFrenzy.Token.NONE, WeaponAdrenalineJunkie.Token.NONE, WeaponFocusedFury.Token.NONE, WeaponStatsForAll.Token.NONE, WeaponHeatingUp.Token.NONE, WeaponVorpal.Token.NONE, WeaponHighImpactReserves.Token.NONE, WeaponZenMoment.Token.NONE, WeaponEnergyPerks.Token.NONE, WeaponPugilist.Token.NONE, WeaponFiringLine.Token.NONE, WeaponEncore.Token.NONE, WeaponAmbitiousAssassin.Token.NONE, WeaponAdagio.Token.NONE, WeaponKillingTally.Token.NONE, WeaponSympatheticArsenal.PaidToken.NONE, WeaponRelentlessStrikes.Token.NONE, WeaponTirelessBlade.Token.NONE,WeaponWhirlwindBlade.Token.NONE,WeaponEnGarde.Token.NONE,WeaponAssassinsBlade.Token.NONE,WeaponUnrelenting.Token.NONE,WeaponShotTraits.NONE);
        static DamageTraits capture(ServerPlayer p) { return capture(p,WeaponHighImpactReserves.Token.NONE); }
        static DamageTraits capture(ServerPlayer p, WeaponHighImpactReserves.Token highImpact) { return capture(p,highImpact,WeaponShotTraits.NONE); }
        static DamageTraits capture(ServerPlayer p, WeaponHighImpactReserves.Token highImpact, WeaponShotTraits.Snapshot shotTraits) { return new DamageTraits(WeaponOneForAll.capture(p),WeaponSurrounded.capture(p),WeaponSwashbuckler.capture(p),WeaponMultikillClip.capture(p),WeaponSubsistence.capture(p),WeaponRapidHit.capture(p),WeaponFrenzy.capture(p),WeaponAdrenalineJunkie.capture(p),WeaponFocusedFury.capture(p),WeaponStatsForAll.capture(p), WeaponHeatingUp.capture(p), WeaponVorpal.capture(p),highImpact,WeaponZenMoment.capture(p),WeaponEnergyPerks.capture(p),WeaponPugilist.capture(p),WeaponFiringLine.capture(p),WeaponEncore.capture(p),WeaponAmbitiousAssassin.capture(p),WeaponAdagio.capture(p), WeaponKillingTally.capture(p), WeaponSympatheticArsenal.capture(p), WeaponRelentlessStrikes.capture(p), WeaponTirelessBlade.capture(p),WeaponWhirlwindBlade.capture(p),WeaponEnGarde.capture(p),WeaponAssassinsBlade.capture(p),WeaponUnrelenting.capture(p),shotTraits); }
        DamageTraits perkSplash() { return new DamageTraits(oneForAll,surrounded,swashbuckler,multikillClip,subsistence,rapidHit,frenzy,adrenalineJunkie,WeaponFocusedFury.Token.NONE,statsForAll,heatingUp,vorpal,WeaponHighImpactReserves.Token.NONE,WeaponZenMoment.Token.NONE,energy,pugilist,WeaponFiringLine.Token.NONE,encore,assassin,adagio,tally,arsenal,relentless,tireless,whirlwind,enGarde,assassins,unrelenting,WeaponShotTraits.damageOnly(shotTraits)); }
        float multiplier(ServerPlayer owner, LivingEntity target) { return WeaponWhirlwindBlade.multiplier(owner,whirlwind)*WeaponEnGarde.multiplier(owner,enGarde)*WeaponAssassinsBlade.multiplier(owner,assassins)*WeaponKillingTally.multiplier(owner,tally,target)*WeaponAdagio.multiplier(owner,adagio)* highImpact.multiplier()*vorpal.multiplier(target)*oneForAll.multiplier()*surrounded.multiplier()*swashbuckler.multiplier()*multikillClip.multiplier()*frenzy.multiplier()*adrenalineJunkie.multiplier()*focusedFury.multiplier(); }
    }
    private static final class Shot {
        final ServerPlayer owner;
        final ServerLevel level;
        final WeaponCatalog.Entry entry;
        final WeaponProfile profile;
        final WeaponBallistics.Profile ballistics;
        final ItemStack sourceStack;
        final WeaponKillClip.Token perks;
        final WeaponOutlaw.Token reloadPerk;
        final WeaponFeedingFrenzy.Token feedingFrenzy;
        final WeaponArcherTempo.Token archerTempo;
        final WeaponRampage.Token rampage;
        final DamageTraits damageTraits;
        final WeaponPrecisionReturn.Token precisionReturn;
        final WeaponDragonfly.Token dragonfly;
        final WeaponDemolitionist.Token demolitionist;
        final WeaponTracking.Flight tracking;
        final WaveFrameProfile.Profile waveProfile;
        final BreachGrenade breach;
        final long launchedAt;
        final Vec3 launchForward;
        final Set<Entity> directContacts = Collections.newSetFromMap(new IdentityHashMap<>());
        WeaponWavefront wave;
        int bounces;
        Vec3 position;
        Vec3 velocity;
        double travelled;
        double remaining;
        int life = 100;
        Shot(ServerPlayer owner, WeaponCatalog.Entry entry, WeaponProfile profile, WeaponHighImpactReserves.Token highImpact) {
            this(owner,entry,profile,highImpact,null);
        }
        Shot(ServerPlayer owner, WeaponCatalog.Entry entry, WeaponProfile profile, WeaponHighImpactReserves.Token highImpact, DamageTraits acceptedTraits) {
            this(owner,entry,profile,highImpact,acceptedTraits,WeaponShotTraits.NONE);
        }
        Shot(ServerPlayer owner, WeaponCatalog.Entry entry, WeaponProfile profile, WeaponHighImpactReserves.Token highImpact, DamageTraits acceptedTraits, WeaponShotTraits.Snapshot shotTraits) {
            this.owner = owner; this.level = owner.level(); this.entry = entry; this.profile = profile;
            this.sourceStack=owner.getMainHandItem();
            this.perks=WeaponKillClip.capture(owner);
            this.reloadPerk=WeaponOutlaw.capture(owner);
            this.feedingFrenzy=WeaponFeedingFrenzy.capture(owner);
            this.archerTempo=WeaponArcherTempo.capture(owner);
            this.rampage=WeaponRampage.capture(owner);
            this.damageTraits=acceptedTraits==null?DamageTraits.capture(owner,highImpact,shotTraits):acceptedTraits;
            this.precisionReturn=WeaponPrecisionReturn.capture(owner);
            this.dragonfly=WeaponDragonfly.capture(owner);
            this.demolitionist=WeaponDemolitionist.capture(owner);
            this.tracking=entry.family().equals("rocket_launcher")?WeaponTracking.capture(owner):null;
            this.waveProfile=WaveFrameProfile.of(entry).orElse(null);
            this.breach=BreachGrenade.supports(entry)?new BreachGrenade():null;
            this.launchedAt=now(owner);
            this.launchForward=Vec3.directionFromRotation(0,owner.getYRot());
            this.ballistics=WeaponAiming.ballistics(owner,entry,WeaponShotTraits.range(owner,shotTraits));
            position = owner.getEyePosition(); velocity = WeaponAiming.direction(owner,WeaponShotTraits.accuracy(owner,shotTraits)).scale(WeaponImpulseAmplifier.projectileSpeed(owner,entry,WeaponRangefinder.projectileSpeed(owner,entry,profile.speed())));
            remaining = WeaponBallistics.traceRange(profile);
        }
    }

    public static void init() {
        if (initialized) return;
        initialized = true;
        WeaponCombatItem.init();
        WeaponLoadout.init();
        kim.biryeong.destiny.fx.WaveCrestVfx.init();
        ServerTickEvents.END_SERVER_TICK.register(WeaponRuntime::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> cleanup(handler.getPlayer()));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> { if (entity instanceof ServerPlayer p) cleanup(p); });
        net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents.AFTER_RESPAWN.register((oldOwner,newOwner,alive) -> {
            cleanup(oldOwner);
            if(!alive)WeaponTirelessBlade.spawned(newOwner);
        });
        net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL
                .register((player, from, to) -> cleanup(player));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> clearAll());
        AttackEntityCallback.EVENT.register((player, level, hand, entity, hit) ->
                WeaponItems.entry(player.getMainHandItem()).isPresent() ? InteractionResult.FAIL : InteractionResult.PASS);
        AttackBlockCallback.EVENT.register((player, level, hand, pos, direction) ->
                WeaponItems.entry(player.getMainHandItem()).isPresent() ? InteractionResult.FAIL : InteractionResult.PASS);
        // Intercept containers/trading before vanilla can consume a combat right-click.
        UseBlockCallback.EVENT.register((player, level, hand, hit) -> {
            if (WeaponItems.entry(player.getMainHandItem()).isEmpty()) return InteractionResult.PASS;
            return WeaponCombatItem.INSTANCE.use(level, player, hand);
        });
        UseEntityCallback.EVENT.register((player, level, hand, entity, hit) -> {
            if (WeaponItems.entry(player.getMainHandItem()).isEmpty()) return InteractionResult.PASS;
            return WeaponCombatItem.INSTANCE.use(level, player, hand);
        });
    }

    private static long now(ServerPlayer player) { return player.level().getServer().getTickCount(); }
    /** A player preference changes trigger repetition, never the base profile or cadence. */
    private static boolean heldAutomatic(ServerPlayer player, WeaponCatalog.Entry entry) {
        return WeaponAutoFirePolicy.supportsAutomatic(entry, WeaponAccessibility.enabled(player)||WeaponFullAuto.selected(player));
    }
    /** A setting change is not a shot/release. Retire only unpaid held input; retain
     * already-paid bolts, firing cooldown and an in-progress real reload. The two-hand
     * carrier must observe a fresh press gap before it can acquire another lease. */
    public static void inputSettingsChanged(ServerPlayer player) {
        State s = STATES.get(player.getUUID());
        if (s != null && s.owner == player) {
            detachRemote(s);
            s.releaseHold();
            s.reloadAllowsHeldInput = false;
            s.heartbeatNeedsFreshPress = true;
            s.lastHeartbeat = now(player);
            WeaponBowPresentation.clear(player, s.stack);
        }
        if (player.isUsingItem() && WeaponItems.entry(player.getUseItem()).isPresent()) player.stopUsingItem();
    }
    /** Opt-in diagnostics only: read the existing state, never bind or advance its clock. */
    public static void traceUse(ServerPlayer player, String event, int sequence) {
        if (!kim.biryeong.destiny.debug.WeaponUseTrace.selected(player)) return;
        State s = STATES.get(player.getUUID());
        boolean owned = s != null && s.owner == player && s.level == player.level();
        kim.biryeong.destiny.debug.WeaponUseTrace.record(player, event, sequence,
                owned && s.stack == player.getMainHandItem(), owned && s.holding,
                owned ? s.heldUntil : -1, owned ? s.cycle.firingDeadline() : -1);
    }
    private static boolean available(ServerPlayer player) {
        return player.isAlive() && !player.isRemoved() && !player.isSpectator() && !player.hasDisconnected()
                && !AbilityService.inSuper(player) && WeaponLoadout.canUse(player);
    }
    private static State bind(ServerPlayer player) {
        State s = STATES.get(player.getUUID());
        if (s == null || s.owner != player) {
            if (s != null) s.cancel();
            s = new State(player); STATES.put(player.getUUID(), s);
        }
        if (s.stack != player.getMainHandItem() || s.level != player.level()) {
            if (s.level == player.level() && WeaponItems.entry(s.stack).isPresent())
                s.cadence.remember(s.stack, s.cycle.firingDeadline(), now(player), SwordItems.isSword(s.stack));
            s.cancel(); s.stack = player.getMainHandItem(); s.level = player.level();
            s.cycle.restoreFiringDeadline(s.cadence.deadline(s.stack, now(player)));
            s.glaive.bind(GlaiveItems.energy(s.stack),now(player));
        }
        if (SwordItems.isSword(s.stack) && !s.swordBound) {
            s.sword.bind(SwordItems.energy(s.stack),SwordItems.delay(s.stack),now(player));
            s.swordBound=true;
        }
        return s;
    }
    public static boolean beginUse(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return false;
        traceUse(player, "runtime.begin", -1);
        var entry = WeaponItems.entry(player.getMainHandItem());
        if (entry.isEmpty() || !available(player)) return false;
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if (WeaponHandling.blocked(player)) return false;
        State s = bind(player);
        if (s.holding) return true; // Duplicate use packets cannot restart a charge or bypass a cadence.
        var p = WeaponProfile.forEntry(entry.get());
        if (entry.get().family().equals("sword")) {
            // Keep a real native use session even on denial: a held RMB never becomes another heavy.
            s.holding=true; s.fired=true;
            swordAttack(player,s,entry.get(),true);
            return true;
        }
        var ammo = WeaponItems.magazine(s.stack, p);
        s.cycle.interruptReloadForShot(now(player), ammo);
        // Actual native input can hold through shot-caused automatic reload or
        // bow nocking. A bow buffers a DRAW, never a shot or elapsed charge time.
        if (s.cycle.reloading() && s.reloadAllowsHeldInput
                && (heldAutomatic(player, entry.get()) || entry.get().family().equals("bow"))) {
            s.holding=true; s.fired=false; updateBow(player,s); return true;
        }
        if (!s.cycle.reloading()) {
            WeaponReloadPresentation.clear(player,s.stack);
            WeaponInsertPresentation.clear(player,s.stack);
        }
        if (!s.cycle.ready(now(player))) return false;
        if (ammo.rounds() == 0) { reload(player); return false; }
        if (p.mode() == WeaponProfile.Mode.PROJECTILE && activeProjectiles(player) >= MAX_PROJECTILES_PER_PLAYER) return false;
        s.holding = true; s.fired = false;
        if (p.chargeTicks() > 0) {
            if(s.cycle.startCharge(now(player))) {
                if(entry.get().family().equals("bow")) s.acceptedBowDraw=WeaponArcherTempo.draw(player,entry.get(),p);
                else if(entry.get().family().equals("fusion_rifle") || entry.get().family().equals("linear_fusion_rifle")) {
                    s.chargeEntry=entry.get(); s.acceptedCharge=WeaponBackupPlan.charge(player,entry.get(),p);
                }
            }
            DestinySounds.weapon(player, entry.get(), "charge");
        } else s.fired = fire(player, s, entry.get(), p);
        updateBow(player, s);
        return true;
    }
    /** Charged-crossbow clients repeat RMB every four ticks; the server grants only a six-tick lease. */
    public static boolean heartbeatUse(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) return false;
        if (WeaponItems.entry(player.getMainHandItem()).isEmpty() || !WeaponModels.twoHanded(player.getMainHandItem()) || !available(player)) return false;
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if (WeaponHandling.blocked(player)) return false;
        State s = bind(player);
        // Reload owns its deadline, independently of the short firing lease. Only
        // shot-caused automatic reload accepts renewed real input for later firing.
        // Manual/empty-trigger reload retains its existing no-latent-shot behavior.
        long tick = now(player);
        boolean freshPress = tick - s.lastHeartbeat > HEARTBEAT_LEASE_TICKS;
        s.lastHeartbeat = tick;
        if(s.heartbeatNeedsFreshPress&&!freshPress)return false;
        if(freshPress)s.heartbeatNeedsFreshPress=false;
        if (s.cycle.reloading()) {
            var p = WeaponProfile.forEntry(WeaponItems.entry(s.stack).orElseThrow());
            var ammo = WeaponItems.magazine(s.stack, p);
            if (!freshPress || !s.cycle.interruptReloadForShot(tick, ammo)) {
                if (s.reloadAllowsHeldInput && heldAutomatic(player, WeaponItems.entry(s.stack).orElseThrow())) {
                    s.holding=true; s.heldUntil=tick+HEARTBEAT_LEASE_TICKS;
                    return true;
                }
                s.heartbeatNeedsFreshPress=true;
                s.heldUntil = -1; return false;
            }
        }
        if (s.heldUntil >= 0 && tick >= s.heldUntil) endHeldInput(s);
        // Renew even when cooling down, so a legitimate held press can become ready later.
        s.heldUntil = tick + HEARTBEAT_LEASE_TICKS;
        if (!s.holding) {
            long lease = s.heldUntil;
            boolean accepted = beginUse(player);
            // Empty-trigger beginUse may have started reload and deliberately cleared the lease.
            s.heldUntil = s.cycle.reloading() ? -1 : lease;
            return accepted;
        }
        return true;
    }
    public static void continueUse(ServerPlayer player) {
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if (WeaponHandling.blocked(player)) return;
        var entry = WeaponItems.entry(player.getMainHandItem());
        State s = STATES.get(player.getUUID());
        if (entry.isEmpty() || s == null || s.owner != player || !s.holding) return;
        if (!available(player) || s.stack != player.getMainHandItem() || s.level != player.level()) { s.cancel(); player.stopUsingItem(); return; }
        var p = WeaponProfile.forEntry(entry.get());
        if(entry.get().family().equals("sword"))return; // Heavy is press-only, never a held repeat.
        if(entry.get().family().equals("bow")) {
            if(player.isUsingItem()&&player.getUseItem()==s.stack&&s.cycle.ready(now(player))
                    && !s.cycle.charging()&&WeaponItems.magazine(s.stack,p).rounds()>0) {
                if(s.cycle.startCharge(now(player)))s.acceptedBowDraw=WeaponArcherTempo.draw(player,entry.get(),p);
                DestinySounds.weapon(player,entry.get(),"charge");
            }
            updateBow(player,s);
            return;
        }
        boolean automatic = heldAutomatic(player, entry.get());
        if (p.chargeTicks() > 0) {
            // A repeated fusion trigger must acquire a NEW complete charge after the
            // paid burst/cadence/reload has finished. Held input never skips charge,
            // spends per bolt, or carries elapsed time through a reload.
            if (automatic && !s.cycle.charging() && s.cycle.ready(now(player))
                    && WeaponItems.magazine(s.stack, p).rounds() > 0 && s.cycle.startCharge(now(player))) {
                s.fired = false;
                s.chargeEntry = entry.get(); s.acceptedCharge = WeaponBackupPlan.charge(player,entry.get(),p);
                DestinySounds.weapon(player, entry.get(), "charge");
            }
            var accepted=entry.get().equals(s.chargeEntry)&&s.acceptedCharge!=null?s.acceptedCharge:p;
            if (!s.fired && s.cycle.charged(now(player), accepted.chargeTicks()))
                s.fired = fire(player, s, entry.get(), accepted);
        } else if (automatic) fire(player, s, entry.get(), p);
    }
    public static void releaseUse(ServerPlayer player, ItemStack released) {
        traceUse(player, "runtime.release.before", -1);
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        State s = STATES.get(player.getUUID());
        if (s == null || s.owner!=player || !s.holding || s.stack!=released) return;
        if (s.stack == released && player.getMainHandItem() == released && s.level == player.level() && available(player)) {
            if(!WeaponHandling.blocked(player))releaseRemote(s);
            else detachRemote(s);
            WeaponItems.entry(released).filter(e -> e.family().equals("bow")).ifPresent(entry -> {
                var p = s.acceptedBowDraw!=null?s.acceptedBowDraw:WeaponProfile.forEntry(entry);
                long drawn=s.cycle.chargeElapsed(now(player));
                if (drawn>=0) fire(player, s, entry, WeaponBowDraw.shot(p,drawn));
            });
        }
        if(s.remoteShot!=null)detachRemote(s);
        WeaponDynamicSway.released(player,released);
        WeaponTapTheTrigger.released(player,released);
        s.holding=false; s.heldUntil=-1; s.cycle.cancelCharge(); s.acceptedBowDraw=null;
        traceUse(player, "runtime.release.after", -1);
        if (s.stack == player.getMainHandItem() && s.level == player.level() && available(player)) updateBow(player,s);
        else WeaponBowPresentation.clear(player,s.stack);
    }
    /** Crouch releases native consumption before the Guardian melee input, without firing a bow. */
    public static void cancelUseForSkill(ServerPlayer player) {
        WeaponAiming.suspend(player);
        State s = STATES.get(player.getUUID());
        if (s != null && s.owner == player) { s.cancel();s.glaive.stop(); }
        if (player.isUsingItem() && player.getUseItem().is(WeaponCombatItem.INSTANCE)) player.stopUsingItem();
    }
    /** A valid grenade refill can retire only its ORIGINAL weapon's pending work.
     * State.cancel preserves firing deadline; it never invokes a manual reload callback. */
    static void cancelForGrenadeRefill(ServerPlayer player, ItemStack original) {
        cancelForTraitRefill(player,original);
    }
    /** Reserve-only trait refill, never a manual reload proc or cadence reset. */
    static void cancelForTraitRefill(ServerPlayer player, ItemStack original) {
        State s=STATES.get(player.getUUID());
        if (s!=null && s.owner==player && s.level==player.level() && s.stack==original) {
            s.cancel(); s.glaive.stop();
            if (player.isUsingItem() && player.getUseItem()==original) player.stopUsingItem();
        }
    }
    /** Accepted Marksman's Dodge effect, not a player command or a timed reload.
     * Current D2 reloads ALL equipped weapons and collects nearby personal ammo at activation.
     * Uses real stacks/reserves, never resets cadence or buffers a later shot. Standalone OP
     * fixtures affect their held live weapon only; ordinary gameplay uses the three slots.
     * @return actual rounds moved into reloadable magazines (not pickup grant or sword ammo)
     */
    public static int reloadFromMarksmanDodge(ServerPlayer player) {
        if (!player.isAlive() || player.isRemoved() || player.isSpectator() || player.hasDisconnected()
                || AbilityService.inSuper(player)) return 0;
        WeaponAiming.suspend(player);
        State state = STATES.get(player.getUUID());
        if (state != null && state.owner == player) {
            // Preserve readyAt, but retire every old reload/charge/burst/held-input candidate.
            // Do not recreate the State: that would erase the shared firing cooldown.
            // Dodge cancels pending work, not a surviving funded item cosmetic.
            // Keep the existing binding/cache offset so a denied charged refill is byte-pure.
            state.cancel(state.stack == player.getMainHandItem()); state.glaive.stop();
        }
        if (player.isUsingItem() && WeaponItems.entry(player.getUseItem()).isPresent()) player.stopUsingItem();
        List<ItemStack> candidates = WeaponLoadout.enabled(player)
                ? WeaponLoadout.equipped(player).stream().map(WeaponLoadout.Equipped::stack).toList()
                : WeaponItems.entry(player.getMainHandItem()).isPresent() ? List.of(player.getMainHandItem()) : List.of();
        Set<ItemStack> seen = Collections.newSetFromMap(new IdentityHashMap<>());
        List<ItemStack> reloadable = candidates.stream().filter(seen::add)
                .filter(stack -> WeaponItems.entry(stack).filter(e -> !e.family().equals("sword")).isPresent()).toList();
        int loaded = 0;
        // One bounded activation transaction: first use existing reserves to make pickup room,
        // collect once, then fill any remaining magazine space from the newly collected ammo.
        // The precise ordering is authored; official notes specify the two effects, not internals.
        for (var stack : reloadable) loaded += fillDodgeMagazine(player,stack);
        int picked = AmmoEconomy.collectForMarksmanDodge(player);
        for (var stack : reloadable) {
            loaded += fillDodgeMagazine(player,stack);
            WeaponReloadPresentation.clear(player,stack);
            WeaponBowPresentation.clear(player,stack);
        }
        if (WeaponLoadout.canUse(player) && WeaponItems.entry(player.getMainHandItem())
                .filter(WeaponBowPresentation::supports).isPresent()) updateBow(player, bind(player));
        if (loaded > 0 || picked > 0) {
            player.getInventory().setChanged(); player.containerMenu.broadcastChanges();
        }
        return loaded;
    }

    private static int fillDodgeMagazine(ServerPlayer player,ItemStack stack) {
        // Do not silently decompose or add ordinary rounds to a paid Honed projectile.
        if(WeaponIzanagi.charge(stack)>0)return 0;
        var entry = WeaponItems.entry(stack).orElseThrow();
        var ammo = WeaponItems.magazine(stack, WeaponProfile.forEntry(entry));
        int moved = ammo.reload();
        if (moved > 0) {
            WeaponItems.save(stack, ammo);
            WeaponKillClip.reloaded(player,stack);
            WeaponFocusedFury.reloadStarted(player,stack);
            WeaponKillingTally.reloadStarted(player,stack);
            WeaponMultikillClip.reloaded(player,stack);
            WeaponAce.instantReload(player,stack);
        }
        return moved;
    }

    /** Sympathetic Arsenal's accepted source reload refills other equipped ranged items.
     * These are reserve transfers, not nested reload events, ability activations or ammo generation. */
    private static int refillStowedArsenal(ServerPlayer player) {
        List<ItemStack> candidates;
        if(WeaponLoadout.enabled(player)) candidates=WeaponLoadout.equipped(player).stream().map(WeaponLoadout.Equipped::stack).toList();
        else {
            var hotbar=new ArrayList<ItemStack>();
            for(int slot=0;slot<9;slot++)hotbar.add(player.getInventory().getItem(slot));
            candidates=hotbar;
        }
        Set<ItemStack> seen=Collections.newSetFromMap(new IdentityHashMap<>());
        int moved=0;
        for(var stack:candidates) {
            if(stack==player.getMainHandItem() || !seen.add(stack) || SwordItems.isSword(stack)
                || WeaponIzanagi.charge(stack)>0)continue;
            var entry=WeaponItems.entry(stack).orElse(null);if(entry==null)continue;
            var ammo=WeaponItems.magazine(stack,WeaponProfile.forEntry(entry));
            int amount=ammo.reload();
            if(amount>0) { WeaponItems.save(stack,ammo);moved+=amount; }
        }
        if(moved>0) { player.getInventory().setChanged();player.containerMenu.broadcastChanges(); }
        return moved;
    }

    /** Called by the validated native hotbar handler BEFORE changing the selected slot.
     * Observe even an away-and-back swap within one server tick; polling identity misses it. */
    public static void selectedSlotChanging(ServerPlayer player,int slot) {
        if (slot < 0 || slot >= 9) return;
        WeaponKillClip.selecting(player,slot);
        WeaponAce.selecting(player,slot);
        WeaponOutlaw.selecting(player,slot);
        WeaponArcherTempo.selecting(player,slot);
        WeaponHolster.selecting(player,slot);
        WeaponHandling.selecting(player,slot);
        if(slot==player.getInventory().getSelectedSlot())return;
        WeaponSurrounded.stowing(player,player.getMainHandItem()); WeaponThreatDetector.stowing(player,player.getMainHandItem());
        WeaponFocusedFury.stowing(player,player.getMainHandItem());
        WeaponTapTheTrigger.changed(player,player.getMainHandItem()); WeaponZenMoment.changed(player,player.getMainHandItem());
        WeaponSwashbuckler.stowing(player,player.getMainHandItem());
        WeaponMultikillClip.stowing(player,player.getMainHandItem());
        WeaponGraveRobber.changed(player,player.getMainHandItem());
        WeaponPugilist.stowing(player,player.getMainHandItem());
        WeaponAssassinsBlade.stowing(player,player.getMainHandItem()); WeaponUnrelenting.stowing(player,player.getMainHandItem()); WeaponWhirlwindBlade.stowing(player,player.getMainHandItem()); WeaponEnGarde.stowing(player,player.getMainHandItem()); WeaponOpeningShot.stowing(player,player.getMainHandItem()); WeaponBoxBreathing.stowing(player,player.getMainHandItem()); WeaponHeadseeker.stowing(player,player.getMainHandItem()); WeaponOsmosis.stowing(player,player.getMainHandItem()); WeaponSteadyHands.stowing(player,player.getMainHandItem()); WeaponDynamicSway.released(player,player.getMainHandItem());
        WeaponKillingTally.stowing(player,player.getMainHandItem()); WeaponSympatheticArsenal.stowing(player,player.getMainHandItem());
        WeaponAdagio.stowing(player,player.getMainHandItem()); WeaponClownCartridge.stowing(player,player.getMainHandItem());
        WeaponAiming.inventoryStowing(player,player.getMainHandItem());
        State s=STATES.get(player.getUUID());
        if(s!=null&&s.owner==player&&(SwordItems.isSword(s.stack)
                ||WeaponAccessibility.enabled(player)||WeaponFullAuto.selected(player)
                ||WeaponItems.entry(s.stack).filter(WeaponExotics::izanagi).isPresent()))s.cancel();
    }
    /** An accepted inventory mutation can stow/restore the exact object within one tick. */
    public static void inventoryStowing(ServerPlayer player,ItemStack previous) {
        WeaponBackupPlan.stowing(player,previous);
        WeaponQuickdraw.changed(player,previous);
        WeaponSurrounded.stowing(player,previous); WeaponThreatDetector.stowing(player,previous);
        WeaponFocusedFury.stowing(player,previous);
        WeaponTapTheTrigger.changed(player,previous); WeaponZenMoment.changed(player,previous);
        WeaponSwashbuckler.stowing(player,previous);
        WeaponMultikillClip.stowing(player,previous);
        WeaponGraveRobber.changed(player,previous);
        WeaponPugilist.stowing(player,previous);
        WeaponAssassinsBlade.stowing(player,previous); WeaponUnrelenting.stowing(player,previous); WeaponWhirlwindBlade.stowing(player,previous); WeaponEnGarde.stowing(player,previous); WeaponOpeningShot.stowing(player,previous); WeaponBoxBreathing.stowing(player,previous); WeaponHeadseeker.stowing(player,previous); WeaponOsmosis.stowing(player,previous); WeaponSteadyHands.changed(player,previous); WeaponPulseMonitor.changed(player,previous); WeaponDynamicSway.released(player,previous);
        WeaponKillingTally.stowing(player,previous); WeaponSympatheticArsenal.stowing(player,previous);
        WeaponAdagio.stowing(player,previous); WeaponClownCartridge.stowing(player,previous);
        WeaponAiming.inventoryStowing(player,previous);
        var s=STATES.get(player.getUUID());
        if(s!=null&&s.owner==player&&s.stack==previous
                &&(s.acceptedCharge!=null || WeaponAccessibility.enabled(player)||WeaponFullAuto.selected(player)
                ||WeaponItems.entry(previous).filter(WeaponExotics::izanagi).isPresent()))s.cancel();
    }
    /** Vanilla Ctrl+Q alternate weapon action; Q remains ordinary reload. */
    public static boolean reloadHoned(ServerPlayer player) {
        if(!available(player) || !WeaponIzanagi.canStart(player))return false;
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if(WeaponHandling.blocked(player))return false;
        var s=bind(player);
        // An empty shot can already have begun its automatic ordinary reload.
        // Accept the alternate action without forcing a complete normal reload first.
        // Iza has no early ordinary ammo credit; restart at the explicit Honed deadline.
        if(s.cycle.reloading())s.cancel();
        // bind may retire an old pending session; check the exact new item again.
        if(!WeaponIzanagi.canStart(player)||!s.cycle.startExternalReload(now(player),WeaponIzanagi.RELOAD_TICKS))return false;
        WeaponIzanagi.started(player);
        detachRemote(s);s.emptyReloadPending=false;s.reloadAllowsHeldInput=false;s.heartbeatNeedsFreshPress=true;
        s.releaseHold();player.stopUsingItem();WeaponAiming.suspend(player);
        WeaponReloadPresentation.update(player,s.stack,true,0);
        WeaponIzanagiPresentation.update(player,s.stack,WeaponIzanagiPresentation.Mode.HONED,0);
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        if(!kim.biryeong.destiny.sound.ReloadAudio.startHoned(player,entry,WeaponIzanagi.RELOAD_TICKS))
            DestinySounds.weapon(player,entry,"honed_reload");
        return true;
    }
    public static boolean reload(ServerPlayer player) {
        var entry = WeaponItems.entry(player.getMainHandItem());
        if (entry.isEmpty() || !available(player) || entry.get().family().equals("sword")) return false;
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if (WeaponHandling.blocked(player)) return false;
        State s = bind(player);
        var p = WeaponProfile.forEntry(entry.get());
        // The original bow reload command lets the drawn string down. Do not
        // fire/reload/refill a full bow, or leave an armed buffered draw behind.
        if(entry.get().family().equals("bow")&&s.holding
                &&(s.cycle.charging()||s.cycle.reloading())) {
            s.releaseHold(); player.stopUsingItem(); updateBow(player,s); return true;
        }
        return startReload(player,s,entry.get(),p,false);
    }
    private static boolean startReload(ServerPlayer player,State s,WeaponCatalog.Entry entry,
                                       WeaponProfile p,boolean shotCaused) {
        if (entry.family().equals("sword")) return false;
        if(WeaponExotics.izanagi(entry)&&WeaponIzanagi.charge(s.stack)>0)return false;
        var ammo = WeaponItems.magazine(s.stack, p);
        var plan=WeaponAce.plan(player,entry,WeaponFrenzy.plan(player,entry,WeaponPerpetualMotion.plan(player,entry,WeaponRapidHit.plan(player,entry,WeaponFeedingFrenzy.plan(player,entry,WeaponOutlaw.plan(player,entry,p))))));
        plan=WeaponStatsForAll.plan(player,entry,plan);
        WeaponThreatDetector.update(player);
        plan=WeaponThreatDetector.plan(player,entry,plan);
        // Observe charged abilities now; the accepted cycle retains this immutable plan.
        plan=WeaponSurplus.plan(player,entry,plan);
        plan=WeaponElementalCapacitor.plan(player,entry,plan);
        WeaponEnsemble.update(player);
        plan=WeaponEnsemble.plan(player,entry,plan);
        plan=WeaponCompulsiveReloader.plan(player,entry,plan);
        plan=WeaponImpulseAmplifier.plan(player,entry,plan);
        plan=WeaponSympatheticArsenal.plan(player,entry,plan);
        if (!s.cycle.startReload(now(player), p, ammo, plan, ReloadCreditProfile.ammoTicks(entry,plan))) return false;
        s.clownReload=WeaponClownCartridge.acceptedReload(player);
        s.arsenalReload=WeaponSympatheticArsenal.acceptedReload(player);
        WeaponKillingTally.reloadStarted(player,s.stack);
        s.assassinReload=WeaponAmbitiousAssassin.acceptedReload(player);
        WeaponAce.reloadStarted(player,s.stack);
        WeaponFocusedFury.reloadStarted(player,s.stack);
        detachRemote(s); // A reload action is not the original trigger's release.
        s.emptyReloadPending=false;
        s.reloadAllowsHeldInput=shotCaused&&(heldAutomatic(player,entry)||entry.family().equals("bow"));
        s.heartbeatNeedsFreshPress=!s.reloadAllowsHeldInput;
        WeaponAiming.suspend(player);
        boolean liveHold=s.holding&&(WeaponModels.twoHanded(s.stack)?s.heldUntil>now(player)
                :player.isUsingItem()&&player.getUseItem()==s.stack);
        // Keep an already-fired native semiauto consumption session alive until
        // its real release, so a held button cannot become a new trigger merely
        // because the server finished reloading. fired stays true throughout.
        boolean nativeFiredHold=shotCaused&&!WeaponModels.twoHanded(s.stack)&&liveHold
                &&s.fired&&!entry.family().equals("bow");
        if (!(s.reloadAllowsHeldInput&&liveHold)&&!nativeFiredHold) {
            s.releaseHold(); player.stopUsingItem();
        }
        WeaponReloadPresentation.update(player,s.stack, true, 0);
        WeaponIzanagiPresentation.update(player,s.stack,WeaponIzanagiPresentation.Mode.RELOAD,0);
        WeaponInsertPresentation.start(player,s.stack);
        updateBow(player,s);
        if(!kim.biryeong.destiny.sound.ReloadAudio.start(player,entry,s.cycle.reloadPhaseTicks())
                && !kim.biryeong.destiny.sound.ShotgunReloadAudio.handles(entry))
            DestinySounds.weapon(player, entry, "reload");
        return true;
    }
    /** True consumes a live-item punch; super and crouched Guardian skill inputs retain priority. */
    public static boolean onPunch(ServerPlayer player) {
        var entry = WeaponItems.entry(player.getMainHandItem());
        if (entry.isEmpty() || AbilityService.inSuper(player) || player.isShiftKeyDown() && Guardians.isGuardian(player)) return false;
        if (!available(player)) return true;
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        if (WeaponHandling.blocked(player)) return true;
        if (!List.of("sword", "glaive").contains(entry.get().family())) return true;
        State s = bind(player);
        var p = WeaponProfile.forEntry(entry.get());
        if (entry.get().family().equals("glaive")) {
            int multiplier=s.glaive.melee(now(player));
            if(multiplier==0)return true;
            s.cancel(); // A melee cancels a pending reload/charge, without erasing the ranged cooldown.
            p = new WeaponProfile(WeaponProfile.Mode.MELEE, 7*multiplier, 12, p.magazine(), p.reserve(), p.reloadTicks(), 3.5, 0, 1, 1, 0, 0, 0, 0, false);
            DestinySounds.orVanilla(player.level(),player.getEyePosition(),"weapon.glaive.melee",
                    net.minecraft.sounds.SoundEvents.PLAYER_ATTACK_SWEEP,.65f,multiplier==2?.8f:1.2f);
            emit(player,entry.get(),p,false);
            return true;
        }
        swordAttack(player,s,entry.get(),false);
        return true;
    }
    private static boolean swordAttack(ServerPlayer player, State s, WeaponCatalog.Entry entry, boolean heavy) {
        WeaponEnGarde.update(player);
        if (!available(player) || s.stack != player.getMainHandItem() || player.isShiftKeyDown()
                || s.swordContact!=null || kim.biryeong.destiny.fx.PlayerAnimations.foreignToSword(player)
                || player.getCamera()!=player || kim.biryeong.minigamelib.cinematic.CameraViews.get(player)!=null) return false;
        var base=WeaponProfile.forEntry(entry);
        var profile=SwordProfile.of(entry);
        if (heavy && profile.shape()==SwordProfile.Shape.CASTER
                && activeProjectiles(player)>=MAX_PROJECTILES_PER_PLAYER) return false;
        var ammo=WeaponItems.magazine(s.stack,base);
        boolean empty=ammo.rounds()==0;
        // Every rejection precedes energy/combo/ammo mutation. Empty swords have only a weak light.
        if (heavy && empty) return false;
        var cadence=profile.attack(base,base.damage(),heavy);
        if (!(empty?s.cycle.emptyMelee(now(player),cadence)
                :s.cycle.fire(now(player),cadence,ammo,heavy?profile.heavyCost(s.sword.energy()):1))) return false;
        if (!empty) WeaponItems.save(s.stack,ammo);
        float damage;
        if (heavy) damage=base.damage()*profile.heavyMultiplier()*profile.power(s.sword.heavy(now(player)));
        else {
            int combo=s.sword.light(now(player));
            damage=empty?3:base.damage()*(combo==3?1.25f:1);
        }
        SwordItems.save(s.stack,s.sword.energy(),s.sword.rechargeRemaining(now(player)));
        player.swing(InteractionHand.MAIN_HAND,new net.minecraft.world.item.component.SwingAnimation(
                net.minecraft.world.item.SwingAnimationType.WHACK,heavy?6:4),true);
        boolean visual=kim.biryeong.destiny.fx.SwordPresentation.attack(player,profile.shape(),heavy,s.sword.combo());
        s.swordContact=new SwordContact(player,entry,base,profile,heavy,empty,damage,s.sword.combo(),visual);
        return true;
    }
    /** Main-thread, at most one accepted contact. Cost/cadence are already committed.
     * A cancelled windup is not refunded and cannot survive a rebind or skill handoff. */
    private static void tickSwordContact(ServerPlayer player,State s) {
        SwordContact contact=s.swordContact;
        if(contact==null)return;
        boolean invalid=now(player)<contact.acceptedAt||player.isShiftKeyDown()
                ||kim.biryeong.destiny.fx.PlayerAnimations.foreignToSword(player)
                ||player.getCamera()!=player||kim.biryeong.minigamelib.cinematic.CameraViews.get(player)!=null
                ||player.position().distanceToSqr(contact.previous)>64
                ||WeaponItems.entry(s.stack).filter(e->e.id().equals(contact.entry.id())&&e.family().equals("sword")).isEmpty();
        contact.previous=player.position();
        if(invalid) {
            s.swordContact=null;
            kim.biryeong.destiny.fx.PlayerAnimations.cancelSwordAttack(player);
            return;
        }
        if(now(player)-contact.acceptedAt<contact.delay)return;
        // A call after this tick's animation listener has one fewer real pose tick
        // than an ordinary native-input call. Wait for the owned clock, not just
        // the server timestamp. Missing/closed cosmetic models retain timed gameplay.
        if(contact.visualFrames>=0&&kim.biryeong.destiny.fx.PlayerAnimations.swordPlaying(player)
                &&kim.biryeong.destiny.fx.PlayerAnimations.serverFrames(player)-contact.visualFrames<contact.delay*2L)return;
        s.swordContact=null; // Consume BEFORE damage callbacks/projectile creation can re-enter.
        swordContact(player,contact);
    }
    private static void swordContact(ServerPlayer player,SwordContact contact) {
        var entry=contact.entry;
        var base=contact.base;
        var profile=contact.profile;
        float damage=contact.damage;
        var damageTraits=contact.damageTraits;
        // A cancelled windup cannot leave a delayed sound. These named one-shots
        // begin at authored contact, not at input acceptance or per target hit.
        if(!contact.heavy||profile.shape()!=SwordProfile.Shape.CASTER)
            kim.biryeong.destiny.sound.SwordSounds.contact(player,entry,contact.heavy,contact.empty,contact.grounded);
        if(!contact.heavy) {
            // Keep legal start contacts when lunging past nearby side enemies. This authored
            // start/end sweep is deduplicated; one enemy never pays damage twice.
            var contacts=new LinkedHashSet<>(SwordMelee.cleave(player));
            if(!contact.empty) { SwordMelee.lunge(player);contacts.addAll(SwordMelee.cleave(player)); }
            int hits=0;
            for(var target:contacts) {
                if(hits++>=SwordArc.MAX_HITS)break;
                apply(player,target,damage,false,SwordMelee.point(target),AmmoGeneration.weapon(entry),damageTraits);
            }
            return;
        }
        if (profile.shape()==SwordProfile.Shape.DASH) SwordMelee.move(player,player.getLookAngle(),1.6);
        if (profile.shape()==SwordProfile.Shape.UPPERCUT || profile.shape()==SwordProfile.Shape.DASH)
            emit(player,entry,profile.attack(base,damage,true),false,0,WeaponHighImpactReserves.Token.NONE,damageTraits);
        else if (profile.shape()==SwordProfile.Shape.CASTER) {
            if(activeProjectiles(player)<MAX_PROJECTILES_PER_PLAYER) {
                kim.biryeong.destiny.sound.SwordSounds.contact(player,entry,true,contact.empty,contact.grounded);
                SHOTS.add(new Shot(player,entry,profile.caster(base,damage),WeaponHighImpactReserves.Token.NONE,damageTraits));
            }
        }
        else {
            // Authored slam/spin: one damage transaction per enemy, never through walls.
            Vec3 center=player.position().add(0,.5,0);
            double radius=profile.shape()==SwordProfile.Shape.SLAM?3:3.5;
            for(var target:Combat.enemiesNear(player.level(),player,center,radius)) {
                if(!enemy(player,target))continue;
                Vec3 point=target.position().add(0,target.getBbHeight()*.5,0);
                if(!player.level().hasChunkAt(BlockPos.containing(point)))continue;
                var wall=player.level().clip(new ClipContext(center,point,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,player));
                if(wall.getType()!=HitResult.Type.MISS&&center.distanceToSqr(wall.getLocation())+1e-3<center.distanceToSqr(point))continue;
                apply(player,target,damage,false,point,AmmoGeneration.weapon(entry),damageTraits);
            }
            Fx.ring(player.level(),center,radius,WeaponCharacteristics.of(entry).damage().color(),24);
        }
    }
    private static boolean fire(ServerPlayer player, State s, WeaponCatalog.Entry entry, WeaponProfile p) {
        if (!available(player) || WeaponHandling.blocked(player) || s.stack != player.getMainHandItem()) return false;
        if (p.mode() == WeaponProfile.Mode.PROJECTILE && activeProjectiles(player) >= MAX_PROJECTILES_PER_PLAYER) return false;
        var ammo = WeaponItems.magazine(s.stack, p);
        int roundsBefore=ammo.rounds();
        p=WeaponFullAuto.firingProfile(player,entry,p);
        p=WeaponAdagio.firingProfile(player,entry,p);
        if (!s.cycle.fire(now(player), p, ammo)) return false;
        WeaponItems.save(s.stack, ammo);
        var shotTraits=WeaponShotTraits.paid(player,entry,roundsBefore,true);
        // HIR belongs to this genuinely paid cartridge, before any precision refund or later bolt.
        s.paidHighImpact=WeaponHighImpactReserves.capture(player,roundsBefore,WeaponProfile.forEntry(entry).magazine());
        traceUse(player, "runtime.paid", -1);
        WeaponTapTheTrigger.paidEmission(player,entry);
        WeaponBackupPlan.paidEmission(player,entry);
        updateBow(player,s);
        if(ammo.rounds()==0&&p.mode()!=WeaponProfile.Mode.MELEE)s.emptyReloadPending=true;
        if(entry.family().equals("glaive"))s.glaive.shot(now(player));
        emit(player, entry, p, true,0,s.paidHighImpact,null,shotTraits);
        WeaponAiming.shot(player,entry,WeaponShotTraits.stability(player,shotTraits),WeaponShotTraits.growth(player,shotTraits));
        return true;
    }
    private static void emit(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile p, boolean playFire) {
        emit(player, entry, p, playFire, 0);
    }
    private static void emit(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile p, boolean playFire, int boltIndex) {
        emit(player,entry,p,playFire,boltIndex,WeaponHighImpactReserves.Token.NONE);
    }
    private static void emit(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile p, boolean playFire, int boltIndex, WeaponHighImpactReserves.Token highImpact) {
        emit(player,entry,p,playFire,boltIndex,highImpact,null);
    }
    private static void emit(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile p, boolean playFire, int boltIndex,
                             WeaponHighImpactReserves.Token highImpact, DamageTraits acceptedTraits) {
        emit(player,entry,p,playFire,boltIndex,highImpact,acceptedTraits,WeaponShotTraits.NONE);
    }
    private static void emit(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile p, boolean playFire, int boltIndex,
                             WeaponHighImpactReserves.Token highImpact, DamageTraits acceptedTraits, WeaponShotTraits.Snapshot shotTraits) {
        int honed=p.mode()==WeaponProfile.Mode.HITSCAN?WeaponIzanagi.shot(player,entry):0;
        if (WeaponExotics.izanagi(entry))
            WeaponIzanagiPresentation.update(player,player.getMainHandItem(),WeaponIzanagiPresentation.Mode.IDLE,0);
        // A successful shotgun shot also cancels an already-started final closing tail.
        // Denied input never silences it; emitter removal cannot stop another owner.
        if (playFire && kim.biryeong.destiny.sound.ShotgunReloadAudio.handles(entry))
            kim.biryeong.destiny.sound.ReloadAudio.stop(player);
        if (playFire) DestinySounds.weapon(player, entry, honed>=2?"honed_fire":"fire");
        if (p.mode() == WeaponProfile.Mode.PROJECTILE) {
            var shot=new Shot(player,entry,p,highImpact,acceptedTraits,shotTraits);
            SHOTS.add(shot);
            var state=STATES.get(player.getUUID());
            if(shot.breach!=null&&state!=null&&state.owner==player&&state.stack==shot.sourceStack&&state.holding) {
                detachRemote(state);
                state.remoteShot=shot;
            }
            return;
        }
        var mulligan=p.mode()==WeaponProfile.Mode.HITSCAN?WeaponMulligan.capture(player,entry):WeaponMulligan.Token.NONE;
        Vec3 from = player.getEyePosition();
        // Deterministic symmetric spread; damage is aggregated so pellets do not fight vanilla immunity.
        Map<LivingEntity, HitDamage> damage = new LinkedHashMap<>();
        var ace = p.mode() == WeaponProfile.Mode.HITSCAN ? WeaponAce.shot(player,entry) : WeaponAce.Token.NONE;
        var ballistics = WeaponAce.ballistics(WeaponAiming.ballistics(player,entry,WeaponShotTraits.range(player,shotTraits)),ace);
        Vec3 impactPosition = null;
        var payload=WeaponPayload.capture(player,entry,p);
        HitResult payloadHit=null;
        var shotgunShape=ShotgunPatternProfile.shape(entry);
        for (int i = 0; i < p.pellets(); i++) {
            Vec3 direction = WeaponAiming.direction(player,WeaponShotTraits.accuracy(player,shotTraits));
            int spreadIndex = entry.family().equals("fusion_rifle") ? boltIndex : i;
            int spreadCount = entry.family().equals("fusion_rifle") ? p.burst() : p.pellets();
            if (shotgunShape.isPresent()&&shotgunShape.get()!=ShotgunSpread.Shape.SLUG) {
                var ray=ShotgunSpread.direction(new ShotgunSpread.Vector(direction.x,direction.y,direction.z),
                        ShotgunSpread.offsets(shotgunShape.get()).get(i),
                        ShotgunPatternProfile.spread(p.spread(),WeaponAiming.progress(player)));
                direction=new Vec3(ray.x(),ray.y(),ray.z());
            } else if (spreadIndex > 0) {
                Vec3 right = direction.cross(Vec3.Y_AXIS);
                if (right.lengthSqr() < 1.0e-6) right = Vec3.X_AXIS;
                right = right.normalize();
                Vec3 up = right.cross(direction).normalize();
                double angle = (spreadIndex - 1) * Math.PI * 2 / Math.max(1, spreadCount - 1);
                double spread=p.spread()*(1-.35*WeaponAiming.progress(player))*WeaponTapTheTrigger.accuracyScalar(player)*WeaponUnderPressure.accuracyScalar(player);
                direction = direction.add(right.scale(Math.cos(angle) * spread)).add(up.scale(Math.sin(angle) * spread)).normalize();
            }
            Vec3 to = loadedEnd(player.level(), from, from.add(direction.scale(WeaponBallistics.traceRange(p))));
            HitResult hit = trace(player, from, to, p.mode() == WeaponProfile.Mode.MELEE ? 0.15f : 0.03f);
            // Native AABB.clip reports entry crossings, not a ray beginning inside an inflated
            // enemy box. Dash/point-blank melee must still hit that contact; a zero-distance wall wins.
            if(p.mode()==WeaponProfile.Mode.MELEE
                    &&(hit.getType()==HitResult.Type.MISS||from.distanceToSqr(hit.getLocation())>1e-6)) {
                var contact=player.level().getEntities(player,AABB.ofSize(from,.7,.7,.7),
                        entity->enemy(player,entity)&&entity.getBoundingBox().inflate(.15).contains(from))
                        .stream().min(Comparator.comparingDouble(e->e.position().distanceToSqr(from)));
                if(contact.isPresent())hit=new EntityHitResult(contact.get(),from);
            }
            if (hit instanceof EntityHitResult entity && entity.getEntity() instanceof LivingEntity target) {
                boolean precision = p.mode() != WeaponProfile.Mode.MELEE
                        && WeaponPrecision.critical(target, from, hit.getLocation(), ballistics.precision());
                float amount = p.mode() == WeaponProfile.Mode.MELEE ? p.damage()
                        : ballistics.damage(p.damage(), from.distanceTo(hit.getLocation()), precision);
                if(payload.active())amount=PayloadProfile.impact(p.damage(),ballistics.precision(),precision,
                        ballistics.falloff(from.distanceTo(hit.getLocation())));
                damage.computeIfAbsent(target, ignored -> new HitDamage()).add(amount, precision, hit.getLocation());
            }
            if(payload.active())payloadHit=hit;
            if (impactPosition == null && hit.getType() != HitResult.Type.MISS) impactPosition = hit.getLocation();
            if (i == 0) Fx.line(player.level(), from, hit.getLocation(), ace.empowered()?0xFFC773:shotTraits.damage().color(), 1.0, 0.5f);
        }
        WeaponMulligan.resolved(player,mulligan,!damage.isEmpty());
        var attribution=entry.family().equals("glaive")&&p.mode()==WeaponProfile.Mode.MELEE
                ?AmmoGeneration.ABILITY:AmmoGeneration.weapon(entry);
        var perks = p.mode() == WeaponProfile.Mode.MELEE ? WeaponKillClip.Token.NONE : WeaponKillClip.capture(player);
        var reloadPerk = p.mode() == WeaponProfile.Mode.MELEE ? WeaponOutlaw.Token.NONE : WeaponOutlaw.capture(player);
        var feedingFrenzy = p.mode() == WeaponProfile.Mode.MELEE ? WeaponFeedingFrenzy.Token.NONE : WeaponFeedingFrenzy.capture(player);
        var rampage = p.mode() == WeaponProfile.Mode.MELEE ? WeaponRampage.Token.NONE : WeaponRampage.capture(player);
        var precisionReturn = p.mode() == WeaponProfile.Mode.MELEE ? WeaponPrecisionReturn.Token.NONE : WeaponPrecisionReturn.capture(player);
        var dragonfly = p.mode() == WeaponProfile.Mode.MELEE ? WeaponDragonfly.Token.NONE : WeaponDragonfly.capture(player);
        var demolitionist = p.mode() == WeaponProfile.Mode.MELEE ? WeaponDemolitionist.Token.NONE : WeaponDemolitionist.capture(player);
        // Paid sword contacts qualify; glaive melee remains an excluded ability transaction.
        var damageTraits=acceptedTraits!=null?acceptedTraits
                :p.mode()!=WeaponProfile.Mode.MELEE || entry.family().equals("sword")
                ? DamageTraits.capture(player,highImpact,shotTraits) : DamageTraits.NONE;
        var meleeTraits = entry.family().equals("glaive") && p.mode()==WeaponProfile.Mode.MELEE
                ? MeleeWeaponTraits.accepted(player) : MeleeWeaponTraits.Snapshot.NONE;
        damage.forEach((target, hits) -> {
            float mori = ace.multiplier(target instanceof net.minecraft.world.entity.player.Player);
            boolean pvp=target instanceof net.minecraft.world.entity.player.Player;
            hits.body *= mori*WeaponIzanagi.multiplier(honed,false,pvp);
            hits.precision *= mori*WeaponIzanagi.multiplier(honed,true,pvp);
            float actual = apply(player, target, hits, attribution, perks, reloadPerk, rampage, precisionReturn, demolitionist, feedingFrenzy, damageTraits);
            if(actual>0) MeleeWeaponTraits.confirmed(player,meleeTraits,target,false,!target.isAlive());
            if (actual > 0 && !target.isAlive()) {
                WeaponDragonfly.killed(player, dragonfly, target, hits.precision > 0);
                WeaponAce.confirmedKill(player, ace, target, hits.precision > 0);
            }
        });
        // A separate body-only transaction: explosive final blows cannot become precision kills/refunds.
        // Capture the same source's damage buffs above, never whichever weapon a callback equipped later.
        for(var contact:WeaponPayload.detonate(player,payload,payloadHit))
            apply(player,contact.target(),PayloadProfile.explosion(p.damage())*contact.fraction(),false,contact.point(),
                    attribution,perks,WeaponOutlaw.Token.NONE,rampage,WeaponPrecisionReturn.Token.NONE,demolitionist,feedingFrenzy,damageTraits.perkSplash());
        if (impactPosition != null) DestinySounds.at(player.level(), impactPosition, DestinySounds.weaponKey(entry, "impact"), .8f);
    }
    /** One damage transaction per target: pellet precision cannot multiply every pellet or bypass immunity. */
    private static final class HitDamage {
        float body, precision;
        Vec3 bodyPoint, precisionPoint;
        void add(float amount, boolean critical, Vec3 point) {
            if (critical) { precision += amount; precisionPoint = point; }
            else { body += amount; bodyPoint = point; }
        }
    }
    private static float apply(ServerPlayer owner, LivingEntity target, HitDamage hits, AmmoGeneration attribution) {
        return apply(owner,target,hits,attribution,WeaponKillClip.Token.NONE,WeaponOutlaw.Token.NONE,WeaponRampage.Token.NONE,
                WeaponPrecisionReturn.Token.NONE,WeaponDemolitionist.Token.NONE);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, HitDamage hits, AmmoGeneration attribution,
                               WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk, WeaponRampage.Token rampage,
                               WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist) {
        return apply(owner,target,hits,attribution,perks,reloadPerk,rampage,precisionReturn,demolitionist,WeaponFeedingFrenzy.Token.NONE);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, HitDamage hits, AmmoGeneration attribution,
                               WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk, WeaponRampage.Token rampage,
                               WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist,
                               WeaponFeedingFrenzy.Token feedingFrenzy) {
        return apply(owner,target,hits,attribution,perks,reloadPerk,rampage,precisionReturn,demolitionist,feedingFrenzy,DamageTraits.NONE);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, HitDamage hits, AmmoGeneration attribution,
                               WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk, WeaponRampage.Token rampage,
                               WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist,
                               WeaponFeedingFrenzy.Token feedingFrenzy, DamageTraits damageTraits) {
        float effectivePrecision=WeaponPrecisionDamage.boost(WeaponShotTraits.precisionDamage(owner,damageTraits.shotTraits(),hits.precision),damageTraits.firingLine().precisionMultiplier())*WeaponShotTraits.precision(owner,damageTraits.shotTraits());
        float requested = (hits.body + effectivePrecision) * perks.multiplier() * rampage.multiplier() * damageTraits.multiplier(owner,target);
        if (!Float.isFinite(requested) || requested <= 0) return 0;
        boolean weakened = kim.biryeong.destiny.combat.Statuses.has(target, kim.biryeong.destiny.combat.Keyword.WEAKENED);
        float before = target.getHealth() + target.getAbsorptionAmount();
        boolean killed = Combat.damage(owner.level(), owner, target, requested, WeaponShotTraits.element(damageTraits.shotTraits()), attribution);
        float actual = before - target.getHealth() - target.getAbsorptionAmount();
        if (!Float.isFinite(actual) || actual <= 0) return 0;
        // One cue per observed damage transaction, after immunity/absorption checks.
        kim.biryeong.destiny.hud.WeaponHitHud.confirm(owner, actual, killed);
        WeaponShotTraits.confirmed(owner,damageTraits.shotTraits(),target,hits.precision>0,actual,killed);
        WeaponPrecisionReturn.confirmed(owner, precisionReturn, hits.precision > 0);
        WeaponFocusedFury.confirmed(owner,damageTraits.focusedFury(),hits.precision>0,actual);
        WeaponOneForAll.confirmed(owner, damageTraits.oneForAll(), target);
        WeaponStatsForAll.confirmed(owner,damageTraits.statsForAll(),target,actual);
        WeaponRapidHit.confirmed(owner,damageTraits.rapidHit(),hits.precision>0,weakened,actual);
        WeaponZenMoment.confirmed(owner,damageTraits.zenMoment(),target,actual);
        WeaponRelentlessStrikes.confirmed(owner,damageTraits.relentless(),target,actual);
        WeaponWhirlwindBlade.confirmed(owner,damageTraits.whirlwind(),target,actual);
        if (killed) {
            WeaponKillClip.killed(owner,perks);
            WeaponRampage.killed(owner,rampage);
            WeaponSwashbuckler.killed(owner,damageTraits.swashbuckler(),target);
            WeaponAdrenalineJunkie.killed(owner,damageTraits.adrenalineJunkie(),target);
            WeaponMultikillClip.killed(owner,damageTraits.multikillClip(),target);
            WeaponSubsistence.killed(owner,damageTraits.subsistence(),target);
            WeaponHeatingUp.killed(owner,damageTraits.heatingUp(),target);
            // Ranged transaction's confirmed precision component; never inferred from look angle or a nearby ability kill.
            WeaponOutlaw.killed(owner,reloadPerk,hits.precision>0);
            WeaponDemolitionist.killed(owner,demolitionist,target);
            WeaponEnergyPerks.killed(owner,damageTraits.energy(),target);
            WeaponPugilist.killed(owner,damageTraits.pugilist(),target);
            WeaponEncore.killed(owner,damageTraits.encore(),target,hits.precision>0);
            WeaponAmbitiousAssassin.killed(owner,damageTraits.assassin(),target);
            WeaponAdagio.killed(owner,damageTraits.adagio(),target);
            WeaponKillingTally.killed(owner,damageTraits.tally(),target);
            WeaponSympatheticArsenal.killed(owner,damageTraits.arsenal(),target);
            WeaponTirelessBlade.killed(owner,damageTraits.tireless(),target);
            WeaponAssassinsBlade.killed(owner,damageTraits.assassins(),target);
            WeaponUnrelenting.killed(owner,damageTraits.unrelenting(),target);
            WeaponFeedingFrenzy.killed(owner,feedingFrenzy);
        }
        // Mixed pellets share the observed transaction proportionally, not imaginary per-pellet HP measurements.
        if (hits.body > 0) kim.biryeong.destiny.fx.WeaponDamageNumbers.confirm(owner, owner.level(), hits.bodyPoint,
                actual * hits.body / (hits.body + effectivePrecision), weakened);
        if (hits.precision > 0) kim.biryeong.destiny.fx.WeaponDamageNumbers.confirm(owner, owner.level(), hits.precisionPoint,
                actual * effectivePrecision / (hits.body + effectivePrecision), true);
        return actual;
    }
    private static float apply(ServerPlayer owner, LivingEntity target, float amount, boolean precision,
                               Vec3 point, AmmoGeneration attribution, DamageTraits damageTraits) {
        var hits=new HitDamage(); hits.add(amount,precision,point);
        return apply(owner,target,hits,attribution,WeaponKillClip.Token.NONE,WeaponOutlaw.Token.NONE,WeaponRampage.Token.NONE,
                WeaponPrecisionReturn.Token.NONE,WeaponDemolitionist.Token.NONE,WeaponFeedingFrenzy.Token.NONE,damageTraits);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, float amount, boolean precision,
                               Vec3 point, AmmoGeneration attribution) {
        var hits = new HitDamage(); hits.add(amount, precision, point);
        return apply(owner, target, hits, attribution);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, float amount, boolean precision,
                               Vec3 point, AmmoGeneration attribution, WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk,
                               WeaponRampage.Token rampage, WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist) {
        var hits = new HitDamage(); hits.add(amount, precision, point);
        return apply(owner, target, hits, attribution,perks,reloadPerk,rampage,precisionReturn,demolitionist);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, float amount, boolean precision,
                               Vec3 point, AmmoGeneration attribution, WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk,
                               WeaponRampage.Token rampage, WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist,
                               WeaponFeedingFrenzy.Token feedingFrenzy) {
        return apply(owner,target,amount,precision,point,attribution,perks,reloadPerk,rampage,precisionReturn,demolitionist,feedingFrenzy,DamageTraits.NONE);
    }
    private static float apply(ServerPlayer owner, LivingEntity target, float amount, boolean precision,
                               Vec3 point, AmmoGeneration attribution, WeaponKillClip.Token perks, WeaponOutlaw.Token reloadPerk,
                               WeaponRampage.Token rampage, WeaponPrecisionReturn.Token precisionReturn, WeaponDemolitionist.Token demolitionist,
                               WeaponFeedingFrenzy.Token feedingFrenzy, DamageTraits damageTraits) {
        var hits=new HitDamage(); hits.add(amount,precision,point);
        return apply(owner,target,hits,attribution,perks,reloadPerk,rampage,precisionReturn,demolitionist,feedingFrenzy,damageTraits);
    }
    private static boolean enemy(ServerPlayer owner, Entity target) {
        return Combat.isEnemy(owner, target) && !owner.isAlliedTo(target)
                && !(target instanceof TamableAnimal tame && tame.isTame());
    }
    private static HitResult trace(ServerPlayer owner, Vec3 from, Vec3 to, float margin) {
        return trace(owner,from,to,margin,Set.of());
    }
    private static HitResult trace(ServerPlayer owner, Vec3 from, Vec3 to, float margin, Set<Entity> ignored) {
        var level = owner.level();
        HitResult wall = level.clip(new ClipContext(from, to, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, owner));
        Vec3 end = wall.getType() == HitResult.Type.MISS ? to : wall.getLocation();
        var target = ProjectileUtil.getEntityHitResult(level, owner, from, end, new AABB(from, end).inflate(margin + 0.2),
                entity -> enemy(owner, entity) && !ignored.contains(entity), margin);
        // An exact endpoint tie belongs to the wall, not the entity behind it.
        return target != null && (wall.getType() == HitResult.Type.MISS || from.distanceToSqr(target.getLocation()) + 1.0e-6 < from.distanceToSqr(end)) ? target : wall;
    }
    /** Stop before unloaded chunks, without forcing chunk loads through collision queries. */
    private static Vec3 loadedEnd(ServerLevel level, Vec3 from, Vec3 to) {
        // Fast full-ray preflight includes native traversal endpoint expansion. On an unloaded
        // boundary, each candidate prefix is checked as the ACTUAL ray that clip() will receive.
        if(WeaponWavefront.loadedSegment(level,from,to))return to;
        int steps = Math.max(1, (int)Math.ceil(from.distanceTo(to) * 2));
        Vec3 previous = from;
        for (int i = 0; i <= steps; i++) {
            Vec3 next = from.lerp(to, (double)i / steps);
            if (!level.hasChunkAt(BlockPos.containing(next))
                    || !WeaponWavefront.loadedSegment(level,from,next)) return previous;
            previous = next;
        }
        return to;
    }
    public static void tick(MinecraftServer server) {
        for(var player:server.getPlayerList().getPlayers()) {
            WeaponKillClip.update(player);
            WeaponAce.update(player);
            WeaponOutlaw.update(player);
            WeaponFeedingFrenzy.update(player); WeaponRapidHit.update(player); WeaponPerpetualMotion.update(player); WeaponTapTheTrigger.update(player); WeaponZenMoment.update(player); WeaponFrenzy.update(player); WeaponAdrenalineJunkie.update(player); WeaponFocusedFury.update(player); WeaponStatsForAll.update(player); WeaponHeatingUp.update(player); WeaponThreatDetector.update(player); WeaponEnsemble.update(player);
            WeaponOneForAll.update(player);
            WeaponSurrounded.update(player);
            WeaponSwashbuckler.update(player);
            WeaponMultikillClip.update(player);
            WeaponSubsistence.update(player);
            WeaponGraveRobber.update(player);
            WeaponArcherTempo.update(player);
            WeaponRampage.update(player);
            WeaponPrecisionReturn.update(player);
            WeaponDemolitionist.update(player);
            WeaponEnergyPerks.update(player); WeaponPugilist.update(player); WeaponBackupPlan.update(player); WeaponEncore.update(player); WeaponAmbitiousAssassin.update(player); WeaponClownCartridge.update(player); WeaponAdagio.update(player); WeaponWellRounded.update(player); WeaponKillingTally.update(player); WeaponSympatheticArsenal.update(player); WeaponRelentlessStrikes.update(player); WeaponTirelessBlade.update(player); WeaponWhirlwindBlade.update(player); WeaponOpeningShot.update(player); WeaponDynamicSway.update(player); WeaponAssassinsBlade.update(player); WeaponPerkMovement.update(player); WeaponPulseMonitor.update(player); WeaponUnrelenting.update(player); WeaponHeadseeker.update(player); WeaponOsmosis.update(player); WeaponSteadyHands.update(player);
            WeaponHolster.update(player);
            WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
            WeaponEnGarde.update(player);
            if(available(player)&&WeaponItems.entry(player.getMainHandItem()).isPresent())bind(player);
        }
        for (State s : List.copyOf(STATES.values())) {
            if (s.owner.level().getServer() != server) continue;
            tickPlayer(s.owner);
        }
        WeaponTracking.tick(server);
        SHOTS.removeIf(shot -> {
            if(shot.level.getServer()!=server||tickShot(shot))return false;
            if(shot.wave!=null)shot.wave.close();
            retireRemote(shot);
            return true;
        });
    }
    public static void tickPlayer(ServerPlayer player) {
        traceUse(player, "runtime.tick", -1);
        WeaponCrouchPresentation.update(player);
        WeaponKillClip.update(player);
        WeaponAce.update(player);
        WeaponOutlaw.update(player);
        WeaponFeedingFrenzy.update(player); WeaponRapidHit.update(player); WeaponPerpetualMotion.update(player); WeaponTapTheTrigger.update(player); WeaponZenMoment.update(player); WeaponFrenzy.update(player); WeaponAdrenalineJunkie.update(player); WeaponFocusedFury.update(player); WeaponStatsForAll.update(player); WeaponHeatingUp.update(player); WeaponThreatDetector.update(player); WeaponEnsemble.update(player);
        WeaponOneForAll.update(player);
        WeaponSurrounded.update(player);
            WeaponSwashbuckler.update(player);
            WeaponMultikillClip.update(player);
            WeaponSubsistence.update(player);
            WeaponGraveRobber.update(player);
        WeaponArcherTempo.update(player);
        WeaponRampage.update(player);
        WeaponPrecisionReturn.update(player);
        WeaponDemolitionist.update(player);
        WeaponEnergyPerks.update(player); WeaponPugilist.update(player); WeaponBackupPlan.update(player); WeaponEncore.update(player); WeaponAmbitiousAssassin.update(player); WeaponClownCartridge.update(player); WeaponAdagio.update(player); WeaponWellRounded.update(player); WeaponKillingTally.update(player); WeaponSympatheticArsenal.update(player); WeaponRelentlessStrikes.update(player); WeaponTirelessBlade.update(player); WeaponWhirlwindBlade.update(player); WeaponOpeningShot.update(player); WeaponDynamicSway.update(player); WeaponAssassinsBlade.update(player); WeaponPerkMovement.update(player); WeaponPulseMonitor.update(player); WeaponUnrelenting.update(player); WeaponHeadseeker.update(player); WeaponOsmosis.update(player); WeaponSteadyHands.update(player);
        WeaponHolster.update(player);
        WeaponQuickdraw.update(player);
        WeaponHandling.update(player);
        WeaponEnGarde.update(player);
        WeaponAiming.tick(player);
        WeaponTracking.update(player);
        if(available(player)&&(GlaiveItems.isGlaive(player.getMainHandItem())||SwordItems.isSword(player.getMainHandItem())))bind(player);
        State s = STATES.get(player.getUUID());
        if (s == null) {
            if (available(player)) WeaponIzanagiPresentation.update(player,player.getMainHandItem(),
                    WeaponIzanagiPresentation.Mode.IDLE,0);
            return;
        }
        if (!available(player) || s.level != player.level() || s.stack != player.getMainHandItem()
                || WeaponItems.entry(s.stack).isEmpty()) { s.cancel(); s.glaive.stop();
            kim.biryeong.destiny.fx.GlaiveShieldVfx.remove(player);return; }
        if (WeaponHandling.blocked(player)) {
            s.glaive.stop();
            kim.biryeong.destiny.fx.GlaiveShieldVfx.remove(player);
            return;
        }
        boolean leaseInput = WeaponModels.twoHanded(s.stack);
        if (s.remoteShot!=null&&!WeaponItems.entry(s.stack).filter(s.remoteShot.entry::equals).isPresent()) detachRemote(s);
        if (leaseInput && s.heldUntil >= 0 && now(player) >= s.heldUntil) endHeldInput(s);
        var entry = WeaponItems.entry(s.stack).orElseThrow();
        var p = WeaponProfile.forEntry(entry);
        var ammo = WeaponItems.magazine(s.stack, p);
        int beforeReload=ammo.rounds();
        boolean inserted=s.cycle.finishReload(now(player), ammo);
        int creditedRounds=Math.max(0,ammo.rounds()-beforeReload);
        if (inserted) kim.biryeong.destiny.sound.ShotgunReloadAudio.inserted(player,entry,s.cycle.reloading());
        if(WeaponIzanagi.finishReload(player,s.stack))ammo=WeaponItems.magazine(s.stack,p);
        if (inserted) {
            ammo.reloadOverflow(WeaponAmbitiousAssassin.target(player,s.assassinReload));
            ammo.reloadOverflow(WeaponClownCartridge.target(player,s.clownReload));
            s.assassinReload=WeaponAmbitiousAssassin.ReloadToken.NONE;
            s.clownReload=WeaponClownCartridge.Token.NONE;
            WeaponItems.save(s.stack, ammo);
            WeaponKillClip.reloaded(player,s.stack);
            WeaponMultikillClip.reloaded(player,s.stack);
            boolean refillArsenal=WeaponSympatheticArsenal.reloaded(player,s.arsenalReload,creditedRounds);
            s.arsenalReload=WeaponSympatheticArsenal.ReloadToken.NONE;
            if(refillArsenal)refillStowedArsenal(player);
        }
        WeaponAce.reloadTick(player,s.stack,inserted,s.cycle.reloading());
        if (!s.cycle.reloading()) s.reloadAllowsHeldInput=false;
        kim.biryeong.destiny.sound.ReloadAudio.tick(player,s.stack,s.cycle.reloading());
        WeaponReloadPresentation.update(player,s.stack, s.cycle.reloading(),
                1 - s.cycle.reloadRemaining(now(player)) / (float)Math.max(1,s.cycle.reloadPhaseTicks()));
        WeaponIzanagiPresentation.update(player,s.stack,s.cycle.reloading()
                        ? WeaponIzanagi.honing(player) ? WeaponIzanagiPresentation.Mode.HONED : WeaponIzanagiPresentation.Mode.RELOAD
                        : WeaponIzanagiPresentation.Mode.IDLE,
                1 - s.cycle.reloadRemaining(now(player)) / (float)Math.max(1,s.cycle.reloadPhaseTicks()));
        WeaponInsertPresentation.tick(player,s.stack,s.cycle.reloading(),
                1 - s.cycle.reloadRemaining(now(player)) / (float)Math.max(1,s.cycle.reloadPhaseTicks()),inserted);
        if(entry.family().equals("glaive")) {
            s.glaive.tick(now(player),player.isShiftKeyDown(),s.cycle.reloading());
            GlaiveItems.saveEnergy(s.stack,s.glaive.energy());
            kim.biryeong.destiny.fx.GlaiveShieldVfx.update(player,s.glaive.guarding());
        } else kim.biryeong.destiny.fx.GlaiveShieldVfx.remove(player);
        if(entry.family().equals("sword")) {
            s.sword.tick(now(player),player.isShiftKeyDown(),ammo.rounds()>0,s.cycle.ready(now(player)));
            if(s.sword.guarding())WeaponWhirlwindBlade.blocking(player,s.stack);
            SwordItems.save(s.stack,s.sword.energy(),s.sword.rechargeRemaining(now(player)));
            if(s.swordGuardAudio.sample(now(player),swordStatus(player).map(SwordStatus::guarding).orElse(false)))
                kim.biryeong.destiny.sound.SwordSounds.guard(player,entry);
            kim.biryeong.destiny.fx.SwordPresentation.tick(player);
            tickSwordContact(player,s);
        }
        // 30-fps source burst spacing may be below one 20-Hz tick. Drain only this bounded burst;
        // never synthesize extra triggers or carry idle-time shot credits.
        if(p.sharedBurstAmmo()&&entry.equals(s.chargeEntry)&&s.acceptedCharge!=null)p=s.acceptedCharge;
        int due = 0;
        while (due++ < p.burst() && s.cycle.burst(now(player), ammo)) {
            WeaponItems.save(s.stack, ammo);
            if(ammo.rounds()==0&&p.mode()!=WeaponProfile.Mode.MELEE)s.emptyReloadPending=true;
            // Fusion/LFR bolts share the already-paid cartridge; pulse bullets pay separately.
            var highImpact=p.sharedBurstAmmo()?s.paidHighImpact:
                    WeaponHighImpactReserves.capture(player,ammo.rounds()+1,WeaponProfile.forEntry(entry).magazine());
            var shotTraits=WeaponShotTraits.paid(player,entry,p.sharedBurstAmmo()?ammo.rounds():ammo.rounds()+1,false);
            emit(player, entry, p, false, s.cycle.burstIndex(),highImpact,null,shotTraits);
            // A precision return may have saved fresh ammo during this bolt's damage callback.
            // Never overwrite that reward with the pre-emission local copy on the next bolt.
            ammo = WeaponItems.magazine(s.stack, p);
            WeaponAiming.shot(player,entry,WeaponShotTraits.stability(player,shotTraits),WeaponShotTraits.growth(player,shotTraits));
        }
        // A shared-ammo fusion burst can have zero magazine ammo while later bolts
        // still exist. Never let auto reload consume/cancel those pending hits.
        // The candidate belongs only to this successful last shot and this stack;
        // cancel()/bind() discards it, so a swapped/skill-cancelled empty item does
        // not silently restart reload. No reserve means no timer or retry loop.
        if(s.emptyReloadPending&&!s.cycle.bursting()&&s.remoteShot==null) {
            s.emptyReloadPending=false;
            if(ammo.rounds()==0&&p.mode()!=WeaponProfile.Mode.MELEE)
                startReload(player,s,entry,p,true);
        }
        if (leaseInput) {
            if (s.heldUntil > now(player)) {
                if (!s.holding && !s.cycle.reloading()) beginUse(player);
                continueUse(player);
            }
        } else if (s.holding) {
            if(!player.isUsingItem()) { detachRemote(s); WeaponDynamicSway.released(player,s.stack); WeaponTapTheTrigger.released(player,s.stack); s.holding=false; s.cycle.cancelCharge(); s.acceptedBowDraw=null; }
            else if(entry.family().equals("bow"))continueUse(player);
        }
        updateBow(player,s);
    }
    /** Read-only fusion/LFR charge and paid-burst clock. Never binds a stack or advances combat.
     * A stopped two-hand heartbeat cannot appear as a live charge between gameplay ticks.
     * Paid remaining bolts deliberately survive button release, as the firing cycle already does.
     */
    public static WeaponChargeState chargeState(ServerPlayer player) {
        State s = STATES.get(player.getUUID());
        if (!available(player) || s == null || s.owner != player || s.level != player.level()
                || s.stack != player.getMainHandItem() || s.cycle.reloading() || WeaponHandling.blocked(player))
            return WeaponChargeState.idle();
        var entry = WeaponItems.entry(s.stack).filter(e -> e.family().equals("fusion_rifle")
                || e.family().equals("linear_fusion_rifle"));
        if (entry.isEmpty() || !entry.get().equals(s.chargeEntry) || s.acceptedCharge == null)
            return WeaponChargeState.idle();
        var profile = s.acceptedCharge;
        if (s.cycle.bursting()) return WeaponChargeState.bursting(1 + s.cycle.burstIndex(), profile.burst());
        if (!s.holding || s.fired || !s.cycle.charging()) return WeaponChargeState.idle();
        long tick = now(player);
        boolean held = WeaponModels.twoHanded(s.stack) ? s.heldUntil > tick
                : player.isUsingItem() && player.getUseItem() == s.stack;
        return held ? WeaponChargeState.charging(s.cycle.chargeElapsed(tick), profile.chargeTicks(), profile.burst())
                : WeaponChargeState.idle();
    }
    /** Pure view of the owned native draw, using the same accepted duration as the string/shot.
     * Never binds, refreshes perks, starts a draw, grants ammo or releases an arrow.
     * LATE is informational until original fatigue/late-shot curves are established.
     */
    public static WeaponBowWindow.State bowDrawState(ServerPlayer player) {
        State s = STATES.get(player.getUUID());
        if (!available(player) || s == null || s.owner != player || s.level != player.level()
                || s.stack != player.getMainHandItem() || !s.holding || s.acceptedBowDraw == null
                || !player.isUsingItem() || player.getUseItem() != s.stack || s.cycle.reloading()
                || WeaponHandling.blocked(player)) return WeaponBowWindow.idle();
        var e = WeaponItems.entry(s.stack).filter(x -> x.family().equals("bow"));
        return e.map(entry -> WeaponBowWindow.state(entry, s.acceptedBowDraw.chargeTicks(),
                s.cycle.chargeElapsed(now(player)),WeaponRapidHit.stabilityBonus(player))).orElseGet(WeaponBowWindow::idle);
    }
    /** Draw is the active charge clock; buffered input during a nock cannot age the next draw. */
    private static void updateBow(ServerPlayer player, State s) {
        var entry = WeaponItems.entry(s.stack).filter(WeaponBowPresentation::supports);
        if (entry.isEmpty()) { WeaponBowPresentation.clear(player,s.stack); return; }
        var profile = s.acceptedBowDraw!=null?s.acceptedBowDraw:WeaponProfile.forEntry(entry.get());
        float progress = 1 - s.cycle.reloadRemaining(now(player)) / (float)Math.max(1,s.cycle.reloadPhaseTicks());
        WeaponBowPresentation.update(player, s.stack, WeaponItems.magazine(s.stack,profile).rounds() > 0,
                s.holding ? s.cycle.chargeElapsed(now(player)) : -1, profile.chargeTicks(), s.cycle.reloading(), progress);
    }
    private static void releaseRemote(State state) {
        var shot=state.remoteShot;
        state.remoteShot=null;
        if(shot!=null&&shot.owner==state.owner&&shot.level==state.level&&shot.sourceStack==state.stack
                &&WeaponItems.entry(state.stack).filter(shot.entry::equals).isPresent())
            shot.breach.release(Math.max(0,now(state.owner)-shot.launchedAt));
        else if(shot!=null)shot.breach.detach();
    }
    private static void detachRemote(State state) {
        if(state.remoteShot!=null)state.remoteShot.breach.detach();
        state.remoteShot=null;
    }
    private static void endHeldInput(State state) { releaseRemote(state);state.releaseHold(); }
    private static void retireRemote(Shot shot) {
        var state=STATES.get(shot.owner.getUUID());
        if(state!=null&&state.owner==shot.owner&&state.remoteShot==shot)state.remoteShot=null;
    }
    /** Real input release/fuse uses the existing accepted damage/ammo/perk snapshot, never a new shot. */
    private static void detonateBreach(Shot shot) {
        impact(shot,BlockHitResult.miss(shot.position,net.minecraft.core.Direction.UP,BlockPos.containing(shot.position)),shot.position);
    }
    private static boolean tickShot(Shot shot) {
        var owner = shot.owner;
        if (!owner.isAlive() || owner.isRemoved() || owner.isSpectator() || owner.hasDisconnected() || owner.level() != shot.level) return false;
        if(shot.breach!=null&&(shot.breach.detonate()||shot.life==0)) {
            if(shot.level.hasChunkAt(BlockPos.containing(shot.position))) detonateBreach(shot);
            return false;
        }
        if(--shot.life<0)return false;
        if(shot.wave!=null) {
            for(var contact:shot.wave.advance())
                apply(owner,contact.target(),shot.profile.damage()*shot.waveProfile.waveMultiplier(),false,
                        contact.point(),AmmoGeneration.weapon(shot.entry),shot.perks,shot.reloadPerk,shot.rampage,shot.precisionReturn,shot.demolitionist,shot.feedingFrenzy,shot.damageTraits);
            return shot.wave.alive();
        }
        if(shot.tracking!=null)shot.velocity=shot.tracking.steer(shot.position,shot.velocity);
        Vec3 expected = shot.position.add(shot.velocity.normalize().scale(Math.min(shot.velocity.length(), shot.remaining)));
        Vec3 next = loadedEnd(shot.level, shot.position, expected);
        if (next.distanceToSqr(expected) > 1.0e-6) return false;
        HitResult hit = shot.waveProfile==null?trace(owner, shot.position, next, 0.08f)
                :trace(owner,shot.position,next,0.08f,shot.directContacts);
        if (shot.entry.family().equals("bow")) {
            kim.biryeong.destiny.fx.BowTrailFx.line(owner, shot.level, shot.position,
                    hit.getLocation(), 0xFFE2A8, 0.35, 0.7f);
        } else {
            Fx.line(shot.level, shot.position, hit.getLocation(),
                    shot.waveProfile==null&&shot.breach==null?0xFFE2A8:WeaponCharacteristics.of(shot.entry).damage().color(), 0.35, 0.7f);
        }
        Vec3 segmentFrom = shot.position;
        double step = shot.position.distanceTo(hit.getLocation());
        shot.remaining -= step;
        shot.travelled += step;
        shot.position = hit.getLocation();
        if (hit.getType() != HitResult.Type.MISS) {
            if(shot.waveProfile!=null)return waveImpact(shot,hit);
            if(shot.breach!=null&&hit instanceof BlockHitResult block) {
                if(++shot.bounces>BreachGrenade.MAX_BOUNCES||shot.remaining<=.001) { detonateBreach(shot);return false; }
                var face=block.getDirection();
                var v=BreachGrenade.reflect(shot.velocity.x,shot.velocity.y,shot.velocity.z,
                        face.getStepX(),face.getStepY(),face.getStepZ());
                shot.velocity=new Vec3(v.x(),v.y()-shot.profile.gravity(),v.z());
                shot.position=shot.position.add(face.getStepX()*.04,face.getStepY()*.04,face.getStepZ()*.04);
                // A collision is a ricochet, not a blast; preserve impact audio for actual detonation.
                return true;
            }
            impact(shot, hit, segmentFrom); return false;
        }
        if (shot.remaining <= 0.001) {
            if(shot.breach!=null)detonateBreach(shot);
            return false;
        }
        shot.velocity = shot.velocity.add(0, -shot.profile.gravity(), 0);
        return true;
    }
    /** Only the two exact wave intrinsics bypass radial explosive impact. Ground contact owns a
     * forward wave; wall/ceiling reflections and direct-hit split are bounded Minecraft adaptation.
     */
    private static boolean waveImpact(Shot shot,HitResult hit) {
        if(hit instanceof BlockHitResult block&&block.getDirection()==net.minecraft.core.Direction.UP) {
            Vec3 direction=new Vec3(shot.velocity.x,0,shot.velocity.z);
            if(direction.lengthSqr()<1e-8)direction=shot.launchForward;
            shot.wave=new WeaponWavefront(shot.owner,shot.waveProfile,hit.getLocation(),direction,
                    WeaponCharacteristics.of(shot.entry).damage());
            DestinySounds.at(shot.level,hit.getLocation(),DestinySounds.weaponKey(shot.entry,"impact"),.8f);
            return shot.wave.alive();
        }
        if(hit instanceof EntityHitResult entity&&entity.getEntity() instanceof LivingEntity target) {
            if(!shot.directContacts.add(target)||shot.directContacts.size()>16)return false;
            if(shot.waveProfile.directMultiplier()>0)
                apply(shot.owner,target,shot.profile.damage()*shot.waveProfile.directMultiplier(),false,hit.getLocation(),
                        AmmoGeneration.weapon(shot.entry),shot.perks,shot.reloadPerk,shot.rampage,shot.precisionReturn,shot.demolitionist,shot.feedingFrenzy,shot.damageTraits);
            if(++shot.bounces>6)return false;
            // Historical reports support pre-ground combatant ricochet; exact restitution and
            // direct/wave damage split are explicitly local W78 policy, not recovered original physics.
            var box=target.getBoundingBox();var delta=hit.getLocation().subtract(box.getCenter());
            double x=Math.abs(delta.x)/Math.max(.001,box.getXsize()/2);
            double y=Math.abs(delta.y)/Math.max(.001,box.getYsize()/2);
            double z=Math.abs(delta.z)/Math.max(.001,box.getZsize()/2);
            Vec3 normal=x>=y&&x>=z?new Vec3(Math.signum(delta.x),0,0)
                    :y>=z?new Vec3(0,Math.signum(delta.y),0):new Vec3(0,0,Math.signum(delta.z));
            shot.velocity=shot.velocity.subtract(normal.scale(2*shot.velocity.dot(normal))).scale(.65);
            shot.position=shot.position.add(normal.scale(.12));
        } else if(hit instanceof BlockHitResult block) {
            if(++shot.bounces>6)return false;
            var face=block.getDirection();
            Vec3 normal=new Vec3(face.getStepX(),face.getStepY(),face.getStepZ());
            shot.velocity=shot.velocity.subtract(normal.scale(2*shot.velocity.dot(normal))).scale(.65);
            shot.position=shot.position.add(normal.scale(.04));
        } else return false;
        shot.velocity=shot.velocity.add(0,-shot.profile.gravity(),0);
        return shot.remaining>.001;
    }
    private static void impact(Shot shot, HitResult hit, Vec3 segmentFrom) {
        var p = shot.profile;
        if(shot.entry.family().equals("sword"))
            kim.biryeong.destiny.sound.SwordSounds.casterImpact(shot.level,hit.getLocation());
        else DestinySounds.at(shot.level, hit.getLocation(), DestinySounds.weaponKey(shot.entry, "impact"), .8f);
        if (p.blastRadius() > 0) {
            Vec3 center = hit.getLocation().subtract(shot.velocity.normalize().scale(0.04));
            for (var target : Combat.enemiesNear(shot.level, shot.owner, center, p.blastRadius())) {
                if (!enemy(shot.owner, target)) continue;
                Vec3 aim = target.position().add(0, target.getBbHeight() * 0.5, 0);
                var wall = shot.level.clip(new ClipContext(center, aim, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, shot.owner));
                if (wall.getType() != HitResult.Type.MISS && center.distanceToSqr(wall.getLocation()) + 0.001 < center.distanceToSqr(aim)) continue;
                float falloff = (float)Math.max(0.3, 1 - center.distanceTo(aim) / p.blastRadius());
                apply(shot.owner, target, p.damage() * falloff, false, aim, AmmoGeneration.weapon(shot.entry),shot.perks,shot.reloadPerk,shot.rampage,
                        shot.precisionReturn,shot.demolitionist,shot.feedingFrenzy,shot.damageTraits);
            }
            Fx.ring(shot.level, center, p.blastRadius(), shot.breach==null?0xFFAF50:WeaponCharacteristics.of(shot.entry).damage().color(), 24);
        } else if (hit instanceof EntityHitResult entity && entity.getEntity() instanceof LivingEntity target && enemy(shot.owner, target)) {
            var ballistics = shot.ballistics;
            boolean precision = WeaponPrecision.critical(target, segmentFrom, hit.getLocation(), ballistics.precision());
            float actual = apply(shot.owner, target, ballistics.damage(p.damage(), shot.travelled, precision),
                    precision, hit.getLocation(), AmmoGeneration.weapon(shot.entry),shot.perks,shot.reloadPerk,shot.rampage,shot.precisionReturn,shot.demolitionist,shot.feedingFrenzy,shot.damageTraits);
            if(actual>0) {
                WeaponArcherTempo.confirmed(shot.owner,shot.archerTempo,precision);
                if (!target.isAlive()) WeaponDragonfly.killed(shot.owner,shot.dragonfly,target,precision);
            }
            if(shot.entry.family().equals("glaive")&&actual > 0)
                chargeGlaive(shot);
        }
    }
    private static void chargeGlaive(Shot shot) {
        // In-flight shots never charge a different weapon equipped after the shot or a dropped/traded item.
        boolean owns=false;
        for(int i=0;i<shot.owner.getInventory().getContainerSize();i++)
            if(shot.owner.getInventory().getItem(i)==shot.sourceStack){owns=true;break;}
        if(!owns||!GlaiveItems.isGlaive(shot.sourceStack))return;
        var s=STATES.get(shot.owner.getUUID());
        if(s!=null&&s.owner==shot.owner&&s.stack==shot.sourceStack) {
            s.glaive.hit();GlaiveItems.saveEnergy(shot.sourceStack,s.glaive.energy());
        } else GlaiveItems.saveEnergy(shot.sourceStack,GlaiveItems.energy(shot.sourceStack)+GlaiveCycle.HIT_ENERGY);
    }
    public record SwordStatus(float energy,boolean guarding,int combo) {}
    /** Pure held-item snapshot; querying HUD cannot bind, refill or advance recharge. */
    public static Optional<SwordStatus> swordStatus(ServerPlayer player) {
        if(!available(player)||!SwordItems.isSword(player.getMainHandItem()))return Optional.empty();
        State s=STATES.get(player.getUUID());
        boolean match=s!=null&&s.owner==player&&s.level==player.level()&&s.stack==player.getMainHandItem();
        boolean guard=match&&!WeaponHandling.blocked(player)&&player.isShiftKeyDown()&&s.cycle.ready(now(player))&&s.sword.guarding()
                &&WeaponItems.magazine(s.stack,WeaponProfile.forEntry(WeaponItems.entry(s.stack).orElseThrow())).rounds()>0;
        return Optional.of(new SwordStatus(SwordItems.energy(player.getMainHandItem())/(float)SwordCycle.CAPACITY,
                guard,match?s.sword.combo():0));
    }
    public record GlaiveStatus(float energy,boolean guarding,int combo) {}
    /** Read-only: HUD and damage checks must not create state or grant passive regeneration. */
    public static Optional<GlaiveStatus> glaiveStatus(ServerPlayer player) {
        if(!available(player)||!GlaiveItems.isGlaive(player.getMainHandItem()))return Optional.empty();
        State s=STATES.get(player.getUUID());
        boolean match=s!=null&&s.owner==player&&s.level==player.level()&&s.stack==player.getMainHandItem();
        return Optional.of(new GlaiveStatus(GlaiveItems.energy(player.getMainHandItem())/(float)GlaiveCycle.CAPACITY,
                match&&!WeaponHandling.blocked(player)&&player.isShiftKeyDown()&&!s.cycle.reloading()&&s.glaive.guarding(),match?s.glaive.combo():0));
    }
    /** Frontal PvE only; source/held-state queries are pure and do not spend guard energy. */
    private static boolean frontalMob(ServerPlayer player,net.minecraft.world.damagesource.DamageSource source) {
        if(source.is(net.minecraft.tags.DamageTypeTags.BYPASSES_SHIELD)
                ||!(source.getEntity() instanceof net.minecraft.world.entity.Mob mob)
                ||mob.level()!=player.level()||player.isAlliedTo(mob)
                ||mob instanceof TamableAnimal tame&&tame.isTame())return false;
        Vec3 incoming=mob.getEyePosition().subtract(player.getEyePosition());
        return incoming.lengthSqr()>=1e-8&&player.getLookAngle().dot(incoming.normalize())>0;
    }
    public static float guardDamage(ServerPlayer player,net.minecraft.world.damagesource.DamageSource source,float amount) {
        if(!Float.isFinite(amount)||amount<=0||!frontalMob(player,source))return amount;
        if(swordStatus(player).map(SwordStatus::guarding).orElse(false))return amount*.05f;
        return glaiveStatus(player).map(GlaiveStatus::guarding).orElse(false)?amount*.025f:amount;
    }
    /** Read-only observations of actual accepted Shots, not a target-injection or simulation API. */
    public record FlightSnapshot(String weaponId,Vec3 position,Vec3 velocity,UUID target,boolean tracking,long launchedAt) {}
    public static List<FlightSnapshot> flights(ServerPlayer owner) {
        return SHOTS.stream().filter(s->s.owner==owner).map(s->new FlightSnapshot(s.entry.id(),s.position,s.velocity,
                s.tracking==null?null:s.tracking.id,s.tracking!=null&&s.tracking.active,s.launchedAt)).toList();
    }
    public static int activeProjectiles(ServerPlayer owner) { return (int)SHOTS.stream().filter(s -> s.owner == owner).count(); }
    /** Reads current stack and matching owner/dimension state without binding or advancing timers. */
    public static Optional<WeaponAmmoState> ammunition(ServerPlayer player) {
        if (!available(player)) return Optional.empty();
        return WeaponItems.entry(player.getMainHandItem()).map(entry -> {
            var profile = WeaponProfile.forEntry(entry);
            var ammo = WeaponItems.magazine(player.getMainHandItem(), profile);
            State s = STATES.get(player.getUUID());
            boolean reloading = s != null && s.owner == player && s.level == player.level()
                    && s.stack == player.getMainHandItem() && s.cycle.reloading();
            int phase = reloading ? s.cycle.reloadPhaseTicks() : profile.reloadTicks();
            int remaining = reloading ? (int)Math.min(phase,s.cycle.reloadRemaining(now(player))) : 0;
            return new WeaponAmmoState(entry.family(), ammo.rounds(), ammo.reserve(), Math.max(profile.magazine(),ammo.rounds()),
                    remaining, phase, false, profile.infiniteReserve());
        });
    }
    public static boolean reloading(ServerPlayer player) {
        State s = STATES.get(player.getUUID());
        return s != null && s.stack == player.getMainHandItem() && s.cycle.reloading();
    }
    /** Read-only transport provenance; never binds state or advances a reload clock. */
    public static boolean reloadOwnedBy(ServerPlayer owner, ItemStack stack) {
        if (owner == null || stack == null || owner.getMainHandItem() != stack || !available(owner)) return false;
        State s = STATES.get(owner.getUUID());
        return s != null && s.owner == owner && s.level == owner.level()
                && s.stack == stack && s.cycle.reloading();
    }
    public static void cleanup(ServerPlayer owner) {
        kim.biryeong.destiny.sound.ReloadAudio.stop(owner);
        WeaponCrouchPresentation.cleanup(owner);
        WeaponOutlaw.cleanup(owner);
        WeaponFeedingFrenzy.cleanup(owner); WeaponRapidHit.cleanup(owner); WeaponPerpetualMotion.cleanup(owner); WeaponTapTheTrigger.cleanup(owner); WeaponZenMoment.cleanup(owner); WeaponFrenzy.cleanup(owner); WeaponAdrenalineJunkie.cleanup(owner); WeaponFocusedFury.cleanup(owner); WeaponStatsForAll.cleanup(owner); WeaponHeatingUp.cleanup(owner); WeaponThreatDetector.cleanup(owner); WeaponEnsemble.cleanup(owner);
        WeaponOneForAll.cleanup(owner);
        WeaponSurrounded.cleanup(owner);
        WeaponSwashbuckler.cleanup(owner);
        WeaponMultikillClip.cleanup(owner);
        WeaponSubsistence.cleanup(owner);
        WeaponGraveRobber.cleanup(owner);
        WeaponArcherTempo.cleanup(owner);
        WeaponKillClip.cleanup(owner);
        WeaponAce.cleanup(owner);
        WeaponIzanagi.cancelReload(owner);
        WeaponIzanagiPresentation.cleanup(owner);
        WeaponRampage.cleanup(owner);
        WeaponPrecisionReturn.cleanup(owner);
        WeaponDemolitionist.cleanup(owner);
        WeaponEnergyPerks.cleanup(owner); WeaponPugilist.cleanup(owner); WeaponBackupPlan.cleanup(owner); WeaponEncore.cleanup(owner); WeaponAmbitiousAssassin.cleanup(owner); WeaponClownCartridge.cleanup(owner); WeaponAdagio.cleanup(owner); WeaponWellRounded.cleanup(owner); WeaponKillingTally.cleanup(owner); WeaponSympatheticArsenal.cleanup(owner); WeaponRelentlessStrikes.cleanup(owner); WeaponTirelessBlade.cleanup(owner); WeaponWhirlwindBlade.cleanup(owner); WeaponEnGarde.cleanup(owner); WeaponOpeningShot.cleanup(owner); WeaponBoxBreathing.cleanup(owner); WeaponDynamicSway.cleanup(owner); WeaponAssassinsBlade.cleanup(owner); WeaponPerkMovement.cleanup(owner); WeaponPulseMonitor.cleanup(owner); WeaponRecoveryHandling.cleanup(owner); WeaponUnrelenting.cleanup(owner); WeaponHeadseeker.cleanup(owner); WeaponOsmosis.cleanup(owner); WeaponSteadyHands.cleanup(owner);
        WeaponTracking.cleanup(owner);
        WeaponHolster.cleanup(owner);
        WeaponQuickdraw.cleanup(owner);
        WeaponHandling.cleanup(owner);
        WeaponAiming.cleanup(owner);
        State s = STATES.get(owner.getUUID());
        if (s != null && s.owner==owner) { STATES.remove(owner.getUUID());s.cancel(); }
        kim.biryeong.destiny.fx.GlaiveShieldVfx.remove(owner);
        SHOTS.removeIf(shot -> {
            if(shot.owner!=owner)return false;
            if(shot.wave!=null)shot.wave.close();
            return true;
        });
        if (owner.isUsingItem() && owner.getUseItem().is(WeaponCombatItem.INSTANCE)) owner.stopUsingItem();
    }
    public static void clearAll() {
        for (State s : List.copyOf(STATES.values())) cleanup(s.owner);
        WeaponCrouchPresentation.clearAll();
        for(var shot:SHOTS)if(shot.wave!=null)shot.wave.close();
        STATES.clear(); SHOTS.clear(); WeaponAiming.clear(); WeaponHandling.clear(); WeaponQuickdraw.clear(); WeaponHolster.clear(); WeaponKillClip.clear(); WeaponAce.clear(); WeaponIzanagi.clear(); WeaponOutlaw.clear(); WeaponFeedingFrenzy.clear(); WeaponRapidHit.clear(); WeaponPerpetualMotion.clear(); WeaponTapTheTrigger.clear(); WeaponZenMoment.clear(); WeaponFrenzy.clear(); WeaponAdrenalineJunkie.clear(); WeaponFocusedFury.clear(); WeaponStatsForAll.clear(); WeaponHeatingUp.clear(); WeaponThreatDetector.clear(); WeaponEnsemble.clear(); WeaponOneForAll.clear(); WeaponSurrounded.clear(); WeaponSwashbuckler.clear(); WeaponMultikillClip.clear(); WeaponSubsistence.clear(); WeaponGraveRobber.clear(); WeaponArcherTempo.clear(); WeaponRampage.clear();
        WeaponPrecisionReturn.clear();
        WeaponDemolitionist.clear(); WeaponEnergyPerks.clear(); WeaponPugilist.clear(); WeaponBackupPlan.clear(); WeaponEncore.clear(); WeaponAmbitiousAssassin.clear(); WeaponClownCartridge.clear(); WeaponAdagio.clear(); WeaponWellRounded.clear(); WeaponKillingTally.clear(); WeaponSympatheticArsenal.clear(); WeaponRelentlessStrikes.clear(); WeaponTirelessBlade.clear(); WeaponWhirlwindBlade.clear(); WeaponEnGarde.clear(); WeaponOpeningShot.clear(); WeaponBoxBreathing.clear(); WeaponDynamicSway.clear(); WeaponAssassinsBlade.clear(); WeaponPerkMovement.clear(); WeaponPulseMonitor.clear(); WeaponRecoveryHandling.clear(); WeaponUnrelenting.clear(); WeaponHeadseeker.clear(); WeaponOsmosis.clear(); WeaponSteadyHands.clear();
        WeaponTracking.clear();
        WeaponIzanagiPresentation.clearAll();
        kim.biryeong.destiny.sound.ReloadAudio.clear();
        kim.biryeong.destiny.fx.SwordPresentation.clearAll();
    }
}
