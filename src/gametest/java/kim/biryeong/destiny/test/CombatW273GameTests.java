package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.List;

/** W273: server damage/packet assertions, not native movement or visual QA.
 * PvP test is manual and owns the singleton Control session; run it alone.
 * Login/ack/cleanup fixture reused from CrucibleW263GameTests, with no shared edits.
 */
public final class CombatW273GameTests {
    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < .00001, message + "; expected=" + expected + ", actual=" + actual);
    }
    private static float total(LivingEntity entity) {
        return Math.max(0, entity.getHealth()) + Math.max(0, entity.getAbsorptionAmount());
    }
    private static void noDefenses(LivingEntity target) {
        target.removeAllEffects();
        for (var slot : List.of(EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET))
            target.setItemSlot(slot, ItemStack.EMPTY);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(0);
        target.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
        target.setHealth(target.getMaxHealth());
        target.setAbsorptionAmount(0);
    }
    private static final class Login {
        final ServerPlayer initial;
        final io.netty.channel.embedded.EmbeddedChannel channel;
        net.minecraft.world.entity.PositionMoveRotation clientPose;

        Login(ServerPlayer initial, io.netty.channel.embedded.EmbeddedChannel channel) {
            this.initial = initial;
            this.channel = channel;
            clientPose = net.minecraft.world.entity.PositionMoveRotation.of(initial);
        }
    }

    private static ServerPlayer login(GameTestHelper h, List<Login> logins, String name, Element element) {
        check(h, name.length() <= 16, "Fixture profile respects protocol username length");
        var server = h.getLevel().getServer();
        var profile = new com.mojang.authlib.GameProfile(java.util.UUID.randomUUID(), name);
        var cookie = net.minecraft.server.network.CommonListenerCookie.createInitial(profile, false);
        var p = new ServerPlayer(server, h.getLevel(), profile, cookie.clientInformation());
        p.setPos(h.absoluteVec(new Vec3(2, 1, 2)));
        var connection = new net.minecraft.network.Connection(net.minecraft.network.protocol.PacketFlow.SERVERBOUND);
        var channel = new io.netty.channel.embedded.EmbeddedChannel(connection);
        var login = new Login(p, channel);
        logins.add(login);
        // Register before login can fail. Separate callbacks ensure one failed teardown cannot leak others.
        TestCleanup.register(h, () -> {
            var current = server.getPlayerList().getPlayer(p.getUUID());
            try {
                if (current != null) {
                    try {
                        CrucibleRuntime.leave(current, true);
                    } finally {
                        current.connection.disconnect(Component.literal("W273 Control QA cleanup"));
                    }
                }
            } finally {
                try {
                    channel.finishAndReleaseAll();
                } finally {
                    if (current != null && current != p) Guardians.forget(current);
                    Guardians.forget(p);
                }
            }
        });
        TestPacketContexts.initialize(connection, server, profile);
        server.getPlayerList().placeNewPlayer(connection, p, cookie);
        p.connection.handleAcceptPlayerLoad(new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        TowerSpawnWorld.tick(server);
        var data = Guardians.data(p);
        data.setGuardianClass(kim.biryeong.destiny.guardian.GuardianClass.HUNTER);
        data.setLoadout(kim.biryeong.destiny.guardian.GuardianClass.HUNTER,
                kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(element));
        return p;
    }

    /** W260 acknowledgements; CameraViews' negative synthetic IDs must never move the server body. */
    private static void acknowledge(Login login, ServerPlayer player, Object packet) {
        if (packet instanceof net.minecraft.network.protocol.BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) acknowledge(login, player, child);
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket position
                && position.id() >= 0) {
            login.clientPose = net.minecraft.world.entity.PositionMoveRotation.calculateAbsolute(
                    login.clientPose, position.change(), position.relatives());
            var at = login.clientPose.position();
            player.connection.handleAcceptTeleportPacket(
                    new net.minecraft.network.protocol.game.ServerboundAcceptTeleportationPacket(position.id(),
                            at.x, at.y, at.z, login.clientPose.yRot(), login.clientPose.xRot()));
        } else if (packet instanceof net.minecraft.network.protocol.common.ClientboundKeepAlivePacket keepAlive) {
            player.connection.handleKeepAlive(
                    new net.minecraft.network.protocol.common.ServerboundKeepAlivePacket(keepAlive.getId()));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundChunkBatchFinishedPacket) {
            player.connection.handleChunkBatchReceived(
                    new net.minecraft.network.protocol.game.ServerboundChunkBatchReceivedPacket(64f));
        } else if (packet instanceof net.minecraft.network.protocol.game.ClientboundRespawnPacket) {
            player.connection.handleAcceptPlayerLoad(
                    new net.minecraft.network.protocol.game.ServerboundPlayerLoadedPacket());
        }
    }

    private static void tickLogin(net.minecraft.server.MinecraftServer server, Login login) {
        var player = server.getPlayerList().getPlayer(login.initial.getUUID());
        if (player != null && !player.hasDisconnected()) player.connection.tick();
        login.channel.runPendingTasks();
        // Bounded per-tick draining; any remaining packets are handled on the next real server tick.
        for (int n = 0; n < 8192; n++) {
            Object packet = login.channel.readOutbound();
            if (packet == null) return;
            try {
                if (player != null && !player.hasDisconnected()) acknowledge(login, player, packet);
            } finally {
                io.netty.util.ReferenceCountUtil.release(packet);
            }
        }
    }


    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=20)
    public void customDamagePreservesMotionAndRestoresVanillaKnockback(GameTestHelper h) {
        var owner = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 2), 0, 0);
        var target = h.spawn(EntityTypes.HUSK, new net.minecraft.core.BlockPos(4, 1, 4));
        target.setNoAi(true);
        TestCleanup.register(h, () -> { target.discard(); TestPlayers.remove(owner); });
        noDefenses(target);
        var motion = new Vec3(.25, .18, -.35);
        for (var kind : AmmoGeneration.Kind.values()) {
            target.setDeltaMovement(motion);
            target.setOnGround(true);
            float before = total(target);
            Combat.damage(owner.level(), owner, target, 1, Element.KINETIC, new AmmoGeneration(kind, 0));
            check(h, total(target) < before, "Actual hurtServer removes health for " + kind);
            check(h, target.getDeltaMovement().equals(motion), "Damage preserves existing dodge/jump velocity for " + kind);
            check(h, !Combat.suppressesKnockback(target, target.getLastDamageSource()), "Damage context clears after return");
        }
        // This is an explicit external impulse, not another Combat.damage invocation.
        target.knockback(.4, 1, 0, owner.damageSources().playerAttack(owner), 1, false);
        check(h, !target.getDeltaMovement().equals(motion), "Unrelated explicit knockback remains functional");
        target.setDeltaMovement(motion);
        target.damageCooldownTime = 0;
        target.hurtServer(owner.level(), owner.damageSources().playerAttack(owner), 1);
        check(h, !target.getDeltaMovement().equals(motion), "Ordinary vanilla damage is not globally disabled");
        target.setDeltaMovement(motion);
        float before = total(target);
        for (float bad : new float[]{0, -1, Float.NaN, Float.POSITIVE_INFINITY})
            check(h, !Combat.damage(owner, target, bad, Element.KINETIC), "Invalid damage rejected");
        near(h, total(target), before, "Invalid requests do not change health");
        check(h, target.getDeltaMovement().equals(motion), "Invalid requests do not change movement");
        Guardians.data(owner).setSuperEnergy(0);
        Combat.damage(owner, target, 10000, Element.KINETIC);
        near(h, Guardians.data(owner).superEnergy(), AbilityService.killSuperEnergy, "Existing PvE kill reward is preserved");
        h.succeed();
    }

    private static void checkMotionPacket(GameTestHelper h, Object packet, ServerPlayer target, Vec3 before) {
        if (packet instanceof net.minecraft.network.protocol.BundlePacket<?> bundle) {
            for (var child : bundle.subPackets()) checkMotionPacket(h, child, target, before);
        } else if (packet instanceof ClientboundSetEntityMotionPacket motion && motion.id() == target.getId()) {
            check(h, motion.movement().distanceToSqr(before) < .000001,
                    "No damage-generated impulse reaches the client before server velocity restoration");
        }
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=510, manualOnly=true)
    public void controlActualLossRewardsExcludeDuplicatesAlliesAndSupers(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Run alone with an empty Control session");
        var server = h.getLevel().getServer();
        TowerSpawnWorld.open(server);
        var logins = new ArrayList<Login>();
        var owner = login(h, logins, "W273Owner", Element.SOLAR);
        var victim = login(h, logins, "W273Victim", Element.ARC);
        var ally = login(h, logins, "W273Ally", Element.VOID);
        h.onEachTick(() -> { for (var login : logins) tickLogin(server, login); });
        for (var p : List.of(owner, victim, ally)) {
            check(h, TowerSpawnWorld.teleport(p), "Fixture starts in Tower");
            check(h, CrucibleRuntime.join(p), "Fixture joins Control");
        }
        check(h, CrucibleRuntime.team(owner) == CrucibleRuntime.team(ally), "Third player joins owner's team");
        check(h, !CrucibleRuntime.canFight(owner, victim), "Intro denies fighting");
        float introHealth = total(victim);
        Guardians.data(owner).setSuperEnergy(0);
        check(h, !Combat.damage(owner, victim, 3, Element.KINETIC), "Intro damage denied");
        near(h, total(victim), introHealth, "Intro preserves victim health");
        near(h, Guardians.data(owner).superEnergy(), 0, "Intro grants no energy");

        h.runAfterDelay(450, () -> {
            check(h, CrucibleRuntime.canFight(owner, victim), "Intro and protection have ended");
            noDefenses(victim); noDefenses(ally);
            var primary = new AmmoGeneration(AmmoGeneration.Kind.PRIMARY, 0);
            var movement = new Vec3(.25, .18, -.35);
            tickLogin(server, logins.get(1)); // Drain/ack old packets before establishing measured velocity.
            victim.setDeltaMovement(movement); victim.setOnGround(true);
            victim.setAbsorptionAmount(4);
            float before = total(victim);
            Guardians.data(owner).setSuperEnergy(0);
            Combat.damage(owner.level(), owner, victim, 2, Element.KINETIC, primary);
            float loss = before - total(victim);
            near(h, loss, 2, "Absorption-only hit removes actual absorption");
            near(h, victim.getAbsorptionAmount(), 2, "Absorption pool actually consumed");
            near(h, victim.getHealth(), victim.getMaxHealth(), "Absorption-only hit preserves health");
            near(h, Guardians.data(owner).superEnergy(), loss * CrucibleSuperRewards.ENERGY_PER_HP,
                    "Actual absorbed damage pays the local curve");
            check(h, victim.getDeltaMovement().equals(movement), "Player hurt preserves existing velocity");
            var channel = logins.get(1).channel;
            channel.runPendingTasks();
            for (int n = 0; n < 8192; n++) {
                Object packet = channel.readOutbound();
                if (packet == null) break;
                try { checkMotionPacket(h, packet, victim, movement); acknowledge(logins.get(1), victim, packet); }
                finally { io.netty.util.ReferenceCountUtil.release(packet); }
            }
            float energy = Guardians.data(owner).superEnergy();
            float allyHp = total(ally);
            Combat.damage(owner, ally, 10000, Element.KINETIC);
            Combat.damage(owner, owner, 10000, Element.KINETIC);
            near(h, total(ally), allyHp, "Friendly hit is denied");
            near(h, Guardians.data(owner).superEnergy(), energy, "Friendly/self requests grant nothing");
            victim.getAbilities().invulnerable = true;
            try { Combat.damage(owner, victim, 10000, Element.KINETIC); }
            finally { victim.getAbilities().invulnerable = false; }
            near(h, Guardians.data(owner).superEnergy(), energy, "Rejected invulnerable hit grants nothing");

            noDefenses(victim);
            Guardians.data(owner).setSuperEnergy(0);
            float nestedBefore = total(victim);
            var outer = CrucibleSuperRewards.begin(owner, victim, primary);
            try { Combat.damage(owner.level(), owner, victim, 2, Element.KINETIC, primary); }
            finally { outer.finish(true); }
            near(h, Guardians.data(owner).superEnergy(), (nestedBefore-total(victim))*CrucibleSuperRewards.ENERGY_PER_HP,
                    "Nested actual loss is paid once, not again by the parent");
            float once = Guardians.data(owner).superEnergy();
            outer.finish(true);
            near(h, Guardians.data(owner).superEnergy(), once, "Replayed transaction cannot pay again");
            Guardians.data(owner).setSuperEnergy(0);
            Combat.damage(owner.level(), owner, victim, 2, Element.ARC, AmmoGeneration.SUPER);
            near(h, Guardians.data(owner).superEnergy(), 0, "Delayed super-attributed damage cannot charge a new super");
            Guardians.runtime(owner).superSession = new SuperSession() {
                public boolean tick() { return true; }
                public void primary() { }
                public void end() { }
                public float remaining() { return 1; }
            };
            try { Combat.damage(owner.level(), owner, victim, 2, Element.KINETIC, primary); }
            finally { Guardians.runtime(owner).superSession = null; }
            near(h, Guardians.data(owner).superEnergy(), 0, "Even gun hits during an active super grant nothing");
            Guardians.data(owner).setSuperEnergy(.9995f);
            Combat.damage(owner.level(), owner, victim, 2, Element.KINETIC, primary);
            near(h, Guardians.data(owner).superEnergy(), 1, "Energy is capped at one");
            noDefenses(victim); victim.setHealth(3); victim.setAbsorptionAmount(1);
            Guardians.data(owner).setSuperEnergy(0);
            check(h, Combat.damage(owner.level(), owner, victim, 10000, Element.KINETIC, primary), "Actual lethal hit kills");
            near(h, Guardians.data(owner).superEnergy(), 4*CrucibleSuperRewards.ENERGY_PER_HP+CrucibleSuperRewards.KILL_ENERGY,
                    "Overkill pays only four remaining HP plus 1.5%, without generic 4% duplication");
            float lethal = Guardians.data(owner).superEnergy();
            check(h, !Combat.damage(owner, victim, 10000, Element.KINETIC), "Dead-target replay is rejected");
            near(h, Guardians.data(owner).superEnergy(), lethal, "Dead life never pays a second kill");
            h.succeed();
        });
    }
}
