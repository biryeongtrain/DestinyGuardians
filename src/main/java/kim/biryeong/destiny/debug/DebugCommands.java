package kim.biryeong.destiny.debug;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kr.toxicity.model.api.BetterModel;
import kim.biryeong.destiny.fx.HunterVfx;
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
                        .then(Commands.literal("weapon-honed-reload").then(Commands.argument("player", EntityArgument.player())
                                .executes(c -> {
                                    // Authorized fixture input to the real transaction, not a completed charge grant.
                                    ServerPlayer p = EntityArgument.getPlayer(c, "player");
                                    boolean accepted = kim.biryeong.destiny.weapon.WeaponRuntime.reloadHoned(p);
                                    c.getSource().sendSuccess(() -> Component.literal("WeaponHoned accepted=" + accepted), false);
                                    return accepted ? 1 : 0;
                                })))
                        .then(Commands.literal("weapon-presentation-status").then(Commands.argument("player", EntityArgument.player())
                                .executes(c -> {
                                    // Read existing state only. In particular do not tick/bind a visual or Handling session.
                                    ServerPlayer p = EntityArgument.getPlayer(c, "player");
                                    var stack = p.getMainHandItem();
                                    var entry = kim.biryeong.destiny.weapon.WeaponItems.entry(stack);
                                    var swap = kim.biryeong.destiny.weapon.WeaponHandling.presentation(p);
                                    var readiness = kim.biryeong.destiny.weapon.WeaponHandling.readiness(p);
                                    var fusionCharge = kim.biryeong.destiny.weapon.WeaponRuntime.chargeState(p);
                                    var tracking = kim.biryeong.destiny.weapon.WeaponTracking.status(p);
                                    var perkRows = kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).entrySet().stream()
                                            .filter(e -> e.getKey().startsWith(kim.biryeong.destiny.hud.WeaponPerkHud.PREFIX)
                                                    && e.getKey().endsWith("label"))
                                            .map(e -> e.getKey().substring(kim.biryeong.destiny.hud.WeaponPerkHud.PREFIX.length())
                                                    + "@" + e.getValue().getLocation().y()).sorted().toList();
                                    var data = stack.getOrDefault(net.minecraft.core.component.DataComponents.CUSTOM_MODEL_DATA,
                                            net.minecraft.world.item.component.CustomModelData.EMPTY);
                                    var context = ((net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider)
                                            (Object)p.connection).getPacketContext();
                                    var model = kim.biryeong.destiny.weapon.WeaponCombatItem.INSTANCE
                                            .getPolymerItemModel(stack, context, p.registryAccess());
                                    String ammo = entry.map(e -> {
                                        var magazine = kim.biryeong.destiny.weapon.WeaponItems.magazine(stack,
                                                kim.biryeong.destiny.weapon.WeaponProfile.forEntry(e));
                                        return magazine.rounds() + "/" + magazine.reserve();
                                    }).orElse("none");
                                    c.getSource().sendSuccess(() -> Component.literal("WeaponPresentation tick="
                                            + p.level().getServer().getTickCount() + " weapon="
                                            + entry.map(kim.biryeong.destiny.weapon.WeaponCatalog.Entry::id).orElse("none")
                                            + " model=" + model + " floats=" + data.floats()
                                            + " swap=" + swap.map(v -> v.outgoing().id() + ":" + v.phase() + ":" + v.progress()).orElse("none")
                                            + " handling=" + readiness.map(v -> v.phase() + ":" + v.remainingTicks()).orElse("unobserved")
                                            + " grip=" + (kim.biryeong.destiny.weapon.WeaponModels.twoHanded(stack) ? "two_hand" : "native")
                                            + " entityPose=" + p.getPose()
                                            + " crouchPose=" + kim.biryeong.destiny.weapon.WeaponCrouchPresentation.crouched(stack)
                                            + " hitHud=" + kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).keySet().stream()
                                                    .filter(id -> id.startsWith(kim.biryeong.destiny.hud.WeaponHitHud.PREFIX)).sorted()
                                                    .map(id -> {
                                                        var h = kim.biryeong.minigamelib.displayhud.DisplayHud.getHud(p, id);
                                                        return id + "@" + (h instanceof kim.biryeong.minigamelib.displayhud.ItemDisplayHud item
                                                                ? item.getItem().get(net.minecraft.core.component.DataComponents.ITEM_MODEL) : "none");
                                                    }).toList()
                                            + " mori=" + kim.biryeong.destiny.weapon.WeaponAce.rounds(p)
                                            + " moriPips=" + kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).keySet().stream()
                                                    .filter(id -> id.startsWith(kim.biryeong.destiny.hud.AceReticleCounter.PREFIX)).count()
                                            + " reloading=" + kim.biryeong.destiny.weapon.WeaponRuntime.reloading(p)
                                            + " honing=" + kim.biryeong.destiny.weapon.WeaponIzanagi.honing(p)
                                            + " charge=" + kim.biryeong.destiny.weapon.WeaponIzanagi.charge(stack)
                                            + " fusionCharge=" + fusionCharge.phase() + ":" + fusionCharge.progress()
                                            + ":" + fusionCharge.emittedBolts() + "/" + fusionCharge.totalBolts()
                                            + " tracking=" + tracking.phase() + ":" + tracking.ticks() + "/" + tracking.requiredTicks()
                                            + " perkRows=" + perkRows
                                            + " ofa=" + kim.biryeong.destiny.weapon.WeaponOneForAll.progress(p)
                                            + ":" + kim.biryeong.destiny.weapon.WeaponOneForAll.remaining(p)
                                            + " surrounded=" + kim.biryeong.destiny.weapon.WeaponSurrounded.active(p)
                                            + " multikillClip=" + kim.biryeong.destiny.weapon.WeaponMultikillClip.stacks(p)
                                            + " perpetualMotion=" + kim.biryeong.destiny.weapon.WeaponPerpetualMotion.stacks(p)
                                            + " perpetualMovingTicks=" + kim.biryeong.destiny.weapon.WeaponPerpetualMotion.movingTicks(p)
                                            + " focusedFuryTicks=" + kim.biryeong.destiny.weapon.WeaponFocusedFury.remaining(p)
                                            + " focusedFuryHits=" + kim.biryeong.destiny.weapon.WeaponFocusedFury.progress(p)
                                            + " statsForAllTicks=" + kim.biryeong.destiny.weapon.WeaponStatsForAll.remaining(p)
                                            + " threatDetectorStacks=" + kim.biryeong.destiny.weapon.WeaponThreatDetector.stacks(p)
                                            + " quickdrawRemaining=" + kim.biryeong.destiny.weapon.WeaponQuickdraw.remaining(p)
                                            + " elementalCapacitor=" + kim.biryeong.destiny.weapon.WeaponElementalCapacitor.element(p).getSerializedName()
                                            + " elementalStabilityBonus=" + kim.biryeong.destiny.weapon.WeaponElementalCapacitor.stabilityBonus(p)
                                            + " firmlyPlanted=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.active(p)
                                            + " plantedStability=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.stabilityBonus(p)
                                            + " plantedHandling=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.handlingBonus(p)
                                            + " plantedCone=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.accuracyScalar(p)
                                            + " plantedGrowth=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.growthScalar(p)
                                            + " plantedYaw=" + kim.biryeong.destiny.weapon.WeaponFirmlyPlanted.yawScalar(p)
                                            + " zenMomentStacks=" + kim.biryeong.destiny.weapon.WeaponZenMoment.stacks(p)
                                            + " zenMomentTicks=" + kim.biryeong.destiny.weapon.WeaponZenMoment.remaining(p)
                                            + " zenFlinchScalar=" + kim.biryeong.destiny.weapon.WeaponZenMoment.flinchScalar(p)
                                            + " surplusCharges=" + kim.biryeong.destiny.weapon.WeaponSurplus.stacks(p)
                                            + " killingTally=" + kim.biryeong.destiny.weapon.WeaponKillingTally.stacks(p)
                                            + " whirlwindBlade=" + kim.biryeong.destiny.weapon.WeaponWhirlwindBlade.stacks(p)
                                            + ":" + kim.biryeong.destiny.weapon.WeaponWhirlwindBlade.remaining(p)
                                            + " enGardeTicks=" + kim.biryeong.destiny.weapon.WeaponEnGarde.remaining(p)
                                            + " assassinsBladeTicks=" + kim.biryeong.destiny.weapon.WeaponAssassinsBlade.remaining(p)
                                            + " pulseMonitor=" + kim.biryeong.destiny.weapon.WeaponPulseMonitor.active(p)
                                            + " unrelenting=" + kim.biryeong.destiny.weapon.WeaponUnrelenting.active(p)
                                            + " boxBreathingReady=" + kim.biryeong.destiny.weapon.WeaponBoxBreathing.ready(p)
                                            + " dynamicSway=" + kim.biryeong.destiny.weapon.WeaponDynamicSway.stacks(p)
                                            + " surplusStabilityBonus=" + kim.biryeong.destiny.weapon.WeaponSurplus.stabilityBonus(p)
                                            + " reloadDuration=" + kim.biryeong.destiny.weapon.WeaponRuntime.ammunition(p).map(a -> Integer.toString(a.reloadDuration())).orElse("none")
                                            + " heatingUpStacks=" + kim.biryeong.destiny.weapon.WeaponHeatingUp.stacks(p)
                                            + " heatingUpTicks=" + kim.biryeong.destiny.weapon.WeaponHeatingUp.remaining(p)
                                            + " statsForAllTargets=" + kim.biryeong.destiny.weapon.WeaponStatsForAll.progress(p)
                                            + " adrenalineJunkie=" + kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.stacks(p)
                                            + " adrenalineJunkieTicks=" + kim.biryeong.destiny.weapon.WeaponAdrenalineJunkie.remaining(p)
                                            + " frenzyTicks=" + kim.biryeong.destiny.weapon.WeaponFrenzy.remaining(p)
                                            + " frenzyCombatTicks=" + kim.biryeong.destiny.weapon.WeaponFrenzy.combatTicks(p)
                                            + " tapTheTriggerTicks=" + kim.biryeong.destiny.weapon.WeaponTapTheTrigger.remaining(p)
                                            + " tapTheTriggerStabilityBonus=" + kim.biryeong.destiny.weapon.WeaponTapTheTrigger.stabilityBonus(p)
                                            + " rapidHit=" + kim.biryeong.destiny.weapon.WeaponRapidHit.stacks(p)
                                            + " rapidHitTicks=" + kim.biryeong.destiny.weapon.WeaponRapidHit.remaining(p)
                                            + " rapidHitStabilityBonus=" + kim.biryeong.destiny.weapon.WeaponRapidHit.stabilityBonus(p)
                                            + " multikillClipTicks=" + kim.biryeong.destiny.weapon.WeaponMultikillClip.remaining(p)
                                            + " swashbuckler=" + kim.biryeong.destiny.weapon.WeaponSwashbuckler.stacks(p)
                                            + " swashbucklerTicks=" + kim.biryeong.destiny.weapon.WeaponSwashbuckler.remaining(p)
                                            + " frenzy=" + kim.biryeong.destiny.weapon.WeaponFeedingFrenzy.stacks(p)
                                            + ":" + kim.biryeong.destiny.weapon.WeaponFeedingFrenzy.remaining(p)
                                            + " ammo=" + ammo), false);
                                    return 1;
                                })))
                        .then(Commands.literal("critical-hud-status").then(Commands.argument("player", EntityArgument.player())
                                .executes(c -> {
                                    // Read the exact already-owned HUD; never spawn/update it for a QA query.
                                    ServerPlayer p = EntityArgument.getPlayer(c, "player");
                                    var hud = kim.biryeong.minigamelib.displayhud.DisplayHud.getHud(p,
                                            kim.biryeong.destiny.hud.IncomingDamageHud.PREFIX + "critical");
                                    String model = hud instanceof kim.biryeong.minigamelib.displayhud.ItemDisplayHud item
                                            ? String.valueOf(item.getItem().get(net.minecraft.core.component.DataComponents.ITEM_MODEL)) : "none";
                                    c.getSource().sendSuccess(() -> Component.literal("CriticalHud tick="
                                            + p.level().getServer().getTickCount() + " hp=" + p.getHealth()
                                            + " max=" + p.getMaxHealth() + " model=" + model
                                            + " entity=" + (hud == null ? -1 : hud.getEntityId())), false);
                                    return 1;
                                })))
                        .then(Commands.literal("camera-status").then(Commands.argument("player", EntityArgument.player())
                                .executes(c -> {
                                    ServerPlayer p = EntityArgument.getPlayer(c, "player");
                                    c.getSource().sendSuccess(() -> Component.literal("SuperCamera active="
                                            + kim.biryeong.destiny.camera.SuperCamera.active(p)
                                            + " rotations=" + kim.biryeong.destiny.camera.SuperCamera.rotations(p)
                                            + " body=" + p.position() + " yaw=" + p.getYRot() + " pitch=" + p.getXRot()
                                            + " ground=" + p.onGround() + " input=" + p.getLastClientInput()
                                            + " limbFrames=" + kim.biryeong.destiny.fx.PlayerAnimations.serverFrames(p)
                                            + " vfxCues=" + kim.biryeong.destiny.fx.SuperVfx.lifecycleCount(p)
                                            + " camera=" + kim.biryeong.destiny.camera.SuperCamera.cameraPosition(p)), false);
                                    return 1;
                                })))
                        .then(Commands.literal("owner-view")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.literal("first").executes(c -> ownerView(c, false)))
                                        .then(Commands.literal("third").executes(c -> ownerView(c, true)))))
                        .then(Commands.literal("dodge")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.argument("direction", StringArgumentType.word())
                                                .suggests((ctx, builder) -> net.minecraft.commands.SharedSuggestionProvider.suggest(
                                                        new String[]{"forward", "back", "left", "right"}, builder))
                                                .executes(DebugCommands::dodge))))
                        .then(Commands.literal("vfx")
                                .then(Commands.argument("player", EntityArgument.player())
                                        .then(Commands.argument("kind", StringArgumentType.word())
                                                .suggests((ctx, builder) -> net.minecraft.commands.SharedSuggestionProvider.suggest(
                                                        java.util.Arrays.stream(HunterVfx.Kind.values()).map(k -> k.name().toLowerCase(java.util.Locale.ROOT)), builder))
                                                .executes(DebugCommands::vfx))))
                        .then(Commands.literal("vfx-status").executes(ctx -> {
                            ctx.getSource().sendSuccess(() -> Component.literal("Active Hunter VFX=" + HunterVfx.activeCount()
                                    + " super-beams=" + kim.biryeong.destiny.fx.SuperVfx.activeCount()), false);
                            return HunterVfx.activeCount();
                        }))
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

    /** Production VFX factory preview, intentionally cosmetic and without damage. */
    private static int vfx(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        HunterVfx.Kind kind;
        try {
            kind = HunterVfx.Kind.valueOf(StringArgumentType.getString(ctx, "kind").toUpperCase(java.util.Locale.ROOT));
        } catch (IllegalArgumentException e) {
            ctx.getSource().sendFailure(Component.literal("Unknown VFX kind"));
            return 0;
        }
        boolean loop = kind == HunterVfx.Kind.VOID_VORTEX || kind == HunterVfx.Kind.VOID_SMOKE
                || kind == HunterVfx.Kind.VOID_ANCHOR;
        double radius = switch (kind) {
            case ARC_STRIKE -> 1.1;
            case SOLAR_KNIFE -> 0.65;
            case VOID_SMOKE -> 3.5;
            default -> 4.5;
        };
        Vec3 pos = player.position().add(Vec3.directionFromRotation(0, player.getYRot()).scale(6)).add(0, 0.2, 0);
        boolean played = HunterVfx.play(player, player.level(), pos, kind, radius,
                loop ? (kind == HunterVfx.Kind.VOID_SMOKE ? 100 : 60) : (kind == HunterVfx.Kind.ARC_FLASH || kind == HunterVfx.Kind.ARC_STRIKE ? 16 : 22));
        ctx.getSource().sendSuccess(() -> Component.literal("VFX preview " + kind + " played=" + played + " active=" + HunterVfx.activeCount()), false);
        return played ? 1 : 0;
    }

    /** QA direction injection exercises the real ability; it is NOT a client WASD transport test. */
    private static int dodge(CommandContext<CommandSourceStack> ctx) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(ctx, "player");
        String direction = StringArgumentType.getString(ctx, "direction");
        if (!List.of("forward", "back", "left", "right").contains(direction)) {
            ctx.getSource().sendFailure(Component.literal("Unknown dodge direction"));
            return 0;
        }
        var runtime = kim.biryeong.destiny.guardian.Guardians.runtime(player);
        var old = runtime.lastInput;
        boolean ok;
        try {
            runtime.lastInput = new net.minecraft.world.entity.player.Input(direction.equals("forward"),
                    direction.equals("back"), direction.equals("left"), direction.equals("right"), false, false, false);
            ok = kim.biryeong.destiny.input.InputRouter.dispatch(player,
                    kim.biryeong.destiny.input.GuardianAction.CLASS_ABILITY);
        } finally {
            runtime.lastInput = old;
        }
        ctx.getSource().sendSuccess(() -> Component.literal("QA dodge " + direction + " → " + ok
                + " (simulated direction; real ability)"), false);
        return ok ? 1 : 0;
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
        int count = DUMMIES.size() + LIMBS.size() + HunterVfx.activeCount() + kim.biryeong.destiny.fx.SuperVfx.activeCount();
        HunterVfx.clearAll();
        kim.biryeong.destiny.fx.SuperVfx.clearAll();
        DUMMIES.forEach(DummyTracker::close);
        DUMMIES.clear();
        LIMBS.forEach(EntityTracker::close);
        LIMBS.clear();
        ctx.getSource().sendSuccess(() -> Component.literal("Cleared " + count + " debug models"), false);
        return count;
    }
}
