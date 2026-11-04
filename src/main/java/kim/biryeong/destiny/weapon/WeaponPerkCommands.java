package kim.biryeong.destiny.weapon;

import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/** Player-owned prototype socket selection, not OP item creation or a complete random-roll system. */
public final class WeaponPerkCommands {
    private WeaponPerkCommands() {}
    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
            dispatcher.register(Commands.literal("destiny").then(Commands.literal("perk")
                .then(Commands.literal("status").executes(WeaponPerkCommands::status))
                .then(Commands.literal("list").executes(WeaponPerkCommands::status))
                .then(Commands.literal("select").then(Commands.argument("id", StringArgumentType.word())
                    .suggests((c, b) -> SharedSuggestionProvider.suggest(
                            WeaponPerks.choices(c.getSource().getPlayerOrException().getMainHandItem()), b))
                    .executes(c -> change(c, false))))
                .then(Commands.literal("clear").executes(c -> change(c, true))))));
    }
    private static boolean eligible(ServerPlayer p) {
        return p.isAlive() && !p.isRemoved() && !p.isSpectator() && !p.hasDisconnected()
                && !kim.biryeong.destiny.ability.AbilityService.inSuper(p);
    }
    private static int change(CommandContext<CommandSourceStack> c, boolean clear) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = c.getSource().getPlayerOrException();
        var stack = p.getMainHandItem();
        if (!eligible(p) || WeaponItems.entry(stack).isEmpty())
            return fail(c, "소유한 전투 무기를 들어 주세요. 궁극기·관전·프리뷰 중에는 변경할 수 없습니다.");
        String id = clear ? null : StringArgumentType.getString(c, "id");
        if (!clear && !WeaponPerks.ids().contains(id))
            return fail(c, "아직 구현되지 않은 특성입니다.");
        // W320: official Heavy Snapshot rolls use the local 0.8 scalar (w320-snapshot-heavy.json).
        boolean wasFullAuto=WeaponFullAuto.selected(p);
        boolean changed;
        if (clear) changed = WeaponPerks.clear(stack);
        else {
            boolean already = WeaponPerks.selected(stack, id).isPresent();
            if (!already && !WeaponPerks.select(stack, id))
                return fail(c, "선택한 무기의 공식 소켓 풀에는 해당 특성이 없습니다.");
            changed = !already;
        }
        if (changed) {
            if(wasFullAuto!=WeaponFullAuto.selected(p))WeaponRuntime.inputSettingsChanged(p);
            WeaponAmbitiousAssassin.changed(p,stack); WeaponClownCartridge.changed(p,stack); WeaponAdagio.changed(p,stack); WeaponWhirlwindBlade.changed(p,stack); WeaponEnGarde.changed(p,stack); WeaponOpeningShot.changed(p,stack); WeaponBoxBreathing.changed(p,stack); WeaponDynamicSway.changed(p,stack); WeaponAssassinsBlade.changed(p,stack); WeaponPulseMonitor.changed(p,stack); WeaponUnrelenting.changed(p,stack); WeaponKillingTally.changed(p,stack); WeaponSympatheticArsenal.changed(p,stack); WeaponRelentlessStrikes.changed(p,stack); WeaponTirelessBlade.changed(p,stack);
            WeaponCornered.changed(p,stack); WeaponBackupPlan.changed(p,stack); WeaponEncore.changed(p,stack); WeaponWellRounded.changed(p,stack);
            WeaponEnergyPerks.changed(p,stack);
            WeaponPugilist.changed(p,stack);
            WeaponEnsemble.changed(p, stack);
            WeaponHolster.changed(p, stack);
            PerkBatchC.changed(p, stack); // W322 batch C
            WeaponKillClip.changed(p, stack);
            WeaponOutlaw.changed(p, stack);
            WeaponFeedingFrenzy.changed(p, stack);
            WeaponRapidHit.changed(p, stack);
            WeaponPerpetualMotion.changed(p, stack);
            WeaponTapTheTrigger.changed(p, stack);
            WeaponFrenzy.changed(p, stack);
            WeaponAdrenalineJunkie.changed(p, stack); kim.biryeong.destiny.weapon.WeaponFocusedFury.changed(p, stack);
            WeaponStatsForAll.changed(p,stack); WeaponHeatingUp.changed(p,stack); WeaponThreatDetector.changed(p,stack); WeaponZenMoment.changed(p,stack);
            WeaponOneForAll.changed(p, stack);
            WeaponSurrounded.changed(p, stack);
            WeaponSwashbuckler.changed(p, stack);
            WeaponMultikillClip.changed(p, stack);
            WeaponSubsistence.changed(p, stack);
            WeaponGraveRobber.changed(p, stack);
            WeaponArcherTempo.changed(p, stack);
            WeaponRampage.changed(p, stack);
            WeaponPrecisionReturn.changed(p, stack);
            WeaponDemolitionist.changed(p, stack);
            PerkBatchD.changed(p, stack); // W323 batch D
            PerkBatchB.changed(p, stack); // W321 batch B
            PerkBatchA.changed(p, stack); // W320 batch A
            p.getInventory().setChanged(); p.containerMenu.broadcastChanges();
        }
        c.getSource().sendSuccess(() -> Component.literal(clear ? "선택 특성 해제 · 탄약 보존"
                : WeaponPerks.name(id) + " 선택 · 같은 소켓의 다른 특성만 교체 · 탄약 보존"), false);
        return 1;
    }
    private static int status(CommandContext<CommandSourceStack> c) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = c.getSource().getPlayerOrException();
        var stack = p.getMainHandItem();
        if (WeaponItems.entry(stack).isEmpty()) return fail(c, "소유한 전투 무기를 먼저 들어 주세요.");
        var selected = WeaponPerks.ids().stream().filter(id -> WeaponPerks.selected(stack, id).isPresent()).map(WeaponPerks::name).toList();
        c.getSource().sendSuccess(() -> Component.literal("선택 특성: " + (selected.isEmpty() ? "없음" : selected)
                + " · 구현된 특성 " + WeaponPerks.ids().size() + "종"), false);
        for (String id : WeaponPerks.choices(stack)) c.getSource().sendSuccess(() -> Component.literal(
                "선택 가능: " + id + " · 공식 소켓 " + WeaponPerks.available(stack, id).stream().map(WeaponPerks.Roll::socket).toList()), false);
        if (WeaponPerks.choices(stack).isEmpty()) c.getSource().sendSuccess(() -> Component.literal("이 무기의 확인된 구현 특성 소켓 없음"), false);
        return 1;
    }
    private static int fail(CommandContext<CommandSourceStack> c, String message) {
        c.getSource().sendFailure(Component.literal(message)); return 0;
    }
}
