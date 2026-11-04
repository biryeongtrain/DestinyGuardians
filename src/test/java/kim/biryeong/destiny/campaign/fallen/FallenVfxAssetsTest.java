package kim.biryeong.destiny.campaign.fallen;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.io.DataInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;
import java.util.HexFormat;
import java.util.Set;
import java.util.stream.Collectors;

import static org.junit.jupiter.api.Assertions.*;

/** W300 r5: the ported Fallen VFX sprite table matches the shipped assets and the FallenVfx sprite ids. */
class FallenVfxAssetsTest {
    private JsonObject json(String path) throws IOException {
        try (InputStream in = getClass().getResourceAsStream(path)) {
            assertNotNull(in, path);
            return JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    private JsonObject table() throws IOException { return json("/destiny/guardian_rises/fallen_vfx.json").getAsJsonObject("sprites"); }

    @Test
    void everyTableSpriteHasTextureModelAndItem() throws Exception {
        var sprites = table();
        assertEquals(13, sprites.size());
        for (var e : sprites.entrySet()) {
            String name = e.getKey();
            var row = e.getValue().getAsJsonObject();
            assertTrue(row.get("texture").getAsString().matches("[0-9A-F]{8}"), name);
            assertFalse(row.getAsJsonArray("particles").isEmpty(), name);
            int size = row.get("size").getAsInt();
            String shape = row.get("shape").getAsString();
            assertTrue(Set.of("quad", "beam").contains(shape), name);

            try (InputStream in = getClass().getResourceAsStream("/assets/destiny/textures/item/guardian_rises/vfx/" + name + ".png")) {
                assertNotNull(in, name + " texture");
                byte[] png = in.readAllBytes();
                assertArrayEquals(new byte[]{(byte) 0x89, 'P', 'N', 'G', 13, 10, 26, 10}, Arrays.copyOf(png, 8), name);
                var d = new DataInputStream(new java.io.ByteArrayInputStream(png, 16, 13));
                assertEquals(size, d.readInt(), name + " width");
                assertEquals(size, d.readInt(), name + " height");
                assertEquals(8, d.readUnsignedByte());
                assertEquals(6, d.readUnsignedByte(), name + " must be RGBA");
                var sha = HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(png));
                assertEquals(row.get("output_sha256").getAsString(), sha, name + " texture drifted from table");
            }

            var model = json("/assets/destiny/models/guardian_rises/vfx/" + name + ".json");
            assertEquals("destiny:item/guardian_rises/vfx/" + name, model.getAsJsonObject("textures").get("t").getAsString());
            var elements = model.getAsJsonArray("elements");
            assertEquals(shape.equals("beam") ? 2 : 1, elements.size(), name);
            for (var el : elements) {
                var faces = el.getAsJsonObject().getAsJsonObject("faces");
                for (var f : faces.entrySet()) assertEquals(0, f.getValue().getAsJsonObject().get("tintindex").getAsInt(), name);
                assertEquals(15, el.getAsJsonObject().get("light_emission").getAsInt(), name);
            }

            var item = json("/assets/destiny/items/guardian_rises/vfx/" + name + ".json").getAsJsonObject("model");
            assertEquals("destiny:guardian_rises/vfx/" + name, item.get("model").getAsString());
            assertEquals("minecraft:custom_model_data", item.getAsJsonArray("tints").get(0).getAsJsonObject().get("type").getAsString());
        }
    }

    @Test
    void codeSpriteIdsMatchTable() throws IOException {
        Set<String> table = table().keySet();
        Set<String> code = Arrays.stream(FallenVfx.Sprite.values()).map(FallenVfx.Sprite::id).collect(Collectors.toSet());
        assertEquals(table, code);
        for (var s : FallenVfx.Sprite.values())
            assertEquals(s.beam, table().getAsJsonObject(s.id()).get("shape").getAsString().equals("beam"), s.id());
    }

    @Test
    void segmentDistance() {
        Vec3 a = new Vec3(0, 0, 0), b = new Vec3(10, 0, 0);
        assertEquals(4, FallenVfx.segmentDistanceSq(new Vec3(5, 2, 0), a, b), 1e-9);
        assertEquals(1, FallenVfx.segmentDistanceSq(new Vec3(-1, 0, 0), a, b), 1e-9);
        assertEquals(4, FallenVfx.segmentDistanceSq(new Vec3(12, 0, 0), a, b), 1e-9);
        assertEquals(1, FallenVfx.segmentDistanceSq(new Vec3(0, 1, 0), a, a), 1e-9);
    }

    @Test
    void jetAxisMapsXOntoDirection() {
        var q = FallenVfx.axisX(new Vec3(0, 0, 1), 0);
        var v = q.transform(new org.joml.Vector3f(1, 0, 0));
        assertEquals(0, v.x, 1e-5); assertEquals(0, v.y, 1e-5); assertEquals(1, v.z, 1e-5);
    }

    @Test
    void starsAreCappedToFourDegreesAndShrunk() {
        // r5b: a burst_star impact (peak .95 * STAR_SCALE) seen from 1.5 / 3 / 10 / 30 blocks
        float peak = .95f * FallenVfx.STAR_SCALE;
        for (double d : new double[]{1.5, 3, 10, 30}) {
            float k = FallenVfx.capFactor(FallenVfx.Sprite.BURST_STAR, peak, d);
            double deg = Math.toDegrees(2 * Math.atan(peak * k / 2 / d));
            assertTrue(deg <= FallenVfx.STAR_DEG + 1e-3, d + " -> " + deg);
        }
        assertEquals(1f, FallenVfx.capFactor(FallenVfx.Sprite.BURST_STAR, peak, 30), 1e-6); // far: untouched
        assertEquals(4.0, Math.toDegrees(2 * Math.atan(FallenVfx.maxSize(5, 4) / 2 / 5)), 1e-4);
        assertEquals(0x4C4C4C, FallenVfx.dim(0x808080, .6f));
        assertTrue(FallenVfx.TRAIL_W0 <= .12f && FallenVfx.TRAIL_LIFE <= 2);
    }
}
