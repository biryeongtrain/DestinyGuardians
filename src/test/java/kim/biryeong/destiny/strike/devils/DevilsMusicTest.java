package kim.biryeong.destiny.strike.devils;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.io.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class DevilsMusicTest {
    private JsonObject data() throws Exception {
        try(var reader=new InputStreamReader(Objects.requireNonNull(getClass().getResourceAsStream("/destiny/devils_lair/music.json")))) {
            return JsonParser.parseReader(reader).getAsJsonObject();
        }
    }
    private JsonObject tree(int container) throws Exception {
        for(var row:data().getAsJsonArray("playlists"))if(row.getAsJsonObject().get("container_id").getAsInt()==container)
            return row.getAsJsonObject().getAsJsonObject("tree");
        throw new AssertionError("No container");
    }
    @Test void sepiksKeepsIntroEightLoopsAndOutro() throws Exception {
        var p=new DevilsMusicPlaylist(tree(501705178),1);
        assertEquals(949958315,p.next());
        for(int i=0;i<8;i++)assertEquals(21796713,p.next());
        assertEquals(756934739,p.next());assertNull(p.next());assertNull(p.next());
    }
    @Test void refineryKeepsAuthoredPairsBeforeRandomLoop() throws Exception {
        var p=new DevilsMusicPlaylist(tree(979679608),1);
        for(int id:new int[]{933801940,933801940,402177965,402177965,849805584,849805584})assertEquals(id,p.next());
        var first=new ArrayList<Integer>();var second=new ArrayList<Integer>();
        for(int i=0;i<5;i++)first.add(p.next());
        for(int i=0;i<5;i++)second.add(p.next());
        assertEquals(5,new HashSet<>(first).size());assertEquals(new HashSet<>(first),new HashSet<>(second));
        assertNotEquals(first.getLast(),second.getFirst());
        assertNotEquals(first,second,"Shuffle must reshuffle each bag instead of repeating the first permutation forever");
        for(int i=0;i<100;i++)assertNotNull(p.next());
    }
    @Test void walkerBattleAndAftermathAreDifferentStates() {
        assertEquals(5,DevilsMusic.section(DevilsDirector.Phase.BL_BATTLE));
        assertEquals(6,DevilsMusic.section(DevilsDirector.Phase.BL_CLEAR));
        assertEquals(6,DevilsMusic.section(DevilsDirector.Phase.SP_GUARD));
        assertEquals(7,DevilsMusic.section(DevilsDirector.Phase.SP_SHIELD1));
        assertEquals(9,DevilsMusic.section(DevilsDirector.Phase.COMPLETE));
        assertEquals(-1,DevilsMusic.section(DevilsDirector.Phase.BRIEFING));
    }
    @Test void everySelectedSegmentHasPackSoundAndFiniteDuration() throws Exception {
        var d=data();
        for(var row:d.getAsJsonArray("playlists")) {
            var p=new DevilsMusicPlaylist(row.getAsJsonObject().getAsJsonObject("tree"),42);
            for(int i=0;i<100;i++) {
                Integer next=p.next();if(next==null)break;
                var clip=d.getAsJsonObject("segments").getAsJsonObject(next.toString());
                assertNotNull(clip);assertTrue(clip.get("seconds").getAsDouble()>0);
                assertNotNull(getClass().getResource("/assets/destiny_music/sounds/devils/"+next+".ogg"));
            }
        }
    }
}
