package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.MeleeSuperMovement;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;

/** W276: melee supers grant +30% speed while active and step forward on light attacks. */
public final class MeleeSuperW276GameTests {
    private static void check(GameTestHelper h, boolean v, String m) { h.assertTrue(v, Component.literal(m)); }
    private static final class Idle implements SuperSession {
        int primaries;
        @Override public boolean tick() { return true; }
        @Override public void primary() { primaries++; }
        @Override public void end() { }
        @Override public float remaining() { return 1; }
    }

    @GameTest(structure = "destiny-test:floor", maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void meleeSuperSpeedAndStep(GameTestHelper h) {
        var p = TestPlayers.hunter(h, Element.ARC, new Vec3(2, 1, 2), 0, 0); // yaw 0 faces +Z
        TestCleanup.register(h, () -> { AbilityService.endSuper(p); TestPlayers.remove(p); });
        var data = Guardians.data(p);
        data.setLoadout(GuardianClass.HUNTER, kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.ARC));
        check(h, AbilityService.equipped(p, AbilitySlot.SUPER).map(a -> MeleeSuperMovement.isMeleeSuper(a.id())).orElse(false),
                "Arc preset equips Arc Staff, a melee super");
        double base = p.getAttributeValue(Attributes.MOVEMENT_SPEED);
        var session = new Idle();
        AbilityService.startSuper(p, session);
        h.runAfterDelay(2, () -> {
            AbilityService.tickPlayer(p); // mock players are not in the PlayerList ticked by AbilityService
            double boosted = p.getAttributeValue(Attributes.MOVEMENT_SPEED);
            check(h, Math.abs(boosted - base * 1.3) < 1e-6, "Speed +30% during melee super: base=" + base + " now=" + boosted);
            double z = p.getZ();
            check(h, AbilityService.perform(p, GuardianAction.PRIMARY) && session.primaries == 1, "Primary reaches the session");
            check(h, Math.abs(p.getZ() - z) < 1e-6, "A session without an accepted contact cannot lunge: dz=" + (p.getZ() - z));
            double z2 = p.getZ();
            AbilityService.perform(p, GuardianAction.PRIMARY);
            check(h, Math.abs(p.getZ() - z2) < 1e-6, "Held clicks are rate-limited");
            AbilityService.endSuper(p);
            check(h, Math.abs(p.getAttributeValue(Attributes.MOVEMENT_SPEED) - base) < 1e-6, "Speed restored after super");
            h.succeed();
        });
    }
}
