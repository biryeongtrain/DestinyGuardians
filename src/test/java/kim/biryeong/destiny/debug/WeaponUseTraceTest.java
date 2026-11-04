package kim.biryeong.destiny.debug;

import com.google.gson.JsonParser;
import com.sun.source.tree.ClassTree;
import com.sun.source.tree.MethodTree;
import com.sun.source.tree.VariableTree;
import com.sun.source.util.JavacTask;
import java.net.URI;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.concurrent.CountDownLatch;
import java.util.concurrent.Executors;
import java.util.concurrent.Future;
import java.util.concurrent.TimeUnit;
import javax.tools.Diagnostic;
import javax.tools.DiagnosticCollector;
import javax.tools.JavaFileObject;
import javax.tools.SimpleJavaFileObject;
import javax.tools.ToolProvider;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.Timeout;
import static org.junit.jupiter.api.Assertions.*;

/** W107: pure limiter tests and parsed source contracts; no Minecraft bootstrap or native input proof. */
class WeaponUseTraceTest {
    private static final Path JAVA = Path.of("src/main/java/kim/biryeong/destiny");

    @Test void rejectsInvalidCapsAndStartsEveryValidCapEmpty() {
        for (int cap : new int[] {Integer.MIN_VALUE, -4096, -1, 0, 4097, 8192, Integer.MAX_VALUE})
            assertThrows(IllegalArgumentException.class, () -> new WeaponUseTrace.TraceLimit(cap), "cap=" + cap);
        for (int cap = 1; cap <= 4096; cap++)
            assertEquals(0, new WeaponUseTrace.TraceLimit(cap).count(), "cap=" + cap);
    }

    @Test void admitsExactlyTheCapAndNeverReopensAfterExhaustion() {
        for (int cap : new int[] {1, 2, 3, 31, 255, 4095, 4096}) {
            var limit = new WeaponUseTrace.TraceLimit(cap);
            for (int used = 0; used < cap; used++) {
                assertEquals(used, limit.count());
                assertTrue(limit.take(), "premature exhaustion at " + used + " of " + cap);
                assertEquals(used + 1, limit.count());
            }
            for (int denied = 0; denied < 16_384; denied++) {
                assertFalse(limit.take(), "exhausted limiter reopened: " + cap);
                assertEquals(cap, limit.count(), "denied attempts must not increment or overflow");
            }
            var independent = new WeaponUseTrace.TraceLimit(1);
            assertEquals(0, independent.count());
            assertTrue(independent.take());
            assertEquals(cap, limit.count(), "a new limiter must not reset an exhausted instance");
        }
    }

    @Test @Timeout(40)
    void concurrentAdmissionNeverExceedsCapOrLosesSuccessfulTakes() throws Exception {
        for (int cap : new int[] {1, 4096}) {
            var limit = new WeaponUseTrace.TraceLimit(cap);
            var ready = new CountDownLatch(8);
            var start = new CountDownLatch(1);
            var workers = Executors.newFixedThreadPool(8);
            try {
                List<Future<Integer>> results = new ArrayList<>();
                for (int worker = 0; worker < 8; worker++) results.add(workers.submit(() -> {
                    ready.countDown();
                    assertTrue(start.await(10, TimeUnit.SECONDS), "start gate timed out");
                    int admitted = 0, previous = 0;
                    for (int attempt = 0; attempt < 2048; attempt++) {
                        if (limit.take()) admitted++;
                        int observed = limit.count();
                        assertTrue(observed >= previous && observed <= cap, "count regressed or exceeded cap");
                        previous = observed;
                    }
                    return admitted;
                }));
                assertTrue(ready.await(10, TimeUnit.SECONDS), "workers did not reach start gate");
                start.countDown();
                int admitted = 0;
                for (var result : results) admitted += result.get(10, TimeUnit.SECONDS);
                assertEquals(cap, admitted);
                assertEquals(admitted, limit.count());
                assertFalse(limit.take());
                assertEquals(cap, limit.count());
            } finally {
                start.countDown();
                workers.shutdownNow();
                assertTrue(workers.awaitTermination(5, TimeUnit.SECONDS), "limiter workers leaked");
            }
        }
    }

    @Test void optInAndExactPlayerSelectionPrecedeExistingStateOnlyProjection() throws Exception {
        var trace = source("debug/WeaponUseTrace.java");
        assertEquals(Set.of("ENABLED", "PLAYER", "LIMIT"), fields(trace).stream()
                .map(field -> field.getName().toString()).collect(java.util.stream.Collectors.toSet()));
        assertInitializer(trace, "ENABLED", "Boolean.getBoolean(\"destiny.weapon.useTrace\")");
        assertInitializer(trace, "PLAYER", "System.getProperty(\"destiny.weapon.useTrace.player\", \"\")");
        assertInitializer(trace, "LIMIT", "new TraceLimit(4096)");
        assertEquals(List.of("<init>", "selected", "record"), methods(trace).stream()
                .map(method -> method.getName().toString()).toList());
        assertTrue(trace.getMembers().stream().allMatch(member -> member instanceof VariableTree
                || member instanceof MethodTree || member instanceof ClassTree), "unexpected initializer block");
        assertBody(method(trace, "selected"), """
                { return ENABLED && !PLAYER.isEmpty() && player != null
                        && PLAYER.equals(player.getGameProfile().name()); }
                """);
        assertBody(method(source("weapon/WeaponRuntime.java"), "traceUse"), """
                {
                    if (!kim.biryeong.destiny.debug.WeaponUseTrace.selected(player)) return;
                    State s = STATES.get(player.getUUID());
                    boolean owned = s != null && s.owner == player && s.level == player.level();
                    kim.biryeong.destiny.debug.WeaponUseTrace.record(player, event, sequence,
                            owned && s.stack == player.getMainHandItem(), owned && s.holding,
                            owned ? s.heldUntil : -1, owned ? s.cycle.firingDeadline() : -1);
                }
                """);
        assertBody(method(source("weapon/WeaponCycle.java"), "firingDeadline"), "{ return readyAt; }");
    }

    @Test void boundedPayloadUsesOnlyReviewedReadOnlyProjectionsAndNoSecretsOrSends() throws Exception {
        // Exact parsed bodies deliberately freeze the observer's effect boundary. New calls require review.
        assertBody(method(source("debug/WeaponUseTrace.java"), "record"), """
                {
                    if (!selected(player) || !LIMIT.take()) return;
                    var held = player.getMainHandItem();
                    var entry = WeaponItems.entry(held);
                    var out = new JsonObject();
                    out.addProperty("event", event);
                    out.addProperty("index", LIMIT.count());
                    out.addProperty("wallMs", System.currentTimeMillis());
                    out.addProperty("nanoTime", System.nanoTime());
                    out.addProperty("serverTick", player.level().getServer().getTickCount());
                    out.addProperty("sequence", sequence);
                    out.addProperty("usingItem", player.isUsingItem());
                    out.addProperty("useMatchesHeld", player.getUseItem() == held);
                    out.addProperty("heldIdentity", System.identityHashCode(held));
                    out.addProperty("weapon", entry.map(e -> e.id()).orElse("none"));
                    out.addProperty("twoHanded", WeaponModels.twoHanded(held));
                    out.addProperty("rounds", entry.map(e -> WeaponItems.magazine(held, WeaponProfile.forEntry(e)).rounds()).orElse(-1));
                    out.addProperty("runtimeBound", bound);
                    out.addProperty("holding", holding);
                    out.addProperty("heldUntil", heldUntil);
                    out.addProperty("firingDeadline", firingDeadline);
                    DestinyGuardians.LOGGER.info("[W107 use trace] {}", out);
                }
                """);
        // W193 review: loadedLimit reads saved authorization and exact selected rolls only;
        // it never binds perk sessions, grants/saves ammo or writes the observed item.
        assertBody(method(source("weapon/WeaponItems.java"), "magazine"), """
                {
                    var data = stack.get(DataComponents.CUSTOM_DATA);
                    if (data == null) return new WeaponMagazine(p, 0, 0);
                    var tag = data.copyTag();
                    var ammo = new WeaponMagazine(p, savedCount(tag, ROUNDS), savedCount(tag, RESERVE), savedCount(tag, OVERFLOW), loadedLimit(stack, p, tag));
                    if (SwordItems.isSword(stack)) ammo.reload();
                    return ammo;
                }
                """);
    }

    @Test void registeredPacketObserversRunAfterExactMainThreadCheckWithoutCancellationOrMutation() throws Exception {
        var mixin = source("mixin/WeaponUseTraceMixin.java");
        assertEquals("@Mixin(ServerGamePacketListenerImpl.class)", mixin.getModifiers().getAnnotations().getFirst().toString());
        assertEquals(1, mixin.getModifiers().getAnnotations().size());
        assertEquals(1, fields(mixin).size());
        assertEquals("@Shadow", fields(mixin).getFirst().getModifiers().getAnnotations().getFirst().toString());
        assertEquals("player", fields(mixin).getFirst().getName().toString());
        assertNull(fields(mixin).getFirst().getInitializer());
        assertEquals(List.of("destiny$useReceived", "destiny$actionReceived"), methods(mixin).stream()
                .map(method -> method.getName().toString()).toList());
        assertEquals(3, mixin.getMembers().size(), "no extra initialization or behavior in the observer");
        String target = "Lnet/minecraft/network/protocol/PacketUtils;ensureRunningOnSameThread("
                + "Lnet/minecraft/network/protocol/Packet;Lnet/minecraft/network/PacketListener;"
                + "Lnet/minecraft/server/level/ServerLevel;)V";
        assertObserver(method(mixin, "destiny$useReceived"), "handleUseItem", target, """
                { WeaponRuntime.traceUse(player, "packet.use." + packet.hand().name(), packet.sequence()); }
                """);
        assertObserver(method(mixin, "destiny$actionReceived"), "handlePlayerAction", target, """
                { WeaponRuntime.traceUse(player, "packet.action." + packet.getAction().name(), packet.getSequence()); }
                """);
        var config = JsonParser.parseString(Files.readString(Path.of("src/main/resources/destiny.mixins.json"))).getAsJsonObject();
        assertTrue(config.get("required").getAsBoolean());
        assertEquals("kim.biryeong.destiny.mixin", config.get("package").getAsString());
        assertEquals(1, config.getAsJsonObject("injectors").get("defaultRequire").getAsInt());
        long registrations = 0;
        for (var name : config.getAsJsonArray("mixins"))
            if (name.getAsString().equals("WeaponUseTraceMixin")) registrations++;
        assertEquals(1, registrations);
    }

    private static void assertObserver(MethodTree observer, String handler, String target, String body) throws Exception {
        var expected = parse("class Contract { @Inject(method = \"" + handler
                + "\", at = @At(value = \"INVOKE\", target = \"" + target
                + "\", shift = At.Shift.AFTER)) private void check() {} }");
        assertEquals(method(expected, "check").getModifiers().getAnnotations().toString(),
                observer.getModifiers().getAnnotations().toString(), "injection must not cancel, replace arguments or ignore missing targets");
        assertBody(observer, body);
    }

    private static void assertInitializer(ClassTree type, String name, String expected) {
        var field = fields(type).stream().filter(candidate -> candidate.getName().contentEquals(name)).findFirst().orElseThrow();
        assertTrue(field.getModifiers().getFlags().containsAll(Set.of(
                javax.lang.model.element.Modifier.PRIVATE, javax.lang.model.element.Modifier.STATIC,
                javax.lang.model.element.Modifier.FINAL)));
        assertEquals(expected, field.getInitializer().toString());
    }

    private static void assertBody(MethodTree method, String expectedBody) throws Exception {
        var expected = method(parse("class Contract { void check() " + expectedBody + " }"), "check");
        assertEquals(expected.getBody().toString(), method.getBody().toString(), method.getName().toString());
    }

    private static List<MethodTree> methods(ClassTree type) {
        return type.getMembers().stream().filter(MethodTree.class::isInstance).map(MethodTree.class::cast).toList();
    }

    private static List<VariableTree> fields(ClassTree type) {
        return type.getMembers().stream().filter(VariableTree.class::isInstance).map(VariableTree.class::cast).toList();
    }

    private static MethodTree method(ClassTree type, String name) {
        var matches = methods(type).stream().filter(candidate -> candidate.getName().contentEquals(name)).toList();
        assertEquals(1, matches.size(), "missing or ambiguous method " + name);
        return matches.getFirst();
    }

    private static ClassTree source(String relativePath) throws Exception {
        return parse(Files.readString(JAVA.resolve(relativePath)));
    }

    private static ClassTree parse(String text) throws Exception {
        var compiler = ToolProvider.getSystemJavaCompiler();
        assertNotNull(compiler, "source contracts require the project's Java 25 JDK");
        var diagnostics = new DiagnosticCollector<JavaFileObject>();
        var input = new SimpleJavaFileObject(URI.create("string:///TraceContract.java"), JavaFileObject.Kind.SOURCE) {
            @Override public CharSequence getCharContent(boolean ignoreEncodingErrors) { return text; }
        };
        try (var files = compiler.getStandardFileManager(diagnostics, null, null)) {
            // Parse only: no class loading, annotation processing, compilation output or registry bootstrap.
            var task = (JavacTask) compiler.getTask(null, files, diagnostics, List.of("-proc:none"), null, List.of(input));
            var unit = task.parse().iterator().next();
            assertTrue(diagnostics.getDiagnostics().stream().noneMatch(d -> d.getKind() == Diagnostic.Kind.ERROR),
                    () -> diagnostics.getDiagnostics().toString());
            return unit.getTypeDecls().stream().filter(ClassTree.class::isInstance)
                    .map(ClassTree.class::cast).findFirst().orElseThrow();
        }
    }
}
