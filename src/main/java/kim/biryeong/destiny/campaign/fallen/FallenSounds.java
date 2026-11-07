package kim.biryeong.destiny.campaign.fallen;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import kim.biryeong.destiny.sound.DestinySounds;
import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayDeque;
import java.util.Deque;
import java.util.HashMap;
import java.util.Map;
import java.util.Random;

/**
 * Destiny 2 Fallen SFX for the Guardian Rises enemies (W300 r6). Each {@link Ev} is a curated D2 sound event
 * (see docs/design/guardian-rises/fallen-audio.md) shipped as {@code destiny:guardian_rises.fallen.<event>} with up to
 * eight mono variants; the client picks a variant. Positional HOSTILE packets with a fixed attenuation range per
 * category. If the key is missing from sounds.json the vanilla fallback (if any) plays instead.
 * Barks go through {@link BarkGate}: per-mob and per-event cooldowns plus a global budget of
 * {@link BarkGate#BUDGET} barks per second within {@link BarkGate#RADIUS} m, so a squad of Dregs does not chatter over itself.
 */
public final class FallenSounds {
    private FallenSounds() {}

    /** Attenuation range (blocks), volume and pitch jitter per category. */
    enum Cat {
        GUN(48, kim.biryeong.destiny.sound.EnemySoundMix.COMBAT, .06f), IMPACT(16, .45f, .05f), FLYBY(12, .4f, .08f), MELEE(24, .5f, .06f),
        BARK(24, .45f, .05f), DEATH(24, kim.biryeong.destiny.sound.EnemySoundMix.DEATH, .05f),
        FOLEY(20, kim.biryeong.destiny.sound.EnemySoundMix.FOLEY, .05f), WALKER(64, .6f, .04f), SKIFF(64, .6f, .03f);
        final float range, volume, jitter;
        Cat(float range, float volume, float jitter) { this.range = range; this.volume = volume; this.jitter = jitter; }
    }

    public enum Ev {
        SHOCK_PISTOL_FIRE("shock_pistol_fire", Cat.GUN, () -> SoundEvents.SHULKER_SHOOT),
        WIRE_RIFLE_FIRE("wire_rifle_fire", Cat.GUN, () -> SoundEvents.SHULKER_SHOOT),
        SHRAPNEL_LAUNCHER_FIRE("shrapnel_launcher_fire", Cat.GUN, () -> SoundEvents.BREEZE_SHOOT),
        FLYBY_GENERIC("flyby_fallen_generic", Cat.FLYBY, null),
        THWACK("fallen_generic_thwack", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        THWACK_LETHAL("fallen_generic_thwack_lethal", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        WIRE_RIFLE_THWACK("wire_rifle_thwack", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        SHRAPNEL_THWACK("shrapnel_launcher_thwack", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        SHRAPNEL_THWACK_LETHAL("shrapnel_launcher_thwack_lethal", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        DREG_MELEE_SWING("dreg_melee_swing", Cat.MELEE, () -> SoundEvents.PLAYER_ATTACK_SWEEP),
        SHOCK_BLADE_SWISH("shock_blade_melee_swish", Cat.MELEE, null),
        VANDAL_SWORD("vandal_sword_melee_any", Cat.MELEE, () -> SoundEvents.PLAYER_ATTACK_SWEEP),
        SWORD_TELEGRAPH("fallen_sword_generic_telegraph", Cat.MELEE, () -> SoundEvents.BREEZE_INHALE),
        CAPTAIN_MELEE("fallen_captain_melee_attack", Cat.MELEE, () -> SoundEvents.PLAYER_ATTACK_SWEEP),
        DREG_SIGHTED("fallen_dreg_target_sighted", Cat.BARK, null),
        DREG_TAUNT("fallen_dreg_taunt", Cat.BARK, null),
        DREG_UNDER_FIRE("fallen_dreg_under_fire", Cat.BARK, () -> SoundEvents.SPIDER_HURT),
        DREG_EVADE("fallen_dreg_dive_evade", Cat.BARK, null),
        DREG_DEATH("fallen_dreg_death", Cat.DEATH, () -> SoundEvents.SPIDER_DEATH),
        DREG_KILL("fallen_dreg_kill", Cat.BARK, null),
        VANDAL_SIGHTED("fallen_vandal_target_sighted", Cat.BARK, null),
        VANDAL_UNDER_FIRE("fallen_vandal_under_fire", Cat.BARK, () -> SoundEvents.SPIDER_HURT),
        VANDAL_EVADE("fallen_vandal_dive_evade", Cat.BARK, null),
        VANDAL_DEATH("fallen_vandal_death", Cat.DEATH, () -> SoundEvents.SPIDER_DEATH),
        CAPTAIN_SIGHTED("fallen_captain_target_sighted", Cat.BARK, null),
        CAPTAIN_UNDER_FIRE("fallen_captain_under_fire", Cat.BARK, () -> SoundEvents.SPIDER_HURT),
        CAPTAIN_DEATH("fallen_captain_death", Cat.DEATH, () -> SoundEvents.SPIDER_DEATH),
        CAPTAIN_KILL("fallen_captain_kill", Cat.BARK, null),
        SHANK_SIGHTED("fallen_shank_target_sighted", Cat.BARK, null),
        SHANK_PAIN("fallen_shank_pain", Cat.BARK, () -> SoundEvents.IRON_GOLEM_HURT),
        SHANK_DEATH("fallen_shank_death", Cat.DEATH, () -> SoundEvents.IRON_GOLEM_DEATH),
        SHANK_SHOOT("fallen_shank_shoot", Cat.BARK, null),
        SHANK_EXPLODE("shank_explode", Cat.GUN, null),
        DREG_EVADE_SPIN("dreg_evade_spin", Cat.FOLEY, null),
        DREG_SHORTMOVE("dreg_shortmove", Cat.FOLEY, null),
        DREG_BODYFALL("fallen_dreg_bodyfall", Cat.FOLEY, null),
        CAPTAIN_BODYFALL("fallen_captain_bodyfall", Cat.FOLEY, null),
        BASE_DEATH_MVMT("fallen_base_death_mvmt", Cat.FOLEY, null),
        TELEPORT_BEGIN("teleport_begin", Cat.FOLEY, () -> SoundEvents.ILLUSIONER_MIRROR_MOVE),
        TELEPORT_END("teleport_end", Cat.FOLEY, null),
        DISSOLVE("generic_dissolve", Cat.FOLEY, () -> SoundEvents.AMETHYST_BLOCK_RESONATE),
        WALKER_CANNON_FIRE("spidertank_cannon_fire", Cat.WALKER, () -> SoundEvents.GENERIC_EXPLODE.value()),
        WALKER_CANNON_EXPLO("spidertank_cannon_explo", Cat.WALKER, () -> SoundEvents.GENERIC_EXPLODE.value()),
        WALKER_NOSE_FIRE("spidertank_nose_fire", Cat.WALKER, () -> SoundEvents.BREEZE_SHOOT),
        WALKER_NOSE_OPEN("spidertank_nose_barrel_open", Cat.WALKER, () -> SoundEvents.BEACON_POWER_SELECT),
        WALKER_NOSE_THWACK("spidertank_nose_thwack", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        WALKER_NOSE_THWACK_LETHAL("spidertank_nose_thwack_lethal", Cat.IMPACT, () -> SoundEvents.TRIDENT_HIT),
        WALKER_FLYBY("flyby_fallen_spidertank_turret", Cat.FLYBY, null),
        WALKER_STEP("spidertank_step_front", Cat.WALKER, () -> SoundEvents.RAVAGER_STEP),
        WALKER_STEP_RUMBLE("spidertank_step_rumble", Cat.WALKER, null),
        WALKER_LEG_EXPLO("spidertank_leg_explo", Cat.WALKER, () -> SoundEvents.IRON_GOLEM_DAMAGE),
        WALKER_WEAKSPOT_CLOSE("spidertank_expose_weakspot_exit", Cat.WALKER, () -> SoundEvents.BEACON_DEACTIVATE),
        WALKER_INTIMIDATE("spidertank_voice_intimidate", Cat.WALKER, () -> SoundEvents.RAVAGER_ROAR),
        WALKER_EXPLODE("spidertank_explode_1", Cat.WALKER, () -> SoundEvents.GENERIC_EXPLODE.value()),
        WALKER_LAND("spidertank_land", Cat.WALKER, null),
        WALKER_ARMOR_IMPACT("spider_tank_impact", Cat.WALKER, () -> SoundEvents.ANVIL_LAND),
        SKIFF_FLYOVER("skiff_flyover", Cat.SKIFF, () -> SoundEvents.PHANTOM_SWOOP),
        SKIFF_ENEMY_SPAWNER("skiff_enemy_spawner", Cat.SKIFF, () -> SoundEvents.BEACON_POWER_SELECT);

        public final String event;
        final Cat cat;
        /** Lazy so the table stays usable without a bootstrapped registry (unit tests). */
        private final java.util.function.Supplier<SoundEvent> fallbackRef;
        Ev(String event, Cat cat, java.util.function.Supplier<SoundEvent> fallback) {
            this.event = event; this.cat = cat; this.fallbackRef = fallback;
        }
        SoundEvent fallback() { return fallbackRef == null ? null : fallbackRef.get(); }
        public String key() { return "guardian_rises.fallen." + event; }
        public Identifier id() { return DestinyGuardians.id(key()); }
    }

    // ------------------------------------------------------------------------------------------ per-unit tables

    static Ev sighted(FallenKind k) {
        return switch (k) { case DREG -> Ev.DREG_SIGHTED; case VANDAL -> Ev.VANDAL_SIGHTED; case CAPTAIN -> Ev.CAPTAIN_SIGHTED;
            case SHANK -> Ev.SHANK_SIGHTED; case WALKER -> Ev.WALKER_INTIMIDATE; };
    }
    static Ev hurt(FallenKind k) {
        return switch (k) { case DREG -> Ev.DREG_UNDER_FIRE; case VANDAL -> Ev.VANDAL_UNDER_FIRE;
            case CAPTAIN -> Ev.CAPTAIN_UNDER_FIRE; case SHANK -> Ev.SHANK_PAIN; case WALKER -> null; };
    }
    static Ev death(FallenKind k) {
        return switch (k) { case DREG -> Ev.DREG_DEATH; case VANDAL -> Ev.VANDAL_DEATH; case CAPTAIN -> Ev.CAPTAIN_DEATH;
            case SHANK -> Ev.SHANK_DEATH; case WALKER -> null; };
    }
    static Ev kill(FallenKind k) {
        // Vandal kill shares the dive_evade WEM pool in the extraction, so it reuses that event.
        return switch (k) { case DREG -> Ev.DREG_KILL; case VANDAL -> Ev.VANDAL_EVADE; case CAPTAIN -> Ev.CAPTAIN_KILL;
            default -> null; };
    }
    static Ev bodyfall(FallenKind k) {
        return switch (k) { case DREG -> Ev.DREG_BODYFALL; case VANDAL -> Ev.BASE_DEATH_MVMT; case CAPTAIN -> Ev.CAPTAIN_BODYFALL;
            default -> null; };
    }
    /** Gunfire for a ranged attack: splash orbs are the Captain's launcher, otherwise by unit. */
    static Ev fire(FallenKind k, boolean splash) {
        if (splash) return Ev.SHRAPNEL_LAUNCHER_FIRE;
        return switch (k) { case VANDAL, CAPTAIN -> Ev.WIRE_RIFLE_FIRE; case WALKER -> Ev.WALKER_NOSE_FIRE; default -> Ev.SHOCK_PISTOL_FIRE; };
    }
    /** {thwack, lethal thwack, flyby} for a projectile from this shooter. Shells (splash) have no flyby/thwack. */
    static Ev[] impact(FallenKind k, boolean splash) {
        if (k == FallenKind.WALKER) return new Ev[]{Ev.WALKER_NOSE_THWACK, Ev.WALKER_NOSE_THWACK_LETHAL, Ev.WALKER_FLYBY};
        if (splash) return new Ev[]{Ev.SHRAPNEL_THWACK, Ev.SHRAPNEL_THWACK_LETHAL, null};
        if (k == FallenKind.VANDAL) return new Ev[]{Ev.WIRE_RIFLE_THWACK, Ev.WIRE_RIFLE_THWACK, Ev.FLYBY_GENERIC};
        return new Ev[]{Ev.THWACK, Ev.THWACK_LETHAL, Ev.FLYBY_GENERIC};
    }
    static Ev[] melee(FallenKind k) {
        return switch (k) {
            case DREG -> new Ev[]{Ev.DREG_MELEE_SWING, Ev.SHOCK_BLADE_SWISH};
            case CAPTAIN -> new Ev[]{Ev.CAPTAIN_MELEE, Ev.SHOCK_BLADE_SWISH};
            default -> new Ev[]{Ev.VANDAL_SWORD};
        };
    }
    static FallenKind kindOf(LivingEntity e) { return e instanceof FallenMob m ? m.fallenKind() : null; }

    // ------------------------------------------------------------------------------------------ playback

    private static final Random JITTER = new Random();
    private static final BarkGate BARKS = new BarkGate();

    /** Positional playback to everyone in range. Returns false if neither the D2 sound nor a fallback exists. */
    public static boolean play(ServerLevel level, Vec3 at, Ev ev) { return play(level, at, ev, 1f, 1f); }

    public static boolean play(ServerLevel level, Vec3 at, Ev ev, float volume, float pitch) {
        if (ev == null || at == null || level == null) return false;
        float p = pitch(pitch, ev.cat.jitter, JITTER.nextFloat());
        float v = Math.max(.05f, Math.min(1f, ev.cat.volume * volume));
        if (DestinySounds.has(ev.key())) {
            var packet = new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(ev.id(), ev.cat.range)),
                    SoundSource.HOSTILE, at.x, at.y, at.z, v, p, level.getRandom().nextLong());
            double r2 = (double) ev.cat.range * ev.cat.range;
            for (ServerPlayer pl : level.players()) if (pl.position().distanceToSqr(at) <= r2) pl.connection.send(packet);
            return true;
        }
        var fallback = ev.fallback();
        if (fallback == null) return false;
        level.playSound(null, at.x, at.y, at.z, fallback, SoundSource.HOSTILE, v, p);
        return true;
    }

    /** Only to one listener (flyby/thwack heard by the victim). */
    static void playTo(ServerPlayer listener, Vec3 at, Ev ev) {
        if (ev == null || listener == null || !DestinySounds.has(ev.key())) {
            var fallback = ev == null ? null : ev.fallback();
            if (fallback != null && listener != null)
                listener.level().playSound(null, at.x, at.y, at.z, fallback, SoundSource.HOSTILE, ev.cat.volume, 1f);
            return;
        }
        listener.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(ev.id(), ev.cat.range)),
                SoundSource.HOSTILE, at.x, at.y, at.z, ev.cat.volume, pitch(1f, ev.cat.jitter, JITTER.nextFloat()),
                listener.getRandom().nextLong()));
    }

    /** Gated vocal bark from a mob (budgeted). priority: death cries (skip per-mob cooldown, small extra budget). */
    static boolean bark(LivingEntity mob, Ev ev, boolean priority) {
        if (ev == null || !(mob.level() instanceof ServerLevel level)) return false;
        Vec3 at = mob.position().add(0, mob.getBbHeight() * .8, 0);
        if (!BARKS.allow(mob.getId(), ev.ordinal(), level.getServer().getTickCount(), at.x, at.y, at.z, priority)) return false;
        return play(level, at, ev);
    }

    static void clear() { BARKS.clear(); }

    static float pitch(float base, float jitter, float unit) {
        return Math.max(.5f, Math.min(2f, base * (1 + jitter * (2 * unit - 1))));
    }

    /**
     * Pure bark budget (unit tested). Per mob: one bark per {@link #PER_MOB} ticks; per mob and event:
     * {@link #PER_EVENT} ticks. Globally at most {@link #BUDGET} barks in any {@link #WINDOW}-tick window within
     * {@link #RADIUS} blocks of each other (priority barks get one extra slot and ignore the per-mob limits).
     */
    static final class BarkGate {
        static final int PER_MOB = 50, PER_EVENT = 140, WINDOW = 20, BUDGET = 2, RADIUS = 24, MAX_TRACKED = 512;
        private record Recent(long tick, double x, double y, double z) {}
        private final Map<Integer, Long> mobLast = new HashMap<>();
        private final Map<Long, Long> eventLast = new HashMap<>();
        private final Deque<Recent> recent = new ArrayDeque<>();

        boolean allow(int mob, int event, long now, double x, double y, double z, boolean priority) {
            while (!recent.isEmpty() && now - recent.peekFirst().tick() >= WINDOW) recent.pollFirst();
            long ek = ((long) mob << 16) ^ event;
            if (!priority) {
                Long m = mobLast.get(mob);
                if (m != null && now - m < PER_MOB) return false;
                Long e = eventLast.get(ek);
                if (e != null && now - e < PER_EVENT) return false;
            }
            int near = 0;
            for (var r : recent) {
                double dx = r.x() - x, dy = r.y() - y, dz = r.z() - z;
                if (dx * dx + dy * dy + dz * dz <= RADIUS * RADIUS) near++;
            }
            if (near >= BUDGET + (priority ? 1 : 0)) return false;
            recent.addLast(new Recent(now, x, y, z));
            if (mobLast.size() > MAX_TRACKED) { mobLast.clear(); eventLast.clear(); }
            mobLast.put(mob, now);
            eventLast.put(ek, now);
            return true;
        }

        void clear() { mobLast.clear(); eventLast.clear(); recent.clear(); }
    }
}
