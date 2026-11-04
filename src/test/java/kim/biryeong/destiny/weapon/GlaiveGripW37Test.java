package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.joml.Vector3f;
import org.joml.Quaternionf;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import java.security.MessageDigest;
import java.util.HexFormat;
import static org.junit.jupiter.api.Assertions.*;

class GlaiveGripW37Test {
    private JsonObject json(String path) throws Exception {
        return JsonParser.parseString(Files.readString(Path.of(path))).getAsJsonObject();
    }
    @Test void onlyGlaiveHeldDisplaysMayChangeWhileOtherRuntimeAssetsRemainByteIdentical() throws Exception {
        var before=json("art/weapons/w37/baseline-runtime-hashes.json");
        var changed=new HashSet<String>();
        for(var pair:before.entrySet()) {
            String name=pair.getKey();String hash=HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(Files.readAllBytes(Path.of(name))));
            if(!hash.equals(pair.getValue().getAsString()))changed.add(name);
        }
        // Separate the exact four reviewed Ammit changes from this stage's Glaive ownership.
        var ammit=GripContractsW163Support.ammitLegacyChanges();
        assertTrue(changed.containsAll(ammit));
        for (String path : ammit) GripContractsW163Support.assertAssetHash(path,
                before.get(path).getAsString());
        changed.removeAll(ammit);
        var expected=new HashSet<String>();
        for (String pose : List.of("", "_ads", "_inspect")) for (String grip : List.of("", "_twohand"))
            expected.add("src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper"+pose+grip+".json");
        assertEquals(expected, changed, "Exactly six Glaive files, with independently validated Ammit ownership");
        assertEquals(WeaponModels.Grip.TWO_HAND,WeaponModels.defaultGrip(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()));
        assertTrue(WeaponModels.supportsTwoHand(WeaponCatalog.find("nezarec_s_whisper").orElseThrow()),"W38 enables a shaft-specific two-hand parent, not rifle transforms");
    }
    @Test void localShaftPointsForwardRatherThanUprightAndBothHandsUseNativeMirroring() throws Exception {
        var config=json("art/weapons/w37/firstperson-poses.json").getAsJsonObject("poses");
        for(String state:List.of("hip","ads","inspect")) {
            String suffix=state.equals("hip")?"":"_"+state;
            var d=json("src/main/resources/assets/destiny/models/weapon/glaive/nezarec_s_whisper"+suffix+".json").getAsJsonObject("display");
            var right=d.getAsJsonObject("firstperson_righthand");
            assertEquals(config.get(state),right);
            assertEquals(right,d.getAsJsonObject("firstperson_lefthand"),"Native code mirrors, not handwritten double reflection");
            for(boolean left:List.of(false,true)) {
                var a=right.getAsJsonArray("rotation");float sign=left?-1:1;
                var rotation=new Quaternionf().rotationXYZ((float)Math.toRadians(a.get(0).getAsDouble()),
                        sign*(float)Math.toRadians(a.get(1).getAsDouble()),sign*(float)Math.toRadians(a.get(2).getAsDouble()));
                var shaft=new Vector3f(0,1,0).rotate(rotation);
                assertTrue(shaft.z<-.5f,"Long local +Y shaft must project into the forward -Z hemisphere: "+state);
                if(!state.equals("inspect")) assertTrue(shaft.z<-.9f&&shaft.y>0&&shaft.y<.4f,"Ready shaft is foreshortened, not vertical");
            }
        }
    }
}
