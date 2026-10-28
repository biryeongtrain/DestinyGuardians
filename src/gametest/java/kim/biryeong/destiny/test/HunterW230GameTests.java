package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.hunter.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.SwordTiming;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Mob;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual acceptance, collision, ownership and finite field tests, not individual damage-number tests. */
public final class HunterW230GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static final float HP=200; // 26.3 MAX_HEALTH is capped at1024; never expect unclamped2000.
    private static void check(GameTestHelper h,boolean value,String why) { h.assertTrue(value,Component.literal(why)); }
    private static ServerPlayer player(GameTestHelper h,Identifier id,Vec3 pos) {
        for(int x=0;x<16;x++) for(int z=0;z<14;z++) h.setBlock(x,0,z,Blocks.STONE);
        Element element=AbilityRegistry.get(id).orElseThrow().element();
        ServerPlayer p=TestPlayers.hunter(h,element,pos,-90,0,"W230H"+UUID.randomUUID().toString().substring(0,7));
        Guardians.data(p).setLoadout(GuardianClass.HUNTER,HunterAbilities.preset(element).with(AbilitySlot.SUPER,id));
        Guardians.data(p).setSuperEnergy(1); Guardians.runtime(p); p.setOnGround(true);
        p.getInventory().setItem(0,new ItemStack(Items.DIAMOND,3));
        TestCleanup.register(h,() -> { HunterExpandedSupers.cleanup(p); TestPlayers.remove(p); });
        h.onEachTick(() -> {
            TestPlayers.drain(p);
            if(AbilityService.inSuper(p)) {
                int rotations=SuperCamera.rotations(p);
                p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),false,false));
                check(h,SuperCamera.active(p) && SuperCamera.rotations(p)==rotations+1,"Native fake-client camera heartbeat accepted");
                AbilityService.tickPlayer(p);
            }
            HunterExpandedSupers.tick(h.getLevel().getServer()); // Same gameTime is intentionally safe if central lifecycle also runs.
        });
        return p;
    }
    private static ServerPlayer player(GameTestHelper h,Identifier id) { return player(h,id,new Vec3(2.5,1,6.5)); }
    private static Husk enemy(GameTestHelper h,Vec3 pos) {
        Husk e=h.spawn(EntityTypes.HUSK,pos); e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HP); e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(HP);
        check(h,e.getMaxHealth()==HP && e.getHealth()==HP,"Valid health fixture starts at observed HP="+e.getHealth()+" max="+e.getMaxHealth());
        TestCleanup.register(h,() -> { kim.biryeong.destiny.combat.Statuses.forget(e); e.discard(); }); return e;
    }
    private static void wall(GameTestHelper h,int x) {
        for(int y=1;y<=5;y++) for(int z=0;z<=13;z++) h.setBlock(x,y,z,Blocks.STONE);
    }
    private static void aim(ServerPlayer p,Vec3 at) {
        Vec3 d=at.subtract(p.getEyePosition());
        float yaw=(float)Math.toDegrees(Math.atan2(-d.x,d.z));
        p.setYRot(yaw); p.setYHeadRot(yaw);
        p.setXRot((float)-Math.toDegrees(Math.atan2(d.y,Math.sqrt(d.x*d.x+d.z*d.z))));
    }
    private static int windup(Identifier id,int fallback) {
        return ClassSuperModelAssets.durationTicks(id.getPath(),"start",fallback)+SwordTiming.START_TICKS;
    }
    private static void cast(GameTestHelper h,ServerPlayer p) {
        check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Real equipped expanded super accepted");
        check(h,SuperCamera.active(p) && Guardians.data(p).superEnergy()==0,"Rear camera active and accepted cast spends energy");
    }
    private static String status(ServerPlayer p) { return HunterExpandedSupers.status(p); }
    private static Vec3 center(LivingEntity e) { return e.position().add(0,e.getBbHeight()*.5,0); }
    private static HitResult ray(ServerPlayer p,Vec3 from,Vec3 to) {
        return p.level().clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p));
    }
    private static String entityName(LivingEntity e) {
        return e==null?"null":e.getType()+"/"+e.getUUID();
    }
    private static String diagnostic(GameTestHelper h,ServerPlayer p,LivingEntity... targets) {
        StringBuilder out=new StringBuilder(" [testTick=").append(h.getTick()).append(" gameTime=").append(p.level().getGameTime())
                .append(" difficulty=").append(p.level().getDifficulty()).append(" feet=").append(p.position())
                .append(" eye=").append(p.getEyePosition()).append(" hpBaseline=").append(HP)
                .append(" status={").append(status(p)).append('}');
        Vec3 effect=HunterExpandedSupers.fieldOrigin(p); out.append(" fieldOrigin=").append(effect);
        for(LivingEntity e:targets) {
            out.append(" target={id=").append(entityName(e)).append(" hp=").append(e.getHealth()).append(" max=").append(e.getMaxHealth())
                    .append(" alive=").append(e.isAlive()).append(" invulnerable=").append(e.isInvulnerable())
                    .append(" position=").append(e.position()).append(" clearBody=").append(e.level().noCollision(e,e.getBoundingBox()))
                    .append(" eyeRay=").append(ray(p,p.getEyePosition(),center(e)).getType());
            if(effect!=null) out.append(" fieldDistance=").append(effect.distanceTo(center(e)))
                    .append(" fieldRay=").append(ray(p,effect,center(e)).getType());
            if(e instanceof Mob m) out.append(" rawTarget=").append(entityName(m.getTargetUnchecked()))
                    .append(" validTarget=").append(entityName(m.getTarget())).append(" canAttackOwner=").append(m.canAttack(p));
            out.append('}');
        }
        return out.append(']').toString();
    }
    private static void inventory(GameTestHelper h,ServerPlayer p) {
        check(h,p.getInventory().getItem(0).is(Items.DIAMOND) && p.getInventory().getItem(0).getCount()==3,
                "Virtual props preserve actual inventory");
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=150,skyAccess=true)
    public void barrageAutomaticallyReleasesExactlyTwoFansAndExplodesOnlyOnVisibleSide(GameTestHelper h) {
        ServerPlayer p=player(h,HunterExpandedSupers.BLADE_BARRAGE); wall(h,7);
        Husk front=enemy(h,new Vec3(5.75,1,6.5)), blocked=enemy(h,new Vec3(8.5,1,6.5));
        check(h,h.getLevel().noCollision(blocked,blocked.getBoundingBox()),"Occluded control never overlaps wall");
        aim(p,blocked.position().add(0,.9,0)); cast(h,p);
        h.onEachTick(() -> { if(AbilityService.inSuper(p)) for(int i=0;i<12;i++) Guardians.runtime(p).superSession.primary(); });
        h.runAfterDelay(5,() -> check(h,HunterExpandedSupers.emitted(p)==0,"Primary spam cannot bypass automatic windup"));
        h.runAfterDelay(windup(HunterExpandedSupers.BLADE_BARRAGE,40)+35,() -> {
            check(h,HunterExpandedSupers.emitted(p)==14 && status(p).contains("volleys=2"),"Two automatic seven-knife fans only: "+status(p));
            check(h,front.getHealth()<HP && blocked.getHealth()==HP,"Embedded delayed blast respects near-side collider LOS"+diagnostic(h,p,front,blocked));
            check(h,!AbilityService.inSuper(p) && SimProjectile.activeCount(p)==0,"Camera/session and finite knife flights recover");
            inventory(h,p); h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=400,skyAccess=true)
    public void gatheringStaffCollidesAndFiniteLightningFieldOutlivesCastCamera(GameTestHelper h) {
        ServerPlayer p=player(h,HunterExpandedSupers.GATHERING_STORM); wall(h,7);
        Husk front=enemy(h,new Vec3(5.75,1,6.5)),blocked=enemy(h,new Vec3(8.5,1,6.5));
        aim(p,blocked.position().add(0,.9,0)); cast(h,p);
        int ready=windup(HunterExpandedSupers.GATHERING_STORM,33);
        final Husk[] late={null};
        h.runAfterDelay(ready+15,() -> {
            check(h,!AbilityService.inSuper(p) && HunterExpandedSupers.fieldCount(p)==1,"One stuck field survives cast/camera recovery: "+status(p));
            check(h,HunterExpandedSupers.emitted(p)==1 && HunterExpandedSupers.fieldOrigin(p)!=null,"Exactly one automatic staff collision");
            late[0]=enemy(h,new Vec3(5.5,1,8));
        });
        h.runAfterDelay(ready+110,() -> {
            check(h,front.getHealth()<HP && late[0].getHealth()<HP,"Real delayed field damages targets arriving after cast completion"+diagnostic(h,p,front,blocked,late[0]));
            check(h,HunterExpandedSupers.fieldOrigin(p).distanceTo(center(blocked))<4
                            && ray(p,HunterExpandedSupers.fieldOrigin(p),center(blocked)).getType()==HitResult.Type.BLOCK,
                    "Blocked staff control is inside actual radius and genuinely occluded"+diagnostic(h,p,front,blocked));
            check(h,blocked.getHealth()==HP,"Stuck staff cannot pulse through wall"+diagnostic(h,p,front,blocked,late[0]));
            int count=HunterExpandedSupers.fieldCount(p);
            for(int i=0;i<10;i++) HunterExpandedSupers.tick(h.getLevel().getServer());
            check(h,HunterExpandedSupers.fieldCount(p)==count,"Manual same-gameTime ticks cannot accelerate or duplicate field lifecycle");
        });
        h.runAfterDelay(ready+300,() -> {
            check(h,HunterExpandedSupers.fieldCount(p)==0 && SimProjectile.activeCount(p)==0,"Finite 2s strike+1.2s delay+8s field expires");
            inventory(h,p); h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=200,skyAccess=true)
    public void spectralRoamingContactsScopeRealCloakAndPreserveForeignInvisibility(GameTestHelper h) {
        ServerPlayer p=player(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(3.5,1,6.5)); wall(h,5);
        ServerPlayer foreign=player(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(2.5,1,11.5));
        ServerPlayer swapped=player(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(12.5,1,11.5));
        ServerPlayer dying=player(h,HunterExpandedSupers.SPECTRAL_BLADES,new Vec3(12.5,1,2.5));
        MobEffectInstance preexisting=new MobEffectInstance(MobEffects.INVISIBILITY,1200,1,false,true,true);
        foreign.addEffect(preexisting);
        Husk front=enemy(h,new Vec3(4.5,1,6.5)),blocked=enemy(h,new Vec3(6.5,1,6.5));
        cast(h,p); cast(h,foreign); cast(h,swapped); cast(h,dying);
        int ready=windup(HunterExpandedSupers.SPECTRAL_BLADES,32);
        final MobEffectInstance[] externallyRefreshed={null};
        h.runAfterDelay(ready+1,() -> {
            check(h,p.hasEffect(MobEffects.INVISIBILITY) && status(p).contains("cloakOwned=true"),
                    "Prepared Spectral owns a real short vanilla invisibility effect: "+status(p));
            p.updateDataBeforeSync();
            check(h,p.isInvisible() && p.getVisibilityPercent(h.getLevel(),front)<1,
                    "Native effect metadata and vanilla AI visibility weight reflect actual invisibility");
            front.setTarget(p); blocked.setTarget(front);
            check(h,front.getTargetUnchecked()==p && blocked.getTargetUnchecked()==front,
                    "Aggro fixture must accept owner and unrelated raw target before cloak cleanup"+diagnostic(h,p,front,blocked));
        });
        h.runAfterDelay(ready+4,() -> {
            check(h,AbilityService.inSuper(p) && !SuperCamera.movementBlocked(p),"Roaming movement released after source cast");
            check(h,front.getTargetUnchecked()==null && blocked.getTargetUnchecked()==front,
                    "Scoped cloak drops this owner's raw hostile aggro, preserves unrelated raw target selection"+diagnostic(h,p,front,blocked));
            check(h,foreign.getEffect(MobEffects.INVISIBILITY)==preexisting && preexisting.getAmplifier()==1,
                    "Pre-existing foreign cloak is neither replaced nor extended");
            HunterExpandedSupers.cleanup(foreign);
            check(h,foreign.getEffect(MobEffects.INVISIBILITY)==preexisting,"Cleanup preserves exact pre-existing foreign cloak");
            check(h,swapped.hasEffect(MobEffects.INVISIBILITY) && dying.hasEffect(MobEffects.INVISIBILITY),"Other sessions own their own cloak");
            Guardians.data(swapped).setLoadout(GuardianClass.HUNTER,new Loadout(Guardians.data(swapped).loadout().orElseThrow().abilities()));
            dying.setHealth(0);
            HunterExpandedSupers.tick(h.getLevel().getServer());
            check(h,!swapped.hasEffect(MobEffects.INVISIBILITY) && !dying.hasEffect(MobEffects.INVISIBILITY),
                    "Equal-valued loadout epoch replacement and death each remove their owned cloak");
            var session=Guardians.runtime(p).superSession;
            for(int i=0;i<20;i++) session.primary();
            p.updateDataBeforeSync();
            check(h,!p.hasEffect(MobEffects.INVISIBILITY) && !p.isInvisible(),"Light acceptance immediately releases only owned cloak");
            float before=session.remaining();
            for(int i=0;i<20;i++) session.tick();
            check(h,session.remaining()==before,"Repeated same-gameTime ticks do not drain roaming duration");
        });
        h.runAfterDelay(ready+70,() -> {
            check(h,front.getHealth()<HP && blocked.getHealth()==HP,"Slash real contact respects wall"+diagnostic(h,p,front,blocked));
            check(h,status(p).contains("contacts=1") && !p.hasEffect(MobEffects.INVISIBILITY),
                    "Primary spam makes one contact and leaves scoped cloak off: "+status(p));
            p.setShiftKeyDown(true); Guardians.runtime(p).superSession.primary();
        });
        h.runAfterDelay(ready+80,() -> {
            check(h,status(p).contains("contacts=2") && status(p).contains("cloaked=true") && p.hasEffect(MobEffects.INVISIBILITY),
                    "Heavy contact re-acquires real scoped invisibility: "+status(p));
            MobEffectInstance installed=p.getEffect(MobEffects.INVISIBILITY);
            p.addEffect(new MobEffectInstance(MobEffects.INVISIBILITY,900,0,false,false,false));
            externallyRefreshed[0]=p.getEffect(MobEffects.INVISIBILITY);
            check(h,externallyRefreshed[0]==installed && installed.getDuration()>=890,
                    "Fixture exercises vanilla's same-object foreign refresh, not only replacement identity");
            check(h,status(p).contains("cloakOwned=false"),"Foreign update relinquishes removal ownership immediately");
        });
        h.runAfterDelay(ready+115,() -> {
            HunterExpandedSupers.cleanup(p); HunterExpandedSupers.cleanup(p);
            check(h,!AbilityService.inSuper(p) && HunterExpandedSupers.fieldCount(p)==0,"Spectral cleanup is idempotent");
            check(h,p.getEffect(MobEffects.INVISIBILITY)==externallyRefreshed[0] && externallyRefreshed[0].getDuration()>700,
                    "End cleanup preserves same-object external invisibility and its remaining duration");
            check(h,foreign.getEffect(MobEffects.INVISIBILITY)==preexisting,"Other player's pre-existing cloak remains untouched");
            check(h,!p.isNoGravity() && !p.getAbilities().flying,"Scoped cloak does not own physics flags");
            inventory(h,p); h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=240,skyAccess=true)
    public void stormsEdgeFirstThrowIsAutomaticAndAllThreeBlinksKeepPlayerBeforeWall(GameTestHelper h) {
        ServerPlayer p=player(h,HunterExpandedSupers.STORMS_EDGE); wall(h,7);
        Husk target=enemy(h,new Vec3(6.5,1,6.5)),blocked=enemy(h,new Vec3(8.5,1,6.5));
        aim(p,target.position().add(0,.9,0)); cast(h,p);
        int ready=windup(HunterExpandedSupers.STORMS_EDGE,34);
        h.runAfterDelay(ready+20,() -> {
            check(h,HunterExpandedSupers.emitted(p)==1 && HunterExpandedSupers.blinkCount(p)==1,"First throw and safe blink automatic: "+status(p));
            check(h,p.position().add(0,1,0).distanceTo(center(blocked))<4
                            && ray(p,p.position().add(0,1,0),center(blocked)).getType()==HitResult.Type.BLOCK,
                    "Blocked whirlwind control is inside actual radius and genuinely occluded"+diagnostic(h,p,target,blocked));
            check(h,target.getHealth()<HP && blocked.getHealth()==HP,"Whirlwind hits only accessible side"+diagnostic(h,p,target,blocked));
            check(h,p.getX()<h.absoluteVec(new Vec3(7,1,0)).x && h.getLevel().noCollision(p,p.getBoundingBox()),"Safe body before wall");
            p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5))); p.setOnGround(true); aim(p,target.position().add(0,.9,0));
            for(int i=0;i<20;i++) Guardians.runtime(p).superSession.primary();
        });
        h.runAfterDelay(ready+80,() -> {
            check(h,HunterExpandedSupers.emitted(p)==2,"Second primary recast has a single emission: "+status(p));
            p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5))); p.setOnGround(true); aim(p,target.position().add(0,.9,0));
            for(int i=0;i<20;i++) Guardians.runtime(p).superSession.primary();
        });
        h.runAfterDelay(ready+145,() -> {
            check(h,HunterExpandedSupers.emitted(p)==3 && HunterExpandedSupers.blinkCount(p)==3,"Three finite charges, three collision-checked blinks: "+status(p));
            check(h,!AbilityService.inSuper(p) && SimProjectile.activeCount(p)==0,"Final blink recovery naturally completes");
            check(h,p.getX()<h.absoluteVec(new Vec3(7,1,0)).x && h.getLevel().noCollision(p,p.getBoundingBox()),"No recast crosses wall");
            inventory(h,p); h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=130,skyAccess=true)
    public void loadoutEpochRevokesPersistentFieldAndPreservesUnrelatedEmission(GameTestHelper h) {
        ServerPlayer a=player(h,HunterExpandedSupers.GATHERING_STORM,new Vec3(2.5,1,3.5));
        ServerPlayer b=player(h,HunterExpandedSupers.GATHERING_STORM,new Vec3(2.5,1,10.5));
        wall(h,7); cast(h,a); cast(h,b);
        int ready=windup(HunterExpandedSupers.GATHERING_STORM,33);
        h.runAfterDelay(ready+15,() -> {
            check(h,HunterExpandedSupers.fieldCount(a)==1 && HunterExpandedSupers.fieldCount(b)==1,"Independent owned fields coexist");
            SimProjectile ordinary=SimProjectile.launch(a,a.position().add(0,4,0),Vec3.ZERO,0,100,
                    new ItemStack(Items.SNOWBALL),.2f,Element.KINETIC.color(),hit -> {});
            // Even an equal-valued new loadout is a new captured epoch.
            Guardians.data(a).setLoadout(GuardianClass.HUNTER,new Loadout(Guardians.data(a).loadout().orElseThrow().abilities()));
            HunterExpandedSupers.tick(h.getLevel().getServer());
            check(h,HunterExpandedSupers.fieldCount(a)==0 && HunterExpandedSupers.fieldCount(b)==1,"Epoch replacement retires only previous owner's field");
            HunterExpandedSupers.cleanup(a); HunterExpandedSupers.cleanup(a);
            check(h,!ordinary.isDone() && SimProjectile.activeCount(a)==1,"Exact-instance cleanup retains same-owner unrelated flight");
            Guardians.data(b).setGuardianClass(GuardianClass.TITAN);
            HunterExpandedSupers.tick(h.getLevel().getServer());
            Guardians.data(b).setGuardianClass(GuardianClass.HUNTER);
            HunterExpandedSupers.tick(h.getLevel().getServer());
            check(h,HunterExpandedSupers.fieldCount(b)==0,"Class round trip cannot resurrect retired field");
            inventory(h,a); inventory(h,b); h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=110,skyAccess=true)
    public void eyeHeightSlitCannotTeleportWholeBodyThroughWall(GameTestHelper h) {
        ServerPlayer p=player(h,HunterExpandedSupers.STORMS_EDGE); wall(h,6);
        // Dagger eye ray passes a 1-block slit; a survival player's 1.8-block body cannot.
        for(int z=0;z<=13;z++) h.setBlock(6,2,z,Blocks.AIR);
        Husk beyond=enemy(h,new Vec3(9,1,6.5));
        aim(p,beyond.position().add(0,.9,0)); cast(h,p);
        h.runAfterDelay(windup(HunterExpandedSupers.STORMS_EDGE,34)+25,() -> {
            check(h,HunterExpandedSupers.emitted(p)==1 && status(p).contains("impacts=1"),"Real automatic dagger resolves its collision: "+status(p));
            check(h,HunterExpandedSupers.blinkCount(p)==0 && p.getX()<h.absoluteVec(new Vec3(6,1,0)).x,
                    "Point-visible target cannot bypass swept player-volume wall: "+status(p));
            check(h,beyond.getHealth()==HP,"Failed route cannot create through-wall whirlwind damage"+diagnostic(h,p,beyond));
            HunterExpandedSupers.cleanup(p); inventory(h,p); h.succeed();
        });
    }

}
