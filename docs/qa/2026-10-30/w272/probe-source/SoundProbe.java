package qa;


import net.minecraft.client.Minecraft;
import net.minecraft.client.resources.sounds.SoundInstance;
import net.minecraft.client.resources.sounds.EntityBoundSoundInstance;
import net.minecraft.world.entity.Entity;
import java.util.*;
public class SoundProbe {
 static int tick; static final Map<SoundInstance,Integer> watches=new IdentityHashMap<>();
 public static void tickProbe(){tick++;var it=watches.entrySet().iterator();while(it.hasNext()){var e=it.next();int age=tick-e.getValue();if(age==1||age==2||age==5||age==10||age==20||age==40||age==60)log("tick age="+age,e.getKey());if(age>=80)it.remove();}}
 public static void played(SoundInstance s,Object result){if(!s.getIdentifier().getNamespace().equals("destiny"))return;log("play result="+result,s);watches.put(s,tick);}
 static void log(String action,SoundInstance s){String entity="none";try{if(s instanceof EntityBoundSoundInstance){var f=EntityBoundSoundInstance.class.getDeclaredField("entity");f.setAccessible(true);Entity e=(Entity)f.get(s);entity=e.getId()+":"+e.getType()+":removed="+e.isRemoved()+":silent="+e.isSilent();}}catch(Exception e){entity=e.toString();}
 System.out.println("[W272 sound] "+action+" event="+s.getIdentifier()+" type="+s.getClass().getSimpleName()+" active="+Minecraft.getInstance().getSoundManager().isActive(s)+" canPlay="+s.canPlaySound()+" volume="+s.getVolume()+" path="+(s.getSound()==null?"null":s.getSound().getPath())+" entity="+entity);}
}