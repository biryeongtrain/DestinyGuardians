package kim.biryeong.destiny.loot;

import java.util.List;
import java.util.function.Predicate;

/** A chest owns each rolled reward until a drop or mailbox accepts it. Server-thread only. */
final class ChestRewards {
    private final List<LootRoller.Reward> rewards;
    private final boolean[] transferred;

    ChestRewards(List<LootRoller.Reward> rewards) {
        this.rewards = List.copyOf(rewards);
        this.transferred = new boolean[rewards.size()];
    }

    List<LootRoller.Reward> all() { return rewards; }

    boolean transfer(int index, Predicate<LootRoller.Reward> receiver) {
        if (transferred[index]) return true;
        if (!receiver.test(rewards.get(index))) return false;
        transferred[index] = true;
        return true;
    }

    boolean drain(Predicate<LootRoller.Reward> receiver) {
        boolean complete = true;
        for (int i = 0; i < rewards.size(); i++) if (!transfer(i, receiver)) complete = false;
        return complete;
    }
}
