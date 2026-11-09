package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Actual paid WeaponRuntime emission/flight fixtures; no client, model, sound or source-quality acceptance. */
public final class ExoticW350ProjectileGameTests {
    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static boolean near(float a,float b){return Math.abs(a-b)<.005f;}
    private static ServerPlayer player(GameTestHelper h,String id,double z){
        var p=TestPlayers.create(h,new Vec3(2.5,1,z),-90,0,"W350"+java.util.UUID.randomUUID().toString().substring(0,8));
        p.setNoGravity(true);
        equip(p,id);
        TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);WeaponAiming.cleanup(p);p.discard();TestPlayers.remove(p);});
        return p;
    }
    private static ItemStack equip(ServerPlayer p,String id){
        var stack=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());WeaponAccuracy.setAirborneBonus(stack,100);
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);return stack;
    }
    private static Husk target(GameTestHelper h,double x,double y,double z){
        var e=h.spawn(EntityTypes.HUSK,new Vec3(x,y,z));e.setNoAi(true);e.setNoGravity(true);e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);e.setHealth(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        TestCleanup.register(h,e::discard);return e;
    }
    private static WeaponProfile profile(ServerPlayer p){return WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow());}
    private static WeaponMagazine ammo(ServerPlayer p){return WeaponItems.magazine(p.getMainHandItem(),profile(p));}
    private static ExoticWeaponsW350.Token paid(ServerPlayer p){
        var a=ammo(p);checkPaid(a.consume());WeaponItems.save(p.getMainHandItem(),a);return ExoticWeaponsW350.capture(p);
    }
    private static void checkPaid(boolean paid){if(!paid)throw new IllegalStateException("Fixture requires an actual cartridge");}
    private static void prepare(GameTestHelper h,List<ServerPlayer> players,Runnable action){
        for(var p:players){WeaponRuntime.tickPlayer(p);WeaponAiming.toggle(p);}
        var sequence=h.startSequence();
        for(int tick=1;tick<=40;tick++){
            final int age=tick;
            sequence.thenExecuteAfter(1,()->{
                for(var p:players){
                    WeaponRuntime.tickPlayer(p);
                    if(!WeaponAiming.requested(p)&&age%4==0)WeaponAiming.toggle(p);
                }
                if(age==40){
                    for(var p:players)check(h,WeaponAiming.progress(p)==1&&WeaponAiming.coneDegrees(p)==0,"ADS and AE100 earn an exact ray");
                    action.run();
                }
            });
        }
    }
    private static void burst(GameTestHelper h,ServerPlayer p){
        check(h,WeaponRuntime.beginUse(p),"Real paid burst accepted");WeaponRuntime.cancelTrigger(p);
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",skyAccess=true,maxTicks=70)
    public void gravitonSecondPaidBoltUsesFullScaledDamageBeyondFalloff(GameTestHelper h){
        var p=player(h,"graviton_lance",6.5);p.setXRot(-90);
        var enemy=target(h,2.5,82,6.5);
        prepare(h,List.of(p),()->{
            var entry=WeaponItems.entry(p.getMainHandItem()).orElseThrow();
            check(h,enemy.getY()-p.getEyeY()>WeaponAiming.ballistics(p,entry).end(),"Witness is beyond ADS falloff end");
            int before=ammo(p).rounds();float base=profile(p).damage();
            burst(h,p);
            float first=1000-enemy.getHealth();
            check(h,near(first,base*.85f*.5f),"First actual body hit retains -15% and the 50% far floor; loss="+first);
            check(h,ammo(p).rounds()==before-1,"First bolt pays one cartridge synchronously");
            h.runAfterDelay(4,()->{
                WeaponRuntime.tickPlayer(p);float second=1000-enemy.getHealth()-first;
                check(h,near(second,base*1.353f),"Second actual body hit has +35.3% and no falloff; loss="+second);
                check(h,ammo(p).rounds()==before-2,"Exactly two cartridges pay for the two-bolt burst");
                check(h,WeaponRuntime.activeProjectiles(p)==0,"Pulse bolts stay synchronous hitscan");h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=70)
    public void gravitonFirstBulletKeepsBloomButOnlySecondBulletKicksTheView(GameTestHelper h){
        var p=player(h,"graviton_lance",6.5);target(h,10.5,1.8,6.5);
        prepare(h,List.of(p),()->{
            float yaw=p.getYRot(),pitch=p.getXRot(),bloom=WeaponAiming.bloom(p);burst(h,p);
            check(h,p.getYRot()==yaw&&p.getXRot()==pitch,"First paid bullet has no view recoil");
            check(h,WeaponAiming.bloom(p)>bloom,"Recoil suppression preserves the first paid bullet's bloom update");
            h.runAfterDelay(4,()->{
                WeaponRuntime.tickPlayer(p);
                check(h,p.getYRot()!=yaw||p.getXRot()!=pitch,"The second paid bullet retains its normal recoil");h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=135)
    public void jotunnOneChargeTracksOffAxisThenCreatesExactlySevenBurnPulses(GameTestHelper h){
        var p=player(h,"jotunn",6.5);var enemy=target(h,10.5,1.8,7.6);
        final boolean[] holding={false},launched={false};final int[] impactTick={-1};final float[] impactHealth={0};
        final int[] before={0};final double[] originZ={0};final boolean[] steered={false};
        h.onEachTick(()->{
            if(holding[0]){
                WeaponRuntime.heartbeatUse(p);WeaponRuntime.tickPlayer(p);
                if(ammo(p).rounds()<before[0]){
                    holding[0]=false;launched[0]=true;WeaponRuntime.cancelTrigger(p);
                    check(h,ammo(p).rounds()==before[0]-1,"The completed charge pays exactly one cartridge");
                    check(h,enemy.getHealth()==1000,"Paid launch cannot deal instant damage");
                }
            }
            if(!launched[0])return;
            for(var flight:WeaponRuntime.flights(p))if(Math.abs(flight.position().z-originZ[0])>.1)steered[0]=true;
            if(impactTick[0]<0&&WeaponRuntime.activeProjectiles(p)==0&&enemy.getHealth()<1000){
                impactTick[0]=h.getLevel().getServer().getTickCount();impactHealth[0]=enemy.getHealth();
                check(h,steered[0],"Actual flight turns away from its original axis before impact");
                check(h,ExoticWeaponsW350.pending(p)==1,"One impact owns one finite burn field");
            }
            if(impactTick[0]>=0&&h.getLevel().getServer().getTickCount()>=impactTick[0]+36){
                float burn=impactHealth[0]-enemy.getHealth();
                check(h,near(burn,7*profile(p).damage()*46/1453f),"Seven actual quarter-second burn pulses, loss="+burn);
                check(h,ExoticWeaponsW350.pending(p)==0&&ammo(p).rounds()==before[0]-1,"Burn completes with no extra cartridge or task");h.succeed();
            }
        });
        prepare(h,List.of(p),()->{
            var box=enemy.getBoundingBox().inflate(.08);var from=p.getEyePosition();
            check(h,box.clip(from,from.add(p.getLookAngle().scale(20))).isEmpty(),"Straight untracked flight misses the witness");
            before[0]=ammo(p).rounds();originZ[0]=p.getZ();
            check(h,WeaponRuntime.heartbeatUse(p),"Actual charge input accepted");holding[0]=true;
            check(h,ammo(p).rounds()==before[0]&&WeaponRuntime.activeProjectiles(p)==0,"Starting a charge neither pays nor creates a projectile");
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",skyAccess=true,maxTicks=150)
    public void outbreakCountsOnlyActualPaidHitsAndEmbeddedNanitesBoostTheNextRuntimeHit(GameTestHelper h){
        var p=player(h,"outbreak_perfected",6.5);p.setXRot(-90);var enemy=target(h,2.5,12,6.5);
        enemy.setPermanentlyInvulnerable(true);
        prepare(h,List.of(p),()->{
            int before=ammo(p).rounds();float base=profile(p).damage();
            for(int i=0;i<4;i++){
                int delay=i*8;
                if(delay==0)burst(h,p);else h.runAfterDelay(delay,()->burst(h,p));
            }
            h.runAfterDelay(29,()->{
                check(h,enemy.getHealth()==1000&&ExoticWeaponsW350.pending(p)==0&&ExoticWeaponsW350.outlawRemaining(p)==0,"Twelve invulnerable contacts create no nanites or Outlaw");
                check(h,ammo(p).rounds()==before-12,"Denied damage still pays the twelve actual bullets");enemy.setPermanentlyInvulnerable(false);
            });
            for(int i=0;i<4;i++)h.runAfterDelay(32+i*8,()->burst(h,p));
            h.runAfterDelay(70,()->{
                check(h,ExoticWeaponsW350.pending(p)==0,"All three rapid-hit seekers finish embedding");
                check(h,near(1000-enemy.getHealth(),12*base+3*base*77/27f),"Twelve paid body hits and exactly three nanite impacts lose actual health");
                float health=enemy.getHealth();burst(h,p);
                check(h,near(health-enemy.getHealth(),base*1.9f),"The next real direct hit receives the three-nanite 90% bonus");
                check(h,ammo(p).rounds()==before-25,"No nanite creates or consumes a cartridge");h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=200)
    public void originalOutbreakFixedOutlawUsesActualPrecisionKillAndNeverNaniteRefresh(GameTestHelper h){
        var p=player(h,"outbreak_perfected",6.5);var first=target(h,10.5,1,6.5);first.setHealth(1);
        prepare(h,List.of(p),()->{
            burst(h,p);
            check(h,!first.isAlive()&&ExoticWeaponsW350.outlawRemaining(p)==OutlawProfile.perk().durationTicks(),"Actual precision final blow activates the fixed Outlaw window");
            var source=p.getMainHandItem();p.setItemInHand(InteractionHand.MAIN_HAND,source.copy());
            check(h,ExoticWeaponsW350.outlawRemaining(p)==0,"Copied inventory data cannot borrow the original stack's fixed Outlaw proc");
            p.setItemInHand(InteractionHand.MAIN_HAND,source);
            h.runAfterDelay(5,()->{
                var secondary=target(h,10.5,1,6.5);secondary.setHealth(1);
                int remaining=ExoticWeaponsW350.outlawRemaining(p);
                h.runAfterDelay(8,()->{
                    check(h,!secondary.isAlive(),"A real secondary nanite killed the nearby witness");
                    check(h,ExoticWeaponsW350.outlawRemaining(p)==remaining-8,"Secondary nanite kills cannot refresh fixed Outlaw");
                    var entry=WeaponItems.entry(p.getMainHandItem()).orElseThrow();var base=profile(p);
                    var plan=ExoticWeaponsW350.reloadPlan(p,entry,new WeaponReloadPolicy.Plan(base.firstReloadTicks(),base.reloadTicks(),base.roundsPerInsert()));
                    var perk=OutlawProfile.perk();
                    check(h,plan.firstTicks()==WeaponStatCurves.reloadTicks(entry.id(),base.firstReloadTicks(),perk.reloadBonus(),perk.durationMultiplier())
                                    &&plan.firstTicks()<base.firstReloadTicks(),"Pinned Outlaw bonus and multiplier flow through the original weapon curve");
                    check(h,WeaponRuntime.reload(p),"A real reload accepts the fixed-trait plan");
                    check(h,WeaponRuntime.ammunition(p).orElseThrow().reloadDuration()==plan.firstTicks(),"Accepted runtime reload retains the accelerated duration");
                });
            });
            h.runAfterDelay(OutlawProfile.perk().durationTicks(),()->{
                check(h,ExoticWeaponsW350.outlawRemaining(p)==0,"The original fixed Outlaw expires on its sourced boundary");
                var entry=WeaponItems.entry(p.getMainHandItem()).orElseThrow();var base=profile(p);
                var normal=new WeaponReloadPolicy.Plan(base.firstReloadTicks(),base.reloadTicks(),base.roundsPerInsert());
                check(h,ExoticWeaponsW350.reloadPlan(p,entry,normal).equals(normal),"Expired fixed trait grants no reload bonus");h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=50)
    public void repeatedJotunnImpactReceiptCannotDuplicateDamageOrBurnField(GameTestHelper h){
        var p=player(h,"jotunn",6.5);var enemy=target(h,5,1.8,6.5);var token=paid(p);var at=enemy.getBoundingBox().getCenter();
        check(h,ExoticWeaponsW350.projectileImpact(token,at,enemy),"Paid Jotunn receipt owns its impact");
        float health=enemy.getHealth();check(h,ExoticWeaponsW350.pending(p)==1,"First receipt creates one field");
        check(h,ExoticWeaponsW350.projectileImpact(token,at,enemy),"Duplicate receipt stays handled by Jotunn");
        check(h,enemy.getHealth()==health&&ExoticWeaponsW350.pending(p)==1,"Duplicate impact cannot transact damage or create another field");
        h.runAfterDelay(36,()->{
            check(h,near(health-enemy.getHealth(),7*profile(p).damage()*46/1453f)&&ExoticWeaponsW350.pending(p)==0,"Only the original seven pulses execute");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void packHunterRejectsNonAlliedTeamAndRetiredGuardianSession(GameTestHelper h){
        var caster=player(h,"gjallarhorn",4.5);var friend=player(h,"bad_omens",6.5);var stranger=player(h,"bad_omens",8.5);
        var board=h.getLevel().getScoreboard();var blue=board.addPlayerTeam("w350b"+caster.getId());var red=board.addPlayerTeam("w350r"+caster.getId());
        TestCleanup.register(h,()->{board.removePlayerTeam(blue);board.removePlayerTeam(red);});
        board.addPlayerToTeam(caster.getScoreboardName(),blue);board.addPlayerToTeam(friend.getScoreboardName(),blue);board.addPlayerToTeam(stranger.getScoreboardName(),red);
        h.getLevel().addNewPlayer(caster);h.getLevel().addNewPlayer(friend);h.getLevel().addNewPlayer(stranger);
        paid(caster);
        check(h,ExoticWeaponsW350.packRemaining(friend)>0,"Same-team nearby player receives Pack Hunter");
        check(h,!Combat.isEnemy(caster,stranger)&&!caster.isAlliedTo(stranger)&&ExoticWeaponsW350.packRemaining(stranger)==0,"PvE non-opponent on another team is still not an ally");
        Guardians.data(friend).setGuardianClass(GuardianClass.TITAN);
        var stale=paid(friend);ExoticWeaponsW350.rocketDetonated(stale,friend.position());
        check(h,ExoticWeaponsW350.packRemaining(friend)==0&&ExoticWeaponsW350.pending(friend)==0,"Retired Guardian state cannot lend one final stale Wolfpack receipt");h.succeed();
    }
}
