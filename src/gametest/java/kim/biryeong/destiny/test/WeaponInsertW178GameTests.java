package kim.biryeong.destiny.test;

import eu.pb4.polymer.core.api.item.PolymerItemUtils;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.fabricmc.fabric.api.networking.v1.context.PacketContextProvider;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Real incremental transfers and actual Polymer publication, not native input/render. */
public final class WeaponInsertW178GameTests {
    static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated",ID="first_in_last_out";
    static final net.minecraft.resources.Identifier MODEL=WeaponGripGameTests.projected(net.minecraft.resources.Identifier.parse("destiny:weapon_insert_w208_"+ID+"/"+ID));
    static final CustomModelData SENTINEL=new CustomModelData(List.of(7.25f,.375f,47f,-1f,99f,17.5f),List.of(true,false),List.of("hip","keep"),List.of(0x123456));
    static void check(GameTestHelper h,boolean ok,String why){h.assertTrue(ok,Component.literal(why));}
    static final class Fixture {
        final ServerPlayer p;final WeaponCatalog.Entry entry=WeaponCatalog.find(ID).orElseThrow();
        final WeaponProfile profile=WeaponProfile.forEntry(entry);final ItemStack gun=WeaponItems.create(entry);
        final ItemStack idle;
        Fixture(GameTestHelper h,int reserve){
            p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,-80);
            WeaponItems.save(gun,new WeaponMagazine(profile,0,reserve));p.setItemInHand(InteractionHand.MAIN_HAND,gun);
            tick();gun.set(DataComponents.CUSTOM_MODEL_DATA,SENTINEL);idle=gun.copy();
            h.onEachTick(this::tick);TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        float selector(){return gun.get(DataComponents.CUSTOM_MODEL_DATA).getFloat(4);}
        WeaponMagazine ammo(){return WeaponItems.magazine(gun,profile);}
        ItemStack wire(){var context=((PacketContextProvider)(Object)p.connection).getPacketContext();return PolymerItemUtils.getPolymerItemStack(gun,context,p.level().registryAccess());}
        void route(GameTestHelper h){check(h,WeaponInsertPresentation.ownedBy(p,gun)&&MODEL.equals(wire().get(DataComponents.ITEM_MODEL))&&idle.get(DataComponents.ITEM_MODEL).equals(gun.get(DataComponents.ITEM_MODEL)),"Actual owner receives First In Last Out graph, not Long Arm");}
        void restored(GameTestHelper h){check(h,!WeaponInsertPresentation.active(gun)&&SENTINEL.equals(gun.get(DataComponents.CUSTOM_MODEL_DATA)),"Retirement restores original CMD including unrelated selector values");check(h,WeaponGripGameTests.projected(idle.get(DataComponents.ITEM_MODEL)).equals(wire().get(DataComponents.ITEM_MODEL))&&idle.get(DataComponents.ITEM_MODEL).equals(gun.get(DataComponents.ITEM_MODEL)),"Original wire graph restored");}
    }
    @GameTest(structure=FLOOR,maxTicks=65,environment=ENV)
    public void actualSingleShellInitialLoopAndSixTickReturnFollowFundedDeadlines(GameTestHelper h){
        var f=new Fixture(h,2);check(h,f.profile.shellReload()&&f.profile.roundsPerInsert()==1&&f.profile.firstReloadTicks()==15&&f.profile.reloadTicks()==15,"Unchanged First In Last Out single-shell15tick mechanics");
        check(h,WeaponRuntime.reload(f.p),"Actual empty reload accepted");f.route(h);check(h,f.selector()==0,"Initial phase owns0");
        h.runAfterDelay(14,()->{f.tick();check(h,f.ammo().rounds()==0&&f.ammo().reserve()==2&&f.selector()>0&&f.selector()<1,"No early cartridge; initial gesture advances");});
        h.runAfterDelay(15,()->{f.tick();f.route(h);check(h,f.ammo().rounds()==1&&f.ammo().reserve()==1&&f.selector()==2,"One paid cartridge and persistent held LOOP at exact boundary");});
        h.runAfterDelay(29,()->{f.tick();check(h,f.ammo().rounds()==1&&f.selector()>2&&f.selector()<3,"Second cycle remains LOOP, not repeated HIP raise");});
        h.runAfterDelay(30,()->{f.tick();f.route(h);check(h,f.ammo().rounds()==2&&f.ammo().reserve()==0&&!WeaponRuntime.reloading(f.p)&&f.selector()==4,"Final funded shell starts cosmetic return, no extra ammo or gameplay delay");});
        h.runAfterDelay(36,()->{f.tick();f.restored(h);check(h,f.ammo().rounds()==2&&f.ammo().reserve()==0,"Six cosmetic ticks never create a third shell");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void realShotInterruptsAfterFirstPaidShellAndClearsPropImmediately(GameTestHelper h){
        var f=new Fixture(h,20);check(h,WeaponRuntime.reload(f.p),"Reload accepted");
        h.runAfterDelay(15,()->{f.tick();check(h,f.ammo().rounds()==1&&f.ammo().reserve()==19,"One actual shell inserted");check(h,WeaponRuntime.beginUse(f.p),"Actual trigger interrupts incremental reload");WeaponRuntime.releaseUse(f.p,f.gun);
            check(h,f.ammo().rounds()==0&&f.ammo().reserve()==19,"Exactly one funded shell fired, reserve not fabricated");check(h,!WeaponInsertPresentation.active(f.gun),"No lingering shell prop after shot");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void earlySkillCancelAndCopiedReplacementNeverFundNextShell(GameTestHelper h){
        var f=new Fixture(h,20);check(h,WeaponRuntime.reload(f.p),"Reload accepted");WeaponRuntime.cancelUseForSkill(f.p);f.restored(h);check(h,f.ammo().rounds()==0&&f.ammo().reserve()==20,"Early cancel transfers nothing");
        check(h,WeaponRuntime.reload(f.p),"Second real reload accepted");var copy=f.gun.copy();f.p.setItemInHand(InteractionHand.MAIN_HAND,copy);f.tick();
        check(h,!WeaponInsertPresentation.active(f.gun)&&!WeaponInsertPresentation.active(copy),"Copied selector has no live binding");
        h.runAfterDelay(20,()->{check(h,f.ammo().rounds()==0&&WeaponItems.magazine(copy,f.profile).rounds()==0,"Old deadline cannot grant ammunition to either source");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=15,environment=ENV)
    public void expandedCatalogStillRoutesLongArmSeparatelyAndExcludesOtherSixtyThree(GameTestHelper h){
        new WeaponInsertW71GameTests().actualAimThenReloadRoutesLongArmAndFirstInLastOutAndExcludesOtherCatalogEntries(h);
    }
    @GameTest(structure=FLOOR,maxTicks=55,environment=ENV)
    public void legacyLongArmPairDeadlinesAndLoopAreStillRealServerBehavior(GameTestHelper h){
        new WeaponInsertW71GameTests().acceptedReloadUsesExactFirstAndNextPairDeadlinesWithPureMidLoopReads(h);
    }
    @GameTest(structure=FLOOR,maxTicks=10,environment=ENV)
    public void persistedSelectorAndPreviewAreNotReloadAuthority(GameTestHelper h){
        var f=new Fixture(h,20);var data=new CustomModelData(List.of(0f,0f,0f,0f,2.5f),List.of(true),List.of("hip"),List.of());f.gun.set(DataComponents.CUSTOM_MODEL_DATA,data);
        check(h,!WeaponInsertPresentation.active(f.gun)&&!WeaponInsertPresentation.ownedBy(f.p,f.gun),"Persisted float4 cannot own a reload");check(h,WeaponGripGameTests.projected(f.idle.get(DataComponents.ITEM_MODEL)).equals(f.wire().get(DataComponents.ITEM_MODEL)),"Inert selector does not select insert graph");
        var preview=WeaponModels.create(f.entry);preview.set(DataComponents.CUSTOM_MODEL_DATA,data);check(h,!WeaponInsertPresentation.active(preview),"Model preview inert");check(h,f.ammo().rounds()==0&&f.ammo().reserve()==20,"No ammo from projections");h.succeed();
    }
}
