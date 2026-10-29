package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** Scoped event/ownership/paid charge regressions. Numeric-only Rangefinder has source/path review.
 * These are headless server actions, not native input, screenshots or animation validation. */
public final class PerksW193GameTests {
    private static final String FLOOR="destiny-test:floor",ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h,boolean ok,String why) { h.assertTrue(ok,Component.literal(why)); }
    private static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final List<Husk> targets=new ArrayList<>();
        ItemStack gun;WeaponCatalog.Entry entry;WeaponProfile profile;int slot;
        Fixture(GameTestHelper h) {
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,0,"W193_"+UUID.randomUUID().toString().substring(0,8));
            Guardians.runtime(p);p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            TestCleanup.register(h,()->{targets.forEach(Husk::discard);AmmoEconomy.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void equip(String id,String perk) {
            entry=WeaponCatalog.find(id).orElseThrow();gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,perk),"Exact base socket "+id+"/"+perk);
            profile=WeaponProfile.forEntry(entry);WeaponItems.save(gun,new WeaponMagazine(profile,profile.magazine(),profile.reserve()));
            slot=WeaponCharacteristics.of(entry).slot().hotbar();p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);
            tick();
        }
        void tick() { WeaponRuntime.tickPlayer(p);TestPlayers.drain(p); }
        void select(int index) { p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(index));TestPlayers.drain(p); }
        Husk target(float hp,boolean precision) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(8.5,precision?1:1.8,6));targets.add(t);
            t.setNoAi(true);t.setNoGravity(true);t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1);t.setHealth(hp);return t;
        }
        WeaponMagazine ammo() { return WeaponItems.magazine(gun,profile); }
        int rounds() { return WeaponItems.magazine(gun,profile).rounds(); }
        void face() { p.setYRot(-90);p.setYHeadRot(-90);p.setXRot(0); }
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=220)
    public void ambitiousAssassinActualKillSurvivesCancelledReloadAndStowThenCreditsOnce(GameTestHelper h) {
        var f=new Fixture(h);f.equip("seventh_seraph_officer_revolver","ambitious_assassin");
        var corpse=f.target(1,false);f.face();
        check(h,WeaponRuntime.beginUse(f.p),"Real paid shot accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,!corpse.isAlive()&&WeaponAmbitiousAssassin.kills(f.p)==1,"Actual paid final blow gives one counter");
        int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));
        check(h,WeaponRuntime.reload(f.p),"First timed reload accepted");
        f.select(other);f.tick();f.select(f.slot);f.tick();
        check(h,WeaponAmbitiousAssassin.kills(f.p)==1&&f.rounds()==f.profile.magazine()-1,"Cancelled reload and ordinary stow preserve kills and cannot give ammo");
        h.onEachTick(f::tick);
        h.runAfterDelay(30,()->{
            check(h,WeaponRuntime.reload(f.p),"Second real reload accepted after ready recovery");
            int phase=WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration();
            h.runAfterDelay(phase+1,()->{
                int expected=AmbitiousAssassinProfile.target(f.entry,1);
                check(h,f.rounds()==expected&&WeaponAmbitiousAssassin.kills(f.p)==0,"Single ammo-credit event consumes counter and actually loads extra rounds");
                var hud=WeaponRuntime.ammunition(f.p).orElseThrow();
                check(h,hud.rounds()==expected&&hud.capacity()>=expected,"Existing HUD projection retains over-base loaded rounds");
                int before=f.rounds();f.tick();f.tick();check(h,f.rounds()==before,"Later ticks cannot repeat the transaction");h.succeed();
            });
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=160)
    public void clownCartridgeTimedCreditIsFundedAndCannotRerollOnQueries(GameTestHelper h) {
        var f=new Fixture(h);f.equip("canis_major","clown_cartridge");
        WeaponItems.save(f.gun,new WeaponMagazine(f.profile,0,f.profile.reserve()));
        check(h,WeaponRuntime.reload(f.p),"Real empty magazine reload accepted");
        int phase=WeaponRuntime.ammunition(f.p).orElseThrow().reloadDuration();long total=f.ammo().total();
        check(h,f.rounds()==0,"No early overfill on acceptance or queries");h.onEachTick(f::tick);
        h.runAfterDelay(phase+1,()->{
            int actual=f.rounds();
            int min=ClownCartridgeProfile.target(f.entry,10),max=ClownCartridgeProfile.target(f.entry,50);
            check(h,actual>=min&&actual<=max&&f.ammo().total()==total,"One bounded CC result is paid by finite reserves");
            for(int i=0;i<5;i++){WeaponRuntime.ammunition(f.p);WeaponItems.magazine(f.gun,f.profile);f.tick();}
            check(h,f.rounds()==actual,"Queries and completion replay never reroll or grant");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void fundedLoadedRoundTripAndTraitRevocationPreserveFiniteTotal(GameTestHelper h) {
        var f=new Fixture(h);f.equip("canis_major","clown_cartridge");
        var ammo=f.ammo();long total=ammo.total();int expected=ClownCartridgeProfile.target(f.entry,50);
        check(h,ammo.reloadOverflow(expected)>0,"Explicit funded transfer fixture");WeaponItems.save(f.gun,ammo);
        check(h,f.rounds()==expected&&f.ammo().total()==total,"NBT round-trip restores authorized loaded rounds");
        var copy=f.gun.copy();check(h,WeaponItems.magazine(copy,f.profile).rounds()==expected,"Already-funded ammo survives item copying/transfer serialization");
        WeaponPerks.clear(f.gun);var revoked=f.ammo();
        check(h,revoked.rounds()==f.profile.magazine()&&revoked.total()==total,"Removing trait migrates excess to reserve/debt instead of deleting finite ammo");h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=55)
    public void adagioActualPaidKillBuffsNextEmissionThenStowClearsLiveBenefit(GameTestHelper h) {
        var f=new Fixture(h);f.equip("aishas_embrace","adagio");var corpse=f.target(1,false);f.face();
        check(h,WeaponRuntime.beginUse(f.p),"Real first emission accepted");WeaponRuntime.releaseUse(f.p,f.gun);
        check(h,!corpse.isAlive()&&WeaponAdagio.remaining(f.p)==140,"Real final blow activates duration");
        var victim=f.target(1000,false);h.onEachTick(f::tick);
        h.runAfterDelay((int)Math.ceil(f.profile.cadenceTicks())+2,()->{
            f.face();check(h,WeaponRuntime.beginUse(f.p),"Next paid emission accepted");WeaponRuntime.releaseUse(f.p,f.gun);
            float actual=1000-victim.getHealth();
            check(h,Math.abs(actual-f.profile.damage()*1.3)<.01,"Runtime damage uses the paid Adagio snapshot once");
            var token=WeaponAdagio.capture(f.p);int other=f.slot==0?1:0;f.p.getInventory().setItem(other,new ItemStack(Items.STONE));f.select(other);f.tick();
            check(h,WeaponAdagio.remaining(f.p)==0&&Math.abs(WeaponAdagio.multiplier(f.p,token)-1.3)<.001,"Stow removes live buff but preserves already-paid scalar");
            f.select(f.slot);f.tick();check(h,WeaponAdagio.remaining(f.p)==0,"Returning cannot resurrect outgoing buff");h.succeed();
        });
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=30)
    public void overflowActualFullHeavyPickupRefillsStowedPrimaryAndConsumesOnlyWithGain(GameTestHelper h) {
        var f=new Fixture(h);f.equip("gnawing_hunger","overflow");f.p.setAttached(WeaponLoadout.ENABLED,true);
        var heavyEntry=WeaponCatalog.find("bad_omens").orElseThrow();var heavy=WeaponItems.create(heavyEntry);
        var hp=WeaponProfile.forEntry(heavyEntry);WeaponItems.save(heavy,new WeaponMagazine(hp,hp.magazine(),hp.reserve()));
        f.p.getInventory().setItem(2,heavy);f.p.getInventory().setSelectedSlot(2);f.tick();
        var reserves=WeaponItems.magazine(heavy,hp).reserve();
        f.p.setAttached(AmmoEconomy.METERS,new AmmoMeters(0,AmmoMeters.FULL-1000));
        var corpse=f.target(1,false);
        kim.biryeong.destiny.combat.Combat.damage(f.p.level(),f.p,corpse,100,Element.KINETIC,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(f.p)==1,"Actual earned personal heavy brick");
        f.p.setPos(AmmoEconomy.brickPositions(f.p).getFirst());AmmoEconomy.tickPlayer(f.p);
        check(h,f.rounds()==2*f.profile.magazine()&&AmmoEconomy.bricks(f.p)==0,"Stowed Primary overfills from actual pickup even when Heavy reserves are full");
        check(h,WeaponItems.magazine(heavy,hp).reserve()==reserves,"No phantom heavy reserve gain");
        f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6)));f.p.setAttached(AmmoEconomy.METERS,new AmmoMeters(0,AmmoMeters.FULL-1000));
        var next=f.target(1,false);kim.biryeong.destiny.combat.Combat.damage(f.p.level(),f.p,next,100,Element.KINETIC,AmmoGeneration.ABILITY);
        check(h,AmmoEconomy.bricks(f.p)==1,"Second earned personal brick");f.p.setPos(AmmoEconomy.brickPositions(f.p).getFirst());AmmoEconomy.tickPlayer(f.p);
        check(h,AmmoEconomy.bricks(f.p)==1,"No eligible space retains brick; no free repeated consumption");
        AmmoEconomy.cleanup(f.p);h.succeed();
    }
}
