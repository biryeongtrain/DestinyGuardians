package kim.biryeong.destiny.campaign;

import kim.biryeong.destiny.campaign.GuardianRisesProgress.Stage;
import kim.biryeong.destiny.campaign.RisingMission.Hint;
import kim.biryeong.destiny.activity.presentation.GuideRoute;
import kim.biryeong.destiny.activity.presentation.GuideTrail;
import kim.biryeong.destiny.activity.presentation.ObjectiveWaypoint;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.destiny.tutorial.Tutorial;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayDeque;
import java.util.Deque;

/**
 * Per-run objective HUD, lost-player guidance and fall recovery. The HUD reuses the tutorial tracker (left
 * panel, key prompt, stage toast); subtitles belong to the presentation service. Key labels follow the
 * existing GCB / non-GCB control split.
 *
 * <p>Guidance (original design, r2): while moving toward a place, a faint breadcrumb trail runs along the
 * zone's walkable route (routes.json) from the waypoint nearest the Guardian toward the objective, 0.3 m above
 * the floor, flowing forward; jump spots show rising sparks. 10 s without getting 3 blocks closer adds a
 * direction line; 25 s makes the trail dense, marks the target and gives one Ghost nudge. Without a route the
 * trail falls back to a straight 14 m line. Particles are sent to the owner only. Falling below the zone floor
 * returns the Guardian to the last safe ground; three falls within a minute use the stage anchor.
 */
public final class RisingObjectives {
    static final int WEAK_HINT = 20 * 10;
    static final int STRONG_HINT = 20 * 25;
    /** Soft trail: from 2 s into a stage, every 30 ticks, sparse. Strong trail: every 10 ticks, dense. */
    static final int SOFT_DELAY = 40, SOFT_PERIOD = 30, STRONG_PERIOD = 10;
    static final double FLOOR_MARGIN = 24;
    private static final int GHOST = 0x8FE3FF;
    /** Campaign-owned markers; cleared through {@link #clear(ServerPlayer)} on every campaign exit path. */
    private static final java.util.Map<java.util.UUID, ObjectiveWaypoint> WAYPOINTS = new java.util.HashMap<>();

    private Stage stage;
    private int stageAt;
    private RisingServices.Zone routeZone;
    private GuideRoute route;
    private double best = Double.MAX_VALUE;
    private int progressAt;
    private boolean weak, strong;
    private Vec3 safe;
    private final Deque<Integer> falls = new ArrayDeque<>();
    private int toastUntil;
    private String toastTitle, toastSub;
    private String lastNotice;
    private boolean shown;
    private int noticeUntil;

    /** Key prompt for a hint, honouring the GCB control scheme. Pure; returns {key, action} or null. */
    public static String[] keys(Hint hint, boolean gcb) {
        return switch (hint) {
            case NONE, WAIT -> null;
            case LOOK -> new String[]{"마우스", "주위를 둘러보기"};
            case MOVE -> new String[]{"W A S D", "이동 · Ctrl 질주 · Space 점프"};
            case GRAB -> new String[]{"이동", "가까이 다가가 집기"};
            case EQUIP_MENU -> new String[]{"E", "장비 설정 · 직업도 언제든 변경 가능"};
            case FIRE -> new String[]{gcb ? "좌클릭" : "우클릭", gcb ? "사격 · 우클릭 홀드 정조준" : "사격 · 좌클릭 정조준"};
            case AIM -> new String[]{gcb ? "우클릭 홀드" : "좌클릭", "정조준"};
            case RELOAD -> new String[]{"Q", "재장전"};
            case SWAP -> new String[]{"1 · 2 · 3", "무기 교체 · 산탄총은 특수탄"};
            case FIGHT -> new String[]{gcb ? "Z · C" : "F · Shift+좌클릭", "수류탄 · 근접 능력도 사용하세요"};
        };
    }

    /** Relative direction words for guidance. Pure for tests. */
    public static String direction(float playerYaw, Vec3 from, Vec3 to) {
        double dx = to.x - from.x, dz = to.z - from.z;
        double bearing = Math.toDegrees(Math.atan2(-dx, dz));
        double rel = ((bearing - playerYaw) % 360 + 540) % 360 - 180;
        String side = Math.abs(rel) <= 35 ? "앞쪽" : Math.abs(rel) >= 145 ? "뒤쪽" : rel > 0 ? "오른쪽" : "왼쪽";
        double dy = to.y - from.y;
        String vertical = dy > 4 ? " 위" : dy < -4 ? " 아래" : "";
        return side + vertical + " " + Math.round(Math.sqrt(dx * dx + dz * dz)) + "m";
    }

    public void toast(int now, String title, String sub) {
        toastTitle = title;
        toastSub = sub;
        toastUntil = now + 80;
    }

    public void notice(ServerPlayer p, int now, String text) {
        // Downed/cinematic: the Guardian Down HUD owns the screen; no Ghost guidance over it.
        if (kim.biryeong.destiny.campaign.presentation.RisingPresentation.hudHidden(p)) return;
        if (text.equals(lastNotice) && now < noticeUntil) return;
        lastNotice = text;
        noticeUntil = now + 60;
        p.sendOverlayMessage(Component.literal(text).withColor(GHOST));
    }

    /**
     * @param floorY lowest walkable Y of the current zone (from markers); below floorY - margin is a fall.
     * @param anchor stage anchor used after repeated falls (may be null)
     */
    public void tick(ServerPlayer p, RisingMission mission, int now, double floorY, Vec3 anchor) {
        tick(p, mission, now, floorY, anchor, null, null);
    }

    /** @param zone current zone and {@code origin} its placement origin, for the walkable guide route. */
    public void tick(ServerPlayer p, RisingMission mission, int now, double floorY, Vec3 anchor,
                     RisingServices.Zone zone, Vec3 origin) {
        if (zone != routeZone) {
            routeZone = zone;
            route = zone == null || origin == null ? null : RisingRoutes.world(zone, origin).orElse(null);
        }
        Stage current = mission.stage();
        var objective = mission.objective();
        if (current != stage) {
            if (stage != null && current != Stage.COMPLETE) toast(now, objective.chapter(), objective.title());
            stage = current;
            stageAt = now;
            best = Double.MAX_VALUE;
            progressAt = now;
            weak = strong = false;
        }
        // W301: Destiny-style waypoint over the destination of every travel step (hidden in cinematics/fights).
        boolean marker = !mission.placing() && !mission.finishing() && current != Stage.GHOST_SCAN && current != Stage.DEPARTURE
                && softGuide(objective.hint()) && now - stageAt >= 20
                && !kim.biryeong.destiny.campaign.presentation.RisingPresentation.hudHidden(p);
        var waypoint = WAYPOINTS.get(p.getUUID());
        if (waypoint != null && waypoint.owner() != p) { waypoint.clear(); waypoint = null; }
        if (waypoint == null && marker) WAYPOINTS.put(p.getUUID(), waypoint = new ObjectiveWaypoint(p));
        if (waypoint != null) waypoint.update(objective.target(), marker, now);
        if (mission.placing() || mission.finishing()) { progressAt = now; }
        else {
            guide(p, mission, objective, now);
            recover(p, now, floorY, anchor);
        }
        if (now % 4 == 0) render(p, mission, objective, now);
    }

    private void guide(ServerPlayer p, RisingMission mission, RisingMission.Objective objective, int now) {
        Vec3 target = objective.target();
        if (target == null) { progressAt = now; return; }
        double d = p.position().distanceTo(target);
        if (d < best - 3) { best = d; progressAt = now; weak = strong = false; }
        int lost = now - progressAt;
        // The on-screen waypoint marker already shows where to go: no text direction hints (user W303).
        if (lost >= WEAK_HINT && !weak) weak = true;
        boolean hidden = kim.biryeong.destiny.campaign.presentation.RisingPresentation.hudHidden(p);
        if (lost >= STRONG_HINT) {
            if (!strong) { strong = true; mission.lostCue(); }
            if (!hidden && now % STRONG_PERIOD == 0) trail(p, target, now, true);
        } else if (!hidden && softGuide(objective.hint()) && now - stageAt >= SOFT_DELAY && now % SOFT_PERIOD == 0) {
            trail(p, target, now, false);
        }
    }

    /** Places to walk to get the faint trail from the start; fights only get it once lost. */
    static boolean softGuide(Hint hint) {
        return hint == Hint.MOVE || hint == Hint.GRAB || hint == Hint.SWAP || hint == Hint.EQUIP_MENU;
    }

    private void trail(ServerPlayer p, Vec3 target, int now, boolean strong) {
        GuideTrail.draw(p, route, target, now, strong);
    }

    private void recover(ServerPlayer p, int now, double floorY, Vec3 anchor) {
        if (now % 10 == 0 && p.onGround() && !p.isInLiquid() && p.getY() > floorY - 2) safe = p.position();
        if (p.getY() >= floorY - FLOOR_MARGIN) return;
        while (!falls.isEmpty() && now - falls.peekFirst() > 20 * 60) falls.pollFirst();
        falls.addLast(now);
        Vec3 to = falls.size() >= 3 && anchor != null ? anchor : safe != null ? safe : anchor;
        if (to == null) return;
        if (falls.size() >= 3) falls.clear();
        p.teleportTo((ServerLevel) p.level(), to.x, to.y, to.z, java.util.Set.of(), p.getYRot(), p.getXRot(), true);
        p.resetFallDistance();
        p.setDeltaMovement(Vec3.ZERO);
        notice(p, now, "고스트: 조심해요! 안전한 곳으로 되돌려 놨어요.");
    }

    private void render(ServerPlayer p, RisingMission mission, RisingMission.Objective o, int now) {
        // Cinematics own the screen: no tracker during the opening scan or the departure.
        if (mission.stage() == Stage.GHOST_SCAN || mission.stage() == Stage.DEPARTURE || mission.finishing()
                || kim.biryeong.destiny.campaign.presentation.RisingPresentation.hudHidden(p)) {
            if (shown) { shown = false; clear(p); }
            return;
        }
        shown = true;
        var keys = keys(o.hint(), ClientControls.gcb(p));
        boolean compact = kim.biryeong.destiny.inventory.WeaponScreen.active(p);
        kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.render(p, new kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.View(
                "떠오르는 수호자", o.chapter(), o.title(), o.count(), o.goal(),
                keys == null ? null : keys[0], keys == null ? null : keys[1],
                now < toastUntil ? toastTitle : null, now < toastUntil ? toastSub : null, compact));
    }

    /** Choice prompt before entering the instance (class NONE). */
    public static void renderClassChoice(ServerPlayer p) {
        kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.render(p, new kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.View(
                "떠오르는 수호자", "수호자의 길", "당신은 어떤 수호자였나요?", 0, 1,
                "E", "타이탄 · 헌터 · 워록 — 장비에서 언제든 변경", null, null, false));
    }

    public static void renderLoading(ServerPlayer p, String line) {
        kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.render(p, new kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.View(
                "떠오르는 수호자", "준비 중", line, 0, 0, null, null, null, null, false));
    }

    public static void clear(ServerPlayer p) {
        kim.biryeong.destiny.campaign.presentation.ObjectiveTracker.remove(p);
        Tutorial.campaignHudClear(p);
        var waypoint = WAYPOINTS.remove(p.getUUID());
        if (waypoint != null) waypoint.clear();
    }
}
