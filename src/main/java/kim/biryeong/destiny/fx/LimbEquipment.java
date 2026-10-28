package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.util.TransformedItemStack;

/** One safely-published two-hand choice. Suppliers retain no player/tracker/global registry.
 * Read by BM deferred context and mapping callbacks as well as the server thread.
 */
final class LimbEquipment {
    private static final TransformedItemStack AIR=TransformedItemStack.empty();
    record Selection(TransformedItemStack item, boolean bowInLeftHand, TransformedItemStack offItem) { }
    private volatile Selection selection=new Selection(null,false,null);
    Selection selection() { return selection; }
    void set(TransformedItemStack item, boolean left) { selection=new Selection(item,left,null); }
    void dual(TransformedItemStack main, TransformedItemStack off) { selection=new Selection(main,false,off); }
    void clear() { set(null,false); }
    void bind(EntityTracker tracker) {
        tracker.bones().forEach(bone->{
            String name=bone.name().rawName();
            if(name.equals("pli_left_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=selection;
                return current.offItem()!=null?current.offItem():current.item()!=null&&current.bowInLeftHand()?current.item():null;
            });
            else if(name.equals("pri_right_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=selection;return current.item()==null?null:current.bowInLeftHand()?AIR:current.item();
            });
        });
    }
}
