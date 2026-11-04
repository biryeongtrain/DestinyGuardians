package kim.biryeong.destiny.campaign.fallen;

import java.util.EnumSet;
import java.util.Optional;
import java.util.Set;

/**
 * Ghost callouts that guide the Walker fight (W300 r4). All lines are original authored subtitle-only text
 * ({@code authored=true, voice=false} in subtitles_ko.json); no extracted voice says these things.
 * Pure policy: a cue is said at most once per Walker cycle, and non-priority cues respect a cooldown so the
 * presentation queue never piles up. EXPOSED and DOWN are priority (the player must act on them now).
 */
final class FallenCallouts {
    enum Cue {
        LEGS("rg.walker.legs", false),
        LEG_BROKEN("rg.walker.leg_broken", false),
        EXPOSED("rg.walker.exposed", true),
        RECOVER("rg.walker.recover", false),
        DOWN("rg.walker.down", true);

        final String lineId;
        final boolean priority;
        Cue(String lineId, boolean priority) { this.lineId = lineId; this.priority = priority; }
    }

    static final int COOLDOWN_TICKS = 80;

    private final Set<Cue> said = EnumSet.noneOf(Cue.class);
    private int cycle = Integer.MIN_VALUE;
    private long last = Long.MIN_VALUE / 2;

    /** @return the cue to say now, or empty if it was already said this cycle or is inside the cooldown. */
    Optional<Cue> request(Cue cue, int cycle, long now) {
        if (cycle != this.cycle) { said.clear(); this.cycle = cycle; }
        if (said.contains(cue)) return Optional.empty();
        if (!cue.priority && now - last < COOLDOWN_TICKS) return Optional.empty();
        said.add(cue);
        last = now;
        return Optional.of(cue);
    }

    /** Phase entered -> cue (STAGGER is covered by LEG_BROKEN; ARMORED only opens the fight). */
    static Optional<Cue> forPhase(WalkerBoss.Phase phase) {
        return switch (phase) {
            case LEG_BREAK -> Optional.of(Cue.LEG_BROKEN);
            case EXPOSED -> Optional.of(Cue.EXPOSED);
            case RECOVER -> Optional.of(Cue.RECOVER);
            case DEAD -> Optional.of(Cue.DOWN);
            default -> Optional.empty();
        };
    }
}
