package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class WeaponGripW32Test {
    private static JsonObject read(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    private static Matrix4f transform(JsonObject display, boolean left) {
        var r=display.getAsJsonArray("rotation");var t=display.getAsJsonArray("translation");
        var s=display.getAsJsonArray("scale");float sign=left?-1:1;
        return new Matrix4f().translate(t.get(0).getAsFloat()*sign/16,t.get(1).getAsFloat()/16,t.get(2).getAsFloat()/16)
                .rotateXYZ((float)Math.toRadians(r.get(0).getAsDouble()),(float)Math.toRadians(r.get(1).getAsDouble())*sign,(float)Math.toRadians(r.get(2).getAsDouble())*sign)
                .scale(s.get(0).getAsFloat(),s.get(1).getAsFloat(),s.get(2).getAsFloat());
    }
    @Test void chargedCrossbowIdleCompensationPreservesEveryFirstPersonPoseAndHand() throws Exception {
        for(var row:WeaponCatalogTest.originalW30Entries())for(String suffix:List.of("","_ads","_inspect")) {
            Path root=Path.of("src/main/resources/assets/destiny/models/weapon/"+row.family());
            var nativeModel=read(root.resolve(row.id()+suffix+".json"));
            var gripModel=read(root.resolve(row.id()+suffix+"_twohand.json"));
            assertEquals("destiny:weapon/"+row.family()+"/"+row.id()+suffix,gripModel.get("parent").getAsString());
            assertFalse(gripModel.has("elements"),"No geometry duplication");
            var old=nativeModel.getAsJsonObject("display");var next=gripModel.getAsJsonObject("display");
            for(boolean left:List.of(false,true)) {
                String context="firstperson_"+(left?"lefthand":"righthand");float sign=left?-1:1;
                Matrix4f compensated=new Matrix4f().translate(-.641864f*sign,0,0)
                        .rotateY((float)Math.toRadians(10)*sign).mul(transform(next.getAsJsonObject(context),left));
                assertTrue(transform(old.getAsJsonObject(context),left).equals(compensated,.000002f),row.id()+suffix+context);
            }
            for(String context:List.of("gui","ground","fixed","head"))
                assertEquals(old.get(context),next.get(context),"Non-held contexts preserved");
        }
    }
    @Test void gripFlagAndPoseStringRemainIndependentAndNativeFallbackIsRetained() throws Exception {
        for(var row:WeaponCatalogTest.originalW30Entries()) {
            var item=read(Path.of("src/main/resources/assets/destiny/items/weapon/"+row.id()+".json"));
            if (row.id().equals("ammit_ar2")) {
                var record=read(Path.of("art/weapons/w161/ammit-crouch.json")).getAsJsonObject("graphs")
                        .getAsJsonObject("src/main/resources/assets/destiny/items/weapon/ammit_ar2.json");
                GripContractsW163Support.assertAssetHash("src/main/resources/assets/destiny/items/weapon/ammit_ar2.json",
                        record.get("beforeSha256").getAsString());
                item=GripContractsW163Support.originalAmmitGraph(item);
            }
            var root=item.getAsJsonObject("model");
            assertEquals("minecraft:select",root.get("type").getAsString());
            var branches=new java.util.ArrayList<JsonObject>();branches.add(root.getAsJsonObject("fallback"));
            root.getAsJsonArray("cases").forEach(c->branches.add(c.getAsJsonObject().getAsJsonObject("model")));
            for(var branch:branches) {
                assertEquals("minecraft:condition",branch.get("type").getAsString());
                assertEquals("minecraft:custom_model_data",branch.get("property").getAsString());
                assertEquals(0,branch.get("index").getAsInt());
                String nativeId=branch.getAsJsonObject("on_false").get("model").getAsString();
                assertEquals(nativeId+"_twohand",branch.getAsJsonObject("on_true").get("model").getAsString());
            }
        }
    }
    @Test void reviewedCrouchMigrationRejectsWrongFlagContextAndFallback() throws Exception {
        var path=Path.of("src/main/resources/assets/destiny/items/weapon/ammit_ar2.json");
        for (String mutation : List.of("flag", "context", "fallback")) {
            var item=read(path);
            var wrapper=item.getAsJsonObject("model").getAsJsonObject("fallback").getAsJsonObject("on_true");
            var branch=wrapper.getAsJsonArray("cases").get(0).getAsJsonObject();
            switch (mutation) {
                case "flag" -> branch.getAsJsonObject("model").addProperty("index", 0);
                case "context" -> branch.add("when", JsonParser.parseString("[\"firstperson_righthand\",\"thirdperson_lefthand\"]"));
                case "fallback" -> branch.getAsJsonObject("model").add("on_false",
                        GripContractsW163Support.leaf("destiny:weapon/auto_rifle/ammit_ar2"));
            }
            assertThrows(AssertionError.class, () -> GripContractsW163Support.originalAmmitGraph(item), mutation);
        }
    }
    @Test void longGunsAndGlaiveOptInButBowsAndSwordsRemainNative() {
        assertEquals(47,WeaponCatalogTest.originalW30Entries().stream().filter(e->WeaponModels.defaultGrip(e)==WeaponModels.Grip.TWO_HAND).count());
        assertEquals(48,WeaponCatalog.all().stream().filter(e->WeaponModels.defaultGrip(e)==WeaponModels.Grip.TWO_HAND).count());
        assertEquals(56,WeaponCatalogTest.originalW30Entries().stream().filter(WeaponModels::supportsTwoHand).count());
        assertEquals(58,WeaponCatalog.all().stream().filter(WeaponModels::supportsTwoHand).count());
        for(var row:WeaponCatalog.all())if(List.of("hand_cannon","sidearm","bow","sword").contains(row.family()))
            assertEquals(WeaponModels.Grip.NATIVE,WeaponModels.defaultGrip(row));
    }
}
