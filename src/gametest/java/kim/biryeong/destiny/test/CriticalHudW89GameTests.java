package kim.biryeong.destiny.test;

import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.IncomingDamageHud;
import kim.biryeong.destiny.hud.IncomingDamageState;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/** Native state/model contracts only; the parent owns registration and native pixel evidence. */
public final class CriticalHudW89GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final String CRITICAL = IncomingDamageHud.PREFIX + "critical";

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < .0003, message + ": expected=" + expected + " actual=" + actual);
    }

    private static Set<String> incoming(ServerPlayer p) {
        return DisplayHud.getHuds(p).keySet().stream().filter(k -> k.startsWith(IncomingDamageHud.PREFIX))
                .collect(Collectors.toSet());
    }

    private static ItemDisplayHud node(GameTestHelper h, ServerPlayer p, String key) {
        var value = DisplayHud.getHud(p, key);
        check(h, value instanceof ItemDisplayHud, "Actual native item HUD exists: " + key);
        return (ItemDisplayHud) value;
    }

    private static int expectedFrame(long tick, float hp, float maxHp) {
        double severity = 1 - (hp / maxHp) / .30f;
        double pulse = Math.sin(Math.floorMod(tick / 2, 12) * Math.PI / 6);
        return Math.clamp((int) Math.round(7 * (.25 + .55 * severity + .20 * pulse)), 0, 7);
    }

    private static int active(GameTestHelper h, ServerPlayer p, ItemDisplayHud cached, int entityId,
                              float hp, float absorption) {
        near(h, p.getHealth(), hp, "Observation preserves actual HP");
        near(h, p.getAbsorptionAmount(), absorption, "Observation preserves native absorption");
        var current = node(h, p, CRITICAL);
        check(h, current == cached && current.getEntityId() == entityId, "Exact cached critical node survives pulse");
        long tick = p.level().getServer().getTickCount();
        int expected = expectedFrame(tick, hp, p.getMaxHealth());
        check(h, IncomingDamageState.criticalFrame(tick, hp / p.getMaxHealth()) == expected,
                "Existing eight-frame formula/clock remains unchanged");
        var model = current.getItem().get(DataComponents.ITEM_MODEL);
        check(h, Identifier.fromNamespaceAndPath("destiny", "gui/hud/incoming_w89_critical_" + expected).equals(model),
                "Every selected tick has the exact active W89 model, never empty/old bank: " + model);
        near(h, current.getScale().x, 1920, "Full screen width");
        near(h, current.getScale().y, 1080, "Full screen height");
        near(h, current.getLocation().x, 960, "Screen center X");
        near(h, current.getLocation().y, 540, "Screen center Y");
        near(h, current.getLocation().z, 0, "W99 critical layer remains behind ordinary foreground HUD and incoming arcs");
        check(h, current.getAlignment() == DisplayHud.HudAlignment.CENTER, "Centered full screen plane");
        return expected;
    }

    /** Uses the existing TestPlayers native connection, without another connection fixture. */
    private static final class Fixture {
        final GameTestHelper h;
        final long createdAt;
        final List<ServerPlayer> players = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h;
            createdAt = h.getLevel().getServer().getTickCount();
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            TestCleanup.register(h, () -> {
                for (var p : players) {
                    p.setServerLevel(h.getLevel());
                    IncomingDamageHud.cleanup(p);
                    CombatHud.remove(p);
                    if (p.level().players().contains(p)) p.level().removePlayerImmediately(p, Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
            });
            h.onEachTick(() -> players.forEach(IncomingDamageHud::update));
        }

        ServerPlayer player(int x, float hp, float absorption) {
            var p = TestPlayers.create(h, new Vec3(x, 4, 16), 0, 0,
                    "W89_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p);
            p.setNoGravity(true);
            p.setOnGround(true);
            p.setAttached(WeaponLoadout.ENABLED, false);
            p.getAttribute(Attributes.MAX_HEALTH).setBaseValue(20);
            p.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);
            p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
            p.setHealth(hp);
            p.setAbsorptionAmount(absorption);
            TestPlayers.drain(p);
            return p;
        }

        void at(int ticks, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == createdAt,
                    "All callbacks register at fixture creation, never from delayed callbacks");
            h.runAfterDelay(ticks, () -> {
                check(h, h.getLevel().getServer().getTickCount() - createdAt == ticks,
                        "Exact real server tick deadline " + ticks);
                players.forEach(IncomingDamageHud::update);
                action.run();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void actualSixFiveAndOneHpUseOnlyActiveW89ModelsAcrossTheEntirePulseThenHeal(GameTestHelper h) {
        var f = new Fixture(h);
        float[] health = {6, 5, 1}, absorption = {20, 4, 0};
        var players = new ArrayList<ServerPlayer>();
        var cached = new ArrayList<ItemDisplayHud>();
        var ids = new ArrayList<Integer>();
        var seen = new HashSet<Integer>();
        for (int i = 0; i < health.length; i++) {
            var p = f.player(8 + 12 * i, health[i], absorption[i]);
            CombatHud.update(p);
            var critical = node(h, p, CRITICAL);
            players.add(p); cached.add(critical); ids.add(critical.getEntityId());
            seen.add(active(h, p, critical, critical.getEntityId(), health[i], absorption[i]));
        }
        for (int t = 1; t <= 24; t++) f.at(t, () -> {
            for (int i = 0; i < players.size(); i++) {
                var p = players.get(i);
                CombatHud.update(p);
                seen.add(active(h, p, cached.get(i), ids.get(i), health[i], absorption[i]));
                check(h, incoming(p).equals(Set.of(CRITICAL)), "Critical without a hit invents no directional arc");
                var bar = node(h, p, CombatHud.HEALTH_ID);
                near(h, bar.getScale().x, Math.round(424 * (health[i] / 20) * 2) / 2f,
                        "Health bar remains actual current HP, independent of absorption");
            }
        });
        f.at(25, () -> {
            // The unchanged formula reaches exactly frames 0..6 at HP6/5/1 over a full pulse.
            // Frame 7 is covered by the asset tests and the existing near-zero-HP pure state test.
            check(h, seen.equals(Set.of(0, 1, 2, 3, 4, 5, 6)),
                    "HP6/5/1 exercise exactly active W89 frames 0..6 across the real server pulse");
            for (int i = 0; i < players.size(); i++) {
                var p = players.get(i);
                p.setHealth(7);
                CombatHud.update(p);
                check(h, incoming(p).isEmpty(), "Healing to actual HP7 immediately removes critical");
                near(h, p.getAbsorptionAmount(), absorption[i], "Healing cleanup does not invent or spend absorption");
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void actualNativeHpLossKeepsW86ArcAboveW89CriticalAndHealingRetiresOnlyCritical(GameTestHelper h) {
        var f = new Fixture(h);
        var p = f.player(16, 7, 0);
        p.damageCooldownTime = 0;
        // An explicitly positioned native source supplies an origin without another mob fixture.
        var source = new net.minecraft.world.damagesource.DamageSource(
                p.damageSources().generic().typeHolder(), p.position().add(0, 0, 4));
        check(h, p.hurtServer(p.level(), source, 1), "Positioned native damage is accepted");
        near(h, p.getHealth(), 6, "Native damage actually reaches six HP");
        CombatHud.update(p);
        var critical = node(h, p, CRITICAL);
        active(h, p, critical, critical.getEntityId(), 6, 0);
        var arc = node(h, p, IncomingDamageHud.PREFIX + "arc_0");
        near(h, arc.getLocation().z, 7, "Existing directional arc layer");
        check(h, arc.getLocation().z > critical.getLocation().z, "Directional arc remains above full screen critical");
        check(h, arc.getItem().get(DataComponents.ITEM_MODEL).equals(
                Identifier.fromNamespaceAndPath("destiny", "gui/hud/incoming_w86_arc_0")), "Existing arc bank remains W86");
        p.setHealth(7);
        CombatHud.update(p);
        check(h, DisplayHud.getHud(p, CRITICAL) == null &&
                DisplayHud.getHud(p, IncomingDamageHud.PREFIX + "arc_0") == arc,
                "HP7 healing removes only critical and preserves exact existing directional node");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void nativeDeathSpectatorAndLevelInvalidationRetireCriticalWithoutOldNodeResurrection(GameTestHelper h) {
        var f = new Fixture(h);
        var dead = f.player(8, 6, 0);
        var spectator = f.player(20, 5, 0);
        var traveler = f.player(32, 1, 0);
        for (var p : f.players) IncomingDamageHud.update(p);
        var oldTraveler = node(h, traveler, CRITICAL);
        dead.damageCooldownTime = 0;
        dead.hurtServer(dead.level(), dead.damageSources().generic(), 100);
        check(h, !dead.isAlive(), "Native lethal damage actually kills player");
        IncomingDamageHud.update(dead);
        check(h, incoming(dead).isEmpty(), "Death removes critical node");
        spectator.setGameMode(GameType.SPECTATOR);
        IncomingDamageHud.update(spectator);
        check(h, incoming(spectator).isEmpty(), "Ineligible spectator removes critical");
        spectator.setHealth(7);
        spectator.setGameMode(GameType.SURVIVAL);
        IncomingDamageHud.update(spectator);
        check(h, incoming(spectator).isEmpty(), "HP7 eligible return cannot resurrect critical");
        var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != h.getLevel(), "Distinct native server level exists");
        traveler.setServerLevel(other);
        IncomingDamageHud.update(traveler);
        var fresh = node(h, traveler, CRITICAL);
        check(h, fresh != oldTraveler && fresh.getEntityId() != oldTraveler.getEntityId(),
                "Low HP in a new level creates a fresh owner/level node, never reuses stale session");
        active(h, traveler, fresh, fresh.getEntityId(), 1, 0);
        traveler.setHealth(7);
        traveler.setServerLevel(h.getLevel());
        IncomingDamageHud.update(traveler);
        check(h, incoming(traveler).isEmpty(), "Returning at HP7 cleans the changed-level critical session");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void consoleCriticalStatusIsReadOnlyAndNonOpPlayerIsDenied(GameTestHelper h) throws CommandSyntaxException {
        var f = new Fixture(h);
        var p = f.player(16, 6, 4);
        // World-scoped selector resolves the embedded player without adding a second connection fixture.
        h.getLevel().addNewPlayer(p);
        IncomingDamageHud.update(p);
        var critical = node(h, p, CRITICAL);
        int entityId = critical.getEntityId();
        var beforeItem = critical.getItem().copy();
        var beforeKeys = Set.copyOf(DisplayHud.getHuds(p).keySet());
        var dispatcher = h.getLevel().getServer().getCommands().getDispatcher();
        var console = h.getLevel().getServer().createCommandSourceStack().withLevel(h.getLevel()).withPosition(p.position());
        String command = "destiny debug critical-hud-status @p[name=" + p.getGameProfile().name() + ",distance=..2]";
        check(h, dispatcher.execute(command, console) == 1, "Actual console status command succeeds");
        check(h, node(h, p, CRITICAL) == critical && critical.getEntityId() == entityId &&
                        net.minecraft.world.item.ItemStack.matches(beforeItem, critical.getItem()) &&
                        beforeKeys.equals(DisplayHud.getHuds(p).keySet()),
                "Console observation preserves exact node, model/item and HUD membership");
        boolean denied = false;
        try { dispatcher.execute(command, p.createCommandSourceStack()); }
        catch (CommandSyntaxException expected) { denied = true; }
        check(h, denied, "Existing OP gate denies native non-OP player");
        active(h, p, critical, entityId, 6, 4);
        p.setHealth(7);
        check(h, dispatcher.execute(command, console) == 1, "Console observes existing node after HP changes without updating it");
        check(h, DisplayHud.getHud(p, CRITICAL) == critical && critical.getEntityId() == entityId &&
                        net.minecraft.world.item.ItemStack.matches(beforeItem, critical.getItem()),
                "Status must not call HUD update or clean the existing node even after threshold crossing");
        IncomingDamageHud.update(p);
        var healedKeys = Set.copyOf(DisplayHud.getHuds(p).keySet());
        check(h, dispatcher.execute(command, console) == 1, "Console can observe absent critical at HP7");
        check(h, DisplayHud.getHud(p, CRITICAL) == null && healedKeys.equals(DisplayHud.getHuds(p).keySet()),
                "Read-only status at HP7 never spawns a node");
        near(h, p.getHealth(), 7, "Status preserves healed HP");
        near(h, p.getAbsorptionAmount(), 4, "Status preserves absorption");
        h.succeed();
    }
}
