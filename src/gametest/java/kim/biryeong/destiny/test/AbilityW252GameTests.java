package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;

public final class AbilityW252GameTests {
    static { SkinLandmarksW254.register(); }
    private static kim.biryeong.minigamelib.displayhud.ItemDisplayHud view(ServerPlayer p,String part) {
        return (kim.biryeong.minigamelib.displayhud.ItemDisplayHud)
                kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).get("destiny:profile_view_"+part);
    }
    private static boolean hidden(ServerPlayer p,String part) {
        try {
            var method=net.minecraft.world.entity.Display.class.getDeclaredMethod("createTransformation",net.minecraft.network.syncher.SynchedEntityData.class);
            method.setAccessible(true);
            var transform=(com.mojang.math.Transformation)method.invoke(null,view(p,part).getDisplay().getEntityData());
            return transform.scale().lengthSquared()==0;
        } catch (ReflectiveOperationException error) {throw new AssertionError(error);}
    }
    private static void viewOperation(ServerPlayer p,String operation) {
        // TestPlayers are level entities, not connected PlayerList members.
        // Exercise the real HUD updater explicitly; this is not framebuffer evidence.
        try {
            var method=kim.biryeong.destiny.weapon.ProfileWeaponView.class.getDeclaredMethod(operation,ServerPlayer.class);
            method.setAccessible(true);method.invoke(null,p);
        } catch (ReflectiveOperationException error) {throw new AssertionError(error);}
    }
    private static net.minecraft.world.item.ItemStack armWeapon(ServerPlayer p,String id) {
        var gun=kim.biryeong.destiny.weapon.WeaponItems.create(kim.biryeong.destiny.weapon.WeaponCatalog.find(id).orElseThrow());
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gun);return gun;
    }
    private static void profileReady(GameTestHelper h, Runnable action) {
        // Headless SERVER_STARTED releases AutoHost generation through StartupPackCoordinator;
        // compact() publishes graphs atomically after successful profile/pose preparation.
        check(h, net.fabricmc.loader.api.FabricLoader.getInstance().isModLoaded("polymer-autohost")
                        && kim.biryeong.destiny.weapon.ProfileWeaponView.enabled(),
                "HUD fixture requires startup autohost generation and enabled profile view");
        h.startSequence().thenWaitUntil(() -> {
            var gun = kim.biryeong.destiny.weapon.WeaponItems.create(
                    kim.biryeong.destiny.weapon.WeaponCatalog.find("ace_of_spades").orElseThrow());
            var route = kim.biryeong.destiny.weapon.WeaponCombatItem.INSTANCE.getPolymerItemModel(
                    gun, null, h.getLevel().registryAccess());
            check(h, kim.biryeong.destiny.compat.pack.ProfileArmAssets.graph(route) != null,
                    "Await successful pack profile-graph publication before starting the HUD scenario");
        }).thenExecute(action);
    }

    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static ServerPlayer player(GameTestHelper h,GuardianClass cls,int index) {
        var p=TestPlayers.create(h,new Vec3(2.5+index*6,3,2.5),0,-45,"W252_"+cls+index);
        p.setNoGravity(true);p.setOnGround(true);
        CharacterLoadouts.selectClass(p,cls);CharacterLoadouts.selectSubclass(p,Element.ARC);
        h.onEachTick(()->viewOperation(p,"update"));
        TestCleanup.register(h,()->{viewOperation(p,"remove");TestPlayers.remove(p);});return p;
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=60)
    public void allClassesThrowAfterWindupAndEmitOnlyOnce(GameTestHelper h) {
        var players=new ArrayList<ServerPlayer>();int i=0;
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK)) {
            var p=player(h,cls,i++);players.add(p);
            check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Throw accepted "+cls);
            check(h,GrenadeThrow.active(p)&&SimProjectile.activeCount(p)==0,"No instant projectile "+cls);
            check(h,AbilityService.use(p,AbilitySlot.MELEE)==AbilityService.Result.BUSY,"Throw owns recovery");
        }
        h.runAfterDelay(3,()->players.forEach(p->check(h,SimProjectile.activeCount(p)==0,"Still winding up")));
        h.runAfterDelay(8,()->players.forEach(p->{
            check(h,SimProjectile.activeCount(p)==1,"One actual flight "+p.getName().getString());
            check(h,GrenadeThrow.prop(p).isEmpty(),"Held grenade disappears at release");
        }));
        h.runAfterDelay(23,()->{for(var p:players)check(h,!GrenadeThrow.active(p),"Recovery retired");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void subclassChangeCancelsPendingThrowWithoutGhostEmission(GameTestHelper h) {
        var players=new ArrayList<ServerPlayer>();int i=0;
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK)) {
            var p=player(h,cls,i++);players.add(p);AbilityService.use(p,AbilitySlot.GRENADE);
            check(h,CharacterLoadouts.selectSubclass(p,Element.SOLAR)==null,"Subclass changed");
            check(h,!GrenadeThrow.active(p),"Pending cast cancelled immediately");
        }
        h.runAfterDelay(10,()->{for(var p:players)check(h,SimProjectile.activeCount(p)==0,"Old callbacks cannot emit");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void jumpOptionsAreClassBoundAndBlinkIsSubclassBound(GameTestHelper h) {
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK))for(var e:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
            var options=CharacterLoadouts.options(cls,e,AbilitySlot.JUMP);
            boolean blink=(cls==GuardianClass.HUNTER&&e==Element.ARC)||(cls==GuardianClass.WARLOCK&&e==Element.VOID);
            check(h,options.size()==(blink?4:3),"Expected jump options "+cls+" "+e+": "+options.size());
            check(h,options.stream().allMatch(a->a.guardianClass()==cls),"No foreign class jump");
            check(h,options.stream().anyMatch(a->a.id().getPath().endsWith("blink"))==blink,"Blink membership");
        }
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void grenadeHidesGunAndSupportArmWithoutReplacingInventory(GameTestHelper h) {
        profileReady(h, () -> {
            var p=player(h,GuardianClass.TITAN,0);var gun=armWeapon(p,"ace_of_spades");
            h.runAfterDelay(2,()->{
                check(h,view(p,"gun")!=null,"Actual profile HUD prepared");
                check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Throw accepted");
            });
            h.runAfterDelay(6,()->{
                check(h,p.getMainHandItem()==gun,"Authoritative inventory identity preserved");
                check(h,view(p,"gun").getItem().isEmpty(),"No gun during windup");
                check(h,kim.biryeong.destiny.fx.PlayerAnimations.ownsGrenadeHand(p,gun),"Owner logical carrier protected");
                for(int segment:new int[]{0,2})check(h,hidden(p,"arm_"+segment),
                        "Nonthrowing profile arm is lowered");
            });
            h.runAfterDelay(20,()->check(h,view(p,"gun").getItem().isEmpty(),"No early gun during recovery"));
            h.runAfterDelay(29,()->{
                check(h,!GrenadeThrow.active(p)&&p.getMainHandItem()==gun,"Throw ended without inventory replacement");
                check(h,!view(p,"gun").getItem().isEmpty(),"Gun raised again");h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void grenadeCancellationRestoresCurrentWeaponInsteadOfCachedWeapon(GameTestHelper h) {
        profileReady(h, () -> {
            var p=player(h,GuardianClass.WARLOCK,0);armWeapon(p,"ace_of_spades");
            h.runAfterDelay(2,()->check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Throw accepted"));
            h.runAfterDelay(6,()->{
                armWeapon(p,"blast_furnace");
                check(h,CharacterLoadouts.selectSubclass(p,Element.SOLAR)==null,"Cancel by loadout change");
            });
            h.runAfterDelay(14,()->{
                check(h,!GrenadeThrow.active(p),"Cancelled cast retired");
                check(h,kim.biryeong.destiny.weapon.WeaponItems.entry(p.getMainHandItem()).orElseThrow().id().equals("blast_furnace"),"Current logical gun preserved");
                check(h,view(p,"gun").getItem().get(net.minecraft.core.component.DataComponents.ITEM_MODEL).getPath().contains("blast_furnace"),"Current HUD gun restored");
                h.succeed();
            });
        });
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void hunterMeleeHidesWeaponGripAndCannotFireUntilRecovery(GameTestHelper h) {
        profileReady(h, () -> {
            var p=player(h,GuardianClass.HUNTER,0);var gun=armWeapon(p,"ace_of_spades");
            h.runAfterDelay(2,()->check(h,AbilityService.use(p,AbilitySlot.MELEE)==AbilityService.Result.OK,"Melee accepted"));
            h.runAfterDelay(5,()->{
                check(h,kim.biryeong.destiny.fx.PlayerAnimations.meleePlaying(p),"Actual melee clip running");
                check(h,p.getMainHandItem()==gun&&view(p,"gun").getItem().isEmpty(),"Melee hides cosmetic gun only");
                for(int i=0;i<4;i++)check(h,hidden(p,"arm_"+i),"No static grip arm over melee");
                check(h,!kim.biryeong.destiny.weapon.WeaponRuntime.beginUse(p),"No hidden shot during melee");
            });
            h.runAfterDelay(27,()->{
                check(h,!kim.biryeong.destiny.fx.PlayerAnimations.meleePlaying(p),"Melee recovered");
                check(h,p.getMainHandItem()==gun&&!view(p,"gun").getItem().isEmpty(),"Current gun restored");h.succeed();
            });
        });
    }
}
