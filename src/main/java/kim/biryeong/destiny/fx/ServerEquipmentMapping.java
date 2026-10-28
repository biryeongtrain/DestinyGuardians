package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.util.TransformedItemStack;
import java.util.function.Supplier;

/** Only owned equipment bones opt in. Null supplier output means current native mapping.
 * Kept until the bone dies so an already-evaluated stale write cannot resurrect a prop.
 */
public interface ServerEquipmentMapping {
    void destiny$bindEquipment(Supplier<TransformedItemStack> selection);
}
