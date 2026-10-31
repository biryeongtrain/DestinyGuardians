package kim.biryeong.destiny.test;

import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.tutorial.Tutorial;
import kim.biryeong.destiny.tutorial.TutorialLoan;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.phys.Vec3;
import java.util.Map;
import java.util.List;

public final class TutorialStarterW287GameTests {
    private static void check(GameTestHelper h,boolean ok,String text) {h.assertTrue(ok,Component.literal(text));}
    private static Object field(Object target,String name) {
        try {var f=(target instanceof Class<?> c?c:target.getClass()).getDeclaredField(name);f.setAccessible(true);return f.get(target instanceof Class<?>?null:target);}
        catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    private static void call(String name,Object session,Object... args) {
        try {
            var method=java.util.Arrays.stream(Tutorial.class.getDeclaredMethods()).filter(m->m.getName().equals(name)).findFirst().orElseThrow();
            method.setAccessible(true);var all=new Object[args.length+1];all[0]=session;System.arraycopy(args,0,all,1,args.length);method.invoke(null,all);
        } catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    private static Object step(String name) {
        try {var c=Class.forName(Tutorial.class.getName()+"$Step");return java.util.Arrays.stream(c.getEnumConstants()).filter(s->s.toString().equals(name)).findFirst().orElseThrow();}
        catch(ClassNotFoundException e){throw new AssertionError(e);}
    }
    private static void set(Object target,String name,Object value) {
        try {var f=target.getClass().getDeclaredField(name);f.setAccessible(true);f.set(target,value);}
        catch(ReflectiveOperationException e){throw new AssertionError(e);}
    }
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w287_tutorial",maxTicks=120)
    public void firstCombatLoansAutomaticRifleWithoutMenuAndRestoresEquipment(GameTestHelper h) {
        var p=TestPlayers.hunter(h,Element.ARC,new Vec3(2,1,2),0,0);
        var saved=List.of(new ItemStack(Items.DIAMOND,3),new ItemStack(Items.BOOK,2),new ItemStack(Items.EMERALD,5));
        for(int i=0;i<3;i++)p.getInventory().setItem(i,saved.get(i).copy());
        p.getInventory().setSelectedSlot(4);p.setAttached(WeaponLoadout.ENABLED,false);
        Object[] session={null};
        TestCleanup.register(h,()->{if(session[0]!=null)call("end",session[0],false);TestPlayers.remove(p);});
        check(h,Tutorial.start(p)==null,"Tutorial starts");
        session[0]=((Map<?,?>)field(Tutorial.class,"SESSIONS")).get(p.getUUID());
        call("skipTo",session[0],step("EQUIP"));
        var gun=p.getMainHandItem();var entry=WeaponItems.entry(gun).orElseThrow();
        check(h,entry.id().equals("halfdan_d")&&entry.family().equals("auto_rifle"),"Automatic rifle is immediately selected");
        check(h,TutorialLoan.borrowed(p,gun)&&TutorialLoan.active(p),"Marked temporary loan, original slots escrowed");
        var profile=WeaponProfile.forEntry(entry);
        check(h,profile.automatic()&&profile.infiniteReserve()&&WeaponItems.magazine(gun,profile).rounds()>0,"Loaded continuous-fire primary with infinite reserve");
        h.runAfterDelay(45,()->{
            check(h,field(session[0],"step").toString().equals("FIRE"),"Advances to first combat without opening E or selecting a weapon");
            check(h,!((List<?>)field(session[0],"targets")).isEmpty(),"First targets exist after weapon delivery");
            check(h,p.getMainHandItem()==gun,"Transition does not replace/refill the same loan");
            TutorialLoan.equip(p,WeaponCatalog.find("beloved").orElseThrow());
            call("end",session[0],false);session[0]=null;
            for(int i=0;i<3;i++)check(h,ItemStack.matches(p.getInventory().getItem(i),saved.get(i)),"Original slot restored "+i);
            check(h,p.getInventory().getSelectedSlot()==4&&!WeaponLoadout.enabled(p)&&!TutorialLoan.active(p),"Selection/loadout restored and backup retired");
            for(int i=0;i<p.getInventory().getContainerSize();i++)check(h,!TutorialLoan.borrowed(p,p.getInventory().getItem(i)),"Temporary weapons removed on exit");
            // A fresh account must not lose its only usable weapon after the family lessons.
            for(int i=0;i<3;i++)p.getInventory().setItem(i,ItemStack.EMPTY);
            check(h,Tutorial.start(p)==null,"Start an empty-equipment run");
            session[0]=((Map<?,?>)field(Tutorial.class,"SESSIONS")).get(p.getUUID());
            call("skipTo",session[0],step("ARSENAL"));
            set(session[0],"lessonIndex",kim.biryeong.destiny.tutorial.TutorialArsenal.LESSONS.size()-1);
            int now=p.level().getServer().getTickCount();
            set(session[0],"lessonDoneAt",now-40);set(session[0],"lineUntil",0);
            ((java.util.Deque<?>)field(session[0],"lines")).clear();
            call("tickLesson",session[0],now);
            check(h,field(session[0],"step").toString().equals("TRAVERSE"),"Final lesson advances");
            check(h,TutorialLoan.borrowed(p,p.getMainHandItem())&&WeaponItems.entry(p.getMainHandItem()).orElseThrow().id().equals("halfdan_d"),"Empty account keeps a temporary rifle for remaining training");
            call("end",session[0],false);session[0]=null;
            for(int i=0;i<3;i++)check(h,p.getInventory().getItem(i).isEmpty(),"Fresh account loan removed on exit "+i);
            h.succeed();
        });
    }
}
