package kim.biryeong.destiny.test;

import com.mojang.authlib.GameProfile;
import io.netty.buffer.Unpooled;
import io.netty.channel.embedded.EmbeddedChannel;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.IncomingDamageHud;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.Connection;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.BundlePacket;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.PacketFlow;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.server.network.ServerGamePacketListenerImpl;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.BlocksAttacks;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import java.util.*;
import java.util.stream.Collectors;

/** Actual native hurtServer/Player.actuallyHurt integration, never direct damaged() grants.
 * Timings, merge radius and presentation curves are authored local HUD policy, not measured D2.
 * Projectile test exercises native arrow damage attribution, not a simulated flying-arrow collision.
 * Every callback is registered at fixture creation; no late registrations or native-client claims.
 */
public final class IncomingDamageW86GameTests {
    private static final String FLOOR="destiny-test:w78_floor", PREFIX=IncomingDamageHud.PREFIX;
    private static void check(GameTestHelper h,boolean ok,String message) {h.assertTrue(ok,Component.literal(message));}
    private static void near(GameTestHelper h,double actual,double expected,String message) {
        check(h,Math.abs(actual-expected)<.0003,message+": expected="+expected+", actual="+actual);
    }
    private static void bounded(GameTestHelper h,Entity e) {
        var o=h.absoluteVec(Vec3.ZERO);var b=e.getBoundingBox();
        check(h,b.minX>o.x&&b.maxX<o.x+48&&b.minY>o.y&&b.maxY<o.y+12&&b.minZ>o.z&&b.maxZ<o.z+32,
                "Whole W86 entity AABB remains within raised48x12x32 fixture");
    }
    private static Set<String> keys(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(PREFIX)).collect(Collectors.toSet());
    }
    private static ItemDisplayHud node(GameTestHelper h,ServerPlayer p,String suffix) {
        var hud=DisplayHud.getHud(p,PREFIX+suffix);
        check(h,hud instanceof ItemDisplayHud,"Actual incoming ItemDisplay exists: "+suffix);
        return (ItemDisplayHud)hud;
    }
    private static void absent(GameTestHelper h,ServerPlayer p,String reason) {check(h,keys(p).isEmpty(),reason+": no incoming nodes");}
    private static void model(GameTestHelper h,ItemDisplayHud hud,String sprite) {
        check(h,Identifier.fromNamespaceAndPath("destiny","gui/hud/"+sprite).equals(hud.getItem().get(DataComponents.ITEM_MODEL)),
                "Dedicated pack-backed incoming sprite "+sprite);
    }
    private static void rotation(GameTestHelper h,ServerPlayer p,int slot,float degrees) {
        var hud=node(h,p,"arc_"+slot);
        near(h,(Float)hud.getExtraData("incomingRotation"),degrees,"Quantized screen bearing");
        var expected=new Quaternionf().rotationZ((float)Math.toRadians(degrees));
        near(h,Math.abs(hud.getRightRotation().dot(expected)),1,"REAL quaternion is screen Z rotation, not the DisplayHud third-argument X axis");
        var normal=hud.getRightRotation().transform(new org.joml.Vector3f(0,0,1));
        near(h,normal.x,0,"Z rotation keeps screen normal X");near(h,normal.y,0,"Z rotation keeps screen normal Y");near(h,normal.z,1,"Z rotation keeps screen normal Z");
    }
    private static float hurt(GameTestHelper h,ServerPlayer p,DamageSource source,float amount,boolean resetIframe) {
        if(resetIframe)p.damageCooldownTime=0;
        float before=p.getHealth()+p.getAbsorptionAmount();
        p.hurtServer(p.level(),source,amount);
        return before-p.getHealth()-p.getAbsorptionAmount();
    }
    private static void hit(GameTestHelper h,ServerPlayer p,Entity attacker,float amount) {
        check(h,attacker.isAlive()&&attacker.level()==p.level()&&attacker!=p,"Positive live/local/distinct responsible attacker preflight");
        check(h,hurt(h,p,p.damageSources().mobAttack((Husk)attacker),amount,true)>0,"Actual native HP/absorption loss admitted");
    }
    private static final class Fixture {
        final GameTestHelper h;final long createdAt;
        final List<ServerPlayer> players=new ArrayList<>();final Set<ServerPlayer> dormant=Collections.newSetFromMap(new IdentityHashMap<>());
        final List<Entity> entities=new ArrayList<>();final List<EmbeddedChannel> extraChannels=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;createdAt=h.getLevel().getServer().getTickCount();
            for(int x=0;x<48;x++)for(int z=0;z<32;z++)h.setBlock(x,3,z,Blocks.STONE);
            TestCleanup.register(h, ()->{
                for(var p:players) {
                    if(CameraViews.get(p)!=null)CameraViews.stop(p);
                    p.setServerLevel(h.getLevel());p.stopUsingItem();SuperCamera.stop(p);
                    p.setCamera(p);IncomingDamageHud.cleanup(p);CombatHud.remove(p);
                    if(p.level().players().contains(p))p.level().removePlayerImmediately(p,Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
                entities.forEach(Entity::discard);extraChannels.forEach(EmbeddedChannel::finishAndReleaseAll);
            });
            h.onEachTick(()->{
                for(var p:players)if(!dormant.contains(p)) {bounded(h,p);IncomingDamageHud.update(p);}
                for(var e:entities)if(!e.isRemoved())bounded(h,e);
            });
        }
        ServerPlayer player(double x,double z,boolean guardian) {
            String name="W86_"+UUID.randomUUID().toString().substring(0,8);
            var p=guardian?TestPlayers.hunter(h,Element.ARC,new Vec3(x,4,z),0,0,name):TestPlayers.create(h,new Vec3(x,4,z),0,0,name);
            players.add(p);prepare(p);bounded(h,p);return p;
        }
        void prepare(ServerPlayer p) {
            p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);p.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
            p.setHealth(20);p.setAbsorptionAmount(0);TestPlayers.drain(p);
        }
        Husk mob(double x,double z) {
            var m=h.spawn(EntityTypes.HUSK,new Vec3(x,4,z));entities.add(m);
            m.setNoAi(true);m.setNoGravity(true);m.setPersistenceRequired();m.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(4);bounded(h,m);return m;
        }
        void at(int ticks,Runnable action) {
            check(h,h.getLevel().getServer().getTickCount()==createdAt,"Callbacks install only at fixture initialization");
            h.runAfterDelay(ticks,()->{
                check(h,h.getLevel().getServer().getTickCount()-createdAt==ticks,"Exact real server deadline "+ticks);
                for(var p:players)if(!dormant.contains(p))IncomingDamageHud.update(p);
                action.run();
            });
        }
        ServerPlayer replacement(ServerPlayer old) {
            // Independent native connection, same profile UUID: not merely two different owners.
            var server=h.getLevel().getServer();GameProfile profile=old.getGameProfile();
            var cookie=CommonListenerCookie.createInitial(profile,false);
            var p=new ServerPlayer(server,h.getLevel(),profile,cookie.clientInformation());
            var connection=new Connection(PacketFlow.SERVERBOUND);var channel=new EmbeddedChannel(connection);extraChannels.add(channel);
            TestPacketContexts.initialize(connection,server,profile);
            p.connection=new ServerGamePacketListenerImpl(server,connection,p,cookie);
            connection.setupInboundProtocol(GameProtocols.SERVERBOUND_TEMPLATE.bind(RegistryFriendlyByteBuf.decorator(server.registryAccess()),p.connection),p.connection);
            p.setPos(old.position());p.connection.handleAcceptPlayerLoad(new ServerboundPlayerLoadedPacket());p.setGameMode(GameType.SURVIVAL);
            dormant.add(old);players.add(p);prepare(p);return p;
        }
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void realNativeMobHpAndAbsorptionLossReachEmptyHandGuardianAndNonGuardianHud(GameTestHelper h) {
        var f=new Fixture(h);var hp=f.player(10,8,false);var absorbed=f.player(10,24,true);var a=f.mob(10,12);var b=f.mob(10,28);
        check(h,!Guardians.isGuardian(hp)&&Guardians.isGuardian(absorbed)&&hp.getMainHandItem().isEmpty()&&absorbed.getMainHandItem().isEmpty(),"Both real vitals audiences with no weapon requirement");
        absorbed.setAbsorptionAmount(8);float before=hp.getHealth(),shieldBefore=absorbed.getAbsorptionAmount();
        a.doHurtTarget(h.getLevel(),hp);b.doHurtTarget(h.getLevel(),absorbed);
        check(h,hp.getHealth()<before&&hp.getAbsorptionAmount()==0,"Actual native mob attack loses HP");
        check(h,absorbed.getHealth()==20&&absorbed.getAbsorptionAmount()<shieldBefore,"Actual native mob attack loses absorption only");
        near(h,before-hp.getHealth(),shieldBefore-absorbed.getAbsorptionAmount(),"Equal native exclusive total loss");
        for(var p:List.of(hp,absorbed)) {rotation(h,p,0,0);model(h,node(h,p,"arc_0"),"incoming_w86_arc_0");CombatHud.update(p);check(h,keys(p).equals(Set.of(PREFIX+"arc_0")),"Shared health HUD preserves incoming arc");}
        Guardians.data(absorbed).setGuardianClass(GuardianClass.NONE);CombatHud.update(absorbed);
        check(h,keys(absorbed).equals(Set.of(PREFIX+"arc_0")),"Non-Guardian ability cleanup preserves incoming prefix");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=24, environment = "destiny-test:w90_isolated")
    public void invulnerabilityZeroFullBlockAndIframeCannotCreateOrRefreshIncomingCue(GameTestHelper h) {
        var f=new Fixture(h);var immune=f.player(8,5,false);var zero=f.player(18,5,false);var blocked=f.player(28,5,false);var iframe=f.player(38,5,false);
        var a=f.mob(8,9);var b=f.mob(18,9);var c=f.mob(28,9);var d=f.mob(38,9);
        immune.setPermanentlyInvulnerable(true);near(h,hurt(h,immune,immune.damageSources().mobAttack(a),4,true),0,"Native invulnerability rejects loss");
        near(h,hurt(h,zero,zero.damageSources().mobAttack(b),0,true),0,"Native zero amount loses nothing");
        // Native zero-delay shield component: embedded fixtures do not execute vanilla item-use ticks.
        var shield=new ItemStack(Items.SHIELD);var base=shield.get(DataComponents.BLOCKS_ATTACKS);
        shield.set(DataComponents.BLOCKS_ATTACKS,new BlocksAttacks(0,base.disableCooldownScale(),base.damageReductions(),base.itemDamage(),base.bypassedBy(),base.blockSound(),base.disableSound()));
        blocked.setItemInHand(InteractionHand.OFF_HAND,shield);blocked.startUsingItem(InteractionHand.OFF_HAND);
        check(h,blocked.isBlocking(),"Positive actual native blocking state with source in front");
        near(h,hurt(h,blocked,blocked.damageSources().mobAttack(c),4,true),0,"Full native shield block removes no health/absorption");
        for(var p:List.of(immune,zero,blocked))absent(h,p,"No actual loss");
        hit(h,iframe,d,4);check(h,iframe.damageCooldownTime>0,"Real first hit establishes native iframe");
        f.at(5,()->{near(h,hurt(h,iframe,iframe.damageSources().mobAttack(d),4,false),0,"Equal repeat rejected by native iframe");rotation(h,iframe,0,0);});
        f.at(19,()->model(h,node(h,iframe,"arc_0"),"incoming_w86_arc_7"));
        f.at(20,()->{absent(h,iframe,"Original exact20tick expiry proves rejected repeat did not refresh");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void fourCardinalsUseRealScreenZQuaternionsAndRecomputeFromCurrentYawAndBody(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(20,16,false);
        for(var m:List.of(f.mob(20,22),f.mob(14,16),f.mob(20,10),f.mob(26,16)))hit(h,p,m,1);
        rotation(h,p,0,0);rotation(h,p,1,90);rotation(h,p,2,-180);rotation(h,p,3,-90);
        // Match the shipped displayhud_clip X mirror, not just raw quaternion metadata.
        // The top texture anchor is +Y in model space; screen Y increases downwards.
        float[][] screen={{0,-1},{1,0},{0,1},{-1,0}};
        for(int i=0;i<4;i++) {
            var anchor=node(h,p,"arc_"+i).getRightRotation().transform(new org.joml.Vector3f(0,1,0));
            near(h,-anchor.x,screen[i][0],"Actual shader-projected cardinal screen X");
            near(h,-anchor.y,screen[i][1],"Actual shader-projected cardinal screen Y");
        }
        var first=node(h,p,"arc_0");int id=first.getEntityId();
        p.setYRot(90);IncomingDamageHud.update(p);rotation(h,p,0,-90);rotation(h,p,1,0);rotation(h,p,2,90);rotation(h,p,3,-180);
        p.setYRot(0);p.setPos(h.absoluteVec(new Vec3(14,4,22)));IncomingDamageHud.update(p);rotation(h,p,0,-90);
        check(h,node(h,p,"arc_0")==first&&first.getEntityId()==id,"Body/yaw changes reuse exact HUD entity");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=12, environment = "destiny-test:w90_isolated")
    public void nativeProjectilePrefersFarResponsibleOwnerSnapshotOverNearContactAndDirectOnlyFallsBack(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(10,16,false);var fallback=f.player(34,16,false);var owner=f.mob(18,16);
        var arrow=h.spawn(EntityTypes.ARROW,new Vec3(10,5,16.5));f.entities.add(arrow);arrow.setNoGravity(true);arrow.setDeltaMovement(Vec3.ZERO);arrow.setOwner(owner);
        var source=p.damageSources().arrow(arrow,owner);
        check(h,source.getDirectEntity()==arrow&&source.getEntity()==owner&&arrow.getOwner()==owner&&arrow.distanceTo(p)<2&&owner.distanceTo(p)>7,"Actual native projectile near victim with far responsible owner");
        check(h,hurt(h,p,source,2,true)>0,"Real native projectile-source damage removes HP");rotation(h,p,0,-90);
        var direct=h.spawn(EntityTypes.ARROW,new Vec3(34,5,22));f.entities.add(direct);direct.setNoGravity(true);direct.setDeltaMovement(Vec3.ZERO);
        var directSource=fallback.damageSources().arrow(direct,null);
        check(h,directSource.getEntity()==null&&directSource.getDirectEntity()==direct,"Real native direct-only arrow source has no responsible owner");
        check(h,hurt(h,fallback,directSource,2,true)>0,"Direct-only native arrow damage is actually paid in HP");rotation(h,fallback,0,0);
        // Move both live projectile and owner elsewhere: later bearing must retain initial world origin.
        owner.setPos(h.absoluteVec(new Vec3(10,4,24)));arrow.setPos(h.absoluteVec(new Vec3(6,5,16)));
        direct.setPos(h.absoluteVec(new Vec3(40,5,16)));
        f.at(2,()->{rotation(h,p,0,-90);rotation(h,fallback,0,0);p.setYRot(90);IncomingDamageHud.update(p);rotation(h,p,0,-180);});
        f.at(3,()->{p.setYRot(0);p.setPos(h.absoluteVec(new Vec3(18,4,12)));IncomingDamageHud.update(p);rotation(h,p,0,0);h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=34, environment = "destiny-test:w90_isolated")
    public void nearbySourceRefreshRetainsNodeAndRestartsOnlyItsExactTwentyTickDeadline(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(10,16,false);var m=f.mob(10,22);hit(h,p,m,1);var arc=node(h,p,"arc_0");int id=arc.getEntityId();
        f.at(10,()->{m.setPos(h.absoluteVec(new Vec3(12,4,22)));hit(h,p,m,1);check(h,keys(p).equals(Set.of(PREFIX+"arc_0"))&&node(h,p,"arc_0")==arc,"Exact2block merge refreshes one existing node");model(h,arc,"incoming_w86_arc_0");});
        f.at(20,()->check(h,node(h,p,"arc_0").getEntityId()==id,"Merged hit survives original deadline without respawn"));
        f.at(29,()->model(h,node(h,p,"arc_0"),"incoming_w86_arc_7"));
        f.at(30,()->{absent(h,p,"Exact refreshed deadline removes final arc");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void fourArcCapacityReplacesOldestTieAndCriticalIsTheOnlyFifthNode(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(20,16,false);p.setHealth(11);
        for(var m:List.of(f.mob(20,22),f.mob(14,16),f.mob(20,10),f.mob(26,16)))hit(h,p,m,1);
        check(h,p.getHealth()==7&&keys(p).size()==4,"Four real distinct origins and noncritical7HP");
        var ids=new ArrayList<Integer>();for(int i=0;i<4;i++)ids.add(node(h,p,"arc_"+i).getEntityId());
        hit(h,p,f.mob(14,22),1);check(h,p.getHealth()==6&&keys(p).equals(Set.of(PREFIX+"arc_0",PREFIX+"arc_1",PREFIX+"arc_2",PREFIX+"arc_3",PREFIX+"critical")),"Capacity4 plus independently native-critical node, never sixth");
        rotation(h,p,0,46); // atan2(6,6)=45; Java round(45/2)=23 => +46 after shader X mirror.
        for(int i=0;i<4;i++)check(h,node(h,p,"arc_"+i).getEntityId()==ids.get(i),"Same-tick oldest tie replaces slot0 without respawn");
        var critical=node(h,p,"critical");near(h,critical.getScale().x,1920,"Critical full-screen width");near(h,critical.getScale().y,1080,"Critical full-screen height");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=18, environment = "destiny-test:w90_isolated")
    public void criticalUsesCurrentSixNotSevenHpIgnoresAbsorptionAndHealsWithoutRecentHit(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(10,16,false);p.setHealth(7);p.setAbsorptionAmount(20);CombatHud.update(p);absent(h,p,"7of20HP with no hit");
        p.setHealth(6);CombatHud.update(p);var critical=node(h,p,"critical");int id=critical.getEntityId();
        check(h,keys(p).equals(Set.of(PREFIX+"critical"))&&p.getAbsorptionAmount()==20,"6of20HP pulses independently of full native absorption and recent damage");
        var models=new HashSet<Identifier>();models.add(critical.getItem().get(DataComponents.ITEM_MODEL));
        for(int t=1;t<=12;t++)f.at(t,()->{var current=node(h,p,"critical");check(h,current==critical&&current.getEntityId()==id,"Pulse reuses cached native entity");models.add(current.getItem().get(DataComponents.ITEM_MODEL));});
        f.at(13,()->{check(h,models.size()>1,"Actual server-time pulse changes bank frame");p.setHealth(7);CombatHud.update(p);absent(h,p,"Healing above threshold removes critical immediately");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void verticalAndEnvironmentalLossInventNoHeadingAndHudObservationMutatesNoGameplayState(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(10,16,false);var above=f.mob(10,16);above.setPos(above.position().add(0,3,0));p.setHealth(7);
        hit(h,p,above,1);check(h,keys(p).equals(Set.of(PREFIX+"critical")),"Actual vertical loss gives critical but no invented directional heading");
        IncomingDamageHud.cleanup(p);p.setHealth(10);check(h,hurt(h,p,p.damageSources().fall(),1,true)>0,"Environmental native damage really loses health");absent(h,p,"No source position means no fabricated heading");
        p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.STONE,12));p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.DIAMOND,3));
        p.setHealth(6);p.setAbsorptionAmount(4);var main=p.getMainHandItem().copy();var off=p.getOffhandItem().copy();var pos=p.position();var velocity=p.getDeltaMovement();float yaw=p.getYRot(),pitch=p.getXRot();var camera=p.getCamera();
        double speed=p.getAttribute(Attributes.MOVEMENT_SPEED).getValue(),armor=p.getAttribute(Attributes.ARMOR).getValue();
        for(int i=0;i<8;i++)IncomingDamageHud.update(p);
        check(h,ItemStack.matches(main,p.getMainHandItem())&&ItemStack.matches(off,p.getOffhandItem())&&p.position().equals(pos)&&p.getDeltaMovement().equals(velocity)&&p.getCamera()==camera,"Observing incoming HUD writes no items, velocity, body or camera");
        near(h,p.getYRot(),yaw,"HUD never writes yaw");near(h,p.getXRot(),pitch,"HUD never writes pitch");near(h,p.getHealth(),6,"HUD never changes actual HP");near(h,p.getAbsorptionAmount(),4,"HUD never changes native absorption");near(h,p.getAttribute(Attributes.MOVEMENT_SPEED).getValue(),speed,"No movement attribute writes");near(h,p.getAttribute(Attributes.ARMOR).getValue(),armor,"No armor attribute writes");h.succeed();
    }

    

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void sameUuidReplacementSurvivesOldCleanupAndOwnerOnlyNativePacketCodecsRemainCached(GameTestHelper h) {
        var f=new Fixture(h);var old=f.player(10,8,false);var bystander=f.player(12,8,false);var attacker=f.mob(10,14);
        h.getLevel().addNewPlayer(bystander);check(h,h.getLevel().players().contains(bystander),"Nearby bystander participates in real native tracking");TestPlayers.drain(bystander);TestPlayers.drain(old);
        hit(h,old,attacker,1);var arc=node(h,old,"arc_0");int id=arc.getEntityId();var wire=packets(old);
        var adds=wire.stream().filter(ClientboundAddEntityPacket.class::isInstance).map(ClientboundAddEntityPacket.class::cast).filter(p->p.getId()==id).toList();
        var metadata=wire.stream().filter(ClientboundSetEntityDataPacket.class::isInstance).map(ClientboundSetEntityDataPacket.class::cast).filter(p->p.id()==id).toList();
        check(h,adds.size()==1&&!metadata.isEmpty(),"Actual owner channel carries one display spawn and native metadata");
        for(var add:adds) {
            var buf=new RegistryFriendlyByteBuf(Unpooled.buffer(),old.registryAccess());
            try {ClientboundAddEntityPacket.STREAM_CODEC.encode(buf,add);var decoded=ClientboundAddEntityPacket.STREAM_CODEC.decode(buf);check(h,decoded.getId()==id&&decoded.getType()==EntityTypes.ITEM_DISPLAY&&buf.readableBytes()==0,"Native add codec preserves private item-display identity");}finally{buf.release();}
        }
        for(var data:metadata) {
            var buf=new RegistryFriendlyByteBuf(Unpooled.buffer(),old.registryAccess());
            try {ClientboundSetEntityDataPacket.STREAM_CODEC.encode(buf,data);var decoded=ClientboundSetEntityDataPacket.STREAM_CODEC.decode(buf);check(h,decoded.id()==id&&decoded.packedItems().size()==data.packedItems().size()&&buf.readableBytes()==0,"Native metadata codec preserves all fields and owner display ID");}finally{buf.release();}
        }
        check(h,packets(bystander).stream().noneMatch(p->touches(p,id)),"Nearby tracked bystander receives NONE of owner's private display spawn/metadata/removal");
        IncomingDamageHud.update(old);IncomingDamageHud.update(old);check(h,node(h,old,"arc_0")==arc&&packets(old).stream().noneMatch(p->touches(p,id)),"Unchanged same-tick updates preserve exact node and emit no redundant HUD packets");
        var replacement=f.replacement(old);check(h,replacement!=old&&replacement.getUUID().equals(old.getUUID()),"Exact UUID but different native owner object and connection");
        hit(h,replacement,attacker,1);var fresh=node(h,replacement,"arc_0");check(h,fresh.getEntityId()!=id,"Replacement has a fresh exact-owner session");
        IncomingDamageHud.cleanup(old);IncomingDamageHud.cleanup(old);IncomingDamageHud.update(replacement);
        check(h,node(h,replacement,"arc_0")==fresh,"Repeated old-object cleanup cannot remove replacement owner's HUD");h.succeed();
    }
    private static void flatten(Packet<?> packet,List<Packet<?>> out) {
        if(packet instanceof BundlePacket<?> bundle)for(var child:bundle.subPackets())flatten(child,out);else out.add(packet);
    }
    private static List<Packet<?>> packets(ServerPlayer p) {
        var out=new ArrayList<Packet<?>>();for(var packet:TestPlayers.outbound(p))flatten(packet,out);return out;
    }
    private static boolean touches(Packet<?> packet,int id) {
        return packet instanceof ClientboundAddEntityPacket add&&add.getId()==id
                ||packet instanceof ClientboundSetEntityDataPacket data&&data.id()==id
                ||packet instanceof ClientboundRemoveEntitiesPacket remove&&remove.entityIds().contains(id);
    }
}
