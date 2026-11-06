package kim.biryeong.destiny.inventory.gear;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.inventory.WeaponEquipmentService;
import kim.biryeong.destiny.inventory.WeaponStorage;
import kim.biryeong.destiny.inventory.WeaponHotbarGuard;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.inventory.WeaponScreenControls;
import kim.biryeong.destiny.inventory.WeaponScreenLayout.Box;
import kim.biryeong.destiny.inventory.WeaponScreenView;
import kim.biryeong.destiny.inventory.gear.GearLayout.Stage;
import kim.biryeong.destiny.weapon.WeaponAiming;
import kim.biryeong.destiny.weapon.WeaponRuntime;
import kim.biryeong.destiny.weapon.WeaponSlot;
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
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Destiny character gear screen (replaces the debug loadout wizard for players). Opens in combat: the Guardian
 * stands still but takes damage and gravity as normal. Weapons come only from the player's real stacks; equipping
 * swaps an owned stack into its hotbar slot through {@link WeaponEquipmentService}. Perks are read from the
 * stack and cannot be edited here. Armour and ghost slots are display-only. One session per player, server thread.
 */
public final class GearScreen {
    private static final Map<UUID, Session> OPEN = new HashMap<>();
    private static final net.minecraft.resources.Identifier FREEZE = DestinyGuardians.id("gear_screen");
    /** Delay before a hover tooltip appears, and the Destiny 175 ms fade (3-4 ticks). */
    static final int TOOLTIP_DELAY = 2;

    static final class Session {
        final ServerPlayer owner; final ServerLevel level; final Object connection;
        Vec3 anchor;
        final WeaponScreenControls controls = new WeaponScreenControls();
        Stage stage = Stage.GEAR;
        GearSlot expanded;
        int focus = -1, hoverSince, lastClick = Integer.MIN_VALUE / 2, lastActive, openedAt;
        /** W325 dismantle confirmation: the inventory index armed by the first Q and its expiry tick. */
        int dismantleIndex = -1, dismantleUntil;
        Input input = Input.EMPTY;
        String message = "";
        int messageUntil;
        GearItems.Weapon detail;
        String field = "CLASS";
        List<WeaponScreenView.CharacterField> fields = List.of();
        List<WeaponScreenView.CharacterOption> options = List.of();
        final EnumMap<WeaponSlot, GearItems.Bucket> buckets = new EnumMap<>(WeaponSlot.class);
        final EnumMap<WeaponSlot, Integer> storagePages = new EnumMap<>(WeaponSlot.class);
        GearView view;
        Session(ServerPlayer p) {
            owner = p; level = p.level(); connection = p.connection; anchor = p.position();
            controls.baseline(p.getYRot(), p.getXRot());
            controls.point(960, 540);
            lastActive = openedAt = p.level().getServer().getTickCount();
        }
    }

    private GearScreen() { }

    public static void init() {
        GearAcquisition.init();
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents.END_SERVER_TICK.register(GearScreen::tick);
        net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents.DISCONNECT.register((h, s) -> {
            close(h.getPlayer());
            kim.biryeong.destiny.inventory.PlayerFigure.forget(h.getPlayer().getUUID());
        });
        net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p, a, b) -> close(p));
        net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents.AFTER_DEATH.register((e, s) -> { if (e instanceof ServerPlayer p) close(p); });
        net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var s : List.copyOf(OPEN.values())) if (s.level.getServer() == server) retire(s);
        });
    }

    public static boolean active(ServerPlayer p) { return current(p) != null; }
    public static Optional<GearView> snapshot(ServerPlayer p) { var s = current(p); return s == null ? Optional.empty() : Optional.ofNullable(s.view); }
    private static Session current(ServerPlayer p) {
        var s = OPEN.get(p.getUUID());
        return s != null && s.owner == p && s.connection == p.connection ? s : null;
    }

    /** Null when the screen may open now, otherwise the reason. Combat and airborne states are allowed. */
    static String blocked(ServerPlayer p) {
        if (kim.biryeong.destiny.tutorial.TutorialLoan.active(p)) return "무기군 실습 중입니다. 대표 무기로 표적을 처치하면 다음 무기를 드립니다.";
        if (!p.level().getServer().isSameThread() || !p.isAlive() || p.isRemoved() || p.hasDisconnected() || p.isSpectator())
            return "지금은 장비 화면을 열 수 없습니다.";
        if (p.isSleeping() || p.isPassenger() || p.getCamera() != p || AbilityService.inSuper(p)
                || kim.biryeong.destiny.down.GuardianDown.active(p) || p.containerMenu != p.inventoryMenu)
            return "현재 동작을 마친 뒤 장비 화면을 여세요.";
        return null;
    }

    public static boolean open(ServerPlayer p) {
        if (active(p)) return true;
        String reason = blocked(p);
        if (reason != null) { p.sendOverlayMessage(Component.literal(reason)); return false; }
        WeaponStorage.migrate(p);
        var old = OPEN.get(p.getUUID()); if (old != null) retire(old);
        WeaponRuntime.cancelUseForSkill(p); WeaponAiming.suspend(p); p.stopUsingItem();
        p.setSprinting(false); p.setShiftKeyDown(false); p.setLastClientInput(Input.EMPTY);
        p.setDeltaMovement(new Vec3(0, Math.min(0, p.getDeltaMovement().y), 0));
        freeze(p, Attributes.MOVEMENT_SPEED); freeze(p, Attributes.JUMP_STRENGTH);
        var s = new Session(p); OPEN.put(p.getUUID(), s);
        CombatHud.remove(p); p.inventoryMenu.broadcastFullState();
        refresh(s); return true;
    }

    private static void freeze(ServerPlayer p, Holder<Attribute> type) {
        var attr = p.getAttribute(type);
        if (attr != null) { attr.removeModifier(FREEZE); attr.addTransientModifier(new AttributeModifier(FREEZE, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL)); }
    }

    public static void close(ServerPlayer p) { var s = current(p); if (s != null) retire(s); }

    private static void retire(Session s) {
        if (!OPEN.remove(s.owner.getUUID(), s)) return;
        GearHud.remove(s.owner);
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = s.owner.getAttribute(type); if (attr != null) attr.removeModifier(FREEZE);
        }
        s.owner.setLastClientInput(Input.EMPTY);
        if (!s.owner.hasDisconnected()) { WeaponHotbarGuard.restoreCombatSlot(s.owner); s.owner.inventoryMenu.broadcastFullState(); }
    }

    /** Pointer from view rotation. Horizontal position claims are pinned; vertical (falling) passes through. */
    public static boolean move(ServerPlayer p, ServerboundMovePlayerPacket packet) {
        var s = current(p); if (s == null) return false;
        if (packet.hasRotation()) {
            float yaw = packet.getYRot(p.getYRot()), pitch = packet.getXRot(p.getXRot());
            if (Float.isFinite(yaw) && Float.isFinite(pitch)) {
                p.setYRot(yaw); p.setYHeadRot(yaw); p.setXRot(Math.clamp(pitch, -90, 90));
                float lastYaw = s.controls.yaw(), lastPitch = s.controls.pitch();
                if (s.controls.rotate(yaw, pitch)) { s.lastActive = now(s); hover(s); render(s); }
                // Clamped at an edge: the pointer stays, but its reference rotation must follow the view or the
                // client would keep extrapolating it past the edge.
                else if (lastYaw != s.controls.yaw() || lastPitch != s.controls.pitch()) render(s);
            }
        }
        if (packet.hasPosition()) {
            double x = packet.getX(s.anchor.x), y = packet.getY(p.getY()), z = packet.getZ(s.anchor.z);
            if (!Double.isFinite(x + y + z)) { pin(p, s.anchor.x, p.getY(), s.anchor.z); return true; }
            double dx = x - s.anchor.x, dz = z - s.anchor.z;
            if (dx * dx + dz * dz > .0001) pin(p, s.anchor.x, y, s.anchor.z);
            else { p.absSnapTo(s.anchor.x, y, s.anchor.z); p.setOnGround(packet.isOnGround()); }
            s.anchor = new Vec3(s.anchor.x, y, s.anchor.z);
        }
        return true;
    }

    /** Correct a position claim without touching the view: the rotation is the mouse pointer and is relative 0. */
    private static void pin(ServerPlayer p, double x, double y, double z) {
        p.connection.teleport(new net.minecraft.world.entity.PositionMoveRotation(new Vec3(x, y, z), Vec3.ZERO, 0, 0),
                java.util.Set.of(net.minecraft.world.entity.Relative.Y_ROT, net.minecraft.world.entity.Relative.X_ROT));
    }

    public static boolean input(ServerPlayer p, Input next) {
        var s = current(p); if (s == null) return false;
        Input old = s.input; s.input = next; s.lastActive = now(s);
        if (next.jump() && !old.jump()) click(p, false);
        if (s.stage != Stage.GEAR) return true;
        if (next.forward() && !old.forward()) openEconomy(s, true);
        else if (next.backward() && !old.backward()) openEconomy(s, false);
        else if (next.left() && !old.left()) sell(s);
        else if (next.right() && !old.right()) { var p0 = s.owner; close(p0); kim.biryeong.destiny.fireteam.FinderScreen.open(p0); }
        else if (next.shift() && !old.shift()) lock(s);
        return true;
    }

    /** W: auction house, S: vault. The gear screen closes first (economy menus need the plain inventory menu). */
    private static void openEconomy(Session s, boolean auction) {
        var p = s.owner;
        close(p);
        if (auction) kim.biryeong.destiny.economy.EconomyMenus.openAuction(p);
        else kim.biryeong.destiny.economy.EconomyMenus.openVault(p);
    }

    /** A: list the hovered stored weapon on the auction house. */
    private static void sell(Session s) {
        var w = hoveredWeapon(s);
        if (w == null) { notice(s, "무기에 커서를 올린 뒤 A를 누르면 경매장에 판매합니다."); render(s); return; }
        String why = kim.biryeong.destiny.economy.EconomyMenus.sellable(s.owner, w.inventoryIndex());
        if (why != null) { notice(s, why); render(s); return; }
        var p = s.owner; int index = w.inventoryIndex();
        close(p);
        kim.biryeong.destiny.economy.EconomyMenus.openSell(p, index);
    }

    /** Shift: lock or unlock the hovered weapon (locked weapons cannot be dismantled or sold). */
    private static void lock(Session s) {
        var w = hoveredWeapon(s);
        if (w == null) { notice(s, "무기에 커서를 올린 뒤 Shift를 누르면 잠급니다."); render(s); return; }
        var stack = WeaponStorage.resolve(s.owner, w.inventoryIndex());
        if (stack != w.stack()) { refresh(s); return; }
        boolean locked = kim.biryeong.destiny.weapon.WeaponLock.toggle(stack);
        s.owner.getInventory().setChanged();
        s.owner.level().playSound(null, s.owner.getX(), s.owner.getY(), s.owner.getZ(), net.minecraft.sounds.SoundEvents.UI_BUTTON_CLICK.value(),
                net.minecraft.sounds.SoundSource.PLAYERS, .4f, locked ? 1.4f : 1f);
        notice(s, w.name() + (locked ? " 잠금" : " 잠금 해제"));
        refresh(s);
    }

    /** QA: park the pointer at screen coordinates (1920x1080 space) and hover what is under it. */
    public static boolean qaPoint(ServerPlayer p, float x, float y) {
        var s = current(p); if (s == null) return false;
        s.controls.point(x, y); hover(s); render(s); return true;
    }

    /** F (swap hands): open/close the detail view of the hovered weapon. */
    public static boolean inspect(ServerPlayer p) {
        var s = current(p); if (s == null) return false;
        if (s.stage == Stage.DETAIL) { s.stage = Stage.GEAR; s.detail = null; render(s); return true; }
        var w = hoveredWeapon(s);
        if (w == null) { notice(s, "무기에 커서를 올린 뒤 F를 누르면 상세 정보를 봅니다."); render(s); return true; }
        s.detail = w; s.stage = Stage.DETAIL; s.focus = GearLayout.BACK;
        render(s); return true;
    }

    /**
     * Q (drop): dismantle the hovered stored weapon. The first press arms it, a second press within two seconds
     * removes it (Destiny's hold-to-dismantle without a hold input). Equipped weapons cannot be dismantled.
     */
    public static boolean dismantle(ServerPlayer p) {
        var s = current(p); if (s == null) return false;
        if (s.stage != Stage.GEAR) return true;
        var w = hoveredWeapon(s);
        if (w == null) { notice(s, "보관함의 무기에 커서를 올린 뒤 Q를 누르면 분해합니다."); render(s); return true; }
        if (w.equipped()) { notice(s, "장착 중인 무기는 분해할 수 없습니다."); render(s); return true; }
        if (kim.biryeong.destiny.weapon.WeaponLock.locked(w.stack())) { notice(s, "잠긴 무기는 분해할 수 없습니다. Shift로 잠금을 해제하세요."); render(s); return true; }
        int now = now(s);
        if (s.dismantleIndex != w.inventoryIndex() || now > s.dismantleUntil) {
            s.dismantleIndex = w.inventoryIndex(); s.dismantleUntil = now + 40;
            notice(s, w.name() + " · 한 번 더 Q를 누르면 분해합니다."); render(s); return true;
        }
        s.dismantleIndex = -1;
        if (WeaponStorage.resolve(p, w.inventoryIndex()) != w.stack()) { notice(s, "무기 상태가 바뀌어 분해를 취소했습니다."); refresh(s); return true; }
        if (WeaponStorage.token(w.inventoryIndex())) WeaponStorage.remove(p, w.inventoryIndex(), w.stack());
        else { p.getInventory().setItem(w.inventoryIndex(), net.minecraft.world.item.ItemStack.EMPTY); p.getInventory().setChanged(); }
        p.level().playSound(null, p.getX(), p.getY(), p.getZ(), net.minecraft.sounds.SoundEvents.GRINDSTONE_USE,
                net.minecraft.sounds.SoundSource.PLAYERS, .6f, 1.4f);
        long glimmer = kim.biryeong.destiny.economy.Economy.reward(p, kim.biryeong.destiny.economy.Economy.dismantleValue(w.rarity()), "분해");
        notice(s, w.name() + " 분해" + (glimmer > 0 ? " · 미광체 +" + glimmer : ""));
        refresh(s); return true;
    }

    public static boolean click(ServerPlayer p, boolean back) {
        var s = current(p); if (s == null) return false;
        int now = now(s); if (now - s.lastClick < 3) return true;
        s.lastClick = now; s.lastActive = now;
        if (back) { back(s); return true; }
        int node = s.focus;
        if (node == GearLayout.CLOSE) { close(p); return true; }
        if (node == GearLayout.BACK) { back(s); return true; }
        switch (s.stage) {
            case GEAR -> gearClick(s, node);
            case SUBCLASS, OPTIONS -> characterClick(s, node);
            case DETAIL -> { }
        }
        return true;
    }

    private static void back(Session s) {
        switch (s.stage) {
            case GEAR -> close(s.owner);
            case DETAIL, SUBCLASS -> { s.stage = Stage.GEAR; s.detail = null; render(s); }
            case OPTIONS -> { s.stage = Stage.SUBCLASS; refresh(s); }
        }
    }

    private static void gearClick(Session s, int node) {
        if (node == GearLayout.ARMORY && armory(s.owner)) {
            close(s.owner); WeaponScreen.openArmory(s.owner); return;
        }
        if (node >= GearLayout.ENGRAM && node < GearLayout.ENGRAM + GearLayout.ENGRAM_COUNT) {
            String error = kim.biryeong.destiny.loot.Loot.decode(s.owner, node - GearLayout.ENGRAM);
            notice(s, error == null ? "엔그램을 해독했습니다." : error);
            refresh(s); return;
        }
        if (node == GearSlot.SUBCLASS.ordinal()) { s.stage = Stage.SUBCLASS; s.expanded = null; refresh(s); return; }
        if (node >= 0 && node < GearLayout.SLOT_COUNT) {
            var slot = GearSlot.values()[node];
            if (slot.weapon() != null) {
                var bucket = s.buckets.get(slot.weapon());
                if (s.expanded == slot && bucket != null && bucket.stored().size() > GearLayout.STORAGE_COUNT) {
                    int pages = (bucket.stored().size() + GearLayout.STORAGE_COUNT - 1) / GearLayout.STORAGE_COUNT;
                    s.storagePages.put(slot.weapon(), (s.storagePages.getOrDefault(slot.weapon(), 0) + 1) % pages);
                }
                s.expanded = slot; render(s);
            }
            else notice(s, slot.armor() ? "방어구는 아직 교체할 수 없습니다." : "고스트 의체는 아직 교체할 수 없습니다.");
            render(s); return;
        }
        if (node >= GearLayout.STORAGE && node < GearLayout.STORAGE + GearLayout.STORAGE_COUNT && s.expanded != null) {
            var bucket = s.buckets.get(s.expanded.weapon());
            int index = node - GearLayout.STORAGE + storageOffset(s, s.expanded.weapon());
            if (bucket == null || index >= bucket.stored().size()) return;
            var w = bucket.stored().get(index);
            String error = WeaponEquipmentService.equip(s.owner, w.inventoryIndex(), w.stack());
            notice(s, error == null ? w.name() + " 장착" : error);
            refresh(s);
        }
    }

    private static void characterClick(Session s, int node) {
        if (node >= GearLayout.FIELD && node < GearLayout.FIELD + GearLayout.FIELD_COUNT) {
            int i = node - GearLayout.FIELD;
            if (i >= s.fields.size()) return;
            var field = s.fields.get(i);
            if (!field.enabled()) { notice(s, field.reason()); render(s); return; }
            s.field = field.id(); s.stage = Stage.OPTIONS; refresh(s); return;
        }
        if (s.stage == Stage.OPTIONS && node >= GearLayout.STORAGE && node < GearLayout.STORAGE + GearLayout.STORAGE_COUNT) {
            int i = node - GearLayout.STORAGE;
            if (i >= s.options.size()) return;
            var option = s.options.get(i);
            if (!option.enabled()) { notice(s, option.reason()); render(s); return; }
            String error = WeaponScreen.applyCharacter(s.owner, s.field, option.id());
            notice(s, error == null ? option.name() + " 적용" : error);
            if (error == null) s.stage = Stage.SUBCLASS;
            refresh(s);
        }
    }

    static boolean armory(ServerPlayer p) {
        return kim.biryeong.destiny.inventory.WeaponTestArmory.enabled()
                && p.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER);
    }

    private static long glimmer(ServerPlayer p) {
        var ledger = kim.biryeong.destiny.economy.Economy.ledger();
        return ledger == null ? -1 : ledger.glimmer(p.getUUID());
    }

    private static void notice(Session s, String text) { s.message = text; s.messageUntil = now(s) + 80; }
    private static int now(Session s) { return s.level.getServer().getTickCount(); }

    private static Map<Integer, Box> nodes(Session s) {
        int stored = s.expanded == null || s.expanded.weapon() == null ? 0
                : Optional.ofNullable(s.buckets.get(s.expanded.weapon())).map(b -> b.stored().size()).orElse(0);
        return GearLayout.nodes(s.stage, s.expanded, Math.max(stored, s.expanded == null ? 0 : GearLayout.STORAGE_COUNT),
                s.options.size(), s.stage == Stage.GEAR && armory(s.owner),
                kim.biryeong.destiny.loot.Loot.profile(s.owner).engrams().size());
    }

    /** Pointer hover: focus the node under the cursor; a weapon slot opens its grid until the cursor leaves. */
    private static void hover(Session s) {
        int before = s.focus;
        if (s.stage == Stage.GEAR) {
            if (s.expanded != null && !GearLayout.region(s.expanded).contains(s.controls.x(), s.controls.y())) s.expanded = null;
            int hit = GearLayout.hit(nodes(s), s.controls.x(), s.controls.y());
            if (hit >= 0 && hit < GearLayout.SLOT_COUNT) {
                var slot = GearSlot.values()[hit];
                if (slot.weapon() != null) s.expanded = slot;
                else if (s.expanded != null && !GearLayout.region(s.expanded).contains(s.controls.x(), s.controls.y())) s.expanded = null;
            }
            s.focus = GearLayout.hit(nodes(s), s.controls.x(), s.controls.y());
        } else s.focus = GearLayout.hit(nodes(s), s.controls.x(), s.controls.y());
        if (s.focus != before) s.hoverSince = now(s);
    }

    static GearItems.Weapon hoveredWeapon(Session s) {
        int n = s.focus;
        if (n >= GearSlot.KINETIC.ordinal() && n <= GearSlot.POWER.ordinal()) {
            var b = s.buckets.get(GearSlot.values()[n].weapon());
            return b == null ? null : b.equipped();
        }
        if (s.stage == Stage.GEAR && s.expanded != null && n >= GearLayout.STORAGE && n < GearLayout.STORAGE + GearLayout.STORAGE_COUNT) {
            var b = s.buckets.get(s.expanded.weapon());
            int i = n - GearLayout.STORAGE + storageOffset(s, s.expanded.weapon());
            return b == null || i >= b.stored().size() ? null : b.stored().get(i);
        }
        return null;
    }

    /** Compact status line for {@code /destiny inventory status}. */
    public static String describe(GearView v) {
        var sb = new StringBuilder("GearScreen stage=").append(v.stage()).append(" focus=").append(v.focus())
                .append(" expanded=").append(v.expanded());
        for (var slot : WeaponSlot.values()) {
            var b = v.bucket(slot);
            sb.append(' ').append(slot).append('=').append(b == null || b.equipped() == null ? "-" : b.equipped().id())
                    .append('+').append(b == null ? 0 : b.stored().size());
        }
        if (v.tooltip() != null) sb.append(" tooltip=").append(v.tooltip().id());
        if (v.detail() != null) sb.append(" detail=").append(v.detail().id());
        return sb.toString();
    }

    private static void tick(MinecraftServer server) {
        for (var s : List.copyOf(OPEN.values())) {
            if (s.level.getServer() != server) continue;
            var p = s.owner;
            double dx = p.getX() - s.anchor.x, dz = p.getZ() - s.anchor.z;
            if (p.hasDisconnected() || !p.isAlive() || p.isRemoved() || p.isSpectator() || p.level() != s.level
                    || p.isPassenger() || p.isSleeping() || p.getCamera() != p || AbilityService.inSuper(p)
                    || kim.biryeong.destiny.down.GuardianDown.active(p)
                    || dx * dx + dz * dz > .25 || now(s) - s.lastActive > 20 * 120) { retire(s); continue; }
            var v = p.getDeltaMovement(); p.setDeltaMovement(0, v.y, 0);
            if (now(s) % 10 == 0) refresh(s);
            else if (server.getTickCount() % kim.biryeong.destiny.inventory.PlayerFigure.BREATH == 0) render(s); // idle breath key
            else if (now(s) - s.hoverSince <= TOOLTIP_DELAY + 1 || (s.stage == Stage.DETAIL && now(s) % 20 == 0)
                    || (s.messageUntil > 0 && now(s) >= s.messageUntil)) render(s);
        }
    }

    private static void refresh(Session s) {
        for (var slot : WeaponSlot.values()) s.buckets.put(slot, GearItems.bucket(s.owner, slot));
        if (s.stage == Stage.SUBCLASS || s.stage == Stage.OPTIONS) {
            var view = WeaponScreen.characterView(s.owner, s.field);
            s.fields = view.fields();
            s.options = s.stage == Stage.OPTIONS ? WeaponScreen.characterOptions(s.owner, s.field) : List.of();
        }
        hover(s);
        render(s);
    }

    private static int storageOffset(Session s, WeaponSlot slot) {
        var bucket = s.buckets.get(slot);
        int pages = bucket == null ? 1 : Math.max(1, (bucket.stored().size() + GearLayout.STORAGE_COUNT - 1) / GearLayout.STORAGE_COUNT);
        int page = Math.min(s.storagePages.getOrDefault(slot, 0), pages - 1);
        s.storagePages.put(slot, page);
        return page * GearLayout.STORAGE_COUNT;
    }
    private static Map<WeaponSlot, GearItems.Bucket> visibleBuckets(Session s) {
        var result = new EnumMap<WeaponSlot, GearItems.Bucket>(WeaponSlot.class);
        s.buckets.forEach((slot, bucket) -> {
            int from = storageOffset(s, slot);
            result.put(slot, new GearItems.Bucket(bucket.equipped(), bucket.stored().subList(from, Math.min(from + GearLayout.STORAGE_COUNT, bucket.stored().size()))));
        });
        return Map.copyOf(result);
    }
    private static void render(Session s) {
        if (s.messageUntil > 0 && now(s) >= s.messageUntil) { s.message = ""; s.messageUntil = 0; }
        var hovered = s.stage == Stage.GEAR ? hoveredWeapon(s) : null;
        var bucket = s.expanded == null || s.expanded.weapon() == null ? null : s.buckets.get(s.expanded.weapon());
        var compare = hovered != null && !hovered.equipped() && bucket != null ? bucket.equipped() : null;
        boolean tooltip = hovered != null && now(s) - s.hoverSince >= TOOLTIP_DELAY;
        String message = s.message;
        if (message.isBlank() && bucket != null && bucket.stored().size() > GearLayout.STORAGE_COUNT)
            message = "보관함 " + (storageOffset(s, s.expanded.weapon()) / GearLayout.STORAGE_COUNT + 1) + "/"
                    + ((bucket.stored().size() + GearLayout.STORAGE_COUNT - 1) / GearLayout.STORAGE_COUNT)
                    + " · 장착 무기 클릭: 다음 페이지";
        s.view = new GearView(s.owner.getGameProfile().name(), s.stage, s.expanded, s.focus,
                s.controls.x(), s.controls.y(), s.controls.yaw(), s.controls.pitch(), visibleBuckets(s), tooltip ? hovered : null, compare, s.detail,
                ((now(s) - s.openedAt) / 20) * 30f % 360, s.field, s.fields, s.options, message, armory(s.owner),
                kim.biryeong.destiny.guardian.Guardians.data(s.owner).guardianClass(),
                WeaponScreen.characterView(s.owner, s.field), kim.biryeong.destiny.loot.Loot.profile(s.owner).engrams(),
                glimmer(s.owner));
        GearHud.render(s.owner, s.view);
    }
}
