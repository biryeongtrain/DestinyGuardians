package kim.biryeong.destiny.strike.devils;

import kim.biryeong.destiny.DestinyGuardians;
import kr.toxicity.model.api.BetterModel;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.data.renderer.ModelRenderer;
import kr.toxicity.model.api.mod.platform.ModEntity;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.TrackerModifier;
import kr.toxicity.model.api.tracker.TrackerUpdateAction;
import net.minecraft.core.BlockPos;
import net.minecraft.world.level.LightLayer;

/** Strict model attachment: missing assets fail admission/spawn rather than produce invisible enemies. */
final class DevilsActorModel implements AutoCloseable {
    private final DevilsMob mob;
    private final EntityTracker tracker;
    private final ModelRenderer renderer;
    private String base, held;
    private boolean cloaked;
    private int lastBase = -20, block = -1, sky = -1;
    private DevilsActorModel(DevilsMob mob, ModelRenderer renderer, EntityTracker tracker) {
        this.mob=mob;this.renderer=renderer;this.tracker=tracker;
    }
    static DevilsActorModel attach(DevilsMob mob) {
        try {
            var renderer=BetterModel.model(DevilsActors.model(mob.kind())).orElse(null);
            if(renderer==null)return null;
            var tracker=renderer.getOrCreate(ModEntity.of(mob),TrackerModifier.builder().sightTrace(false).damageAnimation(false).damageTint(true).build());
            if(tracker==null)return null;
            var model=new DevilsActorModel(mob,renderer,tracker);
            model.base("idle");
            // Sepiks awakens only after the guard encounter, under the presentation completion gate.
            if(mob.kind()!=DevilsPlan.Kind.SEPIKS)model.play("spawn");
            model.tick();return model;
        } catch(RuntimeException error) {
            DestinyGuardians.LOGGER.error("Devils model attachment failed: {}",DevilsActors.model(mob.kind()),error);return null;
        }
    }
    void base(String clip) {
        if(tracker.isClosed()||held!=null||clip.equals(base)||mob.tickCount-lastBase<5||renderer.animation(clip).isEmpty())return;
        if(base!=null)tracker.stopAnimation(base);
        if(tracker.animate(clip,new AnimationModifier(4,4,AnimationIterator.Type.LOOP))) {base=clip;lastBase=mob.tickCount;}
    }
    void play(String clip) {
        // The retained Guardian Rises Walker names its firing clip "fire".
        if(mob.kind()==DevilsPlan.Kind.WALKER && clip.equals("shoot"))clip="fire";
        if(tracker.isClosed()||renderer.animation(clip).isEmpty())return;
        if(clip.equals("recover")||clip.equals("death"))release();
        if(clip.equals("weakpoint_open")) {
            release(); held=clip; tracker.animate(clip,new AnimationModifier(2,0,AnimationIterator.Type.HOLD_ON_LAST));return;
        }
        if(clip.equals("death"))cloak(false);
        if(clip.equals("death")&&base!=null) {tracker.stopAnimation(base);base=null;}
        tracker.animate(clip,new AnimationModifier(2,3,clip.equals("death")?AnimationIterator.Type.HOLD_ON_LAST:AnimationIterator.Type.PLAY_ONCE));
    }
    private void release() {if(held!=null){tracker.stopAnimation(held);held=null;}}
    int deathTicks() {return Math.clamp(Math.round(renderer.animation("death").map(a->a.length()).orElse(1f)*20)+4,20,80);}
    void tick() {
        if(tracker.isClosed()||mob.tickCount%10!=0&&block>=0)return;
        var at=BlockPos.containing(mob.position().add(0,Math.min(2.5,mob.getBbHeight()*.7),0));
        int b=Math.max(5,mob.level().getBrightness(LightLayer.BLOCK,at)),s=mob.level().getBrightness(LightLayer.SKY,at);
        if(b==block&&s==sky)return;block=b;sky=s;
        var body=TrackerUpdateAction.brightness(b,s);var glow=TrackerUpdateAction.brightness(15,15);
        tracker.update(TrackerUpdateAction.perBone(bone->bone.name().name().endsWith("_glow")?glow:body));
    }
    void armorOpen() {
        // Model author must isolate the front plate under this explicit bone. Never hide the entire chest.
        tracker.update(TrackerUpdateAction.togglePart(false),bone->bone.name().name().equals("armor_plate"));
    }
    void cloak(boolean value) {
        if(value==cloaked||tracker.isClosed())return;cloaked=value;
        tracker.update(TrackerUpdateAction.togglePart(!value),bone->!bone.name().name().endsWith("_glow"));
    }
    void hit(){if(!tracker.isClosed()) {tracker.damageTint();play("damage");}}
    @Override public void close(){if(!tracker.isClosed())tracker.close();}
}
