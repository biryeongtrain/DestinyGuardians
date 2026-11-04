package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.weapon.*;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import java.util.*;

/** Session-owned checkpoint supplies. Server thread only. Never copies or replaces an item. */
public final class DevilsSupplies implements AutoCloseable {
    private static final String TOKEN = "destiny_devils_supply_identity";
    private final String session = UUID.randomUUID().toString() + ":";
    private final Ledger ledger;
    private final Map<UUID,ServerPlayer> online = new HashMap<>();
    public DevilsSupplies(Collection<UUID> participants) { ledger = new Ledger(participants); }

    /** First zone entry captures once; repeated entry/rejoin cannot recapture or renew a supply use. */
    public void entry(ServerPlayer player, DevilsPlan.Zone zone) {
        thread(player); if (!ledger.member(player.getUUID())) return;
        online.put(player.getUUID(), player);
        if (ledger.entered(player.getUUID(),zone)) return;
        for (var e : WeaponLoadout.equipped(player)) {
            if (e.characteristics().ammo() == WeaponAmmoType.PRIMARY || e.stack().getCount() != 1) continue;
            var tag = e.stack().getOrDefault(DataComponents.CUSTOM_DATA, CustomData.EMPTY).copyTag();
            if (!tag.getStringOr(TOKEN, "").startsWith(session)) {
                tag.putString(TOKEN, session + UUID.randomUUID());
                e.stack().set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            }
        }
        ledger.entry(player.getUUID(),zone,snapshots(player),duplicates());
        sync(player);
    }
    /** Invoke only after session validates current-zone, alive/not-down, range and deliberate interaction. */
    public boolean use(ServerPlayer player, DevilsPlan.Zone zone) {
        thread(player); if (online.get(player.getUUID()) != player || !ledger.available(player.getUUID(),zone)) return false;
        WeaponRuntime.cancelUseForSkill(player);
        var changes = ledger.use(player.getUUID(),zone,snapshots(player),duplicates());
        if (changes.isEmpty()) return false;
        apply(player, changes.get()); return true;
    }
    /** Wipe only, not reconnect. Frozen baseline cannot grow after pickups, swaps or repeated resets. */
    public void reset(ServerPlayer player, DevilsPlan.Zone zone) {
        thread(player); if (online.get(player.getUUID()) != player || !ledger.entered(player.getUUID(),zone)) return;
        WeaponRuntime.cancelUseForSkill(player);
        apply(player,ledger.reset(player.getUUID(),zone,snapshots(player),duplicates()));
    }
    public void reconnect(ServerPlayer player) {
        thread(player); if (ledger.member(player.getUUID())) online.put(player.getUUID(),player);
    }
    /** Preserve entitlement and baseline during the session's rejoin grace period. */
    public void leave(ServerPlayer player) { thread(player); online.remove(player.getUUID(),player); }
    public boolean available(UUID player, DevilsPlan.Zone zone) { return ledger.available(player,zone); }
    @Override public void close() { online.clear(); ledger.close(); }

    private List<Stock> snapshots(ServerPlayer player) {
        var result = new ArrayList<Stock>();
        for (var e : WeaponLoadout.equipped(player)) {
            ItemStack stack=e.stack(); String token=token(stack);
            if (!token.startsWith(session) || stack.getCount()!=1) continue;
            var profile=WeaponProfile.forEntry(e.weapon()); var mag=WeaponItems.magazine(stack,profile);
            var tag=stack.getOrDefault(DataComponents.CUSTOM_DATA,CustomData.EMPTY).copyTag();
            String identity=e.weapon().id()+"|"+tag.get(WeaponPerks.HASH_KEY)+"|"+tag.get(WeaponPerks.SOCKET_KEY)+"|"+tag.get(WeaponPerks.SLOTS_KEY);
            int honed=WeaponIzanagi.charge(stack);
            long funded=Math.max(0,honed-1);
            long conserved=Math.min(Long.MAX_VALUE-funded,mag.overflow())+funded;
            result.add(new Stock(token,identity,e.characteristics().ammo(),mag.rounds(),mag.reserve(),conserved,
                    honed>0?Math.max(1,mag.rounds()):profile.magazine(),profile.reserve()));
        }
        return result;
    }
    /** Include stowed inventory and carried stacks; duplicate tokens are permanently quarantined by ledger. */
    private Set<String> duplicates() {
        var seen=new HashSet<String>(); var duplicates=new HashSet<String>();
        for (var p:online.values()) {
            for(int i=0;i<p.getInventory().getContainerSize();i++) count(p.getInventory().getItem(i),seen,duplicates);
            count(p.containerMenu.getCarried(),seen,duplicates);
        }
        return duplicates;
    }
    private void count(ItemStack stack,Set<String> seen,Set<String> duplicates) {
        String key=token(stack);
        if(key.startsWith(session) && (!seen.add(key)||stack.getCount()!=1)) duplicates.add(key);
    }
    private static String token(ItemStack stack) { return stack.getOrDefault(DataComponents.CUSTOM_DATA,CustomData.EMPTY).copyTag().getStringOr(TOKEN,""); }
    private void apply(ServerPlayer player,Map<String,Grant> changes) {
        for(var e:WeaponLoadout.equipped(player)) {
            Grant grant=changes.get(token(e.stack())); if(grant==null)continue;
            var mag=WeaponItems.magazine(e.stack(),WeaponProfile.forEntry(e.weapon()));
            mag.addReserve(grant.reserve()); mag.generateLoaded(grant.loaded());
            WeaponItems.save(e.stack(),mag);
        }
        sync(player);
    }
    private static void sync(ServerPlayer p) { p.getInventory().setChanged(); p.containerMenu.broadcastChanges(); }
    private static void thread(ServerPlayer p) {
        if(!p.level().getServer().isSameThread())throw new IllegalStateException("Supplies are server-thread owned");
    }

    record Stock(String token,String identity,WeaponAmmoType type,int rounds,int reserve,long overflow,int magazineCapacity,int reserveCapacity) {
        Stock { Objects.requireNonNull(token);Objects.requireNonNull(identity);Objects.requireNonNull(type);
            if(rounds<0||reserve<0||overflow<0||magazineCapacity<1||reserveCapacity<0)throw new IllegalArgumentException("ammo"); }
        long total() { return Math.min(Long.MAX_VALUE-overflow,(long)rounds+reserve)+overflow; }
    }
    record Grant(int loaded,int reserve) { }
    static final class Checkpoint {
        final Map<String,Stock> baseline=new HashMap<>(); boolean used;
    }
    /** Deterministic entitlement/identity policy; no Minecraft server bootstrap required for tests. */
    static final class Ledger {
        final Set<UUID> members; final Map<UUID,EnumMap<DevilsPlan.Zone,Checkpoint>> checkpoints=new HashMap<>();
        final Map<String,UUID> owners=new HashMap<>(); final Set<String> quarantined=new HashSet<>(); boolean closed;
        Ledger(Collection<UUID> ids) {
            members=Set.copyOf(ids);
            if(members.isEmpty()||members.size()>3||members.size()!=ids.size())throw new IllegalArgumentException("1-3 distinct participants");
        }
        boolean member(UUID id) { return !closed&&members.contains(id); }
        boolean entered(UUID id,DevilsPlan.Zone z) {return checkpoints.containsKey(id)&&checkpoints.get(id).containsKey(z);}
        boolean available(UUID id,DevilsPlan.Zone z) {return member(id)&&entered(id,z)&&!checkpoints.get(id).get(z).used;}
        void entry(UUID id,DevilsPlan.Zone z,List<Stock> stocks,Set<String> duplicates) {
            if(!member(id)||entered(id,z))return;
            quarantined.addAll(duplicates); var cp=new Checkpoint();
            for(var s:stocks) {
                UUID owner=owners.putIfAbsent(s.token(),id);
                if((owner==null||owner.equals(id))&&!quarantined.contains(s.token())&&s.type()!=WeaponAmmoType.PRIMARY)
                    cp.baseline.put(s.token(),s);
            }
            checkpoints.computeIfAbsent(id,k->new EnumMap<>(DevilsPlan.Zone.class)).put(z,cp);
        }
        Optional<Map<String,Grant>> use(UUID id,DevilsPlan.Zone z,List<Stock> stocks,Set<String> duplicates) {
            if(!available(id,z))return Optional.empty();
            quarantined.addAll(duplicates);var cp=checkpoints.get(id).get(z);cp.used=true;
            var grants=new HashMap<String,Grant>();
            for(var s:stocks) if(valid(id,cp,s)) {
                int divisor=s.type()==WeaponAmmoType.SPECIAL?2:4;
                int target=(int)(((long)s.reserveCapacity()+divisor-1)/divisor);
                int add=(int)Math.min(Math.max(0,target-s.reserve()),Long.MAX_VALUE-s.total());
                grants.put(s.token(),new Grant(0,add));
                cp.baseline.put(s.token(),new Stock(s.token(),s.identity(),s.type(),s.rounds(),s.reserve()+add,s.overflow(),s.magazineCapacity(),s.reserveCapacity()));
            }
            return Optional.of(Map.copyOf(grants));
        }
        Map<String,Grant> reset(UUID id,DevilsPlan.Zone z,List<Stock> stocks,Set<String> duplicates) {
            if(!member(id)||!entered(id,z))return Map.of();
            quarantined.addAll(duplicates);var cp=checkpoints.get(id).get(z);var grants=new HashMap<String,Grant>();
            for(var s:stocks) if(valid(id,cp,s)) {
                Stock base=cp.baseline.get(s.token());
                // Compare total ammunition so reloading before a wipe cannot restore the same rounds twice.
                long deficit=Math.max(0,Math.min((long)base.rounds()+base.reserve(),(long)s.magazineCapacity()+s.reserveCapacity())-s.total());
                int reserve=(int)Math.min(deficit,Math.max(0,s.reserveCapacity()-s.reserve()));
                int loaded=(int)Math.min(deficit-reserve,Math.max(0,s.magazineCapacity()-s.rounds()));
                grants.put(s.token(),new Grant(loaded,reserve));
            }
            return Map.copyOf(grants);
        }
        private boolean valid(UUID id,Checkpoint cp,Stock s) {
            var base=cp.baseline.get(s.token());
            return !quarantined.contains(s.token())&&id.equals(owners.get(s.token()))&&base!=null
                    &&base.identity().equals(s.identity())&&base.type()==s.type();
        }
        void close(){closed=true;checkpoints.clear();owners.clear();quarantined.clear();}
    }
}
