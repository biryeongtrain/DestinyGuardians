package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.bone.*;
import kr.toxicity.model.api.data.blueprint.BlueprintElement;
import kr.toxicity.model.api.data.renderer.*;
import kr.toxicity.model.api.tracker.*;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

/** Offline fixture bypasses server/display creation only; executes real BM name parsing,
 * Tracker.bone predicates and the production projection constructor. No server or Mixin. */
class LimbHandPropBindingR4Test {
    private static final sun.misc.Unsafe UNSAFE;
    static {
        try {
            var field=sun.misc.Unsafe.class.getDeclaredField("theUnsafe");
            field.setAccessible(true); UNSAFE=(sun.misc.Unsafe)field.get(null);
            // Only the air adapter needed by BM static item mapper initialization is stubbed.
            kr.toxicity.model.api.BetterModel.register(stub(kr.toxicity.model.api.BetterModelPlatform.class));
        } catch (ReflectiveOperationException e) { throw new ExceptionInInitializerError(e); }
    }
    private static <T> T stub(Class<T> type) {
        return type.cast(java.lang.reflect.Proxy.newProxyInstance(type.getClassLoader(),new Class<?>[]{type},
                (proxy,method,args)->{
                    if(method.getName().equals("adapter") || method.getName().equals("air"))
                        return stub(method.getReturnType());
                    throw new UnsupportedOperationException(method.toString());
                }));
    }
    private static <T> T allocate(Class<T> type) throws Exception {
        return type.cast(UNSAFE.allocateInstance(type));
    }
    private static void set(Object target, Class<?> type, String field, Object value) throws Exception {
        var f=type.getDeclaredField(field); f.setAccessible(true); f.set(target,value);
    }
    private static Object get(Object target,String field) throws Exception {
        var f=LimbHandPropPackets.class.getDeclaredField(field); f.setAccessible(true);return f.get(target);
    }
    private static RenderedBone bone(String raw) throws Exception {
        BoneName name=BoneName.of(raw);
        var blueprint=new BlueprintElement.Locator(java.util.UUID.randomUUID(),name,null);
        var group=allocate(RendererGroup.class);set(group,RendererGroup.class,"parent",blueprint);
        var bone=allocate(RenderedBone.class);set(bone,RenderedBone.class,"group",group);return bone;
    }
    private static EntityTracker tracker(RenderedBone... bones) throws Exception {
        var pipeline=allocate(RenderPipeline.class);set(pipeline,RenderPipeline.class,"flattenBones",bones);
        var tracker=allocate(EntityTracker.class);set(tracker,Tracker.class,"pipeline",pipeline);return tracker;
    }
    @Test void projectionConstructorFindsBothTaggedHandBones() throws Exception {
        var left=bone("pli_left_item");var right=bone("pri_right_item");
        var tracker=tracker(left,right);
        assertEquals("left_item",left.name().name());assertEquals("right_item",right.name().name());
        // Reproduces the original API mismatch, while exercising the fixed constructor below.
        assertNull(tracker.bone("pli_left_item"));assertNull(tracker.bone("pri_right_item"));
        var projection=new LimbHandPropPackets(null,tracker,()->null);
        assertSame(left,get(projection,"left"));assertSame(right,get(projection,"right"));
    }
    @Test void untaggedSameNamesAndArmorAreNotSelected() throws Exception {
        var plainLeft=bone("left_item");var plainRight=bone("right_item");var armor=bone("head");
        var right=bone("pri_right_item");
        var projection=new LimbHandPropPackets(null,tracker(plainLeft,plainRight,armor,right),()->null);
        assertNull(get(projection,"left"));assertSame(right,get(projection,"right"));
    }
}
