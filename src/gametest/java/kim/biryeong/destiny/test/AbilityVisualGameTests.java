package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.ability.hunter.HunterAbilityVisuals;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;

import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Supplier;

/** Resource-pack model selection and the unarmed combination-blow path. */
public final class AbilityVisualGameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final List<VisualCase> VISUALS = List.of(
            new VisualCase("arc_flashbang", () -> HunterAbilityVisuals.grenade(Element.ARC)),
            new VisualCase("solar_incendiary", () -> HunterAbilityVisuals.grenade(Element.SOLAR)),
            new VisualCase("void_vortex", () -> HunterAbilityVisuals.grenade(Element.VOID)),
            new VisualCase("solar_knife", () -> HunterAbilityVisuals.melee(Element.SOLAR)),
            new VisualCase("void_smoke_bomb", () -> HunterAbilityVisuals.melee(Element.VOID)));

    private record VisualCase(String name, Supplier<ItemStack> factory) {
        Identifier model() {
            return Identifier.fromNamespaceAndPath("destiny", "hunter/" + name);
        }
    }

    private static void check(GameTestHelper h, boolean condition, String message) {
        h.assertTrue(condition, Component.literal(message));
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void modelForwardAxisFollowsFlightIncludingReverseAndZero(GameTestHelper h) {
        for (Vec3 velocity : List.of(new Vec3(1, 0, 0), new Vec3(0, 0, 1),
                new Vec3(0, 1, 0), new Vec3(-1, -0.3, -2))) {
            // Vanilla ItemDisplayRenderer first rotates the authored -Z by Y=PI to +Z.
            var forward = SimProjectile.flightRotation(velocity).transform(new org.joml.Vector3f(0, 0, 1));
            Vec3 actual = new Vec3(forward.x, forward.y, forward.z);
            check(h, actual.distanceTo(velocity.normalize()) < 1.0e-5, "Authored -Z must align with velocity");
        }
        check(h, SimProjectile.flightRotation(Vec3.ZERO).equals(new org.joml.Quaternionf().rotationY((float) Math.PI)),
                "Zero velocity must keep a finite renderer-corrected orientation");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void hunterProjectileModelsAreCustomAndDistinct(GameTestHelper h) {
        Set<Identifier> models = new HashSet<>();
        for (VisualCase visual : VISUALS) {
            ItemStack stack = visual.factory().get();
            Identifier model = stack.get(DataComponents.ITEM_MODEL);
            check(h, stack.is(Items.PAPER) && stack.getCount() == 1,
                    visual.name() + " should use one PAPER carrier");
            check(h, visual.model().equals(model),
                    visual.name() + " should select " + visual.model() + ", got " + model);
            check(h, models.add(model), "Each hunter projectile must have a distinct item model");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void hunterVisualStacksAreIndependent(GameTestHelper h) {
        for (VisualCase visual : VISUALS) {
            ItemStack first = visual.factory().get();
            ItemStack second = visual.factory().get();
            check(h, first != second, visual.name() + " must return a fresh stack");
            first.setCount(7);
            first.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "test/mutated"));
            check(h, second.getCount() == 1 && visual.model().equals(second.get(DataComponents.ITEM_MODEL)),
                    "Mutating one " + visual.name() + " stack must not change another");
            ItemStack third = visual.factory().get();
            check(h, third != first && third != second && third.getCount() == 1
                            && visual.model().equals(third.get(DataComponents.ITEM_MODEL)),
                    "Mutating a " + visual.name() + " stack must not change future factory results");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20)
    public void arcCombinationBlowStaysUnarmedWithoutProjectile(GameTestHelper h) {
        check(h, HunterAbilityVisuals.melee(Element.ARC).isEmpty(), "Arc melee has no item visual");
        ServerPlayer player = TestPlayers.hunter(h, Element.ARC, new Vec3(2.5, 1, 6.5), -90, 0);
        boolean scheduled = false;
        try {
            player.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
            player.setItemInHand(InteractionHand.OFF_HAND, ItemStack.EMPTY);
            check(h, SimProjectile.activeCount(player) == 0, "Fixture should start without projectiles");
            check(h, AbilityService.use(player, AbilitySlot.MELEE) == AbilityService.Result.OK,
                    "Combination blow should activate");
            check(h, Tasks.count(player) > 0, "Combination blow should schedule its melee strike");
            assertUnarmed(h, player);
            h.runAfterDelay(6, () -> {
                try {
                    check(h, Tasks.count(player) == 0, "Combination blow strike should have completed");
                    assertUnarmed(h, player);
                    h.succeed();
                } finally {
                    TestPlayers.remove(player);
                }
            });
            scheduled = true;
        } finally {
            if (!scheduled) {
                TestPlayers.remove(player);
            }
        }
    }

    private static void assertUnarmed(GameTestHelper h, ServerPlayer player) {
        check(h, SimProjectile.activeCount(player) == 0, "Combination blow must not launch a projectile");
        check(h, player.getMainHandItem().isEmpty() && player.getOffhandItem().isEmpty(),
                "Combination blow must leave an unarmed hunter's hands empty");
    }
}
