package kim.biryeong.destiny.testfixtures;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HexFormat;
import java.util.Map;
import static org.junit.jupiter.api.Assertions.*;

/** Historical derivation inputs authenticated by the original W123/W112 records.
 * Current W251 assets are validated by their current contracts, not these old banks. */
public final class PreW251Assets {
    private static final String MODEL = "src/main/resources/assets/destiny/models/weapon_surface_w123/";
    private static final Map<String,String> HASHES = Map.ofEntries(
            Map.entry(MODEL+"austringer.json", "2026a115380d72420a5f7bd60928547ef567303addd511c75b92f58b0c3bf93c"),
            Map.entry(MODEL+"mindbender_s_ambition_adept.json", "2c972e49103f55ce199d21b90c74f2b934ce7376f9066c7ee4eaf00fb8a65112"),
            Map.entry(MODEL+"blast_furnace.json", "4dc5630b15495f173118b0fa87b0b75b0d89dd79a9e9e14d5ce75960495fa821"),
            Map.entry(MODEL+"hammerhead.json", "77bf5d1b9d9ac4b1034a2332dbce818e7ae215fc94c09041a6e4eb19d9f38555"),
            Map.entry(MODEL+"the_recluse.json", "7b4aa9c3d2294659c33a2f8ca5c03f1aa52bdea7223d4176f4856c9a4e104dd2"),
            Map.entry("src/main/resources/weapon_surface_w123/manifest.json", "4972bd808e5150d09e8f55e2c663b45f88ad8e660300310c5ecc04f4f672db6b"),
            Map.entry(MODEL+"blast_furnace_body.json", "8887432fef357782eaaf621a8880c2a4bedc73b43a813d6607fd0cbe1b8eb195"),
            Map.entry(MODEL+"blast_furnace_magazine.json", "0bc7d79954d411b95626e454b929ab7f4ecbbf065c9cf0bf43dccfab0898edde"),
            Map.entry(MODEL+"hammerhead_body.json", "e7326f52499020baf6254261851361203336c02035148b07f6f366764d3dd8cf"),
            Map.entry(MODEL+"hammerhead_cover.json", "6b319f4c799a6b197055342dba0f87cf4e66959cffc427b64ac62ab5feff32c0"),
            Map.entry(MODEL+"hammerhead_magazine.json", "992cd16a82cd2c3ebc3afb9425b765d1dfcfce6111e67443e392c6cacb47caec"));
    private PreW251Assets() {}
    public static Path path(String original) throws IOException {
        assertTrue(HASHES.containsKey(original), "Unreviewed historical fixture: "+original);
        var path=Path.of("src/test/resources/fixtures/weapon-assets-pre-w251").resolve(original);
        try {
            assertEquals(HASHES.get(original), HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256")
                    .digest(Files.readAllBytes(path))), original);
        } catch (java.security.NoSuchAlgorithmException e) { throw new AssertionError(e); }
        return path;
    }
}
