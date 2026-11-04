package kim.biryeong.destiny.weapon;

import net.minecraft.client.resources.model.cuboid.CuboidModel;
import net.minecraft.client.resources.model.cuboid.CuboidRotation;
import net.minecraft.client.resources.model.cuboid.UnbakedCuboidGeometry;
import org.joml.Matrix4f;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import java.io.StringReader;
import static org.junit.jupiter.api.Assertions.*;

/** Exact installed 26.3 parser facts, NOT renderer/performance acceptance. */
class NativeGeometryW115Test {
    private static String element(String rotation) {
        return "{\"from\":[6,8,8],\"to\":[10,12,8],\"rotation\":"+rotation
                +",\"faces\":{\"north\":{\"uv\":[16,0,0,16],\"texture\":\"#0\"},\"south\":{\"uv\":[0,0,16,16],\"texture\":\"#0\"}}}";
    }
    private static UnbakedCuboidGeometry parse(String element) {
        var model=CuboidModel.fromStream(new StringReader("{\"textures\":{\"0\":\"destiny:test\"},\"elements\":["+element+"]}"));
        return assertInstanceOf(UnbakedCuboidGeometry.class,model.geometry());
    }
    @Test void arbitraryThreeAxisElementRotationAndZeroDepthTwoFacePlaneAreAccepted() {
        var e=parse(element("{\"origin\":[8,8,8],\"x\":17.3,\"y\":-61.2,\"z\":134.7}")).elements().getFirst();
        assertEquals(e.from().z(),e.to().z());assertEquals(2,e.faces().size());
        assertInstanceOf(CuboidRotation.EulerXYZRotation.class,e.rotation().value());
        var expected=new Matrix4f().rotationZYX((float)Math.toRadians(134.7),(float)Math.toRadians(-61.2),(float)Math.toRadians(17.3));
        var actual=e.rotation().transform();
        for(var v:new Vector3f[]{new Vector3f(1,0,0),new Vector3f(0,1,0),new Vector3f(0,0,1)}) {
            assertTrue(expected.transformDirection(new Vector3f(v)).distance(actual.transformDirection(new Vector3f(v)))<0.00001f);
        }
    }
    @Test void singleAxisIsNotRestrictedToHistoricalTwentyTwoPointFiveDegreeSteps() {
        var e=parse(element("{\"origin\":[8,8,8],\"axis\":\"x\",\"angle\":67.4}")).elements().getFirst();
        assertInstanceOf(CuboidRotation.SingleAxisRotation.class,e.rotation().value());
    }
    @Test void everyRevisedWeaponPartParsesThroughTheInstalledVanillaClientModelLoader() {
        for(var rule:WeaponSurfaceAssets.rules().values()) {
            var model=CuboidModel.fromStream(new StringReader(rule.replacement()));
            var geometry=assertInstanceOf(UnbakedCuboidGeometry.class,model.geometry());
            assertFalse(geometry.elements().isEmpty());
            for(var e:geometry.elements()) {
                assertTrue(e.faces().size()>=1 && e.faces().size()<=6);
                // Opaque cuboids may omit faces covered by same-part neighbours.
                // Zero-depth contour planes still require their two visible sides.
                if(e.from().x()==e.to().x() || e.from().y()==e.to().y() || e.from().z()==e.to().z())
                    assertTrue(e.faces().size()>=2);
                if(e.rotation()!=null) for(var v:new Vector3f[]{new Vector3f(1,0,0),new Vector3f(0,1,0),new Vector3f(0,0,1)})
                    assertTrue(e.rotation().transform().transformDirection(v).isFinite());
            }
        }
    }

    @Test void parserDoesNotImposeTheHistoricalProjectTwoHundredFiftySixCubeCap() {
        var e=element("{\"origin\":[8,8,8],\"x\":0,\"y\":0,\"z\":0}");
        assertEquals(768,parse(String.join(",",java.util.Collections.nCopies(768,e))).elements().size());
    }
}
