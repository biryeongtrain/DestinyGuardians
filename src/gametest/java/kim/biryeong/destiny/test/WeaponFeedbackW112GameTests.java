package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicBoolean;

/** Actual owned inventory/cycle/HUD graph tests. Server fixtures are not native-input evidence. */
public final class WeaponFeedbackW112GameTests {
    private static final String FLOOR="destiny-test:w109_arena", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h; final ServerPlayer p;
        Fixture(GameTestHelper h) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(24,1,24),0,-80,"W112_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);
            TestCleanup.register(h,()->{Guardians.runtime(p).superSession=null;WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
            h.onEachTick(()->TestPlayers.drain(p));
        }
        ItemStack equip(String id) {
            WeaponRuntime.cleanup(p);WeaponHandling.cleanup(p);WeaponAiming.cleanup(p);WeaponLoadout.standalone(p);
            p.getInventory().setSelectedSlot(0);
            var gun=WeaponItems.create(WeaponCatalog.find(id).orElseThrow());p.setItemInHand(InteractionHand.MAIN_HAND,gun);return gun;
        }
        void begin() { check(h,WeaponRuntime.heartbeatUse(p),"Accepted real two-hand use heartbeat"); }
        void reticle() { WeaponReticleHud.update(p,0,0,WeaponRuntime.reloading(p)); }
        void idle() { check(h,WeaponRuntime.chargeState(p).phase()==WeaponChargeState.Phase.IDLE,"No live charge/burst projection"); }
    }
    private static int rounds(ItemStack stack) { return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).rounds(); }
    private static long reticleNodes(ServerPlayer p) { return DisplayHud.getHuds(p).keySet().stream().filter(k->k.startsWith(WeaponReticleHud.PREFIX)).count(); }
    private static String model(ServerPlayer p,String id) {
        return ((ItemDisplayHud)Objects.requireNonNull(DisplayHud.getHud(p,id))).getItem().get(DataComponents.ITEM_MODEL).toString();
    }
    private static void same(GameTestHelper h,ItemStack real,ItemStack snapshot) { check(h,ItemStack.matches(real,snapshot),"Read-only HUD retains every real stack component"); }

    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void all65SelectedSilhouettesAreExactOwnedReadOnlyItems(GameTestHelper h) {
        var f=new Fixture(h);check(h,WeaponCatalog.all().size()==65,"Exact selected catalog including two exotics");
        for(var e:WeaponCatalog.all()) {
            var gun=f.equip(e.id());var before=gun.copy();AmmoHud.update(f.p);
            check(h,model(f.p,AmmoHud.PREFIX+"weapon").equals("destiny:gui/hud/ammo_weapon_w112_"+e.id()),"Selected exact weapon silhouette "+e.id());
            same(h,gun,before);f.idle();
        }
        h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void stowedRowsUseRealDistinctWeaponsAndGoldenGunKeepsSuperFallback(GameTestHelper h) {
        var f=new Fixture(h);String[] ids={"ace_of_spades","erentil_fr4","stormchaser"};
        for(int i=0;i<ids.length;i++)f.p.getInventory().setItem(i,WeaponItems.create(WeaponCatalog.find(ids[i]).orElseThrow()));
        f.p.getInventory().setSelectedSlot(0);f.p.setAttached(WeaponLoadout.ENABLED,true);AmmoHud.update(f.p);
        for(int i=0;i<2;i++)check(h,model(f.p,AmmoHud.PREFIX+"stowed_"+i+"_weapon").endsWith("ammo_weapon_w112_"+ids[i+1]),"Stowed exact source, not selected copy/family");
        Guardians.runtime(f.p).superSession=new SuperSession() {
            public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}
            public OptionalInt ammunition(){return OptionalInt.of(3);}public int ammunitionCapacity(){return 3;}
        };
        AmmoHud.update(f.p);check(h,model(f.p,AmmoHud.PREFIX+"weapon").equals("destiny:gui/hud/ammo_golden_gun_w122"),"Golden Gun does not borrow underlying Ace silhouette");
        check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.startsWith(AmmoHud.PREFIX+"stowed_")),"No fabricated stowed rows during super");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=40,environment=ENV)
    public void allSevenChargedGunsExposeZeroProgressWithoutSpendingOrHudMutation(GameTestHelper h) {
        var f=new Fixture(h);int count=0;
        for(var e:WeaponCatalog.all())if(e.family().equals("fusion_rifle")||e.family().equals("linear_fusion_rifle")) {
            var gun=f.equip(e.id());f.idle();f.begin();var before=gun.copy();var state=WeaponRuntime.chargeState(f.p);
            check(h,state.phase()==WeaponChargeState.Phase.CHARGING&&state.progress()==0&&state.emittedBolts()==0,"Actual accepted initial charge "+e.id());
            check(h,state.totalBolts()==WeaponProfile.forEntry(e).burst(),"Exact profile burst, including simultaneous Coriolis/one-bolt LFR");
            for(int i=0;i<8;i++){f.reticle();check(h,WeaponRuntime.chargeState(f.p).equals(state),"Same-tick observation cannot age charge");}
            check(h,reticleNodes(f.p)==6,"Base2+exact4 bounded charge ticks");same(h,gun,before);count++;
        }
        check(h,count==7,"All five fusion/two LFR entries");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void elapsedProgressComesFromServerChargeAndNotRenderCalls(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");f.begin();int tick=f.p.level().getServer().getTickCount();int before=rounds(gun);
        h.runAfterDelay(3,()->{var s=WeaponRuntime.chargeState(f.p);int elapsed=f.p.level().getServer().getTickCount()-tick;
            check(h,s.phase()==WeaponChargeState.Phase.CHARGING&&Math.abs(s.progress()-elapsed/20f)<.00001,"Actual accepted20tick profile clock");
            var saved=gun.copy();for(int i=0;i<20;i++)f.reticle();same(h,gun,saved);check(h,rounds(gun)==before,"No cartridge before actual discharge");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void expiredTwoHandLeaseHidesChargeWithoutPayment(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");int before=rounds(gun);f.begin();
        h.runAfterDelay(9,()->{f.idle();f.reticle();check(h,reticleNodes(f.p)==2&&rounds(gun)==before,"Expired six-tick lease clears only charge feedback and never fires");h.succeed();});
    }
    @GameTest(structure=FLOOR,maxTicks=60,environment=ENV)
    public void paidStormchaserBurstSurvivesReleaseAndNeverPaysPerBolt(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("stormchaser");int before=rounds(gun);f.begin();var renew=new AtomicBoolean(true);
        h.onEachTick(()->{if(renew.get())WeaponRuntime.heartbeatUse(f.p);});
        h.runAfterDelay(12,()->{var s=WeaponRuntime.chargeState(f.p);
            check(h,s.phase()==WeaponChargeState.Phase.BURSTING&&s.emittedBolts()>=1&&s.emittedBolts()<3&&s.totalBolts()==3,"Actual three-bolt paid burst clock");
            check(h,rounds(gun)==before-1,"One shared cartridge at actual first bolt");renew.set(false);WeaponRuntime.releaseUse(f.p,gun);
            check(h,WeaponRuntime.chargeState(f.p).phase()==WeaponChargeState.Phase.BURSTING,"Release does not hide or cancel paid pending bolts");f.reticle();check(h,reticleNodes(f.p)<=6,"Bounded remaining-bolt feedback");
            h.runAfterDelay(10,()->{f.idle();f.reticle();check(h,rounds(gun)==before-1&&reticleNodes(f.p)==2,"All paid bolts done, same cartridge cost, charge tick cleanup");h.succeed();});});
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void manualReloadCancelsChargeAndNeverPredictsAmmo(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");var p=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());WeaponItems.save(gun,new WeaponMagazine(p,1,4));f.begin();
        check(h,WeaponRuntime.reload(f.p),"Actual valid manual reload");f.idle();f.reticle();check(h,reticleNodes(f.p)==0&&rounds(gun)==1,"Reload hides all reticle nodes, real ammo arrives later");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void sameTickSlotAwayBackCannotRestoreOldCharge(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");f.begin();int before=rounds(gun);
        WeaponRuntime.selectedSlotChanging(f.p,1);f.p.getInventory().setSelectedSlot(1);WeaponRuntime.selectedSlotChanging(f.p,0);f.p.getInventory().setSelectedSlot(0);
        f.idle();f.reticle();check(h,rounds(gun)==before&&reticleNodes(f.p)==2,"Real selection hooks revoke old charge in same tick");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void sameTickAcceptedInventoryStowCannotRestoreOldCharge(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");f.begin();int before=rounds(gun);
        WeaponRuntime.inventoryStowing(f.p,gun);f.p.setItemInHand(InteractionHand.MAIN_HAND,ItemStack.EMPTY);f.p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        f.idle();WeaponRuntime.continueUse(f.p);check(h,rounds(gun)==before,"Accepted stow revokes pending original charge, no payment");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void editedDefinitionAndCopiedSourceNeverBorrowLiveCharge(GameTestHelper h) {
        var f=new Fixture(h);var gun=f.equip("erentil_fr4");f.begin();var copy=gun.copy();f.p.setItemInHand(InteractionHand.MAIN_HAND,copy);f.idle();
        f.p.setItemInHand(InteractionHand.MAIN_HAND,gun);var other=WeaponItems.create(WeaponCatalog.find("stormchaser").orElseThrow());
        gun.set(DataComponents.CUSTOM_DATA,other.get(DataComponents.CUSTOM_DATA));gun.set(DataComponents.ITEM_MODEL,other.get(DataComponents.ITEM_MODEL));var saved=gun.copy();
        f.idle();same(h,gun,saved);h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void nativeOneHandChargeRequiresRealUseAndReleaseClearsIt(GameTestHelper h) {
        var f=new Fixture(h);var gun=WeaponModels.withGrip(f.equip("erentil_fr4"),WeaponModels.Grip.NATIVE).orElseThrow();f.p.setItemInHand(InteractionHand.MAIN_HAND,gun);
        check(h,WeaponRuntime.beginUse(f.p),"Actual one-hand native use accepted");f.idle();f.p.startUsingItem(InteractionHand.MAIN_HAND);
        check(h,WeaponRuntime.chargeState(f.p).phase()==WeaponChargeState.Phase.CHARGING,"Actual current owned native use admits charge");int before=rounds(gun);WeaponRuntime.releaseUse(f.p,gun);f.p.stopUsingItem();
        f.idle();check(h,rounds(gun)==before,"Early native release cancels, never partial fusion shot");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void ineligibleSpectatorAndSuperCannotKeepChargeFeedback(GameTestHelper h) {
        var f=new Fixture(h);f.equip("erentil_fr4");f.begin();f.reticle();check(h,reticleNodes(f.p)==6,"Actual active graph before lifecycle change");
        Guardians.runtime(f.p).superSession=new SuperSession() {
            public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}
        };
        f.idle();f.reticle();check(h,reticleNodes(f.p)==0,"Super eligibility removes charge feedback");Guardians.runtime(f.p).superSession=null;
        f.p.setGameMode(GameType.SPECTATOR);f.idle();f.reticle();check(h,reticleNodes(f.p)==0,"Spectator eligibility removes exact prefix");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=30,environment=ENV)
    public void physicalFusionSightsRetainChargeTicksWithoutHipRingOrDot(GameTestHelper h) {
        var f=new Fixture(h);
        for(String id:List.of("erentil_fr4","hollow_words","dream_breaker","null_composure","coriolis_force")) {
            var gun=f.equip(id);f.begin();var saved=gun.copy();
            WeaponReticleHud.update(f.p,1,0,false);
            check(h,reticleNodes(f.p)==4,"Four live charge ticks around physical optic: "+id);
            check(h,DisplayHud.getHud(f.p,WeaponReticleHud.FRAME_ID)==null
                    && DisplayHud.getHud(f.p,WeaponReticleHud.CENTER_ID)==null,"No overlapping hip ring/dot: "+id);
            same(h,gun,saved);
            WeaponRuntime.releaseUse(f.p,gun);
            WeaponReticleHud.update(f.p,1,0,false);
            check(h,reticleNodes(f.p)==0,"Released physical optic removes all charge ticks: "+id);
            WeaponReticleHud.update(f.p,.94f,0,false);
            check(h,reticleNodes(f.p)==2,"Unraised hip ring returns independently: "+id);
        }
        h.succeed();
    }

}
