package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.titan.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.*;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.entity.projectile.arrow.Arrow;
import net.minecraft.world.item.*;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/** New lifecycle/geometry behavior; original animation timing is a source contract, not a visual claim. */
public final class TitanW230GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean b,String message) {h.assertTrue(b,Component.literal(message));}
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;
        final List<Entity> entities=new ArrayList<>();
        private record Task(long due,Runnable action) { }
        final List<Task> tasks=new ArrayList<>();
        Fixture(GameTestHelper h,Element element,String superName) {
            this.h=h;TitanAbilities.register();
            for(int x=0;x<=14;x++)for(int z=0;z<=10;z++)h.setBlock(x,0,z,Blocks.STONE);
            p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0,"T230_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.data(p).setGuardianClass(GuardianClass.TITAN);
            var slots=new EnumMap<AbilitySlot,net.minecraft.resources.Identifier>(AbilitySlot.class);
            var preset=TitanAbilities.preset(element);for(AbilitySlot s:AbilitySlot.values())slots.put(s,preset.get(s));
            slots.put(AbilitySlot.SUPER,kim.biryeong.destiny.DestinyGuardians.id("titan/"+superName));
            Guardians.data(p).setLoadout(GuardianClass.TITAN,new Loadout(slots));
            p.setNoGravity(true);p.setOnGround(true);
            TestCleanup.register(h,()->{
                tasks.clear();TitanExpandedSupers.cleanup(p);TitanAbilities.cleanup(p);TestPlayers.remove(p);
                entities.forEach(Entity::discard);
            });
        }
        void cast() {
            Guardians.data(p).setSuperEnergy(1);
            check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Accepted native ability service super");
        }
        void tick() {
            if(SuperCamera.active(p)) {
                int rotations=SuperCamera.rotations(p);
                p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
                check(h,SuperCamera.rotations(p)==rotations+1,"Real rotation packet refreshes owned camera watchdog");
            }
            AbilityService.tickPlayer(p);TitanAbilities.tick(h.getLevel().getServer());TitanExpandedSupers.tick(h.getLevel().getServer());
            TestPlayers.drain(p);
            for(Task task:List.copyOf(tasks))if(h.getLevel().getGameTime()>=task.due) {
                tasks.remove(task);check(h,h.getLevel().getGameTime()==task.due,"Product game-clock deadline");task.action.run();
            }
        }
        void after(int ticks,Runnable action) {tasks.add(new Task(h.getLevel().getGameTime()+ticks,action));}
        void primary() {AbilityService.perform(p,GuardianAction.PRIMARY);}
        Husk target(double x,double z) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,1,z));entities.add(t);t.setNoAi(true);t.setNoGravity(true);
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(200);t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(200);return t;
        }
        Arrow arrow(Husk owner,double x,double z) {
            var arrow=h.spawn(EntityTypes.ARROW,new Vec3(x,2,z));entities.add(arrow);arrow.setOwner(owner);arrow.setNoGravity(true);
            arrow.setDeltaMovement(Vec3.ZERO);arrow.xo=arrow.getX();arrow.yo=arrow.getY();arrow.zo=arrow.getZ();return arrow;
        }
        String status() {return TitanExpandedSupers.status(p);}
    }

    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void fistsGroundStartHasOneContactAndFullStartupAttackGate(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC,"arc_super");var target=f.target(4.5,6.5);f.cast();h.onEachTick(f::tick);
        for(int i=0;i<8;i++)f.primary();
        check(h,target.getHealth()==200,"Early primary cannot bypass source cast");
        f.after(27,()->check(h,target.getHealth()==200,"Ground cast candidate not released early"));
        f.after(28,()->{
            check(h,target.getHealth()<200&&target.getLastHurtByPlayer()==f.p,"One grounded activation impact credits caster");
            float health=target.getHealth();for(int i=0;i<8;i++)f.primary();
            f.after(3,()->{
                check(h,target.getHealth()==health,"Activation hit is not replayed and cast recovery remains gated");
                f.primary();f.after(7,()->{check(h,target.getHealth()<health,"Authored light attack available after original cast");h.succeed();});
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=70,skyAccess=true)
    public void fistsAirWaitsForActualLandingThenPlaysFiniteLandingRecovery(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC,"arc_super");var target=f.target(4.5,6.5);
        f.p.setPos(h.absoluteVec(new Vec3(2.5,4,6.5)));f.p.setOnGround(false);f.cast();h.onEachTick(f::tick);
        f.after(16,()->{
            f.primary();check(h,target.getHealth()==200,"Air enter cannot cause an imaginary ground slam");
            f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5)));f.p.setOnGround(true);
            f.after(1,()->{
                f.primary();check(h,target.getHealth()==200,"Landing animation windup cannot be skipped");
                f.after(15,()->check(h,target.getHealth()==200,"No slam before provisional landing contact"));
                f.after(17,()->{
                    check(h,target.getHealth()<200,"One contact only after true support and landing animation");float health=target.getHealth();
                    f.after(4,()->{check(h,target.getHealth()==health,"Landing contact does not repeat");h.succeed();});
                });
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=70,skyAccess=true)
    public void thundercrashSweepsWallAndRestoresOnlyOwnedPhysics(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC,"thundercrash");var behind=f.target(7.5,6.5);
        for(int y=1;y<=5;y++)for(int z=4;z<=8;z++)h.setBlock(5,y,z,Blocks.STONE);
        f.p.setNoGravity(false);Vec3 beforeVelocity=new Vec3(0,.03,0);f.p.setDeltaMovement(beforeVelocity);
        f.p.getInventory().setItem(0,new ItemStack(Items.DIAMOND,3));
        boolean flying=f.p.getAbilities().flying,mayfly=f.p.getAbilities().mayfly,noPhysics=f.p.noPhysics;
        Vec3 before=f.p.position();f.cast();h.onEachTick(f::tick);
        f.after(16,()->check(h,f.p.position().distanceToSqr(before)<1e-8,"No flight before original startup completes"));
        f.after(28,()->{
            check(h,f.status().contains("impacted=true"),"Swept body volume actually produces wall impact");
            check(h,f.p.getX()<=h.absoluteVec(new Vec3(4.71,1,6.5)).x&&h.getLevel().noCollision(f.p,f.p.getBoundingBox()),"Entire body remains on safe side of wall");
            check(h,behind.getHealth()==200,"Impact cannot damage through wall");
            Vec3 pos=f.p.position();f.tick();f.tick();check(h,f.p.position().distanceToSqr(pos)<1e-8,"Same game tick cannot move twice");
            TitanExpandedSupers.cleanup(f.p);
            check(h,!f.p.isNoGravity()&&f.p.getDeltaMovement().distanceToSqr(beforeVelocity)<1e-8,"Original gravity/velocity restored");
            check(h,f.p.getAbilities().flying==flying&&f.p.getAbilities().mayfly==mayfly&&f.p.noPhysics==noPhysics,"No flight/noclip authority leak");
            check(h,f.p.getInventory().getItem(0).is(Items.DIAMOND)&&f.p.getInventory().getItem(0).getCount()==3,"Inventory unchanged");
            check(h,!SuperCamera.active(f.p)&&!AbilityService.inSuper(f.p),"Owned camera/session cleaned");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=70,skyAccess=true)
    public void thundercrashCeilingAndEpochCancellationCannotLeaveFlight(GameTestHelper h) {
        var f=new Fixture(h,Element.ARC,"thundercrash");
        for(int x=1;x<=5;x++)for(int z=4;z<=8;z++)h.setBlock(x,4,z,Blocks.STONE);
        f.p.setXRot(-90);f.p.setNoGravity(false);f.cast();h.onEachTick(f::tick);
        f.after(26,()->{
            check(h,f.status().contains("impacted=true")&&f.p.getBoundingBox().maxY<=h.absoluteVec(new Vec3(0,4,0)).y+.001,"Swept head volume cannot enter ceiling");
            Guardians.data(f.p).setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.SOLAR));
            f.after(1,()->{
                check(h,!AbilityService.inSuper(f.p)&&!f.p.isNoGravity()&&!f.status().contains("aftershock=true"),"Epoch change cleans flight and lingering damage field");
                h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=150)
    public void maulRejectsSpamAndWaveStopsAtWallAndExpires(GameTestHelper h) {
        var f=new Fixture(h,Element.SOLAR,"burning_maul");var close=f.target(4.5,6.5);var behind=f.target(8.5,6.5);
        for(int y=1;y<=3;y++)for(int z=4;z<=8;z++)h.setBlock(7,y,z,Blocks.STONE);
        f.cast();h.onEachTick(f::tick);f.primary();check(h,close.getHealth()==200,"Deployment primary rejected");
        f.after(28,()->{
            f.primary();float hp=close.getHealth();for(int i=0;i<8;i++)f.primary();
            check(h,close.getHealth()==hp,"Repeated presses cannot bypass contact delay");
            f.after(7,()->{
                check(h,close.getHealth()<hp,"Finite spin actually hits nearby enemy");float after=close.getHealth();
                f.after(4,()->check(h,close.getHealth()==after,"Repeated input causes only one spin contact"));
            });
            f.after(16,()->{
                f.p.setShiftKeyDown(true);f.primary();for(int i=0;i<8;i++)f.primary();
                f.after(10,()->{
                    check(h,f.status().contains("waves=1"),"One accepted heavy emits one bounded wave");
                    check(h,close.getHealth()<hp-14,"The released wave actually damages a visible target");
                    f.p.setShiftKeyDown(false);
                    f.after(82,()->{
                        check(h,f.status().contains("waves=0")&&behind.getHealth()==200,"Wave expires and cannot cross wall");
                        TitanExpandedSupers.cleanup(f.p);h.succeed();
                    });
                });
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=670)
    public void wardExternalThreatsAlliesFiniteFieldAndEpochCleanup(GameTestHelper h) {
        var f=new Fixture(h,Element.VOID,"ward_of_dawn");var outside=f.target(9.5,6.5);var inside=f.target(3.5,6.5);
        var ally=TestPlayers.create(h,new Vec3(2.5,1,5.5),0,0,"WardAlly"+UUID.randomUUID().toString().substring(0,6));
        TestCleanup.register(h,()->TestPlayers.remove(ally));
        var board=h.getLevel().getScoreboard();var team=board.addPlayerTeam("w230"+UUID.randomUUID().toString().substring(0,8));
        board.addPlayerToTeam(f.p.getScoreboardName(),team);board.addPlayerToTeam(ally.getScoreboardName(),team);
        TestCleanup.register(h,()->board.removePlayerTeam(team));
        f.cast();h.onEachTick(f::tick);
        f.after(31,()->{
            check(h,f.status().contains("ward=true")&&!AbilityService.inSuper(f.p)&&!SuperCamera.active(f.p),"Dome outlives cast while camera/pose are free");
            var a=f.arrow(outside,9.5,6.5);var b=f.arrow(inside,3.5,6.5);
            check(h,!TitanExpandedSupers.allowDamage(f.p,f.p.damageSources().arrow(a,outside),2),"External projectile damage denied");
            check(h,!TitanExpandedSupers.allowDamage(ally,ally.damageSources().mobAttack(outside),2),"Allied player inside is protected");
            check(h,TitanExpandedSupers.allowDamage(f.p,f.p.damageSources().arrow(b,inside),2),"Attacker already inside is not blocked");
            check(h,TitanExpandedSupers.allowDamage(f.p,f.p.damageSources().generic(),2),"Environment damage is not immunity");
            var incoming=f.arrow(outside,7.5,6.5);incoming.setDeltaMovement(-2,0,0);
            var outgoing=f.arrow(null,5.5,6.5);outgoing.setOwner(f.p);outgoing.setDeltaMovement(2,0,0);
            f.after(1,()->check(h,incoming.isRemoved()&&!outgoing.isRemoved(),"Native inbound projectile intercepted; caster outbound projectile retained"));
            f.p.setPos(h.absoluteVec(new Vec3(9.5,1,4.5)));
            check(h,TitanExpandedSupers.allowDamage(f.p,f.p.damageSources().mobAttack(outside),2),"Caster outside loses cover");
            f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5)));
            f.after(600,()->{
                check(h,!f.status().contains("ward=true")&&TitanExpandedSupers.allowDamage(f.p,f.p.damageSources().arrow(a,outside),2),"Exact field lifetime is finite");
                f.cast();f.after(31,()->{
                    check(h,f.status().contains("ward=true"),"Can recast after full cleanup");
                    var saved=Guardians.data(f.p).loadout().orElseThrow();
                    TitanExpandedSupers.cleanup(f.p);
                    Guardians.data(f.p).setGuardianClass(GuardianClass.NONE);Guardians.data(f.p).setGuardianClass(GuardianClass.TITAN);
                    Guardians.data(f.p).setLoadout(GuardianClass.TITAN,saved);f.tick();
                    check(h,!f.status().contains("ward=true"),"Returning to the same class/loadout cannot resurrect old dome");h.succeed();
                });
            });
        });
    }
}
