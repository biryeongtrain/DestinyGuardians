package kim.biryeong.destiny.weapon;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.arguments.IntegerArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;

/** OP-only model previews and explicit live-combat load; use/reload inputs need no OP. */
public final class WeaponCommands {
    private WeaponCommands() {}
    public static void register() {
        WeaponPerkCommands.register();
        WeaponAccessibility.init();
        WeaponAccessibilityCommands.register();
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> {
            var root = Commands.literal("destiny").then(Commands.literal("weapon")
                    .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                    .then(Commands.literal("list").executes(c -> list(c, null))
                            .then(Commands.argument("family", StringArgumentType.word())
                                    .suggests((c,b) -> SharedSuggestionProvider.suggest(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).distinct(), b))
                                    .executes(c -> list(c, StringArgumentType.getString(c, "family")))))
                    .then(Commands.literal("equip").then(Commands.argument("id", StringArgumentType.word())
                            .suggests((c,b) -> SharedSuggestionProvider.suggest(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id), b))
                            .executes(c -> equip(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> equip(c, EntityArgument.getPlayer(c,"player"))))))
                    .then(Commands.literal("load").then(Commands.argument("id", StringArgumentType.word())
                            .suggests((c,b) -> SharedSuggestionProvider.suggest(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::id), b))
                            .executes(c -> load(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> load(c, EntityArgument.getPlayer(c,"player"))))))
                    .then(Commands.literal("standalone").executes(c -> {
                        WeaponLoadout.standalone(c.getSource().getPlayerOrException());return 1;
                    }).then(Commands.argument("player",EntityArgument.player()).executes(c -> {
                        WeaponLoadout.standalone(EntityArgument.getPlayer(c,"player"));return 1;
                    })))
                    .then(Commands.literal("reload").executes(c -> WeaponRuntime.reload(c.getSource().getPlayerOrException()) ? 1 : fail(c,"재장전 불가: 탄창·예비탄·현재 동작을 확인하세요.")))
                    .then(Commands.literal("status").executes(c -> status(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> status(c, EntityArgument.getPlayer(c,"player")))))
                    .then(Commands.literal("airborne").then(Commands.argument("bonus", IntegerArgumentType.integer(-100, 200))
                            .executes(c -> airborne(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> airborne(c, EntityArgument.getPlayer(c,"player"))))))
                    .then(Commands.literal("pose").then(Commands.argument("pose", StringArgumentType.word())
                            .suggests((c,b) -> SharedSuggestionProvider.suggest(new String[]{"hip","ads","inspect"}, b))
                            .executes(c -> pose(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> pose(c, EntityArgument.getPlayer(c,"player"))))))
                    .then(Commands.literal("grip").then(Commands.argument("grip", StringArgumentType.word())
                            .suggests((c,b) -> SharedSuggestionProvider.suggest(new String[]{"native","two_hand"}, b))
                            .executes(c -> grip(c, c.getSource().getPlayerOrException()))
                            .then(Commands.argument("player", EntityArgument.player()).executes(c -> grip(c, EntityArgument.getPlayer(c,"player")))))));
            dispatcher.register(root);
            dispatcher.register(Commands.literal("destiny").then(Commands.literal("loadout")
                    .then(Commands.literal("equip").executes(c -> {
                        var player=c.getSource().getPlayerOrException();
                        String error=WeaponLoadout.equipHeld(player);
                        if(error!=null)return fail(c,error);
                        c.getSource().sendSuccess(()->Component.literal("장착 완료 · 1 물리 / 2 에너지 / 3 파워 · 기존 탄약 보존"),false);
                        return 1;
                    }))
                    .then(Commands.literal("select").then(Commands.argument("slot",StringArgumentType.word())
                            .suggests((c,b)->SharedSuggestionProvider.suggest(new String[]{"kinetic","energy","power"},b))
                            .executes(c->{
                                WeaponSlot slot;
                                try { slot=WeaponSlot.valueOf(StringArgumentType.getString(c,"slot").toUpperCase(java.util.Locale.ROOT)); }
                                catch(IllegalArgumentException e) { return fail(c,"슬롯: kinetic / energy / power"); }
                                return WeaponLoadout.select(c.getSource().getPlayerOrException(),slot)?1:fail(c,"장착된 슬롯만 선택할 수 있습니다.");
                            })))
                    .then(Commands.literal("status").executes(c -> {
                        var player=c.getSource().getPlayerOrException();
                        c.getSource().sendSuccess(()->Component.literal("three-slot loadout = "+WeaponLoadout.enabled(player)),false);
                        for(var e:WeaponLoadout.equipped(player))c.getSource().sendSuccess(()->Component.literal(
                                (e.slot().hotbar()+1)+" "+e.slot()+" · "+e.weapon().name()+" · "+e.characteristics().ammo()),false);
                        return WeaponLoadout.equipped(player).size();
                    }))));

        });
    }
    private static int list(CommandContext<CommandSourceStack> c, String family) {
        var entries = family == null ? WeaponCatalog.all() : WeaponCatalog.family(family);
        if (entries.isEmpty()) return fail(c,"알 수 없는 무기군: " + family);
        c.getSource().sendSuccess(() -> Component.literal("W30 모델 프리뷰 " + entries.size() + "종 (사격 기능 아님)"), false);
        for (var e : entries) c.getSource().sendSuccess(() -> Component.literal(e.id() + " · " + e.family() + "/" + e.frame()), false);
        return entries.size();
    }
    private static int equip(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        var entry = WeaponCatalog.find(StringArgumentType.getString(c,"id"));
        if (entry.isEmpty()) return fail(c,"알 수 없는 무기 모델");
        var held = player.getMainHandItem();
        if (!held.isEmpty() && (WeaponModels.entry(held).isEmpty() || held.is(WeaponCombatItem.INSTANCE)))
            return fail(c,"기존 아이템·전투 탄약 보호: 주 손을 먼저 비워 주세요.");
        player.setItemInHand(InteractionHand.MAIN_HAND, WeaponModels.create(entry.get()));
        c.getSource().sendSuccess(() -> Component.literal(entry.get().name() + " 모델 장착 (시각 프리뷰)"), false);
        return 1;
    }
    private static int load(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        var entry = WeaponCatalog.find(StringArgumentType.getString(c,"id"));
        if (entry.isEmpty()) return fail(c,"알 수 없는 무기 모델");
        var held = player.getMainHandItem();
        if (!held.isEmpty() && (WeaponModels.entry(held).isEmpty() || held.is(WeaponCombatItem.INSTANCE)))
            return fail(c,"기존 아이템·전투 탄약 보호: 주 손을 먼저 비워 주세요.");
        // Preserve the owner's cooldown when load replaces a preview.
        player.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(entry.get()));
        c.getSource().sendSuccess(() -> Component.literal("[전투] " + entry.get().name()
                + (entry.get().family().equals("glaive")
                    ? " · 좌클릭 무료 근접 · 우클릭 발사 · 웅크리기 방패/방패사격 · Q 재장전"
                    : " · 우클릭 발사/충전 · 좌클릭 ADS 토글 · Q 재장전 · 검 좌클릭 근접")
                + (WeaponLoadout.enabled(player) ? " · 먼저 /destiny loadout equip 으로 슬롯 장착" : "")), false);
        return 1;
    }
    private static int status(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        var entry = WeaponItems.entry(player.getMainHandItem());
        if (entry.isEmpty()) return fail(c,"/destiny weapon load <id>로 전투 무기를 장착하세요.");
        var p = WeaponProfile.forEntry(entry.get());
        var ammo = WeaponItems.magazine(player.getMainHandItem(), p);
        c.getSource().sendSuccess(() -> Component.literal(entry.get().name() + " · " + p.mode()
                + " · 탄창 " + ammo.rounds() + "/" + p.magazine() + " · 예비 " + (p.infiniteReserve() ? "∞" : ammo.reserve())
                + " · 재장전 " + WeaponRuntime.reloading(player)+" · ADS "+WeaponAiming.progress(player)+" · bloom "+WeaponAiming.bloom(player)
                + (WeaponExotics.ace(entry.get())?" · Mori "+WeaponAce.rounds(player)+" · Firefly "+WeaponAce.fireflyRemaining(player):"")), false);
        if (WeaponAccuracy.supports(entry.get())) c.getSource().sendSuccess(() -> Component.literal(
                "공중 효율 " + WeaponAccuracy.airborne(entry.get(), player.getMainHandItem())
                + " (기본 " + WeaponAccuracy.baseAirborne(entry.get()) + " / 프레임 +" + WeaponAccuracy.frameAirborne(entry.get())
                + " / 추가 " + WeaponAccuracy.airborneBonus(player.getMainHandItem()) + ")"
                + " · " + (WeaponAccuracy.airborne(player) ? "공중" : "지상/수중/등반")
                + " · 탄퍼짐 반각 " + String.format(java.util.Locale.ROOT, "%.3f°", WeaponAiming.coneDegrees(player))), false);
        if (ammo.overflow() > 0) c.getSource().sendSuccess(() -> Component.literal(
                "[W47 이관 보존탄] " + ammo.overflow() + " · 총 보유 " + ammo.total()
                        + " · 정상 재장전 시 순차 사용 (HUD는 현재 탄창/예비 용량만 표시)"), false);
        WeaponRuntime.glaiveStatus(player).ifPresent(g->c.getSource().sendSuccess(()->Component.literal(
                "월도 방패 "+Math.round(g.energy()*100)+"% · 방어 "+g.guarding()+" · 콤보 "+g.combo()
                        +" · 웅크리기 방패/방패사격 · Q 재장전"),false));
        return 1;
    }
    private static int airborne(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        int bonus = IntegerArgumentType.getInteger(c, "bonus");
        if (!WeaponAccuracy.setAirborneBonus(player.getMainHandItem(), bonus))
            return fail(c, "공중 효율을 설정할 전투 사격 무기를 먼저 장착하세요.");
        player.containerMenu.broadcastChanges();
        c.getSource().sendSuccess(() -> Component.literal("추가 공중 효율 " + bonus + " · 0으로 기본값 복원"), false);
        return status(c, player);
    }
    private static int pose(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        WeaponModels.Pose pose;
        try { pose = WeaponModels.Pose.valueOf(StringArgumentType.getString(c,"pose").toUpperCase(java.util.Locale.ROOT)); }
        catch (IllegalArgumentException e) { return fail(c,"포즈: hip / ads / inspect"); }
        if (!WeaponModels.setPose(player.getMainHandItem(), pose)) return fail(c,"W30 무기 프리뷰를 먼저 장착하세요.");
        player.containerMenu.broadcastChanges();
        return 1;
    }
    private static int fail(CommandContext<CommandSourceStack> c,String message) {
        c.getSource().sendFailure(Component.literal(message));return 0;
    }
    private static int grip(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        WeaponModels.Grip grip;
        try { grip = WeaponModels.Grip.valueOf(StringArgumentType.getString(c,"grip").toUpperCase(java.util.Locale.ROOT)); }
        catch (IllegalArgumentException e) { return fail(c,"그립: native / two_hand"); }
        var replacement = WeaponModels.withGrip(player.getMainHandItem(), grip);
        if (replacement.isEmpty()) return fail(c,"지원하는 무기 프리뷰를 먼저 장착하세요. 활·검은 native만 지원합니다.");
        player.setItemInHand(InteractionHand.MAIN_HAND, replacement.get());
        player.containerMenu.broadcastChanges();
        c.getSource().sendSuccess(() -> Component.literal("무기 그립: " + grip.name().toLowerCase(java.util.Locale.ROOT)), false);
        return 1;
    }
}
