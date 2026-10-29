package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.titan.*;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.*;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.*;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Behavioral server tests. Run by master after manifest registration; no native visual QA claim. */
public final class TitanW229GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean b,String message) {h.assertTrue(b,Component.literal(message));}
    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer p;
        final List<Entity> entities=new ArrayList<>();
        private record Scheduled(long gameTick,long testTickAtStart,long gameTickAtStart,Runnable action) {}
        final List<Scheduled> scheduled=new ArrayList<>();
        Fixture(GameTestHelper h,Element element) {
            this.h=h;TitanAbilities.register();
            p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0,"Titan_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.data(p).setGuardianClass(GuardianClass.TITAN);
            Guardians.data(p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(element));
            p.setNoGravity(true);p.setOnGround(true);
            TestCleanup.register(h,()->{
                scheduled.clear();TitanAbilities.cleanup(p);TestPlayers.remove(p);
                for(Entity e:entities){Statuses.forget(e);e.discard();}
            });
        }
        void tick() {
            // The shared END_SERVER_TICK camera loop DOES visit its own session map, including
            // embedded owners. Feed the same Rot handler as a connected client; never disable it.
            if(SuperCamera.active(p)) {
                int before=SuperCamera.rotations(p);
                p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
                check(h,SuperCamera.rotations(p)==before+1,"Actual move-packet path refreshes camera watchdog ["+clock()+"]");
            }
            AbilityService.tickPlayer(p);TitanAbilities.tick(h.getLevel().getServer());TestPlayers.drain(p);
            long now=gameTick();
            for(Scheduled task:List.copyOf(scheduled))if(now>=task.gameTick) {
                scheduled.remove(task); // Remove before running; nested scheduling cannot lose itself.
                check(h,now==task.gameTick,"Exact product game-clock deadline; test delta="+(h.getTick()-task.testTickAtStart)
                        +", game delta="+(now-task.gameTickAtStart)+" ["+clock()+"]");
                task.action.run();
            }
        }
        long gameTick() {return h.getLevel().getGameTime();}
        String clock() {return "game="+gameTick()+", server="+h.getLevel().getServer().getTickCount()+", test="+h.getTick();}
        void afterGameTicks(int delay,Runnable action) {
            scheduled.add(new Scheduled(gameTick()+delay,h.getTick(),gameTick(),action));
        }
        void prepareGround() {
            // Existing 26.3 camera regression documents air at source floor.snbt relative y=0.
            // Own a real landing/deploy pad; onGround alone must never bypass product support.
            for(int x=1;x<=5;x++)for(int z=2;z<=8;z++)h.setBlock(x,0,z,Blocks.STONE);
            check(h,h.getBlockState(new BlockPos(3,0,6)).is(Blocks.STONE),"Fixture owns full-block support at relative y=0");
        }
        Husk target(double x,double z) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,1,z));entities.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(200);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(200);return t;
        }
        Arrow arrow(Husk owner,double x,double y,double z,Vec3 velocity) {
            var a=h.spawn(EntityTypes.ARROW,new Vec3(x,y,z));entities.add(a);a.setOwner(owner);a.setNoGravity(true);a.setDeltaMovement(velocity);
            // The first sweep must start at this spawn, not Entity's zero default history.
            a.xo=a.getX();a.yo=a.getY();a.zo=a.getZ();return a;
        }
        void cast(AbilitySlot slot) {
            var result=AbilityService.use(p,slot);
            check(h,result==AbilityService.Result.OK,"Accepted "+slot+", got "+result+" ["+clock()+"]");
            if(slot==AbilitySlot.CLASS_ABILITY)ClassCastFieldFixture.installAcceptedField(p);
        }
        void barrier() {prepareGround();p.setOnGround(true);Guardians.data(p).setCooldown(AbilitySlot.CLASS_ABILITY,0);cast(AbilitySlot.CLASS_ABILITY);}
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void elevenAbilitiesAndThreeCompleteTitanPresets(GameTestHelper h) {
        TitanAbilities.register();
        // W230 adds three supers; the shared jump registry supplies each selectable variant.
        var expected = Set.of(
                "destiny:titan/class_ability",
                "destiny:titan/arc_grenade",
                "destiny:titan/arc_melee",
                "destiny:titan/arc_super",
                "destiny:titan/solar_grenade",
                "destiny:titan/solar_melee",
                "destiny:titan/solar_super",
                "destiny:titan/void_grenade",
                "destiny:titan/void_melee",
                "destiny:titan/void_super",
                "destiny:titan/thundercrash",
                "destiny:titan/burning_maul",
                "destiny:titan/ward_of_dawn",
                "destiny:titan/high_lift",
                "destiny:titan/jump",
                "destiny:titan/catapult_lift");
        var actual = AbilityRegistry.all().stream().filter(a -> a.guardianClass() == GuardianClass.TITAN)
                .map(a -> a.id().toString()).collect(java.util.stream.Collectors.toSet());
        check(h, actual.equals(expected), "Exact class roster including expanded supers and selectable jumps: " + actual);
        for(Element e:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
            var preset=TitanAbilities.preset(e);
            for(AbilitySlot slot:AbilitySlot.values()) {
                var a=AbilityRegistry.get(preset.get(slot)).orElseThrow();
                check(h,a.guardianClass()==GuardianClass.TITAN&&a.slot()==slot,"Class and slot metadata");
                if(slot!=AbilitySlot.JUMP&&slot!=AbilitySlot.CLASS_ABILITY)check(h,a.element()==e,"Element-specific preset");
            }
        }
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=35)
    public void liftIsBoundedAndPreservesFlagsAndInventory(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.p.setOnGround(false);f.p.setDeltaMovement(0,-.3,0);
        f.p.getInventory().setItem(0,new ItemStack(Items.DIAMOND,3));
        boolean flying=f.p.getAbilities().flying,mayfly=f.p.getAbilities().mayfly;
        check(h,AbilityService.use(f.p,AbilitySlot.JUMP)==AbilityService.Result.FAILED
                &&f.p.isNoGravity()&&f.p.getDeltaMovement().equals(new Vec3(0,-.3,0)),
                "No-gravity fixture is ineligible and rejection preserves its velocity/flags");
        // Shared jump eligibility requires real gravity; scope this to the lift test.
        f.p.setNoGravity(false);
        // Jump momentum reads the last client movement, not our last server velocity
        // command. Start from a measured vanilla ascent; strafe lift is not catapult.
        f.p.setKnownMovement(new Vec3(0,.05,0));f.p.setDeltaMovement(0,.05,0);
        f.cast(AbilitySlot.JUMP);
        check(h,f.p.getDeltaMovement().y>0 && Math.abs(f.p.getDeltaMovement().y-.15)<1e-9,
                "Strafe lift adds its .10 impulse to measured .05 ascent");
        check(h,AbilityService.use(f.p,AbilitySlot.JUMP)==AbilityService.Result.FAILED,"Repeated input cannot extend lift");
        h.onEachTick(f::tick);
        h.runAfterDelay(20,()->{
            check(h,!TitanJump.active(f.p),"Finite lift expires");
            check(h,!f.p.isNoGravity()&&f.p.getAbilities().flying==flying&&f.p.getAbilities().mayfly==mayfly,"Unrelated physics flags preserved");
            check(h,f.p.getInventory().getItem(0).is(Items.DIAMOND)&&f.p.getInventory().getItem(0).getCount()==3,"Inventory unchanged");
            f.p.setOnGround(true);
        });
        // Budget.observe is once per server tick. Leave an entire observed landing
        // tick before asking for a fresh airborne budget.
        h.runAfterDelay(22,()->{f.p.setOnGround(false);f.cast(AbilitySlot.JUMP);h.succeed();});
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void barricadeRejectsAirAndObstructionWithoutCooldownOrBlockWrites(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.prepareGround();f.p.setOnGround(false);
        check(h,AbilityService.use(f.p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.FAILED,"Airborne deploy rejected");
        check(h,Guardians.data(f.p).cooldown(AbilitySlot.CLASS_ABILITY)==0,"No cooldown spent on rejection");
        f.p.setOnGround(true);h.setBlock(new BlockPos(3,0,6),Blocks.AIR);
        check(h,AbilityService.use(f.p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.FAILED,"Spoofed onGround without actual support rejected");
        check(h,Guardians.data(f.p).cooldown(AbilitySlot.CLASS_ABILITY)==0,"Unsupported deploy spends no cooldown");
        f.prepareGround();
        BlockPos obstruction=new BlockPos(3,2,6);h.setBlock(obstruction,Blocks.DIAMOND_BLOCK);f.p.setOnGround(true);
        check(h,AbilityService.use(f.p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.FAILED,"Occupied rectangle rejected");
        check(h,h.getBlockState(obstruction).is(Blocks.DIAMOND_BLOCK)&&Guardians.data(f.p).cooldown(AbilitySlot.CLASS_ABILITY)==0,"Existing block preserved");
        h.setBlock(obstruction,Blocks.AIR);f.barrier();
        check(h,TitanClassAbility.displays(f.p)==1,"Exactly one virtual display");
        TitanAbilities.cleanup(f.p);check(h,!TitanClassAbility.active(f.p),"Cleanup removes cover");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=20)
    public void barricadeBlocksActualFrontRangedDamageButPassesBackAndMelee(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.barrier();
        var front=f.target(8,6.5);var back=f.target(.5,6.5);
        var a=f.arrow(front,8,2,6.5,Vec3.ZERO);float before=f.p.getHealth();
        f.p.hurtServer(h.getLevel(),f.p.damageSources().arrow(a,front),3);
        check(h,f.p.getHealth()==before&&TitanClassAbility.health(f.p)<80,"Front ranged hit blocked and HP spent");
        f.p.damageCooldownTime=0;f.p.hurtServer(h.getLevel(),f.p.damageSources().mobAttack(front),2);
        check(h,f.p.getHealth()<before,"Even front melee passes through");
        before=f.p.getHealth();var b=f.arrow(back,.5,2,6.5,Vec3.ZERO);f.p.damageCooldownTime=0;
        f.p.hurtServer(h.getLevel(),f.p.damageSources().arrow(b,back),2);
        check(h,f.p.getHealth()<before,"Back ranged hit passes through");
        before=f.p.getHealth();f.p.damageCooldownTime=0;f.p.hurtServer(h.getLevel(),f.p.damageSources().generic(),1);
        check(h,f.p.getHealth()<before,"Directionless environmental damage passes");
        var unowned=f.arrow(null,8,2,6.5,Vec3.ZERO);before=f.p.getHealth();f.p.damageCooldownTime=0;
        f.p.hurtServer(h.getLevel(),f.p.damageSources().arrow(unowned,null),2);
        check(h,f.p.getHealth()==before,"Unowned native ranged source is still physical cover");
        f.p.damageCooldownTime=0;f.p.hurtServer(h.getLevel(),f.p.damageSources().arrow(a,front),100);
        check(h,f.p.getHealth()==before&&!TitanClassAbility.active(f.p),"Final overkill hit absorbed once, zero-HP display destroyed");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=430)
    public void barricadeSweepsNativeArrowsRecastsOnceAndExpires(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.barrier();var mob=f.target(8,6.5);
        var front=f.arrow(mob,5,2,6.5,new Vec3(-2,0,0));
        var back=f.arrow(mob,3,2,6.5,new Vec3(1,0,0));
        // Exercise the same sweep handler synchronously before native entity movement.
        TitanAbilities.tick(h.getLevel().getServer());
        check(h,front.isRemoved()&&!back.isRemoved(),"Front arrow intercepted, back arrow preserved");
        check(h,TitanClassAbility.health(f.p)<80,"Projectile costs barrier health");back.discard();
        f.barrier();check(h,TitanClassAbility.displays(f.p)==1,"Recast replaces, never duplicates");
        h.onEachTick(f::tick);
        int duration=(int)AbilityService.equipped(f.p,AbilitySlot.CLASS_ABILITY).orElseThrow().param("duration_ticks",400);
        f.afterGameTicks(duration-1,()->check(h,TitanClassAbility.displays(f.p)==1,"Live cover remains before full configured duration ["+f.clock()+"]"));
        f.afterGameTicks(duration,()->{check(h,TitanClassAbility.displays(f.p)==0,"Product-clock expiry destroys display and protection");h.succeed();});
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=120)
    public void pulseGrenadeDamagesRepeatedlyButCannotCrossWallOrHitPlayer(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.p.setXRot(15);var target=f.target(6.5,6.5);var hidden=f.target(6.5,8.5);
        for(int x=4;x<=8;x++)for(int y=1;y<=3;y++)h.setBlock(new BlockPos(x,y,7),Blocks.STONE);
        float playerHealth=f.p.getHealth();f.cast(AbilitySlot.GRENADE);h.onEachTick(f::tick);
        h.startSequence().thenExecuteAfter(65,()->{
            check(h,target.getHealth()<195,"Actual pulse field damages more than once");
            check(h,hidden.getHealth()==200&&f.p.getHealth()==playerHealth,"LOS wall and player exclusion");
            check(h,target.getLastHurtByPlayer()==f.p,"Accepted grenade owner credited");
            h.runAfterDelay(40,()->{check(h,TitanGrenade.fields(f.p)==0,"Pulse field expires");h.succeed();});
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=120)
    public void fusionWaitsForFuseAndSuppressorCleansOnlyItsOwnEffects(GameTestHelper h) {
        var f=new Fixture(h,Element.SOLAR);var target=f.target(6.5,6.5);f.cast(AbilitySlot.GRENADE);h.onEachTick(f::tick);
        h.runAfterDelay(10,()->check(h,target.getHealth()==200,"Fusion contact does not explode before fuse"));
        h.startSequence().thenExecuteAfter(35,()->{
            check(h,target.getHealth()<200&&TitanGrenade.fields(f.p)==0,"Fusion detonates once after fuse");
            float after=target.getHealth();
            Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.VOID));f.tick();
            Guardians.data(f.p).setCooldown(AbilitySlot.GRENADE,0);
            target.addEffect(new MobEffectInstance(MobEffects.SPEED,150,1));
            f.cast(AbilitySlot.GRENADE);
            h.runAfterDelay(12,()->{
                check(h,target.hasEffect(MobEffects.WEAKNESS)&&target.getHealth()<after,"Real suppressor field applies weakness and damage");
                TitanAbilities.cleanup(f.p);
                check(h,!target.hasEffect(MobEffects.WEAKNESS)&&target.hasEffect(MobEffects.SPEED),"Own suppression cleared, unrelated effect preserved");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void frontalPoweredStrikeAndThrownMeleesUseRealContact(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);var front=f.target(4.5,6.5);var rear=f.target(.5,6.5);
        var blocked=f.target(4.5,8);for(int y=1;y<=3;y++)h.setBlock(new BlockPos(3,y,7),Blocks.STONE);
        f.cast(AbilitySlot.MELEE);
        check(h,front.getHealth()<200&&rear.getHealth()==200&&blocked.getHealth()==200,"Front cone and LOS enforced");
        front.setPos(h.absoluteVec(new Vec3(7.5,1,6.5)));Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.SOLAR));f.tick();
        Guardians.data(f.p).setCooldown(AbilitySlot.MELEE,0);f.cast(AbilitySlot.MELEE);h.onEachTick(f::tick);
        float health=front.getHealth();
        h.startSequence().thenExecuteAfter(10,()->{
            check(h,front.getHealth()<health,"Solar hammer actually collides and damages");
            Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.VOID));f.tick();
            Guardians.data(f.p).setCooldown(AbilitySlot.MELEE,0);float before=front.getHealth();f.cast(AbilitySlot.MELEE);
            h.startSequence().thenExecuteAfter(10,()->{check(h,front.getHealth()<before,"Void shield actually collides and damages");h.succeed();});
        });
    }
    // The 16x8x12 floor is normally encased with a BARRIER ceiling. These upward
    // flight controls require open sky; normal collision would finish them before deployment.
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=600,skyAccess=true)
    public void allThreeRoamingSupersSpendEnergyAttackAndRejectRepeatedClicks(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);f.prepareGround();var target=f.target(4.5,6.5);
        check(h,AbilityService.use(f.p,AbilitySlot.SUPER)==AbilityService.Result.NOT_READY,"No free super");
        h.onEachTick(f::tick);
        ordinaryFlightCoexists(h,f,()->superStage(h,f,target,Element.ARC,()->superStage(h,f,target,Element.SOLAR,
                ()->superStage(h,f,target,Element.VOID,()->naturalExpiryFlight(h,f)))));
    }
    private static void ordinaryFlightCoexists(GameTestHelper h,Fixture f,Runnable next) {
        Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.VOID));
        f.p.setXRot(-90);f.cast(AbilitySlot.GRENADE);
        // W252 owns preparation/release/recovery before another ability may begin.
        // This coexistence test starts from a real released flight, never an instant-emission fixture.
        f.afterGameTicks(kim.biryeong.destiny.ability.GrenadeThrow.DURATION_TICKS+1,
                ()->ordinaryReleasedFlightCoexists(h,f,next));
    }
    private static void ordinaryReleasedFlightCoexists(GameTestHelper h,Fixture f,Runnable next) {
        check(h,SimProjectile.activeCount(f.p)==1,"Real accepted ordinary grenade flight exists before super");
        Guardians.data(f.p).setSuperEnergy(1);f.cast(AbilitySlot.SUPER);
        check(h,SimProjectile.activeCount(f.p)==1&&AbilityService.inSuper(f.p),"Ordinary context flight does not reject or disappear on super start");
        f.afterGameTicks(30,()->{
            check(h,AbilityService.inSuper(f.p)&&TitanSuper.active(f.p)&&SimProjectile.activeCount(f.p)==1&&TitanGrenade.fields(f.p)==0,
                    "Ordinary context flight survives full deploy without collision or cancellation ["+f.clock()+"]");
            check(h,AbilityService.perform(f.p,GuardianAction.PRIMARY),"Active super handles primary after deployment");
        });
        f.afterGameTicks(38,()->{
            check(h,SimProjectile.activeCount(f.p)==2,"Both ordinary context flight and released super flight actually coexist ["+f.clock()+", flights="+SimProjectile.activeCount(f.p)+", fields="+TitanGrenade.fields(f.p)+", inSuper="+AbilityService.inSuper(f.p)+"]");
            AbilityService.endSuper(f.p);
            check(h,SimProjectile.activeCount(f.p)==1,"Ending session cancels only super flight, preserves ordinary context flight");
            TitanAbilities.cleanup(f.p);
            check(h,SimProjectile.activeCount(f.p)==0,"Owner context cleanup then cancels the remaining owned grenade");
            f.p.setXRot(0);next.run();
        });
    }
    private static void naturalExpiryFlight(GameTestHelper h,Fixture f) {
        Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.VOID));
        // A real non-session SimProjectile with a long fixture lifetime remains an ordinary-flight
        // control through the full configured super duration. Its stationary empty-space path avoids collisions.
        var ordinary=SimProjectile.launch(f.p,f.p.getEyePosition().add(0,2,0),Vec3.ZERO,0,600,
                new ItemStack(Items.SNOWBALL),.25f,Element.VOID.color(),hit->check(h,false,"Ordinary control unexpectedly impacted"));
        TestCleanup.register(h,ordinary::cancel);
        Guardians.data(f.p).setSuperEnergy(1);f.cast(AbilitySlot.SUPER);
        SuperSession session=Guardians.runtime(f.p).superSession;
        int duration=(int)AbilityService.equipped(f.p,AbilitySlot.SUPER).orElseThrow().param("duration_ticks",340);
        f.p.setXRot(-60);
        f.afterGameTicks(duration-10,()->{
            check(h,Guardians.runtime(f.p).superSession==session,"Original session survives real rotation heartbeat until late attack ["+f.clock()+"]");
            AbilityService.perform(f.p,GuardianAction.PRIMARY);
        });
        f.afterGameTicks(duration-2,()->check(h,!ordinary.isDone()&&SimProjectile.activeCount(f.p)==2,
                "Control: ordinary and super projectile visuals are actually in flight ["+f.clock()+"]"));
        f.afterGameTicks(duration-1,()->check(h,Guardians.runtime(f.p).superSession==session,"Super remains active until product-clock expiry"));
        f.afterGameTicks(duration,()->{
            check(h,!AbilityService.inSuper(f.p)&&!ordinary.isDone()&&SimProjectile.activeCount(f.p)==1,
                    "Natural expiry cancels only super flight and preserves ordinary visual");
            ordinary.cancel();check(h,SimProjectile.activeCount(f.p)==0,"Ordinary fixture tears down explicitly");h.succeed();
        });
    }
    private static void superStage(GameTestHelper h,Fixture f,Husk target,Element e,Runnable next) {
        TitanAbilities.cleanup(f.p);Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(e));
        Guardians.data(f.p).setSuperEnergy(1);f.p.setOnGround(true);f.p.setDeltaMovement(Vec3.ZERO);
        target.setHealth(200);f.cast(AbilitySlot.SUPER);
        check(h,AbilityService.inSuper(f.p)&&Guardians.data(f.p).superEnergy()==0,"Accepted super spends full energy");
        int deploy=e==Element.SOLAR?27:e==Element.VOID?29:31;
        int contact=e==Element.ARC?5:7;
        AbilityService.perform(f.p,GuardianAction.PRIMARY);
        check(h,SimProjectile.activeCount(f.p)==0&&target.getHealth()==200,"Deploy locks attack");
        f.afterGameTicks(deploy+1,()->{
            AbilityService.perform(f.p,GuardianAction.PRIMARY);
            int projectiles=SimProjectile.activeCount(f.p);float after=target.getHealth();
            for(int n=0;n<5;n++)AbilityService.perform(f.p,GuardianAction.PRIMARY);
            check(h,SimProjectile.activeCount(f.p)==projectiles&&target.getHealth()==after,"Repeated clicks cannot duplicate attack");
            f.afterGameTicks(contact-1,()->check(h,SimProjectile.activeCount(f.p)==projectiles&&target.getHealth()==after,
                    "Animation wind-up cannot release payload early"));
            f.afterGameTicks(contact+5,()->{
                check(h,target.getHealth()<after&&target.getLastHurtByPlayer()==f.p,"Primary contact adds damage after any activation slam and credits owner");
                TitanAbilities.cleanup(f.p);check(h,!AbilityService.inSuper(f.p),"Cleanup ends owned session");next.run();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void lifecycleCancelsDisplaysProjectilesAndLeavesOtherOwnerIntact(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC);var other=new Fixture(h,Element.VOID);
        other.p.setPos(h.absoluteVec(new Vec3(2.5,1,3.5)));f.barrier();other.barrier();f.cast(AbilitySlot.GRENADE);
        Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.SOLAR));f.tick();
        check(h,!TitanClassAbility.active(f.p)&&SimProjectile.activeCount(f.p)==0,"Reselection cancels old display and projectile");
        check(h,TitanClassAbility.active(other.p),"Other owner's cover preserved");
        f.barrier();f.p.setHealth(0);f.tick();check(h,!TitanClassAbility.active(f.p),"Death cleans display");
        f.p.setHealth(20);f.barrier();
        var second=h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER)?Level.OVERWORLD:Level.NETHER);
        check(h,second!=null,"Second dimension fixture");f.p.setServerLevel(second);TitanAbilities.tick(h.getLevel().getServer());
        check(h,!TitanClassAbility.active(f.p),"Dimension change cleans display");f.p.setServerLevel(h.getLevel());
        f.barrier();Guardians.data(f.p).setGuardianClass(GuardianClass.NONE);f.tick();
        check(h,!TitanClassAbility.active(f.p),"Class removal cleans display");
        Guardians.data(f.p).setGuardianClass(GuardianClass.TITAN);
        TitanAbilities.cleanup(f.p);TitanAbilities.cleanup(f.p);
        check(h,TitanClassAbility.active(other.p),"Repeated cleanup stays owner-scoped");h.succeed();
    }
}
