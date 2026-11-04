package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.guardian.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;

/** Immediate paid hitscan miss transaction, not an input/query or damage-dealt listener. */
public final class WeaponMulligan {
    public static final class Token {
        public static final Token NONE=new Token();
        private final ServerPlayer owner;
        private final ServerLevel level;
        private final ItemStack stack;
        private final WeaponCatalog.Entry entry;
        private final WeaponPerks.Roll roll;
        private final GuardianData data;
        private final GuardianRuntime runtime;
        private final GuardianClass guardianClass;
        private final int slot;
        private final long tick;
        private boolean spent;
        private Token() { owner=null;level=null;stack=null;entry=null;roll=null;data=null;runtime=null;guardianClass=null;slot=-1;tick=-1;spent=true; }
        private Token(ServerPlayer p,WeaponCatalog.Entry e,WeaponPerks.Roll r) {
            owner=p;level=p.level();stack=p.getMainHandItem();entry=e;roll=r;
            data=p.getAttachedOrElse(Guardians.DATA,null);runtime=Guardians.runtimeIfPresent(p).orElse(null);
            guardianClass=data.guardianClass();slot=p.getInventory().getSelectedSlot();tick=now(p);
        }
    }
    private WeaponMulligan() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        if(p==null || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.hasDisconnected() || !WeaponLoadout.canUse(p))return false;
        var d=p.getAttachedOrElse(Guardians.DATA,null);var r=Guardians.runtimeIfPresent(p).orElse(null);
        return d!=null && d.guardianClass()!=null && d.guardianClass()!=GuardianClass.NONE && r!=null && r.superSession==null;
    }
    private static boolean source(ServerPlayer p,ItemStack stack) {
        int slot=p.getInventory().getSelectedSlot();
        return slot>=0 && slot<9 && stack.getCount()==1 && p.getMainHandItem()==stack
            && p.getInventory().getItem(slot)==stack && (!WeaponLoadout.enabled(p)
                || WeaponLoadout.equipped(p).stream().anyMatch(e->e.stack()==stack));
    }
    /** Capture ONLY after successful cartridge payment, before tracing this emission. */
    public static Token capture(ServerPlayer p,WeaponCatalog.Entry entry) {
        if(!eligible(p) || !MulliganProfile.supports(entry))return Token.NONE;
        var stack=p.getMainHandItem();var roll=WeaponPerks.selected(stack,MulliganProfile.ID).orElse(null);
        return source(p,stack) && WeaponItems.entry(stack).filter(entry::equals).isPresent()
            && roll!=null && MulliganProfile.rolls().contains(roll) ? new Token(p,entry,roll):Token.NONE;
    }
    /** One decision after ALL pellets. Geometry contacts with eligible living enemies count as
     * hits even when damage is rejected; wall/air contacts count as misses. No reload hooks. */
    public static int resolved(ServerPlayer p,Token token,boolean entityHit) {
        if(p==null || token==null || token==Token.NONE || token.owner!=p || token.spent)return 0;
        if(!p.level().getServer().isSameThread())throw new IllegalStateException("Mulligan is server thread owned");
        token.spent=true;
        if(entityHit || !eligible(p) || p.level()!=token.level || now(p)!=token.tick || !source(p,token.stack)
            || p.getInventory().getSelectedSlot()!=token.slot
            || p.getAttachedOrElse(Guardians.DATA,null)!=token.data || token.data.guardianClass()!=token.guardianClass
            || Guardians.runtimeIfPresent(p).orElse(null)!=token.runtime
            || WeaponItems.entry(token.stack).filter(token.entry::equals).isEmpty()
            || WeaponPerks.selected(token.stack,MulliganProfile.ID).filter(token.roll::equals).isEmpty())return 0;
        if(p.getRandom().nextInt(100)>=MulliganProfile.chancePercent(token.entry))return 0;
        var ammo=WeaponItems.magazine(token.stack,WeaponProfile.forEntry(token.entry));
        int generated=ammo.generateLoaded(1);
        if(generated>0) { WeaponItems.save(token.stack,ammo);p.getInventory().setChanged();p.containerMenu.broadcastChanges(); }
        return generated;
    }
}
