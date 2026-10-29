package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.sound.ReloadAudioProfile;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** W62 paid-kill, W63 EmbeddedChannel and W64 live HUD/Polymer fixtures.
 * All deadlines use advancing server ticks; perk credit is earned by actual weapon kills.
 * Server/packet assertions only, without native input, rendered motion or acoustic claims.
 * Registration belongs to the main change, not this sidecar.
 */
public final class ReloadCreditW65GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String DUKE = "duke_mk_44";
    private static final float EPS = .0001f;
    private record Timing(String id, int full, int credit, boolean primary) {}
    private static final List<Timing> NORMAL = List.of(
            new Timing(DUKE, 59, 42, true),
            new Timing("austringer", 53, 38, true),
            new Timing("seventh_seraph_officer_revolver", 52, 37, true),
            new Timing("fixed_odds", 106, 69, false),
            new Timing("hammerhead", 91, 60, false),
            new Timing("retrofit_escapade", 90, 59, false));
    private record Reload(ServerPlayer owner, ItemStack gun, WeaponProfile profile,
                          Identifier model, int rounds, int reserve, long total,
                          long started, int full, int credit, int loaded, int left) {}

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry entry(ItemStack gun) { return WeaponItems.entry(gun).orElseThrow(); }
    private static WeaponProfile profile(ItemStack gun) { return WeaponProfile.forEntry(entry(gun)); }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun, profile(gun)); }
    private static WeaponReloadPolicy.Plan base(WeaponProfile p) {
        return new WeaponReloadPolicy.Plan(p.firstReloadTicks(), p.reloadTicks(), p.roundsPerInsert());
    }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static ItemStack equip(ServerPlayer p, String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow();
        var gun = WeaponItems.create(e);
        WeaponItems.save(gun, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        int slot = WeaponCharacteristics.of(e).slot().hotbar();
        p.getInventory().setItem(slot, gun);
        p.getInventory().setSelectedSlot(slot);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return gun;
    }
    private static Reload start(GameTestHelper h, ServerPlayer p, ItemStack gun, int full, int credit) {
        var f = profile(gun);
        var before = ammo(gun);
        var plan = WeaponOutlaw.plan(p, entry(gun), f);
        check(h, plan.firstTicks() == full && ReloadCreditProfile.ammoTicks(entry(gun), plan) == credit,
                "Pinned captured full/credit deadlines for " + entry(gun).id() + ": " + full + "/" + credit);
        long started = now(p);
        check(h, WeaponRuntime.reload(p), "Actual production reload accepted: " + entry(gun).id());
        int moved = f.infiniteReserve() ? f.magazine() - before.rounds()
                : Math.min(f.magazine() - before.rounds(), before.reserve());
        var r = new Reload(p, gun, f, gun.get(DataComponents.ITEM_MODEL), before.rounds(),
                before.reserve(), before.total(), started, full, credit, before.rounds() + moved,
                f.infiniteReserve() ? 0 : before.reserve() - moved);
        amounts(h, r, r.rounds(), r.reserve());
        phase(h, r, 0);
        return r;
    }
    private static void drive(GameTestHelper h, Reload... reloads) {
        h.onEachTick(() -> {
            for (var r : reloads) {
                WeaponRuntime.tickPlayer(r.owner());
                TestPlayers.drain(r.owner());
            }
        });
    }
    private static ItemDisplayHud node(ServerPlayer p, String suffix) {
        return (ItemDisplayHud) DisplayHud.getHud(p, AmmoHud.PREFIX + suffix);
    }
    private static void digits(GameTestHelper h, ServerPlayer p, String field, int value) {
        var text = Integer.toString(value);
        for (int i = 0; i < text.length(); i++) {
            var glyph = node(p, field + "_" + i);
            check(h, glyph != null && Identifier.fromNamespaceAndPath("destiny", "gui/hud/ammo_digit_" + text.charAt(i))
                            .equals(glyph.getItem().get(DataComponents.ITEM_MODEL)),
                    "Actual HUD " + field + " glyph " + i + " reflects " + value);
        }
        for (int i = text.length(); i < 10; i++)
            check(h, node(p, field + "_" + i) == null, "No stale trailing " + field + " digit");
    }
    private static ItemStack wire(Reload r) {
        var context = ((PacketContextProvider) (Object) r.owner().connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(r.gun(), context, r.owner().level().registryAccess());
    }
    private static float motion(ItemStack gun) {
        return gun.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY)
                .getFloat(WeaponReloadPresentation.PROGRESS_INDEX);
    }
    private static void amounts(GameTestHelper h, Reload r, int rounds, int reserve) {
        amounts(h, r, rounds, reserve, r.total());
    }
    private static void amounts(GameTestHelper h, Reload r, int rounds, int reserve, long total) {
        var a = ammo(r.gun());
        check(h, a.rounds() == rounds && a.reserve() == reserve && a.overflow() == 0,
                entry(r.gun()).id() + " persisted rounds/reserve must be " + rounds + "/" + reserve
                        + ", got " + a.rounds() + "/" + a.reserve());
        if (!r.profile().infiniteReserve())
            check(h, a.total() == total, "Finite total matches actual transfers and explicitly paid fixture shots");
    }
    private static void credited(GameTestHelper h, Reload r) { amounts(h, r, r.loaded(), r.left()); }
    private static void phase(GameTestHelper h, Reload r, int elapsed) {
        WeaponRuntime.tickPlayer(r.owner());
        CombatHud.update(r.owner());
        var s = WeaponRuntime.ammunition(r.owner()).orElseThrow();
        check(h, now(r.owner()) - r.started() == elapsed && elapsed < r.full()
                        && WeaponRuntime.reloading(r.owner()) && s.reloading()
                        && s.reloadDuration() == r.full() && s.reloadRemaining() == r.full() - elapsed,
                "Actual full reload phase remains authoritative at elapsed " + elapsed + " for " + entry(r.gun()).id());
        float progress = 1 - (r.full() - elapsed) / (float) r.full();
        check(h, Math.abs(s.reloadProgress() - progress) < EPS && AmmoHud.current(r.owner()).orElseThrow().equals(s),
                "HUD uses elapsed/full duration through the ammo-credit boundary");
        var a = ammo(r.gun());
        check(h, s.rounds() == a.rounds() && s.reserve() == a.reserve(), "Read projection matches saved ammo");
        digits(h, r.owner(), "rounds", a.rounds());
        if (r.profile().infiniteReserve())
            check(h, node(r.owner(), "infinity") != null && node(r.owner(), "reserve_0") == null,
                    "Primary still shows infinity instead of fabricated finite reserve");
        else {
            digits(h, r.owner(), "reserve", a.reserve());
            check(h, node(r.owner(), "infinity") == null, "MG/Special HUD remains finite");
        }
        var fill = node(r.owner(), "reload");
        float width = 276 * (float) Math.floor(progress * 8) / 8;
        check(h, node(r.owner(), "reload_track") != null && (width == 0 ? fill == null
                        : fill != null && Math.abs(fill.getScale().x - width) < EPS),
                "Rendered HUD bar retains the original eight-step full-duration progress");
        if (WeaponReloadPresentation.supports(entry(r.gun()))) {
            float expected = (float) Math.floor(progress * 60 + 1e-6f) / 60;
            var sent = wire(r);
            check(h, WeaponReloadPresentation.active(r.gun()) && Math.abs(motion(r.gun()) - expected) < EPS
                            && Math.abs(motion(sent) - expected) < EPS
                            && WeaponFirstPersonHands.model(WeaponReloadPresentation.model(entry(r.gun()))).equals(sent.get(DataComponents.ITEM_MODEL))
                            && r.model().equals(r.gun().get(DataComponents.ITEM_MODEL)),
                    "Live W64/W47 wrapper and CMD continue on the full phase, preserving stored model identity");
        }
    }
    private static void retired(GameTestHelper h, Reload r) {
        WeaponRuntime.tickPlayer(r.owner());
        CombatHud.update(r.owner());
        check(h, !WeaponRuntime.reloading(r.owner()) && !WeaponReloadPresentation.active(r.gun())
                        && node(r.owner(), "reload_track") == null && node(r.owner(), "reload") == null,
                "Retirement clears reload, live motion and phase HUD");
        if (r.owner().isAlive()) {
            check(h, !WeaponRuntime.ammunition(r.owner()).orElseThrow().reloading(), "No residual reload projection");
            if (WeaponReloadPresentation.supports(entry(r.gun())))
                check(h, motion(r.gun()) == -1 && WeaponFirstPersonHands.model(r.model()).equals(wire(r).get(DataComponents.ITEM_MODEL)),
                        "Retired wrapper restores the base wire model");
        }
    }
    private static void deniedShot(GameTestHelper h, Reload r) {
        var saved = r.gun().copy();
        check(h, !WeaponRuntime.beginUse(r.owner()), "Credited ammunition cannot bypass the full firing lock");
        WeaponRuntime.releaseUse(r.owner(), r.gun());
        check(h, ItemStack.matches(saved, r.gun()), "Denied early fire cannot consume ammo or retire motion");
    }
    private static void reaim(ServerPlayer p) {
        WeaponAiming.cleanup(p);
        p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
    }
    private static void shot(GameTestHelper h, ServerPlayer p) {
        reaim(p);
        // Stable real precision/body geometry for the earned Outlaw and Kill Clip setup.
        p.getRandom().setSeed(0x5DEECE66DL);
        var gun = p.getMainHandItem();
        int before = ammo(gun).rounds();
        check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == before - 1,
                "Actual accepted shot spends exactly one loaded cartridge");
        WeaponRuntime.releaseUse(p, gun);
    }
    private static Husk target(GameTestHelper h, ServerPlayer p, double y, float health) {
        double z = p.getZ() - h.absoluteVec(Vec3.ZERO).z;
        var e = h.spawn(EntityTypes.HUSK, new Vec3(8.5, y, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(health);
        TestCleanup.register(h, e::discard);
        var origin = h.absoluteVec(Vec3.ZERO); var b = e.getBoundingBox();
        check(h, b.minX > origin.x && b.maxX < origin.x + 16 && b.minY > origin.y
                        && b.maxY < origin.y + 8 && b.minZ > origin.z && b.maxZ < origin.z + 12,
                "Whole target AABB stays inside the existing W62 16x8x12 floor fixture");
        check(h, y == 1 ? p.getEyeY() >= b.maxY - b.getYsize() * .25 && p.getEyeY() < b.maxY
                        : p.getEyeY() > b.minY && p.getEyeY() < b.maxY - b.getYsize() * .25,
                "Actual horizontal ray crosses the requested precision/body geometry");
        return e;
    }
    private static void kill(GameTestHelper h, ServerPlayer p, boolean precision) {
        var victim = target(h, p, precision ? 1 : 1.8, 1);
        shot(h, p);
        check(h, victim.isDeadOrDying() && victim.getHealth() == 0, "Actual paid source-weapon final blow");
        victim.discard();
    }
    private static <T> List<T> packets(List<Packet<?>> queued, Class<T> type) {
        return queued.stream().filter(type::isInstance).map(type::cast).toList();
    }
    private static List<ClientboundSoundEntityPacket> sounds(List<Packet<?>> queued) {
        return packets(queued, ClientboundSoundEntityPacket.class).stream().filter(p ->
                p.getSound().value().location().getNamespace().equals("destiny")
                        && p.getSound().value().location().getPath().startsWith("weapon.reload_w63.")).toList();
    }
    private static ClientboundSoundEntityPacket startedSound(GameTestHelper h, Reload r) {
        var queued = TestPlayers.outbound(r.owner());
        var clips = sounds(queued);
        check(h, clips.size() == 1, "One accepted reload produces exactly one W63 entity sound");
        var sound = clips.getFirst();
        var clip = ReloadAudioProfile.find(entry(r.gun()), r.full()).orElseThrow();
        check(h, sound.getPitch() == 1f && sound.getSound().value().location()
                        .equals(Identifier.fromNamespaceAndPath("destiny", clip.event())) && clip.ticks() == r.full(),
                "W63 clip duration is captured full duration, never ammo-credit ticks");
        var spawns = packets(queued, ClientboundAddEntityPacket.class).stream()
                .filter(p -> p.getId() == sound.getId()).toList();
        check(h, spawns.size() == 1 && spawns.getFirst().getType() == EntityTypes.ITEM_DISPLAY
                        && queued.indexOf(spawns.getFirst()) < queued.indexOf(sound)
                        && sound.getId() != r.owner().getId() && r.owner().level().getEntity(sound.getId()) == null,
                "Source owns a separate client-only emitter spawned before its sound");
        return sound;
    }
    private static long removals(List<Packet<?>> queued, int emitter) {
        return packets(queued, ClientboundRemoveEntitiesPacket.class).stream()
                .filter(p -> p.entityIds().contains(emitter)).count();
    }
    private static void noStopOrReplay(GameTestHelper h, List<Packet<?>> queued, int a, int b, Reload... sources) {
        check(h, packets(queued, ClientboundStopSoundPacket.class).isEmpty()
                        && packets(queued, ClientboundSoundEntityPacket.class).stream()
                        .noneMatch(sound -> sound.getId() == a || sound.getId() == b)
                        && packets(queued, ClientboundAddEntityPacket.class).stream().noneMatch(spawn ->
                        spawn.getType() == EntityTypes.ITEM_DISPLAY && java.util.Arrays.stream(sources).anyMatch(r ->
                                new Vec3(spawn.getX(), spawn.getY(), spawn.getZ())
                                        .distanceToSqr(r.owner().getEyePosition()) < 1)),
                "Ammo credit/queries/full retirement never globally stop or restart reload audio");
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void allSixNormalReloadsCreditExactlyOnceButHudMotionAndFireWaitForFull(GameTestHelper h) {
        var reloads = new ArrayList<Reload>();
        for (int i = 0; i < NORMAL.size(); i++) {
            var t = NORMAL.get(i);
            var p = player(h, 2 + i * 1.5);
            var gun = equip(p, t.id(), 2, t.primary() ? 0 : 3);
            check(h, profile(gun).infiniteReserve() == t.primary() && !profile(gun).shellReload()
                            && WeaponOutlaw.remaining(p) == 0 && WeaponKillClip.remaining(p) == 0,
                    "Normal six-weapon fixture uses actual reserve policy without fabricated perks");
            var r = start(h, p, gun, t.full(), t.credit());
            reloads.add(r);
            check(h, t.credit() == (int) Math.ceil(t.full() * (t.primary() ? .71 : .65)),
                    "Pinned source-6 explicit HC .71 / MG .65 fraction");
            h.runAfterDelay(r.credit() - 1, () -> {
                phase(h, r, r.credit() - 1); amounts(h, r, 2, t.primary() ? 0 : 3); deniedShot(h, r);
            });
            h.runAfterDelay(r.credit(), () -> {
                phase(h, r, r.credit()); credited(h, r); deniedShot(h, r);
                for (int n = 0; n < 8; n++) {
                    WeaponRuntime.tickPlayer(p); AmmoHud.current(p); CombatHud.update(p);
                    check(h, !WeaponRuntime.reload(p), "Duplicate reload remains denied after credit");
                }
                credited(h, r); phase(h, r, r.credit());
                check(h, t.primary() ? r.loaded() == r.profile().magazine() : r.loaded() == 5 && r.left() == 0,
                        "Primary fills while each short finite MG transfers exactly its three reserve rounds");
            });
            h.runAfterDelay(r.full() - 1, () -> { phase(h, r, r.full() - 1); credited(h, r); deniedShot(h, r); });
            h.runAfterDelay(r.full(), () -> {
                retired(h, r); credited(h, r);
                digits(h, p, "rounds", r.loaded());
                shot(h, p);
                check(h, ammo(gun).rounds() == r.loaded() - 1 && ammo(gun).reserve() == r.left(),
                        "First full-deadline shot, rather than credit, spends loaded ammunition");
            });
        }
        drive(h, reloads.toArray(Reload[]::new));
        h.runAfterDelay(107, h::succeed);
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void sameEventEmittersSurviveCreditAndOnlyTheirOwnFullFinishOrCancelRemovesThem(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 9.5);
        var hearer = TestPlayers.create(h, new Vec3(3.5, 1, 6.5), 0, 0);
        hearer.setGameMode(GameType.SPECTATOR);
        h.getLevel().players().add(hearer);
        TestCleanup.register(h, () -> { h.getLevel().players().remove(hearer); TestPlayers.remove(hearer); });
        var gunA = equip(a, DUKE, 2, 0); var gunB = equip(b, DUKE, 2, 0);
        TestPlayers.drain(hearer);
        var ra = start(h, a, gunA, 59, 42); var sa = startedSound(h, ra);
        var rb = start(h, b, gunB, 59, 42); var sb = startedSound(h, rb);
        var heard = TestPlayers.outbound(hearer);
        check(h, sa.getId() != sb.getId() && sa.getSound().value().location().equals(sb.getSound().value().location())
                        && sounds(heard).stream().filter(p -> p.getId() == sa.getId() || p.getId() == sb.getId()).count() == 2,
                "Nearby spectator receives two distinct source emitters for the same full-duration event");
        var later = new ArrayList<Packet<?>>();
        h.onEachTick(() -> {
            WeaponRuntime.tickPlayer(a); WeaponRuntime.tickPlayer(b);
            later.addAll(TestPlayers.outbound(hearer));
            TestPlayers.drain(a); TestPlayers.drain(b);
        });
        h.runAfterDelay(42, () -> {
            phase(h, ra, 42); phase(h, rb, 42); credited(h, ra); credited(h, rb);
            for (int i = 0; i < 8; i++) { check(h, !WeaponRuntime.reload(b), "Credited duplicate cannot replay sound"); AmmoHud.current(b); }
            later.addAll(TestPlayers.outbound(hearer));
            check(h, removals(later, sa.getId()) == 0 && removals(later, sb.getId()) == 0,
                    "Neither source emitter is removed at ammo credit");
            noStopOrReplay(h, later, sa.getId(), sb.getId(), ra, rb);
        });
        h.runAfterDelay(43, () -> {
            WeaponRuntime.cancelUseForSkill(a); retired(h, ra); credited(h, ra);
            b.setPos(b.position().add(.25, 0, 0)); WeaponRuntime.tickPlayer(b);
            later.addAll(TestPlayers.outbound(hearer));
            check(h, removals(later, sa.getId()) == 1 && removals(later, sb.getId()) == 0
                            && packets(later, ClientboundTeleportEntityPacket.class).stream().anyMatch(p -> p.id() == sb.getId()),
                    "Post-credit cancellation stops only A; B's same-event source keeps following");
            noStopOrReplay(h, later, sa.getId(), sb.getId(), ra, rb);
        });
        h.runAfterDelay(58, () -> {
            phase(h, rb, 58); credited(h, rb); later.addAll(TestPlayers.outbound(hearer));
            check(h, removals(later, sb.getId()) == 0, "Surviving source remains until the last full-phase tick");
            noStopOrReplay(h, later, sa.getId(), sb.getId(), ra, rb);
        });
        h.runAfterDelay(59, () -> {
            retired(h, rb); credited(h, rb); later.addAll(TestPlayers.outbound(hearer));
            check(h, removals(later, sa.getId()) == 1 && removals(later, sb.getId()) == 1,
                    "Each original source emitter is removed exactly once at its own retirement");
            noStopOrReplay(h, later, sa.getId(), sb.getId(), ra, rb);
        });
        h.runAfterDelay(65, () -> {
            credited(h, ra); credited(h, rb); later.addAll(TestPlayers.outbound(hearer));
            check(h, removals(later, sa.getId()) == 1 && removals(later, sb.getId()) == 1, "No delayed duplicate removal");
            noStopOrReplay(h, later, sa.getId(), sb.getId(), ra, rb); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 250, environment = "destiny-test:w90_isolated")
    public void earnedOutlawCapturesTwentyFourAndThirtyThreeAcrossExpiryThenNextReloadUsesBase(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(p, DUKE, 9, 0);
        check(h, WeaponPerks.select(gun, OutlawProfile.ID), "Actual official Duke Outlaw socket selected");
        kill(h, p, true);
        check(h, ammo(gun).rounds() == 8 && WeaponOutlaw.remaining(p) == 120,
                "Paid precision final blow earns a real 120-tick window");
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); });
        // Capture runtime-owned reloads later; register every observation now.
        var phases = new Reload[2];
        h.runAfterDelay(119, () -> {
            check(h, WeaponOutlaw.remaining(p) == 1, "Capture on last earned Outlaw tick");
            phases[0] = start(h, p, gun, 33, 24); startedSound(h, phases[0]);
        });
        h.runAfterDelay(120, () -> {
            var r = phases[0]; phase(h, r, 1); amounts(h, r, 8, 0);
            check(h, WeaponOutlaw.remaining(p) == 0, "Real Outlaw expires without retiming captured full or credit");
        });
        h.runAfterDelay(119 + 23, () -> { var r = phases[0]; phase(h, r, 23); amounts(h, r, 8, 0); });
        h.runAfterDelay(119 + 24, () -> { var r = phases[0]; phase(h, r, 24); credited(h, r); deniedShot(h, r); });
        h.runAfterDelay(119 + 32, () -> { var r = phases[0]; phase(h, r, 32); credited(h, r); deniedShot(h, r); });
        h.runAfterDelay(119 + 33, () -> {
            var r = phases[0]; retired(h, r); credited(h, r);
            check(h, WeaponOutlaw.remaining(p) == 0, "Full finish cannot restore expired Outlaw");
            var tank = target(h, p, 1.8, 1000); shot(h, p);
            check(h, tank.isAlive() && tank.getHealth() < 1000, "Fresh real nonlethal shot creates next reload deficit");
            tank.discard();
            phases[1] = start(h, p, gun, 59, 42); startedSound(h, phases[1]);
        });
        h.runAfterDelay(119 + 33 + 24, () -> { var next = phases[1]; phase(h, next, 24); amounts(h, next, 8, 0); });
        h.runAfterDelay(119 + 33 + 41, () -> { var next = phases[1]; phase(h, next, 41); amounts(h, next, 8, 0); });
        h.runAfterDelay(119 + 33 + 42, () -> { var next = phases[1]; phase(h, next, 42); credited(h, next); deniedShot(h, next); });
        h.runAfterDelay(119 + 33 + 58, () -> { var next = phases[1]; phase(h, next, 58); credited(h, next); deniedShot(h, next); });
        h.runAfterDelay(119 + 33 + 59, () -> { var next = phases[1]; retired(h, next); credited(h, next); h.succeed(); });
    }

    @GameTest(structure = FLOOR, maxTicks = 180, environment = "destiny-test:w90_isolated")
    public void actualKillClipKillActivatesAtAmmoCreditAndFullFinishCannotRefreshIt(GameTestHelper h) {
        var p = player(h, 3.5); var gun = equip(p, DUKE, 9, 0);
        var control = player(h, 9.5); equip(control, DUKE, 9, 0);
        check(h, WeaponPerks.select(gun, KillClipProfile.ID), "Official Duke Kill Clip is feasible and selected");
        kill(h, p, false); kill(h, control, false);
        check(h, WeaponKillClip.remaining(p) == 0 && WeaponOutlaw.remaining(p) == 0, "Body kill arms only pending Kill Clip");
        var r = start(h, p, gun, 59, 42);
        drive(h, r);
        h.runAfterDelay(41, () -> {
            phase(h, r, 41); amounts(h, r, 8, 0);
            check(h, WeaponKillClip.remaining(p) == 0, "No activation one tick before actual ammo transfer");
        });
        h.runAfterDelay(42, () -> {
            phase(h, r, 42); credited(h, r); deniedShot(h, r);
            check(h, WeaponKillClip.remaining(p) == 100 && WeaponKillClip.capture(p).multiplier() == 1.25f,
                    "Persisted credit invokes real Kill Clip reload activation while full phase is still locked");
            for (int i = 0; i < 8; i++) WeaponRuntime.tickPlayer(p);
            check(h, WeaponKillClip.remaining(p) == 100, "Duplicate credit processing does not consume or restart buff time");
        });
        h.runAfterDelay(58, () -> {
            phase(h, r, 58); deniedShot(h, r);
            check(h, WeaponKillClip.remaining(p) == 84, "Kill Clip clock starts at credit rather than full finish");
        });
        h.runAfterDelay(59, () -> {
            retired(h, r); credited(h, r);
            for (int i = 0; i < 8; i++) WeaponRuntime.tickPlayer(p);
            check(h, WeaponKillClip.remaining(p) == 83, "Full finish retires cycle without a second reloaded notification");
            var buffed = target(h, p, 1.8, 1000); var plain = target(h, control, 1.8, 1000);
            shot(h, p); shot(h, control);
            float baseline = 1000 - plain.getHealth();
            check(h, baseline > 0 && Math.abs((1000 - buffed.getHealth()) - baseline * 1.25f) < .002f,
                    "First legal post-full shot deals actual 1.25x body HP damage");
            buffed.discard(); plain.discard();
        });
        h.runAfterDelay(141, () -> check(h, WeaponKillClip.remaining(p) == 1, "Last buff tick is credit+99"));
        h.runAfterDelay(142, () -> {
            check(h, WeaponKillClip.remaining(p) == 0 && WeaponKillClip.capture(p).multiplier() == 1,
                    "Buff expires at credit+100, with no full-finish refresh"); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void cancellationBeforeAndAfterCreditCannotGhostTransferOrDoubleFill(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 9.5);
        var before = start(h, a, equip(a, "hammerhead", 2, 3), 91, 60);
        var after = start(h, b, equip(b, "hammerhead", 2, 3), 91, 60);
        drive(h, before, after);
        h.runAfterDelay(59, () -> {
            phase(h, before, 59); amounts(h, before, 2, 3);
            WeaponRuntime.cancelUseForSkill(a); WeaponRuntime.cancelUseForSkill(a);
            retired(h, before); amounts(h, before, 2, 3);
        });
        h.runAfterDelay(60, () -> {
            phase(h, after, 60); credited(h, after); amounts(h, before, 2, 3);
            WeaponRuntime.cancelUseForSkill(b); WeaponRuntime.cancelUseForSkill(b);
            retired(h, after); credited(h, after);
        });
        h.runAfterDelay(92, () -> {
            retired(h, before); retired(h, after); amounts(h, before, 2, 3); credited(h, after);
            check(h, !WeaponRuntime.reload(b), "Credited finite reserve stays exhausted after cancellation");
        });
        h.runAfterDelay(120, () -> {
            amounts(h, before, 2, 3); credited(h, after); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 140, environment = "destiny-test:w90_isolated")
    public void creditReturnsTrueOnceFullReturnsFalseAndRoomCannotStartSecondProductionReload(GameTestHelper h) {
        var p = player(h, 6.5); var e = WeaponCatalog.find("hammerhead").orElseThrow();
        var f = WeaponProfile.forEntry(e);
        var r = start(h, p, equip(p, e.id(), 2, f.magazine() + 5), 91, 60);
        // A companion generic cycle uses the SAME advancing server tick and captured plan.
        // Its return value is the runtime's WeaponItems.save / KillClip.reloaded contract.
        var cycle = new WeaponCycle();
        var magazine = new WeaponMagazine(f, r.rounds(), r.reserve());
        check(h, cycle.startReload(now(p), f, magazine, base(f), ReloadCreditProfile.ammoTicks(e, base(f))),
                "Generic distinct-credit overload accepts captured normal plan");
        drive(h, r);
        h.runAfterDelay(59, () -> {
            phase(h, r, 59); amounts(h, r, 2, f.magazine() + 5);
            check(h, !cycle.finishReload(now(p), magazine) && magazine.rounds() == 2,
                    "Generic finish returns false before ammo-credit deadline");
        });
        h.runAfterDelay(60, () -> {
            phase(h, r, 60); credited(h, r);
            check(h, cycle.finishReload(now(p), magazine) && !cycle.finishReload(now(p), magazine)
                            && cycle.reloading() && !cycle.ready(now(p)) && cycle.reloadPhaseTicks() == 91
                            && cycle.reloadRemaining(now(p)) == 31 && magazine.rounds() == f.magazine()
                            && magazine.reserve() == 7 && magazine.total() == r.total(),
                    "Exactly one true transfer; generic phase, remaining time and ready lock still use full deadline");
            // Explicit external ammo fixture: create magazine room while finite reserve remains.
            // An actual shot is forbidden here; only the reload-start eligibility is under test.
            var changed = ammo(r.gun());
            check(h, changed.consume() && magazine.consume(), "Create one real deficit without cancelling either cycle");
            WeaponItems.save(r.gun(), changed);
            check(h, changed.canReload() && magazine.canReload(), "Room AND finite reserve make a second reload otherwise eligible");
            for (int i = 0; i < 8; i++) {
                check(h, !WeaponRuntime.reload(p) && !cycle.startReload(now(p), f, magazine, base(f), 60),
                        "Active full phase denies second production and generic reload despite available room/reserve");
                WeaponRuntime.tickPlayer(p);
                check(h, !cycle.finishReload(now(p), magazine), "Already-credited generic cycle cannot transfer twice");
            }
            deniedShot(h, r);
        });
        h.runAfterDelay(90, () -> {
            phase(h, r, 90); amounts(h, r, f.magazine() - 1, 7, r.total() - 1); deniedShot(h, r);
            check(h, !cycle.finishReload(now(p), magazine) && cycle.reloading() && !cycle.ready(now(p)),
                    "Last full-phase tick neither refills new room nor unlocks generic firing");
        });
        h.runAfterDelay(91, () -> {
            retired(h, r); amounts(h, r, f.magazine() - 1, 7, r.total() - 1);
            check(h, !cycle.finishReload(now(p), magazine) && !cycle.reloading() && cycle.ready(now(p))
                            && magazine.rounds() == f.magazine() - 1 && magazine.reserve() == 7
                            && magazine.total() == r.total() - 1,
                    "Full finish returns false, retires generic cycle, and preserves post-credit deficit/reserve");
            check(h, WeaponRuntime.reload(p), "Production start becomes eligible exactly when original full phase retires");
            check(h, WeaponRuntime.ammunition(p).orElseThrow().reloadRemaining() == 91,
                    "Accepted second reload starts a new full phase only after the first is over");
            WeaponRuntime.cancelUseForSkill(p);
        });
        h.runAfterDelay(100, () -> {
            check(h, !cycle.finishReload(now(p), magazine), "Retired generic finish stays false on later ticks");
            amounts(h, r, f.magazine() - 1, 7, r.total() - 1); h.succeed();
        });
    }

    private static void swapAwayAndBack(GameTestHelper h, Reload r) {
        var p = r.owner(); int slot = p.getInventory().getSelectedSlot(); long tick = now(p);
        p.getInventory().setItem(7, new ItemStack(Items.STONE));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
        WeaponRuntime.tickPlayer(p);
        check(h, now(p) == tick && p.getMainHandItem() == r.gun() && !WeaponRuntime.reloading(p),
                "Validated server slot handlers observe same-tick away/back and cancel captured reload");
        retired(h, r);
    }

    @GameTest(structure = FLOOR, maxTicks = 110, environment = "destiny-test:w90_isolated")
    public void sameTickSwapBeforeAndAfterCreditPreservesEachOwnersIndependentAmmo(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 6.5); var c = player(h, 9.5);
        var early = start(h, a, equip(a, DUKE, 2, 0), 59, 42);
        var late = start(h, b, equip(b, DUKE, 2, 0), 59, 42);
        var survivor = start(h, c, equip(c, DUKE, 2, 0), 59, 42);
        swapAwayAndBack(h, early); amounts(h, early, 2, 0);
        drive(h, early, late, survivor);
        h.runAfterDelay(42, () -> {
            phase(h, late, 42); phase(h, survivor, 42); credited(h, late); credited(h, survivor);
            var independent = survivor.gun().copy();
            swapAwayAndBack(h, late); credited(h, late); amounts(h, early, 2, 0);
            check(h, ItemStack.matches(independent, survivor.gun()) && WeaponRuntime.reloading(c),
                    "Other owner's same-tick credited stow cannot change survivor's ammo, motion or deadline");
            phase(h, survivor, 42);
        });
        h.runAfterDelay(58, () -> { phase(h, survivor, 58); credited(h, late); amounts(h, early, 2, 0); });
        h.runAfterDelay(59, () -> { retired(h, survivor); credited(h, survivor); });
        h.runAfterDelay(85, () -> {
            retired(h, early); retired(h, late); amounts(h, early, 2, 0); credited(h, late); credited(h, survivor);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 150, environment = "destiny-test:w90_isolated")
    public void postCreditCleanupAndDeathPreserveFiniteLoadedAmmoAndOtherOwnersFullPhase(GameTestHelper h) {
        var a = player(h, 3.5); var b = player(h, 6.5); var c = player(h, 9.5);
        var cleaned = start(h, a, equip(a, "hammerhead", 2, 3), 91, 60);
        var dead = start(h, b, equip(b, "hammerhead", 2, 3), 91, 60);
        var survivor = start(h, c, equip(c, "hammerhead", 2, 3), 91, 60);
        drive(h, cleaned, dead, survivor);
        h.runAfterDelay(60, () -> {
            for (var r : List.of(cleaned, dead, survivor)) { phase(h, r, 60); credited(h, r); }
            var independent = survivor.gun().copy();
            WeaponRuntime.cleanup(a); WeaponRuntime.cleanup(a);
            b.setHealth(0); WeaponRuntime.tickPlayer(b); WeaponRuntime.tickPlayer(b);
            retired(h, cleaned); retired(h, dead); credited(h, cleaned); credited(h, dead);
            check(h, AmmoHud.current(b).isEmpty() && ItemStack.matches(independent, survivor.gun()),
                    "Death hides its HUD and repeated owner retirement cannot mutate survivor's credited stack");
            phase(h, survivor, 60); deniedShot(h, survivor);
        });
        h.runAfterDelay(90, () -> { phase(h, survivor, 90); credited(h, cleaned); credited(h, dead); });
        h.runAfterDelay(91, () -> { retired(h, survivor); credited(h, survivor); });
        h.runAfterDelay(120, () -> {
            for (var r : List.of(cleaned, dead, survivor)) { retired(h, r); credited(h, r); }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void excludedCatalogBelovedAndIncrementalShellDeadlinesRemainUnchanged(GameTestHelper h) {
        for (var e : WeaponModelGameTests.originalW30Entries()) {
            if (NORMAL.stream().anyMatch(t -> t.id().equals(e.id()))) continue;
            var f = WeaponProfile.forEntry(e);
            check(h, ReloadCreditProfile.ammoTicks(e, base(f)) == f.firstReloadTicks(),
                    "No source-6 fraction leaks to excluded catalog entry " + e.id());
        }
        var p = player(h, 3.5); var q = player(h, 9.5);
        var beloved = start(h, p, equip(p, "beloved", 1, 2), 62, 62);
        var slug = start(h, q, equip(q, "first_in_last_out", 3, 2), 15, 15);
        check(h, slug.profile().shellReload() && slug.profile().roundsPerInsert() == 1
                        && !slug.profile().infiniteReserve() && beloved.loaded() == 3,
                "Excluded fixtures use real finite short reserves and original one-slug granularity");
        drive(h, beloved, slug);
        h.runAfterDelay(14, () -> { phase(h, slug, 14); amounts(h, slug, 3, 2); });
        h.runAfterDelay(15, () -> {
            WeaponRuntime.tickPlayer(q); CombatHud.update(q);
            var state = WeaponRuntime.ammunition(q).orElseThrow();
            amounts(h, slug, 4, 1); digits(h, q, "rounds", 4); digits(h, q, "reserve", 1);
            check(h, state.reloading() && state.reloadDuration() == 15 && state.reloadRemaining() == 15,
                    "First original shell deadline transfers ONE slug and starts its original repeat phase");
            for (int i = 0; i < 8; i++) WeaponRuntime.tickPlayer(q);
            amounts(h, slug, 4, 1);
        });
        h.runAfterDelay(29, () -> { WeaponRuntime.tickPlayer(q); amounts(h, slug, 4, 1); });
        h.runAfterDelay(30, () -> {
            retired(h, slug); amounts(h, slug, 5, 0);
            check(h, !WeaponRuntime.reload(q), "Original second insert stops at reserve exhaustion, below capacity");
        });
        h.runAfterDelay(44, () -> { phase(h, beloved, 44); amounts(h, beloved, 1, 2); });
        h.runAfterDelay(61, () -> { phase(h, beloved, 61); amounts(h, beloved, 1, 2); deniedShot(h, beloved); });
        h.runAfterDelay(62, () -> {
            retired(h, beloved); credited(h, beloved); digits(h, p, "rounds", 3); digits(h, p, "reserve", 0);
            check(h, !WeaponRuntime.reload(p), "Beloved keeps its full-duration transfer and exhausted finite reserve");
        });
        h.runAfterDelay(80, () -> { credited(h, beloved); amounts(h, slug, 5, 0); h.succeed(); });
    }
}
