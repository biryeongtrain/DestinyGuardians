package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.joml.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.security.MessageDigest;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class GlaiveGripW38Test {
    private JsonObject read(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    @Test void onlyThreeCompensatedGlaiveThirdPersonParentsChangeFromAcceptedW37() throws Exception {
        var baseline=read("art/weapons/w38/baseline-runtime-hashes.json");var changed=new HashSet<String>();
        for(var e:baseline.entrySet()) {
            String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(e.getKey()))));
            if(!hash.equals(e.getValue().getAsString()))changed.add(e.getKey());
        }
        // Separate the exact four reviewed Ammit changes from this stage's Glaive ownership.
        var ammit=GripContractsW163Support.ammitLegacyChanges();
        assertTrue(changed.containsAll(ammit));
        for (String path : ammit) GripContractsW163Support.assertAssetHash(path,
                baseline.get(path).getAsString());
        changed.removeAll(ammit);
        assertEquals(Set.of("src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper_twohand.json",
                "src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper_ads_twohand.json",
                "src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper_inspect_twohand.json"),changed);
        var config=read("art/weapons/w38/thirdperson-pose.json");config.remove("schema");
        for(String suffix:List.of("","_ads","_inspect")) {
            var display=read("src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper"+suffix+"_twohand.json").getAsJsonObject("display");
            assertEquals(config,display.get("thirdperson_righthand"));
            assertEquals(config,display.get("thirdperson_lefthand"),"Vanilla mirrors left rotations and X translation");
        }
    }
    @Test void longShaftIntersectsBothFistVolumesAcrossPitchAndHandedness() throws Exception {
        var d=read("art/weapons/w38/thirdperson-pose.json");
        var r=d.getAsJsonArray("rotation");var t=d.getAsJsonArray("translation");
        for(boolean left:List.of(false,true)) for(float pitch:new float[]{-25,0,25}) {
            float aim=(float)java.lang.Math.toRadians(pitch);
            float sign=left?-1:1;
            var main=new Matrix4f().translate(-5*sign,2,0).rotateY(-.3f*sign).rotateX(-(float)java.lang.Math.PI/2+aim+.1f);
            var support=new Matrix4f().translate(5*sign,2,0).rotateY(.6f*sign).rotateX(-1.5f+aim).transformPosition(new Vector3f(0,10,0));
            var fist=main.transformPosition(new Vector3f(0,10,0));
            var item=new Matrix4f(main).rotateX(-(float)java.lang.Math.PI/2).rotateY((float)java.lang.Math.PI)
                    .translate(sign,2,-10).translate(t.get(0).getAsFloat()*sign,t.get(1).getAsFloat(),t.get(2).getAsFloat())
                    .rotateXYZ((float)java.lang.Math.toRadians(r.get(0).getAsDouble()),sign*(float)java.lang.Math.toRadians(r.get(1).getAsDouble()),sign*(float)java.lang.Math.toRadians(r.get(2).getAsDouble()))
                    .scale(d.getAsJsonArray("scale").get(0).getAsFloat());
            var grip=item.transformPosition(new Vector3f(0,0,0));
            var shaft=item.transformDirection(new Vector3f(0,1,0)).normalize();
            assertTrue(new Vector3f(fist).sub(grip).cross(shaft).length()<1.5f,"Shaft intersects main fist volume: "+left);
            var delta=new Vector3f(support).sub(grip);
            assertTrue(new Vector3f(delta).cross(shaft).length()<1.2f,"Shaft must stay within support fist volume (2px half-width), not float beside it: "+left);
            assertTrue(java.lang.Math.abs(delta.dot(shaft))<6,"Both fists stay on shaft, not blade/tip");
            var aimDirection=new Vector3f(0,(float)java.lang.Math.sin(aim),-(float)java.lang.Math.cos(aim));
            assertTrue(shaft.dot(aimDirection)>.999f,"PRIMARY ACCEPTANCE: blade points along view, not sideways: "+left+"/"+pitch);
            assertTrue(java.lang.Math.abs(shaft.x)<.03f,"No lateral blade direction at normal pitch");
        }
    }
}
