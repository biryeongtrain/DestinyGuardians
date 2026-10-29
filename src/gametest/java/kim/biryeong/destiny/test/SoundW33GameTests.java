package kim.biryeong.destiny.test;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.hunter.HunterMelee;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.sound.SoundCommands;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.phys.Vec3;

import java.util.List;

public final class SoundW33GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static List<ClientboundSoundPacket> sounds(ServerPlayer player) {
        return TestPlayers.outbound(player).stream().filter(ClientboundSoundPacket.class::isInstance)
                .map(ClientboundSoundPacket.class::cast).filter(p -> p.getSound().value().location().getNamespace().equals("destiny")).toList();
    }
    private static boolean has(List<ClientboundSoundPacket> packets, String key) {
        return packets.stream().anyMatch(p -> p.getSound().value().location().getPath().equals(key));
    }
    private static long countAt(List<ClientboundSoundPacket> packets, ClientboundSoundPacket expected) {
        // Compare the wire-quantized origin, not a radius: adjacent parallel tests are audible too.
        return packets.stream().filter(p -> p.getSound().value().location().equals(expected.getSound().value().location())
                && p.getX() == expected.getX() && p.getY() == expected.getY() && p.getZ() == expected.getZ()).count();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void soundCommandsStayOperatorOnlyAfterMergingIntoPublicRoot(GameTestHelper h) throws CommandSyntaxException {
        var player = TestPlayers.create(h, new Vec3(2,1,2), 0, 0);
        try {
            var dispatcher = new CommandDispatcher<CommandSourceStack>();
            // Reproduce the production merge: a public root exists before sound registration.
            dispatcher.register(Commands.literal("destiny")
                    .then(Commands.literal("public").executes(c -> 1)));
            SoundCommands.register(dispatcher);
            var nonOp = player.createCommandSourceStack();
            var op = h.getLevel().getServer().createCommandSourceStack().withEntity(player);
            check(h, dispatcher.execute("destiny public", nonOp) == 1, "Existing public command remains accessible");
            TestPlayers.drain(player);
            for (String command : List.of("destiny sound list", "destiny sound play ui.super_ready",
                    "destiny sound play ui.super_ready @s")) {
                boolean denied = false;
                try { dispatcher.execute(command, nonOp); }
                catch (CommandSyntaxException expected) { denied = true; }
                check(h, denied, "Non-OP denied after root merge: " + command);
            }
            check(h, sounds(player).isEmpty(), "Denied commands dispatch no sound packets");
            check(h, dispatcher.execute("destiny sound list", op) == DestinySounds.events().size(), "OP can list sounds");
            check(h, dispatcher.execute("destiny sound play ui.super_ready", op) == 1, "OP can audition personally");
            check(h, dispatcher.execute("destiny sound play ui.super_ready @s", op) == 1, "OP can use the target-player branch");
            var packets = sounds(player);
            check(h, packets.size() == 2 && packets.stream().allMatch(p -> p.getSound().value().location().getPath().equals("ui.super_ready")),
                    "Accepted OP commands dispatch exactly two real sound packets");
            h.succeed();
        } finally { TestPlayers.remove(player); }
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void arcMeleeImpactPlaysOnceForMultipleContactTargets(GameTestHelper h) {
        arcMeleeImpact(h, true);
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void arcMeleeMissHasCastButNoImpactSound(GameTestHelper h) {
        arcMeleeImpact(h, false);
    }
    private static void arcMeleeImpact(GameTestHelper h, boolean withTargets) {
        var owner = TestPlayers.hunter(h, Element.ARC, new Vec3(2.5,1,6.5), -90, 0);
        var listener = TestPlayers.create(h, new Vec3(2.5,1,4.5), 0, 0);
        // Keep the fake caster stationary, as in the ordinary contact timing tests.
        h.getLevel().addNewPlayer(listener);
        TestCleanup.register(h, () -> {
            h.getLevel().removePlayerImmediately(listener, Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(listener);
            TestPlayers.remove(owner);
        });
        var targets = new java.util.ArrayList<net.minecraft.world.entity.LivingEntity>();
        if (withTargets) {
            for (double z : new double[]{6, 7}) {
                var target = h.spawn(EntityTypes.HUSK, new Vec3(4.5,1,z));
                target.setNoAi(true);
                targets.add(target);
                TestCleanup.register(h, target::discard);
            }
        }
        var health = targets.stream().map(net.minecraft.world.entity.LivingEntity::getHealth).toList();
        // The unregistered caster stays fixed; derive both expected origins before activation.
        var contact = owner.position().add(0, 1, 0).add(Motion.horizontalLook(owner).scale(1.2));
        var expectedCast = DestinySounds.packet("hunter.arc.melee.cast", owner.position(), SoundSource.PLAYERS, 1f, 0L);
        var expectedImpact = DestinySounds.packet("hunter.arc.melee.impact", contact, SoundSource.PLAYERS, .8f, 0L);
        TestPlayers.drain(listener);
        var melee = new HunterMelee(DestinyGuardians.id("w33_test_arc_melee"), "W33 Arc melee", Element.ARC, 30);
        check(h, melee.activate(owner), "Arc melee accepted");
        check(h, sounds(listener).isEmpty(), "No sound before the contact windup");
        h.runAfterDelay(2, () -> check(h, countAt(sounds(listener), expectedImpact) == 0, "No own impact at the lunge"));
        h.runAfterDelay(8, () -> {
            var packets = sounds(listener);
            check(h, countAt(packets, expectedCast) == 1, "Own contact callback ran exactly once even when the melee missed");
            long impacts = countAt(packets, expectedImpact);
            check(h, impacts == (withTargets ? 1 : 0), "One impact per contact, none on a miss; got " + impacts);
            for (int i = 0; i < targets.size(); i++)
                check(h, targets.get(i).getHealth() < health.get(i), "Each nearby target actually received contact damage");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void allCustomSoundsRoundTripAsInlineVanillaPackets(GameTestHelper h) {
        for (String key : DestinySounds.events()) {
            var packet = DestinySounds.packet(key, new Vec3(10, 65, -2), SoundSource.PLAYERS, .8f, 123L);
            check(h,packet.getSound().kind()==Holder.Kind.DIRECT,"No unknown custom registry reference: " + key);
            var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(),h.getLevel().registryAccess());
            try {
                ClientboundSoundPacket.STREAM_CODEC.encode(buffer,packet);
                var decoded = ClientboundSoundPacket.STREAM_CODEC.decode(buffer);
                check(h,decoded.getSound().kind()==Holder.Kind.DIRECT,"Wire remains inline");
                check(h,decoded.getSound().value().location().equals(packet.getSound().value().location()),"Event preserved");
                check(h,decoded.getVolume()==.8f&&decoded.getPitch()==1f&&decoded.getSeed()==123L,"Volume/pitch/seed preserved");
            } finally {buffer.release();}
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void readyEdgeQueuesOnlyOneOwnerPacketAndNeverOnJoinOrFailedActivation(GameTestHelper h) {
        var owner=TestPlayers.hunter(h,Element.ARC,new Vec3(2,1,2),0,0);
        var observer=TestPlayers.create(h,new Vec3(3,1,2),0,0);
        try {
            Guardians.data(owner).setSuperEnergy(1f);CombatHud.update(owner);
            check(h,sounds(owner).isEmpty(),"Full on joining is not a ready sound");
            Guardians.data(owner).setSuperEnergy(.5f);CombatHud.update(owner);sounds(owner);
            Guardians.data(owner).setSuperEnergy(1f);CombatHud.update(owner);
            for(int i=0;i<32;i++)CombatHud.update(owner);
            var packets=sounds(owner);
            check(h,packets.size()==1&&has(packets,"ui.super_ready"),"Ready transition queues exactly one real packet");
            check(h,sounds(observer).isEmpty(),"No ready packet on another connection");
            Guardians.data(owner).setSuperEnergy(0);
            check(h,AbilityService.use(owner,AbilitySlot.SUPER)==AbilityService.Result.NOT_READY,"Reject uncharged cast");
            check(h,sounds(owner).isEmpty(),"Rejected super does not start sound");
            h.succeed();
        } finally {TestPlayers.remove(owner);TestPlayers.remove(observer);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void positionalDispatchReachesOnlyNearbyListenersAndUnknownKeysDoNotSend(GameTestHelper h) {
        var near=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        var far=TestPlayers.create(h,new Vec3(60,1,2),0,0);
        var level=h.getLevel();
        level.addNewPlayer(near);level.addNewPlayer(far);
        try {
            TestPlayers.drain(near);TestPlayers.drain(far);
            check(h,DestinySounds.at(level,near.position(),"weapon.auto_rifle.fire",.8f),"Mapped cue accepted");
            check(h,has(sounds(near),"weapon.auto_rifle.fire"),"Nearby connection receives real packet");
            check(h,sounds(far).isEmpty(),"Distant connection receives none");
            check(h,!DestinySounds.at(level,near.position(),"invalid.unmapped",.8f),"Missing mapping explicit");
            check(h,sounds(near).isEmpty(),"Unknown key sends no invalid custom sound");
            check(h,!DestinySounds.canHear(near,level.getServer().getLevel(net.minecraft.world.level.Level.NETHER),near.position()),"No cross-dimension audience");
            h.succeed();
        } finally {
            level.removePlayerImmediately(near,Entity.RemovalReason.DISCARDED);
            level.removePlayerImmediately(far,Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(near);TestPlayers.remove(far);
        }
    }
    @GameTest(structure="destiny-test:floor",maxTicks=30, environment = "destiny-test:w90_isolated")
    public void acceptedSuperStartsExactlyOnceForEachElement(GameTestHelper h) {
        for(Element element:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
            var owner=TestPlayers.hunter(h,element,new Vec3(2,1,2),0,0);
            h.getLevel().addNewPlayer(owner);
            try {
                Guardians.data(owner).setSuperEnergy(1f);TestPlayers.drain(owner);
                check(h,AbilityService.use(owner,AbilitySlot.SUPER)==AbilityService.Result.OK,"Accepted " + element);
                var packets=sounds(owner);
                check(h,packets.size()==1&&has(packets,"hunter."+element.getSerializedName()+".super.start"),"Exactly one start at accepted activation");
                check(h,AbilityService.use(owner,AbilitySlot.SUPER)==AbilityService.Result.BUSY,"Duplicate cast rejected");
                check(h,sounds(owner).isEmpty(),"No duplicate start on busy");
                AbilityService.endSuper(owner);
                packets=sounds(owner);
                check(h,packets.size()==(element==Element.VOID?0:1),
                        "Void has no split end cue; other supers retain bounded end cue");
                AbilityService.endSuper(owner);
                check(h,sounds(owner).isEmpty(),"Repeated cleanup is silent");
            } finally {
                h.getLevel().removePlayerImmediately(owner,Entity.RemovalReason.DISCARDED);
                TestPlayers.remove(owner);
            }
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void voidContinuousCastEmitsOnlyOneSoundAcrossDrawReleaseImpactAndEnd(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h,
                kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(),
                "Void limb loaded")).thenExecute(() -> {
            var owner=TestPlayers.hunter(h,Element.VOID,new Vec3(2.5,1,6.5),-90,0);
            h.getLevel().addNewPlayer(owner);
            var target=h.spawn(EntityTypes.HUSK,new Vec3(9.5,1,6.5));
            target.setNoAi(true);
            target.getAttribute(net.minecraft.world.entity.ai.attributes.Attributes.MAX_HEALTH).setBaseValue(1000);
            target.setHealth(1000);
            TestCleanup.register(h, () -> {
                target.discard();
                h.getLevel().removePlayerImmediately(owner,Entity.RemovalReason.DISCARDED);
                TestPlayers.remove(owner);
            });
            TestPlayers.drain(owner);Guardians.data(owner).setSuperEnergy(1);
            var packets=new java.util.ArrayList<ClientboundSoundPacket>();
            check(h,AbilityService.use(owner,AbilitySlot.SUPER)==AbilityService.Result.OK,"Continuous cast starts");
            packets.addAll(sounds(owner));
            check(h,packets.size()==1&&has(packets,"hunter.void.super.start"),"Single continuous cue begins at activation");
            h.onEachTick(() -> {
                if(AbilityService.inSuper(owner)) AbilityService.perform(owner,kim.biryeong.destiny.input.GuardianAction.PRIMARY);
                AbilityService.tickPlayer(owner);
                packets.addAll(sounds(owner));
            });
            h.runAfterDelay(25,() -> {
                check(h,target.getHealth()<1000&&kim.biryeong.destiny.combat.Statuses.has(target,kim.biryeong.destiny.combat.Keyword.WEAKENED),
                        "Automatic arrow actually hit and activated tether");
                check(h,!AbilityService.inSuper(owner),"Release completed gameplay session");
                // Adjacent parallel fixtures can be audible: filter the full Void super namespace.
                var own=packets.stream().filter(p -> p.getSound().value().location().getPath().startsWith("hunter.void.super.")).toList();
                check(h,own.size()==1&&has(own,"hunter.void.super.start"),
                        "No additional draw/fire/impact/end packets after the continuous activation cue");
                h.succeed();
            });
        });
    }

}
