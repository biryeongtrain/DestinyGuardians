package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.*;

public final class AbilityW252GameTests {
    private static void check(GameTestHelper h,boolean ok,String message){h.assertTrue(ok,Component.literal(message));}
    private static ServerPlayer player(GameTestHelper h,GuardianClass cls,int index) {
        var p=TestPlayers.create(h,new Vec3(2.5+index*6,3,2.5),0,-45,"W252_"+cls+index);
        p.setNoGravity(true);p.setOnGround(true);
        CharacterLoadouts.selectClass(p,cls);CharacterLoadouts.selectSubclass(p,Element.ARC);
        TestCleanup.register(h,()->TestPlayers.remove(p));return p;
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=60)
    public void allClassesThrowAfterWindupAndEmitOnlyOnce(GameTestHelper h) {
        var players=new ArrayList<ServerPlayer>();int i=0;
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK)) {
            var p=player(h,cls,i++);players.add(p);
            check(h,AbilityService.use(p,AbilitySlot.GRENADE)==AbilityService.Result.OK,"Throw accepted "+cls);
            check(h,GrenadeThrow.active(p)&&SimProjectile.activeCount(p)==0,"No instant projectile "+cls);
            check(h,AbilityService.use(p,AbilitySlot.MELEE)==AbilityService.Result.BUSY,"Throw owns recovery");
        }
        h.runAfterDelay(3,()->players.forEach(p->check(h,SimProjectile.activeCount(p)==0,"Still winding up")));
        h.runAfterDelay(8,()->players.forEach(p->{
            check(h,SimProjectile.activeCount(p)==1,"One actual flight "+p.getName().getString());
            check(h,GrenadeThrow.prop(p).isEmpty(),"Held grenade disappears at release");
        }));
        h.runAfterDelay(23,()->{for(var p:players)check(h,!GrenadeThrow.active(p),"Recovery retired");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void subclassChangeCancelsPendingThrowWithoutGhostEmission(GameTestHelper h) {
        var players=new ArrayList<ServerPlayer>();int i=0;
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK)) {
            var p=player(h,cls,i++);players.add(p);AbilityService.use(p,AbilitySlot.GRENADE);
            check(h,CharacterLoadouts.selectSubclass(p,Element.SOLAR)==null,"Subclass changed");
            check(h,!GrenadeThrow.active(p),"Pending cast cancelled immediately");
        }
        h.runAfterDelay(10,()->{for(var p:players)check(h,SimProjectile.activeCount(p)==0,"Old callbacks cannot emit");h.succeed();});
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=40)
    public void jumpOptionsAreClassBoundAndBlinkIsSubclassBound(GameTestHelper h) {
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK))for(var e:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
            var options=CharacterLoadouts.options(cls,e,AbilitySlot.JUMP);
            boolean blink=(cls==GuardianClass.HUNTER&&e==Element.ARC)||(cls==GuardianClass.WARLOCK&&e==Element.VOID);
            check(h,options.size()==(blink?4:3),"Expected jump options "+cls+" "+e+": "+options.size());
            check(h,options.stream().allMatch(a->a.guardianClass()==cls),"No foreign class jump");
            check(h,options.stream().anyMatch(a->a.id().getPath().endsWith("blink"))==blink,"Blink membership");
        }
        h.succeed();
    }
}
