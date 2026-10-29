package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;

/** Native movement attribute drives vanilla speed-dependent FOV, never a projection packet.
 * Left-click ADS does not neutralize sneak: Shift remains ordinary crouch with its native slowdown.
 * Own the exact modifier object, not its ID alone. A foreign takeover yields until ADS ends.
 */
final class WeaponAimMovement {
    static final Identifier SPEED_ID = DestinyGuardians.id("weapon_ads_movement_w75");
    private final ServerPlayer owner;
    private final net.minecraft.server.level.ServerLevel level;
    private final net.minecraft.world.item.ItemStack stack;
    private final AttributeInstance speed;
    private AttributeModifier ownedSpeed;
    private boolean yielded;

    WeaponAimMovement(ServerPlayer owner) {
        this.owner = owner; level = owner.level(); stack = owner.getMainHandItem();
        speed = owner.getAttribute(Attributes.MOVEMENT_SPEED);
    }
    private boolean ordinaryLocomotion() {
        return !owner.isPassenger() && !owner.getAbilities().flying && !owner.isFallFlying()
                && !owner.isSwimming() && !owner.isInWater() && !owner.isInLava()
                && !owner.onClimbable() && !owner.isVisuallyCrawling();
    }
    void update(WeaponCatalog.Entry entry, boolean accepted, float progress) {
        if (!accepted || owner.level() != level || owner.getMainHandItem() != stack || !ordinaryLocomotion()) {
            release(); yielded = false; return;
        }
        if (yielded) return;
        if (speed == null || speed != owner.getAttribute(Attributes.MOVEMENT_SPEED)) {
            release(); yielded = true; return;
        }
        double scalar=WeaponNativeZoom.movementScalar(WeaponAimMovementProfile.scalar(entry),
                WeaponAimProfile.of(entry).zoom()*WeaponRangefinder.zoomScalar(owner,entry),progress);
        double amount=WeaponAimMovementProfile.modifierAmount(WeaponMovingTarget.movementScalar(owner,entry,scalar));
        if (ownedSpeed != null) {
            if (speed.getModifier(SPEED_ID) != ownedSpeed) {
                // A foreign takeover still owns its exact objects, including equal-valued clones.
                release(); yielded = true; return;
            }
            if (Double.compare(ownedSpeed.amount(),amount)==0) return;
            release();
        }
        if (speed.hasModifier(SPEED_ID)) { yielded = true; return; }
        ownedSpeed = new AttributeModifier(SPEED_ID, amount,
                AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        speed.addTransientModifier(ownedSpeed);
    }
    void release() {
        if (speed != null && ownedSpeed != null && speed.getModifier(SPEED_ID) == ownedSpeed)
            speed.removeModifier(SPEED_ID);
        ownedSpeed = null;
    }
}
