package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.input.InputRouter;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.Vec3;

/** W51 server integration with TestPlayers; does not prove native client/network delivery. */
public final class SwordW51GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String[] SWORDS = {
            "abide_the_return", "goldtusk", "crown_splitter", "falling_guillotine", "temptation_s_hook"
    };
    private static final float TARGET_HEALTH = 1000;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, double z, boolean guardian) {
        var at = new Vec3(2.5, 1, z);
        var p = guardian ? TestPlayers.hunter(h, Element.SOLAR, at, -90, 0)
                : TestPlayers.create(h, at, -90, 0);
        TestCleanup.register(h, () -> {
            AbilityService.cleanup(p);
            WeaponRuntime.cleanup(p);
            AmmoEconomy.cleanup(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ItemStack sword(String id, int rounds, int energy, int delay) {
        var entry = WeaponCatalog.find(id).orElseThrow();
        var stack = WeaponModels.withGrip(WeaponItems.create(entry), WeaponModels.Grip.NATIVE).orElseThrow();
        WeaponItems.save(stack, new WeaponMagazine(WeaponProfile.forEntry(entry), rounds, 0));
        SwordItems.save(stack, energy, delay);
        return stack;
    }

    private static ItemStack equip(ServerPlayer p, String id, int rounds, int energy, int delay) {
        var stack = sword(id, rounds, energy, delay);
        p.setItemInHand(InteractionHand.MAIN_HAND, stack);
        WeaponRuntime.tickPlayer(p);
        return stack;
    }

    private static WeaponMagazine ammo(ItemStack stack) {
        return WeaponItems.magazine(stack, WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));
    }

    private static Husk target(GameTestHelper h, double x, double z) {
        var e = h.spawn(EntityTypes.HUSK, new Vec3(x, 1, z));
        e.setNoAi(true);
        e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(TARGET_HEALTH);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);
        e.setHealth(TARGET_HEALTH);
        TestCleanup.register(h, e::discard);
        return e;
    }

    private static void use(GameTestHelper h, ServerPlayer p) {
        p.gameMode.useItem(p, h.getLevel(), p.getMainHandItem(), InteractionHand.MAIN_HAND);
    }

    private static int contact(ItemStack stack, boolean heavy) {
        return SwordTiming.contactTicks(SwordProfile.of(WeaponItems.entry(stack).orElseThrow()).shape(), heavy, 1);
    }

    private static void windup(GameTestHelper h, ServerPlayer p, Vec3 position, Husk... enemies) {
        check(h, p.position().distanceToSqr(position) < 1e-12, "Wind-up cannot move the sword owner");
        for (var enemy : enemies) check(h, enemy.getHealth() == TARGET_HEALTH,
                "Accepted attack cannot change actual HP before contact");
    }

    private static float hurt(GameTestHelper h, ServerPlayer p, DamageSource source) {
        p.damageCooldownTime = 0;
        p.setHealth(p.getMaxHealth());
        float before = p.getHealth();
        p.hurtServer(h.getLevel(), source, 8);
        return before - p.getHealth();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void fiveFramesCreateFullAndLegacyPoolProjectionAndQArePure(GameTestHelper h) {
        var p = player(h, 6.5, false);
        for (String id : SWORDS) {
            var entry = WeaponCatalog.find(id).orElseThrow();
            var profile = WeaponProfile.forEntry(entry);
            var stack = WeaponItems.create(entry);
            check(h, SwordItems.isSword(stack) && profile.reserve() == 0 && !profile.infiniteReserve(),
                    id + ": sword has one finite loaded pool");
            check(h, ammo(stack).rounds() == profile.magazine() && ammo(stack).total() == profile.magazine()
                            && SwordItems.energy(stack) == SwordCycle.CAPACITY && SwordItems.delay(stack) == 0,
                    id + ": creation starts with full real ammo and energy");
            SwordItems.save(stack, 27150, 13);
            var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
            tag.putInt(WeaponItems.ROUNDS, 2);
            tag.putInt(WeaponItems.RESERVE, 3);
            tag.putLong(WeaponItems.OVERFLOW, 4);
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            var before = stack.copy();
            for (int i = 0; i < 3; i++) {
                var projected = ammo(stack);
                check(h, projected.rounds() == 9 && projected.reserve() == 0 && projected.total() == 9,
                        id + ": legacy rounds/reserve/overflow fold exactly once per pure read");
            }
            p.setItemInHand(InteractionHand.MAIN_HAND, stack);
            check(h, !WeaponRuntime.reload(p), id + ": reload is denied");
            for (var action : new ServerboundPlayerActionPacket.Action[] {
                    ServerboundPlayerActionPacket.Action.DROP_ITEM,
                    ServerboundPlayerActionPacket.Action.DROP_ALL_ITEMS }) {
                p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(action, BlockPos.ZERO, Direction.UP));
            }
            check(h, p.getMainHandItem() == stack && !WeaponRuntime.reloading(p)
                            && WeaponRuntime.ammunition(p).orElseThrow().reloadRemaining() == 0
                            && ItemStack.matches(stack, before),
                    id + ": real Q handlers keep the item, counts, energy and delay without a reload timer");
            tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
            tag.putLong(WeaponItems.OVERFLOW, profile.magazine() + 7L);
            stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
            before = stack.copy();
            var excess = ammo(stack);
            check(h, excess.rounds() == profile.magazine() && excess.reserve() == 0
                            && excess.total() == profile.magazine() + 12L && ItemStack.matches(stack, before),
                    id + ": over-capacity legacy ammo is conserved without a read-time save");
            var ops = h.getLevel().registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE);
            var decoded = ItemStack.CODEC.parse(ops, ItemStack.CODEC.encodeStart(ops, stack).getOrThrow()).getOrThrow();
            var grip = WeaponModels.withGrip(stack, WeaponModels.Grip.NATIVE).orElseThrow();
            check(h, SwordItems.energy(decoded) == 27150 && SwordItems.delay(decoded) == 13
                            && ammo(decoded).total() == excess.total() && SwordItems.energy(grip) == 27150
                            && SwordItems.delay(grip) == 13 && ammo(grip).total() == excess.total(),
                    id + ": item codec and grip preserve owned energy, delay and conserved ammo");
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 55, environment = "destiny-test:w90_isolated")
    public void routedLightHitsOnceAndMissStillCostsOneAmmo(GameTestHelper h) {
        var p = player(h, 6.5, false);
        var stack = equip(p, SWORDS[0], 12, SwordCycle.CAPACITY, 0);
        var enemy = target(h, 4.5, 6.5);
        var start = p.position();
        InputRouter.onPunch(p);
        windup(h, p, start, enemy);
        check(h, ammo(stack).rounds() == 11, "Routed powered light pays one ammo on acceptance");
        InputRouter.onPunch(p);
        WeaponRuntime.onPunch(p);
        check(h, enemy.getHealth() == TARGET_HEALTH && ammo(stack).rounds() == 11,
                "Duplicate punch paths cannot repeat payment or cause early damage");
        float[] after = new float[1];
        h.runAfterDelay(contact(stack, false) - 1, () -> windup(h, p, start, enemy));
        h.runAfterDelay(contact(stack, false) + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            after[0] = enemy.getHealth();
            check(h, after[0] < TARGET_HEALTH && ammo(stack).rounds() == 11,
                    "Routed light changes actual HP only after contact for its single payment");
        });
        int wait = WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()).intervalTicks() + 1;
        h.runAfterDelay(wait, () -> {
            check(h, enemy.getHealth() == after[0], "Contact is applied once across later real ticks");
            enemy.discard();
            InputRouter.onPunch(p);
            check(h, ammo(stack).rounds() == 10 && ammo(stack).reserve() == 0,
                    "An accepted light miss also pays one real ammo, with no reserve");
        });
        h.runAfterDelay(wait + SwordTiming.contactTicks(SwordProfile.Shape.UPPERCUT, false, 2) + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, ammo(stack).rounds() == 10 && ammo(stack).reserve() == 0,
                    "Delayed miss contact cannot add another payment or reserve");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void emptySwordLightIsWeakerAndCannotMintAmmo(GameTestHelper h) {
        var powered = player(h, 2.5, false);
        var empty = player(h, 9.5, false);
        var paid = equip(powered, SWORDS[0], 10, SwordCycle.CAPACITY, 0);
        var dry = equip(empty, SWORDS[0], 0, SwordCycle.CAPACITY, 0);
        var a = target(h, 4.5, 2.5);
        var b = target(h, 4.5, 9.5);
        var poweredStart = powered.position();
        var emptyStart = empty.position();
        InputRouter.onPunch(powered);
        InputRouter.onPunch(empty);
        windup(h, powered, poweredStart, a);
        windup(h, empty, emptyStart, b);
        check(h, ammo(paid).rounds() == 9 && ammo(dry).total() == 0,
                "Powered acceptance spends one ammo while empty acceptance cannot mint ammo");
        h.runAfterDelay(contact(paid, false) - 1, () -> {
            windup(h, powered, poweredStart, a);
            windup(h, empty, emptyStart, b);
        });
        h.runAfterDelay(contact(paid, false) + 1, () -> {
            WeaponRuntime.tickPlayer(powered);
            WeaponRuntime.tickPlayer(empty);
            float paidDamage = TARGET_HEALTH - a.getHealth();
            float dryDamage = TARGET_HEALTH - b.getHealth();
            check(h, dryDamage > 0 && paidDamage > dryDamage && ammo(paid).rounds() == 9,
                    "Empty light really hurts an enemy but is weaker than the same powered light");
            check(h, ammo(dry).total() == 0 && !WeaponRuntime.reloading(empty),
                    "Empty melee cannot grant ammo or start an automatic reload");
            InputRouter.onPunch(empty);
            check(h, b.getHealth() == TARGET_HEALTH - dryDamage && ammo(dry).total() == 0,
                    "Empty duplicate input is bounded too");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 340, environment = "destiny-test:w90_isolated")
    public void fiveNativeHeavyFramesPayOnceWhileHeldAndZeroEnergyIsWeaker(GameTestHelper h) {
        var charged=player(h,2.5,false);var depleted=player(h,9.5,false);
        // Register every task up front. Adding nested tasks during the native GameTestInfo
        // Object2LongOpenHashMap iteration can rehash/revisit a callback and recreate its ammo.
        for(int i=0;i<SWORDS.length;i++) {
            String id=SWORDS[i];boolean last=i==SWORDS.length-1;int start=1+i*64;
            ItemStack[] stacks=new ItemStack[2];Husk[] targets=new Husk[2];int[] paid=new int[2];int[] starts={0};
            Vec3[] positions=new Vec3[2];
            int contact=SwordTiming.contactTicks(SwordProfile.of(WeaponCatalog.find(id).orElseThrow()).shape(),true,0);
            h.runAfterDelay(start,()->{
                check(h,++starts[0]==1,"Frame fixture starts exactly once: "+id);
                charged.setPos(h.absoluteVec(new Vec3(2.5,1,2.5)));
                depleted.setPos(h.absoluteVec(new Vec3(2.5,1,9.5)));
                charged.setYRot(-90);depleted.setYRot(-90);
                stacks[0]=equip(charged,id,20,SwordCycle.CAPACITY,13);
                stacks[1]=equip(depleted,id,20,0,13);
                targets[0]=target(h,4.5,2.5);targets[1]=target(h,4.5,9.5);
                positions[0]=charged.position();positions[1]=depleted.position();
                use(h,charged);use(h,depleted);
                windup(h,charged,positions[0],targets[0]);windup(h,depleted,positions[1],targets[1]);
                paid[0]=ammo(stacks[0]).rounds();paid[1]=ammo(stacks[1]).rounds();
                check(h,paid[0]<19&&paid[1]==19&&SwordItems.energy(stacks[0])==0,
                        id+": full heavy pays multiple ammo/energy; zero-energy heavy pays one: "+paid[0]+"/"+paid[1]);
                use(h,charged);use(h,depleted);
                check(h,ammo(stacks[0]).rounds()==paid[0]&&ammo(stacks[1]).rounds()==paid[1],
                        id+": duplicate native use cannot spend a second heavy");
            });
            h.runAfterDelay(start+contact-1,()->{
                windup(h,charged,positions[0],targets[0]);windup(h,depleted,positions[1],targets[1]);
            });
            h.runAfterDelay(start+contact+1,()->{
                WeaponRuntime.tickPlayer(charged);WeaponRuntime.tickPlayer(depleted);
            });
            for(int tick=1;tick<=56;tick++) {
                int remaining=72000-tick;
                h.runAfterDelay(start+tick,()->{
                    check(h,stacks[0]!=null&&stacks[1]!=null,"Start task precedes held tick");
                    WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(),charged,stacks[0],remaining);
                    WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(),depleted,stacks[1],remaining);
                });
            }
            h.runAfterDelay(start+57,()->{
                WeaponRuntime.tickPlayer(charged);WeaponRuntime.tickPlayer(depleted);
                float fullDamage=TARGET_HEALTH-targets[0].getHealth(),zeroDamage=TARGET_HEALTH-targets[1].getHealth();
                check(h,fullDamage>zeroDamage&&zeroDamage>0,id+": actual full/weak HP: "+fullDamage+"/"+zeroDamage
                                +" p="+charged.position()+" eye="+charged.getEyePosition()+" look="+charged.getLookAngle()
                                +" target="+targets[0].position()+" box="+targets[0].getBoundingBox());
                check(h,ammo(stacks[0]).rounds()==paid[0]&&ammo(stacks[1]).rounds()==paid[1]
                                &&!WeaponRuntime.reloading(charged)&&!WeaponRuntime.reloading(depleted),
                        id+": held native ticks cannot repeat after cadence");
                charged.stopUsingItem();depleted.stopUsingItem();targets[0].discard();targets[1].discard();
                if(last)h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void guardReducesOnlyFrontalMobHpLossWithoutExtraHitEnergyDrain(GameTestHelper h) {
        var p = player(h, 6.5, false);
        var stack = equip(p, SWORDS[0], 12, SwordCycle.CAPACITY, 0);
        var front = target(h, 5.5, 6.5);
        var back = target(h, .5, 6.5);
        var attacker = player(h, 6.5, false);
        attacker.setPos(h.absoluteVec(new Vec3(5.5, 1, 6.5)));
        p.setShiftKeyDown(true);
        h.runAfterDelay(2, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, WeaponRuntime.swordStatus(p).orElseThrow().guarding(), "Sneaking activates actual sword guard");
            int loaded = ammo(stack).rounds();
            int energy = SwordItems.energy(stack);
            use(h, p);
            check(h, ammo(stack).rounds() == loaded && SwordItems.energy(stack) == energy,
                    "Guard denies heavy without paying ammo or energy");
            int delayBeforeQuery = SwordItems.delay(stack);
            float queried = WeaponRuntime.guardDamage(p, p.damageSources().mobAttack(front), 8);
            WeaponRuntime.guardDamage(p, p.damageSources().mobAttack(front), 8);
            check(h, queried >= 0 && queried < 8 && SwordItems.energy(stack) == energy
                            && SwordItems.delay(stack) == delayBeforeQuery,
                    "Pure guardDamage queries cannot spend energy or start recharge delay");
            p.setPermanentlyInvulnerable(true);
            float rejected = hurt(h, p, p.damageSources().mobAttack(front));
            p.setPermanentlyInvulnerable(false);
            check(h, rejected == 0 && SwordItems.energy(stack) == energy
                            && SwordItems.delay(stack) == delayBeforeQuery,
                    "Invulnerability-rejected incoming damage cannot drain guard energy or start delay");
            float frontal = hurt(h, p, p.damageSources().mobAttack(front));
            int afterFirst = SwordItems.energy(stack);
            check(h, frontal > 0 && frontal < 8 && afterFirst == energy
                            && SwordItems.delay(stack) == delayBeforeQuery,
                    "Real frontal mob damage is reduced without additional hit energy cost (2023 rule)");
            hurt(h, p, p.damageSources().mobAttack(front));
            int afterSecond = SwordItems.energy(stack);
            check(h, afterSecond == afterFirst && ammo(stack).rounds() == loaded,
                    "Repeated accepted guard hits add no energy or ammo cost");
            check(h, Math.abs(hurt(h, p, p.damageSources().mobAttack(back)) - 8) < .001f,
                    "Rear mob damage reaches actual HP in full");
            check(h, Math.abs(hurt(h, p, p.damageSources().fall()) - 8) < .001f,
                    "Environmental damage reaches actual HP in full");
            check(h, Math.abs(hurt(h, p, p.damageSources().playerAttack(attacker)) - 8) < .001f,
                    "Frontal player damage is not PvE guard damage");
            check(h, SwordItems.energy(stack) == afterSecond && ammo(stack).rounds() == loaded,
                    "Rejected guard conditions cannot spend block energy or ammo");
            p.setShiftKeyDown(false);
            check(h, Math.abs(hurt(h, p, p.damageSources().mobAttack(front)) - 8) < .001f,
                    "Releasing sneak revokes protection before another runtime tick");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void idleGuardConsumesHeldEnergyThenRegeneratesAfterReleaseDelay(GameTestHelper h) {
        var p = player(h, 6.5, false);
        var stack = equip(p, SWORDS[0], 12, 25000, SwordCycle.RECHARGE_DELAY);
        p.setShiftKeyDown(true);
        var empty = player(h, 2.5, false);
        equip(empty, SWORDS[0], 0, SwordCycle.CAPACITY, 0);
        empty.setShiftKeyDown(true);
        var depleted = player(h, 9.5, false);
        equip(depleted, SWORDS[0], 12, 0, SwordCycle.RECHARGE_DELAY);
        depleted.setShiftKeyDown(true);
        var emptyFront = target(h, 5.5, 2.5);
        var depletedFront = target(h, 5.5, 9.5);
        h.runAfterDelay(2, () -> {
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(empty);
            WeaponRuntime.tickPlayer(depleted);
            check(h, !WeaponRuntime.swordStatus(empty).orElseThrow().guarding()
                            && !WeaponRuntime.swordStatus(depleted).orElseThrow().guarding(),
                    "Sneak alone cannot guard without both usable ammo and positive energy");
            check(h, Math.abs(hurt(h, empty, empty.damageSources().mobAttack(emptyFront)) - 8) < .001f
                            && Math.abs(hurt(h, depleted, depleted.damageSources().mobAttack(depletedFront)) - 8) < .001f,
                    "Missing ammo or energy leaves real frontal mob HP damage unreduced");
            check(h, WeaponRuntime.swordStatus(p).orElseThrow().guarding() && SwordItems.energy(stack) < 25000
                            && ammo(stack).rounds()==12,
                    "Holding guard consumes time-based energy, not ammo, even without incoming hits");
            p.setShiftKeyDown(false);
            WeaponRuntime.tickPlayer(p);
        });
        h.runAfterDelay(SwordCycle.RECHARGE_DELAY - 1, () -> {
            WeaponRuntime.tickPlayer(p);
            check(h, SwordItems.energy(stack) >= 25000-2*SwordCycle.GUARD_DRAIN_PER_TICK
                            && SwordItems.energy(stack)<25000,
                    "Release respects the last active guard recharge delay");
        });
        h.runAfterDelay(SwordCycle.RECHARGE_DELAY + 4, () -> {
            WeaponRuntime.tickPlayer(p);
            int energy = SwordItems.energy(stack);
            check(h, energy > 25000 && energy <= SwordCycle.CAPACITY
                            && !WeaponRuntime.swordStatus(p).orElseThrow().guarding() && ammo(stack).rounds() == 12,
                    "Released guard regenerates only after delay without draining ammo");
            WeaponRuntime.tickPlayer(p);
            WeaponRuntime.tickPlayer(p);
            var status = WeaponRuntime.swordStatus(p).orElseThrow();
            check(h, SwordItems.energy(stack) == energy && status.energy() >= 0 && status.energy() <= 1
                            && Math.abs(status.energy() - energy / (float) SwordCycle.CAPACITY) < .00001f,
                    "Duplicate ticks/status reads cannot add recharge and status reflects real bounded energy");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void swapCancelsTransientSwordStateWithoutRefillOrOwnerCadenceReset(GameTestHelper h) {
        var p = player(h, 6.5, false);
        var first = equip(p, SWORDS[0], 12, 62000, 13);
        var enemy = target(h, 4.5, 6.5);
        var start = p.position();
        InputRouter.onPunch(p);
        windup(h, p, start, enemy);
        check(h, ammo(first).rounds() == 11 && WeaponRuntime.swordStatus(p).orElseThrow().combo() > 0,
                "Initial light establishes paid attack and live combo");
        int energy = SwordItems.energy(first);
        int delay = SwordItems.delay(first);
        p.setItemInHand(InteractionHand.MAIN_HAND, ItemStack.EMPTY);
        WeaponRuntime.tickPlayer(p);
        check(h, WeaponRuntime.swordStatus(p).isEmpty(), "Removing sword clears available combo/guard status");
        var replacement = equip(p, SWORDS[1], 12, 31000, 17);
        check(h, WeaponRuntime.swordStatus(p).orElseThrow().combo() == 0
                        && !WeaponRuntime.swordStatus(p).orElseThrow().guarding(),
                "Replacement never inherits combo or guard");
        use(h, p);
        InputRouter.onPunch(p);
        check(h, ammo(replacement).rounds() == 12 && SwordItems.energy(replacement) == 31000,
                "Changing item cannot bypass owner's shared light/heavy cadence or refill replacement energy");
        h.runAfterDelay(3, () -> {
            check(h, SwordItems.energy(first) == energy && SwordItems.delay(first) == delay,
                    "Stowed source receives no elapsed-time recharge or delay countdown");
            p.setItemInHand(InteractionHand.MAIN_HAND, first);
            p.setShiftKeyDown(true);
            WeaponRuntime.tickPlayer(p);
            check(h, !WeaponRuntime.swordStatus(p).orElseThrow().guarding(),
                    "Guard cannot bypass the outstanding owner attack cadence");
            p.setShiftKeyDown(false);
            InputRouter.onPunch(p);
            check(h, ammo(first).rounds() == 11 && SwordItems.energy(first) == energy
                            && WeaponRuntime.swordStatus(p).orElseThrow().combo() == 0,
                    "Re-equipping source preserves item energy and owner cooldown, with old combo cancelled");
        });
        h.runAfterDelay(contact(first, false) + 1, () -> {
            WeaponRuntime.tickPlayer(p);
            windup(h, p, start, enemy);
            check(h, ammo(first).rounds() == 11 && ammo(replacement).rounds() == 12,
                    "Canceled pre-contact attack never damages or moves later and refunds neither sword");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 30, environment = "destiny-test:w90_isolated")
    public void guardianMeleeAndSuperPunchRetainPriorityOverSword(GameTestHelper h) {
        var p = player(h, 6.5, true);
        var stack = equip(p, SWORDS[0], 12, 62000, 13);
        var data = Guardians.data(p);
        p.setShiftKeyDown(true);
        check(h, !WeaponRuntime.onPunch(p), "Crouched Guardian punch is offered to the existing skill router");
        InputRouter.onPunch(p);
        check(h, data.cooldown(AbilitySlot.MELEE) > 0 && ammo(stack).rounds() == 12
                        && SwordItems.energy(stack) == 62000,
                "Routed crouched punch activates Guardian melee without a sword light or ammo payment");
        p.setShiftKeyDown(false);
        data.setSuperEnergy(1);
        check(h, InputRouter.dispatch(p, GuardianAction.SUPER) && AbilityService.inSuper(p),
                "Fixture enters the real equipped Guardian super");
        int rounds = ammo(stack).rounds();
        int energy = SwordItems.energy(stack);
        check(h, !WeaponRuntime.onPunch(p), "Super punch remains available to Guardian PRIMARY");
        InputRouter.onPunch(p);
        use(h, p);
        check(h, ammo(stack).rounds() == rounds && SwordItems.energy(stack) == energy,
                "Super PRIMARY/native RMB cannot also spend the underlying sword");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void swordHudUsesActualEnergyAndSingleAmmoWithoutMutatingGuardianCooldown(GameTestHelper h) {
        var p = player(h, 6.5, true);
        var gun = WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow());
        p.setItemInHand(InteractionHand.MAIN_HAND, gun);
        CombatHud.update(p);
        var stack = equip(p, SWORDS[0], 12, 25000, 13);
        Guardians.data(p).setCooldown(AbilitySlot.MELEE, 123);
        var before = stack.copy();
        CombatHud.update(p);
        CombatHud.update(p);
        var ids = DisplayHud.getHuds(p).keySet();
        check(h, ids.stream().noneMatch(id -> id.startsWith(AmmoHud.PREFIX + "reserve_")
                        || id.equals(AmmoHud.PREFIX + "divider") || id.equals(AmmoHud.PREFIX + "infinity")),
                "Switching from a gun clears reserve digits, divider and infinity for sword");
        String melee = CombatHud.ABILITIES_ID + "_1";
        var icon = (ItemDisplayHud) DisplayHud.getHud(p, melee + "_icon");
        check(h, icon != null && icon.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/ammo_sword"),
                "Guardian melee tile uses the existing sword icon");
        var fill = (ItemDisplayHud) DisplayHud.getHud(p, melee + "_charge");
        check(h, fill != null && Math.abs(fill.getScale().x - 12) < .1,
                "Quarter stored sword energy drives quarter of the existing 48px melee gauge");
        check(h, Guardians.data(p).cooldown(AbilitySlot.MELEE) == 123 && ItemStack.matches(stack, before),
                "Repeated HUD/status queries cannot mutate Guardian cooldown, ammo, energy or recharge delay");
        var status = WeaponRuntime.swordStatus(p).orElseThrow();
        check(h, Math.abs(status.energy() - .25f) < .00001f, "HUD reads authoritative normalized sword energy");
        p.setItemInHand(InteractionHand.MAIN_HAND,gun);CombatHud.update(p);
        var restored=(ItemDisplayHud)DisplayHud.getHud(p,melee+"_icon");
        check(h,restored.getItem().get(DataComponents.ITEM_MODEL).toString().endsWith("/knife")
                        &&Guardians.data(p).cooldown(AbilitySlot.MELEE)==123&&ItemStack.matches(stack,before),
                "Unselect restores actual Guardian melee icon/cooldown without refilling the stowed sword");
        var ordinary=player(h,9.5,false);equip(ordinary,SWORDS[0],12,25000,13);CombatHud.update(ordinary);
        check(h,DisplayHud.getHud(ordinary,AmmoHud.PREFIX+"sword_energy")!=null,
                "Non-Guardian has the bounded fallback energy bar rather than a missing ability tile");
        ordinary.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);CombatHud.update(ordinary);
        check(h,DisplayHud.getHuds(ordinary).keySet().stream().noneMatch(id->id.startsWith(AmmoHud.PREFIX+"sword_")),
                "Non-Guardian fallback energy clears on unselect");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 25, environment = "destiny-test:w90_isolated")
    public void earnedHeavyPickupFillsOnlyFiniteSwordPoolOnceAndPreservesEnergy(GameTestHelper h) {
        var p = player(h, 6.5, false);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.getInventory().setItem(0, WeaponItems.create(WeaponCatalog.find("austringer").orElseThrow()));
        p.getInventory().setItem(1, WeaponItems.create(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()));
        var stack = sword(SWORDS[0], 0, 27150, 13);
        p.getInventory().setItem(2, stack);
        p.getInventory().setSelectedSlot(0);
        p.setAttached(AmmoEconomy.METERS, new AmmoMeters(0, AmmoMeters.FULL));
        var enemy = target(h, 5.5, 6.5);
        Combat.damage(h.getLevel(), p, enemy, TARGET_HEALTH + 100, Element.KINETIC, AmmoGeneration.ABILITY);
        check(h, enemy.isDeadOrDying() && AmmoEconomy.bricks(p) == 1,
                "Real final blow with canonical loadout earns one finite Heavy brick");
        p.setPos(AmmoEconomy.brickPositions(p).getFirst());
        AmmoEconomy.tickPlayer(p);
        var picked = ammo(stack);
        check(h, picked.rounds() > 0 && picked.rounds() <= WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()).magazine()
                        && picked.reserve() == 0 && picked.overflow() == 0 && AmmoEconomy.bricks(p) == 0,
                "Earned Heavy brick fills sword's finite usable pool directly, without a second reserve");
        long total = picked.total();
        AmmoEconomy.tickPlayer(p);
        check(h, ammo(stack).total() == total && SwordItems.energy(stack) == 27150 && SwordItems.delay(stack) == 13,
                "Repeated pickup cannot mint ammo or refill/restart item energy");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void anyPositiveEnergyReallyHitsAtFullPowerAndUnpoweredCostsOne(GameTestHelper h) {
        var full=player(h,2.5,false);var partial=player(h,6.5,false);var weak=player(h,9.5,false);
        var a=equip(full,SWORDS[0],12,SwordCycle.CAPACITY,13);
        var b=equip(partial,SWORDS[0],12,1,13);
        var c=equip(weak,SWORDS[0],12,0,13);
        var x=target(h,4.5,2.5);var y=target(h,4.5,6.5);var z=target(h,4.5,9.5);
        var fullStart=full.position();var partialStart=partial.position();var weakStart=weak.position();
        use(h,full);use(h,partial);use(h,weak);
        windup(h,full,fullStart,x);windup(h,partial,partialStart,y);windup(h,weak,weakStart,z);
        check(h,ammo(a).rounds()==8&&ammo(b).rounds()==8&&ammo(c).rounds()==11
                        &&SwordItems.energy(a)==0&&SwordItems.energy(b)==0,
                "Charged authored adaptive cost4, official unpowered cost1; energy paid only on acceptance");
        h.runAfterDelay(contact(a,true)-1,()->{
            windup(h,full,fullStart,x);windup(h,partial,partialStart,y);windup(h,weak,weakStart,z);
        });
        h.runAfterDelay(contact(a,true)+1,()->{
            WeaponRuntime.tickPlayer(full);WeaponRuntime.tickPlayer(partial);WeaponRuntime.tickPlayer(weak);
            check(h,x.getHealth()<TARGET_HEALTH&&Math.abs(x.getHealth()-y.getHealth())<.001f
                            &&z.getHealth()>x.getHealth()&&z.getHealth()<TARGET_HEALTH,
                    "Real HP: one energy produces full heavy power; zero energy is weaker, not an old partial curve");
            check(h,ammo(a).rounds()==8&&ammo(b).rounds()==8&&ammo(c).rounds()==11,
                    "Delayed contact cannot repeat heavy payment");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void deniedHeavyCannotSpendEnergyAmmoOrHideACooldown(GameTestHelper h) {
        var p=player(h,6.5,false);var stack=equip(p,SWORDS[0],2,80000,13);
        var enemy=target(h,4.5,6.5);var before=stack.copy();
        use(h,p);use(h,p);
        check(h,ItemStack.matches(stack,before)&&enemy.getHealth()==TARGET_HEALTH,
                "Insufficient charged ammo denies atomically, without energy/cost/HP mutation");
        p.stopUsingItem();
        var start=p.position();
        InputRouter.onPunch(p);
        windup(h,p,start,enemy);
        check(h,ammo(stack).rounds()==1&&SwordItems.energy(stack)==80000,
                "Denied heavy establishes no hidden owner cooldown; legal light immediately pays once");
        h.runAfterDelay(contact(stack,false)-1,()->windup(h,p,start,enemy));
        h.runAfterDelay(contact(stack,false)+1,()->{
            WeaponRuntime.tickPlayer(p);
            check(h,ammo(stack).rounds()==1&&enemy.getHealth()<TARGET_HEALTH&&SwordItems.energy(stack)==80000,
                    "Light accepted immediately after heavy denial lands real HP damage at contact");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void vortexCleaveRespectsWallsAndDashCannotCrossBodyCollision(GameTestHelper h) {
        var spin=player(h,2.5,false);var stack=equip(spin,SWORDS[3],12,SwordCycle.CAPACITY,13);
        var behind=target(h,.8,2.5);var blocked=target(h,5.5,2.5);
        h.setBlock(4,1,2,net.minecraft.world.level.block.Blocks.STONE);
        h.setBlock(4,2,2,net.minecraft.world.level.block.Blocks.STONE);
        var spinStart=spin.position();
        use(h,spin);
        windup(h,spin,spinStart,behind,blocked);
        check(h,ammo(stack).rounds()==8,"Vortex pays sourced four ammo at acceptance");
        var dash=player(h,9.5,false);var dashStack=equip(dash,SWORDS[1],12,SwordCycle.CAPACITY,13);
        h.setBlock(3,1,9,net.minecraft.world.level.block.Blocks.STONE);
        h.setBlock(3,2,9,net.minecraft.world.level.block.Blocks.STONE);
        var dashStart=dash.position();use(h,dash);
        windup(h,dash,dashStart);
        h.runAfterDelay(contact(dashStack,true)-1,()->windup(h,dash,dashStart));
        h.runAfterDelay(contact(dashStack,true)+1,()->{
            WeaponRuntime.tickPlayer(dash);
            check(h,dash.getX()>=dashStart.x&&dash.getX()<=h.absoluteVec(new Vec3(2.71,1,9.5)).x,
                    "Authored Goldtusk body dash never crosses the colliding wall at contact");
        });
        h.runAfterDelay(contact(stack,true)-1,()->windup(h,spin,spinStart,behind,blocked));
        h.runAfterDelay(contact(stack,true)+1,()->{
            WeaponRuntime.tickPlayer(spin);
            check(h,behind.getHealth()<TARGET_HEALTH&&blocked.getHealth()==TARGET_HEALTH&&ammo(stack).rounds()==8,
                    "Vortex is radial, costs sourced four ammo, and cannot damage through a solid wall");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void pointBlankSwordContactIsNotLostWhenRayStartsInsideInflatedEnemyBox(GameTestHelper h) {
        var p=player(h,6.5,false);var s=equip(p,SWORDS[0],12,SwordCycle.CAPACITY,13);
        var enemy=target(h,2.9,6.5);
        check(h,enemy.getBoundingBox().inflate(.15).contains(p.getEyePosition()),"Fixture begins inside melee margin");
        var start=p.position();
        InputRouter.onPunch(p);
        windup(h,p,start,enemy);
        check(h,ammo(s).rounds()==11,"Point-blank light pays on acceptance");
        h.runAfterDelay(contact(s,false)-1,()->windup(h,p,start,enemy));
        h.runAfterDelay(contact(s,false)+1,()->{
            WeaponRuntime.tickPlayer(p);
            check(h,enemy.getHealth()<TARGET_HEALTH&&ammo(s).rounds()==11,
                    "Actual point-blank HP transaction lands once instead of AABB entry-ray miss");
            h.succeed();
        });
    }
}
