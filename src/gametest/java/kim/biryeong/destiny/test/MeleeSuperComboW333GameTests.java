package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.ability.hunter.*;
import kim.biryeong.destiny.camera.SuperCamera;
import kim.biryeong.destiny.combat.PveDamageBalance;
import kim.biryeong.destiny.fx.*;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.input.GuardianAction;
import kim.biryeong.destiny.weapon.AmmoGeneration;
import kr.toxicity.model.api.BetterModel;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.function.IntConsumer;

/** Source endpoint/late-input/independent heavy cooldown checks on actual sessions and native movement. */
public final class MeleeSuperComboW333GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean value,String message){h.assertTrue(value,Component.literal(message));}
    private static void loaded(GameTestHelper h,Runnable action) {
        h.startSequence().thenWaitUntil(()->check(h,BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent()
                &&BetterModel.limb(ClassSuperModelAssets.MODEL_NAME).isPresent(),"Both source model rigs loaded")).thenExecute(action);
    }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final boolean arc;final List<Husk> foes=new ArrayList<>();
        final float lightDamage,heavyDamage;final double targetY;
        final net.minecraft.world.item.ItemStack gun;
        Fixture(GameTestHelper h,boolean arc,double z) {
            this.h=h;this.arc=arc;p=TestPlayers.hunter(h,arc?Element.ARC:Element.VOID,new Vec3(2.5,1,z),-90,0,
                    "W333"+UUID.randomUUID().toString().substring(0,7));TestCleanup.register(h,()->TestPlayers.remove(p));
            if(!arc)Guardians.data(p).setLoadout(GuardianClass.HUNTER,HunterAbilities.preset(Element.VOID)
                    .with(AbilitySlot.SUPER,HunterExpandedSupers.SPECTRAL_BLADES));
            var floor=BlockPos.containing(p.getX(),p.getY()-.01,p.getZ());
            targetY=floor.getY()+1.25; // Stable NPC plane from the explicit block surface, independent of caster physics/pose.
            for(int x=-1;x<=14;x++)for(int dz=-7;dz<=7;dz++) {
                p.level().setBlockAndUpdate(floor.offset(x,0,dz),Blocks.STONE.defaultBlockState());
                for(int y=1;y<=3;y++)p.level().setBlockAndUpdate(floor.offset(x,y,dz),Blocks.AIR.defaultBlockState());
            }
            p.setOnGround(true);p.setDeltaMovement(new Vec3(0,-.0784,0));
            for(int side:new int[]{-1,1}) {
                Husk target=h.spawn(EntityTypes.HUSK,new Vec3(5.5,1.25,z+side));target.setNoAi(true);target.setNoGravity(true);
                target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);target.getAttribute(Attributes.ARMOR).setBaseValue(0);
                target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);target.setHealth(1000);foes.add(target);TestCleanup.register(h,target::discard);
            }
            var entry=kim.biryeong.destiny.weapon.WeaponCatalog.find("ace_of_spades").orElseThrow();
            gun=kim.biryeong.destiny.weapon.WeaponItems.create(entry);
            kim.biryeong.destiny.weapon.WeaponItems.save(gun,new kim.biryeong.destiny.weapon.WeaponMagazine(
                    kim.biryeong.destiny.weapon.WeaponProfile.forEntry(entry),1,30));
            p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,gun);
            var ability=AbilityService.equipped(p,AbilitySlot.SUPER).orElseThrow();float base=(float)ability.param("damage",arc?16:11);
            lightDamage=PveDamageBalance.scale(base,AmmoGeneration.Kind.SUPER,false);
            heavyDamage=PveDamageBalance.scale((float)ability.param("heavy_damage",arc?base*79d/54d:18),AmmoGeneration.Kind.SUPER,false);
            Guardians.data(p).setSuperEnergy(1);check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Actual melee super activates");
        }
        String clip(boolean heavy,int combo) {
            return arc?(heavy?"h15_super_arc_attack_heavy":MeleeSuperAnimationTiming.arcAttack(true,combo))
                    :"w230_hunter_spectral_blades_"+MeleeSuperAnimationTiming.spectralAttack(true,heavy,combo);
        }
        int end(boolean heavy,int combo){return MeleeSuperAnimationTiming.durationTicks(clip(heavy,combo),0);}
        int contact(boolean heavy,int combo){return MeleeSuperAnimationTiming.contactTicks(clip(heavy,combo),0);}
        void primary(boolean heavy) {
            if(heavy)rmb(0);
            else {p.setShiftKeyDown(true);kim.biryeong.destiny.input.InputRouter.onPunch(p);p.setShiftKeyDown(false);}
        }
        void rmb(int route) {
            var hand=net.minecraft.world.InteractionHand.MAIN_HAND;
            var result=switch(route) {
                case 1->net.fabricmc.fabric.api.event.player.UseBlockCallback.EVENT.invoker().interact(p,p.level(),hand,
                        new net.minecraft.world.phys.BlockHitResult(p.position(),net.minecraft.core.Direction.UP,p.blockPosition().below(),false));
                case 2->net.fabricmc.fabric.api.event.player.UseEntityCallback.EVENT.invoker().interact(p,p.level(),hand,foes.getFirst(),
                        new net.minecraft.world.phys.EntityHitResult(foes.getFirst()));
                default->net.fabricmc.fabric.api.event.player.UseItemCallback.EVENT.invoker().interact(p,p.level(),hand);
            };
            check(h,result==net.minecraft.world.InteractionResult.CONSUME,"Opted-in main-hand RMB owns air/block/entity use before ordinary weapon interception");
        }
        void nativeEmptyRmb(int sequence) {
            var hand=net.minecraft.world.InteractionHand.MAIN_HAND;
            p.setItemInHand(hand,net.minecraft.world.item.ItemStack.EMPTY);
            check(h,p.connection.hasClientLoaded(),"Native empty-hand transport fixture acknowledged client load");
            p.connection.handleUseItem(new net.minecraft.network.protocol.game.ServerboundUseItemPacket(hand,sequence,p.getYRot(),p.getXRot()));
            check(h,p.getMainHandItem().isEmpty(),"Native secondary never creates an authoritative carrier item");
        }
        void gcbUse(boolean pressed) {
            try {
                var bridge=Class.forName("kim.biryeong.destiny.compat.gcb.GcbInputBridge");
                var key=Class.forName("kim.biryeong.gcbserver.player.Key");
                var method=bridge.getDeclaredMethod("onKey",ServerPlayer.class,boolean.class,key);method.setAccessible(true);
                Object use=java.lang.Enum.valueOf((Class)key,"KEY_USE");method.invoke(null,p,pressed,use);
            } catch(ReflectiveOperationException e){throw new AssertionError(e);}
        }
        void phase(boolean heavy,int combo){check(h,PlayerAnimations.activeClip(p).equals(clip(heavy,combo)),"Exact expected source phase: "+clip(heavy,combo)+" got "+PlayerAnimations.activeClip(p));}
        void health(int lights,int heavies) {
            float expected=1000-lights*lightDamage-heavies*heavyDamage;
            for(var foe:foes)check(h,Math.abs(foe.getHealth()-expected)<.02,
                    "Each of two live foes receives exactly one contact per accepted attack: expected="+expected+" actual="+foe.getHealth()+" source="+foe.getLastDamageSource()+" target="+foe.position()+" caster="+p.position()
                            +" box="+foe.getBoundingBox()+" inWall="+foe.isInWall()
                            +" eyeBlock="+foe.level().getBlockState(BlockPos.containing(foe.getEyePosition()))
                            +" floor="+foe.level().getBlockState(BlockPos.containing(foe.getX(),targetY-.3,foe.getZ())));
        }
        void step() {
            // Keep both live actors inside the sweep while the caster moves. Never reset their HP.
            for(int i=0;i<foes.size();i++) {
                var foe=foes.get(i);foe.setPos(p.getX()+3,targetY,p.getZ()+(i==0?-1:1));foe.setDeltaMovement(Vec3.ZERO);
                check(h,!foe.isInWall()&&p.level().noCollision(foe,foe.getBoundingBox()),
                        "Controlled live foe has clear body/eye space above its own floor plane: "+foe.position()+" box="+foe.getBoundingBox());
            }
            SuperCamera.move(p,new ServerboundMovePlayerPacket.Rot(p.getYRot(),p.getXRot(),p.onGround(),false));
            AbilityService.tickPlayer(p);p.connection.handleClientTickEnd(ServerboundClientTickEndPacket.INSTANCE);p.connection.tick();TestPlayers.drain(p);
        }
    }
    private static void ticks(GameTestHelper h,List<Fixture> fixtures,int total,IntConsumer afterTick) {
        int start=h.getLevel().getServer().getTickCount();var sequence=h.startSequence();
        for(int i=1;i<=total;i++){int elapsed=i;sequence.thenExecuteAfter(1,()->{
            check(h,h.getLevel().getServer().getTickCount()-start==elapsed,"One real native/server frame per tick");
            fixtures.forEach(Fixture::step);afterTick.accept(elapsed);if(elapsed==total)h.succeed();
        });}
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void nominalSourceEndAcceptsNextLightAndOnlyLastTwoTicksBufferOneInput(GameTestHelper h) {
        loaded(h,()->{
            var arc=new Fixture(h,true,3);var spectral=new Fixture(h,false,11);var fixtures=List.of(arc,spectral);
            int ready=Math.max(SuperAttackTiming.ARC_DEPLOY,MeleeSuperAnimationTiming.durationTicks("w230_hunter_spectral_blades_start",0))+2;
            int total=ready+fixtures.stream().mapToInt(f->f.end(false,0)+f.end(false,1)+f.end(false,2)).max().orElseThrow();
            ticks(h,fixtures,total,elapsed->{for(var f:fixtures) {
                int first=ready,second=first+f.end(false,0),third=second+f.end(false,1),fourth=third+f.end(false,2);
                if(elapsed==first){f.primary(false);f.phase(false,0);}
                if(elapsed==second-3)for(int i=0;i<8;i++)f.primary(false); // Mid-swing input must not become a delayed repeat.
                if(elapsed==second) {
                    check(h,!PlayerAnimations.activeClip(f.p).equals(f.clip(false,1)),"Rejected middle input did not auto-advance the chain");
                    f.primary(false);f.phase(false,1); // Exact source end works while the previous exit/display is still blending.
                }
                if(elapsed==third-2)for(int i=0;i<8;i++)f.primary(false);
                if(elapsed==third)f.phase(false,2); // One buffered light, with no extra engine callback/exit wait.
                int hits=(elapsed>=first+f.contact(false,0)?1:0)+(elapsed>=second+f.contact(false,1)?1:0)
                        +(elapsed>=third+f.contact(false,2)?1:0)+(elapsed>=fourth+f.contact(false,3)?1:0);
                f.health(hits,0);
                if(elapsed==fourth){f.primary(false);f.phase(false,3);f.health(3,0);}
            }});
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=1200)
    public void heavyRejectsAtFiftyNineAcceptsAtSixtyAndLightRemainsAvailableBetween(GameTestHelper h) {
        loaded(h,()->{
            var arc=new Fixture(h,true,3);var spectral=new Fixture(h,false,11);var fixtures=List.of(arc,spectral);
            var ordinary=TestPlayers.create(h,new Vec3(2.5,1,22),-90,0);TestCleanup.register(h,()->TestPlayers.remove(ordinary));
            var solar=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,25),-90,0);TestCleanup.register(h,()->TestPlayers.remove(solar));
            solar.setOnGround(true);Guardians.data(solar).setSuperEnergy(1);
            check(h,AbilityService.use(solar,AbilitySlot.SUPER)==AbilityService.Result.OK,"Non-opted-in actual Solar super activates");
            for(var owner:List.of(ordinary,solar))for(var item:List.of(net.minecraft.world.item.Items.APPLE,net.minecraft.world.item.Items.BOW)) {
                owner.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,new net.minecraft.world.item.ItemStack(item));
                check(h,net.fabricmc.fabric.api.event.player.UseItemCallback.EVENT.invoker().interact(owner,owner.level(),net.minecraft.world.InteractionHand.MAIN_HAND)
                        ==net.minecraft.world.InteractionResult.PASS,"Ordinary items and a different super preserve vanilla use callbacks");
            }
            ordinary.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,net.minecraft.world.item.ItemStack.EMPTY);
            ordinary.connection.handleUseItem(new net.minecraft.network.protocol.game.ServerboundUseItemPacket(
                    net.minecraft.world.InteractionHand.MAIN_HAND,1,ordinary.getYRot(),ordinary.getXRot()));
            check(h,ordinary.getMainHandItem().isEmpty()&&!AbilityService.inSuper(ordinary),"Unsupported native empty hand remains vanilla and creates no item/session");
            int ready=Math.max(SuperAttackTiming.ARC_DEPLOY,MeleeSuperAnimationTiming.durationTicks("w230_hunter_spectral_blades_start",0))+2;
            int total=ready+120+fixtures.stream().mapToInt(f->f.end(true,0)).max().orElseThrow();
            ticks(h,fixtures,total,elapsed->{for(var f:fixtures) {
                int first=ready,light=first+f.end(true,0),second=first+60,followingLight=second+f.end(true,0),
                        third=first+120,thirdLight=third+f.end(true,0);
                if(elapsed==first) {
                    String previous=PlayerAnimations.activeClip(f.p);
                    check(h,net.fabricmc.fabric.api.event.player.UseItemCallback.EVENT.invoker().interact(f.p,f.p.level(),net.minecraft.world.InteractionHand.OFF_HAND)
                            ==net.minecraft.world.InteractionResult.PASS&&PlayerAnimations.activeClip(f.p).equals(previous),"Offhand use cannot activate a second heavy");
                    var original=f.p.containerMenu;
                    f.p.containerMenu=net.minecraft.world.inventory.ChestMenu.threeRows(91,f.p.getInventory());
                    try {
                        check(h,net.fabricmc.fabric.api.event.player.UseItemCallback.EVENT.invoker().interact(f.p,f.p.level(),net.minecraft.world.InteractionHand.MAIN_HAND)
                                ==net.minecraft.world.InteractionResult.PASS&&PlayerAnimations.activeClip(f.p).equals(previous),"Open GUI never routes a combat secondary action");
                    } finally {f.p.containerMenu=original;}
                    if(f.arc){f.gcbUse(true);f.gcbUse(false);}else f.rmb(0);
                    f.phase(true,0);for(int i=0;i<8;i++)f.rmb(0);
                }
                if(elapsed==light||elapsed==followingLight||elapsed==thirdLight){
                    f.p.setItemInHand(net.minecraft.world.InteractionHand.MAIN_HAND,f.gun);f.primary(false);f.phase(false,0);
                }
                if(elapsed==first+59) {
                    String previous=PlayerAnimations.activeClip(f.p);for(int i=0;i<8;i++)f.rmb(0);
                    check(h,PlayerAnimations.activeClip(f.p).equals(previous),"T+59 RMB spam cannot accept or replace a visual");
                }
                if(elapsed==second){
                    f.nativeEmptyRmb(100);f.phase(true,0);
                    for(int i=0;i<8;i++){f.nativeEmptyRmb(101+i);f.rmb(1);}
                }
                if(elapsed==third){f.rmb(2);f.phase(true,0);for(int i=0;i<8;i++)f.rmb(2);}
                int heavies=(elapsed>=first+f.contact(true,0)?1:0)+(elapsed>=second+f.contact(true,0)?1:0)
                        +(elapsed>=third+f.contact(true,0)?1:0);
                int lights=(elapsed>=light+f.contact(false,0)?1:0)+(elapsed>=followingLight+f.contact(false,0)?1:0)
                        +(elapsed>=thirdLight+f.contact(false,0)?1:0);f.health(lights,heavies);
                check(h,kim.biryeong.destiny.weapon.WeaponItems.magazine(f.gun,kim.biryeong.destiny.weapon.WeaponProfile.forEntry(
                        kim.biryeong.destiny.weapon.WeaponItems.entry(f.gun).orElseThrow())).rounds()==1,"Super RMB never fires or consumes the equipped ordinary weapon");
                if(elapsed==total) {
                    f.p.setHealth(0);
                    check(h,!AbilityService.secondary(f.p),"Dead owners cannot execute secondary actions");
                }
            }});
        });
    }
}
