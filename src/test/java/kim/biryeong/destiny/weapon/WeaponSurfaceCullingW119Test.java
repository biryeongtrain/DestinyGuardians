package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.nio.file.Files;
import java.nio.file.Path;

import static org.junit.jupiter.api.Assertions.*;

/** Pack optimization/assembly evidence, not a GPU/FPS or art acceptance test. */
class WeaponSurfaceCullingW119Test {
    private static JsonObject model(WeaponSurfaceAssets.Rule rule) {
        return JsonParser.parseString(rule.replacement()).getAsJsonObject();
    }
    private static int faces(JsonObject model) {
        int n=0;
        for (var e:model.getAsJsonArray("elements")) n+=e.getAsJsonObject().getAsJsonObject("faces").size();
        return n;
    }

    @Test void actualOutputKeepsAllSevenHashedInputsAndReducesOnlyReviewedPartInteriors() throws java.io.IOException {
        var original=WeaponSurfaceAssets.rules();
        var sealed=new HashMap<>(original);
        var result=WeaponSurfaceAssets.optimizeRules(original);
        assertEquals(sealed,original,"Authored W118 input rules must not mutate");
        assertEquals(WeaponSurfaceAssets.TARGETS,result.rules().keySet());
        assertEquals(5,result.parts().size());
        int total=0;
        for (var row:result.parts().entrySet()) {
            assertTrue(row.getKey().contains("weapon_reload_w114_"));
            var before=model(original.get(row.getKey()));var after=model(result.rules().get(row.getKey()));
            var oldNames=new HashMap<String,JsonObject>();
            for (var e:before.getAsJsonArray("elements")) oldNames.put(e.getAsJsonObject().get("name").getAsString(),e.getAsJsonObject());
            var kept=new HashMap<String,JsonObject>();
            for (var e:after.getAsJsonArray("elements")) {
                var object=e.getAsJsonObject();String name=object.get("name").getAsString();
                assertEquals(oldNames.get(name),object,"No retained cube/UV/rotation may be simplified");
                kept.put(name,object);
            }
            for (var removed:row.getValue()) {
                assertTrue(oldNames.containsKey(removed.name()));assertFalse(kept.containsKey(removed.name()));
                assertTrue(kept.containsKey(removed.container()),"Audit points at retained SAME-PART container");
                assertTrue(removed.minClearance()>.0001);
            }
            assertEquals(oldNames.size(),kept.size()+row.getValue().size());
            assertTrue(faces(after)<=faces(before));total+=row.getValue().size();
            System.out.printf("W119 %s: %d -> %d elements; %d -> %d faces; removed %d%n",
                    row.getKey(),oldNames.size(),kept.size(),faces(before),faces(after),row.getValue().size());
        }
        assertTrue(total>200,"Concrete authored-model reduction, not only synthetic fixtures");
        for (String path:original.keySet()) {
            var a=original.get(path);var b=result.rules().get(path);
            assertEquals(a.sourceSha256(),b.sourceSha256());assertEquals(a.replacementPath(),b.replacementPath());
            assertEquals(b.replacementSha256(),WeaponSurfaceAssets.sha256(b.replacement()));
            var before=model(a);var after=model(b);
            before.remove("elements");after.remove("elements");assertEquals(before,after,"Textures/transforms/metadata unchanged");
        }
        // Deterministic build-only fixtures for the master's offline/native pack
        // audit. Never overwrite editable assets or sealed docs/qa evidence.
        Path export=Path.of("build/qa/w119-culling");Files.createDirectories(export);
        var audit=new JsonObject();
        for (var row:result.rules().entrySet()) {
            String file=row.getKey().substring(row.getKey().lastIndexOf('/')+1);
            Files.writeString(export.resolve(file),row.getValue().replacement());
            var meta=new JsonObject();meta.addProperty("inputSha256",original.get(row.getKey()).replacementSha256());
            meta.addProperty("outputSha256",row.getValue().replacementSha256());
            var removed=new com.google.gson.Gson().toJsonTree(result.parts().getOrDefault(row.getKey(),List.of()));
            meta.add("removals",removed);audit.add(row.getKey(),meta);
        }
        Files.writeString(export.resolve("audit.json"),audit.toString());
    }

    @Test void optimizedWholeIsExactlyOrderedAssemblyOfSeparatelyOptimizedRigidParts() {
        var rules=WeaponSurfaceAssets.optimizeRules(WeaponSurfaceAssets.rules()).rules();
        for (String id:List.of("blast_furnace","hammerhead")) {
            String family=id.equals("blast_furnace")?"pulse_rifle":"machine_gun";
            var full=model(rules.get("assets/destiny/models/weapon/"+family+"/"+id+".json"));
            var assembly=new JsonArray();
            for (String part:id.equals("blast_furnace")?List.of("body","magazine"):List.of("body","magazine","cover")) {
                var split=model(rules.get("assets/destiny/models/weapon_reload_w114_"+id+"/"+id+"_"+part+".json"));
                assembly.addAll(split.getAsJsonArray("elements"));
            }
            assertEquals(assembly,full.getAsJsonArray("elements"));
        }
    }

    @Test void changedOrIncompleteInputsRejectBeforeOptimization() {
        var rules=new HashMap<>(WeaponSurfaceAssets.rules());
        String path=rules.keySet().iterator().next();var rule=rules.get(path);
        rules.put(path,new WeaponSurfaceAssets.Rule(rule.sourceSha256(),rule.replacementSha256(),rule.replacementPath(),rule.replacement()+" "));
        assertThrows(IllegalStateException.class,()->WeaponSurfaceAssets.optimizeRules(rules));
        assertThrows(IllegalStateException.class,()->WeaponSurfaceAssets.optimizeRules(Map.of()));
    }

    @Test void optimizedConversionStillChecksHashesAndIsIdempotent() {
        var original=WeaponSurfaceAssets.rules();var rules=WeaponSurfaceAssets.optimizeRules(original).rules();
        for (String path:rules.keySet()) {
            var rule=rules.get(path);
            var out=PackResource.fromString(rule.replacement());
            assertSame(out,WeaponSurfaceAssets.convert(path,out,rules));
            assertThrows(IllegalStateException.class,()->WeaponSurfaceAssets.convert(path,PackResource.fromString(rule.replacement()+"\n"),rules));
        }
        var twice=WeaponSurfaceAssets.optimizeRules(rules);
        assertEquals(rules,twice.rules());
        assertTrue(twice.parts().values().stream().allMatch(List::isEmpty));
    }

    @Test void packCallbackIsExplicitlyOptInAndDefaultStillEmitsAuthoredCandidateBytes() throws java.io.IOException {
        String key="destiny.weapon.surface.cull.w119",old=System.getProperty(key);
        try {
            for (boolean enabled:new boolean[]{false,true}) {
                System.setProperty(key,Boolean.toString(enabled));
                var converters=new java.util.ArrayList<eu.pb4.polymer.resourcepack.api.ResourcePackBuilder.ResourceConverter>();
                var builder=(eu.pb4.polymer.resourcepack.api.ResourcePackBuilder)java.lang.reflect.Proxy.newProxyInstance(
                        getClass().getClassLoader(),new Class<?>[]{eu.pb4.polymer.resourcepack.api.ResourcePackBuilder.class},
                        (proxy,method,args)->switch(method.getName()) {
                            case "addResourceConverter" -> {converters.add((eu.pb4.polymer.resourcepack.api.ResourcePackBuilder.ResourceConverter)args[0]);yield null;}
                            case "addPreFinishTask" -> null;
                            default -> throw new AssertionError("Unexpected pack API: "+method.getName());
                        });
                WeaponSurfaceAssets.configure(builder);assertEquals(1,converters.size());
                var expected=enabled?WeaponSurfaceAssets.optimizeRules(WeaponSurfaceAssets.rules()).rules():WeaponSurfaceAssets.rules();
                for (String path:expected.keySet()) {
                    String canonical=Files.readString(Path.of("src/main/resources").resolve(path));
                    var result=converters.getFirst().convert(path,PackResource.fromString(canonical));
                    assertEquals(expected.get(path).replacement(),result.asString());
                    assertSame(result,converters.getFirst().convert(path,result));
                }
            }
        } finally {
            if (old==null) System.clearProperty(key);else System.setProperty(key,old);
        }
    }
}
