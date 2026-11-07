package kim.biryeong.destiny.test;

import kim.biryeong.destiny.campaign.RisingServices;
import kim.biryeong.destiny.campaign.fallen.RisingFallen;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.sound.EnemyHeadburstSounds;
import kim.biryeong.destiny.strike.devils.*;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;
import java.lang.reflect.Method;
import java.util.List;

/** Real damage transactions/queued sound packets. Does not certify native input or speaker mixing. */
public final class EnemyHeadburstW343GameTests {
    private ServerPlayer player(GameTestHelper h, Vec3 at, String name) {
        var p = TestPlayers.create(h, at, 0, 0, name);
        h.getLevel().addNewPlayer(p); // Positional packets use real level membership, not the fixture's participant list.
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            h.getLevel().removePlayerImmediately(p,net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        }); return p;
    }
    private List<ClientboundSoundPacket> sounds(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(v -> v instanceof ClientboundSoundPacket)
                .map(v -> (ClientboundSoundPacket)v)
                .filter(v -> v.getSound().value().location().getNamespace().equals("destiny_headburst")).toList();
    }
    /** Exercise the existing private weapon transaction without inventing a production test entry point. */
    private float transaction(ServerPlayer p, LivingEntity target, float damage, boolean precision, Vec3 point) {
        try {
            Method apply = WeaponRuntime.class.getDeclaredMethod("apply", ServerPlayer.class, LivingEntity.class,
                    float.class, boolean.class, Vec3.class, AmmoGeneration.class);
            apply.setAccessible(true);
            return (float)apply.invoke(null, p, target, damage, precision, point, new AmmoGeneration(AmmoGeneration.Kind.PRIMARY,0));
        } catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
    }
    private Vec3 head(LivingEntity e) { return e.position().add(0,e.getBbHeight()*.875,0); }
    private void checkCue(GameTestHelper h, ServerPlayer p, String group, Vec3 point) {
        var packets = sounds(p);
        h.assertTrue(packets.size()==1,"Exactly one precision final-blow cue: "+group);
        var cue=packets.getFirst();
        h.assertTrue(cue.getSound().value().location().getPath().equals("headburst."+group),"Correct family cue");
        h.assertTrue(Math.abs(cue.getVolume()-.35f)<1e-6&&cue.getPitch()==1,"Quieter gain, original playback speed");
        h.assertTrue(Math.abs(cue.getX()-point.x)<.126&&Math.abs(cue.getY()-point.y)<.126&&Math.abs(cue.getZ()-point.z)<.126,"At the actual precision contact");
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void realAutoTriggerEmitsOnlyAfterLethalHeadshot(GameTestHelper h) {
        var p=player(h,new Vec3(2.5,2,1.5),"HeadburstAuto");
        var far=player(h,new Vec3(100,2,1.5),"HeadburstFar");
        var mob=DevilsFactionFixture.liveActor(h,p,DevilsPlan.Kind.DREG,new Vec3(2.5,2,6.5));
        p.setNoGravity(true);mob.setNoGravity(true);
        p.setAttached(WeaponLoadout.ENABLED,false);
        var entry=WeaponCatalog.find("steelfeather_repeater").orElseThrow();
        var gun=WeaponItems.create(entry);var profile=WeaponProfile.forEntry(entry);
        WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),0));
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gun);
        h.runAfterDelay(6,()->{
            TestPlayers.drain(p);TestPlayers.drain(far);
            p.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES,head(mob));
            h.assertTrue(WeaponRuntime.beginUse(p),"First production trigger accepted");WeaponRuntime.releaseUse(p,gun);
            h.runAfterDelay(4,()->{
                h.assertTrue(mob.isAlive()&&mob.getHealth()<11,"First headshot damages without killing");
                h.assertTrue(sounds(p).isEmpty(),"Nonlethal precision hit is silent");
                p.lookAt(net.minecraft.commands.arguments.EntityAnchorArgument.Anchor.EYES,head(mob));
                h.assertTrue(WeaponRuntime.beginUse(p),"Second production trigger accepted");WeaponRuntime.releaseUse(p,gun);
                h.runAfterDelay(2,()->{
                    h.assertTrue(mob.isDeadOrDying(),"Second auto headshot kills");
                    var cues=sounds(p);h.assertTrue(cues.size()==1&&cues.getFirst().getSound().value().location().getPath().equals("headburst.fallen_dreg"),"Exactly one real trigger death cue");
                    h.assertTrue(sounds(far).isEmpty(),"No distant listener sound");
                    transaction(p,mob,100,true,head(mob));
                    h.assertTrue(sounds(p).isEmpty(),"A dead target cannot repeat the cue");h.succeed();
                });
            });
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void strikeSpeciesRouteFromTheActualWeaponTransaction(GameTestHelper h) {
        var p=player(h,new Vec3(2,2,1),"HeadburstStrike");
        var kinds=List.of(DevilsPlan.Kind.DREG,DevilsPlan.Kind.VANDAL,DevilsPlan.Kind.CAPTAIN);
        var groups=List.of("fallen_dreg","fallen_vandal","fallen_captain");
        for(int i=0;i<kinds.size();i++) {
            var mob=DevilsFactionFixture.liveActor(h,p,kinds.get(i),new Vec3(3,2,5));
            mob.setAbsorptionAmount(0);var point=head(mob);TestPlayers.drain(p);
            h.assertTrue(transaction(p,mob,1000,true,point)>0&&mob.isDeadOrDying(),"Accepted precision final blow");
            checkCue(h,p,groups.get(i),point);
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void campaignSpeciesUseTheSameSharedRoutes(GameTestHelper h) {
        var p=player(h,new Vec3(2,2,1),"HeadburstCampaign");
        var kinds=List.of(RisingServices.FallenKind.DREG,RisingServices.FallenKind.VANDAL,RisingServices.FallenKind.CAPTAIN);
        var groups=List.of("fallen_dreg","fallen_vandal","fallen_captain");
        for(int i=0;i<kinds.size();i++) {
            var mob=RisingFallen.instance().spawn(h.getLevel(),kinds.get(i),h.absoluteVec(new Vec3(3,2,5)),0,RisingServices.Difficulty.FIRST_MISSION,null);
            TestCleanup.register(h,mob::discard);mob.setAbsorptionAmount(0);var point=head(mob);TestPlayers.drain(p);
            h.assertTrue(transaction(p,mob,1000,true,point)>0,"Actual campaign damage");checkCue(h,p,groups.get(i),point);
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void bodyAbilityShieldAndUnmappedTargetsNeverBorrowAHeadburst(GameTestHelper h) {
        var p=player(h,new Vec3(2,2,1),"HeadburstNegative");
        var body=DevilsFactionFixture.liveActor(h,p,DevilsPlan.Kind.DREG,new Vec3(3,2,5));TestPlayers.drain(p);
        transaction(p,body,1000,false,body.position());h.assertTrue(sounds(p).isEmpty(),"Body final blow is silent");
        var ability=DevilsFactionFixture.liveActor(h,p,DevilsPlan.Kind.DREG,new Vec3(4,2,5));TestPlayers.drain(p);
        Combat.damage(p,ability,1000,Element.ARC);h.assertTrue(sounds(p).isEmpty(),"Ability kill is not a weapon precision kill");
        var shield=DevilsFactionFixture.liveActor(h,p,DevilsPlan.Kind.CAPTAIN,new Vec3(5,2,5));TestPlayers.drain(p);
        boolean critical=WeaponPrecision.critical(shield,head(shield).add(0,0,-8),head(shield),1.5);
        h.assertTrue(!critical,"Combatant shield prevents precision classification");
        transaction(p,shield,1000,critical,head(shield));h.assertTrue(sounds(p).isEmpty(),"Shielded body classification cannot play headburst");
        var unrelated=h.spawn(net.minecraft.world.entity.EntityTypes.ZOMBIE,new net.minecraft.core.BlockPos(3,2,3));TestPlayers.drain(p);
        transaction(p,unrelated,1000,true,head(unrelated));h.assertTrue(sounds(p).isEmpty(),"Unmapped species gets no substituted Fallen/Cabal cue");
        h.assertTrue(EnemyHeadburstSounds.family(p)==null,"Players are never a PvE species");h.succeed();
    }
}
