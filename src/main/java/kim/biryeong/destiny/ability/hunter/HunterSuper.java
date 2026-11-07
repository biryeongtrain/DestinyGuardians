package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.AbilityDamage;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.AbilityParticles;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.fx.PostEffects;
import kim.biryeong.destiny.fx.PlayerAnimations;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.fx.SuperVfx;
import kim.biryeong.destiny.fx.SuperAttackTiming;
import kim.biryeong.destiny.fx.GoldenGunHandPose;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.ItemDisplayHud;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.projectile.ProjectileUtil;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.EntityHitResult;
import net.minecraft.world.phys.HitResult;
import net.minecraft.world.phys.Vec3;

/**
 * 헌터 궁극기 3종.
 * <ul>
 *   <li>Arc 아크 지팡이: 지속시간 동안 좌클릭으로 전방 부채꼴 타격, 증폭 상태</li>
 *   <li>Solar 황금 총: 좌클릭으로 강력한 즉발 사격 3발</li>
 *   <li>Void 그림자 사격: 공허 화살 한 발 → 착탄 지점 닻이 주변 적을 약화·억제</li>
 * </ul>
 */
public final class HunterSuper extends Ability {
    public static final String HAND_HUD_ID = "destiny:super_hand";

    public HunterSuper(Identifier id, String name, Element element) {
        super(id, GuardianClass.HUNTER, AbilitySlot.SUPER, element, 0, name);
    }

    @Override
    public boolean activate(ServerPlayer player) {
        if(element()==Element.ARC&&!kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.available(
                kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.ARC_RESOURCE))return false;
        if (!kim.biryeong.destiny.camera.SuperCamera.start(player, element())) return false;
        Session session = switch (element()) {
            case ARC -> new ArcStaff(player);
            case SOLAR -> new GoldenGun(player);
            default -> new Shadowshot(player);
        };
        AbilityService.startSuper(player, session);
        PostEffects.enter(player, element());
        PostEffects.pulse(player, element(), false);
        boolean animated = PlayerAnimations.loop(player, "super_" + element().getSerializedName());
        if (!animated && kim.biryeong.destiny.camera.SuperCamera.active(player)) {
            // A combat camera without the requested limb is not a successful activation.
            AbilityService.endSuper(player);
            kim.biryeong.destiny.camera.SuperCamera.stop(player);
            return false;
        }
        PlayerAnimations.superItem(player, kim.biryeong.destiny.fx.SuperVisuals.item(element()), element() == Element.VOID);
        if (session instanceof ArcStaff arc) {
            kim.biryeong.destiny.camera.SuperCamera.blockMovement(player,arc.deployTicks);
            PlayerAnimations.play(player,arc.startClip);
        } else if (element() != Element.VOID) PlayerAnimations.play(player, "super_" + element().getSerializedName() + "_start");
        SuperVfx.materialize(player, element());
        // Keep the core silhouette readable; the old eye-height flame cloud obscured first person.
        AbilityParticles.send(player, player.level(), Fx.dust(element().color(), 0.65f), player.getX(), player.getY() + 0.25,
                player.getZ(), 16, 0.55, 0.12, 0.55, 0.01);
        kim.biryeong.destiny.sound.SuperCastSounds.play(player, player.position(),
                "hunter." + element().getSerializedName() + ".super.start", SoundEvents.BEACON_ACTIVATE, 1f, 1.4f);
        session.onActivated();
        return true;
    }

    private abstract class Session implements SuperSession {
        protected final ServerPlayer player;
        protected final int duration;
        protected int age;
        private ItemStack handStack;

        Session(ServerPlayer player, int duration) {
            this.player = player;
            this.duration = duration;
        }

        /** Runs only after the camera, limb, equipment and start cue have succeeded. */
        protected void onActivated() { }

        @Override
        public boolean tick() {
            syncHand();
            return ++age < duration && player.isAlive();
        }

        @Override
        public float remaining() {
            return Math.max(0f, 1f - (float) age / duration);
        }

        @Override
        public void end() {
            if (player.isAlive() && element() != Element.VOID) DestinySounds.hunter(player.level(), player.position(), element(), "super.end", .65f);
            PostEffects.exit(player, element());
            SuperVfx.dematerialize(player, element());
            PlayerAnimations.finishSuper(player);
            DisplayHud.removeHud(player, HAND_HUD_ID);
        }

        protected void handItem(ItemStack stack) {
            handStack = stack;
            syncHand();
        }

        protected void animateHand(ItemDisplayHud hud) { }

        protected void syncHand() {
            if (PlayerAnimations.ownerSeesLimb(player)) {
                DisplayHud.removeHud(player, HAND_HUD_ID);
                return;
            }
            if (handStack == null) return;
            if (DisplayHud.getHud(player, HAND_HUD_ID) instanceof ItemDisplayHud existing) {
                animateHand(existing);
                return;
            }
            DisplayHud.removeHud(player, HAND_HUD_ID);
            ItemDisplayHud hud = new ItemDisplayHud();
            hud.setItem(handStack);
            hud.setItemTransform(ItemDisplayContext.GUI);
            hud.setScale(220, 220, 1);
            hud.setViewRange(1000);
            hud.setAboveHand(true);
            hud.setLocation(1420, 860, 0);
            animateHand(hud);
            hud.spawn(player, HAND_HUD_ID);
        }
    }

    /** Arc: 아크 지팡이. */
    private final class ArcStaff extends Session {
        private int nextStrike,combo;
        private final String startClip;
        private final int deployTicks;
        private boolean queued,acceptedGrounded;
        private final SuperAttackTiming contact = new SuperAttackTiming();
        private static final int DODGE_COOLDOWN=40,DODGE_INVULNERABLE=6;
        private final ServerLevel dodgeLevel;
        private long nextDodge,dodgeUntil=-1,dodgeMotionAt=-1,dodgeMotionEnd=-1,dodgeInvulnerableUntil=-1;
        private Vec3 dodgeDirection=Vec3.ZERO;
        private boolean dodgeImpulse;

        ArcStaff(ServerPlayer player) {
            super(player, (int) param("duration_ticks", 400));
            dodgeLevel=player.level();
            startClip=!player.onGround()&&kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.has("h15_super_arc_start_air")
                    ?"h15_super_arc_start_air":"h15_super_arc_start";
            deployTicks=kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.durationTicks(startClip,SuperAttackTiming.ARC_DEPLOY);
            Statuses.apply(player, Keyword.AMPLIFIED, duration);
            handItem(kim.biryeong.destiny.fx.SuperVisuals.item(element()));
        }

        @Override
        public boolean tick() {
            advanceDodge();
            if (age + 1 == SuperAttackTiming.ARC_DEPLOY_SWING) SuperVfx.arcDeploy(player);
            if (age >= deployTicks && queued) { queued = false; primary(); }
            if (contact.advance()) strike();
            if (age == duration - 7) PlayerAnimations.play(player, "super_arc_end");
            if (age % 4 == 0) {
                Vec3 p = player.position().add(0, 1, 0);
                AbilityParticles.send(player, player.level(), ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 4, 0.4, 0.6, 0.4, 0.05);
            }
            return super.tick();
        }

        @Override
        public void primary() {
            if (age < deployTicks) { queued = true; return; }
            if(age<nextStrike||contact.pending()||dodgeActive())return;
            boolean grounded=player.onGround();
            String phase=kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.arcAttack(grounded,combo);
            int hit=kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.contactTicks(phase,SuperAttackTiming.ARC_CONTACT);
            if(age+hit>=duration)return;
            acceptedGrounded=grounded;combo++;
            nextStrike=age+Math.max(kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.recoveryTicks(phase,SuperAttackTiming.ARC_RECOVERY),
                    (int)param("strike_interval_ticks",SuperAttackTiming.ARC_RECOVERY));
            contact.request(hit);
            PlayerAnimations.play(player,phase);
        }

        private long now() { return dodgeLevel.getServer().getTickCount(); }
        private boolean dodgeActive() { return dodgeUntil>=0&&now()<dodgeUntil; }
        private boolean ownsDodge() {
            return player.level()==dodgeLevel&&player.isAlive()&&!player.isRemoved()&&!player.hasDisconnected()
                    &&player.getCamera()==player&&kim.biryeong.minigamelib.cinematic.CameraViews.get(player)==null
                    &&(!kim.biryeong.destiny.camera.SuperCamera.ENABLED||kim.biryeong.destiny.camera.SuperCamera.active(player))
                    &&Guardians.runtimeIfPresent(player).map(r->r.superSession==this).orElse(false);
        }
        @Override public java.util.Optional<SuperSession.ClassAbilityCooldown> classAbilityCooldown() {
            return java.util.Optional.of(new SuperSession.ClassAbilityCooldown((int)Math.max(0,nextDodge-now()),DODGE_COOLDOWN));
        }
        @Override public AbilityService.Result classAbility() {
            if(!ownsDodge()||age<deployTicks||age<nextStrike||contact.pending()||dodgeActive()
                    ||kim.biryeong.destiny.combat.MeleeLunge.active(player))return AbilityService.Result.BUSY;
            if(now()<nextDodge)return AbilityService.Result.COOLDOWN;
            var runtime=Guardians.runtime(player);
            String clip=kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.arcDodge(runtime.lastInput);
            int playback=kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.playbackTicks(clip,24);
            if(!kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.has(clip))return AbilityService.Result.BUSY;
            if(!PlayerAnimations.play(player,clip))return AbilityService.Result.FAILED;
            dodgeDirection=Motion.inputDirection(player,runtime.lastInput);
            nextDodge=now()+DODGE_COOLDOWN;
            dodgeUntil=now()+playback;
            dodgeMotionAt=now()+kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.entryBlendTicks(clip);
            dodgeMotionEnd=now()+kim.biryeong.destiny.fx.MeleeSuperAnimationTiming.durationTicks(clip,22);
            dodgeImpulse=false;
            DestinySounds.orVanilla(dodgeLevel,player.position(),"class.hunter.dodge.gambler",
                    SoundEvents.PLAYER_ATTACK_SWEEP,.6f,1.4f);
            advanceDodge();
            return AbilityService.Result.OK;
        }
        private void advanceDodge() {
            if(dodgeUntil<0)return;
            if(!ownsDodge()){finishDodge();return;}
            if(!dodgeImpulse&&now()>=dodgeMotionAt&&now()<dodgeMotionEnd) {
                dodgeImpulse=true;
                Motion.setVelocity(player,new Vec3(dodgeDirection.x*1.15,.18,dodgeDirection.z*1.15));
                Guardians.runtime(player).invulnerableTicks=Math.max(Guardians.runtime(player).invulnerableTicks,DODGE_INVULNERABLE);
                dodgeInvulnerableUntil=now()+DODGE_INVULNERABLE;
                player.resetFallDistance();
            }
            if(dodgeImpulse&&now()>=dodgeMotionEnd)stopDodgeImpulse();
            if(now()>=dodgeUntil)finishDodge();
        }
        private void stopDodgeImpulse() {
            if(!dodgeImpulse)return;
            dodgeImpulse=false;
            if(player.level()!=dodgeLevel||!player.isAlive()||player.hasDisconnected())return;
            Vec3 velocity=player.getDeltaMovement();double along=velocity.dot(dodgeDirection);
            // Retire only the small residual of this impulse; preserve vertical gravity and unrelated lateral/strong impulses.
            if(along>0&&along<=1.1501&&velocity.subtract(dodgeDirection.scale(along)).horizontalDistanceSqr()<.01)
                Motion.setVelocity(player,velocity.subtract(dodgeDirection.scale(along)));
        }
        private void finishDodge() {
            stopDodgeImpulse();
            var runtime=Guardians.runtimeIfPresent(player).orElse(null);
            if(runtime!=null&&now()<dodgeInvulnerableUntil&&runtime.invulnerableTicks<=dodgeInvulnerableUntil-now())
                runtime.invulnerableTicks=0;
            dodgeUntil=dodgeMotionAt=dodgeMotionEnd=dodgeInvulnerableUntil=-1;
            dodgeDirection=Vec3.ZERO;
        }

        private void strike() {
            ServerLevel level = player.level();
            Vec3 eye = player.getEyePosition();
            Vec3 look = player.getLookAngle();
            double reach = param("reach", 4.5);
            SuperVfx.arcSweep(player, reach);
            double cosHalf = Math.cos(Math.toRadians(param("arc_degrees", 70) / 2));
            for (int i = 0; i < 12; i++) {
                double a = Math.toRadians(-35 + i * 6.4);
                Vec3 dir = look.yRot((float) a);
                Fx.line(player, level, eye.add(dir.scale(1.0)), eye.add(dir.scale(reach)), element().glow(), 0.6, 0.7f);
            }
            DestinySounds.hunterOrVanilla(level, eye, element(), "super.fire", SoundEvents.PLAYER_ATTACK_SWEEP, 1f, 1.2f);
            int[] impactVisuals = {0};
            kim.biryeong.destiny.ability.MeleeSuperMovement.contact(player,this,
                    Math.clamp(reach,.1,8),cosHalf,1.8,true,acceptedGrounded,e->{
                Combat.damage(level,player,e,AbilityDamage.pvp(HunterSuper.this,"strike",e,(float)param("damage",16)),
                        element(),kim.biryeong.destiny.weapon.AmmoGeneration.SUPER);
                if(impactVisuals[0]++==0)DestinySounds.hunter(level,e.position(),element(),"super.impact",.65f);
                if(impactVisuals[0]<=2)SuperVfx.arcHit(player,e);
                PostEffects.pulse(player,element(),true);
            });
        }

        @Override
        public void end() {
            queued = false;
            contact.cancel();
            finishDodge();
            super.end();
            player.removeEffect(net.minecraft.world.effect.MobEffects.SPEED);
        }
    }

    /** Solar: 황금 총. */
    private final class GoldenGun extends Session {
        private int shots;
        private int nextShot;
        private boolean queued;
        private int lastContact = -1;
        private int dissolveAt = -1;
        private final SuperAttackTiming contact = new SuperAttackTiming();

        GoldenGun(ServerPlayer player) {
            super(player, (int) param("duration_ticks", 200));
            this.shots = (int) param("shots", 3);
            handItem(kim.biryeong.destiny.fx.SuperVisuals.item(element()));
        }

        @Override
        public boolean tick() {
            if (age >= SuperAttackTiming.SOLAR_DEPLOY && queued) { queued = false; primary(); }
            if (contact.advance()) {
                lastContact = age;
                hitscan(player, param("range", 80), (float) param("damage", 80), element(), Keyword.SCORCHED);
                DestinySounds.hunterOrVanilla(player.level(), player.getEyePosition(), element(), "super.fire", SoundEvents.TRIDENT_THUNDER.value(), 0.7f, 1.8f);
                if (shots == 0) dissolveAt = age + 3;
            }
            if (age == dissolveAt || age == duration - 7) PlayerAnimations.play(player, "super_solar_end");
            boolean live = super.tick();
            return live && (dissolveAt < 0 || age < dissolveAt + 6);
        }

        @Override
        public void primary() {
            if (age < SuperAttackTiming.SOLAR_DEPLOY) { queued = true; return; }
            if (shots <= 0 || age < nextShot || contact.pending() || age + SuperAttackTiming.SOLAR_CONTACT >= duration) {
                return;
            }
            shots--;
            nextShot = age + Math.max(SuperAttackTiming.SOLAR_RECOVERY, (int) param("shot_interval_ticks", 8));
            contact.request(SuperAttackTiming.SOLAR_CONTACT);
            PlayerAnimations.superAttack(player, element());
        }

        @Override
        protected void animateHand(ItemDisplayHud hud) {
            var pose = GoldenGunHandPose.sample(age, lastContact < 0 ? -1 : age - lastContact,
                    duration - age, dissolveAt < 0 ? -1 : age - dissolveAt);
            hud.updateWhenDataChanged(false);
            // Separate aim view from GUI inventory yaw. Shared mesh still equips in third-person.
            hud.setItemTransform(ItemDisplayContext.FIRST_PERSON_RIGHT_HAND);
            hud.setLocation(pose.x(), pose.y(), 0);
            hud.setScale(pose.size(), pose.size(), 1);
            // DisplayHud.vecToQuat calls rotateZYX(vector.x, vector.y, vector.z).
            // Its first slot is therefore physical Z roll; the old third slot pitched X instead.
            hud.setLeftRotation(pose.roll(), 0, 0);
            hud.updateWhenDataChanged(true);
            hud.update();
        }

        @Override
        public void end() {
            queued = false;
            contact.cancel();
            super.end();
        }

        @Override
        public java.util.OptionalInt ammunition() { return java.util.OptionalInt.of(shots); }

        @Override
        public int ammunitionCapacity() { return Math.max(1, (int)param("shots", 3)); }

        @Override
        public float remaining() {
            return Math.min(super.remaining(), shots / (float) Math.max(1, param("shots", 3)));
        }
    }

    /** Void: 그림자 사격 (데드폴 닻). */
    private final class Shadowshot extends Session {
        private boolean fired;
        private final kim.biryeong.destiny.fx.ShadowshotTiming draw = new kim.biryeong.destiny.fx.ShadowshotTiming();
        private int bowStage = -1;
        private ShadowshotLift lift;

        Shadowshot(ServerPlayer player) {
            super(player, kim.biryeong.destiny.fx.ShadowshotTiming.RELEASE_TICKS + 1);
            handItem(kim.biryeong.destiny.fx.SuperVisuals.item(element()));
        }

        @Override
        public boolean tick() {
            if (lift != null) lift.tick(player);
            if (draw.advance()) releaseArrow();
            if (draw.requested() && !fired) {
                SuperVfx.charge(player, draw.progress());
                if (bowStage != draw.bowStage()) {
                    bowStage = draw.bowStage();
                    PlayerAnimations.superItem(player, kim.biryeong.destiny.fx.SuperVisuals.bowStage(bowStage), true);
                }
            }
            boolean live = super.tick();
            return !fired && live;
        }

        @Override
        public void primary() {
            // Deadfall is one automatic cast. Clicks cannot restart, rush or duplicate it.
        }

        @Override
        protected void onActivated() {
            if (!draw.request()) return;
            lift = new ShadowshotLift(player);
            bowStage = 0;
            PlayerAnimations.superItem(player, kim.biryeong.destiny.fx.SuperVisuals.bowStage(0), true);
            PlayerAnimations.superAttack(player, element());
        }

        private void releaseArrow() {
            fired = true;
            PlayerAnimations.superItem(player, kim.biryeong.destiny.fx.SuperVisuals.releasedBow(), true);
            ServerLevel level = player.level();
            double radius = param("tether_radius", 7);
            int tetherTicks = (int) param("tether_ticks", 160);
            float impactDamage = (float) param("damage", 20);
            // W36: activation already plays the uninterrupted cast, including release/impact tail.
            Vec3 release = ShadowshotLift.releasePoint(player);
            SuperVfx.voidRelease(player, release, player.getLookAngle());
            SimProjectile arrow = SimProjectile.launch(player, release, player.getLookAngle().scale(2.6), 0.01, 40,
                    shadowArrow(), 0.8f, element().color(), hit -> {
                        Vec3 anchor = hit.getLocation();
                        SuperVfx.anchor(player, anchor, tetherTicks);
                        PostEffects.pulse(player, element(), true);
                        Fx.burst(player, level, anchor, element(), 80, 1.0);
                        for (LivingEntity e : Combat.enemiesNear(level, player, anchor, radius)) {
                            Combat.damage(level, player, e, AbilityDamage.pvp(HunterSuper.this, "impact", e, impactDamage), element(),kim.biryeong.destiny.weapon.AmmoGeneration.SUPER);
                        }
                        Tasks.run(player, level, age -> {
                            var enemies = Combat.enemiesNear(level, player, anchor, radius);
                            if (age % 10 == 0) SuperVfx.tether(player, anchor, radius, enemies);
                            if (age % 3 == 0) {
                                Fx.ring(player, level, anchor, radius, element().color(), 36);
                            }
                            for (LivingEntity e : enemies) {
                                if (age % 10 == 0) {
                                    Statuses.apply(e, Keyword.WEAKENED, 30);
                                    Statuses.apply(e, Keyword.SUPPRESSED, 30);
                                    Fx.line(player, level, anchor, e.position().add(0, e.getBbHeight() / 2, 0), element().glow(), 0.35, 0.7f);
                                }
                                Vec3 pull = anchor.subtract(e.position()).scale(0.04);
                                e.setDeltaMovement(e.getDeltaMovement().add(pull.x, 0, pull.z));
                                e.needsSync = true;
                            }
                            boolean keep = age < tetherTicks;
                            if (!keep) SuperVfx.cancelLinks(player, anchor);
                            return keep;
                        });
                    });
            SuperVfx.followArrow(player, arrow);
        }

        @Override
        public void end() {
            // No persistent gravity/flight state to restore, and no task can write after this.
            lift = null;
            super.end();
        }

        @Override
        public float remaining() {
            return fired ? 0f : super.remaining();
        }
    }

    private static ItemStack shadowArrow() {
        ItemStack stack = new ItemStack(Items.ARROW);
        stack.set(net.minecraft.core.component.DataComponents.ITEM_MODEL,
                kim.biryeong.destiny.DestinyGuardians.id("shadow_arrow"));
        return stack;
    }

    /** 즉발 사격: 시선 방향 레이캐스트로 첫 적에게 피해. */
    LivingEntity hitscan(ServerPlayer player, double range, float damage, Element element, Keyword keyword) {
        ServerLevel level = player.level();
        Vec3 eye = player.getEyePosition();
        Vec3 end = eye.add(player.getLookAngle().scale(range));
        HitResult block = level.clip(new ClipContext(eye, end, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE, player));
        if (block.getType() != HitResult.Type.MISS) {
            end = block.getLocation();
        }
        EntityHitResult entity = ProjectileUtil.getEntityHitResult(player, eye, end, new AABB(eye, end).inflate(1.0),
                e -> Combat.isEnemy(player, e), eye.distanceToSqr(end));
        Vec3 impact = entity != null ? entity.getLocation() : end;
        if (element == Element.SOLAR) {
            SuperVfx.solarShot(player, eye.add(player.getLookAngle().scale(0.8)).add(0, -0.15, 0), impact);
        }
        Fx.line(player, level, eye.add(player.getLookAngle().scale(0.8)).add(0, -0.15, 0), impact, element.color(), 0.3, 1.1f);
        Fx.burst(player, level, impact, element, 30, 0.3);
        if (entity != null && entity.getEntity() instanceof LivingEntity target) {
            Combat.damage(level, player, target, AbilityDamage.pvp(this, "shot", target, damage), element,kim.biryeong.destiny.weapon.AmmoGeneration.SUPER);
            PostEffects.pulse(player, element, true);
            if (keyword != null && target.isAlive()) {
                if (keyword == Keyword.SCORCHED) Statuses.scorch(player, target, 100);
                else Statuses.apply(target, keyword, 100);
            }
            return target;
        }
        return null;
    }
}
