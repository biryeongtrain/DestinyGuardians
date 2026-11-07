package kim.biryeong.destiny.test;

import kim.biryeong.destiny.strike.devils.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.world.phys.Vec3;

/** Headless damage and packet regression, not speaker/visual acceptance. */
public final class CombatBalanceW342GameTests {
    private net.minecraft.server.level.ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(1,2,1),0,0);
        TestCleanup.register(h,()->TestPlayers.remove(p));return p;
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void fragileMinorsAndAbilitySuperDamage(GameTestHelper h) { DevilsWalkerFixture.verifyMinorBalance(h,player(h));h.succeed(); }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void walkerReducedPoolsKeepMultipartDedupAndDeath(GameTestHelper h) { DevilsWalkerFixture.verify(h,player(h));h.succeed(); }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void sepiksReducedPoolKeepsShieldsAndCompletion(GameTestHelper h) { DevilsWalkerFixture.verifySepiks(h,player(h));h.succeed(); }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void brigArmorThresholdIsUnaffected(GameTestHelper h) { DevilsWalkerFixture.verifyBrigs(h,player(h));h.succeed(); }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void everyEnemyDeathQueuesAQuieterOwnedSoundPacket(GameTestHelper h) {
        var p=player(h);var at=p.position().add(2,0,0);
        for(var kind:DevilsPlan.Kind.values()) {
            TestPlayers.drain(p);
            h.assertTrue(DevilsCombatSounds.play(h.getLevel(),java.util.List.of(p),kind,"death",at)==1,"One owned listener: "+kind);
            var packets=TestPlayers.outbound(p).stream().filter(v->v instanceof net.minecraft.network.protocol.game.ClientboundSoundPacket)
                    .map(v->(net.minecraft.network.protocol.game.ClientboundSoundPacket)v).toList();
            h.assertTrue(packets.size()==1,"One death packet: "+kind);
            h.assertTrue(Math.abs(packets.getFirst().getVolume()-.35f)<1e-6,"Quiet death mix: "+kind);
            h.assertTrue(packets.getFirst().getSource()==net.minecraft.sounds.SoundSource.HOSTILE,"Enemy sound category");
        }
        h.succeed();
    }
}
