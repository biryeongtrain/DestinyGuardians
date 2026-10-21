package kim.biryeong.destiny.debug;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.mod.platform.ModLocation;
import kr.toxicity.model.api.mod.platform.ModPlayer;
import kr.toxicity.model.api.tracker.DummyTracker;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/**
 * 개발용 검증 명령 (W1-05). 콘솔에서도 대상 플레이어를 지정해 실행할 수 있다.
 *
 * <pre>
 * /destiny debug model &lt;player&gt; &lt;model&gt; &lt;animation&gt;   플레이어 앞 6블록에 모델을 띄우고 애니메이션 반복
 * /destiny debug limb  &lt;player&gt; &lt;limb&gt; &lt;animation&gt; [loop] 플레이어 몸을 limb 모델로 바꿔 애니메이션 재생 (loop 는 clear 까지 반복)
 * /destiny debug clear                                    debug 로 띄운 모델 정리
 * </pre>
 */
public final class DebugCommands {
    private static final List<DummyTracker> DUMMIES = new ArrayList<>();
    private static final List<EntityTracker> LIMBS = new ArrayList<>();

    private DebugCommands() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> register(dispatcher));
    }

    private static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        dispatcher.register(Commands.literal("destiny")
                .requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.literal("debug")
                        .then(Commands.literal("owner-view")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.literal("first").executes(c -> ownerView(c, false)))
                                        .then(Commands.literal("third").executes(c -> ownerView(c, true)))))
                        .then(Commands.literal("model")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.argument("model", StringArgumentType.word())
                                                .then(Commands.argument("animation", StringArgumentType.word())
                                                        .executes(DebugCommands::model)))))
                        .then(Commands.literal("limb")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.argument("limb", StringArgumentType.word())
                                                .then(Commands.argument("animation", StringArgumentType.word())
                                                        .executes(ctx -> limb(ctx, false))
                                                        .then(Commands.literal("loop").executes(ctx -> limb(ctx, true)))))))
                        .then(Commands.literal("clear").executes(DebugCommands::clear))));
    }

    private static int model(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        String name = StringArgumentType.getString(ctx, "model");
        String animation = StringArgumentType.getString(ctx, "animation");
        var renderer = BetterModel.model(name).orElse(null);
        if (renderer == null) {
            ctx.getSource().sendFailure(Component.literal("Unknown model: " + name));
            return 0;
        }
        Vec3 forward = Vec3.directionFromRotation(0, player.getYRot()).scale(6);
        Vec3 pos = player.position().add(forward);
        DummyTracker tracker = renderer.create(ModLocation.of(player.level(), pos.x, pos.y, pos.z, 0, player.getYRot()));
        tracker.spawn(ModPlayer.of(player.connection));
        boolean animated = tracker.animate(animation, new AnimationModifier(0, 0, AnimationIterator.Type.LOOP));
        DUMMIES.add(tracker);
        ctx.getSource().sendSuccess(() -> Component.literal("Spawned " + name + " (" + animation + ", animated=" + animated + ")"), false);
        return 1;
    }

    /** QA override for testing owner visibility without installing GCB in the vision-only client. */
    private static int ownerView(CommandContext<CommandSourceStack> ctx, boolean third) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        var runtime = kim.biryeong.destiny.guardian.Guardians.runtime(player);
        runtime.gcbClient = third;
        runtime.gcbThirdPerson = third;
        kim.biryeong.destiny.fx.PlayerAnimations.refreshOwnerVisibility(player);
        ctx.getSource().sendSuccess(() -> Component.literal("QA owner-view=" + (third ? "third" : "first") + " (simulated; not GCB transport verification)"), false);
        return 1;
    }

    private static int limb(CommandContext<CommandSourceStack> ctx, boolean loop) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        String name = StringArgumentType.getString(ctx, "limb");
        String animation = StringArgumentType.getString(ctx, "animation");
        var renderer = BetterModel.limb(name).orElse(null);
        if (renderer == null) {
            ctx.getSource().sendFailure(Component.literal("Unknown limb: " + name));
            return 0;
        }
        EntityTracker tracker = renderer.getOrCreate(ModPlayer.of(player.connection), TrackerModifier.DEFAULT);
        boolean animated = loop
                ? tracker.animate(animation, new AnimationModifier(0, 0, AnimationIterator.Type.LOOP))
                : tracker.animate(animation, AnimationModifier.DEFAULT_WITH_PLAY_ONCE, tracker::close);
        if (!animated) {
            tracker.close();
        } else if (loop) {
            LIMBS.add(tracker);
        }
        ctx.getSource().sendSuccess(() -> Component.literal("Limb " + name + " / " + animation + " animated=" + animated), false);
        return animated ? 1 : 0;
    }

    private static int clear(CommandContext<CommandSourceStack> ctx) {
        int count = DUMMIES.size() + LIMBS.size();
        DUMMIES.forEach(DummyTracker::close);
        DUMMIES.clear();
        LIMBS.forEach(EntityTracker::close);
        LIMBS.clear();
        ctx.getSource().sendSuccess(() -> Component.literal("Cleared " + count + " debug models"), false);
        return count;
    }
}
