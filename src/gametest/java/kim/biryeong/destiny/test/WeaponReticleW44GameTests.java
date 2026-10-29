package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponReticleHud;
import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponItems;
import kim.biryeong.destiny.weapon.WeaponLoadout;
import kim.biryeong.destiny.weapon.WeaponModels;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

/** W44 sidecar contract tests: real personal HUD nodes, not a shadow diagnostic state.
 * Register this class in the main agent's coordinated fabric-gametest entrypoint change.
 */
public final class WeaponReticleW44GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h) {
        var player = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 6), 0, 0);
        TestCleanup.register(h, () -> {
            Guardians.runtime(player).superSession = null;
            WeaponReticleHud.remove(player);
            TestPlayers.remove(player);
        });
        return player;
    }

    private static ItemStack equip(ServerPlayer player, WeaponCatalog.Entry entry) {
        var stack = WeaponItems.create(entry);
        player.setItemInHand(InteractionHand.MAIN_HAND, stack);
        return stack;
    }

    private static WeaponCatalog.Entry family(String family) {
        return WeaponCatalog.family(family).getFirst();
    }

    private static ItemDisplayHud frame(ServerPlayer player) {
        return (ItemDisplayHud) DisplayHud.getHud(player, WeaponReticleHud.FRAME_ID);
    }

    private static ItemDisplayHud center(ServerPlayer player) {
        return (ItemDisplayHud) DisplayHud.getHud(player, WeaponReticleHud.CENTER_ID);
    }

    private static long count(ServerPlayer player) {
        return DisplayHud.getHuds(player).keySet().stream().filter(id -> id.startsWith(WeaponReticleHud.PREFIX)).count();
    }

    private static String model(ItemDisplayHud hud) {
        return hud.getItemDisplay().getItemStack().get(DataComponents.ITEM_MODEL).toString();
    }

    private static boolean excluded(WeaponCatalog.Entry entry) {
        return entry.family().equals("sword") || entry.family().equals("glaive");
    }

    private static String shape(WeaponCatalog.Entry entry) {
        return switch(entry.id()) {
            case "mindbender_s_ambition_adept" -> "w105_shotgun_aggressive";
            case "dust_rock_blues" -> "w105_shotgun_precision";
            case "parcel_of_stardust_fell_to_earth" -> "w105_shotgun_lightweight";
            case "ikelos_sg_v1_0_1" -> "w105_shotgun_rapid_fire";
            default -> "w44_"+(entry.family().equals("shotgun") && entry.frame().equals("pinpoint_slug")
                    ? "shotgun_slug" : entry.family());
        };
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void everyLiveCatalogEntryHasCorrectPackModelAndBoundedNodesWithoutItemMutation(GameTestHelper h) {
        var player = player(h);
        for (var entry : WeaponCatalog.all()) {
            var stack = equip(player, entry);
            var before = stack.copy();
            WeaponReticleHud.update(player, 0, 0, false);
            if(!excluded(entry))check(h,frame(player).isAboveHand()&&center(player).isAboveHand(),"Reticle must not be occluded by centered ADS models");
            if (excluded(entry)) {
                check(h, count(player) == 0, "No W44 gun reticle for " + entry.family());
            } else {
                check(h, count(player) == 2 && count(player) <= 8, "Actual nodes bounded: " + entry.id());
                check(h, model(frame(player)).equals("destiny:gui/hud/reticle_" + shape(entry)),
                        "Family/frame selects original pack model: " + entry.id());
                check(h, model(center(player)).equals("destiny:gui/hud/reticle_w44_dot"), "Fixed central dot model");
                check(h, frame(player).getItemTransform() == net.minecraft.world.item.ItemDisplayContext.NONE,
                        "Flat quad uses explicit NONE context");
                check(h, frame(player).getAlignment() == DisplayHud.HudAlignment.CENTER, "Responsive centre alignment");
                check(h, frame(player).getLocation().x() == 960 && frame(player).getLocation().y() == 540,
                        "Actual frame stays at screen centre");
            }
            check(h, ItemStack.matches(before, stack), "No ammo, component, pose or identity mutation: " + entry.id());
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void adsAndBloomChangeEveryFrameGeometryButPreserveCentreAndDisplayIdentity(GameTestHelper h) {
        var player = player(h);
        for (var entry : WeaponCatalog.all()) {
            if (excluded(entry)) continue;
            equip(player, entry);
            WeaponReticleHud.update(player, 0, 0, false);
            var frame = frame(player);
            var center = center(player);
            int frameEntity = frame.getEntityId(), dotEntity = center.getEntityId();
            var hip = frame.getScale();
            var point = center.getLocation();
            var pointScale = center.getScale();
            var pointItem = center.getItemDisplay().getItemStack();
            WeaponReticleHud.update(player, .5f, 0, false);
            var halfway = frame.getScale();
            WeaponReticleHud.update(player, .94f, 0, false);
            var ads = frame.getScale();
            check(h, hip.x() > halfway.x() && halfway.x() > ads.x() && hip.y() > ads.y(),
                    "Actual ADS geometry contracts continuously: " + entry.id());
            WeaponReticleHud.update(player, .94f, 1, false);
            var bloomed = frame.getScale();
            check(h, bloomed.x() > ads.x() && bloomed.y() > ads.y()
                            && bloomed.x() - ads.x() <= 12 && bloomed.y() - ads.y() <= 12,
                    "Responsive, conservative bloom expansion: " + entry.id());
            check(h, frame(player) == frame && center(player) == center
                            && frame.getEntityId() == frameEntity && center.getEntityId() == dotEntity,
                    "ADS and recoil reuse both actual display entities");
            check(h, center.getLocation().equals(point) && center.getScale().equals(pointScale)
                            && center.getItemDisplay().getItemStack() == pointItem,
                    "Bloom never moves, enlarges or resends the unchanged aim point");
            check(h, count(player) == 2, "No animated ghost/echo nodes before physical-optic takeover");
            boolean physical = !List.of("sniper_rifle", "linear_fusion_rifle").contains(entry.family());
            WeaponReticleHud.update(player,.95f,0,false);
            if(physical)check(h,count(player)==0&&frame.isRemoved()&&center.isRemoved(),"At .95 the physical sight removes both hip quads: "+entry.id());
            else check(h,count(player)==2&&frame(player)==frame&&center(player)==center,"Non-physical optics retain both stable generic quads");
            WeaponReticleHud.update(player,1,1,false);
            check(h,count(player)==(physical?0:2),"Full ADS/bloom cannot resurrect a physical-optic hip reticle");
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void precisionAdsIsNarrowAndSlugCannotInheritPelletSpreadCircle(GameTestHelper h) {
        var player = player(h);
        for (String family : List.of("sniper_rifle", "linear_fusion_rifle")) {
            equip(player, family(family));
            WeaponReticleHud.update(player, 1, 0, false);
            check(h, frame(player).getScale().x() <= 24 && frame(player).getScale().y() <= 20,
                    "Narrow precision ADS: " + family);
        }
        var pellet = WeaponCatalog.family("shotgun").stream().filter(e -> !e.frame().equals("pinpoint_slug")).findFirst().orElseThrow();
        var slug = WeaponCatalog.family("shotgun").stream().filter(e -> e.frame().equals("pinpoint_slug")).findFirst().orElseThrow();
        equip(player, pellet);
        WeaponReticleHud.update(player, 0, 0, false);
        float pelletWidth = frame(player).getScale().x();
        int entity = frame(player).getEntityId();
        equip(player, slug);
        WeaponReticleHud.update(player, 0, 0, false);
        check(h, model(frame(player)).endsWith("reticle_w44_shotgun_slug")
                        && frame(player).getScale().x() < pelletWidth / 2,
                "Slug has its own smaller precision-circle/diamond artwork");
        check(h, frame(player).getEntityId() == entity && count(player) == 2, "Swap replaces art without respawning nodes");
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void nonFiniteAndExtremeInputsCannotPoisonActualTransformsOrDefeatCaching(GameTestHelper h) {
        var player = player(h);
        equip(player, family("auto_rifle"));
        WeaponReticleHud.update(player, 0, 0, false);
        var rested = frame(player).getScale();
        var restedItem = frame(player).getItemDisplay().getItemStack();
        for (float invalid : new float[]{Float.NaN, Float.POSITIVE_INFINITY, Float.NEGATIVE_INFINITY, -Float.MAX_VALUE}) {
            WeaponReticleHud.update(player, invalid, invalid, false);
            check(h, frame(player).getScale().equals(rested), "Invalid/negative input sanitizes to rested hip geometry");
            check(h, frame(player).getItemDisplay().getItemStack() == restedItem, "Equivalent sanitized state remains cached");
        }
        WeaponReticleHud.update(player, 1, 1, false);
        check(h,count(player)==0,"Full finite ADS hands over to the auto-rifle physical sight");
        WeaponReticleHud.update(player, Float.MAX_VALUE, Float.MAX_VALUE, false);
        check(h,count(player)==0,"Extreme finite ADS must not resurrect the hip reticle");
        for (float aim : new float[]{Float.NaN, Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY, -.5f, .25f, 1.5f}) {
            for (float bloom : new float[]{Float.NaN, Float.NEGATIVE_INFINITY, Float.POSITIVE_INFINITY, -1, .5f, Float.MAX_VALUE}) {
                WeaponReticleHud.update(player, aim, bloom, false);
                if(Float.isFinite(aim)&&aim>=.95f){
                    check(h,count(player)==0,"Finite physical-optic takeover has no stale HUD nodes");
                    continue;
                }
                check(h,frame(player)!=null&&center(player)!=null,"Sanitized non-optic inputs retain both quads");
                for (var hud : List.of(frame(player), center(player))) {
                    var scale = hud.getScale();
                    var location = hud.getLocation();
                    check(h, Float.isFinite(scale.x()) && Float.isFinite(scale.y()) && Float.isFinite(scale.z())
                                    && Float.isFinite(location.x()) && Float.isFinite(location.y()) && Float.isFinite(location.z())
                                    && scale.x() > 0 && scale.x() <= 100 && scale.y() > 0 && scale.y() <= 100,
                            "All real HUD transforms stay finite and bounded");
                }
                check(h, count(player) == 2, "Malformed inputs never allocate more nodes");
            }
        }
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void reloadHidesReticleAndUnchangedFramesDoNotReplaceDisplayMetadata(GameTestHelper h) {
        var player = player(h);
        var stack = equip(player, family("hand_cannon"));
        var before = stack.copy();
        WeaponReticleHud.update(player, .5f, .5f, false);
        var frame = frame(player);
        var dot = center(player);
        var scale = frame.getScale();
        var unchanged = frame.getItemDisplay().getItemStack();
        var unchangedDot = dot.getItemDisplay().getItemStack();
        TestPlayers.drain(player);
        WeaponReticleHud.update(player, .5f, .5f, false);
        check(h, frame.getItemDisplay().getItemStack() == unchanged, "Exact stable frame does not replace item metadata");
        check(h, TestPlayers.outbound(player).isEmpty(), "Stable reticle queues no network updates");
        WeaponReticleHud.update(player, .5f, .5f, true);
        check(h, count(player) == 0 && frame.isRemoved() && dot.isRemoved(), "Reload hides both actual gun-reticle nodes");
        check(h, ItemStack.matches(before, stack), "HUD reload flag never transfers/refills ammunition");
        WeaponReticleHud.update(player, .5f, .5f, false);
        check(h, count(player) == 2 && frame(player).getScale().equals(scale)
                        && ItemStack.matches(center(player).getItemDisplay().getItemStack(), unchangedDot),
                "Reticle restores supplied ADS/bloom geometry and fixed dot after reload");
        h.succeed();
    }

    private static ItemDisplayHud sentinel(ServerPlayer player, String id) {
        var hud = new ItemDisplayHud();
        var item = new ItemStack(Items.PAPER);
        item.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/reticle_w44_dot"));
        hud.setItem(item);
        hud.spawn(player, id);
        return hud;
    }

    private static void absentAndIsolated(GameTestHelper h, ServerPlayer player, Map<String, ItemDisplayHud> sentinels) {
        check(h, count(player) == 0, "All W44 parts removed");
        sentinels.forEach((id, hud) -> check(h, DisplayHud.getHud(player, id) == hud && !hud.isRemoved(),
                "Other HUD owner remains intact: " + id));
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void previewEmptyMeleeSuperSpectatorDeathAndInactiveLoadoutRemoveOnlyOwnPrefix(GameTestHelper h) {
        var player = player(h);
        Map<String, ItemDisplayHud> sentinels = new LinkedHashMap<>();
        for (String id : List.of(CombatHud.HEALTH_ID, AmmoHud.PREFIX + "panel", AmmoHud.PREFIX + "glaive_reticle",
                "destiny:reticle_w440_neighbor")) sentinels.put(id, sentinel(player, id));
        TestCleanup.register(h, () -> sentinels.keySet().forEach(id -> DisplayHud.removeHud(player, id)));
        var gun = family("hand_cannon");
        equip(player, gun);
        WeaponReticleHud.update(player, 0, 0, false);
        var obsolete = sentinel(player, WeaponReticleHud.PREFIX + "old_segment_7");
        WeaponReticleHud.update(player, 0, 0, false);
        check(h, obsolete.isRemoved() && count(player) == 2, "Update prunes obsolete W44 parts and preserves bound");
        WeaponReticleHud.update(player, 0, 0, true);
        absentAndIsolated(h, player, sentinels);
        for (var entry : List.of(family("sword"), family("glaive"))) {
            equip(player, entry);
            WeaponReticleHud.update(player, 0, 0, false);
            absentAndIsolated(h, player, sentinels);
        }
        equip(player, gun);
        WeaponReticleHud.update(player, 0, 0, false);
        player.setItemInHand(InteractionHand.MAIN_HAND, WeaponModels.create(gun));
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        equip(player, gun);
        WeaponReticleHud.update(player, 0, 0, false);
        player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        equip(player, gun);
        WeaponReticleHud.update(player, 0, 0, false);
        Guardians.runtime(player).superSession = new SuperSession() {
            public boolean tick() { return true; }
            public void primary() { }
            public void end() { }
            public float remaining() { return 1; }
        };
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        Guardians.runtime(player).superSession = null;
        WeaponReticleHud.update(player, 0, 0, false);
        player.setGameMode(GameType.SPECTATOR);
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        player.setGameMode(GameType.SURVIVAL);
        player.getInventory().setSelectedSlot(4);
        equip(player, gun);
        WeaponReticleHud.update(player, 0, 0, false);
        check(h, count(player) == 2, "Standalone fixture can show a live gun in slot 4");
        player.setAttached(WeaponLoadout.ENABLED, true);
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        player.setAttached(WeaponLoadout.ENABLED, false);
        WeaponReticleHud.update(player, 0, 0, false);
        player.setHealth(0);
        WeaponReticleHud.update(player, 0, 0, false);
        absentAndIsolated(h, player, sentinels);
        WeaponReticleHud.remove(player);
        absentAndIsolated(h, player, sentinels);
        h.succeed();
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void onePlayersCleanupCannotRemoveAnotherPlayersReticle(GameTestHelper h) {
        var first = player(h);
        var second = player(h);
        equip(first, family("hand_cannon"));
        equip(second, family("auto_rifle"));
        WeaponReticleHud.update(first, 0, 0, false);
        WeaponReticleHud.update(second, .94f, .5f, false);
        var secondFrame = frame(second);
        int entity = secondFrame.getEntityId();
        WeaponReticleHud.remove(first);
        WeaponReticleHud.remove(first);
        check(h, count(first) == 0 && count(second) == 2 && frame(second) == secondFrame
                        && secondFrame.getEntityId() == entity && !secondFrame.isRemoved(),
                "Idempotent cleanup remains player-local as well as prefix-local");
        h.succeed();
    }
}
