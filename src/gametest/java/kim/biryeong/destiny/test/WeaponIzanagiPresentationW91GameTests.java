package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.UUID;

/** Production runtime/packet tests. All deadlines register at initialization, with W90 terminal cleanup.
 * Packet Q/slot tests are fixtures, not claims of supported Vision native Q/slot input or audio listening.
 */
public final class WeaponIzanagiPresentationW91GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final int SLOT = WeaponIzanagiPresentation.SELECTOR_INDEX;

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static CustomModelData data(ItemStack stack) {
        return stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
    }
    private static float selector(ItemStack stack) {
        return data(stack).floats().size() > SLOT ? data(stack).floats().get(SLOT) : -1;
    }
    private static boolean restoredAbsent(ItemStack stack, List<Float> prefix) {
        var values = data(stack).floats();
        return values.size() == SLOT && values.subList(0, prefix.size()).equals(prefix);
    }
    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }
    private static void state(GameTestHelper h, ItemStack stack, int loaded, int reserve, int charge) {
        var a = ammo(stack);
        check(h, a.rounds() == loaded && a.reserve() == reserve && a.overflow() == 0
                        && WeaponIzanagi.charge(stack) == charge,
                "Exact production ammo/charge: " + loaded + "/" + reserve + " x" + charge
                        + "; actual " + a.rounds() + "/" + a.reserve() + " x" + WeaponIzanagi.charge(stack));
    }
    private static void range(GameTestHelper h, ItemStack stack, float low, float high) {
        check(h, WeaponIzanagiPresentation.active(stack) && selector(stack) >= low && selector(stack) < high,
                "Live slot6 must be in " + low + ".." + high + "; actual " + selector(stack));
    }
    private static void request(GameTestHelper h, ServerPlayer p, boolean honed) {
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(honed
                ? ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS
                : ServerboundPlayerActionPacket.Action.DROP_ITEM, BlockPos.ZERO, Direction.UP));
        check(h, WeaponRuntime.reloading(p) && WeaponIzanagi.honing(p) == honed,
                "Actual Q/CtrlQ packet admits the intended owned reload");
    }
    private static ItemStack wire(GameTestHelper h, ServerPlayer p, ItemStack stack) {
        var context = ((PacketContextProvider) (Object) p.connection).getPacketContext();
        return PolymerItemUtils.getPolymerItemStack(stack, context, h.getLevel().registryAccess());
    }

    private static final class Fixture {
        final GameTestHelper h;
        final long created;
        final List<ServerPlayer> players = new ArrayList<>();
        final List<ItemStack> stacks = new ArrayList<>();

        Fixture(GameTestHelper h) {
            this.h = h; created = h.getLevel().getServer().getTickCount();
            // Registered before construction/mutation so setup failures also release owned state.
            TestCleanup.register(h, () -> {
                for (var p : players) {
                    WeaponRuntime.cleanup(p);
                    for (var s : stacks) WeaponIzanagiPresentation.clear(p, s);
                    p.setServerLevel(h.getLevel()); p.stopUsingItem(); ads(p, false);
                    WeaponPerkHud.remove(p); CombatHud.remove(p); TestPlayers.remove(p);
                }
            });
            for (int x = 0; x < 48; x++) for (int z = 0; z < 32; z++) h.setBlock(x, 3, z, Blocks.STONE);
            h.onEachTick(() -> {
                var origin = h.absoluteVec(Vec3.ZERO);
                for (var p : players) {
                    var b = p.getBoundingBox();
                    check(h, p.level() == h.getLevel() && b.minX > origin.x && b.maxX < origin.x + 48
                                    && b.minY > origin.y && b.maxY < origin.y + 12
                                    && b.minZ > origin.z && b.maxZ < origin.z + 32,
                            "Entire owned fake player AABB remains in its isolated fixture");
                }
            });
        }
        ServerPlayer player(int z) {
            var p = TestPlayers.create(h, new Vec3(3, 4, z), -90, 90,
                    "W91_" + UUID.randomUUID().toString().substring(0, 8));
            players.add(p); p.setNoGravity(true); p.setOnGround(true);
            p.setAttached(WeaponLoadout.ENABLED, false);
            return p;
        }
        ItemStack equip(ServerPlayer p, int loaded, int reserve) {
            var e = WeaponCatalog.find("izanagis_burden").orElseThrow();
            var s = WeaponItems.create(e); stacks.add(s);
            s.set(DataComponents.CUSTOM_NAME, Component.literal("W91_" + UUID.randomUUID()));
            WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), loaded, reserve));
            p.getInventory().setItem(0, s); p.getInventory().setSelectedSlot(0);
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p);
            return s;
        }
        void at(int ticks, Runnable action) {
            check(h, h.getLevel().getServer().getTickCount() == created,
                    "Static callback lifecycle: register every deadline at test initialization");
            h.runAfterDelay(ticks, () -> {
                check(h, h.getLevel().getServer().getTickCount() - created == ticks,
                        "Observe actual server tick " + ticks + ", never a reflected clock");
                for (var p : players) { WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); }
                action.run();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void w198OrdinaryAndHonedNoLongerHoldEachOfTwentyOnePosesForSeveralTicks(GameTestHelper h) {
        var f = new Fixture(h); var normal=f.player(8); var honed=f.player(24);
        var a=f.equip(normal,1,5); var b=f.equip(honed,1,5);
        var normalFrames=new java.util.HashSet<Float>(); var honedFrames=new java.util.HashSet<Float>();
        request(h,normal,false); request(h,honed,true);
        for(int tick=1;tick<=60;tick++) f.at(tick,()->{
            range(h,a,0,1.01f); range(h,b,2,3.01f);
            normalFrames.add(wire(h,normal,a).get(DataComponents.CUSTOM_MODEL_DATA).getFloat(SLOT));
            honedFrames.add(wire(h,honed,b).get(DataComponents.CUSTOM_MODEL_DATA).getFloat(SLOT));
            state(h,a,1,5,0); state(h,b,1,5,0);
        });
        f.at(61,()->{
            check(h,normalFrames.size()>45 && honedFrames.size()>45,
                    "Both actual wire selectors advance near each tick; ordinary="+normalFrames.size()+", honed="+honedFrames.size());
            state(h,a,4,2,0); state(h,b,1,2,4);
            check(h,!WeaponRuntime.reloading(normal)&&!WeaponRuntime.reloading(honed),"Gameplay commit stays61 ticks");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void normalAndHonedSeparateUntilRealCommitAndPaidShotClearsCompletedCue(GameTestHelper h) {
        var f = new Fixture(h); var normal = f.player(8); var honed = f.player(24);
        var a = f.equip(normal, 1, 5); var b = f.equip(honed, 1, 5);
        var before = data(a).floats();
        request(h, normal, false); request(h, honed, true);
        range(h, a, 0, 1.01f); range(h, b, 2, 3.01f);
        state(h, a, 1, 5, 0); state(h, b, 1, 5, 0);
        check(h, wire(h, honed, b).get(DataComponents.ITEM_MODEL).equals(projected(WeaponIzanagiPresentation.model(b))),
                "Actual Polymer serialization selects the live W91 model immediately");
        f.at(30, () -> {
            range(h, a, .45f, .51f); range(h, b, 2.45f, 2.51f);
            var unchanged = b.copy(); WeaponRuntime.tickPlayer(honed);
            check(h, ItemStack.matches(unchanged, b), "Same server sample is idempotent");
        });
        f.at(60, () -> {
            state(h, a, 1, 5, 0); state(h, b, 1, 5, 0);
            range(h, a, .95f, 1.01f); range(h, b, 2.95f, 3.01f);
        });
        f.at(61, () -> {
            state(h, a, 4, 2, 0); state(h, b, 1, 2, 4);
            check(h, !WeaponRuntime.reloading(normal) && !WeaponRuntime.reloading(honed)
                            && !WeaponIzanagi.honing(honed), "Real full-ready transactions finished");
            check(h, !WeaponIzanagiPresentation.active(a) && restoredAbsent(a, before),
                    "Ordinary reload never creates a charged cue and removes slot6 without trimming unrelated lower slots");
            range(h, b, 4, 4.01f);
        });
        f.at(65, () -> {
            // Genuine funded hitscan into the stone floor. No fake shot()/finishReload()/charge tag grants.
            WeaponAiming.cleanup(honed); ads(honed, false); honed.setXRot(90);
            WeaponAiming.tick(honed);
            check(h, WeaponRuntime.beginUse(honed), "Real paid charged miss admitted after actual61 commit");
            WeaponRuntime.releaseUse(honed, b); honed.stopUsingItem();
            state(h, b, 0, 2, 0);
            check(h, !WeaponIzanagiPresentation.active(b) || selector(b) < 2,
                    "Same paid emission removes completed cue; only an actual ordinary auto reload may render");
            check(h, !b.get(DataComponents.CUSTOM_DATA).copyTag().contains(WeaponIzanagi.CHARGE),
                    "Actual shot clears W84 saved charge without a cosmetic authority field");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void skillStowCopyLevelAndDeathCancelExactPendingIdentityWithoutChargedCue(GameTestHelper h) {
        var f = new Fixture(h);
        var guns = new ArrayList<ItemStack>();
        for (int i = 0; i < 5; i++) {
            var p = f.player(4 + i * 5); guns.add(f.equip(p, 2, 2)); request(h, p, true);
        }
        var other = h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER) ? Level.OVERWORLD : Level.NETHER);
        check(h, other != null && other != h.getLevel(), "Distinct production ServerLevel available");
        var copy = new ItemStack[1];
        f.at(20, () -> {
            WeaponRuntime.cancelUseForSkill(f.players.get(0));
            var stow = f.players.get(1); stow.getInventory().setItem(1, new ItemStack(Items.STONE));
            stow.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            stow.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
            var replace = f.players.get(2); copy[0] = guns.get(2).copy(); f.stacks.add(copy[0]);
            replace.getInventory().setItem(0, copy[0]); WeaponRuntime.tickPlayer(replace);
            check(h, !WeaponIzanagiPresentation.active(copy[0]), "Copied persisted float6 cannot bind a live generation");
            var traveler = f.players.get(3); traveler.setServerLevel(other);
            check(h, !WeaponIzanagiPresentation.active(guns.get(3)), "Pure getter rejects changed level before cleanup");
            WeaponRuntime.tickPlayer(traveler); traveler.setServerLevel(h.getLevel()); WeaponRuntime.tickPlayer(traveler);
            var dying = f.players.get(4); dying.setHealth(0);
            check(h, !WeaponIzanagiPresentation.active(guns.get(4)), "Pure getter rejects dead owner before cleanup");
            WeaponRuntime.tickPlayer(dying); dying.setHealth(20); WeaponRuntime.tickPlayer(dying);
            for (var s : guns) check(h, !WeaponIzanagiPresentation.active(s), "Every cancelled original binding is inactive");
        });
        f.at(62, () -> {
            for (var s : guns) state(h, s, 2, 2, 0);
            state(h, copy[0], 2, 2, 0);
            for (var p : f.players) check(h, !WeaponRuntime.reloading(p) && !WeaponIzanagi.honing(p),
                    "Cancelled generation cannot complete at its old61 deadline");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void clearRestoresOnlyOwnedFloatSixAndPreservesConcurrentSelectorsAndMetadata(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(8); var stranger = f.player(24);
        var s = f.equip(p, 2, 2); f.equip(stranger, 2, 2);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(
                List.of(11f, 12f, 13f, .35f, 14f, 15f, 91f, 17f), List.of(true, false), List.of("hip", "before"), List.of(0x123456)));
        request(h, p, true);
        f.at(10, () -> {
            var values = new ArrayList<>(data(s).floats());
            values.set(0, 21f); values.set(1, 22f); values.set(2, 23f); values.set(3, .6f);
            values.set(4, 24f); values.set(5, 25f); values.set(7, 27f); values.add(28f);
            s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values,
                    List.of(true, true, false), List.of("scope", "concurrent"), List.of(0xabcdef, 0x314159)));
            var concurrent = data(s);
            WeaponIzanagiPresentation.clear(stranger, s);
            check(h, data(s).equals(concurrent) && WeaponIzanagiPresentation.active(s),
                    "Foreign-owner clear is a strict no-op on live owner and selectors");
            WeaponRuntime.cancelUseForSkill(p);
            var expected = new ArrayList<>(values); expected.set(SLOT, 91f);
            check(h, data(s).equals(new CustomModelData(expected, concurrent.flags(), concurrent.strings(), concurrent.colors())),
                    "Restore only original float6; preserve all concurrently changed lower/higher floats, flags, strings and colors");
            state(h, s, 2, 2, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void exactStackTransferRebindsRecipientAndLateDonorClearCannotRestoreRecipientsSelectors(GameTestHelper h) {
        var f = new Fixture(h); var donor = f.player(8); var recipient = f.player(24);
        var s = f.equip(donor, 2, 2); var replaced = f.equip(recipient, 2, 2);
        var values = new ArrayList<>(data(s).floats());
        while (values.size() <= SLOT) values.add(0f); values.set(SLOT, 77f);
        s.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(values, data(s).flags(), data(s).strings(), data(s).colors()));
        request(h, donor, true);
        f.at(20, () -> {
            donor.getInventory().setItem(0, replaced); recipient.getInventory().setItem(0, s);
            check(h, !WeaponIzanagiPresentation.active(s), "Exact owner identity invalidates donor getter before a runtime tick");
            WeaponRuntime.tickPlayer(donor); WeaponRuntime.tickPlayer(recipient);
            state(h, s, 2, 2, 0);
        });
        f.at(40, () -> {
            check(h, !WeaponHandling.blocked(recipient), "Recipient pays actual handling before fresh reload");
            request(h, recipient, true); range(h, s, 2, 3.01f);
            var current = data(s);
            WeaponIzanagiPresentation.clear(donor, s); WeaponRuntime.cleanup(donor);
            check(h, data(s).equals(current) && WeaponIzanagiPresentation.active(s),
                    "Late donor cleanup cannot restore donor snapshot over recipient generation");
        });
        f.at(61, () -> { state(h, s, 2, 2, 0); range(h, s, 2, 3.01f); });
        f.at(100, () -> { state(h, s, 2, 2, 0); range(h, s, 2.95f, 3.01f); });
        f.at(101, () -> {
            state(h, s, 1, 0, 4); range(h, s, 4, 4.01f);
            WeaponRuntime.cleanup(recipient);
            check(h, selector(s) == 77f && !WeaponIzanagiPresentation.active(s), "Recipient cleanup restores original float6 exactly");
            state(h, s, 1, 0, 4); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void absentFloatSixKeepsLaterHigherSlotsAndExternalReplacementWinsRestoration(GameTestHelper h) {
        var f = new Fixture(h); var a = f.player(8); var b = f.player(24);
        var absent = f.equip(a, 2, 2); var replaced = f.equip(b, 2, 2);
        absent.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(List.of(11f, 12f), List.of(true), List.of("hip"), List.of(0x123456)));
        request(h, a, true); request(h, b, true);
        f.at(10, () -> {
            var higher = new ArrayList<>(data(absent).floats()); higher.add(71f); higher.add(81f);
            absent.set(DataComponents.CUSTOM_MODEL_DATA,
                    new CustomModelData(higher, data(absent).flags(), data(absent).strings(), data(absent).colors()));
            var foreign = new ArrayList<>(data(replaced).floats()); foreign.set(SLOT, 901f);
            replaced.set(DataComponents.CUSTOM_MODEL_DATA,
                    new CustomModelData(foreign, data(replaced).flags(), data(replaced).strings(), data(replaced).colors()));
            var replacement = data(replaced);
            WeaponIzanagiPresentation.clear(a, absent); WeaponIzanagiPresentation.clear(b, replaced);
            higher.set(SLOT, -1f);
            check(h, data(absent).floats().equals(higher),
                    "Absent old slot6 uses inactive -1 without shifting new float7/8 or restoring lower snapshots");
            check(h, data(replaced).equals(replacement), "External slot6 writer wins; cleanup cannot restore stale data");
            WeaponRuntime.cancelUseForSkill(a); WeaponRuntime.cancelUseForSkill(b);
            state(h, absent, 2, 2, 0); state(h, replaced, 2, 2, 0); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 95, environment = "destiny-test:w90_isolated")
    public void fundedCueSurvivesStowAsGameplayChargeAndKeepsChargedAdsRoute(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var s = f.equip(p, 2, 0);
        request(h, p, true);
        f.at(61, () -> {
            state(h, s, 1, 0, 2); range(h, s, 4, 4.01f);
            p.getInventory().setItem(1, new ItemStack(Items.STONE));
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            check(h, !WeaponIzanagiPresentation.active(s), "Stow removes live cosmetic binding");
            state(h, s, 1, 0, 2);
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
        });
        f.at(78, () -> {
            check(h, !WeaponHandling.blocked(p), "Existing seven-stow/eight-ready handling remains authoritative");
            WeaponRuntime.tickPlayer(p); range(h, s, 4, 4.01f); ads(p, true);
        });
        f.at(79, () -> { /* Fixture tick starts the actual held-crouch ADS session. */ });
        f.at(89, () -> {
            check(h, WeaponAiming.progress(p) == 1 && WeaponAimPresentation.active(s), "Real charged ADS reaches existing9-tick transition");
            range(h, s, 4, 4.01f);
            check(h, data(s).floats().get(3) >= 1 && WeaponModels.twoHanded(s), "ADS float3 and original two-hand grip remain live");
            check(h, WeaponIzanagiPresentation.scopedIdle(s)
                            && wire(h, p, s).get(DataComponents.ITEM_MODEL).equals(WeaponScopes.model(WeaponItems.entry(s).orElseThrow())),
                    "Charged idle ADS selects W162 scope while retaining W91 binding/selector for non-FP fallback");
            state(h, s, 1, 0, 2); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void idleChargedBindingWithoutCombatStateCleansOldStackAfterHeldIdentityChanges(GameTestHelper h) {
        var f = new Fixture(h); var p = f.player(16); var s = f.equip(p, 2, 0);
        var original = data(s).floats(); request(h, p, true);
        f.at(61, () -> {
            state(h, s, 1, 0, 2); range(h, s, 4, 4.01f);
            WeaponRuntime.cleanup(p);
            check(h, !WeaponIzanagiPresentation.active(s) && restoredAbsent(s, original),
                    "Cleanup removes combat state and cosmetic selector while retaining funded charge");
            WeaponRuntime.tickPlayer(p); range(h, s, 4, 4.01f);
            p.getInventory().setItem(0, new ItemStack(Items.STONE));
            check(h, !WeaponIzanagiPresentation.active(s), "Changed exact held identity is immediately inactive");
            WeaponRuntime.cleanup(p);
            check(h, restoredAbsent(s, original),
                    "Owner cleanup restores old bound stack even with no combat state and a different current hand");
            state(h, s, 1, 0, 2); h.succeed();
        });
    }
}
