package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.hunter.HunterAbilities;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.weapon.*;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.IntConsumer;

/** Real server clocks, native physics, contact HP and existing class input routing; master owns framebuffer QA. */
public final class ArcStaffDodgeW331GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static final Input[] INPUTS={new Input(true,false,false,false,false,false,false),
            new Input(false,true,false,false,false,false,false),new Input(false,false,true,false,false,false,false),
            new Input(false,false,false,true,false,false,false)};
    private static void check(GameTestHelper h,boolean value,String message){h.assertTrue(value,Component.literal(message));}
    private static void loaded(GameTestHelper h,Runnable action) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent(),"W331 source Hunter limb is loaded"))
                .thenExecute(action);
    }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final boolean arc;final Input input;final Vec3 direction;
        final net.minecraft.world.item.ItemStack gun;final List<net.minecraft.network.protocol.Packet<?>> packets=new ArrayList<>();
        Fixture(GameTestHelper h,Element element,Vec3 pos,Input input,boolean marksman) {
            this.h=h;this.arc=element==Element.ARC;this.input=input;
            p=TestPlayers.hunter(h,element,pos,-90,0,"W331"+UUID.randomUUID().toString().substring(0,7));
            TestCleanup.register(h,()->TestPlayers.remove(p));
            if(marksman)Guardians.data(p).setLoadout(GuardianClass.HUNTER,
                    HunterAbilities.preset(element).with(AbilitySlot.CLASS_ABILITY,HunterAbilities.MARKSMANS_DODGE));
            var feet=BlockPos.containing(p.getX(),p.getY()-.01,p.getZ());
            for(int x=-6;x<=6;x++)for(int z=-6;z<=6;z++)p.level().setBlockAndUpdate(feet.offset(x,0,z),Blocks.STONE.defaultBlockState());
            p.setOnGround(true);p.setDeltaMovement(new Vec3(0,-.0784,0));
            var entry=WeaponCatalog.find("ace_of_spades").orElseThrow();gun=WeaponItems.create(entry);
            WeaponItems.save(gun,new WeaponMagazine(WeaponProfile.forEntry(entry),1,30));p.setItemInHand(InteractionHand.MAIN_HAND,gun);
            Guardians.runtime(p).lastInput=input;direction=Motion.inputDirection(p,input);
            Guardians.data(p).setSuperEnergy(1);
            check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Actual named super activates");
        }
        void step() {
            if(SuperCamera.active(p))SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
            AbilityService.tickPlayer(p);
            if(arc) {p.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);p.connection.tick();}
            packets.clear();packets.addAll(TestPlayers.outbound(p));
        }
        int ammo(){return WeaponItems.magazine(gun,WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow())).rounds();}
        SuperSession session(){return Guardians.runtime(p).superSession;}
        AbilityService.Result dodge(){return AbilityService.use(p,AbilitySlot.CLASS_ABILITY);}
        void ordinaryCharges(int elapsed) {
            check(h,Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY)==200-elapsed,"Normal class cooldown only ages naturally, never resets or shortens");
            check(h,Guardians.data(p).cooldown(AbilitySlot.MELEE)==180-elapsed,"Super dodge does not trigger Gambler melee recharge");
            check(h,p.getMainHandItem()==gun&&ammo()==1,"Super dodge does not reload or replace the actual held weapon");
        }
    }
    private static void ticks(GameTestHelper h,List<Fixture> fixtures,int total,IntConsumer afterTick) {
        int start=h.getLevel().getServer().getTickCount();var sequence=h.startSequence();
        for(int i=1;i<=total;i++) {int elapsed=i;sequence.thenExecuteAfter(1,()->{
            check(h,h.getLevel().getServer().getTickCount()-start==elapsed,"One native fixture frame per real server tick");
            fixtures.forEach(Fixture::step);afterTick.accept(elapsed);if(elapsed==total)h.succeed();
        });}
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void fourSourceDirectionsUseIndependentFortyTickCooldownAndPreserveOrdinaryCharges(GameTestHelper h) {
        loaded(h,()->{
            var fixtures=new ArrayList<Fixture>();
            for(int i=0;i<4;i++)fixtures.add(new Fixture(h,Element.ARC,new Vec3(6.5,1,3+i*3),INPUTS[i],i%2==1));
            var nearby=h.spawn(EntityTypes.HUSK,new Vec3(11.5,1,7.5));nearby.setNoAi(true);nearby.setNoGravity(true);
            TestCleanup.register(h,nearby::discard); // Real nearby enemy makes an accidental Gambler refresh observable.
            int ready=SuperAttackTiming.ARC_DEPLOY+2;var origins=new Vec3[4];
            ticks(h,fixtures,ready+43,elapsed->{
                if(elapsed==ready)for(int i=0;i<4;i++) {
                    var f=fixtures.get(i);origins[i]=f.p.position();
                    Guardians.data(f.p).setCooldown(AbilitySlot.CLASS_ABILITY,200);Guardians.data(f.p).setCooldown(AbilitySlot.MELEE,180);
                    check(h,CombatHud.charge(f.p,AbilitySlot.CLASS_ABILITY)==1,"Arc entry has an independent ready dodge despite normal cooldown");
                    check(h,f.dodge()==AbilityService.Result.OK,"Existing class ability input accepts the dedicated source dodge");
                    check(h,PlayerAnimations.activeClip(f.p).equals(MeleeSuperAnimationTiming.arcDodge(INPUTS[i])),"The accepted direction selects its original source clip");
                    check(h,SuperCamera.active(f.p)&&f.session()!=null,"Dedicated dodge retains the same Arc session/rear camera");
                    check(h,CombatHud.charge(f.p,AbilitySlot.CLASS_ABILITY)==0,"HUD shows the new forty-tick charge immediately");
                }
                if(elapsed>ready&&elapsed<=ready+40)for(var f:fixtures)f.ordinaryCharges(elapsed-ready);
                if(elapsed==ready+1)for(var f:fixtures) {
                    check(h,f.packets.stream().anyMatch(x->x instanceof ClientboundSetEntityMotionPacket m&&m.id()==f.p.getId()
                            &&m.movement().dot(f.direction)>1.14),"Native velocity packet carries the existing directional dodge impulse");
                    check(h,Guardians.runtime(f.p).invulnerableTicks==6,"Source entry starts exactly six invulnerable ticks");
                }
                if(elapsed==ready+7)for(int i=0;i<4;i++) {
                    var f=fixtures.get(i);Vec3 displacement=f.p.position().subtract(origins[i]);
                    check(h,displacement.dot(f.direction)>.5&&displacement.subtract(f.direction.scale(displacement.dot(f.direction))).horizontalDistanceSqr()<.01,
                            "Native movement follows forward/back/left/right direction without lateral drift");
                    check(h,Guardians.runtime(f.p).invulnerableTicks==0,"Invulnerability cannot extend to the full animation");
                }
                if(elapsed==ready+39)for(var f:fixtures)check(h,f.dodge()==AbilityService.Result.COOLDOWN,"T+39 remains on cooldown after visual recovery");
                if(elapsed==ready+40)for(var f:fixtures) {
                    check(h,f.dodge()==AbilityService.Result.OK,"T+40 exact boundary accepts once");
                    check(h,f.dodge()==AbilityService.Result.BUSY,"Same-tick double input cannot create a second action");
                    AbilityService.endSuper(f.p);
                }
                if(elapsed==ready+43)for(var f:fixtures) {
                    f.ordinaryCharges(43);check(h,!AbilityService.inSuper(f.p)&&!SuperCamera.active(f.p)&&Guardians.runtime(f.p).invulnerableTicks==0,
                            "Ending before a new impulse cancels future motion/iframe ownership");
                }
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void acceptedAttackAndDodgeCannotOverlapAndEndingMidDodgeRevokesOwnedEffects(GameTestHelper h) {
        loaded(h,()->{
            var arc=new Fixture(h,Element.ARC,new Vec3(6.5,1,6.5),INPUTS[2],false);
            var solar=new Fixture(h,Element.SOLAR,new Vec3(6.5,1,12.5),INPUTS[0],false);
            Husk enemy=h.spawn(EntityTypes.HUSK,new Vec3(9.5,1,6.5));enemy.setNoAi(true);enemy.setNoGravity(true);
            enemy.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);
            enemy.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);enemy.setHealth(1000);TestCleanup.register(h,enemy::discard);
            check(h,arc.dodge()==AbilityService.Result.BUSY&&solar.dodge()==AbilityService.Result.BUSY,"Arc cast is busy and a different super does not opt in");
            int ready=SuperAttackTiming.ARC_DEPLOY+2,contact=SuperAttackTiming.ARC_CONTACT,recovery=SuperAttackTiming.ARC_RECOVERY;
            int dodgeAt=ready+recovery;SuperSession[] original={null};Vec3[] endedAt={null};
            ticks(h,List.of(arc,solar),dodgeAt+6,elapsed->{
                if(elapsed==ready) {
                    original[0]=arc.session();AbilityService.perform(arc.p,GuardianAction.PRIMARY);
                    check(h,arc.dodge()==AbilityService.Result.BUSY,"Dodge cannot cancel an accepted pending contact");
                }
                if(elapsed>=ready&&elapsed<dodgeAt) {
                    check(h,arc.dodge()==AbilityService.Result.BUSY,"Dodge remains busy through attack contact and full source recovery");
                    check(h,Math.abs(enemy.getHealth()-(elapsed<ready+contact?1000:952))<.01,"The accepted contact occurs exactly once at its source beat");
                }
                if(elapsed==dodgeAt)check(h,arc.dodge()==AbilityService.Result.OK,"Dodge accepts at the attack recovery boundary");
                if(elapsed>dodgeAt&&elapsed<=dodgeAt+3) {
                    for(int i=0;i<8;i++)AbilityService.perform(arc.p,GuardianAction.PRIMARY);
                    check(h,arc.session()==original[0]&&PlayerAnimations.activeClip(arc.p).startsWith("h15_super_arc_dodge_")
                            &&Math.abs(enemy.getHealth()-952)<.01,"Attack spam cannot replace the source dodge or cause another contact");
                    if(elapsed==dodgeAt+3) {
                        AbilityService.endSuper(arc.p);endedAt[0]=arc.p.position();
                        check(h,Guardians.runtime(arc.p).invulnerableTicks==0&&!SuperCamera.active(arc.p),"Mid-dodge end revokes owned iframe and camera immediately");
                        check(h,original[0].classAbility()==AbilityService.Result.BUSY,"A retired session cannot start a new velocity action");
                    }
                }
                if(elapsed==dodgeAt+6)check(h,arc.p.position().subtract(endedAt[0]).horizontalDistanceSqr()<.0001
                        &&!PlayerAnimations.isPlaying(arc.p)&&Math.abs(enemy.getHealth()-952)<.01,"No stale impulse/animation/contact appears after end");
                check(h,solar.dodge()==AbilityService.Result.BUSY,"Non-Arc super class ability remains blocked at every boundary");
            });
        });
    }
}
