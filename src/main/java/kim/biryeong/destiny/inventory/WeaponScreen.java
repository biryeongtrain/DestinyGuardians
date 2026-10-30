package kim.biryeong.destiny.inventory;

import com.google.gson.Gson;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
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
import net.minecraft.resources.Identifier;
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

/** Server-side equipment screen. Weapon drafts require confirmation; character options apply immediately. */
public final class WeaponScreen {
    private static final Map<UUID, Session> OPEN = new HashMap<>();
    private static final net.minecraft.resources.Identifier FREEZE = DestinyGuardians.id("equipment_screen");
    private static final int PAGE_SIZE = 9;
    private static final String[] CHARACTER_FIELDS = {"CLASS", "SUBCLASS", "GRENADE", "MELEE", "CLASS_ABILITY", "SUPER", "JUMP"};
    private static final class Session {
        final ServerPlayer owner;
        final ServerLevel level;
        final Object connection;
        final Vec3 anchor;
        final WeaponScreenControls controls = new WeaponScreenControls();
        WeaponSlot slot = WeaponSlot.KINETIC;
        Input input = Input.EMPTY;
        String stage = "LOADOUT", family = "";
        boolean pointerDriven = true;
        String characterField = "CLASS";
        WeaponScreenView.CharacterView character = WeaponScreenView.CharacterView.EMPTY;
        List<WeaponScreenView.CharacterOption> characterOptions = List.of();
        List<WeaponScreenView.FamilyOption> families = List.of();
        List<WeaponCatalog.Entry> choices = List.of();
        WeaponPerkSelection.Group perkGroup = WeaponPerkSelection.Group.DAMAGE;
        List<WeaponPerkSelection.Option> perks = List.of();
        WeaponCatalog.Entry draftEntry;
        ItemStack draft;
        String damage = "", utility = "";
        WeaponScreenView view;
        int page, focus, repeatAt, lastClick = Integer.MIN_VALUE / 2, lastActive;
        String message = "슬롯을 고른 뒤 새 무기로 로드아웃을 구성하세요.";
        Session(ServerPlayer p) {
            owner = p; level = p.level(); connection = p.connection; anchor = p.position();
            controls.baseline(p.getYRot(), p.getXRot());
            lastActive = p.level().getServer().getTickCount();
        }
    }
    private WeaponScreen() {}

    public static void init() {
        InventoryMenuRedirect.init();
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
                dispatcher.register(Commands.literal("메뉴").executes(c -> toggle(c.getSource().getPlayerOrException()) ? 1 : 0)));
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
            dispatcher.register(Commands.literal("destiny").then(Commands.literal("inventory")
                .executes(c -> open(c.getSource().getPlayerOrException()) ? 1 : 0)
                .then(Commands.literal("test").executes(c -> open(c.getSource().getPlayerOrException()) ? 1 : 0))
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
    /** Observation only: never opens, refreshes, renders or initializes guardian state. Server thread only. */
    public static Optional<WeaponScreenView> snapshot(ServerPlayer p) {
        var s = current(p);
        return s == null ? Optional.empty() : Optional.ofNullable(s.view);
    }
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
                    s.pointerDriven = true;
                    s.focus = WeaponScreenLayout.hit(s.controls.x(), s.controls.y(), s.stage); touch(s); render(s);
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
        if (next.jump() && !old.jump()) { s.pointerDriven = false; click(p, false); }
        if (!next.equals(old)) { s.repeatAt = now(s) + 7; navigate(s); }
        return true;
    }
    private static void navigate(Session s) {
        int dx = (s.input.right() ? 1 : 0) - (s.input.left() ? 1 : 0);
        int dy = (s.input.backward() ? 1 : 0) - (s.input.forward() ? 1 : 0);
        if (dx == 0 && dy == 0) return;
        s.pointerDriven = false;
        s.focus = WeaponScreenLayout.navigate(s.focus, dx, dy, s.stage);
        var b = WeaponScreenLayout.bounds(s.focus); s.controls.point(b.x(), b.y());
        touch(s); render(s);
    }
    public static boolean click(ServerPlayer p, boolean back) {
        var s = current(p); if (s == null) return false;
        // Coalesce same-tick packet variants, while allowing a fresh click at the same screen position.
        int now = now(s); if (now - s.lastClick < 3) return true;
        s.lastClick = now; touch(s);
        if (back) { close(p); return true; }
        int node = s.focus;
        // A stale/hidden node must never activate a control from another tab.
        if (!WeaponScreenLayout.visible(node, s.stage)) return true;
        if (node == WeaponScreenLayout.CRUCIBLE) {
            close(p);
            if (kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p))
                kim.biryeong.destiny.crucible.CrucibleRuntime.leave(p, true);
            else kim.biryeong.destiny.crucible.CrucibleRuntime.join(p);
            return true;
        }
        if (node == WeaponScreenLayout.CHARACTER_TAB) {
            if (!s.stage.equals("CHARACTER")) {
                resetDraft(s); s.family = ""; s.stage = "CHARACTER"; s.page = 0;
                s.message = "변경할 항목을 선택하세요. 옵션을 선택하면 즉시 장착됩니다.";
                focus(s, WeaponScreenLayout.CLASS); refresh(s);
            }
            return true;
        }
        if (node == WeaponScreenLayout.LOADOUT_TAB) {
            if (characterMode(s)) {
                s.stage = "LOADOUT"; s.page = 0; s.message = "무기 로드아웃으로 돌아왔습니다.";
                focus(s, s.slot.ordinal()); refresh(s);
            }
            return true;
        }
        if (characterMode(s)) { characterClick(s, node); return true; }
        if (node >= 0 && node < 3) {
            s.slot = WeaponSlot.values()[node]; resetDraft(s); s.stage = "LOADOUT"; s.family = ""; s.page = 0;
            s.message = "이 슬롯에 추가하려면 새 무기를 누르세요."; refresh(s);
        } else if (node == WeaponScreenLayout.TEST_ARMORY && s.stage.equals("LOADOUT")) {
            if (!WeaponTestArmory.enabled()) { s.message = "테스트 무기 기능이 비활성화되어 있습니다."; render(s); }
            else { s.stage = "FAMILY"; s.page = 0; s.message = "무기군을 선택하세요. 확정 전에는 장비가 변경되지 않습니다."; refresh(s); }
        } else if (node >= 3 && node < 12 && !s.stage.equals("LOADOUT")) {
            int index = s.page * PAGE_SIZE + node - 3;
            if (s.stage.equals("FAMILY") && index < s.families.size()) {
                s.family = s.families.get(index).id(); s.stage = "WEAPON"; s.page = 0;
                s.message = "무기를 선택하면 퍽 선택으로 넘어갑니다.";
            } else if (s.stage.equals("WEAPON") && index < s.choices.size()) {
                s.draftEntry = s.choices.get(index); s.draft = WeaponItems.create(s.draftEntry);
                s.damage = ""; s.utility = ""; s.perkGroup = WeaponPerkSelection.Group.DAMAGE;
                s.stage = "PERKS"; s.page = 0;
                s.message = "데미지·유틸리티 퍽을 고른 뒤 로드아웃에 추가하세요. 아직 장비에는 적용되지 않았습니다.";
            } else if (s.stage.equals("PERKS") && index < s.perks.size()) {
                var option = s.perks.get(index);
                String damage = s.perkGroup == WeaponPerkSelection.Group.DAMAGE ? option.id() : s.damage;
                String utility = s.perkGroup == WeaponPerkSelection.Group.UTILITY ? option.id() : s.utility;
                String error = option.enabled() ? WeaponPerkSelection.configure(s.draft, damage, utility) : option.reason();
                if (error == null) { s.damage = damage; s.utility = utility; s.message = "퍽 선택 저장 · 로드아웃에 추가하면 실제 적용됩니다."; }
                else s.message = error;
            }
            refresh(s);
        } else if ((node == WeaponScreenLayout.PREVIOUS || node == WeaponScreenLayout.NEXT) && !s.stage.equals("LOADOUT")) {
            s.page = Math.clamp(s.page + (node == WeaponScreenLayout.PREVIOUS ? -1 : 1), 0, pages(s) - 1); render(s);
        } else if (node == WeaponScreenLayout.DAMAGE_PERKS || node == WeaponScreenLayout.UTILITY_PERKS) {
            if (s.stage.equals("PERKS")) {
                s.perkGroup = node == WeaponScreenLayout.DAMAGE_PERKS ? WeaponPerkSelection.Group.DAMAGE : WeaponPerkSelection.Group.UTILITY;
                s.page = 0; refresh(s);
            }
        } else if (node == WeaponScreenLayout.BACK_WEAPONS && !s.stage.equals("LOADOUT")) {
            if (s.stage.equals("PERKS")) { resetDraft(s); s.stage = "WEAPON"; }
            else if (s.stage.equals("WEAPON")) { s.family = ""; s.stage = "FAMILY"; }
            else s.stage = "LOADOUT";
            s.page = 0; s.message = "이전 단계로 돌아왔습니다. 실제 장비는 변경하지 않았습니다."; refresh(s);
        } else if (node == WeaponScreenLayout.CONFIRM_LOADOUT && s.stage.equals("PERKS") && s.draftEntry != null) {
            String error = WeaponTestArmory.add(p, s.draftEntry.id(), s.damage, s.utility);
            if (error == null) {
                resetDraft(s); s.stage = "LOADOUT"; s.page = 0;
                s.message = "로드아웃에 추가 완료 · 선택한 슬롯에 무기와 퍽을 적용했습니다.";
            } else s.message = error;
            refresh(s);
        } else if (node == WeaponScreenLayout.CLOSE) close(p);
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
    private static void resetDraft(Session s) {
        s.draft = null; s.draftEntry = null; s.damage = ""; s.utility = ""; s.perks = List.of();
    }
    private static int count(Session s) {
        return switch (s.stage) { case "FAMILY" -> s.families.size(); case "WEAPON" -> s.choices.size(); case "PERKS" -> s.perks.size(); case "CHARACTER_OPTIONS" -> s.characterOptions.size(); default -> 0; };
    }
    private static int pages(Session s) { return Math.max(1, (count(s) + PAGE_SIZE - 1) / PAGE_SIZE); }
    private static void refresh(Session s) {
        if (characterMode(s)) refreshCharacter(s);
        var catalog = WeaponTestArmory.catalog(s.slot);
        s.families = catalog.stream().map(WeaponCatalog.Entry::family).distinct().sorted()
                .map(id -> new WeaponScreenView.FamilyOption(id, WeaponScreenText.family(id),
                        (int)catalog.stream().filter(e -> e.family().equals(id)).count())).toList();
        s.choices = s.stage.equals("WEAPON") ? catalog.stream().filter(e -> e.family().equals(s.family)).toList() : List.of();
        s.perks = s.stage.equals("PERKS") ? WeaponPerkSelection.options(s.draft, s.perkGroup) : List.of();
        s.page = Math.clamp(s.page, 0, pages(s) - 1);
        // Hover -1 is a valid pointer position between controls, not a focus error.
        // Periodic data refresh must never warp the pointer back onto a button.
        s.focus = WeaponScreenLayout.hit(s.controls.x(), s.controls.y(), s.stage);
        render(s);
    }
    private static WeaponScreenView.Card card(int index, ItemStack stack, WeaponCatalog.Entry entry, boolean equipped) {
        var c = WeaponCharacteristics.of(entry); var profile = WeaponProfile.forEntry(entry);
        var ammo = WeaponItems.magazine(stack, profile);
        return new WeaponScreenView.Card(index, entry.id(), entry.name(), entry.family(), entry.source_frame_label(),
                c.slot(), c.damage().name(), c.ammo().name(), c.exotic(), c.stats(), ammo.rounds(), ammo.loadedLimit(), equipped);
    }
    private static WeaponScreenView.Card preview(WeaponCatalog.Entry entry) {
        var c = WeaponCharacteristics.of(entry); var profile = WeaponProfile.forEntry(entry);
        return new WeaponScreenView.Card(-1, entry.id(), entry.name(), entry.family(), entry.source_frame_label(),
                c.slot(), c.damage().name(), c.ammo().name(), c.exotic(), c.stats(), profile.magazine(), profile.magazine(), false);
    }
    private static String perkName(String id) { return id.isEmpty() ? "" : WeaponPerkLabels.name(id); }
    private static void render(Session s) {
        var equipped = WeaponLoadout.equipped(s.owner).stream()
                .map(e -> card(e.slot().hotbar(), e.stack(), e.weapon(), true)).toList();
        var choices = s.choices.stream().skip((long)s.page * PAGE_SIZE).limit(PAGE_SIZE).map(WeaponScreen::preview).toList();
        var families = s.families.stream().skip((long)s.page * PAGE_SIZE).limit(PAGE_SIZE).toList();
        var perks = s.perks.stream().skip((long)s.page * PAGE_SIZE).limit(PAGE_SIZE)
                .map(o -> new WeaponScreenView.PerkOption(o.id(), o.name(), o.description(), o.selected(), o.enabled(), o.reason())).toList();
        var current = equipped.stream().filter(c -> c.slot() == s.slot).findFirst().orElse(null);
        var inspected = s.stage.equals("PERKS") && s.draftEntry != null ? preview(s.draftEntry)
                : s.stage.equals("WEAPON") ? s.focus >= 3 && s.focus < 3 + choices.size() ? choices.get(s.focus - 3)
                    : choices.isEmpty() ? null : choices.getFirst()
                : current;
        s.view = new WeaponScreenView(s.owner.getGameProfile().name(), s.slot, equipped, choices, inspected,
                s.page, pages(s), s.focus, s.controls.x(), s.controls.y(), s.message, true,
                s.stage.equals("PERKS") ? s.perkGroup.name() : "", perks, perkName(s.damage), perkName(s.utility),
                s.stage, s.stage.equals("FAMILY") ? families : List.of(), s.family,
                characterMode(s) ? new WeaponScreenView.CharacterView(s.character.guardianClass(),
                        s.character.className(), s.character.subclass(), s.character.subclassName(),
                        s.characterField, s.character.fields(), s.characterOptions.stream()
                                .skip((long)s.page * PAGE_SIZE).limit(PAGE_SIZE).toList())
                        : WeaponScreenView.CharacterView.EMPTY);
        WeaponScreenHud.render(s.owner, s.view);
    }

    private static boolean characterMode(Session s) {
        return s.stage.equals("CHARACTER") || s.stage.equals("CHARACTER_OPTIONS");
    }

    private static void focus(Session s, int node) {
        if (s.pointerDriven) {
            s.focus = WeaponScreenLayout.hit(s.controls.x(), s.controls.y(), s.stage);
            return;
        }
        s.focus = node;
        var box = WeaponScreenLayout.bounds(node); s.controls.point(box.x(), box.y());
    }

    private static void characterClick(Session s, int node) {
        if (node == WeaponScreenLayout.CLOSE) { close(s.owner); return; }
        if (s.stage.equals("CHARACTER") && node >= WeaponScreenLayout.CLASS && (node <= WeaponScreenLayout.SUPER || node == WeaponScreenLayout.JUMP)) {
            int index = node == WeaponScreenLayout.JUMP ? 6 : node - WeaponScreenLayout.CLASS;
            var field = s.character.fields().get(index);
            if (!field.enabled()) { s.message = field.reason(); render(s); return; }
            s.characterField = CHARACTER_FIELDS[index]; s.stage = "CHARACTER_OPTIONS"; s.page = 0;
            s.message = field.name() + " 선택 · 선택하면 즉시 적용됩니다.";
            focus(s, 3); refresh(s); return;
        }
        if (!s.stage.equals("CHARACTER_OPTIONS")) return;
        if (node == WeaponScreenLayout.BACK_CHARACTER) {
            characterRoot(s); refresh(s); return;
        }
        if (node == WeaponScreenLayout.PREVIOUS || node == WeaponScreenLayout.NEXT) {
            s.page = Math.clamp(s.page + (node == WeaponScreenLayout.PREVIOUS ? -1 : 1), 0, pages(s) - 1);
            render(s); return;
        }
        int index = s.page * PAGE_SIZE + node - 3;
        if (node < 3 || node > 11 || index >= s.characterOptions.size()) return;
        var option = s.characterOptions.get(index);
        if (!option.enabled()) { s.message = option.reason(); render(s); return; }
        String error = switch (s.characterField) {
            case "CLASS" -> CharacterLoadouts.selectClass(s.owner, GuardianClass.valueOf(option.id()));
            case "SUBCLASS" -> CharacterLoadouts.selectSubclass(s.owner, Element.valueOf(option.id()));
            default -> CharacterLoadouts.selectAbility(s.owner, AbilitySlot.valueOf(s.characterField), Identifier.parse(option.id()));
        };
        if (error == null) {
            s.message = option.name() + " 적용 완료 · 캐릭터에 즉시 반영했습니다.";
            characterRoot(s);
        } else s.message = error;
        refresh(s);
    }

    private static void characterRoot(Session s) {
        s.stage = "CHARACTER"; s.page = 0;
        int index = Arrays.asList(CHARACTER_FIELDS).indexOf(s.characterField);
        focus(s, index == 6 ? WeaponScreenLayout.JUMP : WeaponScreenLayout.CLASS + Math.max(0, index));
    }

    private static void refreshCharacter(Session s) {
        var data = Guardians.data(s.owner);
        GuardianClass cls = data.guardianClass();
        Element element = CharacterLoadouts.subclass(data);
        List<WeaponScreenView.CharacterField> fields = new ArrayList<>();
        for (String field : CHARACTER_FIELDS) {
            List<WeaponScreenView.CharacterOption> options = characterOptions(data, cls, element, field);
            boolean enabled = !options.isEmpty();
            String reason = enabled ? "옵션을 선택하면 즉시 적용됩니다."
                    : cls == GuardianClass.NONE ? "직업을 먼저 선택하세요."
                    : element == null && !field.equals("SUBCLASS") ? "하위직업을 먼저 선택하세요."
                    : "현재 직업·하위직업에 등록된 " + fieldName(field) + " 옵션이 없습니다.";
            String value = switch (field) {
                case "CLASS" -> className(cls);
                case "SUBCLASS" -> elementName(element);
                default -> data.loadout().map(l -> l.get(AbilitySlot.valueOf(field)))
                        .flatMap(id -> id == null ? Optional.<Ability>empty() : AbilityRegistry.get(id))
                        .map(Ability::displayName).orElse("미장착");
            };
            fields.add(new WeaponScreenView.CharacterField(field, fieldName(field), value, enabled, reason));
        }
        s.characterOptions = s.stage.equals("CHARACTER_OPTIONS")
                ? characterOptions(data, cls, element, s.characterField) : List.of();
        s.character = new WeaponScreenView.CharacterView(cls.name(), className(cls),
                element == null ? "" : element.name(), elementName(element), s.characterField, fields, List.of());
    }

    private static List<WeaponScreenView.CharacterOption> characterOptions(GuardianData data,
            GuardianClass cls, Element element, String field) {
        if (field.equals("CLASS")) return Arrays.stream(GuardianClass.values()).filter(c -> c != GuardianClass.NONE)
                .map(c -> new WeaponScreenView.CharacterOption(c.name(), className(c),
                        classDescription(c), c == cls, true, "직업 변경은 즉시 적용됩니다. 능력 구성은 선택한 직업에 맞춰집니다.")).toList();
        if (cls == GuardianClass.NONE) return List.of();
        if (field.equals("SUBCLASS")) return CharacterLoadouts.subclasses(cls).stream()
                .map(e -> new WeaponScreenView.CharacterOption(e.name(), elementName(e),
                        className(cls) + "의 " + elementName(e) + " 하위직업입니다.", e == element, true,
                        "하위직업 변경 시 해당 속성의 능력 구성이 즉시 적용됩니다.")).toList();
        if (element == null) return List.of();
        AbilitySlot slot = AbilitySlot.valueOf(field);
        Identifier equipped = data.loadout().map(l -> l.get(slot)).orElse(null);
        // The central service owns class/subclass membership, including shared class abilities.
        return CharacterLoadouts.options(cls, element, slot).stream()
                .map(a -> new WeaponScreenView.CharacterOption(a.id().toString(), a.displayName(),
                        abilityDescription(a), a.id().equals(equipped), true,
                        className(cls) + " · " + elementName(element) + "에서 선택 가능 · " + fieldName(field) + "에 즉시 장착")).toList();
    }

    private static String fieldName(String field) {
        return switch (field) {
            case "CLASS" -> "직업"; case "SUBCLASS" -> "하위직업"; case "GRENADE" -> "수류탄";
            case "MELEE" -> "근접 능력"; case "CLASS_ABILITY" -> "직업 능력"; case "SUPER" -> "궁극기"; case "JUMP" -> "점프";
            default -> "능력";
        };
    }

    private static String className(GuardianClass cls) {
        return switch (cls) { case TITAN -> "타이탄"; case HUNTER -> "헌터"; case WARLOCK -> "워록"; case NONE -> "미선택"; };
    }

    private static String elementName(Element element) {
        if (element == null) return "미선택";
        return switch (element) { case ARC -> "전기"; case SOLAR -> "태양"; case VOID -> "공허"; case KINETIC -> "공용"; };
    }

    private static String classDescription(GuardianClass cls) {
        return switch (cls) {
            case TITAN -> "방벽과 강력한 근접 능력을 사용하는 수호자입니다.";
            case HUNTER -> "회피와 기동성을 활용하는 수호자입니다.";
            case WARLOCK -> "균열과 빛의 능력을 사용하는 수호자입니다.";
            case NONE -> "직업을 선택하세요.";
        };
    }

    private static String abilityDescription(Ability ability) {
        if (ability.slot() == AbilitySlot.JUMP) return switch (ability.id().getPath()) {
            case "hunter/double_jump" -> "공중에서 한 번 더 점프해 더 높이 상승합니다.";
            case "hunter/strafe_jump" -> "공중에서 한 번 더 점프하며 입력 방향으로 궤도를 바꿉니다.";
            case "hunter/triple_jump" -> "착지 전 두 번 더 점프해 높이와 체공을 나눠 제어합니다.";
            case "titan/high_lift" -> "높은 상승에 특화된 리프트. 공중 점프로 켜고 다시 눌러 중단합니다.";
            case "titan/jump" -> "방향 제어에 특화된 리프트. 공중 점프로 켜고 다시 눌러 중단합니다.";
            case "titan/catapult_lift" -> "강한 초기 추진력의 리프트. 공중 재입력은 남은 추진 자원을 공유합니다.";
            case "warlock/strafe_glide" -> "활공 중 방향 제어를 강화합니다. 상승 중 켜면 상승 관성을 유지합니다.";
            case "warlock/burst_glide" -> "활공을 켤 때 전진 추진을 강화합니다. 낙하를 새 상승으로 바꾸지는 않습니다.";
            case "warlock/jump" -> "전진 추진과 방향 제어를 절충한 활공. 다시 누르면 중단하고 남은 자원으로 재개합니다.";
            default -> "공중 이동 방향으로 짧게 점멸합니다. 벽과 천장을 통과할 수 없습니다.";
        };
        return className(ability.guardianClass()) + " · " + elementName(ability.element()) + " "
                + fieldName(ability.slot().name()) + " 능력입니다. 선택하면 해당 슬롯에 즉시 장착됩니다.";
    }
}
