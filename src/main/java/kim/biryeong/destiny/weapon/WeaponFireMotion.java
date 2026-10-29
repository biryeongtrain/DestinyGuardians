package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import org.joml.Matrix4f;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.io.InputStreamReader;
import java.io.Reader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Source-authored cosmetic root motion; never changes camera, aim, ammo, CMD or item models.
 * JSON already contains endpoint-relative view metres/quaternions and the 1/30s onset blend.
 * Its sourceUnitToView=1 is an explicit Minecraft calibration, not a measured Destiny scale.
 * Local display policy: at most 24 overlapping impulses, summed translations/rotation vectors,
 * bounded to .35 view metres and 40 degrees. These bounds are not original game statistics.
 * Original arm articulation and moving weapon parts are not reconstructed by this rigid root.
 * All production entry points run on the server thread. */
public final class WeaponFireMotion {
    static final int SAMPLES = 61, MAX_IMPULSES = 24;
    static final float MAX_TRANSLATION = .35f, MAX_ROTATION = (float)Math.toRadians(40);
    private static final Controller LIVE = new Controller();
    private WeaponFireMotion() {}

    private static final class Source {
        static final Library LIBRARY = load();
        private static Library load() {
            var in = WeaponFireMotion.class.getResourceAsStream("/destiny/weapons/w242-fire-motion.json");
            if (in == null) throw new IllegalStateException("Missing W242 source fire motion");
            try (var reader = new InputStreamReader(in, StandardCharsets.UTF_8)) {
                var library = Library.read(reader);
                var expected = new HashSet<String>();
                for (var entry : WeaponCatalog.all()) if (!entry.family().equals("sword")) expected.add(entry.id());
                if (!expected.equals(library.weapons.keySet()))
                    throw new IllegalStateException("W242 fire motion must cover every non-sword catalog weapon");
                return library;
            } catch (java.io.IOException e) { throw new IllegalStateException("Unreadable W242 fire motion", e); }
        }
    }

    /** Called only for an accepted emission, once outside the pellet loop. playFire also marks
     * the first shared-ammo bolt; later shared bolts must not restart the source clip. */
    public static void emitted(ServerPlayer player, WeaponCatalog.Entry entry, WeaponProfile profile,
                               boolean playFire, int boltIndex) {
        if (!ProfileWeaponView.enabled() || entry == null || profile.mode() == WeaponProfile.Mode.MELEE
                || entry.family().equals("sword") || !visible(player)
                || WeaponItems.entry(player.getMainHandItem()).filter(entry::equals).isEmpty()) return;
        if (!accepts(profile.sharedBurstAmmo(), playFire, boltIndex)) return;
        var clips = Source.LIBRARY.weapons.get(entry.id());
        if (clips == null) return;
        LIVE.emit(player.getUUID(), player, player.getMainHandItem(), player.level(), entry.id(), clips,
                player.level().getServer().getTickCount(), profile.sharedBurstAmmo(), playFire, boltIndex,
                WeaponAiming.progress(player));
    }

    public static void clear(ServerPlayer player) { LIVE.clear(player.getUUID(), player); }

    /** Exact outgoing object only: a stale donor must not clear a recipient's binding. */
    public static void inventoryStowing(ServerPlayer player, ItemStack stack) {
        LIVE.stow(player.getUUID(), player, stack);
    }

    /** Read-only, detached current view-space delta, before left-hand mirroring. No clock is
     * advanced, binding created, or expired impulse removed by this QA/render snapshot. */
    public static Matrix4f matrix(ServerPlayer player) { return pose(player).matrix(false); }

    static Pose pose(ServerPlayer player) {
        if (!visible(player) || WeaponHandling.blocked(player)) return Pose.IDENTITY;
        // Only shot-caused reload keeps the binding: manual reload/suspend explicitly clear it.
        // ADS suspension resets live progress to zero; retain each paid shot's source variant.
        return LIVE.sample(player.getUUID(), player, player.getMainHandItem(), player.level(),
                player.level().getServer().getTickCount(), WeaponAiming.progress(player), WeaponRuntime.reloading(player));
    }

    /** Render lifecycle retirement, separate from the read-only matrix snapshot. */
    static void retire(ServerPlayer player) {
        if (!visible(player) || WeaponHandling.blocked(player)) { clear(player); return; }
        LIVE.retire(player.getUUID(), player, player.getMainHandItem(), player.level(),
                player.level().getServer().getTickCount(), WeaponRuntime.reloading(player));
    }

    private static boolean visible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected() && p.getCamera() == p
                && !kim.biryeong.destiny.guardian.Guardians.runtime(p).gcbThirdPerson
                && !kim.biryeong.destiny.ability.AbilityService.inSuper(p);
    }

    static boolean accepts(boolean sharedAmmo, boolean first, int bolt) {
        return bolt >= 0 && bolt < 9 && (!sharedAmmo || first && bolt == 0);
    }

    /** Immutable pose values prevent callers from modifying the loaded source samples. */
    record Pose(float x, float y, float z, float qx, float qy, float qz, float qw) {
        static final Pose IDENTITY = new Pose(0, 0, 0, 0, 0, 0, 1);
        Pose {
            if (!Float.isFinite(x) || !Float.isFinite(y) || !Float.isFinite(z)
                    || !Float.isFinite(qx) || !Float.isFinite(qy) || !Float.isFinite(qz) || !Float.isFinite(qw))
                throw new IllegalArgumentException("Non-finite W242 pose");
            double length = Math.sqrt((double)qx*qx + (double)qy*qy + (double)qz*qz + (double)qw*qw);
            if (length < 1e-8 || Math.abs(length - 1) > .001)
                throw new IllegalArgumentException("Non-unit W242 quaternion");
            // Canonical sign makes q and -q identical and exposes the shortest rotation vector.
            float divisor = (float)(qw < 0 ? -length : length);
            qx /= divisor; qy /= divisor; qz /= divisor; qw /= divisor;
        }
        Quaternionf rotation() { return new Quaternionf(qx, qy, qz, qw); }
        Matrix4f matrix(boolean left) {
            return new Matrix4f().translation(left ? -x : x, y, z)
                    .rotate(new Quaternionf(qx, left ? -qy : qy, left ? -qz : qz, qw));
        }
        boolean neutral() {
            return Math.abs(x) < 1e-6 && Math.abs(y) < 1e-6 && Math.abs(z) < 1e-6
                    && Math.abs(qx) < 1e-6 && Math.abs(qy) < 1e-6 && Math.abs(qz) < 1e-6;
        }
        static Pose blend(Pose a, Pose b, float fraction) {
            float t = Float.isFinite(fraction) ? Math.clamp(fraction, 0, 1) : 0;
            var q = a.rotation().slerp(b.rotation(), t).normalize();
            return new Pose(a.x+(b.x-a.x)*t, a.y+(b.y-a.y)*t, a.z+(b.z-a.z)*t, q.x, q.y, q.z, q.w);
        }
    }

    record Clip(double duration, List<Pose> samples) {
        Clip {
            if (!Double.isFinite(duration) || duration <= 0 || duration > 10 || samples == null || samples.size() != SAMPLES)
                throw new IllegalArgumentException("Invalid W242 clip duration/sample count");
            samples = List.copyOf(samples);
            if (!samples.getFirst().neutral() || !samples.getLast().neutral())
                throw new IllegalArgumentException("W242 endpoints must be neutral, not first-frame referenced");
        }
        Pose sample(double elapsed) {
            if (!Double.isFinite(elapsed) || elapsed <= 0 || elapsed >= duration) return Pose.IDENTITY;
            double sample = elapsed / duration * (SAMPLES - 1);
            int lo = Math.min((int)sample, SAMPLES - 2);
            return Pose.blend(samples.get(lo), samples.get(lo+1), (float)(sample-lo));
        }
    }

    record Clips(Clip hip, Clip ads) {
        Clips { Objects.requireNonNull(hip); Objects.requireNonNull(ads); }
        double duration() { return Math.max(hip.duration, ads.duration); }
        Pose sample(double elapsed, float adsProgress) {
            return Pose.blend(hip.sample(elapsed), ads.sample(elapsed), adsProgress);
        }
    }

    static final class Library {
        private record Document(int schemaVersion, int samplesPerClip, double sourceUnitToView,
                                Map<String, Route> weapons, Map<String, Map<String, RawClip>> groups) {}
        private record Route(String group, String hip, String ads) {}
        private record RawClip(double duration, List<RawPose> samples) {}
        private record RawPose(float[] translation, float[] rotation) {}
        final Map<String, Clips> weapons;
        final Map<String, Map<String, Clip>> groups;
        private Library(Map<String, Clips> weapons, Map<String, Map<String, Clip>> groups) {
            this.weapons = Map.copyOf(weapons); this.groups = Map.copyOf(groups);
        }
        static Library read(Reader reader) {
            var data = new Gson().fromJson(reader, Document.class);
            if (data == null || data.schemaVersion != 1 || data.samplesPerClip != SAMPLES || data.sourceUnitToView != 1
                    || data.weapons == null || data.weapons.isEmpty() || data.groups == null || data.groups.isEmpty())
                throw new IllegalArgumentException("Invalid W242 fire motion schema/calibration");
            var groups = new HashMap<String, Map<String, Clip>>();
            data.groups.forEach((name, actions) -> {
                var clips = new HashMap<String, Clip>();
                actions.forEach((tag, raw) -> {
                    var poses = new ArrayList<Pose>();
                    if (raw == null || raw.samples == null) throw new IllegalArgumentException("Missing W242 samples");
                    for (var p : raw.samples) {
                        if (p == null || p.translation == null || p.translation.length != 3 || p.rotation == null || p.rotation.length != 4)
                            throw new IllegalArgumentException("Invalid W242 pose dimensions");
                        poses.add(new Pose(p.translation[0], p.translation[1], p.translation[2],
                                p.rotation[0], p.rotation[1], p.rotation[2], p.rotation[3]));
                    }
                    clips.put(tag, new Clip(raw.duration, poses));
                });
                groups.put(name, Map.copyOf(clips));
            });
            var weapons = new HashMap<String, Clips>();
            data.weapons.forEach((id, route) -> {
                var group = route == null ? null : groups.get(route.group);
                if (group == null || !group.containsKey(route.hip) || !group.containsKey(route.ads))
                    throw new IllegalArgumentException("Missing W242 hip/ADS route for " + id);
                weapons.put(id, new Clips(group.get(route.hip), group.get(route.ads)));
            });
            return new Library(weapons, groups);
        }
    }

    /** Pure cosmetic controller also used by unit tests with ordinary identity tokens. */
    static final class Controller {
        private static final class Impulse {
            final long tick; final Clips clips; final float emittedAds;
            boolean reloadTail;
            Impulse(long tick, Clips clips, float emittedAds) { this.tick=tick; this.clips=clips; this.emittedAds=emittedAds; }
        }
        private static final class Playback {
            final Object owner, stack, level;
            final String weapon;
            final Deque<Impulse> impulses = new ArrayDeque<>();
            long eventTick = Long.MIN_VALUE;
            int eventMask;
            Playback(Object owner, Object stack, Object level, String weapon) {
                this.owner=owner; this.stack=stack; this.level=level; this.weapon=weapon;
            }
            boolean matches(Object owner, Object stack, Object level) {
                return this.owner == owner && this.stack == stack && this.level == level;
            }
        }
        private final Map<Object, Playback> active = new HashMap<>();
        void emit(Object key, Object owner, Object stack, Object level, String weapon, Clips clips,
                  long tick, boolean sharedAmmo, boolean first, int bolt, float emittedAds) {
            if (!accepts(sharedAmmo, first, bolt)) return;
            var s = active.get(key);
            if (s == null || !s.matches(owner, stack, level) || !s.weapon.equals(weapon) || tick < s.eventTick) {
                s = new Playback(owner, stack, level, weapon); active.put(key, s);
            }
            if (s.eventTick != tick) { s.eventTick=tick; s.eventMask=0; }
            int bit = 1 << bolt;
            if ((s.eventMask & bit) != 0) return; // Same event, not distinct paid burst bullets in this tick.
            s.eventMask |= bit;
            s.impulses.removeIf(i -> (tick-i.tick)/20.0 >= i.clips.duration());
            if (s.impulses.size() == MAX_IMPULSES) s.impulses.removeFirst();
            s.impulses.addLast(new Impulse(tick, clips, Float.isFinite(emittedAds) ? Math.clamp(emittedAds, 0, 1) : 0));
        }
        void clear(Object key, Object owner) {
            var s = active.get(key);
            if (s != null && s.owner == owner) active.remove(key);
        }
        void stow(Object key, Object owner, Object stack) {
            var s = active.get(key);
            if (s != null && s.owner == owner && s.stack == stack) active.remove(key);
        }
        void retire(Object key, Object owner, Object stack, Object level, long tick) {
            retire(key, owner, stack, level, tick, false);
        }
        void retire(Object key, Object owner, Object stack, Object level, long tick, boolean reloading) {
            var s = active.get(key);
            if (s == null) return;
            if (!s.matches(owner, stack, level) || tick < s.eventTick) { active.remove(key); return; }
            s.impulses.removeIf(i -> (tick-i.tick)/20.0 >= i.clips.duration());
            // A short bow nock/reload can finish before its fire clip: keep the paid source
            // variant through the whole tail, even when live ADS is subsequently reset.
            if (reloading) for (var i : s.impulses) i.reloadTail=true;
            if (s.impulses.isEmpty()) active.remove(key);
        }
        int count(Object key) { var s=active.get(key); return s == null ? 0 : s.impulses.size(); }
        Pose sample(Object key, Object owner, Object stack, Object level, long tick, float ads, boolean reloading) {
            var s = active.get(key);
            if (s == null || !s.matches(owner, stack, level) || tick < s.eventTick) return Pose.IDENTITY;
            var translation = new Vector3f(); var rotation = new Vector3f();
            for (var i : s.impulses) {
                double elapsed = (tick-i.tick)/20.0;
                if (elapsed < 0 || elapsed >= i.clips.duration()) continue;
                var pose = i.clips.sample(elapsed, reloading || i.reloadTail ? i.emittedAds : ads);
                translation.add(pose.x, pose.y, pose.z);
                float sin = (float)Math.sqrt(pose.qx*pose.qx + pose.qy*pose.qy + pose.qz*pose.qz);
                if (sin > 1e-8f) rotation.add(new Vector3f(pose.qx, pose.qy, pose.qz)
                        .mul(2*(float)Math.atan2(sin, pose.qw)/sin));
            }
            if (translation.length() > MAX_TRANSLATION) translation.normalize(MAX_TRANSLATION);
            float angle = rotation.length();
            var q = angle < 1e-8f ? new Quaternionf() : new Quaternionf().rotationAxis(Math.min(angle, MAX_ROTATION), rotation.div(angle));
            return new Pose(translation.x, translation.y, translation.z, q.x, q.y, q.z, q.w);
        }
    }
}
