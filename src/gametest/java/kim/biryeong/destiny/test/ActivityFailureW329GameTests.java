package kim.biryeong.destiny.test;

import kim.biryeong.destiny.activity.presentation.ActivityFailurePresentation;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.network.protocol.game.ClientboundStopSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;

public final class ActivityFailureW329GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static boolean hud(ServerPlayer player, UUID activity, String key) {
        return DisplayHud.getHud(player, "destiny:activity_failure/" + activity + "/" + key) != null;
    }
    private static List<ClientboundSoundPacket> sounds(ServerPlayer player) {
        return TestPlayers.outbound(player).stream().filter(ClientboundSoundPacket.class::isInstance).map(ClientboundSoundPacket.class::cast).toList();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=20, environment="destiny-test:w90_isolated")
    public void restrictionEntryDeduplicatesAndPhaseExitRemovesOwnedHudAndAudio(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        var outsider = TestPlayers.create(h, new Vec3(3.5, 1, 2.5), 0, 0);
        UUID id = UUID.randomUUID(); var presentation = new ActivityFailurePresentation(id);
        TestCleanup.register(h, () -> { presentation.close(); TestPlayers.remove(player); TestPlayers.remove(outsider); });
        TestPlayers.drain(player); TestPlayers.drain(outsider);
        presentation.scope(1, "RF", true);
        presentation.render(List.of(player), p -> true, 0, -1);
        check(h, sounds(player).isEmpty(), "Hidden cinematic cannot consume the entry cue");
        presentation.render(List.of(player), p -> false, 1, -1);
        var sounds = sounds(player);
        check(h, sounds.size() == 1 && sounds.getFirst().getSource() == SoundSource.PLAYERS
                && sounds.getFirst().getSound().value().location().toString().startsWith("destiny_activity_failure:restricted_entry_"),
                "One direct dedicated replaceable entry event on PLAYERS");
        for (int n = 2; n <= 120; n++) presentation.render(List.of(player), p -> false, n, -1);
        check(h, sounds(player).isEmpty(), "Stable restriction cannot replay its cue every tick");
        check(h, hud(player, id, "restricted") && !hud(player, id, "entry"), "Sustained restriction marker outlives entry banner");
        check(h, !hud(outsider, id, "restricted") && sounds(outsider).isEmpty(), "Outside player gets no private HUD/audio");
        presentation.scope(1, "RF", false);
        check(h, !hud(player, id, "restricted"), "Cleared phase removes marker before zone transition");
        var stops = TestPlayers.outbound(player).stream().filter(ClientboundStopSoundPacket.class::isInstance)
                .map(ClientboundStopSoundPacket.class::cast).toList();
        check(h, stops.size() == 2 && stops.stream().allMatch(p -> p.getSource() == SoundSource.PLAYERS
                && p.getName() != null && p.getName().getNamespace().equals("destiny_activity_failure")),
                "Only dedicated owned events stop; no category-wide stops");
        presentation.scope(2, "RF", true); presentation.render(List.of(player), p -> false, 121, -1);
        check(h, sounds(player).size() == 1, "New encounter generation receives one fresh entry cue");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=80, environment="destiny-test:w90_isolated")
    public void wipeHudHandoffKeepsDownOwnershipAndCannotReviveOrEraseAnotherSession(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL); h.getLevel().addNewPlayer(player);
        AtomicInteger revived = new AtomicInteger();
        var owner = new GuardianDown.Options(false, 600, true, false, "W329 제한 구역", p -> revived.incrementAndGet(), 60, true, true);
        var foreign = new GuardianDown.Options(false, 600, true, false, "다른 활동", null, 60, true, true);
        UUID id = UUID.randomUUID(), otherId = UUID.randomUUID();
        var failure = new ActivityFailurePresentation(id); var other = new ActivityFailurePresentation(otherId);
        TestCleanup.register(h, () -> { failure.close(); other.close(); GuardianDown.cancelOwned(player, owner);
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED); TestPlayers.remove(player); });
        check(h, GuardianDown.resumeOwned(player, owner, player.position()), "Actual owned down scene starts");
        check(h, !GuardianDown.suppressHudOwned(player, foreign, true), "Foreign activity cannot suppress owned down HUD");
        failure.scope(1, "RF", true); check(h, failure.beginWipe(1), "Authoritative wipe starts once");
        check(h, !failure.beginWipe(1), "Repeated wipe trigger rejected");
        check(h, GuardianDown.suppressHudOwned(player, owner, true), "Wipe takes presentation only");
        TestPlayers.drain(player);
        for (int n = 0; n < 30; n++) {
            check(h, !failure.tick(1, true), "Scene cannot recover before full delay");
            failure.render(List.of(player), p -> false, n, 0);
        }
        check(h, sounds(player).size() == 1, "Wipe sends one dedicated cue despite 30 renders");
        check(h, hud(player, id, "black") && hud(player, id, "title"), "Full wipe backdrop and checkpoint text exist on real DisplayHud");
        other.scope(2, "SP", true); other.render(List.of(player), p -> false, 31, -1);
        failure.close();
        check(h, hud(player, otherId, "restricted"), "Closing old session cannot erase another session's HUD prefix");
        h.runAfterDelay(20, () -> {
            check(h, GuardianDown.active(player) && revived.get() == 0, "Presentation close is never a successful revival");
            check(h, DisplayHud.getHuds(player).keySet().stream().noneMatch(k -> k.startsWith("destiny:gd_")), "Suppressed down title stays absent across native ticks");
            check(h, GuardianDown.cancelOwned(player, owner) && revived.get() == 0, "Checkpoint cleanup cancels exact owned scene without success");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void fullScreenMenuHidesRestrictionWithoutReplayingCueAndWipeKeepsPriority(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL); h.getLevel().addNewPlayer(player);
        UUID id = UUID.randomUUID(); var failure = new ActivityFailurePresentation(id);
        TestCleanup.register(h, () -> {
            kim.biryeong.destiny.inventory.gear.GearScreen.close(player); failure.close();
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED); TestPlayers.remove(player);
        });
        failure.scope(1, "RF", true); failure.render(List.of(player), p -> false, 0, -1);
        check(h, hud(player, id, "restricted") && sounds(player).size() == 1, "Restriction starts with one cue");
        check(h, kim.biryeong.destiny.inventory.gear.GearScreen.open(player), "Actual Gear screen opens");
        failure.render(List.of(player), p -> false, 1, -1);
        check(h, !hud(player, id, "restricted") && !hud(player, id, "entry"), "Shared menu state suppresses restriction overlay");
        kim.biryeong.destiny.inventory.gear.GearScreen.close(player);
        failure.render(List.of(player), p -> false, 120, -1);
        check(h, hud(player, id, "restricted") && !hud(player, id, "entry"), "Closing menu restores sustained marker without rearming entry");
        check(h, sounds(player).isEmpty(), "Closing menu cannot replay entry cue");
        check(h, kim.biryeong.destiny.inventory.gear.GearScreen.open(player), "Menu can reopen");
        check(h, failure.beginWipe(1), "Wipe begins with existing menu state");
        for (int n = 0; n < 30; n++) { failure.tick(1, true); failure.render(List.of(player), p -> false, 121 + n, 0); }
        check(h, hud(player, id, "black") && hud(player, id, "title"), "Full wipe presentation retains priority over screen suppression");
        h.succeed();
    }
}
