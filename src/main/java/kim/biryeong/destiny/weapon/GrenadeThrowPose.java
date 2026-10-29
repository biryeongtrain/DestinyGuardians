package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import org.joml.Matrix3f;
import java.io.*;
import java.nio.charset.StandardCharsets;

/** Evaluated source FK, calibrated to view coordinates. No fingers or per-frame client models. */
public final class GrenadeThrowPose {
    private static final JsonArray FRAMES=load();
    private GrenadeThrowPose() {}
    private static JsonArray load() {
        try(var stream=GrenadeThrowPose.class.getResourceAsStream("/destiny/animation/grenade_throw_w252.json")) {
            if(stream==null)throw new IOException("Missing W252 throw poses");
            return JsonParser.parseReader(new InputStreamReader(stream,StandardCharsets.UTF_8)).getAsJsonObject().getAsJsonArray("frames");
        }catch(IOException ex){throw new IllegalStateException(ex);}
    }
    private static Vector3f point(String name,float progress,boolean mirror) {
        float f=Math.clamp(progress,0,1)*(FRAMES.size()-1);int a=(int)f,b=Math.min(a+1,FRAMES.size()-1);
        var x=FRAMES.get(a).getAsJsonObject().getAsJsonArray(name);var y=FRAMES.get(b).getAsJsonObject().getAsJsonArray(name);
        var v=new Vector3f(x.get(0).getAsFloat(),x.get(1).getAsFloat(),x.get(2).getAsFloat())
                .lerp(new Vector3f(y.get(0).getAsFloat(),y.get(1).getAsFloat(),y.get(2).getAsFloat()),f-a);
        return new Vector3f((mirror?1:-1)*v.y*.9f,(v.z-1.55f)*.9f-.08f,-v.x*.9f-.90f);
    }
    public static Matrix4f arm(int segment,float progress,boolean slim,boolean mirror) {
        boolean left=(segment%2==1)^mirror,upper=segment>=2;String side=left?"left":"right";
        Vector3f start=point(side+(upper?"Shoulder":"Elbow"),progress,mirror);
        // The rip has a world-space shoulder, not an authored first-person camera.
        // Keep the evaluated elbow/wrist path while rooting upper arms below the view.
        if(upper)start.set(segment%2==1?-.32f:.32f,-.80f,-.72f);
        Vector3f end=point(side+(upper?"Elbow":"Wrist"),progress,mirror);
        Vector3f axis=new Vector3f(end).sub(start);float length=axis.length();
        Quaternionf q=new Quaternionf().rotationTo(new Vector3f(0,1,0),axis.normalize());
        // Native SkullModel head spans Y=-.5..0 after item-local centering.
        // Match weapon arms: negative Y is proximal, zero is distal.
        return new Matrix4f().translation(end).rotate(q).scale(slim?-.225f:-.3f,length*2,.3f);
    }
    public static Matrix4f prop(float progress,boolean mirror) {
        return new Matrix4f().translation(point("leftWrist",progress,mirror)).scale(.56f);
    }
    /** Interpolate joints and twist, rebuilding the segment instead of shearing its matrix. */
    public static Matrix4f blendArm(Matrix4f from,Matrix4f to,float t,boolean slim) {
        if(t<=0)return new Matrix4f(from);
        if(t>=1)return new Matrix4f(to);
        var start=new Vector3f(0,-.5f,0).mulPosition(from).lerp(new Vector3f(0,-.5f,0).mulPosition(to),t);
        var end=new Vector3f().mulPosition(from).lerp(new Vector3f().mulPosition(to),t);
        var axis=new Vector3f(end).sub(start);float length=axis.length();
        var rotation=rotation(from).slerp(rotation(to),t);
        var direction=new Vector3f(0,1,0).rotate(rotation);
        rotation=new Quaternionf().rotationTo(direction,axis.normalize()).mul(rotation);
        return new Matrix4f().translation(end).rotate(rotation).scale(slim?-.225f:-.3f,length*2,.3f);
    }
    private static Quaternionf rotation(Matrix4f arm) {
        var x=arm.getColumn(0,new Vector3f()).normalize().negate();
        var y=arm.getColumn(1,new Vector3f()).normalize();
        var z=arm.getColumn(2,new Vector3f()).normalize();
        return new Quaternionf().setFromNormalized(new Matrix3f().setColumn(0,x).setColumn(1,y).setColumn(2,z));
    }
}
