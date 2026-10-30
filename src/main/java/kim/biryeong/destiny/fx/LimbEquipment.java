package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.mod.entity.BaseModPlayer;
import kr.toxicity.model.api.util.TransformedItemStack;

/** One safely-published two-hand choice. Suppliers retain no player/tracker/global registry.
 * Read by BM deferred context and mapping callbacks as well as the server thread.
 */
final class LimbEquipment {
    private static final TransformedItemStack AIR=TransformedItemStack.empty();
    record Selection(TransformedItemStack item, boolean bowInLeftHand, TransformedItemStack offItem) { }
    private static final class State { volatile Selection selection=new Selection(null,false,null); }
    private final State state=new State();
    private LimbHandPropPackets viewerProps;
    Selection selection() { return state.selection; }
    void set(TransformedItemStack item, boolean left) {
        state.selection=new Selection(item,left,null);
        if(viewerProps!=null)viewerProps.publish(false);
    }
    void dual(TransformedItemStack main, TransformedItemStack off) {
        state.selection=new Selection(main,false,off);
        if(viewerProps!=null)viewerProps.publish(false);
    }
    void clear() { set(null,false); }
    void bind(EntityTracker tracker) {
        State values=state; // Deferred bone suppliers must retain only selection, not owner/tracker.
        tracker.bones().forEach(bone->{
            String name=bone.name().rawName();
            if(name.equals("pli_left_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=values.selection;
                return current.offItem()!=null?current.offItem():current.item()!=null&&current.bowInLeftHand()?current.item():null;
            });
            else if(name.equals("pri_right_item")) ((ServerEquipmentMapping)(Object)bone).destiny$bindEquipment(()->{
                var current=values.selection;return current.item()==null?null:current.bowInLeftHand()?AIR:current.item();
            });
        });
        if(tracker.sourceEntity() instanceof BaseModPlayer player) {
            var projection=new LimbHandPropPackets(player.entity(),tracker,()->values.selection);
            viewerProps=projection;
            tracker.frame((ignored,bundlers)->projection.publish(true));
            tracker.handleCloseEvent((ignored,reason)->projection.close());
        }
    }
}
