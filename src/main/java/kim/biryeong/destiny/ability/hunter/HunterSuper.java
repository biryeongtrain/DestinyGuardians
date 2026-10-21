package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.ability.Motion;
import kim.biryeong.destiny.ability.SuperSession;
import kim.biryeong.destiny.ability.Tasks;
import kim.biryeong.destiny.combat.Combat;
import kim.biryeong.destiny.combat.Keyword;
import kim.biryeong.destiny.combat.Statuses;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.fx.PostEffects;
import kim.biryeong.destiny.fx.SimProjectile;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
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
        SuperSession session = switch (element()) {
            case ARC -> new ArcStaff(player);
            case SOLAR -> new GoldenGun(player);
            default -> new Shadowshot(player);
        };
        AbilityService.startSuper(player, session);
        PostEffects.enter(player, element());
        Fx.burst(player.level(), player.position().add(0, 1, 0), element(), 80, 0.8);
        Fx.sound(player.level(), player.position(), SoundEvents.BEACON_ACTIVATE, 1f, 1.4f);
        return true;
    }

    private abstract class Session implements SuperSession {
        protected final ServerPlayer player;
        protected final int duration;
        protected int age;

        Session(ServerPlayer player, int duration) {
            this.player = player;
            this.duration = duration;
        }

        @Override
        public boolean tick() {
            return ++age < duration && player.isAlive();
        }

        @Override
        public float remaining() {
            return Math.max(0f, 1f - (float) age / duration);
        }

        @Override
        public void end() {
            PostEffects.exit(player, element());
            DisplayHud.removeHud(player, HAND_HUD_ID);
        }

        protected void handItem(ItemStack stack) {
            DisplayHud.removeHud(player, HAND_HUD_ID);
            ItemDisplayHud hud = new ItemDisplayHud();
            hud.setItem(stack);
            hud.setItemTransform(ItemDisplayContext.GUI);
            hud.setScale(220, 220, 1);
            hud.setViewRange(1000);
            hud.setAboveHand(true);
            hud.setLocation(1420, 860, 0);
            hud.spawn(player, HAND_HUD_ID);
        }
    }

    /** Arc: 아크 지팡이. */
    private final class ArcStaff extends Session {
        private int nextStrike;

        ArcStaff(ServerPlayer player) {
            super(player, (int) param("duration_ticks", 400));
            Statuses.apply(player, Keyword.AMPLIFIED, duration);
            handItem(new ItemStack(Items.BREEZE_ROD));
        }

        @Override
        public boolean tick() {
            if (age % 4 == 0) {
                Vec3 p = player.position().add(0, 1, 0);
                player.level().sendParticles(ParticleTypes.ELECTRIC_SPARK, p.x, p.y, p.z, 4, 0.4, 0.6, 0.4, 0.05);
            }
            return super.tick();
        }

        @Override
        public void primary() {
            if (age < nextStrike) {
                return;
            }
            nextStrike = age + (int) param("strike_interval_ticks", 6);
            ServerLevel level = player.level();
            Vec3 eye = player.getEyePosition();
            Vec3 look = player.getLookAngle();
            double reach = param("reach", 4.5);
            double cosHalf = Math.cos(Math.toRadians(param("arc_degrees", 70) / 2));
            for (int i = 0; i < 12; i++) {
                double a = Math.toRadians(-35 + i * 6.4);
                Vec3 dir = look.yRot((float) a);
                Fx.line(level, eye.add(dir.scale(1.0)), eye.add(dir.scale(reach)), element().glow(), 0.6, 0.7f);
            }
            Fx.sound(level, eye, SoundEvents.PLAYER_ATTACK_SWEEP, 1f, 1.2f);
            for (LivingEntity e : Combat.enemiesNear(player, eye, reach)) {
                Vec3 to = e.position().add(0, e.getBbHeight() / 2, 0).subtract(eye).normalize();
                if (to.dot(look) >= cosHalf) {
                    Combat.damage(player, e, (float) param("damage", 16), element());
                    level.sendParticles(ParticleTypes.ELECTRIC_SPARK, e.getX(), e.getY() + 1, e.getZ(), 12, 0.3, 0.5, 0.3, 0.2);
                }
            }
        }

        @Override
        public void end() {
            super.end();
            player.removeEffect(net.minecraft.world.effect.MobEffects.SPEED);
        }
    }

    /** Solar: 황금 총. */
    private final class GoldenGun extends Session {
        private int shots;
        private int nextShot;

        GoldenGun(ServerPlayer player) {
            super(player, (int) param("duration_ticks", 200));
            this.shots = (int) param("shots", 3);
            handItem(new ItemStack(Items.GOLDEN_HORSE_ARMOR));
        }

        @Override
        public boolean tick() {
            return shots > 0 && super.tick();
        }

        @Override
        public void primary() {
            if (shots <= 0 || age < nextShot) {
                return;
            }
            shots--;
            nextShot = age + (int) param("shot_interval_ticks", 8);
            hitscan(player, param("range", 80), (float) param("damage", 80), element(), Keyword.SCORCHED);
            Fx.sound(player.level(), player.getEyePosition(), SoundEvents.TRIDENT_THUNDER.value(), 0.7f, 1.8f);
        }

        @Override
        public float remaining() {
            return Math.min(super.remaining(), shots / (float) Math.max(1, param("shots", 3)));
        }
    }

    /** Void: 그림자 사격 (데드폴 닻). */
    private final class Shadowshot extends Session {
        private boolean fired;

        Shadowshot(ServerPlayer player) {
            super(player, (int) param("aim_ticks", 200));
            handItem(new ItemStack(Items.BOW));
        }

        @Override
        public boolean tick() {
            if (!fired && age + 1 >= duration) {
                primary();
            }
            return !fired && super.tick();
        }

        @Override
        public void primary() {
            if (fired) {
                return;
            }
            fired = true;
            ServerLevel level = player.level();
            double radius = param("tether_radius", 7);
            int tetherTicks = (int) param("tether_ticks", 160);
            float impactDamage = (float) param("damage", 20);
            Fx.sound(level, player.getEyePosition(), SoundEvents.ARROW_SHOOT, 1f, 0.6f);
            SimProjectile.launch(player, player.getEyePosition(), player.getLookAngle().scale(2.6), 0.01, 40,
                    new ItemStack(Items.ARROW), 0.8f, element().color(), hit -> {
                        Vec3 anchor = hit.getLocation();
                        Fx.burst(level, anchor, element(), 80, 1.0);
                        Fx.sound(level, anchor, SoundEvents.ENDER_EYE_DEATH, 1f, 0.5f);
                        for (LivingEntity e : Combat.enemiesNear(player, anchor, radius)) {
                            Combat.damage(player, e, impactDamage, element());
                        }
                        Tasks.run(age -> {
                            if (age % 3 == 0) {
                                Fx.ring(level, anchor, radius, element().color(), 36);
                            }
                            for (LivingEntity e : Combat.enemiesNear(player, anchor, radius)) {
                                if (age % 10 == 0) {
                                    Statuses.apply(e, Keyword.WEAKENED, 30);
                                    Statuses.apply(e, Keyword.SUPPRESSED, 30);
                                    Fx.line(level, anchor, e.position().add(0, e.getBbHeight() / 2, 0), element().glow(), 0.35, 0.7f);
                                }
                                Vec3 pull = anchor.subtract(e.position()).scale(0.04);
                                e.setDeltaMovement(e.getDeltaMovement().add(pull.x, 0, pull.z));
                                e.needsSync = true;
                            }
                            return age < tetherTicks;
                        });
                    });
        }

        @Override
        public float remaining() {
            return fired ? 0f : super.remaining();
        }
    }

    /** 즉발 사격: 시선 방향 레이캐스트로 첫 적에게 피해. */
    static LivingEntity hitscan(ServerPlayer player, double range, float damage, Element element, Keyword keyword) {
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
        Fx.line(level, eye.add(player.getLookAngle().scale(0.8)).add(0, -0.15, 0), impact, element.color(), 0.3, 1.1f);
        Fx.burst(level, impact, element, 30, 0.3);
        if (entity != null && entity.getEntity() instanceof LivingEntity target) {
            Combat.damage(player, target, damage, element);
            if (keyword != null && target.isAlive()) {
                Statuses.apply(target, keyword, 100);
            }
            return target;
        }
        return null;
    }
}
