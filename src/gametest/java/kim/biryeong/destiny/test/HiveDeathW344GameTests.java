package kim.biryeong.destiny.test;

import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.strike.devils.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.protocol.game.ClientboundSoundPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Server audio identity/gain checks, not speaker or native-client acceptance. */
public final class HiveDeathW344GameTests {
    private ServerPlayer player(GameTestHelper h){var p=TestPlayers.create(h,new Vec3(4,20,1),0,0,"HiveDeathQA");TestCleanup.register(h,()->TestPlayers.remove(p));return p;}
    private List<ClientboundSoundPacket> sounds(ServerPlayer p){return TestPlayers.outbound(p).stream().filter(v->v instanceof ClientboundSoundPacket).map(v->(ClientboundSoundPacket)v).toList();}
    private final List<DevilsPlan.Kind> kinds=List.of(DevilsPlan.Kind.THRALL,DevilsPlan.Kind.ACOLYTE,DevilsPlan.Kind.KNIGHT,DevilsPlan.Kind.WIZARD);
    private final List<String> units=List.of("thrall","trooper","knight","wizard");
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void actualHiveDeathsEmitTheirOwnSoftCueOnce(GameTestHelper h) {
        var p=player(h);
        for(int i=0;i<kinds.size();i++) {
            var mob=HiveDeathW344Fixture.spawn(h,p,kinds.get(i));TestPlayers.drain(p);
            h.assertTrue(Combat.damage(p,mob,1000,Element.ARC),"Actual accepted damage kills "+kinds.get(i));
            var packets=sounds(p).stream().filter(v->v.getSound().value().location().getNamespace().equals("destiny_hive_death")).toList();
            h.assertTrue(packets.size()==1,"One species death cue");var cue=packets.getFirst();
            h.assertTrue(cue.getSound().value().location().getPath().equals("death."+units.get(i)+".soft"),"Correct source species");
            h.assertTrue(Math.abs(cue.getVolume()-.35f)<1e-6&&cue.getPitch()==1,"Quiet gain and original speed");
            h.assertTrue(!Combat.damage(p,mob,1000,Element.ARC),"Dead actor cannot be killed again");
            h.assertTrue(sounds(p).stream().noneMatch(v->v.getSound().value().location().getNamespace().equals("destiny_hive_death")),"No duplicate death cue");
        }
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",maxTicks=100,environment="destiny-test:w90_isolated")
    public void hardVariantsRemainSeparateAndUseTheSameDeathGain(GameTestHelper h) {
        var p=player(h);
        for(int i=0;i<kinds.size();i++) {
            TestPlayers.drain(p);
            h.assertTrue(DevilsCombatSounds.play(h.getLevel(),List.of(p),kinds.get(i),"death_hard",p.position())==1,"Explicit hard event routed");
            var packets=sounds(p);h.assertTrue(packets.size()==1,"One hard event, not a stacked variant pool");var cue=packets.getFirst();
            h.assertTrue(cue.getSound().value().location().toString().equals("destiny_hive_death:death."+units.get(i)+".hard"),"Hard is distinct from the default");
            h.assertTrue(Math.abs(cue.getVolume()-.35f)<1e-6,"Hard uses quiet death gain");
        }
        h.succeed();
    }
}
