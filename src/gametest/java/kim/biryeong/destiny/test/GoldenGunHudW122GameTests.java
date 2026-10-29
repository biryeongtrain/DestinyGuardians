package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Actual personal HUD graphs / authoritative ability state, not framebuffer evidence. */
public final class GoldenGunHudW122GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(30,1,30),0,-80,"W122r_"+UUID.randomUUID().toString().substring(0,8));
        p.setNoGravity(true);p.setOnGround(true);
        TestCleanup.register(h,()->{AbilityService.endSuper(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        h.onEachTick(()->TestPlayers.drain(p));return p;
    }
    private static ItemDisplayHud hud(ServerPlayer p,String id) { return (ItemDisplayHud)DisplayHud.getHud(p,id); }
    private static int color(ItemDisplayHud h) { return h.getItem().get(DataComponents.CUSTOM_MODEL_DATA).colors().getFirst(); }
    private static long nodes(ServerPlayer p) { return DisplayHud.getHuds(p).keySet().stream().filter(x->x.startsWith(WeaponReticleHud.PREFIX)).count(); }
    private static String model(ItemDisplayHud h) { return h.getItem().get(DataComponents.ITEM_MODEL).toString(); }
    private static void update(ServerPlayer p) { WeaponReticleHud.update(p,Float.NaN,1,true);FallbackAimHud.update(p); }
    private static final class Finite implements SuperSession {
        int shots=3;
        public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return .5f;}
        public OptionalInt ammunition(){return OptionalInt.of(shots);}public int ammunitionCapacity(){return 3;}
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void finiteSuperOwnsAimDespiteUnderlyingReloadBloomAndUnknownItem(GameTestHelper h) {
        var p=player(h);p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND,2));var stack=p.getMainHandItem().copy();
        var session=new Finite();Guardians.runtime(p).superSession=session;update(p);
        var f=hud(p,WeaponReticleHud.FRAME_ID);var c=hud(p,WeaponReticleHud.CENTER_ID);
        check(h,nodes(p)==2&&f!=null&&c!=null,"Finite super owns exactly two reticle nodes");
        check(h,model(f).endsWith("reticle_w44_hand_cannon")&&model(c).endsWith("reticle_w44_dot"),"Solar ring and fixed aim point");
        check(h,f.getScale().x==40&&f.getScale().y==40&&c.getScale().x==4,"No underlying reload/charge/bloom projection");
        check(h,color(f)==0xF4D36A&&color(c)==0xF1F3F5&&f.isAboveHand()&&c.isAboveHand(),"Bounded Solar colors and above-hand pass");
        check(h,DisplayHud.getHud(p,FallbackAimHud.ID)==null,"No stacked fallback dot");
        var point=c.getLocation();var item=f.getItemDisplay().getItemStack();for(int i=0;i<20;i++)update(p);
        check(h,hud(p,WeaponReticleHud.FRAME_ID)==f&&f.getItemDisplay().getItemStack()==item&&hud(p,WeaponReticleHud.CENTER_ID)==c&&c.getLocation().equals(point),"Repeated update reuses identities/cached metadata and fixed aim point");
        check(h,ItemStack.matches(stack,p.getMainHandItem())&&session.shots==3,"HUD read cannot mutate inventory or consume super rounds");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void chargeToSuperRemovesOnlyOwnedChargeTicksAndEmptyTracksRealShots(GameTestHelper h) {
        var p=player(h);var gun=WeaponItems.create(WeaponCatalog.find("erentil_fr4").orElseThrow());p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        check(h,WeaponRuntime.heartbeatUse(p),"Actual initial fusion charge accepted");WeaponReticleHud.update(p,0,0,false);
        check(h,nodes(p)==6,"Real charge has four extra ticks before super");var c=hud(p,WeaponReticleHud.CENTER_ID);var point=c.getLocation();
        var unrelated=new ItemDisplayHud();unrelated.setItem(new ItemStack(Items.PAPER));unrelated.spawn(p,"w122:unrelated");
        TestCleanup.register(h,()->DisplayHud.removeHud(p,"w122:unrelated"));
        var finite=new Finite();Guardians.runtime(p).superSession=finite;update(p);
        check(h,nodes(p)==2&&hud(p,WeaponReticleHud.CENTER_ID)==c,"Old charge nodes retired without respawning centre");
        check(h,DisplayHud.getHud(p,"w122:unrelated")!=null,"Other owner's HUD untouched");
        finite.shots=0;update(p);check(h,color(hud(p,WeaponReticleHud.FRAME_ID))==0xF16B5B,"Actual zero rounds produces empty ring");
        finite.shots=2;update(p);check(h,color(hud(p,WeaponReticleHud.FRAME_ID))==0xF4D36A&&c.getLocation().equals(point),"Actual finite rounds restore gold without moving aim point");
        h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=50,environment=ENV)
    public void nonFiniteSupersAndNormalWeaponsKeepTheirExistingReticlePolicy(GameTestHelper h) {
        var p=player(h);var finite=new Finite();Guardians.runtime(p).superSession=finite;update(p);
        Guardians.runtime(p).superSession=new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}};
        WeaponReticleHud.update(p,0,0,false);FallbackAimHud.update(p);
        check(h,nodes(p)==0&&DisplayHud.getHud(p,FallbackAimHud.ID)!=null,"Arc/Void-style nonfinite super keeps existing fallback point, no Solar ring");
        Guardians.runtime(p).superSession=null;var gun=WeaponItems.create(WeaponCatalog.find("ace_of_spades").orElseThrow());p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        WeaponReticleHud.update(p,0,0,false);FallbackAimHud.update(p);
        check(h,nodes(p)==2&&color(hud(p,WeaponReticleHud.FRAME_ID))==0xF1F3F5&&DisplayHud.getHud(p,FallbackAimHud.ID)==null,"Actual normal gun restored after super");
        WeaponReticleHud.update(p,0,0,true);check(h,nodes(p)==0,"Normal weapon reload still hides gun reticle");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void deadAndSpectatorCannotKeepSolarReticle(GameTestHelper h) {
        var p=player(h);Guardians.runtime(p).superSession=new Finite();update(p);check(h,nodes(p)==2,"Initial finite graph");
        p.setGameMode(GameType.SPECTATOR);update(p);check(h,nodes(p)==0&&DisplayHud.getHud(p,FallbackAimHud.ID)==null,"Spectator retires all aim nodes");
        p.setGameMode(GameType.SURVIVAL);Guardians.runtime(p).superSession=new Finite();update(p);check(h,nodes(p)==2,"Eligible finite super graph returns");
        p.setHealth(0);update(p);check(h,nodes(p)==0&&DisplayHud.getHud(p,FallbackAimHud.ID)==null,"Dead cannot retain finite super aim");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=1200,environment=ENV)
    public void actualGoldenGunActivationShotAndEndUseRealSessionWithoutInventoryMutation(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"Hunter limb loaded"))
            .thenExecute(()->{
                var p=player(h);p.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND,2));var before=p.getMainHandItem().copy();
                Guardians.data(p).setSuperEnergy(1);check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Real Solar ability activated");
                update(p);check(h,AmmoHud.current(p).orElseThrow().rounds()==3&&nodes(p)==2,"Actual three-round session owns ring");
                h.onEachTick(()->{if(Guardians.runtime(p).superSession!=null)AbilityService.tickPlayer(p);});
                h.runAfterDelay(12,()->{
                    check(h,AbilityService.perform(p,GuardianAction.PRIMARY),"Actual Solar primary fired");update(p);
                    check(h,AmmoHud.current(p).orElseThrow().rounds()==2&&nodes(p)==2,"Actual shot spends exactly one and keeps bounded graph");
                    check(h,ItemStack.matches(before,p.getMainHandItem()),"Super feedback never borrows or mutates real hand item");
                    AbilityService.endSuper(p);WeaponReticleHud.update(p,0,0,false);FallbackAimHud.update(p);
                    check(h,nodes(p)==0&&DisplayHud.getHud(p,FallbackAimHud.ID)!=null,"Unknown underlying item regains fallback after actual super end");h.succeed();
                });
            });
    }
}
