package kim.biryeong.destiny.weapon;

import com.google.gson.*;
import kim.biryeong.destiny.loot.*;
import kim.biryeong.destiny.sound.*;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import net.minecraft.world.item.component.CustomModelData;
import org.junit.jupiter.api.Test;
import java.nio.file.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

class ExoticCatalogW350Test {
    private static JsonObject read(Path path) throws Exception {
        return JsonParser.parseString(Files.readString(path)).getAsJsonObject();
    }
    @Test void nineExactIndependentIdentitiesOccupyThreeEquipmentSlots() throws Exception {
        var evidence=read(Path.of("art/weapons/w350/catalog-source.json")).getAsJsonArray("weapons");
        assertEquals(9, WeaponExotics.expansionIds().size());
        var slots=new EnumMap<WeaponSlot,Integer>(WeaponSlot.class);var hashes=new HashSet<Long>();
        for(var value:evidence) {
            var row=value.getAsJsonObject();String id=row.get("id").getAsString();
            var entry=WeaponCatalog.find(id).orElseThrow();var meta=WeaponCharacteristics.of(entry);
            assertTrue(WeaponExotics.expanded(entry));assertTrue(meta.exotic());
            assertEquals(row.get("hash").getAsLong(),meta.bungieHash());assertTrue(hashes.add(meta.bungieHash()));
            assertNotEquals(WeaponCharacteristics.Damage.STASIS,meta.damage());
            assertNotEquals(WeaponCharacteristics.Damage.STRAND,meta.damage());
            assertEquals(row.get("nameKo").getAsString(),WeaponScreenText.weapon(id,entry.name()));
            assertTrue(WeaponStatCurves.supports(id));assertFalse(LegendaryWeapons.contains(id));
            slots.merge(meta.slot(),1,Integer::sum);
        }
        assertEquals(Map.of(WeaponSlot.KINETIC,3,WeaponSlot.ENERGY,3,WeaponSlot.POWER,3),slots);
        var pool=LootRoller.candidates(new LootTables.WeaponFilter(true,null,null,null,List.copyOf(WeaponExotics.expansionIds()),null,List.of("exotic")));
        assertEquals(9,pool.size());assertTrue(pool.stream().allMatch(c->c.skin()==null));
    }
    @Test void paidBurstAmmoAndFiniteHeavyMagazinesUseCorrectUnits() {
        var crimson=WeaponProfile.forEntry(WeaponCatalog.find("crimson").orElseThrow());
        var cycle=new WeaponCycle();var mag=new WeaponMagazine(crimson,24,0);
        assertTrue(cycle.fire(0,crimson,mag));assertEquals(23,mag.rounds());
        assertTrue(cycle.burst(2,mag));assertTrue(cycle.burst(4,mag));assertEquals(21,mag.rounds());
        assertFalse(crimson.sharedBurstAmmo());
        var jotunn=WeaponProfile.forEntry(WeaponCatalog.find("jotunn").orElseThrow());
        assertEquals(WeaponProfile.Mode.PROJECTILE,jotunn.mode());assertEquals(17,jotunn.chargeTicks());
        assertEquals(1,jotunn.burst());assertEquals(1,jotunn.pellets());assertFalse(jotunn.infiniteReserve());
        for(String id:List.of("gjallarhorn","whisper_of_the_worm","tractor_cannon")) {
            var p=WeaponProfile.forEntry(WeaponCatalog.find(id).orElseThrow());assertFalse(p.infiniteReserve());assertFalse(p.shellReload());
        }
        assertEquals(3,WeaponProfile.forEntry(WeaponCatalog.find("whisper_of_the_worm").orElseThrow()).magazine());
        assertEquals(1,WeaponProfile.forEntry(WeaponCatalog.find("gjallarhorn").orElseThrow()).magazine());
    }
    @Test void everyActiveNewPresentationRouteSelectsOwnedHandsAndHasASingleSoundVariant() throws Exception {
        Path assets=Path.of("src/main/resources/assets/destiny");
        var sounds=read(assets.resolve("sounds.json"));
        for(String id:WeaponExotics.expansionIds()) {
            var entry=WeaponCatalog.find(id).orElseThrow();
            for(String prefix:List.of("weapon/","weapon_reload_w350/","weapon_aim_w350/")) {
                String route="destiny:"+prefix+id;
                assertTrue(WeaponFirstPersonHands.sources().contains(net.minecraft.resources.Identifier.parse(route)),route);
                var graph=ProfileArmGraph.armsOnly(read(assets.resolve("items/weapon_hands_w201/"+prefix+id+".json")).getAsJsonObject("model"));
                for(float progress:new float[]{0,.25f,.5f,.75f,1}) {
                    var cmd=new CustomModelData(List.of(0f,progress,0f,progress),List.of(),List.of("hip"),List.of());
                    var selected=ProfileArmGraph.select(graph,cmd,false,false);
                    assertFalse(selected.isEmpty(),route+"@"+progress);
                    assertEquals(selected.size(),new HashSet<>(selected).size(),route);
                }
            }
            assertTrue(Files.exists(assets.resolve("items/gui/hud/ammo_weapon_w112_"+id+".json")));
            for(String action:List.of("fire","reload","ads","equip")) {
                String event="weapon."+id+"."+action;
                assertEquals(1,sounds.getAsJsonObject(event).getAsJsonArray("sounds").size(),event);
                assertEquals(event,DestinySounds.weaponKey(entry,action));
            }
            assertTrue(ReloadAudioProfile.find(entry,WeaponProfile.forEntry(entry).reloadTicks()).isPresent(),id);
        }
    }
}
