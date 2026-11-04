package kim.biryeong.destiny.test;

import kim.biryeong.destiny.strike.devils.DevilsWalkerFixture;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.phys.Vec3;

public final class DevilsWalkerGameTests {
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void modelTransportMovesPausesAndClosesWithoutCombatActors(GameTestHelper h) {
        var start=h.absoluteVec(new Vec3(3.5,20,3.5));
        var hover=start.add(0,0,2);
        var route=new kim.biryeong.destiny.activity.presentation.ModelTransport.Route(start,hover,hover.add(0,2,2),0,
                new net.minecraft.world.phys.AABB(-.1,-.1,-.1,.1,.1,.1));
        var transport=kim.biryeong.destiny.activity.presentation.ModelTransport.create(h.getLevel(),kim.biryeong.destiny.campaign.presentation.DevilsTransportPaths.MODEL,route,4,8,2,4).orElseThrow();
        TestCleanup.register(h,transport::close);
        transport.delivered();
        for(int i=0;i<4;i++) transport.tick(false,java.util.List.of());
        h.assertTrue(transport.position().distanceToSqr(hover)<1e-10,"Accepted delivery still finishes approach");
        for(int i=0;i<20;i++) transport.tick(true,java.util.List.of());
        h.assertTrue(!transport.closed() && transport.position().equals(hover),"Paused encounter freezes departure");
        for(int i=0;i<6;i++) transport.tick(false,java.util.List.of());
        h.assertTrue(transport.closed(),"Delivery settles then removes the tracker at departure end");
        transport.close(); transport.tick(false,java.util.List.of());
        h.assertTrue(transport.closed(),"Repeated cleanup never resurrects the prop");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void modelTransportRechecksObstaclesBeforeMoving(GameTestHelper h) {
        var start=h.absoluteVec(new Vec3(3.5,20.5,3.5));
        var hover=start.add(0,0,2);
        var route=new kim.biryeong.destiny.activity.presentation.ModelTransport.Route(start,hover,hover.add(0,2,2),0,
                new net.minecraft.world.phys.AABB(-.1,-.1,-.1,.1,.1,.1));
        var block=net.minecraft.core.BlockPos.containing(start.add(0,0,1));
        var before=h.getLevel().getBlockState(block);
        TestCleanup.register(h,()->h.getLevel().setBlockAndUpdate(block,before));
        var transport=kim.biryeong.destiny.activity.presentation.ModelTransport.create(h.getLevel(),kim.biryeong.destiny.campaign.presentation.DevilsTransportPaths.MODEL,route,2,8,2,4).orElseThrow();
        TestCleanup.register(h,transport::close);
        h.getLevel().setBlockAndUpdate(block,net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
        transport.tick(false,java.util.List.of());
        h.assertTrue(transport.closed() && transport.position().equals(start),"New obstruction closes prop before crossing it");
        h.assertTrue(kim.biryeong.destiny.activity.presentation.ModelTransport.create(h.getLevel(),kim.biryeong.destiny.campaign.presentation.DevilsTransportPaths.MODEL,route,2,8,2,4).isEmpty(),
                "Blocked corridor is rejected at admission as well");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void flightSweepUsesActualBlockShapes(GameTestHelper h) {
        var level=h.getLevel();
        var block=h.absolutePos(new net.minecraft.core.BlockPos(6,4,4));
        var before=level.getBlockState(block);
        TestCleanup.register(h,()->level.setBlockAndUpdate(block,before));
        var hull=new net.minecraft.world.phys.AABB(-.1,-.1,-.1,.1,.1,.1);
        var a=h.absoluteVec(new Vec3(4.5,4.75,4.5));
        var b=h.absoluteVec(new Vec3(8.5,4.75,4.5));
        var sweep=kim.biryeong.destiny.activity.presentation.FlightSweep.between(hull,
                new kim.biryeong.destiny.activity.presentation.FlightSweep.Pose(a,new org.joml.Quaterniond()),
                new kim.biryeong.destiny.activity.presentation.FlightSweep.Pose(b,new org.joml.Quaterniond()));
        level.setBlockAndUpdate(block,net.minecraft.world.level.block.Blocks.STONE_SLAB.defaultBlockState());
        h.assertTrue(kim.biryeong.destiny.activity.presentation.FlightTerrain.inspect(level,sweep)
                ==kim.biryeong.destiny.activity.presentation.FlightTerrain.Result.CLEAR,"Flight above a lower slab is clear");
        h.assertTrue(kim.biryeong.destiny.activity.presentation.FlightTerrain.inspect(level,sweep.move(0,-.5,0))
                ==kim.biryeong.destiny.activity.presentation.FlightTerrain.Result.BLOCKED,"Lower flight intersects actual slab shape");
        level.setBlockAndUpdate(block,net.minecraft.world.level.block.Blocks.STONE.defaultBlockState());
        h.assertTrue(kim.biryeong.destiny.activity.presentation.FlightTerrain.inspect(level,sweep)
                ==kim.biryeong.destiny.activity.presentation.FlightTerrain.Result.BLOCKED,"Obstacle between endpoints blocks the corridor");
        level.setBlockAndUpdate(block,net.minecraft.world.level.block.Blocks.AIR.defaultBlockState());
        h.assertTrue(kim.biryeong.destiny.activity.presentation.FlightTerrain.inspect(level,sweep)
                ==kim.biryeong.destiny.activity.presentation.FlightTerrain.Result.CLEAR,"Fresh inspection sees removed obstacle");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void spawnPresentationObservesAcceptedActorsWithoutControllingCombat(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(1,2,1), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        DevilsWalkerFixture.verifySpawnPresentation(h, player);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void revivalSupportUsesSlabAndStairCollisionShapes(GameTestHelper h) {
        var player=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        TestCleanup.register(h,()->TestPlayers.remove(player));
        kim.biryeong.destiny.strike.devils.DevilsSupportFixture.verify(h,player);
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void missingVoiceShowsOwnedFallbackWithoutFakingAudioCompletion(GameTestHelper h) {
        var a=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        var b=TestPlayers.create(h,new Vec3(2,2,1),0,0);
        TestCleanup.register(h,()->{TestPlayers.remove(a);TestPlayers.remove(b);});
        kim.biryeong.destiny.strike.devils.DevilsVoiceFixture.fallback(h,a,b,TestPlayers::outbound);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void availableVoiceRetainsOriginalPacketDurationAndCompletion(GameTestHelper h) {
        var a=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        TestCleanup.register(h,()->TestPlayers.remove(a));
        kim.biryeong.destiny.strike.devils.DevilsVoiceFixture.original(h,a,TestPlayers::outbound);
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void factionRetargetStartsFreshAttackWarning(GameTestHelper h) {
        kim.biryeong.destiny.strike.devils.DevilsFactionFixture.verifyRetargetWarning(h);
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=300, environment="destiny-test:w90_isolated")
    public void sepiksWarpWaitsForWarningBeforeMoving(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(1,2,1), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        DevilsWalkerFixture.verifySepiksWarp(h, player, false);
    }
    @GameTest(structure="destiny-test:floor", maxTicks=300, environment="destiny-test:w90_isolated")
    public void sepiksWarpCancelsWhenDestinationBlockedAfterWarning(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(1,2,1), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        DevilsWalkerFixture.verifySepiksWarp(h, player, true);
    }

    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void brigArmorBreakUsesActualDamageAndKeepsWalkerGate(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(1,2,1), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        DevilsWalkerFixture.verifyBrigs(h, player);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void sepiksActualDamageRespectsBothShieldsAndCompletesOnce(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(1,2,1), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(player));
        DevilsWalkerFixture.verifySepiks(h, player);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void everyPlannedSpeciesAttachesItsBundledModel(GameTestHelper h) {
        kim.biryeong.destiny.strike.devils.DevilsFactionFixture.verifyModelCatalog(h);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void fallenAndHiveFightWithinTheirOwnEncounter(GameTestHelper h) {
        var player=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        TestCleanup.register(h,()->TestPlayers.remove(player));
        kim.biryeong.destiny.strike.devils.DevilsFactionFixture.verify(h,player);
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void combatAudioUsesOwnedListenersHostileCategoryAndSourcePosition(GameTestHelper h) {
        var near=TestPlayers.create(h,new Vec3(1,2,1),0,0,"DevilsNear");
        var far=TestPlayers.create(h,new Vec3(100,2,1),0,0,"DevilsFar");
        var other=TestPlayers.create(h,new Vec3(1,2,1),0,0,"DevilsOther");
        TestCleanup.register(h,()->{TestPlayers.remove(near);TestPlayers.remove(far);TestPlayers.remove(other);});
        TestPlayers.drain(near);TestPlayers.drain(far);TestPlayers.drain(other);
        var at=near.position().add(2,0,0);
        int sent=kim.biryeong.destiny.strike.devils.DevilsCombatSounds.play(h.getLevel(),java.util.List.of(near,far),
                kim.biryeong.destiny.strike.devils.DevilsPlan.Kind.WALKER,"fire",at);
        h.assertTrue(sent==1,net.minecraft.network.chat.Component.literal("Only in-range owned listener gets audio"));
        var packets=TestPlayers.outbound(near).stream()
                .filter(p->p instanceof net.minecraft.network.protocol.game.ClientboundSoundPacket)
                .map(p->(net.minecraft.network.protocol.game.ClientboundSoundPacket)p).toList();
        h.assertTrue(packets.size()==1,net.minecraft.network.chat.Component.literal("Actual connection queues one sound packet"));
        var sound=packets.getFirst();
        h.assertTrue(sound.getSource()==net.minecraft.sounds.SoundSource.HOSTILE
                &&sound.getSound().value().location().toString().equals("destiny_devils_sfx:spidertank_cannon_fire")
                &&Math.abs(sound.getX()-at.x)<.126&&Math.abs(sound.getY()-at.y)<.126&&Math.abs(sound.getZ()-at.z)<.126,
                net.minecraft.network.chat.Component.literal("Original event, hostile category and positional emitter"));
        h.assertTrue(TestPlayers.outbound(far).isEmpty()&&TestPlayers.outbound(other).isEmpty(),
                net.minecraft.network.chat.Component.literal("No remote or unrelated listener audio"));
        kim.biryeong.destiny.strike.devils.DevilsCombatSounds.stop(near);
        var stops=TestPlayers.outbound(near);
        h.assertTrue(!stops.isEmpty()&&stops.stream().allMatch(p->p instanceof net.minecraft.network.protocol.game.ClientboundStopSoundPacket),
                net.minecraft.network.chat.Component.literal("Cleanup emits only owned sound stop packets"));
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void multipartDamageAndDeathUseTheRealBoss(GameTestHelper h) {
        var player=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        TestCleanup.register(h,()->TestPlayers.remove(player));
        DevilsWalkerFixture.verify(h,player);
        h.succeed();
    }
    /** Plan §6 acceptance: one centred Special shot at normal range kills an ordinary Dreg through the real fire path. */
    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void specialShotgunCentreHitKillsOrdinaryDreg(GameTestHelper h) {
        var player=TestPlayers.create(h,new Vec3(2.5,2,1.5),0,0,"DevilsSpecial");
        TestCleanup.register(h,()->{kim.biryeong.destiny.weapon.WeaponRuntime.cleanup(player);TestPlayers.remove(player);});
        var dreg=kim.biryeong.destiny.strike.devils.DevilsFactionFixture.liveActor(h,player,
                kim.biryeong.destiny.strike.devils.DevilsPlan.Kind.DREG,new Vec3(2.5,2,6.5));
        player.setAttached(kim.biryeong.destiny.weapon.WeaponLoadout.ENABLED,false);
        var entry=kim.biryeong.destiny.weapon.WeaponCatalog.find(kim.biryeong.destiny.campaign.RisingLoadout.SHOTGUN).orElseThrow();
        var gun=kim.biryeong.destiny.weapon.WeaponItems.create(entry);
        var profile=kim.biryeong.destiny.weapon.WeaponProfile.forEntry(entry);
        kim.biryeong.destiny.weapon.WeaponItems.save(gun,new kim.biryeong.destiny.weapon.WeaponMagazine(profile,profile.magazine(),0));
        player.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gun);
        float before=dreg.getHealth();
        h.runAfterDelay(6,()->{
            player.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES,dreg.getBoundingBox().getCenter());
            h.assertTrue(kim.biryeong.destiny.weapon.WeaponRuntime.beginUse(player),"Production trigger admitted");
            kim.biryeong.destiny.weapon.WeaponRuntime.releaseUse(player,gun);
            h.runAfterDelay(2,()->{
                h.assertTrue(dreg.isDeadOrDying(),"Centred Special shot kills a planned 20 HP Dreg; health "+before+" -> "+dreg.getHealth());
                h.succeed();
            });
        });
    }
    /** Plan §6 acceptance: a direct-hit Super (Solar Golden Gun) shot kills an ordinary Dreg. */
    @GameTest(structure="destiny-test:floor", maxTicks=1200, environment="destiny-test:w90_isolated")
    public void directSuperShotKillsOrdinaryDreg(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> h.assertTrue(
                kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(),"Hunter limb loaded"))
                .thenExecute(() -> {
                    var p=TestPlayers.hunter(h,kim.biryeong.destiny.guardian.Element.SOLAR,new Vec3(2.5,2,1.5),0,0,"DevilsSuper");
                    TestCleanup.register(h,()->{kim.biryeong.destiny.ability.AbilityService.endSuper(p);TestPlayers.remove(p);});
                    var dreg=kim.biryeong.destiny.strike.devils.DevilsFactionFixture.liveActor(h,p,
                            kim.biryeong.destiny.strike.devils.DevilsPlan.Kind.DREG,new Vec3(2.5,2,8.5));
                    kim.biryeong.destiny.guardian.Guardians.data(p).setSuperEnergy(1);
                    h.assertTrue(kim.biryeong.destiny.ability.AbilityService.use(p,kim.biryeong.destiny.guardian.AbilitySlot.SUPER)
                            ==kim.biryeong.destiny.ability.AbilityService.Result.OK,"Activate Golden Gun");
                    superStep(h,p,dreg,1);
                });
    }
    private static void superStep(GameTestHelper h, net.minecraft.server.level.ServerPlayer p,
                                  kim.biryeong.destiny.strike.devils.DevilsMob dreg, int tick) {
        h.runAfterDelay(1,()->{
            kim.biryeong.destiny.ability.AbilityService.tickPlayer(p);
            if(tick==12) {
                p.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES,dreg.getBoundingBox().getCenter());
                h.assertTrue(kim.biryeong.destiny.ability.AbilityService.perform(p,kim.biryeong.destiny.input.GuardianAction.PRIMARY),"Fire via primary route");
            }
            if(dreg.isDeadOrDying()) { h.succeed(); return; }
            if(tick>=40) { h.fail("Golden Gun shot left Dreg at "+dreg.getHealth()); return; }
            superStep(h,p,dreg,tick+1);
        });
    }
}
