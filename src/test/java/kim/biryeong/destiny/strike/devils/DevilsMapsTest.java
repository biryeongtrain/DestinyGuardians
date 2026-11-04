package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonParser;
import net.minecraft.core.BlockPos;
import net.minecraft.world.phys.Vec3;
import org.junit.jupiter.api.Test;

import java.io.*;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.*;

import static org.junit.jupiter.api.Assertions.*;

class DevilsMapsTest {
    @Test void sourceDerivedTemplatesHaveRealCollisionAndRequiredAnchors() {
        var required = Map.of(DevilsPlan.Zone.RY,List.of("IN","C1","C2","L","R","OUT"),
                DevilsPlan.Zone.RF,List.of("IN","G","A","B","C","D","EXIT"),
                DevilsPlan.Zone.BL,List.of("IN","W","B1","B2","H","L","R","D1","EXIT"),
                DevilsPlan.Zone.SP,List.of("IN","C","L","R","D1","D2","S1","S2","S3","CHEST","WARP.1","WARP.2","WARP.3","WARP.4"));
        for (var zone : DevilsPlan.Zone.values()) {
            var t = DevilsMaps.template(zone);
            assertTrue(t.blockCount()>40000, "Source geometry missing: "+zone);
            assertTrue(t.palette().size()>20, "Source material coverage: "+zone);
            for (String key : required.get(zone)) assertNotNull(DevilsMaps.anchor(zone,zone.name()+"."+key,BlockPos.ZERO));
            var seats = new HashSet<Vec3>();
            for (int i=0;i<3;i++) seats.add(DevilsMaps.anchor(zone,zone.name()+".IN."+i,BlockPos.ZERO).pos());
            assertEquals(3,seats.size());
            for (var m : DevilsMaps.markers(zone,BlockPos.ZERO)) {
                assertTrue(DevilsMaps.contains(zone,BlockPos.ZERO,m.pos()),m.id());
                if (!"ground".equals(m.tags().get("role"))) continue;
                int x=(int)Math.floor(m.pos().x),y=(int)Math.floor(m.pos().y),z=(int)Math.floor(m.pos().z);
                assertTrue(open(t.palette().get(t.paletteIndexAt(x,y,z))),m.id()+" feet");
                assertTrue(open(t.palette().get(t.paletteIndexAt(x,y+1,z))),m.id()+" head");
                assertFalse(open(t.palette().get(t.paletteIndexAt(x,y-1,z))),m.id()+" floor");
            }
        }
        var b1=DevilsMaps.anchor(DevilsPlan.Zone.BL,"BL.B1",BlockPos.ZERO).pos();
        var b2=DevilsMaps.anchor(DevilsPlan.Zone.BL,"BL.B2",BlockPos.ZERO).pos();
        assertTrue(b1.distanceTo(b2)>24,"Duplicated Brig source parents must not overlap");
    }
    @Test void originsAreAppliedExactlyOnceAndDoNotMutateCachedMarkers() {
        var offset=new BlockPos(1024,64,2048);
        for (var zone:DevilsPlan.Zone.values()) {
            var a=DevilsMaps.anchor(zone,zone.name()+".IN",BlockPos.ZERO);
            var b=DevilsMaps.anchor(zone,zone.name()+".IN",offset);
            assertEquals(a.pos().add(Vec3.atLowerCornerOf(offset)),b.pos());
            assertEquals(a,DevilsMaps.anchor(zone,zone.name()+".IN",BlockPos.ZERO));
            assertFalse(DevilsMaps.contains(zone,offset,new Vec3(Double.NaN,64,2048)));
        }
    }
    @Test void laneCandidatesHaveEnoughDistinctGroundedChoices() {
        var lanes=Map.of(DevilsPlan.Zone.RY,List.of("C1","R","L"),DevilsPlan.Zone.RF,List.of("A","B","C","D"),
                DevilsPlan.Zone.BL,List.of("R","L","H","D1","EXIT"),DevilsPlan.Zone.SP,List.of("L","R","D1","D2"));
        for(var entry:lanes.entrySet()) for(var lane:entry.getValue()) {
            var c=DevilsMaps.candidates(entry.getKey(),entry.getKey().name()+"."+lane,BlockPos.ZERO);
            assertTrue(c.size()>=8,entry.getKey()+"/"+lane);
            assertEquals(c.size(),c.stream().map(m->m.pos()).distinct().count());
        }
    }
    @Test void shieldServitorsHaveDistinctAuthoredFlyingAlternatives() {
        var all = new HashSet<Vec3>();
        for (int i = 1; i <= 3; i++) {
            String lane = "SP.S" + i;
            var candidates = DevilsMaps.candidates(DevilsPlan.Zone.SP, lane, BlockPos.ZERO);
            assertTrue(candidates.size() >= 3, "A single obstructed shield pad must have alternatives: " + lane);
            var anchor = DevilsMaps.anchor(DevilsPlan.Zone.SP, lane, BlockPos.ZERO);
            assertTrue(candidates.contains(anchor));
            for (var candidate : candidates) {
                assertEquals("flying", candidate.tags().get("role"), "Keep authored air height");
                assertTrue(all.add(candidate.pos()), "No duplicate pads across shield lanes");
                assertTrue(candidate.pos().distanceTo(anchor.pos()) < 8, "Keep each Servitor in its authored arena sector");
            }
        }
    }
    @Test void bundledRoutesAreContiguousAndHaveRealFloorAndHeadroom() throws Exception {
        try(var reader=new InputStreamReader(resource("routes.json"),StandardCharsets.UTF_8)) {
            var zones=JsonParser.parseReader(reader).getAsJsonObject().getAsJsonObject("zones");
            for(var zone:DevilsPlan.Zone.values()) {
                var t=DevilsMaps.template(zone);
                for(var value:zones.getAsJsonObject(DevilsMaps.resourceName(zone)).getAsJsonArray("routes")) {
                    var r=value.getAsJsonObject();int[] previous=null;
                    var cells=r.getAsJsonArray("cells");assertTrue(cells.size()>1,r.get("id").getAsString());
                    for(var v:cells) {
                        var a=v.getAsJsonArray();int x=a.get(0).getAsInt(),y=a.get(1).getAsInt(),z=a.get(2).getAsInt();
                        assertTrue(open(t.palette().get(t.paletteIndexAt(x,y,z))),"route feet");
                        assertTrue(open(t.palette().get(t.paletteIndexAt(x,y+1,z))),"route head");
                        assertFalse(open(t.palette().get(t.paletteIndexAt(x,y-1,z))),"route support");
                        if(previous!=null) {
                            assertEquals(1,Math.abs(previous[0]-x)+Math.abs(previous[2]-z));
                            assertTrue(y-previous[1]<=1 && previous[1]-y<=2,"route step");
                        }
                        previous=new int[]{x,y,z};
                    }
                }
            }
        }
    }
    @Test void packagedOutputHashesMatchManifest() throws Exception {
        try(var reader=new InputStreamReader(resource("manifest.json"),StandardCharsets.UTF_8)) {
            var manifest=JsonParser.parseReader(reader).getAsJsonObject();
            for(var e:manifest.getAsJsonObject("outputsSha256").entrySet()) try(var in=resource(e.getKey())) {
                assertEquals(e.getValue().getAsString(),HexFormat.of().formatHex(MessageDigest.getInstance("SHA-256").digest(in.readAllBytes())),e.getKey());
            }
        }
    }
    @Test void malformedMarkersRejectDuplicateNonfiniteAndOutOfBounds() throws Exception {
        String raw;
        try(var in=resource("markers.json")){raw=new String(in.readAllBytes(),StandardCharsets.UTF_8);}
        for(String mode:List.of("duplicate","nan","outside","missingArrival")) {
            var root=JsonParser.parseString(raw).getAsJsonObject();
            var rows=root.getAsJsonObject("zones").getAsJsonObject("rocketyard").getAsJsonArray("markers");
            var first=rows.get(0).getAsJsonObject();
            switch(mode) {
                case "duplicate" -> rows.add(first.deepCopy());
                case "nan" -> first.getAsJsonArray("pos").set(0,new com.google.gson.JsonPrimitive("NaN"));
                case "outside" -> first.getAsJsonArray("pos").set(0,new com.google.gson.JsonPrimitive(-1));
                case "missingArrival" -> first.addProperty("id","RY.wrong");
            }
            assertThrows(IOException.class,()->DevilsMaps.parse(new StringReader(root.toString())),mode);
        }
    }
    private static boolean open(String block) {return block.equals("minecraft:air")||block.startsWith("minecraft:light[")||block.startsWith("minecraft:snow[");}
    private static InputStream resource(String name) throws IOException {
        var in=DevilsMapsTest.class.getResourceAsStream(DevilsMaps.RESOURCE_DIR+name);
        if(in==null)throw new FileNotFoundException(name);return in;
    }
    @Test void arrivalViewRadiusIsWarmedWithoutReachingAnotherZone() {
        assertEquals(11, DevilsMaps.warmupMargin(10));
        assertEquals(12, DevilsMaps.warmupMargin(32));
        int margin = DevilsMaps.warmupMargin(10), total = 0;
        for (var zone : DevilsPlan.Zone.values()) {
            var min = DevilsWorldBuild.origin(zone); var size = DevilsMaps.dimensions(zone);
            int w = ((min.getX()+size.getX()-1)>>4) - (min.getX()>>4) + 1 + 2*margin;
            int d = ((min.getZ()+size.getZ()-1)>>4) - (min.getZ()>>4) + 1 + 2*margin;
            total += w*d;
            // Rings of neighbouring zones (origins 512 blocks apart) never overlap.
            int nextMin = (min.getX() + 512) >> 4;
            assertTrue(((min.getX()+size.getX()-1)>>4) + margin < nextMin - margin, "Warm ring stays local: " + zone);
            System.out.println("[warmup] " + zone + " size=" + size + " columns=" + (w*d));
        }
        assertTrue(total <= 4 * 1600, "Bounded warmup columns per instance: " + total);
    }
}
