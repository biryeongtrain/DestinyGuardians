package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItem;
import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.projectile.Projectile;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.Vec3;

public final class WeaponGripGameTests {
    /** Exercise the production left-click router, without ticking, resetting or bypassing debounce. */
    static void ads(net.minecraft.server.level.ServerPlayer player, boolean requested) {
        if (WeaponAiming.requested(player) != requested)
            kim.biryeong.destiny.input.InputRouter.onPunch(player);
    }

    /** Pack-declared wrapper contract, independent of the production projection implementation. */
    private static final java.util.Set<String> HAND_ROUTES = handRoutes();
    private static java.util.Set<String> handRoutes() {
        try (var stream = WeaponGripGameTests.class.getResourceAsStream("/destiny/weapons/w201-first-person-hands.json")) {
            if (stream == null) throw new AssertionError("Missing authored W201 route manifest");
            var json = com.google.gson.JsonParser.parseString(new String(stream.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            if (json.get("schemaVersion").getAsInt() != 1) throw new AssertionError("Unexpected W201 route schema");
            var models = json.getAsJsonObject("models");
            for (var entry : models.entrySet()) {
                String expected = "destiny:weapon_hands_w201/" + entry.getKey().substring("destiny:".length());
                if (!entry.getKey().startsWith("destiny:") || !expected.equals(entry.getValue().getAsString()))
                    throw new AssertionError("Invalid authored hand route: " + entry);
            }
            return java.util.Set.copyOf(models.keySet());
        } catch (java.io.IOException e) { throw new AssertionError(e); }
    }
    static net.minecraft.resources.Identifier projected(net.minecraft.resources.Identifier route) {
        return route != null && HAND_ROUTES.contains(route.toString())
                ? net.minecraft.resources.Identifier.parse("destiny:weapon_hands_w201/" + route.getPath()) : route;
    }
    static net.minecraft.resources.Identifier projected(ItemStack source, net.minecraft.resources.Identifier route) {
        return source.is(WeaponCombatItem.INSTANCE) || source.is(WeaponPreviewItem.INSTANCE) ? projected(route) : route;
    }
    /** W161 reserves flag1 only for the live two-hand Ammit; preview and all others keep flag0 only. */
    static java.util.List<Boolean> wireFlags(ItemStack source) {
        boolean two = WeaponModels.twoHanded(source);
        boolean ammit = source.is(WeaponCombatItem.INSTANCE) && two
                && WeaponItems.entry(source).map(e -> e.id().equals("ammit_ar2")).orElse(false);
        return ammit ? java.util.List.of(two, Boolean.TRUE.equals(source.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,
                net.minecraft.world.item.component.CustomModelData.EMPTY).getBoolean(1))) : java.util.List.of(two);
    }
    /** Explicit authored sight-family oracle; never calls the model getter being tested. */
    static net.minecraft.resources.Identifier aimRoute(String id, boolean bow) {
        String prefix;
        if (id.equals("ace_of_spades")) prefix = "weapon_sight_w159/";
        else if (java.util.Set.of("patron_of_lost_causes", "aishas_embrace", "long_arm", "antiope_d", "bug_out_bag",
                "ikelos_smg_v1_0_1", "the_recluse", "dead_man_walking_xx7463", "high_albedo", "brass_attacks",
                "erentil_fr4", "hollow_words", "dream_breaker", "null_composure", "coriolis_force", "edge_transit",
                "fixed_odds", "retrofit_escapade").contains(id)) prefix = "weapon_sight_w153/";
        else if (java.util.Set.of("duke_mk_44", "austringer", "seventh_seraph_officer_revolver", "allied_demand", "farewell",
                "lonesome", "halfdan_d", "ammit_ar2", "gnawing_hunger", "steelfeather_repeater", "frontier_justice",
                "distant_relation", "cold_denial", "bygones", "chattering_bone", "blast_furnace", "claws_of_the_wolf",
                "hammerhead", "bad_omens", "code_duello").contains(id)) prefix = "weapon_sight_w151/";
        else if (java.util.Set.of("retraced_path", "bellowing_giant", "pyroclastic_flow", "line_in_the_sand", "stormchaser").contains(id)) prefix = "weapon_sight_w150/";
        else if (java.util.Set.of("canis_major", "dimensional_hypotrochoid", "deafening_whisper", "salvager_s_salvo").contains(id)) prefix = "weapon_sight_w149/";
        else if (java.util.Set.of("dust_rock_blues", "first_in_last_out", "ikelos_sg_v1_0_1", "parcel_of_stardust_fell_to_earth",
                "mindbender_s_ambition_adept", "biting_winds", "whispering_slab").contains(id)) prefix = "weapon_sight_w148/";
        else prefix = "weapon_aim_w70/";
        return net.minecraft.resources.Identifier.parse("destiny:" + prefix + id + (bow ? "_bow" : ""));
    }

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void allWireCopiesUseVanillaCarrierAndClientOnlyCharge(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            var context=((PacketContextProvider)(Object)p.connection).getPacketContext();
            int twoHands=0, previousTwoHands=0;
            check(h,WeaponPreviewItem.INSTANCE instanceof PolymerItem,"Server-only registry item is Polymer backed");
            check(h,!((Item)WeaponPreviewItem.INSTANCE instanceof CrossbowItem),"Server item cannot run crossbow shooting");
            for(var e:WeaponCatalog.all()) {
                var real=WeaponModels.create(e);var snapshot=real.copy();
                var wire=PolymerItemUtils.getPolymerItemStack(real,context,h.getLevel().registryAccess());
                boolean two=WeaponModels.defaultGrip(e)==WeaponModels.Grip.TWO_HAND;
                if(two){twoHands++;if(!WeaponExotics.izanagi(e))previousTwoHands++;}
                check(h,wire.is(two?Items.CROSSBOW:Items.STICK),e.id()+" client carrier");
                check(h,CrossbowItem.isCharged(wire)==two,e.id()+" client pose marker");
                check(h,Boolean.valueOf(two).equals(wire.get(DataComponents.CUSTOM_MODEL_DATA).getBoolean(0)),"Grip model selector");
                check(h,wire.get(DataComponents.ITEM_MODEL).equals(projected(real.get(DataComponents.ITEM_MODEL))),"Weapon model retained");
                check(h,real.get(DataComponents.CHARGED_PROJECTILES)==null,"No server ammunition");
                check(h,ItemStack.matches(real,snapshot),"Polymer never mutates original");
                var roundTrip=PolymerItemUtils.getRealItemStack(wire,context,h.getLevel().registryAccess());
                check(h,ItemStack.matches(real,roundTrip),"Polymer roundtrip retains authoritative components");
            }
            check(h,previousTwoHands==47,"All previous 47 two-hand defaults remain unchanged");
            check(h,twoHands==48,"Izanagi adds exactly one new two-hand default");
            h.succeed();
        } finally {TestPlayers.remove(p);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void repeatedServerUseCannotShootConsumeAmmoOrStartUsing(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.ARROW,16));
            for(var e:WeaponCatalog.all()) {
                var stack=WeaponModels.create(e);p.setItemInHand(InteractionHand.MAIN_HAND,stack);
                var before=stack.copy();
                for(int i=0;i<3;i++)p.gameMode.useItem(p,h.getLevel(),stack,InteractionHand.MAIN_HAND);
                check(h,ItemStack.matches(before,p.getMainHandItem()),"Use does not alter preview: "+e.id());
                check(h,!p.isUsingItem(),"No artificial use/slowdown state");
                check(h,p.getOffhandItem().is(Items.ARROW)&&p.getOffhandItem().getCount()==16,"Offhand ammo untouched");
                check(h,h.getLevel().getEntitiesOfClass(Projectile.class,p.getBoundingBox().inflate(16),
                        projectile->projectile.getOwner()==p).isEmpty(),"No projectile from inert server item");
            }
            check(h,p.getCamera()==p,"No camera takeover");
            h.succeed();
        } finally {TestPlayers.remove(p);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void gripMigrationPreservesLegacyPoseAndRejectsUnrelatedItems(GameTestHelper h) {
        var e=WeaponCatalog.find("austringer").orElseThrow();
        var legacy=WeaponModels.create(e).transmuteCopy(Items.STICK);
        WeaponModels.setPose(legacy,WeaponModels.Pose.ADS);
        var tag=legacy.get(DataComponents.CUSTOM_DATA).copyTag();tag.putString("unrelated","retained");
        legacy.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
        var migrated=WeaponModels.withGrip(legacy,WeaponModels.Grip.TWO_HAND).orElseThrow();
        check(h,WeaponModels.twoHanded(migrated),"Legacy preview migrates to inert carrier");
        check(h,!WeaponModels.twoHanded(legacy)&&legacy.is(Items.STICK),"Original not mutated");
        check(h,"ads".equals(migrated.get(DataComponents.CUSTOM_MODEL_DATA).getString(0)),"Static ADS state retained");
        check(h,"retained".equals(migrated.get(DataComponents.CUSTOM_DATA).copyTag().getString("unrelated").orElseThrow()),"Extra metadata retained");
        check(h,WeaponModels.withGrip(new ItemStack(Items.CROSSBOW),WeaponModels.Grip.TWO_HAND).isEmpty(),"Ordinary crossbows untouched");
        for(var row:WeaponCatalog.all())if(!WeaponModels.supportsTwoHand(row))
            check(h,WeaponModels.withGrip(WeaponModels.create(row),WeaponModels.Grip.TWO_HAND).isEmpty(),"Do not force crossbow pose onto "+row.family());
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void gripCommandsAreScopedAndReversibleWithoutOffhandChanges(GameTestHelper h) throws Exception {
        var p=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            var server=h.getLevel().getServer();var commands=server.getCommands().getDispatcher();
            var op=server.createCommandSourceStack().withEntity(p);
            p.setItemInHand(InteractionHand.MAIN_HAND,WeaponModels.create(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()));
            p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.EMERALD,4));
            check(h,commands.execute("destiny weapon grip native",op)==1,"Native command");
            check(h,!WeaponModels.twoHanded(p.getMainHandItem()),"Native mode restored");
            check(h,commands.execute("destiny weapon grip two_hand",op)==1,"Two hand command");
            check(h,WeaponModels.twoHanded(p.getMainHandItem()),"Two hand mode selected");
            check(h,commands.execute("destiny weapon grip invalid",op)==0,"Unknown grip rejected");
            boolean denied=false;
            try {commands.execute("destiny weapon grip native",p.createCommandSourceStack());}
            catch(com.mojang.brigadier.exceptions.CommandSyntaxException expected){denied=true;}
            check(h,denied&&WeaponModels.twoHanded(p.getMainHandItem()),"Non OP cannot mutate grip");
            check(h,p.getOffhandItem().is(Items.EMERALD)&&p.getOffhandItem().getCount()==4,"Offhand preserved");
            h.succeed();
        } finally {TestPlayers.remove(p);}
    }
}
