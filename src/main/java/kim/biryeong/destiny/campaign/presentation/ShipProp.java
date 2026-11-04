package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.ModelScaler;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

/**
 * The parked jumpship at Dock 13: owner-only BetterModel rg_ship, lit to a readable floor, idle loop,
 * engine glow parts off. Departure takes the live tracker over ({@link #takeOver}) so the player never
 * sees two ships; closing a taken-over prop is a no-op.
 */
final class ShipProp extends RisingPresentation.Scene {
    /** rg_ship is ~6.9 x 9 blocks at 1.0; Dock 13 hangar read too small in Vision r2 (d01). */
    static final float SCALE = 1.35f;
    static final int LIGHT_FLOOR = 13;

    private final Vec3 pos;
    private final float yaw;
    private DummyTracker ship;

    ShipProp(ServerPlayer player, Vec3 pos, float yaw) {
        super(player, null);
        this.pos = pos;
        this.yaw = yaw;
    }

    @Override void begin() {
        ship = spawn(player, pos, yaw);
        if (ship != null) {
            engines(ship, false);
            ship.animate("idle", new AnimationModifier(0, 0, AnimationIterator.Type.LOOP));
        }
    }

    @Override void update(int t, int now) { }

    /** Hands the live tracker to a departure; this handle becomes finished and owns nothing. */
    DummyTracker takeOver() {
        var s = ship;
        ship = null;
        complete();
        close();
        return s != null && !s.isClosed() ? s : null;
    }

    @Override void restore() {
        if (ship != null) { ship.close(); ship = null; }
    }

    /** Spawns a lit, scaled, owner-only rg_ship or null when the model is unavailable. */
    static DummyTracker spawn(ServerPlayer player, Vec3 pos, float yaw) {
        var renderer = BetterModel.model(RisingServices.Models.SHIP).orElse(null);
        if (renderer == null) {
            DestinyGuardians.LOGGER.warn("Guardian Rises: BetterModel rg_ship not loaded; no ship model");
            return null;
        }
        try {
            var tracker = renderer.create(ModLocation.of(player.level(), pos, 0, yaw));
            tracker.scaler(ModelScaler.value(SCALE));
            tracker.spawn(ModPlayer.of(player.connection));
            engines(tracker, false);
            return tracker;
        } catch (RuntimeException e) {
            DestinyGuardians.LOGGER.warn("Guardian Rises: rg_ship spawn failed", e);
            return null;
        }
    }

    /** Body at the light floor, lights_glow full bright, engine_*_glow shown full bright only when on. */
    static void engines(DummyTracker tracker, boolean on) {
        var body = TrackerUpdateAction.brightness(LIGHT_FLOOR, 15);
        var glow = TrackerUpdateAction.brightness(15, 15);
        var engine = on ? TrackerUpdateAction.composite(TrackerUpdateAction.togglePart(true), glow)
                : TrackerUpdateAction.togglePart(false);
        tracker.update(TrackerUpdateAction.perBone(bone -> {
            String n = bone.name().name();
            if (n.startsWith("engine") && n.endsWith("_glow")) return engine;
            return n.endsWith("_glow") ? glow : body;
        }));
    }
}
