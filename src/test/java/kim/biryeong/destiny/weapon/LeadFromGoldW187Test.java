package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import java.nio.file.*;
import java.util.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Actual production profile/math. Offline JUnit; no Minecraft grant is simulated. */
class LeadFromGoldW187Test {
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactSixBaseSocketsAcrossTheReal65EntryCatalog() {
        assertEquals("lead_from_gold", LeadFromGoldProfile.ID);
        assertEquals(1556840489L, LeadFromGoldProfile.HASH);
        assertEquals(65, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList().size());
        var expected = Set.of(
            new WeaponPerks.Roll("apostate",2164448701L,3,1556840489L,1306932196L),
            new WeaponPerks.Roll("mindbender_s_ambition_adept",912150785L,3,1556840489L,1732284294L),
            new WeaponPerks.Roll("hollow_words",607191995L,3,1556840489L,637298592L),
            new WeaponPerks.Roll("dream_breaker",2931957300L,3,1556840489L,3785896921L),
            new WeaponPerks.Roll("deafening_whisper",981718087L,3,1556840489L,3110206796L),
            new WeaponPerks.Roll("nezarec_s_whisper",254636484L,3,1556840489L,210449465L));
        assertEquals(6, LeadFromGoldProfile.rolls().size());
        assertEquals(expected, Set.copyOf(LeadFromGoldProfile.rolls()));
        assertThrows(UnsupportedOperationException.class, () -> LeadFromGoldProfile.rolls().clear());
        for (var e : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) {
            boolean supported = expected.stream().anyMatch(r -> r.id().equals(e.id()));
            assertEquals(supported, LeadFromGoldProfile.supports(e), e.id());
            if (supported) {
                var c = WeaponCharacteristics.of(e);
                assertFalse(c.exotic()); assertEquals(WeaponAmmoType.SPECIAL, c.ammo());
                assertTrue(expected.stream().anyMatch(r -> r.id().equals(e.id()) && r.hash() == c.bungieHash()));
            }
        }
    }
    @Test void canonicalIdentityRejectsForgedFamilyFrameAndMetadata() {
        var a = entry("apostate");
        assertTrue(LeadFromGoldProfile.supports(new WeaponCatalog.Entry(a.id(),a.family(),a.frame(),a.name(),a.source_frame_label(),a.item_model())));
        for (var fake : List.of(
                new WeaponCatalog.Entry(a.id(),"machine_gun",a.frame(),a.name(),a.source_frame_label(),a.item_model()),
                new WeaponCatalog.Entry(a.id(),a.family(),"fake",a.name(),a.source_frame_label(),a.item_model()),
                new WeaponCatalog.Entry(a.id(),a.family(),a.frame(),"fake",a.source_frame_label(),a.item_model()),
                new WeaponCatalog.Entry("fake",a.family(),a.frame(),a.name(),a.source_frame_label(),a.item_model()))) {
            assertFalse(LeadFromGoldProfile.supports(fake)); assertEquals(0, LeadFromGoldProfile.amount(fake,1));
        }
        assertFalse(LeadFromGoldProfile.supports(null)); assertEquals(0,LeadFromGoldProfile.amount(null,1));
    }
    @Test void realProfilesUseReserveCapacityAndBothEquippedSpecialCount() {
        Map<String,List<Integer>> expected = Map.of(
            "apostate",List.of(20,5,3), "mindbender_s_ambition_adept",List.of(25,7,4),
            "hollow_words",List.of(30,8,4), "dream_breaker",List.of(30,8,4),
            "deafening_whisper",List.of(16,4,2), "nezarec_s_whisper",List.of(30,8,4));
        expected.forEach((id, values) -> {
            var e = entry(id);
            assertEquals(values.get(0).intValue(),WeaponProfile.forEntry(e).reserve());
            assertEquals(values.get(1).intValue(),LeadFromGoldProfile.amount(e,1));
            assertEquals(values.get(2).intValue(),LeadFromGoldProfile.amount(e,2));
            for (int count : new int[]{Integer.MIN_VALUE,-1,0,3,Integer.MAX_VALUE})
                assertEquals(0,LeadFromGoldProfile.amount(e,count));
        });
        for (var e : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id())).toList()) if (!LeadFromGoldProfile.supports(e)) {
            assertEquals(0,LeadFromGoldProfile.amount(e,1)); assertEquals(0,LeadFromGoldProfile.amount(e,2));
        }
    }
    @Test void integerPolicyIsOneCeilingAndHandlesBoundariesWithoutOverflow() {
        for (int cap = 1; cap < 1024; cap++) for (int count = 1; count <= 2; count++)
            assertEquals((cap+4*count-1)/(4*count),LeadFromGoldProfile.reserveGrant(cap,count));
        assertEquals(536870912,LeadFromGoldProfile.reserveGrant(Integer.MAX_VALUE,1));
        assertEquals(268435456,LeadFromGoldProfile.reserveGrant(Integer.MAX_VALUE,2));
        for (int cap : new int[]{Integer.MIN_VALUE,-1,0}) assertEquals(0,LeadFromGoldProfile.reserveGrant(cap,1));
        assertEquals(0,LeadFromGoldProfile.reserveGrant(25,0));
        assertEquals(0,LeadFromGoldProfile.reserveGrant(25,3));
    }
    @Test void resourceRejectsEnhancedMissingDuplicateSocketAndPolicyMutations() throws Exception {
        String text = Files.readString(Path.of("src/main/resources/destiny/weapons/w187-lead_from_gold.json"));
        LeadFromGoldProfile.validateResource(text);
        for (String mutation : List.of("enhanced","missing","duplicate","socket","pool","mechanics","rounding","basis","extra")) {
            var root = JsonParser.parseString(text).getAsJsonObject();
            var rolls = root.getAsJsonArray("weapons"); var first = rolls.get(0).getAsJsonObject();
            switch (mutation) {
                case "enhanced" -> first.addProperty("perkHash",3442762221L);
                case "missing" -> rolls.remove(0);
                case "duplicate" -> rolls.add(first.deepCopy());
                case "socket" -> first.addProperty("socket",4);
                case "pool" -> first.addProperty("plugSetHash",1L);
                case "mechanics" -> root.getAsJsonObject("perk").addProperty("reserveFraction",.35);
                case "rounding" -> root.getAsJsonObject("perk").addProperty("originalRoundingVerified",true);
                case "basis" -> root.getAsJsonObject("perk").addProperty("reserveBasis","current_ammo");
                case "extra" -> first.addProperty("extra",true);
            }
            assertThrows(IllegalStateException.class,()->LeadFromGoldProfile.validateResource(root.toString()),mutation);
        }
    }
    @Test void amountAndSupportsQueriesStayPureAndCannotEnterGrantOrRegistryInitialization() throws Exception {
        String source = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/LeadFromGoldProfile.java"));
        for (String forbidden : List.of("WeaponPerks.selected(","WeaponCatalog.find(","WeaponLeadFromGold.grant(",
                "WeaponItems.save(","addReserve(","ServerPlayer","getAttached","SESSIONS"))
            assertFalse(source.contains(forbidden),forbidden);
        var e = entry("apostate");
        for (int i=0;i<100;i++) { assertTrue(LeadFromGoldProfile.supports(e)); assertEquals(3,LeadFromGoldProfile.amount(e,2)); }
    }
}
