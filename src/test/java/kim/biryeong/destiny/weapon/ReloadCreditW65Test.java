package kim.biryeong.destiny.weapon;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import java.io.InputStreamReader;
import java.lang.reflect.Modifier;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.MessageDigest;
import java.util.HashMap;
import java.util.HashSet;
import java.util.HexFormat;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Pure W65 contract tests: resources and local source evidence, without Minecraft bootstrap. */
class ReloadCreditW65Test {
    private record Expected(String id, long hash, String family, String oracleFamily,
                            String category, int percent, int fullTicks, int creditTicks) {}

    // Independent selected-item/category pins from W46, not expectations read from W65 output.
    private static final List<Expected> SELECTED = List.of(
            new Expected("duke_mk_44", 2112909414L, "hand_cannon", "Hand Cannon", "120 RPM", 71, 59, 42),
            new Expected("austringer", 3055790362L, "hand_cannon", "Hand Cannon", "default", 71, 53, 38),
            new Expected("seventh_seraph_officer_revolver", 3037520408L, "hand_cannon", "Hand Cannon", "default", 71, 52, 37),
            new Expected("fixed_odds", 2194955522L, "machine_gun", "Machine Gun", "default", 65, 106, 69),
            new Expected("hammerhead", 603242241L, "machine_gun", "Machine Gun", "default", 65, 91, 60),
            new Expected("retrofit_escapade", 3103325054L, "machine_gun", "Machine Gun", "default", 65, 90, 59));

    private static WeaponCatalog.Entry entry(String id) {
        return WeaponCatalog.find(id).orElseThrow();
    }

    private static WeaponReloadPolicy.Plan whole(int ticks) {
        return new WeaponReloadPolicy.Plan(ticks, ticks, 0);
    }

    // Like W62: explicit finite ammunition and primitive fields avoid WeaponProfile.forEntry's MC policies.
    private static WeaponProfile profile(boolean shell) {
        return new WeaponProfile(WeaponProfile.Mode.HITSCAN, 3, 10, 10, 20, 59, 48,
                0, 1, 1, 0, 0, 0, 0, false, false, 10, 0, false, shell, 59, shell ? 1 : 0);
    }

    private static JsonObject artifact(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }

    private static JsonObject resource() throws Exception {
        var stream = ReloadCreditW65Test.class.getResourceAsStream("/destiny/weapons/w65-reload-credit.json");
        assertNotNull(stream);
        try (var reader = new InputStreamReader(stream, StandardCharsets.UTF_8)) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        }
    }

    private static Map<String, JsonObject> originalRows() throws Exception {
        var rows = new HashMap<String, JsonObject>();
        for (var value : artifact("art/weapons/w46/extraction.json").getAsJsonArray("entries")) {
            var row = value.getAsJsonObject();
            assertNull(rows.put(row.get("id").getAsString(), row), "duplicate W46 ID");
        }
        assertEquals(63, rows.size());
        return rows;
    }

    private static void counts(WeaponMagazine ammo, int loaded, int reserve) {
        assertEquals(loaded, ammo.rounds(), "loaded");
        assertEquals(reserve, ammo.reserve(), "reserve");
        assertEquals(0, ammo.overflow(), "overflow");
        assertEquals((long) loaded + reserve, ammo.total(), "finite total");
    }

    @Test void exactlySixCanonicalFractionsJoinOriginalExtractionAndCategoryFormulas() throws Exception {
        var original = originalRows();
        var formulas = artifact("art/weapons/w46/weapon_formulas.json");
        var output = resource();
        assertEquals("W65", output.get("stage").getAsString());
        assertEquals(6, output.getAsJsonArray("weapons").size());
        Set<String> outputIds = new HashSet<>();
        for (var value : output.getAsJsonArray("weapons")) {
            var row = value.getAsJsonObject();
            String id = row.get("id").getAsString();
            assertTrue(outputIds.add(id), "duplicate W65 ID: " + id);
            var expected = SELECTED.stream().filter(e -> e.id().equals(id)).findFirst().orElseThrow();
            var source = original.get(id);
            assertEquals(expected.hash(), source.get("bungieHash").getAsLong(), id);
            assertEquals(expected.family(), source.get("family").getAsString(), id);
            assertEquals(expected.oracleFamily(), source.get("oracleFamily").getAsString(), id);
            assertEquals(expected.category(), source.get("category").getAsString(), id);
            var curve = formulas.getAsJsonObject(expected.oracleFamily()).getAsJsonObject("cat")
                    .getAsJsonObject(expected.category()).getAsJsonObject("reload");
            assertEquals(curve, source.getAsJsonObject("reloadCurve"), id);
            double fraction = expected.percent() / 100.0;
            assertEquals(fraction, curve.get("ammo_percent").getAsDouble(), 0.0, id);
            assertEquals(expected.hash(), row.get("hash").getAsLong(), id);
            assertEquals(expected.family(), row.get("family").getAsString(), id);
            assertEquals(expected.oracleFamily(), row.get("oracleFamily").getAsString(), id);
            assertEquals(expected.category(), row.get("category").getAsString(), id);
            assertEquals(fraction, row.get("fraction").getAsDouble(), 0.0, id);
            var credit = ReloadCreditProfile.find(entry(id)).orElseThrow();
            assertEquals(new ReloadCreditProfile.Credit(id, expected.hash(), expected.family(), fraction), credit);
            assertEquals(expected.hash(), WeaponCharacteristics.of(entry(id)).bungieHash(), id);
            int stat = source.get("reloadStatUsed").getAsInt();
            double seconds = curve.get("evpp").getAsDouble() * stat * stat
                    + curve.get("vpp").getAsDouble() * stat + curve.get("offset").getAsDouble();
            assertEquals(expected.fullTicks(), (int) Math.ceil(seconds * 20), id);
            assertEquals(expected.fullTicks(), WeaponTiming.of(entry(id)).reloadTicks().orElseThrow(), id);
            assertEquals(expected.creditTicks(), ReloadCreditProfile.ammoTicks(entry(id), whole(expected.fullTicks())), id);
            for (int ticks : new int[]{1, 2, 10, 33, 59, 100, Integer.MAX_VALUE}) {
                // Integer arithmetic independently checks ceil and the captured first phase, not intervalTicks.
                int ceil = (int) (((long) ticks * expected.percent() + 99) / 100);
                assertEquals(ceil, ReloadCreditProfile.ammoTicks(entry(id),
                        new WeaponReloadPolicy.Plan(ticks, 7, 0)), id + "/" + ticks);
            }
        }
        assertEquals(SELECTED.stream().map(Expected::id).collect(Collectors.toSet()), outputIds);
    }

    @Test void remaining57WithoutExplicitFractionsKeepFullFirstPhaseIncludingBothLfrs() throws Exception {
        var original = originalRows();
        Set<String> selected = SELECTED.stream().map(Expected::id).collect(Collectors.toSet());
        Set<String> excluded = new HashSet<>();
        assertEquals(63, WeaponCatalogTest.originalW30Entries().size());
        for (var e : WeaponCatalogTest.originalW30Entries()) {
            if (selected.contains(e.id())) continue;
            excluded.add(e.id());
            var source = original.get(e.id());
            assertNotNull(source, e.id());
            assertFalse(source.has("reloadCurve") && source.getAsJsonObject("reloadCurve").has("ammo_percent"), e.id());
            assertTrue(ReloadCreditProfile.find(e).isEmpty(), e.id());
            for (int ticks : new int[]{1, 33, 59})
                assertEquals(ticks, ReloadCreditProfile.ammoTicks(e, new WeaponReloadPolicy.Plan(ticks, 7, 0)), e.id());
        }
        assertEquals(57, excluded.size());
        assertFalse(artifact("art/weapons/w46/weapon_formulas.json").getAsJsonObject("Linear Fusion Rifle")
                .getAsJsonObject("cat").getAsJsonObject("default").getAsJsonObject("reload").has("ammo_percent"));
        for (String id : new String[]{"line_in_the_sand", "stormchaser"}) {
            assertTrue(excluded.contains(id));
            assertEquals("linear_fusion_rifle", entry(id).family());
            assertEquals(100, ReloadCreditProfile.ammoTicks(entry(id), whole(100)), "LFR must not inherit MG 0.65");
        }
        Set<String> recordedExcluded = new HashSet<>();
        for (var id : artifact("art/weapons/w65/provenance.json").getAsJsonArray("excludedWithoutExplicitFraction"))
            assertTrue(recordedExcluded.add(id.getAsString()));
        assertEquals(excluded, recordedExcluded);
    }

    @Test void canonicalIdentityAndImmutableCreditCannotBeOverriddenAndIncrementalPlansUseFirstPhase() {
        assertTrue(ReloadCreditProfile.Credit.class.isRecord());
        for (var field : ReloadCreditProfile.Credit.class.getDeclaredFields())
            if (!Modifier.isStatic(field.getModifiers())) assertTrue(Modifier.isFinal(field.getModifiers()));
        for (var expected : SELECTED) {
            var e = entry(expected.id());
            var captured = ReloadCreditProfile.find(e).orElseThrow();
            var equalCopy = new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model());
            assertSame(captured, ReloadCreditProfile.find(equalCopy).orElseThrow(), "canonical record equality is allowed");
            var impostors = List.of(
                    new WeaponCatalog.Entry(e.id() + "_reissue", e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()),
                    new WeaponCatalog.Entry(e.id(), "linear_fusion_rifle", e.frame(), e.name(), e.source_frame_label(), e.item_model()),
                    new WeaponCatalog.Entry(e.id(), e.family(), "forged", e.name(), e.source_frame_label(), e.item_model()),
                    new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), "forged", e.source_frame_label(), e.item_model()),
                    new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), "forged", e.item_model()),
                    new WeaponCatalog.Entry(e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), "destiny:weapon/forged"));
            for (var forged : impostors) {
                assertTrue(ReloadCreditProfile.find(forged).isEmpty(), forged.toString());
                assertEquals(59, ReloadCreditProfile.ammoTicks(forged, whole(59)));
            }
            var unrelatedValue = new ReloadCreditProfile.Credit(e.id(), 1, e.family(), 0.01);
            assertNotEquals(captured, unrelatedValue);
            assertSame(captured, ReloadCreditProfile.find(e).orElseThrow());
            for (int batch : new int[]{1, 2, 3})
                assertEquals(20, ReloadCreditProfile.ammoTicks(e, new WeaponReloadPolicy.Plan(20, 13, batch)));
        }
        assertTrue(ReloadCreditProfile.find(null).isEmpty());
        assertEquals(59, ReloadCreditProfile.ammoTicks(null, new WeaponReloadPolicy.Plan(59, 7, 0)));
        assertEquals(20, ReloadCreditProfile.ammoTicks(null, new WeaponReloadPolicy.Plan(20, 13, 2)));
        assertThrows(NullPointerException.class, () -> ReloadCreditProfile.ammoTicks(entry("duke_mk_44"), null));
    }

    @Test void provenancePinsOriginalBytesAndSourceChainSeparatesAmmoFromFullRecovery() throws Exception {
        var provenance = artifact("art/weapons/w65/provenance.json");
        assertEquals("W65", provenance.get("stage").getAsString());
        assertEquals("dcd0c7d302b056ffbb532edcb711d724a17ca8c1", provenance.get("oracleCommit").getAsString());
        assertEquals("scripts/extract_reload_credit_w65.py", provenance.get("generator").getAsString());
        assertEquals(6, provenance.get("selectedWeapons").getAsInt());
        assertFalse(provenance.get("nativeVerified").getAsBoolean());
        assertFalse(provenance.get("modernSandboxExact").getAsBoolean());
        var originalPins = Map.of(
                "art/weapons/w46/extraction.json", "be0a670f4db11adca87383344f13d1e3588f18f58bf22b1454b4652653c87cc8",
                "art/weapons/w46/weapon_formulas.json", "fed3a0e02c72e34b8fb6daac459ca776fa31ef90b7350905b5f6276ff9b3178d",
                "art/weapons/w46/stat_calc.rs", "5662ee9dea9e59547d73f81cd7c02872046266acb7b24017d2d09c123f31e5c2",
                "art/weapons/w46/rs_types.rs", "faa476e6589d2362cf9ee8dd948410adfa7fa8507e8809f3cd10bb13ebba9b90",
                "art/weapons/w46/build.rs", "85b2e35f1db47f55c58900020ebf44be0e409802beac395b4b4c538fad67a1bd",
                "art/weapons/w30/catalog.json", "3e9377cce928958a89208ce69f34210fe7e17ae17afd1f4959bb418b1ed120f5");
        assertEquals(originalPins.keySet(), provenance.getAsJsonObject("inputSha256").keySet());
        for (var pin : originalPins.entrySet()) {
            String digest = HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(pin.getKey()))));
            assertEquals(pin.getValue(), digest, pin.getKey());
            assertEquals(pin.getValue(), provenance.getAsJsonObject("inputSha256").get(pin.getKey()).getAsString());
        }
        String output = "src/main/resources/destiny/weapons/w65-reload-credit.json";
        assertEquals(Set.of(output), provenance.getAsJsonObject("outputSha256").keySet());
        assertEquals(provenance.getAsJsonObject("outputSha256").get(output).getAsString(),
                HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(output)))));
        var build = Files.readString(Path.of("art/weapons/w46/build.rs"));
        var calc = Files.readString(Path.of("art/weapons/w46/stat_calc.rs"));
        assertTrue(build.contains("let mut reload: ReloadFormula = cat.reload;"));
        assertTrue(build.contains("#[serde(default)]\n    pub ammo_percent: f64"));
        assertTrue(calc.contains("let reload_time = self.reload_data.solve_at(_reload_stat as f64);"));
        assertTrue(calc.contains("ammo_time: reload_time * self.ammo_percent"));
        assertTrue(calc.contains("self.reload_formula.calc_reload_time_formula(reload_stat)"));
        assertTrue(calc.contains("out.reload_time *= modifiers.reload_time_scale"));
        assertFalse(calc.contains("out.ammo_time *="), "W65 scaling is an authored captured-phase policy");
        var runtime = Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java"));
        assertTrue(runtime.contains("WeaponOutlaw.plan(player,entry,p)"));
        assertTrue(runtime.contains("s.cycle.startReload(now(player), p, ammo, plan, ReloadCreditProfile.ammoTicks(entry,plan))"));
        assertTrue(runtime.contains("s.cycle.finishReload(now(player), ammo)"));
        assertTrue(runtime.contains("s.cycle.reloadRemaining(now(player))"));
    }

    @Test void modeled59AndBoosted33CreditAt42And24PayOnceWhileReadQueriesAndFireStayGated() {
        var p = profile(false);
        for (int[] timing : new int[][]{{59, 42}, {33, 24}}) {
            int full = timing[0], credit = timing[1];
            var plan = whole(full); // 33 models an already captured boost; this is not an Outlaw integration test.
            assertEquals(credit, ReloadCreditProfile.ammoTicks(entry("duke_mk_44"), plan));
            for (int reserve : new int[]{5, 20}) {
                var ammo = new WeaponMagazine(p, 1, reserve);
                var cycle = new WeaponCycle();
                assertTrue(cycle.startReload(100, p, ammo, plan, credit));
                assertFalse(cycle.finishReload(100 + credit - 1, ammo));
                counts(ammo, 1, reserve);
                for (long tick : new long[]{100 + credit, 100 + full - 1, 100 + full, 1000}) {
                    assertFalse(cycle.ready(tick));
                    assertTrue(cycle.reloading());
                    assertEquals(full, cycle.reloadPhaseTicks());
                    assertEquals(Math.max(0L, 100 + full - tick), cycle.reloadRemaining(tick));
                    assertFalse(cycle.charging());
                    assertFalse(cycle.bursting());
                    assertFalse(cycle.fire(tick, p, ammo));
                    counts(ammo, 1, reserve);
                }
                assertTrue(cycle.finishReload(100 + credit, ammo));
                int loaded = Math.min(10, 1 + reserve), remaining = reserve - (loaded - 1);
                counts(ammo, loaded, remaining);
                assertTrue(cycle.reloading());
                assertEquals(full, cycle.reloadPhaseTicks());
                assertEquals(full - credit, cycle.reloadRemaining(100 + credit));
                assertFalse(cycle.interruptReloadForShot(100 + credit, ammo));
                assertTrue(ammo.consume());
                for (int elapsed = credit; elapsed < full; elapsed++) {
                    assertFalse(cycle.finishReload(100 + elapsed, ammo), "credit already paid");
                    assertFalse(cycle.ready(100 + elapsed));
                    assertFalse(cycle.fire(100 + elapsed, p, ammo));
                    counts(ammo, loaded - 1, remaining);
                }
                assertFalse(cycle.finishReload(100 + full, ammo), "recovery is not another transfer");
                assertFalse(cycle.reloading());
                assertEquals(0, cycle.reloadPhaseTicks());
                assertTrue(cycle.ready(100 + full));
                assertTrue(cycle.fire(100 + full, p, ammo));
                counts(ammo, loaded - 2, remaining);
                assertFalse(cycle.finishReload(1000, ammo));
                counts(ammo, loaded - 2, remaining);
            }
        }
    }

    @Test void aLateFirstTickTransfersOnceAndCompletesWithoutCatchUpOrDeferredRefill() {
        var p = profile(false);
        var ammo = new WeaponMagazine(p, 1, 20);
        var cycle = new WeaponCycle();
        assertTrue(cycle.startReload(100, p, ammo, whole(59), 42));
        assertTrue(cycle.finishReload(1000, ammo));
        counts(ammo, 10, 11);
        assertFalse(cycle.reloading());
        assertTrue(cycle.ready(1000));
        assertEquals(0, cycle.reloadRemaining(1000));
        assertTrue(ammo.consume());
        for (long tick : new long[]{1000, 1000, 1001, 10000}) {
            assertFalse(cycle.finishReload(tick, ammo));
            counts(ammo, 9, 11);
        }
    }

    @Test void cancelBeforeCreditTransfersNothingAndCancelAfterCreditKeepsOnlyPaidAmmo() {
        var p = profile(false);
        for (boolean credited : new boolean[]{false, true}) {
            var ammo = new WeaponMagazine(p, 1, 20);
            var cycle = new WeaponCycle();
            assertTrue(cycle.startReload(100, p, ammo, whole(59), 42));
            assertFalse(cycle.finishReload(141, ammo));
            if (credited) assertTrue(cycle.finishReload(142, ammo));
            cycle.cancelPending();
            assertFalse(cycle.reloading());
            assertEquals(0, cycle.reloadPhaseTicks());
            assertEquals(0, cycle.reloadRemaining(142));
            counts(ammo, credited ? 10 : 1, credited ? 11 : 20);
            assertTrue(ammo.consume());
            assertFalse(cycle.finishReload(142, ammo));
            assertFalse(cycle.finishReload(1000, ammo));
            counts(ammo, credited ? 9 : 0, credited ? 11 : 20);
            assertTrue(cycle.startReload(1000, p, ammo, whole(59), 42));
            assertFalse(cycle.finishReload(1041, ammo), "restart has a fresh credit deadline");
            assertTrue(cycle.finishReload(1042, ammo));
            counts(ammo, 10, 10);
        }
    }

    @Test void noOpCreditConsumesEligibilityAndExternalFillConsumeOrLatePickupCannotRearmIt() {
        var p = profile(false);
        for (int scenario = 0; scenario < 3; scenario++) {
            var ammo = new WeaponMagazine(p, 1, scenario == 0 ? 5 : 20);
            var cycle = new WeaponCycle();
            assertTrue(cycle.startReload(0, p, ammo, whole(59), 42));
            assertEquals(scenario == 0 ? 5 : 9, ammo.reload(), "external transfer before credit");
            if (scenario == 0) {
                assertTrue(ammo.consume(6)); // Both pools empty at credit.
                assertFalse(cycle.finishReload(42, ammo));
                assertEquals(7, ammo.addReserve(7)); // Pickup after a no-op must wait for a new reload.
                counts(ammo, 0, 7);
            } else if (scenario == 1) {
                assertFalse(cycle.finishReload(42, ammo)); // Full magazine consumes eligibility too.
                assertTrue(ammo.consume());
                counts(ammo, 9, 11);
            } else {
                assertTrue(ammo.consume(2)); // Space exists again before the one eligible credit.
                assertTrue(cycle.finishReload(42, ammo));
                counts(ammo, 10, 9);
                assertTrue(ammo.consume());
            }
            int loaded = ammo.rounds(), reserve = ammo.reserve();
            assertTrue(cycle.reloading());
            for (long tick : new long[]{42, 43, 58, 59, 1000}) {
                assertFalse(cycle.finishReload(tick, ammo));
                counts(ammo, loaded, reserve);
            }
            assertFalse(cycle.reloading());
        }
    }

    @Test void refusedNewPlanCannotRetimeEitherActiveCreditOrRecoveryDeadline() {
        var p = profile(false);
        for (int[] timing : new int[][]{{59, 42, 33, 24}, {33, 24, 59, 42}}) {
            var ammo = new WeaponMagazine(p, 1, 20);
            var cycle = new WeaponCycle();
            assertTrue(cycle.startReload(100, p, ammo, whole(timing[0]), timing[1]));
            assertFalse(cycle.startReload(110, p, ammo, whole(timing[2]), timing[3]));
            assertEquals(timing[0], cycle.reloadPhaseTicks());
            assertEquals(timing[0] - 10, cycle.reloadRemaining(110));
            assertFalse(cycle.finishReload(100 + timing[1] - 1, ammo));
            counts(ammo, 1, 20);
            assertTrue(cycle.finishReload(100 + timing[1], ammo));
            counts(ammo, 10, 11);
            assertTrue(ammo.consume());
            assertFalse(cycle.startReload(100 + timing[1], p, ammo, whole(1), 1));
            assertFalse(cycle.finishReload(100 + timing[0] - 1, ammo));
            assertFalse(cycle.ready(100 + timing[0] - 1));
            assertFalse(cycle.finishReload(100 + timing[0], ammo));
            assertTrue(cycle.ready(100 + timing[0]));
            counts(ammo, 9, 11);
        }
    }

    @Test void invalidCreditAndShellSplitsAreDeniedWhileBothLegacyOverloadsKeepAtomicBehavior() {
        var p = profile(false);
        var cycle = new WeaponCycle();
        var ammo = new WeaponMagazine(p, 1, 20);
        for (int invalid : new int[]{Integer.MIN_VALUE, -1, 0, 60, Integer.MAX_VALUE}) {
            assertThrows(IllegalArgumentException.class, () -> cycle.startReload(0, p, ammo, whole(59), invalid));
            assertFalse(cycle.reloading());
            counts(ammo, 1, 20);
        }
        var shell = profile(true);
        var shellAmmo = new WeaponMagazine(shell, 0, 3);
        var shellCycle = new WeaponCycle();
        assertThrows(IllegalArgumentException.class, () -> shellCycle.startReload(0, shell, shellAmmo,
                new WeaponReloadPolicy.Plan(9, 6, 1), 8));
        assertThrows(IllegalArgumentException.class, () -> shellCycle.startReload(0, shell, shellAmmo,
                new WeaponReloadPolicy.Plan(9, 6, 2), 9));
        assertThrows(IllegalArgumentException.class, () -> shellCycle.startReload(0, shell, shellAmmo, whole(9), 9));
        assertThrows(IllegalArgumentException.class, () -> cycle.startReload(0, p, ammo,
                new WeaponReloadPolicy.Plan(9, 6, 1), 9));
        assertFalse(shellCycle.reloading());
        counts(shellAmmo, 0, 3);
        for (boolean explicitPlan : new boolean[]{false, true}) {
            var legacy = new WeaponCycle();
            var finite = new WeaponMagazine(p, 1, 5);
            int first = explicitPlan ? 12 : 59;
            assertTrue(explicitPlan ? legacy.startReload(100, p, finite, whole(first)) : legacy.startReload(100, p, finite));
            assertFalse(legacy.finishReload(100 + first - 1, finite));
            counts(finite, 1, 5);
            assertTrue(legacy.finishReload(100 + first, finite));
            counts(finite, 6, 0);
            assertFalse(legacy.reloading());
            assertFalse(legacy.finishReload(1000, finite));
            var inserts = new WeaponCycle();
            var shells = new WeaponMagazine(shell, 0, 3);
            int initial = explicitPlan ? 9 : 59, interval = explicitPlan ? 6 : 59;
            assertTrue(explicitPlan ? inserts.startReload(100, shell, shells,
                    new WeaponReloadPolicy.Plan(initial, interval, 1)) : inserts.startReload(100, shell, shells));
            assertFalse(inserts.finishReload(100 + initial - 1, shells));
            assertTrue(inserts.finishReload(100 + initial, shells));
            counts(shells, 1, 2);
            assertEquals(interval, inserts.reloadPhaseTicks());
            assertFalse(inserts.finishReload(100 + initial + interval - 1, shells));
            assertTrue(inserts.finishReload(1000, shells), "late shell tick transfers only one insert");
            counts(shells, 2, 1);
            assertFalse(inserts.finishReload(1000, shells));
            assertTrue(inserts.finishReload(1000 + interval, shells));
            counts(shells, 3, 0);
            assertFalse(inserts.reloading());
        }
    }
}
