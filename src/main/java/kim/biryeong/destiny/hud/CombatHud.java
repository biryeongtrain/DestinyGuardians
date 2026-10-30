package kim.biryeong.destiny.hud;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;

import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Destiny-style combat HUD: upper-centre vitals and lower-left ability cluster.
 * All imagery is original, pack-backed flat quads, not visible debug text or vanilla item icons.
 * Vanilla player-heart sprites are transparent in the required pack; vitals therefore cover non-guardians too.
 */
public final class CombatHud {
    private static final String PREFIX = "destiny:hud_";
    public static final String ABILITIES_ID = PREFIX + "abilities";
    public static final String SUPER_ID = PREFIX + "super";
    public static final String HEALTH_ID = PREFIX + "health";
    public static final String ABSORPTION_ID = PREFIX + "absorption";
    public static final String READY_ID = PREFIX + "ready_banner";
    public static final String READY_ECHO_ID = PREFIX + "ready_echo";
    public static final String CAST_ID = PREFIX + "cast_flash";
    private static final String SWEEP_ID = PREFIX + "ready_sweep";
    private static final Map<UUID, SuperHudCue> CUES = new HashMap<>();
    private static final Map<UUID, String> LAST = new HashMap<>();
    private static final int WHITE = 0xF1F3F5;
    private static final int GOLD = 0xF4D36A;
    private static final int MUTED = 0x606872;
    private static final AbilitySlot[] SLOTS = {AbilitySlot.GRENADE, AbilitySlot.MELEE, AbilitySlot.CLASS_ABILITY};

    private CombatHud() { }

    public static float healthFraction(ServerPlayer player) {
        return fraction(player.getHealth(), player.getMaxHealth());
    }

    /** Cooldown fill is an actual charge fraction, not a fabricated timer. */
    public static float charge(ServerPlayer player, AbilitySlot slot) {
        Ability ability = AbilityService.equipped(player, slot).orElse(null);
        return ability == null ? 0f : Math.clamp(1f - fraction(Guardians.data(player).cooldown(slot),
                Math.max(1, ability.cooldownTicks())), 0f, 1f);
    }

    private static float fraction(float value, float max) {
        return Float.isFinite(value) && Float.isFinite(max) && max > 0 ? Math.clamp(value / max, 0f, 1f) : 0f;
    }

    public static void update(ServerPlayer player) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(player)) { remove(player); return; }
        if (player.isDeadOrDying() || player.isSpectator()) {
            remove(player);
            return;
        }
        // The pack is shared by the whole server, so every living player needs a health replacement.
        bar(player, HEALTH_ID + "_track", 744, 76, 432, 13, 1, 0x3C414A, DisplayHud.HudAlignment.CENTER);
        bar(player, HEALTH_ID, 748, 76, 424 * healthFraction(player), 7, 2,
                healthFraction(player) <= 0.3f ? 0xE75A4E : WHITE, DisplayHud.HudAlignment.CENTER);
        float absorption = fraction(player.getAbsorptionAmount(), player.getMaxHealth());
        bar(player, ABSORPTION_ID, 748, 65, 424 * absorption, 4, 2, 0x9DDBEE, DisplayHud.HudAlignment.CENTER);
        AmmoHud.update(player);
        AmmoMeterHud.update(player);
        WeaponPerkHud.update(player);
        WeaponScopeHud.update(player, kim.biryeong.destiny.weapon.WeaponRuntime.reloading(player));
        WeaponReticleHud.update(player, kim.biryeong.destiny.weapon.WeaponAiming.progress(player),
                kim.biryeong.destiny.weapon.WeaponAiming.bloom(player),kim.biryeong.destiny.weapon.WeaponRuntime.reloading(player));
        AceReticleCounter.update(player);
        WeaponHitHud.update(player);
        FallbackAimHud.update(player);
        IncomingDamageHud.update(player);
        if (!Guardians.isGuardian(player)) {
            removeAbilities(player);
            LAST.put(player.getUUID(), "체력 " + player.getHealth() + "/" + player.getMaxHealth());
            return;
        }
        GuardianData data = Guardians.data(player);
        var runtime = Guardians.runtime(player);
        Ability superAbility = AbilityService.equipped(player, AbilitySlot.SUPER).orElse(null);
        Element element = superAbility == null ? Element.KINETIC : superAbility.element();
        boolean active = runtime.superSession != null;
        float superCharge = Math.clamp(active ? runtime.superSession.remaining() : data.superEnergy(), 0f, 1f);
        boolean ready = active || data.superEnergy() >= 1f;

        sprite(player, PREFIX + "super_diamond", ready && !active ? "diamond_ready" : "diamond", 120, 856, 80, 80, 1,
                ready ? GOLD : MUTED, DisplayHud.HudAlignment.LEFT);
        sprite(player, PREFIX + "super_icon", superIcon(superAbility), 120, 856, 44, 44, 2,
                ready && !active ? 0x292820 : ready ? GOLD : WHITE, DisplayHud.HudAlignment.LEFT);
        bar(player, SUPER_ID + "_track", 176, 856, 230, 8, 1, 0x3C414A, DisplayHud.HudAlignment.LEFT);
        bar(player, SUPER_ID, 176, 856, 230 * superCharge, 5, 2, ready ? GOLD : WHITE, DisplayHud.HudAlignment.LEFT);

        updateSuperCue(player, superAbility, ready && !active, active, element);

        StringBuilder debug = new StringBuilder("체력=" + player.getHealth());
        for (int i = 0; i < SLOTS.length; i++) {
            AbilitySlot slot = SLOTS[i];
            Ability ability = AbilityService.equipped(player, slot).orElse(null);
            var sword = slot == AbilitySlot.MELEE ? kim.biryeong.destiny.weapon.WeaponRuntime.swordStatus(player)
                    : java.util.Optional.<kim.biryeong.destiny.weapon.WeaponRuntime.SwordStatus>empty();
            int tint = sword.isPresent() ? (sword.get().guarding()?0x95ECF8:WHITE)
                    : ability == null ? MUTED : ability.element().color();
            float progress = sword.isPresent() ? sword.get().energy() : charge(player, slot);
            float x = 104 + i * 70;
            String id = i == 0 ? ABILITIES_ID : ABILITIES_ID + "_" + i;
            sprite(player, id, "tile", x, 948, 53, 53, 1, progress >= 1 ? WHITE : MUTED, DisplayHud.HudAlignment.LEFT);
            sprite(player, id + "_icon", sword.isPresent()?"ammo_sword":icon(slot, ability), x, 948, 37, 37, 2,
                    progress >= 1 ? WHITE : 0x747C86, DisplayHud.HudAlignment.LEFT);
            bar(player, id + "_charge", x - 24, 980, 48 * progress, 4, 2,
                    progress >= 1 ? tint : WHITE, DisplayHud.HudAlignment.LEFT);
            if(sword.isPresent()) { debug.append("|검 에너지 ").append(Math.round(progress*100)).append('%'); continue; }
            debug.append('|').append(switch(slot) {
                case GRENADE -> "수류탄 "; case MELEE -> "근접 "; default -> "직업 ";
            }).append(data.cooldown(slot) > 0 ? (data.cooldown(slot) + 19) / 20 + "s" : "ready");
        }
        AbilityKeyHud.update(player);
        LAST.put(player.getUUID(), debug.append("|궁극기 ").append(Math.round(superCharge * 100)).append('%').toString());
    }

    private static void updateSuperCue(ServerPlayer player, Ability ability, boolean ready, boolean active, Element element) {
        int now = player.level().getServer().getTickCount();
        SuperHudCue cue = CUES.computeIfAbsent(player.getUUID(), ignored -> new SuperHudCue());
        if (cue.sample(now, ability == null ? null : ability.id(), ready, active))
            kim.biryeong.destiny.sound.DestinySounds.ready(player);
        int age = cue.readyAge(now);
        if (age >= 0 && age < SuperHudCue.READY_TICKS) {
            // Two-tick steps bound metadata traffic. The texture itself carries the alpha envelope.
            int frame = age < 6 ? age / 2 : age < 44 ? 3 : 4 + (age - 44) / 4;
            float opening = Math.min(1f, (age / 2 * 2) / 6f);
            sprite(player, READY_ID, "ready_banner_" + frame, 960, 402,
                    560 * (0.94f + 0.06f * opening), 112, 4, GOLD, DisplayHud.HudAlignment.CENTER);
            if (age < 20) {
                int step = age / 2;
                sprite(player, READY_ECHO_ID, "ready_echo_" + Math.min(3, step / 3), 120, 856,
                        88 + step * 5, 88 + step * 5, 3, GOLD, DisplayHud.HudAlignment.LEFT);
                bar(player, SWEEP_ID, 176 + step * 22, 856, 12, 9, 3, 0xFFF4C8, DisplayHud.HudAlignment.LEFT);
            } else {
                DisplayHud.removeHud(player, READY_ECHO_ID);
                DisplayHud.removeHud(player, SWEEP_ID);
            }
        } else {
            DisplayHud.removeHud(player, READY_ID);
            DisplayHud.removeHud(player, READY_ECHO_ID);
            DisplayHud.removeHud(player, SWEEP_ID);
        }
        int castAge = cue.castAge(now);
        if (castAge >= 0 && castAge < SuperHudCue.CAST_TICKS) {
            // Short peripheral release, not a full-screen flash. Existing post-effect ownership is untouched.
            int stage = castAge / 2;
            sprite(player, CAST_ID, "cast_flash_" + stage, 960, 540, 1920, 1080, 3,
                    element.glow(), DisplayHud.HudAlignment.CENTER);
        } else DisplayHud.removeHud(player, CAST_ID);
    }

    private static String icon(AbilitySlot slot, Ability ability) {
        if (ability != null && ability.guardianClass() == kim.biryeong.destiny.guardian.GuardianClass.TITAN) {
            if (slot == AbilitySlot.CLASS_ABILITY) return "titan_barricade";
            if (slot == AbilitySlot.MELEE) return switch (ability.element()) {
                case SOLAR -> "titan_hammer"; case VOID -> "titan_shield"; default -> "fist";
            };
        }
        if (ability != null && ability.guardianClass() == kim.biryeong.destiny.guardian.GuardianClass.WARLOCK) {
            if (slot == AbilitySlot.CLASS_ABILITY) return "warlock_rift";
            if (slot == AbilitySlot.MELEE) return switch (ability.element()) {
                case SOLAR -> "warlock_snap"; case VOID -> "warlock_singularity"; default -> "warlock_storm";
            };
        }
        if (slot == AbilitySlot.CLASS_ABILITY) return "dodge";
        Element element = ability == null ? Element.KINETIC : ability.element();
        if (slot == AbilitySlot.GRENADE) return switch (element) {
            case ARC -> "flash"; case SOLAR -> "flame"; default -> "vortex";
        };
        return switch (element) { case ARC -> "fist"; case SOLAR -> "knife"; default -> "smoke"; };
    }

    static String superIcon(Ability ability) {
        if (ability != null && kim.biryeong.destiny.fx.ClassSuperModelAssets.isExpanded(ability.id().getPath()))
            return "w230_" + ability.id().getPath().substring(ability.id().getPath().indexOf('/') + 1);
        Element element = ability == null ? Element.KINETIC : ability.element();
        if (ability != null) {
            if (ability.guardianClass() == kim.biryeong.destiny.guardian.GuardianClass.TITAN)
                return switch (element) { case SOLAR -> "titan_hammer"; case VOID -> "titan_shield"; default -> "titan_havoc"; };
            if (ability.guardianClass() == kim.biryeong.destiny.guardian.GuardianClass.WARLOCK)
                return switch (element) { case SOLAR -> "warlock_daybreak"; case VOID -> "warlock_nova"; default -> "warlock_storm"; };
        }
        return switch (element) { case ARC -> "staff"; case SOLAR -> "gun"; default -> "bow"; };
    }

    /** Diagnostic state only; never rendered as a line of HUD text. */
    public static String lastText(ServerPlayer player) { return LAST.get(player.getUUID()); }

    public static void remove(ServerPlayer player) {
        IncomingDamageHud.cleanup(player);
        AceReticleCounter.remove(player);
        WeaponHitHud.remove(player);
        WeaponReticleHud.remove(player);
        WeaponScopeHud.remove(player);
        FallbackAimHud.remove(player);
        LAST.remove(player.getUUID());
        CUES.remove(player.getUUID());
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX)) DisplayHud.removeHud(player, id);
        }
    }

    private static void removeAbilities(ServerPlayer player) {
        CUES.remove(player.getUUID());
        for (String id : List.copyOf(DisplayHud.getHuds(player).keySet())) {
            if (id.startsWith(PREFIX) && !id.startsWith(HEALTH_ID) && !id.equals(ABSORPTION_ID)
                    && !id.startsWith(AmmoHud.PREFIX) && !id.startsWith(AmmoMeterHud.PREFIX)
                    && !id.startsWith(WeaponPerkHud.PREFIX) && !id.startsWith(IncomingDamageHud.PREFIX)) {
                DisplayHud.removeHud(player, id);
            }
        }
    }

    static void bar(ServerPlayer player, String id, float left, float y, float width, float height,
                            float z, int color, DisplayHud.HudAlignment align) {
        width = Math.round(width * 2) / 2f;
        if (width <= 0.01f) { DisplayHud.removeHud(player, id); return; }
        sprite(player, id, "solid", left + width / 2, y, width, height, z, color, align);
    }

    static void sprite(ServerPlayer player, String id, String image, float x, float y,
                               float width, float height, float z, int color, DisplayHud.HudAlignment align) {
        // The native offhand model occupies the lower-left corner. Only affected left-aligned
        // HUDs request the existing DisplayHud above-hand pass; ordinary/centre HUDs keep their path.
        boolean aboveHand = align == DisplayHud.HudAlignment.LEFT && !player.getOffhandItem().isEmpty();
        String key = image + ":" + color + ":" + Math.round(width * 10) + ":" + height + ":" + x + ":" + y + ":" + z + ":" + align + ":" + aboveHand;
        DisplayHud existing = DisplayHud.getHud(player, id);
        if (existing != null && key.equals(existing.getExtraData("state"))) return;
        ItemDisplayHud hud = existing instanceof ItemDisplayHud item ? item : new ItemDisplayHud();
        hud.updateWhenDataChanged(false);
        ItemStack stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + image));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
        hud.setItem(stack);
        hud.setItemTransform(ItemDisplayContext.NONE);
        hud.setScale(width, height, 1);
        hud.setAlignment(align);
        hud.setLocation(x, y, z);
        hud.setViewRange(1000);
        hud.setExtraData("state", key);
        hud.setAboveHand(aboveHand);
        if (existing == null) hud.spawn(player, id);
        hud.updateWhenDataChanged(true);
        hud.update();
    }
}
