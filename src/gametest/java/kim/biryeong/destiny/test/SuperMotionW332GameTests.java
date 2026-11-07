package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.warlock.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundMovePlayerPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Embedded real server/session clocks and HP; source full lengths never become damage or recovery deadlines. */
public final class SuperMotionW332GameTests {
    private static void check(GameTestHelper h,boolean value,String message){h.assertTrue(value,Component.literal(message));}
    private static ServerPlayer player(GameTestHelper h,boolean nova,boolean air,double z) {
        var p=TestPlayers.hunter(h,Element.VOID,new Vec3(2.5,air?6:1,z),-90,0,"W332"+UUID.randomUUID().toString().substring(0,7));
        TestCleanup.register(h,()->TestPlayers.remove(p));p.setOnGround(!air);
        if(nova) {
            Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
            Guardians.data(p).setLoadout(GuardianClass.WARLOCK,WarlockAbilities.preset(Element.VOID).with(AbilitySlot.SUPER,WarlockExpandedSupers.NOVA_WARP));
            h.setBlock(2,0,(int)z,Blocks.STONE);
        }
        Guardians.data(p).setSuperEnergy(1);check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"The actual requested super activates");return p;
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void shadowshotReleaseAndNovaChargeKeepGameplayClocksWhileFullVisualPhasesPlay(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent()
                &&BetterModel.limb(ClassSuperModelAssets.MODEL_NAME).isPresent(),"Both source overlay rigs loaded")).thenExecute(()->{
            var ground=player(h,false,false,3);var air=player(h,false,true,9);var nova=player(h,true,false,15);
            check(h,PlayerAnimations.activeClip(ground).equals("h15_super_void_attack")
                    &&PlayerAnimations.activeClip(air).equals("h15_super_void_attack_air"),"Shadowshot snapshots ground/air source selection on accepted cast");
            var daybreak=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,6,21),-90,0,"W332Air"+UUID.randomUUID().toString().substring(0,5));
            TestCleanup.register(h,()->TestPlayers.remove(daybreak));daybreak.setOnGround(false);
            Guardians.data(daybreak).setGuardianClass(GuardianClass.WARLOCK);
            Guardians.data(daybreak).setLoadout(GuardianClass.WARLOCK,WarlockAbilities.preset(Element.SOLAR));
            Guardians.data(daybreak).setSuperEnergy(1);
            check(h,AbilityService.use(daybreak,AbilitySlot.SUPER)==AbilityService.Result.OK
                    &&PlayerAnimations.activeClip(daybreak).equals("w229_warlock_solar_start_air"),
                    "The existing generic air-cast selector uses the newly installed original Daybreak clip");
            var enemy=h.spawn(EntityTypes.HUSK,new Vec3(5.5,1,15));enemy.setNoAi(true);enemy.setNoGravity(true);
            enemy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);
            enemy.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);enemy.setHealth(1000);TestCleanup.register(h,enemy::discard);
            var ability=AbilityService.equipped(nova,AbilitySlot.SUPER).orElseThrow();
            int charge=(int)ability.param("charge_ticks",12),recovery=(int)ability.param("burst_recovery_ticks",6);
            int ready=1+ClassSuperModelAssets.durationTicks("warlock/nova_warp","start",41)+2;
            int second=ready+charge+recovery,total=second+charge;
            int cost=(int)Math.ceil(ability.param("duration_ticks",490)*.05);
            float hit=kim.biryeong.destiny.combat.PveDamageBalance.scale((float)ability.param("damage",16),kim.biryeong.destiny.weapon.AmmoGeneration.Kind.SUPER,false);
            int start=h.getLevel().getServer().getTickCount();var sequence=h.startSequence();
            for(int i=1;i<=total;i++){int elapsed=i;sequence.thenExecuteAfter(1,()->{
                check(h,h.getLevel().getServer().getTickCount()-start==elapsed,"One actual server tick per embedded session frame");
                // Input precedes this frame's service update, matching the existing charge/recovery age contract.
                if(elapsed==ready||elapsed==second)for(int n=0;n<8;n++)AbilityService.perform(nova,GuardianAction.PRIMARY);
                if(elapsed==second-1) {
                    for(int n=0;n<8;n++)AbilityService.perform(nova,GuardianAction.PRIMARY);
                    check(h,PlayerAnimations.activeClip(nova).equals("w230_warlock_nova_warp_charge_exit"),"Recovery-1 rejects input while full source exit remains visible");
                }
                for(var p:List.of(ground,air,nova,daybreak)) {
                    if(SuperCamera.active(p))SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
                    AbilityService.tickPlayer(p);TestPlayers.drain(p);
                }
                if(elapsed<ShadowshotTiming.RELEASE_TICKS)for(var p:List.of(ground,air)) {
                    check(h,AbilityService.inSuper(p)&&SimProjectile.activeCount(p)==0,"Source full span cannot rush gameplay arrow release");
                    AbilityService.perform(p,GuardianAction.PRIMARY);
                }
                if(elapsed==ShadowshotTiming.RELEASE_TICKS)for(var p:List.of(ground,air))check(h,!AbilityService.inSuper(p)
                        &&SimProjectile.activeCount(p)==1&&PlayerAnimations.isPlaying(p)&&SuperCamera.active(p),
                        "T+7 releases exactly one arrow and retains the longer source visual tail without extending gameplay ownership");
                int blasts=(elapsed>=ready+charge?1:0)+(elapsed>=second+charge?1:0);
                check(h,Math.abs(enemy.getHealth()-(1000-blasts*hit))<.02,"Nova uses unchanged charge contact and once-per-accepted-input damage");
                if(elapsed==ready||elapsed==second) {
                    check(h,PlayerAnimations.activeClip(nova).equals("w230_warlock_nova_warp_charge_idle"),"Accepted charge uses the explicit original single-pose hold");
                    check(h,WarlockExpandedSupers.status(nova).contains(" spent="+(elapsed==ready?cost:2*cost)+" "),"Input spam spends a single super cost");
                }
                if(elapsed==ready+charge||elapsed==second+charge)check(h,PlayerAnimations.activeClip(nova).equals("w230_warlock_nova_warp_charge_exit"),
                        "The unchanged gameplay blast starts the full source exit; its visual duration cannot extend recovery");
                if(elapsed==total)h.succeed();
            });}
        });
    }
}
