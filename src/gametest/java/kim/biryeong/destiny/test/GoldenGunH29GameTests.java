package kim.biryeong.destiny.test;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.hunter.HunterSuper;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.minigamelib.displayhud.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;
import org.joml.Vector3f;

public final class GoldenGunH29GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static ItemDisplayHud hud(GameTestHelper h, ServerPlayer p) {
        var value = DisplayHud.getHud(p, HunterSuper.HAND_HUD_ID);
        check(h, value instanceof ItemDisplayHud, "Personal Solar aim HUD exists");
        var hud = (ItemDisplayHud) value;
        check(h, hud.getItemTransform() == ItemDisplayContext.FIRST_PERSON_RIGHT_HAND,
                "Personal view uses aim context, not GUI inventory rotation");
        check(h, DestinyGuardians.id("golden_gun_h29").equals(hud.getItem().get(DataComponents.ITEM_MODEL)),
                "Real transmitted HUD selects source mesh");
        check(h, !SuperCamera.active(p) && p.getCamera() == p, "Solar stays self-camera");
        return hud;
    }
    @GameTest(structure = "destiny-test:floor", maxTicks = 1200, environment = "destiny-test:w90_isolated")
    public void solarAimRecoilAndCleanupPreserveHandsAndSelfCamera(GameTestHelper h) {
        h.startSequence().thenWaitUntil(() -> check(h,
                BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(), "Hunter limb loaded"))
                .thenExecute(() -> {
                    var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5,1,6.5), 0,0);
                    TestCleanup.register(h, () -> TestPlayers.remove(p));
                    p.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND, 2));
                    Guardians.data(p).setSuperEnergy(1);
                    check(h, AbilityService.use(p, AbilitySlot.SUPER) == AbilityService.Result.OK, "Activate Solar");
                    hud(h, p);
                    step(h, p, 1);
                });
    }
    private static void step(GameTestHelper h, ServerPlayer p, int tick) {
        h.runAfterDelay(1, () -> {
            AbilityService.tickPlayer(p);
            var value = hud(h, p);
            check(h, p.getMainHandItem().is(Items.DIAMOND) && p.getMainHandItem().getCount() == 2,
                    "Prop cannot mutate real main hand");
            if (tick == 12) check(h, AbilityService.perform(p, GuardianAction.PRIMARY), "Fire via primary route");
            if (tick == 15) {
                var z = new Vector3f(0,0,1).rotate(value.getLeftRotation());
                check(h, z.distance(new Vector3f(0,0,1)) < .0001,
                        "Actual recoil quaternion preserves screen normal instead of pitching X");
                check(h, Math.abs(value.getLeftRotation().z()) > .01, "Actual recoil has nonzero screen roll");
            }
            if (tick < 24) step(h,p,tick+1);
            else {
                check(h, value.getScale().x == 420, "Recovered ready size");
                check(h, value.getLeftRotation().angle() < .0001, "Recovered neutral roll");
                AbilityService.endSuper(p);
                check(h, DisplayHud.getHud(p,HunterSuper.HAND_HUD_ID) == null, "Hand HUD removed");
                check(h, !PlayerAnimations.isPlaying(p) && !SuperCamera.active(p), "Limb/camera cleaned");
                h.succeed();
            }
        });
    }
}
