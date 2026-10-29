package kim.biryeong.destiny.test;

import com.mojang.brigadier.exceptions.CommandSyntaxException;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;

/** Only tests the master's OP fixture/observation commands; native input is a separate claim. */
public final class WeaponPresentationCommandsW91GameTests {
    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }
    private static ServerPlayer player(GameTestHelper h) {
        var p = TestPlayers.create(h,new Vec3(1,2,1),0,0);
        p.setNoGravity(true);
        p.setAttached(WeaponLoadout.ENABLED,false);
        TestCleanup.register(h,()->{ WeaponRuntime.cleanup(p); TestPlayers.remove(p); });
        return p;
    }
    private static int execute(ServerPlayer p,String command) {
        try {
            var server=p.level().getServer();
            return server.getCommands().getDispatcher().execute(command,server.createCommandSourceStack().withEntity(p));
        } catch (CommandSyntaxException e) { throw new AssertionError(e); }
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void repeatedStatusDoesNotBindTickOrMutateWeaponState(GameTestHelper h) {
        var p=player(h);
        var gun=WeaponItems.create(WeaponCatalog.find("izanagis_burden").orElseThrow());
        p.getInventory().setItem(p.getInventory().getSelectedSlot(),gun);
        var before=gun.copy();
        check(h, !WeaponIzanagiPresentation.active(gun) && WeaponHandling.presentation(p).isEmpty(),
                "Fixture starts before presentation binding or a Handling transaction");
        for(int i=0;i<3;i++)check(h,execute(p,"destiny debug weapon-presentation-status @s")==1,"OP reads current state");
        check(h,ItemStack.matches(before,gun) && !WeaponIzanagiPresentation.active(gun)
                        && WeaponHandling.presentation(p).isEmpty() && !WeaponIzanagi.honing(p)
                        && WeaponIzanagi.charge(gun)==0 && !WeaponRuntime.reloading(p),
                "Observation never ticks/binds a visual, creates a reload or changes any component/ammunition");
        boolean rejected=false;
        try {
            p.level().getServer().getCommands().getDispatcher().execute(
                    "destiny debug weapon-presentation-status @s",p.createCommandSourceStack());
        } catch(CommandSyntaxException expected) { rejected=true; }
        check(h,rejected,"Non-OP cannot access fixture observations");
        h.succeed();
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void moriStatusDoesNotGrantOrCreateCounterHuds(GameTestHelper h) {
        var p=player(h);
        var gun=WeaponItems.create(WeaponCatalog.find("ace_of_spades").orElseThrow());
        p.getInventory().setItem(p.getInventory().getSelectedSlot(),gun);
        var before=gun.copy();
        var huds=java.util.Map.copyOf(kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p));
        for(int i=0;i<3;i++)check(h,execute(p,"destiny debug weapon-presentation-status @s")==1,
                "Read-only Mori status executes through the real permission-guarded command");
        check(h,WeaponAce.rounds(p)==0 && ItemStack.matches(before,gun)
                        && huds.equals(kim.biryeong.minigamelib.displayhud.DisplayHud.getHuds(p))
                        && !WeaponRuntime.reloading(p) && WeaponHandling.presentation(p).isEmpty(),
                "Mori status never grants earned rounds, creates HUD nodes or starts a transaction");
        h.succeed();
    }

    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=20)
    public void honedFixtureStartsRealPendingTransactionWithoutFreeCharge(GameTestHelper h) {
        var p=player(h);
        var gun=WeaponItems.create(WeaponCatalog.find("izanagis_burden").orElseThrow());
        p.getInventory().setItem(p.getInventory().getSelectedSlot(),gun);
        var profile=WeaponProfile.forEntry(WeaponItems.entry(gun).orElseThrow());
        var before=WeaponItems.magazine(gun,profile);
        check(h,execute(p,"destiny debug weapon-honed-reload @s")==1
                        && WeaponIzanagi.honing(p) && WeaponRuntime.reloading(p),
                "OP fixture calls the real accepted pending Honed transaction");
        var during=WeaponItems.magazine(gun,profile);
        check(h,WeaponIzanagi.charge(gun)==0 && before.rounds()==during.rounds()
                        && before.reserve()==during.reserve() && before.total()==during.total(),
                "Fixture does not grant completed charge or move ammunition before actual deadline");
        check(h,execute(p,"destiny debug weapon-honed-reload @s")==0,
                "Duplicate command cannot restart an accepted pending reload");
        WeaponRuntime.cancelUseForSkill(p);
        p.setGameMode(GameType.SPECTATOR);
        check(h,execute(p,"destiny debug weapon-honed-reload @s")==0 && !WeaponIzanagi.honing(p)
                        && WeaponIzanagi.charge(gun)==0,
                "Spectator or canceled transaction cannot use the fixture as a charge grant");
        h.succeed();
    }
}
