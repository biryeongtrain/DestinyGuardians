package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.*;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.*;
import net.minecraft.resources.Identifier;
import org.joml.Matrix4f;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Converts the accepted pose graph into server-side selectors and five shared view displays.
 * Legacy sources stay on disk; pixel/tint arm graphs never enter the production client pack. */
public final class ProfileArmAssets {
    public record Pose(Matrix4f right, Matrix4f left, boolean leftArm, boolean upper) {}
    private static volatile Map<Identifier, JsonObject> graphs = Map.of();
    private static volatile Map<String, Pose> poses = Map.of();
    public static final String ITEM = "profile_arm";
    public static final String ITEM_JSON = "{\"model\":{\"type\":\"minecraft:special\",\"base\":\"destiny:profile_arm\",\"transformation\":[1,0,0,0.5,0,1,0,0.5,0,0,1,0.5,0,0,0,1],\"model\":{\"type\":\"minecraft:player_head\"}}}";
    private ProfileArmAssets() {}
    public static Identifier view(Identifier id) {return DestinyGuardians.id("profile_view/"+id.getPath());}
    public static JsonObject graph(Identifier id) {return graphs.get(id);}
    public static Pose pose(String id) {return poses.get(id);}

    static void compact(ResourcePackBuilder builder, Map<String,PackResource> files, Set<Identifier> active) {
        var newGraphs=new HashMap<Identifier,JsonObject>();var newPoses=new HashMap<String,Pose>();
        var omitted=new HashSet<String>();
        for(String path:files.keySet())
            if(path.startsWith("assets/destiny/items/weapon_hands_w201/") || path.startsWith("assets/destiny/models/skin_arm_w204/")
                    || path.startsWith("assets/destiny/textures/item/skin_arm_w204/")) omitted.add(path);
        long before=0,after=0;
        for(var source:WeaponFirstPersonHands.sources()) {
            if(!active.contains(source)) {omitted.add(WeaponPackOptimizer.itemPath(source));continue;}
            String wrapped=WeaponPackOptimizer.itemPath(WeaponFirstPersonHands.model(source));
            var old=files.get(wrapped);
            if(old==null)throw new IllegalStateException("Missing profile-arm source "+wrapped);
            var original=JsonParser.parseString(old.asString()).getAsJsonObject();before+=old.readAllBytes().length;
            var arms=ProfileArmGraph.armsOnly(original.getAsJsonObject("model"));
            newGraphs.put(source,arms);collectPoses(arms,files,newPoses);
            // The world view display evaluates the exact same CMD selectors as the held item.
            var gun=WeaponPackOptimizer.specialize(gunOnly(original.getAsJsonObject("model")));
            var view=new JsonObject();view.add("model",gun);
            put(builder,files,WeaponPackOptimizer.itemPath(view(source)),view);
            after+=view.toString().getBytes(StandardCharsets.UTF_8).length;
            // Inventory, dropped and observer third-person representations retain the original route.
            var held=new JsonObject();held.add("model",firstPersonEmpty(
                    JsonParser.parseString(files.get(WeaponPackOptimizer.itemPath(source)).asString()).getAsJsonObject().getAsJsonObject("model")));
            put(builder,files,wrapped,held);omitted.remove(wrapped);
            after+=held.toString().getBytes(StandardCharsets.UTF_8).length;
        }
        put(builder,files,"assets/destiny/items/"+ITEM+".json",JsonParser.parseString(ITEM_JSON).getAsJsonObject());
        put(builder,files,"assets/destiny/models/"+ITEM+".json",new JsonObject());
        var reachable=new HashSet<String>();
        for(var e:files.entrySet())if(e.getKey().contains("/items/")&&e.getKey().endsWith(".json")&&!omitted.contains(e.getKey()))
            WeaponPackOptimizer.references(JsonParser.parseString(e.getValue().asString()),reachable);
        for(String path:files.keySet())if(path.contains("/models/")&&path.endsWith(".json")&&!WeaponPackOptimizer.generatedPose(path)&&!omitted.contains(path))reachable.add(path);
        var queue=new ArrayDeque<>(reachable);
        while(!queue.isEmpty()) {
            var data=files.get(queue.removeFirst());if(data==null)continue;
            var n=JsonParser.parseString(data.asString()).getAsJsonObject();
            if(n.has("parent")) {String parent=WeaponPackOptimizer.modelPath(n.get("parent").getAsString());if(reachable.add(parent))queue.add(parent);}
        }
        for(String path:files.keySet())if(WeaponPackOptimizer.generatedPose(path)&&!reachable.contains(path))omitted.add(path);
        int sharedModels=PackModelDeduplicator.compact(builder,files,omitted);
        int previousOmitted=omitted.size();
        PackModelPruner.prune(files,omitted);
        DestinyGuardians.LOGGER.info("Weapon model sharing: {} exact aliases, {} additional unused models omitted",sharedModels,omitted.size()-previousOmitted);
        int removedTextures=Boolean.getBoolean("destiny.weapon.surface.w115")?0:PackWeaponTexturePruner.prune(files,omitted);
        DestinyGuardians.LOGGER.info("Weapon textures: {} unused versioned PNGs omitted without resampling",removedTextures);
        Set<String> excluded=Set.copyOf(omitted);builder.addResourceConverter((path,data)->excluded.contains(path)?null:data);
        patchShaders(builder);
        poses=Map.copyOf(newPoses);graphs=Map.copyOf(newGraphs);
        DestinyGuardians.LOGGER.info("Profile skin view: {} routes, {} server poses, {} omitted files; item graphs {} -> {} bytes",newGraphs.size(),newPoses.size(),omitted.size(),before,after);
    }
    private static JsonObject firstPersonEmpty(JsonObject fallback) {
        var n=new JsonObject();n.addProperty("type","minecraft:select");n.addProperty("property","minecraft:display_context");
        var cases=new JsonArray();var c=new JsonObject();var contexts=new JsonArray();contexts.add("firstperson_righthand");contexts.add("firstperson_lefthand");c.add("when",contexts);c.add("model",empty());cases.add(c);n.add("cases",cases);n.add("fallback",fallback);return n;
    }
    private static JsonObject empty(){var n=new JsonObject();n.addProperty("type","minecraft:empty");return n;}
    static JsonObject gunOnly(JsonObject input) {
        String type=input.get("type").getAsString();
        if(type.equals("minecraft:model")&&input.get("model").getAsString().startsWith("destiny:skin_arm_w204/"))return empty();
        var n=new JsonObject();
        // Copy opaque metadata once; model edges are rebuilt without copying their source subtrees.
        // Iterate in source order so serialized field order also stays unchanged.
        for(var field:input.entrySet()) {
            String key=field.getKey();var value=field.getValue();
            if(key.equals("fallback")||key.equals("on_true")||key.equals("on_false")) {
                n.add(key,gunOnly(value.getAsJsonObject()));
            } else if(key.equals("entries")||key.equals("cases")) {
                var entries=new JsonArray();
                for(var entry:value.getAsJsonArray()) {
                    var source=entry.getAsJsonObject();
                    var child=gunOnly(source.getAsJsonObject("model"));
                    var copy=new JsonObject();
                    for(var metadata:source.entrySet())
                        copy.add(metadata.getKey(),metadata.getKey().equals("model")?child:metadata.getValue().deepCopy());
                    entries.add(copy);
                }
                n.add(key,entries);
            } else if(key.equals("models")&&type.equals("minecraft:composite")) {
                var models=new JsonArray();
                for(var entry:value.getAsJsonArray()) {
                    var child=gunOnly(entry.getAsJsonObject());
                    if(!child.get("type").getAsString().equals("minecraft:empty"))models.add(child);
                }
                n.add(key,models);
            } else n.add(key,value.deepCopy());
        }
        if(type.equals("minecraft:composite")) {
            var models=n.getAsJsonArray("models");
            if(models.isEmpty())return empty();
            if(models.size()==1)return models.get(0).getAsJsonObject();
        }
        return n;
    }
    private static void collectPoses(JsonObject n,Map<String,PackResource> files,Map<String,Pose> out) {
        if(n.get("type").getAsString().equals("minecraft:model")) {
            String id=n.get("model").getAsString();
            out.computeIfAbsent(id,key->{var p=JsonParser.parseString(files.get(WeaponPackOptimizer.modelPath(key)).asString()).getAsJsonObject();
                String parent=p.get("parent").getAsString();var d=p.getAsJsonObject("display");
                return new Pose(SharedArmGeometry.displayMatrix(d.getAsJsonObject("firstperson_righthand"),false),SharedArmGeometry.displayMatrix(d.getAsJsonObject("firstperson_lefthand"),true),parent.contains("/left"),parent.contains("_upper_"));});return;
        }
        for(String k:List.of("fallback","on_true","on_false"))if(n.has(k))collectPoses(n.getAsJsonObject(k),files,out);
        for(String k:List.of("entries","cases","models"))if(n.has(k))for(var v:n.getAsJsonArray(k))collectPoses((k.equals("models")?v:v.getAsJsonObject().get("model")).getAsJsonObject(),files,out);
    }
    private static void put(ResourcePackBuilder b,Map<String,PackResource> files,String path,JsonObject n){var r=PackResource.fromString(n.toString());b.addData(path,r);files.put(path,r);}
    private static void patchShaders(ResourcePackBuilder pack) {
        // CriticalHudShader runs as an output converter; patch its byte-pinned result afterwards.
        pack.addResourceConverter((path,data)->{
            if(!path.equals("assets/minecraft/shaders/core/item.vsh"))return data;
            if(data==null)throw new IllegalStateException("Missing item shader");
            byte[] item=data.readAllBytes();
            try {String actual=HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(item));
                if(!actual.equals("ba38368c958a83ceb790ba68c119eb596dd30d8b1cf0e7f9197932e8fc168641"))throw new IllegalStateException("Incompatible item shader "+actual);
            }catch(java.security.NoSuchAlgorithmException e){throw new AssertionError(e);}
            String source=new String(item,StandardCharsets.UTF_8);int end=source.lastIndexOf('}');
            return PackResource.fromString(source.substring(0,end)+resource("main.item.vsh")+source.substring(end));
        });
        for(String ext:List.of("vsh","fsh")) {
            String path="assets/minecraft/shaders/core/entity."+ext;
            byte[] bytes=pack.getDataOrSource(path);if(bytes==null)throw new IllegalStateException("Missing entity shader");
            String expected=ext.equals("vsh")?"cdb69b412e00d06aa5e76556331ce82e5c0695c5b6a8c0b14da7081fad2f6227":"b349430785b693e8635765b7804034e28c3e6ec0e91f21fb9c224b4e226a90fa";
            try {if(!HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes)).equals(expected))throw new IllegalStateException("Incompatible entity shader "+path);}catch(java.security.NoSuchAlgorithmException e){throw new AssertionError(e);}
            String s=new String(bytes,StandardCharsets.UTF_8);s=s.replace("void main() {",resource("decl."+ext)+"\nvoid main() {");
            if(ext.equals("vsh")){int end=s.lastIndexOf('}');s=s.substring(0,end)+resource("main.vsh")+s.substring(end);}
            else s=s.replace("    vec4 color = texture(Sampler0, texCoord0);",resource("sample.fsh"));
            pack.addData(path,PackResource.fromString(s));
        }
    }
    private static String resource(String name) {
        try(var in=ProfileArmAssets.class.getResourceAsStream("/destiny/profile_view/"+name)){if(in==null)throw new IllegalStateException(name);return new String(in.readAllBytes(),StandardCharsets.UTF_8);}catch(java.io.IOException e){throw new IllegalStateException(e);}
    }
}
