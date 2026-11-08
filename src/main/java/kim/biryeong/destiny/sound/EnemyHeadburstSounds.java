package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.campaign.fallen.FallenMob;
import net.minecraft.core.Holder;
import net.minecraft.core.registries.Registries;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.tags.TagKey;
import net.minecraft.world.entity.EntityType;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.player.Player;
import net.minecraft.world.phys.Vec3;

/** Positional ether/headburst layer after an observed weapon precision final blow.
 * Normal death vocals remain separate. No timers, target mutation or shared session state. */
public final class EnemyHeadburstSounds {
    public static final float RANGE = 24;
    /** Reserved for actual Cabal entity types; unrelated enemies never inherit a Cabal sound. */
    public static final TagKey<EntityType<?>> CABAL = TagKey.create(Registries.ENTITY_TYPE,
            DestinyGuardians.id("headburst_cabal"));
    public enum Family {
        FALLEN_DREG("fallen_dreg"), FALLEN_VANDAL("fallen_vandal"), FALLEN_CAPTAIN("fallen_captain"), CABAL("cabal");
        private final Identifier event;
        Family(String key) { event = Identifier.fromNamespaceAndPath("destiny_headburst", "headburst." + key); }
        public Identifier event() { return event; }
    }
    private EnemyHeadburstSounds() { }

    public static Family family(LivingEntity target) {
        if (target instanceof Player) return null;
        if (target instanceof FallenMob mob) return switch (mob.fallenKind()) {
            case DREG -> Family.FALLEN_DREG;
            case VANDAL -> Family.FALLEN_VANDAL;
            case CAPTAIN -> Family.FALLEN_CAPTAIN;
            default -> null;
        };
        if (target instanceof kim.biryeong.destiny.combat.StrikeCombatant combatant) return combatant.headburstFamily();
        return target.getType().builtInRegistryHolder().is(CABAL) ? Family.CABAL : null;
    }

    /** Called once by the weapon transaction after actual loss and final-blow confirmation.
     * A mixed pellet transaction follows the same precision-credit policy as the existing weapon perks. */
    public static int confirmed(ServerPlayer source, LivingEntity victim, float observedDamage,
                                float precisionDamage, boolean killed, Vec3 point) {
        if (!killed || !Float.isFinite(observedDamage) || observedDamage <= 0
                || !Float.isFinite(precisionDamage) || precisionDamage <= 0 || source == null || victim == null
                || point == null || !Double.isFinite(point.x) || !Double.isFinite(point.y) || !Double.isFinite(point.z)
                || !victim.isDeadOrDying() || !(victim.level() instanceof ServerLevel level)
                || source.level() != level || !level.getServer().isSameThread()) return 0;
        var family = family(victim);
        if (family == null) return 0;
        var packet = new ClientboundSoundPacket(Holder.direct(SoundEvent.createFixedRangeEvent(family.event(), RANGE)),
                SoundSource.HOSTILE, point.x, point.y, point.z, EnemySoundMix.DEATH, 1f, level.getRandom().nextLong());
        int sent = 0;
        for (var listener : level.players()) if (!listener.hasDisconnected() && listener.connection.hasClientLoaded()
                && listener.position().distanceToSqr(point) <= RANGE * RANGE) {
            listener.connection.send(packet); sent++;
        }
        return sent;
    }
}
