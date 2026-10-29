package kim.biryeong.destiny.test;

import kim.biryeong.destiny.fx.HunterModelAssets;
import kim.biryeong.destiny.fx.ClassSuperModelAssets;
import kim.biryeong.destiny.DestinyGuardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import java.util.concurrent.atomic.AtomicBoolean;

/** Runs the engine's parsed bone iterators at its actual40Hz clock, independently of rendering FPS. */
public final class SourceClockW255GameTests {
    @GameTest(structure="destiny-test:floor",environment="destiny-test:w90_isolated",maxTicks=1200)
    public void parsedSourceActionsKeepTheirDeclaredDuration(GameTestHelper h) {
        h.startSequence().thenWaitUntil(()->h.assertTrue(BetterModel.limb(HunterModelAssets.MODEL_NAME).isPresent()
                &&BetterModel.limb(ClassSuperModelAssets.MODEL_NAME).isPresent(),Component.literal("Both owned rigs loaded")))
                .thenExecute(()->{
            int checked=0;int worstExtra=0;
            for(String model:new String[]{HunterModelAssets.MODEL_NAME,ClassSuperModelAssets.MODEL_NAME}) {
                var renderer=BetterModel.limb(model).orElseThrow();
                for(var clip:renderer.animations().values()) {
                    if(!(clip.name().startsWith("h15_class_")||clip.name().startsWith("h15_super_")
                            ||clip.name().startsWith("w229_")||clip.name().startsWith("w230_"))
                            ||clip.loop()!=AnimationIterator.Type.PLAY_ONCE)continue;
                    int expected=(int)Math.ceil(clip.length()*40)+2;
                    int maximum=0;
                    for(var bone:clip.animator().values()) {
                        var finished=new AtomicBoolean();
                        var state=new AnimationStateHandler<AnimationProgress>(null,(a,b)->{});
                        var modifier=AnimationModifier.builder().start(1).end(0).priority(20).type(AnimationIterator.Type.PLAY_ONCE).build();
                        state.addAnimation(clip.name(),bone.iterator(AnimationIterator.Type.PLAY_ONCE),modifier,()->finished.set(true));
                        int frames=0;
                        while(!finished.get()&&frames<2000){state.tick();frames++;}
                        maximum=Math.max(maximum,frames);
                    }
                    DestinyGuardians.LOGGER.info("W255 parsed clock {} expectedFrames={} actualMaxFrames={}",clip.name(),expected,maximum);
                    worstExtra=Math.max(worstExtra,maximum-expected);checked++;
                }
            }
            h.assertTrue(checked>=10,Component.literal("Source action coverage"));
            h.assertTrue(worstExtra<=3,Component.literal("Parsed duration drifts by "+worstExtra+" frames beyond source clock"));
            h.succeed();
        });
    }
}
