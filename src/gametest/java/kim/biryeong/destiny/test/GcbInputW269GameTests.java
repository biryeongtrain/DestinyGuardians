package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.compat.gcb.GcbInputBridge;
import kim.biryeong.destiny.fx.SuperAttackTiming;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.gcbserver.events.PlayerKeyStateChangedEvent;
import kim.biryeong.gcbserver.player.GCBPlayer;
import kim.biryeong.gcbserver.player.Key;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.server.network.CommonListenerCookie;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.Map;

/** Production router + registered GCB callbacks; no native client/key or framebuffer claim. */
public final class GcbInputW269GameTests {
    private static final String FLOOR = "destiny-test:w78_floor";
    private static final Input SHIFT = new Input(false, false, false, false, false, true, false);
    private static final Input JUMP = new Input(false, false, false, false, true, false, false);

    private static void check(GameTestHelper h, boolean ok, String why) {
        h.assertTrue(ok, Component.literal(why));
    }

    private static ServerPlayer hunter(GameTestHelper h, boolean gcb) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(5, 4, 5), -90, 90);
        TestCleanup.register(h, () -> {
            try {
                p.setShiftKeyDown(false);
                TestPlayers.remove(p);
            } finally {
                // Guardian runtime cleanup deliberately does not end the connection capability.
                ClientControls.forget(p);
            }
        });
        p.setOnGround(true);
        if (gcb) handshake(p);
        check(h, ClientControls.gcb(p) == gcb, "Fixture uses actual GCB handshake detection");
        return p;
    }

    private static void handshake(ServerPlayer p) {
        var client = (GCBPlayer) p;
        client.gcb$markHasMod();
        client.gcb$setModVersion("w269-test");
    }

    private static void key(ServerPlayer p, boolean pushed, Key key) {
        // Use the production listener installed at mod initialization, never register another bridge.
        PlayerKeyStateChangedEvent.EVENT.invoker().onKeyStateChanged(p, pushed, key);
    }

    private static void offhand(ServerPlayer p, boolean shift) {
        p.setShiftKeyDown(shift);
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
    }

    private static void doubleShift(ServerPlayer p) {
        InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
        InputRouter.onPlayerInput(p, SHIFT, Input.EMPTY);
        InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
    }

    private static void noFallbacks(GameTestHelper h, ServerPlayer p) {
        var data = Guardians.data(p);
        data.setSuperEnergy(1f);
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.DIAMOND, 2));
        offhand(p, true);
        check(h, !AbilityService.inSuper(p) && data.superEnergy() == 1f
                        && data.cooldown(AbilitySlot.GRENADE) == 0,
                "GCB Shift+F neither casts super nor falls back to grenade");
        check(h, p.getMainHandItem().is(Items.STICK) && p.getOffhandItem().is(Items.DIAMOND)
                        && p.getOffhandItem().getCount() == 2,
                "Blocked Shift+F is still consumed before vanilla swaps hands");
        doubleShift(p);
        check(h, data.cooldown(AbilitySlot.CLASS_ABILITY) == 0,
                "GCB double Shift does not cast the vanilla class fallback");
        p.setShiftKeyDown(true);
        InputRouter.onPunch(p);
        check(h, data.cooldown(AbilitySlot.MELEE) == 0
                        && Guardians.runtime(p).lastActionTick.isEmpty(),
                "GCB Shift+leftclick and the other blocked chords dispatch no ability");
        p.setShiftKeyDown(false);
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void dedicatedKeysMapAndDispatchThroughRegisteredCallback(GameTestHelper h) {
        var actions = Map.of(Key.KEY_Z, GuardianAction.GRENADE, Key.KEY_C, GuardianAction.MELEE,
                Key.KEY_V, GuardianAction.CLASS_ABILITY, Key.KEY_ATTACK, GuardianAction.PRIMARY);
        for (Key key : Key.values()) {
            check(h, GcbInputBridge.actionFor(key) == actions.get(key),
                    "Only Z/C/V and attack map to actions; X no longer casts super: " + key);
        }
        check(h, Key.fromTranslationKey("key.keyboard.f").isEmpty(),
                "GCB has no F enum entry; offhand packet carries super");
        var slots = Map.of(Key.KEY_Z, AbilitySlot.GRENADE, Key.KEY_C, AbilitySlot.MELEE,
                Key.KEY_V, AbilitySlot.CLASS_ABILITY);
        for (var entry : slots.entrySet()) {
            var p = hunter(h, true);
            var data = Guardians.data(p);
            data.setSuperEnergy(1f);
            key(p, false, entry.getKey());
            key(p, true, Key.KEY_X);
            key(p, true, Key.KEY_ATTACK);
            check(h, Guardians.runtime(p).lastActionTick.isEmpty() && !AbilityService.inSuper(p)
                            && data.superEnergy() == 1f && data.cooldown(entry.getValue()) == 0,
                    "Release, obsolete X, and attack outside super do not dispatch");
            key(p, true, entry.getKey());
            check(h, data.cooldown(entry.getValue()) > 0
                            && Guardians.runtime(p).lastActionTick.keySet().equals(java.util.Set.of(actions.get(entry.getKey()))),
                    "Registered GCB callback dispatches exactly the mapped ability: " + entry.getKey());
            for (AbilitySlot slot : slots.values()) {
                if (slot != entry.getValue()) check(h, data.cooldown(slot) == 0,
                        "Mapped callback does not spend a different ability: " + slot);
            }
            check(h, !AbilityService.inSuper(p) && data.superEnergy() == 1f,
                    "Z/C/V never spend super energy");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void gcbBlocksLegacyChordsWhileVanillaControlsStillWork(GameTestHelper h) {
        noFallbacks(h, hunter(h, true));
        var grenade = hunter(h, false);
        // A debug presentation flag is not a handshake and cannot disable vanilla controls.
        Guardians.runtime(grenade).gcbClient = true;
        check(h, !ClientControls.gcb(grenade), "Debug camera flag alone does not identify a GCB client");
        offhand(grenade, false);
        check(h, Guardians.data(grenade).cooldown(AbilitySlot.GRENADE) > 0
                        && !AbilityService.inSuper(grenade), "Vanilla plain F still casts grenade");
        var superPlayer = hunter(h, false);
        Guardians.data(superPlayer).setSuperEnergy(1f);
        offhand(superPlayer, true);
        check(h, AbilityService.inSuper(superPlayer), "Vanilla Shift+F still casts super");
        var dodge = hunter(h, false);
        doubleShift(dodge);
        check(h, Guardians.data(dodge).cooldown(AbilitySlot.CLASS_ABILITY) > 0,
                "Vanilla double Shift still casts class ability");
        var melee = hunter(h, false);
        melee.setShiftKeyDown(true);
        InputRouter.onPunch(melee);
        check(h, Guardians.data(melee).cooldown(AbilitySlot.MELEE) > 0,
                "Vanilla Shift+leftclick still casts melee");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void handshakeAndRetainedSessionSurviveGuardianRuntimeForget(GameTestHelper h) {
        var p = hunter(h, false);
        InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
        handshake(p);
        check(h, ClientControls.gcb(p), "Live handshake upgrades an existing vanilla connection");
        InputRouter.onPlayerInput(p, SHIFT, Input.EMPTY);
        InputRouter.onPlayerInput(p, Input.EMPTY, SHIFT);
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) == 0,
                "Handshake does not complete a pending vanilla double-Shift chord");
        var old = Guardians.runtime(p);
        Guardians.forget(p);
        check(h, ClientControls.gcb(p) && Guardians.runtime(p) != old,
                "GCB detection survives Guardian runtime replacement");
        noFallbacks(h, p);
        key(p, true, Key.KEY_V);
        check(h, Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY) > 0,
                "Dedicated callback still casts after runtime replacement");
        // A respawn-style object has the same connection identity but no mixin handshake yet.
        // This capability-only probe is never placed in the world and owns no channel or abilities.
        var cookie = CommonListenerCookie.createInitial(p.getGameProfile(), false);
        var replacement = new ServerPlayer(p.level().getServer(), p.level(), p.getGameProfile(), cookie.clientInformation());
        check(h, !((GCBPlayer) replacement).gcb$hasMod(), "Replacement starts without fresh handshake state");
        Guardians.forget(p);
        check(h, ClientControls.gcb(replacement), "Connection capability remains when the replacement has no handshake");
        ClientControls.forget(p);
        check(h, !ClientControls.gcb(replacement), "Disconnect cleanup removes the retained connection capability");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void plainFUsesOffhandAndDeduplicatesSuccessfulDispatchOnly(GameTestHelper h) {
        var p = hunter(h, true);
        var data = Guardians.data(p);
        p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.STICK));
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.DIAMOND, 2));
        data.setSuperEnergy(0f);
        offhand(p, false);
        check(h, !AbilityService.inSuper(p) && Guardians.runtime(p).lastActionTick.isEmpty(),
                "Unfunded F is consumed without recording a successful action");
        data.setSuperEnergy(1f);
        offhand(p, false);
        var session = Guardians.runtime(p).superSession;
        check(h, session != null && data.superEnergy() == 0f && data.cooldown(AbilitySlot.GRENADE) == 0,
                "Funded F in the same tick casts super, never the vanilla grenade");
        offhand(p, false);
        check(h, Guardians.runtime(p).superSession == session && data.superEnergy() == 0f,
                "Duplicate F preserves the one accepted super session");
        check(h, p.getMainHandItem().is(Items.STICK) && p.getOffhandItem().is(Items.DIAMOND)
                        && p.getOffhandItem().getCount() == 2, "F never swaps the actual hands");
        // Remove the ordinary BUSY/energy guards so the assertion specifically exercises router dedup.
        AbilityService.endSuper(p);
        data.setSuperEnergy(1f);
        offhand(p, false);
        check(h, !AbilityService.inSuper(p) && data.superEnergy() == 1f,
                "Successful same-tick F stays deduplicated even after session end/refill");
        h.runAfterDelay(1, () -> {
            offhand(p, false);
            check(h, AbilityService.inSuper(p) && data.superEnergy() == 0f,
                    "A later server tick can accept another funded F");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void gcbKeepsAirJumpAndPrimaryCombatWithBothDispatchOrders(GameTestHelper h) {
        for (boolean callbackFirst : new boolean[] {true, false}) {
            var p = hunter(h, true);
            p.setOnGround(false);
            p.setDeltaMovement(0, -0.2, 0);
            InputRouter.onPlayerInput(p, Input.EMPTY, JUMP);
            check(h, Guardians.runtime(p).airJumpsUsed == 1 && p.getDeltaMovement().y > 0,
                    "GCB leaves real airborne jump input enabled");
            p.setOnGround(true);
            Guardians.data(p).setSuperEnergy(1f);
            offhand(p, false);
            var session = Guardians.runtime(p).superSession;
            check(h, session != null, "Real offhand input starts the primary-combat fixture super");
            for (int tick = 0; tick < SuperAttackTiming.SOLAR_DEPLOY; tick++) AbilityService.tickPlayer(p);
            int before = session.ammunition().orElseThrow();
            // Shift suppresses fallback melee, but must not suppress primary during an active super.
            p.setShiftKeyDown(true);
            if (callbackFirst) {
                key(p, true, Key.KEY_ATTACK);
                InputRouter.onPunch(p);
            } else {
                InputRouter.onPunch(p);
                key(p, true, Key.KEY_ATTACK);
            }
            check(h, session.ammunition().orElseThrow() == before - 1
                            && Guardians.runtime(p).lastActionTick.containsKey(GuardianAction.PRIMARY)
                            && Guardians.data(p).cooldown(AbilitySlot.MELEE) == 0,
                    "Both input orders spend one primary shot and no melee: callbackFirst=" + callbackFirst);
            key(p, false, Key.KEY_ATTACK);
            check(h, session.ammunition().orElseThrow() == before - 1, "Attack release spends no extra shot");
        }
        h.succeed();
    }
}
