package kim.biryeong.destiny.test;

import kim.biryeong.destiny.activity.ActivityExit;
import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.campaign.RisingLoadout;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.inventory.gear.*;
import kim.biryeong.destiny.tutorial.TutorialLoan;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSystemChatPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

/** Actual server controllers and their teardown; fixtures are not native keyboard or framebuffer acceptance. */
public final class ActivityExitW329GameTests {
    private static final String FLOOR = "destiny-test:floor", ENV = "destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean value, String why) { h.assertTrue(value, Component.literal(why)); }
    private static ServerPlayer player(GameTestHelper h, String name) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2, 1, 6), 0, 0, name);
        p.setNoGravity(true); p.setOnGround(true); h.getLevel().addNewPlayer(p);
        TestCleanup.register(h, () -> {
            GearScreen.close(p); ActivityExit.capture(p).ifPresent(ticket -> ActivityExit.leave(p, ticket));
            p.level().removePlayerImmediately(p, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static String command(Component component, String prefix) {
        if (component.getStyle().getClickEvent() instanceof ClickEvent.RunCommand click && click.command().startsWith(prefix))
            return click.command();
        for (var sibling : component.getSiblings()) { String found = command(sibling, prefix); if (found != null) return found; }
        return null;
    }
    private static String nonce(ServerPlayer p, String action) {
        String prefix = "/활동 나가기 " + action + " ";
        for (var packet : TestPlayers.outbound(p)) if (packet instanceof ClientboundSystemChatPacket chat) {
            String value = command(chat.content(), prefix);
            if (value != null) return value.substring(prefix.length());
        }
        throw new IllegalStateException("Expected actual clickable confirmation packet");
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=40)
    public void campaignExitRestoresRealLoanKeepsCheckpointAndRejectsEarlierRunTicket(GameTestHelper h) {
        var p = player(h, "ExitCampaign");
        var checkpoint = new RisingCampaign.Stored("GHOST_SCAN", false, false, false);
        p.setAttached(RisingCampaign.PROGRESS, checkpoint);
        check(h, RisingCampaign.start(p, false) == null, "Actual queued campaign starts");
        var first = ActivityExit.capture(p).orElseThrow();
        check(h, first.id().equals("guardian_rises"), "Campaign adapter selected");
        var original = new ItemStack(Items.DIAMOND, 7); p.getInventory().setItem(0, original);
        RisingLoadout.grantRifle(p);
        check(h, TutorialLoan.active(p), "Actual mission loan escrow acquired");
        check(h, ActivityExit.leave(p, first), "Shared service calls actual campaign leave");
        check(h, !RisingCampaign.participating(p) && !TutorialLoan.active(p), "Campaign ownership and loan retired");
        check(h, ItemStack.matches(p.getInventory().getItem(0), original), "Original equipment restored exactly once");
        check(h, checkpoint.equals(p.getAttached(RisingCampaign.PROGRESS)), "Incomplete queued exit preserves stored checkpoint");
        check(h, RisingCampaign.start(p, false) == null, "Same activity can be entered again");
        check(h, !ActivityExit.leave(p, first) && RisingCampaign.participating(p), "Old run ticket cannot leave new run");
        check(h, ActivityExit.leave(p, ActivityExit.capture(p).orElseThrow()), "Fresh ticket leaves the new run"); h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=50)
    public void gearButtonCancelsThenRejectsStaleConfirmationAndFreshConfirmLeaves(GameTestHelper h) {
        var p = player(h, "ExitGear");
        // The actual strike controller retains PREPARING membership without requiring a fabricated PlayerList login.
        // A bare queued RisingCampaign player is correctly dropped at its first server tick as disconnected.
        new Strike(h, java.util.List.of(p));
        check(h, kim.biryeong.destiny.strike.devils.DevilsLair.participating(p) && GearScreen.open(p),
                "Gear remains accessible while actual preparing activity owns player");
        check(h, !GearScreen.snapshot(p).orElseThrow().activityName().isBlank(), "Visible frame exposes activity leave action");
        point(p, GearLayout.leave()); GearScreen.click(p, false);
        check(h, GearScreen.snapshot(p).orElseThrow().stage() == GearLayout.Stage.ACTIVITY_EXIT,
                "Leave button opens confirmation, never exits directly");
        h.runAfterDelay(4, () -> {
            GearScreen.click(p, true);
            check(h, kim.biryeong.destiny.strike.devils.DevilsLair.participating(p) && GearScreen.snapshot(p).orElseThrow().stage() == GearLayout.Stage.GEAR,
                    "Back keeps activity and restores gear");
        });
        h.runAfterDelay(8, () -> {
            point(p, GearLayout.leave()); GearScreen.click(p, false);
            var old = ActivityExit.capture(p).orElseThrow();
            check(h, ActivityExit.leave(p, old), "Old activity leaves through its real teardown");
            new Strike(h, java.util.List.of(p));
            check(h, kim.biryeong.destiny.strike.devils.DevilsLair.participating(p), "Run replaced while confirmation remains open");
        });
        h.runAfterDelay(12, () -> {
            point(p, GearLayout.exitConfirm()); GearScreen.click(p, false);
            check(h, kim.biryeong.destiny.strike.devils.DevilsLair.participating(p) && GearScreen.snapshot(p).orElseThrow().stage() == GearLayout.Stage.GEAR,
                    "Old UI cannot leave another run of same activity");
        });
        h.runAfterDelay(16, () -> { point(p, GearLayout.leave()); GearScreen.click(p, false); });
        h.runAfterDelay(20, () -> {
            point(p, GearLayout.exitConfirm()); GearScreen.click(p, false);
            check(h, !kim.biryeong.destiny.strike.devils.DevilsLair.participating(p) && !GearScreen.active(p), "Fresh UI confirm exits and removes freeze/HUD"); h.succeed();
        });
    }
    private static void point(ServerPlayer p, kim.biryeong.destiny.inventory.WeaponScreenLayout.Box box) {
        GearScreen.qaPoint(p, box.x(), box.y());
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=60)
    public void crucibleConfirmationCancelsWithoutTeardownAndPersonalExitKeepsOtherParticipant(GameTestHelper h) {
        var p = player(h, "ExitControlA"); var other = player(h, "ExitControlB");
        check(h, CrucibleRuntime.join(p) && CrucibleRuntime.join(other), "Actual independent Crucible members join");
        var otherTicket = ActivityExit.capture(other).orElseThrow();
        check(h, ActivityExit.request(p), "Shared command opens genuine clickable confirmation");
        var cancelled = nonce(p, "취소");
        check(h, ActivityExit.cancel(p, cancelled) && CrucibleRuntime.participating(p), "Cancel preserves actual activity member");
        check(h, !ActivityExit.confirm(p, cancelled), "Cancelled action cannot later confirm");
        check(h, ActivityExit.request(p), "Fresh confirmation opens"); var confirmed = nonce(p, "확인");
        check(h, ActivityExit.confirm(p, confirmed) && !CrucibleRuntime.participating(p), "Confirmation invokes real personal departure");
        check(h, ActivityExit.current(other, otherTicket) && CrucibleRuntime.participating(other), "Other participant and membership survive");
        check(h, !ActivityExit.confirm(p, confirmed), "Confirmation is single use");
        check(h, !p.isSpectator(), "Prior game mode restored by existing teardown"); h.succeed();
    }
    /** Construct the actual controller in its owned temporary world, without fabricating map-readiness claims. */
    private static final class Strike implements AutoCloseable {
        final kim.biryeong.destiny.strike.devils.DevilsInstances instances;
        final kim.biryeong.destiny.strike.devils.DevilsInstances.Instance instance;
        final kim.biryeong.destiny.strike.devils.DevilsSession session;
        final java.util.List<ServerPlayer> members;
        final java.util.Map<java.util.UUID, kim.biryeong.destiny.strike.devils.DevilsSession> sessions;
        @SuppressWarnings("unchecked") Strike(GameTestHelper h, java.util.List<ServerPlayer> members) {
            try {
                this.members = members;
                var server = h.getLevel().getServer();
                instances = new kim.biryeong.destiny.strike.devils.DevilsInstances(server, 1);
                instance = instances.prepare(members.stream().map(ServerPlayer::getUUID).toList()).orElseThrow();
                var ctor = kim.biryeong.destiny.strike.devils.DevilsSession.class.getDeclaredConstructor(
                        net.minecraft.server.MinecraftServer.class, kim.biryeong.destiny.activity.strike.StrikeInstances.class,
                        kim.biryeong.destiny.activity.strike.StrikeInstances.Instance.class, java.util.List.class);
                ctor.setAccessible(true); session = ctor.newInstance(server, instances, instance, members);
                var hostField = kim.biryeong.destiny.strike.devils.DevilsLair.class.getDeclaredField("HOST");
                hostField.setAccessible(true); var host = hostField.get(null);
                var field = host.getClass().getDeclaredField("runs");
                field.setAccessible(true); sessions = (java.util.Map<java.util.UUID, kim.biryeong.destiny.strike.devils.DevilsSession>) field.get(host);
                sessions.put(instance.id(), session); TestCleanup.register(h, this::close);
            } catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
        }
        void state(String name) {
            try {
                var field = session.getClass().getDeclaredField("state"); field.setAccessible(true);
                Object value = java.util.Arrays.stream(field.getType().getEnumConstants()).filter(v -> v.toString().equals(name)).findFirst().orElseThrow();
                field.set(session, value);
            } catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
        }
        Object call(String name, Class<?>[] types, Object... args) {
            try { var method = session.getClass().getDeclaredMethod(name, types); method.setAccessible(true); return method.invoke(session, args); }
            catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
        }
        void returnSaved(ServerPlayer p) {
            try {
                var method = kim.biryeong.destiny.strike.devils.DevilsLair.class.getDeclaredMethod("saveReturn", ServerPlayer.class);
                method.setAccessible(true); method.invoke(null, p);
            } catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
        }
        void present(ServerPlayer p) {
            try {
                var field = session.getClass().getDeclaredField("recovery"); field.setAccessible(true);
                var recovery = (kim.biryeong.destiny.strike.devils.DevilsRecovery) field.get(session);
                recovery.presence(p.getUUID(), true, true);
            } catch (ReflectiveOperationException e) { throw new IllegalStateException(e); }
        }
        @Override public void close() {
            for (var p : members) if (!p.hasDisconnected()) ActivityExit.capture(p).ifPresent(ticket -> ActivityExit.leave(p, ticket));
            sessions.remove(instance.id(), session);
            call("stop", new Class<?>[]{String.class}, "fixture cleanup");
            call("drain", new Class<?>[]{});
            instances.close(instance);
        }
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=60)
    public void preparingAndAdmittingStrikeDepartureRetainsOtherMembersAndSession(GameTestHelper h) {
        var first = player(h, "ExitPrepA"); var second = player(h, "ExitPrepB"); var third = player(h, "ExitPrepC");
        try (var fixture = new Strike(h, java.util.List.of(first, second, third))) {
            check(h, ActivityExit.leave(first, ActivityExit.capture(first).orElseThrow()), "Preparing member exits through shared service");
            check(h, fixture.session.status().startsWith("PREPARING") && fixture.session.member(second.getUUID())
                    && fixture.session.member(third.getUUID()), "Preparing leave does not stop retained team");
            fixture.state("ADMITTING");
            check(h, ActivityExit.leave(second, ActivityExit.capture(second).orElseThrow()), "Admitting member exits through shared service");
            check(h, fixture.session.status().startsWith("ADMITTING") && fixture.session.member(third.getUUID()),
                    "Admitting leave keeps last participant and controller");
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR, environment=ENV, maxTicks=60)
    public void downedStrikeCommandExitCancelsOwnedSceneReturnsPlayerAndKeepsTeammate(GameTestHelper h) {
        var p = player(h, "ExitDownA"); var other = player(h, "ExitDownB"); var returnLevel = p.level();
        try (var fixture = new Strike(h, java.util.List.of(p, other))) {
            fixture.state("RUNNING"); fixture.returnSaved(p);
            var at = new Vec3(2.5, 180, 2.5);
            check(h, p.teleportTo(fixture.instance.level(), at.x, at.y, at.z, java.util.Set.of(), 0, 0, true), "Fixture enters owned strike world");
            fixture.present(p); fixture.present(other);
            var option = (kim.biryeong.destiny.down.GuardianDown.Options) fixture.call("downed", new Class<?>[]{ServerPlayer.class}, p);
            check(h, option != null && kim.biryeong.destiny.down.GuardianDown.fallOwned(p, option, p.position()),
                    "Actual strike down ownership and GuardianDown scene acquired");
            check(h, kim.biryeong.destiny.down.GuardianDown.active(p), "Player is down before requesting exit");
            check(h, ActivityExit.request(p), "Down/camera state permits command confirmation"); var token = nonce(p, "확인");
            check(h, ActivityExit.confirm(p, token), "Command executes existing personal teardown while down");
            check(h, !kim.biryeong.destiny.down.GuardianDown.active(p) && p.getCamera() == p && p.level() == returnLevel,
                    "Owned down scene removed and saved return location restored");
            check(h, fixture.session.running() && fixture.session.member(other.getUUID()) && !fixture.session.member(p.getUUID()),
                    "Other participant's running session survives");
        }
        h.succeed();
    }

}
