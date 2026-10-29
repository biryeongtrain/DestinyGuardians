package kim.biryeong.destiny.command;

import com.mojang.brigadier.CommandDispatcher;
import com.mojang.brigadier.arguments.FloatArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityRegistry;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.CharacterLoadouts;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.GuardianData;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.guardian.GuardianPresets;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.InputRouter;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.SharedSuggestionProvider;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

import java.util.Arrays;
import java.util.Locale;

/**
 * /guardian 명령.
 * <pre>
 * /guardian class &lt;hunter|titan|warlock|none&gt; [player]
 * /guardian subclass &lt;arc|solar|void&gt; [player]          속성 기본 장착
 * /guardian equip &lt;slot&gt; &lt;ability&gt; [player]
 * /guardian info [player]
 * /guardian super &lt;0..100&gt; [player]                       (op)
 * /guardian reset [player]                                  쿨타임 초기화 (op)
 * /guardian action &lt;action&gt; &lt;player&gt;                     입력 경로 시뮬레이션 (op)
 * </pre>
 */
public final class GuardianCommands {
    private GuardianCommands() {
    }

    public static void register() {
        CommandRegistrationCallback.EVENT.register((dispatcher, registryAccess, environment) -> register(dispatcher));
    }

    private static void register(CommandDispatcher<CommandSourceStack> dispatcher) {
        LiteralArgumentBuilder<CommandSourceStack> root = Commands.literal("guardian");
        root.then(Commands.literal("class")
                .then(Commands.argument("class", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(Arrays.stream(GuardianClass.values()).map(GuardianClass::getSerializedName), b))
                        .executes(c -> setClass(c, self(c)))
                        .then(Commands.argument("player", EntityArgument.player()).requires(op())
                                .executes(c -> setClass(c, EntityArgument.getPlayer(c, "player"))))));
        root.then(Commands.literal("subclass")
                .then(Commands.argument("element", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(new String[]{"arc", "solar", "void"}, b))
                        .executes(c -> subclass(c, self(c)))
                        .then(Commands.argument("player", EntityArgument.player()).requires(op())
                                .executes(c -> subclass(c, EntityArgument.getPlayer(c, "player"))))));
        root.then(Commands.literal("equip")
                .then(Commands.argument("ability", StringArgumentType.greedyString())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(available(c.getSource()).stream().map(a -> a.id().toString()), b))
                        .executes(c -> equip(c, self(c), StringArgumentType.getString(c, "ability")))));
        root.then(Commands.literal("info")
                .executes(c -> info(c, self(c)))
                .then(Commands.argument("player", EntityArgument.player()).requires(op())
                        .executes(c -> info(c, EntityArgument.getPlayer(c, "player")))));
        root.then(Commands.literal("supers").executes(c -> supers(c, self(c))));
        root.then(Commands.literal("super").requires(op())
                .then(Commands.argument("percent", FloatArgumentType.floatArg(0, 100))
                        .executes(c -> superEnergy(c, self(c)))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(c -> superEnergy(c, EntityArgument.getPlayer(c, "player"))))));
        root.then(Commands.literal("reset").requires(op())
                .executes(c -> reset(c, self(c)))
                .then(Commands.argument("player", EntityArgument.player())
                        .executes(c -> reset(c, EntityArgument.getPlayer(c, "player")))));
        root.then(Commands.literal("action").requires(op())
                .then(Commands.argument("action", StringArgumentType.word())
                        .suggests((c, b) -> SharedSuggestionProvider.suggest(Arrays.stream(GuardianAction.values()).map(a -> a.name().toLowerCase(Locale.ROOT)), b))
                        .then(Commands.argument("player", EntityArgument.player())
                                .executes(GuardianCommands::action))));
        dispatcher.register(root);
    }

    private static java.util.function.Predicate<CommandSourceStack> op() {
        return Commands.hasPermission(Commands.LEVEL_GAMEMASTERS);
    }

    private static ServerPlayer self(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        return c.getSource().getPlayerOrException();
    }

    private static int setClass(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        GuardianClass cls;
        try {
            cls = GuardianClass.valueOf(StringArgumentType.getString(c, "class").toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            c.getSource().sendFailure(Component.literal("알 수 없는 직업"));
            return 0;
        }
        String error = CharacterLoadouts.selectClass(player, cls);
        if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
        c.getSource().sendSuccess(() -> Component.literal(player.getName().getString() + " → " + cls.getSerializedName()), false);
        return 1;
    }

    private static int subclass(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        Element element;
        try {
            element = Element.valueOf(StringArgumentType.getString(c, "element").toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            c.getSource().sendFailure(Component.literal("알 수 없는 속성"));
            return 0;
        }
        GuardianData data = Guardians.data(player);
        if (data.guardianClass() == GuardianClass.NONE) {
            c.getSource().sendFailure(Component.literal("먼저 /guardian class <hunter|titan|warlock>"));
            return 0;
        }
        if (!GuardianPresets.supported(element)) {
            c.getSource().sendFailure(Component.literal("지원하는 속성: arc, solar, void"));
            return 0;
        }
        String error = CharacterLoadouts.selectSubclass(player, element);
        if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
        c.getSource().sendSuccess(() -> Component.literal(player.getName().getString() + " → "
                + data.guardianClass().getSerializedName() + " / " + element.getSerializedName()), false);
        return 1;
    }

    private static int equip(CommandContext<CommandSourceStack> c, ServerPlayer player, String abilityId) {
        Identifier id = Identifier.tryParse(abilityId.trim());
        Ability ability = id == null ? null : AbilityRegistry.get(id).orElse(null);
        GuardianData data = Guardians.data(player);
        if (ability == null || ability.guardianClass() != data.guardianClass()) {
            c.getSource().sendFailure(Component.literal("장착할 수 없는 능력: " + abilityId));
            return 0;
        }
        String error = CharacterLoadouts.selectAbility(player, ability.slot(), id);
        if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
        c.getSource().sendSuccess(() -> Component.literal(ability.slot().getSerializedName() + " = " + ability.displayName()), false);
        return 1;
    }

    private static int info(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        GuardianData data = Guardians.data(player);
        StringBuilder sb = new StringBuilder("[수호자] ").append(player.getName().getString())
                .append(" class=").append(data.guardianClass().getSerializedName())
                .append(" super=").append(Math.round(data.superEnergy() * 100)).append('%');
        for (AbilitySlot slot : AbilitySlot.values()) {
            sb.append("\n ").append(slot.getSerializedName()).append(": ")
                    .append(AbilityService.equipped(player, slot).map(Ability::displayName).orElse("-"))
                    .append(" (cd ").append(data.cooldown(slot)).append("t)");
        }
        c.getSource().sendSuccess(() -> Component.literal(sb.toString()), false);
        return 1;
    }

    private static java.util.List<Ability> available(CommandSourceStack source) {
        var player = source.getPlayer();
        if (player == null) return java.util.List.of();
        var data = Guardians.data(player);
        return Arrays.stream(AbilitySlot.values()).flatMap(slot ->
                CharacterLoadouts.options(data.guardianClass(), CharacterLoadouts.subclass(data), slot).stream()).toList();
    }

    private static int supers(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        var data = Guardians.data(player);
        var supers = CharacterLoadouts.options(data.guardianClass(), CharacterLoadouts.subclass(data), AbilitySlot.SUPER);
        c.getSource().sendSuccess(() -> Component.literal("[궁극기 선택] /guardian equip <ID>\n"
                + supers.stream().map(a -> a.displayName() + " — " + a.id()).collect(java.util.stream.Collectors.joining("\n"))), false);
        return supers.size();
    }

    private static int superEnergy(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        float percent = FloatArgumentType.getFloat(c, "percent");
        Guardians.data(player).setSuperEnergy(percent / 100f);
        CombatHud.update(player);
        c.getSource().sendSuccess(() -> Component.literal("super = " + percent + "%"), false);
        return 1;
    }

    private static int reset(CommandContext<CommandSourceStack> c, ServerPlayer player) {
        for (AbilitySlot slot : AbilitySlot.values()) {
            Guardians.data(player).setCooldown(slot, 0);
        }
        CombatHud.update(player);
        c.getSource().sendSuccess(() -> Component.literal("cooldowns reset"), false);
        return 1;
    }

    private static int action(CommandContext<CommandSourceStack> c) throws CommandSyntaxException {
        ServerPlayer player = EntityArgument.getPlayer(c, "player");
        GuardianAction action;
        try {
            action = GuardianAction.valueOf(StringArgumentType.getString(c, "action").toUpperCase(Locale.ROOT));
        } catch (IllegalArgumentException e) {
            c.getSource().sendFailure(Component.literal("알 수 없는 동작"));
            return 0;
        }
        boolean ok = InputRouter.dispatch(player, action);
        c.getSource().sendSuccess(() -> Component.literal(action + " → " + ok), false);
        return ok ? 1 : 0;
    }
}
