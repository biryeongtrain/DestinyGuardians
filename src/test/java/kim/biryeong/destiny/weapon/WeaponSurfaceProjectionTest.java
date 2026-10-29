package kim.biryeong.destiny.weapon;

import eu.pb4.polymer.resourcepack.api.PackResource;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.HashMap;
import static org.junit.jupiter.api.Assertions.*;

class WeaponSurfaceProjectionTest {
    private static final Path RES = Path.of("src/main/resources");
    @Test void projectedSnapshotMatchesFinalConverterAndKeepsInputsDetached() throws Exception {
        var original = new HashMap<String, PackResource>();
        for (String path : WeaponSurfaceW123Assets.TARGETS)
            original.put(path, PackResource.fromString(Files.readString(RES.resolve(path))));
        var projected = new HashMap<>(original);
        WeaponSurfaceProjection.projectOutput(projected, false);
        var rules = WeaponSurfaceW123Assets.rules();
        for (String path : original.keySet()) {
            assertEquals(WeaponSurfaceW123Assets.convert(path, original.get(path), rules).asString(), projected.get(path).asString());
            assertEquals(Files.readString(RES.resolve(path)), original.get(path).asString());
        }
        var legacy = new HashMap<>(original);
        WeaponSurfaceProjection.projectOutput(legacy, true);
        for (String path : WeaponSurfaceAssets.TARGETS) assertSame(original.get(path), legacy.get(path));
        // Sword replacement textures are introduced by the converter, and must survive pruning.
        assertTrue(projected.values().stream().anyMatch(r -> r.asString().contains("destiny:item/weapon/w123/crown_splitter")));
    }

}
