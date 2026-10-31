package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.item.ItemStack;
import java.util.*;

/** GCB's authenticated button transitions, independent of vanilla use-item prediction. */
public final class GcbWeaponInput {
    // Legacy GCB has no screen/focus signal or heartbeat. Bound a lost-release trigger.
    public static final int MAX_FIRE_HOLD_TICKS = 300;
    private static final Map<UUID, State> STATES = new HashMap<>();
    private static final class State {
        final ServerPlayer owner;
        boolean attackDown, useDown;
        ItemStack fire, aim;
        int fireStarted;
        ServerLevel fireLevel, aimLevel;
        State(ServerPlayer owner) { this.owner = owner; }
    }
    private GcbWeaponInput() { }
    public static boolean remapped(ServerPlayer p) {
        return ClientControls.gcb(p) && WeaponItems.entry(p.getMainHandItem())
                .filter(e -> !e.family().equals("sword")).isPresent();
    }
    private static boolean usable(ServerPlayer p) {
        return remapped(p) && WeaponRuntime.available(p) && !WeaponScreen.active(p)
                && p.containerMenu == p.inventoryMenu && CameraViews.get(p) == null
                && !kim.biryeong.destiny.camera.SuperCamera.active(p) && p.getCamera() == p;
    }
    private static State state(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s == null || s.owner != p) { s = new State(p); STATES.put(p.getUUID(), s); }
        return s;
    }
    /** attack=true is KEY_ATTACK; false is KEY_USE. Release is accepted even inside menus. */
    public static void key(ServerPlayer p, boolean attack, boolean pressed) {
        if (!ClientControls.gcb(p)) return;
        var s = state(p);
        boolean old = attack ? s.attackDown : s.useDown;
        if (old == pressed) return;
        if (attack) s.attackDown = pressed; else s.useDown = pressed;
        if (!pressed) {
            if (attack) {
                var released = s.fire;
                boolean valid = released != null && released == p.getMainHandItem()
                        && s.fireLevel == p.level() && usable(p);
                // Retain token during release: an empty shot's reload observes the real held source.
                if (valid) WeaponRuntime.releaseUse(p, released);
                else if (released != null) WeaponRuntime.cancelUseForSkill(p);
                s.fire = null;
            } else { s.aim = null; WeaponAiming.releasedAim(p); }
            return;
        }
        if (!usable(p)) return;
        if (attack) {
            s.fire = p.getMainHandItem(); s.fireLevel = p.level();
            s.fireStarted = p.level().getServer().getTickCount();
            if (!WeaponRuntime.beginUse(p)) s.fire = null;
        } else if (GlaiveItems.isGlaive(p.getMainHandItem())) {
            WeaponRuntime.onPunch(p);
        } else if (WeaponAimProfile.supports(WeaponItems.entry(p.getMainHandItem()).orElseThrow())) {
            s.aim = p.getMainHandItem(); s.aimLevel = p.level();
            WeaponAiming.hold(p, true);
        }
    }
    public static boolean buttonsDown(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        return s != null && s.owner == p && (s.attackDown || s.useDown);
    }
    public static boolean firing(ServerPlayer p, ItemStack stack) {
        var s = STATES.get(p.getUUID());
        return s != null && s.owner == p && s.attackDown && s.fire == stack
                && stack == p.getMainHandItem() && s.fireLevel == p.level() && usable(p);
    }
    public static void tick(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s == null || s.owner != p) return;
        if (!usable(p) || (s.fire != null && (s.fire != p.getMainHandItem() || s.fireLevel != p.level()))
                || (s.aim != null && (s.aim != p.getMainHandItem() || s.aimLevel != p.level()))) {
            if (s.fire != null || s.aim != null) WeaponRuntime.cancelUseForSkill(p);
            return;
        }
        if (s.fire != null && p.level().getServer().getTickCount() - s.fireStarted >= MAX_FIRE_HOLD_TICKS) {
            WeaponRuntime.cancelTrigger(p);
            p.sendOverlayMessage(net.minecraft.network.chat.Component.literal("발사 버튼을 놓았다 다시 눌러 주세요."));
        }
        if (s.useDown && s.aim != null) WeaponAiming.hold(p, true);
    }
    /** Invalidates tokens but keeps down edges: holding through cancellation cannot restart. */
    public static void cancel(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s != null && s.owner == p) { s.fire = null; s.aim = null; }
        WeaponAiming.releasedAim(p);
    }
    public static void cancelFire(ServerPlayer p) {
        var s = STATES.get(p.getUUID());
        if (s != null && s.owner == p) s.fire = null;
    }
    public static void cleanup(ServerPlayer p) {
        cancel(p);
        var s = STATES.get(p.getUUID());
        if (s != null && s.owner == p) STATES.remove(p.getUUID());
    }
    public static void clearAll() { STATES.clear(); }
}
