package kim.biryeong.destiny.test;

import kim.biryeong.destiny.input.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.tutorial.*;
import kim.biryeong.gcbserver.events.PlayerKeyStateChangedEvent;
import kim.biryeong.gcbserver.player.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.phys.Vec3;

/** Real registered GCB callback and combat state; native-client evidence is recorded separately. */
public final class WeaponInputW283GameTests {
    private static void check(GameTestHelper h, boolean b, String message) { h.assertTrue(b, Component.literal(message)); }
    private static ServerPlayer equip(GameTestHelper h, String id, boolean gcb) {
        var p = TestPlayers.create(h, new Vec3(2.5, 2, 6.5), -90, 0);
        p.setOnGround(true);
        WeaponAccessibility.setEnabled(p, false);
        p.setItemInHand(InteractionHand.MAIN_HAND, WeaponItems.create(WeaponCatalog.find(id).orElseThrow()));
        WeaponHandling.update(p);
        if (gcb) { ((GCBPlayer)p).gcb$markHasMod(); ((GCBPlayer)p).gcb$setModVersion("4.2.0"); }
        TestCleanup.register(h, () -> { TutorialLoan.restore(p); WeaponRuntime.cleanup(p); ClientControls.forget(p); TestPlayers.remove(p); });
        return p;
    }
    private static void key(ServerPlayer p, Key key, boolean pressed) {
        PlayerKeyStateChangedEvent.EVENT.invoker().onKeyStateChanged(p, pressed, key);
    }
    private static int rounds(ServerPlayer p) {
        return WeaponItems.magazine(p.getMainHandItem(), WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow())).rounds();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=50, environment="destiny-test:w90_isolated")
    public void independentButtonsAndVanillaFallback(GameTestHelper h) {
        var p = equip(h,"austringer",true);
        int full = rounds(p);
        key(p,Key.KEY_USE,true);
        check(h,WeaponAiming.requested(p),"GCB right press requests ADS");
        check(h,WeaponRuntime.triggerHeld(p),"ADS-only hold blocks tutorial equipment handoff");
        WeaponCombatItem.INSTANCE.use(p.level(),p,InteractionHand.MAIN_HAND);
        check(h,rounds(p)==full,"Native right use cannot fire GCB weapon");
        key(p,Key.KEY_ATTACK,true);
        check(h,rounds(p)==full-1,"GCB left press fires one round");
        InputRouter.onPunch(p); key(p,Key.KEY_ATTACK,true);
        check(h,rounds(p)==full-1 && WeaponAiming.requested(p),"Punch and repeated key press do not double fire or toggle ADS");
        key(p,Key.KEY_USE,false);
        check(h,!WeaponAiming.requested(p) && GcbWeaponInput.firing(p,p.getMainHandItem()),"Right release leaves independent fire hold");
        key(p,Key.KEY_ATTACK,false);
        check(h,!WeaponRuntime.triggerHeld(p) && !GcbWeaponInput.buttonsDown(p),"Handoff becomes safe only after both buttons release");
        var v = equip(h,"austringer",false);
        int before = rounds(v);
        InputRouter.onPunch(v);
        check(h,WeaponAiming.requested(v),"Vanilla left still toggles ADS");
        WeaponCombatItem.INSTANCE.use(v.level(),v,InteractionHand.MAIN_HAND);
        check(h,rounds(v)==before-1,"Vanilla right still fires");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void bowReleaseAndCancellation(GameTestHelper h) {
        var p=equip(h,"biting_winds",true); int full=rounds(p);
        key(p,Key.KEY_ATTACK,true); key(p,Key.KEY_USE,true);
        h.runAfterDelay(25,()->{
            WeaponRuntime.tickPlayer(p);
            key(p,Key.KEY_USE,false);
            WeaponCombatItem.INSTANCE.releaseUsing(p.getMainHandItem(),p.level(),p,0);
            check(h,rounds(p)==full,"Right/native release cannot release left-owned bow");
            WeaponRuntime.cancelUseForSkill(p);
            key(p,Key.KEY_ATTACK,false);
            check(h,rounds(p)==full,"Canceled bow release fires nothing");
            key(p,Key.KEY_ATTACK,true);
        });
        h.runAfterDelay(55,()->{
            WeaponRuntime.tickPlayer(p); key(p,Key.KEY_ATTACK,false);
            check(h,rounds(p)==full-1,"Fresh left release fires the drawn bow once"); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=100, environment="destiny-test:w90_isolated")
    public void automaticHoldAndSameTickSlotCancellation(GameTestHelper h) {
        var p=equip(h,"ammit_ar2",true); int full=rounds(p);
        key(p,Key.KEY_ATTACK,true);
        for(int i=1;i<=30;i++) h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(31,()->{
            check(h,rounds(p)<full-2,"GCB hold repeats automatic fire without vanilla use session");
            int before=rounds(p);
            WeaponRuntime.selectedSlotChanging(p,1);
            p.getInventory().setSelectedSlot(1);
            WeaponRuntime.selectedSlotChanging(p,0);
            p.getInventory().setSelectedSlot(0);
            key(p,Key.KEY_ATTACK,true); WeaponRuntime.tickPlayer(p);
            check(h,rounds(p)==before && !GcbWeaponInput.firing(p,p.getMainHandItem()),"Away/back and duplicate pressed cannot revive old hold");
            key(p,Key.KEY_ATTACK,false); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=120, environment="destiny-test:w90_isolated")
    public void rejectedReloadPreservesValidCharge(GameTestHelper h) {
        var p=equip(h,"hollow_words",true); int full=rounds(p);
        key(p,Key.KEY_ATTACK,true);
        check(h,!WeaponRuntime.reload(p),"Full fusion cannot reload");
        check(h,GcbWeaponInput.firing(p,p.getMainHandItem()),"Rejected reload keeps original trigger ownership");
        key(p,Key.KEY_ATTACK,false);
        check(h,rounds(p)==full,"Early release spends no fusion ammo");
        key(p,Key.KEY_ATTACK,true);
        for(int i=1;i<=65;i++) h.runAfterDelay(i,()->WeaponRuntime.tickPlayer(p));
        h.runAfterDelay(66,()->{ check(h,rounds(p)<full,"Fresh fusion charge finishes normally"); key(p,Key.KEY_ATTACK,false); h.succeed(); });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=340, environment="destiny-test:w90_isolated")
    public void lostReleaseExpiresWithoutBowShot(GameTestHelper h) {
        var p=equip(h,"biting_winds",true); int full=rounds(p);
        key(p,Key.KEY_ATTACK,true);
        h.runAfterDelay(GcbWeaponInput.MAX_FIRE_HOLD_TICKS+1,()->{
            WeaponRuntime.tickPlayer(p);
            check(h,!GcbWeaponInput.firing(p,p.getMainHandItem()) && rounds(p)==full,"Missing release expires without firing a bow");
            key(p,Key.KEY_ATTACK,true); key(p,Key.KEY_ATTACK,false);
            check(h,rounds(p)==full,"Late release after expiration cannot fire"); h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=220, environment="destiny-test:w90_isolated")
    public void reloadDoesNotTurnHeldSemiautoIntoAnotherPress(GameTestHelper h) {
        var semi=equip(h,"austringer",true);
        var auto=equip(h,"ammit_ar2",true);
        for(var p:new ServerPlayer[]{semi,auto}) {
            var profile=WeaponProfile.forEntry(WeaponItems.entry(p.getMainHandItem()).orElseThrow());
            WeaponItems.save(p.getMainHandItem(),new WeaponMagazine(profile,1,profile.reserve()));
            key(p,Key.KEY_ATTACK,true);
        }
        for(int i=1;i<=160;i++) h.runAfterDelay(i,()->{WeaponRuntime.tickPlayer(semi);WeaponRuntime.tickPlayer(auto);});
        h.runAfterDelay(161,()->{
            int full=WeaponProfile.forEntry(WeaponItems.entry(semi.getMainHandItem()).orElseThrow()).magazine();
            check(h,rounds(semi)==full && !WeaponRuntime.reloading(semi),"Held semiauto reloads then waits for a fresh press");
            int autoFull=WeaponProfile.forEntry(WeaponItems.entry(auto.getMainHandItem()).orElseThrow()).magazine();
            check(h,rounds(auto)<autoFull,"Automatic hold resumes after shot-caused reload");
            key(semi,Key.KEY_ATTACK,false);key(auto,Key.KEY_ATTACK,false);h.succeed();
        });
    }
    @GameTest(structure="destiny-test:floor", maxTicks=30, environment="destiny-test:w90_isolated")
    public void glaiveProjectileAndSwordKeepDistinctActions(GameTestHelper h) {
        var glaive=equip(h,"nezarec_s_whisper",true);int full=rounds(glaive);
        key(glaive,Key.KEY_ATTACK,true);
        check(h,rounds(glaive)==full-1,"GCB glaive left fires its paid projectile");
        key(glaive,Key.KEY_ATTACK,false);key(glaive,Key.KEY_USE,true);
        check(h,!WeaponAiming.requested(glaive),"Glaive has melee instead of nonexistent ADS");
        var sword=equip(h,"abide_the_return",true);
        check(h,!GcbWeaponInput.remapped(sword),"Sword keeps original native light/heavy controls");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor", maxTicks=40, environment="destiny-test:w90_isolated")
    public void arsenalRestoresExactEquipmentAndAllFamilies(GameTestHelper h) {
        var p=equip(h,"austringer",false);
        p.getInventory().setItem(1,new ItemStack(Items.DIAMOND,7));
        p.getInventory().setItem(2,ItemStack.EMPTY);
        var saved=p.getMainHandItem().copy();
        var families=new java.util.HashSet<String>();
        for(var lesson:TutorialArsenal.LESSONS) {
            check(h,families.add(lesson.family()) && lesson.weapon().family().equals(lesson.family()),"Unique real representative for "+lesson.family());
            TutorialLoan.equip(p,lesson.weapon());
            check(h,TutorialLoan.borrowed(p,p.getMainHandItem()) && WeaponLoadout.canUse(p),"Usable owned loan "+lesson.id());
        }
        check(h,families.equals(WeaponCatalog.all().stream().map(WeaponCatalog.Entry::family).collect(java.util.stream.Collectors.toSet())),"Every implemented family is taught exactly once");
        p.getInventory().setItem(8,new ItemStack(Items.EMERALD,3));
        TutorialLoan.restore(p); TutorialLoan.restore(p);
        check(h,ItemStack.matches(saved,p.getInventory().getItem(0)),"Original weapon, perks and ammo restored exactly");
        check(h,p.getInventory().getItem(1).is(Items.DIAMOND) && p.getInventory().getItem(1).getCount()==7,"Unrelated original slot restored");
        check(h,p.getInventory().getItem(2).isEmpty() && !TutorialLoan.active(p),"Empty slot restored and escrow retired idempotently");
        check(h,p.getInventory().getItem(8).getCount()==3,"Items acquired during training preserved");
        for(int i=0;i<p.getInventory().getContainerSize();i++) check(h,!TutorialLoan.borrowed(p,p.getInventory().getItem(i)),"No loan survives restoration");
        h.succeed();
    }
}
