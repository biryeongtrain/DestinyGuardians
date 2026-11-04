package kim.biryeong.destiny.campaign.fallen;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.campaign.fallen.FallenSounds.BarkGate;
import kim.biryeong.destiny.campaign.fallen.FallenSounds.Ev;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.io.InputStream;
import java.nio.charset.StandardCharsets;
import java.util.HashSet;

import static org.junit.jupiter.api.Assertions.*;

/** W300 r6: curated D2 Fallen SFX table, shipped files and the bark budget. */
class FallenSoundsTest {
    private static JsonObject sounds() throws IOException {
        try (InputStream in = FallenSoundsTest.class.getResourceAsStream("/assets/destiny/sounds.json")) {
            assertNotNull(in);
            return JsonParser.parseString(new String(in.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
        }
    }

    @Test void everyCuratedEventHasASoundsJsonKeyAndMonoOggVariants() throws IOException {
        var root = sounds();
        long bytes = 0;
        var files = new HashSet<String>();
        for (Ev ev : Ev.values()) {
            assertTrue(ev.event.matches("[a-z0-9_]+"), ev.event);
            assertTrue(root.has(ev.key()), "sounds.json missing " + ev.key());
            var list = root.getAsJsonObject(ev.key()).getAsJsonArray("sounds");
            assertTrue(list.size() >= 1 && list.size() <= 8, ev + " variants " + list.size());
            for (var s : list) {
                String name = s.getAsJsonObject().get("name").getAsString();
                assertTrue(name.startsWith("destiny:guardian_rises/fallen/"), name);
                String path = "/assets/destiny/sounds/" + name.substring("destiny:".length()) + ".ogg";
                try (InputStream ogg = getClass().getResourceAsStream(path)) {
                    assertNotNull(ogg, path);
                    byte[] head = ogg.readNBytes(64);
                    assertEquals("OggS", new String(head, 0, 4, StandardCharsets.US_ASCII), path);
                    // First page: 27-byte header + 1 lacing byte, then the Vorbis id packet: type, "vorbis", version(4), channels.
                    assertEquals("vorbis", new String(head, 29, 6, StandardCharsets.US_ASCII), path);
                    assertEquals(1, head[39], "Minecraft only attenuates mono: " + path);
                    if (files.add(path)) bytes += head.length + ogg.readAllBytes().length;
                }
            }
        }
        assertTrue(bytes <= 25L * 1024 * 1024, "added audio " + bytes);
    }

    @Test void noOrphanFallenKeys() throws IOException {
        var keys = new HashSet<String>();
        for (Ev ev : Ev.values()) keys.add(ev.key());
        for (var k : sounds().keySet())
            if (k.startsWith("guardian_rises.fallen.")) assertTrue(keys.contains(k), "unused sounds.json key " + k);
    }

    @Test void everyUnitHasItsHooks() {
        for (FallenKind k : new FallenKind[]{FallenKind.DREG, FallenKind.VANDAL, FallenKind.CAPTAIN, FallenKind.SHANK}) {
            assertNotNull(FallenSounds.sighted(k), k.name());
            assertNotNull(FallenSounds.hurt(k), k.name());
            assertNotNull(FallenSounds.death(k), k.name());
            assertNotNull(FallenSounds.fire(k, false), k.name());
            var impact = FallenSounds.impact(k, false);
            assertNotNull(impact[0]); assertNotNull(impact[1]); assertNotNull(impact[2]);
            assertTrue(FallenSounds.melee(k).length > 0);
        }
        assertEquals(Ev.SHRAPNEL_LAUNCHER_FIRE, FallenSounds.fire(FallenKind.CAPTAIN, true));
        assertNull(FallenSounds.impact(FallenKind.CAPTAIN, true)[2], "slow orbs: no flyby");
        assertEquals(Ev.WALKER_FLYBY, FallenSounds.impact(FallenKind.WALKER, false)[2]);
        for (Ev ev : Ev.values())
            if (ev.cat == FallenSounds.Cat.BARK) assertEquals(24, ev.cat.range);
        assertEquals(48, Ev.WIRE_RIFLE_FIRE.cat.range);
        assertEquals(64, Ev.WALKER_CANNON_FIRE.cat.range);
    }

    @Test void pitchJitterIsBounded() {
        assertEquals(.95f, FallenSounds.pitch(1, .05f, 0), 1e-6);
        assertEquals(1.05f, FallenSounds.pitch(1, .05f, 1), 1e-6);
        assertEquals(2f, FallenSounds.pitch(3, .05f, .5f), 1e-6);
    }

    @Test void perMobAndPerEventCooldowns() {
        var g = new BarkGate();
        assertTrue(g.allow(1, 0, 0, 0, 0, 0, false));
        assertFalse(g.allow(1, 1, BarkGate.PER_MOB - 1, 0, 0, 0, false), "same mob too soon");
        assertTrue(g.allow(1, 1, BarkGate.PER_MOB, 0, 0, 0, false));
        assertFalse(g.allow(1, 0, BarkGate.PER_MOB * 2, 0, 0, 0, false), "same event inside PER_EVENT");
        assertTrue(g.allow(1, 0, BarkGate.PER_EVENT, 0, 0, 0, false));
    }

    @Test void tenDregsShareABudgetOfTwoBarksPerSecondNearby() {
        var g = new BarkGate();
        int allowed = 0;
        for (int mob = 0; mob < 10; mob++) if (g.allow(mob, 0, 100, mob, 0, 0, false)) allowed++;
        assertEquals(BarkGate.BUDGET, allowed);
        // Over a 10 s firefight with every Dreg trying every tick, at most BUDGET per WINDOW.
        g = new BarkGate();
        allowed = 0;
        for (long t = 0; t < 200; t++) for (int mob = 0; mob < 10; mob++) if (g.allow(mob, (int) (t % 3), t, mob, 0, 0, false)) allowed++;
        assertTrue(allowed <= BarkGate.BUDGET * (200 / BarkGate.WINDOW + 1), "barks " + allowed);
        assertTrue(allowed >= 10, "still audible: " + allowed);
    }

    @Test void farGroupsHaveTheirOwnBudgetAndDeathCriesGetAnExtraSlot() {
        var g = new BarkGate();
        assertTrue(g.allow(1, 0, 0, 0, 0, 0, false));
        assertTrue(g.allow(2, 0, 0, 1, 0, 0, false));
        assertFalse(g.allow(3, 0, 0, 2, 0, 0, false));
        assertTrue(g.allow(4, 0, 0, 100, 0, 0, false), "40+ m away: separate budget");
        assertTrue(g.allow(1, 5, 1, 0, 0, 0, true), "death cry ignores per-mob cooldown and has one extra slot");
        assertFalse(g.allow(2, 5, 1, 0, 0, 0, true));
        assertTrue(g.allow(3, 0, BarkGate.WINDOW, 2, 0, 0, false), "window slides");
    }

    @Test void flybyClosestPoint() {
        var a = new Vec3(0, 0, 0); var b = new Vec3(10, 0, 0);
        assertEquals(new Vec3(4, 0, 0), FallenWeapons.closestOnSegment(a, b, new Vec3(4, 2, 0)));
        assertEquals(a, FallenWeapons.closestOnSegment(a, b, new Vec3(-5, 1, 0)));
        assertEquals(b, FallenWeapons.closestOnSegment(a, b, new Vec3(20, 1, 0)));
        assertEquals(a, FallenWeapons.closestOnSegment(a, a, new Vec3(3, 3, 3)));
    }
}
