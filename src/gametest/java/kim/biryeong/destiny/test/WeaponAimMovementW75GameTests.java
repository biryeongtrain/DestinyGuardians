package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponScopeHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.shaderfx.impl.ModConfig;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundPlayerPositionPacket;
import net.minecraft.network.protocol.game.ClientboundUpdateAttributesPacket;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerEntity;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.Pose;
import net.minecraft.world.entity.UpdateInterval;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeMap;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.AttributeSupplier;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;
import java.util.Set;

import static net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED;
import static net.minecraft.world.entity.ai.attributes.Attributes.SNEAKING_SPEED;
import static net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL;
import static net.minecraft.world.entity.ai.attributes.AttributeModifier.Operation.ADD_VALUE;

/** Bounded real server-tick tests of native ADS movement and untouched crouch, not native client movement evidence.
 * Ordinary airborne travel's fixed .02 speed is outside the claimed ground-speed ratio.
 * First observation uses normal already-equipped handling; replacements pay the actual deadline.
 * The last two tests need an isolated environment registry entry, supplied by the coordinator:
 * data/destiny-test/test_environment/w75_global.json = {"type":"minecraft:all_of","definitions":[]}.
 * They complete synchronously so their global clears cannot overlap each other's delayed work.
 */
public final class WeaponAimMovementW75GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String GLOBAL = "destiny-test:w90_w75_global";
    private static final Identifier SPEED_ID = Identifier.fromNamespaceAndPath("destiny", "weapon_ads_movement_w75");
    private static final Identifier SNEAK_ID = Identifier.fromNamespaceAndPath("destiny", "weapon_ads_sneak_w75");
    private static final double EPS = 1e-7;

    private static void check(GameTestHelper h, boolean ok, String message) {
        h.assertTrue(ok, Component.literal(message));
    }
    private static void near(GameTestHelper h, double actual, double expected, String message) {
        check(h, Math.abs(actual - expected) < EPS, message + ": expected " + expected + ", got " + actual);
    }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static double expected(WeaponCatalog.Entry e) {
        if (e.family().equals("sidearm")) return .85;
        return e.id().equals("seventh_seraph_officer_revolver") ? .775 : .75;
    }
    private static AttributeInstance speed(ServerPlayer p) { return p.getAttribute(MOVEMENT_SPEED); }
    private static AttributeInstance sneak(ServerPlayer p) { return p.getAttribute(SNEAKING_SPEED); }
    private static ServerPlayer player(GameTestHelper h, String id) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, 6.5), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        int slot = WeaponCharacteristics.of(entry(id)).slot().hotbar();
        p.getInventory().setItem(slot, WeaponItems.create(entry(id)));
        p.getInventory().setSelectedSlot(slot);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            p.setServerLevel(h.getLevel());
            p.stopRiding();
            WeaponRuntime.cleanup(p);
            CombatHud.remove(p); WeaponScopeHud.remove(p);
            for (String node : List.copyOf(DisplayHud.getHuds(p).keySet())) DisplayHud.removeHud(p, node);
            CameraEffects.resetFov(p);
            TestPlayers.remove(p);
        });
        return p;
    }
    private static void tick(ServerPlayer p) { WeaponRuntime.tickPlayer(p); }
    private static void nativeSpeed(GameTestHelper h, ServerPlayer p, double scalar) {
        var movement = speed(p).getModifier(SPEED_ID);
        check(h, movement != null, "Native ADS movement modifier installed");
        check(h, movement.operation() == ADD_MULTIPLIED_TOTAL, "Native zoom multiplies total movement");
        near(h, movement.amount(), zoomed(p, scalar) - 1, "Progress-dependent native movement ratio");
        check(h, !speed(p).getPermanentModifiers().contains(movement), "ADS movement is never permanent");
    }
    private static double zoomed(ServerPlayer p, double scalar) {
        double progress = WeaponAiming.progress(p);
        double zoom = WeaponAimProfile.of(WeaponItems.entry(p.getMainHandItem()).orElseThrow()).zoom();
        return (1 - progress) + progress * (scalar / Math.max(1, zoom));
    }
    private static void absent(GameTestHelper h, ServerPlayer p) {
        check(h, !speed(p).hasModifier(SPEED_ID) && !sneak(p).hasModifier(SNEAK_ID), "Owned native speed is absent and retired sneak modifier is never installed");
    }
    private static void defaults(GameTestHelper h, ServerPlayer p, double base) {
        absent(h, p);
        near(h, speed(p).getBaseValue(), base, "Native movement base snapshot preserved");
        near(h, speed(p).getValue(), base, "Default movement restored");
        near(h, sneak(p).getBaseValue(), .3, "Native sneak base preserved");
        near(h, sneak(p).getValue(), .3, "Default sneak restored");
    }
    private static AttributeModifier modifier(Identifier id, double amount) {
        return new AttributeModifier(id, amount, ADD_MULTIPLIED_TOTAL);
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void all57RatiosInstallOnFirstAcceptedTickAndReleaseBeforeAdsExitCompletes(GameTestHelper h) {
        var entries = WeaponCatalog.all().stream().filter(WeaponAimProfile::supports).toList();
        WeaponModelGameTests.assertCatalogExpansion(h);
        check(h, WeaponModelGameTests.originalW30Entries().stream().filter(WeaponAimProfile::supports).count() == 57,
                "Original 57 normal W44 ADS entries preserved");
        check(h, entries.size() == 59, "Normal W44 ADS set plus Ace and Izanagi");
        var actors = new ArrayList<ServerPlayer>();
        var bases = new ArrayList<Double>();
        for (var e : entries) {
            var p = player(h, e.id()); actors.add(p); bases.add(speed(p).getBaseValue());
            near(h, speed(p).getBaseValue(), .1, "Default player speed");
            tick(p); absent(h, p); ads(p, true);
        }
        h.runAfterDelay(1, () -> {
            for (int i = 0; i < actors.size(); i++) {
                var p = actors.get(i); var e = entries.get(i); tick(p);
                check(h, WeaponAiming.progress(p) > 0 && WeaponAiming.progress(p) < 1,
                        e.id() + " first accepted tick is still entering ADS");
                nativeSpeed(h, p, expected(e)); near(h, speed(p).getValue(), bases.get(i) * zoomed(p, expected(e)), e.id());
                near(h, speed(p).getBaseValue(), bases.get(i), "Movement base remains native");
                near(h, sneak(p).getValue(), .3, "ADS never neutralizes native crouch slowdown");
            }
        });
        h.runAfterDelay(2, () -> { for (var p : actors) tick(p); });
        h.runAfterDelay(3, () -> {
            for (int i = 0; i < actors.size(); i++) {
                var p = actors.get(i); ads(p, false); tick(p);
                check(h, WeaponAiming.progress(p) > 0, "Movement releases while visual ADS still exits");
                defaults(h, p, bases.get(i));
            }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void swordsGlaivesPreviewAndOrdinaryItemsNeverAcquireThePair(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (var e : WeaponCatalog.all().stream().filter(e -> !WeaponAimProfile.supports(e)).toList()) {
            actors.add(player(h, e.id()));
        }
        check(h, actors.size() == 6, "All sword and glaive catalog rows");
        var preview = player(h, "austringer");
        preview.setItemInHand(InteractionHand.MAIN_HAND, WeaponModels.create(entry("austringer"))); actors.add(preview);
        var ordinary = player(h, "austringer");
        ordinary.setItemInHand(InteractionHand.MAIN_HAND, new ItemStack(Items.DIAMOND)); actors.add(ordinary);
        for (var p : actors) { ads(p, true); tick(p); absent(h, p); }
        h.runAfterDelay(1, () -> {
            for (var p : actors) { tick(p); absent(h, p); near(h, WeaponAiming.progress(p), 0, "Excluded input never aims"); }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void heldTicksKeepExactObjectsAndDoNotContinuallyDirtyEitherAttribute(GameTestHelper h) {
        var p = player(h, "austringer"); var position = p.position(); var motion = p.getDeltaMovement();
        double base = speed(p).getBaseValue(); tick(p); ads(p,true);
        // AttributeMap creates syncable AttributeInstances lazily and dirties them on first lookup.
        // Materialize the observed native sneak attribute before clearing setup dirtiness.
        var nativeSneak = sneak(p);
        var sneakModifiers = Set.copyOf(nativeSneak.getModifiers());
        double sneakBase = nativeSneak.getBaseValue(), sneakValue = nativeSneak.getValue();
        var previous = new AttributeModifier[1]; double[] amount = {Double.NaN};
        p.getAttributes().getAttributesToSync().clear();
        for (int i=1;i<=12;i++) {
            int elapsed=i;
            h.runAfterDelay(i,()->{
                tick(p); nativeSpeed(h,p,.75);
                var current=speed(p).getModifier(SPEED_ID);
                boolean changed=Double.compare(current.amount(),amount[0])!=0;
                check(h,p.getAttributes().getAttributesToSync().contains(speed(p))==changed,
                        "Native sync is dirtied exactly when ADS progress changes the movement amount");
                check(h,!p.getAttributes().getAttributesToSync().contains(nativeSneak) && !nativeSneak.hasModifier(SNEAK_ID)
                                && Set.copyOf(nativeSneak.getModifiers()).equals(sneakModifiers),
                        "ADS never owns, changes or dirties the already-materialized native sneak attribute");
                near(h,nativeSneak.getBaseValue(),sneakBase,"Native crouch base stays unchanged");
                near(h,nativeSneak.getValue(),sneakValue,"Native crouch value stays unchanged");
                if(previous[0]!=null)check(h,(current==previous[0])==!changed,"Unchanged full ADS reuses the exact modifier");
                previous[0]=current;amount[0]=current.amount();p.getAttributes().getAttributesToSync().clear();
                tick(p);check(h,speed(p).getModifier(SPEED_ID)==current&&p.getAttributes().getAttributesToSync().isEmpty(),
                        "Same-tick duplicate tick never rewrites a stable modifier");
                near(h,speed(p).getBaseValue(),base,"Native base unchanged");
                check(h,p.position().equals(position)&&p.getDeltaMovement().equals(motion),"No position/velocity spoof");
                if(elapsed==12){ads(p,false);tick(p);defaults(h,p,base);
                    check(h,p.getAttributes().getAttributesToSync().contains(speed(p))&&!p.getAttributes().getAttributesToSync().contains(nativeSneak),"Release synchronizes only the owned speed restoration");
                    check(h,TestPlayers.outbound(p).stream().noneMatch(x->x instanceof ClientboundPlayerPositionPacket),"No teleport");h.succeed();}
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void unrelatedTransientPermanentModifiersAndLiveBaseEditsSurviveCleanup(GameTestHelper h) {
        var p = player(h, "allied_demand"); tick(p); ads(p, true);
        var foreignSpeed = new AttributeModifier(Identifier.fromNamespaceAndPath("w75_test", "speed"), .02, ADD_VALUE);
        var foreignSneak = new AttributeModifier(Identifier.fromNamespaceAndPath("w75_test", "swift_sneak"), .15, ADD_VALUE);
        speed(p).addPermanentModifier(foreignSpeed); sneak(p).addTransientModifier(foreignSneak);
        h.runAfterDelay(1, () -> {
            tick(p); nativeSpeed(h, p, .85);
            speed(p).setBaseValue(.2); sneak(p).setBaseValue(.4);
            near(h, speed(p).getValue(), (.2 + .02) * zoomed(p, .85), "ADS composes with edited base and foreign speed");
            near(h, sneak(p).getValue(), .55, "ADS leaves foreign Swift Sneak and base untouched");
            WeaponRuntime.cleanup(p);
            near(h, speed(p).getBaseValue(), .2, "Latest external movement base survives");
            near(h, sneak(p).getBaseValue(), .4, "Latest external sneak base survives");
            near(h, speed(p).getValue(), .22, "Foreign speed still contributes after cleanup");
            near(h, sneak(p).getValue(), .55, "Foreign sneak still contributes after cleanup");
            check(h, speed(p).getModifier(foreignSpeed.id()) == foreignSpeed
                    && sneak(p).getModifier(foreignSneak.id()) == foreignSneak, "Foreign objects preserved exactly");
            check(h, speed(p).getPermanentModifiers().equals(Set.of(foreignSpeed)), "Foreign permanence preserved");
            absent(h, p); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void eitherInitialCollisionYieldsTheWholePairUntilReleaseIncludingPermanentCollisions(GameTestHelper h) {
        var actors=new ArrayList<ServerPlayer>();var foreign=new ArrayList<AttributeModifier>();
        for(int i=0;i<4;i++){
            var p=player(h,"austringer");tick(p);actors.add(p);
            var m=modifier(i%2==0?SPEED_ID:SNEAK_ID,.125);foreign.add(m);
            var target=i%2==0?speed(p):sneak(p);
            if(i<2)target.addTransientModifier(m);else target.addPermanentModifier(m);ads(p,true);
        }
        for(int i=1;i<=7;i++){int elapsed=i;h.runAfterDelay(i,()->{
            for(int j=0;j<actors.size();j++){
                var p=actors.get(j);var target=j%2==0?speed(p):sneak(p);var m=foreign.get(j);
                if(elapsed==6)ads(p,true);tick(p);
                if(elapsed==1){
                    check(h,target.getModifier(m.id())==m,"Foreign collision identity preserved");
                    check(h,target.getPermanentModifiers().contains(m)==(j>=2),"Foreign permanence preserved");
                    if(j%2==0)near(h,speed(p).getValue(),.1*1.125,"Speed collision blocks owned native zoom");
                    else {nativeSpeed(h,p,.75);near(h,sneak(p).getValue(),.3*1.125,"Retired sneak ID does not block ADS or neutralize crouch");}
                    target.removeModifier(m.id());
                }
                if(elapsed==2&&j%2==0)check(h,!speed(p).hasModifier(SPEED_ID),"Removing collision alone cannot rearm yielded ADS");
                if(elapsed==3){ads(p,false);tick(p);defaults(h,p,.1);}
                if(elapsed>=6)nativeSpeed(h,p,.75);
            }
            if(elapsed==7)h.succeed();
        });}
    }

    private static void takeover(GameTestHelper h, boolean equalClone) {
        var actors=List.of(player(h,"austringer"),player(h,"austringer"));
        var replacements=new AttributeModifier[2];
        for(var p:actors){tick(p);ads(p,true);}
        for(int i=1;i<=7;i++){int elapsed=i;h.runAfterDelay(i,()->{
            for(int j=0;j<actors.size();j++){
                var p=actors.get(j);if(elapsed==6)ads(p,true);tick(p);
                if(elapsed==1){
                    nativeSpeed(h,p,.75);var original=speed(p).getModifier(SPEED_ID);
                    var replacement=modifier(SPEED_ID,equalClone?original.amount():.123);replacements[j]=replacement;
                    check(h,replacement!=original&&(!equalClone||replacement.equals(original)),"Distinct foreign takeover fixture");
                    speed(p).removeModifier(SPEED_ID);
                    if(j==0)speed(p).addTransientModifier(replacement);else speed(p).addPermanentModifier(replacement);
                    tick(p);check(h,speed(p).getModifier(SPEED_ID)==replacement,"Same-tick update yields to exact foreign identity");
                    check(h,!sneak(p).hasModifier(SNEAK_ID),"No retired sneak partner is installed");
                }
                if(elapsed==2){check(h,speed(p).getModifier(SPEED_ID)==replacements[j],"Held toggle cannot overwrite foreign owner");speed(p).removeModifier(SPEED_ID);}
                if(elapsed==3){absent(h,p);ads(p,false);tick(p);}
                if(elapsed==6)nativeSpeed(h,p,.75);
                if(elapsed==7){var m=modifier(SPEED_ID,.123);speed(p).removeModifier(SPEED_ID);speed(p).addTransientModifier(m);
                    WeaponRuntime.cleanup(p);WeaponRuntime.cleanup(p);check(h,speed(p).getModifier(SPEED_ID)==m,"Repeated cleanup leaves foreign takeover intact");}
            }
            if(elapsed==7)h.succeed();
        });}
    }
    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void equalValueCloneOnEitherAttributeIsForeignIdentity(GameTestHelper h) { takeover(h, true); }
    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void changedValueTakeoverOnEitherAttributeReleasesTheOtherHalf(GameTestHelper h) { takeover(h, false); }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void realReloadSkillAndExplicitSuspendRemoveImmediatelyAndLatchHeldInput(GameTestHelper h) {
        var reload = player(h, "austringer"); var skill = player(h, "austringer"); var suspended = player(h, "austringer");
        var actors = List.of(reload, skill, suspended); var profile = WeaponProfile.forEntry(entry("austringer"));
        WeaponItems.save(reload.getMainHandItem(), new WeaponMagazine(profile, 1, 6));
        for (var p : actors) { tick(p); ads(p, true); }
        int done = 2 + profile.reloadTicks(); check(h, done + 5 < 120, "Real reload fits fixed test bound");
        for (int i = 1; i <= done + 3; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                if (elapsed == done + 1) for (var p : actors) ads(p, true);
                for (var p : actors) tick(p);
                if (elapsed == 1) {
                    for (var p : actors) nativeSpeed(h, p, .75);
                    check(h, WeaponRuntime.reload(reload), "Real Q-path reload accepted");
                    WeaponRuntime.cancelUseForSkill(skill); WeaponAiming.suspend(suspended);
                    for (var p : actors) absent(h, p);
                } else if (elapsed <= done) {
                    for (var p : actors) absent(h, p);
                }
                if (elapsed == done) {
                    check(h, !WeaponRuntime.reloading(reload), "Reload actually finishes at its normal deadline");
                    for (var p : actors) { ads(p, false); tick(p); }
                }
                if (elapsed == done + 1) for (var p : actors) nativeSpeed(h, p, .75);
                if (elapsed == done + 3) { for (var p : actors) nativeSpeed(h, p, .75); h.succeed(); }
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void stowAndDrawPayNormalHandlingAndAcquireOnlyAtTheRealDeadline(GameTestHelper h) {
        var p = player(h, "austringer"); var outgoing = p.getMainHandItem();
        var incoming = WeaponItems.create(entry("beloved")); p.getInventory().setItem(1, incoming);
        tick(p); ads(p, true);
        int duration = WeaponHandlingProfile.of(entry("austringer")).stowTicks()
                + WeaponHandlingProfile.of(entry("beloved")).readyTicks();
        check(h, duration > 1 && duration + 5 < 80, "Actual switch fits test bound");
        for (int i = 1; i <= duration + 2; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tick(p);
                if (elapsed == 1) {
                    nativeSpeed(h, p, .75);
                    p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1)); tick(p);
                    absent(h, p); check(h, WeaponHandling.remaining(p) == duration, "Normal stow plus ready duration");
                    check(h, p.getInventory().getItem(0) == outgoing && p.getMainHandItem() == incoming, "Actual inventory stack switch");
                } else if (elapsed < duration + 1) {
                    absent(h, p); check(h, WeaponHandling.remaining(p) == duration + 1 - elapsed, "Readiness never reset to pass assertion");
                } else {
                    check(h, !WeaponHandling.blocked(p), "Original handling deadline reached");
                    if(elapsed==duration+1){absent(h,p);check(h,!WeaponAiming.requested(p),"Stowed toggle never transfers or queues");ads(p,true);}
                    else nativeSpeed(h,p,.75);
                }
                if (elapsed == duration + 2) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void exactStackReplacementAndTransferDoNotInheritAnOldPair(GameTestHelper h) {
        var donor = player(h, "austringer"); var recipient = player(h, "austringer");
        var original = donor.getMainHandItem(); var recipientOriginal = recipient.getMainHandItem();
        tick(donor); tick(recipient); ads(donor, true); ads(recipient, true);
        int duration = WeaponHandlingProfile.of(entry("austringer")).stowTicks()
                + WeaponHandlingProfile.of(entry("austringer")).readyTicks();
        check(h, duration + 5 < 80, "Actual replacement duration fits");
        var old = new AttributeModifier[4];
        for (int i = 1; i <= duration + 2; i++) {
            int elapsed = i;
            h.runAfterDelay(i, () -> {
                tick(donor); tick(recipient);
                if (elapsed == 1) {
                    nativeSpeed(h, donor, .75); nativeSpeed(h, recipient, .75);
                    old[0] = speed(donor).getModifier(SPEED_ID); old[1] = sneak(donor).getModifier(SNEAK_ID);
                    old[2] = speed(recipient).getModifier(SPEED_ID); old[3] = sneak(recipient).getModifier(SNEAK_ID);
                    donor.setItemInHand(InteractionHand.MAIN_HAND, original.copy());
                    recipient.setItemInHand(InteractionHand.MAIN_HAND, original);
                    check(h, donor.getMainHandItem() != original && recipient.getMainHandItem() != recipientOriginal,
                            "Component copy and actual transfer both replace identity");
                    tick(donor); tick(recipient); absent(h, donor); absent(h, recipient);
                } else if (elapsed < duration + 1) { absent(h, donor); absent(h, recipient); }
                else {
                    if(elapsed==duration+1){absent(h,donor);absent(h,recipient);ads(donor,true);ads(recipient,true);}
                    else {nativeSpeed(h, donor, .75); nativeSpeed(h, recipient, .75);
                    check(h, speed(donor).getModifier(SPEED_ID) != old[0] && !sneak(donor).hasModifier(SNEAK_ID)
                            && speed(recipient).getModifier(SPEED_ID) != old[2] && !sneak(recipient).hasModifier(SNEAK_ID),
                            "New stack/owner acquire fresh exact objects only after readiness and a new click");}
                }
                if (elapsed == duration + 2) h.succeed();
            });
        }
    }

    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void levelSpectatorSuperDeathAndRepeatedCleanupRetireTheirOwnPairs(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (int i = 0; i < 6; i++) { var p = player(h, "austringer"); tick(p); ads(p, true); actors.add(p); }
        h.runAfterDelay(1, () -> {
            for (var p : actors) { tick(p); nativeSpeed(h, p, .75); }
            var keeperSpeed = speed(actors.get(5)).getModifier(SPEED_ID);
            var keeperSneak = sneak(actors.get(5)).getModifier(SNEAK_ID);
            var other = java.util.stream.StreamSupport.stream(h.getLevel().getServer().getAllLevels().spliterator(), false)
                    .filter(level -> level != h.getLevel()).findFirst().orElseThrow();
            var moved = actors.get(0); ads(moved, false); moved.setServerLevel(other); tick(moved);
            defaults(h, moved, .1); moved.setServerLevel(h.getLevel());
            actors.get(1).setGameMode(GameType.SPECTATOR); tick(actors.get(1));
            AbilityService.startSuper(actors.get(2), new SuperSession() {
                public boolean tick() { return true; }
                public void primary() { }
                public void end() { }
                public float remaining() { return 1; }
            }); tick(actors.get(2));
            actors.get(3).setHealth(0); tick(actors.get(3));
            WeaponRuntime.cleanup(actors.get(4)); WeaponRuntime.cleanup(actors.get(4));
            for (int i = 0; i < 5; i++) defaults(h, actors.get(i), .1);
            check(h, speed(actors.get(5)).getModifier(SPEED_ID) == keeperSpeed
                    && sneak(actors.get(5)).getModifier(SNEAK_ID) == keeperSneak, "Other owner retains exact speed object and untouched native crouch");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 15, environment = "destiny-test:w90_fov_w75")
    public void fovTakeoverReleasesBothInTheSameTickAndPreservesForeignFov(GameTestHelper h) {
        var config=ModConfig.getInstance();boolean previous=config.dynamicFovShader;
        config.dynamicFovShader=true;TestCleanup.register(h,()->config.dynamicFovShader=previous);
        var p=player(h,"austringer");tick(p);ads(p,true);
        h.runAfterDelay(1,()->{
            tick(p);nativeSpeed(h,p,.75);check(h,CameraEffects.getFov(p)==null,"Native ADS never acquires shader FOV");
            var owned=speed(p).getModifier(SPEED_ID);float progress=WeaponAiming.progress(p);
            CameraEffects.setFov(p,55);tick(p);nativeSpeed(h,p,.75);
            check(h,speed(p).getModifier(SPEED_ID)==owned&&WeaponAiming.progress(p)==progress,"Foreign shader FOV does not disturb same-tick ADS or its speed owner");
            near(h,CameraEffects.getFov(p),55,"Foreign projection preserved");
        });
        h.runAfterDelay(2,()->{tick(p);nativeSpeed(h,p,.75);WeaponRuntime.cleanup(p);defaults(h,p,.1);
            near(h,CameraEffects.getFov(p),55,"Cleanup only releases native movement, never foreign shader projection");h.succeed();});
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void passengerFlyingGlidingSwimmingAndCrawlingReleaseThePair(GameTestHelper h) {
        var actors = new ArrayList<ServerPlayer>();
        for (int i = 0; i < 5; i++) { var p = player(h, "austringer"); tick(p); ads(p, true); actors.add(p); }
        var mount = h.spawn(EntityTypes.PIG, new Vec3(4.5, 1, 4.5)); mount.setNoAi(true); TestCleanup.register(h, mount::discard);
        h.startSequence().thenIdle(1).thenExecute(() -> {
            for (var p : actors) { tick(p); nativeSpeed(h, p, .75); }
            check(h, actors.get(0).startRiding(mount, true, true), "Native mounted fixture accepted");
            actors.get(1).getAbilities().flying = true;
            actors.get(2).startFallFlying(); check(h, actors.get(2).isFallFlying(), "Native gliding flag set");
            actors.get(3).setSwimming(true); check(h, actors.get(3).isSwimming(), "Native swimming flag set");
            actors.get(4).setPose(Pose.SWIMMING); actors.get(4).setSwimming(false);
            check(h, actors.get(4).isVisuallyCrawling(), "Native crawling pose independent of swimming flag");
            for (var p : actors) { tick(p); absent(h, p); }
        }).thenIdle(1).thenExecute(() -> {
            // The pig is world-ticked but these embedded players are not world-registered.
            // Re-establish the explicit modes before the second exclusion sample instead
            // of assuming that an artificial mount/swim/glide survives a native world tick.
            System.out.println("W75 fixture prior modes: passenger=" + actors.get(0).isPassenger()
                    + ", flying=" + actors.get(1).getAbilities().flying
                    + ", gliding=" + actors.get(2).isFallFlying() + ", swimming=" + actors.get(3).isSwimming()
                    + ", crawling=" + actors.get(4).isVisuallyCrawling());
            check(h, actors.get(0).startRiding(mount, true, true) || actors.get(0).isPassenger(), "Mounted fixture refreshed");
            actors.get(1).getAbilities().flying = true; actors.get(2).startFallFlying();
            actors.get(3).setSwimming(true); actors.get(4).setPose(Pose.SWIMMING); actors.get(4).setSwimming(false);
            for (var p : actors) { tick(p); absent(h, p); check(h,WeaponAiming.requested(p),"Locomotion exclusion leaves the input toggle intact"); }
            actors.get(0).stopRiding(); actors.get(1).getAbilities().flying = false;
            actors.get(2).stopFallFlying(); actors.get(3).setSwimming(false);
            // Embedded players do not run Player.updatePlayerPose. In 26.3 a stale FALL_FLYING
            // pose with the flight flag cleared also counts as visual swimming/crawling.
            // Restore native fixture poses explicitly; do not reset ADS or handling readiness.
            for (var p : actors) p.setPose(Pose.STANDING);
        }).thenIdle(1).thenExecute(() -> {
            var modes = List.of("passenger", "flying", "gliding", "swimming", "crawling");
            for (int i = 0; i < actors.size(); i++) {
                var p = actors.get(i);
                check(h, !p.isPassenger() && !p.getAbilities().flying && !p.isFallFlying()
                                && !p.isSwimming() && !p.isInWater() && !p.isInLava()
                                && !p.onClimbable() && !p.isVisuallyCrawling(),
                        modes.get(i) + " fixture restored ordinary locomotion while ADS toggle stays accepted: passenger=" + p.isPassenger()
                                + ", flying=" + p.getAbilities().flying + ", fallFlying=" + p.isFallFlying()
                                + ", swimming=" + p.isSwimming() + ", water=" + p.isInWater() + ", lava=" + p.isInLava()
                                + ", climbable=" + p.onClimbable() + ", crawling=" + p.isVisuallyCrawling() + ", pose=" + p.getPose());
                ads(p, true); tick(p); nativeSpeed(h, p, .75);
            }
        }).thenSucceed();
    }

    /** Explicit fixture refresh: embedded players do not run Entity.baseTick automatically.
     * Its fluid update alone is insufficient: 26.3 isInLava() also requires firstTick=false,
     * which baseTick establishes after refreshing fluid contact and cached in-block state.
     */
    private static void refreshFluidFixture(ServerPlayer p) { p.baseTick(); }
    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void actualWaterLavaAndClimbableBlocksExcludeThePair(GameTestHelper h) {
        var actors = List.of(player(h, "austringer"), player(h, "austringer"), player(h, "austringer"));
        for (var p : actors) { tick(p); ads(p, true); }
        h.runAfterDelay(1, () -> {
            for (var p : actors) { tick(p); nativeSpeed(h, p, .75); }
            h.setBlock(new BlockPos(2, 1, 2), Blocks.WATER);
            h.setBlock(new BlockPos(4, 1, 2), Blocks.LAVA);
            h.setBlock(new BlockPos(6, 1, 2), Blocks.VINE);
            for (int i = 0; i < actors.size(); i++) actors.get(i).setPos(h.absoluteVec(new Vec3(2.5 + 2 * i, 1, 2.5)));
            refreshFluidFixture(actors.get(0)); refreshFluidFixture(actors.get(1));
            check(h, actors.get(0).isInWater() && !actors.get(0).isSwimming(), "Water independently excludes non-swimming player");
            check(h, actors.get(1).isInLava(), "Native lava contact detected");
            check(h, actors.get(2).onClimbable(), "Actual climbable block detected");
            for (var p : actors) { tick(p); absent(h, p); }
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void acceptedShiftDoesNotRequireOnGroundOrCrouchingPose(GameTestHelper h) {
        var p=player(h,"austringer");tick(p);p.setOnGround(false);p.setPose(Pose.STANDING);p.setShiftKeyDown(true);
        tick(p);check(h,WeaponAiming.progress(p)==0&&!WeaponAiming.requested(p),"Shift alone never requests ADS");
        ads(p,true);
        h.runAfterDelay(1,()->{
            check(h,!p.onGround()&&!p.isCrouching(),"Left-click ADS does not require grounded or crouch pose");
            tick(p);nativeSpeed(h,p,.75);near(h,speed(p).getValue(),.1*zoomed(p,.75),"Only native attribute value is asserted, not airborne travel");
            near(h,sneak(p).getValue(),.3,"Shift keeps ordinary crouch slowdown");
        });
        h.runAfterDelay(3,()->{ads(p,false);tick(p);defaults(h,p,.1);h.succeed();});
    }

    @GameTest(structure = FLOOR, maxTicks = 12, environment = "destiny-test:w90_isolated")
    public void nativeServerSynchronizerSendsBothRatiosAndTheirRestorationWithoutHeldTickResends(GameTestHelper h) {
        var ids=List.of("austringer","allied_demand","seventh_seraph_officer_revolver");
        var actors=new ArrayList<ServerPlayer>();var trackers=new ArrayList<ServerEntity>();
        double[] previous={1,1,1};
        for(String id:ids){var p=player(h,id);tick(p);actors.add(p);TestPlayers.drain(p);p.getAttributes().getAttributesToSync().clear();
            trackers.add(new ServerEntity(p.level(),p,UpdateInterval.periodic(1),false,CameraViews.synchronizer(packet->p.connection.send(packet))));ads(p,true);}
        for(int i=1;i<=11;i++){int elapsed=i;h.runAfterDelay(i,()->{
            for(int j=0;j<actors.size();j++){
                var p=actors.get(j);if(elapsed==11)ads(p,false);tick(p);
                double scalar=elapsed==11?1:zoomed(p,expected(entry(ids.get(j))));
                trackers.get(j).sendChanges();var packets=TestPlayers.outbound(p).stream().filter(ClientboundUpdateAttributesPacket.class::isInstance).map(ClientboundUpdateAttributesPacket.class::cast).toList();
                if(Double.compare(scalar,previous[j])==0)check(h,packets.isEmpty(),"Stable full ADS emits no native attribute resend");
                else {
                    check(h,packets.size()==1&&packets.getFirst().getEntityId()==p.getId(),"Exactly one real player attribute update per changed native zoom sample");
                    var values=packets.getFirst().getValues();
                    check(h,values.stream().noneMatch(v->v.attribute().equals(SNEAKING_SPEED)),"No retired sneak neutralizer on wire");
                    var value=values.stream().filter(v->v.attribute().equals(MOVEMENT_SPEED)).findFirst().orElseThrow();
                    near(h,value.base(),.1,"Wire retains native base");var mod=value.modifiers().stream().filter(v->v.id().equals(SPEED_ID)).findFirst();
                    if(elapsed==11)check(h,mod.isEmpty(),"Release packet removes owned speed modifier");
                    else {check(h,mod.isPresent()&&mod.orElseThrow().operation()==ADD_MULTIPLIED_TOTAL,"Native zoom modifier encoded");near(h,mod.orElseThrow().amount(),scalar-1,"Wire carries independently calculated zoom ratio");}
                }
                previous[j]=scalar;
            }
            if(elapsed==11)h.succeed();
        });}
    }

    /** Explicit missing-attribute fixture only; production never replaces an AttributeMap. */
    private static void attributeMapFixture(ServerPlayer p, AttributeMap attributes) {
        try {
            var field = LivingEntity.class.getDeclaredField("attributes"); field.setAccessible(true); field.set(p, attributes);
        } catch (ReflectiveOperationException e) { throw new AssertionError("Cannot install missing-attribute fixture", e); }
    }
    @GameTest(structure = FLOOR, maxTicks = 10, environment = "destiny-test:w90_isolated")
    public void eitherMissingAttributeIsHarmlessAndCannotInstallHalfAPair(GameTestHelper h) throws ReflectiveOperationException {
        // A real player must have MOVEMENT_SPEED: Aiming.tick calls vanilla setSprinting before
        // reaching movement. Exercise the movement component's explicit nullable-attribute guard
        // directly, without inventing a null-safe vanilla player or modifying production visibility.
        var type = Class.forName("kim.biryeong.destiny.weapon.WeaponAimMovement");
        var constructor = type.getDeclaredConstructor(ServerPlayer.class); constructor.setAccessible(true);
        var update = type.getDeclaredMethod("update", WeaponCatalog.Entry.class, boolean.class, float.class); update.setAccessible(true);
        var release = type.getDeclaredMethod("release"); release.setAccessible(true);
        for (Holder<Attribute> remaining : List.of(MOVEMENT_SPEED, SNEAKING_SPEED)) {
            var p = player(h, "austringer"); var original = p.getAttributes();
            var partial = new AttributeMap(new AttributeSupplier.Builder().add(remaining, remaining.equals(MOVEMENT_SPEED) ? .1 : .3).build());
            attributeMapFixture(p, partial);
            Object movement = null;
            try {
                movement = constructor.newInstance(p);
                for (float progress : new float[]{.25f, 1f}) {
                    update.invoke(movement, entry("austringer"), true, progress);
                    if (remaining.equals(MOVEMENT_SPEED)) {
                        var modifier = speed(p).getModifier(SPEED_ID);
                        check(h, modifier != null && modifier.operation() == ADD_MULTIPLIED_TOTAL
                                        && !speed(p).getPermanentModifiers().contains(modifier),
                                "Native zoom needs only movement; missing sneak still installs the transient total multiplier");
                        double scalar = (1 - (double)progress) + progress * (.75 / Math.max(1, WeaponAimProfile.of(entry("austringer")).zoom()));
                        near(h, modifier.amount(), scalar - 1, "Available speed receives exact partial/full native zoom");
                        near(h, speed(p).getBaseValue(), .1, "Native movement base survives direct update");
                    } else {
                        check(h, p.getAttribute(remaining).getModifiers().isEmpty(), "Missing movement fails closed without touching sneak");
                        near(h, sneak(p).getValue(), .3, "Missing movement preserves native crouch value");
                    }
                }
                release.invoke(movement); release.invoke(movement);
                check(h, p.getAttribute(remaining).getModifiers().isEmpty(), "Repeated direct cleanup is harmless with either missing attribute");
                check(h, !WeaponAiming.requested(p) && WeaponAiming.progress(p) == 0,
                        "Component boundary fixture never fabricates an actual ADS session");
            } finally {
                try { if (movement != null) release.invoke(movement); }
                finally { attributeMapFixture(p, original); }
            }
        }
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 10)
    public void isolatedAimingClearRemovesAimingOnlyPairsAndPreservesForeignTakeover(GameTestHelper h) {
        var owned = player(h, "austringer"); var foreign = player(h, "allied_demand");
        // Intentionally only Aiming.tick: never Runtime.tickPlayer/beginUse, so no Runtime.State exists.
        ads(owned, true); ads(foreign, true); WeaponAiming.tick(owned); WeaponAiming.tick(foreign);
        nativeSpeed(h, owned, .75); nativeSpeed(h, foreign, .85);
        var replacement = modifier(SPEED_ID, -.12); speed(foreign).removeModifier(SPEED_ID); speed(foreign).addPermanentModifier(replacement);
        WeaponAiming.clear(); WeaponAiming.clear(); defaults(h, owned, .1);
        check(h, speed(foreign).getModifier(SPEED_ID) == replacement && speed(foreign).getPermanentModifiers().contains(replacement)
                && !sneak(foreign).hasModifier(SNEAK_ID), "Aiming clear preserves foreign permanent speed takeover and leaves crouch untouched");
        h.succeed();
    }

    @GameTest(structure = FLOOR, environment = GLOBAL, maxTicks = 10)
    public void isolatedRuntimeClearAllCleansAimingOnlySessionsWithoutBeginUse(GameTestHelper h) {
        var owned = player(h, "austringer"); var foreign = player(h, "allied_demand");
        ads(owned, true); ads(foreign, true); WeaponAiming.tick(owned); WeaponAiming.tick(foreign);
        nativeSpeed(h, owned, .75); nativeSpeed(h, foreign, .85);
        var replacement = modifier(SNEAK_ID, .12); sneak(foreign).removeModifier(SNEAK_ID); sneak(foreign).addTransientModifier(replacement);
        WeaponRuntime.clearAll(); WeaponRuntime.clearAll(); defaults(h, owned, .1);
        check(h, sneak(foreign).getModifier(SNEAK_ID) == replacement && !speed(foreign).hasModifier(SPEED_ID),
                "Global cleanup retires Aiming-only speed and preserves foreign sneak identity");
        h.succeed();
    }
}
