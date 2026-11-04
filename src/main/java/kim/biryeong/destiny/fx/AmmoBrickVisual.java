package kim.biryeong.destiny.fx;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ManualAttachment;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.weapon.WeaponAmmoType;
import net.minecraft.core.component.DataComponents;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.util.Brightness;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

/** Personal, non-colliding ammo pickup silhouette. Other clients never watch these entity IDs. */
public final class AmmoBrickVisual {
    public static final float SCALE=.65f;
    private AmmoBrickVisual() {}
    public static ElementHolder create(ServerPlayer owner,WeaponAmmoType type,Vec3 position) {
        if(type==WeaponAmmoType.PRIMARY)throw new IllegalArgumentException("Primary reserves are infinite");
        var holder=new ElementHolder();
        new ManualAttachment(holder,owner.level(),()->position);
        var item=new ItemStack(Items.PAPER);
        item.set(DataComponents.ITEM_MODEL,DestinyGuardians.id("fx/ammo_brick_"+type.name().toLowerCase(java.util.Locale.ROOT)+"_w42"));
        var display=new ItemDisplayElement(item);
        display.setItemDisplayContext(ItemDisplayContext.NONE);
        display.setScale(new Vector3f(SCALE));
        // ItemDisplayContext.NONE centres Java item geometry at (8,8,8).
        // These shells use a model-space y=0 floor, not y=8: lift half a scaled block.
        display.setTranslation(new Vector3f(0,SCALE*.5f,0));
        display.setBrightness(new Brightness(15,15));
        display.setViewRange(1);holder.addElement(display);holder.startWatching(owner);holder.tick();
        return holder;
    }
}
