package kim.biryeong.destiny.test;

import com.mojang.serialization.JsonOps;
import kim.biryeong.destiny.ability.*;
import kim.biryeong.destiny.guardian.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.phys.Vec3;
import java.util.List;

public final class CharacterLoadoutW247GameTests {
    private static final String FLOOR="destiny-test:floor", ENV="destiny-test:w90_isolated";
    private static void check(GameTestHelper h, boolean ok, String message) { h.assertTrue(ok, Component.literal(message)); }
    private static ServerPlayer player(GameTestHelper h) {
        var p=TestPlayers.create(h,new Vec3(2.5,1,2.5),0,0,"W247_character");
        p.setOnGround(true);p.setNoGravity(true);
        TestCleanup.register(h,()->{ kim.biryeong.destiny.inventory.WeaponScreen.close(p);TestPlayers.remove(p); });
        return p;
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=100)
    public void classAndSubclassRestrictEveryAbilityAndRejectInvalidEditsAtomically(GameTestHelper h) {
        var p=player(h);
        for(var cls:List.of(GuardianClass.HUNTER,GuardianClass.TITAN,GuardianClass.WARLOCK)) {
            check(h,CharacterLoadouts.selectClass(p,cls)==null,"Choose class "+cls);
            for(var element:List.of(Element.ARC,Element.SOLAR,Element.VOID)) {
                check(h,CharacterLoadouts.selectSubclass(p,element)==null,"Choose subclass "+element);
                for(var slot:AbilitySlot.values()) {
                    var options=CharacterLoadouts.options(cls,element,slot);
                    check(h,!options.isEmpty(),"Every implemented slot has an option");
                    for(var a:options) {
                        check(h,a.guardianClass()==cls && a.slot()==slot && (a.element()==element
                                || (a.element()==Element.KINETIC && (slot==AbilitySlot.JUMP || slot==AbilitySlot.CLASS_ABILITY))),"Only compatible options");
                        check(h,CharacterLoadouts.selectAbility(p,slot,a.id())==null,"Compatible selection accepted");
                        check(h,a.id().equals(AbilityService.idOf(p,slot)),"Selection is equipped");
                    }
                }
                var data=Guardians.data(p);var before=data.loadout().orElseThrow();data.setSuperEnergy(.5f);data.setCooldown(AbilitySlot.GRENADE,90);
                var foreign=AbilityRegistry.all().stream().filter(a->a.guardianClass()!=cls && a.slot()==AbilitySlot.GRENADE).findFirst().orElseThrow();
                var wrongElement=AbilityRegistry.all().stream().filter(a->a.guardianClass()==cls && a.slot()==AbilitySlot.GRENADE && a.element()!=element).findFirst().orElseThrow();
                check(h,CharacterLoadouts.selectAbility(p,AbilitySlot.GRENADE,foreign.id())!=null
                        && CharacterLoadouts.selectAbility(p,AbilitySlot.GRENADE,wrongElement.id())!=null
                        && CharacterLoadouts.selectAbility(p,AbilitySlot.MELEE,before.get(AbilitySlot.SUPER))!=null
                        && CharacterLoadouts.selectAbility(p,AbilitySlot.SUPER,Identifier.parse("destiny:missing"))!=null,"Wrong class/subclass/slot/unknown rejected");
                check(h,before.equals(data.loadout().orElseThrow()) && data.superEnergy()==.5f && data.cooldown(AbilitySlot.GRENADE)==90,"Rejected edits preserve state");
            }
        }
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=60)
    public void selectionPersistsAndSwitchesCannotRefillCooldownOrSuper(GameTestHelper h) {
        var p=player(h);CharacterLoadouts.selectClass(p,GuardianClass.HUNTER);CharacterLoadouts.selectSubclass(p,Element.SOLAR);
        var supers=CharacterLoadouts.options(GuardianClass.HUNTER,Element.SOLAR,AbilitySlot.SUPER);
        var chosen=supers.getLast();check(h,CharacterLoadouts.selectAbility(p,AbilitySlot.SUPER,chosen.id())==null,"Alternative solar super selected");
        var d=Guardians.data(p);d.setSuperEnergy(.4f);d.setCooldown(AbilitySlot.MELEE,123);
        check(h,CharacterLoadouts.selectAbility(p,AbilitySlot.SUPER,chosen.id())==null && d.superEnergy()==.4f,"Identical selection is no-op");
        CharacterLoadouts.selectClass(p,GuardianClass.TITAN);check(h,d.superEnergy()==0 && d.cooldown(AbilitySlot.MELEE)==123,"Class switch cannot refill resources");
        CharacterLoadouts.selectClass(p,GuardianClass.HUNTER);check(h,chosen.id().equals(d.loadout().orElseThrow().get(AbilitySlot.SUPER)),"Class-specific choices restored");
        var encoded=GuardianData.CODEC.encodeStart(JsonOps.INSTANCE,d).getOrThrow();var decoded=GuardianData.CODEC.parse(JsonOps.INSTANCE,encoded).getOrThrow();
        check(h,decoded.guardianClass()==d.guardianClass() && decoded.loadout(GuardianClass.HUNTER).equals(d.loadout(GuardianClass.HUNTER))
                && decoded.loadout(GuardianClass.TITAN).equals(d.loadout(GuardianClass.TITAN)) && CharacterLoadouts.subclass(decoded)==Element.SOLAR,"Codec preserves both class loadouts and subclass");
        Guardians.runtime(p).superSession=new SuperSession(){public boolean tick(){return true;}public void primary(){}public void end(){}public float remaining(){return 1;}};
        var before=d.loadout().orElseThrow();check(h,CharacterLoadouts.selectSubclass(p,Element.VOID)!=null && before.equals(d.loadout().orElseThrow()) && AbilityService.inSuper(p),"Active super blocks changes without cancelling it");
        h.succeed();
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=40)
    public void nonGuardianAndInvalidSubclassCannotCorruptSavedChoices(GameTestHelper h) {
        var p=player(h);var d=Guardians.data(p);
        check(h,CharacterLoadouts.selectSubclass(p,Element.SOLAR)!=null,"Subclass needs a class");
        check(h,CharacterLoadouts.options(GuardianClass.NONE,Element.SOLAR,AbilitySlot.SUPER).isEmpty(),"No abilities for non-guardian");
        CharacterLoadouts.selectClass(p,GuardianClass.WARLOCK);
        CharacterLoadouts.selectSubclass(p,Element.VOID);
        var saved=d.loadout().orElseThrow();d.setSuperEnergy(.7f);d.setCooldown(AbilitySlot.CLASS_ABILITY,81);
        check(h,CharacterLoadouts.selectClass(p,GuardianClass.WARLOCK)==null
                && CharacterLoadouts.selectSubclass(p,Element.VOID)==null && d.superEnergy()==.7f,"Identical class/subclass do not consume energy");
        check(h,CharacterLoadouts.selectSubclass(p,Element.KINETIC)!=null && saved.equals(d.loadout().orElseThrow()),"Unsupported subclass rejected atomically");
        check(h,CharacterLoadouts.selectClass(p,GuardianClass.NONE)==null && d.guardianClass()==GuardianClass.NONE
                && d.loadout(GuardianClass.WARLOCK).equals(saved) && d.superEnergy()==0
                && d.cooldown(AbilitySlot.CLASS_ABILITY)==81,"NONE preserves saved class choices and cooldown");
        check(h,CharacterLoadouts.selectClass(p,GuardianClass.WARLOCK)==null
                && d.loadout().orElseThrow().equals(saved) && CharacterLoadouts.subclass(d)==Element.VOID,"Restored class keeps saved subclass");
        h.succeed();
    }

    private static kim.biryeong.destiny.inventory.WeaponScreenView view(ServerPlayer p) {
        return kim.biryeong.destiny.inventory.WeaponScreen.snapshot(p).orElseThrow();
    }
    private static void click(GameTestHelper h, ServerPlayer p, int node) {
        var target=kim.biryeong.destiny.inventory.WeaponScreenLayout.bounds(node);var v=view(p);
        kim.biryeong.destiny.inventory.WeaponScreen.move(p,new net.minecraft.network.protocol.game.ServerboundMovePlayerPacket.Rot(
                p.getYRot()+(target.x()-v.cursorX())/15f,p.getXRot()+(target.y()-v.cursorY())/15f,true,false));
        check(h,view(p).focus()==node,"Pointer targets visible node "+node);
        kim.biryeong.destiny.inventory.WeaponScreen.click(p,false);
        check(h,Math.abs(view(p).cursorX()-target.x())<.1 && Math.abs(view(p).cursorY()-target.y())<.1,
                "Mouse clicks and stage changes do not warp the pointer");
    }
    private static void choose(GameTestHelper h,ServerPlayer p,String id) {
        var options=view(p).character().options();int index=java.util.stream.IntStream.range(0,options.size())
                .filter(n->options.get(n).id().equals(id)).findFirst().orElseThrow();
        click(h,p,3+index);
    }
    @GameTest(structure=FLOOR,environment=ENV,maxTicks=160)
    public void nativeMenuChoosesCharacterFieldsAndReturnsToWeaponLoadout(GameTestHelper h) {
        var p=player(h);var inv=p.getInventory();
        var stack=kim.biryeong.destiny.weapon.WeaponItems.create(kim.biryeong.destiny.weapon.WeaponCatalog.find("ammit_ar2").orElseThrow());
        inv.setItem(1,stack);inv.setSelectedSlot(1);
        double speed=p.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED);
        check(h,kim.biryeong.destiny.inventory.WeaponScreen.open(p),"Menu opens for unassigned character");
        kim.biryeong.destiny.inventory.WeaponScreen.move(p,new net.minecraft.network.protocol.game.ServerboundMovePlayerPacket.Rot(
                p.getYRot()+(600-view(p).cursorX())/15f,p.getXRot()+(230-view(p).cursorY())/15f,true,false));
        check(h,view(p).focus()==-1,"Blank canvas has no focused button");
        h.runAfterDelay(31,()->check(h,view(p).focus()==-1 && Math.abs(view(p).cursorX()-600)<.1
                && Math.abs(view(p).cursorY()-230)<.1,"Pointer stays in blank canvas across three refresh cycles"));
        var actions=List.<Runnable>of(
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.CHARACTER_TAB),
            ()->{check(h,view(p).character().fields().size()==7,"Seven editable character fields including jump");click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.CLASS);},
            ()->choose(h,p,"HUNTER"),
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.SUBCLASS),
            ()->choose(h,p,"SOLAR"),
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.SUPER),
            ()->{var options=view(p).character().options();check(h,!options.isEmpty(),"Super choices available");
                for(var option:options) {var a=AbilityRegistry.get(Identifier.parse(option.id())).orElseThrow();
                    check(h,a.guardianClass()==GuardianClass.HUNTER&&a.element()==Element.SOLAR,"Menu only exposes same-class solar supers");}
                choose(h,p,options.getLast().id());},
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.CLASS_ABILITY),
            ()->choose(h,p,view(p).character().options().getLast().id()),
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.JUMP),
            ()->{choose(h,p,"destiny:hunter/triple_jump");check(h,
                    AbilityService.idOf(p,AbilitySlot.JUMP).toString().equals("destiny:hunter/triple_jump"),"Jump menu equips the chosen option");},
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.GRENADE),
            ()->choose(h,p,view(p).character().options().getFirst().id()),
            ()->click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.MELEE),
            ()->choose(h,p,view(p).character().options().getFirst().id()),
            ()->{check(h,view(p).stage().equals("CHARACTER")&&CharacterLoadouts.subclass(Guardians.data(p))==Element.SOLAR,"All character selections return to root");
                click(h,p,kim.biryeong.destiny.inventory.WeaponScreenLayout.LOADOUT_TAB);},
            ()->{check(h,view(p).stage().equals("LOADOUT")&&inv.getItem(1)==stack,"Weapon tab preserves exact inventory item");
                check(h,p.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED)==0,"Character changes preserve owned menu freeze");
                kim.biryeong.destiny.inventory.WeaponScreen.close(p);
                check(h,p.getAttributeValue(net.minecraft.world.entity.ai.attributes.Attributes.MOVEMENT_SPEED)==speed,"Close restores movement");h.succeed();}
        );
        for(int n=0;n<actions.size();n++) {var action=actions.get(n);h.runAfterDelay(33+4*n,action);}
    }

}
