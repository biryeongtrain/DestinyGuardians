package kim.biryeong.destiny.experimental;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import com.mojang.math.Transformation;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemDisplayContext;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Isolated skin/UV proof, never an automatic replacement for first-person weapon hands. */
public final class ProfileArmProbe {
    // NONE skips base display transforms. This local matrix cancels LayerRenderState's T(-.5).
    static final String ITEM_JSON="""
        {"model":{"type":"minecraft:special","base":"destiny:probe/profile_arm",
          "transformation":[1,0,0,0.5,0,1,0,0.5,0,0,1,0.5,0,0,0,1],
          "model":{"type":"minecraft:player_head"}}}
        """;
    public static final String PROPERTY="destiny.weapon.profileArmsProbe";
    private static final Map<UUID,Session> ACTIVE=new HashMap<>();
    private record Session(ServerPlayer owner, List<ItemDisplayHud> parts, int started, boolean slim) {}
    private ProfileArmProbe() {}
    public static void init() {
        if (!Boolean.getBoolean(PROPERTY)) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder -> {
            builder.addPreFinishTask(pack -> {
                for (String ext:List.of("vsh","fsh")) {
                    String path="assets/minecraft/shaders/core/entity."+ext;
                    byte[] bytes=pack.getDataOrSource(path);
                    if(bytes==null) throw new IllegalStateException("Missing native shader "+path);
                    String input=new String(bytes,StandardCharsets.UTF_8);
                    String expected=ext.equals("vsh") ? "b500fe893570dce943575415fca52f0a7ea1644909b7a0f0a71fc0e4e9101db4" : "b349430785b693e8635765b7804034e28c3e6ec0e91f21fb9c224b4e226a90fa";
                    if(!sha256(bytes).equals(expected)) throw new IllegalStateException("Unsupported upstream arm shader "+path);
                    String declaration=resource("decl."+ext);
                    if(input.contains("destinyArmInfo")) throw new IllegalStateException("Duplicate arm probe shader");
                    input=once(input,"void main() {",declaration+"\nvoid main() {");
                    if(ext.equals("vsh")) {
                        int end=input.lastIndexOf('}');
                        input=input.substring(0,end)+resource("main.vsh")+input.substring(end);
                    } else input=once(input,"    vec4 color = texture(Sampler0, texCoord0);",resource("sample.fsh"));
                    pack.addData(path,PackResource.fromString(input));
                }
                pack.addData("assets/destiny/items/probe/profile_arm.json",PackResource.fromString(ITEM_JSON));
                pack.addData("assets/destiny/models/probe/profile_arm.json",PackResource.fromString("{}"));
            });
        });
        CommandRegistrationCallback.EVENT.register((dispatcher,context,environment)->dispatcher.register(
            Commands.literal("destiny").then(Commands.literal("armprobe")
                .requires(source->source.permissions().hasPermission(net.minecraft.server.permissions.Permissions.COMMANDS_GAMEMASTER))
                .then(Commands.argument("player",EntityArgument.player())
                    .then(Commands.literal("classic").executes(c->show(EntityArgument.getPlayer(c,"player"),false)))
                    .then(Commands.literal("slim").executes(c->show(EntityArgument.getPlayer(c,"player"),true)))
                    .then(Commands.literal("off").executes(c->{remove(EntityArgument.getPlayer(c,"player"));return 1;}))))));
        ServerTickEvents.END_SERVER_TICK.register(server->{
            for(var s:List.copyOf(ACTIVE.values())) {
                var owner=s.owner();int age=server.getTickCount()-s.started();
                if(age>=1200||!owner.isAlive()||owner.isRemoved()||owner.hasDisconnected()||owner.getCamera()!=owner) {remove(owner);continue;}
                // Slow isolated hinge sweep demonstrates skin UVs during native display interpolation.
                for(int i=0;i<4;i++) transform(s.parts().get(i),i,s.slim(),age);
            }
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler,server)->remove(handler.getPlayer()));
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((player,from,to)->remove(player));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity,source)->{if(entity instanceof ServerPlayer p)remove(p);});
        ServerLifecycleEvents.SERVER_STOPPING.register(server->{for(var s:List.copyOf(ACTIVE.values()))remove(s.owner());});
        DestinyGuardians.LOGGER.warn("W237 experimental profile-arm probe enabled; no weapon routes replaced");
    }
    private static int show(ServerPlayer player,boolean slim) {
        remove(player);var parts=new ArrayList<ItemDisplayHud>();
        for(int i=0;i<4;i++) {
            var stack=kim.biryeong.destiny.weapon.ProfileSkinArmCarrier.createCarrier(player.getGameProfile());
            var hud=new ItemDisplayHud();hud.updateWhenDataChanged(false);
            hud.setItem(stack);hud.setItemTransform(ItemDisplayContext.NONE);
            hud.removeWhenPlayerDied();hud.spawn(player,"destiny:profile_arm_probe_"+i);
            // DisplayRenderer normalizes light channels to four bits. Use legal channels plus a reserved Y lane.
            int id=(i%2)|((i/2)<<1)|(slim?4:0)|8;
            hud.getDisplay().setBrightnessOverride(kim.biryeong.destiny.weapon.ProfileSkinArmCarrier.marker(id));
            transform(hud,i,slim,0);parts.add(hud);
        }
        ACTIVE.put(player.getUUID(),new Session(player,parts,player.level().getServer().getTickCount(),slim));
        player.sendSystemMessage(Component.literal("W237: 스킨 팔 셰이더 실험 (60초). 기존 무기/손 교체 아님."));
        return 1;
    }
    private static void transform(ItemDisplayHud hud,int index,boolean slim,int age) {
        boolean left=index%2==1,upper=index>=2;
        float x=left?16000:-16000;
        float angle=upper?0:(float)Math.sin(age*.06)*.55f;
        if(!left) angle=-angle;
        // Pivot the forearm around its elbow, rather than rotating around the wrist.
        float y=-10_000_000;
        if(!upper) {x+=6000*(float)Math.sin(angle);y-=6000*(float)Math.cos(angle);}
        hud.setTransformation(new Transformation(new Vector3f(x,y,0),
            new Quaternionf().rotateZ(angle),new Vector3f(slim?-6000:-8000,-12000,8000),new Quaternionf()));
        hud.getDisplay().setTransformationInterpolationDuration(1);
        hud.update();
    }
    private static void remove(ServerPlayer player) {
        var s=ACTIVE.remove(player.getUUID());if(s!=null)for(var hud:s.parts())hud.remove();
    }
    private static String resource(String name) {
        try(var in=ProfileArmProbe.class.getResourceAsStream("/destiny/probe/"+name)) {
            if(in==null)throw new IllegalStateException("Missing arm shader snippet "+name);
            return new String(in.readAllBytes(),StandardCharsets.UTF_8);
        }catch(java.io.IOException e){throw new IllegalStateException(e);}
    }
    private static String sha256(byte[] bytes) {
        try {return HexFormat.of().formatHex(java.security.MessageDigest.getInstance("SHA-256").digest(bytes));}
        catch(java.security.NoSuchAlgorithmException e){throw new AssertionError(e);}
    }
    static String once(String input,String anchor,String replacement) {
        int at=input.indexOf(anchor);
        if(at<0||input.indexOf(anchor,at+anchor.length())>=0)throw new IllegalStateException("Unsupported arm shader anchor "+anchor);
        return input.substring(0,at)+replacement+input.substring(at+anchor.length());
    }
}
