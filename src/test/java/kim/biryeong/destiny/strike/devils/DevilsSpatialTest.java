package kim.biryeong.destiny.strike.devils;
import net.minecraft.world.phys.*;
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;
class DevilsSpatialTest {
 @Test void twelveBlockAdmissionUsesExactDistance() {
  assertTrue(DevilsSpatial.farEnough(Vec3.ZERO,List.of(new Vec3(12,0,0)),12));
  assertFalse(DevilsSpatial.farEnough(Vec3.ZERO,List.of(new Vec3(11.99,0,0)),12));
 }
 @Test void wholeBossFootprintMustFit() {
  AABB map=new AABB(0,0,0,100,80,100);
  assertFalse(DevilsSpatial.within(new AABB(98,10,20,102,15,24),map));
  assertTrue(DevilsSpatial.within(new AABB(96,10,20,100,15,24),map));
  assertFalse(DevilsSpatial.within(new AABB(0,0,0,Double.NaN,1,1),map));
 }
 @Test void HiddenIsPreferenceAndBlockedHasNoFallback() {
  var visible=new DevilsSpatial.Point("a",Vec3.ZERO,0,true);
  var hidden=new DevilsSpatial.Point("b",new Vec3(20,0,0),0,false);
  assertEquals(hidden,DevilsSpatial.preferHidden(List.of(visible,hidden)).orElseThrow());
  assertEquals(visible,DevilsSpatial.preferHidden(List.of(visible)).orElseThrow());
  assertTrue(DevilsSpatial.preferHidden(List.of()).isEmpty());
 }
 @Test void BossGroundAndAirModesAreExplicit() {
  assertFalse(DevilsSpatial.flying(DevilsPlan.Kind.WALKER));
  assertFalse(DevilsSpatial.flying(DevilsPlan.Kind.BRIG));
  assertTrue(DevilsSpatial.flying(DevilsPlan.Kind.SEPIKS));
 }
}
