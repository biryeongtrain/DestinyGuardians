package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.Ability;
import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import net.minecraft.core.component.DataComponents;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.fx.AbilityDisplayElement;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** A stationary healing field with an optional authored ring display. No block placement or shared potion ownership. */
public final class WarlockClassAbility extends Ability {
    private static final Map<ServerPlayer, Rift> ACTIVE = new IdentityHashMap<>();
    private static final class Rift {
        final WarlockAbilities.Lease lease; final WarlockClassAbility ability; final Vec3 origin;
        final int duration, interval; final double radius, height; final float heal;
        final ElementHolder holder;
        final ItemDisplayElement display;
        final double modelDiameterPixels;
        int age; boolean destroyed;
        Rift(WarlockAbilities.Lease lease, WarlockClassAbility ability, Vec3 origin) {
            this.lease = lease; this.ability = ability; this.origin = origin;
            duration = WarlockAbilities.ticks(ability, "duration_ticks", 300, 1, 400);
            interval = WarlockAbilities.ticks(ability, "pulse_ticks", 10, 5, 40);
            radius = WarlockAbilities.value(ability, "radius", 4, 1, 6);
            height = WarlockAbilities.value(ability, "height", 1.5, .5, 2);
            heal = (float) WarlockAbilities.value(ability, "heal", 2, .1, 6);
            modelDiameterPixels = WarlockAbilities.value(ability, "model_diameter_pixels", 0, 0, 256);
            ElementHolder allocated = null;
            ItemDisplayElement element = null;
            try {
                var item = ClassAbilityEffects.item(ability.id().getPath());
                // Canonical art metadata must be supplied. Never display a fallback fire-charge sprite.
                if (item.has(DataComponents.ITEM_MODEL) && modelDiameterPixels > 0) {
                    allocated = new ElementHolder();
                    element = new AbilityDisplayElement(lease.owner, item);
                    element.setItemDisplayContext(ItemDisplayContext.NONE);
                    element.setBillboardMode(Display.BillboardConstraints.FIXED);
                    element.setBrightness(new Brightness(15, 15));
                    float horizontal = (float) (radius * 32 / modelDiameterPixels);
                    float vertical = (float) WarlockAbilities.value(ability, "model_height_scale", 1, .1, 4);
                    element.setScale(new Vector3f(horizontal, vertical, horizontal));
                    double cx = WarlockAbilities.value(ability, "model_center_x_pixels", 8, -128, 128);
                    double cz = WarlockAbilities.value(ability, "model_center_z_pixels", 8, -128, 128);
                    double ground = WarlockAbilities.value(ability, "model_ground_y_pixels", 8, -128, 128);
                    element.setTranslation(new Vector3f((float) ((8 - cx) / 16 * horizontal),
                            (float) ((8 - ground) / 16 * vertical), (float) ((8 - cz) / 16 * horizontal)));
                    // Cancel the item renderer's built-in Y=PI: art's X/Z anchor remains canonical.
                    element.setLeftRotation(new Quaternionf().rotationY((float) Math.PI));
                    allocated.addElement(element);
                    ChunkAttachment.ofTicking(allocated, lease.level, origin);
                }
            } catch (RuntimeException failure) {
                if (allocated != null) allocated.destroy();
                allocated = null; element = null;
                kim.biryeong.destiny.DestinyGuardians.LOGGER.warn("Rift ring unavailable; keeping particle field", failure);
            }
            holder = allocated; display = element;
        }
        void destroy() {
            if (destroyed) return;
            destroyed = true;
            if (holder != null) holder.destroy();
        }
    }
    public WarlockClassAbility(Identifier id) { super(id, GuardianClass.WARLOCK, AbilitySlot.CLASS_ABILITY, Element.KINETIC, 118.7, "치유 균열"); }
    @Override public boolean activate(ServerPlayer p) {
        // Validate support before accepting the cast/cooldown, including fake onGround claims.
        if (!p.onGround() || p.isInWater() || p.isPassenger() || p.isFallFlying() || p.getAbilities().flying) return false;
        var ground = p.level().clip(new ClipContext(p.position().add(0, .15, 0), p.position().add(0, -.3, 0),
                ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, p));
        if (ground.getType() != HitResult.Type.BLOCK || ground.getDirection() != net.minecraft.core.Direction.UP) return false;
        var lease = WarlockAbilities.acquire(p, this);
        if (lease == null || ACTIVE.containsKey(p)) return false;
        Vec3 origin = new Vec3(p.getX(), ground.getLocation().y + .04, p.getZ());
        boolean accepted = kim.biryeong.destiny.ability.ClassAbilityCast.begin(p,id(),"class_warlock_healing",lease::valid,()->{
            var support=p.level().clip(new ClipContext(origin.add(0,.15,0),origin.add(0,-.3,0),
                    ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p));
            if(!p.onGround()||support.getType()!=HitResult.Type.BLOCK)return;
            ACTIVE.put(p,new Rift(lease,this,origin));
            DestinySounds.orVanilla(lease.level, origin, "class.warlock.rift.healing",
                    SoundEvents.BEACON_ACTIVATE, .65f, 1f);
        });
        if (accepted) DestinySounds.orVanilla(lease.level, p.position(), "class.warlock.rift.precast",
                SoundEvents.BEACON_ACTIVATE, .65f, 1f);
        return accepted;
    }
    static void tick() {
        for (Rift r : List.copyOf(ACTIVE.values())) {
            if (!r.lease.valid()) { ACTIVE.remove(r.lease.owner); r.destroy(); continue; }
            if (r.age >= r.duration) {
                ACTIVE.remove(r.lease.owner);
                r.destroy();
                DestinySounds.orVanilla(r.lease.level, r.origin, "class.warlock.rift.end",
                        SoundEvents.BEACON_DEACTIVATE, .65f, 1f);
                continue;
            }
            if (r.holder != null) r.holder.tick();
            if (r.age % 5 == 0) Fx.ring(r.lease.owner, r.lease.level, r.origin, r.radius, 0xF4F3E8, 32);
            if (r.age % r.interval == 0) {
                for (Player ally : r.lease.level.getEntitiesOfClass(Player.class, new AABB(r.origin, r.origin).inflate(r.radius, r.height + 2, r.radius))) if (ally != r.lease.owner) heal(r, ally);
                // TestPlayers and some server-side NPC players are not in the world's entity index.
                heal(r, r.lease.owner);
            }
            r.age++;
        }
    }
    private static void heal(Rift r, Player ally) {
        if (!ally.isAlive() || ally.isSpectator() || ally.level() != r.lease.level || !friendly(r.lease.owner, ally)) return;
        Vec3 feet = ally.position(); double dx = feet.x - r.origin.x, dz = feet.z - r.origin.z;
        if (dx * dx + dz * dz > r.radius * r.radius || Math.abs(feet.y - r.origin.y) > r.height) return;
        if (!WarlockAbilities.visible(r.lease, r.origin.add(0, .3, 0), ally.getEyePosition())) return;
        ally.heal(r.heal);
    }
    private static boolean friendly(ServerPlayer owner, Player ally) {
        // Untagged PvE co-op players share the field; explicit opposing teams do not.
        return ally instanceof ServerPlayer player
                ? kim.biryeong.destiny.crucible.CrucibleRuntime.friendly(owner, player)
                : ally == owner || owner.isAlliedTo(ally) || owner.getTeam() == null && ally.getTeam() == null;
    }
    static void cleanup(ServerPlayer p) {
        Rift r = ACTIVE.remove(p);
        if (r != null) r.destroy();
    }
    public static int visualCount(ServerPlayer p) {
        Rift r = ACTIVE.get(p);
        return r == null || r.holder == null ? 0 : r.holder.getElements().size();
    }
    public static double visualRadius(ServerPlayer p) {
        Rift r = ACTIVE.get(p);
        return r == null || r.display == null ? 0 : r.display.getScale().x() * r.modelDiameterPixels / 32;
    }
    public static boolean active(ServerPlayer p) { return ACTIVE.containsKey(p); }
    public static Vec3 origin(ServerPlayer p) { Rift r = ACTIVE.get(p); return r == null ? null : r.origin; }
}
