package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.titan.TitanClassAbility;
import kim.biryeong.destiny.ability.warlock.WarlockClassAbility;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

public final class ClassAbilityW255GameTests {
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
        int x=3+index*8;
        for(int dx=-2;dx<=2;dx++)for(int z=1;z<=6;z++)h.setBlock(x+dx,0,z,Blocks.STONE);
        var p=TestPlayers.create(h,new Vec3(x+.5,1,3.5),0,0,"W255_"+cls+index);
        p.setNoGravity(true);p.setOnGround(true);
        CharacterLoadouts.selectClass(p,cls);CharacterLoadouts.selectSubclass(p,Element.ARC);
        var gun=kim.biryeong.destiny.weapon.WeaponItems.create(kim.biryeong.destiny.weapon.WeaponCatalog.find("ace_of_spades").orElseThrow());
        p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gun);
        h.onEachTick(()->{
            if(SuperCamera.active(p))p.connection.handleMovePlayer(new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),true,false));
            view(p,"update");
        });
        TestCleanup.register(h,()->{view(p,"remove");TestPlayers.remove(p);});return p;
    }
    private static void view(ServerPlayer p,String operation) {
        try {var m=kim.biryeong.destiny.weapon.ProfileWeaponView.class.getDeclaredMethod(operation,ServerPlayer.class);m.setAccessible(true);m.invoke(null,p);}
        catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    private static boolean field(ServerPlayer p) {return Guardians.data(p).guardianClass()==GuardianClass.TITAN?TitanClassAbility.active(p):WarlockClassAbility.active(p);}
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void classContactDelaysFieldAndRestoresCameraAndCurrentWeapon(GameTestHelper h) {
        profileReady(h, () -> {
            var players=List.of(player(h,GuardianClass.TITAN,0),player(h,GuardianClass.WARLOCK,1));
            var guns=players.stream().map(ServerPlayer::getMainHandItem).toList();
            for(var p:players) {
                check(h,AbilityService.use(p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.OK,"Class accepted");
                check(h,ClassAbilityCast.active(p)&&!field(p),"Preparation precedes field");
                check(h,PlayerAnimations.activeClip(p).startsWith("h15_class_"),"Source clip selected");
                check(h,SuperCamera.active(p),"Rear camera owned");
                check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.BUSY,"Cast blocks grenade");
                check(h,!kim.biryeong.destiny.weapon.WeaponRuntime.beginUse(p),"No hidden firing");
            }
            h.runAfterDelay(10,()->players.forEach(p->check(h,!field(p),"No field before contact")));
            h.runAfterDelay(22,()->players.forEach(p->check(h,field(p),"One field created at contact")));
            h.runAfterDelay(45,()->{
                for(int i=0;i<players.size();i++) {var p=players.get(i);
                    check(h,!ClassAbilityCast.active(p)&&!SuperCamera.active(p)&&!PlayerAnimations.isPlaying(p),"Recovery cleans model/camera");
                    check(h,p.getMainHandItem()==guns.get(i)&&field(p),"Real inventory and persistent field preserved");
                    check(h,kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p).containsKey("destiny:profile_view_gun"),"FP gun view restored");
                }h.succeed();
            });
        });
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=45)
    public void classChangeCancelsPendingContactAndOwnedCamera(GameTestHelper h) {
        var players=List.of(player(h,GuardianClass.TITAN,0),player(h,GuardianClass.WARLOCK,1));
        for(var p:players)check(h,AbilityService.use(p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.OK,"Accepted");
        h.runAfterDelay(4,()->{for(var p:players) {
            CharacterLoadouts.selectSubclass(p,Element.SOLAR);
            check(h,!ClassAbilityCast.active(p)&&!SuperCamera.active(p),"Immediate owned cancellation");
        }});
        h.runAfterDelay(30,()->{for(var p:players)check(h,!TitanClassAbility.active(p)&&!WarlockClassAbility.active(p),"No stale field after loadout change");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=45)
    public void teleportBeforeContactCancelsWithoutGhostField(GameTestHelper h) {
        var p=player(h,GuardianClass.TITAN,0);
        check(h,AbilityService.use(p,AbilitySlot.CLASS_ABILITY)==AbilityService.Result.OK,"Accepted");
        h.runAfterDelay(4,()->p.setPos(p.position().add(2,0,0)));
        h.runAfterDelay(25,()->{
            check(h,!ClassAbilityCast.active(p)&&!SuperCamera.active(p)&&!TitanClassAbility.active(p),"Teleport cancels delayed contact and camera");h.succeed();
        });
    }
}
