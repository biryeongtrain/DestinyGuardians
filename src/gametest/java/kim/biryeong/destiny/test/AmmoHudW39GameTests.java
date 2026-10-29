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
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.item.*;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

public final class AmmoHudW39GameTests {
    private static void check(GameTestHelper h, boolean ok, String s) { h.assertTrue(ok,Component.literal(s)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.hunter(h,Element.SOLAR,new Vec3(2,1,6),0,0);
        TestCleanup.register(h, ()->{WeaponRuntime.cleanup(p); TestPlayers.remove(p);});
        return p;
    }
    private static ItemStack equip(ServerPlayer p,String id,int rounds,int reserve) {
        var entry=WeaponCatalog.find(id).orElseThrow();
        var stack=WeaponItems.create(entry);
        WeaponItems.save(stack,new WeaponMagazine(WeaponProfile.forEntry(entry),rounds,reserve));
        p.setItemInHand(InteractionHand.MAIN_HAND,stack);return stack;
    }
    private static ItemDisplayHud node(ServerPlayer p,String suffix) {
        return (ItemDisplayHud)DisplayHud.getHud(p,AmmoHud.PREFIX+suffix);
    }
    private static void digit(GameTestHelper h,ServerPlayer p,String field,int i,int value) {
        check(h,node(p,field+"_"+i).getItem().get(DataComponents.ITEM_MODEL).toString()
                .equals("destiny:gui/hud/ammo_digit_"+value),"Actual transmitted "+field+" glyph "+i+"="+value);
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void magazineReserveAndCachedGlyphsFollowRealShot(GameTestHelper h) {
        var p=player(h);var stack=equip(p,"austringer",10,70);
        CombatHud.update(p);digit(h,p,"rounds",0,1);digit(h,p,"rounds",1,0);
        check(h,node(p,"infinity")!=null&&node(p,"reserve_0")==null,"Primary has actual infinite reserve policy");
        int entity=node(p,"rounds_0").getEntityId();
        var item=node(p,"rounds_0").getItemDisplay().getItemStack();
        TestPlayers.drain(p);CombatHud.update(p);
        check(h,node(p,"rounds_0").getItemDisplay().getItemStack()==item,"Unchanged frame does not replace item metadata");
        check(h,WeaponRuntime.beginUse(p),"Native runtime fires");
        CombatHud.update(p);digit(h,p,"rounds",0,9);
        check(h,node(p,"rounds_1")==null,"10 to 9 removes stale tens glyph");
        check(h,node(p,"rounds_0").getEntityId()==entity,"Count reuses stable display entity");
        check(h,WeaponItems.magazine(stack,WeaponProfile.forEntry(WeaponItems.entry(stack).orElseThrow())).rounds()==9,"HUD read cannot refill");
        check(h,DisplayHud.getHuds(p).keySet().stream().filter(x->x.startsWith(AmmoHud.PREFIX)&&!x.startsWith(AmmoHud.PREFIX+"glaive_")).count()<=12,"Normal ammo HUD bounded");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void all63ProfilesShowExactMagazineReserveAndFamilyWithoutMutatingItems(GameTestHelper h) {
        var p=player(h);
        for(var entry:WeaponCatalog.all()) {
            var profile=WeaponProfile.forEntry(entry);
            var stack=equip(p,entry.id(),profile.magazine(),profile.reserve());
            var before=stack.copy();CombatHud.update(p);
            var state=AmmoHud.current(p).orElseThrow();
            check(h,state.rounds()==profile.magazine()&&state.reserve()==profile.reserve(),"Exact profile "+entry.id());
            check(h,node(p,"weapon").getItem().get(DataComponents.ITEM_MODEL).toString()
                    .equals("destiny:gui/hud/ammo_weapon_w112_"+entry.id()),"Matching actual weapon silhouette");
            for(var field:java.util.List.of("rounds","reserve")) {
                if(field.equals("reserve")&&entry.family().equals("sword")) {
                    check(h,node(p,"infinity")==null&&node(p,"reserve_0")==null&&node(p,"divider")==null,
                            "Sword has a single finite ammo count without reserve UI");
                    continue;
                }
                if(field.equals("reserve")&&profile.infiniteReserve()) {
                    check(h,node(p,"infinity")!=null&&node(p,"reserve_0")==null,"Primary infinity without fake numeric reserve");
                    continue;
                }
                String text=Integer.toString(field.equals("rounds")?profile.magazine():profile.reserve());
                for(int i=0;i<text.length();i++)digit(h,p,field,i,text.charAt(i)-'0');
                check(h,node(p,field+"_"+text.length())==null,"No stale trailing digit after weapon swap");
            }
            check(h,ItemStack.matches(before,stack),"HUD cannot mutate ammo/pose/identity: "+entry.id());
            check(h,DisplayHud.getHuds(p).keySet().stream().filter(x->x.startsWith(AmmoHud.PREFIX)&&!x.startsWith(AmmoHud.PREFIX+"glaive_")).count()<=12,"Bounded per profile");
        }
        p.setHealth(0);CombatHud.update(p);
        check(h,DisplayHud.getHuds(p).isEmpty(),"Death removes ammo as well as ability/health HUD");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void reloadOnlyTransfersAtAuthoritativeDeadlineAndShowsNoEarlyBullets(GameTestHelper h) {
        var p=player(h);equip(p,"retraced_path",2,3);
        check(h,WeaponRuntime.reload(p),"Start reload");CombatHud.update(p);
        check(h,node(p,"reload_track")!=null,"Visible reload track");
        digit(h,p,"rounds",0,2);
        var duration=AmmoHud.current(p).orElseThrow().reloadDuration();
        h.runAfterDelay(duration-1,()->{
            WeaponRuntime.tickPlayer(p);CombatHud.update(p);
            digit(h,p,"rounds",0,2);digit(h,p,"reserve",0,3);
            check(h,node(p,"reload")!=null,"Progress comes from actual remaining server ticks");
        });
        h.runAfterDelay(duration+1,()->{
            WeaponRuntime.tickPlayer(p);CombatHud.update(p);
            digit(h,p,"rounds",0,5);digit(h,p,"reserve",0,0);
            check(h,node(p,"reload_track")==null&&node(p,"reload")==null,"Completion clears progress");
            check(h,!WeaponRuntime.reload(p),"No reserve cannot manufacture ammo");
            h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=90, environment = "destiny-test:w90_isolated")
    public void swapCancelsReloadAndSnapshotCannotBindOrRefillOldItem(GameTestHelper h) {
        var p=player(h);var old=equip(p,"austringer",1,7);
        check(h,WeaponRuntime.reload(p),"Old reload started");
        var fresh=equip(p,"nezarec_s_whisper",6,30);
        var snapshot=WeaponRuntime.ammunition(p).orElseThrow();
        check(h,!snapshot.reloading()&&snapshot.family().equals("glaive"),"Stale old-stack deadline hidden");
        WeaponRuntime.tickPlayer(p);CombatHud.update(p);digit(h,p,"rounds",0,6);
        h.runAfterDelay(40,()->{
            p.setItemInHand(InteractionHand.MAIN_HAND,old);WeaponRuntime.tickPlayer(p);CombatHud.update(p);
            digit(h,p,"rounds",0,1);check(h,node(p,"infinity")!=null,"Old primary reserve remains infinite, magazine not refilled");
            check(h,!AmmoHud.current(p).orElseThrow().reloading(),"Cancelled deadline never completes on return");
            check(h,WeaponItems.entry(fresh).isPresent(),"Swap leaves other stack live");h.succeed();
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=40, environment = "destiny-test:w90_isolated")
    public void emptyCriticalPreviewNonGuardianAndSpectatorCleanup(GameTestHelper h) {
        var p=player(h);equip(p,"retraced_path",0,0);CombatHud.update(p);digit(h,p,"rounds",0,0);
        check(h,node(p,"rounds_0").getItem().get(DataComponents.CUSTOM_MODEL_DATA).getColor(0)==0xF16B5B,"Zero is red");
        check(h,!WeaponRuntime.beginUse(p)&&!WeaponRuntime.reload(p),"Dry trigger/no reserve cannot mint rounds");
        Guardians.data(p).setGuardianClass(GuardianClass.NONE);CombatHud.update(p);
        check(h,node(p,"panel")!=null&&DisplayHud.getHud(p,CombatHud.ABILITIES_ID)==null,"Live non-guardian retains ammo without abilities");
        p.setItemInHand(InteractionHand.MAIN_HAND,WeaponModels.create(WeaponCatalog.find("austringer").orElseThrow()));
        CombatHud.update(p);check(h,node(p,"panel")==null,"Preview never fabricates combat ammunition");
        equip(p,"austringer",2,70);CombatHud.update(p);
        check(h,node(p,"rounds_0").getItem().get(DataComponents.CUSTOM_MODEL_DATA).getColor(0)==0xF2BE75,"Low is amber");
        p.setGameMode(GameType.SPECTATOR);CombatHud.update(p);
        check(h,DisplayHud.getHuds(p).isEmpty(),"Spectator clears all HUD");h.succeed();
    }

    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void goldenGunUsesActualShotsNotTimeAndRestoresNormalMagazine(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->check(h,
                kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(),"Limb ready"))
            .thenExecute(()->{
                var p=player(h);equip(p,"austringer",7,29);Guardians.data(p).setSuperEnergy(1);
                check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Activate Golden Gun");
                CombatHud.update(p);digit(h,p,"rounds",0,3);
                check(h,node(p,"reserve_0")==null&&node(p,"divider")==null,"No fabricated Golden Gun reserves");
                solarStep(h,p,1);
            });
    }
    private static void solarStep(GameTestHelper h,ServerPlayer p,int tick) {
        h.runAfterDelay(1,()->{
            AbilityService.tickPlayer(p);
            if(tick==20) {
                digit(h,p,"rounds",0,3);Guardians.runtime(p).superSession.primary();
                CombatHud.update(p);digit(h,p,"rounds",0,2);
            }
            if(tick==32) {
                Guardians.runtime(p).superSession.primary();CombatHud.update(p);digit(h,p,"rounds",0,1);
            }
            if(tick==44) {
                Guardians.runtime(p).superSession.primary();CombatHud.update(p);digit(h,p,"rounds",0,0);
            }
            if(tick<60)solarStep(h,p,tick+1);
            else {
                check(h,!AbilityService.inSuper(p),"Last-shot dissolve ends super");
                CombatHud.update(p);digit(h,p,"rounds",0,7);check(h,node(p,"infinity")!=null,"Original primary ammo policy restored");
                h.succeed();
            }
        });
    }

    @GameTest(structure="destiny-test:floor",maxTicks=1200, environment = "destiny-test:w90_isolated")
    public void arcSuperHidesOrdinaryWeaponAmmoAndEndRestoresIt(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->check(h,
                kr.toxicity.model.api.BetterModel.limb(kim.biryeong.destiny.fx.HunterModelAssets.MODEL_NAME).isPresent(),"Limb ready"))
            .thenExecute(()->{
                var p=player(h);Guardians.data(p).setLoadout(GuardianClass.HUNTER,
                        kim.biryeong.destiny.ability.hunter.HunterAbilities.preset(Element.ARC));
                equip(p,"austringer",4,12);CombatHud.update(p);
                Guardians.data(p).setSuperEnergy(1);check(h,AbilityService.use(p,AbilitySlot.SUPER)==AbilityService.Result.OK,"Arc cast");
                CombatHud.update(p);check(h,node(p,"panel")==null,"Arc is not a gun magazine");
                AbilityService.endSuper(p);CombatHud.update(p);digit(h,p,"rounds",0,4);h.succeed();
            });
    }
}
