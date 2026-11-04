package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class QuickdrawW185Test {
    private static final Path RESOURCE=Path.of("src/main/resources/destiny/weapons/w185-quickdraw.json");
    static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    @Test void exactSixteenCanonicalOfficialRollsAndNoFamilyOrExoticGrant() throws Exception {
        var root=JsonParser.parseString(Files.readString(RESOURCE)).getAsJsonObject();
        var expected=new Gson().fromJson(root.get("weapons"),WeaponPerks.Roll[].class);
        assertEquals(706527188L,QuickdrawProfile.HASH);assertEquals("quickdraw",QuickdrawProfile.ID);
        assertEquals(16,QuickdrawProfile.rolls().size());assertEquals(Set.of(expected),Set.copyOf(QuickdrawProfile.rolls()));
        for(var e:WeaponCatalog.all())assertEquals(Arrays.stream(expected).anyMatch(r->r.id().equals(e.id())),QuickdrawProfile.supports(e),e.id());
        assertFalse(QuickdrawProfile.supports(null));
        assertThrows(UnsupportedOperationException.class,()->QuickdrawProfile.rolls().clear());
    }
    @Test void allRawReadyStowResultsIncludingEachLegalTdTier() {
        String[] rows={"blast_furnace 1 5 4","dead_man_walking_xx7463 1 4 5","biting_winds 1 9 8","whispering_slab 1 9 8",
            "beloved 1 5 5","apostate 1 5 5","parcel_of_stardust_fell_to_earth 1 5 5","hollow_words 1 7 4","dream_breaker 1 7 4",
            "edge_transit 1 6 6","bad_omens 1 6 5","bellowing_giant 1 6 5","code_duello 1 6 5","pyroclastic_flow 1 6 5","fixed_odds 1 5 6","hammerhead 1 5 6",
            "parcel_of_stardust_fell_to_earth .9 4 5","parcel_of_stardust_fell_to_earth .81 4 4","dream_breaker .9 7 3","dream_breaker .81 6 3",
            "edge_transit .9 5 5","edge_transit .81 5 5","bellowing_giant .9 5 4","bellowing_giant .81 5 4"};
        for(String row:rows) {
            var a=row.split(" ");var e=entry(a[0]);double scalar=Double.parseDouble(a[1]);
            assertEquals(Integer.parseInt(a[2]),QuickdrawProfile.handlingTicks(e,scalar,true),row);
            assertEquals(Integer.parseInt(a[3]),QuickdrawProfile.handlingTicks(e,scalar,false),row);
        }
        // Applying .81 after the already-ceiled QD value gives 5, while raw combination is 4.
        assertEquals(5,(int)Math.ceil(QuickdrawProfile.handlingTicks(entry("parcel_of_stardust_fell_to_earth"),1,true)*.81));
        assertEquals(4,QuickdrawProfile.handlingTicks(entry("parcel_of_stardust_fell_to_earth"),.81,true));
    }
    @Test void exactCompanionsRejectSameSocketWrongHashPoolAndWeapon() throws Exception {
        var doc=JsonParser.parseString(Files.readString(RESOURCE)).getAsJsonObject();int td=0;
        for(var item:doc.getAsJsonArray("coSelections")) {
            var pair=item.getAsJsonObject();String id=pair.get("id").getAsString(),perk=pair.get("perk").getAsString();
            var roll=new Gson().fromJson(pair.get("roll"),WeaponPerks.Roll.class);var e=entry(id);
            assertTrue(QuickdrawProfile.compatible(e,perk,roll));
            var source=QuickdrawProfile.rolls().stream().filter(r->r.id().equals(id)).findFirst().orElseThrow();
            assertFalse(QuickdrawProfile.compatible(e,perk,new WeaponPerks.Roll(id,roll.hash(),source.socket(),roll.perkHash(),roll.plugSetHash())));
            assertFalse(QuickdrawProfile.compatible(e,perk,new WeaponPerks.Roll(id,roll.hash(),roll.socket(),roll.perkHash(),roll.plugSetHash()+1)));
            assertFalse(QuickdrawProfile.compatible(e,perk,new WeaponPerks.Roll(id,roll.hash()+1,roll.socket(),roll.perkHash(),roll.plugSetHash())));
            assertFalse(QuickdrawProfile.compatible(entry(id.equals("beloved")?"blast_furnace":"beloved"),perk,roll));
            if(perk.equals("threat_detector"))td++;
        }
        assertEquals(4,td);
    }
    @Test void unsupportedScalarAndUnprovedTdCannotBeInvented() {
        for(double scalar:new double[]{Double.NaN,Double.POSITIVE_INFINITY,0,-1,1.01,.95,.8})
            assertThrows(IllegalArgumentException.class,()->QuickdrawProfile.handlingTicks(entry("dream_breaker"),scalar,true));
        assertThrows(IllegalArgumentException.class,()->QuickdrawProfile.handlingTicks(entry("beloved"),.9,true));
        assertThrows(IllegalArgumentException.class,()->QuickdrawProfile.handlingTicks(null,1,true));
        assertThrows(IllegalArgumentException.class,()->QuickdrawProfile.handlingTicks(entry("ace_of_spades"),1,true));
    }
    @Test void semanticMutationFailsClosedForMechanicsRollCurvesAndCompanions() throws Exception {
        String text=Files.readString(RESOURCE);QuickdrawProfile.validateResource(text);
        for(String field:List.of("perk","weapons","curves","coSelections")) {
            var doc=JsonParser.parseString(text).getAsJsonObject();doc.remove(field);
            assertThrows(IllegalStateException.class,()->QuickdrawProfile.validateResource(doc.toString()));
        }
        assertThrows(IllegalStateException.class,()->QuickdrawProfile.validateResource("{}"));
        assertThrows(IllegalStateException.class,()->QuickdrawProfile.validateResource("["));
    }
}
