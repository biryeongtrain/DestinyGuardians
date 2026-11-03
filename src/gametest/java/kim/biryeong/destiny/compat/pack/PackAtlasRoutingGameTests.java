package kim.biryeong.destiny.compat.pack;

import com.google.gson.*;
import eu.pb4.polymer.resourcepack.api.*;
import eu.pb4.polymer.resourcepack.impl.generation.DefaultRPBuilder;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import java.util.*;

public final class PackAtlasRoutingGameTests {
    @GameTest(structure="destiny-test:floor", maxTicks=300, environment="destiny-test:w90_isolated")
    public void realMergePipelineKeepsRoutedAtlases(GameTestHelper h) throws Exception {
        var builder = new DefaultRPBuilder<Map<String, PackResource>>((entries, converter, status) -> {
            var out = new HashMap<String, PackResource>();
            for (var e : entries) {
                var data = converter.convert(e.getKey(), e.getValue());
                if (data != null) out.put(e.getKey(), data);
            }
            return out;
        }, ResourcePackStatusConsumer.nonLogging());
        PackAtlasRouting.prepare(builder);
        try (var in = getClass().getResourceAsStream("/destiny/devils_lair/models/dl_skiff.bbmodel")) {
            var model = JsonParser.parseString(new String(in.readAllBytes(), java.nio.charset.StandardCharsets.UTF_8)).getAsJsonObject();
            int index = 0;
            for (var texture : model.getAsJsonArray("textures")) {
                var data = Base64.getDecoder().decode(texture.getAsJsonObject().get("source").getAsString().split(",", 2)[1]);
                builder.addData("assets/bettermodel/textures/item/renamed_" + index++ + ".png", data);
            }
        }
        builder.addPreFinishTask(b -> {
            var files = new HashMap<String, PackResource>(); b.forEachResource(files::put);
            PackAtlasRouting.apply(b, files);
        });
        var future = builder.buildResourcePack();
        h.succeedWhen(() -> {
            h.assertTrue(future.isDone(), "Pack output completed");
            var output = future.join();
            for (String path : List.of("assets/minecraft/atlases/items.json", "assets/minecraft/atlases/blocks.json")) {
                h.assertTrue(output.containsKey(path), "Merged output includes " + path);
                var sources = JsonParser.parseString(output.get(path).asString()).getAsJsonObject().getAsJsonArray("sources");
                h.assertTrue(sources.size() == 2, "Both exact textures routed in " + path);
            }
        });
    }
}
