package kim.biryeong.destiny.weapon;

import com.mojang.blaze3d.platform.NativeImage;
import com.mojang.math.Quadrant;
import net.minecraft.client.model.geom.builders.UVPair;
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
import static org.junit.jupiter.api.Assertions.*;

/** Uses the installed vanilla face baker, not the Python preview's corner table.
 *  Establishes UV orientation/geometry only; no GPU, mipmap or aesthetic claim. */
class NativeFaceUvW116Test {
    private static final ModelState IDENTITY = new ModelState() {};
    private static final ModelBaker.Interner INTERNER = new ModelBaker.Interner() {
        public Vector3fc vector(Vector3fc value) { return new Vector3f(value); }
        public BakedQuad.MaterialInfo materialInfo(BakedQuad.MaterialInfo value) { return value; }
    };

    private static final class TestSprite extends TextureAtlasSprite {
        TestSprite() {
            super(Identifier.parse("destiny:w116_uv_test"), new SpriteContents(
                    Identifier.parse("destiny:w116_uv_test"), new FrameSize(16, 16),
                    new NativeImage(16, 16, true)), 128, 128, 16, 32, 0);
        }
        @Override public void close() { contents().close(); }
    }

    private static CuboidModelElement plane(String angles, boolean mirrorNorth) {
        String json="""
                {"textures":{"0":"destiny:test"},"elements":[{
                "from":[6,8,8],"to":[10,12,8],
                "rotation":{"origin":[8,10,8],%s},"faces":{
                "south":{"uv":[4,8,12,16],"texture":"#0"},
                "north":{"uv":%s,"texture":"#0"}}}]}
                """.formatted(angles, mirrorNorth ? "[12,8,4,16]" : "[4,8,12,16]");
        return ((UnbakedCuboidGeometry)CuboidModel.fromStream(new StringReader(json)).geometry()).elements().getFirst();
    }

    private static void check(CuboidModelElement element, TextureAtlasSprite sprite) {
        var material = new BakedQuad.MaterialInfo(sprite, null, null, null, null, -1, null, 0);
        var inverse = new Matrix4f(element.rotation().transform()).invert();
        var origin = element.rotation().origin(); // Already normalized to block units by vanilla.
        for (var direction : new Direction[]{Direction.SOUTH, Direction.NORTH}) {
            var face = element.faces().get(direction);
            var rect = face.uvs();
            assertEquals(Quadrant.R0, face.rotation());
            var quad = FaceBakery.bakeQuad(INTERNER, element.from(), element.to(), face.uvs(),
                    face.rotation(), material, direction, IDENTITY, element.rotation());
            for (int i=0; i<4; i++) {
                var p = new Vector3f(quad.position(i)).sub(origin);
                inverse.transformPosition(p).add(origin).mul(16);
                float localU = (p.x-element.from().x())/(element.to().x()-element.from().x());
                float localV = (element.to().y()-p.y)/(element.to().y()-element.from().y());
                float packedU = (UVPair.unpackU(quad.packedUV(i))-sprite.getU0())/(sprite.getU1()-sprite.getU0());
                float packedV = (UVPair.unpackV(quad.packedUV(i))-sprite.getV0())/(sprite.getV1()-sprite.getV0());
                float atlasU = (packedU*16-Math.min(rect.minU(),rect.maxU()))/Math.abs(rect.maxU()-rect.minU());
                float atlasV = (packedV*16-Math.min(rect.minV(),rect.maxV()))/Math.abs(rect.maxV()-rect.minV());
                assertEquals(localU, atlasU, .003f, ()->element+" "+direction+" U");
                assertEquals(localV, atlasV, .003f, ()->element+" "+direction+" V");
            }
        }
    }

    @Test void actualVanillaBakerMapsBothSidesToTheSameIntendedTriangle() {
        try(var sprite=new TestSprite()) { check(plane("\"x\":0,\"y\":0,\"z\":0",true),sprite); }
    }
    @Test void arbitraryElementRotationDoesNotChangeTriangleIslandOrientation() {
        try(var sprite=new TestSprite()) { check(plane("\"x\":17.3,\"y\":-61.2,\"z\":134.7",true),sprite); }
    }
    @Test void verticalAndGimbalRotationsRetainTheSameUvMapping() {
        try(var sprite=new TestSprite()) {
            check(plane("\"x\":90,\"y\":90,\"z\":0",true),sprite);
            check(plane("\"x\":-90,\"y\":-90,\"z\":180",true),sprite);
        }
    }
    @Test void theCheckRejectsAnUnmirroredBackFace() {
        try(var sprite=new TestSprite()) {
            assertThrows(AssertionError.class,()->check(plane("\"x\":17,\"y\":21,\"z\":-33",false),sprite));
        }
    }
    @Test void everyEmittedNativeTrianglePlaneHasCorrectActualBakedUvOrientation() {
        int checked=0;
        try(var sprite=new TestSprite()) {
            for(var rule:WeaponSurfaceAssets.rules().values()) {
                var geometry=(UnbakedCuboidGeometry)CuboidModel.fromStream(new StringReader(rule.replacement())).geometry();
                for(var element:geometry.elements()) {
                    if(element.from().z()==element.to().z() && element.faces().size()==2
                            && element.faces().containsKey(Direction.NORTH) && element.faces().containsKey(Direction.SOUTH)) {
                        assertNotNull(element.rotation());
                        check(element,sprite);checked++;
                    }
                }
            }
        }
        assertEquals(7,WeaponSurfaceAssets.rules().size());
        // Triangles are optional in product geometry; the four synthetic tests
        // above always exercise the actual baker even for an all-cuboid revision.
        System.out.println("W116 engine-baked triangle planes checked: "+checked);
    }
}
