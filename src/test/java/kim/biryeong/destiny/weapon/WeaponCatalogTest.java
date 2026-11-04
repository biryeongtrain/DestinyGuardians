package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

public class WeaponCatalogTest {
    // Exact original W30 selection. Never infer this set by dropping whichever new rows exist.
    private static final List<String> ORIGINAL_W30_IDS = List.of(
            "duke_mk_44", "austringer", "seventh_seraph_officer_revolver",
            "halfdan_d", "ammit_ar2", "gnawing_hunger",
            "steelfeather_repeater", "cold_denial", "bygones",
            "chattering_bone", "blast_furnace", "claws_of_the_wolf",
            "frontier_justice", "distant_relation", "patron_of_lost_causes",
            "aishas_embrace", "long_arm", "antiope_d",
            "bug_out_bag", "ikelos_smg_v1_0_1", "the_recluse",
            "allied_demand", "farewell", "lonesome",
            "dead_man_walking_xx7463", "high_albedo", "brass_attacks",
            "biting_winds", "whispering_slab", "bite_of_the_fox",
            "beloved", "apostate", "mindbender_s_ambition_adept",
            "dust_rock_blues", "first_in_last_out", "parcel_of_stardust_fell_to_earth",
            "ikelos_sg_v1_0_1", "erentil_fr4", "hollow_words",
            "dream_breaker", "null_composure", "coriolis_force",
            "line_in_the_sand", "stormchaser", "retraced_path",
            "salvager_s_salvo", "deafening_whisper", "edge_transit",
            "canis_major", "dimensional_hypotrochoid", "bad_omens",
            "bellowing_giant", "code_duello", "pyroclastic_flow",
            "fixed_odds", "hammerhead", "retrofit_escapade",
            "abide_the_return", "goldtusk", "crown_splitter",
            "falling_guillotine", "temptation_s_hook", "nezarec_s_whisper");

    public static List<WeaponCatalog.Entry> originalW30Entries() {
        assertEquals(63, ORIGINAL_W30_IDS.size());
        return ORIGINAL_W30_IDS.stream().map(id -> WeaponCatalog.find(id).orElseThrow()).toList();
    }

    static void assertExpandedCatalog() {
        assertEquals(65, WeaponCatalog.all().size());
        var expected = new HashSet<>(ORIGINAL_W30_IDS);
        assertTrue(expected.add("ace_of_spades"));
        assertTrue(expected.add("izanagis_burden"));
        assertEquals(expected, new HashSet<>(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id).toList()));
        assertEquals(18, WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).distinct().count());
        var ace = WeaponCatalog.find("ace_of_spades").orElseThrow();
        assertEquals("hand_cannon", ace.family()); assertEquals("exotic", ace.frame());
        assertEquals(347366834L, WeaponCharacteristics.of(ace).bungieHash());
        assertTrue(WeaponCharacteristics.of(ace).exotic());
        var izanagi = WeaponCatalog.find("izanagis_burden").orElseThrow();
        assertEquals("sniper_rifle", izanagi.family()); assertEquals("exotic", izanagi.frame());
        assertEquals(3211806999L, WeaponCharacteristics.of(izanagi).bungieHash());
        assertTrue(WeaponCharacteristics.of(izanagi).exotic());
        assertEquals(Set.of("ace_of_spades", "izanagis_burden"), WeaponCatalog.all().stream()
                .filter(e -> WeaponCharacteristics.of(e).exotic()).map(WeaponCatalog.Entry::id)
                .collect(java.util.stream.Collectors.toSet()));
    }


    private static final Path ROOT=Path.of("src/main/resources/assets/destiny");
    private static JsonObject json(Path p) throws Exception {
        return JsonParser.parseString(Files.readString(p)).getAsJsonObject();
    }
    @Test void expandedCoverageIsUniqueAndIncludesThreeRealSniperFrames() throws Exception {
        assertExpandedCatalog();
        var frozen = List.of(new Gson().fromJson(Files.readString(Path.of("src/main/resources/destiny/weapons/w30.json")), WeaponCatalog.Entry[].class));
        assertEquals(ORIGINAL_W30_IDS, frozen.stream().map(WeaponCatalog.Entry::id).toList());
        assertEquals(frozen, originalW30Entries(), "Every original W30 row stays unchanged");
        assertEquals(18,WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).distinct().count());
        assertEquals(Set.of("aggressive","adaptive","rapid_fire"),new HashSet<>(WeaponCatalog.family("sniper_rifle").stream().filter(e -> !WeaponCharacteristics.of(e).exotic()).map(WeaponCatalog.Entry::frame).toList()));
        assertEquals(Set.of("izanagis_burden"), WeaponCatalog.family("sniper_rifle").stream()
                .filter(e -> WeaponCharacteristics.of(e).exotic()).map(WeaponCatalog.Entry::id)
                .collect(java.util.stream.Collectors.toSet()));
        assertEquals(5,WeaponCatalog.family("shotgun").size());
        assertEquals(5,WeaponCatalog.family("fusion_rifle").size());
        assertEquals(5,WeaponCatalog.family("sword").size());
        assertTrue(WeaponCatalog.find("not_a_weapon").isEmpty());
        assertThrows(UnsupportedOperationException.class,()->WeaponCatalog.all().clear());
        assertEquals("adaptive_burst",WeaponCatalog.find("stormchaser").orElseThrow().frame());
        assertEquals("heavy_burst",WeaponCatalog.find("brass_attacks").orElseThrow().frame());
    }
    @Test void everyNativeItemAndCuboidModelPassesTheActualClientCodecs() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();
        net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        net.minecraft.client.renderer.item.properties.select.SelectItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.conditional.ConditionalItemModelProperties.bootstrap();
        net.minecraft.client.renderer.item.properties.numeric.RangeSelectItemModelProperties.bootstrap();
        for(var e:WeaponCatalog.all()) {
            var item=json(ROOT.resolve("items/weapon/"+e.id()+".json"));
            var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,item.get("model"));
            assertTrue(result.isSuccess(),e.id()+": "+result.error());
            String model=Set.of("ace_of_spades", "izanagis_burden").contains(e.id()) ? "models/item/weapon/"+e.id()
                    : "models/weapon/"+e.family()+"/"+e.id();
            for(String suffix:List.of("","_ads","_inspect"))
                assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(ROOT.resolve(model+suffix+".json")))));
            var definition=item.getAsJsonObject("model");
            assertEquals("minecraft:custom_model_data",definition.get("property").getAsString());
            assertEquals(0,definition.get("index").getAsInt());
            assertFalse(item.get("hand_animation_on_swap").getAsBoolean());
        }
        // Both supplied exotic models use their own directories, not W30's reconstruction layout.
        // Parse every manifested pose/transition without skipping either exotic or relaxing W83 counts.
        for (String stage : List.of("w83", "w84")) {
            var outputs=json(Path.of("art/weapons/"+stage+"/model/manifest.json")).getAsJsonObject("outputSha256");
            int models=0,items=0;
            for(var path:outputs.keySet()) {
                if(path.contains("/models/")) {
                    assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(Path.of(path)))),path);
                    models++;
                } else if(path.contains("/items/")) {
                    var result=ItemModels.CODEC.parse(JsonOps.INSTANCE,json(Path.of(path)).get("model"));
                    assertTrue(result.isSuccess(),path+": "+result.error()); items++;
                }
            }
            assertEquals(50,models,stage); assertEquals(2,items,stage);
        }
    }
    @Test void sourceReconstructionHasBoundedEditableCubesAndRealColorNotGenericBoxes() throws Exception {
        Set<String> geometry=new HashSet<>(),textures=new HashSet<>();
        for(var e:originalW30Entries()) {
            var bb=json(Path.of("art/blockbench/weapons/w30/"+e.id()+".bbmodel"));
            var info=bb.getAsJsonObject("destiny_w30");
            var cubes=bb.getAsJsonArray("elements");
            assertTrue(cubes.size()>8 && cubes.size()<=256,e.id());
            assertEquals(cubes.size(),info.get("cube_count").getAsInt());
            assertTrue(info.get("source_triangles").getAsInt()>100);
            assertTrue(info.get("textured_triangles").getAsInt()>.5*info.get("source_triangles").getAsInt(),e.id());
            for(var v:cubes) {
                var c=v.getAsJsonObject();assertEquals("cube",c.get("type").getAsString());
                for(int a=0;a<3;a++) {
                    double low=c.getAsJsonArray("from").get(a).getAsDouble(),high=c.getAsJsonArray("to").get(a).getAsDouble();
                    assertTrue(Double.isFinite(low)&&Double.isFinite(high)&&low<high&&low>=-16&&high<=32,e.id());
                }
            }
            var image=ImageIO.read(ROOT.resolve("textures/item/weapon/w30/"+e.id()+".png").toFile());
            assertEquals(1024,image.getWidth());assertEquals(1024,image.getHeight());
            Set<Integer> colors=new HashSet<>();
            for(int y=0;y<image.getHeight();y++)for(int x=0;x<image.getWidth();x++)if((image.getRGB(x,y)>>>24)!=0)colors.add(image.getRGB(x,y));
            assertTrue(colors.size()>32,e.id()+" has no surface detail");
            assertTrue(geometry.add(cubes.toString()),"Duplicated gun geometry: "+e.id());
            assertTrue(textures.add(info.get("texture_sha256").getAsString()));
        }
    }
    @Test void pinEveryRuntimeAndEditableAssetHash() throws Exception {
        var manifest=json(Path.of("art/weapons/w30/manifest.json"));
        for(var e:manifest.getAsJsonObject("runtime_sha256").entrySet())
            GripContractsW163Support.assertAssetHash(e.getKey(), e.getValue().getAsString());
        for(var v:manifest.getAsJsonArray("models")) {
            var e=v.getAsJsonObject();String id=e.get("id").getAsString();
            assertEquals(e.get("bbmodel_sha256").getAsString(),sha(Path.of("art/blockbench/weapons/w30/"+id+".bbmodel")));
            assertFalse(e.getAsJsonObject("source_files").isEmpty());
            assertFalse(e.get("source_drive_id").getAsString().isBlank());
        }
    }
    @Test void thinBowStructureStaysConnectedAndTranslatedSniperReturnsToItsGrip() throws Exception {
        var bow=json(Path.of("art/blockbench/weapons/w30/biting_winds.bbmodel"));
        var cubes=bow.getAsJsonArray("elements");
        assertEquals("source_conservative_volume_cuboids_v2",bow.getAsJsonObject("destiny_w30").get("method").getAsString());
        // A center-ray sampler used to produce dozens of floating bow fragments.
        // Touching at a grid edge is valid for a diagonal voxelized limb.
        Set<Integer> connected=new HashSet<>();var queue=new ArrayDeque<Integer>();
        connected.add(0);queue.add(0);
        while(!queue.isEmpty()) {
            var a=cubes.get(queue.remove()).getAsJsonObject();
            for(int k=0;k<cubes.size();k++) {
                if(connected.contains(k))continue;
                var b=cubes.get(k).getAsJsonObject();boolean touches=true;
                for(int axis=0;axis<3;axis++)
                    touches &= a.getAsJsonArray("from").get(axis).getAsDouble()<=b.getAsJsonArray("to").get(axis).getAsDouble()+.00001
                            && b.getAsJsonArray("from").get(axis).getAsDouble()<=a.getAsJsonArray("to").get(axis).getAsDouble()+.00001;
                if(touches){connected.add(k);queue.add(k);}
            }
        }
        assertEquals(cubes.size(),connected.size(),"Bow limbs, arrow and string must form one connected structure");
        var sniper=json(Path.of("art/blockbench/weapons/w30/apostate.bbmodel")).getAsJsonObject("destiny_w30");
        assertTrue(sniper.has("source_coordinate_correction"));
        assertEquals(-1,sniper.getAsJsonObject("source_axis").get("muzzle_sign").getAsInt());
        var lo=sniper.getAsJsonArray("model_bounds").get(0).getAsJsonArray();
        var hi=sniper.getAsJsonArray("model_bounds").get(1).getAsJsonArray();
        assertTrue(lo.get(0).getAsDouble()<8 && hi.get(0).getAsDouble()>8,"Grip must not be shifted off hand");
        assertTrue(Math.abs((lo.get(0).getAsDouble()+hi.get(0).getAsDouble())*.5-8)<.2);
        assertTrue(8-lo.get(2).getAsDouble()>hi.get(2).getAsDouble()-8,"Long barrel must point toward -Z");
    }
    @Test void firstThirdLeftRightGuiAndAdsContextsStayDistinct() throws Exception {
        for(var e:originalW30Entries()) {
            var base=json(ROOT.resolve("models/weapon/"+e.family()+"/"+e.id()+".json"));
            var d=base.getAsJsonObject("display");
            for(String context:List.of("firstperson_righthand","firstperson_lefthand","thirdperson_righthand","thirdperson_lefthand","gui","ground","fixed"))
                assertTrue(d.has(context),e.id()+context);
            assertNotEquals(d.get("gui"),d.get("firstperson_righthand"));
            assertEquals(e.id().equals("ammit_ar2") ? 72 : 90,d.getAsJsonObject("thirdperson_righthand").getAsJsonArray("rotation").get(0).getAsInt());
            assertTrue(base.getAsJsonObject("textures").get("0").getAsString().startsWith("destiny:item/weapon/"),"Default native item atlas directory");
            var ads=json(ROOT.resolve("models/weapon/"+e.family()+"/"+e.id()+"_ads.json"));
            assertEquals("destiny:weapon/"+e.family()+"/"+e.id(),ads.get("parent").getAsString());
            assertNotEquals(d.get("firstperson_righthand"),ads.getAsJsonObject("display").get("firstperson_righthand"));
            assertEquals(d.get("thirdperson_righthand"),ads.getAsJsonObject("display").get("thirdperson_righthand"));
            assertEquals(e.family().equals("glaive")?90:0,ads.getAsJsonObject("display").getAsJsonObject("firstperson_righthand").getAsJsonArray("rotation").get(1).getAsInt(),
                    "Glaive twists its +Y shaft blade face; firearm -Z muzzle must not borrow GUI yaw");
            var bb=json(Path.of("art/blockbench/weapons/w30/"+e.id()+".bbmodel"));
            var bounds=bb.getAsJsonObject("destiny_w30").getAsJsonArray("model_bounds");
            for(String context:List.of("gui","fixed")) {
                var t=d.getAsJsonObject(context);
                var r=t.getAsJsonArray("rotation");
                var rotation=new org.joml.Quaternionf().rotationXYZ((float)Math.toRadians(r.get(0).getAsDouble()),(float)Math.toRadians(r.get(1).getAsDouble()),(float)Math.toRadians(r.get(2).getAsDouble()));
                var scale=t.getAsJsonArray("scale");var translation=t.getAsJsonArray("translation");
                for(int mask=0;mask<8;mask++) {
                    var v=new org.joml.Vector3f();
                    for(int a=0;a<3;a++)v.setComponent(a,bounds.get((mask>>a)&1).getAsJsonArray().get(a).getAsFloat()-8);
                    v.rotate(rotation).mul(scale.get(0).getAsFloat()).add(translation.get(0).getAsFloat(),translation.get(1).getAsFloat(),translation.get(2).getAsFloat());
                    assertTrue(Math.abs(v.x)<=7.401 && Math.abs(v.y)<=7.401,e.id()+" clipped "+context);
                }
            }
        }
    }
    private static String sha(Path p) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(p)));
    }
}
