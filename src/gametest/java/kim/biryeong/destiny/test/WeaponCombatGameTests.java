package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.input.InputRouter;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.fabricmc.fabric.api.event.player.AttackEntityCallback;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundPlayerActionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

/** Real stack/Polymer/command/collision/use acceptance, in addition to pure cadence tests. */
public final class WeaponCombatGameTests {
    private static void check(GameTestHelper h, boolean condition, String message) { h.assertTrue(condition, Component.literal(message)); }
    private static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    private static ServerPlayer player(GameTestHelper h) { return TestPlayers.create(h, new Vec3(2.5,1,6.5), -90, 0); }
    private static ItemStack equip(ServerPlayer player, String id) {
        var stack = WeaponItems.create(entry(id)); player.setItemInHand(InteractionHand.MAIN_HAND,stack); return stack;
    }
    private static int rounds(ItemStack stack) { return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).rounds(); }
    private static void use(GameTestHelper h, ServerPlayer player) {
        player.gameMode.useItem(player,h.getLevel(),player.getMainHandItem(),InteractionHand.MAIN_HAND);
    }
    private static void cleanup(ServerPlayer player) { WeaponRuntime.cleanup(player); TestPlayers.remove(player); }
    private static Husk target(GameTestHelper h, double x, double z) {
        var target=h.spawn(EntityTypes.HUSK,new Vec3(x,1,z)); target.setNoAi(true);target.setPersistenceRequired(); return target;
    }

    public void all63LiveModelsSerializeAndSelectSafeDualWireProtocols(GameTestHelper h) {
        var player=player(h);
        try {
            var context=((PacketContextProvider)(Object)player.connection).getPacketContext();
            var ops=h.getLevel().registryAccess().createSerializationContext(com.mojang.serialization.JsonOps.INSTANCE);
            int twoHanded=0, previousTwoHanded=0;
            for(var e:WeaponCatalog.all()) {
                var stack=WeaponItems.create(e);var snapshot=stack.copy();
                var encoded=ItemStack.CODEC.encodeStart(ops,stack).getOrThrow();
                var decoded=ItemStack.CODEC.parse(ops,encoded).getOrThrow();
                check(h,WeaponItems.entry(decoded).orElseThrow().equals(e),"Live identity roundtrips: "+e.id());
                check(h,decoded.getHoverName().getString().contains("[전투]"),"Explicit combat name");
                check(h,decoded.get(DataComponents.LORE).lines().stream().anyMatch(x->x.getString().contains(e.family().equals("sword")?"재장전 없음":"Q 재장전")),"Live item help matches actual reload binding: "+e.id());
                var wire=PolymerItemUtils.getPolymerItemStack(stack,context,h.getLevel().registryAccess());
                boolean two=WeaponModels.twoHanded(stack);if(two){twoHanded++;if(!WeaponExotics.izanagi(e))previousTwoHanded++;}
                check(h,wire.is(two?Items.CROSSBOW:Items.STICK),"Wire protocol carrier: "+e.id());
                check(h,CrossbowItem.isCharged(wire)==two,"Heartbeat-only crossbow marker");
                check(h,wire.has(DataComponents.CONSUMABLE)!=two,"Native-only consumption hold");
                check(h,Boolean.valueOf(two).equals(wire.get(DataComponents.CUSTOM_MODEL_DATA).getBoolean(0)),"Grip model selector retained");
                check(h,wire.get(DataComponents.USE_EFFECTS).canSprint() && wire.get(DataComponents.USE_EFFECTS).speedMultiplier()==1f,"No consumption slowdown");
                check(h,!stack.has(DataComponents.CONSUMABLE)&&!stack.has(DataComponents.CHARGED_PROJECTILES),"No real consumption/vanilla ammunition");
                check(h,ItemStack.matches(stack,snapshot),"Wire conversion leaves authoritative ammunition unchanged");
                var restored=PolymerItemUtils.getRealItemStack(wire,context,h.getLevel().registryAccess());
                check(h,ItemStack.matches(stack,restored),"Polymer roundtrip keeps combat identity/ammo");
                var nativeGrip=WeaponModels.withGrip(stack,WeaponModels.Grip.NATIVE).orElseThrow();
                check(h,nativeGrip.is(WeaponCombatItem.INSTANCE)&&rounds(nativeGrip)==rounds(stack),"Grip conversion cannot inert/refill combat item");
            }
            check(h,previousTwoHanded==47,"All previous 47 two-handed live weapons remain");
            check(h,twoHanded==48,"Izanagi adds one two-handed live weapon");h.succeed();
        } finally {cleanup(player);}
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void nativeWireStartsUseWithoutArrowsEvenAtFullHunger(GameTestHelper h) {
        var player=player(h);
        try {
            var context=((PacketContextProvider)(Object)player.connection).getPacketContext();
            var real=WeaponItems.create(entry("austringer"));
            var wire=PolymerItemUtils.getPolymerItemStack(real,context,h.getLevel().registryAccess());
            player.setItemInHand(InteractionHand.MAIN_HAND,wire);
            // Vanilla STICK Item.use itself dispatches the consumable component.
            wire.getItem().use(h.getLevel(),player,InteractionHand.MAIN_HAND);
            check(h,player.isUsingItem(),"Native client carrier can enter use with no ammunition or hunger requirement");
            player.releaseUsingItem();check(h,!player.isUsingItem(),"Native release ends use");
            check(h,wire.getCount()==1,"Release never consumes the carrier");h.succeed();
        } finally {cleanup(player);}
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void liveLoadIsOpOnlyAndProtectsInventoryAndExistingCombatAmmo(GameTestHelper h) throws Exception {
        var player=player(h);
        try {
            var server=h.getLevel().getServer();var dispatcher=server.getCommands().getDispatcher();
            var op=server.createCommandSourceStack().withEntity(player);
            boolean denied=false;
            try {dispatcher.execute("destiny weapon load austringer",player.createCommandSourceStack());}
            catch(com.mojang.brigadier.exceptions.CommandSyntaxException expected){denied=true;}
            check(h,denied&&player.getMainHandItem().isEmpty(),"Non-OP cannot mint live weapons");
            player.setItemInHand(InteractionHand.MAIN_HAND,new ItemStack(Items.DIAMOND,3));
            check(h,dispatcher.execute("destiny weapon load austringer",op)==0&&player.getMainHandItem().getCount()==3,"Ordinary item protected");
            player.setItemInHand(InteractionHand.MAIN_HAND,WeaponModels.create(entry("austringer")));
            check(h,dispatcher.execute("destiny weapon load austringer",op)==1,"Explicit preview to combat opt-in");
            use(h,player);int count=rounds(player.getMainHandItem());
            check(h,dispatcher.execute("destiny weapon load austringer",op)==0&&rounds(player.getMainHandItem())==count,"Load cannot refill a held combat item");
            check(h,dispatcher.execute("destiny weapon status",op)==1,"Combat state inspectable");h.succeed();
        } finally {cleanup(player);}
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void hitscanDamagesNearestEnemyOnceAndNeverUsesOffhandAmmo(GameTestHelper h) {
        var player=player(h);var near=target(h,5.5,6.5);var far=target(h,8.5,6.5);
        try {
            var stack=equip(player,"austringer");int before=rounds(stack);
            player.setItemInHand(InteractionHand.OFF_HAND,new ItemStack(Items.ARROW,16));
            use(h,player);float health=near.getHealth();
            check(h,health<near.getMaxHealth(),"Hitscan hits the aimed enemy");
            check(h,far.getHealth()==far.getMaxHealth(),"Nearest hit stops the ray");
            for(int i=0;i<20;i++)use(h,player);
            check(h,rounds(stack)==before-1&&near.getHealth()==health,"Duplicate same-tick inputs cannot multiply damage");
            check(h,player.getOffhandItem().getCount()==16,"Inventory ammunition untouched");
            check(h,AttackEntityCallback.EVENT.invoker().interact(player,h.getLevel(),InteractionHand.MAIN_HAND,near,null)==InteractionResult.FAIL,"No vanilla punch bypass");
            check(h,InputRouter.onPlayerAction(player,ServerboundPlayerActionPacket.Action.START_DESTROY_BLOCK),"No mining through combat item");h.succeed();
        } finally {near.discard();far.discard();cleanup(player);}
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void wallsAndSpectatorAndTamperedPreviewCannotCauseDamage(GameTestHelper h) {
        var player=player(h);var enemy=target(h,6.5,6.5);
        try {
            h.setBlock(new BlockPos(4,2,6),Blocks.STONE);
            var stack=equip(player,"austringer");use(h,player);
            check(h,enemy.getHealth()==enemy.getMaxHealth(),"Solid wall blocks hitscan");
            player.releaseUsingItem();player.setGameMode(GameType.SPECTATOR);int ammo=rounds(stack);use(h,player);
            check(h,rounds(stack)==ammo,"Spectators cannot fire");
            player.setGameMode(GameType.SURVIVAL);
            var preview=WeaponModels.create(entry("austringer"));var tag=preview.get(DataComponents.CUSTOM_DATA).copyTag();tag.putBoolean(WeaponItems.LIVE,true);
            preview.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));player.setItemInHand(InteractionHand.MAIN_HAND,preview);use(h,player);
            check(h,WeaponItems.entry(preview).isEmpty()&&!player.isUsingItem(),"Preview marker alone never becomes combat");h.succeed();
        } finally {enemy.discard();cleanup(player);}
    }

    @GameTest(structure="destiny-test:floor",maxTicks=160, environment = "destiny-test:w90_isolated")
    public void reloadIsDelayedFiniteAndCancelledBySwap(GameTestHelper h) {
        var player=player(h);var stack=equip(player,"beloved");
        var profile=WeaponProfile.forEntry(entry("beloved"));
        WeaponItems.save(stack,new WeaponMagazine(profile,1,2));
        check(h,WeaponRuntime.reload(player),"Reload accepted");
        check(h,rounds(stack)==1,"No early transfer");
        player.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);WeaponRuntime.tickPlayer(player);
        player.setItemInHand(InteractionHand.MAIN_HAND,stack);
        h.runAfterDelay(profile.reloadTicks()+1,()-> {
            try {
                WeaponRuntime.tickPlayer(player);check(h,rounds(stack)==1,"Swap cancels reload without granting ammo");
                check(h,WeaponRuntime.reload(player),"Reload restarts from fresh deadline");
            } catch(Throwable failure){cleanup(player);throw failure;}
        });
        h.runAfterDelay(profile.reloadTicks()*2+3,()-> {
            try {
                WeaponRuntime.tickPlayer(player);check(h,rounds(stack)==3,"Only two reserve rounds transfer at completion");
                check(h,WeaponItems.magazine(stack,profile).reserve()==0,"Reserve is finite");h.succeed();
            } finally {cleanup(player);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=50, environment = "destiny-test:w90_isolated")
    public void nativeAutoStopsOnReleaseAndSkillCancelsChargeWithoutFiring(GameTestHelper h) {
        var player=player(h);
        var stack=WeaponModels.withGrip(equip(player,"ammit_ar2"),WeaponModels.Grip.NATIVE).orElseThrow();
        player.setItemInHand(InteractionHand.MAIN_HAND,stack);use(h,player);
        check(h,player.isUsingItem(),"Native auto uses real hold state");int before=rounds(stack);
        h.runAfterDelay(8,()-> {
            try {
                WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(),player,stack,71992);
                check(h,rounds(stack)<before,"Held auto advances at cadence");
                player.releaseUsingItem();int released=rounds(stack);
                WeaponCombatItem.INSTANCE.onUseTick(h.getLevel(),player,stack,71990);
                check(h,rounds(stack)==released,"Released auto cannot fire");
                var bow=equip(player,"biting_winds");use(h,player);int arrow=rounds(bow);
                WeaponRuntime.cancelUseForSkill(player);player.releaseUsingItem();
                check(h,rounds(bow)==arrow&&WeaponRuntime.activeProjectiles(player)==0,"Skill cancellation never releases a charged arrow");h.succeed();
            } finally {cleanup(player);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=70, environment = "destiny-test:w90_isolated")
    public void chargedBowUsesServerElapsedTimeAndProjectileTravels(GameTestHelper h) {
        var player=player(h);var enemy=target(h,8.5,6.5);var stack=equip(player,"biting_winds");use(h,player);
        check(h,rounds(stack)==1&&WeaponRuntime.activeProjectiles(player)==0,"No projectile before release");
        int charge=WeaponProfile.forEntry(entry("biting_winds")).chargeTicks();
        h.runAfterDelay(charge+1,()-> {
            try {player.releaseUsingItem();check(h,rounds(stack)==0&&WeaponRuntime.activeProjectiles(player)==1,"Charged release spends exactly one arrow");}
            catch(Throwable failure){enemy.discard();cleanup(player);throw failure;}
        });
        h.runAfterDelay(charge+6,()-> {
            try {check(h,enemy.getHealth()<enemy.getMaxHealth(),"Server projectile hits after travel");h.succeed();}
            finally {enemy.discard();cleanup(player);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void twoHandLeaseExpiresBeforeFireAndChargeNeverFiresAfterLostHeartbeat(GameTestHelper h) {
        var player=player(h);var stack=equip(player,"ammit_ar2");use(h,player);
        check(h,!player.isUsingItem(),"Heartbeat protocol does not start native use");
        final int[] expired={-1};
        h.runAfterDelay(WeaponRuntime.HEARTBEAT_LEASE_TICKS,()-> {WeaponRuntime.tickPlayer(player);expired[0]=rounds(stack);});
        h.runAfterDelay(WeaponRuntime.HEARTBEAT_LEASE_TICKS+5,()-> {
            try {
                WeaponRuntime.tickPlayer(player);check(h,rounds(stack)==expired[0],"No auto fire after lease expires");
                equip(player,"erentil_fr4");use(h,player);check(h,WeaponRuntime.activeProjectiles(player)==0,"Fusion begins charge");
            } catch(Throwable failure){cleanup(player);throw failure;}
        });
        h.runAfterDelay(WeaponRuntime.HEARTBEAT_LEASE_TICKS+28,()-> {
            try {check(h,rounds(player.getMainHandItem())==WeaponProfile.forEntry(entry("erentil_fr4")).magazine(),"Lost heartbeat cancels charged fusion before firing");h.succeed();}
            finally {cleanup(player);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void meleeAndProjectileCleanupAreOwnedAndDoNotTouchOtherPlayers(GameTestHelper h) {
        var player=player(h);var other=TestPlayers.create(h,new Vec3(2.5,1,9.5),-90,0);var enemy=target(h,4.5,6.5);
        TestCleanup.register(h, ()->{enemy.discard();cleanup(player);cleanup(other);});
        var sword=equip(player,"goldtusk");int before=rounds(sword);InputRouter.onPunch(player);
        check(h,enemy.getHealth()==enemy.getMaxHealth()&&rounds(sword)==before-1,
                "Sword acceptance pays once but cannot deal HP before the visual contact");
        int delay=kim.biryeong.destiny.weapon.SwordTiming.contactTicks(kim.biryeong.destiny.weapon.SwordProfile.Shape.DASH,false,1);
        h.runAfterDelay(delay,()-> {
            WeaponRuntime.tickPlayer(player);
            check(h,enemy.getHealth()<enemy.getMaxHealth()&&rounds(sword)==before-1,"Sword contact has bounded real melee damage without another payment");
            check(h,other.getHealth()==other.getMaxHealth(),"Players are never weapon targets");
            WeaponRuntime.cleanup(player);equip(player,"bad_omens");use(h,player);
            equip(other,"bad_omens");use(h,other);
            check(h,WeaponRuntime.activeProjectiles(player)==1&&WeaponRuntime.activeProjectiles(other)==1,"Each owner has a server projectile");
            WeaponRuntime.cleanup(player);
            check(h,WeaponRuntime.activeProjectiles(player)==0&&WeaponRuntime.activeProjectiles(other)==1,"Cleanup is owner scoped");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=70, environment = "destiny-test:w90_isolated")
    public void emptyTwoHandTriggerReloadCompletesAfterHeartbeatStops(GameTestHelper h) {
        var player=player(h);var stack=equip(player,"retraced_path");
        var profile=WeaponProfile.forEntry(entry("retraced_path"));
        try {
            WeaponItems.save(stack,new WeaponMagazine(profile,0,3));use(h,player);
            check(h,WeaponRuntime.reloading(player),"Empty two-hand trigger starts reload");
            check(h,!player.isUsingItem()&&rounds(stack)==0,"Reload uses no native hold and grants no early rounds");
        } catch(Throwable failure){cleanup(player);throw failure;}
        h.runAfterDelay(WeaponRuntime.HEARTBEAT_LEASE_TICKS+1,()-> {
            try {
                WeaponRuntime.tickPlayer(player);
                check(h,WeaponRuntime.reloading(player)&&rounds(stack)==0,"Lost firing lease must not cancel reload");
            } catch(Throwable failure){cleanup(player);throw failure;}
        });
        h.runAfterDelay(profile.reloadTicks()-1,()-> {
            try {
                WeaponRuntime.tickPlayer(player);
                check(h,WeaponRuntime.reloading(player)&&rounds(stack)==0,"Auto reload retains its full server deadline");
                check(h,WeaponItems.magazine(stack,profile).reserve()==3,"No reserve is spent before completion");
            } catch(Throwable failure){cleanup(player);throw failure;}
        });
        h.runAfterDelay(profile.reloadTicks()+1,()-> {
            try {
                WeaponRuntime.tickPlayer(player);
                check(h,!WeaponRuntime.reloading(player)&&rounds(stack)==3,"Auto reload completes without renewed input or firing");
                check(h,WeaponItems.magazine(stack,profile).reserve()==0,"Auto reload transfers only finite reserve");h.succeed();
            } finally {cleanup(player);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=70, environment = "destiny-test:w90_isolated")
    public void repeatedHeartbeatsCannotCancelRestartOrQueueFireDuringReload(GameTestHelper h) {
        var automatic=player(h);var manual=TestPlayers.create(h,new Vec3(2.5,1,9.5),-90,0);
        var empty=equip(automatic,"retraced_path");var partial=equip(manual,"retraced_path");
        var profile=WeaponProfile.forEntry(entry("retraced_path"));
        try {
            WeaponItems.save(empty,new WeaponMagazine(profile,0,3));
            WeaponItems.save(partial,new WeaponMagazine(profile,1,2));
            use(h,automatic);check(h,WeaponRuntime.reload(manual),"Explicit reload starts on partial two-hand magazine");
        } catch(Throwable failure){cleanup(automatic);cleanup(manual);throw failure;}
        // Both normal four-tick packets and a gap longer than the firing lease occur during reload.
        for(int delay:new int[]{4,8,12,24,28,32,36}) h.runAfterDelay(delay,()-> {
            try {
                use(h,automatic);use(h,manual);WeaponRuntime.tickPlayer(automatic);WeaponRuntime.tickPlayer(manual);
                check(h,WeaponRuntime.reloading(automatic)&&WeaponRuntime.reloading(manual),"Repeated heartbeat preserves both reloads");
                check(h,rounds(empty)==0&&rounds(partial)==1,"Repeated input neither fires nor transfers rounds early");
            } catch(Throwable failure){cleanup(automatic);cleanup(manual);throw failure;}
        });
        h.runAfterDelay(19,()-> {
            try {
                WeaponRuntime.tickPlayer(automatic);WeaponRuntime.tickPlayer(manual);
                check(h,WeaponRuntime.reloading(automatic)&&WeaponRuntime.reloading(manual),"Heartbeat gap cannot cancel auto or explicit reload");
            } catch(Throwable failure){cleanup(automatic);cleanup(manual);throw failure;}
        });
        h.runAfterDelay(profile.reloadTicks()+1,()-> {
            try {
                WeaponRuntime.tickPlayer(automatic);WeaponRuntime.tickPlayer(manual);
                check(h,!WeaponRuntime.reloading(automatic)&&!WeaponRuntime.reloading(manual),"Packets cannot postpone the original reload deadlines");
                check(h,rounds(empty)==3&&rounds(partial)==3,"Reload input cannot queue a free shot at completion");
                check(h,WeaponItems.magazine(empty,profile).reserve()==0&&WeaponItems.magazine(partial,profile).reserve()==0,"Both reloads conserve ammunition");
            } catch(Throwable failure){cleanup(automatic);cleanup(manual);throw failure;}
        });
        h.runAfterDelay(profile.reloadTicks()+WeaponRuntime.HEARTBEAT_LEASE_TICKS+2,()-> {
            try {
                WeaponRuntime.tickPlayer(automatic);WeaponRuntime.tickPlayer(manual);
                check(h,rounds(empty)==3&&rounds(partial)==3,"No latent heartbeat shot after reload completion");h.succeed();
            } finally {cleanup(automatic);cleanup(manual);}
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void previewEquipCannotOverwriteLiveMagazineOrPendingReload(GameTestHelper h) throws Exception {
        var player=player(h);
        try {
            var stack=equip(player,"ammit_ar2");var profile=WeaponProfile.forEntry(entry("ammit_ar2"));
            WeaponItems.save(stack,new WeaponMagazine(profile,1,2));
            check(h,WeaponRuntime.reload(player),"Live reload starts");var snapshot=stack.copy();
            var dispatcher=h.getLevel().getServer().getCommands().getDispatcher();
            var op=h.getLevel().getServer().createCommandSourceStack().withEntity(player);
            for(String id:new String[]{"ammit_ar2","austringer"}) {
                check(h,dispatcher.execute("destiny weapon equip "+id,op)==0,"Preview equip rejects live item even for the same model");
                check(h,player.getMainHandItem()==stack&&ItemStack.matches(snapshot,stack),"Rejected preview equip preserves live stack and ammunition");
                check(h,WeaponRuntime.reloading(player),"Rejected preview equip preserves pending reload");
            }
            h.succeed();
        } finally {cleanup(player);}
    }
}
