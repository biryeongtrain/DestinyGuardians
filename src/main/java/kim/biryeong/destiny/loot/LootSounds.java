package kim.biryeong.destiny.loot;

import net.minecraft.core.Holder;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.phys.Vec3;

/** Owner-only loot cues (player category). No original engram/chest audio is extracted yet: transmat + vanilla. */
final class LootSounds {
    private LootSounds() { }

    static void play(ServerPlayer p, String id, Vec3 at, float volume, float pitch) {
        if (p.hasDisconnected()) return;
        p.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(Identifier.parse(id))),
                SoundSource.PLAYERS, at.x, at.y, at.z, volume, pitch, p.getRandom().nextLong()));
    }

    static void drop(ServerPlayer p, Vec3 at, boolean exotic) {
        play(p, "minecraft:block.amethyst_block.chime", at, 1.2f, exotic ? .7f : 1.1f);
        play(p, "minecraft:block.beacon.activate", at, .35f, exotic ? 1.2f : 1.8f);
    }
    static void pickup(ServerPlayer p) {
        play(p, "destiny:guardian_rises.sfx.transmat", p.position(), .6f, 1.4f);
        play(p, "minecraft:entity.experience_orb.pickup", p.position(), .5f, .7f);
    }
    static void chest(ServerPlayer p, Vec3 at) {
        play(p, "minecraft:block.iron_trapdoor.open", at, .9f, .7f);
        play(p, "minecraft:block.chest.open", at, .7f, .75f);
        play(p, "minecraft:block.beacon.power_select", at, .45f, 1.6f);
    }
    static void chestArrive(ServerPlayer p, Vec3 at) {
        play(p, "destiny:guardian_rises.sfx.transmat", at, .8f, 1.15f);
        play(p, "minecraft:block.amethyst_block.resonate", at, .5f, 1.4f);
    }
    static void burst(ServerPlayer p, Vec3 at, boolean exotic) {
        play(p, "minecraft:block.amethyst_cluster.break", at, .9f, .8f);
        play(p, "minecraft:entity.firework_rocket.blast", at, .45f, 1.5f);
        play(p, "minecraft:block.amethyst_block.chime", at, 1f, 1.3f);
        if (exotic) play(p, "minecraft:ui.toast.challenge_complete", at, .45f, 1.1f);
    }
    static void glimmer(ServerPlayer p, float pitch) { play(p, "minecraft:entity.experience_orb.pickup", p.position(), .32f, Math.min(2f, pitch)); }
    static void chestLeave(ServerPlayer p, Vec3 at) { play(p, "destiny:guardian_rises.sfx.transmat", at, .5f, 1.4f); }
    static void decode(ServerPlayer p) { play(p, "minecraft:block.enchantment_table.use", p.position(), .8f, 1.2f); }
}
