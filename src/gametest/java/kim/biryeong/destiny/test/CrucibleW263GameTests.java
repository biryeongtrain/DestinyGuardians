package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.crucible.ControlMatch;
import kim.biryeong.destiny.crucible.CrucibleAmmo;
import kim.biryeong.destiny.crucible.CrucibleAmmoRules;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.crucible.CrucibleWorld;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kim.biryeong.destiny.weapon.AmmoEconomy;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.destiny.weapon.CrucibleDamage;
import kim.biryeong.destiny.weapon.WeaponBallistics;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponCharacteristics;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponMagazine;
import kim.biryeong.destiny.weapon.WeaponPrecision;
import kim.biryeong.destiny.weapon.WeaponProfile;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.registries.Registries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.ResourceKey;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageTypes;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.EquipmentSlot;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.enchantment.Enchantments;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/**
 * Run alone in the master's owned tower-enabled server: this manual test owns the Control session.
 * Real PlayerList login, Combat/hurtServer and runtime respawn; packet acknowledgements are simulated.
 * This is server gameplay evidence, not native Vision input, rendering or acoustic verification.
 * W260's CURRENT main login/ack lifecycle is duplicated here so the stale worker needs no shared edits.
 */
public final class CrucibleW263GameTests {
    private static final double EPS = .004;
    private static final EquipmentSlot[] ARMOR = {
            EquipmentSlot.HEAD, EquipmentSlot.CHEST, EquipmentSlot.LEGS, EquipmentSlot.FEET
    };

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < EPS,
                message + "; expected=" + expected + ", actual=" + actual);
    }

    static final class Login {
        final ServerPlayer initial;
        final io.netty.channel.embedded.EmbeddedChannel channel;
        net.minecraft.world.entity.PositionMoveRotation clientPose;

        Login(ServerPlayer initial, io.netty.channel.embedded.EmbeddedChannel channel) {
            this.initial = initial;
            this.channel = channel;
            clientPose = net.minecraft.world.entity.PositionMoveRotation.of(initial);
        }
    }

    static ServerPlayer login(GameTestHelper h, List<Login> logins, String name, Element element) {
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
                        current.connection.disconnect(Component.literal("W263 Control QA cleanup"));
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

    static void tickLogin(net.minecraft.server.MinecraftServer server, Login login) {
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

    private static WeaponMagazine ammo(GameTestHelper h, ServerPlayer player, WeaponCatalog.Entry sniper) {
        int slot = WeaponCharacteristics.of(sniper).slot().hotbar();
        var stack = player.getInventory().getItem(slot);
        check(h, WeaponItems.entry(stack).filter(e -> e.id().equals(sniper.id())).isPresent(),
                "The equipped sniper survives in its canonical inventory slot");
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(sniper));
    }

    private static void noDefenses(LivingEntity target) {
        target.removeAllEffects();
        for (var slot : ARMOR) target.setItemSlot(slot, ItemStack.EMPTY);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
        target.setAbsorptionAmount(0);
        target.setHealth(target.getMaxHealth());
    }

    /** Resets a living fixture between independent nonlethal samples, never resurrects a dead entity. */
    private static float hit(GameTestHelper h, ServerPlayer shooter, LivingEntity target,
                             WeaponCatalog.Entry weapon, float amount) {
        check(h, target.isAlive() && amount > 0 && amount < target.getMaxHealth(),
                "Damage comparison is a positive nonlethal transaction on a living target");
        target.setHealth(target.getMaxHealth());
        float before = target.getHealth() + target.getAbsorptionAmount();
        check(h, !Combat.damage(shooter.level(), shooter, target, amount, Element.KINETIC,
                        AmmoGeneration.weapon(weapon)), "Comparison hit must not kill");
        return before - target.getHealth() - target.getAbsorptionAmount();
    }

    private static void crucibleSource(GameTestHelper h, LivingEntity target, ServerPlayer killer) {
        var source = target.getLastDamageSource();
        check(h, source != null && source.is(ResourceKey.create(Registries.DAMAGE_TYPE,
                        DestinyGuardians.id("crucible"))), "Actual hurt records destiny:crucible");
        check(h, source.getEntity() == killer && source.getDirectEntity() == killer,
                "Actual damage source retains the attacking player, including the lethal transaction");
    }

    private static void aceDamage(GameTestHelper h, ServerPlayer shooter, ServerPlayer target) {
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        var original = WeaponBallistics.of(ace);
        float localBase = WeaponProfile.forEntry(ace).damage();
        noDefenses(target);
        double originalMaxBase = target.getAttributeBaseValue(Attributes.MAX_HEALTH);
        float originalMax = target.getMaxHealth();
        float d2Body;
        double precisionAt230;
        // Sample the public API at the D2 health scale; do not couple to an unpublished row-loader API.
        // The three-headshot gameplay assertion below separately constrains lethal damage behavior.
        try {
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(230);
            near(h, target.getMaxHealth(), 230, "Normalization reference has exactly 230 HP");
            d2Body = CrucibleDamage.base(ace, target, localBase);
            precisionAt230 = CrucibleDamage.precision(ace, target, original.precision());
            check(h, d2Body > 0 && precisionAt230 > 1, "Ace has positive base damage and a critical multiplier");
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(originalMax * 2);
            near(h, CrucibleDamage.base(ace, target, localBase), d2Body * target.getMaxHealth() / 230,
                    "Conversion follows changed target maxHealth instead of assuming a 20 HP player");
        } finally {
            target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(originalMaxBase);
            target.setHealth(target.getMaxHealth());
        }
        float base = CrucibleDamage.base(ace, target, localBase);
        double precision = CrucibleDamage.precision(ace, target, original.precision());
        var pvp = CrucibleDamage.ballistics(ace, target, original);
        near(h, base, d2Body * target.getMaxHealth() / 230, "Ace body uses normalized PvP damage");
        near(h, precision, precisionAt230, "PvP critical/body ratio is independent of target maxHealth");
        near(h, pvp.precision(), precision, "Target ballistics carries PvP precision");
        check(h, pvp.start() == original.start() && pvp.end() == original.end() && pvp.floor() == original.floor(),
                "Per-target precision preserves the original falloff curve");
        near(h, CrucibleDamage.base(ace, target, localBase * 1.5f), base * 1.5,
                "Per-shot local damage modifiers survive normalization");

        var box = target.getBoundingBox();
        double z = (box.minZ + box.maxZ) / 2;
        var from = new Vec3(box.minX - 3, box.maxY - .1, z);
        var head = new Vec3(box.minX, from.y, z);
        var bodyFrom = new Vec3(from.x, box.minY + box.getYsize() * .5, z);
        var body = new Vec3(box.minX, bodyFrom.y, z);
        check(h, WeaponPrecision.critical(target, from, head, precision), "Player head hit is critical");
        check(h, !WeaponPrecision.critical(target, bodyFrom, body, precision), "Player torso remains noncritical");
        float bodyDamage = pvp.damage(base, 0, false);
        float criticalDamage = pvp.damage(base, 0, true);
        check(h, criticalDamage > bodyDamage, "Ace PvP critical damage exceeds its base damage");
        float bodyLoss = hit(h, shooter, target, ace, bodyDamage);
        near(h, bodyLoss, bodyDamage, "Unarmored body hit removes the normalized amount of actual HP");
        crucibleSource(h, target, shooter);
        float criticalLoss = hit(h, shooter, target, ace, criticalDamage);
        near(h, criticalLoss, d2Body * precision * target.getMaxHealth() / 230, "Actual critical HP loss is normalized");
        near(h, criticalLoss / bodyLoss, precision, "Actual PvP critical/base HP losses match the ratio");

        target.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
        target.setAbsorptionAmount(4);
        near(h, target.getAbsorptionAmount(), 4, "Shield fixture has real absorption");
        check(h, WeaponPrecision.critical(target, from, head, precision), "Player absorption does not suppress headshots");
        near(h, hit(h, shooter, target, ace, criticalDamage), criticalDamage,
                "Shielded critical removes the same combined HP and absorption");
        check(h, target.getAbsorptionAmount() < 4, "Critical actually consumes absorption");
        target.setAbsorptionAmount(0);

        ItemStack[] armor = {new ItemStack(Items.NETHERITE_HELMET), new ItemStack(Items.NETHERITE_CHESTPLATE),
                new ItemStack(Items.NETHERITE_LEGGINGS), new ItemStack(Items.NETHERITE_BOOTS)};
        for (int i = 0; i < ARMOR.length; i++) target.setItemSlot(ARMOR[i], armor[i]);
        // Set effective armor immediately; equipment attribute refresh otherwise depends on the next tick.
        target.getAttribute(Attributes.ARMOR).setBaseValue(20);
        target.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(8);
        check(h, target.getArmorValue() >= 20, "Armored control has effective vanilla armor");
        near(h, hit(h, shooter, target, ace, bodyDamage), bodyLoss, "Armor/toughness cannot reduce Crucible HP loss");
        var protection = target.level().registryAccess().lookupOrThrow(Registries.ENCHANTMENT)
                .getOrThrow(Enchantments.PROTECTION);
        for (var piece : armor) piece.enchant(protection, 4);
        check(h, target.getItemBySlot(EquipmentSlot.CHEST).getEnchantments().getLevel(protection) == 4,
                "Protection enchantment is actually equipped");
        near(h, hit(h, shooter, target, ace, bodyDamage), bodyLoss, "Protection cannot reduce Crucible HP loss");
        target.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 1));
        check(h, target.hasEffect(MobEffects.RESISTANCE), "Resistance control is active");
        near(h, hit(h, shooter, target, ace, criticalDamage), criticalLoss,
                "Armor, Protection and Resistance together cannot reduce Crucible critical HP loss");
        crucibleSource(h, target, shooter);
        noDefenses(target);
    }

    private static void pveUnchanged(GameTestHelper h, ServerPlayer shooter) {
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        var original = WeaponBallistics.of(ace);
        float local = WeaponProfile.forEntry(ace).damage();
        var mob = EntityTypes.HUSK.create(shooter.level(), EntitySpawnReason.COMMAND);
        check(h, mob != null, "PvE control mob created");
        TestCleanup.register(h, mob::discard);
        mob.setPos(shooter.position().add(0, 3, 0));
        mob.setNoAi(true);
        mob.setNoGravity(true);
        mob.setPersistenceRequired();
        mob.getAttribute(Attributes.MAX_HEALTH).setBaseValue(200);
        mob.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        noDefenses(mob);
        check(h, shooter.level().addFreshEntity(mob), "PvE control is a real world entity");
        near(h, CrucibleDamage.base(ace, mob, local), local, "PvE retains the local base");
        near(h, CrucibleDamage.precision(ace, mob, original.precision()), original.precision(), "PvE retains precision");
        check(h, CrucibleDamage.ballistics(ace, mob, original).equals(original), "PvE ballistics remains unchanged");
        near(h, hit(h, shooter, mob, ace, local), local, "Unarmored PvE Combat still applies the local damage");
        check(h, mob.getLastDamageSource().is(DamageTypes.PLAYER_ATTACK), "PvE retains vanilla playerAttack source");
        mob.getAttribute(Attributes.ARMOR).setBaseValue(12);
        mob.addEffect(new MobEffectInstance(MobEffects.RESISTANCE, 200, 0));
        mob.setHealth(mob.getMaxHealth());
        mob.damageCooldownTime = 0;
        check(h, mob.hurtServer(shooter.level(), shooter.damageSources().playerAttack(shooter), local),
                "Vanilla PvE comparison accepts damage");
        float vanillaLoss = mob.getMaxHealth() - mob.getHealth();
        check(h, vanillaLoss > 0 && vanillaLoss < local, "Vanilla PvE control is actually mitigated");
        near(h, hit(h, shooter, mob, ace, local), vanillaLoss, "PvE armor/resistance matches ordinary vanilla damage");
        mob.discard();
    }

    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 760, manualOnly = true)
    public void controlDamageAndSpecialAmmoSurviveDeathRespawn(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Fixture requires exclusive empty Control session");
        var server = h.getLevel().getServer();
        var tower = TowerSpawnWorld.open(server);
        var logins = new ArrayList<Login>();
        var shooter = login(h, logins, "W263Sniper", Element.SOLAR);
        var enemy = login(h, logins, "W263Enemy", Element.ARC);
        h.onEachTick(() -> { for (var login : logins) tickLogin(server, login); });
        check(h, TowerSpawnWorld.teleport(shooter) && TowerSpawnWorld.teleport(enemy), "Both login players start in Tower");
        var sniper = WeaponCatalog.find("beloved").orElseThrow();
        int sniperSlot = WeaponCharacteristics.of(sniper).slot().hotbar();
        shooter.getInventory().setItem(sniperSlot, WeaponItems.create(sniper));
        shooter.getInventory().setSelectedSlot(sniperSlot);
        check(h, WeaponLoadout.equipHeld(shooter) == null, "Real sniper is equipped before joining Control");
        check(h, CrucibleRuntime.join(shooter) && CrucibleRuntime.join(enemy), "Two simulated login players join Control");
        check(h, shooter.level() == enemy.level() && CrucibleWorld.isArena(shooter.level()), "Both share the Control arena");
        check(h, shooter.gameMode() == GameType.ADVENTURE && !CrucibleRuntime.canAct(shooter), "Intro blocks combat");
        check(h, ammo(h, shooter, sniper).total() == 2, "First-life join grants exactly two sniper cartridges");
        ServerPlayer[] ally = new ServerPlayer[1];
        int[] scoreAfterKill = new int[1];

        h.runAfterDelay(450, () -> {
            check(h, CrucibleRuntime.snapshot().phase() == ControlMatch.Phase.PLAYING, "450-tick intro wait reaches play");
            check(h, CrucibleRuntime.canFight(shooter, enemy), "Initial enemy protection expires before measurements");
            var magazine = ammo(h, shooter, sniper);
            check(h, magazine.total() == 2, "Intro/tick hooks cannot repeat the first-life ammo grant");
            if (magazine.rounds() == 0) magazine.reload();
            check(h, magazine.consume(2), "Consume both real starting sniper cartridges");
            WeaponItems.save(shooter.getInventory().getItem(sniperSlot), magazine);
            check(h, ammo(h, shooter, sniper).total() == 0, "Consumed sniper state is persisted on its item");
            ally[0] = login(h, logins, "W263Ally", Element.VOID);
            check(h, CrucibleRuntime.join(ally[0]) && CrucibleRuntime.team(shooter) == CrucibleRuntime.team(ally[0]),
                    "Third connected fixture joins the shooter's team for friendly-fire coverage");
        });
        h.runAfterDelay(510, () -> {
            check(h, CrucibleRuntime.canAct(ally[0]) && CrucibleRuntime.canFight(enemy, ally[0]),
                    "Ally is damageable by an enemy; friendly test is not passing because of spawn protection");
            float before = ally[0].getHealth() + ally[0].getAbsorptionAmount();
            var previousSource = ally[0].getLastDamageSource();
            check(h, !CrucibleRuntime.canFight(shooter, ally[0]), "Same-team fighting is rejected");
            check(h, !Combat.damage(shooter, ally[0], 10000, Element.ARC), "Actual friendly lethal request is rejected");
            near(h, ally[0].getHealth() + ally[0].getAbsorptionAmount(), before, "Friendly hit cannot remove HP or absorption");
            check(h, ally[0].getLastDamageSource() == previousSource, "Rejected friendly hit cannot replace attribution");
            aceDamage(h, shooter, enemy);
            pveUnchanged(h, shooter);
            // W267: exercise the shared ability scaling/real damage route, not every tuning row.
            noDefenses(enemy);
            var meleeId = DestinyGuardians.id("titan/arc_melee");
            float abilityHit = kim.biryeong.destiny.combat.AbilityDamage.pvp(meleeId, "strike", enemy, 6f);
            float abilityHealth = enemy.getHealth();
            Combat.damage(shooter, enemy, abilityHit, Element.ARC);
            near(h, abilityHealth - enemy.getHealth(), abilityHit, "Ability PvP contact reaches actual HP once");
            var sword = WeaponCatalog.find("abide_the_return").orElseThrow();
            float swordBase = WeaponProfile.forEntry(sword).damage();
            near(h, CrucibleDamage.melee(sword, enemy, swordBase * .35f),
                    CrucibleDamage.melee(sword, enemy, swordBase) * .35f,
                    "Sword energy multiplier survives PvP conversion");
            // W267: real PvP scorch stays non-lethal and does not add a second vanilla fire source.
            noDefenses(enemy);
            enemy.setRemainingFireTicks(0);
            enemy.setHealth(.2f);
            kim.biryeong.destiny.combat.Statuses.apply(enemy, kim.biryeong.destiny.combat.Keyword.WEAKENED, 40);
            kim.biryeong.destiny.combat.Statuses.scorch(shooter, enemy, 100);
            check(h, enemy.getRemainingFireTicks() == 0, "PvP scorch must not also ignite vanilla fire");
        });
        h.runAfterDelay(534, () -> {
            check(h, enemy.isAlive() && enemy.getHealth() >= .099f && enemy.getHealth() < .2f,
                    "Normalized scorch damages an enemy but preserves its last HP even when weakened");
            kim.biryeong.destiny.combat.Statuses.forget(enemy);
            enemy.setHealth(enemy.getMaxHealth());
        });
        h.runAfterDelay(560, () -> {
            check(h, shooter.isAlive() && enemy.isAlive() && CrucibleRuntime.canFight(enemy, shooter),
                    "Both players are alive and eligible before the only lethal transaction");
            check(h, ammo(h, shooter, sniper).total() == 0, "Spent special ammo stays empty until death");
            int before = CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(enemy));
            noDefenses(shooter);
            ItemStack[] diamond = {new ItemStack(Items.DIAMOND_HELMET), new ItemStack(Items.DIAMOND_CHESTPLATE),
                    new ItemStack(Items.DIAMOND_LEGGINGS), new ItemStack(Items.DIAMOND_BOOTS)};
            for (int i = 0; i < ARMOR.length; i++) shooter.setItemSlot(ARMOR[i], diamond[i]);
            shooter.getAttribute(Attributes.ARMOR).setBaseValue(20);
            shooter.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(8);
            check(h, shooter.getArmorValue() >= 20 && shooter.getAbsorptionAmount() == 0,
                    "Three-hit victim has diamond armor and no leftover absorption");
            var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
            var ballistics = CrucibleDamage.ballistics(ace, shooter, WeaponBallistics.of(ace));
            float base = CrucibleDamage.base(ace, shooter, WeaponProfile.forEntry(ace).damage());
            var box = shooter.getBoundingBox();
            var from = new Vec3(box.minX - 3, box.maxY - .1, (box.minZ + box.maxZ) / 2);
            var head = new Vec3(box.minX, from.y, from.z);
            check(h, WeaponPrecision.critical(shooter, from, head, ballistics.precision()),
                    "Lethal sequence uses classified player head contacts");
            float critical = ballistics.damage(base, 0, true);
            float fullHealth = shooter.getMaxHealth();
            check(h, critical * 2 < fullHealth && critical * 3 > fullHealth,
                    "Mapped Ace critical damage crosses full health on the third hit");
            // All three real transactions share one server tick: no food/recovery regeneration in between.
            for (int shot = 1; shot <= 3; shot++) {
                check(h, shooter.isAlive(), "Never forge damage attribution after a target has already died");
                boolean killed = Combat.damage(enemy.level(), enemy, shooter, critical, Element.KINETIC,
                        AmmoGeneration.weapon(ace));
                check(h, killed == (shot == 3), "Only the third immediate Ace headshot kills through diamond armor");
                near(h, shooter.getHealth(), Math.max(0, fullHealth - critical * shot),
                        "Actual armored health after Ace headshot " + shot);
            }
            check(h, shooter.isDeadOrDying(), "Third Ace headshot enters real death lifecycle");
            check(h, CrucibleAmmo.sharedPositions(enemy).isEmpty(), "Empty Special death creates no shared brick");
            crucibleSource(h, shooter, enemy);
            check(h, shooter.getLastHurtByPlayer() == enemy, "Lethal damage retains killer attribution");
            scoreAfterKill[0] = before + 1;
            check(h, CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(enemy)) == scoreAfterKill[0],
                    "Death callback awards exactly one kill");
            // Never call damage/hurtServer on this dead object again to forge a lethal source.
        });
        h.runAfterDelay(670, () -> {
            var next = server.getPlayerList().getPlayer(shooter.getUUID());
            check(h, next != null && next != shooter && next.isAlive(), "Runtime respawns a living replacement after five seconds");
            check(h, next.connection.getPlayer() == next, "Network listener owns the replacement player");
            check(h, CrucibleRuntime.participating(next) && CrucibleWorld.isArena(next.level()), "Respawn preserves membership and arena");
            check(h, TowerSpawnWorld.isSafeArrival(next.level(), next.position()), "Respawn lands on a safe arena floor");
            check(h, !CrucibleRuntime.canFight(enemy, next), "Respawn protection still rejects incoming damage");
            float hp = next.getHealth();
            check(h, !Combat.damage(enemy, next, 10000, Element.ARC), "Actual lethal request is rejected during respawn protection");
            near(h, next.getHealth(), hp, "Protected replacement keeps its HP");
            check(h, ammo(h, next, sniper).total() == 2, "Respawn grants two Special cartridges even after an empty death");
            check(h, CrucibleRuntime.snapshot().scores().get(CrucibleRuntime.team(enemy)) == scoreAfterKill[0],
                    "Respawn/protected damage cannot duplicate the kill score");
        });
        h.runAfterDelay(720, () -> {
            var next = server.getPlayerList().getPlayer(shooter.getUUID());
            check(h, next != null && next.isAlive() && CrucibleRuntime.canFight(enemy, next), "Replacement returns to combat after protection");
            check(h, ammo(h, next, sniper).total() == 2, "Subsequent ticks cannot duplicate the respawn allocation");
            // Actual Runtime hooks supplied the fresh life allocation; no manual arrive/died was used.
            for (var login : logins) {
                var current = server.getPlayerList().getPlayer(login.initial.getUUID());
                check(h, current != null && CrucibleRuntime.leave(current, true), "Every owned participant leaves normally");
                check(h, current.level() == tower && current.gameMode() == GameType.SURVIVAL, "Leave restores Tower and original mode");
            }
            check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Normal leave clears the owned match");
            h.succeed();
        });
    }

    static void moveFixture(GameTestHelper h, ServerPlayer p, Vec3 at) {
        check(h, p.teleportTo(p.level(), at.x, at.y, at.z, java.util.Set.of(), 0, 0, false),
                "Owned fixture teleport succeeds");
        p.setDeltaMovement(Vec3.ZERO);
        p.fallDistance = 0;
    }

    /** One paid PRIMARY kill, real pickups and real death/respawn; seeded health/ammo are fixture data. */
    @GameTest(structure = "destiny-test:floor", environment = "destiny-test:w90_isolated",
            maxTicks = 1200, manualOnly = true)
    public void runtimeDeathDropsRespawnAllocationsAndDisabledSpecialCrates(GameTestHelper h) {
        check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Extended fixture owns an empty singleton match");
        var defaults = CrucibleAmmoRules.Config.localDefaults();
        TestCleanup.register(h, () -> CrucibleAmmo.configure(defaults));
        CrucibleAmmo.configure(new CrucibleAmmoRules.Config(1, defaults.assist(), defaults.repeatCrateTicks(),
                defaults.assistTicks(), defaults.maxBricks(), defaults.heavyCrates()));
        var server = h.getLevel().getServer();
        var logins = new ArrayList<Login>();
        var shooter = login(h, logins, "W263Runtime", Element.SOLAR);
        var enemy = login(h, logins, "W263Target", Element.ARC);
        var sniper = WeaponCatalog.find("beloved").orElseThrow();
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        int sniperSlot = WeaponCharacteristics.of(sniper).slot().hotbar();
        int aceSlot = WeaponCharacteristics.of(ace).slot().hotbar();
        check(h, sniperSlot != aceSlot, "Primary and sniper occupy separate canonical slots");
        check(h, TowerSpawnWorld.teleport(shooter) && TowerSpawnWorld.teleport(enemy), "Both fixtures start in Tower");
        shooter.getInventory().setItem(sniperSlot, WeaponItems.create(sniper));
        shooter.getInventory().setItem(aceSlot, WeaponItems.create(ace));
        shooter.getInventory().setSelectedSlot(aceSlot);
        check(h, WeaponLoadout.equipHeld(shooter) == null, "Primary plus stowed sniper equipped before join");
        enemy.getInventory().setItem(sniperSlot, WeaponItems.create(sniper));
        enemy.getInventory().setSelectedSlot(sniperSlot);
        check(h, WeaponLoadout.equipHeld(enemy) == null, "Victim equips Special before joining");
        check(h, CrucibleRuntime.join(shooter) && CrucibleRuntime.join(enemy), "Both players join Control");
        Vec3[] deathPickup = new Vec3[1];
        h.onEachTick(() -> { for (var login : logins) tickLogin(server, login); });
        h.runAfterDelay(450, () -> {
            check(h, CrucibleRuntime.canFight(shooter, enemy), "Intro/protection complete before paid shot");
            check(h, ammo(h, shooter, sniper).total() == 2, "Initial Special allocation is two sniper rounds");
            var old = shooter.getInventory().getItem(sniperSlot);
            var fresh = WeaponItems.create(sniper);
            check(h, WeaponItems.magazine(fresh, WeaponProfile.forEntry(sniper)).total() > 1,
                    "Fresh item starts with a real PvE ammo pool before reconciliation");
            shooter.getInventory().setItem(sniperSlot, fresh);
            CrucibleAmmo.equipmentChanged(shooter);
            check(h, ammo(h, shooter, sniper).total() == 0
                            && WeaponItems.magazine(old, WeaponProfile.forEntry(sniper)).total() == 0,
                    "Actual item replacement clears new and removed finite pools");
            CrucibleAmmo.arrive(shooter, true);
            CrucibleAmmo.arrive(shooter, false);
            check(h, ammo(h, shooter, sniper).total() == 0, "Repeated fresh/arrival callbacks cannot refill replacement");
        });
        h.runAfterDelay(490, () -> {
            // Find a short walkable corridor in the existing arena; never edit arena blocks.
            Vec3 origin = shooter.position(), targetAt = null;
            for (var offset : List.of(new Vec3(3, 0, 0), new Vec3(-3, 0, 0),
                    new Vec3(0, 0, 3), new Vec3(0, 0, -3))) {
                Vec3 candidate = origin.add(offset);
                if (TowerSpawnWorld.isSafeArrival(shooter.level(), candidate)
                        && shooter.level().clip(new net.minecraft.world.level.ClipContext(shooter.getEyePosition(),
                        candidate.add(0, .9, 0), net.minecraft.world.level.ClipContext.Block.COLLIDER,
                        net.minecraft.world.level.ClipContext.Fluid.NONE, shooter)).getType()
                        == net.minecraft.world.phys.HitResult.Type.MISS) { targetAt = candidate; break; }
            }
            check(h, targetAt != null, "An existing safe three-block firing corridor is available");
            moveFixture(h, enemy, targetAt);
            noDefenses(enemy);
            enemy.setHealth(1); // Explicit low-health fixture; WeaponRuntime must cause the actual death.
            WeaponItems.save(enemy.getInventory().getItem(sniperSlot), new WeaponMagazine(WeaponProfile.forEntry(sniper), 0, 1));
            check(h, ammo(h, enemy, sniper).rounds() == 0 && ammo(h, enemy, sniper).reserve() == 1,
                    "Reserve-only Special must qualify for a death drop");
            Vec3 aim = enemy.getBoundingBox().getCenter().subtract(shooter.getEyePosition());
            float yaw = (float)Math.toDegrees(Math.atan2(-aim.x, aim.z));
            float pitch = (float)-Math.toDegrees(Math.atan2(aim.y, Math.sqrt(aim.x * aim.x + aim.z * aim.z)));
            WeaponAiming.cleanup(shooter);
            shooter.setShiftKeyDown(false);
            shooter.setYRot(yaw); shooter.setYHeadRot(yaw); shooter.setXRot(pitch);
            WeaponAiming.tick(shooter);
            shooter.getRandom().setSeed(0x5DEECE66DL);
            Vec3 from = shooter.getEyePosition(), to = from.add(WeaponAiming.direction(shooter).scale(6));
            var witness = net.minecraft.world.entity.projectile.ProjectileUtil.getEntityHitResult(shooter.level(),
                    shooter, from, to, new net.minecraft.world.phys.AABB(from, to).inflate(.23),
                    e -> Combat.isEnemy(shooter, e), .03f);
            check(h, witness != null && witness.getEntity() == enemy, "Paid ray preflight selects the intended enemy");
            deathPickup[0] = AmmoEconomy.safePosition(shooter.level(), enemy.position()).orElseThrow();
            var gun = shooter.getMainHandItem();
            int paidBefore = WeaponItems.magazine(gun, WeaponProfile.forEntry(ace)).rounds();
            shooter.getRandom().setSeed(0x5DEECE66DL);
            check(h, WeaponRuntime.beginUse(shooter), "Real WeaponRuntime accepts the primary trigger");
            WeaponRuntime.releaseUse(shooter, gun); shooter.stopUsingItem();
            check(h, WeaponItems.magazine(gun, WeaponProfile.forEntry(ace)).rounds() == paidBefore - 1,
                    "One actual runtime emission consumes exactly one primary round");
            check(h, enemy.isDeadOrDying(), "The paid runtime ray causes a real enemy death");
            crucibleSource(h, enemy, shooter);
            check(h, CrucibleAmmo.bricks(shooter) == 1, "Victim with reserve Special leaves one shared death shell");
            check(h, ammo(h, shooter, sniper).total() == 0, "Death shell requires physical pickup");
            CrucibleAmmo.died(enemy);
            check(h, CrucibleAmmo.bricks(shooter) == 1 && CrucibleAmmo.meter(shooter) == 0,
                    "Duplicate death and configured full kill credit cannot create another shell");
        });
        h.runAfterDelay(500, () -> moveFixture(h, shooter, deathPickup[0]));
        h.runAfterDelay(520, () -> {
            check(h, ammo(h, shooter, sniper).total() == 2 && CrucibleAmmo.bricks(shooter) == 0,
                    "Actual shared death-shell pickup grants two sniper rounds and consumes its shell");
        });
        h.runAfterDelay(640, () -> {
            var killer = server.getPlayerList().getPlayer(enemy.getUUID());
            check(h, killer != null && killer != enemy && killer.isAlive()
                    && CrucibleRuntime.canFight(killer, shooter), "Enemy has genuinely respawned before the next death");
            var stack = shooter.getInventory().getItem(sniperSlot);
            // Explicit positive-ammo fixture on an already recognized equipped item, not an earned-ammo claim.
            WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(sniper), 3, 6));
            check(h, ammo(h, shooter, sniper).total() == 9, "Positive-ammo death fixture explicitly seeds nine rounds");
            check(h, Combat.damage(killer, shooter, shooter.getHealth() + shooter.getAbsorptionAmount() + 1, Element.ARC),
                    "A living enemy causes the positive-ammo fixture's real death");
            crucibleSource(h, shooter, killer);
            check(h, ammo(h, shooter, sniper).total() == 0, "Death clears all nine before native copying");
            check(h, CrucibleAmmo.sharedPositions(killer).size() == 1, "Positive death leaves exactly one shared shell");
            moveFixture(h, killer, CrucibleAmmo.sharedPositions(killer).getFirst());
        });
        h.runAfterDelay(760, () -> {
            var next = server.getPlayerList().getPlayer(shooter.getUUID());
            check(h, next != null && next != shooter && next.isAlive() && CrucibleRuntime.participating(next),
                    "Runtime creates a living participating replacement");
            check(h, next.connection.getPlayer() == next && ammo(h, next, sniper).total() == 2,
                    "Native respawn grants exactly two fresh rounds");
            var remaining = ammo(h, next, sniper);
            if (remaining.rounds() < 2) remaining.reload();
            check(h, remaining.consume(2), "Explicit fixture consumes the fresh life allocation");
            WeaponItems.save(next.getInventory().getItem(sniperSlot), remaining);
            CrucibleAmmo.arrive(next, true);
            CrucibleAmmo.arrive(next, false);
            check(h, ammo(h, next, sniper).total() == 0, "Repeated arrive cannot refill spent respawn ammo");
        });
        h.runAfterDelay(1100, () -> {
            var next = server.getPlayerList().getPlayer(shooter.getUUID());
            check(h, CrucibleRuntime.snapshot().phaseTicks() >= CrucibleAmmoRules.FIRST_CRATE_TICKS,
                    "Actual match passes the old thirty-second Special crate boundary");
            check(h, CrucibleAmmo.bricks(next) == 0 && ammo(h, next, sniper).total() == 0
                            && CrucibleAmmo.meter(next) == 0,
                    "No timed Special crate, meter payout or remote refill after the consumed death shells");
            for (var login : logins) {
                var current = server.getPlayerList().getPlayer(login.initial.getUUID());
                check(h, current != null && CrucibleRuntime.leave(current, true), "Both lifecycle fixtures leave normally");
            }
            check(h, CrucibleRuntime.snapshot().members().isEmpty(), "Extended fixture clears its singleton match");
            h.succeed();
        });
    }
}
