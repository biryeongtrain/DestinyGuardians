package kim.biryeong.destiny.test;

import com.mojang.math.Transformation;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.IncomingDamageHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponMagazine;
import kim.biryeong.destiny.weapon.WeaponProfile;
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
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.players.PlayerList;
import net.minecraft.util.Brightness;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.gamerules.GameRules;
import net.minecraft.world.phys.Vec3;

import java.lang.reflect.Method;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;

/** Candidate W97 z0 contracts. Parent owns registry, integration, execution and actual pixel proof. */
public final class CriticalHudLayerW97GameTests {
    private static final String CRITICAL = IncomingDamageHud.PREFIX + "critical";
    private static final String ARC = IncomingDamageHud.PREFIX + "arc_0";
    private static final Brightness SOFT = new Brightness(2, 3);
    private static final Brightness ORDINARY = new Brightness(15, 15);
    private static final Brightness ABOVE_HAND = new Brightness(1, 2);
    private static final Method NATIVE_TRANSFORMATION = nativeTransformationMethod();

    private static void check(GameTestHelper h, boolean ok, String why) {
        h.assertTrue(ok, Component.literal(why));
    }

    private static void near(GameTestHelper h, double value, double expected, String why) {
        check(h, Math.abs(value - expected) < .0003, why + ": " + value + " != " + expected);
    }

    // javap of the installed 26.3 Display: no public getTransformation(). Use its exact native
    // SynchedEntityData -> Transformation reader, not guessed tracker indices or a fake client tick.
    private static Method nativeTransformationMethod() {
        try {
            var method = Display.class.getDeclaredMethod("createTransformation", SynchedEntityData.class);
            method.setAccessible(true);
            return method;
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("Installed native display transformation API changed", error);
        }
    }

    private static Transformation transformation(Display display) {
        try {
            return (Transformation) NATIVE_TRANSFORMATION.invoke(null, display.getEntityData());
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("Cannot read actual native display transformation", error);
        }
    }

    private static ItemDisplayHud node(GameTestHelper h, ServerPlayer player, String id) {
        var value = DisplayHud.getHud(player, id);
        check(h, value instanceof ItemDisplayHud, "Actual ItemDisplayHud exists: " + id);
        return (ItemDisplayHud) value;
    }

    @SuppressWarnings("unchecked")
    private static Map<UUID, ServerPlayer> playerLookup(GameTestHelper h) {
        try {
            var field = PlayerList.class.getDeclaredField("playersByUUID");
            field.setAccessible(true);
            return (Map<UUID, ServerPlayer>) field.get(h.getLevel().getServer().getPlayerList());
        } catch (ReflectiveOperationException error) {
            throw new AssertionError("W97 lookup-only HUD viewer", error);
        }
    }

    private static ItemStack weapon(String id, int rounds, int reserve) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponItems.create(entry);
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, reserve));
        return stack;
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<InventoryWireW92> wires = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h;
            created = h.getLevel().getServer().getTickCount();
            check(h, !h.getLevel().getGameRules().get(GameRules.SPAWN_MOBS), "W90 isolated spawning policy");
            check(h, DisplayHudManager.unitX == 100 && DisplayHudManager.unitY == 100
                            && DisplayHudManager.screenX == 1920 && DisplayHudManager.screenY == 1080
                            && DisplayHudManager.alignmentGap == 1_000_000,
                    "Existing DisplayHud screen/translation units remain unchanged");
            h.onEachTick(this::inside);
        }

        void inside() {
            var origin = h.absoluteVec(Vec3.ZERO);
            for (var wire : wires) {
                var p = wire.player;
                var box = p.getBoundingBox();
                check(h, p.level() == h.getLevel() && box.minX > origin.x && box.maxX < origin.x + 48
                                && box.minY > origin.y && box.maxY < origin.y + 12
                                && box.minZ > origin.z && box.maxZ < origin.z + 32,
                        "Whole lookup-only player stays inside its W90 48x12x32 footprint");
            }
        }

        InventoryWireW92 player(boolean guardianAndStowed) {
            var wire = new InventoryWireW92(h, new Vec3(8 + 12 * wires.size(), 4, 16));
            wires.add(wire); // W92 owns native channel cleanup, registered before listener construction.
            var p = wire.player;
            var lookup = playerLookup(h);
            TestCleanup.register(h, () -> {
                try { CombatHud.remove(p); }
                finally { lookup.remove(p.getUUID(), p); }
            });
            check(h, lookup.putIfAbsent(p.getUUID(), p) == null, "Unique lookup-only owner");
            p.getAttribute(Attributes.MAX_HEALTH).setBaseValue(20);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);
            p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            p.setYRot(0); p.setYHeadRot(0); p.setXRot(0);
            p.setHealth(20); p.setAbsorptionAmount(0);
            p.getInventory().setItem(0, weapon("ace_of_spades", 13, 0));
            p.getInventory().setSelectedSlot(0);
            p.setAttached(WeaponLoadout.ENABLED, guardianAndStowed);
            if (guardianAndStowed) {
                p.getInventory().setItem(1, weapon("nezarec_s_whisper", 6, 12));
                p.getInventory().setItem(2, weapon("bad_omens", 1, 4));
                Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
                Guardians.data(p).setLoadout(GuardianClass.HUNTER, HunterAbilities.preset(Element.SOLAR));
            }
            inside();
            wire.discard();
            return wire;
        }

        void at(int ticks, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created, "Register deadlines only at creation");
            h.runAfterDelay(ticks, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == ticks, "Exact real tick " + ticks);
                inside();
                action.run();
            });
        }
    }

    /** Reconstruct native item displays from the unchanged W92 actual PLAY encoder/decoder. */
    private static final class ClientView {
        final Map<Integer, Display.ItemDisplay> displays = new HashMap<>();
        Set<Integer> added = Set.of(), removed = Set.of(), dataIds = Set.of();

        void read(ServerPlayer owner, List<Packet<?>> packets) {
            var adds = new HashSet<Integer>();
            var removals = new HashSet<Integer>();
            var updates = new HashSet<Integer>();
            for (var packet : packets) {
                if (packet instanceof ClientboundAddEntityPacket add && add.getType() == EntityTypes.ITEM_DISPLAY) {
                    displays.put(add.getId(), new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY, owner.level()));
                    adds.add(add.getId());
                } else if (packet instanceof ClientboundSetEntityDataPacket data) {
                    var display = displays.get(data.id());
                    if (display != null) {
                        display.getEntityData().assignValues(data.packedItems());
                        updates.add(data.id());
                    }
                } else if (packet instanceof ClientboundRemoveEntitiesPacket remove) {
                    for (int id : remove.entityIds()) { displays.remove(id); removals.add(id); }
                }
            }
            added = Set.copyOf(adds); removed = Set.copyOf(removals); dataIds = Set.copyOf(updates);
        }
    }

    private static Map<String, Integer> layers(boolean extended, boolean arc) {
        var result = new LinkedHashMap<String, Integer>();
        result.put(AmmoHud.PREFIX + "panel", 1);
        result.put(AmmoHud.PREFIX + "weapon", 2);
        result.put(AmmoHud.PREFIX + "rounds_0", 3);
        result.put(AmmoHud.PREFIX + "rounds_1", 3);
        result.put(AmmoHud.PREFIX + "infinity", 3);
        result.put(CombatHud.HEALTH_ID + "_track", 1);
        result.put(CombatHud.HEALTH_ID, 2);
        result.put(WeaponReticleHud.FRAME_ID, 5);
        result.put(WeaponReticleHud.CENTER_ID, 6);
        if (arc) result.put(ARC, 7);
        if (extended) {
            for (int i = 0; i < 2; i++) {
                result.put(AmmoHud.PREFIX + "stowed_" + i + "_panel", 1);
                result.put(AmmoHud.PREFIX + "stowed_" + i + "_weapon", 2);
                result.put(AmmoHud.PREFIX + "stowed_" + i + "_total_0", 3);
                if (i == 0) result.put(AmmoHud.PREFIX + "stowed_0_total_1", 3);
            }
            for (int i = 0; i < 3; i++) {
                String id = CombatHud.ABILITIES_ID + (i == 0 ? "" : "_" + i);
                result.put(id, 1); result.put(id + "_icon", 2); result.put(id + "_charge", 2);
            }
        }
        return result;
    }

    private static void nativeNode(GameTestHelper h, ServerPlayer owner, ItemDisplayHud hud, ClientView view) {
        var client = view.displays.get(hud.getEntityId());
        check(h, client != null, "Decoded native spawn exists: " + hud.getId());
        check(h, owner.level().getEntity(hud.getEntityId()) == null, "HUD remains client-only");
        var actual = transformation(client);
        check(h, actual.equals(transformation(hud.getDisplay())), "Wire transformation equals native source: " + hud.getId());
        // Independent screen->native translation calculation for actual PAPER HUD quads.
        check(h, hud.getItem().is(Items.PAPER), "Expected unchanged paper quad carrier");
        near(h, actual.translation().x(), (960 - hud.getLocation().x) * 100, "Native screen X");
        float y = (float) (-1_500_000 - .178 + (540 - hud.getLocation().y) * 100);
        y -= hud.getAlignmentInt();
        near(h, actual.translation().y(), y, "Native alignment Y");
        near(h, actual.translation().z(), 100 * hud.getScale().z / 32 - hud.getLocation().z * 100, "Native layer Z");
        check(h, ItemStack.matches(client.getItemStack(), hud.getItem())
                        && client.getItemTransform() == ItemDisplayContext.NONE,
                "Wire model/color/components and item context unchanged: " + hud.getId());
        boolean aboveHand = hud.getId().equals(WeaponReticleHud.FRAME_ID)
                || hud.getId().equals(WeaponReticleHud.CENTER_ID);
        check(h, hud.isAboveHand() == aboveHand, "Only actual reticle controls use above-hand in empty-offhand fixture");
        var expected = hud.getId().equals(CRITICAL) ? SOFT : aboveHand ? ABOVE_HAND : ORDINARY;
        check(h, expected.equals(client.getBrightnessOverride())
                        && expected.equals(hud.getDisplay().getBrightnessOverride()),
                "Decoded brightness preserves selective/ordinary/above-hand path: " + hud.getId());
        check(h, hud.getBrightnessBlock() == (hud.getId().equals(CRITICAL) ? 2 : 15)
                        && hud.getBrightnessSky() == (hud.getId().equals(CRITICAL) ? 3 : 15),
                "Stored ordinary brightness never acquires critical marker");
    }

    private static void ammo(GameTestHelper h, ServerPlayer p, ItemStack original, ItemStack before) {
        check(h, p.getMainHandItem() == original && ItemStack.matches(original, before),
                "Exact selected Ace object and every canonical component remain unchanged");
        var state = AmmoHud.current(p).orElseThrow();
        check(h, state.family().equals("hand_cannon") && state.rounds() == 13 && state.reserve() == 0
                        && !state.reloading() && !state.superWeapon(), "Actual selected Ace remains 13/0, no reload/super");
        for (int i = 0; i < 2; i++) check(h, Identifier.parse("destiny:gui/hud/ammo_digit_" + (i == 0 ? 1 : 3))
                        .equals(node(h, p, AmmoHud.PREFIX + "rounds_" + i).getItem().get(DataComponents.ITEM_MODEL)),
                "Actual ammo glyphs remain one/three");
        if (WeaponLoadout.enabled(p)) {
            var equipped = WeaponLoadout.equipped(p);
            check(h, equipped.size() == 3, "Stowed rows come from actual three-slot inventory");
            for (int i = 1; i <= 2; i++) {
                var stack = p.getInventory().getItem(i);
                var entry = WeaponItems.entry(stack).orElseThrow();
                var magazine = WeaponItems.magazine(stack, WeaponProfile.forEntry(entry));
                check(h, entry.id().equals(i == 1 ? "nezarec_s_whisper" : "bad_omens")
                                && magazine.rounds() == (i == 1 ? 6 : 1) && magazine.reserve() == (i == 1 ? 12 : 4),
                        "Actual stowed magazines remain unchanged");
                check(h, Identifier.parse("destiny:gui/hud/ammo_weapon_w112_" + entry.id()).equals(
                                node(h, p, AmmoHud.PREFIX + "stowed_" + (i - 1) + "_weapon").getItem().get(DataComponents.ITEM_MODEL)),
                        "Stowed silhouette is the actual inventory weapon, not just its family");
            }
            for (var glyph : Map.of("stowed_0_total_0", 1, "stowed_0_total_1", 8, "stowed_1_total_0", 5).entrySet())
                check(h, Identifier.parse("destiny:gui/hud/ammo_digit_" + glyph.getValue()).equals(
                                node(h, p, AmmoHud.PREFIX + glyph.getKey()).getItem().get(DataComponents.ITEM_MODEL)),
                        "Actual stowed total glyph: " + glyph.getKey());
        }
    }

    private static int active(GameTestHelper h, ServerPlayer p, ItemDisplayHud cached,
                              ClientView view, Map<String, Integer> foreground) {
        check(h, node(h, p, CRITICAL) == cached && !cached.isRemoved(), "Pulse reuses exact critical entity");
        check(h, cached.getLocation().x == 960 && cached.getLocation().y == 540 && cached.getLocation().z == 0
                        && cached.getScale().x == 1920 && cached.getScale().y == 1080 && cached.getScale().z == 1
                        && cached.getAlignment() == DisplayHud.HudAlignment.CENTER && !cached.isAboveHand(),
                "Only critical depth becomes literal layer0; geometry/alignment/ordinary path unchanged");
        long tick = p.level().getServer().getTickCount();
        double severity = 1 - (p.getHealth() / p.getMaxHealth()) / .30f;
        double pulse = Math.sin(Math.floorMod(tick / 2, 12) * Math.PI / 6);
        int frame = Math.clamp((int) Math.round(7 * (.25 + .55 * severity + .20 * pulse)), 0, 7);
        check(h, Identifier.parse("destiny:gui/hud/incoming_w89_critical_" + frame)
                        .equals(cached.getItem().get(DataComponents.ITEM_MODEL))
                        && cached.getItem().get(DataComponents.CUSTOM_MODEL_DATA).colors().equals(List.of(0xB52B25)),
                "Exact W89 real two-tick model bank/formula and tint retained");
        nativeNode(h, p, cached, view);
        double criticalZ = transformation(view.displays.get(cached.getEntityId())).translation().z();
        near(h, criticalZ, 3.125, "Actual decoded layer0 native translation");
        for (var entry : foreground.entrySet()) {
            var hud = node(h, p, entry.getKey());
            check(h, hud.getLocation().z == entry.getValue() && 0 < hud.getLocation().z,
                    "Critical literal layer0 strictly below foreground logical layer: " + entry.getKey());
            nativeNode(h, p, hud, view);
            double foregroundZ = transformation(view.displays.get(hud.getEntityId())).translation().z();
            check(h, criticalZ > foregroundZ && .5 - criticalZ / 2_000_000 < .5 - foregroundZ / 2_000_000,
                    "Decoded translation/reverse-Z ordering agrees, not a compositor-pixel proof");
        }
        check(h, node(h, p, WeaponReticleHud.CENTER_ID).isAboveHand(), "Actual reticle exercises separate 1/2 above-hand marker");
        for (var entry : DisplayHud.getHuds(p).entrySet()) if (!entry.getKey().equals(CRITICAL)) {
            var hud = entry.getValue();
            check(h, !SOFT.equals(hud.getDisplay().getBrightnessOverride())
                            && !(hud.getBrightnessBlock() == 2 && hud.getBrightnessSky() == 3),
                    "Critical marker never leaks to ordinary or above-hand HUD: " + entry.getKey());
        }
        return frame;
    }

    private static void resend(GameTestHelper h, InventoryWireW92 wire, ClientView view, List<ItemDisplayHud> nodes) {
        var before = new HashMap<Integer, Transformation>();
        for (var hud : nodes) before.put(hud.getEntityId(), transformation(view.displays.get(hud.getEntityId())));
        DisplayHudManager.resend(wire.player);
        view.read(wire.player, wire.capture());
        for (var hud : nodes) {
            check(h, view.added.contains(hud.getEntityId()) && view.dataIds.contains(hud.getEntityId()),
                    "Resend actually supplies native spawn and metadata, never stale reconstructed state");
            nativeNode(h, wire.player, hud, view);
            check(h, before.get(hud.getEntityId()).equals(transformation(view.displays.get(hud.getEntityId())))
                            && DisplayHud.getHud(wire.player, hud.getId()) == hud && !hud.isRemoved(),
                    "Actual native transformation and cached object/entity unchanged across resend");
        }
    }

    @GameTest(structure = "destiny-test:w78_floor", maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void selectedAceNativeDepthAndMarkerSurviveThresholdsAndActualResend(GameTestHelper h) {
        var f = new Fixture(h); var wire = f.player(false); var p = wire.player;
        var original = p.getMainHandItem(); var before = original.copy(); var view = new ClientView();
        CombatHud.update(p); view.read(p, wire.capture());
        check(h, DisplayHud.getHud(p, CRITICAL) == null, "HP20 begins without critical plane");
        var ordinary = layers(false, false).keySet().stream().map(id -> node(h, p, id)).toList();
        ordinary.forEach(hud -> nativeNode(h, p, hud, view)); ammo(h, p, original, before);
        p.damageCooldownTime = 0;
        var source = new DamageSource(p.damageSources().generic().typeHolder(), p.position().add(0, 0, 4));
        check(h, p.hurtServer(p.level(), source, 14) && p.getHealth() == 6, "Actual HP20->6 loss creates directional arc");
        CombatHud.update(p); view.read(p, wire.capture());
        var critical = node(h, p, CRITICAL);
        check(h, view.added.contains(critical.getEntityId()) && view.dataIds.contains(critical.getEntityId()), "Critical initial encoded spawn/metadata");
        var foreground = layers(false, true);
        active(h, p, critical, view, foreground);
        var all = new ArrayList<>(ordinary); all.add(node(h, p, ARC)); all.add(critical);
        resend(h, wire, view, all); active(h, p, critical, view, foreground);
        p.setHealth(1); CombatHud.update(p); view.read(p, wire.capture());
        active(h, p, critical, view, foreground); ammo(h, p, original, before);
        resend(h, wire, view, all); active(h, p, critical, view, foreground);
        p.setHealth(7); CombatHud.update(p); view.read(p, wire.capture());
        check(h, DisplayHud.getHud(p, CRITICAL) == null && critical.isRemoved()
                        && view.removed.contains(critical.getEntityId()) && !view.displays.containsKey(critical.getEntityId()),
                "HP7 recovery removes exact critical entity on actual client wire");
        for (var hud : ordinary) check(h, node(h, p, hud.getId()) == hud && !hud.isRemoved()
                        && !view.removed.contains(hud.getEntityId()), "Recovery preserves ordinary cached entities");
        resend(h, wire, view, ordinary); ammo(h, p, original, before);
        p.setHealth(1); CombatHud.update(p); view.read(p, wire.capture());
        var fresh = node(h, p, CRITICAL);
        check(h, fresh != critical && fresh.getEntityId() != critical.getEntityId(), "Next episode never resurrects removed cache");
        active(h, p, fresh, view, foreground); ammo(h, p, original, before);
        h.succeed();
    }

    @GameTest(structure = "destiny-test:w78_floor", maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void realPulseKeepsSelectedStowedAndAbilityHudAboveCriticalOnNativeWire(GameTestHelper h) {
        var f = new Fixture(h);
        var views = new ArrayList<ClientView>(); var cached = new ArrayList<ItemDisplayHud>();
        var originals = new ArrayList<ItemStack>(); var snapshots = new ArrayList<ItemStack>();
        var ordinary = new ArrayList<List<ItemDisplayHud>>(); var frames = new HashSet<Integer>();
        var foreground = layers(true, false);
        for (int i = 0; i < 2; i++) {
            var wire = f.player(true); var p = wire.player; var view = new ClientView();
            originals.add(p.getMainHandItem()); snapshots.add(p.getMainHandItem().copy());
            CombatHud.update(p); view.read(p, wire.capture());
            check(h, p.getHealth() == 20 && DisplayHud.getHud(p, CRITICAL) == null, "Independent HP20 healthy baseline");
            p.setHealth(i == 0 ? 6 : 1); CombatHud.update(p); view.read(p, wire.capture());
            var critical = node(h, p, CRITICAL);
            check(h, view.added.contains(critical.getEntityId()) && view.dataIds.contains(critical.getEntityId()), "Initial encoded critical entity");
            views.add(view); cached.add(critical);
            ordinary.add(foreground.keySet().stream().map(id -> node(h, p, id)).toList());
            active(h, p, critical, view, foreground); ammo(h, p, originals.get(i), snapshots.get(i));
        }
        for (int t = 1; t <= 24; t++) {
            final int tick = t;
            f.at(t, () -> {
                for (int i = 0; i < 2; i++) {
                    var wire = f.wires.get(i); var p = wire.player; var view = views.get(i);
                    CombatHud.update(p); view.read(p, wire.capture());
                    check(h, p.getHealth() == (i == 0 ? 6 : 1), "Pulse observes, never changes actual HP");
                    for (var hud : ordinary.get(i)) check(h, node(h, p, hud.getId()) == hud
                                    && !view.added.contains(hud.getEntityId()) && !view.removed.contains(hud.getEntityId()),
                            "Actual pulse never respawns/removes ordinary selected/stowed/ability entity");
                    check(h, !view.added.contains(cached.get(i).getEntityId()) && !view.removed.contains(cached.get(i).getEntityId()), "Critical pulse never respawns");
                    frames.add(active(h, p, cached.get(i), view, foreground));
                    ammo(h, p, originals.get(i), snapshots.get(i));
                    if (tick == 12 || tick == 24) {
                        var all = new ArrayList<>(ordinary.get(i)); all.add(cached.get(i));
                        resend(h, wire, view, all); active(h, p, cached.get(i), view, foreground);
                    }
                }
            });
        }
        f.at(25, () -> {
            check(h, frames.equals(Set.of(0, 1, 2, 3, 4, 5, 6)), "HP6/1 full real pulse retains exact W89 bank0..6 coverage");
            for (int i = 0; i < 2; i++) {
                var wire = f.wires.get(i); var p = wire.player; var view = views.get(i);
                p.setHealth(7); CombatHud.update(p); view.read(p, wire.capture());
                check(h, DisplayHud.getHud(p, CRITICAL) == null && cached.get(i).isRemoved()
                                && view.removed.contains(cached.get(i).getEntityId()), "Threshold recovery retires encoded critical plane");
                for (var hud : ordinary.get(i)) check(h, node(h, p, hud.getId()) == hud && !hud.isRemoved(), "Ordinary cache survives recovery");
                resend(h, wire, view, ordinary.get(i)); ammo(h, p, originals.get(i), snapshots.get(i));
            }
            h.succeed();
        });
    }
}
