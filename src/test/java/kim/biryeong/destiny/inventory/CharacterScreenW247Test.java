package kim.biryeong.destiny.inventory;

import org.junit.jupiter.api.Test;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class CharacterScreenW247Test {
    @Test void stagesNeverTargetHiddenControlsAndKeyboardCanReachEveryVisibleNode() {
        for(String stage:List.of("LOADOUT","FAMILY","WEAPON","PERKS","CHARACTER","CHARACTER_OPTIONS")) {
            Set<Integer> visible=new HashSet<>();
            for(int n=0;n<WeaponScreenLayout.NODE_COUNT;n++) if(WeaponScreenLayout.visible(n,stage)) {
                visible.add(n);var b=WeaponScreenLayout.bounds(n);
                assertEquals(n,WeaponScreenLayout.hit(b.x(),b.y(),stage),stage+" hit "+n);
            }
            for(int start:visible) {
                Set<Integer> seen=new HashSet<>();var queue=new ArrayDeque<Integer>();seen.add(start);queue.add(start);
                while(!queue.isEmpty()) {int n=queue.remove();for(var d:new int[][]{{-1,0},{1,0},{0,-1},{0,1}}) {
                    int next=WeaponScreenLayout.navigate(n,d[0],d[1],stage);assertTrue(visible.contains(next));
                    if(seen.add(next))queue.add(next);
                }}
                assertEquals(visible,seen,stage+" keyboard reachability");
            }
            assertTrue(visible.contains(WeaponScreenLayout.navigate(-1,0,0,stage)),stage+" recovers hidden pointer focus");
        }
    }
    @Test void characterAndWeaponControlsStayInTheirOwnStage() {
        assertFalse(WeaponScreenLayout.visible(0,"CHARACTER"));
        assertFalse(WeaponScreenLayout.visible(WeaponScreenLayout.CLASS,"LOADOUT"));
        assertFalse(WeaponScreenLayout.visible(WeaponScreenLayout.TEST_ARMORY,"CHARACTER"));
        for(String stage:List.of("CHARACTER","CHARACTER_OPTIONS")) {
            assertTrue(WeaponScreenLayout.visible(WeaponScreenLayout.LOADOUT_TAB,stage));
            assertTrue(WeaponScreenLayout.visible(WeaponScreenLayout.CHARACTER_TAB,stage));
            assertTrue(WeaponScreenLayout.visible(WeaponScreenLayout.CLOSE,stage));
        }
    }
}
