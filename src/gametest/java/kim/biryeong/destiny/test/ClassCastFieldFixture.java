package kim.biryeong.destiny.test;

import kim.biryeong.destiny.ability.ClassAbilityCast;
import net.minecraft.server.level.ServerPlayer;
import java.util.Map;

/** Legacy W229 tests isolate installed field physics, not the new cast timeline.
 * Execute the accepted contact once in their setup. W255 tests exercise real ticking/contact/cancellation. */
final class ClassCastFieldFixture {
    private ClassCastFieldFixture() { }
    static void installAcceptedField(ServerPlayer player) {
        try {
            var active=ClassAbilityCast.class.getDeclaredField("ACTIVE");active.setAccessible(true);
            Object cast=((Map<?,?>)active.get(null)).get(player);
            if(cast==null)throw new AssertionError("Expected accepted class cast");
            var emission=cast.getClass().getDeclaredField("emission");emission.setAccessible(true);
            ((Runnable)emission.get(cast)).run();
        } catch(ReflectiveOperationException error) {throw new AssertionError(error);}
        finally {ClassAbilityCast.cleanup(player);}
    }
}
