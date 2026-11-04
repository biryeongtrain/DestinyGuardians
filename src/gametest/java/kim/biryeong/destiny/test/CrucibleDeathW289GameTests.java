package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.*;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;

/** Real login/death/replacement/arena lifecycle; no rendering or native-input claim. */
public final class CrucibleDeathW289GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static boolean deathHud(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().anyMatch(id -> id.startsWith("destiny:crucible_ui/down_"));
    }
    private static Object field(Object target, String name) {
        try {
            var type = target instanceof Class<?> c ? c : target.getClass();
            var f = type.getDeclaredField(name); f.setAccessible(true);
            return f.get(target instanceof Class<?> ? null : target);
        } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
    }
    private static void recovery(String method, ServerPlayer p) {
        try {
            var type = Class.forName("kim.biryeong.destiny.crucible.CrucibleRecovery");
            var m = type.getDeclaredMethod(method, ServerPlayer.class); m.setAccessible(true); m.invoke(null, p);
        } catch (ReflectiveOperationException error) { throw new AssertionError(error); }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w289_control", maxTicks=730)
    public void nativeDeathShowsGhostThenRespawnsAndDepartureCleansUp(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Exclusive Control fixture");
        var server = h.getLevel().getServer();
        TowerSpawnWorld.open(server);
        var logins = new ArrayList<CrucibleW263GameTests.Login>();
        var killer = CrucibleW263GameTests.login(h, logins, "W289Killer", Element.SOLAR);
        var victim = CrucibleW263GameTests.login(h, logins, "W289Victim", Element.ARC);
        h.onEachTick(() -> { for (var login : logins) CrucibleW263GameTests.tickLogin(server, login); });
        check(h, TowerSpawnWorld.teleport(killer) && TowerSpawnWorld.teleport(victim), "Tower ready");
        check(h, CrucibleRuntime.join(killer) && CrucibleRuntime.join(victim), "Opposing teams joined");
        int[] score = {0};
        Vec3[] deathAt = {null};
        ServerPlayer[] replacement = {null};
        h.runAfterDelay(450, () -> {
            check(h, CrucibleRuntime.canFight(killer, victim), "Match is playing and protection ended");
            check(h, victim.level().getGameRules().get(GameRules.IMMEDIATE_RESPAWN), "Native death menu suppressed only in arena");
            deathAt[0] = victim.position();
            score[0] = CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(killer)) + 1;
            check(h, Combat.damage(killer, victim, 10000, Element.KINETIC), "Real lethal hit");
        });
        h.runAfterDelay(465, () -> {
            var p = server.getPlayerList().getPlayer(victim.getUUID());
            replacement[0] = p;
            check(h, p != null && p != victim && p.isAlive(), "Native replacement is ready during countdown");
            check(h, p.isSpectator() && CrucibleDeathScene.active(p), "Noncombat death scene active");
            check(h, p.getPostEffects().contains(CrucibleDeathScene.EFFECT) && deathHud(p), "Red grade and dedicated death HUD published");
            check(h, p.getCamera() != p && p.level().getEntity(p.getCamera().getId()) == null, "Private camera never enters world storage");
            check(h, p.getCamera().position().distanceTo(deathAt[0]) < 5, "Camera stays at death location");
            Object scene = ((java.util.Map<?, ?>) field(CrucibleDeathScene.class, "ACTIVE")).get(p.getUUID());
            Object ghost = field(scene, "ghost");
            check(h, ((java.util.List<?>) field(ghost, "parts")).size() == 11
                    && (Float) field(ghost, "openness") > .7f, "All eleven shell parts deploy over time");
            var camera = p.getCamera();
            p.setCamera(p);
            check(h, p.getCamera() == camera, "Sneak cannot escape the death camera");
            p.setCamera(killer);
            check(h, p.getCamera() == camera, "Spectator target cannot replace the death camera");
            check(h, !CrucibleRuntime.canAct(p) && !CrucibleRuntime.canFight(p, killer), "No combat or capture before deadline");
            check(h, !Combat.damage(p, killer, 10000, Element.KINETIC), "Dead participant cannot damage a live opponent");
            check(h, CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(killer)) == score[0], "Exactly one death score");
        });
        h.runAfterDelay(545, () -> check(h, CrucibleDeathScene.active(replacement[0])
                && !CrucibleRuntime.canAct(replacement[0]), "Wait the full five seconds"));
        h.runAfterDelay(555, () -> {
            var p = replacement[0];
            check(h, p.gameMode() == GameType.ADVENTURE && p.getCamera() == p, "Return to normal player camera/mode");
            check(h, !CrucibleDeathScene.active(p) && !p.getPostEffects().contains(CrucibleDeathScene.EFFECT)
                    && !deathHud(p), "No death entities, red grade or countdown after respawn");
            check(h, CrucibleWorld.isArena(p.level()) && TowerSpawnWorld.isSafeArrival(p.level(), p.position()), "Safe team spawn");
            check(h, p.getHealth() == p.getMaxHealth() && CrucibleRuntime.canAct(p), "Restored health and combat eligibility");
            check(h, !CrucibleRuntime.canFight(killer, p), "Spawn protection starts after countdown");
        });
        h.runAfterDelay(600, () -> {
            check(h, CrucibleRuntime.canFight(killer, replacement[0]), "Spawn protection naturally expires");
            check(h, Combat.damage(killer, replacement[0], 10000, Element.KINETIC), "Second real death");
        });
        h.runAfterDelay(615, () -> {
            var p = server.getPlayerList().getPlayer(victim.getUUID());
            check(h, CrucibleDeathScene.active(p), "Second death has a fresh scene");
            check(h, CrucibleRuntime.leave(p, true), "Can leave during countdown");
            check(h, !CrucibleDeathScene.active(p) && p.getCamera() == p
                    && !p.getPostEffects().contains(CrucibleDeathScene.EFFECT) && !deathHud(p), "Departure removes all owned presentation");
            check(h, !p.isSpectator() && !CrucibleWorld.isArena(p.level()), "Departure restores normal mode and tower");
        });
        h.runAfterDelay(715, () -> {
            var p = server.getPlayerList().getPlayer(victim.getUUID());
            check(h, !CrucibleRuntime.participating(p) && !CrucibleDeathScene.active(p)
                    && !CrucibleWorld.isArena(p.level()), "Expired countdown cannot pull departed player back");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w289_scene", maxTicks=50)
    public void wallClippingAndEffectOwnershipCleanup(GameTestHelper h) {
        var server = h.getLevel().getServer();
        var logins = new ArrayList<CrucibleW263GameTests.Login>();
        var p = CrucibleW263GameTests.login(h, logins, "W289Scene", Element.SOLAR);
        TestCleanup.register(h, () -> CrucibleDeathScene.stop(p));
        h.onEachTick(() -> { for (var login : logins) CrucibleW263GameTests.tickLogin(server, login); });
        for (int x = 0; x <= 4; x++) for (int y = 1; y <= 4; y++)
            h.setBlock(x, y, 0, net.minecraft.world.level.block.Blocks.STONE);
        Vec3 origin = h.absoluteVec(new Vec3(2, 2, 2));
        var foreign = kim.biryeong.destiny.DestinyGuardians.id("crucible/intro");
        p.addPostEffect(foreign);
        p.addPostEffect(CrucibleDeathScene.EFFECT);
        CrucibleDeathScene.start(p, new CrucibleDeathScene.Death(h.getLevel(), origin, 0, server.getTickCount() + 100, "QA"));
        check(h, p.getCamera().position().distanceTo(origin) >= 1.8, "Wall obstruction selects a side with framing room");
        var hit = h.getLevel().clip(new net.minecraft.world.level.ClipContext(origin, p.getCamera().position(),
                net.minecraft.world.level.ClipContext.Block.COLLIDER, net.minecraft.world.level.ClipContext.Fluid.NONE, p));
        check(h, hit.getType() == net.minecraft.world.phys.HitResult.Type.MISS, "Ghost remains visible without a wall through the lens");
        CrucibleDeathScene.stop(p);
        CrucibleDeathScene.stop(p);
        check(h, p.getCamera() == p && !CrucibleDeathScene.active(p) && !deathHud(p), "Idempotent cleanup releases camera and HUD");
        check(h, p.getPostEffects().contains(foreign) && p.getPostEffects().contains(CrucibleDeathScene.EFFECT), "Never remove effects this scene did not add");
        p.removePostEffect(foreign); p.removePostEffect(CrucibleDeathScene.EFFECT);
        p.setGameMode(GameType.SURVIVAL);
        h.succeed();
    }

    @SuppressWarnings({"unchecked", "rawtypes"})
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void persistedOwnershipRecoversWithoutLiveCameraSession(GameTestHelper h) throws Exception {
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(2, 1, 2), 0, 0);
        TestCleanup.register(h, () -> TestPlayers.remove(p));
        recovery("remember", p);
        recovery("markDeathEffect", p);
        var recoveryType = Class.forName("kim.biryeong.destiny.crucible.CrucibleRecovery");
        var attachment = (net.fabricmc.fabric.api.attachment.v1.AttachmentType) field(recoveryType, "DATA");
        Object state = p.getAttached(attachment);
        var codec = (com.mojang.serialization.Codec) field(state.getClass(), "CODEC");
        var json = codec.encodeStart(com.mojang.serialization.JsonOps.INSTANCE, state).getOrThrow();
        p.setAttached(attachment, codec.parse(com.mojang.serialization.JsonOps.INSTANCE, json).getOrThrow());
        var foreign = kim.biryeong.destiny.DestinyGuardians.id("crucible/intro");
        p.setGameMode(GameType.SPECTATOR);
        p.addPostEffect(CrucibleDeathScene.EFFECT); p.addPostEffect(foreign);
        check(h, !CrucibleDeathScene.active(p), "No in-memory session after simulated reload");
        recovery("restore", p);
        check(h, p.gameMode() == GameType.SURVIVAL && !p.getPostEffects().contains(CrucibleDeathScene.EFFECT), "Persisted recovery restores mode and clears owned grade");
        check(h, p.getPostEffects().contains(foreign), "Foreign effect survives recovery");
        p.removePostEffect(foreign); recovery("finish", p);
        h.succeed();
    }
}
