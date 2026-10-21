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

    private record Running(Task task, int[] age) {
    }

    private static final List<Running> RUNNING = new ArrayList<>();

    private Tasks() {
    }

    public static void run(Task task) {
        RUNNING.add(new Running(task, new int[]{0}));
    }

    public static void tickAll() {
        if (RUNNING.isEmpty()) {
            return;
        }
        for (Running r : List.copyOf(RUNNING)) {
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
