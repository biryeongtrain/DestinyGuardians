package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import com.mojang.math.Transformation;
import kim.biryeong.destiny.compat.pack.ProfileArmAssets;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.fabricmc.fabric.api.event.lifecycle.v1.*;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.entity.event.v1.*;
import net.minecraft.core.component.DataComponents;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.HumanoidArm;
import net.minecraft.world.entity.player.PlayerModelPart;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.util.Brightness;
import org.joml.Matrix4f;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Owner-only first-person view. Gameplay inventory and observer equipment stay native. */
public final class ProfileWeaponView {
    public static final String LEGACY_PROPERTY="destiny.weapon.legacyPixelArms";
    private static final float SCALE=32000;
    private static final Map<UUID,Session> ACTIVE=new HashMap<>();
    private static final class Session {
        final ServerPlayer owner;final ItemDisplayHud gun;final ItemDisplayHud[] arms=new ItemDisplayHud[4];
        final Object profile;final boolean slim;boolean leftHand,lastTwoHand;ItemStack lastGun=ItemStack.EMPTY;
        final String[] lastPoses=new String[4];final int[] lastMarkers={-1,-1,-1,-1};int sleeves=-1;float lastHandX=Float.NaN;
        Session(ServerPlayer p){owner=p;profile=p.getGameProfile();slim=slim(p);
            gun=create(p,"gun",new ItemStack(Items.STICK),ItemDisplayContext.FIRST_PERSON_RIGHT_HAND,new Brightness(0,12));
            for(int i=0;i<4;i++) {var carrier=ProfileSkinArmCarrier.createCarrier(p.getGameProfile());carrier.set(DataComponents.ITEM_MODEL,kim.biryeong.destiny.DestinyGuardians.id(ProfileArmAssets.ITEM));
                arms[i]=create(p,"arm_"+i,carrier,ItemDisplayContext.NONE,ProfileSkinArmCarrier.marker(i));}
        }
    }
    private ProfileWeaponView(){}
    public static boolean enabled(){return !Boolean.getBoolean(LEGACY_PROPERTY);}
    public static void init(){
        if(!enabled())return;
        ServerTickEvents.END_SERVER_TICK.register(server->{for(var p:server.getPlayerList().getPlayers())update(p);});
        ServerPlayConnectionEvents.DISCONNECT.register((handler,server)->remove(handler.getPlayer()));
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p,a,b)->remove(p));
        ServerLivingEntityEvents.AFTER_DEATH.register((e,source)->{if(e instanceof ServerPlayer p)remove(p);});
        ServerLifecycleEvents.SERVER_STOPPING.register(server->{for(var s:List.copyOf(ACTIVE.values()))remove(s.owner);});
    }
    private static ItemDisplayHud create(ServerPlayer p,String suffix,ItemStack stack,ItemDisplayContext context,Brightness marker){
        var h=new ItemDisplayHud();h.updateWhenDataChanged(false);h.setItem(stack);h.setItemTransform(context);h.removeWhenPlayerDied();
        h.spawn(p,"destiny:profile_view_"+suffix);h.getDisplay().setBrightnessOverride(marker);return h;
    }
    private static void update(ServerPlayer p){
        var original=p.getMainHandItem();
        if(kim.biryeong.destiny.guardian.Guardians.runtime(p).gcbThirdPerson||!p.isAlive()||p.isSpectator()||p.hasDisconnected()||p.getCamera()!=p||WeaponModels.entry(original).isEmpty()
                ||kim.biryeong.destiny.fx.PlayerAnimations.ownsSwordHand(p,original)){remove(p);return;}
        Identifier route=original.is(WeaponCombatItem.INSTANCE)?WeaponCombatItem.INSTANCE.getPolymerItemModel(original,null,p.level().registryAccess()):original.get(DataComponents.ITEM_MODEL);
        var graph=ProfileArmAssets.graph(route);if(graph==null){remove(p);return;}
        var s=ACTIVE.get(p.getUUID());if(s==null||s.owner!=p||!s.profile.equals(p.getGameProfile())){remove(p);s=new Session(p);ACTIVE.put(p.getUUID(),s);}
        boolean left=p.getMainArm()==HumanoidArm.LEFT;
        var originalData=original.getOrDefault(DataComponents.CUSTOM_MODEL_DATA,CustomModelData.EMPTY);
        var flags=new ArrayList<>(originalData.flags());while(flags.size()<2)flags.add(false);
        flags.set(0,WeaponModels.twoHanded(original));flags.set(1,WeaponCrouchPresentation.supports(original)&&WeaponCrouchPresentation.crouched(original));
        var data=new CustomModelData(originalData.floats(),flags,originalData.strings(),originalData.colors());
        var gun=new ItemStack(Items.STICK);gun.set(DataComponents.ITEM_MODEL,ProfileArmAssets.view(route));gun.set(DataComponents.CUSTOM_MODEL_DATA,data);
        if(!ItemStack.matches(gun,s.lastGun)){s.gun.setItem(gun);s.lastGun=gun.copy();}
        boolean handChanged=left!=s.leftHand;
        if(handChanged){s.leftHand=left;s.gun.setItemTransform(left?ItemDisplayContext.FIRST_PERSON_LEFT_HAND:ItemDisplayContext.FIRST_PERSON_RIGHT_HAND);Arrays.fill(s.lastPoses,null);}
        // Move the whole grip inward at hip; keep the calibrated ADS sight line unchanged.
        boolean twoHand=WeaponModels.twoHanded(original);
        float handX=handX(left,twoHand,WeaponAiming.progress(p));
        boolean framingChanged=handChanged||twoHand!=s.lastTwoHand||Float.compare(handX,s.lastHandX)!=0;
        var hand=handMatrix(left,twoHand,WeaponAiming.progress(p));
        apply(s.gun,hand,framingChanged&&Float.isFinite(s.lastHandX)&&!handChanged);
        var selected=ProfileArmGraph.select(graph,data,s.slim,left);var seen=new boolean[4];
        int sleeves=(p.isModelPartShown(PlayerModelPart.RIGHT_SLEEVE)?1:0)|(p.isModelPartShown(PlayerModelPart.LEFT_SLEEVE)?2:0);
        for(String id:selected){var pose=ProfileArmAssets.pose(id);if(pose==null)throw new IllegalStateException("Missing profile pose "+id);
            int index=(pose.leftArm()?1:0)+(pose.upper()?2:0);if(seen[index])throw new IllegalStateException("Duplicate profile arm segment");seen[index]=true;
            int marker=(pose.leftArm()?1:0)|(pose.upper()?2:0)|(s.slim?4:0)|((sleeves&(pose.leftArm()?2:1))!=0?8:0);
            if(s.lastMarkers[index]!=marker){s.arms[index].getDisplay().setBrightnessOverride(ProfileSkinArmCarrier.marker(marker));s.lastMarkers[index]=marker;}
            if(!id.equals(s.lastPoses[index])||framingChanged) {
                var m=new Matrix4f(hand).mul(left?pose.left():pose.right());
                // Native head spans x/z -4..4 and y -8..0 in sixteenths. Preserve W204 contact geometry exactly.
                m.translate(.5f,pose.upper()?.5f:.5625f,.5f).scale(s.slim?-.225f:-.3f,.9375f,.3f);
                apply(s.arms[index],m,s.lastPoses[index]!=null);s.lastPoses[index]=id;
            } else s.arms[index].update();
        }
        for(int i=0;i<4;i++)if(!seen[i]){if(s.lastPoses[i]!=null){apply(s.arms[i],new Matrix4f().translation(0,0,1).scale(0),false);s.lastPoses[i]=null;}else if(s.arms[i].getDisplay().getTransformationInterpolationDuration()==0)apply(s.arms[i],new Matrix4f().translation(0,0,1).scale(0),false);}
        s.sleeves=sleeves;s.lastHandX=handX;s.lastTwoHand=twoHand;s.gun.update();
    }
    static float handX(boolean left,boolean twoHand,float adsProgress){
        float progress=Float.isFinite(adsProgress)?Math.clamp(adsProgress,0f,1f):0f;
        float hip=twoHand?.56f:.44f;
        float x=hip+(.56f-hip)*progress;
        return left?-x:x;
    }
    static Matrix4f handMatrix(boolean left,boolean twoHand,float adsProgress){
        var hand=new Matrix4f().translation(handX(left,twoHand,adsProgress),-.52f,-.72f);
        // FirstPersonHandsAndItemsRenderer charged-crossbow idle branch. ItemDisplayRenderer
        // does not apply it, but both the two-hand gun and arm poses compensate for it.
        if(twoHand){float sign=left?-1:1;hand.translate(sign*-.641864f,0,0).rotateY(sign*(float)Math.toRadians(10));}
        return hand;
    }
    private static void apply(ItemDisplayHud h,Matrix4f local,boolean interpolate){
        var matrix=new Matrix4f().translation(0,-10_000_000,0).scale(SCALE).mul(local).rotateY((float)Math.PI);
        h.setTransformation(new Transformation(matrix));h.setInterpolationDuration(interpolate?1:0);h.setInterpolationDelay(0);h.update();
    }
    private static boolean slim(ServerPlayer p){
        var values=p.getGameProfile().properties().get("textures");
        for(var property:values)try {var n=JsonParser.parseString(new String(Base64.getDecoder().decode(property.value()),StandardCharsets.UTF_8)).getAsJsonObject();var textures=n.getAsJsonObject("textures");if(textures!=null&&textures.has("SKIN")){var skin=textures.getAsJsonObject("SKIN");return skin.has("metadata")&&skin.getAsJsonObject("metadata").has("model")&&skin.getAsJsonObject("metadata").get("model").getAsString().equals("slim");}}catch(RuntimeException ignored){}
        return Math.floorMod(p.getUUID().hashCode(),18)<9;
    }
    private static void remove(ServerPlayer p){var s=ACTIVE.remove(p.getUUID());if(s!=null){s.gun.remove();for(var h:s.arms)h.remove();}}
}
