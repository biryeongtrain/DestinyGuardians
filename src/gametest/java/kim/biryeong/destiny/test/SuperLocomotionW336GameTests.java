package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.hunter.*;
import kim.biryeong.destiny.ability.titan.TitanAbilities;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.InputRouter;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.MoverType;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;

public final class SuperLocomotionW336GameTests {
    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final String idle,base,attack;final BlockPos floor;
        BlockPos wall;
        Vec3 lastRequested=Vec3.ZERO,lastResolved=Vec3.ZERO;
        Fixture(GameTestHelper h,int kind,int z) {
            this.h=h;p=TestPlayers.create(h,new Vec3(2.5,1,z),-90,0,"W336"+UUID.randomUUID().toString().substring(0,7));
            TestCleanup.register(h,()->TestPlayers.remove(p));
            var data=Guardians.data(p);
            if(kind==2){data.setGuardianClass(GuardianClass.TITAN);data.setLoadout(GuardianClass.TITAN,TitanAbilities.preset(Element.SOLAR));}
            else {data.setGuardianClass(GuardianClass.HUNTER);data.setLoadout(GuardianClass.HUNTER,
                    kind==0?HunterAbilities.preset(Element.ARC):HunterAbilities.preset(Element.VOID).with(AbilitySlot.SUPER,HunterExpandedSupers.SPECTRAL_BLADES));}
            idle=kind==0?"h15_super_arc":kind==1?"w230_hunter_spectral_blades_idle":"w229_titan_solar_idle";
            base=kind==0?idle:idle.substring(0,idle.length()-5);
            attack=kind==0?"h15_super_arc_attack":base+"_attack";
            floor=BlockPos.containing(p.getX(),p.getY()-.01,p.getZ());
            for(int x=-3;x<=10;x++)for(int dz=-3;dz<=3;dz++) {
                p.level().setBlockAndUpdate(floor.offset(x,0,dz),Blocks.STONE.defaultBlockState());
                for(int y=1;y<=3;y++)p.level().setBlockAndUpdate(floor.offset(x,y,dz),Blocks.AIR.defaultBlockState());
            }
            p.setOnGround(true);p.setDeltaMovement(new Vec3(0,-.0784,0));
            data.setSuperEnergy(1);check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Actual roaming super accepts activation: "+idle);
        }
        void step(Vec3 motion) {
            // Collision resolution is real Entity.move against an explicit floor/wall, not setPos or held input.
            Vec3 from=p.position();lastRequested=motion;
            p.setDeltaMovement(new Vec3(0,-.0784,0));p.move(MoverType.SELF,motion.add(0,-.0784,0));
            SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
            AbilityService.tickPlayer(p);p.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);p.connection.tick();TestPlayers.drain(p);
            lastResolved=p.position().subtract(from);
        }
        void phase(String expected){check(h,PlayerAnimations.activeClip(p).equals(expected),"Expected "+expected+", actual "+PlayerAnimations.activeClip(p)+" at "+p.position()+" grounded="+p.onGround()+" requested="+lastRequested+" resolved="+lastResolved
                +" camera="+SuperCamera.active(p)+" super="+AbilityService.inSuper(p));}
        void wall() {
            wall=new BlockPos((int)Math.ceil(p.getX()+.3),floor.getY()+1,(int)Math.floor(p.getZ()));
            for(int z=-2;z<=2;z++)for(int y=0;y<3;y++)p.level().setBlockAndUpdate(wall.offset(0,y,z),Blocks.STONE.defaultBlockState());
        }
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void collisionResolvedFourDirectionsIdleWallAndAttackPriorityUseTheSameSessions(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent()
                &&BetterModel.limb(ClassSuperModelAssets.MODEL_NAME).isPresent(),"Both source locomotion models loaded")).thenExecute(()->{
            var fixtures=List.of(new Fixture(h,0,3),new Fixture(h,1,11),new Fixture(h,2,19));
            for(var f:fixtures)check(h,SuperLocomotionW336.hasFamily(f.idle),"Source-backed family exists: "+f.idle);
            int ready=100,attackAt=ready+42;
            int afterAttack=attackAt+Math.max(MeleeSuperAnimationTiming.playbackTicks("h15_super_arc_attack",0),
                    Math.max(MeleeSuperAnimationTiming.playbackTicks("w230_hunter_spectral_blades_attack",0),
                            ClassSuperModelAssets.durationTicks("titan/solar_super","attack",0)+3))+8;
            int total=afterAttack+12;var sequence=h.startSequence();
            String[] directions={"forward","backward","left","right"};
            Vec3[] motions={new Vec3(.08,0,0),new Vec3(-.08,0,0),new Vec3(0,0,-.08),new Vec3(0,0,.08)};
            for(int i=1;i<=total;i++) {int elapsed=i;sequence.thenExecuteAfter(1,()->{
                int local=elapsed-ready;
                for(var f:fixtures) {
                    Vec3 movement=Vec3.ZERO;
                    if(local>=0&&local<32&&local%8<5)movement=motions[local/8];
                    if(local==32)f.wall();
                    if(local>=32&&local<=39)movement=motions[0];
                    // Four moving frames prove attack priority without strafing beyond the explicit +/-3 corridor.
                    // Recovery then rests; the separate post-recovery window must produce real leftward movement.
                    if(elapsed>=attackAt&&elapsed<attackAt+4)movement=motions[2];
                    if(elapsed>=afterAttack&&elapsed<afterAttack+6)movement=motions[2];
                    f.step(movement);
                    if(local==-1)f.phase(f.idle);
                    if(local>=0&&local<32&&local%8>=2&&local%8<=4)f.phase(f.base+"_move_"+directions[local/8]);
                    if(local>=0&&local<32&&local%8==7)f.phase(f.idle);
                    if(local==39) {
                        check(h,f.p.getX()<=f.wall.getX()-.299,"Whole body stops at actual wall collision");f.phase(f.idle);
                    }
                    if(elapsed==attackAt){InputRouter.onPunch(f.p);f.phase(f.attack);}
                    if(elapsed>attackAt&&elapsed<=attackAt+3)f.phase(f.attack);
                    if(elapsed>=afterAttack+2&&elapsed<=afterAttack+5) {
                        check(h,f.lastResolved.z<-.04,"Post-attack left input resolves into real clear-corridor travel: requested="
                                +f.lastRequested+" resolved="+f.lastResolved+" position="+f.p.position()+" floor="+f.floor);
                        f.phase(f.base+"_move_left");
                    }
                    if(elapsed==afterAttack+9)f.phase(f.idle);
                    if(elapsed==total) {
                        check(h,f.p.getMainHandItem().isEmpty(),"Wire input carrier never became an authoritative item");
                        AbilityService.cleanup(f.p);check(h,!PlayerAnimations.isPlaying(f.p),"Cleanup retires exact locomotion playback");
                    }
                }
                if(elapsed==total)h.succeed();
            });}
        });
    }
}
