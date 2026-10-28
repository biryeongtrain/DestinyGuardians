package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.util.TransformedItemStack;

/** One safely-published two-hand choice. Suppliers retain no player/tracker/global registry.
 * Read by BM deferred context and mapping callbacks as well as the server thread.
 */
final class LimbEquipment {
    private static final TransformedItemStack AIR=TransformedItemStack.empty();
    record Selection(TransformedItemStack item, boolean bowInLeftHand) { }
    private volatile Selection selection=new Selection(null,false);
    Selection selection() { return selection; }
    void set(TransformedItemStack item, boolean left) { selection=new Selection(item,left); }
    void clear() { set(null,false); }
    void bind(EntityTracker tracker) {
        tracker.bones().forEach(bone->{
            String name=bone.name().rawName();
            if(name.equals("pli_left_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=selection;return current.item()!=null&&current.bowInLeftHand()?current.item():null;
            });
            else if(name.equals("pri_right_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=selection;return current.item()==null?null:current.bowInLeftHand()?AIR:current.item();
            });
        });
    }
}
