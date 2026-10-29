package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;

public final class WeaponModelGameTests {
    private static void check(GameTestHelper h,boolean ok,String message) {
        h.assertTrue(ok,Component.literal(message));
    }
    // Archived W30 rows remain the exact historical selection, independent of appended exotics.
    static java.util.List<WeaponCatalog.Entry> originalW30Entries() {
        var stream = WeaponModelGameTests.class.getResourceAsStream("/destiny/weapons/w30.json");
        if (stream == null) throw new IllegalStateException("Missing original W30 catalog");
        try (var reader = new java.io.InputStreamReader(stream, java.nio.charset.StandardCharsets.UTF_8)) {
            return java.util.List.of(new com.google.gson.Gson().fromJson(reader, WeaponCatalog.Entry[].class));
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }

    static void assertCatalogExpansion(GameTestHelper h) {
        var original = originalW30Entries();
        check(h, original.size() == 63 && WeaponCatalog.all().containsAll(original), "All 63 original W30 rows unchanged");
        var expected = new java.util.HashSet<>(original.stream().map(WeaponCatalog.Entry::id).toList());
        check(h, expected.size() == 63 && expected.add("ace_of_spades"), "Ace is separate from the unique original 63");
        check(h, expected.add("izanagis_burden"), "Izanagi is separate from the original63 and Ace");
        check(h, WeaponCatalog.all().size() == 65 && expected.equals(new java.util.HashSet<>(
                        WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id).toList())), "Exact original63 plus Ace and Izanagi catalog");
        check(h, WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).distinct().count() == 18, "Same 18 families");
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        check(h, ace.family().equals("hand_cannon") && ace.frame().equals("exotic")
                        && WeaponCharacteristics.of(ace).bungieHash() == 347366834L && WeaponCharacteristics.of(ace).exotic(),
                "Exact first exotic Ace of Spades identity");
        var izanagi = WeaponCatalog.find("izanagis_burden").orElseThrow();
        check(h, izanagi.family().equals("sniper_rifle") && izanagi.frame().equals("exotic")
                        && WeaponCharacteristics.of(izanagi).bungieHash() == 3211806999L && WeaponCharacteristics.of(izanagi).exotic(),
                "Exact second exotic Izanagi identity");
        check(h, WeaponCatalog.all().stream().filter(e -> WeaponCharacteristics.of(e).exotic())
                        .map(WeaponCatalog.Entry::id).collect(java.util.stream.Collectors.toSet())
                        .equals(java.util.Set.of("ace_of_spades", "izanagis_burden")),
                "Exactly two canonical exotics; original63 remain legendary");
    }

    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void previewCommandsRequireOpAndPreserveOrdinaryHeldItems(GameTestHelper h) throws Exception {
        var p=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            var server=h.getLevel().getServer();var dispatcher=server.getCommands().getDispatcher();
            var op=server.createCommandSourceStack().withEntity(p);
            boolean rejected=false;
            try {dispatcher.execute("destiny weapon equip austringer",p.createCommandSourceStack());}
            catch(com.mojang.brigadier.exceptions.CommandSyntaxException expected){rejected=true;}
            check(h,rejected && p.getMainHandItem().isEmpty(),"Non-OP cannot equip previews");
            p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND,3));
            check(h,dispatcher.execute("destiny weapon equip austringer",op)==0,"Protect ordinary held items");
            check(h,p.getMainHandItem().is(Items.DIAMOND)&&p.getMainHandItem().getCount()==3,"No inventory destruction");
            p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);
            check(h,dispatcher.execute("destiny weapon equip austringer",op)==1,"OP can equip an empty hand");
            check(h,WeaponModels.entry(p.getMainHandItem()).orElseThrow().id().equals("austringer"),"Correct model equipped");
            check(h,dispatcher.execute("destiny weapon pose ads",op)==1,"OP can change static pose");
            check(h,"ads".equals(p.getMainHandItem().get(DataComponents.CUSTOM_MODEL_DATA).getString(0)),"Pose updated");
            check(h,dispatcher.execute("destiny weapon pose not_a_pose",op)==0,"Unknown pose rejected");
            check(h,"ads".equals(p.getMainHandItem().get(DataComponents.CUSTOM_MODEL_DATA).getString(0)),"Invalid pose preserves item");
            check(h,dispatcher.execute("destiny weapon equip apostate",op)==1,"Our preview can replace our preview");
            check(h,WeaponModels.entry(p.getMainHandItem()).orElseThrow().id().equals("apostate"),"Catalog selection updated");
            h.succeed();
        } finally {TestPlayers.remove(p);}
    }
    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void everyCatalogStackRoundTripsRealRegistryCodecAndEveryPose(GameTestHelper h) {
        assertCatalogExpansion(h);
        var ops=h.getLevel().registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE);
        for(var e:WeaponCatalog.all()) {
            var stack=WeaponModels.create(e);
            check(h,stack.is(WeaponPreviewItem.INSTANCE),"Inert Polymer server carrier");
            check(h,stack.getMaxStackSize()==1,"Individual preview weapon");
            check(h,Identifier.parse(e.item_model()).equals(stack.get(DataComponents.ITEM_MODEL)),e.id());
            for(var pose:WeaponModels.Pose.values()) {
                check(h,WeaponModels.setPose(stack,pose),"Known item accepts pose");
                var encoded=ItemStack.CODEC.encodeStart(ops,stack).getOrThrow();
                var decoded=ItemStack.CODEC.parse(ops,encoded).getOrThrow();
                check(h,WeaponModels.entry(decoded).orElseThrow().equals(e),"Identity survives inventory serialization");
                check(h,pose.name().equalsIgnoreCase(decoded.get(DataComponents.CUSTOM_MODEL_DATA).getString(0)),"String state selector survives serialization");
            }
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void ordinaryAndTamperedItemsCannotBeConvertedByPosePreview(GameTestHelper h) {
        var normal=new ItemStack(Items.DIAMOND,3);
        check(h,!WeaponModels.setPose(normal,WeaponModels.Pose.ADS),"Do not mutate ordinary inventory items");
        check(h,normal.getCount()==3 && normal.get(DataComponents.CUSTOM_MODEL_DATA)==null,"Preserve unrelated item");
        var spoof=WeaponModels.create(WeaponCatalog.all().getFirst());
        spoof.set(DataComponents.ITEM_MODEL,Identifier.withDefaultNamespace("stick"));
        check(h,WeaponModels.entry(spoof).isEmpty(),"Model and marker must agree");
        check(h,!WeaponModels.setPose(spoof,WeaponModels.Pose.INSPECT),"Reject forged visual identity");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=20, environment = "destiny-test:w90_isolated")
    public void nativeHeldModelsDoNotSpawnHudOrStealCameraOrOffhand(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            p.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.EMERALD,4));
            for(var e:WeaponCatalog.all()) {
                var stack=WeaponModels.create(e);p.setItemInHand(InteractionHand.MAIN_HAND,stack);
                WeaponModels.setPose(stack,WeaponModels.Pose.ADS);
                check(h,p.getCamera()==p,"Held items preserve self-camera");
                check(h,kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).isEmpty(),"No owner HUD pseudo-viewmodel");
                check(h,p.getOffhandItem().is(Items.EMERALD)&&p.getOffhandItem().getCount()==4,"Offhand preserved");
            }
            h.succeed();
        } finally {TestPlayers.remove(p);}
    }
}
