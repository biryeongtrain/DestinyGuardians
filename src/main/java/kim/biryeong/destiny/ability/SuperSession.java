package kim.biryeong.destiny.ability;

/** 진행 중인 궁극기. 매 틱 호출되며 끝나면 {@link #tick()} 이 false 를 돌려준다. */
public interface SuperSession {
    /** @return 계속 진행하면 true */
    boolean tick();

    /** 궁극기 중 기본 공격(좌클릭). */
    void primary();

    /** 종료 정리. 자연 종료·사망·접속 종료 모두 호출된다. */
    void end();

    /** HUD 에 보일 남은 비율 0~1. */
    float remaining();
}
