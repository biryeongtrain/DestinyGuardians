package kim.biryeong.destiny.test;

import static kim.biryeong.destiny.test.WeaponGripGameTests.*;

import io.netty.buffer.Unpooled;
import it.unimi.dsi.fastutil.ints.Int2ObjectOpenHashMap;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.hud.WeaponPerkHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.camera.api.CameraEffects;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import kim.biryeong.minigamelib.shaderfx.impl.ModConfig;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.FriendlyByteBuf;
import net.minecraft.network.HashedStack;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.inventory.ContainerInput;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.phys.Vec3;
import java.util.ArrayList;
import java.util.List;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;

/** Native Player.actuallyHurt integration: no direct damaged(), shot() or fake trait grants.
 * Camera angles/interpolation/budget and pre-proc reset are explicit local policies, not exact D2 curves.
 * All callbacks install at fixture initialization on the raised48x12x32 W78 deck; no native client claims.
 */
public final class WeaponFlinchW85GameTests {
    private static final String FLOOR="destiny-test:w78_floor", IZA="izanagis_burden";
    private static final float EPS=.0002f;
    private static final Input IDLE=new Input(false,false,false,false,false,false,false);
    private static final Input SHIFT=new Input(false,false,false,false,false,true,false);
    private static void check(GameTestHelper h,boolean ok,String text) { h.assertTrue(ok,Component.literal(text)); }
    private static void near(GameTestHelper h,float value,float expected,String text) {
        check(h,Math.abs(value-expected)<EPS,text+": expected="+expected+", actual="+value);
    }
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static WeaponMagazine ammo(ItemStack stack) { return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())); }
    private static void bounded(GameTestHelper h,Entity e) {
        var o=h.absoluteVec(Vec3.ZERO);var b=e.getBoundingBox();
        check(h,b.minX>o.x&&b.maxX<o.x+48&&b.minY>o.y&&b.maxY<o.y+12&&b.minZ>o.z&&b.maxZ<o.z+32,
                "Whole W85 entity AABB stays within its own48x12x32 fixture");
    }
    private static final class Fixture {
        final GameTestHelper h;final long createdAt;
        final List<ServerPlayer> players=new ArrayList<>(); final List<Husk> mobs=new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;createdAt=h.getLevel().getServer().getTickCount();
            for(int x=0;x<48;x++)for(int z=0;z<32;z++)h.setBlock(x,3,z,Blocks.STONE);
            TestCleanup.register(h, ()->{
                for(var p:players) {
                    if(CameraViews.get(p)!=null)CameraViews.stop(p);
                    p.setServerLevel(h.getLevel());p.stopUsingItem();p.setGameMode(GameType.SURVIVAL);
                    if(AbilityService.inSuper(p))AbilityService.endSuper(p);
                    kim.biryeong.destiny.camera.SuperCamera.stop(p);p.setCamera(p);
                    WeaponRuntime.cleanup(p);WeaponPerkHud.remove(p);CombatHud.remove(p);CameraEffects.resetFov(p);
                    if(p.level().players().contains(p))p.level().removePlayerImmediately(p,Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
                mobs.forEach(Entity::discard);
            });
            h.onEachTick(()->{
                for(var p:players) {bounded(h,p);WeaponRuntime.tickPlayer(p);}
                for(var m:mobs)if(!m.isRemoved())bounded(h,m);
            });
        }
        ServerPlayer player(double z,String id,boolean ads) {
            var p=TestPlayers.create(h,new Vec3(3,4,z),0,0,"W85_"+UUID.randomUUID().toString().substring(0,8));
            players.add(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);p.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(20);
            p.setHealth(20);p.setAbsorptionAmount(0);equip(p,id);ads(p, ads);WeaponRuntime.tickPlayer(p);
            // First runtime observation may already have consumed this server tick for the ADS animation,
            // but No Distractions records actual held input now, not twenty calls later.
            WeaponAiming.noDistractions(p);bounded(h,p);TestPlayers.drain(p);return p;
        }
        ItemStack equip(ServerPlayer p,String id) {
            var e=entry(id);var stack=WeaponItems.create(e);var profile=WeaponProfile.forEntry(e);
            WeaponItems.save(stack,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            p.getInventory().setItem(0,stack);p.getInventory().setSelectedSlot(0);WeaponRuntime.tickPlayer(p);return stack;
        }
        Husk mob(ServerPlayer p) {
            var z=h.relativeVec(p.position()).z;
            var m=h.spawn(EntityTypes.HUSK,new Vec3(6,4,z+1));mobs.add(m);
            m.setNoAi(true);m.setNoGravity(true);m.setPersistenceRequired();
            m.getAttribute(Attributes.ATTACK_DAMAGE).setBaseValue(4);
            check(h,m.isAlive()&&!m.isRemoved()&&m.level()==p.level(),"Native mob attacker is live, local and distinct from victim");
            bounded(h,m);return m;
        }
        void at(int ticks,Runnable action) {
            check(h,h.getLevel().getServer().getTickCount()==createdAt,"No late/nested callback registration");
            h.runAfterDelay(ticks,()->{
                check(h,h.getLevel().getServer().getTickCount()-createdAt==ticks,"Exact actual server deadline "+ticks);
                for(var p:players)WeaponRuntime.tickPlayer(p);
                action.run();
            });
        }
    }
    private record Hit(float loss,float yaw,float pitch,List<ClientboundPlayerRotationPacket> packets) {}
    private static Hit observe(GameTestHelper h,ServerPlayer p,Runnable nativeDamage) {
        float before=p.getHealth()+p.getAbsorptionAmount(),yaw=p.getYRot(),pitch=p.getXRot();var position=p.position();
        TestPlayers.drain(p);nativeDamage.run();var packets=TestPlayers.outbound(p);
        check(h,packets.stream().noneMatch(ClientboundPlayerPositionPacket.class::isInstance),"Incoming flinch never teleports victim");
        check(h,p.position().equals(position),"Incoming camera impulse never moves the server body");
        return new Hit(before-p.getHealth()-p.getAbsorptionAmount(),p.getYRot()-yaw,p.getXRot()-pitch,
                packets.stream().filter(ClientboundPlayerRotationPacket.class::isInstance).map(ClientboundPlayerRotationPacket.class::cast).toList());
    }
    private static Hit hurt(GameTestHelper h,ServerPlayer p,DamageSource source,float amount,boolean resetIframe) {
        if(resetIframe)p.damageCooldownTime=0;
        return observe(h,p,()->p.hurtServer(p.level(),source,amount));
    }
    private static float expected(ServerPlayer p,float loss,boolean noD) {
        var e=WeaponItems.entry(p.getMainHandItem()).orElseThrow();
        return WeaponFlinchState.magnitude(loss,p.getMaxHealth(),WeaponAimProfile.of(e).stability(),
                WeaponFlinchProfile.maxResistance(e),WeaponAiming.progress(p),noD);
    }
    private static void kicked(GameTestHelper h,ServerPlayer p,Hit hit,boolean noD) {
        check(h,hit.loss()>0&&hit.packets().size()==1,"Actual exclusive HP/absorption loss emits exactly one rotation packet");
        near(h,-hit.pitch(),expected(p,hit.loss(),noD),"Native loss drives authored upward pitch once");
        near(h,Math.abs(hit.yaw()),-hit.pitch()*.30f,"Authored source-side bias is30 percent of the same impulse");
        codec(h,hit);
    }
    private static void quiet(GameTestHelper h,Hit hit,String reason) {
        check(h,hit.packets().isEmpty(),reason+": no rotation packet");near(h,hit.yaw(),0,reason+": yaw unchanged");near(h,hit.pitch(),0,reason+": pitch unchanged");
    }
    private static void codec(GameTestHelper h,Hit hit) {
        float yaw=0,pitch=0;
        for(var packet:hit.packets()) {
            var buffer=new FriendlyByteBuf(Unpooled.buffer());
            try {
                ClientboundPlayerRotationPacket.STREAM_CODEC.encode(buffer,packet);
                var decoded=ClientboundPlayerRotationPacket.STREAM_CODEC.decode(buffer);
                check(h,decoded.relativeX()&&decoded.relativeY()&&decoded.equals(packet)&&buffer.readableBytes()==0,
                        "Actual native rotation codec preserves both relative flags and exact deltas");
                yaw+=decoded.yRot();pitch+=decoded.xRot();
            } finally {buffer.release();}
        }
        near(h,yaw,hit.yaw(),"Wire yaw matches authoritative server delta");near(h,pitch,hit.pitch(),"Wire pitch matches authoritative server delta");
    }
    private static void hud(GameTestHelper h,ServerPlayer p,boolean active) {
        var before=p.getMainHandItem().copy();WeaponPerkHud.update(p);WeaponPerkHud.update(p);
        String key=WeaponPerkHud.PREFIX+"no_distractions_";
        var keys=DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(key)).collect(Collectors.toSet());
        check(h,keys.equals(active?Set.of(key+"marker",key+"label"):Set.of()),"No Distractions HUD has exactly marker/label, never countdown or stale digits");
        if(active) {
            var label=(ItemDisplayHud)DisplayHud.getHud(p,key+"label");
            check(h,Identifier.fromNamespaceAndPath("destiny","gui/hud/perk_no_distractions_w85").equals(label.getItem().get(DataComponents.ITEM_MODEL)),"Dedicated sourced-trait label sprite");
        }
        check(h,WeaponAiming.noDistractions(p)==active&&ItemStack.matches(before,p.getMainHandItem()),"HUD observes actual earned runtime state without item mutation");
    }
    private static void paid(GameTestHelper h,ServerPlayer p) {
        var gun=p.getMainHandItem();int loaded=ammo(gun).rounds();int reserve=ammo(gun).reserve();
        check(h,WeaponAiming.requested(p)&&WeaponAiming.aimInput(p)&&WeaponAiming.progress(p)==1&&!WeaponHandling.blocked(p)&&!WeaponRuntime.reloading(p)&&loaded>1,"Paid shot fixture has actual continuous ADS, ammo and completed handling");
        // Downward miss into the raised deck: no synthetic shot/kill notification and no victim acquisition.
        p.setXRot(90);WeaponAiming.tick(p);
        var from=p.getEyePosition();var floor=p.level().clip(new net.minecraft.world.level.ClipContext(from,from.add(0,-4,0),
                net.minecraft.world.level.ClipContext.Block.COLLIDER,net.minecraft.world.level.ClipContext.Fluid.NONE,p));
        check(h,floor.getType()==net.minecraft.world.phys.HitResult.Type.BLOCK,"Paid ADS shot has positive stone-deck miss preflight");
        check(h,WeaponRuntime.beginUse(p),"Actual paid WeaponRuntime beginUse accepted");WeaponRuntime.releaseUse(p,gun);p.stopUsingItem();
        check(h,ammo(gun).rounds()==loaded-1&&ammo(gun).reserve()==reserve&&WeaponAiming.requested(p)&&WeaponAiming.aimInput(p)&&WeaponAiming.progress(p)==1,"One real cartridge paid without releasing ADS");
        p.setXRot(0);TestPlayers.drain(p);
    }
    private static void hotbarRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.getInventory().setItem(1, new ItemStack(Items.STONE));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
        check(h, p.getMainHandItem().is(Items.STONE), "First validated packet genuinely stows Izanagi");
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(0));
        check(h, now(p) == tick && p.getMainHandItem() == gun && ammo(gun).rounds() == rounds,
                "Same-tick native slot round trip returns the identical paid stack");
        WeaponRuntime.tickPlayer(p);
    }
    private static void offhandRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds(); long tick = now(p);
        p.setItemInHand(InteractionHand.OFF_HAND, new ItemStack(Items.STONE));
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, p.getOffhandItem() == gun && p.getMainHandItem().is(Items.STONE), "Actual non-Guardian packet stows exact Izanagi in offhand");
        p.connection.handlePlayerAction(new ServerboundPlayerActionPacket(
                ServerboundPlayerActionPacket.Action.SWAP_ITEM_WITH_OFFHAND, BlockPos.ZERO, Direction.UP));
        check(h, now(p) == tick && p.getMainHandItem() == gun && p.getOffhandItem().is(Items.STONE)
                        && ammo(gun).rounds() == rounds, "Actual same-tick offhand return preserves exact identity and paid ammo");
        WeaponRuntime.tickPlayer(p);
    }

    private static void containerRoundTrip(GameTestHelper h, ServerPlayer p) {
        var gun = p.getMainHandItem(); var menu = p.containerMenu;
        int backpack = menu.findSlot(p.getInventory(), 9).orElseThrow();
        int rounds = ammo(gun).rounds(); long tick = now(p);
        check(h, menu == p.inventoryMenu && menu.stillValid(p) && p.getInventory().getSelectedSlot() == 0
                        && menu.getCarried().isEmpty() && menu.getSlot(backpack).getItem().isEmpty()
                        && menu.getSlot(backpack).mayPickup(p) && menu.getSlot(backpack).mayPlace(gun),
                "Positive native player-inventory preflight: selected hotbar0 and an empty ordinary backpack slot");
        // Empty sparse client predictions request no speculative remote-slot updates. Vanilla still
        // executes both validated SWAPs and broadcasts authoritative contents; carried EMPTY is exact.
        // Crucially, no selected-slot/action packet, weapon update or tick occurs between the clicks.
        p.connection.handleContainerClick(new ServerboundContainerClickPacket(menu.containerId, menu.getStateId(),
                (short) backpack, (byte) 0, ContainerInput.SWAP, new Int2ObjectOpenHashMap<>(), HashedStack.EMPTY));
        check(h, p.getMainHandItem().isEmpty() && menu.getSlot(backpack).getItem() == gun
                        && p.getInventory().getSelectedSlot() == 0,
                "Actual accepted container number-key packet moves the original stack out of the selected slot");
        p.connection.handleContainerClick(new ServerboundContainerClickPacket(menu.containerId, menu.getStateId(),
                (short) backpack, (byte) 0, ContainerInput.SWAP, new Int2ObjectOpenHashMap<>(), HashedStack.EMPTY));
        check(h, now(p) == tick && p.containerMenu == menu && p.getMainHandItem() == gun
                        && menu.getSlot(backpack).getItem().isEmpty() && menu.getCarried().isEmpty()
                        && p.getInventory().getSelectedSlot() == 0 && ammo(gun).rounds() == rounds,
                "Second accepted container SWAP returns the exact original object in the same tick without minting ammunition");
    }



    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void nativeMobHpAndAbsorptionOnlyLossAndDirectEntityFallbackEmitExactRelativePackets(GameTestHelper h) {
        var f=new Fixture(h);var hp=f.player(6,"austringer",false);var shield=f.player(16,"austringer",false);var direct=f.player(26,IZA,false);
        var a=f.mob(hp);var b=f.mob(shield);var c=f.mob(direct);
        shield.setAbsorptionAmount(8);near(h,shield.getAbsorptionAmount(),8,"Positive native absorption fixture");
        hp.damageCooldownTime=0;shield.damageCooldownTime=0;
        var healthHit=observe(h,hp,()->a.doHurtTarget(h.getLevel(),hp));
        var absorptionHit=observe(h,shield,()->b.doHurtTarget(h.getLevel(),shield));
        check(h,hp.getHealth()<20&&hp.getAbsorptionAmount()==0,"Real native mob attack causes actual HP loss");
        check(h,shield.getHealth()==20&&shield.getAbsorptionAmount()<8,"Real native mob attack causes absorption-only loss");
        near(h,absorptionHit.loss(),healthHit.loss(),"Equal real total loss receives equal flinch regardless of HP vs absorption");
        kicked(h,hp,healthHit,false);kicked(h,shield,absorptionHit,false);
        near(h,absorptionHit.pitch(),healthHit.pitch(),"Same weapon and actual loss share exact impulse");
        var source=new DamageSource(direct.damageSources().mobAttack(c).typeHolder(),c,null);
        check(h,source.getEntity()==null&&source.getDirectEntity()==c,"Native direct-only entity attribution preflight");
        kicked(h,direct,hurt(h,direct,source,4,true),false);h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=10, environment = "destiny-test:w90_isolated")
    public void immuneIframeZeroEnvironmentalSelfAndFullyBlockedNativeDamageCannotFlinch(GameTestHelper h) {
        var f=new Fixture(h);var immune=f.player(3,"austringer",false);var iframe=f.player(8,"austringer",false);
        var zero=f.player(13,"austringer",false);var environment=f.player(18,"austringer",false);
        var self=f.player(23,"austringer",false);var blocked=f.player(28,"austringer",false);
        var mi=f.mob(immune);var mt=f.mob(iframe);var mz=f.mob(zero);var mb=f.mob(blocked);
        immune.setPermanentlyInvulnerable(true);
        var i=hurt(h,immune,immune.damageSources().mobAttack(mi),4,true);near(h,i.loss(),0,"Native invulnerability rejected loss");quiet(h,i,"Invulnerable");
        kicked(h,iframe,hurt(h,iframe,iframe.damageSources().mobAttack(mt),4,true),false);
        check(h,iframe.damageCooldownTime>0,"Positive native iframe established by actual first hit");
        var t=hurt(h,iframe,iframe.damageSources().mobAttack(mt),4,false);near(h,t.loss(),0,"Equal repeat damage rejected by real iframe");quiet(h,t,"Iframe rejection");
        var z=hurt(h,zero,zero.damageSources().mobAttack(mz),0,true);near(h,z.loss(),0,"Zero native amount cannot remove HP or absorption");quiet(h,z,"Zero loss");
        var e=hurt(h,environment,environment.damageSources().fall(),4,true);check(h,e.loss()>0,"Environmental negative control really loses HP");quiet(h,e,"Unattributed environment");
        var s=hurt(h,self,self.damageSources().playerAttack(self),4,true);check(h,s.loss()>0,"Self-attributed negative control really loses HP");quiet(h,s,"Self source");
        // Zero-delay shield is a fixture-only native blocking component, not a flinch/trait override.
        // Standalone fake players do not execute vanilla item-use ticks, so no invented elapsed-use clock.
        var shield=new ItemStack(Items.SHIELD);var base=shield.get(DataComponents.BLOCKS_ATTACKS);
        shield.set(DataComponents.BLOCKS_ATTACKS,new net.minecraft.world.item.component.BlocksAttacks(0,base.disableCooldownScale(),
                base.damageReductions(),base.itemDamage(),base.bypassedBy(),base.blockSound(),base.disableSound()));
        blocked.setItemInHand(InteractionHand.OFF_HAND,shield);blocked.startUsingItem(InteractionHand.OFF_HAND);
        check(h,blocked.isBlocking(),"Native shield is positively active before blocked hit");
        var g=hurt(h,blocked,blocked.damageSources().mobAttack(mb),4,true);near(h,g.loss(),0,"Native shield fully blocks actual loss");quiet(h,g,"Fully blocked native hit");h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=15, environment = "destiny-test:w90_isolated")
    public void actualGlaiveAndSwordGuardLoseReducedHpButExcludedFamiliesNeverBindFlinch(GameTestHelper h) {
        var f=new Fixture(h);var glaive=f.player(8,"nezarec_s_whisper",false);var sword=f.player(24,"goldtusk",false);
        glaive.setShiftKeyDown(true);sword.setShiftKeyDown(true); // Native guard remains Shift, independently of ranged ADS.
        var a=f.mob(glaive);var b=f.mob(sword);
        GlaiveItems.saveEnergy(glaive.getMainHandItem(),75000);SwordItems.save(sword.getMainHandItem(),SwordCycle.CAPACITY,0);
        // Rebind funded fixture energy through normal production loading before guard ticks begin.
        WeaponRuntime.cleanup(glaive);WeaponRuntime.cleanup(sword);glaive.setYRot(-90);sword.setYRot(-90);
        WeaponRuntime.tickPlayer(glaive);WeaponRuntime.tickPlayer(sword);
        f.at(2,()->{
            check(h,WeaponRuntime.glaiveStatus(glaive).orElseThrow().guarding()&&WeaponRuntime.swordStatus(sword).orElseThrow().guarding(),"Both genuine production guard sessions are active");
            for(var pair:List.of(new Object[]{glaive,a},new Object[]{sword,b})) {
                var p=(ServerPlayer)pair[0];var mob=(Husk)pair[1];
                var hit=hurt(h,p,p.damageSources().mobAttack(mob),4,true);
                check(h,hit.loss()>0&&hit.loss()<1,"Real guarded damage reaches native HP with mitigation, not an immune fake fixture");
                quiet(h,hit,"Excluded guarded family");check(h,!WeaponAiming.noDistractions(p)&&WeaponAiming.progress(p)==0,"Neither excluded family borrows ranged ADS trait");
            }
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_fov_w85")
    public void realReloadSuperHandlingBlockedAdsAndExternalCamerasSuppressIncomingFlinch(GameTestHelper h) {
        var f=new Fixture(h);var reload=f.player(3,IZA,true);var supers=f.player(8,IZA,true);
        var handling=f.player(13,IZA,true);var suspended=f.player(18,IZA,true);var cinematic=f.player(23,IZA,true);var fov=f.player(28,IZA,true);
        var mobs=new ArrayList<Husk>();for(var p:f.players)mobs.add(f.mob(p));
        WeaponItems.save(reload.getMainHandItem(),new WeaponMagazine(WeaponProfile.forEntry(entry(IZA)),1,3));
        handling.getInventory().setItem(1,WeaponItems.create(entry("austringer")));
        var config=ModConfig.getInstance();boolean old=config.dynamicFovShader;config.dynamicFovShader=true;
        TestCleanup.register(h, ()->config.dynamicFovShader=old);
        f.at(25,()->{
            for(var p:f.players)check(h,WeaponAiming.noDistractions(p),"Positive earned ADS session before blocking boundary");
            reload.connection.handlePlayerAction(new ServerboundPlayerActionPacket(ServerboundPlayerActionPacket.Action.DROP_ITEM,BlockPos.ZERO,Direction.UP));
            check(h,WeaponRuntime.reloading(reload),"Actual Q reload owns blocking deadline");
            AbilityService.startSuper(supers,new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}});
            check(h,AbilityService.inSuper(supers),"Real gameplay super boundary active");
            handling.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(1));
            check(h,handling.getMainHandItem()==handling.getInventory().getItem(1),"Validated selected slot really changed");
            // No runtime/aiming tick between inventory replacement and the actual native hit.
            WeaponAiming.suspend(suspended);check(h,WeaponAiming.progress(suspended)==0,"Held ADS explicitly suspended");
            CameraViews.open(cinematic,h.getLevel(),h.absoluteVec(new Vec3(12,6,23)),0,0);
            check(h,CameraViews.get(cinematic)!=null,"Actual external cinematic owns its view");
            CameraEffects.setFov(fov,55);
            for(int i=0;i<f.players.size();i++) {
                var p=f.players.get(i);var hit=hurt(h,p,p.damageSources().mobAttack(mobs.get(i)),4,true);
                if(p==cinematic)near(h,hit.loss(),0,"CameraViews ALLOW_DAMAGE gate rejects native loss");
                else check(h,hit.loss()>0,"Blocked flinch control still experiences actual native damage");
                if (p == fov) {
                    check(h,WeaponAiming.noDistractions(p)&&WeaponAiming.progress(p)==1,"Shader FOV does not interrupt native ADS or its earned trait");
                    kicked(h,p,hit,true); hud(h,p,true);
                } else if (p == suspended) {
                    check(h,!WeaponAiming.requested(p)&&WeaponAiming.progress(p)==0&&!WeaponAiming.noDistractions(p),
                            "Suspension clears ADS and its trait, while an ordinary equipped gun remains eligible for hip flinch");
                    kicked(h,p,hit,false); hud(h,p,false);
                } else {
                    quiet(h,hit,"Reload/super/handling/camera boundary");check(h,!WeaponAiming.noDistractions(p),"Boundary retires earned No Distractions");hud(h,p,false);
                }
            }
            check(h,WeaponHandling.blocked(handling),"Between-tick incoming damage refreshed real handling protection");
            near(h,CameraEffects.getFov(fov),55,"Flinch never overwrites foreign projection");
        });
        f.at(26,()->{CameraViews.stop(cinematic);AbilityService.endSuper(supers);h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=35, environment = "destiny-test:w90_isolated")
    public void twentyTickActualAdsProcAndTwoNodeHudReduceEqualIncomingLossByExactlyThirtyFivePercent(GameTestHelper h) {
        var f=new Fixture(h);var earned=f.player(8,IZA,true);var control=f.player(24,IZA,false);var a=f.mob(earned);var b=f.mob(control);
        f.at(1,()->ads(control, true));
        f.at(19,()->{check(h,!WeaponAiming.noDistractions(earned)&&!WeaponAiming.noDistractions(control),"19 elapsed ADS ticks do not earn base trait");hud(h,earned,false);});
        f.at(20,()->{
            check(h,WeaponAiming.progress(earned)==1&&WeaponAiming.progress(control)==1,"Both actual ADS animations fully entered");
            check(h,WeaponAiming.noDistractions(earned)&&!WeaponAiming.noDistractions(control),"Only exact20 elapsed continuous input earns No Distractions");
            hud(h,earned,true);hud(h,control,false);
            var x=hurt(h,earned,earned.damageSources().mobAttack(a),4,true);var y=hurt(h,control,control.damageSources().mobAttack(b),4,true);
            near(h,x.loss(),y.loss(),"Positive equal native incoming loss");kicked(h,earned,x,true);kicked(h,control,y,false);
            near(h,x.pitch(),y.pitch()*.65f,"Actual earned trait multiplies remaining incoming flinch by .65");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=65, environment = "destiny-test:w90_isolated")
    public void realPaidPreProcShotResetsQuietIntervalButThresholdAndEarnedShotsRetainTraitUntilAdsEnds(GameTestHelper h) {
        var f=new Fixture(h);var interrupted=f.player(8,IZA,true);var threshold=f.player(24,IZA,true);var a=f.mob(interrupted);f.mob(threshold);
        f.at(10,()->{check(h,!WeaponAiming.noDistractions(interrupted),"Pre-proc fixture is unearned");paid(h,interrupted);check(h,!WeaponAiming.noDistractions(interrupted),"Real paid shot cannot prematurely grant trait");});
        f.at(20,()->{
            check(h,!WeaponAiming.noDistractions(interrupted),"Pre-proc paid shot requires a fresh uninterrupted quiet interval");
            paid(h,threshold);check(h,WeaponAiming.noDistractions(threshold),"At threshold production evaluates proc before paid emission");hud(h,threshold,true);
        });
        f.at(29,()->check(h,!WeaponAiming.noDistractions(interrupted),"19 elapsed ticks after paid reset remain unearned"));
        f.at(30,()->{
            check(h,WeaponAiming.noDistractions(interrupted),"20 elapsed quiet ticks after paid reset earn trait");paid(h,interrupted);
            check(h,WeaponAiming.noDistractions(interrupted),"Firing after earning does not restart or remove No Distractions");hud(h,interrupted,true);
            kicked(h,interrupted,hurt(h,interrupted,interrupted.damageSources().mobAttack(a),4,true),true);
        });
        f.at(31,()->{ads(interrupted, false);WeaponRuntime.tickPlayer(interrupted);check(h,!WeaponAiming.noDistractions(interrupted),"Actual ADS end removes earned firing-persistent trait");hud(h,interrupted,false);h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void actualSameTickHotbarOffhandAndContainerOutBackResetEarnedTraitWithoutTouchingOtherOwner(GameTestHelper h) {
        var f=new Fixture(h);for(int i=0;i<4;i++)f.player(4+i*7,IZA,true);
        f.at(25,()->{
            for(var p:f.players)check(h,WeaponAiming.noDistractions(p),"Positive earned trait before same-tick packet regression");
            hotbarRoundTrip(h,f.players.get(0));offhandRoundTrip(h,f.players.get(1));containerRoundTrip(h,f.players.get(2));
            for(int i=0;i<3;i++){check(h,!WeaponAiming.noDistractions(f.players.get(i)),"Exact original object returning same tick cannot retain continuous ADS credit");hud(h,f.players.get(i),false);}
            check(h,WeaponAiming.noDistractions(f.players.get(3)),"Unrelated exact owner retains earned state");hud(h,f.players.get(3),true);
        });
        f.at(26,()->{for(int i=0;i<3;i++)check(h,!WeaponAiming.noDistractions(f.players.get(i)),"Next tick cannot resurrect retired wind-up");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=60, environment = "destiny-test:w90_isolated")
    public void realNonGuardianReleasePressInputPacketResetsEvenWhenSameTickAndSameStackReturn(GameTestHelper h) {
        var f=new Fixture(h);var p=f.player(8,IZA,true);var ordinary=f.player(24,"beloved",true);
        f.at(25,()->{
            check(h,WeaponAiming.noDistractions(p)&&!WeaponAiming.noDistractions(ordinary),"Exact fixed Izanagi only; another fully ADS sniper never borrows perk");
            var gun=p.getMainHandItem();long tick=now(p);
            p.connection.handlePlayerInput(new ServerboundPlayerInputPacket(IDLE));
            p.connection.handlePlayerInput(new ServerboundPlayerInputPacket(SHIFT));
            check(h,WeaponAiming.noDistractions(p),"Native Shift release/press leaves left-click ADS and earned trait intact");
            ads(p, false); ads(p, true);
            check(h,!WeaponAiming.requested(p),"Same-tick second click is debounced; it cannot re-enter ADS");
            check(h,now(p)==tick&&p.getMainHandItem()==gun&&!WeaponAiming.noDistractions(p),"Native non-Guardian release/press retires earned interval before next server tick");hud(h,p,false);
        });
        f.at(28,()->{ads(p,true);WeaponRuntime.tickPlayer(p);check(h,WeaponAiming.requested(p)&&!WeaponAiming.noDistractions(p),"Three quiet ticks permit a fresh click and start a new trait interval");});
        f.at(47,()->check(h,!WeaponAiming.noDistractions(p),"19 elapsed ticks after fresh accepted click remain unearned"));
        f.at(48,()->{check(h,WeaponAiming.noDistractions(p),"20 elapsed ticks after fresh accepted click earn again");hud(h,p,true);h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=60, environment = "destiny-test:w90_isolated")
    public void stackCopiesOwnerTransferDeathLevelAndSpectatorCannotInheritEarnedAdsState(GameTestHelper h) {
        var f=new Fixture(h);var donor=f.player(3,IZA,true);var recipient=f.player(8,IZA,true);var dying=f.player(13,IZA,true);
        var traveler=f.player(18,IZA,true);var spectator=f.player(23,IZA,true);var keeper=f.player(28,IZA,true);
        var original=donor.getMainHandItem();
        var other=h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER)?Level.OVERWORLD:Level.NETHER);
        check(h,other!=null&&other!=h.getLevel(),"Distinct actual server level exists");
        f.at(25,()->{
            for(var p:f.players)check(h,WeaponAiming.noDistractions(p),"Positive earned state before lifecycle transition");
            var copy=original.copy();donor.getInventory().setItem(0,copy);recipient.getInventory().setItem(0,original);
            check(h,donor.getMainHandItem()==copy&&recipient.getMainHandItem()==original,"Real identity replacement and exact object owner transfer");
            for(var p:List.of(donor,recipient)) {check(h,!WeaponAiming.noDistractions(p),"Copies and transferred stacks do not carry earned ADS session");WeaponRuntime.tickPlayer(p);}
            dying.setHealth(0);WeaponRuntime.tickPlayer(dying);dying.setHealth(20);WeaponRuntime.tickPlayer(dying);
            traveler.setServerLevel(other);WeaponRuntime.tickPlayer(traveler);traveler.setServerLevel(h.getLevel());WeaponRuntime.tickPlayer(traveler);
            spectator.setGameMode(GameType.SPECTATOR);WeaponRuntime.tickPlayer(spectator);spectator.setGameMode(GameType.SURVIVAL);WeaponRuntime.tickPlayer(spectator);
            for(var p:List.of(donor,recipient,dying,traveler,spectator)){check(h,!WeaponAiming.noDistractions(p),"Eligible return cannot inherit retired exact session");hud(h,p,false);}
            WeaponAiming.cleanup(donor);WeaponAiming.cleanup(donor);check(h,WeaponAiming.noDistractions(keeper),"Repeated old-owner cleanup leaves another earned session intact");hud(h,keeper,true);
            check(h,ammo(original).rounds()==4&&ammo(copy).rounds()==4,"Ownership checks never spend or grant a cartridge");
        });
        f.at(26,()->{for(var p:List.of(donor,recipient,dying,traveler,spectator))check(h,!WeaponAiming.noDistractions(p),"No next-tick stale trait resurrection");h.succeed();});
    }

    @GameTest(structure=FLOOR,maxTicks=15, environment = "destiny-test:w90_isolated")
    public void actualNativeHitsRespectPitchClampPerVictimTickBudgetAndNeverQueueCameraRecovery(GameTestHelper h) {
        var f=new Fixture(h);var capped=f.player(8,"austringer",false);var clamped=f.player(24,"austringer",false);var a=f.mob(capped);var b=f.mob(clamped);
        float total=0;
        for(int i=0;i<8;i++) {
            capped.setHealth(20);var hit=hurt(h,capped,capped.damageSources().mobAttack(a),4,true);
            check(h,hit.loss()>0,"Every same-tick budget witness actually damages HP");total-=hit.pitch();codec(h,hit);
        }
        near(h,total,2.5f,"All native hits share exactly2.5degree victim budget, not2.5 per callback");
        clamped.setXRot(-89.9f);var hit=hurt(h,clamped,clamped.damageSources().mobAttack(b),4,true);
        check(h,hit.loss()>0&&hit.packets().size()==1,"Pitch-clamp fixture still experiences native damage");
        near(h,clamped.getXRot(),-90,"Native authoritative pitch saturates at-90");near(h,hit.pitch(),-.1f,"Packet carries actual clamped pitch delta, not requested impulse");codec(h,hit);
        f.at(1,()->{
            capped.setHealth(20);kicked(h,capped,hurt(h,capped,capped.damageSources().mobAttack(a),4,true),false);
            capped.setYRot(37);capped.setXRot(12);clamped.setYRot(-17);clamped.setXRot(9);TestPlayers.drain(capped);TestPlayers.drain(clamped);
        });
        f.at(5,()->{
            near(h,capped.getYRot(),37,"Subsequent mouse yaw is not pulled back");near(h,capped.getXRot(),12,"No queued pitch recovery");
            near(h,clamped.getYRot(),-17,"Other victim mouse yaw remains independent");near(h,clamped.getXRot(),9,"Other victim mouse pitch remains independent");
            for(var p:List.of(capped,clamped))check(h,TestPlayers.outbound(p).stream().noneMatch(ClientboundPlayerRotationPacket.class::isInstance),"Ticks without damage/fire emit no recovery rotations");h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=40, environment = "destiny-test:w90_isolated")
    public void standaloneRetainedSuperCameraAndForeignNativeCameraBlockRealDamageFlinchWithoutGameplaySuper(GameTestHelper h) {
        var f=new Fixture(h);var retained=f.player(8,IZA,true);var foreign=f.player(24,IZA,true);var a=f.mob(retained);var b=f.mob(foreign);
        f.at(25,()->{
            check(h,kim.biryeong.destiny.camera.SuperCamera.ENABLED,"Gate requires real enabled SuperCamera, never a conditional pass");
            check(h,WeaponAiming.noDistractions(retained)&&WeaponAiming.noDistractions(foreign),"Both ordinary sessions earned trait before camera takeover");
            check(h,kim.biryeong.destiny.camera.SuperCamera.start(retained,kim.biryeong.destiny.guardian.Element.VOID),"Real standalone Void camera starts through its native production API");
            check(h,kim.biryeong.destiny.camera.SuperCamera.active(retained)&&!AbilityService.inSuper(retained)
                            &&retained.getCamera()==retained&&CameraViews.get(retained)==null,
                    "Exact P2 gap: retained fake camera is active while gameplay super is false and native camera still self");
            var x=hurt(h,retained,retained.damageSources().mobAttack(a),4,true);
            check(h,x.loss()>0,"Retained-camera regression receives actual native HP loss");quiet(h,x,"Retained/standalone SuperCamera ownership");
            check(h,!WeaponAiming.noDistractions(retained)&&WeaponAiming.progress(retained)==0,"Camera recovery cannot bind ranged ADS or No Distractions");hud(h,retained,false);
            // Native setCamera teleports and updates ChunkMap tracking. Standalone TestPlayers
            // are not registered there; register this real camera witness after the earned-state check.
            h.getLevel().addNewPlayer(foreign);
            check(h,h.getLevel().players().contains(foreign),"Positive native player/chunk tracking before camera takeover");
            foreign.setCamera(b);check(h,foreign.getCamera()==b&&!AbilityService.inSuper(foreign)&&CameraViews.get(foreign)==null,"Real foreign native entity camera owns view independently of gameplay super");
            var y=hurt(h,foreign,foreign.damageSources().mobAttack(b),4,true);check(h,y.loss()>0,"Foreign-camera regression receives actual native HP loss");quiet(h,y,"Foreign native camera ownership");
            check(h,!WeaponAiming.noDistractions(foreign)&&WeaponAiming.progress(foreign)==0,"Foreign native camera cannot bind ranged trait");hud(h,foreign,false);
            foreign.setCamera(foreign);kim.biryeong.destiny.camera.SuperCamera.stop(retained);h.succeed();
        });
    }
}
