package kim.biryeong.destiny.weapon;

import static org.junit.jupiter.api.Assertions.*;
import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;
import java.util.function.Consumer;

class StatsForAllProfileW176Test {
    private static final String RESOURCE = "src/main/resources/destiny/weapons/w176-stats-for-all.json";
    private static final String ART = "art/weapons/w176/stats-for-all/";
    private static final List<String> IDS = List.of("ammit_ar2", "aishas_embrace", "dimensional_hypotrochoid", "retrofit_escapade");
    private static JsonElement json(String path) throws Exception { return JsonParser.parseString(Files.readString(Path.of(path))); }
    private static JsonObject object(String path) throws Exception { return json(path).getAsJsonObject(); }
    private static JsonObject row(String file, String id) throws Exception {
        for (var e : json("src/main/resources/destiny/weapons/"+file).getAsJsonArray())
            if (e.getAsJsonObject().get("id").getAsString().equals(id)) return e.getAsJsonObject();
        throw new AssertionError("Missing " + id);
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static JsonObject oracle(String id) throws Exception {
        for (var e : object("art/weapons/w43/extraction.json").getAsJsonArray("entries")) {
            var m = e.getAsJsonObject();
            if (m.get("id").getAsString().equals(id)) return object("art/weapons/w46/weapon_formulas.json")
                .getAsJsonObject(m.get("family").getAsString()).getAsJsonObject("cat").getAsJsonObject(m.get("category").getAsString());
        }
        throw new AssertionError("No Oracle mapping");
    }
    private static double solve(JsonObject q, int stat) {
        double a = q.has("evpp") ? q.get("evpp").getAsDouble() : 0;
        double b = q.has("vpp") ? q.get("vpp").getAsDouble() : 0;
        return a * stat * stat + b * stat + q.get("offset").getAsDouble();
    }
    private static int stat(String id, String hash) throws Exception {
        return row("w40-characteristics.json", id).getAsJsonObject("stats").get(hash).getAsInt();
    }
    private static int cap(int base, int bonus) { return (int)Math.min(100L, Math.max(0L, (long)base+bonus)); }
    private static int ticks(double seconds) { return Math.max(1, (int)Math.ceil(seconds*20)); }
    private static String sha(Path path) throws Exception {
        return HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(path)));
    }
    private static void rejects(Consumer<JsonObject> edit) throws Exception {
        var bad = object(RESOURCE); edit.accept(bad);
        assertThrows(IllegalStateException.class, () -> StatsForAllProfile.validateResource(bad.toString()));
    }
    @Test void exactFourBaseSocketIdentitiesAndImmutableRolls() {
        assertEquals("stats_for_all", StatsForAllProfile.ID); assertEquals(1583705720L, StatsForAllProfile.HASH);
        assertEquals(Set.of(new WeaponPerks.Roll("ammit_ar2",2119346509L,3,1583705720L,1723759242L),
            new WeaponPerks.Roll("aishas_embrace",2638190703L,3,1583705720L,7997267L),
            new WeaponPerks.Roll("dimensional_hypotrochoid",1311684613L,3,1583705720L,3235863202L),
            new WeaponPerks.Roll("retrofit_escapade",3103325054L,3,1583705720L,3756086698L)), Set.copyOf(StatsForAllProfile.rolls()));
        assertThrows(UnsupportedOperationException.class, () -> StatsForAllProfile.rolls().clear());
        assertEquals(35, StatsForAllProfile.handlingBonus()); assertEquals(35, StatsForAllProfile.reloadBonus());
        assertEquals(10, StatsForAllProfile.stabilityBonus()); assertEquals(10, StatsForAllProfile.rangeBonus());
        assertEquals(.95, StatsForAllProfile.reloadScalar()); assertEquals(1.05, StatsForAllProfile.falloffScalar());
    }
    @Test void canonicalAll65CoverageAndEachForgedCatalogFieldRejected() {
        assertEquals(65, WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList().size());
        for (var e : WeaponCatalog.all().stream().filter(legacy -> !LegendaryWeapons.contains(legacy.id()) && !WeaponExotics.expanded(legacy)).toList()) assertEquals(IDS.contains(e.id()), StatsForAllProfile.supports(e), e.id());
        assertFalse(StatsForAllProfile.supports(null));
        assertFalse(StatsForAllProfile.supports(new WeaponCatalog.Entry(null,null,null,null,null,null)));
        var e = entry("ammit_ar2");
        String[] fields = {e.id(), e.family(), e.frame(), e.name(), e.source_frame_label(), e.item_model()};
        for (int i = 0; i < fields.length; i++) for (String replacement : new String[]{null,"forged"}) {
            String[] f = fields.clone(); f[i] = replacement;
            var fake = new WeaponCatalog.Entry(f[0],f[1],f[2],f[3],f[4],f[5]);
            assertFalse(StatsForAllProfile.supports(fake));
            assertThrows(IllegalArgumentException.class, () -> StatsForAllProfile.handlingTicks(fake,35,true));
            assertThrows(IllegalArgumentException.class, () -> StatsForAllProfile.adsTicks(fake,35,false));
            assertThrows(IllegalArgumentException.class, () -> StatsForAllProfile.reloadTicks(fake,35,.95));
            assertThrows(IllegalArgumentException.class, () -> StatsForAllProfile.ballistics(fake));
        }
    }
    @Test void independentlyReproduceAllFourExistingBaseTimingsAndWholeMagazineTopology() throws Exception {
        for (String id : IDS) {
            var e = entry(id); var t = row("w46-timing.json",id).getAsJsonObject("timing");
            var h = row("w58-handling.json",id).getAsJsonObject("profile");
            assertTrue(t.get("supported").getAsBoolean()); assertFalse(t.get("shellReload").getAsBoolean());
            assertTrue(t.get("reloadInitialTicks").isJsonNull()); assertTrue(t.get("reloadPerRoundTicks").isJsonNull());
            assertEquals(t.get("reloadTicks").getAsInt(), StatsForAllProfile.reloadTicks(e,0,1));
            assertEquals(h.get("readyTicks").getAsInt(), StatsForAllProfile.handlingTicks(e,0,true));
            assertEquals(h.get("stowTicks").getAsInt(), StatsForAllProfile.handlingTicks(e,0,false));
            assertEquals(row("w44-aim.json",id).getAsJsonObject("profile").get("transitionTicks").getAsInt(), StatsForAllProfile.adsTicks(e,0,false));
        }
    }
    @Test void everyEffectiveStatAgainstRawOracleAndActualRuntimeBonusInputs() throws Exception {
        for (String id : IDS) {
            var e = entry(id); var source = oracle(id); var h = source.getAsJsonObject("handling");
            int baseH = stat(id,"943549884"), baseR = stat(id,"4188031367");
            var bonuses = new ArrayList<>(List.of(Integer.MIN_VALUE,-1000,-1,0,35,55,135,1000,Integer.MAX_VALUE));
            for (int value = 0; value <= 100; value++) { bonuses.add(value-baseH); bonuses.add(value-baseR); }
            for (int bonus : bonuses) {
                int hs = cap(baseH,bonus), rs = cap(baseR,bonus);
                assertEquals(hs, StatsForAllProfile.effectiveStat(baseH,bonus));
                assertEquals(ticks(solve(h.getAsJsonObject("ready"),hs)), StatsForAllProfile.handlingTicks(e,bonus,true),id+bonus);
                assertEquals(ticks(Math.max(solve(h.getAsJsonObject("stow"),hs),solve(h.getAsJsonObject("stow"),100))), StatsForAllProfile.handlingTicks(e,bonus,false),id+bonus);
                assertEquals(Math.clamp(ticks(solve(h.getAsJsonObject("ads"),hs)),2,20), StatsForAllProfile.adsTicks(e,bonus,false),id+bonus);
                for (double scalar : new double[]{1,.95,.8,.95*.8,.95*.6,.0001,Double.MIN_VALUE})
                    assertEquals(ticks(solve(source.getAsJsonObject("reload"),rs)*scalar), StatsForAllProfile.reloadTicks(e,bonus,scalar),id+bonus+" scalar"+scalar);
            }
        }
    }
    @Test void actualRuntimeCallsUseTotalsOnceAndFrenzyCapsAt100BeforeCeil() throws Exception {
        // Expected integer results independently frozen from the pinned Oracle curves.
        int[][] expected = {{29,6,6,5},{32,8,7,7},{51,7,7,8},{76,6,6,7}};
        for (int i = 0; i < IDS.size(); i++) {
            var e = entry(IDS.get(i));
            assertEquals(expected[i][0],StatsForAllProfile.reloadTicks(e,35,.95),e.id()+"reload");
            assertEquals(expected[i][1],StatsForAllProfile.handlingTicks(e,35,true),e.id()+"ready");
            assertEquals(expected[i][2],StatsForAllProfile.handlingTicks(e,35,false),e.id()+"stow");
            assertEquals(expected[i][3],StatsForAllProfile.adsTicks(e,35,false),e.id()+"ADS");
        }
        var retrofit = entry("retrofit_escapade");
        assertEquals(76, StatsForAllProfile.reloadTicks(retrofit,135,.95));
        assertEquals(StatsForAllProfile.reloadTicks(retrofit,100,.95),StatsForAllProfile.reloadTicks(retrofit,135,.95));
        assertEquals(StatsForAllProfile.handlingTicks(retrofit,100,true),StatsForAllProfile.handlingTicks(retrofit,135,true));
        assertEquals(StatsForAllProfile.adsTicks(retrofit,100,false),StatsForAllProfile.adsTicks(retrofit,135,false));
        var ammit = entry("ammit_ar2");
        // AJ contributes +20handling for EVERY active stack1..5, while SFA contributes35.
        for (int ajStack = 1; ajStack <= 5; ajStack++) {
            assertEquals(5, StatsForAllProfile.handlingTicks(ammit,55,true));
            assertEquals(5, StatsForAllProfile.handlingTicks(ammit,55,false));
            assertEquals(5, StatsForAllProfile.adsTicks(ammit,55,false));
        }
    }
    @Test void singleCeilDiffersFromScalingAlreadyRoundedTicksOnRealCurves() throws Exception {
        int witnesses = 0;
        for (String id : IDS) {
            var e = entry(id); var q = oracle(id).getAsJsonObject("reload");
            int rs = cap(stat(id,"4188031367"),35);
            int correct = ticks(solve(q,rs)*.95), wrong = ticks(Math.ceil(solve(q,rs)*20)/20*.95);
            assertEquals(correct,StatsForAllProfile.reloadTicks(e,35,.95));
            if (correct != wrong) witnesses++;
        }
        assertTrue(witnesses > 0,"Must catch double quantization on an actual selected curve");
    }
    @Test void invalidScalarRejectedAndBoundsSafe() {
        for (double bad : new double[]{0,-0.0,-1,1.00001,Double.NaN,Double.POSITIVE_INFINITY,Double.NEGATIVE_INFINITY})
            assertThrows(IllegalArgumentException.class,()->StatsForAllProfile.reloadTicks(entry("ammit_ar2"),35,bad));
        assertEquals(100,StatsForAllProfile.effectiveStat(Integer.MAX_VALUE,Integer.MAX_VALUE));
        assertEquals(0,StatsForAllProfile.effectiveStat(Integer.MIN_VALUE,Integer.MIN_VALUE));
        assertEquals(1,StatsForAllProfile.reloadTicks(entry("ammit_ar2"),35,Double.MIN_VALUE));
    }
    @Test void hipRangePlus10ThenDistanceScalarBothEndpointsPreservesFloorAndPrecision() throws Exception {
        for (String id : IDS) {
            var base = WeaponBallistics.of(entry(id)); var actual = StatsForAllProfile.ballistics(entry(id));
            var b = row("w43-ballistics.json",id); var stats = row("w40-characteristics.json",id).getAsJsonObject("stats");
            boolean sentinel = !stats.has("1240592695");
            int value = sentinel ? 0 : cap(stats.get("1240592695").getAsInt(),10);
            double scale = sentinel ? 1 : 1.05;
            assertEquals((b.get("offsetStart").getAsDouble()+b.get("vppStart").getAsDouble()*value)*scale,actual.start(),1e-12);
            assertEquals((b.get("offsetEnd").getAsDouble()+b.get("vppEnd").getAsDouble()*value)*scale,actual.end(),1e-12);
            assertEquals(base.floor(),actual.floor()); assertEquals(base.precision(),actual.precision());
            assertEquals(1,actual.falloff(actual.start())); assertEquals(actual.floor(),actual.falloff(actual.end()));
            // W44 ADS is applied by the consumer AFTER this hip profile, not baked into SFA.
            double ads = row("w44-aim.json",id).getAsJsonObject("profile").get("falloffScalar").getAsDouble();
            if (!sentinel) assertTrue(actual.start()*ads > actual.start());
        }
        assertEquals(StatsForAllProfile.ballistics(entry("dimensional_hypotrochoid")),WeaponBallistics.of(entry("dimensional_hypotrochoid")));
        assertEquals(999,StatsForAllProfile.ballistics(entry("dimensional_hypotrochoid")).start());
        assertEquals(999.9,StatsForAllProfile.ballistics(entry("dimensional_hypotrochoid")).end());
    }
    @Test void exactCompatiblePairsProvenAndSnapshotRejectedForAllFour() throws Exception {
        var pairs = object(ART+"official-sockets.json").getAsJsonArray("compatiblePairs");
        assertEquals(2,pairs.size());
        var keys = new HashSet<String>();
        for (var value : pairs) {
            var p = value.getAsJsonObject(); var sfa = p.getAsJsonObject("sfa"); var other = p.getAsJsonObject("otherRoll");
            assertEquals(3,sfa.get("socket").getAsInt()); assertEquals(4,other.get("socket").getAsInt());
            assertEquals(sfa.get("hash"),other.get("hash"));
            keys.add(sfa.get("id").getAsString()+"/"+other.get("perkHash").getAsLong()+"/"+other.get("plugSetHash").getAsLong());
            assertTrue(p.getAsJsonArray("matches").get(0).getAsJsonObject().getAsJsonObject("item").get("currentlyCanRoll").getAsBoolean());
        }
        assertEquals(Set.of("retrofit_escapade/4104185692/2461260598","ammit_ar2/11612903/560115158"),keys);
        assertTrue(object(ART+"official-sockets.json").getAsJsonArray("snapshotIntersection").isEmpty());
        for (String id : IDS) assertThrows(IllegalArgumentException.class,()->StatsForAllProfile.adsTicks(entry(id),35,true));
    }
    @Test void officialScannerAuditCovers65WithExactBaseAndEnhancedExcluded() throws Exception {
        var s = object(ART+"official-sockets.json");
        assertEquals(65,s.getAsJsonArray("selectedScan").size()); assertEquals(4,s.getAsJsonArray("weapons").size());
        assertEquals(61,s.getAsJsonArray("unsupportedSelectedIds").size());
        for (var e : s.getAsJsonArray("weapons")) {
            var r = e.getAsJsonObject(); assertEquals(1583705720L,r.get("perkHash").getAsLong());
            assertEquals(4241085061L,r.get("socketCategoryHash").getAsLong());
            assertFalse(r.get("isFakePlugSet").getAsBoolean()); assertEquals("randomizedPlugSetHash",r.get("plugSetField").getAsString());
        }
        var clarity = object(ART+"clarity-source.json");
        assertEquals("039cfbc4732c33573568b28cc6335dd3332a9296",clarity.get("commit").getAsString());
        assertEquals(1409206216L,clarity.get("enhancedExcludedHash").getAsLong());
        assertFalse(clarity.getAsJsonObject("verifiedMechanics").get("refresh").getAsBoolean());
        assertTrue(clarity.getAsJsonObject("localPolicies").get("stowReload").getAsString().contains("NOT_SOURCE_PROVEN"));
    }
    @Test void malformedMechanicsMembershipCurvesAndUnknownFieldsRejectedWithoutMutation() throws Exception {
        StatsForAllProfile.validateResource(Files.readString(Path.of(RESOURCE)));
        rejects(r->r.addProperty("stage","W175")); rejects(r->r.addProperty("unknown",true));
        rejects(r->r.remove("curves")); rejects(r->r.add("weapons",JsonNull.INSTANCE));
        for (String field : List.of("hash","hitWindowTicks","durationTicks","handlingBonus","reloadBonus","stabilityBonus","rangeBonus","falloffScalar","reloadScalar"))
            rejects(r->r.getAsJsonObject("perk").addProperty(field,-1));
        rejects(r->r.getAsJsonObject("perk").addProperty("hash",1409206216L));
        rejects(r->r.getAsJsonObject("perk").addProperty("refresh",true));
        rejects(r->r.getAsJsonObject("policies").addProperty("stowReload","SOURCE_PROVEN"));
        rejects(r->r.getAsJsonArray("weapons").remove(0));
        rejects(r->r.getAsJsonArray("weapons").set(1,r.getAsJsonArray("weapons").get(0).deepCopy()));
        for (String field : List.of("id","hash","socket","perkHash","plugSetHash","unknown"))
            rejects(r->r.getAsJsonArray("weapons").get(0).getAsJsonObject().addProperty(field,"forged"));
        rejects(r->r.getAsJsonArray("curves").remove(0));
        rejects(r->r.getAsJsonArray("curves").set(1,r.getAsJsonArray("curves").get(0).deepCopy()));
        for (int i = 0; i < 4; i++) {
            final int index = i;
            for (String field : List.of("id","baseReloadStat","baseHandlingStat","baseRangeStat","unknown"))
                rejects(r->r.getAsJsonArray("curves").get(index).getAsJsonObject().addProperty(field,"forged"));
            for (String q : List.of("reload","ready","stow","ads")) for (String field : List.of("evpp","vpp","offset","unknown"))
                rejects(r->r.getAsJsonArray("curves").get(index).getAsJsonObject().getAsJsonObject(q).addProperty(field,999));
            for (String field : List.of("offsetStart","vppStart","offsetEnd","vppEnd","floor","precision","unknown"))
                rejects(r->r.getAsJsonArray("curves").get(index).getAsJsonObject().getAsJsonObject("ballistics").addProperty(field,-999));
        }
        rejects(r->r.getAsJsonArray("curves").get(0).getAsJsonObject().getAsJsonObject("reload").addProperty("offset","NaN"));
        assertThrows(IllegalStateException.class,()->StatsForAllProfile.validateResource("null"));
        assertThrows(IllegalStateException.class,()->StatsForAllProfile.validateResource("{"));
        assertEquals(4,StatsForAllProfile.rolls().size());
    }
    @Test void pinnedSourcesAndGeneratedHashesStillMatch() throws Exception {
        var m = object(ART+"manifest.json");
        for (var e : m.getAsJsonObject("sourcePins").entrySet()) {
            var pin = e.getValue().getAsJsonObject();
            var verified = PinnedProfileSourcesW234.verify(pin);
            assertEquals(pin.get("sha256").getAsString(), verified.sha256(), e.getKey());
            assertEquals(pin.get("bytes").getAsLong(), verified.bytes(), e.getKey());
        }
        assertEquals(m.get("generatorSha256").getAsString(),sha(Path.of(m.get("generator").getAsString())));
        for (var e : m.getAsJsonObject("outputSha256").entrySet()) assertEquals(e.getValue().getAsString(),sha(Path.of(e.getKey())));
    }
    @Test void freshInitializationDoesNotLoadOuterRegistries() throws Exception {
        String prefix = "kim.biryeong.destiny.weapon.";
        var forbidden = Set.of("WeaponCatalog","WeaponCharacteristics","WeaponTiming","WeaponExotics","WeaponPerks","WeaponBallistics","SnapshotAimProfile");
        var isolated = new ClassLoader(getClass().getClassLoader()) {
            @Override protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
                if (forbidden.stream().anyMatch(n->name.equals(prefix+n))) throw new AssertionError("Recursive outer load: "+name);
                if (!name.startsWith(prefix+"StatsForAllProfile")) return super.loadClass(name,resolve);
                synchronized(getClassLoadingLock(name)) {
                    var type = findLoadedClass(name);
                    if (type == null) try(var in = getParent().getResourceAsStream(name.replace('.','/')+".class")) {
                        assertNotNull(in); var bytes=in.readAllBytes(); type=defineClass(name,bytes,0,bytes.length);
                    } catch(java.io.IOException ex) { throw new ClassNotFoundException(name,ex); }
                    if (resolve) resolveClass(type); return type;
                }
            }
        };
        var type = Class.forName(prefix+"StatsForAllProfile",true,isolated);
        assertEquals(60,type.getMethod("hitWindowTicks").invoke(null));
        assertEquals(4,((List<?>)type.getMethod("rolls").invoke(null)).size());
        var method=type.getDeclaredMethod("validateResource",String.class); method.setAccessible(true);
        method.invoke(null,Files.readString(Path.of(RESOURCE)));
    }
}
