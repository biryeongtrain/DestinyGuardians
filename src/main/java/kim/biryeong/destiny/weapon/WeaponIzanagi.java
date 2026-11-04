package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.IntTag;
import net.minecraft.nbt.ByteTag;
import net.minecraft.nbt.ShortTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/** Funded, item-owned Honed Edge. Unlike Ace, a completed charge survives stow.
 * Pending reload authority never survives owner/level/identity changes. The saved charge
 * follows the same server-owned item as its ammunition, including save/load and transfer.
 * No catalyst. See W84 design for explicitly unverified transaction/timing policies. */
public final class WeaponIzanagi {
    public static final String CHARGE = "destiny_honed_edge_w84";
    public static final int RELOAD_TICKS = 61;
    private record Pending(ServerPlayer owner, ServerLevel level, ItemStack stack,
                           int loaded, int count, long until) {}
    private static final Map<UUID,Pending> PENDING = new HashMap<>();
    private WeaponIzanagi() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !AbilityService.inSuper(p) && WeaponLoadout.canUse(p)
                && WeaponItems.entry(p.getMainHandItem()).filter(WeaponExotics::izanagi).isPresent();
    }
    private static int saved(ItemStack stack) {
        var data=stack.get(DataComponents.CUSTOM_DATA);
        if(data==null)return 0;
        // JSON-backed ItemStack codecs minimize integral widths (IntTag4 becomes ByteTag4).
        // Preserve funded saved charges, while rejecting floating-point/string coercion.
        long value=switch(data.copyTag().get(CHARGE)) {
            case ByteTag v -> v.longValue();
            case ShortTag v -> v.longValue();
            case IntTag v -> v.longValue();
            case LongTag v -> v.longValue();
            case null, default -> 0;
        };
        return value>=2 && value<=4 ? (int)value : 0;
    }
    private static void save(ItemStack stack,int count) {
        var tag=stack.get(DataComponents.CUSTOM_DATA).copyTag();
        if(count>=2 && count<=4)tag.putInt(CHARGE,count);else tag.remove(CHARGE);
        stack.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
    }
    /** Pure observation; an item copied by the server also copies its funded ammunition.
     * This is not an anti-admin-NBT or anti-server-copy security boundary. */
    public static int charge(ItemStack stack) {
        var entry=WeaponItems.entry(stack).filter(WeaponExotics::izanagi);
        if(entry.isEmpty())return 0;
        return WeaponItems.magazine(stack,WeaponProfile.forEntry(entry.get())).rounds()==1 ? saved(stack) : 0;
    }
    public static int charge(ServerPlayer p) { return eligible(p) ? charge(p.getMainHandItem()) : 0; }
    /** Pure observation of the accepted pending transaction, including its terminal tick. */
    public static boolean honing(ServerPlayer p) {
        var pending = PENDING.get(p.getUUID());
        return eligible(p) && pending != null && pending.owner == p
                && pending.level == p.level() && pending.stack == p.getMainHandItem();
    }
    public static boolean canStart(ServerPlayer p) {
        if(!eligible(p) || charge(p)>0 || PENDING.containsKey(p.getUUID()))return false;
        var ammo=WeaponItems.magazine(p.getMainHandItem(),WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow()));
        return ammo.total()>=2;
    }
    /** Called only after the timer-only gameplay reload has actually been accepted. */
    public static void started(ServerPlayer p) {
        if(!canStart(p))throw new IllegalStateException("Honed reload was not admitted");
        var ammo=WeaponItems.magazine(p.getMainHandItem(),WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow()));
        PENDING.put(p.getUUID(),new Pending(p,p.level(),p.getMainHandItem(),ammo.rounds(),
                (int)Math.min(4,ammo.total()),now(p)+RELOAD_TICKS));
    }
    /** One atomic full-ready commit. No early credit/refund or second ordinary transfer.
     * Local pool policy: loaded first, then reserve/overflow. Pickups do not upgrade n. */
    public static boolean finishReload(ServerPlayer p,ItemStack stack) {
        var pending=PENDING.get(p.getUUID());
        if(pending==null || pending.owner!=p)return false;
        if(!eligible(p) || pending.stack!=stack || stack!=p.getMainHandItem() || pending.level!=p.level()) {
            PENDING.remove(p.getUUID());return false;
        }
        if(now(p)<pending.until)return false;
        PENDING.remove(p.getUUID());
        var ammo=WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
        if(charge(stack)>0 || ammo.rounds()!=pending.loaded || !ammo.compressRounds(pending.count))return false;
        WeaponItems.save(stack,ammo);save(stack,pending.count);
        return true;
    }
    /** Exactly once after the real one-projectile debit; misses consume the charged shot. */
    public static int shot(ServerPlayer p,WeaponCatalog.Entry entry) {
        if(!WeaponExotics.izanagi(entry))return 0;
        var stack=p.getMainHandItem();
        int count=WeaponItems.magazine(stack,WeaponProfile.forEntry(entry)).rounds()==0 ? saved(stack) : 0;
        save(stack,0);return count;
    }
    /** Rounded community increases relative to an uncharged shot of the SAME hit type. */
    public static float multiplier(int count,boolean precision,boolean pvp) {
        return switch(count) {
            case 2 -> precision ? (pvp?1.91f:1.79f) : (pvp?1.20f:1.12f);
            case 3 -> precision ? (pvp?2.67f:2.31f) : (pvp?1.45f:1.25f);
            case 4 -> precision ? (pvp?4.89f:3.91f) : (pvp?2.65f:2.12f);
            default -> 1;
        };
    }
    public static void cancelReload(ServerPlayer p) {
        var pending=PENDING.get(p.getUUID());
        if(pending!=null && pending.owner==p)PENDING.remove(p.getUUID());
    }
    public static void clear() { PENDING.clear(); }
}
