package kim.biryeong.destiny.loot;

import org.junit.jupiter.api.Test;
import java.util.ArrayList;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ChestRewardsTest {
    @Test void leavingBeforeOrDuringBurstTransfersEachRolledRewardExactlyOnce() {
        var rolled = List.of(LootRoller.Reward.engram("legendary"), LootRoller.Reward.engram("exotic"));
        for (int landed = 0; landed <= rolled.size(); landed++) {
            var rewards = new ChestRewards(rolled);
            var drops = new ArrayList<LootRoller.Reward>();
            var mail = new ArrayList<LootRoller.Reward>();
            for (int i = 0; i < landed; i++) assertTrue(rewards.transfer(i, drops::add));
            assertTrue(rewards.drain(mail::add));
            assertTrue(rewards.drain(mail::add));
            for (int i = 0; i < landed; i++) assertTrue(rewards.transfer(i, drops::add));
            assertEquals(rolled.subList(0, landed), drops);
            assertEquals(rolled.subList(landed, rolled.size()), mail);
        }
    }

    @Test void rejectedMailRetainsOnlyTheUnacceptedRewardForRetry() {
        var rolled = List.of(LootRoller.Reward.engram("legendary"), LootRoller.Reward.engram("exotic"));
        var rewards = new ChestRewards(rolled);
        var mail = new ArrayList<LootRoller.Reward>();
        assertFalse(rewards.drain(r -> r.engram().equals("legendary") && mail.add(r)));
        assertTrue(rewards.drain(mail::add));
        assertEquals(rolled, mail);
    }

    @Test void equalTierRollsAreSeparateEntitlementsAndChestsAreIndependent() {
        var r = LootRoller.Reward.engram("legendary");
        var a = new ChestRewards(List.of(r, r));
        var b = new ChestRewards(List.of(r));
        var mail = new ArrayList<LootRoller.Reward>();
        assertTrue(a.drain(mail::add));
        assertTrue(b.drain(mail::add));
        assertEquals(3, mail.size());
    }
}
