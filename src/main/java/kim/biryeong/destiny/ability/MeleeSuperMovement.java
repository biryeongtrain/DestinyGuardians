package kim.biryeong.destiny.ability;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

import java.util.Set;

/** Roaming melee supers: +30% movement speed while active and a forward step on each light attack. */
public final class MeleeSuperMovement {
    public static final Identifier SPEED_ID = DestinyGuardians.id("melee_super_speed");
    public static final double SPEED_BONUS = 0.30;
    static final int STEP_COOLDOWN_TICKS = 8;
    /** Arc Staff, Spectral Blades, Fists of Havoc, Sentinel Shield, Burning Maul. */
    public static final Set<Identifier> MELEE_SUPERS = Set.of(
            DestinyGuardians.id("hunter/arc_staff"), DestinyGuardians.id("hunter/spectral_blades"),
            DestinyGuardians.id("titan/arc_super"), DestinyGuardians.id("titan/void_super"),
            DestinyGuardians.id("titan/burning_maul"));
    private MeleeSuperMovement() { }

    public static boolean isMeleeSuper(Identifier id) { return id != null && MELEE_SUPERS.contains(id); }

    static boolean active(ServerPlayer player) {
        return AbilityService.inSuper(player) && AbilityService.equipped(player, kim.biryeong.destiny.guardian.AbilitySlot.SUPER)
                .map(a -> isMeleeSuper(a.id())).orElse(false);
    }

    /** Called every guardian tick; adds or removes the owned transient modifier. */
    static void tick(ServerPlayer player) {
        var speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed == null) return;
        boolean want = active(player);
        boolean has = speed.hasModifier(SPEED_ID);
        if (want && !has) speed.addTransientModifier(new AttributeModifier(SPEED_ID, SPEED_BONUS,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        else if (!want && has) speed.removeModifier(SPEED_ID);
    }

    static void clear(ServerPlayer player) {
        var speed = player.getAttribute(Attributes.MOVEMENT_SPEED);
        if (speed != null && speed.hasModifier(SPEED_ID)) speed.removeModifier(SPEED_ID);
    }

    /** Forward step on a light attack, rate-limited so held clicks do not chain teleports. */
    static void attackStep(ServerPlayer player, kim.biryeong.destiny.guardian.GuardianRuntime runtime) {
        if (!active(player) || AbilityService.equipped(player, kim.biryeong.destiny.guardian.AbilitySlot.SUPER)
                .map(a -> a.id().equals(DestinyGuardians.id("titan/arc_super"))).orElse(true)) return; // Fists already lunge by velocity
        int now = player.level().getServer().getTickCount();
        if (now - runtime.meleeSuperStepAt < STEP_COOLDOWN_TICKS) return;
        runtime.meleeSuperStepAt = now;
        kim.biryeong.destiny.weapon.SwordMelee.lunge(player, kim.biryeong.destiny.weapon.SwordArc.STEP);
    }
}
