package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonObject;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.component.CustomModelData;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;

import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

class ProfileViewScaleCacheTest {
    private static final String PREFIX="destiny:skin_arm_w204/poses/";
    private static final Identifier ROUTE=Identifier.fromNamespaceAndPath("destiny","weapon/test");

    @Test void steadySelectorReusesResultWithoutMutatingTheSourceComponent() {
        var source=new Object();var cache=new ProfileWeaponView.SelectionCache();
        var graph=condition(0,pose("two"),pose("native"));
        var flags=new ArrayList<>(List.of(false,true,false));
        var input=new CustomModelData(List.of(0f),flags,List.of("hip"),List.of(0x123456));
        var selected=cache.resolve(source,ROUTE,graph,input,false,false,true,false);
        assertEquals(List.of(PREFIX+"two"),selected.poses());
        assertTrue(selected.carrier());
        assertEquals(List.of(false,true,false),flags,"Presentation flags must not rewrite the real item");
        assertEquals(List.of(true,false,false),selected.data().flags());
        var equalInput=new CustomModelData(List.of(0f),List.copyOf(flags),List.of("hip"),List.of(0x123456));
        for(int i=0;i<200;i++)assertSame(selected,cache.resolve(source,ROUTE,graph,equalInput,false,false,true,false));
        flags.set(2,true);
        var changed=cache.resolve(source,ROUTE,graph,input,false,false,true,false);
        assertNotSame(selected,changed,"Retained input lists cannot mutate the cache key silently");
        assertEquals(List.of(true,false,false),selected.data().flags(),"Previous output remains an immutable snapshot");
    }

    @Test void ownerRouteGraphAndPresentationBoundariesInvalidateOnlyTheirSession() {
        var source=new Object();var cache=new ProfileWeaponView.SelectionCache();
        var graph=condition(0,condition(1,pose("crouch"),pose("two")),pose("native"));
        var first=cache.resolve(source,ROUTE,graph,CustomModelData.EMPTY,false,false,true,false);
        var copiedSource=cache.resolve(new Object(),ROUTE,graph,CustomModelData.EMPTY,false,false,true,false);
        assertNotSame(first,copiedSource,"Equivalent replacement stacks are different source owners");
        var crouched=cache.resolve(source,ROUTE,graph,CustomModelData.EMPTY,false,false,true,true);
        assertEquals(List.of(PREFIX+"crouch"),crouched.poses());
        var oneHand=cache.resolve(source,ROUTE,graph,CustomModelData.EMPTY,false,false,false,false);
        assertEquals(List.of(PREFIX+"native"),oneHand.poses());assertFalse(oneHand.carrier());
        var otherRoute=cache.resolve(source,Identifier.fromNamespaceAndPath("destiny","weapon/other"),graph,
                CustomModelData.EMPTY,false,false,false,false);
        assertNotSame(oneHand,otherRoute);
        var replaced=cache.resolve(source,ROUTE,pose("replacement"),CustomModelData.EMPTY,false,false,false,false);
        assertEquals(List.of(PREFIX+"replacement"),replaced.poses());
        var separateSession=new ProfileWeaponView.SelectionCache();
        assertNotSame(first,separateSession.resolve(source,ROUTE,graph,CustomModelData.EMPTY,false,false,true,false));
    }

    @Test void handednessAndSlimChangesSelectTheirOwnPoseWithoutAStaleCacheHit() {
        var source=new Object();var cache=new ProfileWeaponView.SelectionCache();
        var graph=new JsonObject();graph.addProperty("type","minecraft:select");
        graph.addProperty("property","minecraft:display_context");
        var cases=new JsonArray();var left=new JsonObject();left.addProperty("when","firstperson_lefthand");
        left.add("model",condition(9,pose("left_slim"),pose("left_wide")));cases.add(left);
        graph.add("cases",cases);graph.add("fallback",condition(9,pose("right_slim"),pose("right_wide")));
        for(boolean handed:List.of(false,true))for(boolean slim:List.of(false,true)) {
            var selected=cache.resolve(source,ROUTE,graph,CustomModelData.EMPTY,slim,handed,false,false);
            assertEquals(List.of(PREFIX+(handed?"left_":"right_")+(slim?"slim":"wide")),selected.poses());
        }
    }

    @Test void numericSelectorKeepsSignedZeroAndNanBoundarySemantics() {
        var source=new Object();var cache=new ProfileWeaponView.SelectionCache();
        var graph=new JsonObject();graph.addProperty("type","minecraft:range_dispatch");
        graph.addProperty("property","minecraft:custom_model_data");graph.addProperty("index",1);
        var entries=new JsonArray();
        for(int i=0;i<16;i++) {var entry=new JsonObject();entry.addProperty("threshold",i);entry.add("model",pose("frame"+i));entries.add(entry);}
        graph.add("entries",entries);graph.add("fallback",pose("fallback"));
        var negative=cache.resolve(source,ROUTE,graph,data(-0f),false,false,false,false);
        var positive=cache.resolve(source,ROUTE,graph,data(+0f),false,false,false,false);
        assertEquals(List.of(PREFIX+"fallback"),negative.poses());
        assertEquals(List.of(PREFIX+"frame0"),positive.poses());assertNotSame(negative,positive);
        var nan=cache.resolve(source,ROUTE,graph,data(Float.NaN),false,false,false,false);
        assertEquals(List.of(PREFIX+"fallback"),nan.poses());
        assertSame(nan,cache.resolve(source,ROUTE,graph,data(Float.NaN),false,false,false,false));
    }

    @Test void transformSnapshotDoesNotAliasItsMutableInputAndTracksInterpolationTransitions() {
        var state=new ProfileWeaponView.TransformState();var matrix=new Matrix4f().translation(1,2,3);
        assertFalse(state.matches(matrix,false));state.remember(matrix,false);
        assertTrue(state.matches(new Matrix4f(matrix),false));
        assertFalse(state.matches(matrix,true),"A changed interpolation mode still needs one update");
        matrix.translate(0,1,0);
        assertFalse(state.matches(matrix,false),"Mutating the next target cannot mutate the previous snapshot");
        state.remember(matrix,true);assertTrue(state.matches(new Matrix4f(matrix),true));
        state.remember(matrix,false);
        for(int i=0;i<200;i++)assertTrue(state.matches(new Matrix4f(matrix),false));
    }

    private static CustomModelData data(float value) {return new CustomModelData(List.of(0f,value),List.of(),List.of(),List.of());}
    private static JsonObject pose(String suffix) {var n=new JsonObject();n.addProperty("type","minecraft:model");n.addProperty("model",PREFIX+suffix);return n;}
    private static JsonObject condition(int index,JsonObject yes,JsonObject no) {
        var n=new JsonObject();n.addProperty("type","minecraft:condition");n.addProperty("property","minecraft:custom_model_data");
        n.addProperty("index",index);n.add("on_true",yes);n.add("on_false",no);return n;
    }
}
