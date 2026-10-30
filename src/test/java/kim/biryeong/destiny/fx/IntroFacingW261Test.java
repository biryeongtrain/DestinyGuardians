package kim.biryeong.destiny.fx;

import com.google.gson.JsonParser;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import org.junit.jupiter.api.Test;
import java.nio.file.Files;
import java.nio.file.Path;
import static org.junit.jupiter.api.Assertions.*;

class IntroFacingW261Test {
    @Test void allSixSourceEndingsFaceForwardWithoutChangingTheirTilt() throws Exception {
        var source=JsonParser.parseString(Files.readString(Path.of(
                "src/main/resources/destiny/animation/crucible_intro_w260.animation.json")))
                .getAsJsonObject().getAsJsonArray("animations");
        int checked=0;
        for(var entry:source) {
            var clip=entry.getAsJsonObject();
            for(var bone:clip.getAsJsonObject("animators").entrySet()) {
                var animator=bone.getValue().getAsJsonObject();
                if(!animator.get("name").getAsString().equals("player_root"))continue;
                com.google.gson.JsonObject last=null;
                for(var key:animator.getAsJsonArray("keyframes"))
                    if(key.getAsJsonObject().get("channel").getAsString().equals("rotation"))
                        last=key.getAsJsonObject().getAsJsonArray("data_points").get(0).getAsJsonObject();
                assertNotNull(last);
                var q=new Quaternionf().rotateZYX((float)Math.toRadians(last.get("z").getAsDouble()),
                        (float)Math.toRadians(last.get("y").getAsDouble()),(float)Math.toRadians(last.get("x").getAsDouble()));
                var before=q.transform(new Vector3f(0,0,-1));
                var after=new Quaternionf().rotationY(IntroFacing.correctionRadians(clip.get("name").getAsString()))
                        .mul(q).transform(new Vector3f(0,0,-1));
                assertEquals(0,after.x,0.0001,clip.get("name").getAsString());
                assertTrue(after.z<0);assertEquals(before.y,after.y,0.00001);checked++;
            }
        }
        assertEquals(6,checked);
        assertEquals(0,IntroFacing.correctionRadians("h15_grenade"));
    }
}
