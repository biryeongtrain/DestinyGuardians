package kim.biryeong.destiny.campaign.fallen;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.EntityAttachment;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.TextColor;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * Destiny-style floating enemy health bar (W300 r4, original design). A billboarded stack of Polymer text
 * displays above the enemy: small name, then a thin bar drawn as three adjacent coloured rectangles
 * (fill | white trail of recent loss | dark empty). Captains add a shield row; the Walker adds four leg-armour pips
 * while armoured. Rectangles are single-space text displays whose background is the colour, scaled to width, so
 * the bar is continuous (no glyph gaps) and needs no resource-pack assets.
 * Visibility/trail logic lives in {@link HealthBarModel}; elements exist only while the bar is visible and are
 * changed only when the quantized frame changes. Destroyed on death/removal (the holder is client-only state).
 */
final class FallenHealthBars {
    enum Tier {
        // width x height in blocks; nameHeight = rendered height of one text line (9 font px) in blocks.
        NORMAL(0xE5463B, .9, .06, .18), ELITE(0xF0913A, 1.1, .07, .18), BOSS(0xF2D24B, 3.0, .12, .24);
        final int color; final double width, height, nameHeight; final float nameScale;
        Tier(int color, double width, double height, double nameHeight) {
            this.color = color; this.width = width; this.height = height; this.nameHeight = nameHeight;
            this.nameScale = (float) (nameHeight / (LINE_PX * PX));
        }
    }

    static final int TRAIL = 0xF4F4F4, EMPTY = 0x262626, SHIELD = 0x7FD8FF, SHIELD_EMPTY = 0x1E2A30,
            PIP = 0xD9B44A, PIP_EMPTY = 0x3A1E1A;
    /*
     * Exact vanilla 26.3 geometry (DisplayRenderer.TextDisplayRenderer.submitInner, javap-verified):
     *   pose.rotate(PI, Y); pose.scale(-0.025); w = Font.width(text); h = lines*(9+1)-1;
     *   pose.translate(1 - w/2, -h, 0); submitTextBackground(-1, -1, w, h).
     * For " " (default-font space advance 4): font-px x in [-1,4] -> [-2,3], y in [-1,9] -> [-10,0].
     * After R(PI,Y)*S(-0.025): local x = 0.025*x, local y = -0.025*y. So with display scale (sx, sy):
     *   x in [tx - 0.05*sx, tx + 0.075*sx]  (width 0.125*sx, left edge at tx - 0.4*width),
     *   y in [ty, ty + 0.25*sy]             (bottom at the translation).
     * r4 used 0.15 for the width, so every rectangle was 17% narrow around a wrong centre -> gaps.
     */
    static final double PX = 0.025, SPACE_PX = 4, LINE_PX = 9;
    static final double BASE_W = (SPACE_PX + 1) * PX, BASE_H = (LINE_PX + 1) * PX;
    /** Fraction of the rendered width left of the translation point (2 of 5 px). */
    static final double LEFT_FRACTION = 2 / (SPACE_PX + 1);

    /** Display translation-x / scale for a background rectangle spanning [x0, x1] blocks (bar-centred). */
    record Span(float translationX, float scaleX, float scaleY) {
        double renderedLeft() { return translationX - LEFT_FRACTION * BASE_W * scaleX; }
        double renderedRight() { return renderedLeft() + BASE_W * scaleX; }
    }

    static Span span(double x0, double x1, double height) {
        double w = x1 - x0;
        if (w < 1e-4 || height <= 0) return new Span(0, 0, 0);
        double sx = w / BASE_W;
        return new Span((float) (x0 + LEFT_FRACTION * w), (float) sx, (float) (height / BASE_H));
    }
    static final double SIGHT_RANGE = 20, SIGHT_COS = Math.cos(Math.toRadians(9));

    private final FallenMob mob;
    private final Tier tier;
    private final HealthBarModel model = new HealthBarModel();
    private ElementHolder holder;
    private TextDisplayElement name, fill, trail, empty, shieldFill, shieldEmpty;
    private final TextDisplayElement[] pipFill = new TextDisplayElement[4], pipEmpty = new TextDisplayElement[4];
    private HealthBarModel.Frame shown;
    private final int[] shownPips = {-1, -1, -1, -1};
    private boolean inSight, closed;

    FallenHealthBars(FallenMob mob) {
        this.mob = mob;
        this.tier = switch (mob.fallenKind()) {
            case CAPTAIN -> Tier.ELITE;
            case WALKER -> Tier.BOSS;
            default -> Tier.NORMAL;
        };
    }

    static Tier tierOf(FallenKind kind) {
        return switch (kind) { case CAPTAIN -> Tier.ELITE; case WALKER -> Tier.BOSS; default -> Tier.NORMAL; };
    }

    void tick(ServerLevel level) {
        if (closed) return;
        long now = level.getServer().getTickCount();
        var walker = mob.walker();
        double hp = walker != null ? walker.machine().coreFraction() : mob.getHealth() / Math.max(1e-6, mob.getMaxHealth());
        double shieldMax = mob.archetype().shield();
        double sh = walker == null && shieldMax > 0 ? mob.getAbsorptionAmount() / shieldMax : 0;
        model.update(now, hp, sh);
        boolean boss = walker != null;
        if (!boss && mob.tickCount % 5 == 0) inSight = sighted(level);
        boolean alive = mob.isAlive() && !mob.isDeadOrDying() && (!boss || mob.active());
        if (!model.visible(now, inSight, boss, alive)) { hide(); return; }
        show();
        render(walker);
    }

    void touched(long now) { model.touched(now); }

    private boolean sighted(ServerLevel level) {
        Vec3 c = mob.position().add(0, mob.getBbHeight() * .6, 0);
        for (ServerPlayer p : level.players()) {
            if (p.isSpectator() || !p.isAlive()) continue;
            Vec3 eye = p.getEyePosition(), look = p.getLookAngle();
            if (!HealthBarModel.inSight(c.x - eye.x, c.y - eye.y, c.z - eye.z, look.x, look.y, look.z, SIGHT_RANGE, SIGHT_COS))
                continue;
            if (FallenBrain.clearPath(level, eye, c)) return true;
        }
        return false;
    }

    private double top() {
        return mob.walker() != null ? 6.6 : mob.getBbHeight() + .5;
    }

    private TextDisplayElement rect(int rgb) {
        var e = new TextDisplayElement(Component.literal(" "));
        e.setBackground(0xFF000000 | rgb);
        e.setDefaultBackground(false);
        e.setShadow(false);
        e.setSeeThrough(false);
        e.setBillboardMode(Display.BillboardConstraints.CENTER);
        e.setBrightness(new Brightness(15, 15));
        e.setOffset(new Vec3(0, top(), 0));
        e.setScale(new Vector3f(0, 0, 0));
        holder.addElement(e);
        return e;
    }

    private void show() {
        if (holder != null) return;
        holder = new ElementHolder();
        name = new TextDisplayElement(Component.literal(mob.getName().getString())
                .withStyle(s -> s.withColor(TextColor.fromRgb(0xEDEDED))));
        name.setBackground(0);
        name.setDefaultBackground(false);
        name.setShadow(true);
        name.setBillboardMode(Display.BillboardConstraints.CENTER);
        name.setBrightness(new Brightness(15, 15));
        name.setOffset(new Vec3(0, top(), 0));
        name.setScale(new Vector3f(tier.nameScale, tier.nameScale, tier.nameScale));
        // Bottom of the name line sits a small gap above the bar (or the shield row).
        double nameBottom = tier.height + .03 + (mob.archetype().shield() > 0 && mob.walker() == null ? tier.height * .9 : 0);
        // Text glyphs start at 1 - w/2 font px, i.e. centred 1 px right: shift back by one scaled pixel.
        name.setTranslation(new Vector3f((float) (-PX * tier.nameScale), (float) nameBottom, 0));
        holder.addElement(name);
        fill = rect(tier.color);
        trail = rect(TRAIL);
        empty = rect(EMPTY);
        if (mob.archetype().shield() > 0 && mob.walker() == null) {
            shieldFill = rect(SHIELD);
            shieldEmpty = rect(SHIELD_EMPTY);
        }
        if (mob.walker() != null) for (int i = 0; i < 4; i++) { pipFill[i] = rect(PIP); pipEmpty[i] = rect(PIP_EMPTY); }
        EntityAttachment.ofTicking(holder, mob);
        shown = null;
        java.util.Arrays.fill(shownPips, -1);
    }

    private void hide() {
        if (holder == null) return;
        holder.destroy();
        holder = null;
        name = fill = trail = empty = shieldFill = shieldEmpty = null;
        java.util.Arrays.fill(pipFill, null);
        java.util.Arrays.fill(pipEmpty, null);
        shown = null;
    }

    void close() {
        closed = true;
        hide();
    }

    private void render(WalkerBoss.Runtime walker) {
        var frame = model.frame();
        double w = tier.width, h = tier.height;
        if (!frame.equals(shown)) {
            shown = frame;
            double f = frame.fill() / (double) HealthBarModel.RESOLUTION, t = frame.trail() / (double) HealthBarModel.RESOLUTION;
            place(fill, 0, f, 0, h);
            place(trail, f, t, 0, h);
            place(empty, t, 1, 0, h);
            if (shieldFill != null) {
                double s = frame.shield() / (double) HealthBarModel.RESOLUTION;
                place(shieldFill, 0, s, h * 1.25, h * .55);
                place(shieldEmpty, s, 1, h * 1.25, h * .55);
            }
        }
        if (walker != null) {
            var m = walker.machine();
            boolean armored = m.phase() == WalkerBoss.Phase.ARMORED;
            double gap = w * .03, pw = (1 - 3 * gap / w) / 4;
            for (int i = 0; i < 4; i++) {
                int q = armored ? (int) Math.round(m.leg(WalkerBoss.Region.values()[i]) / m.tuning().legArmor() * 20) : -2;
                if (q == shownPips[i]) continue;
                shownPips[i] = q;
                double x0 = i * (pw + gap / w);
                if (q < 0) { place(pipFill[i], 0, 0, 0, 0); place(pipEmpty[i], 0, 0, 0, 0); continue; }
                double pf = q / 20.0;
                place(pipFill[i], x0, x0 + pw * pf, -h * 1.4, h * .55);
                place(pipEmpty[i], x0 + pw * pf, x0 + pw, -h * 1.4, h * .55);
            }
        }
    }

    /**
     * Places a rectangle spanning bar-relative [from, to] (0..1 of the bar width), bottom at {@code y} (blocks,
     * billboard space) and {@code height} tall. Zero width collapses it (scale 0) instead of removing it.
     */
    private void place(TextDisplayElement e, double from, double to, double y, double height) {
        if (e == null) return;
        double width = tier.width;
        double x0 = Math.max(0, Math.min(1, from)) * width - width / 2, x1 = Math.max(0, Math.min(1, to)) * width - width / 2;
        var sp = span(x0, x1, height);
        if (sp.scaleX() == 0) { e.setScale(new Vector3f(0, 0, 0)); return; }
        e.setTranslation(new Vector3f(sp.translationX(), (float) y, 0));
        e.setScale(new Vector3f(sp.scaleX(), sp.scaleY(), 1));
    }
}
