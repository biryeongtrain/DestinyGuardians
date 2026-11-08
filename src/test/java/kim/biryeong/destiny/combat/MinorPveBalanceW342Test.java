package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.strike.devils.DevilsPlan.Kind;
import kim.biryeong.destiny.campaign.fallen.FallenArchetypes;
import kim.biryeong.destiny.campaign.RisingServices.FallenKind;
import org.junit.jupiter.api.Test;
import static org.junit.jupiter.api.Assertions.*;

class MinorPveBalanceW342Test {
    @Test void everyUnbuffedAutoFrameKillsFragileMinorsWithTwoInRangeHeadshots() {
        int checked=0;
        for(var entry:WeaponCatalog.family("auto_rifle")) {
            var profile=WeaponProfile.forEntry(entry);
            var curve=WeaponBallistics.of(entry);
            float head=PveDamageBalance.scale(curve.damage(profile.damage(),curve.start(),true),AmmoGeneration.Kind.PRIMARY,false);
            for(var kind:new Kind[]{Kind.DREG,Kind.THRALL,Kind.ACOLYTE}) {
                assertTrue(head<kind.health(),entry.id()+" must not one-shot "+kind);
                assertTrue(head*2>=kind.health(),entry.id()+" must two-shot "+kind);
            }
            assertTrue(head<FallenArchetypes.of(FallenKind.DREG).health());
            assertTrue(head*2>=FallenArchetypes.of(FallenKind.DREG).health());
            checked++;
        }
        assertTrue(checked>=4);
    }
    @Test void directAbilityAndLightSuperMeetTheirTargetPools() {
        for(var kind:new Kind[]{Kind.DREG,Kind.THRALL,Kind.ACOLYTE})
            assertTrue(PveDamageBalance.scale(4,AmmoGeneration.Kind.ABILITY,false)>=kind.health());
        // The shield servitor is deliberately twice as sturdy (120): it holds Sepiks's barrier, so one light super hit
        // no longer removes it. Every other ordinary enemy still falls to a single light super hit.
        for(var kind:Kind.values()) if(!kind.boss() && kind != Kind.SERVITOR)
            assertTrue(PveDamageBalance.scale(11,AmmoGeneration.Kind.SUPER,false)>=kind.health()+kind.shield(),kind.name());
        assertEquals(120,Kind.SERVITOR.health());
    }
}
