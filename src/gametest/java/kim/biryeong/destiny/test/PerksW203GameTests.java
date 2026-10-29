package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.*;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.ai.attributes.*;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;
import java.util.UUID;

/** Real successful ability use, ammo and HUD. Numeric-only perks get no numeric test matrix. */
public final class PerksW203GameTests {
    /** Production left-click ADS; does not bypass the three-tick toggle debounce. */
    private static void ads(net.minecraft.server.level.ServerPlayer p, boolean requested) {
        if (WeaponAiming.requested(p) != requested) kim.biryeong.destiny.input.InputRouter.onPunch(p);
    }
    private static void check(GameTestHelper h,boolean yes,String message){h.assertTrue(yes,Component.literal(message));}
    private static final class F {
        final GameTestHelper h;final ServerPlayer p;final ItemStack gun;final WeaponCatalog.Entry entry;final WeaponProfile profile;final int slot;
        F(GameTestHelper h,String weapon,String perk){
            this.h=h;p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2.5,1,6),-90,-30,"W203_"+UUID.randomUUID().toString().substring(0,8));
            p.setNoGravity(true);p.setOnGround(true);p.setAttached(WeaponLoadout.ENABLED,false);
            entry=WeaponCatalog.find(weapon).orElseThrow();profile=WeaponProfile.forEntry(entry);gun=WeaponItems.create(entry);
            check(h,WeaponPerks.select(gun,perk),"Select exact base socket");
            WeaponItems.save(gun,new WeaponMagazine(profile,1,0));slot=WeaponCharacteristics.of(entry).slot().hotbar();
            p.getInventory().setItem(slot,gun);p.getInventory().setSelectedSlot(slot);tick();
            TestCleanup.register(h,()->{WeaponRuntime.cleanup(p);AbilityService.cleanup(p);TestPlayers.remove(p);});
        }
        void tick(){WeaponRuntime.tickPlayer(p);TestPlayers.drain(p);}
        int rounds(){return WeaponItems.magazine(gun,profile).rounds();}
        AbilityService.Result grenade(){return AbilityService.use(p,AbilitySlot.GRENADE);}
        void select(int slot){p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));TestPlayers.drain(p);}
        void icon(WeaponCharacteristics.Damage type){
            CombatHud.update(p);var node=(ItemDisplayHud)DisplayHud.getHud(p,AmmoHud.PREFIX+"damage");
            check(h,node!=null && node.getItem().get(DataComponents.ITEM_MODEL).equals(Identifier.parse("destiny:gui/hud/ammo_damage_"+type.name().toLowerCase(java.util.Locale.ROOT))),"Actual ammo HUD element "+type);
        }
    }
    private static void ready(GameTestHelper h,Runnable run){
        h.startSequence().thenWaitUntil(()->check(h,kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(),"Hunter limb ready")).thenExecute(run);
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void acceptedGrenadeConvertsOwnWeaponAndRefillsOnlyOnceUntilRealStow(GameTestHelper h){ready(h,()->{
        var f=new F(h,"steelfeather_repeater","osmosis");f.icon(WeaponCharacteristics.Damage.KINETIC);
        check(h,f.grenade()==AbilityService.Result.OK,"Actual accepted grenade");
        int filled=f.rounds();check(h,filled>1&&WeaponOsmosis.active(f.p),"Actual transfer and conversion at accepted use");
        CombatHud.update(f.p);
        check(h,AmmoHud.current(f.p).isEmpty()&&DisplayHud.getHud(f.p,AmmoHud.PREFIX+"damage")==null,"Active grenade animation hides the weapon HUD");
        check(h,f.grenade()==AbilityService.Result.BUSY&&f.rounds()==filled,"Busy duplicate cannot grant ammunition");
        h.startSequence().thenIdle(kim.biryeong.destiny.ability.GrenadeThrow.DURATION_TICKS+1).thenExecute(()->{
            f.tick();f.icon(WeaponCharacteristics.Damage.SOLAR);
            var before=f.gun.copy();for(int i=0;i<12;i++){WeaponOsmosis.active(f.p);f.icon(WeaponCharacteristics.Damage.SOLAR);}
            check(h,ItemStack.matches(before,f.gun),"HUD polling cannot manufacture another grant");
            check(h,f.grenade()==AbilityService.Result.COOLDOWN&&f.rounds()==filled,"Denied ability never grants ammo after recovery");
            WeaponItems.save(f.gun,new WeaponMagazine(f.profile,1,0));
            AbilityService.resetCooldown(f.p,AbilitySlot.GRENADE);
            check(h,f.grenade()==AbilityService.Result.OK&&f.rounds()==1,"Second accepted grenade before stow cannot refill again");
        }).thenIdle(kim.biryeong.destiny.ability.GrenadeThrow.DURATION_TICKS+1).thenExecute(()->{
            f.tick();int other=f.slot==0?1:0;f.select(other);f.select(f.slot);f.tick();
            check(h,!WeaponOsmosis.active(f.p),"Actual same-tick stow/reselect cancels conversion");f.icon(WeaponCharacteristics.Damage.KINETIC);
        }).thenIdle(1).thenExecute(()->{
            f.tick();AbilityService.resetCooldown(f.p,AbilitySlot.GRENADE);
            check(h,f.grenade()==AbilityService.Result.OK&&f.rounds()>1,"Real stow allows next accepted activation");h.succeed();
        });
    });}
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void grenadeElementAndInventoryIdentityAreLiveButReadersCannotActivate(GameTestHelper h){ready(h,()->{
        var f=new F(h,"seventh_seraph_officer_revolver","osmosis");
        Guardians.data(f.p).setLoadout(GuardianClass.HUNTER,kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.VOID));
        check(h,f.grenade()==AbilityService.Result.OK,"Actual void grenade accepted");
        check(h,WeaponOsmosis.damage(f.p,f.gun,f.entry)==WeaponCharacteristics.Damage.VOID,"Accepted grenade converts original source immediately");
        h.startSequence().thenIdle(kim.biryeong.destiny.ability.GrenadeThrow.DURATION_TICKS+1).thenExecute(()->{
            f.tick();f.icon(WeaponCharacteristics.Damage.VOID);
            var copy=f.gun.copy();f.p.getInventory().setItem(f.slot,copy);f.tick();
            check(h,!WeaponOsmosis.active(f.p),"Equal copied stack cannot inherit original episode");f.icon(WeaponCharacteristics.Damage.KINETIC);
            WeaponPerks.clear(copy);AbilityService.resetCooldown(f.p,AbilitySlot.GRENADE);int rounds=WeaponItems.magazine(copy,f.profile).rounds();
            check(h,f.grenade()==AbilityService.Result.OK&&WeaponItems.magazine(copy,f.profile).rounds()==rounds,"Ordinary grenade has no unselected perk refill");h.succeed();
        });
    });}
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void liveAdsPerkEditRefreshesOnlyOwnedModifiersAndForeignCloneWins(GameTestHelper h){
        var f=new F(h,"duke_mk_44","moving_target");
        // Test actual modifier ownership refresh rather than another per-perk value matrix.
        ads(f.p,true);WeaponAiming.tick(f.p);
        h.startSequence().thenIdle(4).thenExecute(()->{
        f.tick();
        var speed=f.p.getAttribute(Attributes.MOVEMENT_SPEED);var id=Identifier.parse("destiny:weapon_ads_movement_w75");
        var initial=speed.getModifier(id);check(h,initial!=null,"Accepted ADS installs owned movement");
        WeaponPerks.clear(f.gun);WeaponAiming.tick(f.p);var plain=speed.getModifier(id);
        check(h,plain!=null&&plain!=initial&&plain.amount()!=initial.amount(),"Actual perk edit refreshes held owned pair");
        var foreign=new AttributeModifier(id,plain.amount(),plain.operation());speed.removeModifier(id);speed.addTransientModifier(foreign);
        check(h,WeaponPerks.select(f.gun,"moving_target"),"Reselect exact source");WeaponAiming.tick(f.p);
        check(h,speed.getModifier(id)==foreign,"Equal-valued foreign takeover cannot be overwritten on scalar refresh");
        ads(f.p,false);WeaponAiming.tick(f.p);WeaponAiming.cleanup(f.p);
        check(h,speed.getModifier(id)==foreign,"Release preserves foreign identity");speed.removeModifier(id);h.succeed();
        });
    }
}
