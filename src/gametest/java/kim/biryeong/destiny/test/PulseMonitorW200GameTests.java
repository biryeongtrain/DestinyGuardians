package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import net.minecraft.world.phys.Vec3;
import java.util.UUID;

/** Real native hurtServer plus source ownership/ammo/reader regressions.
 * Master registers this class and runs it AFTER shared integration. No native client inputs. */
public final class PulseMonitorW200GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h;
        final ServerPlayer p;
        ItemStack gun;
        WeaponProfile profile;
        Fixture(GameTestHelper h) {
            this.h=h;
            p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W200P_"+UUID.randomUUID().toString().substring(0,7));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            p.getAttribute(Attributes.ARMOR).setBaseValue(0);p.getAttribute(Attributes.ARMOR_TOUGHNESS).setBaseValue(0);
            p.getAttribute(Attributes.MAX_ABSORPTION).setBaseValue(40);p.setHealth(p.getMaxHealth());p.setAbsorptionAmount(0);
            TestCleanup.register(h,()->{WeaponPulseMonitor.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void equip(String id,int slot,int rounds,int reserve) {
            var entry=WeaponCatalog.find(id).orElseThrow();gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,PulseMonitorProfile.ID),"Exact original Pulse tuple: "+id);
            profile=WeaponProfile.forEntry(entry);WeaponItems.save(gun,new WeaponMagazine(profile,rounds,reserve));
            p.getInventory().setItem(slot,gun);
        }
        WeaponMagazine ammo() { return WeaponItems.magazine(gun,profile); }
        void select(int slot) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));TestPlayers.drain(p); }
        void spendOne() { var ammo=ammo();check(h,ammo.consume(),"Consume previously funded round");WeaponItems.save(gun,ammo); }
        float hurt(float amount) {
            p.damageCooldownTime=0;float before=p.getHealth();
            p.hurtServer(p.level(),p.damageSources().generic(),amount);return before-p.getHealth();
        }
        void recover() { p.setHealth(p.getMaxHealth());WeaponPulseMonitor.update(p); }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void realNativeLossRefillsStowedOriginalFromFiniteReservesAndSurvivesSelection(GameTestHelper h) {
        var f=new Fixture(h);f.equip("first_in_last_out",1,0,3);
        var other=WeaponItems.create(WeaponCatalog.find("cold_denial").orElseThrow());
        f.p.getInventory().setItem(0,other);f.p.getInventory().setSelectedSlot(0);
        var tag=f.gun.get(DataComponents.CUSTOM_DATA).copyTag();tag.putString("w200_foreign","preserve");
        f.gun.set(DataComponents.CUSTOM_DATA,CustomData.of(tag));
        long total=f.ammo().total();
        check(h,f.hurt(f.p.getMaxHealth()*.75f)>0,"Real native damage loses health through PlayerDamageMixin");
        check(h,f.ammo().rounds()==3 && f.ammo().reserve()==0 && f.ammo().total()==total,
            "Actual damage hook immediately transfers stowed finite rounds without a manual update");
        check(h,WeaponPulseMonitor.active(f.p) && WeaponPulseMonitor.handlingBonus(f.p,f.gun)>0,
            "HUD observes actual stowed-source buff without selecting it");
        var observed=f.gun.copy();
        for(int i=0;i<20;i++)check(h,WeaponPulseMonitor.active(f.p),"Stowed HUD polling preserves earned episode");
        check(h,ItemStack.matches(observed,f.gun),"Stowed HUD observation never transfers ammo or writes item");
        check(h,"preserve".equals(f.gun.get(DataComponents.CUSTOM_DATA).copyTag().getStringOr("w200_foreign","")),"Foreign data survives");
        f.spendOne();check(h,f.hurt(.25f)>0,"Repeat low native loss is real");
        WeaponPulseMonitor.update(f.p);check(h,f.ammo().rounds()==2,"Repeat damage/tick never refills same episode");
        f.select(1);check(h,WeaponPulseMonitor.active(f.p),"Stow/ready preserves episode and handling");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void readersNeverBindRefillOrAdoptCopiedAndCountTwoObjects(GameTestHelper h) {
        var f=new Fixture(h);f.equip("first_in_last_out",1,0,6);f.p.getInventory().setSelectedSlot(1);
        f.p.setHealth(f.p.getMaxHealth()*.2f);
        for(int i=0;i<40;i++) {
            check(h,!WeaponPulseMonitor.active(f.p),"Readers do not bind initial low source");
            check(h,WeaponPulseMonitor.handlingBonus(f.p,f.gun)==0 && WeaponPulseMonitor.handlingScalar(f.p,f.gun)==1,"Timing getters do not bind");
        }
        check(h,f.ammo().rounds()==0,"Pure queries do not transfer ammo");
        WeaponPulseMonitor.update(f.p);f.spendOne();int rounds=f.ammo().rounds();
        for(int i=0;i<40;i++) {WeaponPulseMonitor.active(f.p);WeaponPulseMonitor.handlingBonus(f.p,f.gun);WeaponPulseMonitor.handlingScalar(f.p,f.gun);}
        check(h,f.ammo().rounds()==rounds,"Queries after proc cannot refill");
        var original=f.gun;var copy=original.copy();f.p.getInventory().setItem(1,copy);
        check(h,WeaponPulseMonitor.handlingBonus(f.p,copy)==0 && WeaponPulseMonitor.handlingBonus(f.p,original)==0,"Copy does not inherit original session");
        copy.setCount(2);WeaponPulseMonitor.update(f.p);
        check(h,WeaponPulseMonitor.handlingBonus(f.p,copy)==0,"Count-two stack cannot bind");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=65)
    public void recoveryLingerExpiresWithoutQueryRefreshAndRealNextEpisodeRefillsAgain(GameTestHelper h) {
        var f=new Fixture(h);f.equip("first_in_last_out",1,0,12);f.p.getInventory().setSelectedSlot(1);
        check(h,f.hurt(f.p.getMaxHealth()*.75f)>0,"First actual native low episode");f.spendOne();
        int depleted=f.ammo().rounds();f.recover();
        check(h,WeaponPulseMonitor.active(f.p),"Recovery starts linger");
        h.runAfterDelay(19,()->{
            for(int i=0;i<30;i++)check(h,WeaponPulseMonitor.active(f.p),"Reads preserve final linger tick");
            check(h,f.ammo().rounds()==depleted,"Recovery/linger never refills");
        });
        h.runAfterDelay(20,()->{
            check(h,!WeaponPulseMonitor.active(f.p),"Linger expires without a writer or reader refresh");
            check(h,f.hurt(f.p.getMaxHealth()*.75f)>0,"Second actual native low episode");
            check(h,f.ammo().rounds()>depleted,"Observed recovery rearms next episode");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void emptyReservesConsumeEpisodeAndLaterPickupCannotCreateTickRefill(GameTestHelper h) {
        var f=new Fixture(h);f.equip("first_in_last_out",1,0,0);f.p.getInventory().setSelectedSlot(1);
        f.p.setHealth(f.p.getMaxHealth()*.2f);WeaponPulseMonitor.update(f.p);
        check(h,f.ammo().rounds()==0 && WeaponPulseMonitor.active(f.p),"No-reserve proc grants handling only");
        var ammo=f.ammo();check(h,ammo.addReserve(3)==3,"Real reserve pickup fixture");WeaponItems.save(f.gun,ammo);
        WeaponPulseMonitor.update(f.p);check(h,f.ammo().rounds()==0,"Later reserves cannot replay spent low episode");
        f.recover();check(h,f.hurt(f.p.getMaxHealth()*.75f)>0,"New actual low episode");
        check(h,f.ammo().rounds()==3 && f.ammo().reserve()==0,"New episode transfers only available finite ammo");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void coldDenialCoSelectionKeepsPrimaryReserveSemanticsAndUnrelenting(GameTestHelper h) {
        var f=new Fixture(h);f.equip("cold_denial",0,0,0);f.p.getInventory().setSelectedSlot(0);
        check(h,WeaponPerks.select(f.gun,"unrelenting"),"Actual distinct-socket Unrelenting coSelection");
        check(h,WeaponPerks.selected(f.gun,PulseMonitorProfile.ID).isPresent(),"Pulse remains selected");
        check(h,f.profile.infiniteReserve(),"Primary fixture uses existing infinite reserves");
        check(h,f.hurt(f.p.getMaxHealth()*.75f)>0,"Native damage hook with both traits selected");
        check(h,f.ammo().rounds()==f.profile.magazine(),"Primary uses existing reload semantics");
        f.spendOne();WeaponPulseMonitor.update(f.p);
        check(h,f.ammo().rounds()==f.profile.magazine()-1,"Primary is not refilled every low tick");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void absorptionOnlyDamageAboveThresholdAndInvalidLossNeverArmLowHealth(GameTestHelper h) {
        var f=new Fixture(h);f.equip("first_in_last_out",1,0,3);f.p.getInventory().setSelectedSlot(1);
        f.p.setAbsorptionAmount(20);float health=f.p.getHealth();check(h,f.hurt(4)==0,"Hit only spends native absorption");
        check(h,f.p.getHealth()==health && f.ammo().rounds()==0 && !WeaponPulseMonitor.active(f.p),"Absorption does not become a fabricated low-health ratio");
        f.p.setHealth(f.p.getMaxHealth()*.2f);
        WeaponPulseMonitor.damaged(f.p,0);WeaponPulseMonitor.damaged(f.p,Float.NaN);
        check(h,f.ammo().rounds()==0,"Invalid damage callbacks do not observe/bind low source");
        WeaponPulseMonitor.update(f.p);check(h,f.ammo().rounds()==3,"Accepted tick can first-bind an already-low native-health source");
        WeaponPulseMonitor.edited(f.gun);check(h,!WeaponPulseMonitor.active(f.p),"Source edit revokes immediately without reader rebinding");h.succeed();
    }
}
