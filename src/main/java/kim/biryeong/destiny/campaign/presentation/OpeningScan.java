package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.guardian.CharacterLoadouts;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import net.minecraft.world.entity.player.Input;
import kr.toxicity.model.api.animation.AnimationIterator;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.phys.Vec3;

/**
 * Opening of "A Guardian Rises" — original W300 staging (the extraction has no opening cinematic,
 * animation or first line; see docs/design/guardian-rises/presentation.md).
 *
 * <pre>
 *  t   0  darkness: blackout grade, blindness fog, hidden HUD, movement locked; view tilted up (lying low)
 *  (W300 r12: intro tightened so blackout → scan is under ~5 s including the Gateway build)
 *  t   6  a single cyan light: the Ghost transmats in above the Guardian (only its eye passes the key)
 *  t  14  [authored subtitle] "…찾았어요. 드디어."
 *  t  22  shell opens
 *  t  30  scan: cold grade + screen sweep band; light fan sweeps the body head to toe (1 s passes, ~5x),
 *         heartbeat (vanilla warden heartbeat, 60 bpm) on the shader's lub beat
 *  t 126  CHOOSE (timeline frozen): the scan grade drops, the Ghost asks [authored] "당신은… 누구입니까?" and three
 *         class cards rise (W301 {@link ClassCardHud}: emblem, role, blurb, class ability); A/D moves the highlight,
 *         Space confirms (auto-confirm after 45 s); the chosen card flashes, the others drop, ~1.5 s outro
 *  +6     after the outro: blackout again, [authored] "움직이지 마세요. 당신의 빛을 되돌려 놓을게요."
 *  +6     [80b779f0] "가만히 있어요." then [80b779ee] "수호자… 수호자? 눈을 뜨세요, 수호자!" over the darkness
 *  t 224  darkness again, revive whoosh builds
 *  t 260  bloom: revive grade, letterbox bars slide in, view eases from the low angle to the Ghost
 *  W301 wake-up cinematic (video 08:52–09:34), staged per spoken line, movement still locked:
 *         ef 성공이야 (Ghost closes in) · e7 찾아 헤맸어요 (drifts aside) · ec 전 고스트예요 (in front, shell open) ·
 *         class pair 54/56/58 + 53/59/5e · ea 몰락자의 영역 (Ghost flies toward the wall, camera pans there) ·
 *         eb 도시로 (Ghost returns) · e9 사라진 거 아니니까… 움직여야 해요 (transmat flicker, to the shoulder,
 *         camera looks down the road) → bars out, HUD back, control returned; Gateway lines (64/60) follow
 * </pre>
 */
final class OpeningScan extends RisingPresentation.Scene {
    static final int GHOST_IN = 6, FOUND = 14, SHELL = 22, SCAN = 30, SCAN_TICKS = 96, CHOOSE = SCAN + SCAN_TICKS,
            WAKE_LINE = CHOOSE + 6, DARK_AGAIN = CHOOSE + 76, BLOOM = DARK_AGAIN + 36, BLOOM_END = BLOOM + 14,
            SPEAK = BLOOM + 16, GLIDE_TICKS = 30, COMBAT_HUD_DELAY = 14, EASE = 30;
    static final int CHOICE_TIMEOUT = 20 * 45;
    /** 성공이야… / 정말 오랫동안… / 전 고스트예요… */
    static final java.util.List<String> OPENING_LINES_BEFORE_CLASS = java.util.List.of("80b779ef", "80b779e7", "80b779ec");
    /** 여긴 몰락자의 영역이에요… / 당신을 도시로 데려가야 해요. / 사라진 거 아니니까… 이제 움직여야 해요. */
    static final java.util.List<String> OPENING_LINES_AFTER_CLASS = java.util.List.of("80b779ea", "80b779eb", "80b779e9");

    /** A/D class picker shown while the Ghost waits in the dark. Pure state; rendering lives in the scene. */
    static final class ClassChoice {
        static final GuardianClass[] ORDER = {GuardianClass.TITAN, GuardianClass.HUNTER, GuardianClass.WARLOCK};
        int index;
        boolean confirmed;
        private Input prev;

        ClassChoice(GuardianClass current, Input held) {
            int i = java.util.Arrays.asList(ORDER).indexOf(current);
            index = i < 0 ? 1 : i;
            prev = held == null ? Input.EMPTY : held; // keys already held when the prompt opens do not count
        }

        GuardianClass selected() { return ORDER[index]; }

        /** Feeds one input sample; returns true when the highlighted class changed. Space confirms. */
        boolean step(Input in) {
            if (in == null) in = Input.EMPTY;
            boolean moved = false;
            if (!confirmed) {
                if (in.left() && !prev.left()) { index = (index + ORDER.length - 1) % ORDER.length; moved = true; }
                if (in.right() && !prev.right()) { index = (index + 1) % ORDER.length; moved = true; }
                if (in.jump() && !prev.jump()) confirmed = true;
            }
            prev = in;
            return moved;
        }
    }

    private int paused, choiceStart = -1;
    private ClassChoice choice;
    private ClassCardHud cards;
    private boolean applied;

    private final Vec3 eye;
    private final float yaw0;
    private final Vec3 ghostStart, ghostSettle, ghostAside;
    private RisingPresentation.Lock lock;
    private boolean blinded;
    private float easeYaw, easePitch, scanPitch;

    OpeningScan(ServerPlayer player, Vec3 guardianEye, Runnable done) { this(player, guardianEye, null, done); }

    OpeningScan(ServerPlayer player, Vec3 guardianEye, Vec3 vista, Runnable done) {
        super(player, done);
        Vec3 actual = player.getEyePosition();
        // The director passes the Guardian's eye; trust the live eye if the marker is stale.
        eye = guardianEye != null && guardianEye.distanceToSqr(actual) < 2.25 ? guardianEye : actual;
        yaw0 = player.getYRot();
        double r = Math.toRadians(yaw0);
        Vec3 forward = new Vec3(-Math.sin(r), 0, Math.cos(r));
        Vec3 right = new Vec3(-Math.cos(r), 0, -Math.sin(r));
        ghostStart = eye.add(forward.scale(1.35)).add(0, .72, 0);
        ghostSettle = eye.add(forward.scale(1.25)).add(right.scale(.55)).add(0, .1, 0);
        // While the cards are up the Ghost waits just behind the Guardian's shoulder (display entities are
        // not depth-sorted against the shell, so a Ghost in front would show through the translucent cards).
        ghostAside = eye.add(forward.scale(-1.1)).add(right.scale(.6)).add(0, .35, 0);
        this.forward = forward;
        this.right = right;
        // Without a marker the Ghost points out the way ahead (spawn facing).
        this.vista = vista != null && vista.distanceToSqr(eye) > 9 ? vista : eye.add(forward.scale(30));
    }

    // ---------------------------------------------------------------- W301 wake-up cinematic (video 08:52–09:34)
    private final Vec3 forward, right, vista;
    private Vec3 camTarget;
    private boolean followGhostCam = true, seenLast;
    private int tNow, dissolveAt = -1;
    private Vec3 road;
    private String lastLine;
    private int outroAt = -1;
    private Letterbox bars;
    static final String LAST_LINE = "80b779e9";
    static final int MONOLOGUE_TIMEOUT = 20 * 75;

    /** Staging per wake-up line: where the Ghost goes and what the camera watches while it is spoken. */
    private void beat(String line, GhostCompanion g) {
        Vec3 toVista = vista.subtract(eye).multiply(1, 0, 1);
        toVista = toVista.lengthSqr() < 1e-4 ? forward : toVista.normalize();
        Vec3 vRight = new Vec3(-toVista.z, 0, toVista.x);
        switch (line) {
            case "80b779ef" -> { // 성공이야… 깨어나셨네요! — closes in, delighted
                g.hold(eye.add(forward.scale(1.15)).add(right.scale(.15)).add(0, .08, 0), eye);
                g.play("look", AnimationIterator.Type.PLAY_ONCE);
                followGhostCam = true;
            }
            case "80b779e7" -> // 정말 오랫동안 당신을 찾아 헤맸어요. — drifts aside, still facing you
                g.hold(eye.add(forward.scale(1.45)).add(right.scale(.55)).add(0, .28, 0), eye);
            case "80b779ec" -> { // 전 고스트예요… 이젠 당신의 고스트예요… — right in front, shell open
                g.hold(eye.add(forward.scale(.95)).add(0, .02, 0), eye);
                g.play("shell_open", AnimationIterator.Type.HOLD_ON_LAST);
            }
            case "80b75f54", "80b75f56", "80b75f58" -> { // class line — settles back, shell closed
                g.play("shell_close", AnimationIterator.Type.PLAY_ONCE);
                g.hold(eye.add(forward.scale(1.35)).add(right.scale(-.35)).add(0, .18, 0), eye);
            }
            case "80b779ea" -> { // 여긴 몰락자의 영역이에요 — flies out toward the wall; the camera follows the gesture
                g.hold(eye.add(toVista.scale(2.6)).add(vRight.scale(.6)).add(0, .7, 0), vista);
                followGhostCam = false;
                camTarget = vista;
            }
            case "80b779eb" -> { // 당신을 도시로 데려가야 해요 — comes back between you and the way out
                g.hold(eye.add(toVista.scale(1.3)).add(vRight.scale(.45)).add(0, .15, 0), eye);
                followGhostCam = true;
            }
            case LAST_LINE -> { // 사라진 거 아니니까… 이제 움직여야 해요 — dissolves into the Guardian while saying it
                g.hold(eye.add(toVista.scale(2.5)).add(vRight.scale(.55)).add(0, .2, 0), eye);
                followGhostCam = true;
                dissolveAt = tNow + 14;
                road = eye.add(toVista.scale(12)).add(0, .3, 0);
                seenLast = true;
            }
            default -> { }
        }
    }

    /** Eases the view toward the current subject (soft handheld lag, never snapping). */
    private void camera(float k) {
        Vec3 subject = followGhostCam ? ghost().map(GhostCompanion::position).orElse(camTarget) : camTarget;
        if (subject == null) return;
        float yaw = RisingPresentation.yawTo(eye, subject), pitch = RisingPresentation.pitchTo(eye, subject) + (followGhostCam ? 3f : 0f);
        float cy = player.getYRot(), cp = player.getXRot();
        RisingPresentation.look(player, cy + wrap(yaw - cy) * k, cp + (pitch - cp) * k);
    }

    @Override void begin() {
        RisingPresentation.clearArrival(player);
        RisingPresentation.closeCurtains(player);
        lock = RisingPresentation.lock(player);
        lock.hideHud(true);
        RisingPresentation.post(player, RisingPresentation.BLACKOUT);
        // Indefinite: the class choice pauses the timeline; the bloom removes it.
        player.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, MobEffectInstance.INFINITE_DURATION, 0, false, false, false));
        blinded = true;
        // Low angle: the Guardian looks up from the ground at where the light will appear.
        RisingPresentation.look(player, RisingPresentation.yawTo(eye, ghostStart), RisingPresentation.pitchTo(eye, ghostStart));
        GhostCompanion.existing(player).ifPresent(GhostCompanion::destroy);
    }

    @Override void update(int raw, int now) {
        int t = raw - paused;
        if (choice != null && cards != null) {
            heartbeat(t);
            choose(now);
            paused++;
            return;
        }
        heartbeat(t);
        if (t == GHOST_IN) {
            var g = GhostCompanion.ensure(player, ghostStart);
            g.hold(ghostStart, eye);
            g.play("transmat", AnimationIterator.Type.PLAY_ONCE);
            RisingAudio.sfx(player, "transmat", .55f, 1.1f);
        }
        if (t == FOUND) RisingAudio.voice(player, "rg.opening.found");
        if (t == SHELL) ghost().ifPresent(g -> g.play("shell_open", AnimationIterator.Type.HOLD_ON_LAST));
        if (t == SCAN) {
            kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[GuardianRises] opening scan start ({} ticks after scene start)", t);
            RisingPresentation.post(player, RisingPresentation.SCAN);
            // W301: one slow pass from just above the head down to the feet (was 1 s loops that read as
            // "middle to bottom" from the low first-person angle); the camera tilts down with the light.
            double top = eye.y + .3, feet = player.getY();
            Vec3 body = new Vec3(player.getX(), (top + feet) * .5, player.getZ());
            ghost().ifPresent(g -> g.scanOnce(body, ghostStart, SCAN_TICKS - 8, .8, top - feet, .75));
            scanPitch = player.getXRot();
            RisingAudio.sfx(player, "scan_loop", .9f, 1f);
        }
        if (t == SCAN + 64) RisingAudio.sfx(player, "scan_loop", .75f, 1f);
        if (t > SCAN && t < CHOOSE) ghost().ifPresent(g -> {
            // Camera follows the sweep line down the body with a soft lag (clamped so it never looks straight down).
            Vec3 line = g.sweepPoint(now, 0);
            float want = Math.clamp(RisingPresentation.pitchTo(eye, line) - 6f, -40f, 62f);
            scanPitch += (want - scanPitch) * .18f;
            RisingPresentation.look(player, yaw0, scanPitch);
        });
        if (t == CHOOSE && choice == null) {
            // Scan done: the light goes out and the Ghost, still hovering over the body, asks who this was.
            ghost().ifPresent(g -> g.hold(ghostStart, eye));
            // The luminance-keyed blackout would key the cards out too: drop every grade; blindness + the
            // cards' own vignette keep the world dark while the picker is up.
            RisingPresentation.post(player, null);
            player.connection.send(new net.minecraft.network.protocol.game.ClientboundStopSoundPacket(
                    RisingAudio.sfxId("scan_loop"), null));
            // rg.opening.who is shown as the card header (W301); no action-bar copy over the cards.
            choice = new ClassChoice(Guardians.data(player).guardianClass(), player.getLastClientInput());
            choiceStart = now;
            cards = new ClassCardHud(player, now);
            cards.tick(now, choice.index, false);
            ghost().ifPresent(g -> g.hold(ghostAside, eye));
            RisingAudio.vanilla(player, "block.beacon.activate", .45f, 1.7f);
            kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[GuardianRises] opening class choice open (current {})", choice.selected());
            paused++;
            return;
        }
        if (t == WAKE_LINE) {
            // W301: extracted c104b opening (Rising-Guardian-Ghost-Opening-KO-2026-11-02). "가만히 있어요." before the
            // revive, then "수호자… 수호자? 눈을 뜨세요, 수호자!" carried over the darkness into the bloom.
            RisingAudio.voice(player, "80b779f0");
            RisingAudio.voice(player, "80b779ee");
        }
        if (t == DARK_AGAIN) RisingAudio.sfx(player, "revive", 1f, 1f); // whoosh peaks into its chord 36 ticks later (BLOOM)
        if (t == BLOOM) {
            RisingPresentation.post(player, RisingPresentation.REVIVE);
            if (blinded) { player.removeEffect(MobEffects.BLINDNESS); blinded = false; }
            ghost().ifPresent(g -> {
                g.hold(ghostSettle, eye);
                g.play("look", AnimationIterator.Type.PLAY_ONCE);
            });
            easeYaw = player.getYRot();
            easePitch = player.getXRot();
        }
        if (t == BLOOM) {
            bars = new Letterbox(player);
            camTarget = ghostSettle;
        }
        tNow = t;
        if (dissolveAt >= 0 && t == dissolveAt) ghost().ifPresent(GhostCompanion::dissolve);
        if (dissolveAt >= 0 && t == dissolveAt + GhostCompanion.DISSOLVE_TICKS - 6) { followGhostCam = false; camTarget = road; }
        if (t > BLOOM + EASE && outroAt < 0) {
            String line = RisingAudio.current(player);
            if (line != null && !line.equals(lastLine)) {
                lastLine = line;
                ghost().ifPresent(g -> beat(line, g));
            }
            camera(followGhostCam ? .10f : .06f);
            boolean finished = seenLast && !LAST_LINE.equals(line) || t > BLOOM + MONOLOGUE_TIMEOUT;
            if (finished) {
                outroAt = t;
                if (!seenLast) ghost().ifPresent(GhostCompanion::dissolve);
                bars.close(10);
            }
        }
        if (bars != null) bars.tick();
        if (outroAt >= 0 && t > outroAt && t < outroAt + 8) camera(.2f);
        if (outroAt >= 0 && t == outroAt + 6) {
            RisingPresentation.holdHud(player, COMBAT_HUD_DELAY);
            lock.hideHud(false);
        }
        if (outroAt >= 0 && t == outroAt + 12) {
            complete();
            close();
        }
        if (t > BLOOM && t <= BLOOM + EASE) {
            // Vision returns: ease out of the low angle onto the settling Ghost's eye line.
            float u = (t - BLOOM) / (float) EASE;
            float s = u * u * (3 - 2 * u);
            float yaw = RisingPresentation.yawTo(eye, ghostSettle), pitch = RisingPresentation.pitchTo(eye, ghostSettle) + 4f;
            RisingPresentation.look(player, easeYaw + wrap(yaw - easeYaw) * s, easePitch + (pitch - easePitch) * s);
        }
        if (t == BLOOM_END) RisingPresentation.removePosts(player, RisingPresentation.REVIVE);
        if (t == SPEAK) {
            RisingAudio.ambient(player, true);
            // W301: the D2 wake-up monologue (c104b 0010..0070, video 08:58–09:34) with the chosen class pair
            // (54/56/58 + 53/59/5e) after "you've been dead a long time"; it keeps playing once the player moves.
            GuardianClass cls = Guardians.data(player).guardianClass();
            for (String id : OPENING_LINES_BEFORE_CLASS) RisingAudio.voice(player, id);
            classLine(cls, false);
            classLine(cls, true);
            for (String id : OPENING_LINES_AFTER_CLASS) RisingAudio.voice(player, id);
        }
    }

    private void choose(int now) {
        boolean moved = !choice.confirmed && choice.step(player.getLastClientInput());
        if (!choice.confirmed && now - choiceStart >= CHOICE_TIMEOUT) choice.confirmed = true;
        if (moved) {
            RisingAudio.vanilla(player, "block.amethyst_block.chime", .7f, 1.25f + choice.index * .12f);
            RisingAudio.vanilla(player, "ui.button.click", .25f, 1.6f);
        }
        cards.tick(now, choice.index, choice.confirmed);
        if (choice.confirmed && !applied) {
            applied = true;
            GuardianClass picked = choice.selected();
            String error = CharacterLoadouts.selectClass(player, picked);
            if (error != null) kim.biryeong.destiny.DestinyGuardians.LOGGER.warn("[GuardianRises] opening class {} failed: {}", picked, error);
            RisingAudio.vanilla(player, "block.beacon.power_select", .8f, 1.3f);
            RisingAudio.vanilla(player, "block.amethyst_block.resonate", .9f, 1.1f);
            kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[GuardianRises] opening class chosen: {} ({})",
                    picked, error == null ? "applied" : error);
        }
        if (applied && cards.done(now)) {
            cards.close();
            cards = null;
            RisingPresentation.post(player, RisingPresentation.BLACKOUT);
            ghost().ifPresent(g -> {
                g.hold(ghostStart, eye);
                g.play("look", AnimationIterator.Type.PLAY_ONCE);
            });
        }
    }

    private java.util.Optional<GhostCompanion> ghost() { return GhostCompanion.existing(player); }

    /** Lub-dub on the rg_scan beat (client game time % 20 == 0, 60 bpm), rising as the scan proceeds. */
    private void heartbeat(int t) {
        if (t < 8 || t >= BLOOM) return;
        if (Math.floorMod(RisingPresentation.clientTime(player.level()), 20) != 0) return;
        float k = Math.min(1f, t / (float) BLOOM);
        RisingAudio.vanilla(player, "entity.warden.heartbeat", .35f + .55f * k, .82f);
    }

    /** Extracted class pair: intro (54 Titan / 56 Hunter / 58 Warlock) and its follow-up (53 / 59 / 5e). */
    static String classLineId(GuardianClass cls, boolean followUp) {
        return switch (cls) {
            case TITAN -> followUp ? "80b75f53" : "80b75f54";
            case HUNTER -> followUp ? "80b75f59" : "80b75f56";
            case WARLOCK -> followUp ? "80b75f5e" : "80b75f58";
            case NONE -> followUp ? null : "80b75f5c";
        };
    }

    private void classLine(GuardianClass cls, boolean followUp) {
        String id = classLineId(cls, followUp);
        if (id != null) RisingAudio.voice(player, id);
    }

    private static float wrap(float degrees) {
        degrees %= 360f;
        if (degrees > 180f) degrees -= 360f;
        if (degrees < -180f) degrees += 360f;
        return degrees;
    }

    @Override void restore() {
        if (cards != null) { cards.close(); cards = null; }
        if (bars != null) { bars.remove(); bars = null; }
        RisingPresentation.removePosts(player, RisingPresentation.BLACKOUT, RisingPresentation.SCAN, RisingPresentation.REVIVE);
        if (blinded && !player.hasDisconnected()) player.removeEffect(MobEffects.BLINDNESS);
        blinded = false;
        if (lock != null) { RisingPresentation.unlock(lock); lock = null; }
        if (!finished && !player.hasDisconnected()) {
            player.connection.send(new net.minecraft.network.protocol.game.ClientboundStopSoundPacket(RisingAudio.sfxId("scan_loop"), null));
            player.connection.send(new net.minecraft.network.protocol.game.ClientboundStopSoundPacket(RisingAudio.sfxId("revive"), null));
            GhostCompanion.existing(player).ifPresent(GhostCompanion::follow);
        }
    }

    /** Cinematic letterbox: two black bars that slide in at the bloom and out when control returns. */
    static final class Letterbox {
        static final float BAR = 118;
        private final ServerPlayer player;
        private int closeIn = -1;
        private boolean removed;

        Letterbox(ServerPlayer player) {
            this.player = player;
            bar("top", 0, 0, 0);
            bar("bottom", 1080, 0, 0);
            pending = 2;
        }

        private int pending;

        void tick() {
            if (removed) return;
            if (pending > 0 && --pending == 0) { bar("top", 0, BAR, 18); bar("bottom", 1080, BAR, 18); }
            if (closeIn > 0 && --closeIn == 0) remove();
        }

        void close(int ticks) {
            if (removed || closeIn > 0) return;
            bar("top", 0, 0, ticks);
            bar("bottom", 1080, 0, ticks);
            closeIn = ticks + 1;
        }

        void remove() {
            if (removed) return;
            removed = true;
            if (!player.hasDisconnected()) for (String k : new String[]{"top", "bottom"})
                kim.biryeong.minigamelib.displayhud.DisplayHud.removeHud(player, "destiny:rg_letterbox_" + k);
        }

        /** edge = 0 (top) or 1080 (bottom); the bar grows from that edge to {@code h} reference pixels. */
        private void bar(String key, float edge, float h, int time) {
            String id = "destiny:rg_letterbox_" + key;
            var existing = kim.biryeong.minigamelib.displayhud.DisplayHud.getHud(player, id);
            var hud = existing instanceof kim.biryeong.minigamelib.displayhud.ItemDisplayHud item ? item
                    : new kim.biryeong.minigamelib.displayhud.ItemDisplayHud();
            hud.updateWhenDataChanged(false);
            if (existing == null) {
                var stack = new net.minecraft.world.item.ItemStack(net.minecraft.world.item.Items.PAPER);
                stack.set(net.minecraft.core.component.DataComponents.ITEM_MODEL,
                        net.minecraft.resources.Identifier.fromNamespaceAndPath("destiny", "gui/hud/solid"));
                stack.set(net.minecraft.core.component.DataComponents.CUSTOM_MODEL_DATA,
                        new net.minecraft.world.item.component.CustomModelData(java.util.List.of(), java.util.List.of(), java.util.List.of(), java.util.List.of(0x000000)));
                hud.setItem(stack);
                hud.setItemTransform(net.minecraft.world.item.ItemDisplayContext.NONE);
                hud.setAlignment(kim.biryeong.minigamelib.displayhud.DisplayHud.HudAlignment.CENTER);
                hud.setViewRange(1000);
                hud.setAboveHand(true);
            }
            float height = Math.max(.01f, h);
            float y = edge == 0 ? height / 2 : 1080 - height / 2;
            hud.setScale(2400, height, 1, time);
            hud.setLocation(960, y, 200, time);
            if (existing == null) hud.spawn(player, id);
            hud.updateWhenDataChanged(true);
            hud.update();
        }
    }
}
