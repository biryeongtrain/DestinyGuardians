package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.combat.*;
import kim.biryeong.destiny.crucible.CrucibleRuntime;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.core.BlockPos;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.AttributeInstance;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.*;
import java.util.*;

/** Nine base exotics, without catalysts. All mutation is on the authoritative server tick.
 * DDC Exotic Weapons gid441434520 rows16/39/50/83/90/104/130/148/152, read 2026-11-09.
 * Secondary D2-unit ratios are applied to the existing per-weapon local MC damage budget.
 * Unknown DDC flight/seek/physics quantities and work limits below are explicit local policies.
 * No activity, encounter, wall clock, inventory copy or global mutable player timer owns a shot.
 */
public final class ExoticWeaponsW350 {
    public static final Set<String> IDS = Set.of("crimson","thorn","outbreak_perfected","sunshot","graviton_lance",
            "jotunn","gjallarhorn","whisper_of_the_worm","tractor_cannon");
    private static final int MAX_WORK = 384, MAX_TARGETS = 32, MAX_CHAINS = 64;
    private static final Identifier SCIENCE_SPEED = DestinyGuardians.id("scientific_method_w350");
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final class Slot {
        final ItemStack stack; final WeaponCatalog.Entry entry;
        final ExoticCycleW350.PrecisionChain nail = new ExoticCycleW350.PrecisionChain();
        OutlawCycle outlaw = new OutlawCycle();
        final IdentityHashMap<LivingEntity, ExoticCycleW350.RapidHits> rapid = new IdentityHashMap<>();
        long soulUntil; int generation;
        Slot(ItemStack stack, WeaponCatalog.Entry entry) { this.stack=stack;this.entry=entry; }
    }
    private static final class Session {
        final ServerPlayer owner; final ServerLevel level;
        final GuardianData data; final GuardianClass guardianClass; final GuardianRuntime runtime;
        final IdentityHashMap<ItemStack, Slot> slots = new IdentityHashMap<>();
        final List<Work> work = new ArrayList<>();
        final IdentityHashMap<LivingEntity, Burn> scorch = new IdentityHashMap<>();
        final IdentityHashMap<LivingEntity, Nanites> nanites = new IdentityHashMap<>();
        final Set<LivingEntity> remnants = Collections.newSetFromMap(new WeakHashMap<>());
        long packUntil, scienceUntil, lastTick = Long.MIN_VALUE;
        AttributeInstance speed; AttributeModifier modifier; boolean yielded;
        Session(ServerPlayer p) {
            owner=p;level=p.level();data=Guardians.data(p);
            guardianClass=data==null?null:data.guardianClass();runtime=Guardians.runtimeIfPresent(p).orElse(null);
        }
        void releaseSpeed() {
            if(speed!=null&&modifier!=null&&speed.getModifier(SCIENCE_SPEED)==modifier)speed.removeModifier(SCIENCE_SPEED);
            modifier=null;
        }
    }
    private record Burn(Token token, ExoticCycleW350.Scorch stacks) {}
    private record Nanites(Token token, int count, long until) {}
    public static final class Token {
        public static final Token NONE = new Token(null,null,null,null,false,0,false);
        final Session session; final Slot slot; final ItemStack stack; final WeaponCatalog.Entry entry;
        final boolean direct, wolfpack; final int generation; final float base;
        final Set<LivingEntity> contacts = Collections.newSetFromMap(new IdentityHashMap<>());
        boolean resolved, detonated;
        Token(Session s, Slot slot, ItemStack stack, WeaponCatalog.Entry entry, boolean direct, float base, boolean wolfpack) {
            session=s;this.slot=slot;this.stack=stack;this.entry=entry;this.direct=direct;this.base=base;this.wolfpack=wolfpack;
            generation=slot==null?0:slot.generation;
        }
        public Token splash() { return NONE; }
    }
    private interface Work { boolean advance(Session session, long now); }
    private ExoticWeaponsW350() {}
    private static long now(ServerPlayer p) { return p.level().getServer().getTickCount(); }
    private static boolean usable(ServerPlayer p) {
        return p!=null&&p.isAlive()&&!p.isRemoved()&&!p.isSpectator()&&!p.hasDisconnected()&&!AbilityService.inSuper(p);
    }
    public static boolean supports(WeaponCatalog.Entry entry) {
        return entry!=null&&IDS.contains(entry.id())&&WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                &&WeaponCharacteristics.of(entry).exotic();
    }
    private static boolean owns(ServerPlayer p, ItemStack stack) {
        if(stack==null||stack.isEmpty()||stack.getCount()!=1)return false;
        for(int i=0;i<p.getInventory().getContainerSize();i++)if(p.getInventory().getItem(i)==stack)return true;
        return false;
    }
    private static Session session(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s!=null&&(s.owner!=p||!live(s))) { s.releaseSpeed();SESSIONS.remove(p.getUUID(),s);s=null; }
        if(s==null) { s=new Session(p);SESSIONS.put(p.getUUID(),s); }
        return s;
    }
    private static boolean live(Session s) {
        return usable(s.owner)&&s.owner.level()==s.level
                &&s.owner.getAttachedOrElse(Guardians.DATA,null)==s.data
                &&(s.data==null||s.data.guardianClass()==s.guardianClass)
                &&Guardians.runtimeIfPresent(s.owner).orElse(null)==s.runtime&&now(s.owner)>=s.lastTick;
    }
    private static boolean valid(Token t) {
        return t!=null&&t!=Token.NONE&&live(t.session)
                &&SESSIONS.get(t.session.owner.getUUID())==t.session&&owns(t.session.owner,t.stack)
                &&WeaponItems.entry(t.stack).filter(t.entry::equals).isPresent()
                &&(t.slot==null||t.slot.generation==t.generation);
    }
    /** Exact firing-time receipt, called only after cartridge payment, once per physical bullet. */
    public static Token capture(ServerPlayer p) {
        var entry=WeaponItems.entry(p.getMainHandItem()).orElse(null);
        if(!usable(p)||entry==null||!WeaponLoadout.canUse(p))return Token.NONE;
        var existing=SESSIONS.get(p.getUUID());
        boolean pack=entry.family().equals("rocket_launcher")&&!WeaponCharacteristics.of(entry).exotic()
                &&existing!=null&&existing.owner==p&&live(existing)&&existing.packUntil>now(p);
        if(!supports(entry)&&!pack)return Token.NONE;
        var s=session(p);var stack=p.getMainHandItem();
        var slot=s.slots.computeIfAbsent(stack, ignored->new Slot(stack,entry));
        var token=new Token(s,slot,stack,entry,true,WeaponProfile.forEntry(entry).damage(),pack||entry.id().equals("gjallarhorn"));
        if(entry.id().equals("gjallarhorn"))grantPack(p);
        return token;
    }
    public static float directMultiplier(Token token, LivingEntity target) {
        if(!valid(token)||!token.direct)return 1;
        return token.entry.id().equals("outbreak_perfected")?ExoticCycleW350.parasitism(nanites(target),target instanceof ServerPlayer):1;
    }
    public static float bulletScale(WeaponCatalog.Entry entry, int index) {
        if(entry.id().equals("graviton_lance"))return ExoticCycleW350.gravitonBolt(index);
        if(entry.id().equals("sunshot"))return 71f/154f;
        return 1;
    }
    public static WeaponBallistics.Profile ballistics(WeaponCatalog.Entry entry,int bolt,WeaponBallistics.Profile base) {
        return entry.id().equals("graviton_lance")&&bolt>0
                ?new WeaponBallistics.Profile(base.start(),base.end(),1,base.precision()):base;
    }
    /** Positive actual-loss only; one contact receipt per normalized living recipient. */
    public static void confirmed(ServerPlayer p,Token t,LivingEntity target,boolean precision,float actual,boolean killed,
                                 CombatantShields.Snapshot shield) {
        if(!valid(t)||t.session.owner!=p||!t.direct||!(actual>0)||!Float.isFinite(actual)||!t.contacts.add(target))return;
        switch(t.entry.id()) {
            case "crimson" -> {
                if(killed) {
                    p.heal(p.getMaxHealth()*32f/(CrucibleRuntime.participating(p)?230f:200f));
                    GuardianRecovery.startRegeneration(p);
                    if(precision)refill(t,0,false);
                }
            }
            case "thorn" -> {
                if(killed)remnant(t,target);
                else poison(t,target);
            }
            case "outbreak_perfected" -> {
                // Original Bungie3824673936 socket3 fixed Outlaw1168162263 (not a random/catalyst trait).
                if(killed&&precision&&p.getMainHandItem()==t.stack)
                    t.slot.outlaw.precisionKilled(now(p),OutlawProfile.perk().durationTicks());
                if(t.slot.rapid.size()>=MAX_TARGETS&&!t.slot.rapid.containsKey(target))t.slot.rapid.remove(t.slot.rapid.keySet().iterator().next());
                if(t.slot.rapid.computeIfAbsent(target,k->new ExoticCycleW350.RapidHits()).confirmed(now(p)))seek(t,target.getBoundingBox().getCenter(),3,SeekerKind.NANITE,null);
                if(killed&&precision)seek(t,target.getBoundingBox().getCenter(),9,SeekerKind.NANITE,null);
            }
            case "sunshot","graviton_lance" -> {
                if(t.entry.id().equals("sunshot")&&target.isAlive())target.addEffect(new MobEffectInstance(MobEffects.GLOWING,20,0));
                if(killed)chain(t,target);
            }
            case "jotunn" -> disorient(t,target,shield);
            case "whisper_of_the_worm" -> {
                if(t.slot.nail.confirmed(now(p),precision,actual))refill(t,1,true);
            }
            case "tractor_cannon" -> tractor(t,target);
            default -> { }
        }
    }
    public static void resolved(Token t, boolean geometryHit) {
        if(!valid(t)||t.resolved)return;
        t.resolved=true;
        if(!t.entry.id().equals("whisper_of_the_worm"))return;
        if(!geometryHit) {
            t.slot.nail.clear();
            if(ExoticCycleW350.mulligan(false,t.session.owner.getRandom().nextInt(100)))generate(t,1);
        }
    }
    private static void changed(ServerPlayer p) {p.getInventory().setChanged();p.containerMenu.broadcastChanges();}
    private static void generate(Token t,int count) {
        if(!valid(t))return;
        var ammo=WeaponItems.magazine(t.stack,WeaponProfile.forEntry(t.entry));
        if(ammo.generateLoaded(count)>0){WeaponItems.save(t.stack,ammo);changed(t.session.owner);}
    }
    private static void refill(Token t,int generate,boolean nail) {
        if(!valid(t)||t.session.owner.getMainHandItem()!=t.stack)return;
        var p=t.session.owner;var ammo=WeaponItems.magazine(t.stack,WeaponProfile.forEntry(t.entry));
        if(WeaponRuntime.reloadOwnedBy(p,t.stack))WeaponRuntime.cancelForTraitRefill(p,t.stack);
        int granted=ammo.generateLoaded(generate);
        int loaded=nail?ammo.reloadRounds(2):ammo.reload();
        if(granted+loaded>0){WeaponItems.save(t.stack,ammo);changed(p);}
    }
    private static boolean add(Session s,Work work) {
        if(s.work.size()>=MAX_WORK)return false;
        s.work.add(work);return true;
    }
    private static Element element(Token t) {
        return switch(WeaponCharacteristics.of(t.entry).damage()) {
            case ARC->Element.ARC;case SOLAR->Element.SOLAR;case VOID->Element.VOID;default->Element.KINETIC;
        };
    }
    private static float units(Token t,LivingEntity target,float pve,float pvp,float reference) {
        return target instanceof ServerPlayer?target.getMaxHealth()*pvp/230f:t.base*pve/reference;
    }
    private record Loss(boolean hit,boolean killed) {}
    /** Secondary transactions preserve weapon economy, owner/region routing, immunity and actual loss.
     * They intentionally bypass direct-hit/precision refund/legendary on-hit callbacks. */
    private static Loss damage(Token t,LivingEntity contact,float amount) {
        if(!valid(t)||!Combat.isEnemy(t.session.owner,contact)||contact.level()!=t.session.level)return new Loss(false,false);
        var target=Combat.damageOwner(contact);float before=Combat.damagePool(contact);
        boolean killed;
        try(var emission=Combat.emission(new Object())) {
            killed=Combat.damage(t.session.level,t.session.owner,contact,amount,element(t),AmmoGeneration.weapon(t.entry));
        }
        float actual=before-Combat.damagePool(contact);
        if(!(actual>0)||!Float.isFinite(actual))return new Loss(false,false);
        kim.biryeong.destiny.hud.WeaponHitHud.confirm(t.session.owner,actual,killed);
        float shown=target instanceof ServerPlayer?actual*230f/target.getMaxHealth():actual;
        kim.biryeong.destiny.fx.WeaponDamageNumbers.confirm(t.session.owner,t.session.level,target.getBoundingBox().getCenter(),shown,false);
        return new Loss(true,killed);
    }
    private static boolean clear(Token t,Vec3 from,Vec3 to) {
        if(!valid(t)||!WeaponWavefront.loadedSegment(t.session.level,from,to))return false;
        var wall=t.session.level.clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,t.session.owner));
        return wall.getType()==HitResult.Type.MISS||from.distanceToSqr(wall.getLocation())+1e-5>=from.distanceToSqr(to);
    }
    private static List<LivingEntity> targets(Token t,Vec3 center,double radius) {
        if(!valid(t)||!t.session.level.hasChunkAt(BlockPos.containing(center)))return List.of();
        var seen=Collections.newSetFromMap(new IdentityHashMap<LivingEntity,Boolean>());
        return Combat.enemiesNear(t.session.level,t.session.owner,center,radius).stream()
                .filter(e->seen.add(Combat.damageOwner(e))&&clear(t,center,e.getBoundingBox().getCenter())).limit(MAX_TARGETS).toList();
    }
    private static void poison(Token t,LivingEntity target) {
        // DDC first pulse .3s, following .5s: ticks6/16/26/36. Corruption instances stack.
        final boolean devour=t.slot.soulUntil>now(t.session.owner);
        add(t.session,new Work(){int left=4;long due=now(t.session.owner)+6;
            public boolean advance(Session s,long tick) {
                if(!valid(t)||!target.isAlive()||target.level()!=s.level)return false;
                if(tick<due)return true;
                // PvP Soul Devourer 1750?% is unknown in DDC; +200% is used only in PvE.
                // DDC1750?% PvP boost stays unsupported until verified.
                float amount=units(t,target,30*(devour?3:1),.4f,70);
                var loss=damage(t,target,amount);
                if(loss.killed)remnant(t,target);
                due+=10;return --left>0&&!loss.killed;
            }});
    }
    private static void remnant(Token t,LivingEntity corpse) {
        if(!valid(t)||!t.session.remnants.add(corpse))return;
        add(t.session,new Work(){Vec3 at=corpse.getBoundingBox().getCenter();final long end=now(t.session.owner)+160;
            public boolean advance(Session s,long tick) {
                if(!valid(t)||tick>=end)return false;
                var goal=s.owner.position().add(0,.8,0);double d=at.distanceTo(goal);
                if(d<=1.2) {
                    var ammo=WeaponItems.magazine(t.stack,WeaponProfile.forEntry(t.entry));
                    // Remnant is the explicitly generated reward, up to the sourced 40-round ceiling.
                    ammo.generateLoadedOverflow(4,40);WeaponItems.save(t.stack,ammo);changed(s.owner);
                    t.slot.soulUntil=ExoticCycleW350.extendSoul(tick,t.slot.soulUntil);return false;
                }
                if(d<=15&&clear(t,at,goal))at=at.add(goal.subtract(at).normalize().scale(Math.min(.45,d)));
                if(tick%4==0)Fx.ring(s.level,at,.15,0x7FAE55,6);
                return true;
            }});
    }
    private enum SeekerKind { NANITE, VOID_ORB, WOLFPACK }
    private static void seek(Token t,Vec3 center,int count,SeekerKind kind,Chain chain) {
        for(int i=0;i<count;i++) {
            double a=Math.PI*2*i/count;
            add(t.session,new Seeker(t,center.add(Math.cos(a)*.25,.2,Math.sin(a)*.25),kind,chain));
        }
    }
    private static final class Seeker implements Work {
        final Token t;final SeekerKind kind;final Chain chain;final long end;
        Vec3 at;LivingEntity target;
        Seeker(Token t,Vec3 at,SeekerKind kind,Chain chain){this.t=t;this.at=at;this.kind=kind;this.chain=chain;end=now(t.session.owner)+60;}
        public boolean advance(Session s,long tick) {
            if(!valid(t)||tick>=end||!s.level.hasChunkAt(BlockPos.containing(at)))return false;
            if(target==null||!target.isAlive()||target.level()!=s.level||!Combat.isEnemy(s.owner,target))
                target=targets(t,at,12).stream().findFirst().orElse(null);
            if(target==null)return true;
            Vec3 goal=target.getBoundingBox().getCenter();double distance=at.distanceTo(goal);
            Vec3 next=at.add(goal.subtract(at).normalize().scale(Math.min(kind==SeekerKind.WOLFPACK?.9:.55,distance)));
            if(!clear(t,at,next))return false;
            Fx.line(s.level,at,next,kind==SeekerKind.NANITE?0xCB3333:element(t).color(),.3,.35f);at=next;
            if(distance>1)return true;
            float amount=switch(kind) {
                case NANITE->units(t,target,77,13,27);
                case VOID_ORB->units(t,target,51,20,52);
                case WOLFPACK->t.base*.0325f; // Local aggregate 26% baseline; exact per-missile units not in DDC.
            };
            var loss=damage(t,target,amount);
            if(loss.hit&&kind==SeekerKind.NANITE&&target.isAlive()) {
                var previous=s.nanites.get(target);int n=previous!=null&&previous.until>tick?previous.count:0;
                if(s.nanites.size()<MAX_TARGETS||previous!=null)s.nanites.put(target,new Nanites(t,Math.min(100,n+1),tick+180));
            }
            if(loss.killed&&kind==SeekerKind.VOID_ORB&&chain!=null)chain.enqueue(target);
            return false;
        }
    }
    private static int nanites(LivingEntity target) {
        int count=0;
        for(var s:SESSIONS.values()) {
            var n=s.nanites.get(target);
            if(n!=null&&n.until>now(s.owner)&&s.level==target.level()&&valid(n.token))count+=n.count;
        }
        return Math.min(100,count);
    }
    private static final class Chain {
        final Token t;final Set<LivingEntity> corpses=Collections.newSetFromMap(new IdentityHashMap<>());
        Chain(Token t){this.t=t;}
        void enqueue(LivingEntity corpse) {
            if(!valid(t)||corpses.size()>=MAX_CHAINS||!corpses.add(corpse))return;
            Vec3 center=corpse.getBoundingBox().getCenter();
            add(t.session,new Work(){boolean ran;
                public boolean advance(Session s,long now){if(ran)return false;ran=true;blast(center);return false;}});
        }
        void blast(Vec3 center) {
            boolean sun=t.entry.id().equals("sunshot");double radius=sun?6:7;
            for(var enemy:targets(t,center,radius)) {
                double distance=center.distanceTo(enemy.getBoundingBox().getCenter());
                float fall=(float)Math.max(sun?.4:0,1-distance/radius*(sun?.6:1));
                var loss=damage(t,enemy,units(t,enemy,sun?432:470,sun?160:100,sun?154:52)*fall);
                if(loss.hit&&sun&&enemy.isAlive())solarScorch(t,enemy);
                if(loss.killed)enqueue(Combat.damageOwner(enemy));
            }
            Fx.ring(t.session.level,center,radius,element(t).color(),28);
            if(!sun)seek(t,center,2,SeekerKind.VOID_ORB,this);
        }
    }
    private static void chain(Token t,LivingEntity corpse) {new Chain(t).enqueue(corpse);}
    private static void solarScorch(Token t,LivingEntity target) {
        var s=t.session;var burn=s.scorch.get(target);
        if(burn==null) {
            if(s.scorch.size()>=MAX_TARGETS)return;
            burn=new Burn(t,new ExoticCycleW350.Scorch());s.scorch.put(target,burn);
        }
        boolean ignite=burn.stacks.add(now(s.owner),10);
        if(burn.stacks.stacks(now(s.owner))>0)Statuses.markScorched(target,46+(int)Math.ceil(burn.stacks.stacks(now(s.owner))/1.25));
        if(ignite) {
            var captured=burn.token;Vec3 center=target.getBoundingBox().getCenter();
            add(s,new Work(){public boolean advance(Session session,long tick){
                for(var enemy:targets(captured,center,8)) {
                    float fall=enemy instanceof ServerPlayer?(float)Math.max(0,1-center.distanceTo(enemy.getBoundingBox().getCenter())/8):1;
                    damage(captured,enemy,units(captured,enemy,676,120,154)*fall);
                }
                Fx.ring(session.level,center,8,Element.SOLAR.color(),32);return false;
            }});
        }
    }
    private static void tickScorch(Session s,long tick) {
        for(var iterator=s.scorch.entrySet().iterator();iterator.hasNext();) {
            var entry=iterator.next();var target=entry.getKey();var burn=entry.getValue();
            if(!target.isAlive()||target.level()!=s.level||!valid(burn.token)||burn.stacks.expired(tick)){iterator.remove();continue;}
            if(!burn.stacks.pulse(tick))continue;
            int stacks=burn.stacks.stacks(tick);
            // DDC Solar row11 gives PvE formula and bracketed PvP examples with rounding.
            float pve=2.7f+.175f*stacks;
            if(CombatantRank.of(target)!=CombatantRank.BOSS)pve*=1.2f;
            float pvp=(2.7f+.175f*stacks)*.57f; // Local normalization of DDC rounded x30/50/80 examples.
            float amount=Math.min(units(burn.token,target,pve,pvp,154),Math.max(0,(target.getHealth()-.1f)/1.3f));
            if(amount>0)damage(burn.token,target,amount);
        }
    }
    /** Sunburn explodes even on terrain. Impact damage was split before the ray transaction. */
    public static void sunburn(Token t,HitResult hit) {
        if(!valid(t)||!t.entry.id().equals("sunshot")||hit==null||hit.getType()==HitResult.Type.MISS)return;
        Vec3 center=hit.getLocation().subtract(t.session.owner.getLookAngle().scale(.04));
        for(var target:targets(t,center,3)) {
            float fall=(float)Math.max(0,1-center.distanceTo(target.getBoundingBox().getCenter())/3);
            var loss=damage(t,target,units(t,target,83,24,154)*fall);
            if(loss.killed)chain(t,Combat.damageOwner(target));
        }
        Fx.ring(t.session.level,center,1,Element.SOLAR.color(),12);
    }
    /** Jotunn's one paid charge owns impact, blast and seven .25-second burn pulses. */
    public static boolean projectileImpact(Token t,Vec3 center,LivingEntity direct) {
        if(!valid(t)||!t.entry.id().equals("jotunn"))return false;
        if(t.detonated)return true; // The paid projectile owns exactly one impact and one burn field.
        t.detonated=true;
        kim.biryeong.destiny.sound.DestinySounds.at(t.session.level,center,
                kim.biryeong.destiny.sound.DestinySounds.weaponKey(t.entry,"impact"),.8f);
        if(direct!=null&&Combat.isEnemy(t.session.owner,direct)) {
            var shield=CombatantShields.snapshot(Combat.damageOwner(direct));
            var loss=damage(t,direct,units(t,direct,1184,160,1453));
            if(loss.hit)disorient(t,Combat.damageOwner(direct),shield);
        }
        for(var target:targets(t,center,7)) {
            var shield=CombatantShields.snapshot(Combat.damageOwner(target));
            float fall=(float)Math.max(0,1-center.distanceTo(target.getBoundingBox().getCenter())/7);
            var loss=damage(t,target,units(t,target,269,40,1453)*fall);
            if(loss.hit)disorient(t,Combat.damageOwner(target),shield);
        }
        add(t.session,new Work(){int left=7;long due=now(t.session.owner)+5;
            public boolean advance(Session s,long tick){
                if(!valid(t))return false;if(tick<due)return true;
                for(var target:targets(t,center,2))damage(t,target,units(t,target,46,8,1453));
                Fx.ring(s.level,center,2,Element.SOLAR.color(),12);
                due+=5;return --left>0;
            }});
        return true;
    }
    private static void disorient(Token t,LivingEntity target,CombatantShields.Snapshot shield) {
        if(shield!=null&&shield.matches(WeaponCharacteristics.Damage.SOLAR)&&shield.broken(target)) {
            var r=PerkBatchCProfile.disorient();
            for(var e:targets(t,target.getBoundingBox().getCenter(),r.radius()))Statuses.apply(t.session.owner,e,Keyword.BLINDED,r.ticks());
        }
    }
    public static void rocketDetonated(Token t,Vec3 center) {
        if(!valid(t)||!t.wolfpack||t.detonated)return;
        t.detonated=true;seek(t,center,8,SeekerKind.WOLFPACK,null);
    }
    /** Jotunn/Gjallarhorn launch acquisition: local 12-degree, 64-block visible cone, no ADS lease.
     * Fixed target, finite steering, actual segment collision remains WeaponRuntime's authority. */
    static LivingEntity launchTarget(ServerPlayer p,WeaponCatalog.Entry entry) {
        if(!entry.id().equals("jotunn")&&!entry.id().equals("gjallarhorn"))return null;
        var from=p.getEyePosition();
        return Combat.enemiesNear(p,from,64).stream().filter(e->{
            var to=e.getBoundingBox().getCenter();
            return p.getLookAngle().dot(to.subtract(from).normalize())>=Math.cos(Math.toRadians(12))
                    &&WeaponWavefront.loadedSegment(p.level(),from,to)
                    &&p.level().clip(new ClipContext(from,to,ClipContext.Block.COLLIDER,ClipContext.Fluid.NONE,p)).getType()==HitResult.Type.MISS;
        }).findFirst().orElse(null);
    }
    static Vec3 steer(ServerPlayer owner,LivingEntity target,Vec3 at,Vec3 velocity) {
        if(target==null||target.level()!=owner.level()||!Combat.isEnemy(owner,target)
                ||!owner.level().hasChunkAt(BlockPos.containing(target.position())))return velocity;
        var desired=target.getBoundingBox().getCenter().subtract(at);
        var result=TrackingSteering.turn(new TrackingSteering.Vector(velocity.x,velocity.y,velocity.z),
                new TrackingSteering.Vector(desired.x,desired.y,desired.z),Math.toRadians(4));
        return new Vec3(result.x(),result.y(),result.z());
    }
    public static boolean pulse(Token t,WeaponProfile profile) {
        if(!valid(t)||!t.entry.id().equals("tractor_cannon"))return false;
        var p=t.session.owner;var from=p.getEyePosition();
        for(var target:targets(t,from,10)) {
            var direction=target.getBoundingBox().getCenter().subtract(from);
            if(direction.lengthSqr()>1e-6&&p.getLookAngle().dot(direction.normalize())<Math.cos(Math.toRadians(35)))continue;
            float fall=(float)Math.max(.1,1-direction.length()/10*.9);
            var loss=damage(t,target,units(t,target,982,100,982)*fall);
            if(loss.hit)tractor(t,Combat.damageOwner(target));
        }
        Fx.ring(p.level(),from.add(p.getLookAngle().scale(2)),1.2,Element.VOID.color(),20);
        return true;
    }
    private static void tractor(Token t,LivingEntity target) {
        var p=t.session.owner;
        if(target.isAlive()) {
            Statuses.apply(p,target,Keyword.SUPPRESSED,200);
            Statuses.applyWeaken(p,target,200,1.30f,1.30f);
            var rank=CombatantRank.of(target);
            if(rank!=CombatantRank.MINIBOSS&&rank!=CombatantRank.BOSS&&rank!=CombatantRank.VEHICLE) {
                var away=target.position().subtract(p.position());
                if(away.lengthSqr()>1e-6) {target.push(away.normalize().scale(1.2).add(0,.15,0));}
            }
        }
        if(t.session.scienceUntil<=now(p)) {t.session.scienceUntil=now(p)+100;t.session.yielded=false;}
    }
    private static boolean ally(ServerPlayer p,ServerPlayer other) {
        return other!=p&&usable(other)&&other.level()==p.level()&&!Combat.isEnemy(p,other)
                &&(p.getTeam()==null&&other.getTeam()==null||p.isAlliedTo(other));
    }
    private static void grantPack(ServerPlayer p) {
        for(var other:p.level().players())if(ally(p,other)&&p.distanceToSqr(other)<=225)
            session(other).packUntil=now(p)+300;
    }
    private static boolean nearbyAlly(ServerPlayer p) {
        for(var other:p.level().players())if(ally(p,other)&&p.distanceToSqr(other)<=225)return true;
        return false;
    }
    public static int handlingTicks(ServerPlayer p,ItemStack stack,boolean ready,int base) {
        if(!usable(p)||!owns(p,stack))return base;
        var e=WeaponItems.entry(stack).orElse(null);if(e==null)return base;
        var s=SESSIONS.get(p.getUUID());
        int bonus=s!=null&&s.owner==p&&live(s)&&s.scienceUntil>now(p)?35:0;
        if(e.id().equals("gjallarhorn")&&nearbyAlly(p))bonus+=50;
        return WeaponStatCurves.handlingTicks(e.id(),ready,base,bonus,1);
    }
    public static WeaponReloadPolicy.Plan reloadPlan(ServerPlayer p,WeaponCatalog.Entry e,WeaponReloadPolicy.Plan plan) {
        if(e.id().equals("outbreak_perfected")&&outlawRemaining(p)>0
                &&WeaponItems.entry(p.getMainHandItem()).filter(e::equals).isPresent()) {
            var perk=OutlawProfile.perk();
            return new WeaponReloadPolicy.Plan(WeaponStatCurves.reloadTicks(e.id(),plan.firstTicks(),perk.reloadBonus(),perk.durationMultiplier()),
                    WeaponStatCurves.reloadTicks(e.id(),plan.intervalTicks(),perk.reloadBonus(),perk.durationMultiplier()),plan.roundsPerInsert());
        }
        if(!usable(p)||!e.id().equals("gjallarhorn")||!nearbyAlly(p))return plan;
        return new WeaponReloadPolicy.Plan(WeaponStatCurves.reloadTicks(e.id(),plan.firstTicks(),50,.9),
                WeaponStatCurves.reloadTicks(e.id(),plan.intervalTicks(),50,.9),plan.roundsPerInsert());
    }
    /** Fixed Outlaw uses the same sourced base perk window and exact held-stack ownership. */
    public static int outlawRemaining(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());
        if(s==null||s.owner!=p||!live(s))return 0;
        var slot=s.slots.get(p.getMainHandItem());
        return slot!=null&&slot.entry.id().equals("outbreak_perfected")&&owns(p,slot.stack)
                &&WeaponItems.entry(slot.stack).filter(slot.entry::equals).isPresent()
                ?slot.outlaw.remaining(now(p),OutlawProfile.perk().durationTicks()):0;
    }
    public static int packRemaining(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());return s!=null&&s.owner==p&&live(s)?(int)Math.max(0,s.packUntil-now(p)):0;
    }
    public static void stowing(ServerPlayer p,ItemStack stack) {
        var s=SESSIONS.get(p.getUUID());if(s==null||s.owner!=p)return;
        var slot=s.slots.get(stack);if(slot!=null){slot.nail.clear();slot.rapid.clear();slot.outlaw=new OutlawCycle();}
        // Soul Devourer, Pack Hunter and Scientific Method explicitly persist through stow.
    }
    public static void tick(MinecraftServer server) {
        for(var s:List.copyOf(SESSIONS.values())) {
            if(s.level.getServer()!=server)continue;
            if(!live(s)){cleanup(s.owner);continue;}
            long tick=now(s.owner);if(s.lastTick==tick)continue;s.lastTick=tick;
            s.slots.values().removeIf(slot->{
                if(owns(s.owner,slot.stack)&&WeaponItems.entry(slot.stack).filter(slot.entry::equals).isPresent())return false;
                slot.generation++;return true;
            });
            for(var slot:s.slots.values())slot.rapid.keySet().removeIf(e->!e.isAlive()||e.level()!=s.level);
            tickScorch(s,tick);
            s.nanites.entrySet().removeIf(e->!e.getKey().isAlive()||e.getKey().level()!=s.level||e.getValue().until<=tick||!valid(e.getValue().token));
            // Drain a snapshot, so chains/remnants cannot recurse or invalidate the iteration.
            var work=List.copyOf(s.work);s.work.clear();
            for(var task:work)if(task.advance(s,tick))add(s,task);
            updateSpeed(s,tick);
            if(s.slots.isEmpty()&&s.work.isEmpty()&&s.scorch.isEmpty()&&s.packUntil<=tick&&s.scienceUntil<=tick)SESSIONS.remove(s.owner.getUUID(),s);
        }
    }
    private static void updateSpeed(Session s,long tick) {
        var p=s.owner;
        boolean walking=!p.isSprinting()&&!p.isPassenger()&&!p.getAbilities().flying&&!p.isFallFlying()
                &&!p.isSwimming()&&!p.isInWater()&&!p.isInLava()&&!p.onClimbable()&&!p.isVisuallyCrawling();
        if(s.scienceUntil<=tick||!walking){s.releaseSpeed();return;}
        if(s.yielded)return;
        var current=p.getAttribute(Attributes.MOVEMENT_SPEED);
        if(current==null){s.releaseSpeed();return;}
        if(s.modifier!=null){if(s.speed==current&&current.getModifier(SCIENCE_SPEED)==s.modifier)return;s.releaseSpeed();s.yielded=true;return;}
        if(current.hasModifier(SCIENCE_SPEED)){s.yielded=true;return;}
        s.speed=current;s.modifier=new AttributeModifier(SCIENCE_SPEED,.4,AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);
        current.addTransientModifier(s.modifier); // Shared port's maximum-Mobility mapping: walking x1.4.
    }
    public static void cleanup(ServerPlayer p) {
        var s=SESSIONS.get(p.getUUID());if(s!=null&&s.owner==p){s.releaseSpeed();SESSIONS.remove(p.getUUID(),s);}
    }
    public static void clearAll(){for(var s:SESSIONS.values())s.releaseSpeed();SESSIONS.clear();}
    public static int pending(ServerPlayer p){var s=SESSIONS.get(p.getUUID());return s!=null&&s.owner==p?s.work.size():0;}
    public static int soulRemaining(ServerPlayer p){var s=SESSIONS.get(p.getUUID());if(s==null||s.owner!=p)return 0;var slot=s.slots.get(p.getMainHandItem());return slot==null?0:(int)Math.max(0,slot.soulUntil-now(p));}
}
