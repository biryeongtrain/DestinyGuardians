package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.fx.WeaponDamageNumbers;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;

/** Actual weapon transactions, not just math or a predicted hit counter. */
public final class WeaponBallisticsW43GameTests {
    private static void check(GameTestHelper h, boolean condition, String message) { h.assertTrue(condition, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.create(h, new Vec3(2.5, 1, z), -90, 0);
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); }); return p;
    }
    private static Husk target(GameTestHelper h, double x, double y, double z) {
        var e = h.spawn(EntityTypes.HUSK, new Vec3(x, y, z));
        e.setNoAi(true); e.setNoGravity(true); e.setPersistenceRequired();
        e.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        e.getAttribute(Attributes.ARMOR).setBaseValue(0);
        e.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); e.setHealth(1000);
        TestCleanup.register(h, e::discard); return e;
    }
    private static void equip(ServerPlayer p, String id) {
        var gun = WeaponItems.create(WeaponCatalog.find(id).orElseThrow());
        WeaponAccuracy.setAirborneBonus(gun, 100);
        p.setItemInHand(InteractionHand.MAIN_HAND, gun);
    }
    /** W241 exact-impact fixture: earn ADS on real ticks, with explicit per-stack AE.
     * No RNG replacement, production tuning change, or synthetic server clock. */
    private static void exactAim(GameTestHelper h, java.util.List<ServerPlayer> owners, Runnable action) {
        for (var p : owners) {
            var gun = p.getMainHandItem();
            check(h, kim.biryeong.destiny.weapon.WeaponAccuracy.airborne(WeaponItems.entry(gun).orElseThrow(), gun) == 100, "Fixture explicitly equips AE100");
            WeaponRuntime.tickPlayer(p);
            if (!WeaponAiming.requested(p)) check(h, WeaponAiming.toggle(p), "Real ADS toggle accepted");
        }
        // GameTestInfo executes sequences after iterating its fastutil callback map.
        // The final action may register follow-up deadlines, so it must run here.
        var sequence = h.startSequence();
        for (int tick = 1; tick <= 40; tick++) {
            final int age = tick;
            sequence.thenExecuteAfter(1, () -> {
                for (var p : owners) {
                    WeaponRuntime.tickPlayer(p);
                    // Initial handling can consume ADS. A later actual click earns it after ready.
                    if (!WeaponAiming.requested(p) && age % 4 == 0) WeaponAiming.toggle(p);
                }
                if (age == 40) {
                    for (var p : owners) check(h, WeaponAiming.progress(p) == 1
                                    && WeaponAiming.coneDegrees(p) == 0,
                            "Fully earned ADS and AE100 give an exact ray before any paid shot");
                    action.run();
                }
            });
        }
    }

    private static void use(GameTestHelper h, ServerPlayer p) { p.gameMode.useItem(p, h.getLevel(), p.getMainHandItem(), InteractionHand.MAIN_HAND); }
    private static boolean near(float a, float b) { return Math.abs(a - b) < .001; }
    private static TextDisplayElement number(ServerPlayer owner) {
        try {
            var field=WeaponDamageNumbers.class.getDeclaredField("NUMBERS");field.setAccessible(true);
            for(var value:(Iterable<?>)field.get(null)) {
                var owned=value.getClass().getDeclaredField("owner");owned.setAccessible(true);
                if(owned.get(value)==owner)return (TextDisplayElement)((ElementHolder)value).getElements().getFirst();
            }
            throw new AssertionError("No actual owned damage display");
        } catch(ReflectiveOperationException e) {throw new AssertionError(e);}
    }

    @GameTest(structure="destiny-test:floor", maxTicks=70, environment = "destiny-test:w90_isolated")
    public void actualHeadAndBodyDamageDifferAndOnlyConfirmedLossCreatesNumbers(GameTestHelper h) {
        var head = player(h, 4.5); var body = player(h, 8.5);
        var a = target(h, 8.5, 1, 4.5); var b = target(h, 8.5, 1.8, 8.5);
        equip(head, "austringer"); equip(body, "austringer");
        // AE100 removes the airborne term, not W241's independent hip cone.
        // Earn actual ADS before asserting exact head/body damage and feedback.
        exactAim(h, java.util.List.of(head, body), () -> {
            var owners = java.util.List.of(head, body);
            var targets = java.util.List.of(a, b);
            int[] rounds = new int[2], reserves = new int[2];
            for (int i = 0; i < owners.size(); i++) {
                var p = owners.get(i); var target = targets.get(i);
                var box = target.getBoundingBox(); var from = p.getEyePosition();
                var surface = box.clip(from, from.add(p.getLookAngle().normalize().scale(12)));
                check(h, surface.isPresent(), "Exact firing axis intersects the actual target body");
                var contact = surface.orElseThrow();
                double headBoundary = box.maxY - box.getYsize() * .25;
                check(h, i == 0 ? contact.y > headBoundary + .1 : contact.y < headBoundary - .1,
                        "Independent actual-AABB contact lies safely inside the intended head/body region: " + contact);
                check(h, h.getLevel().clip(new net.minecraft.world.level.ClipContext(from, contact,
                                net.minecraft.world.level.ClipContext.Block.COLLIDER,
                                net.minecraft.world.level.ClipContext.Fluid.NONE, p)).getType()
                                == net.minecraft.world.phys.HitResult.Type.MISS,
                        "Fixture firing lane has no intervening block collider");
                var gun = p.getMainHandItem(); var entry = WeaponItems.entry(gun).orElseThrow();
                var ammo = WeaponItems.magazine(gun, WeaponProfile.forEntry(entry));
                rounds[i] = ammo.rounds(); reserves[i] = ammo.reserve();
                check(h, from.distanceTo(contact) < WeaponAiming.ballistics(p, entry).start(),
                        "Both contacts precede damage falloff");
                check(h, target.getHealth() == 1000 && target.getAbsorptionAmount() == 0
                                && WeaponDamageNumbers.active(p) == 0,
                        "Full-health unshielded witness and no prior feedback before the paid shot");
            }
            use(h, head); use(h, body);
            check(h, near(1000-a.getHealth(), 10.5f) && near(1000-b.getHealth(), 7),
                    "Head1.5x/body1x actual HP; head loss=" + (1000-a.getHealth()) + ", body loss=" + (1000-b.getHealth()));
            for (int i = 0; i < owners.size(); i++) {
                var gun = owners.get(i).getMainHandItem();
                var ammo = WeaponItems.magazine(gun, WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow()));
                check(h, ammo.rounds() == rounds[i] - 1 && ammo.reserve() == reserves[i],
                        "Each actual head/body transaction costs exactly one round with unchanged reserve");
            }
            check(h, WeaponDamageNumbers.active(head)==1 && WeaponDamageNumbers.active(body)==1, "Actual damage creates owned feedback");
            check(h,number(head).getText().getString().equals("11") && number(body).getText().getString().equals("7"),"Numbers round observed HP, not original damage units");
            check(h,number(head).getText().getStyle().getColor().getValue()==0xffff55
                    && number(body).getText().getStyle().getColor().getValue()==0xffffff,"Confirmed precision yellow, body white");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void absorptionDisablesPrecisionAndNumbersIncludeOnlyObservedShieldLoss(GameTestHelper h) {
        var p = player(h, 6.5); var e = target(h, 8.5, 1, 6.5);
        e.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(50);e.setAbsorptionAmount(50); equip(p, "austringer");
        use(h, p);
        check(h, e.getHealth()==1000 && near(e.getAbsorptionAmount(),43), "Shield absorbs body damage, not precision bonus");
        check(h, WeaponDamageNumbers.active(p)==1, "Confirmed absorption decrease is feedback"); h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void wallMissAndInvulnerabilityCannotProduceFakeDamageNumbers(GameTestHelper h) {
        var wall = player(h, 3.5); var invulnerable = player(h, 7.5); var miss = player(h, 11.5);
        var a = target(h, 8.5, 1, 3.5); var b = target(h, 8.5, 1, 7.5); b.setPermanentlyInvulnerable(true);
        h.setBlock(5,1,3,Blocks.STONE);h.setBlock(5,2,3,Blocks.STONE);
        for (var p : new ServerPlayer[]{wall,invulnerable,miss}) { equip(p,"austringer");use(h,p);check(h,WeaponDamageNumbers.active(p)==0,"No actual HP loss, no number"); }
        check(h,a.getHealth()==1000 && b.getHealth()==1000,"Wall/invulnerability preserve target HP"); h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void precisionRequiresHumanoidExactSurfaceNotInflatedGrazeOrSlime(GameTestHelper h) {
        var e = target(h, 8.5, 1, 6.5); var box=e.getBoundingBox();
        Vec3 head=new Vec3(box.minX-.03,box.maxY-.2,e.getZ());
        check(h,WeaponPrecision.critical(e,head.add(-5,0,0),head,1.5),"Inflated frontal hit resolves exact head surface");
        Vec3 graze=new Vec3(box.minX-.02,box.maxY-.2,box.maxZ+.02);
        check(h,!WeaponPrecision.critical(e,graze.add(-5,0,0),graze,1.5),"Inflated-only graze is not a headshot");
        var slime=h.spawn(EntityTypes.SLIME,new Vec3(5.5,1,10.5));TestCleanup.register(h, slime::discard);
        check(h,!WeaponPrecision.critical(slime,slime.position().add(-5,.9,0),slime.position().add(0,.9,0),2),"Unlisted body is never an arbitrary humanoid weakspot");
        check(h,!WeaponPrecision.critical(e,e.position().add(0,1.8,0),e.position().add(.1,1.8,0),2),"Origin inside body cannot earn precision");h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void babyHeadRegionUsesActualDimensions(GameTestHelper h) {
        var e=target(h,8.5,1,6.5);e.setBaby(true);var box=e.getBoundingBox();
        Vec3 head=new Vec3(box.minX-.03,box.maxY-box.getYsize()*.1,e.getZ());
        Vec3 body=new Vec3(box.minX-.03,box.minY+box.getYsize()*.5,e.getZ());
        check(h,WeaponPrecision.critical(e,head.add(-5,0,0),head,1.5),"Baby head scales to actual AABB");
        check(h,!WeaponPrecision.critical(e,body.add(-5,0,0),body,1.5),"Baby body is not a full-body headshot");h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=70, skyAccess=true, environment = "destiny-test:w90_isolated")
    public void hitscanBeyondOldCutoffStillDealsFlooredDamageWithoutUnboundedReach(GameTestHelper h) {
        // Vertical, no-gravity fixtures avoid neighboring horizontal test arenas.
        var p=player(h,6.5);p.setXRot(-90);var e=target(h,2.5,52,6.5);equip(p,"austringer");
        exactAim(h, java.util.List.of(p), () -> {
            check(h, e.getBoundingBox().minY - p.getEyeY() > WeaponAiming.ballistics(p,
                    WeaponCatalog.find("austringer").orElseThrow()).end(), "Far witness remains beyond ADS falloff end");
            use(h,p);
        check(h,near(1000-e.getHealth(),7*.33f),"50-block body hit survives former42-block hard stop at33% floor");
        check(h,WeaponDamageNumbers.active(p)==1,"Far confirmed hit creates a number");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, skyAccess=true, environment = "destiny-test:w90_isolated")
    public void targetsPast96BlockSafetyBoundCannotBeHit(GameTestHelper h) {
        var p=player(h,6.5);p.setXRot(-90);var e=target(h,2.5,102,6.5);equip(p,"beloved");use(h,p);
        check(h,e.getHealth()==1000 && WeaponDamageNumbers.active(p)==0,"Safety range bounded even on no-falloff sniper");h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=70, environment = "destiny-test:w90_isolated")
    public void mixedPelletsAggregateOnceAndSplitBodyAndPrecisionFeedback(GameTestHelper h) {
        var p=player(h,6.5);var e=target(h,5.5,1,6.5);equip(p,"dust_rock_blues");
        exactAim(h, java.util.List.of(p), () -> {
            // Put the top-quarter boundary .02 above the exact firing axis: the W105
            // vertical oval has five upper, two level and five lower pellets.
            // The level rays are deliberately below the boundary, never on an epsilon edge.
            var from=p.getEyePosition();
            e.setPos(e.getX(),from.y+.02-e.getBoundingBox().getYsize()*.75,e.getZ());
            var box=e.getBoundingBox();
            double[][] oval={{-.22,1},{.22,1},{.48,.48},{.61,0},{.48,-.48},{.22,-1},
                    {-.22,-1},{-.48,-.48},{-.61,0},{-.48,.48},{0,.32},{0,-.32}};
            var forward=p.getLookAngle().normalize();
            var right=forward.cross(Vec3.Y_AXIS).normalize();var up=right.cross(forward);
            int body=0,precision=0;
            // Literal W105 offsets and retained ADS tangent .12 * .65. Do not use
            // production pattern/precision helpers or observed damage as the oracle.
            for(var point:oval) {
                var ray=forward.add(right.scale(point[0]*.078)).add(up.scale(point[1]*.078)).normalize();
                var surface=box.clip(from,from.add(ray.scale(6)));
                check(h,surface.isPresent(),"Each of the twelve independent rays intersects the actual body");
                check(h,from.distanceTo(surface.orElseThrow())<3,"All pellet surfaces precede damage falloff");
                if(surface.orElseThrow().y>=box.maxY-box.getYsize()*.25)precision++;else body++;
            }
            check(h,body==7 && precision==5,"Independent geometry guarantees seven body and five precision pellets");
            var entry=WeaponCatalog.find("dust_rock_blues").orElseThrow();
            var profile=WeaponProfile.forEntry(entry);var gun=p.getMainHandItem();
            check(h,profile.pellets()==12 && near(profile.damage()*12,16)
                            && WeaponAiming.ballistics(p,entry).start()>3,
                    "Twelve pellets retain the 16 HP local body budget with no falloff in this fixture");
            int rounds=WeaponItems.magazine(gun,profile).rounds(),reserve=WeaponItems.magazine(gun,profile).reserve();
            use(h,p);
            float expected=(float)(16.0/12*(7+5*1.107843137254902));
            check(h,near(1000-e.getHealth(),expected),"Exact seven-body/five-precision aggregate HP loss");
            check(h,WeaponItems.magazine(gun,profile).rounds()==rounds-1
                            && WeaponItems.magazine(gun,profile).reserve()==reserve,"One paid shell, unchanged reserve");
            check(h,WeaponDamageNumbers.active(p)==2,"Mixed confirmed transaction generates two categories");
            mixedNumbers(h,p);
            h.succeed();
        });
    }

    private static void mixedNumbers(GameTestHelper h, ServerPlayer owner) {
        try {
            var field=WeaponDamageNumbers.class.getDeclaredField("NUMBERS");field.setAccessible(true);
            int white=0,yellow=0;
            for(var value:(Iterable<?>)field.get(null)) {
                var owned=value.getClass().getDeclaredField("owner");owned.setAccessible(true);
                if(owned.get(value)!=owner)continue;
                var text=(TextDisplayElement)((ElementHolder)value).getElements().getFirst();
                int color=text.getText().getStyle().getColor().getValue();
                if(color==0xffffff && text.getText().getString().equals("9"))white++;
                if(color==0xffff55 && text.getText().getString().equals("7"))yellow++;
            }
            check(h,white==1 && yellow==1,"One rounded body-9 white display and one precision-7 yellow display");
        } catch(ReflectiveOperationException ex) {throw new AssertionError(ex);}
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void slugHeadshotUsesSlugMultiplierWithoutPelletFan(GameTestHelper h) {
        var p=player(h,6.5);var e=target(h,5.5,1,6.5);equip(p,"first_in_last_out");use(h,p);
        float expected=(float)(13*(13/51.0+1.5));
        check(h,near(1000-e.getHealth(),expected),"Single slug headshot uses decoded multiplier");
        check(h,WeaponDamageNumbers.active(p)==1,"Single slug creates one number");h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=70, environment = "destiny-test:w90_isolated")
    public void bowProjectileKeepsOriginalPrecisionProfileAfterWeaponSwitch(GameTestHelper h) {
        var p=player(h,6.5);var e=target(h,8.5,1,6.5);equip(p,"biting_winds");use(h,p);
        h.runAfterDelay(17,()->{p.releaseUsingItem();check(h,WeaponRuntime.activeProjectiles(p)==1,"Charged arrow emitted");equip(p,"bad_omens");});
        h.runAfterDelay(22,()->{check(h,near(1000-e.getHealth(),16.5f),"In-flight bow retains original1.5x instead of new rocket profile");
            check(h,WeaponDamageNumbers.active(p)==1,"Projectile confirmed number");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor", maxTicks=70, environment = "destiny-test:w90_isolated")
    public void overkillNumberUsesActualLossRatherThanRequestedSniperDamage(GameTestHelper h) {
        var p=player(h,6.5);var e=target(h,8.5,1,6.5);e.setHealth(2);equip(p,"beloved");
        exactAim(h, java.util.List.of(p), () -> {
            use(h,p);
        check(h,e.isDeadOrDying() && e.getHealth()==0,"Lethal hit actually loses only2HP");
        check(h,WeaponDamageNumbers.active(p)==1 && number(p).getText().getString().equals("2"),"Confirmed number is actual2HP, not requested sniper overkill");h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=25, environment = "destiny-test:w90_isolated")
    public void distantNumberScaleMaintainsReadableAngularSizeAndStaysBounded(GameTestHelper h) {
        var near=player(h,4.5);var far=player(h,8.5);
        WeaponDamageNumbers.confirm(near,h.getLevel(),near.getEyePosition().add(0,7,0),7,false);
        WeaponDamageNumbers.confirm(far,h.getLevel(),far.getEyePosition().add(0,50,0),7,false);
        float n=number(near).getScale().x(),f=number(far).getScale().x();
        check(h,near(n,.65f)&&near(f,.65f*50/7),"7/50-block glyphs preserve approximately equal angular size");
        check(h,n>0&&f<9,"Scale remains within96-block runtime bound");h.succeed();
    }
}
