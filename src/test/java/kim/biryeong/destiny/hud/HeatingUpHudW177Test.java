package kim.biryeong.destiny.hud;

import com.google.gson.JsonParser;
import com.mojang.serialization.JsonOps;
import net.minecraft.client.color.item.ItemTintSources;
import net.minecraft.client.renderer.item.ItemModels;
import net.minecraft.client.resources.model.cuboid.CuboidModel;
import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.io.StringReader;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class HeatingUpHudW177Test {
    private static final WeaponPerkRows.Kind KIND=WeaponPerkRows.Kind.HEATING_UP;
    static WeaponPerkRows.Snapshot state(int stacks,int ticks) {
        return new WeaponPerkRows.Snapshot(0,0,0,0,0,0,0,false,0,0,0,false,0,0,0,0,0,0,0,0,0,0,0,0,0,stacks,ticks);
    }
    @Test void allActualWindowsShowEightNodesAndCeilSeconds() {
        for(int n=1;n<=2;n++)for(int t=1;t<=110;t++) {
            var row=WeaponPerkRows.project(state(n,t)).getFirst();
            assertEquals(KIND,row.kind());assertEquals(n,row.count());assertEquals(t,row.ticks());
            assertEquals((t+19)/20,row.seconds());assertEquals(8,KIND.nodeIds().size());
            assertEquals("perk_heating_up_w177",row.label());assertEquals(778,row.y());
        }
        assertEquals(WeaponPerkRows.Layout.COUNT_TIMER,KIND.layout);
    }
    @Test void corruptOrInconsistentWindowsStayAbsent() {
        for(int n:new int[]{Integer.MIN_VALUE,-1,0,1,2,3,Integer.MAX_VALUE})
            for(int t:new int[]{Integer.MIN_VALUE,-1,0,1,110,111,Integer.MAX_VALUE})
                assertEquals(n>=1&&n<=2&&t>=1&&t<=110,!WeaponPerkRows.project(state(n,t)).isEmpty());
    }
    @Test void allLegacyAritiesRemainAndTwentyFifthArgumentIsStillStatsForAll() {
        var old=new WeaponPerkRows.Snapshot(0,0,0,0,0,0,0,false,0,0,0,false,0,0,0,0,0,0,0,0,0,0,0,0,200);
        assertEquals(200,old.statsForAllTicks());assertEquals(0,old.heatingUpStacks());assertEquals(0,old.heatingUpTicks());
        assertEquals(Set.of(14,16,18,19,20,21,23,24,25,27,28,29,35,38,40),Arrays.stream(WeaponPerkRows.Snapshot.class.getDeclaredConstructors())
                .map(java.lang.reflect.Constructor::getParameterCount).collect(java.util.stream.Collectors.toSet()));
        assertEquals("heatingUpStacks",WeaponPerkRows.Snapshot.class.getRecordComponents()[25].getName());
        assertEquals("heatingUpTicks",WeaponPerkRows.Snapshot.class.getRecordComponents()[26].getName());
    }
    @Test void priorityCapPromotionAndRemovalUseCurrentObservedTime() {
        var busy=new WeaponPerkRows.Snapshot(99,87,3,61,0,0,0,false,0,0,199,false,0,0,0,0,0,0,0,0,0,0,0,0,0,2,110);
        assertEquals(4,WeaponPerkRows.project(busy).size());
        assertFalse(WeaponPerkRows.project(busy).stream().anyMatch(x->x.kind()==KIND));
        assertEquals(KIND.nodeIds().stream().sorted().toList(),WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(busy),KIND.nodeIds()));
        var promoted=WeaponPerkRows.project(state(2,21)).getFirst();assertEquals(21,promoted.ticks());assertEquals(2,promoted.seconds());
        assertEquals(KIND.nodeIds().stream().sorted().toList(),WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(state(0,0)),KIND.nodeIds()));
        assertTrue(WeaponPerkRows.Kind.values().length>=21);assertEquals(KIND,WeaponPerkRows.Kind.values()[19]);
        var all=Arrays.stream(WeaponPerkRows.Kind.values()).flatMap(x->x.nodeIds().stream()).toList();
        assertEquals(all.size(),Set.copyOf(all).size());
    }
    @Test void actual26CodecsAcceptLabelAndRejectWrongGraphType() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var base=Path.of("src/main/resources/assets/destiny");String name="perk_heating_up_w177";
        var graph=JsonParser.parseString(Files.readString(base.resolve("items/gui/hud/"+name+".json"))).getAsJsonObject().getAsJsonObject("model");
        assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,graph).isSuccess());
        var bad=graph.deepCopy();bad.addProperty("type","destiny:missing");assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE,bad).isSuccess());
        assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(base.resolve("models/gui/hud/"+name+".json")))));
        var image=ImageIO.read(base.resolve("textures/item/hud/"+name+".png").toFile());
        assertEquals(118,image.getWidth());assertEquals(24,image.getHeight());int visible=0;
        for(int y=0;y<24;y++)for(int x=0;x<118;x++) {int a=image.getRGB(x,y)>>>24;if(a>0)visible++;
            if(x==0||x==117||y==0||y==23)assertEquals(0,a);}
        assertTrue(visible>300);assertTrue(Files.readString(Path.of("art/hud/w177/heating-up.svg")).contains("HEATING UP"));
    }
}
