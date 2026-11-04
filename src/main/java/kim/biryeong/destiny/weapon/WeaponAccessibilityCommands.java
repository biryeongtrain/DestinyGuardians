package kim.biryeong.destiny.weapon;

import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/** Non-OP self-only accessibility commands. No target argument or fixture override. */
public final class WeaponAccessibilityCommands {
    private WeaponAccessibilityCommands() {}

    public static void register() {
        WeaponAccessibility.init();
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) ->
                dispatcher.register(Commands.literal("destiny")
                        .then(Commands.literal("settings")
                                .then(Commands.literal("full_auto")
                                        .requires(source -> source.getEntity() instanceof ServerPlayer)
                                        .executes(WeaponAccessibilityCommands::status)
                                        .then(Commands.literal("on").executes(c -> change(c, true)))
                                        .then(Commands.literal("off").executes(c -> change(c, false)))))));
    }

    private static int change(CommandContext<CommandSourceStack> context, boolean fullAuto)
            throws CommandSyntaxException {
        WeaponAccessibility.setEnabled(context.getSource().getPlayerOrException(), fullAuto);
        return status(context);
    }

    private static int status(CommandContext<CommandSourceStack> context) throws CommandSyntaxException {
        boolean fullAuto = WeaponAccessibility.enabled(context.getSource().getPlayerOrException());
        context.getSource().sendSuccess(() -> Component.literal(
                "자동 사격 = " + (fullAuto ? "켜짐" : "꺼짐")
                        + " · 활·검·해제 기폭 무기 제외 · 근접 자동 공격 미지원"), false);
        return 1;
    }
}
