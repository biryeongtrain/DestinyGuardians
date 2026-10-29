package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.bone.RenderedBone;
import org.joml.Quaternionf;
import org.joml.Vector3f;
import java.util.Map;
import com.google.common.collect.MapMaker;

/** Read-only copies of the actual BM 3.5.1 display transform, not worldPosition's Euler rebuild.
 * Only our server-clock scope records data. Weak keys cannot retain stopped trackers.
 */
public final class EquipmentDisplaySamples {
    // RenderedBone.equals compares the authored bone UUID, shared by every player
    // using this rig. Weak identity keys keep each live tracker's sample/cleanup local.
    private static final Map<RenderedBone, Sample> SAMPLES = new MapMaker().weakKeys().makeMap();
    record Sample(Vector3f position, Vector3f scale, Quaternionf rotation) { }
    private EquipmentDisplaySamples() { }

    public static void record(RenderedBone bone, Vector3f position, Vector3f scale, Quaternionf rotation) {
        if (!ServerPoseSampling.active()) return;
        String name = bone.name().rawName();
        if (!name.equals("pri_right_item") && !name.equals("pli_left_item")) return;
        SAMPLES.put(bone, new Sample(new Vector3f(position), new Vector3f(scale), new Quaternionf(rotation)));
    }

    static Sample sample(RenderedBone bone) { return SAMPLES.get(bone); }
    static void forget(RenderedBone bone) { SAMPLES.remove(bone); }
}
