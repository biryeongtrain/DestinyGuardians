package kim.biryeong.destiny.experimental;
import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import com.mojang.math.Transformation;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;
class ProfileArmProbeTest {
    @Test void nativeExtendedMatrixOffsetsBothHeadAndElbowOrigin() {
        var model=JsonParser.parseString(ProfileArmProbe.ITEM_JSON).getAsJsonObject().getAsJsonObject("model");
        var nativeTransform=Transformation.EXTENDED_CODEC.parse(JsonOps.INSTANCE,model.get("transformation")).getOrThrow();
        var matrix=nativeTransform.getMatrix();
        // Client LayerRenderState always translates -.5 after the explicit local transform.
        matrix=new org.joml.Matrix4f(matrix).translate(-.5f,-.5f,-.5f);
        assertEquals(0f,new Vector3f(0,0,0).mulPosition(matrix).length(),1e-6f);
        var elbow=new Vector3f(0,-.5f,0).mulPosition(matrix);
        assertEquals(0f,elbow.x(),1e-6f);assertEquals(-.5f,elbow.y(),1e-6f);assertEquals(0f,elbow.z(),1e-6f);
    }
}
