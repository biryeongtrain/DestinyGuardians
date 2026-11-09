package kim.biryeong.destiny.test;

import kim.biryeong.destiny.loot.LootChest;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

/** Genuine chest lifecycle + owner connection packets; not native mouse or speaker acceptance. */
public final class RewardChestSoundGameTests {
    private static void check(GameTestHelper h, boolean value, String why) { h.assertTrue(value, Component.literal(why)); }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0, name);
        TestCleanup.register(h, () -> TestPlayers.remove(p)); return p;
    }
    private static LootChest chest(GameTestHelper h, ServerPlayer p) {
        try {
            var ctor = LootChest.class.getDeclaredConstructor(ServerPlayer.class, Vec3.class, float.class, String.class, long.class, String.class);
            ctor.setAccessible(true);
            var chest = ctor.newInstance(p, p.position().add(0, 0, 3), 0f, "strike_chest", 0L, "보상 상자 QA");
            TestCleanup.register(h, () -> call(chest, "close", new Class<?>[]{boolean.class}, false));
            return chest;
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static void call(LootChest chest, String method, Class<?>[] types, Object... args) {
        try { var m = LootChest.class.getDeclaredMethod(method, types); m.setAccessible(true); m.invoke(chest, args); }
        catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static void call(LootChest chest, String method) { call(chest, method, new Class<?>[]{}); }
    private static java.util.List<ClientboundSoundPacket> sounds(ServerPlayer p) {
        return TestPlayers.outbound(p).stream().filter(ClientboundSoundPacket.class::isInstance).map(ClientboundSoundPacket.class::cast).toList();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void openingUsesSuppliedCueOnceAndNeverOnRejectedOpenOrCleanup(GameTestHelper h) {
        var p = player(h, "ChestAudio"); var observer = player(h, "ChestListener");
        var original = p.position(); var chest = chest(h, p);
        TestPlayers.drain(p); TestPlayers.drain(observer);
        call(chest, "open"); check(h, sounds(p).isEmpty(), "Arriving chest cannot open or sound yet");
        for (int i = 0; i < 10; i++) call(chest, "tick");
        TestPlayers.drain(p); p.setPos(original.add(0, 0, -10));
        call(chest, "open"); check(h, sounds(p).isEmpty(), "Out-of-range action stays silent");
        p.setPos(original); call(chest, "open");
        var cues = sounds(p); check(h, cues.size() == 1, "One supplied opening cue replaces vanilla layers");
        var cue = cues.getFirst();
        check(h, cue.getSound().value().location().toString().equals("destiny:loot.chest.open")
                && cue.getSource() == SoundSource.PLAYERS && cue.getPitch() == 1f && cue.getVolume() == 1f,
                "Exact recording, owner category and original pitch/volume");
        call(chest, "open");
        for (int i = 0; i < 4; i++) call(chest, "tick");
        check(h, sounds(p).isEmpty(), "Repeated open and burst never duplicate or overlay the opening cue");
        check(h, sounds(observer).isEmpty(), "Other player's connection receives no chest sound");
        call(chest, "close", new Class<?>[]{boolean.class}, false);
        check(h, sounds(p).isEmpty(), "Cleanup does not play opening audio");
        var unopened = chest(h, p); TestPlayers.drain(p);
        call(unopened, "close", new Class<?>[]{boolean.class}, false);
        check(h, sounds(p).isEmpty(), "Closing unopened presentation never plays opening audio");
        h.succeed();
    }
}
