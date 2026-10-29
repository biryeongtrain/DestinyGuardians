package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.Comparator;

/** Actual personal brick transactions and authoritative reserves, not native input/rendering. */
public final class LeadFromGoldW187GameTests {
    static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    static ItemStack item(String id,int rounds,int reserve){
        var e=WeaponCatalog.find(id).orElseThrow();var s=WeaponItems.create(e);
        WeaponItems.save(s,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve));return s;
    }
    static WeaponMagazine ammo(ItemStack stack){return WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()));}
    static void reserve(ItemStack stack,int count){
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow()),ammo(stack).rounds(),count));
    }
    static final class Fixture {
        final GameTestHelper h;final ServerPlayer p;final WeaponCatalog.Entry entry;final WeaponProfile profile;final ItemStack special,heavy;
        Fixture(GameTestHelper h){
            this.h=h;p=TestPlayers.create(h,new Vec3(2.5,1,6.5),-90,0);p.setOnGround(true);p.setNoGravity(true);
            entry=LeadFromGoldProfile.rolls().stream().map(r->WeaponCatalog.find(r.id()).orElseThrow())
                .filter(e->WeaponCharacteristics.of(e).slot()==WeaponSlot.ENERGY&&WeaponCharacteristics.of(e).ammo()==WeaponAmmoType.SPECIAL)
                .sorted(Comparator.comparingInt(e->e.id().equals("hollow_words")?0:1)).findFirst().orElseThrow();
            profile=WeaponProfile.forEntry(entry);special=item(entry.id(),0,0);heavy=item("bad_omens",0,0);
            check(h,WeaponPerks.select(special,LeadFromGoldProfile.ID),"Real exact official source socket selectable");
            p.setAttached(WeaponLoadout.ENABLED,true);p.getInventory().setItem(0,item("austringer",1,0));
            p.getInventory().setItem(1,special);p.getInventory().setItem(2,heavy);p.getInventory().setSelectedSlot(0);
            TestCleanup.register(h,()->{AmmoEconomy.cleanup(p);WeaponRuntime.cleanup(p);CombatHud.remove(p);TestPlayers.remove(p);});
        }
        void brick(boolean heavyType){
            // Explicit earned-meter fixture; actual positive damage/final blow materializes a personal brick.
            p.setAttached(AmmoEconomy.METERS,heavyType?new AmmoMeters(0,AmmoMeters.FULL-1000):new AmmoMeters(AmmoMeters.FULL-2000,0));
            var enemy=h.spawn(EntityTypes.HUSK,new Vec3(5.5,1,6.5));enemy.setNoAi(true);enemy.setPersistenceRequired();
            enemy.getAttribute(Attributes.ARMOR).setBaseValue(0);enemy.setHealth(20);TestCleanup.register(h,enemy::discard);
            Combat.damage(h.getLevel(),p,enemy,100,Element.KINETIC,AmmoGeneration.ABILITY);
            check(h,enemy.isDeadOrDying()&&AmmoEconomy.bricks(p)==1,"One actual personal earned brick");
        }
        void collect(){p.setPos(AmmoEconomy.brickPositions(p).getFirst());AmmoEconomy.tickPlayer(p);TestPlayers.drain(p);}
        int gold(int count){return LeadFromGoldProfile.amount(entry,count);}
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void actualHeavyPickupRewardsStowedReservesOnlyAndConsumesOnce(GameTestHelper h){
        var f=new Fixture(h);f.brick(true);var meters=AmmoEconomy.meters(f.p);f.collect();
        check(h,ammo(f.special).rounds()==0&&ammo(f.special).reserve()==f.gold(1),"Heavy pickup grants stowed Special reserves, never magazine");
        check(h,ammo(f.heavy).reserve()==AmmoGeneration.perBrick(WeaponItems.entry(f.heavy).orElseThrow()),"Existing actual Heavy payout remains");
        check(h,AmmoEconomy.bricks(f.p)==0&&AmmoEconomy.meters(f.p).equals(meters),"Single brick consumed without minting meter progress");
        AmmoEconomy.tickPlayer(f.p);AmmoEconomy.tickPlayer(f.p);
        check(h,ammo(f.special).reserve()==f.gold(1)&&!WeaponRuntime.reloading(f.p),"No duplicate collection or reload transaction");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void fullHeavyStillAllowsActualSpecialBenefit(GameTestHelper h){
        var f=new Fixture(h);int cap=WeaponProfile.forEntry(WeaponItems.entry(f.heavy).orElseThrow()).reserve();reserve(f.heavy,cap);
        f.brick(true);f.collect();check(h,AmmoEconomy.bricks(f.p)==0&&ammo(f.heavy).reserve()==cap&&ammo(f.special).reserve()==f.gold(1),"Full Heavy cannot suppress a funded Special pickup");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void noSpaceRetainsBrickThenOneRoundSpaceConsumesOnce(GameTestHelper h){
        var f=new Fixture(h);reserve(f.heavy,WeaponProfile.forEntry(WeaponItems.entry(f.heavy).orElseThrow()).reserve());reserve(f.special,f.profile.reserve());
        f.brick(true);f.collect();check(h,AmmoEconomy.bricks(f.p)==1,"No recipient space retains the actual brick");
        reserve(f.special,f.profile.reserve()-1);f.collect();check(h,AmmoEconomy.bricks(f.p)==0&&ammo(f.special).reserve()==f.profile.reserve(),"Cap accepts only one available round and consumes the brick once");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void doubleSpecialCountsOtherEquippedSpecialWithoutThePerk(GameTestHelper h){
        var f=new Fixture(h);var other=item("bite_of_the_fox",0,0);f.p.getInventory().setItem(0,other);
        check(h,WeaponCharacteristics.of(WeaponItems.entry(other).orElseThrow()).ammo()==WeaponAmmoType.SPECIAL,"Real kinetic Special equipped");
        f.brick(true);f.collect();check(h,ammo(f.special).reserve()==f.gold(2)&&ammo(other).reserve()==0,"Double Special halves the LFG source; non-LFG recipient gets no bonus");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void backpackOffhandAndClearedSourceCannotBorrowGrant(GameTestHelper h){
        var f=new Fixture(h);f.p.getInventory().setItem(1,ItemStack.EMPTY);f.p.getInventory().setItem(8,f.special);
        var copy=f.special.copy();f.p.setItemInHand(net.minecraft.world.InteractionHand.OFF_HAND,copy);
        f.brick(true);f.collect();check(h,ammo(f.special).reserve()==0&&ammo(copy).reserve()==0,"Backpack and offhand do not count as equipped sources");
        f.p.getInventory().setItem(1,f.special);f.p.getInventory().setItem(8,ItemStack.EMPTY);WeaponPerks.clear(f.special);
        f.p.setPos(h.absoluteVec(new Vec3(2.5,1,6.5)));f.brick(true);f.collect();check(h,ammo(f.special).reserve()==0,"Cleared exact source does not grant");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void anotherOwnerCannotCollectAndReadOrTickDoesNotGrant(GameTestHelper h){
        var a=new Fixture(h);var b=new Fixture(h);a.brick(true);b.p.setPos(AmmoEconomy.brickPositions(a.p).getFirst());AmmoEconomy.tickPlayer(b.p);
        for(int i=0;i<5;i++){CombatHud.update(a.p);WeaponRuntime.tickPlayer(a.p);}
        check(h,AmmoEconomy.bricks(a.p)==1&&ammo(a.special).reserve()==0&&ammo(b.special).reserve()==0,"Owner/range/read boundaries retain brick and no passive ammo");
        a.collect();check(h,ammo(a.special).reserve()==a.gold(1)&&ammo(b.special).reserve()==0,"Only actual owner receives pickup");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void greenBrickIsOnlyOrdinarySpecialPayout(GameTestHelper h){
        var f=new Fixture(h);f.brick(false);f.collect();
        check(h,ammo(f.special).reserve()==AmmoGeneration.perBrick(f.entry)&&ammo(f.special).rounds()==0&&ammo(f.heavy).reserve()==0,"Green brick cannot invoke extra gold grant or reload");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void pickupDuringAcceptedReloadDoesNotRestartOrCreditEarly(GameTestHelper h){
        var f=new Fixture(h);reserve(f.special,1);f.p.getInventory().setSelectedSlot(1);WeaponRuntime.tickPlayer(f.p);
        check(h,WeaponRuntime.reload(f.p),"Real funded manual reload accepted");var before=WeaponRuntime.ammunition(f.p).orElseThrow();
        f.brick(true);f.collect();var after=WeaponRuntime.ammunition(f.p).orElseThrow();
        check(h,after.reloading()&&after.reloadRemaining()==before.reloadRemaining()&&after.reloadDuration()==before.reloadDuration(),"Pickup never restarts accepted reload clock");
        check(h,ammo(f.special).rounds()==0&&ammo(f.special).reserve()==1+f.gold(1),"New reserve is available but no early magazine credit");h.succeed();
    }
    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactOptionalSocketsHaveNoDefaultGrantOrFabricatedHud(GameTestHelper h){
        var ids=LeadFromGoldProfile.rolls().stream().map(WeaponPerks.Roll::id).collect(java.util.stream.Collectors.toSet());check(h,!ids.isEmpty(),"Finite official pool");
        for(var e:WeaponCatalog.all()){var s=WeaponItems.create(e);check(h,WeaponPerks.selected(s,LeadFromGoldProfile.ID).isEmpty(),"No default trait");check(h,WeaponPerks.select(s,LeadFromGoldProfile.ID)==ids.contains(e.id()),"Exact current socket "+e.id());}
        var f=new Fixture(h);CombatHud.update(f.p);check(h,DisplayHud.getHuds(f.p).keySet().stream().noneMatch(k->k.contains("lead_from_gold")),"No fabricated passive buff timer/count");h.succeed();
    }
}
