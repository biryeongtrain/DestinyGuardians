package kim.biryeong.destiny.sound;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;

/** Bounded operator audition of bundled keys, personal playback only. Never changes global volume. */
public final class SoundCommands {
    private SoundCommands() { }
    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, environment) -> register(dispatcher));
    }
    public static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(
            Commands.literal("destiny")
                .then(Commands.literal("sound").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                    .then(Commands.literal("list").executes(c -> {
                        c.getSource().sendSuccess(() -> Component.literal(String.join(", ", DestinySounds.events())), false);
                        return DestinySounds.events().size();
                    }))
                    .then(Commands.literal("play").then(Commands.argument("event", StringArgumentType.word())
                        .suggests((c,b) -> SharedSuggestionProvider.suggest(DestinySounds.events(),b))
                        .executes(c -> play(c.getSource(), c.getSource().getPlayerOrException(), StringArgumentType.getString(c,"event")))
                        .then(Commands.argument("player", EntityArgument.player()).executes(c ->
                            play(c.getSource(),EntityArgument.getPlayer(c,"player"),StringArgumentType.getString(c,"event"))))))));
    }
    private static int play(net.minecraft.commands.CommandSourceStack source,
                            net.minecraft.server.level.ServerPlayer listener, String key) {
        if (!DestinySounds.personal(listener,key,.7f)) {
            source.sendFailure(Component.literal("선별되지 않은 사운드: " + key)); return 0;
        }
        source.sendSuccess(() -> Component.literal("사운드 청음: " + key + " → " + listener.getScoreboardName()),false);
        return 1;
    }
}
