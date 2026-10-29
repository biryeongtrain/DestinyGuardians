package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerInputPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

/** Real ADS clock, real paid WeaponRuntime.beginUse shots and actual SHOTS trajectory snapshots.
 * Global WeaponTracking advances embedded ADS-only sessions; global STATES/SHOTS own flight ticks.
 * This fixture NEVER calls WeaponRuntime.tickPlayer from onEachTick or delayed callbacks.
 * Quantitative tuning is explicitly Minecraft-authored, not measured Destiny 2 physics/art. */
public final class TrackingW104GameTests {
    private static final String FLOOR="destiny-test:w78_floor", ENV="destiny-test:w90_isolated";
    private static final int LOCK_AT=50, WHITE=0xF1F3F5;
    private static final Input IDLE=new Input(false,false,false,false,false,false,false);
    private static final Input ADS=new Input(false,false,false,false,false,true,false);
    private static void check(GameTestHelper h,boolean condition,String message) {
        h.assertTrue(condition,Component.literal(message));
    }
    private static long now(ServerPlayer p) {return p.level().getServer().getTickCount();}
    private static WeaponProfile profile(ItemStack gun) {return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());}
    private static WeaponMagazine ammo(ItemStack gun) {return WeaponItems.magazine(gun,profile(gun));}
    private static void input(ServerPlayer p,boolean ads) {
        // W240 input contract: crouch is native movement; ADS is a debounced left click.
        if (WeaponAiming.requested(p) != ads) WeaponAiming.toggle(p);
    }
    private static void aim(ServerPlayer p,Entity target) {
        Vec3 d=target.getBoundingBox().getCenter().subtract(p.getEyePosition());
        float yaw=(float)Math.toDegrees(Math.atan2(-d.x,d.z));
        p.setYRot(yaw);p.setYHeadRot(yaw);
        p.setXRot((float)-Math.toDegrees(Math.atan2(d.y,Math.hypot(d.x,d.z))));
    }
    private static void idle(GameTestHelper h,ServerPlayer p,String context) {
        var s=WeaponTracking.status(p);
        check(h,s.phase()==WeaponTracking.Phase.IDLE&&s.ticks()==0&&s.lockedTarget()==null,context);
    }
    private static void locked(GameTestHelper h,ServerPlayer p,Entity target) {
        var s=WeaponTracking.status(p);
        check(h,s.supported()&&s.phase()==WeaponTracking.Phase.LOCKED&&s.ticks()==20
                &&target.getUUID().equals(s.lockedTarget()),"Twenty real fully-ADS samples lock only the expected entity");
    }
    private static void hud(GameTestHelper h,ServerPlayer p,int color) {
        WeaponReticleHud.update(p,WeaponAiming.progress(p),WeaponAiming.bloom(p),WeaponRuntime.reloading(p));
        var entry=WeaponItems.entry(p.getMainHandItem()).orElseThrow();
        boolean physical=WeaponAimPresentation.physicalSight(entry,WeaponAiming.progress(p));
        boolean active=WeaponTracking.status(p).phase()!=WeaponTracking.Phase.IDLE;
        long count=DisplayHud.getHuds(p).keySet().stream().filter(id->id.startsWith(WeaponReticleHud.PREFIX)).count();
        if(physical&&!active) {
            check(h,count==0,"Idle physical optic has neither hip overlay nor stale tracking ticks");return;
        }
        var node=DisplayHud.getHud(p,physical?WeaponReticleHud.TRACKING_TOP_ID:WeaponReticleHud.FRAME_ID);
        check(h,node instanceof ItemDisplayHud,"Tracking feedback exists even when physical optics replace hip ring");
        var data=((ItemDisplayHud)node).getItem().get(DataComponents.CUSTOM_MODEL_DATA);
        check(h,data!=null&&Objects.equals(data.getColor(0),color),"Frame uses actual authoritative tracking tint");
        check(h,count==(physical?4:2),"Bounded physical tracking ticks or original hip pair");
        if(physical)check(h,DisplayHud.getHud(p,WeaponReticleHud.FRAME_ID)==null
                &&DisplayHud.getHud(p,WeaponReticleHud.CENTER_ID)==null,"No hip ring over real rocket optic");
    }
    private static final class Actor {
        final ServerPlayer p; final ItemStack gun; final Husk target;
        Actor(ServerPlayer p,ItemStack gun,Husk target) {this.p=p;this.gun=gun;this.target=target;}
    }
    private static final class Fixture {
        final GameTestHelper h; final long started;
        final List<ServerPlayer> players=new ArrayList<>(); final List<Husk> mobs=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;started=h.getLevel().getServer().getTickCount();
            for(int x=0;x<48;x++)for(int z=0;z<32;z++)h.setBlock(x,3,z,Blocks.STONE);
            TestCleanup.register(h,()->{
                for(var p:players) {
                    p.setServerLevel(h.getLevel());p.setGameMode(GameType.SURVIVAL);p.setShiftKeyDown(false);p.stopUsingItem();
                    WeaponRuntime.cleanup(p);CombatHud.remove(p);WeaponReticleHud.remove(p);
                    if(p.level().players().contains(p))p.level().removePlayerImmediately(p,Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
                mobs.forEach(Entity::discard);
            });
            h.onEachTick(()->{
                for(var p:players) {
                    bounded(p);AbilityService.tickPlayer(p);TestPlayers.drain(p);
                    for(var flight:WeaponRuntime.flights(p)) {
                        var r=h.relativeVec(flight.position());
                        check(h,r.x>0&&r.x<48&&r.y>3&&r.y<12&&r.z>0&&r.z<32,
                                "Actual paid flight stays inside committed 48x12x32 raised floor");
                    }
                }
                for(var m:mobs)if(!m.isRemoved())bounded(m);
            });
        }
        void bounded(Entity e) {
            var o=h.absoluteVec(Vec3.ZERO);var b=e.getBoundingBox();
            check(h,b.minX>o.x&&b.maxX<o.x+48&&b.minY>o.y+3&&b.maxY<o.y+12&&b.minZ>o.z&&b.maxZ<o.z+32,
                    "Complete entity AABB inside committed raised fixture");
        }
        Husk target(double x,double z) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,4,z));mobs.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(1000);
            bounded(t);return t;
        }
        Actor actor(String id,boolean selected,boolean ads,double z,int rounds,int reserve) {
            var p=TestPlayers.hunter(h,Element.ARC,new Vec3(3,4,z),-90,0,
                    "W104_"+UUID.randomUUID().toString().substring(0,8));players.add(p);
            p.setAttached(WeaponLoadout.ENABLED,false);p.setNoGravity(true);p.setOnGround(true);
            var e=WeaponCatalog.find(id).orElseThrow();var gun=WeaponItems.create(e);
            if(selected)check(h,WeaponPerks.select(gun,TrackingProfile.ID),"Select actual exact optional socket");
            WeaponItems.save(gun,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));
            p.getInventory().setItem(0,gun);p.getInventory().setSelectedSlot(0);
            var target=target(34,z);aim(p,target);input(p,ads);
            WeaponRuntime.tickPlayer(p); // ONE initial production initialization, never a dummy shot.
            bounded(p);return new Actor(p,gun,target);
        }
        Actor intrinsic(double z) {return actor("pyroclastic_flow",false,true,z,1,2);}
        void at(int elapsed,Runnable action) {
            check(h,h.getLevel().getServer().getTickCount()==started,"Register all callbacks at fixture setup, never nested");
            h.runAfterDelay(elapsed,()->{
                check(h,h.getLevel().getServer().getTickCount()-started==elapsed,"Actual server deadline "+elapsed);
                action.run();
            });
        }
        WeaponRuntime.FlightSnapshot shot(Actor a,UUID expected) {
            var before=ammo(a.gun);long tick=now(a.p);
            check(h,WeaponRuntime.flights(a.p).isEmpty(),"No pre-existing fake or sacrificial projectile");
            check(h,WeaponRuntime.beginUse(a.p),"Real production trigger admitted");
            WeaponRuntime.releaseUse(a.p,a.gun);
            var flights=WeaponRuntime.flights(a.p);
            check(h,flights.size()==1&&ammo(a.gun).rounds()==before.rounds()-1
                    &&ammo(a.gun).reserve()==before.reserve()&&ammo(a.gun).total()==before.total()-1,
                    "Exactly one funded actual projectile, finite reserve conserved");
            var flight=flights.getFirst();
            check(h,flight.launchedAt()==tick&&Objects.equals(flight.target(),expected)
                    &&flight.tracking()==(expected!=null),"Only already-earned target captured at paid launch");
            try {flights.clear();check(h,false,"Actual flight observation list must be immutable");}
            catch(UnsupportedOperationException expectedImmutable) { /* immutable observation */ }
            return flight;
        }
        void wall(int x,int z0,int z1) {
            for(int y=4;y<=10;y++)for(int z=z0;z<=z1;z++)h.setBlock(x,y,z,Blocks.STONE);
        }
    }

    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void exactIntrinsicAndOptionalSocketsNeverBlanketEnableAllRocketsOrDefaultTraits(GameTestHelper h) {
        var f=new Fixture(h);int intrinsic=0,optional=0;
        for(var e:WeaponCatalog.all()) {
            var gun=WeaponItems.create(e);
            check(h,WeaponPerks.selected(gun,TrackingProfile.ID).isEmpty(),"No default Tracking Module on "+e.id());
            boolean fixed=e.id().equals("pyroclastic_flow");
            boolean selectable=Set.of("bad_omens","bellowing_giant").contains(e.id());
            check(h,TrackingProfile.supports(gun)==fixed,"Exact intrinsic before explicit selection "+e.id());
            check(h,WeaponPerks.select(gun,TrackingProfile.ID)==selectable,"Exact source socket eligibility "+e.id());
            check(h,TrackingProfile.supports(gun)==(fixed||selectable),"No expansion to another family/frame");
            if(fixed)intrinsic++;if(selectable)optional++;
        }
        check(h,intrinsic==1&&optional==2,"One actual precision intrinsic and two optional base sockets");
        var a=f.actor("code_duello",false,true,8,1,2);
        check(h,!WeaponTracking.status(a.p).supported(),"Ordinary rocket never gains intrinsic tracking");
        hud(h,a.p,WHITE);h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=85,environment=ENV)
    public void continuousActualAdsSamplesTwentiethTickLocksAndHudReadsNeverAcquire(GameTestHelper h) {
        var f=new Fixture(h);var a=f.intrinsic(8);
        AtomicInteger first=new AtomicInteger(-1),last=new AtomicInteger(-1),previous=new AtomicInteger(0),seen=new AtomicInteger(0);
        h.onEachTick(()->{
            var s=WeaponTracking.status(a.p);long tick=now(a.p);
            if(s.phase()==WeaponTracking.Phase.ACQUIRING||s.phase()==WeaponTracking.Phase.LOCKED) {
                if(first.get()<0) {first.set((int)tick);check(h,s.ticks()==1,"First valid real sample is one, not instant lock");}
                int expected=Math.min(20,previous.get()+1);
                check(h,s.ticks()==expected,"Exactly one sample per real server tick");previous.set(s.ticks());seen.incrementAndGet();
                check(h,WeaponAiming.progress(a.p)>=.95f,"No acquisition before fully entered actual ADS threshold");
                if(s.phase()==WeaponTracking.Phase.LOCKED&&last.get()<0)last.set((int)tick);
                int tint=s.phase()==WeaponTracking.Phase.LOCKED?WeaponReticleHud.TRACKING_LOCKED:WeaponReticleHud.TRACKING_ACQUIRING;
                for(int i=0;i<25;i++) {hud(h,a.p,tint);check(h,s.equals(WeaponTracking.status(a.p)),"Status/HUD reads cannot add acquisition samples");}
            }
            check(h,ammo(a.gun).rounds()==1&&ammo(a.gun).reserve()==2&&WeaponRuntime.flights(a.p).isEmpty(),"Acquisition and HUD do not pay, refill or emit");
        });
        f.at(75,()->{
            locked(h,a.p,a.target);check(h,first.get()>=0&&last.get()-first.get()==19&&seen.get()>=20,
                    "Exactly twentieth inclusive sample locks after nineteen actual tick intervals");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=125,environment=ENV)
    public void lostAimAndActualSameTickReleasePressRestartContinuousAcquisition(GameTestHelper h) {
        var f=new Fixture(h);var a=f.intrinsic(8);
        f.at(LOCK_AT,()->{locked(h,a.p,a.target);a.p.setYRot(a.p.getYRot()+90);idle(h,a.p,"Live off-cone aim immediately invalidates status");hud(h,a.p,WHITE);});
        f.at(52,()->{idle(h,a.p,"Lost aim erased stored acquisition at real intervening tick");aim(a.p,a.target);});
        f.at(68,()->check(h,WeaponTracking.status(a.p).phase()!=WeaponTracking.Phase.LOCKED,"Restored aim cannot reuse old lock progress"));
        f.at(82,()->{
            locked(h,a.p,a.target);long tick=now(a.p);var gun=a.p.getMainHandItem();
            input(a.p,false);idle(h,a.p,"Actual release packet invalidates before next server tick");
            input(a.p,true);check(h,now(a.p)==tick&&a.p.getMainHandItem()==gun,"Release and press occurred on exact original same tick");
            check(h,!WeaponAiming.requested(a.p),"Same-tick second click is debounced");
            idle(h,a.p,"Same-tick press cannot resurrect original lock");hud(h,a.p,WHITE);
        });
        f.at(85,()->input(a.p,true)); // A new click after the three-tick quiet gap.
        f.at(99,()->check(h,WeaponTracking.status(a.p).phase()!=WeaponTracking.Phase.LOCKED,"Fresh release/press still needs twenty actual fully-ADS samples"));
        f.at(115,()->{locked(h,a.p,a.target);h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=75,environment=ENV)
    public void nativeStowCopyActualReloadAndActualAbilityImmediatelyRevokePrelaunchLock(GameTestHelper h) {
        var f=new Fixture(h);var stow=f.intrinsic(4);var copy=f.intrinsic(12);
        var reload=f.actor("pyroclastic_flow",false,true,20,0,2);var skill=f.intrinsic(28);
        f.at(LOCK_AT,()->{
            for(var a:List.of(stow,copy,reload,skill))locked(h,a.p,a.target);
            stow.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            stow.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
            check(h,stow.p.getMainHandItem()==stow.gun,"Native hotbar round trip retained exact original stack");
            copy.p.getInventory().setItem(0,copy.gun.copy());
            check(h,copy.p.getMainHandItem()!=copy.gun,"Real copy replaces selected identity");
            check(h,WeaponRuntime.reload(reload.p),"Actual finite reserve reload starts");
            check(h,AbilityService.use(skill.p,AbilitySlot.MELEE)==AbilityService.Result.OK,"Actual skill accepted, not cosmetic suspend injection");
            for(var a:List.of(stow,copy,reload,skill))idle(h,a.p,"Real prelaunch boundary revokes earned target immediately");
            check(h,WeaponRuntime.flights(reload.p).isEmpty()&&ammo(reload.gun).rounds()==0,"Reload acceptance does not manufacture a paid rocket");
        });
        f.at(54,()->{
            for(var a:List.of(stow,copy,reload,skill))check(h,WeaponTracking.status(a.p).phase()!=WeaponTracking.Phase.LOCKED,
                    "Next tick cannot resurrect invalid prelaunch lock");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=75,environment=ENV)
    public void wallDeadAlliedSpectatorAndOwnerLevelChangesDenyCandidatesWithoutOwnerLeakage(GameTestHelper h) {
        var f=new Fixture(h);var wall=f.intrinsic(3);var dead=f.intrinsic(9);var ally=f.intrinsic(15);
        var spectator=f.intrinsic(21);var level=f.intrinsic(27);
        var scoreboard=h.getLevel().getScoreboard();String name="w104_"+UUID.randomUUID().toString().substring(0,8);
        var team=scoreboard.addPlayerTeam(name);
        TestCleanup.register(h,()->{if(scoreboard.getPlayerTeam(name)==team)scoreboard.removePlayerTeam(team);});
        var other=h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER)?Level.OVERWORLD:Level.NETHER);
        check(h,other!=null&&other!=h.getLevel(),"Actual second level exists");
        f.at(LOCK_AT,()->{
            for(var a:List.of(wall,dead,ally,spectator,level))locked(h,a.p,a.target);
            f.wall(16,1,5);idle(h,wall.p,"Opaque physical wall blocks prelaunch LOS immediately");
            locked(h,level.p,level.target); // Another owner's lock cannot be cleared by a wall in the first lane.
            dead.target.setHealth(0);idle(h,dead.p,"Dead actual candidate denied");
            scoreboard.addPlayerToTeam(ally.p.getScoreboardName(),team);scoreboard.addPlayerToTeam(ally.target.getScoreboardName(),team);
            check(h,ally.p.isAlliedTo(ally.target),"Actual hostile is now scoreboard allied");idle(h,ally.p,"Friendly target denied");
            spectator.p.setGameMode(GameType.SPECTATOR);idle(h,spectator.p,"Spectator owner denied");
            level.p.setServerLevel(other);idle(h,level.p,"Foreign-level owner cannot retain captured candidate");
        });
        f.at(54,()->{
            for(var a:List.of(wall,dead,ally,spectator,level))check(h,WeaponTracking.status(a.p).lockedTarget()==null,"No stale lock after global update");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=75,environment=ENV)
    public void actualPaidShotCapturesOnlyEarnedOriginalWhileHipAndUnsupportedShotsRemainUntracked(GameTestHelper h) {
        var f=new Fixture(h);var tracked=f.intrinsic(4);
        var hip=f.actor("pyroclastic_flow",false,false,16,1,2);
        var plain=f.actor("code_duello",false,true,28,1,2);
        f.at(LOCK_AT,()->{
            locked(h,tracked.p,tracked.target);f.shot(tracked,tracked.target.getUUID());
            var replacement=f.target(34,8);aim(tracked.p,replacement);
            var actual=WeaponRuntime.flights(tracked.p).getFirst();
            check(h,actual.target().equals(tracked.target.getUUID())&&!actual.target().equals(replacement.getUUID()),
                    "New aim/new enemy cannot rewrite paid original snapshot");
            f.shot(hip,null);f.shot(plain,null);
            check(h,ammo(tracked.gun).total()==2&&ammo(hip.gun).total()==2&&ammo(plain.gun).total()==2,
                    "Tracking changes neither finite cost nor reserve totals");
        });
        f.at(54,()->{
            var actual=WeaponRuntime.flights(tracked.p);
            check(h,!actual.isEmpty()&&actual.getFirst().target().equals(tracked.target.getUUID()),"Autonomous flight remains aimed at original despite owner aim change");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void realMovingTargetBendsPaidTrajectoryAtBoundedAngleWhileHipControlStaysStraight(GameTestHelper h) {
        var f=new Fixture(h);var tracked=f.intrinsic(8);var straight=f.actor("pyroclastic_flow",false,false,24,1,2);
        var before=new HashMap<UUID,WeaponRuntime.FlightSnapshot>();
        f.at(LOCK_AT,()->{
            locked(h,tracked.p,tracked.target);
            before.put(tracked.p.getUUID(),f.shot(tracked,tracked.target.getUUID()));
            before.put(straight.p.getUUID(),f.shot(straight,null));
            tracked.target.setPos(tracked.target.position().add(0,0,3));straight.target.setPos(straight.target.position().add(0,0,3));
        });
        for(int t=51;t<=55;t++)f.at(t,()->{
            for(var a:List.of(tracked,straight)) {
                var all=WeaponRuntime.flights(a.p);check(h,all.size()==1,"Long bounded lane retains actual sampled flight");
                var current=all.getFirst();var prior=before.put(a.p.getUUID(),current);
                check(h,Math.abs(current.velocity().length()-prior.velocity().length())<1e-8,"Real homing preserves projectile speed");
                double dot=current.velocity().normalize().dot(prior.velocity().normalize());
                double angle=Math.acos(Math.clamp(dot,-1,1));
                check(h,angle<=TrackingProfile.TURN_RADIANS+1e-7,"One real server flight step cannot exceed authored three-degree turn");
                if(a==tracked)check(h,current.tracking()&&current.target().equals(a.target.getUUID())
                        &&current.velocity().z>0&&current.position().z>a.p.getZ(),"Captured moving enemy creates actual lateral velocity AND displacement");
                // Hip spread chooses an initial axis; an unlocked rocket must retain it.
                else check(h,current.target()==null&&!current.tracking()
                        &&current.velocity().subtract(prior.velocity()).lengthSqr()<1e-14
                        &&current.position().subtract(prior.position()).subtract(prior.velocity()).lengthSqr()<1e-12,
                        "Unlocked paid control preserves its sampled hip-fire launch axis and one-tick displacement");
            }
        });
        f.at(60,()->{check(h,ammo(tracked.gun).rounds()==0&&ammo(straight.gun).rounds()==0,"No hidden second launch or refill while steering");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void postLaunchStowAndTraitClearKeepCapturedTargetThenDeadTargetPermanentlyLosesGuidance(GameTestHelper h) {
        var f=new Fixture(h);var stow=f.intrinsic(8);var edit=f.actor("bad_omens",true,true,24,1,2);
        f.at(LOCK_AT,()->{
            for(var a:List.of(stow,edit)) {locked(h,a.p,a.target);f.shot(a,a.target.getUUID());a.target.setPos(a.target.position().add(0,0,2));}
            stow.p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            check(h,stow.p.getInventory().getItem(0)==stow.gun,"Actual original stowed, not copied");
            check(h,WeaponPerks.clear(edit.gun),"Actual selected source trait cleared after paid launch");
            idle(h,stow.p,"Stow clears prelaunch state only");idle(h,edit.p,"Trait clear disables further prelaunch acquisition");
        });
        f.at(53,()->{
            for(var a:List.of(stow,edit)) {
                var shot=WeaponRuntime.flights(a.p).getFirst();
                check(h,shot.tracking()&&a.target.getUUID().equals(shot.target())&&shot.velocity().z>0,
                        "Paid snapshot continues autonomous steering after original source stow/edit");
            }
            stow.target.setHealth(0);edit.target.setHealth(0);
            f.target(34,8);f.target(34,24); // Visible replacement enemies are not substitute captured objects.
        });
        f.at(55,()->{
            for(var a:List.of(stow,edit)) {
                var shot=WeaponRuntime.flights(a.p).getFirst();
                check(h,!shot.tracking()&&a.target.getUUID().equals(shot.target()),"Dead original irreversibly loses guidance, identity retained for audit");
                a.target.setHealth(1000); // Even same object becoming live cannot reactivate a revoked flight.
            }
        });
        f.at(57,()->{
            for(var a:List.of(stow,edit))check(h,!WeaponRuntime.flights(a.p).getFirst().tracking(),"No original resurrection or different enemy retarget");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=85,environment=ENV)
    public void newlyOccludingWallStillAllowsGuidanceButActualCollisionNeverCrossesOrDamagesBehind(GameTestHelper h) {
        var f=new Fixture(h);var a=f.intrinsic(8);AtomicInteger sampled=new AtomicInteger();
        f.at(LOCK_AT,()->{locked(h,a.p,a.target);f.shot(a,a.target.getUUID());});
        f.at(51,()->f.wall(14,3,13));
        f.at(52,()->{
            var flight=WeaponRuntime.flights(a.p).getFirst();
            check(h,flight.tracking()&&a.target.getUUID().equals(flight.target()),"Midflight LOS occlusion does not silently become an invented cancellation rule");
        });
        h.onEachTick(()->{
            for(var flight:WeaponRuntime.flights(a.p)) {
                double localX=h.relativeVec(flight.position()).x;
                check(h,localX<14,"Ordinary segment collision never lets homing cross the opaque wall");sampled.incrementAndGet();
            }
        });
        f.at(75,()->{
            check(h,sampled.get()>0&&WeaponRuntime.flights(a.p).isEmpty(),"Actual obstacle impact retired paid projectile");
            check(h,a.target.isAlive()&&a.target.getHealth()==1000,"Shielded witness behind wall took zero splash damage");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=80,environment=ENV)
    public void realEmptyAndCadenceDenialsDoNotSpendTwiceAndOwnerDeathRetiresPaidFlight(GameTestHelper h) {
        var f=new Fixture(h);var a=f.intrinsic(8);var empty=f.actor("pyroclastic_flow",false,true,24,0,0);
        f.at(LOCK_AT,()->{
            locked(h,a.p,a.target);locked(h,empty.p,empty.target);f.shot(a,a.target.getUUID());
            check(h,!WeaponRuntime.beginUse(a.p),"Actual immediate repeated trigger denied by existing finite cycle");
            WeaponRuntime.releaseUse(a.p,a.gun);
            check(h,ammo(a.gun).rounds()==0&&ammo(a.gun).reserve()==2&&WeaponRuntime.flights(a.p).size()==1,
                    "Rapid trigger never pays or emits twice");
            check(h,!WeaponRuntime.beginUse(empty.p)&&ammo(empty.gun).total()==0&&WeaponRuntime.flights(empty.p).isEmpty(),
                    "Locked-but-unfunded empty trigger cannot manufacture tracking projectile");
            for(int i=0;i<50;i++)WeaponTracking.status(a.p);
            check(h,ammo(a.gun).total()==2,"Read-only locked HUD queries never replenish finite reserves");
        });
        f.at(51,()->a.p.setHealth(0));
        f.at(54,()->{
            check(h,WeaponRuntime.flights(a.p).isEmpty(),"Actual owner death stops in-flight projectile through existing lifecycle guard");
            idle(h,a.p,"Dead owner cannot retain HUD/capture lock");
            check(h,ammo(a.gun).total()==2&&ammo(empty.gun).total()==0,"Death/denial never refund already-spent ammo");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=85,environment=ENV)
    public void rotatingBoundedLosWindowEventuallyLocksVisibleThirtyThirdRankWithoutHiddenCapture(GameTestHelper h) {
        var f=new Fixture(h);var a=f.intrinsic(8);
        var hidden=new ArrayList<Husk>();hidden.add(a.target);
        // Thirty-one nonoverlapping extra mobs plus the existing actor target: exactly32 hidden.
        for(int i=0;i<31;i++)hidden.add(f.target(15+i*.9,8));
        double rayY=a.p.getEyePosition().y;
        a.target.setPos(h.absoluteVec(new Vec3(45,4,8)));
        for(var mob:hidden) {
            mob.setPos(new Vec3(mob.getX(),rayY-mob.getBbHeight()/2,mob.getZ()));f.bounded(mob);
        }
        var visible=f.target(8,8.35);
        visible.setPos(new Vec3(visible.getX(),rayY-visible.getBbHeight()/2,visible.getZ()));f.bounded(visible);
        a.p.setYRot(-90);a.p.setYHeadRot(-90);a.p.setXRot(0); // Actual horizontal ADS ray, not a candidate injection.
        f.wall(12,6,10);
        var from=a.p.getEyePosition();var look=a.p.getLookAngle();
        double visibleDot=look.dot(visible.getBoundingBox().getCenter().subtract(from).normalize());
        check(h,visibleDot>Math.cos(Math.toRadians(8)),"Visible rank33 remains strictly inside actual eight-degree acquisition cone");
        check(h,hidden.size()==32,"Exactly thirty-two better-angle hidden candidates precede visible rank33");
        for(var mob:hidden) {
            var center=mob.getBoundingBox().getCenter();
            check(h,look.dot(center.subtract(from).normalize())>visibleDot+1e-9,
                    "Each occluded mob ranks ahead of visible candidate by actual aim angle");
            var hit=h.getLevel().clip(new net.minecraft.world.level.ClipContext(from,center,
                    net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,a.p));
            check(h,hit.getType()==net.minecraft.world.phys.HitResult.Type.BLOCK,"Every better-ranked hidden candidate has a real opaque wall");
        }
        var clear=h.getLevel().clip(new net.minecraft.world.level.ClipContext(from,visible.getBoundingBox().getCenter(),
                net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,a.p));
        check(h,clear.getType()==net.minecraft.world.phys.HitResult.Type.MISS,"Visible lower-ranked candidate is actually before the wall");
        AtomicInteger visibleSamples=new AtomicInteger();
        h.onEachTick(()->{
            var status=WeaponTracking.status(a.p);
            check(h,status.candidate()==null||visible.getUUID().equals(status.candidate()),
                    "Real tick search never acquires any of the thirty-two occluded prefix entities");
            if(status.candidate()!=null)visibleSamples.incrementAndGet();
            check(h,ammo(a.gun).rounds()==1&&ammo(a.gun).reserve()==2&&WeaponRuntime.flights(a.p).isEmpty(),
                    "Rotating target search never fires a dummy projectile or changes finite ammunition");
        });
        f.at(75,()->{
            locked(h,a.p,visible);hud(h,a.p,WeaponReticleHud.TRACKING_LOCKED);
            check(h,visibleSamples.get()>=20,"Visible rank33 earned actual continuous samples instead of being starved forever");
            h.succeed();
        });
    }

}
