package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.network.protocol.game.ClientboundPlayerRotationPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Server-owned ADS and relative-camera recoil; no custom client mod, movement spoof or teleport. */
public final class WeaponAiming {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;
        final ItemStack stack;
        final net.minecraft.server.level.ServerLevel level;
        final WeaponAimState state = new WeaponAimState();
        final WeaponFlinchState flinch = new WeaponFlinchState();
        long flinchTick = Long.MIN_VALUE;
        float flinchBudget;
        final WeaponAimMovement movement;
        boolean toggled;
        long lastToggleTick = Long.MIN_VALUE;
        WeaponModels.Pose pose = WeaponModels.Pose.HIP;
        Session(ServerPlayer p) {
            owner=p; stack=p.getMainHandItem();level=p.level();
            movement=new WeaponAimMovement(p);
            // A crash/save may retain the old cosmetic selector without its owner session.
            // Never leave a freshly loaded sniper invisible until the first ADS toggle.
            var data=stack.get(net.minecraft.core.component.DataComponents.CUSTOM_MODEL_DATA);
            if(data!=null && ("scope".equals(data.getString(0)) || "ads".equals(data.getString(0))))
                WeaponModels.setPose(stack,WeaponModels.Pose.HIP);
        }
    }
    private WeaponAiming() {}
    /** W277: authored ADS transitions felt sluggish in play; every enter/exit runs at 60% duration. */
    public static final float ADS_TIME_SCALE = .6f;
    public static int fast(int ticks) { return Math.max(2, Math.round(ticks * ADS_TIME_SCALE)); }

    private static int pugilistAdsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int ticks,boolean entering) {
        ticks=PerkBatchA.adsTicks(p,entry,ticks,entering); // W320 batch A
        return WeaponSlickdraw.adsTicks(p,entry,WeaponSteadyHands.adsTicks(p,entry,WeaponRecoveryHandling.adsTicks(p,entry,WeaponBackupPlan.adsTicks(p,entry,WeaponWellRounded.adsTicks(p,entry,WeaponPugilist.adsTicks(p,entry,WeaponEnsemble.adsTicks(p,entry,ticks,entering),entering),entering),entering),entering),entering),entering);
    }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected() && !AbilityService.inSuper(p) && !kim.biryeong.destiny.ability.GrenadeThrow.active(p) && !kim.biryeong.destiny.ability.ClassAbilityCast.active(p)
                && !kim.biryeong.destiny.fx.PlayerAnimations.meleePlaying(p)
                && WeaponLoadout.canUse(p) && CameraViews.get(p)==null
                && !kim.biryeong.destiny.camera.SuperCamera.active(p) && p.getCamera()==p
                && WeaponItems.entry(p.getMainHandItem()).filter(WeaponAimProfile::supports).isPresent();
    }
    public static void tick(ServerPlayer p) {
        WeaponThreatDetector.update(p);
        WeaponEnsemble.update(p);
        Session s=SESSIONS.get(p.getUUID());
        if (s!=null && s.owner!=p) { remove(s);s=null; }
        if (!eligible(p)) { cleanup(p);return; }
        if(s!=null && (s.stack!=p.getMainHandItem() || s.level!=p.level())) { remove(s);s=null; }
        if(s==null) { s=new Session(p);SESSIONS.put(p.getUUID(),s); }
        var profile=WeaponAimProfile.of(WeaponItems.entry(s.stack).orElseThrow());
        boolean aiming=aimingInput(s);
        if(aiming)p.setSprinting(false);
        var motionEntry=WeaponItems.entry(s.stack).orElseThrow();
        s.state.tick(p.level().getServer().getTickCount(),aiming,
                fast(pugilistAdsTicks(p,motionEntry,WeaponFirmlyPlanted.adsTicks(p,motionEntry,WeaponElementalCapacitor.adsTicks(p,motionEntry,WeaponSurplus.adsTicks(p,motionEntry,WeaponThreatDetector.adsTicks(p,motionEntry,WeaponStatsForAll.adsTicks(p,motionEntry,WeaponFrenzy.adsTicks(p,motionEntry,WeaponAdrenalineJunkie.adsTicks(p,motionEntry,WeaponPerpetualMotion.adsTicks(p,motionEntry,SnapshotAimProfile.enterTicks(s.stack)),true),true),true),true),true),true),true),true)),
                fast(pugilistAdsTicks(p,motionEntry,WeaponFirmlyPlanted.adsTicks(p,motionEntry,WeaponElementalCapacitor.adsTicks(p,motionEntry,WeaponSurplus.adsTicks(p,motionEntry,WeaponThreatDetector.adsTicks(p,motionEntry,WeaponStatsForAll.adsTicks(p,motionEntry,WeaponFrenzy.adsTicks(p,motionEntry,WeaponAdrenalineJunkie.adsTicks(p,motionEntry,WeaponPerpetualMotion.adsTicks(p,motionEntry,profile.transitionTicks()),false),false),false),false),false),false),false),false)),profile.recoveryPerTick());
        updateNoDistractions(s);
        WeaponBoxBreathing.update(p,aimInput(p));
        // Native FOV already eases per frame on the client; ramping the target per server tick too
        // stacked two lags. Request the full ADS target as soon as the input is accepted.
        s.movement.update(motionEntry,aiming,aiming?1f:0f);
        // The scope wrapper hides only first-person contexts; original ITEM_MODEL stays an identity key.
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        var pose=s.state.progress()<.5f?WeaponModels.Pose.HIP:
                WeaponScopes.supports(entry)?WeaponModels.Pose.SCOPE:WeaponModels.Pose.ADS;
        if(pose!=s.pose) { WeaponModels.setPose(s.stack,pose);s.pose=pose; }
        WeaponAimPresentation.update(p,s.stack,s.state.progress());
    }
    /** Left-click toggles only the exact supported live weapon. Shift remains native crouch/skills.
     * Repeated mining punches are debounced until a three-tick quiet gap.
     * Handling/reload consumes the click without queueing an ADS entry after the action ends. */
    public static boolean toggle(ServerPlayer p) {
        if (!eligible(p)) return false;
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && (s.owner!=p || s.stack!=p.getMainHandItem() || s.level!=p.level())) { remove(s);s=null; }
        if(s==null) { s=new Session(p);SESSIONS.put(p.getUUID(),s); }
        long now=p.level().getServer().getTickCount();
        long prior=s.lastToggleTick;
        s.lastToggleTick=now;
        if(prior!=Long.MIN_VALUE && now-prior<2)return true;
        WeaponQuickdraw.aimInput(p,true);
        if(WeaponHandling.blocked(p) || WeaponRuntime.reloading(p)) { suspend(p);return true; }
        s.toggled=!s.toggled;
        if(!s.toggled) { releasedAim(p);s.movement.release(); }
        return true;
    }
    /** Idempotent GCB hold. Reload pauses ADS; the live button token may resume it afterwards. */
    public static boolean hold(ServerPlayer p, boolean held) {
        if (!held) { releasedAim(p); return true; }
        if (!eligible(p)) return false;
        var s = SESSIONS.get(p.getUUID());
        if (s != null && (s.owner != p || s.stack != p.getMainHandItem() || s.level != p.level())) { remove(s); s = null; }
        if (s == null) { s = new Session(p); SESSIONS.put(p.getUUID(), s); }
        if (!s.toggled) WeaponQuickdraw.aimInput(p, true);
        s.toggled = true;
        return true;
    }
    /** True when the held item is an ADS weapon this system owns (so its punch is consumed). */
    public static boolean handles(ServerPlayer p) { return eligible(p); }
    /** Key-event toggle: one event per real press, so no punch-repeat debounce is needed. */
    public static boolean toggleKey(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null)s.lastToggleTick=Long.MIN_VALUE;
        return toggle(p);
    }
    /** Pure selected-source intent, also usable during handling without a recursive ADS tick. */
    public static boolean requested(ServerPlayer p) {
        var s=matching(p);return s!=null && s.toggled;
    }
    /** Skill/reload cancels the toggle immediately; the next click is a fresh ADS request. */
    public static void suspend(ServerPlayer p) { suspend(p,false); }
    /** An empty-magazine automatic reload may keep only the already-paid cosmetic shot tail. */
    static void suspend(ServerPlayer p, boolean preserveFireMotion) {
        if(!preserveFireMotion)WeaponFireMotion.clear(p);
        WeaponTracking.invalidate(p);
        WeaponBoxBreathing.released(p,p.getMainHandItem());
        var s=SESSIONS.get(p.getUUID());
        if(s==null || s.owner!=p)return;
        s.toggled=false;s.state.reset();s.flinch.reset();
        s.movement.release();
        restorePose(s);
        kim.biryeong.destiny.hud.WeaponScopeHud.remove(p);
    }
    /** Actual scoped input session, never an OP preview or a free-standing cosmetic pose. */
    public static boolean scoped(ServerPlayer p) {
        var s=matching(p);
        return s!=null && s.pose==WeaponModels.Pose.SCOPE && s.state.progress()>=.5f && WeaponScopes.scoped(s.stack);
    }
    public static float progress(ServerPlayer p) {
        var s=matching(p);return s==null?0:s.state.progress();
    }
    public static float bloom(ServerPlayer p) {
        var s=matching(p);return s==null?0:s.state.bloom();
    }
    private static boolean aimingInput(Session s) {
        return s.toggled && !WeaponHandling.blocked(s.owner)
                && !WeaponRuntime.reloading(s.owner);
    }
    /** Actual owned ADS input, before transition completion; pure and source-bound. */
    public static boolean aimInput(ServerPlayer p) {
        var s=matching(p);
        return s!=null&&aimingInput(s);
    }
    /** Pure current input/ownership oracle for prelaunch tracking; does not tick ADS or mutate speed. */
    public static boolean trackingInput(ServerPlayer p) {
        var s=matching(p);
        return s!=null && aimingInput(s) && s.state.progress()>=TrackingProfile.MIN_ADS;
    }
    private static void updateNoDistractions(Session s) {
        boolean exactIza=WeaponItems.entry(s.stack).filter(WeaponExotics::izanagi).isPresent();
        s.flinch.tick(s.owner.level().getServer().getTickCount(),(exactIza || WeaponNoDistractions.selected(s.owner,s.stack)) && aimingInput(s));
    }
    /** A real trait edit cannot carry an ADS clock into a newly selected source. */
    public static void perksEdited(ItemStack stack) {
        for(var s:SESSIONS.values())if(s.stack==stack)s.flinch.reset();
    }
    /** Earned runtime buff, not an item cosmetic flag or an invented countdown. */
    public static boolean noDistractions(ServerPlayer p) {
        var s=matching(p);
        if(s==null)return false;
        updateNoDistractions(s);
        return s.flinch.active();
    }
    /** Observe actual same-tick ADS release, including release/press before the next server tick. */
    public static void releasedAim(ServerPlayer p) {
        WeaponTracking.invalidate(p);
        WeaponBoxBreathing.released(p,p.getMainHandItem());
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p) { s.toggled=false;s.flinch.reset();s.movement.release(); }
    }
    /** A validated inventory stow breaks the continuous ADS interval even if the same object returns. */
    public static void inventoryStowing(ServerPlayer p,ItemStack outgoing) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p && s.stack==outgoing) suspend(p);
    }

    /** Called only after native Player.actuallyHurt, with exclusive real HP+absorption loss.
     * Entity-attributed impacts only: fall/fire/void/DOT without an entity never jolt the weapon.
     * Degree curve, side bias and 2.5-degree/tick budget are explicit Minecraft policy. */
    public static void damaged(ServerPlayer p,net.minecraft.world.damagesource.DamageSource source,float actualLoss) {
        if(!Float.isFinite(actualLoss)||actualLoss<=0||!eligible(p))return;
        var attacker=source.getEntity()!=null?source.getEntity():source.getDirectEntity();
        if(attacker==null || attacker==p || attacker.level()!=p.level())return;
        // Damage can arrive between an accepted inventory replacement and END_SERVER_TICK.
        // Observe the real new stack before asking its handling timer, not stale session metadata.
        WeaponHandling.update(p);
        if(WeaponHandling.blocked(p) || WeaponRuntime.reloading(p))return;
        var s=matching(p);
        if(s==null) { tick(p);s=matching(p); }
        if(s==null || WeaponHandling.blocked(p) || WeaponRuntime.reloading(p))return;
        updateNoDistractions(s);
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        var profile=WeaponAimProfile.of(entry);
        float magnitude=WeaponFlinchState.magnitude(actualLoss,p.getMaxHealth(),RapidHitStability.effectiveSigned(profile.stability(),WeaponRapidHit.stabilityBonus(p)+WeaponPerpetualMotion.stabilityBonus(p)+WeaponTapTheTrigger.stabilityBonus(p)+WeaponStatsForAll.stabilityBonus(p)+WeaponHeatingUp.stabilityBonus(p)+WeaponThreatDetector.stabilityBonus(p)+WeaponSurplus.stabilityBonus(p)+WeaponElementalCapacitor.stabilityBonus(p)+WeaponFirmlyPlanted.stabilityBonus(p)+WeaponIronReach.stabilityBonus(p)+WeaponHipFireGrip.stabilityBonus(p)+WeaponUnderPressure.stabilityBonus(p)+WeaponFullAuto.stabilityBonus(p)+WeaponEncore.stabilityBonus(p)+WeaponWellRounded.stabilityBonus(p)+WeaponDynamicSway.stabilityBonus(p)+PerkBatchA.stabilityBonus(p)),
                WeaponFlinchProfile.maxResistance(entry),s.state.progress(),s.flinch.active()) * WeaponZenMoment.flinchScalar(p);
        long now=p.level().getServer().getTickCount();
        if(now!=s.flinchTick) { s.flinchTick=now;s.flinchBudget=0; }
        magnitude=Math.min(magnitude,Math.max(0,2.5f-s.flinchBudget));
        if(magnitude<=0)return;
        s.flinchBudget+=magnitude;
        Vec3 origin=source.getSourcePosition();
        if(origin==null)origin=attacker.position();
        Vec3 right=new Vec3(Math.cos(Math.toRadians(p.getYRot())),0,Math.sin(Math.toRadians(p.getYRot())));
        float side=(float)Math.signum(origin.subtract(p.position()).dot(right))*.30f*magnitude;
        float oldPitch=p.getXRot();
        float pitch=Math.clamp(oldPitch-magnitude,-90,90)-oldPitch;
        p.setYRot(p.getYRot()+side);p.setXRot(oldPitch+pitch);
        if(side!=0 || pitch!=0)p.connection.send(new ClientboundPlayerRotationPacket(side,true,pitch,true));
    }
    /** Pure current half-angle; status/HUD inspection must not consume shot randomness. */
    public static double coneDegrees(ServerPlayer p) { return coneDegrees(p, 1); }
    private static double coneDegrees(ServerPlayer p, double paidAccuracy) {
        var entry = WeaponItems.entry(p.getMainHandItem()).orElse(null);
        if (entry == null || !WeaponAccuracy.supports(entry)) return 0;
        var profile = WeaponAccuracy.of(entry);
        var s = matching(p);
        double ads = s == null ? 0 : s.state.progress();
        double bloom = s == null ? 0 : Math.toDegrees(.006 * s.state.bloom());
        double accuracy = Math.clamp(paidAccuracy, 0, 1)
                * WeaponTapTheTrigger.accuracyScalar(p) * WeaponHeatingUp.accuracyScalar(p)
                * WeaponFirmlyPlanted.accuracyScalar(p) * WeaponUnderPressure.accuracyScalar(p)
                * WeaponEncore.coneScalar(p) * WeaponHipFireGrip.accuracyScalar(p)
                * PerkBatchA.accuracyScalar(p); // W320 batch A
        // Air is independent: an accuracy perk cannot bypass an insufficient AE stat.
        return ShotDispersion.coneDegrees(profile.hipDegrees(), profile.airDegrees(), ads,
                WeaponAccuracy.airborne(p), Math.clamp(WeaponAccuracy.airborne(entry, p.getMainHandItem())+PerkBatchA.airborneBonus(p),0,100), bloom, accuracy);
    }
    public static Vec3 direction(ServerPlayer p) { return direction(p, 1); }
    static Vec3 direction(ServerPlayer p, double paidAccuracy) {
        Vec3 forward = p.getLookAngle().normalize();
        double cone = coneDegrees(p, paidAccuracy);
        if (cone <= 0) return forward;
        return ShotDispersion.sample(forward, cone, p.getRandom().nextDouble(), p.getRandom().nextDouble());
    }
    private static Session matching(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        return s!=null && s.owner==p && s.stack==p.getMainHandItem() && s.level==p.level() && eligible(p)?s:null;
    }
    public static WeaponBallistics.Profile ballistics(ServerPlayer p,WeaponCatalog.Entry entry) { return ballistics(p,entry,0); }
    static WeaponBallistics.Profile ballistics(ServerPlayer p,WeaponCatalog.Entry entry,int paidRange) {
        boolean held=WeaponItems.entry(p.getMainHandItem()).filter(entry::equals).isPresent();
        int bonus=held?paidRange+WeaponIronReach.rangeBonus(p)+WeaponIronGaze.rangeBonus(p)+WeaponStatsForAll.rangeBonus(p)
                +WeaponRangefinder.rangeBonus(p)+WeaponAdagio.rangeBonus(p)+WeaponEncore.rangeBonus(p)+WeaponWellRounded.rangeBonus(p)
                +PerkBatchA.rangeBonus(p):0; // W320 batch A
        var hip=WeaponBallistics.withRangeBonus(entry,bonus);
        if(held)hip=PerkBatchA.falloff(p,entry,hip); // W320 batch A
        // SFA's separate falloff-distance scalar remains after raw Range summation.
        if(held&&WeaponStatsForAll.remaining(p)>0&&WeaponCharacteristics.of(entry).stats().containsKey("1240592695"))
            hip=new WeaponBallistics.Profile(hip.start()*1.05,hip.end()*1.05,hip.floor(),hip.precision());
        double hipFire=held?WeaponHipFireGrip.falloffScalar(p,entry):1;
        if (hipFire != 1) hip=new WeaponBallistics.Profile(hip.start()*hipFire,hip.end()*hipFire,hip.floor(),hip.precision());
        return scale(hip,WeaponAimProfile.of(entry).falloffScalar(),progress(p));
    }
    public static WeaponBallistics.Profile scale(WeaponBallistics.Profile hip,float scalar,float progress) {
        double factor=1+(Math.max(1,scalar)-1)*Math.clamp(progress,0,1);
        return new WeaponBallistics.Profile(hip.start()*factor,hip.end()*factor,hip.floor(),hip.precision());
    }
    public static void shot(ServerPlayer p,WeaponCatalog.Entry entry) { shot(p,entry,0,1); }
    static void shot(ServerPlayer p,WeaponCatalog.Entry entry,int paidStability,double paidGrowth) {
        if(!WeaponAimProfile.supports(entry) || !eligible(p))return;
        var s=matching(p);if(s==null) { tick(p);s=matching(p); }
        if(s==null)return;
        updateNoDistractions(s);
        s.flinch.shot(p.level().getServer().getTickCount());
        var profile=WeaponAimProfile.of(entry);
        float ads=s.state.progress();
        int stabilityBonus=paidStability+WeaponRapidHit.stabilityBonus(p)+WeaponPerpetualMotion.stabilityBonus(p)+WeaponTapTheTrigger.stabilityBonus(p)+WeaponStatsForAll.stabilityBonus(p)+WeaponHeatingUp.stabilityBonus(p)+WeaponThreatDetector.stabilityBonus(p)+WeaponSurplus.stabilityBonus(p)+WeaponElementalCapacitor.stabilityBonus(p)+WeaponFirmlyPlanted.stabilityBonus(p)+WeaponIronReach.stabilityBonus(p)+WeaponHipFireGrip.stabilityBonus(p)+WeaponUnderPressure.stabilityBonus(p)+WeaponFullAuto.stabilityBonus(p)+WeaponEncore.stabilityBonus(p)+WeaponWellRounded.stabilityBonus(p)
                +PerkBatchA.stabilityBonus(p); // W320 batch A
        float kick=RapidHitStability.kickSigned(profile,stabilityBonus)*WeaponTapTheTrigger.recoilScalar(p);
        float vertical=kick*(1-.35f*ads);
        // Recoil Direction informs bounded alternating horizontal kick, not an invented exact D2 curve.
        int recoilDirection=Math.clamp(profile.recoilDirection()+WeaponHeatingUp.recoilDirectionBonus(p),0,100);
        float side=(float)Math.sin(Math.toRadians(recoilDirection*18))*
                (100-recoilDirection)/100f*kick*.5f*(float)WeaponFirmlyPlanted.yawScalar(p);
        if((s.state.shots()&1)!=0)side=-side;
        s.state.shot((float)(Math.clamp(paidGrowth,0,1)*RapidHitStability.bloomSigned(profile,stabilityBonus)*(1-.45f*ads)*WeaponHeatingUp.accuracyScalar(p)*WeaponFirmlyPlanted.growthScalar(p)*PerkBatchA.growthScalar(p)));
        p.setYRot(p.getYRot()+side);p.setXRot(Math.clamp(p.getXRot()-vertical,-90,90));
        p.connection.send(new ClientboundPlayerRotationPacket(side,true,-vertical,true));
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p)remove(s);
    }
    private static void remove(Session s) {
        WeaponTracking.cleanup(s.owner);
        WeaponBoxBreathing.released(s.owner,s.stack);
        s.movement.release();
        restorePose(s);
        kim.biryeong.destiny.hud.WeaponScopeHud.remove(s.owner);
        SESSIONS.remove(s.owner.getUUID(),s);
    }
    /** Include ADS-only sessions which have never created a WeaponRuntime firing State. */
    public static void clear() {
        for (var s : List.copyOf(SESSIONS.values())) remove(s);
    }
    private static void restorePose(Session s) {
        boolean otherOwner=WeaponAimPresentation.boundToOther(s.owner,s.stack);
        WeaponAimPresentation.clear(s.owner,s.stack);
        if(!otherOwner && s.pose!=WeaponModels.Pose.HIP)WeaponModels.setPose(s.stack,WeaponModels.Pose.HIP);
        s.pose=WeaponModels.Pose.HIP;
    }
}
