package kim.biryeong.destiny.economy;

import com.mojang.brigadier.arguments.LongArgumentType;
import com.mojang.brigadier.arguments.StringArgumentType;
import com.mojang.brigadier.context.CommandContext;
import com.mojang.brigadier.builder.LiteralArgumentBuilder;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.minecraft.commands.CommandSourceStack;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

/**
 * Player commands: /창고 (/vault), /우편 (/postmaster) [보내기 &lt;이름&gt; [메시지]], /경매장 (/auction) [검색어],
 * /미광체 (/glimmer). Admin: /destiny economy glimmer|status|expire.
 */
final class EconomyCommands {
    private EconomyCommands() { }

    static void init() {
        CommandRegistrationCallback.EVENT.register((d, registry, env) -> {
            for (String name : new String[]{"창고", "vault"}) d.register(Commands.literal(name).executes(c -> open(c, new EconomyMenus.VaultScreen())));
            for (String name : new String[]{"우편", "postmaster"}) d.register(Commands.literal(name)
                    .executes(c -> open(c, new EconomyMenus.MailScreen()))
                    .then(Commands.literal(name.equals("우편") ? "보내기" : "send").then(Commands.argument("name", StringArgumentType.word())
                            .executes(c -> send(c, null))
                            .then(Commands.argument("message", StringArgumentType.greedyString()).executes(c -> send(c, StringArgumentType.getString(c, "message")))))));
            for (String name : new String[]{"경매장", "auction"}) d.register(Commands.literal(name)
                    .executes(c -> open(c, new EconomyMenus.AuctionScreen("")))
                    .then(Commands.argument("query", StringArgumentType.greedyString())
                            .executes(c -> open(c, new EconomyMenus.AuctionScreen(StringArgumentType.getString(c, "query"))))));
            for (String name : new String[]{"미광체", "glimmer"}) d.register(Commands.literal(name).executes(c -> {
                var p = c.getSource().getPlayerOrException(); var l = Economy.ledger();
                if (l == null) return 0;
                c.getSource().sendSuccess(() -> Component.literal("미광체 " + EconomyMenus.glimmer(l.glimmer(p.getUUID()))), false);
                return 1;
            }));
            d.register(Commands.literal("destiny").then(admin()));
        });
    }

    private static LiteralArgumentBuilder<CommandSourceStack> admin() {
        return Commands.literal("economy").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                .then(Commands.literal("glimmer").then(Commands.argument("player", EntityArgument.player())
                        .then(Commands.literal("give").then(Commands.argument("amount", LongArgumentType.longArg(0)).executes(c -> glimmer(c, 1))))
                        .then(Commands.literal("take").then(Commands.argument("amount", LongArgumentType.longArg(0)).executes(c -> glimmer(c, -1))))
                        .then(Commands.literal("set").then(Commands.argument("amount", LongArgumentType.longArg(0)).executes(c -> glimmer(c, 0))))))
                .then(Commands.literal("status").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                    var p = EntityArgument.getPlayer(c, "player"); var l = Economy.ledger(); var id = p.getUUID();
                    String text = "glimmer=" + l.glimmer(id) + " vault=" + l.vault(id).size() + " mail=" + l.mail(id).size()
                            + " listings=" + l.listingsOf(id).size() + " market=" + l.listings().size()
                            + " menu=" + EconomyMenus.describe(p).orElse("-");
                    c.getSource().sendSuccess(() -> Component.literal(text), false);
                    return 1;
                })))
                .then(Commands.literal("expire").executes(c -> {
                    // QA: end every listing now (returns to sellers' postmasters on the next sweep).
                    var l = Economy.ledger();
                    int n = l.expire(Long.MAX_VALUE).size();
                    EconomyMenus.refreshAll(); Economy.save(false);
                    c.getSource().sendSuccess(() -> Component.literal("만료 처리 " + n + "건"), false);
                    return n;
                }))
                .then(Commands.literal("save").executes(c -> { Economy.save(true); return 1; }))
                .then(Commands.literal("click").then(Commands.argument("player", EntityArgument.player())
                        .then(Commands.argument("target", StringArgumentType.word())
                                .executes(c -> click(c, ""))
                                .then(Commands.argument("mode", StringArgumentType.word()).executes(c -> click(c, StringArgumentType.getString(c, "mode")))))))
                .then(Commands.literal("dump").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                    var p = EntityArgument.getPlayer(c, "player"); var l = Economy.ledger(); var id = p.getUUID();
                    var sb = new StringBuilder("vault=");
                    for (var i : l.vault(id)) sb.append(i.uid()).append(':').append(i.name()).append(',');
                    sb.append(" mail=");
                    for (var m : l.mail(id)) sb.append(m.id()).append(':').append(m.kind()).append(':').append(m.item() == null ? "-" : m.item().name()).append(':').append(m.glimmer()).append(',');
                    sb.append(" listings=");
                    for (var x : l.listings()) sb.append(x.id()).append(':').append(x.sellerName()).append(':').append(x.item().name()).append(':').append(x.price()).append(',');
                    sb.append(" inv=");
                    for (int i = 0; i < 36; i++) { var s = p.getInventory().getItem(i); if (!s.isEmpty()) sb.append(i).append(':').append(s.getHoverName().getString()).append(','); }
                    String text = sb.toString();
                    c.getSource().sendSuccess(() -> Component.literal(text), false);
                    return 1;
                })));
    }

    /** target: c<N> = chest slot N, i<N> = player inventory index N. mode: right / shift. */
    private static int click(CommandContext<CommandSourceStack> c, String mode) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = EntityArgument.getPlayer(c, "player");
        String t = StringArgumentType.getString(c, "target");
        int n = Integer.parseInt(t.substring(1));
        int slot = t.charAt(0) == 'i' ? EconomyMenus.inventorySlot(n) : n;
        boolean ok = EconomyMenus.qaClick(p, slot, mode.contains("right"), mode.contains("shift"));
        String after = EconomyMenus.describe(p).orElse("-");
        c.getSource().sendSuccess(() -> Component.literal("click " + t + " " + mode + " ok=" + ok + " menu=" + after), false);
        return ok ? 1 : 0;
    }

    private static int open(CommandContext<CommandSourceStack> c, EconomyMenus.Screen screen) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        EconomyMenus.open(c.getSource().getPlayerOrException(), screen);
        return 1;
    }

    private static int send(CommandContext<CommandSourceStack> c, String message) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        ServerPlayer p = c.getSource().getPlayerOrException(); var l = Economy.ledger();
        if (l == null) return 0;
        String name = StringArgumentType.getString(c, "name");
        var to = l.find(name);
        if (to.isEmpty()) { c.getSource().sendFailure(Component.literal("서버에 접속한 적이 있는 수호자만 우편을 받을 수 있습니다: " + name)); return 0; }
        if (to.get().equals(p.getUUID())) { c.getSource().sendFailure(Component.literal(EconomyLedger.Error.SELF_MAIL.message)); return 0; }
        if (message != null && message.codePointCount(0, message.length()) > EconomyLedger.MAX_MESSAGE) {
            c.getSource().sendFailure(Component.literal(EconomyLedger.Error.MESSAGE_TOO_LONG.message + " (최대 " + EconomyLedger.MAX_MESSAGE + "자)")); return 0;
        }
        EconomyMenus.open(p, new EconomyMenus.SendScreen(to.get(), l.name(to.get()), message));
        return 1;
    }

    private static int glimmer(CommandContext<CommandSourceStack> c, int mode) throws com.mojang.brigadier.exceptions.CommandSyntaxException {
        var p = EntityArgument.getPlayer(c, "player"); var l = Economy.ledger();
        long amount = LongArgumentType.getLong(c, "amount");
        l.touch(p.getUUID(), p.getGameProfile().name());
        var r = mode > 0 ? l.credit(p.getUUID(), amount) : mode < 0 ? l.debit(p.getUUID(), amount) : l.set(p.getUUID(), amount);
        if (!r.ok()) { c.getSource().sendFailure(Component.literal(r.error().message)); return 0; }
        Economy.changed(p.getUUID()); Economy.save(false);
        c.getSource().sendSuccess(() -> Component.literal(p.getGameProfile().name() + " 미광체 = " + r.value()), false);
        return 1;
    }
}
