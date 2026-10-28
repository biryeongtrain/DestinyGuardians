package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.sound.DestinySounds;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.util.Brightness;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** New-class presentation. Never substitutes Hunter's bow/staff motion for a missing source rig. */
public final class ClassAbilityEffects {
    private static final Map<UUID, Presentation> ACTIVE = new HashMap<>();

    private static final class Presentation {
        final ServerPlayer player;
        final ServerLevel level;
        final Element element;
        final String path;
        final Vec3 origin;
        final ElementHolder holder;
        final ItemDisplayElement prop;
        final boolean ownsPostEffect;
        int attackAt = Integer.MIN_VALUE / 2;

        Presentation(ServerPlayer p, Element e, String path, boolean ownsPostEffect) {
            player = p; level = p.level(); element = e; this.path = path;
            this.ownsPostEffect = ownsPostEffect;
            origin = p.position();
            holder = new ElementHolder();
            prop = new ItemDisplayElement(path.equals("warlock/void_super") ? ItemStack.EMPTY : item(path));
            prop.setItemDisplayContext(ItemDisplayContext.NONE);
            prop.setBrightness(new Brightness(15, 15));
            prop.setTeleportDuration(1);
            prop.setScale(new Vector3f(path.equals("titan/void_super") ? .8f : .7f));
            holder.addElement(prop);
            try { ChunkAttachment.ofTicking(holder, level, origin); }
            catch (RuntimeException ex) { holder.destroy(); throw ex; }
        }
    }

    private ClassAbilityEffects() { }

    public static boolean beginSuper(ServerPlayer p, Element e, String path) {
        cleanup(p);
        if (!SuperCamera.startThirdPerson(p)) return false;
        PlayerAnimations.stop(p);
        boolean owns = p.addPostEffect(PostEffects.superEffect(e));
        try {
            Presentation s = new Presentation(p, e, path, owns);
            ACTIVE.put(p.getUUID(), s);
            String prefix = ClassSuperModelAssets.prefix(path);
            if (ClassSuperModelAssets.hasClip(prefix + "_idle")) {
                if (!PlayerAnimations.loop(p, prefix + "_idle")) {
                    cleanup(p);
                    SuperCamera.stop(p);
                    return false;
                }
                if (path.equals("titan/arc_super") || path.equals("warlock/arc_super") || path.equals("warlock/void_super"))
                    PlayerAnimations.superEmptyHands(p);
                else PlayerAnimations.superItem(p, item(path), path.equals("titan/void_super"));
                if (ClassSuperModelAssets.hasClip(prefix + "_start")) PlayerAnimations.play(p, prefix + "_start");
            }
            superTick(p, e, path, 0);
            PostEffects.pulse(p, e, false);
            sound(p, e, "super.start");
            return true;
        } catch (RuntimeException ex) {
            cleanup(p);
            if (owns) p.removePostEffect(PostEffects.superEffect(e));
            SuperCamera.stop(p);
            DestinyGuardians.LOGGER.warn("Class super presentation failed for {}: {}", path, ex.toString());
            return false;
        }
    }

    public static void superTick(ServerPlayer p, Element e, String path, int age) {
        Presentation s = ACTIVE.get(p.getUUID());
        if (s == null || s.player != p || !s.path.equals(path)) return;
        Vec3 forward = new Vec3(-Math.sin(Math.toRadians(p.getYRot())), 0,
                Math.cos(Math.toRadians(p.getYRot())));
        Vec3 right = new Vec3(-forward.z, 0, forward.x);
        int since = p.level().getServer().getTickCount() - s.attackAt;
        double swing = since >= 0 && since < 6 ? Math.sin(since / 6.0 * Math.PI) : 0;
        Vec3 hand = p.position().add(0, 1.15, 0).add(right.scale(.42)).add(forward.scale(.25 + swing * .45));
        s.prop.setOffset(hand.subtract(s.origin));
        s.prop.setItem(PlayerAnimations.isPlaying(p) || path.equals("warlock/void_super") ? ItemStack.EMPTY : item(path));
        s.prop.setLeftRotation(new Quaternionf().rotationY((float)-Math.toRadians(p.getYRot()))
                .rotateX((float)(-.15 - swing * 1.4)));
        s.holder.tick();
        if (age % 4 == 0) p.level().sendParticles(Fx.dust(e.color(), .65f), p.getX(), p.getY() + .5,
                p.getZ(), 4, .4, .4, .4, .01);
    }

    public static void attack(ServerPlayer p, Element e, String path) {
        Presentation s = ACTIVE.get(p.getUUID());
        if (s != null && s.player == p) s.attackAt = p.level().getServer().getTickCount();
        String clip = ClassSuperModelAssets.prefix(path) + "_attack";
        if (ClassSuperModelAssets.hasClip(clip)) {
            PlayerAnimations.play(p, clip);
            if (path.equals("titan/arc_super") || path.equals("warlock/arc_super") || path.equals("warlock/void_super"))
                PlayerAnimations.superEmptyHands(p);
        } else p.swing(InteractionHand.MAIN_HAND, new net.minecraft.world.item.component.SwingAnimation(
                net.minecraft.world.item.SwingAnimationType.WHACK, 4), true);
    }

    public static void endSuper(ServerPlayer p, Element e, String path) {
        sound(p, e, "super.end");
        cleanup(p);
        String clip = ClassSuperModelAssets.prefix(path) + "_end";
        if (ClassSuperModelAssets.hasClip(clip)) {
            PlayerAnimations.play(p, clip);
            if (path.equals("titan/arc_super") || path.equals("warlock/arc_super") || path.equals("warlock/void_super"))
                PlayerAnimations.superEmptyHands(p);
        } else p.swing(InteractionHand.MAIN_HAND, new net.minecraft.world.item.component.SwingAnimation(
                net.minecraft.world.item.SwingAnimationType.WHACK, 4), true);
        PlayerAnimations.finishSuper(p);
        if (!PlayerAnimations.isPlaying(p)) SuperCamera.stop(p);
    }

    public static void cleanup(ServerPlayer p) {
        Presentation s = ACTIVE.get(p.getUUID());
        if (s == null || s.player != p) return;
        ACTIVE.remove(p.getUUID());
        s.holder.destroy();
        if (s.ownsPostEffect) p.removePostEffect(PostEffects.superEffect(s.element));
        PostEffects.cancel(p);
    }

    public static void clearAll() {
        for (Presentation s : java.util.List.copyOf(ACTIVE.values())) cleanup(s.player);
    }

    public static int activeCount() { return ACTIVE.size(); }

    /** Source-backed item definitions are installed separately; provisional base item is explicit in docs. */
    public static ItemStack item(String path) {
        if (path.equals("titan/arc_super") || path.equals("warlock/arc_super")) return ItemStack.EMPTY;
        ItemStack stack = new ItemStack(switch (path) {
            case "titan/solar_super", "titan/solar_melee" -> Items.MACE;
            case "titan/void_super", "titan/void_melee" -> Items.SHIELD;
            case "warlock/solar_super" -> Items.GOLDEN_SWORD;
            case "warlock/void_super", "warlock/void_melee" -> Items.ENDER_PEARL;
            default -> Items.FIRE_CHARGE;
        });
        if (ClassAbilityAssets.has(path)) stack.set(DataComponents.ITEM_MODEL, DestinyGuardians.id("class_ability/" + path));
        return stack;
    }

    /** Explicit presentation variant; callers must supply the eventual PvP viewer relationship. */
    public static ItemStack item(String path, boolean hostile) {
        return AbilityVisualVariants.item(item(path), hostile);
    }

    public static void sound(ServerPlayer p, Element e, String action) {
        String key = Guardians.data(p).guardianClass().getSerializedName() + "." + e.getSerializedName() + "." + action;
        DestinySounds.orVanilla(p.level(), p.position(), key, action.equals("super.fire")
                ? SoundEvents.PLAYER_ATTACK_SWEEP : action.endsWith("impact")
                ? SoundEvents.GENERIC_EXPLODE.value() : SoundEvents.BEACON_ACTIVATE, .65f, 1f);
    }

    public static void burst(ServerPlayer p, Vec3 at, Element e, double radius) {
        Fx.burst(p.level(), at, e, 24, Math.min(1.5, radius / 3));
        Fx.ring(p.level(), at, radius, e.glow(), 28);
        PostEffects.pulse(p, e, true);
    }
}
