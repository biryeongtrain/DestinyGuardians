package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.List;

/** W73 native SERVER use + production simulated-arrow impacts, not native-client evidence.
 * Only explicitly named lifecycle/policy fixtures call confirmed directly.
 * All tick drivers are registered at test setup; all target AABBs stay inside the existing floor.
 * Accepted-draw snapshots are project policy, not a claim about the original D2 engine.
 */
public final class WeaponArcherTempoW73GameTests {
    private static final String FLOOR = "destiny-test:floor", ID = "archers_tempo";
    private static final String BOW = "whispering_slab", HUD = "archers_tempo_";
    private static final float HEALTH = 1000;
    private record Bow(ServerPlayer player, ItemStack stack, WeaponCatalog.Entry entry, WeaponProfile base) {}

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true); p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p); CombatHud.remove(p);
            p.setServerLevel(h.getLevel()); TestPlayers.remove(p);
        });
        return p;
    }
    private static Bow bow(GameTestHelper h, double z, boolean selected) {
        var p = player(h, z); var e = WeaponCatalog.find(BOW).orElseThrow();
        var s = WeaponItems.create(e); var base = WeaponProfile.forEntry(e);
        if (selected) check(h, WeaponPerks.select(s, ID), "Select exact official Tempo socket");
        p.getInventory().setItem(slot(), s); p.getInventory().setSelectedSlot(slot());
        WeaponRuntime.tickPlayer(p); TestPlayers.drain(p);
        return new Bow(p, s, e, base);
    }
    private static int slot() { return WeaponCharacteristics.of(WeaponCatalog.find(BOW).orElseThrow()).slot().hotbar(); }
    private static int rounds(Bow b) { return WeaponItems.magazine(b.stack, b.base).rounds(); }
    private static int remaining(Bow b) { return WeaponArcherTempo.remaining(b.player); }
    private static long now(Bow b) { return b.player.level().getServer().getTickCount(); }
    private static void drive(GameTestHelper h, ServerPlayer... players) {
        h.onEachTick(() -> {
            for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
        });
    }
    private static void aim(ServerPlayer p) {
        WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
    }
    private static void use(GameTestHelper h, Bow b) {
        aim(b.player);
        WeaponCombatItem.INSTANCE.use(h.getLevel(), b.player, InteractionHand.MAIN_HAND);
        check(h, b.player.isUsingItem() && b.player.getUseItem() == b.stack,
                "Actual server item use owns this exact stack");
    }
    private static void release(GameTestHelper h, Bow b) {
        aim(b.player); b.player.releaseUsingItem();
        check(h, rounds(b) == 0 && !b.player.isUsingItem() && WeaponRuntime.activeProjectiles(b.player) == 1,
                "Native release emits precisely one paid in-flight arrow before impact");
        WeaponRuntime.tickPlayer(b.player);
        check(h, WeaponRuntime.reloading(b.player), "Paid arrow begins actual automatic nock");
    }
    private static Husk target(GameTestHelper h, Bow b, boolean precision) {
        double z = b.player.getZ() - h.absoluteVec(Vec3.ZERO).z;
        // Close target keeps even a one-tick slow/curved arrow inside the body band (W49 fixture).
        var e = h.spawn(EntityTypes.HUSK, new Vec3(4.5, precision ? 1 : 1.8, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(HEALTH);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(HEALTH);
        TestCleanup.register(h, e::discard);
        var o = h.absoluteVec(Vec3.ZERO); var box = e.getBoundingBox();
        check(h, box.minX > o.x && box.maxX < o.x + 16 && box.minY > o.y && box.maxY < o.y + 8
                        && box.minZ > o.z && box.maxZ < o.z + 12,
                "Whole grounded fixture AABB fits the existing 16x8x12 floor");
        check(h, precision ? b.player.getEyeY() >= box.maxY - box.getYsize() * .25 && b.player.getEyeY() < box.maxY
                        : b.player.getEyeY() > box.minY && b.player.getEyeY() < box.maxY - box.getYsize() * .25,
                "Actual horizontal trajectory begins in requested head/body height band");
        return e;
    }
    private static float damage(GameTestHelper h, Bow b, Husk target) {
        float loss = HEALTH - target.getHealth();
        check(h, loss > 0 && target.isAlive() && WeaponRuntime.activeProjectiles(b.player) == 0,
                "Actual positive NONLETHAL projectile impact completed");
        return loss;
    }
    private static int frame(Bow b) {
        return (int)Math.floor(b.stack.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(WeaponBowPresentation.SELECTOR_INDEX));
    }
    private static void frame(GameTestHelper h, Bow b, long started, int duration) {
        WeaponRuntime.continueUse(b.player);
        int expected = 2 + (int)(Math.min(duration, Math.max(0, now(b) - started)) * 20 / duration);
        check(h, WeaponBowPresentation.active(b.stack) && frame(b) == expected,
                "Actual normalized selector uses accepted " + duration + "-tick draw: " + expected + "/" + frame(b));
    }
    /** Explicit lifecycle-only injection; never evidence that gameplay earned a proc. */
    private static WeaponArcherTempo.Token lifecyclePrecision(Bow b) {
        var token = WeaponArcherTempo.capture(b.player);
        WeaponArcherTempo.confirmed(b.player, token, true); return token;
    }
    private static ItemDisplayHud node(Bow b, String suffix) {
        return (ItemDisplayHud)DisplayHud.getHud(b.player, WeaponPerkHud.PREFIX + HUD + suffix);
    }
    private static long nodes(Bow b) {
        return DisplayHud.getHuds(b.player).keySet().stream().filter(k -> k.startsWith(WeaponPerkHud.PREFIX + HUD)).count();
    }
    private static void select(ServerPlayer p, int slot) {
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void exactOfficialSocketAllCatalogEligibilityNoImplicitActivationAndExclusiveSavedSocket(GameTestHelper h) {
        check(h, ArcherTempoProfile.rolls().equals(List.of(new WeaponPerks.Roll(BOW, 211938782L, 3, 201365942L, 1885424927L))),
                "Independent exact official item/socket/perk/plug-set oracle");
        var e = WeaponCatalog.find(BOW).orElseThrow(); var timing = ArcherTempoProfile.timing(e);
        check(h, ArcherTempoProfile.ID.equals(ID) && ArcherTempoProfile.HASH == 201365942L
                        && ArcherTempoProfile.perk().durationTicks() == 60 && ArcherTempoProfile.perk().drawScalar() == .75
                        && timing.baseDrawMs() == 567 && timing.baseDrawTicks() == 12 && timing.acceleratedTicks() == 9,
                "Pinned base trait and raw-ms-before-ceil timing");
        var winds = WeaponCatalog.find("biting_winds").orElseThrow();
        check(h, ArcherTempoProfile.timing(winds).baseDrawMs() == 667
                        && ArcherTempoProfile.timing(winds).baseDrawTicks() == 14
                        && ArcherTempoProfile.timing(winds).acceleratedTicks() == 11,
                "Biting Winds has a timing candidate, not an official Tempo socket");
        boolean rejected = false;
        try { ArcherTempoProfile.accelerated(winds, WeaponProfile.forEntry(winds)); }
        catch (IllegalArgumentException expected) { rejected = true; }
        check(h, rejected, "Timing candidate cannot authorize acceleration for ineligible Biting Winds");
        var b = bow(h, 6, false); var saved = b.stack.copy();
        CombatHud.update(b.player);
        check(h, WeaponPerks.selected(b.stack, ID).isEmpty() && remaining(b) == 0 && nodes(b) == 0
                        && ItemStack.matches(saved, b.stack), "New owned bow and HUD reads never implicitly select or proc");
        for (var entry : WeaponCatalog.all()) {
            var s = WeaponItems.create(entry); var before = s.copy(); boolean eligible = entry.id().equals(BOW);
            check(h, !WeaponPerks.available(s, ID).isEmpty() == eligible && WeaponPerks.selected(s, ID).isEmpty(),
                    "Exact-hash catalog eligibility, no family/name inference: " + entry.id());
            check(h, WeaponPerks.select(s, ID) == eligible && (eligible || ItemStack.matches(before, s)),
                    "Unsupported selection is inert: " + entry.id());
        }
        check(h, WeaponPerks.select(b.stack, ID) && remaining(b) == 0, "Explicit selection alone still grants no timer");
        var ammo = WeaponItems.magazine(b.stack, b.base).total();
        var tag = b.stack.get(DataComponents.CUSTOM_DATA).copyTag(); var sockets = new CompoundTag();
        sockets.putLong("4", 201365942L); tag.put(WeaponPerks.SLOTS_KEY, sockets);
        b.stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(b.stack, ID).isEmpty(), "Correct perk in wrong official socket is inert");
        check(h, WeaponPerks.select(b.stack, ID), "Restore real socket");
        // A different saved hash in the SAME slot must replace, never coexist with Tempo.
        tag = b.stack.get(DataComponents.CUSTOM_DATA).copyTag(); sockets = new CompoundTag();
        sockets.putLong("3", 3300816228L); tag.put(WeaponPerks.SLOTS_KEY, sockets);
        b.stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        check(h, WeaponPerks.selected(b.stack, ID).isEmpty() && remaining(b) == 0,
                "Single-valued trait socket excludes Tempo when another hash occupies socket3");
        check(h, WeaponPerks.select(b.stack, ID) && WeaponPerks.selected(b.stack.copy(), ID).isPresent()
                        && WeaponItems.magazine(b.stack, b.base).total() == ammo && remaining(b) == 0,
                "Copy retains explicit selection only, and edits never mint ammo or proc");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void realNonlethalPrecisionArrowProcsButBodyImmuneAndUnselectedDoNot(GameTestHelper h) {
        var head = bow(h, 2, true); var body = bow(h, 4.5, true);
        var immune = bow(h, 7, true); var plain = bow(h, 9.5, false);
        var a = target(h, head, true); var b = target(h, body, false);
        var c = target(h, immune, true); c.setPermanentlyInvulnerable(true); var d = target(h, plain, true);
        drive(h, head.player, body.player, immune.player, plain.player);
        for (var fixture : List.of(head, body, immune, plain)) use(h, fixture);
        h.runAfterDelay(14, () -> {
            for (var fixture : List.of(head, body, immune, plain)) {
                check(h, remaining(fixture) == 0, "Hold without impact cannot proc"); release(h, fixture);
                check(h, remaining(fixture) == 0, "Emission before collision cannot proc");
            }
        });
        h.runAfterDelay(20, () -> {
            float critical = damage(h, head, a), ordinary = damage(h, body, b); damage(h, plain, d);
            check(h, critical > ordinary && remaining(head) > 0 && remaining(head) <= 60,
                    "Paid positive precision impact on SURVIVING target earns Tempo, no kill required");
            check(h, remaining(body) == 0 && remaining(plain) == 0 && remaining(immune) == 0
                            && c.getHealth() == HEALTH && WeaponRuntime.activeProjectiles(immune.player) == 0,
                    "Real body, immune collision and unselected precision controls never proc");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void genuinelyEarnedTempoNormalizesPartialDamageAndReachesFullBeforeBaseDraw(GameTestHelper h) {
        var fast = bow(h, 3, true); var base = bow(h, 9, false);
        Husk[] a = {target(h, fast, true)}, b = {target(h, base, true)};
        float[] partial = new float[2]; long[] started = {-1};
        drive(h, fast.player, base.player); use(h, fast); use(h, base);
        int first = 14, n = fast.base.firstReloadTicks(), second = first + n + 2, third = second + 4 + n + 2;
        h.runAfterDelay(first, () -> { release(h, fast); release(h, base); });
        h.runAfterDelay(first + 6, () -> {
            damage(h, fast, a[0]); damage(h, base, b[0]);
            check(h, remaining(fast) > 0 && remaining(base) == 0, "Only real earned precision enables accelerated comparison");
            a[0].discard(); b[0].discard(); a[0] = target(h, fast, false); b[0] = target(h, base, false);
        });
        h.runAfterDelay(second, () -> {
            check(h, rounds(fast) == 1 && rounds(base) == 1, "Both actual nocks completed");
            use(h, fast); use(h, base); started[0] = now(fast);
        });
        h.runAfterDelay(second + 4, () -> {
            frame(h, fast, started[0], 9); frame(h, base, started[0], 12);
            check(h, frame(fast) > frame(base) && frame(fast) < 22, "Same four ticks visibly advance boosted partial draw farther");
            release(h, fast); release(h, base);
        });
        h.runAfterDelay(second + 11, () -> {
            partial[0] = damage(h, fast, a[0]); partial[1] = damage(h, base, b[0]);
            check(h, partial[0] > partial[1] * 1.08f, "Normalized boosted partial arrow causes greater actual body HP loss");
            a[0].discard(); b[0].discard(); a[0] = target(h, fast, false); b[0] = target(h, base, false);
        });
        h.runAfterDelay(third, () -> {
            check(h, remaining(fast) > 0, "Earned window still covers third accepted draw");
            use(h, fast); use(h, base); started[0] = now(fast);
        });
        h.runAfterDelay(third + 9, () -> {
            frame(h, fast, started[0], 9); frame(h, base, started[0], 12);
            check(h, frame(fast) == 22 && frame(base) < 22 && rounds(fast) == 1 && rounds(base) == 1,
                    "Boost is fully drawn at nine while base twelve-tick draw is unfinished; neither auto-fires");
            release(h, fast); release(h, base);
        });
        h.runAfterDelay(third + 15, () -> {
            float full = damage(h, fast, a[0]), earlyBase = damage(h, base, b[0]);
            check(h, Math.abs(full - fast.base.damage()) < .01f && full > earlyBase * 1.1f
                            && full > partial[0] && earlyBase > partial[1],
                    "Actual boosted nine-tick impact is full base damage; unboosted nine-tick and both four-tick shots are partial");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 130, environment = "destiny-test:w90_isolated")
    public void lifecycleExact59And60RefreshConsumedTokensAndCachedHudReadsArePure(GameTestHelper h) {
        var expire = bow(h, 3, true); var refresh = bow(h, 9, true);
        drive(h, expire.player, refresh.player);
        var old = lifecyclePrecision(expire); var replay = lifecyclePrecision(refresh);
        CombatHud.update(expire.player); CombatHud.update(refresh.player);
        var label = node(refresh, "label"); int entityId = label.getEntityId();
        var item = label.getItemDisplay().getItemStack(); var saved = refresh.stack.copy();
        check(h, nodes(expire) == 6 && nodes(refresh) == 6 && label.getLocation().y() == 778
                        && label.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/perk_archers_tempo_w73")
                        && node(refresh, "ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_3"),
                "Exact plural HUD row has six nodes and actual0:03");
        for (int i = 0; i < 24; i++) {
            WeaponPerkHud.update(refresh.player); CombatHud.update(refresh.player); AmmoHud.current(refresh.player);
            WeaponRuntime.ammunition(refresh.player); WeaponArcherTempo.draw(refresh.player, refresh.entry, refresh.base);
            check(h, remaining(refresh) == 60, "Reads never consume or extend duration");
        }
        check(h, node(refresh, "label") == label && label.getEntityId() == entityId
                        && label.getItemDisplay().getItemStack() == item && ItemStack.matches(saved, refresh.stack),
                "Repeated read/update preserves cached native display item and gameplay stack");
        h.runAfterDelay(59, () -> {
            check(h, remaining(expire) == 1 && remaining(refresh) == 1, "Exact59 remains one tick");
            CombatHud.update(expire.player);
            check(h, node(expire, "ones").getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_digit_1"),
                    "Last live tick displays0:01");
            lifecyclePrecision(refresh); CombatHud.update(refresh.player);
            check(h, remaining(refresh) == 60 && node(refresh, "label") == label && label.getEntityId() == entityId,
                    "Fresh token refreshes single window and reuses row entity");
        });
        h.runAfterDelay(60, () -> {
            WeaponArcherTempo.confirmed(expire.player, old, true); WeaponArcherTempo.confirmed(refresh.player, replay, true);
            CombatHud.update(expire.player); CombatHud.update(refresh.player);
            check(h, remaining(expire) == 0 && nodes(expire) == 0 && remaining(refresh) == 59,
                    "Exact60 expires; consumed tokens cannot revive or refresh either window");
        });
        h.runAfterDelay(118, () -> check(h, remaining(refresh) == 1, "Refresh expires relative to most recent qualifying token"));
        h.runAfterDelay(119, () -> {
            CombatHud.update(refresh.player);
            check(h, remaining(refresh) == 0 && nodes(refresh) == 0 && ItemStack.matches(saved, refresh.stack),
                    "No stale0:00, inherited time, stack mutation or read-created proc");
            var bodyToken = WeaponArcherTempo.capture(refresh.player);
            WeaponArcherTempo.confirmed(refresh.player, bodyToken, false);
            WeaponArcherTempo.confirmed(refresh.player, bodyToken, true);
            check(h, remaining(refresh) == 0, "Even a nonprecision confirmation consumes its token once"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 45, environment = "destiny-test:w90_isolated")
    public void realInFlightPrecisionCannotProcAfterStowOrSameTickAwayAndBack(GameTestHelper h) {
        var stow = bow(h, 3, true); var back = bow(h, 9, true);
        var a = target(h, stow, true); var b = target(h, back, true);
        drive(h, stow.player, back.player); use(h, stow); use(h, back);
        for (var fixture : List.of(stow, back)) fixture.player.getInventory().setItem(7, new ItemStack(Items.STONE));
        h.runAfterDelay(14, () -> {
            release(h, stow); release(h, back);
            check(h, a.getHealth() == HEALTH && b.getHealth() == HEALTH, "Both genuine arrow tokens are still in flight");
            select(stow.player, 7); select(back.player, 7); select(back.player, slot());
            check(h, back.player.getMainHandItem() == back.stack, "Same-tick native away/back returns exact original stack");
        });
        h.runAfterDelay(21, () -> {
            damage(h, stow, a); damage(h, back, b);
            check(h, remaining(stow) == 0 && remaining(back) == 0,
                    "Both real positive precision impacts survive stow as damage but old generation earns no proc");
            select(stow.player, slot()); WeaponRuntime.tickPlayer(stow.player);
            check(h, remaining(stow) == 0, "Returning source bow after impact cannot resurrect invalidated flight token"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void lifecycleExactStackCopyTradeOwnerLevelAndGenerationCannotInheritProc(GameTestHelper h) {
        var keep = bow(h, 10, true); lifecyclePrecision(keep);
        var original = bow(h, 2, true); var recipient = bow(h, 5, true);
        drive(h, keep.player, original.player, recipient.player);
        var token = lifecyclePrecision(original); var saved = original.stack.copy();
        original.player.setItemInHand(InteractionHand.MAIN_HAND, original.stack.copy());
        WeaponRuntime.tickPlayer(original.player);
        check(h, remaining(original) == 0, "Exact serialized copy inherits selection and ammo, never active runtime window");
        WeaponArcherTempo.confirmed(original.player, token, true);
        original.player.setItemInHand(InteractionHand.MAIN_HAND, original.stack); WeaponRuntime.tickPlayer(original.player);
        var stale = WeaponArcherTempo.capture(original.player); WeaponArcherTempo.cleanup(original.player);
        WeaponArcherTempo.update(original.player); WeaponArcherTempo.confirmed(original.player, stale, true);
        check(h, remaining(original) == 0, "Same owner/level/stack after session generation replacement rejects old token");
        var traded = WeaponArcherTempo.capture(original.player);
        original.player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY); WeaponRuntime.tickPlayer(original.player);
        recipient.player.setItemInHand(InteractionHand.MAIN_HAND, original.stack); WeaponRuntime.tickPlayer(recipient.player);
        WeaponArcherTempo.confirmed(recipient.player, traded, true); WeaponArcherTempo.confirmed(original.player, traded, true);
        check(h, WeaponArcherTempo.remaining(recipient.player) == 0 && remaining(original) == 0
                        && ItemStack.matches(saved, original.stack), "Trading exact stack cannot transfer owner credit, proc or mutate ammo");
        var crossLevel = WeaponArcherTempo.capture(recipient.player);
        var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                .filter(l -> l != h.getLevel()).findFirst().orElseThrow();
        recipient.player.setServerLevel(other); WeaponArcherTempo.confirmed(recipient.player, crossLevel, true);
        recipient.player.setServerLevel(h.getLevel()); WeaponArcherTempo.confirmed(recipient.player, crossLevel, true);
        check(h, WeaponArcherTempo.remaining(recipient.player) == 0 && remaining(keep) == 60,
                "Level mismatch consumes token; returning cannot replay it or alter unrelated owner's window");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void lifecycleMidDrawProcAndExpiryKeepAcceptedSelectorAndActualDamagePolicy(GameTestHelper h) {
        var proc = bow(h, 3, true); var expiry = bow(h, 9, true);
        var a = target(h, proc, false); var b = target(h, expiry, false); long[] start = {-1};
        drive(h, proc.player, expiry.player); use(h, proc); long procStart = now(proc); lifecyclePrecision(expiry);
        h.runAfterDelay(2, () -> lifecyclePrecision(proc));
        h.runAfterDelay(9, () -> {
            frame(h, proc, procStart, 12); check(h, remaining(proc) > 0 && frame(proc) < 22,
                    "Mid-draw proc does not retroactively shorten accepted base draw"); release(h, proc);
        });
        h.runAfterDelay(15, () -> {
            float partial = damage(h, proc, a);
            check(h, partial > 0 && partial < proc.base.damage() * .95f,
                    "Actual nine-tick impact remains partial despite newly active Tempo");
        });
        h.runAfterDelay(55, () -> { use(h, expiry); start[0] = now(expiry); check(h, remaining(expiry) == 5, "Boost accepted before expiration"); });
        h.runAfterDelay(61, () -> {
            check(h, remaining(expiry) == 0, "Window expired during accepted draw"); frame(h, expiry, start[0], 9);
        });
        h.runAfterDelay(64, () -> { frame(h, expiry, start[0], 9); release(h, expiry); });
        h.runAfterDelay(70, () -> {
            check(h, Math.abs(damage(h, expiry, b) - expiry.base.damage()) < .01f && remaining(expiry) == 0,
                    "Expired window leaves accepted nine-tick draw at full actual body damage, without body reproccing"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 60, environment = "destiny-test:w90_isolated")
    public void lifecycleBoostedQAndSkillCancelNeverLeaveGhostArrowsOrNocks(GameTestHelper h) {
        var q = bow(h, 3, true); var skill = bow(h, 9, true);
        var a = target(h, q, true); var b = target(h, skill, true);
        drive(h, q.player, skill.player); lifecyclePrecision(q); lifecyclePrecision(skill); use(h, q); use(h, skill);
        long started=now(q);
        h.runAfterDelay(9, () -> {
            // GameTest callback/driver ordering is not the production END_SERVER_TICK contract.
            // Observe the current tick after the normal continueUse update, as the other draw tests do.
            frame(h,q,started,9); frame(h,skill,started,9);
            check(h, frame(q) == 22 && frame(skill) == 22, "Both boosted native holds fully drawn");
            check(h, InputRouter.onPlayerAction(q.player, ServerboundPlayerActionPacket.Action.DROP_ITEM), "Real Q route consumes letdown");
            WeaponRuntime.cancelUseForSkill(skill.player);
            for (var fixture : List.of(q, skill)) {
                fixture.player.releaseUsingItem(); WeaponRuntime.releaseUse(fixture.player, fixture.stack);
                check(h, rounds(fixture) == 1 && !fixture.player.isUsingItem() && !WeaponRuntime.reloading(fixture.player)
                                && WeaponRuntime.activeProjectiles(fixture.player) == 0, "Cancellation and stale release preserve loaded arrow");
            }
        });
        h.runAfterDelay(40, () -> {
            check(h, a.getHealth() == HEALTH && b.getHealth() == HEALTH && rounds(q) == 1 && rounds(skill) == 1
                            && WeaponRuntime.activeProjectiles(q.player) == 0 && WeaponRuntime.activeProjectiles(skill.player) == 0
                            && !WeaponRuntime.reloading(q.player) && !WeaponRuntime.reloading(skill.player),
                    "No delayed projectile, target damage, ammo transfer or ghost nock after either cancellation"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void lifecycleBufferWaitCannotInheritOldBoostOrNockTimeAndOneTickArrowIsActuallyPartial(GameTestHelper h) {
        var b = bow(h, 6, true); Husk[] victim = {target(h, b, false)}; float[] full = {0}; long[] start = {-1};
        drive(h, b.player); lifecyclePrecision(b); int n = b.base.firstReloadTicks();
        h.runAfterDelay(40, () -> use(h, b));
        h.runAfterDelay(50, () -> release(h, b));
        h.runAfterDelay(51, () -> { use(h, b); check(h, remaining(b) > 0, "Press buffered while old boost is still active"); });
        h.runAfterDelay(56, () -> {
            full[0] = damage(h, b, victim[0]); victim[0].discard(); victim[0] = target(h, b, false);
        });
        h.runAfterDelay(50 + n - 1, () -> check(h, rounds(b) == 0 && WeaponRuntime.reloading(b.player), "Buffered hold cannot accelerate nock"));
        h.runAfterDelay(50 + n, () -> {
            WeaponRuntime.tickPlayer(b.player); start[0] = now(b);
            check(h, remaining(b) == 0 && rounds(b) == 1 && b.player.isUsingItem(), "Actual charge starts only after nock, after old window expired");
            frame(h, b, start[0], 12); check(h, frame(b) == 2, "Nock waiting contributes zero draw time");
        });
        h.runAfterDelay(50 + n + 1, () -> { frame(h, b, start[0], 12); release(h, b); });
        h.runAfterDelay(50 + n + 13, () -> {
            float partial = damage(h, b, victim[0]);
            check(h, partial < full[0] * .55f && remaining(b) == 0,
                    "Actual one-tick arrow is weaker: buffered old boost and elapsed nock never become charge");
        });
        h.runAfterDelay(50 + 2 * n + 3, () -> {
            check(h, rounds(b) == 1 && !b.player.isUsingItem() && WeaponRuntime.activeProjectiles(b.player) == 0,
                    "Partial arrow nocks once and leaves no buffered ghost shot"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void lifecycleProcDuringBufferedNockIsCapturedAtActualContinuationForFullNineTicks(GameTestHelper h) {
        var b = bow(h, 6, true); Husk[] victim = {target(h, b, false)}; long[] start = {-1};
        drive(h, b.player); use(h, b); int shot = 14, n = b.base.firstReloadTicks();
        h.runAfterDelay(shot, () -> release(h, b));
        h.runAfterDelay(shot + 1, () -> { use(h, b); check(h, remaining(b) == 0, "Buffered press is initially unboosted"); });
        h.runAfterDelay(shot + 6, () -> {
            damage(h, b, victim[0]); victim[0].discard(); victim[0] = target(h, b, false);
        });
        h.runAfterDelay(shot + n - 1, () -> { lifecyclePrecision(b); check(h, rounds(b) == 0, "Explicit policy fixture gains proc during actual nock"); });
        h.runAfterDelay(shot + n, () -> {
            WeaponRuntime.tickPlayer(b.player); start[0] = now(b);
            check(h, rounds(b) == 1 && b.player.isUsingItem(), "Actual held continuation starts fresh accepted charge");
            frame(h, b, start[0], 9); check(h, frame(b) == 2, "New boost changes duration, never grants inherited progress");
        });
        h.runAfterDelay(shot + n + 8, () -> {
            frame(h, b, start[0], 9); check(h, frame(b) < 22 && rounds(b) == 1, "Eight complete draw ticks still not full");
        });
        h.runAfterDelay(shot + n + 9, () -> {
            frame(h, b, start[0], 9); check(h, frame(b) == 22 && WeaponRuntime.activeProjectiles(b.player) == 0,
                    "Exactly nine fresh ticks reaches full without automatic release"); release(h, b);
        });
        h.runAfterDelay(shot + n + 15, () -> {
            check(h, Math.abs(damage(h, b, victim[0]) - b.base.damage()) < .01f,
                    "Actual buffered full shot uses new boosted duration and unchanged full damage"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void lifecycleRealPerkCommandEditsRetireTokensButNoopsAndEligibilityReturnsNeverInherit(GameTestHelper h) {
        var b = bow(h, 3, true); var keep = bow(h, 9, true);
        drive(h, b.player, keep.player);
        lifecyclePrecision(b); lifecyclePrecision(keep);
        var pending = WeaponArcherTempo.capture(b.player); var saved = b.stack.copy();
        var dispatcher = h.getLevel().getServer().getCommands().getDispatcher();
        var source = b.player.createCommandSourceStack();
        h.runAfterDelay(1, () -> {
            try {
                check(h, remaining(b) == 59 && dispatcher.execute("destiny perk select " + ID, source) == 1
                                && remaining(b) == 59 && ItemStack.matches(saved, b.stack),
                        "Actual same-choice select is a no-op: active timer and serialized stack stay unchanged");
                WeaponArcherTempo.confirmed(b.player, pending, true);
                check(h, remaining(b) == 60, "No-op command preserves an unconsumed in-flight lifecycle token");
                var beforeEdit = WeaponArcherTempo.capture(b.player);
                check(h, dispatcher.execute("destiny perk clear", source) == 1
                                && WeaponPerks.selected(b.stack, ID).isEmpty() && remaining(b) == 0,
                        "Actual clear edit immediately retires active window");
                var cleared = b.stack.copy();
                check(h, dispatcher.execute("destiny perk clear", source) == 1 && ItemStack.matches(cleared, b.stack)
                                && dispatcher.execute("destiny perk select " + ID, source) == 1,
                        "Already-clear command is inert; actual reselect restores only the official socket");
                WeaponRuntime.tickPlayer(b.player);
                WeaponArcherTempo.confirmed(b.player, beforeEdit, true);
                check(h, remaining(b) == 0 && b.player.getMainHandItem() == b.stack && ItemStack.matches(saved, b.stack),
                        "Clear/reselect returning identical exact stack cannot inherit active time or pre-edit flight token");
            } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) {
                throw new AssertionError("Actual destiny perk command fixture", e);
            }
            for (String transition : List.of("spectator", "super", "cleanup")) {
                lifecyclePrecision(b); var stale = WeaponArcherTempo.capture(b.player);
                check(h, remaining(b) == 60, "Fresh lifecycle window before " + transition);
                switch (transition) {
                    case "spectator" -> b.player.setGameMode(GameType.SPECTATOR);
                    case "super" -> {
                        // Explicit minimal lifecycle session isolates inSuper eligibility from skill damage/VFX.
                        AbilityService.startSuper(b.player, new SuperSession() {
                            public boolean tick() { return true; }
                            public void primary() {}
                            public void end() {}
                            public float remaining() { return 1; }
                        });
                        check(h, AbilityService.inSuper(b.player), "Actual super-session service marks owner ineligible");
                    }
                    case "cleanup" -> WeaponRuntime.cleanup(b.player);
                    default -> throw new AssertionError(transition);
                }
                WeaponRuntime.tickPlayer(b.player); CombatHud.update(b.player);
                check(h, remaining(b) == 0 && nodes(b) == 0, transition + " removes active window and HUD row");
                if (transition.equals("spectator")) b.player.setGameMode(GameType.SURVIVAL);
                if (transition.equals("super")) AbilityService.endSuper(b.player);
                WeaponRuntime.tickPlayer(b.player);
                WeaponArcherTempo.confirmed(b.player, stale, true); CombatHud.update(b.player);
                check(h, remaining(b) == 0 && nodes(b) == 0 && WeaponPerks.selected(b.stack, ID).isPresent()
                                && b.player.getMainHandItem() == b.stack && ItemStack.matches(saved, b.stack),
                        transition + " return retains exact weapon and selection but cannot inherit time or stale token");
            }
            check(h, remaining(keep) == 59, "Commands and all eligibility transitions leave another owner untouched");
            lifecyclePrecision(b);
            check(h, remaining(b) == 60, "Eligible return accepts only fresh-generation credit"); h.succeed();
        });
    }
    private static void offhandSwap(ServerPlayer p) {
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND,
                net.minecraft.core.BlockPos.ZERO,net.minecraft.core.Direction.UP));
    }
    private static void ordinary(Bow b) {
        kim.biryeong.destiny.guardian.Guardians.data(b.player)
                .setGuardianClass(kim.biryeong.destiny.guardian.GuardianClass.NONE);
        b.player.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.STONE));
    }
    @GameTest(structure=FLOOR,maxTicks=45, environment = "destiny-test:w90_isolated")
    public void realNonGuardianOffhandAwayBackRetiresWindowAndActualInFlightPrecisionCredit(GameTestHelper h) {
        var b=bow(h,3,true);var keep=bow(h,9,true);ordinary(b);
        var victim=target(h,b,true);drive(h,b.player,keep.player);lifecyclePrecision(b);lifecyclePrecision(keep);use(h,b);
        h.runAfterDelay(14,()->{
            release(h,b);int left=remaining(b);check(h,left>0,"Active window and real paid arrow precede swap");
            offhandSwap(b.player);
            check(h,b.player.getOffhandItem()==b.stack && b.player.getMainHandItem().is(Items.STONE),"Real vanilla packet moves exact bow to offhand");
            offhandSwap(b.player);
            check(h,b.player.getMainHandItem()==b.stack && b.player.getOffhandItem().is(Items.STONE),"Second real packet returns exact bow within same tick");
            check(h,remaining(b)==0,"Even sub-tick offhand stow retires active Tempo window");
            int control=remaining(keep);
            check(h,InputRouter.onPlayerAction(keep.player,ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND)
                            &&keep.player.getMainHandItem()==keep.stack&&remaining(keep)==control,
                    "Guardian F still routes to grenade and never pretends an actual offhand stow");
        });
        h.runAfterDelay(21,()->{
            damage(h,b,victim);check(h,remaining(b)==0,"Real positive precision arrow from retired offhand generation cannot re-arm window");
            check(h,remaining(keep)>0,"Other owner remains unaffected");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,maxTicks=50, environment = "destiny-test:w90_isolated")
    public void realNonGuardianOffhandAwayBackCancelsAcceptedDrawBeforeSameTickFreshUse(GameTestHelper h) {
        var b=bow(h,6,true);ordinary(b);drive(h,b.player);lifecyclePrecision(b);use(h,b);long began=now(b);
        h.runAfterDelay(9,()->{
            frame(h,b,began,9);check(h,frame(b)==22,"Boosted accepted draw was actually full");
            offhandSwap(b.player);offhandSwap(b.player);
            check(h,b.player.getMainHandItem()==b.stack&&!b.player.isUsingItem()&&remaining(b)==0,"Actual sub-tick stow cancels native hold and buff");
            use(h,b);frame(h,b,now(b),12);
            check(h,frame(b)==2&&rounds(b)==1&&WeaponRuntime.activeProjectiles(b.player)==0,"Immediate new press starts zero-progress base draw, not old boosted/full candidate");
            b.player.releaseUsingItem();
            check(h,rounds(b)==0&&WeaponRuntime.activeProjectiles(b.player)==1,"Only fresh real release pays/emits one partial arrow");
        });
        h.runAfterDelay(40,()->{
            check(h,rounds(b)==1&&!b.player.isUsingItem()&&remaining(b)==0,"Fresh partial shot nocks once with no inherited Tempo");h.succeed();
        });
    }

}
