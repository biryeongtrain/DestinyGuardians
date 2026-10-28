package kim.biryeong.destiny.world;

import org.junit.jupiter.api.Test;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.zip.GZIPOutputStream;
import static org.junit.jupiter.api.Assertions.*;

class TowerVoxelMapTest {
    private static final String MANIFEST = """
            {"schema":1,"id":"destiny:tower","voxelResource":"data/destiny/tower/courtyard.vox.gz",
             "bounds":{"min":[-17,-64,-17],"max":[16,319,16]},
             "spawn":{"x":0.5,"y":1,"z":0.5,"yaw":180,"pitch":0},
             "returnBelowY":-60,"worldBorder":48,"blockCount":%d,
             "provenance":{"extra":"allowed"}}
            """;
    private record Voxel(int x, int y, int z, int palette) {}
    private static byte[] binary(String magic, List<String> palette, List<Voxel> voxels, boolean trailing) throws IOException {
        var bytes = new ByteArrayOutputStream();
        try (var out = new DataOutputStream(new GZIPOutputStream(bytes))) {
            out.write(magic.getBytes(StandardCharsets.US_ASCII));
            out.writeInt(palette.size());
            for (var state : palette) {
                byte[] utf = state.getBytes(StandardCharsets.UTF_8);
                out.writeShort(utf.length); out.write(utf);
            }
            out.writeInt(voxels.size());
            for (var v : voxels) { out.writeInt(v.x()); out.writeInt(v.y()); out.writeInt(v.z()); out.writeShort(v.palette()); }
            if (trailing) out.writeByte(1);
        }
        return bytes.toByteArray();
    }
    private static TowerVoxelMap decode(String manifest, byte[] bytes) throws IOException {
        return TowerVoxelMap.decode(new ByteArrayInputStream(manifest.getBytes(StandardCharsets.UTF_8)), new ByteArrayInputStream(bytes));
    }
    @Test void sparseRoundTripPreservesNegativeChunksAirAndStateProperties() throws IOException {
        var voxels = List.of(new Voxel(-17, -64, -17, 0), new Voxel(-1, 0, -1, 1),
                new Voxel(0, 0, 0, 0), new Voxel(16, 319, 16, 1));
        var map = decode(MANIFEST.formatted(voxels.size()), binary("DGTWR001",
                List.of("minecraft:stone", "minecraft:oak_log[axis=x]"), voxels, false));
        assertEquals(4, map.blockCount());
        assertEquals(0, map.paletteIndexAt(-17, -64, -17));
        assertEquals(1, map.paletteIndexAt(-1, 0, -1));
        assertEquals(1, map.paletteIndexAt(16, 319, 16));
        assertEquals(-1, map.paletteIndexAt(-1, 1, -1), "Source air remains absent");
        assertEquals(-1, map.paletteIndexAt(17, 319, 16), "Outside map remains void");
        var found = new java.util.ArrayList<Voxel>();
        map.forChunk(-1, -1, (x, y, z, palette) -> found.add(new Voxel(x, y, z, palette)));
        assertEquals(List.of(new Voxel(-1, 0, -1, 1)), found);
        assertThrows(UnsupportedOperationException.class, () -> map.palette().set(0, "minecraft:dirt"));
        assertEquals("minecraft:oak_log[axis=x]", map.palette().get(1));
    }
    @Test void malformedPayloadsFailBeforeGeneration() throws IOException {
        var stone = List.of("minecraft:stone");
        var one = List.of(new Voxel(0, 0, 0, 0));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("BADMAGIC", stone, one, false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(2), binary("DGTWR001", stone, one, false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(2), binary("DGTWR001", stone,
                List.of(one.getFirst(), one.getFirst()), false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("DGTWR001", stone, List.of(new Voxel(0, 0, 0, 1)), false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("DGTWR001", stone, List.of(new Voxel(17, 0, 0, 0)), false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("DGTWR001", List.of("minecraft:air"), one, false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("DGTWR001", List.of("destiny:custom"), one, false)));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), binary("DGTWR001", stone, one, true)));
        byte[] complete = binary("DGTWR001", stone, one, false);
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1), java.util.Arrays.copyOf(complete, complete.length - 8)));
    }
    @Test void manifestRejectsInvalidHeightSpawnAndBorderButAllowsProvenance() throws IOException {
        byte[] bytes = binary("DGTWR001", List.of("minecraft:stone"), List.of(new Voxel(0, 0, 0, 0)), false);
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1).replace("-17,-64,-17", "-17,-65,-17"), bytes));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1).replace("\"y\":1", "\"y\":400"), bytes));
        assertThrows(IOException.class, () -> decode(MANIFEST.formatted(1).replace("\"worldBorder\":48", "\"worldBorder\":20"), bytes));
        assertEquals(1, decode(MANIFEST.formatted(1), bytes).blockCount());
    }
}
