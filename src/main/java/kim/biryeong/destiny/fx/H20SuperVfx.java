package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** H20 particle-only accents. No new display holders, backend trackers, gameplay tasks or clocks. */
final class H20SuperVfx {
    private static final int MAX_PER_OWNER = 4;
    private static final int MAX_TOTAL = 24;
    private static final int POINTS_PER_OWNER_TICK = 24;
    private static final int POINTS_TOTAL_TICK = 192;
    private static final List<Cue> CUES = new ArrayList<>();
    private static final Map<UUID, Integer> USED = new HashMap<>();
    private static MinecraftServer budgetServer;
    private static int budgetTick = Integer.MIN_VALUE;
    private static int totalUsed;

    enum Kind { EQUIP, ARROW, ANCHOR }
    enum Phase { FORM, IDLE, CHARGE, RELEASE, DISSOLVE, FLIGHT, ANCHORED }

    private static final class Cue {
        final ServerPlayer owner;
        final ServerLevel level;
        final Element element;
        final Kind kind;
        final int born;
        int expires;
        int phaseAt;
        int chargeAt = Integer.MIN_VALUE;
        int emittedAt = Integer.MIN_VALUE;
        double charge;
        Phase phase = Phase.FORM;
        Vec3 position;
        Vec3 direction;
        SimProjectile arrow;

        Cue(ServerPlayer owner, Element element, Kind kind, int ticks) {
            this.owner = owner;
            this.level = owner.level();
            this.element = element;
            this.kind = kind;
            born = phaseAt = level.getServer().getTickCount();
            expires = born + ticks;
        }
    }

    private H20SuperVfx() { }

    static boolean materialize(ServerPlayer owner, Element element) {
        if (!valid(owner) || element == null || element == Element.KINETIC) return false;
        // Re-entrant activation cannot leave a second set of prop accents behind.
        CUES.removeIf(c -> c.owner == owner && c.kind == Kind.EQUIP);
        add(new Cue(owner, element, Kind.EQUIP, 420));
        return true;
    }

    static void charge(ServerPlayer owner, double progress) {
        if (!Double.isFinite(progress) || !valid(owner)) return;
        Cue cue = equip(owner);
        if (cue == null || cue.element != Element.VOID || cue.phase == Phase.RELEASE
                || cue.phase == Phase.DISSOLVE) return;
        cue.phase = Phase.CHARGE;
        cue.charge = H20VfxGeometry.progress(progress);
        cue.chargeAt = cue.level.getServer().getTickCount();
    }

    static boolean release(ServerPlayer owner, Vec3 from, Vec3 direction) {
        if (!valid(owner) || !finite(from) || !finite(direction)
                || direction.lengthSqr() < 1.0e-8 || !Double.isFinite(direction.lengthSqr())
                || from.distanceToSqr(owner.getEyePosition()) > 16) return false;
        Cue cue = equip(owner);
        if (cue == null || cue.element != Element.VOID) {
            materialize(owner, Element.VOID);
            cue = equip(owner);
        }
        cue.phase = Phase.RELEASE;
        cue.phaseAt = cue.level.getServer().getTickCount();
        cue.expires = cue.phaseAt + 7;
        cue.position = from;
        cue.direction = direction.normalize();
        return true;
    }

    static boolean followArrow(ServerPlayer owner, SimProjectile arrow) {
        if (!valid(owner) || arrow == null || arrow.isDone() || !finite(arrow.position())) return false;
        CUES.removeIf(c -> c.owner == owner && c.kind == Kind.ARROW);
        Cue cue = new Cue(owner, Element.VOID, Kind.ARROW, 42);
        cue.arrow = arrow;
        cue.phase = Phase.FLIGHT;
        cue.position = arrow.position();
        add(cue);
        return true;
    }

    static void dematerialize(ServerPlayer owner, Element element) {
        Cue cue = equip(owner);
        if (cue == null || cue.element != element || cue.phase == Phase.DISSOLVE) return;
        // Normal Void session end immediately follows launch; let the release snap finish.
        if (cue.phase == Phase.RELEASE) return;
        cue.phase = Phase.DISSOLVE;
        cue.phaseAt = cue.level.getServer().getTickCount();
        cue.expires = cue.phaseAt + 5;
    }

    static void anchor(ServerPlayer owner, Vec3 position, int ticks) {
        if (!valid(owner) || !finite(position) || ticks <= 0) return;
        CUES.removeIf(c -> c.owner == owner && c.kind == Kind.ANCHOR && c.position.equals(position));
        Cue cue = new Cue(owner, Element.VOID, Kind.ANCHOR, Math.min(200, ticks));
        cue.position = position;
        cue.phase = Phase.ANCHORED;
        add(cue);
    }

    static void arcStrike(ServerPlayer owner, double reach) {
        if (!valid(owner) || !Double.isFinite(reach) || reach <= 0 || reach > 96) return;
        Vec3 look = owner.getLookAngle();
        Vec3 center = owner.position().add(0, 1.05, 0);
        for (int i = 0; i < 9; i++) {
            double angle = Math.toRadians(-36 + i * 9);
            Vec3 point = center.add(look.yRot((float) angle).scale(Math.min(3.5, reach) * .8));
            emit(owner, point, Element.ARC, i % 3 == 0, .48f);
            if (i % 3 == 0) emit(owner, point.add(0, .12, .04), Element.ARC, true, .4f);
        }
    }

    static void solarShot(ServerPlayer owner, Vec3 from) {
        if (!valid(owner) || !finite(from)) return;
        Basis basis = basis(owner.getLookAngle());
        render(owner, from, basis, H20VfxGeometry.release(0), Element.SOLAR, .45f);
    }

    static void tick(MinecraftServer server) {
        // HunterVfx ticks first. A tracker evicted/closed by its existing pool must not leave orphan runes.
        var anchors = CUES.stream().anyMatch(c -> c.kind == Kind.ANCHOR)
                ? HunterVfx.snapshots() : List.<HunterVfx.Snapshot>of();
        var iterator = CUES.iterator();
        while (iterator.hasNext()) {
            Cue cue = iterator.next();
            if (cue.level.getServer() != server) continue;
            int now = server.getTickCount();
            if (!valid(cue.owner) || cue.owner.level() != cue.level || now >= cue.expires
                    || (cue.arrow != null && cue.arrow.isDone())
                    || (cue.kind == Kind.ANCHOR && anchors.stream().noneMatch(s ->
                    s.owner().equals(cue.owner.getUUID()) && s.model().equals(HunterVfx.Kind.VOID_ANCHOR.modelName())
                            && s.position().equals(cue.position.add(0, .25, 0))))) {
                iterator.remove();
                continue;
            }
            if (cue.emittedAt == now) continue;
            cue.emittedAt = now;
            try {
                switch (cue.kind) {
                    case EQUIP -> equipFrame(cue, now);
                    case ARROW -> arrowFrame(cue);
                    case ANCHOR -> {
                        int age = now - cue.born;
                        if (age % 3 == 0) render(cue.owner, cue.position, WORLD,
                                H20VfxGeometry.anchor(age, cue.expires - now), Element.VOID, .55f);
                    }
                }
            } catch (RuntimeException failure) {
                iterator.remove();
                DestinyGuardians.LOGGER.warn("H20 ultimate accent failed: {}", failure.toString());
            }
        }
    }

    private static void equipFrame(Cue cue, int now) {
        int age = now - cue.phaseAt;
        if (cue.phase == Phase.FORM && age >= 10) cue.phase = Phase.IDLE;
        if (cue.phase == Phase.CHARGE && now - cue.chargeAt > 2) cue.phase = Phase.IDLE;
        if (cue.phase == Phase.IDLE ? age % 8 != 0 : age % 2 != 0) return;
        Basis basis = basis(cue.phase == Phase.RELEASE ? cue.direction : cue.owner.getLookAngle());
        Vec3 eye = cue.phase == Phase.RELEASE ? cue.position : cue.owner.getEyePosition();
        // Approximate prop-side framing, not a bone/socket attachment. Always in front and off-axis.
        Vec3 center = eye.add(basis.forward.scale(.9)).add(basis.right.scale(.48)).add(basis.up.scale(-.45));
        List<H20VfxGeometry.Point> points;
        if (cue.phase == Phase.RELEASE || cue.phase == Phase.DISSOLVE) {
            points = H20VfxGeometry.release(age);
        } else {
            points = switch (cue.element) {
                case VOID -> H20VfxGeometry.bow(age, cue.phase == Phase.CHARGE ? cue.charge : 0,
                        cue.phase == Phase.FORM);
                case ARC -> H20VfxGeometry.staff(age);
                default -> H20VfxGeometry.gun(age);
            };
        }
        render(cue.owner, center, basis, points, cue.element, cue.phase == Phase.CHARGE ? .55f : .4f);
    }

    private static void arrowFrame(Cue cue) {
        Vec3 next = cue.arrow.position();
        if (!finite(next)) { cue.expires = 0; return; }
        Vec3 delta = next.subtract(cue.position);
        double length = delta.length();
        if (!Double.isFinite(length) || length > 8) { cue.position = next; return; }
        if (length > 1.0e-4) {
            Basis basis = basis(delta);
            // Six beads per tick maximum, alternating thin violet wake and pale split fletching.
            int samples = Math.min(4, Math.max(1, (int) Math.ceil(length / .65)));
            for (int i = 1; i <= samples; i++) {
                Vec3 point = cue.position.add(delta.scale(i / (double) samples));
                emit(cue.owner, point, Element.VOID, false, .45f);
            }
            emit(cue.owner, next.add(basis.right.scale(.09)), Element.VOID, true, .3f);
            emit(cue.owner, next.add(basis.right.scale(-.09)), Element.VOID, true, .3f);
        }
        cue.position = next;
    }

    private record Basis(Vec3 right, Vec3 up, Vec3 forward) { }
    private static final Basis WORLD = new Basis(new Vec3(1, 0, 0), new Vec3(0, 1, 0), new Vec3(0, 0, 1));

    private static Basis basis(Vec3 direction) {
        Vec3 forward = direction.normalize();
        Vec3 right = forward.cross(new Vec3(0, 1, 0));
        if (right.lengthSqr() < 1.0e-8) right = new Vec3(1, 0, 0);
        else right = right.normalize();
        return new Basis(right, right.cross(forward).normalize(), forward);
    }

    private static void render(ServerPlayer owner, Vec3 center, Basis basis,
                               List<H20VfxGeometry.Point> points, Element element, float size) {
        for (var point : points) emit(owner, center.add(basis.right.scale(point.right()))
                .add(basis.up.scale(point.up())).add(basis.forward.scale(point.forward())),
                element, point.bright(), size);
    }

    private static void emit(ServerPlayer owner, Vec3 position, Element element, boolean bright, float size) {
        if (!finite(position)) return;
        MinecraftServer server = owner.level().getServer();
        int now = server.getTickCount();
        if (budgetServer != server || budgetTick != now) {
            budgetServer = server;
            budgetTick = now;
            totalUsed = 0;
            USED.clear();
        }
        int used = USED.getOrDefault(owner.getUUID(), 0);
        if (used >= POINTS_PER_OWNER_TICK || totalUsed >= POINTS_TOTAL_TICK) return;
        USED.put(owner.getUUID(), used + 1);
        totalUsed++;
        // One deterministic particle at each authored point; no random cloud or force/long-distance send.
        AbilityParticles.send(owner, owner.level(), Fx.dust(bright ? element.glow() : element.color(), size),
                position.x, position.y, position.z, 1, 0, 0, 0, 0);
    }

    private static void add(Cue cue) {
        while (count(cue.owner) >= MAX_PER_OWNER) {
            for (int i = 0; i < CUES.size(); i++) if (CUES.get(i).owner == cue.owner) {
                CUES.remove(i);
                break;
            }
        }
        while (CUES.size() >= MAX_TOTAL) CUES.removeFirst();
        CUES.add(cue);
    }

    private static Cue equip(ServerPlayer owner) {
        return CUES.stream().filter(c -> c.owner == owner && c.kind == Kind.EQUIP).findFirst().orElse(null);
    }

    static void cancelOwned(ServerPlayer owner) { CUES.removeIf(c -> c.owner == owner); }
    static void cancelAnchor(ServerPlayer owner, Vec3 position) {
        CUES.removeIf(c -> c.owner == owner && c.kind == Kind.ANCHOR && c.position.equals(position));
    }
    static void clearAll() {
        CUES.clear();
        USED.clear();
        budgetServer = null;
        budgetTick = Integer.MIN_VALUE;
        totalUsed = 0;
    }
    static int count(ServerPlayer owner) { return (int) CUES.stream().filter(c -> c.owner == owner).count(); }
    static int particleCount(ServerPlayer owner) {
        return owner != null && budgetServer == owner.level().getServer()
                && budgetTick == budgetServer.getTickCount() ? USED.getOrDefault(owner.getUUID(), 0) : 0;
    }
    static List<SuperVfx.LifecycleSnapshot> snapshots() {
        return CUES.stream().map(c -> new SuperVfx.LifecycleSnapshot(c.owner.getUUID(), c.kind.name(),
                c.phase.name(), c.level.getServer().getTickCount() - c.born, c.expires)).toList();
    }
    private static boolean valid(ServerPlayer owner) {
        return owner != null && owner.isAlive() && !owner.isSpectator() && !owner.isRemoved() && !owner.hasDisconnected()
                && finite(owner.position()) && finite(owner.getLookAngle());
    }
    private static boolean finite(Vec3 p) {
        return p != null && Double.isFinite(p.x) && Double.isFinite(p.y) && Double.isFinite(p.z);
    }
}
