package kim.biryeong.destiny.activity.presentation;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.chat.FontDescription;
import net.minecraft.network.chat.Style;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/**
 * Shared Destiny-style objective waypoint (owner-only, promoted from the W301 campaign marker). A white diamond with the distance under it floats over the
 * stage's destination and is drawn through walls (see-through text display, custom glyph destiny:rg_waypoint).
 * It keeps a constant on-screen size: far targets are drawn at {@link #CLAMP} blocks along the line of sight, near
 * ones at the target scaled with distance. The destination itself gets a soft light column on the ground.
 * It fades out within {@link #ARRIVED} blocks. One instance per player, owned by the activity that shows it;
 * call {@link #clear()} when the player leaves, disconnects or the activity closes.
 */
public final class ObjectiveWaypoint {
    public static final double CLAMP = 18, ARRIVED = 3.5, LIFT = 1.9, COLUMN_RANGE = 48;
    /** Angular height of the marker (radians); scale 1 = one 9 px text line = 0.225 blocks (glyph is 16 px). */
    public static final double ANGLE = .055;
    public static final int COLOR = 0xEAF6FF, DIM = 0xB8C6D2;
    private static final FontDescription.Resource FONT =
            new FontDescription.Resource(Identifier.fromNamespaceAndPath("destiny", "rg_waypoint"));
    private final ServerPlayer owner;
    private ElementHolder holder;
    private TextDisplayElement marker;
    private ServerLevel level;
    private Vec3 anchor;
    private int lastDistance = -1;
    private byte opacity = -1;

    public ObjectiveWaypoint(ServerPlayer owner) { this.owner = owner; }

    private void spawn(Vec3 at) {
        level = owner.level();
        anchor = at;
        lastDistance = -1;
        opacity = -1;
        holder = new ElementHolder();
        marker = new TextDisplayElement();
        marker.setBillboardMode(Display.BillboardConstraints.CENTER);
        marker.setSeeThrough(true);
        marker.setShadow(true);
        marker.setBackground(0);
        marker.setBrightness(new Brightness(15, 15));
        marker.setTeleportDuration(2);
        marker.setInterpolationDuration(2);
        marker.setViewRange(4f);
        marker.setLineWidth(200);
        holder.addElement(marker);
        new ManualAttachment(holder, level, () -> this.anchor);
        holder.startWatching(owner);
    }

    /** Distance text under the glyph, e.g. "42m"; pure for tests. */
    public static String label(double distance) { return Math.max(0, Math.round(distance)) + "m"; }

    /** Constant-size placement; returns {position, scale}. Pure for tests. */
    public static double[] place(Vec3 eye, Vec3 point) {
        Vec3 d = point.subtract(eye);
        double dist = d.length();
        double at = Math.min(dist, CLAMP);
        Vec3 p = dist < 1e-3 ? point : eye.add(d.scale(at / dist));
        double scale = Math.max(.5, ANGLE * Math.max(at, 3) / .225);
        return new double[]{p.x, p.y, p.z, scale};
    }

    public ServerPlayer owner() { return owner; }

    public boolean shown() { return holder != null; }

    /** Shows (or moves) the marker toward {@code target}; null or {@code visible=false} hides it. */
    public void update(Vec3 target, boolean visible, int now) {
        if (holder != null && (level != owner.level() || owner.isRemoved() || owner.hasDisconnected())) clear();
        if (target == null || !visible || owner.hasDisconnected()) { clear(); return; }
        Vec3 point = target.add(0, LIFT, 0);
        double dist = owner.position().distanceTo(target);
        if (holder == null) spawn(point);
        tick(point, dist, now);
        if (now % 3 == 0 && dist > ARRIVED && dist < COLUMN_RANGE) column(owner, target, now);
    }

    public void clear() {
        if (holder != null) holder.destroy();
        holder = null;
        marker = null;
    }

    private void tick(Vec3 point, double dist, int now) {
        double[] pl = place(owner.getEyePosition(), point);
        anchor = new Vec3(pl[0], pl[1], pl[2]);
        // Gentle bob so it reads as a live marker.
        float s = (float) pl[3];
        marker.setTranslation(new Vector3f(0, (float) (Math.sin(now / 10.0) * .025 * s), 0));
        marker.setScale(new Vector3f(s));
        // Fades out over the last couple of blocks.
        float fade = (float) Math.clamp((dist - ARRIVED) / 2.5, 0, 1);
        byte op = (byte) Math.round(25 + 230 * fade);
        if (op != opacity) { opacity = op; marker.setTextOpacity(op); }
        int meters = (int) Math.round(dist);
        if (meters != lastDistance) {
            lastDistance = meters;
            var text = Component.empty()
                    .append(Component.literal("\ue300").withStyle(Style.EMPTY.withFont(FONT).withColor(COLOR)))
                    .append(Component.literal("\n" + label(dist)).withStyle(st -> st.withColor(DIM)));
            marker.setText(text);
        }
        marker.startInterpolationIfDirty();
        holder.tick();
    }

    /** Destination highlight: motes rising in a narrow light column with a faint ring on the floor. */
    private static void column(ServerPlayer p, Vec3 at, int now) {
        var level = (ServerLevel) p.level();
        var rnd = level.getRandom();
        double a = rnd.nextDouble() * Math.PI * 2, r = .25 * rnd.nextDouble();
        level.sendParticles(p, ParticleTypes.END_ROD, true, false,
                at.x + Math.cos(a) * r, at.y + .1, at.z + Math.sin(a) * r, 0, 0, 1, 0, .06);
        if (now % 12 == 0) {
            var dust = new net.minecraft.core.particles.DustParticleOptions(0x9FE6FF, .7f);
            for (int i = 0; i < 12; i++) {
                double t = i / 12.0 * Math.PI * 2 + now * .02;
                level.sendParticles(p, dust, true, false, at.x + Math.cos(t) * .9, at.y + .08, at.z + Math.sin(t) * .9, 1, 0, 0, 0, 0);
            }
        }
    }

}
