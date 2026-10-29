package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.GrenadeThrow;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.component.DataComponents;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ServerboundSetCarriedItemPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.InteractionHand;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.monster.zombie.Husk;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;
import java.util.*;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.concurrent.atomic.AtomicReference;

/** W103 real paid combat and AbilityService contact tests. Embedded players are NOT in the
 * server player list: their ordinary player tick is driven once per real GameTest server tick;
 * global WeaponRuntime already iterates its bound STATES; this driver does not duplicate it.
 * Global Tasks/projectiles are advanced only by the existing END_SERVER_TICK event.
 * No profile/clock/cadence rewrites, reflected tokens, manually injected deaths, or native claims.
 * One explicitly named ICD test additionally exercises the public internal release API at the
 * exact deadline; it does not claim a second grenade passed AbilityService's ability cooldown.
 */
public final class DemolitionistW103GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String ENV = "destiny-test:w90_isolated";
    private static final String DEMO = "demolitionist";
    private static final Set<String> IDS = Set.of("austringer","gnawing_hunger","bug_out_bag","lonesome",
            "high_albedo","whispering_slab","first_in_last_out","stormchaser","retraced_path",
            "salvager_s_salvo","nezarec_s_whisper");
    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static WeaponProfile profile(ItemStack gun) {
        return WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
    }
    private static WeaponMagazine ammo(ItemStack gun) { return WeaponItems.magazine(gun,profile(gun)); }
    private static int slot(ItemStack gun) {
        return WeaponCharacteristics.of(WeaponItems.entry(gun).orElseThrow()).slot().hotbar();
    }
    private static int cooldown(ServerPlayer p) { return Guardians.data(p).cooldown(AbilitySlot.GRENADE); }
    private static int full(ServerPlayer p) {
        return AbilityService.equipped(p,AbilitySlot.GRENADE).orElseThrow().cooldownTicks();
    }
    private static void seedCooldown(ServerPlayer p) { Guardians.data(p).setCooldown(AbilitySlot.GRENADE,full(p)); }

    private static final class Fixture {
        final GameTestHelper h;
        final List<ServerPlayer> players = new ArrayList<>();
        final List<Husk> targets = new ArrayList<>();
        Fixture(GameTestHelper h) {
            this.h=h;
            TestCleanup.register(h, () -> {
                for (var target:targets) target.discard();
                for (var p:players) {
                    p.setServerLevel(h.getLevel()); p.stopUsingItem(); WeaponRuntime.cleanup(p);
                    WeaponDemolitionist.cleanup(p); CombatHud.remove(p);
                    if (p.level().players().contains(p)) p.level().removePlayerImmediately(p,Entity.RemovalReason.DISCARDED);
                    TestPlayers.remove(p);
                }
            });
            h.onEachTick(() -> {
                for (var p:players) {
                    AbilityService.tickPlayer(p); TestPlayers.drain(p);
                }
            });
        }
        ServerPlayer player(double z) {
            var p=TestPlayers.hunter(h,Element.ARC,new Vec3(2.5,1,z),-90,0,
                    "W103_"+UUID.randomUUID().toString().substring(0,8));
            p.setAttached(WeaponLoadout.ENABLED,true); p.setNoGravity(true); p.setOnGround(true);
            players.add(p); bounded(p); return p;
        }
        void bounded(Entity entity) {
            var o=h.absoluteVec(Vec3.ZERO); var b=entity.getBoundingBox();
            check(h,b.minX>o.x && b.maxX<o.x+16 && b.minY>o.y && b.maxY<o.y+8
                    && b.minZ>o.z && b.maxZ<o.z+12,"Whole W103 fixture AABB inside committed 16x8x12 floor");
        }
        Husk target(double x, double y, double z, float hp) {
            var t=h.spawn(EntityTypes.HUSK,new Vec3(x,y,z)); targets.add(t);
            t.setNoAi(true); t.setNoGravity(true); t.setPersistenceRequired();
            t.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
            t.getAttribute(Attributes.ARMOR).setBaseValue(0);
            t.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); t.setHealth(hp);
            bounded(t); return t;
        }
        Husk target(ServerPlayer p, float hp) {
            return target(8.5,1.8,p.getZ()-h.absoluteVec(Vec3.ZERO).z,hp);
        }
        ItemStack item(String id, boolean selected, int rounds, int reserve) {
            var e=WeaponCatalog.find(id).orElseThrow(); var gun=WeaponItems.create(e);
            check(h,WeaponPerks.selected(gun,DEMO).isEmpty(),"New stack is never default Demolitionist");
            if (selected) check(h,WeaponPerks.select(gun,DEMO),"Explicit exact official socket: "+id);
            WeaponItems.save(gun,new WeaponMagazine(WeaponProfile.forEntry(e),rounds,reserve)); return gun;
        }
        ItemStack equip(ServerPlayer p, String id, boolean selected, int rounds, int reserve) {
            var gun=item(id,selected,rounds,reserve);
            p.getInventory().setItem(slot(gun),gun); p.getInventory().setSelectedSlot(slot(gun));
            WeaponRuntime.tickPlayer(p); TestPlayers.drain(p); return gun;
        }
        void select(ServerPlayer p, ItemStack gun) {
            check(h,p.getInventory().getItem(slot(gun))==gun,"Selected original occupies actual loadout slot");
            p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot(gun)));
            WeaponRuntime.tickPlayer(p);
        }
        void aim(ServerPlayer p) {
            WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
        }
        void fire(ServerPlayer p) {
            aim(p); var gun=p.getMainHandItem(); var before=ammo(gun);
            // Stable paid-shot geometry; no change to the actual perk or ammunition path.
            p.getRandom().setSeed(0x5DEECE66DL);
            check(h,profile(gun).chargeTicks()==0,"Immediate paid emission fixture");
            check(h,WeaponRuntime.beginUse(p),"Production trigger accepted");
            WeaponRuntime.releaseUse(p,gun);
            check(h,ammo(gun).rounds()==before.rounds()-1 && ammo(gun).reserve()==before.reserve()
                    && ammo(gun).overflow()==before.overflow(),"Exactly one actual paid cartridge, no reserve reward");
        }
        int cast(ServerPlayer p) {
            p.setXRot(-65); int accepted=h.getLevel().getServer().getTickCount();
            check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Actual grenade button accepted");
            check(h,cooldown(p)==full(p),"Acceptance starts unchanged full ability cooldown");
            return accepted;
        }
    }
    private static void digits(GameTestHelper h, ServerPlayer p, String field, int value) {
        CombatHud.update(p); String s=Integer.toString(value);
        for (int i=0;i<s.length();i++) {
            var node=DisplayHud.getHud(p,AmmoHud.PREFIX+field+"_"+i);
            check(h,node instanceof ItemDisplayHud && Identifier.parse("destiny:gui/hud/ammo_digit_"+s.charAt(i))
                    .equals(((ItemDisplayHud)node).getItem().get(DataComponents.ITEM_MODEL)),"Actual server HUD glyph: "+field+" "+i);
        }
        check(h,DisplayHud.getHud(p,AmmoHud.PREFIX+field+"_"+s.length())==null,"No stale HUD digit");
    }
    private static int command(GameTestHelper h,ServerPlayer p,String text) {
        try { return h.getLevel().getServer().getCommands().getDispatcher().execute(text,p.createCommandSourceStack()); }
        catch (com.mojang.brigadier.exceptions.CommandSyntaxException e) { throw new AssertionError(text,e); }
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void exactElevenSocketsAreSelectableButNeverDefaultOrBlanketSpecial(GameTestHelper h) {
        var f=new Fixture(h); var p=f.player(6);
        check(h,DemolitionistProfile.rolls().size()==11,"Exact frozen eleven rows");
        int selected=0;
        for (var e:WeaponCatalog.all()) {
            var gun=WeaponItems.create(e); long before=ammo(gun).total();
            check(h,WeaponPerks.selected(gun,DEMO).isEmpty(),"No default on "+e.id());
            boolean eligible=IDS.contains(e.id());
            check(h,WeaponPerks.select(gun,DEMO)==eligible,"Exact eligibility for "+e.id());
            check(h,WeaponPerks.selected(gun,DEMO).isPresent()==eligible && ammo(gun).total()==before,
                    "Selection alone changes neither ammo nor source identity");
            if (eligible) selected++;
        }
        check(h,selected==11,"Exactly eleven eligible base weapons, no enhanced/family expansion");
        var salvo=f.equip(p,"salvager_s_salvo",true,0,2);
        var roll=WeaponPerks.selected(salvo,DEMO).orElseThrow();
        check(h,roll.hash()==2060863616L && roll.socket()==3 && roll.plugSetHash()==253L
                && roll.perkHash()==3523296417L,"Salvo fixed curated selectable option, not initial/default or randomized");
        check(h,DemolitionistProfile.energyPercent(WeaponCatalog.find("retraced_path").orElseThrow())==10
                && DemolitionistProfile.energyPercent(WeaponCatalog.find("salvager_s_salvo").orElseThrow())==10,
                "Trace and breach GL stay baseline ten, not blanket Special twenty");
        h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=20,environment=ENV)
    public void paidBodyKillsAwardTenAndSlugTwentyFromFullGrenadeBaseOnly(GameTestHelper h) {
        var f=new Fixture(h);
        for (String id:List.of("austringer","first_in_last_out")) {
            var p=f.player(6); var gun=f.equip(p,id,true,3,id.equals("first_in_last_out")?2:0);
            seedCooldown(p); int before=cooldown(p), percent=id.equals("first_in_last_out")?20:10;
            Guardians.data(p).setCooldown(AbilitySlot.MELEE,123); Guardians.data(p).setCooldown(AbilitySlot.CLASS_ABILITY,77);
            var corpse=f.target(p,1); f.fire(p);
            check(h,!corpse.isAlive(),"Real paid body final blow: "+id);
            check(h,cooldown(p)==before-WeaponDemolitionist.grantTicks(full(p),percent),"Correct flat base chunk: "+id);
            check(h,Guardians.data(p).cooldown(AbilitySlot.MELEE)==123
                    && Guardians.data(p).cooldown(AbilitySlot.CLASS_ABILITY)==77,"Other cooldowns untouched");
            check(h,ammo(gun).rounds()==2,"No ammunition minted for grenade-energy reward");
            corpse.discard();
        }
        // Ready and no-grenade loadouts are both pure no-op energy paths despite real paid kills.
        for (boolean noGrenade:new boolean[]{false,true}) {
            var p=f.player(6); f.equip(p,"austringer",true,2,0);
            if (noGrenade) {
                var abilities=new EnumMap<AbilitySlot,Identifier>(AbilitySlot.class);
                abilities.putAll(Guardians.data(p).loadout().orElseThrow().abilities()); abilities.remove(AbilitySlot.GRENADE);
                Guardians.data(p).setLoadout(GuardianClass.HUNTER,new Loadout(abilities));
            }
            var corpse=f.target(p,1); f.fire(p);
            check(h,!corpse.isAlive() && cooldown(p)==0,"Ready or unequipped grenade never gets a new cooldown"); corpse.discard();
        }
        h.succeed();
    }

    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void nonlethalEmptyPlainAndActualMeleeAbilityNeverBorrowHeldTraitCredit(GameTestHelper h) {
        var f=new Fixture(h); var nonlethal=f.player(3); f.equip(nonlethal,"austringer",true,2,0); seedCooldown(nonlethal);
        var healthy=f.target(nonlethal,1000); int before=cooldown(nonlethal); f.fire(nonlethal);
        check(h,healthy.isAlive() && healthy.getHealth()<1000 && cooldown(nonlethal)==before,"Real nonlethal damage gives no energy"); healthy.discard();
        var empty=f.player(6); var noAmmo=f.equip(empty,"first_in_last_out",true,0,0); seedCooldown(empty);
        before=cooldown(empty); check(h,!WeaponRuntime.beginUse(empty),"Empty finite weapon denied");
        check(h,ammo(noAmmo).total()==0 && cooldown(empty)==before,"Denied trigger has no damage credit or ammo");
        var plain=f.player(9); f.equip(plain,"austringer",false,2,0); seedCooldown(plain);
        var plainVictim=f.target(plain,1); before=cooldown(plain); f.fire(plain);
        check(h,!plainVictim.isAlive() && cooldown(plain)==before,"Same official pool without selected trait is inert"); plainVictim.discard();
        var ability=f.player(6); f.equip(ability,"first_in_last_out",true,2,1); seedCooldown(ability);
        var witness=f.player(10); seedCooldown(witness);
        var victim=f.target(4.5,1,6,1);
        check(h,AbilityService.use(ability,AbilitySlot.MELEE)==AbilityService.Result.OK,"Real Arc melee cast accepted with Demo held");
        h.runAfterDelay(8,()-> {
            check(h,!victim.isAlive(),"Real ability contact actually killed the witness");
            check(h,cooldown(ability)==cooldown(witness),"Only identical passive cooldown elapsed, no generic ability-kill reward");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=35,environment=ENV)
    public void onePaidSalvoExplosionCreditsEachCorpseOnceAfterSourceIsStowed(GameTestHelper h) {
        var f=new Fixture(h); var p=f.player(6); var control=f.player(10); seedCooldown(p); seedCooldown(control);
        var source=f.equip(p,"salvager_s_salvo",true,1,0);
        var next=f.item("first_in_last_out",true,2,0); // Same energy slot: move Salvo to inventory, not a copy.
        var a=f.target(8.5,1.8,6,1); var b=f.target(8.5,1.8,7.3,1);
        f.fire(p);
        check(h,WeaponRuntime.activeProjectiles(p)==1,"One real funded projectile before world travel");
        p.getInventory().setItem(9,source); p.getInventory().setItem(slot(source),next);
        WeaponRuntime.tickPlayer(p);
        h.runAfterDelay(16,()-> {
            check(h,!a.isAlive() && !b.isAlive(),"One actual Salvo radial impact earned two distinct final blows");
            int grant=WeaponDemolitionist.grantTicks(full(p),10);
            check(h,cooldown(p)==cooldown(control)-2*grant,"Exactly two ten-percent source rewards, not one emission or new twenty-percent gun");
            check(h,ammo(source).rounds()==0 && ammo(source).total()==0 && ammo(next).rounds()==2,"Paid source conserved after stow; new held gun unaffected");
            check(h,WeaponRuntime.activeProjectiles(p)==0,"Impact retired the one paid projectile");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=35,environment=ENV)
    public void paidProjectilesCannotAwardAfterObservedDropOrTraitRemoval(GameTestHelper h) {
        var f=new Fixture(h); var dropped=f.player(3); var edited=f.player(9); var control=f.player(6);
        seedCooldown(dropped); seedCooldown(edited); seedCooldown(control);
        var first=f.equip(dropped,"salvager_s_salvo",true,1,0);
        var second=f.equip(edited,"salvager_s_salvo",true,1,0);
        var a=f.target(dropped,1); var b=f.target(edited,1);
        f.fire(dropped); f.fire(edited);
        dropped.getInventory().setItem(slot(first),ItemStack.EMPTY); WeaponRuntime.tickPlayer(dropped);
        check(h,WeaponPerks.clear(second),"Direct clear permanently revokes the already-paid projectile token");
        check(h,WeaponPerks.select(second,DEMO),"Immediate same-tick reselect does not resurrect token; no update intervenes");
        h.runAfterDelay(16,()-> {
            check(h,!a.isAlive() && !b.isAlive(),"Both paid projectiles still dealt actual lethal impact damage");
            check(h,cooldown(dropped)==cooldown(control) && cooldown(edited)==cooldown(control),"Invalid original source cannot borrow a current player's trait");
            check(h,ammo(first).total()==0 && ammo(second).total()==0,"Both invalidated shots still paid their ammunition");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void realGrenadeRefillsFiniteReservesOnlyAtExactContactAndUpdatesHud(GameTestHelper h) {
        var f=new Fixture(h); var p=f.player(6); var gun=f.equip(p,"first_in_last_out",true,0,2);
        check(h, GrenadeThrow.RELEASE_TICKS == 6 && GrenadeThrow.DURATION_TICKS == 20,
                "W252 authored throw releases at six ticks and recovers at twenty");
        digits(h,p,"rounds",0); digits(h,p,"reserve",2);
        long total=ammo(gun).total(); int accepted=f.cast(p);
        check(h,WeaponPerks.select(gun,DEMO),"Selecting an already-selected trait is a pure no-op, not token invalidation");
        check(h,ammo(gun).rounds()==0 && SimProjectile.activeCount(p)==0,"Button acceptance grants no refill or projectile");
        AtomicInteger firstRefill=new AtomicInteger(-1), firstProjectile=new AtomicInteger(-1);
        Tasks.run(p,h.getLevel(),age->{
            int elapsed=h.getLevel().getServer().getTickCount()-accepted;
            if (ammo(gun).rounds()>0) firstRefill.compareAndSet(-1,elapsed);
            if (SimProjectile.activeCount(p)>0) firstProjectile.compareAndSet(-1,elapsed);
            return elapsed<7;
        });
        h.runAfterDelay(5,()->check(h,ammo(gun).rounds()==0 && SimProjectile.activeCount(p)==0,"No refill or projectile on the last tick before T+6 contact"));
        h.runAfterDelay(8,()-> {
            check(h,firstRefill.get()==6 && firstProjectile.get()==6,"Projectile launch and refill first observed at authored T+6 contact");
            check(h,ammo(gun).rounds()==2 && ammo(gun).reserve()==0 && ammo(gun).total()==total,"Finite partial refill exactly consumes two real reserves");
            check(h,!WeaponRuntime.reloading(p) && WeaponKillClip.remaining(p)==0,"Not a timed/manual reload or Kill Clip proc");
            CombatHud.update(p);
            check(h,GrenadeThrow.active(p) && AmmoHud.current(p).isEmpty()
                    && DisplayHud.getHuds(p).keySet().stream().noneMatch(id->id.startsWith(AmmoHud.PREFIX)),
                    "T+8 throw recovery hides the entire ammo HUD despite the completed T+6 refill");
        });
        // Register at setup: T+21 observes the completed T+20 END_SERVER_TICK recovery.
        h.runAfterDelay(21,()-> {
            check(h,!GrenadeThrow.active(p),"Authored T+20 throw recovery has completed");
            check(h,ammo(gun).rounds()==2 && ammo(gun).reserve()==0 && ammo(gun).total()==total,
                    "Recovery preserves the exact contact refill without granting more ammunition");
            digits(h,p,"rounds",2); digits(h,p,"reserve",0); h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void cancelledGrenadeWindupsNeverRefillAcrossLifeRuntimeClassAbilityAndLevel(GameTestHelper h) {
        var f=new Fixture(h); var players=new ArrayList<ServerPlayer>(); var guns=new ArrayList<ItemStack>();
        for (int i=0;i<6;i++) {
            var p=f.player(6); var gun=f.equip(p,"first_in_last_out",true,0,2);
            f.cast(p); players.add(p); guns.add(gun);
        }
        AbilityService.cleanup(players.get(0));
        Guardians.forget(players.get(1));
        Guardians.data(players.get(2)).setGuardianClass(GuardianClass.TITAN);
        players.get(3).setHealth(0);
        var fifth=players.get(4);
        Guardians.data(fifth).setLoadout(GuardianClass.HUNTER,Guardians.data(fifth).loadout().orElseThrow()
                .with(AbilitySlot.GRENADE,Identifier.parse("destiny:hunter/solar_incendiary")));
        var other=h.getLevel().getServer().getLevel(h.getLevel().dimension().equals(Level.NETHER)?Level.OVERWORLD:Level.NETHER);
        check(h,other!=null,"Real second test dimension exists"); players.get(5).setServerLevel(other);
        h.runAfterDelay(8,()-> {
            for (int i=0;i<players.size();i++) check(h,ammo(guns.get(i)).rounds()==0 && ammo(guns.get(i)).reserve()==2
                    && SimProjectile.activeCount(players.get(i))==0,"Cancelled windup has neither launch nor refill, case "+i);
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=25,environment=ENV)
    public void grenadeSnapshotRefillsOnlyOriginalOwnedStowedIdentityNeverCopyOrReselectedRevokedSource(GameTestHelper h) {
        var f=new Fixture(h); var p=f.player(3); var replaced=f.player(6); var revoked=f.player(9);
        var original=f.equip(p,"first_in_last_out",true,0,2);
        var next=f.item("austringer",true,1,0); p.getInventory().setItem(slot(next),next);
        var lost=f.equip(replaced,"first_in_last_out",true,0,2);
        var edited=f.equip(revoked,"first_in_last_out",true,0,2);
        f.cast(p); f.cast(replaced); f.cast(revoked);
        f.select(p,next);
        var copy=lost.copy(); replaced.getInventory().setItem(slot(lost),copy); WeaponRuntime.tickPlayer(replaced);
        check(h,WeaponPerks.clear(edited),"Direct clear revokes pending grenade snapshot immediately");
        check(h,WeaponPerks.select(edited,DEMO),"Immediate same-tick reselect cannot resurrect grenade token; no update intervenes");
        h.runAfterDelay(8,()-> {
            check(h,ammo(original).rounds()==2 && ammo(original).reserve()==0,"Still-owned original stowed gun alone receives refill");
            check(h,ammo(next).rounds()==1,"New held weapon is never granted a redirected refill");
            check(h,ammo(lost).rounds()==0 && ammo(copy).rounds()==0 && ammo(copy).reserve()==2,"Equal-looking copy is not original captured identity");
            check(h,ammo(edited).rounds()==0 && ammo(edited).reserve()==2,"Direct edit hook revokes grenade token even without an intervening update");
            check(h,SimProjectile.activeCount(p)==1 && SimProjectile.activeCount(replaced)==1
                    && SimProjectile.activeCount(revoked)==1,"Weapon-source denial does not erase otherwise valid actual grenade launches");
            h.succeed();
        });
    }

    @GameTest(structure=FLOOR,maxTicks=85,environment=ENV)
    public void actualFullMagazineReleaseStartsOwnerIcdThenInternalReleaseApiAcceptsExactDeadlineAcrossEdits(GameTestHelper h) {
        var f=new Fixture(h); var p=f.player(3); var independent=f.player(9);
        var firstEntry=WeaponCatalog.find("gnawing_hunger").orElseThrow();
        var gun=f.equip(p,firstEntry.id(),true,WeaponProfile.forEntry(firstEntry).magazine(),0);
        var nextEntry=WeaponCatalog.find("austringer").orElseThrow();
        var next=f.item(nextEntry.id(),true,WeaponProfile.forEntry(nextEntry).magazine()-1,0);
        p.getInventory().setItem(slot(next),next);
        var other=f.equip(independent,"first_in_last_out",true,0,2);
        int accepted=f.cast(p); int startRounds=ammo(gun).rounds();
        AtomicReference<WeaponDemolitionist.GrenadeToken> consumed=new AtomicReference<>(), boundary=new AtomicReference<>();
        AtomicInteger moved=new AtomicInteger(-1);
        Tasks.run(p,h.getLevel(),age->{
            int elapsed=h.getLevel().getServer().getTickCount()-accepted;
            if (elapsed==8) check(h,SimProjectile.activeCount(p)>0 && ammo(gun).rounds()==startRounds,
                    "Actual full-magazine release is a no-op refill, still starts ICD");
            if (elapsed==21) {
                check(h, !GrenadeThrow.active(p), "Original twenty-tick throw recovery is complete before firing");
                f.fire(p); // Real paid miss creates space without inventing ammo.
                f.select(p,next); consumed.set(WeaponDemolitionist.grenadeAccepted(p));
                check(h,WeaponDemolitionist.grenadeReleased(p,consumed.get())==0,"Another selected stack cannot bypass owner lock");
                f.cast(independent);
            }
            if (elapsed==23) {
                check(h,command(h,p,"destiny perk clear")==1 && command(h,p,"destiny perk select demolitionist")==1,
                        "Real selection commands invalidate source, not owner ICD");
            }
            if (elapsed==29) check(h,ammo(other).rounds()==2 && ammo(other).reserve()==0,"Independent owner is not locked by first player's release");
            if (elapsed==65) {
                check(h, WeaponDemolitionist.grenadeReleased(p, WeaponDemolitionist.grenadeAccepted(p)) == 0,
                        "One tick before the original owner ICD deadline still denies refill");
                boundary.set(WeaponDemolitionist.grenadeAccepted(p));
                check(h,ammo(next).rounds()==profile(next).magazine()-1,"No refill before original T+6+60 deadline");
            }
            if (elapsed==66) {
                moved.set(WeaponDemolitionist.grenadeReleased(p,boundary.get()));
                check(h,moved.get()==1 && ammo(next).rounds()==profile(next).magazine(),"Accepted during ICD but released at exact deadline may refill");
                check(h,WeaponDemolitionist.grenadeReleased(p,boundary.get())==0
                        && WeaponDemolitionist.grenadeReleased(p,consumed.get())==0,"Every commit token is consumed once, including denied releases");
            }
            return elapsed<68;
        });
        h.runAfterDelay(70,()-> { check(h,moved.get()==1,"Exact deadline branch executed on real server clock"); h.succeed(); });
    }

    @GameTest(structure=FLOOR,maxTicks=110,environment=ENV)
    public void realChargedBowAndGlaiveProjectileKeepTenAndTwentyBaseEnergy(GameTestHelper h) {
        var f=new Fixture(h); var bow=f.player(3); var glaive=f.player(9); var control=f.player(6);
        var bowGun=f.equip(bow,"whispering_slab",true,1,0); var glaiveGun=f.equip(glaive,"nezarec_s_whisper",true,1,0);
        seedCooldown(bow); seedCooldown(glaive); seedCooldown(control);
        var a=f.target(bow,1); var b=f.target(glaive,1);
        f.aim(bow); bow.startUsingItem(InteractionHand.MAIN_HAND);
        check(h,bow.isUsingItem() && bow.getUseItem()==bowGun,"Actual native bow use session owns the draw");
        check(h,profile(bowGun).chargeTicks()>0 && WeaponRuntime.beginUse(bow),"Actual bow draw accepted, not fabricated instant fire");
        check(h,ammo(bowGun).rounds()==1 && a.isAlive(),"Draw acceptance has no paid shot or kill");
        int draw=profile(bowGun).chargeTicks();
        h.runAfterDelay(draw+1,()-> {
            check(h,ammo(bowGun).rounds()==1,"Held real draw still retains its one cartridge until release");
            WeaponRuntime.releaseUse(bow,bowGun); bow.stopUsingItem();
            check(h,ammo(bowGun).rounds()==0,"Actual release paid one arrow");
            f.fire(glaive);
        });
        h.runAfterDelay(draw+20,()-> {
            check(h,!a.isAlive() && !b.isAlive(),"Real drawn arrow and real glaive projectile actually killed their separate witnesses");
            check(h,cooldown(bow)==cooldown(control)-WeaponDemolitionist.grantTicks(full(bow),10),"Bow source baseline ten");
            check(h,cooldown(glaive)==cooldown(control)-WeaponDemolitionist.grantTicks(full(glaive),20),"Glaive projectile exception twenty");
            check(h,ammo(glaiveGun).rounds()==0 && ammo(glaiveGun).total()==0,"Glaive attack stayed finite and funded");
            h.succeed();
        });
    }
}
