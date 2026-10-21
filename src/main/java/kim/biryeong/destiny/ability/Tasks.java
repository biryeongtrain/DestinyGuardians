package kim.biryeong.destiny.ability;

import java.util.ArrayList;
import java.util.List;

/** 서버 틱마다 도는 짧은 작업 (지속형 장판·연출). */
public final class Tasks {
    /** @return 계속하면 true */
    @FunctionalInterface
    public interface Task {
        boolean tick(int age);
    }

    private record Running(Task task, int[] age, net.minecraft.server.level.ServerPlayer owner, net.minecraft.server.level.ServerLevel level) {
    }

    private static final List<Running> RUNNING = new ArrayList<>();

    private Tasks() {
    }

    public static void run(Task task) {
        RUNNING.add(new Running(task, new int[]{0}, null, null));
    }

    public static void run(net.minecraft.server.level.ServerPlayer owner, net.minecraft.server.level.ServerLevel level, Task task) {
        RUNNING.add(new Running(task, new int[]{0}, owner, level));
    }

    public static void cancelOwned(net.minecraft.server.level.ServerPlayer owner) {
        RUNNING.removeIf(r -> r.owner == owner);
    }

    public static int count(net.minecraft.server.level.ServerPlayer owner) {
        return (int) RUNNING.stream().filter(r -> r.owner == owner).count();
    }

    public static void tickAll() {
        if (RUNNING.isEmpty()) {
            return;
        }
        for (Running r : List.copyOf(RUNNING)) {
            if (r.owner != null && (!r.owner.isAlive() || r.owner.isRemoved() || r.owner.level() != r.level)) {
                RUNNING.remove(r);
                continue;
            }
            boolean keep;
            try {
                keep = r.task.tick(r.age[0]++);
            } catch (RuntimeException e) {
                kim.biryeong.destiny.DestinyGuardians.LOGGER.error("Task failed", e);
                keep = false;
            }
            if (!keep) {
                RUNNING.remove(r);
            }
        }
    }

    public static void clearAll() {
        RUNNING.clear();
    }

    public static int count() {
        return RUNNING.size();
    }
}
