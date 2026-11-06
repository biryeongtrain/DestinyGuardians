package kim.biryeong.destiny.activity;

import com.mojang.brigadier.arguments.StringArgumentType;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.strike.devils.DevilsLair;
import kim.biryeong.destiny.tutorial.Tutorial;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import java.util.*;
import java.util.function.BiPredicate;
import java.util.function.Function;

/** Shared personal departure boundary. Activity adapters retain all return/loadout/world ownership. */
public final class ActivityExit {
    private record Adapter(String id, String name, Function<ServerPlayer, Object> token,
                           BiPredicate<ServerPlayer, Object> leave) { }
    private static final List<Adapter> ADAPTERS = List.of(
            new Adapter("devils_lair", "악마의 소굴", DevilsLair::participationToken, DevilsLair::leave),
            new Adapter("guardian_rises", "눈을 뜨세요, 수호자", RisingCampaign::participationToken, RisingCampaign::leave),
            new Adapter("crucible_control", "시련의 장 · 점령", CrucibleRuntime::participationToken, CrucibleRuntime::leave),
            new Adapter("tutorial", "수호자 훈련", Tutorial::participationToken, Tutorial::leave));

    /** Immutable authority captured when the confirmation opens, never recalculated on confirm. */
    public static final class Ticket {
        private final ServerPlayer owner;
        private final Object connection, session;
        private final Adapter adapter;
        private Ticket(ServerPlayer owner, Adapter adapter, Object session) {
            this.owner = owner; connection = owner.connection; this.adapter = adapter; this.session = session;
        }
        public String id() { return adapter.id; }
        public String name() { return adapter.name; }
    }
    private record Pending(Ticket ticket, String nonce, int expires) { }
    private static final Map<UUID, Pending> PENDING = new HashMap<>();
    private static boolean initialized;
    private ActivityExit() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        CommandRegistrationCallback.EVENT.register((dispatcher, access, env) -> {
            dispatcher.register(Commands.literal("활동").then(Commands.literal("나가기")
                    .executes(c -> request(c.getSource().getPlayerOrException()) ? 1 : 0)
                    .then(Commands.literal("확인").then(Commands.argument("token", StringArgumentType.word())
                            .executes(c -> confirm(c.getSource().getPlayerOrException(), StringArgumentType.getString(c, "token")) ? 1 : 0)))
                    .then(Commands.literal("취소").then(Commands.argument("token", StringArgumentType.word())
                            .executes(c -> cancel(c.getSource().getPlayerOrException(), StringArgumentType.getString(c, "token")) ? 1 : 0)))));
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var p = handler.getPlayer(); var pending = PENDING.get(p.getUUID());
            if (pending != null && pending.ticket.owner == p) PENDING.remove(p.getUUID(), pending);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(server ->
                PENDING.entrySet().removeIf(e -> e.getValue().ticket.owner.level().getServer() == server));
        ServerTickEvents.END_SERVER_TICK.register(server -> PENDING.entrySet().removeIf(e -> {
            var pending = e.getValue(); var p = pending.ticket.owner;
            return p.level().getServer() == server && (server.getTickCount() > pending.expires || !current(p, pending.ticket));
        }));
    }

    public static Optional<Ticket> capture(ServerPlayer p) {
        if (p == null || !p.level().getServer().isSameThread() || p.hasDisconnected() || p.isRemoved()) return Optional.empty();
        for (var adapter : ADAPTERS) {
            Object token = adapter.token.apply(p);
            if (token != null) return Optional.of(new Ticket(p, adapter, token));
        }
        return Optional.empty();
    }

    public static boolean current(ServerPlayer p, Ticket ticket) {
        return ticket != null && p != null && ticket.owner == p && ticket.connection == p.connection
                && !p.hasDisconnected() && !p.isRemoved() && p.level().getServer().isSameThread()
                && ticket.adapter.token.apply(p) == ticket.session;
    }

    /** No alive/camera/down checks: the activity's existing teardown owns those states. */
    public static boolean leave(ServerPlayer p, Ticket ticket) {
        if (!current(p, ticket)) return false;
        boolean left = ticket.adapter.leave.test(p, ticket.session);
        if (left) PENDING.remove(p.getUUID());
        return left;
    }

    /** Chat confirmation remains reachable while a down scene or intro owns the view. */
    public static boolean request(ServerPlayer p) {
        var ticket = capture(p).orElse(null);
        if (ticket == null) { p.sendSystemMessage(Component.literal("현재 참가 중인 활동이 없습니다.")); return false; }
        String nonce = UUID.randomUUID().toString();
        PENDING.put(p.getUUID(), new Pending(ticket, nonce, p.level().getServer().getTickCount() + 600));
        p.sendSystemMessage(Component.literal(ticket.name() + "에서 나가시겠습니까? 본인만 활동에서 나갑니다.")
                .append(Component.literal("  [나가기]").withStyle(s -> s.withColor(0xE0645A)
                        .withClickEvent(new ClickEvent.RunCommand("/활동 나가기 확인 " + nonce))))
                .append(Component.literal("  [계속하기]").withStyle(s -> s.withColor(0x8FE3FF)
                        .withClickEvent(new ClickEvent.RunCommand("/활동 나가기 취소 " + nonce)))));
        return true;
    }

    public static boolean confirm(ServerPlayer p, String nonce) {
        var pending = PENDING.get(p.getUUID());
        if (pending == null || !pending.nonce.equals(nonce) || pending.ticket.owner != p
                || pending.ticket.connection != p.connection) return false;
        PENDING.remove(p.getUUID(), pending);
        if (p.level().getServer().getTickCount() > pending.expires || !leave(p, pending.ticket)) {
            p.sendSystemMessage(Component.literal("활동 상태가 바뀌어 나가기를 취소했습니다. 다시 선택하세요.")); return false;
        }
        return true;
    }
    public static boolean cancel(ServerPlayer p, String nonce) {
        var pending = PENDING.get(p.getUUID());
        if (pending == null || !pending.nonce.equals(nonce) || pending.ticket.owner != p
                || pending.ticket.connection != p.connection) return false;
        PENDING.remove(p.getUUID(), pending);
        p.sendSystemMessage(Component.literal("활동을 계속합니다.")); return true;
    }
}
