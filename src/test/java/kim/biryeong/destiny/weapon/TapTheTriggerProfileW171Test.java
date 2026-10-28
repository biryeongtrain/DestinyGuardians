package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class TapTheTriggerProfileW171Test {
    private static final String ART = "art/weapons/w171/tap-the-trigger/";
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w171-tap-the-trigger.json";
    private static final Set<String> SUPPORTED = Set.of("ammit_ar2", "gnawing_hunger", "dead_man_walking_xx7463",
        "dream_breaker", "hammerhead", "retrofit_escapade");
    private static JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    @Test void exactBaseSocketsAndImmutableRolls() {
        assertEquals("tap_the_trigger", TapTheTriggerProfile.ID);
        assertEquals(1890422124L, TapTheTriggerProfile.HASH);
        assertEquals(Set.of(
            new WeaponPerks.Roll("ammit_ar2", 2119346509L, 4, 1890422124L, 560115158L),
            new WeaponPerks.Roll("gnawing_hunger", 821154603L, 3, 1890422124L, 1144396384L),
            new WeaponPerks.Roll("dead_man_walking_xx7463", 3751622019L, 4, 1890422124L, 1210839935L),
            new WeaponPerks.Roll("dream_breaker", 2931957300L, 4, 1890422124L, 1206254527L),
            new WeaponPerks.Roll("hammerhead", 603242241L, 3, 1890422124L, 2515290473L),
            new WeaponPerks.Roll("retrofit_escapade", 3103325054L, 4, 1890422124L, 2461260598L)),
            new HashSet<>(TapTheTriggerProfile.rolls()));
        assertThrows(UnsupportedOperationException.class, () -> TapTheTriggerProfile.rolls().clear());
    }
    @Test void membershipCoversEverySelectedWeaponAndRejectsForgedEntries() {
        assertEquals(65, WeaponCatalog.all().size());
        for (var w : WeaponCatalog.all()) {
            assertEquals(SUPPORTED.contains(w.id()), TapTheTriggerProfile.supports(w), w.id());
            if (!SUPPORTED.contains(w.id())) {
                assertThrows(IllegalArgumentException.class, () -> TapTheTriggerProfile.stabilityBonus(w));
                assertThrows(IllegalArgumentException.class, () -> TapTheTriggerProfile.recoilScalar(w));
                assertThrows(IllegalArgumentException.class, () -> TapTheTriggerProfile.accuracyScalar(w));
            }
        }
        assertFalse(TapTheTriggerProfile.supports(null));
        assertThrows(IllegalArgumentException.class, () -> TapTheTriggerProfile.stabilityBonus(null));
        var a = entry("ammit_ar2");
        for (var forged : List.of(
            new WeaponCatalog.Entry(a.id(), "fusion_rifle", a.frame(), a.name(), a.source_frame_label(), a.item_model()),
            new WeaponCatalog.Entry(a.id(), a.family(), a.frame(), "forged", a.source_frame_label(), a.item_model()))) {
            assertFalse(TapTheTriggerProfile.supports(forged));
            assertThrows(IllegalArgumentException.class, () -> TapTheTriggerProfile.recoilScalar(forged));
        }
    }
    @Test void twelveTicksAndExactOrdinaryAndQuarterFusionBenefits() {
        assertEquals(12, TapTheTriggerProfile.durationTicks());
        assertEquals(.6 * 20, TapTheTriggerProfile.durationTicks());
        for (String id : SUPPORTED) {
            var w = entry(id);
            boolean fusion = id.equals("dream_breaker");
            assertEquals(fusion, w.family().equals("fusion_rifle"));
            assertEquals(fusion ? 10 : 40, TapTheTriggerProfile.stabilityBonus(w), id);
            assertEquals(fusion ? .875f : .5f, TapTheTriggerProfile.recoilScalar(w), id);
            assertEquals(fusion ? .975f : .9f, TapTheTriggerProfile.accuracyScalar(w), id);
        }
        assertEquals(40 * .25, TapTheTriggerProfile.stabilityBonus(entry("dream_breaker")));
        assertEquals(1 - .5 * .25, TapTheTriggerProfile.recoilScalar(entry("dream_breaker")));
        assertEquals(1 - .1 * .25, TapTheTriggerProfile.accuracyScalar(entry("dream_breaker")), 1e-7);
    }
    @Test void sourceEvidenceEstablishesTraitRandomizedRealRollableBaseOnly() throws Exception {
        var source = json(ART + "official-sockets.json");
        assertEquals(65, source.getAsJsonArray("selectedScan").size());
        assertEquals(6, source.getAsJsonArray("weapons").size());
        for (var e : source.getAsJsonArray("weapons")) {
            var r = e.getAsJsonObject();
            assertEquals(1890422124L, r.get("perkHash").getAsLong());
            assertEquals(4241085061L, r.get("socketCategoryHash").getAsLong());
            assertEquals("randomizedPlugSetHash", r.get("plugSetField").getAsString());
            assertFalse(r.get("isFakePlugSet").getAsBoolean());
            assertEquals(r.get("plugSetHash"), r.getAsJsonObject("socketEntry").get("randomizedPlugSetHash"));
            var match = r.getAsJsonArray("matchingEntries").get(0).getAsJsonObject().getAsJsonObject("item");
            assertTrue(match.get("currentlyCanRoll").getAsBoolean());
            assertEquals(1890422124L, match.get("plugItemHash").getAsLong());
            assertEquals(0, match.get("weight").getAsDouble());
        }
        assertEquals(2, source.getAsJsonArray("perkDefinitions").size());
        for (var e : source.getAsJsonArray("perkDefinitions")) {
            var d = e.getAsJsonObject();
            assertEquals(d.get("hash").getAsLong() == 1890422124L, d.get("accepted").getAsBoolean());
        }
    }
    @Test void clarityKeepsRefreshRuleAndControllerSentenceOutsideKeyboardImplementation() throws Exception {
        var source = json(ART + "clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296", source.get("commit").getAsString());
        assertEquals(1523649716L, source.get("enhancedExcludedHash").getAsLong());
        String text = source.getAsJsonObject("base").toString();
        for (String fragment : List.of("0.6 seconds", "40 Stability", "50% decreased Recoil", "10% decreased Accuracy Cone Size",
            "25% of the benefits", "10 Stability, -12.5% Recoil, and -2.5% Accuracy Cone Size",
            "Buff cannot be refreshed until Automatic Weapons stop firing, or until the next burst.",
            "[Controller-Only]", "Weapon fires the instant trigger pressure is applied."))
            assertTrue(text.contains(fragment), fragment);
        var policies = json(RESOURCE).getAsJsonObject("policies");
        assertEquals("AFTER_AUTOMATIC_STOPS_FIRING_OR_NEXT_BURST", policies.get("refresh").getAsString());
        assertEquals("CONTROLLER_ONLY_OUTSIDE_JAVA_KEYBOARD_IMPLEMENTATION", policies.get("controllerPressure").getAsString());
    }
    private static void rejects(Consumer<JsonObject> mutation) throws Exception {
        var root = json(RESOURCE);
        mutation.accept(root);
        assertThrows(IllegalStateException.class, () -> TapTheTriggerProfile.validateResource(root.toString()));
    }
    @Test void enhancedWrongSocketAndChangedMechanicsFailClosed() throws Exception {
        rejects(r -> r.getAsJsonArray("weapons").remove(0));
        rejects(r -> r.getAsJsonArray("weapons").set(1, r.getAsJsonArray("weapons").get(0).deepCopy()));
        for (var field : List.of("hash", "socket", "plugSetHash"))
            rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field, 1));
        rejects(r -> r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty("perkHash", 1523649716L));
        rejects(r -> r.getAsJsonObject("perk").addProperty("hash", 1523649716L));
        rejects(r -> r.getAsJsonObject("perk").addProperty("durationSeconds", .76));
        rejects(r -> r.getAsJsonObject("perk").addProperty("durationTicks", 16));
        for (var kind : List.of("ordinary", "fusion"))
            for (var field : List.of("stabilityBonus", "recoilScalar", "accuracyScalar"))
                rejects(r -> r.getAsJsonObject("perk").getAsJsonObject(kind).addProperty(field, 1));
        rejects(r -> r.getAsJsonObject("policies").addProperty("refresh", "EVERY_SHOT"));
    }
    @Test void pinnedInputsGeneratorAndGeneratedBytesMatch() throws Exception {
        var manifest = json(ART + "manifest.json");
        for (var e : manifest.getAsJsonObject("sourcePins").entrySet()) {
            var pin = e.getValue().getAsJsonObject();
            var verified = PinnedProfileSourcesW234.verify(pin);
            assertEquals(pin.get("sha256").getAsString(), verified.sha256(), e.getKey());
            assertEquals(pin.get("bytes").getAsLong(), verified.bytes(), e.getKey());
        }
        assertEquals(manifest.get("generatorSha256").getAsString(), sha(Path.of(manifest.get("generator").getAsString())));
        for (var e : manifest.getAsJsonObject("outputSha256").entrySet())
            assertEquals(e.getValue().getAsString(), sha(Path.of(e.getKey())), e.getKey());
    }
    @Test void profileInitializationDoesNotLoadOuterCatalogOrPerkRegistries() throws Exception {
        String prefix = "kim.biryeong.destiny.weapon.";
        var forbidden = Set.of(prefix + "WeaponCatalog", prefix + "WeaponCharacteristics", prefix + "WeaponExotics", prefix + "WeaponPerks");
        var isolated = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (forbidden.contains(name)) throw new AssertionError("Recursive registry load: " + name);
                if (!name.startsWith(prefix + "TapTheTriggerProfile")) return super.loadClass(name, resolve);
                synchronized (getClassLoadingLock(name)) {
                    var type = findLoadedClass(name);
                    if (type == null) {
                        try (var in = getParent().getResourceAsStream(name.replace('.', '/') + ".class")) {
                            assertNotNull(in);
                            byte[] bytes = in.readAllBytes();
                            type = defineClass(name, bytes, 0, bytes.length);
                        } catch (java.io.IOException e) { throw new ClassNotFoundException(name, e); }
                    }
                    if (resolve) resolveClass(type);
                    return type;
                }
            }
        };
        var type = Class.forName(prefix + "TapTheTriggerProfile", true, isolated);
        assertEquals(12, type.getMethod("durationTicks").invoke(null));
        assertEquals(6, ((List<?>) type.getMethod("rolls").invoke(null)).size());
        var validate = type.getDeclaredMethod("validateResource", String.class);
        validate.setAccessible(true);
        validate.invoke(null, Files.readString(Path.of(RESOURCE)));
    }
}
