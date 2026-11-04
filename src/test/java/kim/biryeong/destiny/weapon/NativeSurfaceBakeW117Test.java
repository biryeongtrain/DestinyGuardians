package kim.biryeong.destiny.weapon;

import com.mojang.blaze3d.platform.NativeImage;
import net.minecraft.client.renderer.block.dispatch.ModelState;
import net.minecraft.client.renderer.texture.SpriteContents;
import net.minecraft.client.renderer.texture.TextureAtlasSprite;
import net.minecraft.client.resources.metadata.animation.FrameSize;
import net.minecraft.client.resources.model.ModelBaker;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.CuboidModelElement;
import net.minecraft.client.resources.model.cuboid.FaceBakery;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import net.minecraft.client.resources.model.geometry.BakedQuad;
import net.minecraft.core.Direction;
import net.minecraft.resources.Identifier;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.joml.Vector3fc;
import org.junit.jupiter.api.Test;

import java.io.StringReader;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/** Actual installed 26.3 baker, all emitted solid faces as well as contour cards.
 *  This is geometry/winding verification, not GPU aliasing or source-fidelity acceptance. */
class NativeSurfaceBakeW117Test {
    private static final ModelState IDENTITY = new ModelState() {};
    private static final ModelBaker.Interner INTERNER = new ModelBaker.Interner() {
        public Vector3fc vector(Vector3fc value) { return new Vector3f(value); }
        public BakedQuad.MaterialInfo materialInfo(BakedQuad.MaterialInfo value) { return value; }
    };
    private static final class TestSprite extends TextureAtlasSprite {
        TestSprite() {
            super(Identifier.parse("destiny:w117_geometry_test"), new SpriteContents(
                    Identifier.parse("destiny:w117_geometry_test"), new FrameSize(16,16),
                    new NativeImage(16,16,true)),128,128,16,32,0);
        }
        @Override public void close() { contents().close(); }
    }
    private static List<Vector3fc> baked(CuboidModelElement e, Direction direction, TextureAtlasSprite sprite) {
        var f=e.faces().get(direction);
        var material=new BakedQuad.MaterialInfo(sprite,null,null,null,null,-1,null,0);
        var q=FaceBakery.bakeQuad(INTERNER,e.from(),e.to(),f.uvs(),f.rotation(),material,direction,IDENTITY,e.rotation());
        var result=new ArrayList<Vector3fc>();
        for(int i=0;i<4;i++)result.add(new Vector3f(q.position(i)));
        return result;
    }
    private static int axis(Direction direction) {
        return switch(direction.getAxis()) { case X -> 0; case Y -> 1; case Z -> 2; };
    }
    private static void validate(CuboidModelElement e,Direction direction,List<Vector3fc> points) {
        assertEquals(4,points.size());
        var rotation=e.rotation()==null ? new Matrix4f() : new Matrix4f(e.rotation().transform());
        var inverse=new Matrix4f(rotation).invert();
        Vector3fc origin=e.rotation()==null ? new Vector3f() : e.rotation().origin();
        int axis=axis(direction);
        float faceCoordinate=(direction.getAxisDirection()==Direction.AxisDirection.NEGATIVE ? e.from() : e.to()).get(axis);
        var corners=new HashSet<Integer>();
        for(var world:points) {
            assertTrue(world.isFinite());
            var local=new Vector3f(world).sub(origin);inverse.transformPosition(local).add(origin).mul(16);
            assertEquals(faceCoordinate,local.get(axis),.0002f,"Baked vertex escaped its declared face plane");
            int key=0;
            for(int a=0;a<3;a++) {
                if(a==axis)continue;
                float lo=e.from().get(a),hi=e.to().get(a),v=local.get(a);
                assertTrue(Math.min(Math.abs(v-lo),Math.abs(v-hi))<.0002f,"Baked vertex escaped its declared face corner");
                if(Math.abs(v-hi)<Math.abs(v-lo))key|=1<<a;
            }
            assertTrue(corners.add(key),"Face collapsed to repeated corners");
        }
        var n0=new Vector3f(points.get(1)).sub(points.get(0)).cross(new Vector3f(points.get(2)).sub(points.get(0)));
        var n1=new Vector3f(points.get(2)).sub(points.get(0)).cross(new Vector3f(points.get(3)).sub(points.get(0)));
        assertTrue(n0.isFinite() && n1.isFinite() && n0.lengthSquared()>1e-20f && n1.lengthSquared()>1e-20f,"Nonzero surface area on both GPU triangles");
        var expected=rotation.transformDirection(new Vector3f(direction.getUnitVec3f())).normalize();
        assertTrue(n0.normalize().dot(expected)>.999f,"First GPU triangle winding must face outward after arbitrary rotation");
        assertTrue(n1.normalize().dot(expected)>.999f,"Second GPU triangle winding must agree (no bow-tie quad)");
    }
    private static CuboidModelElement synthetic(boolean degenerate) {
        String model="""
                {"textures":{"0":"destiny:test"},"elements":[{
                  "from":[6,8,7],"to":[%s,12,9],
                  "rotation":{"origin":[8,10,8],"x":17.3,"y":-61.2,"z":134.7},
                  "faces":{"north":{"uv":[0,0,16,16],"texture":"#0"},
                           "south":{"uv":[0,0,16,16],"texture":"#0"},
                           "west":{"uv":[0,0,16,16],"texture":"#0"},
                           "east":{"uv":[0,0,16,16],"texture":"#0"},
                           "up":{"uv":[0,0,16,16],"texture":"#0"},
                           "down":{"uv":[0,0,16,16],"texture":"#0"}}}]}
                """.formatted(degenerate ? "6" : "10");
        return ((UnbakedCuboidGeometry)CuboidModel.fromStream(new StringReader(model)).geometry()).elements().getFirst();
    }
    @Test void sixRotatedSolidFacesPreservePlaneCornersAndOutwardGpuWinding() {
        var e=synthetic(false);
        try(var sprite=new TestSprite()) {for(var direction:Direction.values())validate(e,direction,baked(e,direction,sprite));}
    }
    @Test void negativeControlRejectsAPerturbedBakedVertex() {
        var e=synthetic(false);
        try(var sprite=new TestSprite()) {
            var p=baked(e,Direction.NORTH,sprite);p.set(0,new Vector3f(p.getFirst()).add(.01f,.02f,.03f));
            assertThrows(AssertionError.class,()->validate(e,Direction.NORTH,p));
        }
    }
    @Test void negativeControlRejectsZeroAreaSolidFace() {
        var e=synthetic(true);
        try(var sprite=new TestSprite()) {
            var p=baked(e,Direction.NORTH,sprite);
            assertThrows(AssertionError.class,()->validate(e,Direction.NORTH,p));
        }
    }
    @Test void everyEmittedProductFaceBakesWithoutCollapsedCornersOrReversedTriangles() {
        bakeRules(WeaponSurfaceAssets.rules(),"W118 authored");
    }
    @Test void optimizedW119PackOutputAlsoBakesEveryRemainingFaceWithNative26_3Baker() {
        bakeRules(WeaponSurfaceAssets.optimizeRules(WeaponSurfaceAssets.rules()).rules(),"W119 interior culled");
    }
    private static void bakeRules(java.util.Map<String,WeaponSurfaceAssets.Rule> rules,String label) {
        int faces=0;
        try(var sprite=new TestSprite()) {
            for(var rule:rules.values()) {
                var geometry=(UnbakedCuboidGeometry)CuboidModel.fromStream(new StringReader(rule.replacement())).geometry();
                for(var e:geometry.elements()) for(var direction:e.faces().keySet()) {
                    validate(e,direction,baked(e,direction,sprite));faces++;
                }
            }
        }
        assertTrue(faces>1000,"Checks whole weapons and split reload parts, not just synthetic fixtures");
        System.out.println(label+" native-baked product faces checked: "+faces);
    }
}
