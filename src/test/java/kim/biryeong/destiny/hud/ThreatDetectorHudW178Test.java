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

class ThreatDetectorHudW178Test {
    private static final WeaponPerkRows.Kind KIND=WeaponPerkRows.Kind.THREAT_DETECTOR;
    static WeaponPerkRows.Snapshot state(int stacks) {
        return new WeaponPerkRows.Snapshot(0,0,0,0,0,0,0,false,0,0,0,false,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,stacks);
    }
    @Test void actualTiersShowFourCountNodesWithoutInventingTimer() {
        for(int n=1;n<=2;n++) {
            var row=WeaponPerkRows.project(state(n)).getFirst();
            assertEquals(KIND,row.kind());assertEquals(n,row.count());assertEquals(n,row.displayCount());
            assertEquals(0,row.ticks());assertEquals(0,row.seconds());assertEquals(778,row.y());
            assertEquals("perk_threat_detector_w178",row.label());
        }
        assertEquals(WeaponPerkRows.Layout.COUNT,KIND.layout);
        assertEquals(List.of("marker","label","x","count"),KIND.layout.suffixes);
        assertTrue(KIND.nodeIds().stream().noneMatch(x->x.endsWith("minutes")||x.endsWith("tens")||x.endsWith("ones")));
    }
    @Test void absentAndCorruptTiersStayHidden() {
        for(int n:new int[]{Integer.MIN_VALUE,-1,0,3,100,Integer.MAX_VALUE})assertTrue(WeaponPerkRows.project(state(n)).isEmpty());
    }
    @Test void legacy27PreservesHeatingAndAllEarlierConstructorArities() {
        var old=new WeaponPerkRows.Snapshot(0,0,0,0,0,0,0,false,0,0,0,false,0,0,0,0,0,0,0,0,0,0,0,0,0,2,110);
        assertEquals(2,old.heatingUpStacks());assertEquals(110,old.heatingUpTicks());assertEquals(0,old.threatDetectorStacks());
        assertEquals(List.of(WeaponPerkRows.Kind.HEATING_UP),WeaponPerkRows.project(old).stream().map(WeaponPerkRows.Row::kind).toList());
        assertEquals(Set.of(14,16,18,19,20,21,23,24,25,27,28,29,35,38,40),Arrays.stream(WeaponPerkRows.Snapshot.class.getDeclaredConstructors()).map(java.lang.reflect.Constructor::getParameterCount).collect(java.util.stream.Collectors.toSet()));
        assertTrue(WeaponPerkRows.Snapshot.class.getRecordComponents().length>=28);
        assertEquals("threatDetectorStacks",WeaponPerkRows.Snapshot.class.getRecordComponents()[27].getName());
    }
    @Test void stablePriorityCapPromotionAndStowRemoval() {
        var busy=new WeaponPerkRows.Snapshot(99,87,3,61,0,0,0,false,0,0,199,false,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2);
        assertEquals(4,WeaponPerkRows.project(busy).size());
        assertFalse(WeaponPerkRows.project(busy).stream().anyMatch(row->row.kind()==KIND));
        assertEquals(KIND.nodeIds().stream().sorted().toList(),WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(busy),KIND.nodeIds()));
        assertEquals(2,WeaponPerkRows.project(state(2)).getFirst().count());
        assertEquals(KIND.nodeIds().stream().sorted().toList(),WeaponPerkRows.nodesToRemove(WeaponPerkRows.project(state(0)),KIND.nodeIds()));
        assertTrue(WeaponPerkRows.Kind.values().length>=21);assertEquals(KIND,WeaponPerkRows.Kind.values()[20]);
        var all=Arrays.stream(WeaponPerkRows.Kind.values()).flatMap(x->x.nodeIds().stream()).toList();assertEquals(all.size(),Set.copyOf(all).size());
    }
    @Test void actual26CodecsAcceptLabelAndRejectWrongGraphType() throws Exception {
        net.minecraft.SharedConstants.tryDetectVersion();net.minecraft.server.Bootstrap.bootStrap();
        ItemModels.bootstrap();ItemTintSources.bootstrap();
        var base=Path.of("src/main/resources/assets/destiny");String name="perk_threat_detector_w178";
        var graph=JsonParser.parseString(Files.readString(base.resolve("items/gui/hud/"+name+".json"))).getAsJsonObject().getAsJsonObject("model");
        assertTrue(ItemModels.CODEC.parse(JsonOps.INSTANCE,graph).isSuccess());
        var bad=graph.deepCopy();bad.addProperty("type","destiny:missing");assertFalse(ItemModels.CODEC.parse(JsonOps.INSTANCE,bad).isSuccess());
        assertNotNull(CuboidModel.fromStream(new StringReader(Files.readString(base.resolve("models/gui/hud/"+name+".json")))));
        var image=ImageIO.read(base.resolve("textures/item/hud/"+name+".png").toFile());
        assertEquals(118,image.getWidth());assertEquals(24,image.getHeight());int visible=0;
        for(int y=0;y<24;y++)for(int x=0;x<118;x++) {int a=image.getRGB(x,y)>>>24;if(a>0)visible++;
            if(x==0||x==117||y==0||y==23)assertEquals(0,a);}
        assertTrue(visible>300);assertTrue(Files.readString(Path.of("art/hud/w178/threat-detector.svg")).contains("THREAT DETECTOR"));
    }
}
