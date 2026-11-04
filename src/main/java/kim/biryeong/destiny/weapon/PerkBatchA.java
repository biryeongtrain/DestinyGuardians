package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** W320 batch A facade: Field Prep, Slideways, Slideshot, Eye of the Storm, Killing Wind, Air Assault,
 * Tunnel Vision, Fragile Focus, Kickstart, Shot Swap, Bait and Switch.
 * Central weapon code calls exactly one method per hook point; this class fans out to the traits.
 * State is per player session and per genuine equipped ItemStack identity (no global mutable buff).
 */
public final class PerkBatchA {
    private static final List<String> IDS = List.of(FieldPrepProfile.ID, SlidewaysProfile.ID, SlideshotProfile.ID,
        EyeOfTheStormProfile.ID, KillingWindProfile.ID, AirAssaultProfile.ID, TunnelVisionProfile.ID,
        FragileFocusProfile.ID, KickstartProfile.ID, ShotSwapProfile.ID, BaitAndSwitchProfile.ID);
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();

    static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final SlideDetector slide = new SlideDetector();
        final ShieldTraitCycle shield = new ShieldTraitCycle();
        final IdentityHashMap<ItemStack, Slot> slots = new IdentityHashMap<>();
        final Set<LivingEntity> corpses = Collections.newSetFromMap(new WeakHashMap<>());
        /** Last observed custom data per equipped stack; selection is re-read only when it changes. */
        final IdentityHashMap<ItemStack, Object> seen = new IdentityHashMap<>();
        Vec3 previous;
        long last = -1;
        double shieldHp = ShieldTraitCycle.MAX_SHIELD;
        ItemStack lastHeld;
        Session(ServerPlayer p) { owner = p; level = p.level(); previous = p.position(); }
    }
    /** One genuine equipped weapon object with at least one selected batch-A trait. */
    static final class Slot {
        final ItemStack stack;
        final WeaponCatalog.Entry entry;
        final Set<String> perks;
        final KillingWindCycle wind = new KillingWindCycle();
        final AirAssaultCycle air = new AirAssaultCycle();
        final ShotSwapCycle swap = new ShotSwapCycle();
        final SlideBuffCycle slideways = new SlideBuffCycle(), slideshot = new SlideBuffCycle();
        final KickstartCycle kickstart = new KickstartCycle();
        final TunnelVisionCycle tunnel = new TunnelVisionCycle();
        final BaitAndSwitchCycle bait = new BaitAndSwitchCycle();
        Slot(ItemStack stack, WeaponCatalog.Entry entry, Set<String> perks) { this.stack = stack; this.entry = entry; this.perks = perks; }
        boolean has(String id) { return perks.contains(id); }
    }
    /** Immutable per-emission capture. Projectiles keep the state they were fired with. */
    public static final class Token {
        public static final Token NONE = new Token(null, null, 1f, 0);
        final ServerPlayer owner;
        final ItemStack source;
        final float multiplier;
        final int ammoBonus;
        private Token(ServerPlayer owner, ItemStack source, float multiplier, int ammoBonus) {
            this.owner = owner; this.source = source; this.multiplier = multiplier; this.ammoBonus = ammoBonus;
        }
    }
    private PerkBatchA() {}

    // ---- registry ----
    public static List<String> ids() { return IDS; }
    public static boolean has(String id) { return IDS.contains(id); }
    public static List<WeaponPerks.Roll> rolls(String id) {
        return switch (id) {
            case FieldPrepProfile.ID -> FieldPrepProfile.rolls();
            case SlidewaysProfile.ID -> SlidewaysProfile.rolls();
            case SlideshotProfile.ID -> SlideshotProfile.rolls();
            case EyeOfTheStormProfile.ID -> EyeOfTheStormProfile.rolls();
            case KillingWindProfile.ID -> KillingWindProfile.rolls();
            case AirAssaultProfile.ID -> AirAssaultProfile.rolls();
            case TunnelVisionProfile.ID -> TunnelVisionProfile.rolls();
            case FragileFocusProfile.ID -> FragileFocusProfile.rolls();
            case KickstartProfile.ID -> KickstartProfile.rolls();
            case ShotSwapProfile.ID -> ShotSwapProfile.rolls();
            case BaitAndSwitchProfile.ID -> BaitAndSwitchProfile.rolls();
            default -> List.of();
        };
    }
    /** Official Korean names (Bungie ko manifest); null for ids outside this batch. */
    public static String name(String id) {
        return switch (id) {
            case FieldPrepProfile.ID -> "야전 준비";
            case SlidewaysProfile.ID -> "미끄럼길";
            case SlideshotProfile.ID -> "슬라이드 사격";
            case EyeOfTheStormProfile.ID -> "폭풍의 눈";
            case KillingWindProfile.ID -> "살육의 바람";
            case AirAssaultProfile.ID -> "공습";
            case TunnelVisionProfile.ID -> "터널 시야";
            case FragileFocusProfile.ID -> "여린 집중";
            case KickstartProfile.ID -> "촉진";
            case ShotSwapProfile.ID -> "사격 교체";
            case BaitAndSwitchProfile.ID -> "미끼와 스위치";
            default -> null;
        };
    }

    // ---- ownership ----
    static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean ownerValid(ServerPlayer p) {
        return p != null && p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected();
    }
    static List<ItemStack> equipped(ServerPlayer p) {
        var result = new ArrayList<ItemStack>();
        if (WeaponLoadout.enabled(p)) for (var e : WeaponLoadout.equipped(p)) result.add(e.stack());
        else for (int i = 0; i < 9; i++) {
            var stack = p.getInventory().getItem(i);
            if (stack.getCount() == 1 && WeaponItems.entry(stack).isPresent()) result.add(stack);
        }
        return result;
    }
    private static Set<String> selected(ItemStack stack, WeaponCatalog.Entry entry) {
        var result = new HashSet<String>();
        for (var id : IDS) WeaponPerks.selected(stack, id)
            .filter(r -> r.id().equals(entry.id()) && rolls(id).contains(r)).ifPresent(r -> result.add(id));
        return Set.copyOf(result);
    }
    private static Session session(ServerPlayer p) {
        var s = SESSIONS.get(p.getUUID());
        return s != null && s.owner == p && s.level == p.level() ? s : null;
    }
    /** Equipped genuine slot of this exact stack, or null. */
    static Slot slot(ServerPlayer p, ItemStack stack) {
        if (!ownerValid(p) || stack == null) return null;
        update(p);
        var s = session(p);
        return s == null ? null : s.slots.get(stack);
    }
    /** Held, currently usable slot (loadout permits use, not in a Super). */
    static Slot held(ServerPlayer p) {
        if (!ownerValid(p) || AbilityService.inSuper(p) || !WeaponLoadout.canUse(p)) return null;
        return slot(p, p.getMainHandItem());
    }
    static double shield(ServerPlayer p) { var s = session(p); return s == null ? ShieldTraitCycle.MAX_SHIELD : s.shieldHp; }
    static ShieldTraitCycle shieldCycle(ServerPlayer p) { var s = session(p); return s == null ? null : s.shield; }
    /** Guardian shield HP from the single Minecraft health bar: PvE 200=70+130, Crucible 230=100+130. */
    static double shieldHp(ServerPlayer p) {
        boolean crucible = CrucibleRuntime.participating(p);
        double total = crucible ? 230 : 200, health = crucible ? 100 : 70;
        float max = p.getMaxHealth();
        if (!Float.isFinite(max) || max <= 0) return ShieldTraitCycle.MAX_SHIELD;
        return Math.clamp(p.getHealth() * total / max - health, 0, ShieldTraitCycle.MAX_SHIELD);
    }

    // ---- lifecycle ----
    public static void update(ServerPlayer p) {
        if (!ownerValid(p)) { cleanup(p); return; }
        var s = session(p);
        if (s == null) {
            var old = SESSIONS.get(p.getUUID());
            if (old != null && old.owner == p) cleanup(p);
            s = new Session(p);
            SESSIONS.put(p.getUUID(), s);
        }
        long tick = now(p);
        if (s.last == tick) return;
        s.last = tick;
        var equipped = equipped(p);
        s.slots.keySet().removeIf(stack -> equipped.stream().noneMatch(e -> e == stack));
        s.seen.keySet().removeIf(stack -> equipped.stream().noneMatch(e -> e == stack));
        for (var stack : equipped) {
            var data = stack.get(net.minecraft.core.component.DataComponents.CUSTOM_DATA);
            if (data != null && s.seen.get(stack) == data) continue;
            s.seen.put(stack, data);
            var entry = WeaponItems.entry(stack).orElse(null);
            if (entry == null) { s.slots.remove(stack); continue; }
            var existing = s.slots.get(stack);
            var perks = selected(stack, entry);
            if (perks.isEmpty()) { s.slots.remove(stack); continue; }
            if (existing == null || !existing.entry.equals(entry) || !existing.perks.equals(perks))
                s.slots.put(stack, new Slot(stack, entry, perks));
        }
        s.shieldHp = shieldHp(p);
        s.shield.sample(tick, s.shieldHp, EyeOfTheStormProfile.triggerShield(), EyeOfTheStormProfile.fullShield(),
            FragileFocusProfile.reactivateTicks());
        var pos = p.position();
        double dx = pos.x - s.previous.x, dz = pos.z - s.previous.z;
        double speed = p.isPassenger() ? 0 : Math.sqrt(dx * dx + dz * dz);
        s.previous = pos;
        boolean slid = s.slide.sample(tick, p.onGround(), p.isSprinting(), p.isCrouching(), speed);
        var held = p.getMainHandItem();
        if (s.lastHeld != null && s.lastHeld != held) {
            var outgoing = s.slots.get(s.lastHeld);
            if (outgoing != null) stowed(outgoing, false);
        }
        s.lastHeld = held;
        if (slid) {
            var slot = held(p);
            if (slot != null) {
                WeaponSlideways.slide(p, slot, tick);
                WeaponSlideshot.slide(p, slot, tick);
                WeaponKickstart.slide(slot, tick, s.slide.sprintTicksAtSlide());
            }
        }
        WeaponKillingWind.movement(p, held(p));
    }
    private static void stowed(Slot slot, boolean consumeSwap) {
        if (consumeSwap && slot.has(ShotSwapProfile.ID)) slot.swap.stowed();
        slot.slideways.stowed(); slot.slideshot.stowed(); slot.wind.stowed(); slot.air.stowed();
    }
    /** Real stow transaction (WeaponHandling selection), after the outgoing stow duration was computed. */
    public static void stowing(ServerPlayer p, ItemStack stack) {
        var slot = slot(p, stack);
        if (slot != null) stowed(slot, true);
    }
    public static void edited(ItemStack stack) {
        if (stack == null) return;
        for (var s : SESSIONS.values()) { s.slots.remove(stack); s.seen.remove(stack); }
    }
    public static void changed(ServerPlayer p, ItemStack stack) {
        var s = p == null ? null : SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) { s.slots.remove(stack); s.seen.remove(stack); }
    }
    public static void cleanup(ServerPlayer p) {
        if (p == null) return;
        WeaponKillingWind.release(p);
        var s = SESSIONS.get(p.getUUID());
        if (s != null && s.owner == p) SESSIONS.remove(p.getUUID());
    }
    public static void clear() { WeaponKillingWind.clear(); SESSIONS.clear(); }

    // ---- combat ----
    public static Token capture(ServerPlayer p) {
        if (!ownerValid(p)) return Token.NONE;
        update(p);
        var stack = p.getMainHandItem();
        var slot = held(p);
        float multiplier = 1f;
        int ammo = 0;
        if (slot != null) {
            long tick = now(p);
            multiplier *= WeaponKickstart.multiplier(slot, tick) * WeaponBaitAndSwitch.multiplier(slot, tick);
            ammo = WeaponFieldPrep.ammoGenerationBonus(slot);
        }
        return new Token(p, stack, multiplier, ammo);
    }
    public static float multiplier(ServerPlayer owner, Token token) {
        return token == null || token.owner != owner ? 1f : token.multiplier;
    }
    public static AmmoGeneration ammoGeneration(AmmoGeneration attribution, Token token) {
        if (token == null || token.ammoBonus == 0 || attribution == null) return attribution;
        return switch (attribution.kind()) {
            case PRIMARY, SPECIAL, HEAVY -> new AmmoGeneration(attribution.kind(), attribution.stat() + token.ammoBonus);
            default -> attribution;
        };
    }
    /** After positive actual weapon damage; killed is the confirmed final blow of this transaction. */
    public static void confirmed(ServerPlayer owner, Token token, LivingEntity target, float actual, boolean killed) {
        if (token == null || token.owner != owner || token.source == null || !ownerValid(owner) || !(actual > 0)) return;
        update(owner);
        var s = session(owner);
        long tick = now(owner);
        if (s != null) WeaponBaitAndSwitch.damaged(owner, s, token.source, tick);
        if (!killed || s == null || target == null || target == owner || !s.corpses.add(target)) return;
        var slot = s.slots.get(token.source);
        if (slot == null) return;
        boolean heldNow = owner.getMainHandItem() == token.source;
        if (heldNow) {
            WeaponKillingWind.killed(slot, tick);
            WeaponAirAssault.killed(owner, slot, tick);
        }
        WeaponShotSwap.killed(slot);
        WeaponTunnelVision.killed(slot, tick);
    }
    public static void reloadFinished(ServerPlayer p, ItemStack stack) {
        var slot = slot(p, stack);
        if (slot != null) WeaponTunnelVision.reloadFinished(slot, now(p));
    }
    /** After the paid emission's first shot was emitted and its recoil applied. */
    public static void paidEmission(ServerPlayer p, WeaponCatalog.Entry entry) {
        var slot = held(p);
        if (slot != null && slot.entry.equals(entry)) WeaponSlideshot.shot(slot);
    }

    // ---- stat hooks (held weapon unless noted) ----
    public static int stabilityBonus(ServerPlayer p) {
        var slot = held(p);
        if (slot == null) return 0;
        long tick = now(p);
        return WeaponSlideways.stabilityBonus(slot, tick) + WeaponSlideshot.stabilityBonus(slot, tick);
    }
    public static int rangeBonus(ServerPlayer p) {
        var slot = held(p);
        if (slot == null) return 0;
        long tick = now(p);
        return WeaponSlideshot.rangeBonus(slot, tick) + WeaponKillingWind.rangeBonus(slot, tick) + WeaponFragileFocus.rangeBonus(p, slot);
    }
    public static WeaponBallistics.Profile falloff(ServerPlayer p, WeaponCatalog.Entry entry, WeaponBallistics.Profile hip) {
        var slot = held(p);
        if (slot == null || !slot.entry.equals(entry)) return hip;
        double scalar = WeaponKillingWind.falloffScalar(slot, now(p));
        return scalar == 1 ? hip : new WeaponBallistics.Profile(hip.start() * scalar, hip.end() * scalar, hip.floor(), hip.precision());
    }
    public static double accuracyScalar(ServerPlayer p) {
        var slot = held(p);
        return slot == null ? 1 : WeaponEyeOfTheStorm.coneScalar(p, slot);
    }
    public static double growthScalar(ServerPlayer p) {
        var slot = held(p);
        return slot == null ? 1 : WeaponEyeOfTheStorm.growthScalar(p, slot) * WeaponTunnelVision.growthScalar(slot, now(p));
    }
    public static int airborneBonus(ServerPlayer p) {
        var slot = held(p);
        return slot == null ? 0 : WeaponAirAssault.airborneBonus(slot, now(p));
    }
    /** Ready/stow of any genuine equipped stack (outgoing or incoming). */
    public static int handlingTicks(ServerPlayer p, ItemStack stack, boolean ready, int base) {
        var slot = slot(p, stack);
        if (slot == null || base <= 0) return base;
        long tick = now(p);
        double bonus = WeaponSlideways.handlingBonus(slot, tick) + WeaponEyeOfTheStorm.handlingBonus(p, slot)
            + WeaponKillingWind.handlingBonus(slot, tick) + WeaponShotSwap.handlingBonus(slot);
        double scalar = WeaponFieldPrep.handlingScalar(p, slot) * WeaponShotSwap.durationScalar(slot);
        return WeaponStatCurves.handlingTicks(slot.entry.id(), ready, base, bonus, scalar);
    }
    public static int adsTicks(ServerPlayer p, WeaponCatalog.Entry entry, int base, boolean entering) {
        var slot = held(p);
        if (slot == null || !slot.entry.equals(entry)) return base;
        long tick = now(p);
        double bonus = WeaponSlideways.handlingBonus(slot, tick) + WeaponEyeOfTheStorm.handlingBonus(p, slot)
            + WeaponKillingWind.handlingBonus(slot, tick);
        return WeaponStatCurves.adsTicks(entry.id(), base, bonus, WeaponTunnelVision.adsScalar(slot, tick));
    }
    public static WeaponReloadPolicy.Plan plan(ServerPlayer p, WeaponCatalog.Entry entry, WeaponReloadPolicy.Plan plan) {
        var slot = held(p);
        if (slot == null || !slot.entry.equals(entry)) return plan;
        return WeaponFieldPrep.plan(p, slot, plan);
    }
    public static WeaponProfile charge(ServerPlayer p, WeaponCatalog.Entry entry, WeaponProfile profile) {
        var slot = held(p);
        if (slot == null || !slot.entry.equals(entry)) return profile;
        return WeaponKickstart.charge(slot, now(p), profile);
    }
}
