package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import java.lang.reflect.Modifier;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Real pure snapshots and explicitly STATIC source-authority checks. No fake Minecraft or
 * native authority success: runtime/entity/paid hooks are master's actualGT work.
 */
class WeaponHighImpactReservesW182Test {
    static WeaponCatalog.Entry entry(String id) { return WeaponCatalog.find(id).orElseThrow(); }
    static WeaponPerks.Roll roll(String id) {
        return HighImpactReservesProfile.rolls().stream().filter(r -> r.id().equals(id)).findFirst().orElseThrow();
    }
    static WeaponHighImpactReserves.Token snapshot(String id, int before) {
        var e = entry(id);
        return WeaponHighImpactReserves.snapshotSource(e, roll(id), before, WeaponProfile.forEntry(e).magazine());
    }
    static String source() throws Exception {
        return Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/WeaponHighImpactReserves.java"));
    }

    @Test void noneAndNullCaptureNeutral() {
        assertEquals(1f, WeaponHighImpactReserves.Token.NONE.multiplier());
        assertSame(WeaponHighImpactReserves.Token.NONE, WeaponHighImpactReserves.capture(null, 1, 11));
        assertSame(WeaponHighImpactReserves.Token.NONE, WeaponHighImpactReserves.capture(null, 0, 0));
    }
    @Test void everyExactRollFreezesProfileScalarForEveryValidPaidCartridge() {
        for (var r : HighImpactReservesProfile.rolls()) {
            var e = entry(r.id()); int cap = WeaponProfile.forEntry(e).magazine();
            for (int before=cap; before>=1; before--) {
                var token = WeaponHighImpactReserves.snapshotSource(e,r,before,cap);
                assertEquals(HighImpactReservesProfile.multiplier(e,before,cap),token.multiplier());
                assertTrue(Float.isFinite(token.multiplier()));
            }
        }
    }
    @Test void wrongEnhancedSocketPoolItemDefaultCannotMintToken() {
        var e = entry("seventh_seraph_officer_revolver"); var r = roll(e.id());
        for (var bad : Arrays.asList(null,
                new WeaponPerks.Roll(null,r.hash(),r.socket(),r.perkHash(),r.plugSetHash()),
                new WeaponPerks.Roll(r.id(),r.hash(),r.socket(),2002547233L,r.plugSetHash()),
                new WeaponPerks.Roll(r.id(),r.hash(),r.socket()+1,r.perkHash(),r.plugSetHash()),
                new WeaponPerks.Roll(r.id(),r.hash()+1,r.socket(),r.perkHash(),r.plugSetHash()),
                new WeaponPerks.Roll(r.id(),r.hash(),r.socket(),r.perkHash(),r.plugSetHash()+1), roll("bygones")))
            assertSame(WeaponHighImpactReserves.Token.NONE,WeaponHighImpactReserves.snapshotSource(e,bad,1,11));
        assertSame(WeaponHighImpactReserves.Token.NONE,WeaponHighImpactReserves.snapshotSource(null,r,1,11));
        assertSame(WeaponHighImpactReserves.Token.NONE,WeaponHighImpactReserves.snapshotSource(entry("ace_of_spades"),r,1,11));
    }
    @Test void inconsistentAmmoFailsClosedAtSnapshotBoundary() {
        var e=entry("dream_breaker"); var r=roll(e.id());
        for (int n : new int[]{Integer.MIN_VALUE,-1,0,7,Integer.MAX_VALUE})
            assertSame(WeaponHighImpactReserves.Token.NONE,WeaponHighImpactReserves.snapshotSource(e,r,n,6));
        for (int cap : new int[]{Integer.MIN_VALUE,-1,0,1,5,7,12,Integer.MAX_VALUE})
            assertSame(WeaponHighImpactReserves.Token.NONE,WeaponHighImpactReserves.snapshotSource(e,r,1,cap));
        assertSame(WeaponHighImpactReserves.Token.NONE, snapshot(e.id(),5));
    }
    @Test void immutablePaidTokenSurvivesLaterAmmoRefundStowAndSelectionEdits() {
        var paid=snapshot("seventh_seraph_officer_revolver",1);
        assertEquals(1.256f, paid.multiplier());
        // A new full/refunded or unselected source is independent; it cannot rewrite paid work.
        assertEquals(1f,snapshot("seventh_seraph_officer_revolver",11).multiplier());
        assertSame(WeaponHighImpactReserves.Token.NONE,
            WeaponHighImpactReserves.snapshotSource(entry("seventh_seraph_officer_revolver"),null,1,11));
        assertEquals(1.229f,snapshot("dream_breaker",1).multiplier());
        for (int i=0;i<100;i++) assertEquals(1.256f,paid.multiplier());
    }
    @Test void sharedFusionRetainsOneTokenWhileOrdinaryBurstRecapturesEachPaidBullet() {
        var shared=snapshot("dream_breaker",4);
        for (int bolt=0;bolt<7;bolt++) assertEquals(1.103f,shared.multiplier());
        // Models the value contract, not actual emission/payment/native damage.
        assertEquals(1f,snapshot("bygones",21).multiplier());
        assertEquals(1.121f,snapshot("bygones",20).multiplier());
        assertEquals(1.121f,snapshot("bygones",19).multiplier());
    }
    @Test void tokenContainsOnlyPrivateFinalImmutableValuesAndScalarReadHasNoAuthorityReads() throws Exception {
        var cls=WeaponHighImpactReserves.Token.class;
        assertTrue(Modifier.isFinal(cls.getModifiers()));
        for(var ctor:cls.getDeclaredConstructors())assertTrue(Modifier.isPrivate(ctor.getModifiers()));
        var field=cls.getDeclaredField("source");
        assertTrue(Modifier.isPrivate(field.getModifiers())&&Modifier.isFinal(field.getModifiers()));
        assertTrue(field.getType().isRecord());
        assertEquals(List.of(WeaponCatalog.Entry.class,WeaponPerks.Roll.class,int.class,int.class,float.class),
            Arrays.stream(field.getType().getRecordComponents()).map(c->c.getType()).toList());
        String body=source().split("public float multiplier\\(\\)")[1].split("\\}")[0];
        assertEquals("{ return source == null ? 1f : source.multiplier;",body.trim());
    }
    @Test void staticSourceAuthorityIncludesAllVorpalGuardsAndReadOnlySelectedBoundary() throws Exception {
        String text=source();
        String capture=text.split("public static Token capture")[1].split("static Token snapshotSource")[0];
        for(String required:List.of("player == null","!player.isAlive()","player.isRemoved()","player.isSpectator()",
            "player.hasDisconnected()","AbilityService.inSuper(player)","WeaponLoadout.canUse(player)",
            "getMainHandItem()","getItem(i) == stack","WeaponLoadout.equipped(player)","e.stack() == stack",
            "WeaponItems.entry(stack)","WeaponPerks.selected(stack, HighImpactReservesProfile.ID)","selection.isEmpty()",
            "snapshotSource(entry.get(), selection.get(), roundsBefore, baseCapacity)"))
            assertTrue(capture.contains(required),required);
        for(String forbidden:List.of("WeaponRuntime.","WeaponPerks.select(","setAttached(","putLong(","SESSIONS","currentRounds", "getTickCount("))
            assertFalse(text.contains(forbidden),forbidden);
        String profile=Files.readString(Path.of("src/main/java/kim/biryeong/destiny/weapon/HighImpactReservesProfile.java"));
        for(String forbidden:List.of("net.minecraft.","ServerPlayer","ItemStack","WeaponRuntime", "WeaponPerks.selected"))
            assertFalse(profile.contains(forbidden),forbidden);
    }
}
