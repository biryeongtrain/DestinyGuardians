package kim.biryeong.destiny.weapon;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import net.fabricmc.fabric.api.attachment.v1.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** Actual inventory-backed equipment. No shadow copies, hidden ammo pool, or copied-item duplication.
 * Existing standalone debug load remains available until a player explicitly equips a three-slot loadout.
 */
public final class WeaponLoadout {
    public static final AttachmentType<Boolean> ENABLED=AttachmentRegistry.create(DestinyGuardians.id("weapon_loadout"),
            b->b.persistent(Codec.BOOL).copyOnDeath().initializer(()->false));
    public record Equipped(WeaponSlot slot, ItemStack stack, WeaponCatalog.Entry weapon) {
        public WeaponCharacteristics.Entry characteristics() { return WeaponCharacteristics.of(weapon); }
        public WeaponAmmoState ammunition() {
            var profile=WeaponProfile.forEntry(weapon);var ammo=WeaponItems.magazine(stack,profile);
            return new WeaponAmmoState(weapon.family(),ammo.rounds(),ammo.reserve(),WeaponComponents.profile(stack,profile).magazine(),0,
                    profile.reloadTicks(),false,profile.infiniteReserve());
        }
    }
    private WeaponLoadout() {}
    public static void init() {}
    /** OP fixture compatibility; does not alter inventory or firing cooldown. */
    public static void standalone(ServerPlayer p) { WeaponRuntime.cancelUseForSkill(p);p.setAttached(ENABLED,false); }
    public static boolean enabled(ServerPlayer p) { return p.getAttachedOrElse(ENABLED,false); }
    public static WeaponSlot slot(ServerPlayer p, ItemStack stack, WeaponCatalog.Entry weapon) {
        // Khvostov 7G-02 is a kinetic auto rifle in Destiny; its catalog frame donor (Gnawing Hunger) is energy.
        if (weapon.id().equals(kim.biryeong.destiny.campaign.RisingLoadout.RIFLE)
                && WeaponSkins.of(stack).filter(s -> s.id().equals(kim.biryeong.destiny.campaign.RisingLoadout.RIFLE_SKIN)).isPresent())
            return WeaponSlot.KINETIC;
        return WeaponCharacteristics.of(weapon).slot();
    }
    public static List<Equipped> equipped(ServerPlayer p) {
        List<Equipped> result=new ArrayList<>();
        for(var slot:WeaponSlot.values()) {
            ItemStack stack=p.getInventory().getItem(slot.hotbar());
            WeaponItems.entry(stack).filter(e->slot(p,stack,e)==slot)
                    .ifPresent(e->result.add(new Equipped(slot,stack,e)));
        }
        return List.copyOf(result);
    }
    public static boolean canUse(ServerPlayer p) {
        if (!kim.biryeong.destiny.strike.devils.DevilsLair.allows(p)) return false;
        if(!kim.biryeong.destiny.crucible.CrucibleRuntime.canAct(p)||kim.biryeong.destiny.down.GuardianDown.active(p))return false;
        kim.biryeong.destiny.crucible.CrucibleAmmo.guard(p);
        if(!enabled(p))return true;
        int index=p.getInventory().getSelectedSlot();
        return equipped(p).stream().anyMatch(e->e.slot().hotbar()==index&&e.stack()==p.getMainHandItem());
    }
    /** Command/UI equivalent of a vanilla slot choice, with the same inventory and cooldown ownership. */
    public static boolean select(ServerPlayer p,WeaponSlot slot) {
        if(!enabled(p)||!p.isAlive()||p.isRemoved()||p.isSpectator()||AbilityService.inSuper(p)
                ||equipped(p).stream().noneMatch(e->e.slot()==slot))return false;
        WeaponRuntime.selectedSlotChanging(p,slot.hotbar());
        p.getInventory().setSelectedSlot(slot.hotbar());
        p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket(slot.hotbar()));
        p.containerMenu.broadcastChanges();
        return true;
    }
    /** All validation occurs before changing either inventory slot. Never mints or destroys an item. */
    public static String equipHeld(ServerPlayer p) {
        if(!p.isAlive()||p.isRemoved()||p.isSpectator()||AbilityService.inSuper(p))return "현재 동작 중에는 장비를 변경할 수 없습니다.";
        ItemStack held=p.getMainHandItem();var entry=WeaponItems.entry(held);
        if(entry.isEmpty())return "소유한 전투 무기를 주 손에 들어 주세요. 프리뷰는 사용할 수 없습니다.";
        int from=p.getInventory().getSelectedSlot();int to=slot(p,held,entry.get()).hotbar();
        ItemStack previous=p.getInventory().getItem(to);
        if(from!=to&&!previous.isEmpty()) {
            var previousEntry=WeaponItems.entry(previous);
            if(previousEntry.isEmpty()||slot(p,previous,previousEntry.get()).hotbar()!=to||from<3)
                return "대상 장비 슬롯을 먼저 비워 주세요. 기존 아이템은 덮어쓰지 않습니다.";
        }
        long exoticCount=equipped(p).stream().filter(e->e.slot().hotbar()!=to&&e.characteristics().exotic()).count();
        if(WeaponCharacteristics.of(entry.get()).exotic()&&exoticCount>0)return "경이 무기는 한 개만 장착할 수 있습니다.";
        WeaponHandling.update(p);
        WeaponRuntime.cancelUseForSkill(p);
        if(from!=to) {
            p.getInventory().setItem(from,previous);
            p.getInventory().setItem(to,held);
        }
        p.setAttached(ENABLED,true);
        p.getInventory().setSelectedSlot(to);
        p.connection.send(new net.minecraft.network.protocol.game.ClientboundSetHeldSlotPacket(to));
        WeaponHandling.update(p);
        kim.biryeong.destiny.crucible.CrucibleAmmo.equipmentChanged(p);
        p.getInventory().setChanged();
        p.containerMenu.broadcastChanges();
        return null;
    }
}
