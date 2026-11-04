package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.campaign.fallen.SkiffDrop;
import net.minecraft.core.BlockPos;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.world.level.levelgen.Heightmap;
import net.minecraft.world.phys.Vec3;
import java.util.List;

/** Feasibility evidence only. Does not spawn ships or alter planned enemy pads. */
public final class DevilsSkiffSurvey {
    public static void inspect(GameTestHelper h, ServerLevel level, DevilsPlan.Zone zone) {
        if (zone == DevilsPlan.Zone.RY) inspectCompiledMotion(h);
        var anchors=switch(zone) {
            case RY -> List.of("RY.L");
            case RF -> List.of("RF.A","RF.D");
            case BL -> List.of("BL.EXIT","BL.L","BL.R","BL.H");
            case SP -> List.of("SP.D1","SP.D2");
        };
        var origin=DevilsWorldBuild.origin(zone);
        if (zone != DevilsPlan.Zone.RF) {
            var blocked = new java.util.ArrayList<String>();
            for (var id : anchors) for (var pad : DevilsMaps.candidates(zone,id,origin)) {
                var routes = kim.biryeong.destiny.campaign.presentation.DevilsTransportPaths.candidates(pad.pos());
                boolean clear = routes.stream().anyMatch(route ->
                        kim.biryeong.destiny.activity.presentation.ModelTransport.clearRoute(level,route));
                if (!clear) blocked.add(id+"@"+pad.pos()+":"+routes.stream().map(route ->
                        kim.biryeong.destiny.activity.presentation.ModelTransport.inspectRoute(level,route).name()).toList());
            }
            System.out.println("DEVILS_TRANSPORT_ROUTES " + zone + " blocked=" + blocked);
            h.assertTrue(blocked.isEmpty(), "Skiff route must serve actual spawn alternatives: " + blocked);
        }
        var eye=DevilsMaps.anchor(zone,zone.name()+".IN",origin).pos().add(0,1.62,0);
        var grid=new SkiffDrop.Sky.Grid() {
            public boolean solid(int x,int y,int z) {
                var p=new BlockPos(x,y,z);
                return !level.hasChunkAt(p)||!level.getBlockState(p).getCollisionShape(level,p).isEmpty();
            }
            public boolean sky(int x,int y,int z) {
                return level.hasChunkAt(new BlockPos(x,y,z))&&y>=level.getHeight(Heightmap.Types.MOTION_BLOCKING,x,z);
            }
        };
        for(var id:anchors) {
            var ground=DevilsMaps.anchor(zone,id,origin).pos();
            var start=System.nanoTime();
            var spot=SkiffDrop.Sky.find(grid,List.of(ground),ground,null,0,eye);
            var row=new com.google.gson.JsonObject();
            row.addProperty("anchor",id);row.addProperty("found",spot.isPresent());
            row.addProperty("reads",SkiffDrop.Sky.lastReads());row.addProperty("microseconds",(System.nanoTime()-start)/1000);
            if(spot.isPresent()) {
                var v=spot.get();row.addProperty("kind",v.kind().name());row.addProperty("yaw",v.yaw());
                var pos=new com.google.gson.JsonArray();pos.add(v.hover().x);pos.add(v.hover().y);pos.add(v.hover().z);row.add("hover",pos);
                row.addProperty("visibleFromEntry",v.viewerSees());row.addProperty("offset",v.offset());
                // Conservative high-sky envelope at the actual arrive/depart hull-position keyframes.
                // Full pitch/curve interpolation is not certified by these sparse samples.
                double[][] arrive={{87.5,16.25},{26.25,7.5},{3.75,1.875},{.5,.25},{0,0}};
                double[][] depart={{0,0},{.625,2.5},{-16.25,8.75},{-112.5,26.25}};
                row.add("arriveHullKeyframes",sample(level,grid,v,arrive));row.add("departHullKeyframes",sample(level,grid,v,depart));
            }
            System.out.println("DEVILS_SKIFF_SURVEY "+row);
        }
    }
    /** Dump BetterModel's compiled curve, not a linear approximation of the source keyframes. */
    private static void inspectCompiledMotion(GameTestHelper h) {
        var model = kr.toxicity.model.api.BetterModel.model("rg_skiff").orElseThrow();
        for (String clip : List.of("arrive", "drop", "depart")) {
            var animation = model.animations().get(clip);
            h.assertTrue(animation != null, "Skiff animation missing: " + clip);
            for (var entry : animation.animator().entrySet()) {
                var row = new com.google.gson.JsonObject();
                row.addProperty("clip", clip);
                row.addProperty("bone", entry.getKey().name());
                row.addProperty("length", animation.length());
                var frames = new com.google.gson.JsonArray();
                for (var progress : entry.getValue().keyframe().progresses()) {
                    h.assertTrue(Float.isFinite(progress.time()) && progress.time() >= 0,
                            "Invalid compiled skiff frame time: " + clip);
                    var movement = progress.animate(new kr.toxicity.model.api.bone.BoneMovement(),
                            new kr.toxicity.model.api.bone.BoneMovement());
                    h.assertTrue(movement.position().isFinite() && movement.rotation().isFinite(),
                            "Non-finite compiled skiff movement: " + clip);
                    var frame = new com.google.gson.JsonObject();
                    frame.addProperty("rawTime", progress.time());
                    frame.add("position", vector(movement.position()));
                    frame.add("scale", vector(movement.scale()));
                    frame.add("rawRotation", vector(movement.rawRotation()));
                    var rotation = new com.google.gson.JsonArray();
                    rotation.add(movement.rotation().x); rotation.add(movement.rotation().y);
                    rotation.add(movement.rotation().z); rotation.add(movement.rotation().w);
                    frame.add("rotation", rotation);
                    frame.addProperty("skipInterpolation", progress.skipInterpolation());
                    frame.addProperty("globalRotation", progress.globalRotation());
                    frames.add(frame);
                }
                row.add("frames", frames);
                System.out.println("DEVILS_SKIFF_COMPILED " + row);
            }
        }
    }
    private static com.google.gson.JsonArray vector(org.joml.Vector3f v) {
        var result = new com.google.gson.JsonArray();
        result.add(v.x); result.add(v.y); result.add(v.z);
        return result;
    }
    private static com.google.gson.JsonArray sample(ServerLevel level,SkiffDrop.Sky.Grid grid,SkiffDrop.Sky.Spot spot,double[][] points) {
        var result=new com.google.gson.JsonArray();double yaw=Math.toRadians(spot.yaw());
        for(var p:points) {
            var hover=spot.hover().add(-Math.sin(yaw)*p[0],p[1],Math.cos(yaw)*p[0]);
            int unloaded=0,blocked=0;
            var columns=new java.util.HashSet<BlockPos>();
            for(double a=-SkiffDrop.Sky.HULL_BACK;a<=SkiffDrop.Sky.HULL_FRONT+1e-9;a+=.5)
                for(double b=-SkiffDrop.Sky.HULL_HALF_WIDTH;b<=SkiffDrop.Sky.HULL_HALF_WIDTH+1e-9;b+=SkiffDrop.Sky.HULL_HALF_WIDTH/2)
                    columns.add(BlockPos.containing(hover.x-Math.sin(yaw)*a+Math.cos(yaw)*b,hover.y-SkiffDrop.Sky.HULL_BELOW,
                            hover.z+Math.cos(yaw)*a+Math.sin(yaw)*b));
            for(var at:columns) {
                if(!level.hasChunkAt(at))unloaded++;
                else if(at.getY()<level.getHeight(Heightmap.Types.MOTION_BLOCKING,at.getX(),at.getZ()))blocked++;
            }
            var row=new com.google.gson.JsonObject();row.addProperty("clear",SkiffDrop.Sky.hullFits(grid,hover,spot.yaw()));
            row.addProperty("unloadedColumns",unloaded);row.addProperty("blockedColumns",blocked);result.add(row);
        }
        return result;
    }
}
