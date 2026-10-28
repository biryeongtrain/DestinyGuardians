package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Server-side interactive equipment screen. HUDs never own inventory and never grant weapons. */
public final class WeaponScreen {
    private static final Map<UUID, Session> OPEN = new HashMap<>();
    private static final net.minecraft.resources.Identifier FREEZE = DestinyGuardians.id("equipment_screen");
    private static final int PAGE_SIZE = 9;
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final Object connection;
        final Vec3 anchor;
        final WeaponScreenControls controls = new WeaponScreenControls();
        WeaponSlot slot = WeaponSlot.KINETIC;
        Input input = Input.EMPTY;
        List<WeaponEquipmentService.Owned> choices = List.of();
        WeaponScreenView view;
        int page, focus, repeatAt, lastClick = Integer.MIN_VALUE / 2, lastActive;
        boolean armed = true;
        String message = "무기 칸을 고른 뒤 소지 무기를 선택하세요.";
        Session(ServerPlayer p) {
            owner = p; level = p.level(); connection = p.connection; anchor = p.position();
            controls.baseline(p.getYRot(), p.getXRot());
            lastActive = p.level().getServer().getTickCount();
        }
    }
    private WeaponScreen() {}

    public static void init() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
            dispatcher.register(Commands.literal("destiny").then(Commands.literal("inventory")
                .executes(c -> open(c.getSource().getPlayerOrException()) ? 1 : 0)
                .then(Commands.literal("close").executes(c -> { close(c.getSource().getPlayerOrException()); return 1; }))
                .then(Commands.literal("open").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                    .then(Commands.argument("player", EntityArgument.player()).executes(c -> open(EntityArgument.getPlayer(c, "player")) ? 1 : 0)))
                .then(Commands.literal("status").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                    .then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                        var p = EntityArgument.getPlayer(c, "player"); var s = current(p);
                        c.getSource().sendSuccess(() -> Component.literal("EquipmentScreen " +
                                (s == null ? "closed" : new Gson().toJson(s.view))), false); return 1;
                    }))))));
        ServerTickEvents.END_SERVER_TICK.register(WeaponScreen::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> close(handler.getPlayer()));
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p, from, to) -> close(p));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> { if (entity instanceof ServerPlayer p) close(p); });
        ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
            if (entity instanceof ServerPlayer p && taken > 0) close(p);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var s : List.copyOf(OPEN.values())) if (s.level.getServer() == server) retire(s);
        });
    }

    public static boolean active(ServerPlayer p) { return current(p) != null; }
    private static Session current(ServerPlayer p) {
        var s = OPEN.get(p.getUUID());
        return s != null && s.owner == p && s.connection == p.connection ? s : null;
    }
    public static boolean toggle(ServerPlayer p) { if (active(p)) { close(p); return true; } return open(p); }
    public static boolean open(ServerPlayer p) {
        if (active(p)) return true;
        if (!p.level().getServer().isSameThread() || !p.isAlive() || p.isRemoved() || p.hasDisconnected()
                || p.isSpectator() || p.isSleeping() || p.isPassenger() || !p.onGround()
                || p.isFallFlying() || p.getAbilities().flying || p.getCamera() != p
                || AbilityService.inSuper(p) || p.containerMenu != p.inventoryMenu) {
            p.sendOverlayMessage(Component.literal("지면에 선 상태에서 현재 동작을 마친 뒤 장비 창을 여세요."));
            return false;
        }
        var old = OPEN.get(p.getUUID()); if (old != null) retire(old);
        WeaponRuntime.cancelUseForSkill(p); WeaponAiming.suspend(p); p.stopUsingItem();
        p.setSprinting(false); p.setShiftKeyDown(false); p.setLastClientInput(Input.EMPTY);
        p.setDeltaMovement(Vec3.ZERO);
        freeze(p, Attributes.MOVEMENT_SPEED); freeze(p, Attributes.JUMP_STRENGTH);
        var s = new Session(p); OPEN.put(p.getUUID(), s);
        var box = WeaponScreenLayout.bounds(0); s.controls.point(box.x(), box.y());
        CombatHud.remove(p); p.inventoryMenu.broadcastFullState(); refresh(s); return true;
    }
    private static void freeze(ServerPlayer p, Holder<Attribute> type) {
        var attr = p.getAttribute(type);
        if (attr != null) { attr.removeModifier(FREEZE); attr.addTransientModifier(new AttributeModifier(FREEZE, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL)); }
    }
    public static void close(ServerPlayer p) { var s = current(p); if (s != null) retire(s); }
    private static void retire(Session s) {
        if (!OPEN.remove(s.owner.getUUID(), s)) return;
        WeaponScreenHud.remove(s.owner);
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = s.owner.getAttribute(type); if (attr != null) attr.removeModifier(FREEZE);
        }
        s.owner.setLastClientInput(Input.EMPTY);
        s.owner.setDeltaMovement(Vec3.ZERO);
        if (!s.owner.hasDisconnected()) s.owner.inventoryMenu.broadcastFullState();
        // Never restore pre-menu keys, a stale camera or a shadow inventory.
    }

    /** Called only after packet thread validation. Suppress position claims, accept finite pointer rotation. */
    public static boolean move(ServerPlayer p, ServerboundMovePlayerPacket packet) {
        var s = current(p); if (s == null) return false;
        if (packet.hasRotation()) {
            float yaw = packet.getYRot(p.getYRot()), pitch = packet.getXRot(p.getXRot());
            if (Float.isFinite(yaw) && Float.isFinite(pitch)) {
                p.setYRot(yaw); p.setYHeadRot(yaw); p.setXRot(Math.clamp(pitch, -90, 90));
                if (s.controls.rotate(yaw, pitch)) {
                    s.focus = WeaponScreenLayout.hit(s.controls.x(), s.controls.y()); s.armed = true; touch(s); render(s);
                }
            }
        }
        if (packet.hasPosition()) {
            double dx = packet.getX(s.anchor.x) - s.anchor.x, dy = packet.getY(s.anchor.y) - s.anchor.y,
                    dz = packet.getZ(s.anchor.z) - s.anchor.z;
            if (!Double.isFinite(dx + dy + dz) || dx * dx + dy * dy + dz * dz > .0001)
                p.connection.teleport(s.anchor.x, s.anchor.y, s.anchor.z, p.getYRot(), p.getXRot());
        }
        return true;
    }
    public static boolean input(ServerPlayer p, Input next) {
        var s = current(p); if (s == null) return false;
        Input old = s.input; s.input = next; touch(s);
        if (next.jump() && !old.jump()) click(p, false);
        if (!next.equals(old)) { s.repeatAt = now(s) + 7; navigate(s); }
        return true;
    }
    private static void navigate(Session s) {
        int dx = (s.input.right() ? 1 : 0) - (s.input.left() ? 1 : 0);
        int dy = (s.input.backward() ? 1 : 0) - (s.input.forward() ? 1 : 0);
        if (dx == 0 && dy == 0) return;
        s.focus = WeaponScreenLayout.navigate(s.focus, dx, dy);
        var b = WeaponScreenLayout.bounds(s.focus); s.controls.point(b.x(), b.y());
        s.armed = true; touch(s); render(s);
    }
    public static boolean click(ServerPlayer p, boolean back) {
        var s = current(p); if (s == null) return false;
        // Several vanilla attack/use packets may represent one click. A hold cannot swap the new grid again.
        int now = now(s); if (now - s.lastClick < 3) return true;
        s.lastClick = now; touch(s);
        if (back) { close(p); return true; }
        if (!s.armed) return true;
        s.armed = false;
        int node = s.focus;
        if (node >= 0 && node < 3) {
            s.slot = WeaponSlot.values()[node]; s.page = 0; s.message = "장착할 소지 무기를 선택하세요."; refresh(s);
        } else if (node >= 3 && node < 12) {
            int index = s.page * PAGE_SIZE + node - 3;
            if (index < s.choices.size()) {
                var choice = s.choices.get(index);
                String error = WeaponEquipmentService.equip(p, choice.inventoryIndex(), choice.stack());
                s.message = error == null ? "장착 완료 · 탄약과 특성 유지" : error;
                refresh(s);
            }
        } else if (node == 12 || node == 13) {
            int pages = Math.max(1, (s.choices.size() + PAGE_SIZE - 1) / PAGE_SIZE);
            s.page = Math.clamp(s.page + (node == 12 ? -1 : 1), 0, pages - 1); render(s);
        } else if (node == 14) close(p);
        return true;
    }
    private static int now(Session s) { return s.level.getServer().getTickCount(); }
    private static void touch(Session s) { s.lastActive = now(s); }
    private static void tick(MinecraftServer server) {
        for (var s : List.copyOf(OPEN.values())) {
            if (s.level.getServer() != server) continue;
            var p = s.owner;
            if (p.hasDisconnected() || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.level() != s.level
                    || p.isPassenger() || p.isSleeping() || p.getCamera() != p || AbilityService.inSuper(p)
                    || p.position().distanceToSqr(s.anchor) > .25 || now(s) - s.lastActive > 2400) { retire(s); continue; }
            p.setDeltaMovement(Vec3.ZERO);
            if (now(s) >= s.repeatAt) { s.repeatAt = now(s) + 4; navigate(s); }
            if (now(s) % 10 == 0) refresh(s);
        }
    }
    private static void refresh(Session s) {
        s.choices = WeaponEquipmentService.owned(s.owner, s.slot).stream().filter(o -> !o.equipped()).toList();
        int pages = Math.max(1, (s.choices.size() + PAGE_SIZE - 1) / PAGE_SIZE);
        s.page = Math.clamp(s.page, 0, pages - 1); render(s);
    }
    private static WeaponScreenView.Card card(int index, ItemStack stack, WeaponCatalog.Entry entry, boolean equipped) {
        var c = WeaponCharacteristics.of(entry); var profile = WeaponProfile.forEntry(entry);
        var ammo = WeaponItems.magazine(stack, profile);
        return new WeaponScreenView.Card(index, entry.id(), entry.name(), entry.family(), entry.source_frame_label(),
                c.slot(), c.damage().name(), c.ammo().name(), c.exotic(), c.stats(), ammo.rounds(), ammo.loadedLimit(), equipped);
    }
    private static void render(Session s) {
        var equipped = WeaponLoadout.equipped(s.owner).stream()
                .map(e -> card(e.slot().hotbar(), e.stack(), e.weapon(), true)).toList();
        var choices = s.choices.stream().skip((long)s.page * PAGE_SIZE).limit(PAGE_SIZE)
                .map(o -> card(o.inventoryIndex(), o.stack(), o.weapon(), o.equipped())).toList();
        WeaponScreenView.Card inspected = s.focus >= 3 && s.focus < 3 + choices.size() ? choices.get(s.focus - 3)
                : equipped.stream().filter(c -> c.slot() == s.slot).findFirst().orElse(choices.isEmpty() ? null : choices.getFirst());
        s.view = new WeaponScreenView(s.owner.getGameProfile().name(), s.slot, equipped, choices, inspected,
                s.page, Math.max(1, (s.choices.size() + PAGE_SIZE - 1) / PAGE_SIZE), s.focus, s.controls.x(), s.controls.y(), s.message);
        WeaponScreenHud.render(s.owner, s.view);
    }
}
