package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.network.protocol.game.ClientboundPlayerRotationPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Server-owned ADS and relative-camera recoil; no custom client mod, movement spoof or teleport. */
public final class WeaponAiming {
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    public static final float BASE_FOV = 70;
    private static final class Session {
        final ServerPlayer owner;
        final ItemStack stack;
        final net.minecraft.server.level.ServerLevel level;
        final WeaponAimState state = new WeaponAimState();
        final WeaponFlinchState flinch = new WeaponFlinchState();
        long flinchTick = Long.MIN_VALUE;
        float flinchBudget;
        final WeaponAimMovement movement;
        Float applied, previous;
        boolean ownsFov, blocked;
        WeaponModels.Pose pose = WeaponModels.Pose.HIP;
        Session(ServerPlayer p) {
            owner=p; stack=p.getMainHandItem();level=p.level();
            movement=new WeaponAimMovement(p);
            // A crash/save may retain the old cosmetic selector without its owner session.
            // Never leave a freshly loaded sniper invisible until the first crouch/release.
            var data=stack.get(net.minecraft.core.component.DataComponents.CUSTOM_MODEL_DATA);
            if(data!=null && ("scope".equals(data.getString(0)) || "ads".equals(data.getString(0))))
                WeaponModels.setPose(stack,WeaponModels.Pose.HIP);
        }
    }
    private WeaponAiming() {}
    private static int pugilistAdsTicks(ServerPlayer p,WeaponCatalog.Entry entry,int ticks,boolean entering) {
        return WeaponSlickdraw.adsTicks(p,entry,WeaponSteadyHands.adsTicks(p,entry,WeaponRecoveryHandling.adsTicks(p,entry,WeaponBackupPlan.adsTicks(p,entry,WeaponWellRounded.adsTicks(p,entry,WeaponPugilist.adsTicks(p,entry,WeaponEnsemble.adsTicks(p,entry,ticks,entering),entering),entering),entering),entering),entering),entering);
    }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected() && !AbilityService.inSuper(p)
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
        if(!p.isShiftKeyDown())s.blocked=false;
        var profile=WeaponAimProfile.of(WeaponItems.entry(s.stack).orElseThrow());
        boolean aiming=p.isShiftKeyDown() && !s.blocked && !WeaponHandling.blocked(p) && !WeaponRuntime.reloading(p);
        var motionEntry=WeaponItems.entry(s.stack).orElseThrow();
        s.state.tick(p.level().getServer().getTickCount(),aiming,
                pugilistAdsTicks(p,motionEntry,WeaponFirmlyPlanted.adsTicks(p,motionEntry,WeaponElementalCapacitor.adsTicks(p,motionEntry,WeaponSurplus.adsTicks(p,motionEntry,WeaponThreatDetector.adsTicks(p,motionEntry,WeaponStatsForAll.adsTicks(p,motionEntry,WeaponFrenzy.adsTicks(p,motionEntry,WeaponAdrenalineJunkie.adsTicks(p,motionEntry,WeaponPerpetualMotion.adsTicks(p,motionEntry,SnapshotAimProfile.enterTicks(s.stack)),true),true),true),true),true),true),true),true),
                pugilistAdsTicks(p,motionEntry,WeaponFirmlyPlanted.adsTicks(p,motionEntry,WeaponElementalCapacitor.adsTicks(p,motionEntry,WeaponSurplus.adsTicks(p,motionEntry,WeaponThreatDetector.adsTicks(p,motionEntry,WeaponStatsForAll.adsTicks(p,motionEntry,WeaponFrenzy.adsTicks(p,motionEntry,WeaponAdrenalineJunkie.adsTicks(p,motionEntry,WeaponPerpetualMotion.adsTicks(p,motionEntry,profile.transitionTicks()),false),false),false),false),false),false),false),false),profile.recoveryPerTick());
        updateFov(s,profile);
        updateNoDistractions(s);
        WeaponBoxBreathing.update(p,aimInput(p));
        // FOV takeover may have blocked/reset the session. Never retain speed after that boundary.
        s.movement.update(WeaponItems.entry(s.stack).orElseThrow(),aiming && !s.blocked && s.state.progress()>0);
        // The scope wrapper hides only first-person contexts; original ITEM_MODEL stays an identity key.
        // Apply after FOV ownership handling so an external takeover clears the scope in the same tick.
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        var pose=s.state.progress()<.5f?WeaponModels.Pose.HIP:
                WeaponScopes.supports(entry)?WeaponModels.Pose.SCOPE:WeaponModels.Pose.ADS;
        if(pose!=s.pose) { WeaponModels.setPose(s.stack,pose);s.pose=pose; }
        WeaponAimPresentation.update(p,s.stack,s.state.progress());
    }
    private static void updateFov(Session s,WeaponAimProfile profile) {
        if(s.ownsFov && !Objects.equals(CameraEffects.getFov(s.owner),s.applied)) {
            // Another camera owner took over: never overwrite/reset its projection.
            s.ownsFov=false;s.blocked=true;s.state.reset();s.flinch.reset();return;
        }
        if(s.state.progress()<=0 || !kim.biryeong.minigamelib.shaderfx.impl.ModConfig.getInstance().dynamicFovShader) {
            releaseFov(s);return;
        }
        if(!s.ownsFov) { s.previous=CameraEffects.getFov(s.owner);s.ownsFov=true; }
        float base=s.previous==null?BASE_FOV:s.previous;
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        float fov=base+(WeaponAimState.zoomFov(base,profile.zoom()*WeaponRangefinder.zoomScalar(s.owner,entry))-base)*s.state.progress();
        // Optional projection transport has integer degree precision.
        fov=Math.max(1,Math.round(fov));
        if(!Objects.equals(s.applied,fov)) { CameraEffects.setFov(s.owner,fov);s.applied=fov; }
    }
    private static void releaseFov(Session s) {
        if(s.ownsFov && Objects.equals(CameraEffects.getFov(s.owner),s.applied)) {
            if(s.previous==null)CameraEffects.resetFov(s.owner);else CameraEffects.setFov(s.owner,s.previous);
        }
        s.ownsFov=false;s.applied=null;s.previous=null;
    }
    /** Skill/reload cancels ADS immediately; do not re-enter until the player releases crouch. */
    public static void suspend(ServerPlayer p) { suspend(p,false); }
    /** An empty-magazine automatic reload may keep only the already-paid cosmetic shot tail. */
    static void suspend(ServerPlayer p, boolean preserveFireMotion) {
        if(!preserveFireMotion)WeaponFireMotion.clear(p);
        WeaponTracking.invalidate(p);
        WeaponBoxBreathing.released(p,p.getMainHandItem());
        var s=SESSIONS.get(p.getUUID());
        if(s==null || s.owner!=p)return;
        s.blocked=true;s.state.reset();s.flinch.reset();releaseFov(s);
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
        return s.owner.isShiftKeyDown() && !s.blocked && !WeaponHandling.blocked(s.owner)
                && !WeaponRuntime.reloading(s.owner);
    }
    /** Actual owned ADS input, before transition completion; pure and FOV-takeover aware. */
    public static boolean aimInput(ServerPlayer p) {
        var s=matching(p);
        return s!=null&&aimingInput(s)&&(!s.ownsFov||Objects.equals(CameraEffects.getFov(p),s.applied));
    }
    /** Pure current input/ownership oracle for prelaunch tracking; does not tick ADS or restore FOV. */
    public static boolean trackingInput(ServerPlayer p) {
        var s=matching(p);
        return s!=null && aimingInput(s) && s.state.progress()>=TrackingProfile.MIN_ADS
                && (!s.ownsFov || Objects.equals(CameraEffects.getFov(p),s.applied));
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
        if(s.ownsFov && !Objects.equals(CameraEffects.getFov(p),s.applied)) { suspend(p);return false; }
        updateNoDistractions(s);
        return s.flinch.active();
    }
    /** Observe actual same-tick ADS release, including release/press before the next server tick. */
    public static void releasedAim(ServerPlayer p) {
        WeaponTracking.invalidate(p);
        WeaponBoxBreathing.released(p,p.getMainHandItem());
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p)s.flinch.reset();
    }
    /** A validated inventory stow breaks the continuous ADS interval even if the same object returns. */
    public static void inventoryStowing(ServerPlayer p,ItemStack outgoing) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null && s.owner==p && s.stack==outgoing) {s.flinch.reset();WeaponTracking.invalidate(p);
        WeaponBoxBreathing.released(p,p.getMainHandItem());}
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
        if(s==null || s.blocked || WeaponHandling.blocked(p) || WeaponRuntime.reloading(p))return;
        if(s.ownsFov && !Objects.equals(CameraEffects.getFov(p),s.applied)) { suspend(p);return; }
        updateNoDistractions(s);
        var entry=WeaponItems.entry(s.stack).orElseThrow();
        var profile=WeaponAimProfile.of(entry);
        float magnitude=WeaponFlinchState.magnitude(actualLoss,p.getMaxHealth(),RapidHitStability.effectiveSigned(profile.stability(),WeaponRapidHit.stabilityBonus(p)+WeaponPerpetualMotion.stabilityBonus(p)+WeaponTapTheTrigger.stabilityBonus(p)+WeaponStatsForAll.stabilityBonus(p)+WeaponHeatingUp.stabilityBonus(p)+WeaponThreatDetector.stabilityBonus(p)+WeaponSurplus.stabilityBonus(p)+WeaponElementalCapacitor.stabilityBonus(p)+WeaponFirmlyPlanted.stabilityBonus(p)+WeaponIronReach.stabilityBonus(p)+WeaponHipFireGrip.stabilityBonus(p)+WeaponUnderPressure.stabilityBonus(p)+WeaponFullAuto.stabilityBonus(p)+WeaponEncore.stabilityBonus(p)+WeaponWellRounded.stabilityBonus(p)+WeaponDynamicSway.stabilityBonus(p)),
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
                * WeaponEncore.coneScalar(p) * WeaponHipFireGrip.accuracyScalar(p);
        // Air is independent: an accuracy perk cannot bypass an insufficient AE stat.
        return ShotDispersion.coneDegrees(profile.hipDegrees(), profile.airDegrees(), ads,
                WeaponAccuracy.airborne(p), WeaponAccuracy.airborne(entry, p.getMainHandItem()), bloom, accuracy);
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
                +WeaponRangefinder.rangeBonus(p)+WeaponAdagio.rangeBonus(p)+WeaponEncore.rangeBonus(p)+WeaponWellRounded.rangeBonus(p):0;
        var hip=WeaponBallistics.withRangeBonus(entry,bonus);
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
        int stabilityBonus=paidStability+WeaponRapidHit.stabilityBonus(p)+WeaponPerpetualMotion.stabilityBonus(p)+WeaponTapTheTrigger.stabilityBonus(p)+WeaponStatsForAll.stabilityBonus(p)+WeaponHeatingUp.stabilityBonus(p)+WeaponThreatDetector.stabilityBonus(p)+WeaponSurplus.stabilityBonus(p)+WeaponElementalCapacitor.stabilityBonus(p)+WeaponFirmlyPlanted.stabilityBonus(p)+WeaponIronReach.stabilityBonus(p)+WeaponHipFireGrip.stabilityBonus(p)+WeaponUnderPressure.stabilityBonus(p)+WeaponFullAuto.stabilityBonus(p)+WeaponEncore.stabilityBonus(p)+WeaponWellRounded.stabilityBonus(p);
        float kick=RapidHitStability.kickSigned(profile,stabilityBonus)*WeaponTapTheTrigger.recoilScalar(p);
        float vertical=kick*(1-.35f*ads);
        // Recoil Direction informs bounded alternating horizontal kick, not an invented exact D2 curve.
        int recoilDirection=Math.clamp(profile.recoilDirection()+WeaponHeatingUp.recoilDirectionBonus(p),0,100);
        float side=(float)Math.sin(Math.toRadians(recoilDirection*18))*
                (100-recoilDirection)/100f*kick*.5f*(float)WeaponFirmlyPlanted.yawScalar(p);
        if((s.state.shots()&1)!=0)side=-side;
        s.state.shot((float)(Math.clamp(paidGrowth,0,1)*RapidHitStability.bloomSigned(profile,stabilityBonus)*(1-.45f*ads)*WeaponHeatingUp.accuracyScalar(p)*WeaponFirmlyPlanted.growthScalar(p)));
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
        releaseFov(s);
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
