package kim.biryeong.destiny.ability;

/** 진행 중인 궁극기. 매 틱 호출되며 끝나면 {@link #tick()} 이 false 를 돌려준다. */
public interface SuperSession {
    /** @return 계속 진행하면 true */
    boolean tick();

    /** 궁극기 중 기본 공격(좌클릭). */
    void primary();

    /** Only explicit melee-super opt-ins own RMB; every other session preserves ordinary item use. */
    default boolean supportsSecondary() { return false; }
    default void secondary() { }

    /** Explicit opt-in: super-owned class actions never invoke the equipped ordinary ability or its perks. */
    default AbilityService.Result classAbility() { return AbilityService.Result.BUSY; }

    /** Session-local HUD charge, independent of the equipped ordinary class ability's saved cooldown. */
    default java.util.Optional<ClassAbilityCooldown> classAbilityCooldown() { return java.util.Optional.empty(); }
    record ClassAbilityCooldown(int remainingTicks,int totalTicks) {
        public ClassAbilityCooldown {
            if(totalTicks<1)throw new IllegalArgumentException("Cooldown capacity must be positive");
            remainingTicks=Math.clamp(remainingTicks,0,totalTicks);
        }
    }

    /** 종료 정리. 자연 종료·사망·접속 종료 모두 호출된다. */
    void end();

    /** HUD 에 보일 남은 비율 0~1. */
    float remaining();

    /** Cast/roaming protection can end before a projectile or recovery session finishes. */
    default boolean damageResistanceActive() { return true; }

    /** Finite super-weapon shots; empty for supers without a magazine. Not a duration estimate. */
    default java.util.OptionalInt ammunition() { return java.util.OptionalInt.empty(); }
    default int ammunitionCapacity() { return 1; }
}
