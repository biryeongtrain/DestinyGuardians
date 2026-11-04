package kim.biryeong.destiny.test;

import kim.biryeong.destiny.down.GuardianDown;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.concurrent.atomic.AtomicInteger;

public final class DevilsRevivalGameTests {
    @GameTest(structure="destiny-test:floor", maxTicks=110, environment="destiny-test:w90_isolated")
    public void fallKeepsSafeBodyAndOwnedRevivalWithoutDoubleDeath(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL);
        h.getLevel().addNewPlayer(player);
        var callbacks = new AtomicInteger();
        var owner = new GuardianDown.Options(false, 0, true, false, "추락",
                p -> callbacks.incrementAndGet(), 60, true, true);
        var body = player.position();
        int deaths = player.getStats().getValue(net.minecraft.stats.Stats.CUSTOM.get(net.minecraft.stats.Stats.DEATHS));
        TestCleanup.register(h, () -> { GuardianDown.cancelOwned(player, owner);
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(player); });
        player.setPos(body.x, h.getLevel().getMinY() - 20, body.z);
        check(h, GuardianDown.fallOwned(player, owner, body), "Fall enters owned down scene");
        check(h, !GuardianDown.fallOwned(player, owner, body), "Repeated fall cannot duplicate death");
        check(h, GuardianDown.bodyOwned(player, owner).orElseThrow().equals(body), "Body remains at safe ally revival location");
        check(h, player.getStats().getValue(net.minecraft.stats.Stats.CUSTOM.get(net.minecraft.stats.Stats.DEATHS)) == deaths + 1,
                "Fall records exactly one death");
        h.runAfterDelay(20, () -> {
            check(h, GuardianDown.active(player) && callbacks.get() == 0, "Ready countdown cannot auto-revive outside activity policy");
            check(h, GuardianDown.reviveOwned(player, owner), "Activity can revive fallen guardian");
        });
        h.runAfterDelay(90, () -> {
            check(h, !GuardianDown.active(player) && callbacks.get() == 1, "Normal revival callback occurs once");
            check(h, player.position().distanceToSqr(body) < 1, "Revival returns to supported body");
            h.succeed();
        });
    }

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    @GameTest(structure="destiny-test:floor", maxTicks=110, environment="destiny-test:w90_isolated")
    public void reconnectRestoresOwnedDownWithoutDeathOrAutomaticRevival(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL);
        h.getLevel().addNewPlayer(player);
        var callbacks = new AtomicInteger();
        var owner = new GuardianDown.Options(false, 600, true, false, "공격전 복구",
                p -> callbacks.incrementAndGet(), 60, true, true);
        var foreign = new GuardianDown.Options(false, 600, true, false, "다른 활동", null, 60, true, true);
        var body = player.position();
        int deaths = player.getStats().getValue(net.minecraft.stats.Stats.CUSTOM.get(net.minecraft.stats.Stats.DEATHS));
        TestCleanup.register(h, () -> { GuardianDown.cancelOwned(player, owner);
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(player); });
        check(h, GuardianDown.resumeOwned(player, owner, body, 0), "Existing death presentation resumes");
        check(h, GuardianDown.resumeOwned(player, owner, body, 0), "Same owner resume is idempotent");
        check(h, !GuardianDown.resumeOwned(player, foreign, body, 0), "Foreign owner cannot replace active scene");
        check(h, player.getStats().getValue(net.minecraft.stats.Stats.CUSTOM.get(net.minecraft.stats.Stats.DEATHS)) == deaths,
                "Resume does not count a second death");
        h.runAfterDelay(20, () -> {
            check(h, GuardianDown.active(player) && callbacks.get() == 0, "External scheduler retains control after countdown");
            check(h, GuardianDown.cancelOwned(player, owner), "Owned cancellation succeeds");
            check(h, callbacks.get() == 0, "Cancellation has no success callback");
            check(h, GuardianDown.resumeOwned(player, owner, body, 0), "Cancelled presentation can resume existing policy");
            check(h, GuardianDown.reviveOwned(player, owner), "Policy may now finish revival");
        });
        h.runAfterDelay(90, () -> {
            check(h, !GuardianDown.active(player) && callbacks.get() == 1, "Exactly one completed revival");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", maxTicks=130, environment="destiny-test:w90_isolated")
    public void ownedRevivalRejectsOtherActivityAndProtectionEndsOnAttack(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL);
        h.getLevel().addNewPlayer(player);
        var callbacks = new AtomicInteger();
        var owner = new GuardianDown.Options(false, 600, true, false, "테스트", p -> callbacks.incrementAndGet(), 60, true);
        var foreign = new GuardianDown.Options(false, 600, true, false, "테스트", null, 60, true);
        // Rule is identity-scoped; removed test players cannot claim any later session.
        GuardianDown.register((p, source) -> p == player ? owner : null);
        TestCleanup.register(h, () -> { GuardianDown.cancelOwned(player, owner);
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(player); });
        player.setHealth(1);
        player.damageCooldownTime = 0;
        player.hurtServer(h.getLevel(), player.damageSources().generic(), 10);
        check(h, GuardianDown.active(player), "Lethal hit enters owned down flow");
        check(h, GuardianDown.bodyOwned(player, foreign).isEmpty(), "Other activity cannot observe owned body");
        check(h, !GuardianDown.reviveOwned(player, foreign), "Other activity cannot revive");
        check(h, !GuardianDown.cancelOwned(player, foreign), "Other activity cannot cancel camera");
        check(h, GuardianDown.reviveOwned(player, owner), "Owning team can start ally revival");
        check(h, !GuardianDown.reviveOwned(player, owner), "Duplicate revival is rejected");
        h.runAfterDelay(30, () -> {
            check(h, GuardianDown.materializing(player) && callbacks.get() == 0, "Gameplay revival waits for full source motion");
            var anchor = player.position();
            player.setPos(anchor.add(3, 2, 3)); player.setYRot(145); player.setXRot(80);
            check(h, GuardianDown.holdReviveMovement(player), "Revival owns movement");
            check(h, player.position().equals(anchor) && player.getYRot() == 0 && player.getXRot() == 0,
                    "Movement and aim cannot change the fixed revival pose");
            check(h, !kim.biryeong.destiny.weapon.WeaponLoadout.canUse(player), "Cannot fire during revival motion");
        });
        h.runAfterDelay(60, () -> check(h, GuardianDown.active(player) && callbacks.get() == 0,
                "Self revival stays active until sound-aligned 61 tick deadline"));
        h.runAfterDelay(66, () -> {
            check(h, !GuardianDown.active(player) && callbacks.get() == 1, "One normal revival callback");
            check(h, completionSounds(player) == 1, "Exactly one completion sound after successful revival");
            player.damageCooldownTime = 0;
            player.hurtServer(h.getLevel(), player.damageSources().generic(), 2);
            check(h, player.getHealth() == player.getMaxHealth(), "Revival protection blocks damage");
            GuardianDown.attacked(player);
            player.damageCooldownTime = 0;
            player.hurtServer(h.getLevel(), player.damageSources().generic(), 2);
            check(h, player.getHealth() < player.getMaxHealth(), "Accepted attack ends opted-in protection");
            player.setHealth(1); player.damageCooldownTime = 0;
            player.hurtServer(h.getLevel(), player.damageSources().generic(), 10);
            check(h, GuardianDown.cancelOwned(player, owner), "Checkpoint can cancel its own down state");
            check(h, callbacks.get() == 1, "Cancellation cannot masquerade as normal revival");
            check(h, !player.isSpectator(), "Cancellation restores gameplay mode");
            check(h, completionSounds(player) == 0, "Cancelled down cannot emit another completion sound");
            h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void fireteamAudioUsesDirectPlayersPacketsAndIndependentStops(GameTestHelper h) {
        var fallen = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        var ally = TestPlayers.create(h, new Vec3(3.5, 1, 2.5), 0, 0);
        var outsider = TestPlayers.create(h, new Vec3(4.5, 1, 2.5), 0, 0);
        var team = java.util.List.of(fallen, ally);
        TestCleanup.register(h, () -> { TestPlayers.remove(fallen); TestPlayers.remove(ally); TestPlayers.remove(outsider); });
        TestPlayers.drain(fallen); TestPlayers.drain(ally); TestPlayers.drain(outsider);
        kim.biryeong.destiny.down.FireteamReviveAudio.announce(fallen, team);
        var packets = TestPlayers.outbound(ally);
        var announcement = packets.stream().filter(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::isInstance)
                .map(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::cast).findFirst().orElseThrow();
        check(h, announcement.getSource() == net.minecraft.sounds.SoundSource.PLAYERS
                && announcement.getSound().value().location().toString().equals("destiny_fireteam:guardian_down"), "Team-only direct Korean announcement");
        check(h, TestPlayers.outbound(outsider).isEmpty() && TestPlayers.outbound(fallen).isEmpty(), "No announcement to outsider or fallen owner");
        try (var a = new kim.biryeong.destiny.down.FireteamReviveAudio(fallen, team, fallen.position());
             var b = new kim.biryeong.destiny.down.FireteamReviveAudio(ally, team, ally.position())) {
            var sounds = TestPlayers.outbound(ally).stream().filter(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::isInstance)
                    .map(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::cast).toList();
            check(h, sounds.size() == 2 && !sounds.get(0).getSound().value().location().equals(sounds.get(1).getSound().value().location()), "Concurrent rescue clips own distinct events");
            a.close(); a.close();
            var stops = TestPlayers.outbound(ally).stream().filter(net.minecraft.network.protocol.game.ClientboundStopSoundPacket.class::isInstance)
                    .map(net.minecraft.network.protocol.game.ClientboundStopSoundPacket.class::cast).toList();
            check(h, stops.size() == 1 && stops.getFirst().getName().equals(sounds.getFirst().getSound().value().location())
                    && stops.getFirst().getSource() == net.minecraft.sounds.SoundSource.PLAYERS, "Idempotent cancel stops only its own rescue");
        }
        h.succeed();
    }

    private static long completionSounds(net.minecraft.server.level.ServerPlayer player) {
        return TestPlayers.outbound(player).stream()
                .filter(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::isInstance)
                .map(net.minecraft.network.protocol.game.ClientboundSoundPacket.class::cast)
                .filter(p -> p.getSound().value().location().toString().matches("destiny_fireteam:respawn_complete_[1-4]"))
                .count();
    }

    @GameTest(structure="destiny-test:floor", maxTicks=90, environment="destiny-test:w90_isolated")
    public void interruptedAllyPreviewReturnsToDownAndNeverGrantsRevival(GameTestHelper h) {
        var player = TestPlayers.create(h, new Vec3(2.5, 1, 2.5), 0, 0);
        player.setGameMode(GameType.SURVIVAL); h.getLevel().addNewPlayer(player);
        var callbacks = new AtomicInteger();
        var owner = new GuardianDown.Options(false, 600, true, false, "부활", p -> callbacks.incrementAndGet(), 60, true, true);
        var body = player.position(); var ally = java.util.UUID.randomUUID();
        TestCleanup.register(h, () -> { GuardianDown.cancelOwned(player, owner);
            player.level().removePlayerImmediately(player, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED); TestPlayers.remove(player); });
        check(h, GuardianDown.resumeOwned(player, owner, body), "Down restored");
        GuardianDown.progressOwned(player, owner, ally, 29, java.util.List.of(player));
        check(h, GuardianDown.materializing(player) && callbacks.get() == 0, "Motion preview is not successful revival");
        h.runAfterDelay(10, () -> {
            GuardianDown.progressOwned(player, owner, null, 0, java.util.List.of(player));
            check(h, GuardianDown.active(player) && !GuardianDown.materializing(player) && player.isSpectator(), "Lost helper restores ghost and death camera");
            check(h, callbacks.get() == 0, "Interrupted source motion cannot invoke successful callback");
        });
        h.runAfterDelay(12, () -> {
            GuardianDown.progressOwned(player, owner, ally, 29, java.util.List.of(player));
            check(h, GuardianDown.materializing(player), "New helper attempt can present again");
        });
        h.runAfterDelay(46, () -> {
            check(h, callbacks.get() == 0, "Full animation without gameplay authorization cannot revive");
            check(h, GuardianDown.reviveOwned(player, owner), "Completed ally hold authorizes final motion tail");
        });
        h.runAfterDelay(52, () -> {
            check(h, !GuardianDown.active(player) && !player.isSpectator() && callbacks.get() == 1, "Only authorized retry completes exactly once");
            h.succeed();
        });
    }

}
