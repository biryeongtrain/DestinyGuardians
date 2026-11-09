package kim.biryeong.destiny.test;

import kim.biryeong.destiny.loot.Loot;
import kim.biryeong.destiny.tutorial.Guide;
import kim.biryeong.destiny.tutorial.Tutorial;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.commands.Commands;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSystemChatPacket;
import net.minecraft.network.protocol.game.ServerboundChatCommandPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;

/** Real registered command tree and outgoing chat actions; not a native mouse-click test. */
public final class GuideCommandGameTests {
    private static void check(GameTestHelper h, boolean value, String why) {
        h.assertTrue(value, Component.literal(why));
    }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p = TestPlayers.create(h, new Vec3(2, 1, 2), 0, 0, name);
        TestCleanup.register(h, () -> {
            run(p, "/안내 중단");
            joined().remove(p.getUUID());
            TestPlayers.remove(p);
        });
        return p;
    }
    private static int run(ServerPlayer p, String command) {
        try {
            return p.level().getServer().getCommands().getDispatcher()
                    .execute(Commands.trimOptionalPrefix(command), p.createCommandSourceStack());
        } catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) {
            throw new AssertionError("Clickable command did not parse: " + command, e);
        }
    }
    @SuppressWarnings("unchecked") private static <T> T field(String name) {
        try {
            var field = Guide.class.getDeclaredField(name); field.setAccessible(true);
            return (T) field.get(null);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static AttachmentType<Integer> state() { return field("STATE"); }
    private static Map<UUID, Integer> joined() { return field("JOINED"); }
    private static void offer(ServerPlayer p) {
        int now = p.level().getServer().getTickCount();
        joined().put(p.getUUID(), now - 200);
        try {
            var method = Guide.class.getDeclaredMethod("offer", ServerPlayer.class, int.class);
            method.setAccessible(true); method.invoke(null, p, now);
        } catch (ReflectiveOperationException e) { throw new AssertionError(e); }
    }
    private static void commands(Component component, List<String> out) {
        if (component.getStyle().getClickEvent() instanceof ClickEvent.RunCommand click) out.add(click.command());
        for (var sibling : component.getSiblings()) commands(sibling, out);
    }
    private static List<String> buttons(ServerPlayer p) {
        var out = new ArrayList<String>();
        for (var packet : TestPlayers.outbound(p))
            if (packet instanceof ClientboundSystemChatPacket chat) commands(chat.content(), out);
        return out;
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void koreanChoicesParseForOrdinaryPlayerAndRejectExtraArguments(GameTestHelper h) {
        var p = player(h, "GuideChoices");
        for (String root : List.of("안내", "guide")) {
            check(h, run(p, "/" + root) == 1 && Guide.active(p), "Bare alias starts guide");
            for (String action : List.of("시작", "공격전", "엔그램", "분해", "경매장"))
                check(h, run(p, "/" + root + " " + action) == 1 && Guide.active(p), "Korean action starts: " + action);
            check(h, run(p, "/" + root + " 다음") == 1, "Next parses while guide active");
            check(h, run(p, "/" + root + " 중단") == 1 && !Guide.active(p), "Stop retires session");
            check(h, run(p, "/" + root + " 나중에") == 1 && !Guide.active(p), "Defer works without an active session");
        }
        var dispatcher = p.level().getServer().getCommands().getDispatcher();
        for (String invalid : List.of("안내 없는항목", "안내 시작 extra", "guide 나중에 extra")) {
            try { dispatcher.execute(invalid, p.createCommandSourceStack()); h.fail(Component.literal("Accepted: " + invalid)); }
            catch (com.mojang.brigadier.exceptions.CommandSyntaxException expected) { }
        }
        check(h, !Guide.active(p) && Guide.doneMask(p) == 0, "Malformed commands do not restart or complete guide");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void actualInvitationButtonsWorkThroughUnsignedCommandPackets(GameTestHelper h) {
        var p = player(h, "GuideInvite");
        p.setAttached(Tutorial.COMPLETED_REVISION, Tutorial.REQUIRED_REVISION);
        p.setAttached(Loot.PROFILE, Loot.profile(p).withStarter());
        // Preserve a completed lesson and all one-time gift bits when deferring.
        int original = 1 | (1 << 8) | (1 << 9) | (1 << 10);
        p.setAttached(state(), original);
        TestPlayers.drain(p); offer(p);
        var actions = buttons(p);
        check(h, actions.equals(List.of("/안내 시작", "/안내 나중에")), "Use the actual emitted invitation buttons");
        p.connection.handleChatCommand(new ServerboundChatCommandPacket(Commands.trimOptionalPrefix(actions.get(1))));
        h.runAfterDelay(2, () -> {
            check(h, !Guide.active(p) && p.getAttachedOrElse(state(), 0) == (original | (1 << 4)), "Defer preserves progress and gifts");
            boolean acknowledged = TestPlayers.outbound(p).stream().anyMatch(packet ->
                    packet instanceof ClientboundSystemChatPacket chat && chat.content().getString().contains("안내는 나중에"));
            check(h, acknowledged, "Defer acknowledges the invitation without saying no guide is running");
            offer(p); check(h, buttons(p).isEmpty(), "Deferred invitation does not reappear");
            p.connection.handleChatCommand(new ServerboundChatCommandPacket(Commands.trimOptionalPrefix(actions.getFirst())));
        });
        h.runAfterDelay(4, () -> {
            check(h, Guide.active(p) && Guide.doneMask(p) == 1, "Original start button still starts remaining lessons later");
            run(p, "/안내 중단"); check(h, !Guide.active(p), "Started guide can be stopped");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=40)
    public void completedGuideReplayButtonsParseWithoutResettingProgress(GameTestHelper h) {
        var p = player(h, "GuideReplay");
        p.setAttached(state(), 0xF | (1 << 4)); TestPlayers.drain(p);
        run(p, "/안내");
        var actions = buttons(p);
        check(h, actions.equals(List.of("/안내 공격전", "/안내 엔그램", "/안내 분해", "/안내 경매장")), "Actual replay menu exposes all lessons");
        for (String action : actions)
            check(h, run(p, action) == 1 && Guide.active(p) && Guide.doneMask(p) == 0xF, "Replay parses and preserves completion: " + action);
        run(p, "/안내 나중에"); check(h, !Guide.active(p), "Defer also retires active replay");
        h.succeed();
    }
}
