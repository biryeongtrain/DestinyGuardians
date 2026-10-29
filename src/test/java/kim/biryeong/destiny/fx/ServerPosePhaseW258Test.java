package kim.biryeong.destiny.fx;

import kr.toxicity.model.api.animation.*;
import org.junit.jupiter.api.Test;
import java.util.List;
import static org.junit.jupiter.api.Assertions.*;

class ServerPosePhaseW258Test {
    @Test void nativeIntegerDelayStartsAtTheReachedKeyWithoutRoundingBias() {
        var first=AnimationProgress.empty(.05f);
        var next=AnimationProgress.empty(.05f);
        var state=new AnimationStateHandler<AnimationProgress>(null,(a,b)->{});
        state.addAnimation("phase",AnimationIterator.Type.PLAY_ONCE.create(TimedStorage.listOf(List.of(first,next))),
                AnimationModifier.builder().start(0).end(0).type(AnimationIterator.Type.PLAY_ONCE).build(),()->{});
        boolean sawStart=false,sawHalf=false;
        for(int i=0;i<8;i++) {
            state.tick();
            if(Math.round(state.frame())!=2)continue;
            if(state.getDelay()==2) {
                assertTrue(1f-state.progress()>0,"BM native float denominator includes its rounding bias");
                assertEquals(0f,ServerPoseSampling.reachedFraction(state.frame(),state.getDelay()));
                sawStart=true;
            } else if(state.getDelay()==1) {
                assertEquals(.5f,ServerPoseSampling.reachedFraction(state.frame(),state.getDelay()));
                sawHalf=true;
            }
        }
        assertTrue(sawStart);assertTrue(sawHalf);
    }
}
