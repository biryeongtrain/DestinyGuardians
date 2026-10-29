package kim.biryeong.destiny.test;

import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;

/** Real held stacks, ADS sessions, ammunition, hitscan damage and projectile launch paths. */
public final class WeaponAccuracyW241GameTests {
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static ServerPlayer player(GameTestHelper h, String id) {
        var p = TestPlayers.create(h, new Vec3(2.5, 4, 6.5), -90, 0);
        p.setNoGravity(true); p.setOnGround(true); p.setAttached(WeaponLoadout.ENABLED, false);
        p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(entry(id)));
        TestCleanup.register(h, () -> { WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static void tickAds(GameTestHelper h, ServerPlayer p) {
        p.setShiftKeyDown(true);
        for (int i=1;i<=12;i++) h.runAfterDelay(i, () -> WeaponRuntime.tickPlayer(p));
    }
    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void firstHipShotRandomizesAndInspectionNeverChangesStackOrRandomState(GameTestHelper h) {
        var p=player(h,"austringer"); WeaponRuntime.tickPlayer(p);
        var data=p.getMainHandItem().get(DataComponents.CUSTOM_DATA);
        long seed=241;
        p.getRandom().setSeed(seed); Vec3 expected=WeaponAiming.direction(p);
        p.getRandom().setSeed(seed);
        for(int i=0;i<20;i++) WeaponAiming.coneDegrees(p);
        check(h,WeaponAiming.direction(p).equals(expected),"Pure inspection consumes no RNG");
        check(h,WeaponAiming.bloom(p)==0 && expected.distanceToSqr(p.getLookAngle())>1e-9,"First hip ray spreads before bloom");
        check(h,!WeaponAiming.direction(p).equals(expected),"Consecutive rays are random rather than a fixed offset");
        check(h,data.equals(p.getMainHandItem().get(DataComponents.CUSTOM_DATA)),"Sampling never edits item components");
        check(h,WeaponAccuracy.of(entry("beloved")).hipDegrees()>WeaponAccuracy.of(entry("the_recluse")).hipDegrees(),"Weapon families have distinct hip spread");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=35, environment="destiny-test:w90_isolated")
    public void realAirAdsHasPenaltyUntilOneHundredAndHipPenaltyRemains(GameTestHelper h) {
        var p=player(h,"ace_of_spades"); tickAds(h,p);
        h.runAfterDelay(13,()->{
            check(h,WeaponAiming.progress(p)==1,"Real ADS completed");
            p.setOnGround(false);
            check(h,WeaponAccuracy.baseAirborne(entry("ace_of_spades"))==14,"Official baseAE14");
            check(h,WeaponAiming.coneDegrees(p)>0,"Air ADS has spread with base AE");
            WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),85);
            check(h,WeaponAccuracy.airborne(entry("ace_of_spades"),p.getMainHandItem())==99 && WeaponAiming.coneDegrees(p)>0,"AE99 still has air penalty");
            WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),86);
            for(int i=0;i<20;i++)check(h,WeaponAiming.direction(p).equals(p.getLookAngle().normalize()),"AE100 air ADS is exact");
            WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),200);
            check(h,WeaponAiming.coneDegrees(p)==0,"AE above100 also exact");
            WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),0);p.setOnGround(true);
            check(h,WeaponAiming.coneDegrees(p)==0,"Ground ADS has no additional spread");
            WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),200);p.setOnGround(false);
            WeaponAiming.suspend(p);
            check(h,WeaponAiming.coneDegrees(p)>0,"AE100 never removes hip penalty"); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void airborneStatSurvivesAmmoSaveAndMeleeStaysNeutral(GameTestHelper h) {
        var p=player(h,"seventh_seraph_officer_revolver");var stack=p.getMainHandItem();
        check(h,WeaponAccuracy.frameAirborne(entry("seventh_seraph_officer_revolver"))==25,"Precision HC intrinsic separate from base");
        WeaponAccuracy.setAirborneBonus(stack,40);
        var profile=WeaponProfile.forEntry(entry("seventh_seraph_officer_revolver"));
        var ammo=WeaponItems.magazine(stack,profile); ammo.consume();WeaponItems.save(stack,ammo);
        check(h,WeaponAccuracy.airborneBonus(stack)==40,"Ammo save preserves AE customization");
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponItems.create(entry("abide_the_return")));p.setOnGround(false);
        check(h,!WeaponAccuracy.setAirborneBonus(p.getMainHandItem(),100),"Sword has no invented AE stat");
        check(h,WeaponAiming.direction(p).equals(p.getLookAngle().normalize()),"Sword targeting neutral");
        int count=0;
        for(var e:WeaponCatalog.all())if(WeaponAccuracy.supports(e)) {WeaponAccuracy.baseAirborne(e);WeaponAccuracy.of(e);count++;}
        check(h,count==60,"All60 actual ranged entries wired");h.succeed();
    }
    @GameTest(structure="destiny-test:w78_floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void paidHitscanUsesRandomizedAxisAndConsumesOneRound(GameTestHelper h) {
        var p=player(h,"beloved");WeaponRuntime.tickPlayer(p);
        Vec3 direction=null;long seed=0;
        for(;seed<1000;seed++) {
            p.getRandom().setSeed(seed);direction=WeaponAiming.direction(p);
            if(Math.abs(direction.z*10)>.6)break;
        }
        check(h,seed<1000,"Choose an off-axis hip ray");
        var point=p.getEyePosition().add(direction.scale(10));
        // Spawn in the final spatial section rather than moving a freshly spawned entity before its first tick.
        var relative=point.subtract(h.absoluteVec(Vec3.ZERO)).add(0,-.45,0);
        var target=h.spawn(EntityTypes.PIG,relative);
        target.setNoAi(true);target.setNoGravity(true);
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);target.setHealth(1000);
        TestCleanup.register(h,target::discard);
        var profile=WeaponProfile.forEntry(entry("beloved"));int before=WeaponItems.magazine(p.getMainHandItem(),profile).rounds();
        var block=h.getLevel().clip(new net.minecraft.world.level.ClipContext(p.getEyePosition(),point,
                net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,p));
        check(h,block.getType()==net.minecraft.world.phys.HitResult.Type.MISS,"Fixture firing corridor clear: " + block.getLocation());
        p.getRandom().setSeed(seed);
        check(h,WeaponRuntime.beginUse(p),"Actual trigger accepted");
        check(h,target.getHealth()<1000,"Actual hitscan hits randomized off-axis target; seed="+seed+" expected="+direction+" eye="+p.getEyePosition()+" target="+target.getBoundingBox()+" ammo="+WeaponItems.magazine(p.getMainHandItem(),profile).rounds());
        check(h,WeaponItems.magazine(p.getMainHandItem(),profile).rounds()==before-1,"Exactly one paid round");h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=35, environment="destiny-test:w90_isolated")
    public void paidProjectileLaunchUsesAirAdsDispersionAndHundredIsExact(GameTestHelper h) {
        var low=player(h,"bad_omens");var high=player(h,"bad_omens");
        WeaponAccuracy.setAirborneBonus(high.getMainHandItem(),200);tickAds(h,low);tickAds(h,high);
        h.runAfterDelay(13,()->{
            low.setOnGround(false);high.setOnGround(false);
            Vec3 a=low.getLookAngle().normalize(),b=high.getLookAngle().normalize();
            check(h,WeaponRuntime.beginUse(low)&&WeaponRuntime.beginUse(high),"Both real rocket triggers accepted");
            var l=WeaponRuntime.flights(low);var r=WeaponRuntime.flights(high);
            check(h,l.size()==1&&r.size()==1,"Two owned paid flights exist");
            check(h,l.getFirst().velocity().normalize().distanceToSqr(a)>1e-12,"LowAE airADS rocket deviates");
            check(h,r.getFirst().velocity().normalize().distanceToSqr(b)<1e-24,"AE100 airADS rocket launches exactly forward");h.succeed();
        });
    }
}
