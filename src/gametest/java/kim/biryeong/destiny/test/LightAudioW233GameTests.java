package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.ClassAbilityEffects;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.guardian.Element;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.world.phys.Vec3;

/** Actual server connection packets: source selection/decoding are checked by the importer. */
public final class LightAudioW233GameTests {
    @GameTest(structure="destiny-test:floor", maxTicks=20, environment="destiny-test:w90_isolated", manualOnly=true)
    public void novaCastIsOnceAndImpactUsesHitPointAfterPresentation(GameTestHelper h) {
        var p = TestPlayers.create(h, new Vec3(2,1,2),0,0);
        try {
            h.getLevel().addNewPlayer(p);
            Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
            TestPlayers.drain(p);
            var hit = p.position().add(4,0,0);
            ClassAbilityEffects.sound(p,Element.VOID,"warlock/void_super","super.start");
            ClassAbilityEffects.sound(p,Element.VOID,"warlock/void_super","super.fire");
            ClassAbilityEffects.soundAt(p,Element.VOID,"warlock/void_super","super.impact",hit);
            var sounds = TestPlayers.outbound(p).stream().filter(ClientboundSoundPacket.class::isInstance)
                    .map(ClientboundSoundPacket.class::cast)
                    .filter(s->s.getSound().value().location().getNamespace().equals("destiny")).toList();
            h.assertTrue(sounds.size()==2,Component.literal("One cast plus one impact; no duplicate at release"));
            h.assertTrue(sounds.get(0).getSound().value().location().getPath().equals("warlock.void.super.start"),Component.literal("Nova cast route"));
            var impact=sounds.get(1);
            h.assertTrue(impact.getSound().value().location().getPath().equals("warlock.void.super.impact"),Component.literal("Nova impact route"));
            h.assertTrue(Math.abs(impact.getX()-hit.x)<.126 && Math.abs(impact.getZ()-hit.z)<.126,Component.literal("Wire-quantized impact origin is authoritative hit point"));
            h.succeed();
        } finally {
            h.getLevel().removePlayerImmediately(p, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        }
    }
    @GameTest(structure="destiny-test:floor", maxTicks=20, environment="destiny-test:w90_isolated", manualOnly=true)
    public void bladeBarrageKeepsSingleThrowAndRiftUsesOwnClass(GameTestHelper h) {
        var p = TestPlayers.create(h,new Vec3(2,1,2),0,0);
        try {
            h.getLevel().addNewPlayer(p);
            Guardians.data(p).setGuardianClass(GuardianClass.HUNTER);
            TestPlayers.drain(p);
            for (String phase : new String[]{"start","fire","end"})
                ClassAbilityEffects.sound(p,Element.SOLAR,"hunter/blade_barrage","super."+phase);
            var packets=TestPlayers.outbound(p).stream().filter(ClientboundSoundPacket.class::isInstance).map(ClientboundSoundPacket.class::cast).toList();
            h.assertTrue(packets.size()==1 && packets.getFirst().getSound().value().location().getPath().equals("hunter.solar.blade_barrage.fire"),Component.literal("Blade Barrage emits only one throw cue"));
            Guardians.data(p).setGuardianClass(GuardianClass.WARLOCK);
            ClassAbilityEffects.sound(p,Element.SOLAR,"class.cast");
            var rift=TestPlayers.outbound(p).stream().filter(ClientboundSoundPacket.class::isInstance).map(ClientboundSoundPacket.class::cast).toList();
            h.assertTrue(rift.size()==1 && rift.getFirst().getSound().value().location().getPath().equals("warlock.solar.class.cast"),Component.literal("Healing rift has its own mapped class cue"));
            h.succeed();
        } finally {
            h.getLevel().removePlayerImmediately(p, net.minecraft.world.entity.Entity.RemovalReason.DISCARDED);
            TestPlayers.remove(p);
        }
    }
}
