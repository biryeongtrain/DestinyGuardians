package kim.biryeong.destiny.weapon;

import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import java.util.ArrayList;
import java.util.IdentityHashMap;
import java.util.List;
import java.util.Map;

/** Long Arm pair and five shotgun single-shell insert phases. Cosmetic return never delays a shot or transfers ammo.
 * Float4: initial0..1, loop2..3, return4..5; shotguns use61-pose banks, Long Arm retains21, not hand IK.
 */
public final class WeaponInsertPresentation {
    public static final int SELECTOR_INDEX = 4, RETURN_TICKS = 6, STEPS = 20;
    private enum Phase { INITIAL, LOOP, RETURN }
    private static final class Binding {
        final ServerPlayer owner;
        final ServerLevel level;
        final List<Float> previous;
        final float offset;
        final int intervals;
        Phase phase = Phase.INITIAL;
        long returnAt;
        Binding(ServerPlayer owner, List<Float> previous, float offset, int intervals) {
            this.owner=owner; level=owner.level(); this.previous=previous; this.offset=offset; this.intervals=intervals;
        }
    }
    private static final Map<ItemStack, Binding> ACTIVE = new IdentityHashMap<>();
    private WeaponInsertPresentation() {}
    public static boolean supports(WeaponCatalog.Entry e) { e = LegendaryWeapons.base(e); return e != null && (e.id().equals("long_arm") || e.id().equals("first_in_last_out") || e.id().equals("mindbender_s_ambition_adept") || e.id().equals("dust_rock_blues") || e.id().equals("ikelos_sg_v1_0_1") || e.id().equals("parcel_of_stardust_fell_to_earth")); }
    public static Identifier model() { return Identifier.parse("destiny:weapon_insert_w222_long_arm/long_arm"); }
    public static Identifier model(WeaponCatalog.Entry entry) {
        entry = LegendaryWeapons.base(entry);
        if (!supports(entry)) throw new IllegalArgumentException("No insert presentation: " + entry);
        return switch (entry.id()) {
            case "long_arm" -> model();
            case "dust_rock_blues" -> Identifier.parse("destiny:weapon_insert_w207_dust_rock_blues/dust_rock_blues");
            case "first_in_last_out" -> Identifier.parse("destiny:weapon_insert_w208_first_in_last_out/first_in_last_out");
            case "ikelos_sg_v1_0_1", "mindbender_s_ambition_adept", "parcel_of_stardust_fell_to_earth" -> Identifier.parse("destiny:weapon_insert_w221_" + entry.id() + "/" + entry.id());
            default -> throw new IllegalArgumentException("No insert presentation: " + entry);
        };
    }
    public static boolean active(ItemStack stack) {
        var b=ACTIVE.get(stack);
        return b!=null && b.owner.getMainHandItem()==stack && b.owner.level()==b.level
                && b.owner.isAlive() && !b.owner.isRemoved() && !b.owner.isSpectator()
                && WeaponLoadout.canUse(b.owner) && !kim.biryeong.destiny.ability.AbilityService.inSuper(b.owner)
                && WeaponItems.entry(stack).filter(WeaponInsertPresentation::supports).isPresent();
    }
    static int intervals(ItemStack stack) {
        return WeaponItems.entry(stack).filter(e -> (e.id().equals("dust_rock_blues") || e.id().equals("first_in_last_out") || e.id().equals("ikelos_sg_v1_0_1") || e.id().equals("mindbender_s_ambition_adept") || e.id().equals("parcel_of_stardust_fell_to_earth") || e.id().equals("long_arm"))).isPresent() ? 60 : STEPS;
    }
    /** Pure transport admission, including the existing six-tick cosmetic return. */
    public static boolean ownedBy(ServerPlayer owner, ItemStack stack) {
        var binding = ACTIVE.get(stack);
        return binding != null && binding.owner == owner && active(stack);
    }
    static void start(ServerPlayer owner, ItemStack stack) {
        if (!WeaponItems.entry(stack).filter(WeaponInsertPresentation::supports).isPresent()) return;
        var old=ACTIVE.get(stack);
        var current=stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY).floats();
        var previous=old==null?List.copyOf(current):old.previous;
        Float saved=previous.size()>SELECTOR_INDEX?previous.get(SELECTOR_INDEX):null;
        Float replaced=current.size()>SELECTOR_INDEX?current.get(SELECTOR_INDEX):null;
        float offset=0;
        int intervals=intervals(stack);
        while (collides(saved,offset,intervals)||collides(replaced,offset,intervals)) offset+=.001f;
        var b=new Binding(owner,previous,offset,intervals); ACTIVE.put(stack,b); write(stack,b,0);
    }
    /** Retire our padding before ADS captures its original float list, not one tick later. */
    static void beforeAim(ServerPlayer owner, ItemStack stack) {
        var b=ACTIVE.get(stack);
        if (b!=null && (b.owner==owner && b.phase==Phase.RETURN || !active(stack))) clear(b.owner,stack);
    }
    /** inserted means a successful actual WeaponCycle transfer this tick, never predicted progress. */
    static void tick(ServerPlayer owner, ItemStack stack, boolean reloading, float progress, boolean inserted) {
        var b=ACTIVE.get(stack);
        if (b==null || b.owner!=owner) return;
        if (!active(stack)) { clear(owner,stack); return; }
        if (reloading) {
            if (inserted) b.phase=Phase.LOOP;
            write(stack,b,progress); return;
        }
        if (inserted) { b.phase=Phase.RETURN; b.returnAt=owner.level().getServer().getTickCount(); }
        if (b.phase!=Phase.RETURN || WeaponAiming.progress(owner)>0) { clear(owner,stack); return; }
        long elapsed=owner.level().getServer().getTickCount()-b.returnAt;
        if (elapsed>=RETURN_TICKS) clear(owner,stack);
        else write(stack,b,elapsed/(float)RETURN_TICKS);
    }
    public static void clear(ServerPlayer owner, ItemStack stack) {
        var b=ACTIVE.get(stack);
        if (b==null || b.owner!=owner || !ACTIVE.remove(stack,b)) return;
        var d=stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY);
        var values=new ArrayList<>(d.floats());
        if (values.size()>SELECTOR_INDEX) {
            if (b.previous.size()>SELECTOR_INDEX) values.set(SELECTOR_INDEX,b.previous.get(SELECTOR_INDEX));
            else if (values.size()>SELECTOR_INDEX+1) values.set(SELECTOR_INDEX,0f);
            else {
                values.remove(SELECTOR_INDEX);
                // Float3 belongs to ADS, 2 to bow and 1 to whole-mag reload. Only trim our padding.
                while (values.size()>b.previous.size() && !values.isEmpty()) {
                    int i=values.size()-1;
                    if (values.get(i)!=0f || i==WeaponAimPresentation.PROGRESS_INDEX && WeaponAimPresentation.active(stack)
                            || i==WeaponBowPresentation.SELECTOR_INDEX && WeaponBowPresentation.active(stack)
                            || i==WeaponReloadPresentation.PROGRESS_INDEX && WeaponReloadPresentation.active(stack)) break;
                    values.remove(i);
                }
            }
        }
        if (!values.equals(d.floats())) stack.set(DataComponents.CUSTOM_MODEL_DATA,
                new CustomModelData(values,d.flags(),d.strings(),d.colors()));
    }
    private static boolean collides(Float value,float offset,int intervals) {
        if (value==null || !Float.isFinite(value)) return false;
        for (int phase=0;phase<3;phase++) for (int i=0;i<=intervals;i++)
            if (Float.compare(value,phase*2+(float)i/intervals+offset)==0) return true;
        return false;
    }
    private static void write(ItemStack stack,Binding b,float progress) {
        float p=Float.isFinite(progress)?Math.clamp(progress,0,1):0;
        float value=b.phase.ordinal()*2+(float)Math.floor(p*b.intervals+1e-6f)/b.intervals+b.offset;
        var d=stack.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,CustomModelData.EMPTY);
        var values=new ArrayList<>(d.floats());
        while (values.size()<=SELECTOR_INDEX) values.add(0f);
        if (Float.compare(values.get(SELECTOR_INDEX),value)==0 && values.size()==d.floats().size()) return;
        values.set(SELECTOR_INDEX,value);
        stack.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(values,d.flags(),d.strings(),d.colors()));
    }
}
