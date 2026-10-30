package kim.biryeong.destiny.fx;
import net.minecraft.network.syncher.EntityDataAccessor;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.*;
import net.minecraft.network.syncher.SynchedEntityData;
import net.minecraft.resources.Identifier;
import net.minecraft.world.item.*;
import org.junit.jupiter.api.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class LimbHandPropPacketsW260Test {
    private static EntityDataAccessor<ItemStack> ITEM;
    static net.minecraft.network.protocol.Packet<?> project(net.minecraft.network.protocol.Packet<?> packet,
            Map<Integer,LimbHandPropPackets.Rule> rules) {
        return LimbHandPropPackets.project(packet,rules,ITEM);
    }
    @BeforeAll @SuppressWarnings("unchecked") static void bootstrap() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion(); net.minecraft.server.Bootstrap.bootStrap();
        var field=net.minecraft.world.entity.Display.ItemDisplay.class.getDeclaredField("DATA_ITEM_STACK_ID");
        field.setAccessible(true); ITEM=(EntityDataAccessor<ItemStack>)field.get(null);
        var stick=(net.minecraft.core.Holder.Reference<Item>)net.minecraft.core.registries.BuiltInRegistries.ITEM.wrapAsHolder(Items.STICK);
        if(!stick.areComponentsBound())stick.bindComponents(net.minecraft.core.component.DataComponentMap.EMPTY);
    }
    static ItemStack item(String path) {
        var item=new ItemStack(Items.STICK);item.set(DataComponents.ITEM_MODEL,Identifier.fromNamespaceAndPath("destiny",path));return item;
    }
    static ClientboundSetEntityDataPacket packet(int id,ItemStack item) {
        return new ClientboundSetEntityDataPacket(id,List.of(SynchedEntityData.DataValue.create(ITEM,item)));
    }
    static ItemStack payload(ClientboundSetEntityDataPacket packet) {return (ItemStack)packet.packedItems().getFirst().value();}
    @Test void supportedSuperModelsUsePackagedEnemyAssets() {
        for(String path:List.of("arc_staff_h28","golden_gun_h29","shadow_bow_h28_drawn","shadow_bow_h28",
            "class_ability/hunter/blade_barrage","class_ability/hunter/spectral_blades","class_ability/hunter/gathering_storm",
            "class_ability/hunter/storms_edge","class_ability/titan/solar_super","class_ability/titan/void_super",
            "class_ability/titan/burning_maul","class_ability/warlock/solar_super","class_ability/warlock/well_of_radiance_sword_hand")) {
            var original=item(path);var rule=LimbHandPropPackets.rule(original);assertNotNull(rule,path);
            assertEquals(Identifier.fromNamespaceAndPath("destiny",path+"_enemy"),rule.enemy());
            assertEquals(Identifier.fromNamespaceAndPath("destiny",path),original.get(DataComponents.ITEM_MODEL));
        }
    }
    @Test void unsupportedForeignVanillaEmptyAndAlreadyEnemyModelsRemainUntouched() {
        assertNull(LimbHandPropPackets.rule(ItemStack.EMPTY));assertNull(LimbHandPropPackets.rule(new ItemStack(Items.STICK)));
        assertNull(LimbHandPropPackets.rule(item("missing_handprop_w260")));
        assertNull(LimbHandPropPackets.rule(item("shadow_bow_h28_enemy")));
        var foreign=item("shadow_bow_h28");foreign.set(DataComponents.ITEM_MODEL,Identifier.fromNamespaceAndPath("other","shadow_bow_h28"));
        assertNull(LimbHandPropPackets.rule(foreign));
    }
    @Test void hostileHandCopiesOnlyItemModelAndNeverMutatesBroadcastPacket() {
        var original=item("shadow_bow_h28");original.set(DataComponents.CUSTOM_NAME,net.minecraft.network.chat.Component.literal("retain-name"));
        var incoming=packet(41,original);var rule=LimbHandPropPackets.rule(original);
        var projected=assertInstanceOf(ClientboundSetEntityDataPacket.class,project(incoming,Map.of(41,rule)));
        assertNotSame(incoming,projected);assertNotSame(original,payload(projected));
        assertEquals(rule.enemy(),payload(projected).get(DataComponents.ITEM_MODEL));
        assertEquals(original.get(DataComponents.CUSTOM_NAME),payload(projected).get(DataComponents.CUSTOM_NAME));
        assertEquals(rule.original(),payload(incoming).get(DataComponents.ITEM_MODEL));
        assertSame(incoming,project(incoming,Map.of()));
    }
    @Test void otherEntitiesArmorSkinAndOtherHandModelsAreNeverChanged() {
        var original=item("shadow_bow_h28");var rules=Map.of(41,LimbHandPropPackets.rule(original));
        var skin=packet(42,original);assertSame(skin,project(skin,rules));
        var equipment=packet(41,item("golden_gun_h29"));assertSame(equipment,project(equipment,rules));
        var empty=packet(41,ItemStack.EMPTY);assertSame(empty,project(empty,rules));
        var flags=new SynchedEntityData.DataValue<>(0,net.minecraft.network.syncher.EntityDataSerializers.BYTE,(byte)0x20);
        var metadata=new ClientboundSetEntityDataPacket(41,List.of(flags));
        assertSame(metadata,project(metadata,rules));
    }
    @Test void nestedBundlesPreserveUnrelatedPacketsAndSources() {
        var item=item("arc_staff_h28");var original=packet(41,item);var other=packet(99,item);
        var inner=new ClientboundBundlePacket(List.of(original,other));var outer=new ClientboundBundlePacket(List.of(inner));
        var result=assertInstanceOf(ClientboundBundlePacket.class,project(outer,Map.of(41,LimbHandPropPackets.rule(item))));
        var nested=assertInstanceOf(ClientboundBundlePacket.class,result.subPackets().iterator().next());
        var it=nested.subPackets().iterator();var changed=assertInstanceOf(ClientboundSetEntityDataPacket.class,it.next());
        assertEquals(Identifier.fromNamespaceAndPath("destiny","arc_staff_h28_enemy"),payload(changed).get(DataComponents.ITEM_MODEL));
        assertSame(other,it.next());assertEquals(Identifier.fromNamespaceAndPath("destiny","arc_staff_h28"),payload(original).get(DataComponents.ITEM_MODEL));
    }
    @Test void dualAndLeftHandOnlyRulesStayIndependent() {
        var sword=item("class_ability/hunter/spectral_blades");var bow=item("shadow_bow_h28_drawn");
        var left=packet(41,bow);var right=packet(42,sword);
        var leftOnly=Map.of(41,LimbHandPropPackets.rule(bow));
        assertNotSame(left,project(left,leftOnly));assertSame(right,project(right,leftOnly));
        var dual=Map.of(41,LimbHandPropPackets.rule(bow),42,LimbHandPropPackets.rule(sword));
        assertNotSame(left,project(left,dual));assertNotSame(right,project(right,dual));
    }
}
