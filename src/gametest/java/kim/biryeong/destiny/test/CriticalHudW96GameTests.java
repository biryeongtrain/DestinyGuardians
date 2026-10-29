package kim.biryeong.destiny.test;

import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.IncomingDamageHud;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.DisplayHudManager;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.ClientboundAddEntityPacket;
import net.minecraft.network.protocol.game.ClientboundRemoveEntitiesPacket;
import net.minecraft.network.protocol.game.ClientboundSetEntityDataPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.util.Brightness;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** W96 selective HUD marker/state and native outbound metadata; not shader or visual proof.
 * Registration and execution belong to the parent. Existing W89 tests remain independent.
 */
public final class CriticalHudW96GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String CRITICAL = IncomingDamageHud.PREFIX + "critical";
    private static final String ARC = IncomingDamageHud.PREFIX + "arc_0";
    private static final Brightness SOFT = new Brightness(2, 3);
    private static final Brightness ORDINARY = new Brightness(15, 15);

    private static void check(GameTestHelper h, boolean value, String reason) {
        h.assertTrue(value, Component.literal(reason));
    }

    private static ItemDisplayHud node(GameTestHelper h, ServerPlayer player, String id) {
        var hud = DisplayHud.getHud(player, id);
        check(h, hud instanceof ItemDisplayHud, "Native item HUD exists: " + id);
        return (ItemDisplayHud) hud;
    }

    private static void marker(GameTestHelper h, ItemDisplayHud hud, boolean critical) {
        var expected = critical ? SOFT : ORDINARY;
        check(h, hud.getBrightnessBlock() == (critical ? 2 : 15)
                        && hud.getBrightnessSky() == (critical ? 3 : 15)
                        && expected.equals(hud.getDisplay().getBrightnessOverride()),
                "Stored and actual native brightness agree: " + expected);
        check(h, !hud.isAboveHand(), "Center critical/arc/vitals do not acquire the above-hand path");
    }

    private static void selective(GameTestHelper h, ServerPlayer player) {
        marker(h, node(h, player, CRITICAL), true);
        for (var entry : DisplayHud.getHuds(player).entrySet()) {
            if (!entry.getKey().equals(CRITICAL))
                check(h, !SOFT.equals(entry.getValue().getDisplay().getBrightnessOverride())
                                && !(entry.getValue().getBrightnessBlock() == 2
                                && entry.getValue().getBrightnessSky() == 3),
                        "Critical marker never leaks to other HUD: " + entry.getKey());
        }
        marker(h, node(h, player, CombatHud.HEALTH_ID + "_track"), false);
        marker(h, node(h, player, CombatHud.HEALTH_ID), false);
    }

    private static void modelAndPlacement(GameTestHelper h, ServerPlayer player, ItemDisplayHud hud) {
        long now = player.level().getServer().getTickCount();
        double severity = 1 - (player.getHealth() / player.getMaxHealth()) / .30f;
        double pulse = Math.sin(Math.floorMod(now / 2, 12) * Math.PI / 6);
        int frame = Math.clamp((int) Math.round(7 * (.25 + .55 * severity + .20 * pulse)), 0, 7);
        check(h, Identifier.parse("destiny:gui/hud/incoming_w89_critical_" + frame)
                        .equals(hud.getItem().get(DataComponents.ITEM_MODEL)),
                "Marker uses the existing W89 bank and real two-tick server pulse");
        check(h, hud.getAlignment() == DisplayHud.HudAlignment.CENTER
                        && hud.getLocation().x == 960 && hud.getLocation().y == 540 && hud.getLocation().z == 0 /* W99: exact critical-layer contract migration; other geometry unchanged */
                        && hud.getScale().x == 1920 && hud.getScale().y == 1080,
                "Selective shader marker changes neither full-screen placement nor arc ordering");
    }

    /** Same lookup-only seam as W76: no world-ticked player or extra connection implementation. */
    @SuppressWarnings("unchecked")
    private static Map<UUID, ServerPlayer> playerLookup(GameTestHelper h) {
        try {
            var field = PlayerList.class.getDeclaredField("playersByUUID");
            field.setAccessible(true);
            return (Map<UUID, ServerPlayer>) field.get(h.getLevel().getServer().getPlayerList());
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("W96 embedded HUD viewer lookup", error);
        }
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h;
            created = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS),
                    "Existing W90 isolated environment disables natural spawning before setup");
            h.onEachTick(this::inside);
        }

        void inside() {
            var origin = h.absoluteVec(Vec3.ZERO);
            for (var wire : wires) {
                var player = wire.player;
                var box = player.getBoundingBox();
                check(h, player.level() == h.getLevel()
                                && box.minX > origin.x && box.maxX < origin.x + 48
                                && box.minY > origin.y && box.maxY < origin.y + 12
                                && box.minZ > origin.z && box.maxZ < origin.z + 32,
                        "Entire lookup-only owner stays inside its W90 48x12x32 footprint");
            }
        }

        InventoryWireW92 player(float hp, float absorption) {
            var wire = new InventoryWireW92(h, new Vec3(8 + 12 * wires.size(), 4, 16));
            wires.add(wire); // W92 registers channel cleanup before constructing its listener.
            var player = wire.player;
            var lookup = playerLookup(h);
            // Runs before W92 closes its channel; remove only this exact UUID/object on every terminal path.
            TestCleanup.register(h, () -> {
                try { CombatHud.remove(player); }
                finally { lookup.remove(player.getUUID(), player); }
            });
            check(h, lookup.putIfAbsent(player.getUUID(), player) == null, "Unique fixture HUD viewer");
            player.setAttached(WeaponLoadout.ENABLED, false);
            player.getAttribute(Attributes.MAX_HEALTH).setBaseValue(20);
            player.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
            player.getAttribute(Attributes.ARMOR).setBaseValue(0);
            player.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            player.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            player.setYRot(0); player.setYHeadRot(0); player.setXRot(0);
            player.setHealth(hp); player.setAbsorptionAmount(absorption);
            inside();
            wire.discard();
            return wire;
        }

        void at(int delay, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created,
                    "All deadlines register at fixture creation, not inside delayed callbacks");
            h.runAfterDelay(delay, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == delay,
                        "Real server-tick deadline " + delay);
                inside();
                action.run();
            });
        }
    }

    private static void nativeHit(GameTestHelper h, ServerPlayer player) {
        player.damageCooldownTime = 0;
        var source = new DamageSource(player.damageSources().generic().typeHolder(),
                player.position().add(0, 0, 4));
        check(h, player.hurtServer(player.level(), source, 1) && player.getHealth() == 6,
                "Positioned native HP loss reaches six and supplies an actual directional cue");
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void criticalWashMarkerLeavesDirectionalArcAndCombatSpritesOrdinary(GameTestHelper h) {
        var fixture = new Fixture(h);
        var player = fixture.player(7, 0).player;
        nativeHit(h, player);
        player.setAbsorptionAmount(4);
        CombatHud.update(player);
        selective(h, player);
        marker(h, node(h, player, ARC), false);
        marker(h, node(h, player, CombatHud.ABSORPTION_ID), false);
        var critical = node(h, player, CRITICAL);
        modelAndPlacement(h, player, critical);
        var arc = node(h, player, ARC);
        check(h, arc.getLocation().z == 7 && arc.getLocation().z > critical.getLocation().z
                        && Identifier.parse("destiny:gui/hud/incoming_w86_arc_0")
                        .equals(arc.getItem().get(DataComponents.ITEM_MODEL)),
                "Existing W86 directional arc remains ordinary and above W89 critical");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void cachedCriticalMarkerSurvivesPulseAndThresholdRecovery(GameTestHelper h) {
        var fixture = new Fixture(h);
        float[] hp = {6, 5, 1};
        float[] absorption = {20, 4, 0};
        var cached = new ArrayList<ItemDisplayHud>();
        var ordinary = new ArrayList<ItemDisplayHud>();
        var models = new HashSet<Identifier>();
        for (int i = 0; i < hp.length; i++) {
            var player = fixture.player(hp[i], absorption[i]).player;
            CombatHud.update(player);
            cached.add(node(h, player, CRITICAL));
            ordinary.add(node(h, player, CombatHud.HEALTH_ID + "_track"));
        }
        for (int t = 1; t <= 24; t++) fixture.at(t, () -> {
            for (int i = 0; i < hp.length; i++) {
                var player = fixture.wires.get(i).player;
                var old = cached.get(i);
                CombatHud.update(player);
                var current = node(h, player, CRITICAL);
                check(h, current == old && current.getEntityId() == old.getEntityId() && !old.isRemoved(),
                        "Every pulse frame reuses the exact marked entity");
                selective(h, player);
                modelAndPlacement(h, player, current);
                models.add(current.getItem().get(DataComponents.ITEM_MODEL));
                check(h, player.getHealth() == hp[i] && player.getAbsorptionAmount() == absorption[i],
                        "Pulse and marker changes never spend or invent HP/absorption");
            }
        });
        fixture.at(25, () -> {
            var expected = new HashSet<Identifier>();
            for (int i = 0; i <= 6; i++) expected.add(Identifier.parse("destiny:gui/hud/incoming_w89_critical_" + i));
            check(h, models.equals(expected), "HP6/5/1 cover exactly W89 frames 0..6 across a full real pulse");
            for (int i = 0; i < hp.length; i++) {
                var player = fixture.wires.get(i).player;
                player.setHealth(7);
                CombatHud.update(player);
                check(h, DisplayHud.getHud(player, CRITICAL) == null && cached.get(i).isRemoved(),
                        "HP7 recovery retires the marked cached node");
                check(h, node(h, player, CombatHud.HEALTH_ID + "_track") == ordinary.get(i),
                        "Recovery preserves the ordinary combat sprite identity");
                marker(h, ordinary.get(i), false);
                player.setHealth(hp[i]);
                CombatHud.update(player);
                var fresh = node(h, player, CRITICAL);
                check(h, fresh != cached.get(i) && fresh.getEntityId() != cached.get(i).getEntityId(),
                        "New low-health episode gets a fresh entity, never resurrects the removed cache");
                selective(h, player);
                modelAndPlacement(h, player, fresh);
            }
            h.succeed();
        });
    }

    private static Display.ItemDisplay decoded(GameTestHelper h, ServerPlayer owner,
                                                ItemDisplayHud hud, List<Packet<?>> packets) {
        check(h, packets.stream().anyMatch(packet -> packet instanceof ClientboundAddEntityPacket add
                        && add.getId() == hud.getEntityId() && add.getType() == EntityTypes.ITEM_DISPLAY),
                "Actual encoded native spawn exists for this item-display entity");
        // No guessed metadata IDs: native defaults plus actual decoded updates reconstruct the display.
        var display = new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, owner.level());
        int updates = 0;
        for (var packet : packets) {
            if (packet instanceof ClientboundSetEntityDataPacket data && data.id() == hud.getEntityId()) {
                display.getEntityData().assignValues(data.packedItems());
                updates++;
            }
        }
        check(h, updates > 0, "At least one outbound native metadata update was decoded");
        check(h, owner.level().getEntity(hud.getEntityId()) == null,
                "Personal HUD stays client-only, never a level entity");
        return display;
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void outboundNativeDisplayMetadataPreservesSelectiveMarkerOnResend(GameTestHelper h) {
        var fixture = new Fixture(h);
        var wire = fixture.player(7, 0);
        var player = wire.player;
        nativeHit(h, player);
        CombatHud.update(player);
        var critical = node(h, player, CRITICAL);
        var arc = node(h, player, ARC);
        var health = node(h, player, CombatHud.HEALTH_ID);
        for (int pass = 0; pass < 2; pass++) {
            if (pass == 1) DisplayHudManager.resend(player);
            var packets = wire.capture();
            check(h, SOFT.equals(decoded(h, player, critical, packets).getBrightnessOverride()),
                    "Actual clientbound metadata delivers block2/sky3 for critical, including resend");
            for (var ordinary : List.of(arc, health))
                check(h, ORDINARY.equals(decoded(h, player, ordinary, packets).getBrightnessOverride()),
                        "Actual arc/vitals metadata stays block15/sky15, including resend");
            selective(h, player);
            check(h, node(h, player, CRITICAL) == critical && node(h, player, ARC) == arc
                            && node(h, player, CombatHud.HEALTH_ID) == health,
                    "Resend keeps every exact cached HUD object/entity");
        }
        for (int i = 0; i < 8; i++) CombatHud.update(player);
        Set<Integer> ids = Set.of(critical.getEntityId(), arc.getEntityId(), health.getEntityId());
        check(h, wire.capture().stream().noneMatch(packet ->
                        packet instanceof ClientboundSetEntityDataPacket data && ids.contains(data.id())
                        || packet instanceof ClientboundAddEntityPacket add && ids.contains(add.getId())
                        || packet instanceof ClientboundRemoveEntitiesPacket remove
                        && remove.entityIds().intStream().anyMatch(ids::contains)),
                "Repeated same-tick cached updates cause no marker resend, respawn or removal");
        h.succeed();
    }
}
