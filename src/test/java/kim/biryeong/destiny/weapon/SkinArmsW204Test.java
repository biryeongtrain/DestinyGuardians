package kim.biryeong.destiny.weapon;

import net.minecraft.world.item.component.CustomModelData;
import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class SkinArmsW204Test {
    @Test void vanillaUuidDefaultsIncludeClassicSlimAndBareSleeveData() {
        assertTrue(WeaponSkinArms.defaultPixels(new UUID(0,0),3).slim());
        assertFalse(WeaponSkinArms.defaultPixels(new UUID(0,9),3).slim());
        for(int i=0;i<18;i++) {
            var skin=WeaponSkinArms.defaultPixels(new UUID(0,i),3);
            var bare=WeaponSkinArms.defaultPixels(new UUID(0,i),0);
            int n = i < 9 ? 96 : 112;
            for (var pixels : List.of(skin, bare)) {
                assertEquals(n, pixels.right().size()); assertEquals(n, pixels.left().size());
                assertEquals(n, pixels.rightUpper().size()); assertEquals(n, pixels.leftUpper().size());
            }
            assertEquals(skin.slim(),bare.slim());
            assertNotEquals(bare.right(), bare.rightUpper()); assertNotEquals(bare.left(), bare.leftUpper());
            var rightOnly = WeaponSkinArms.defaultPixels(new UUID(0,i),1);
            var leftOnly = WeaponSkinArms.defaultPixels(new UUID(0,i),2);
            assertEquals(skin.rightUpper(),rightOnly.rightUpper()); assertEquals(bare.leftUpper(),rightOnly.leftUpper());
            assertEquals(bare.rightUpper(),leftOnly.rightUpper()); assertEquals(skin.leftUpper(),leftOnly.leftUpper());
        }
    }
    @Test void actualSkinPixelsComposeAtReservedOffsetsWithoutChangingLiveWeaponSelectors() {
        var floats = List.of(.4f, .7f, 3f); var flags = List.of(true, false);
        var old = new CustomModelData(floats, flags, List.of("existing"), List.of(0x123456));
        var pixels = new WeaponSkinArms.Pixels(false, Collections.nCopies(112, 0x102030), Collections.nCopies(112, 0x405060),
                Collections.nCopies(112, 0x708090), Collections.nCopies(112, 0xa0b0c0));
        var out = WeaponSkinArms.merge(old, pixels);
        assertEquals(floats, out.floats()); assertEquals(old.strings(), out.strings());
        assertEquals(flags, out.flags().subList(0, 2)); assertTrue(out.flags().get(8)); assertFalse(out.flags().get(9));
        assertEquals(0x123456, out.colors().get(0)); assertEquals(0x102030, out.colors().get(64)); assertEquals(0x405060, out.colors().get(192));
        assertEquals(576, out.colors().size());
        assertEquals(0x708090, out.colors().get(320)); assertEquals(0x708090, out.colors().get(431));
        assertEquals(0xa0b0c0, out.colors().get(448)); assertEquals(0xa0b0c0, out.colors().get(559));
        assertEquals(0xffffff, out.colors().get(575));
        assertEquals(1, old.colors().size()); assertEquals(2, old.flags().size());
    }
    @Test void mergePreservesEveryUnownedFieldIncludingStrideGapsAndTail() {
        for (boolean slim : List.of(false,true)) {
            int n = slim ? 96 : 112;
            var oldColors = new ArrayList<Integer>();
            for (int i=0; i<600; i++) oldColors.add(i);
            var old = new CustomModelData(List.of(1f), Collections.nCopies(16,true), List.of("selector"), List.copyOf(oldColors));
            var pixels = new WeaponSkinArms.Pixels(slim, Collections.nCopies(n, 1010), Collections.nCopies(n, 2020),
                    Collections.nCopies(n, 3030), Collections.nCopies(n, 4040));
            var out = WeaponSkinArms.merge(old,pixels);
            for (int i=0; i<600; i++) {
                int expected = i;
                int[] offsets = {64,192,320,448};
                for (int j=0; j<offsets.length; j++) if (i>=offsets[j] && i<offsets[j]+n) expected=(j+1)*1010;
                assertEquals(expected,out.colors().get(i));
            }
            assertEquals(oldColors,old.colors()); assertEquals(old.floats(),out.floats()); assertEquals(old.strings(),out.strings());
            for (int i=0;i<16;i++) assertEquals(i==9?slim:true,out.flags().get(i));
            var hidden = WeaponSkinArms.merge(out,null);
            assertFalse(hidden.flags().get(8)); assertFalse(hidden.flags().get(9));
            assertEquals(out.colors(),hidden.colors());
        }
    }
    @Test void sleeveUsesBetterModelQuantizedAlphaAndCanBeHidden() {
        var data = new CustomModelData(List.of(0f, 1f, 2f), List.of(), List.of(),
                List.of(0x102030,0x102030,0x102030, 0xf0e0d0,0xf0e0d0,0xf0e0d0));
        assertEquals(List.of(0x102030,0x808080,0xf0e0d0), WeaponSkinArms.flatten(data, 3, true));
        assertEquals(List.of(0x102030,0x102030,0x102030), WeaponSkinArms.flatten(data, 3, false));
        assertThrows(IllegalArgumentException.class, () -> WeaponSkinArms.flatten(data, 4, true));
    }
    @Test void upperSkinSkipsOnlyTheVerifiedOptionalNineArmorColors() {
        var data = new CustomModelData(List.of(0f,1f,2f), List.of(), List.of(),
                List.of(0x102030,0x102030,0x102030,0xf0e0d0,0xf0e0d0,0xf0e0d0));
        var prefixedColors = new ArrayList<>(Collections.nCopies(9,0xffffff));
        prefixedColors.addAll(data.colors());
        var prefixed = new CustomModelData(data.floats(),List.of(),List.of(),prefixedColors);
        for (var upper : List.of(data,prefixed)) {
            assertEquals(List.of(0x102030,0x808080,0xf0e0d0),WeaponSkinArms.flattenUpper(upper,3,true));
            assertEquals(List.of(0x102030,0x102030,0x102030),WeaponSkinArms.flattenUpper(upper,3,false));
        }
        assertThrows(IllegalArgumentException.class, () -> WeaponSkinArms.flatten(prefixed,3,true));
        assertThrows(IllegalArgumentException.class, () -> WeaponSkinArms.flattenUpper(null,3,true));
        assertThrows(IllegalArgumentException.class, () -> WeaponSkinArms.flattenUpper(
                new CustomModelData(data.floats(),List.of(),List.of(),prefixedColors.subList(1,prefixedColors.size())),3,true));
        assertThrows(IllegalArgumentException.class, () -> WeaponSkinArms.flattenUpper(
                new CustomModelData(List.of(),List.of(),List.of(),data.colors()),3,true));
    }
    @Test void unavailableSkinHidesBothArmsRatherThanShowingWrongPlayerAndSlimLayoutIsExplicit() {
        var old = CustomModelData.EMPTY;
        var hidden = WeaponSkinArms.merge(old, null); assertFalse(hidden.flags().get(8));
        var slim = new WeaponSkinArms.Pixels(true, Collections.nCopies(96, 1), Collections.nCopies(96, 2),
                Collections.nCopies(96, 3), Collections.nCopies(96, 4));
        assertTrue(WeaponSkinArms.merge(old, slim).flags().get(9));
        assertThrows(IllegalArgumentException.class, () -> new WeaponSkinArms.Pixels(true, List.of(), List.of(), List.of(), List.of()));
        assertThrows(IllegalArgumentException.class, () -> new WeaponSkinArms.Pixels(true, slim.right(), slim.left(), List.of(), List.of()));
        assertThrows(NullPointerException.class, () -> new WeaponSkinArms.Pixels(true, slim.right(), slim.left(), null, null));
    }
}
