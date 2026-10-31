package kim.biryeong.destiny.tutorial;

import com.mojang.serialization.Codec;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.fx.Fx;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.CharacterLoadouts;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.input.ClientControls;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.weapon.*;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import kim.biryeong.minigamelib.cinematic.CameraViews;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.event.player.AttackBlockCallback;
import net.fabricmc.fabric.api.event.player.PlayerBlockBreakEvents;
import net.fabricmc.fabric.api.event.player.UseBlockCallback;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvents;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.InteractionResult;
import net.minecraft.world.effect.MobEffectInstance;
import net.minecraft.world.effect.MobEffects;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.EntitySpawnReason;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * New Light style guided tutorial. A new Guardian wakes in a private lane, is revived by their Ghost,
 * chooses a class and a Light, arms themselves through the real equipment menu, and then unlocks one
 * mechanic at a time — firing, aiming, reloading, sprint and air jump, grenade, melee, class ability and
 * super — each practised immediately against targets (learning by doing, Destiny 2's Red War/New Light
 * "Light returns piece by piece" structure). Abilities stay locked until their lesson, the player cannot
 * take damage, a fall always returns to the last checkpoint, and a Ghost-opened shortcut appears if a
 * traversal is too hard. The finale ends in a portal to the Tower: "전설이 되십시오".
 */
public final class Tutorial {
    public static final AttachmentType<Boolean> COMPLETED = AttachmentRegistry.create(DestinyGuardians.id("tutorial_completed"),
            b -> b.persistent(Codec.BOOL).copyOnDeath().initializer(() -> false));
    // One-time rollout for every account, including legacy tutorial completers.
    public static final int REQUIRED_REVISION = TutorialEnrollment.REQUIRED_REVISION;
    public static final AttachmentType<Integer> COMPLETED_REVISION = AttachmentRegistry.create(
            DestinyGuardians.id("tutorial_completed_revision"),
            b -> b.persistent(Codec.INT).copyOnDeath().initializer(() -> 0));
    private static final String TARGET_TAG = "destiny_tutorial_target";
    private static final Identifier FLASH = DestinyGuardians.id("crucible/start_flash");
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static final Map<UUID, UUID> TARGET_OWNERS = new HashMap<>();
    private static boolean initialized;

    public enum Step {
        AWAKEN("각성", "고스트를 바라보세요"),
        WALK("각성", "몸을 움직이세요"),
        CLASS("수호자의 길", "직업을 고르세요"),
        LIGHT("여행자의 빛", "빛을 고르세요"),
        EQUIP("무장", "첫 전투를 준비하세요"),
        FIRE("사격 훈련", "표적을 쓰러뜨리세요"),
        AIM("사격 훈련", "정조준으로 쏘세요"),
        RELOAD("사격 훈련", "재장전하세요"),
        ARSENAL("무기군 실습", "대표 무기를 사용하세요"),
        TRAVERSE("기동 훈련", "틈을 건너세요"),
        GRENADE("빛의 능력", "수류탄"),
        MELEE("빛의 능력", "근접 능력"),
        CLASS_ABILITY("빛의 능력", "직업 능력"),
        SUPER("전설의 힘", "궁극기"),
        ASCEND("전설의 시작", "빛의 문으로");
        final String chapter, title;
        Step(String chapter, String title) { this.chapter = chapter; this.title = title; }
    }

    private record Line(String text, int ticks, int at, String voice) { }
    private record Pending(Vec3 rel, int at) { }

    static final class Session {
        final ServerPlayer player;
        final TutorialCourse course;
        final TutorialGhost ghost;
        Step step;
        int stepStart;
        int lookTicks;
        double sprinted;
        Vec3 lastPos;
        boolean flagA, flagB, flagC;
        int count;
        int choiceTicks;
        Object choiceKey;
        TutorialUi.Choice choice;
        Vec3 checkpoint;
        final List<UUID> targets = new ArrayList<>();
        final Deque<Line> lines = new ArrayDeque<>();
        String currentLine;
        String activeVoice;
        int lineUntil;
        TutorialUi.Toast toast;
        int toastUntil;
        int flashUntil = -1;
        int lockedNoticeAt = -100;
        int finishAt = -1;
        int lessonIndex, lessonStarted, lessonDoneAt = -1;
        int lessonInitialRounds;
        boolean lessonFired;
        final List<Pending> pending = new ArrayList<>();

        Session(ServerPlayer player, TutorialCourse course) {
            this.player = player;
            this.course = course;
            this.ghost = new TutorialGhost(player, course.world(TutorialCourse.GHOST_WAKE));
        }
    }

    private Tutorial() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        TutorialLoan.init();
        ServerTickEvents.END_SERVER_TICK.register(Tutorial::tick);
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var s : List.copyOf(SESSIONS.values())) end(s, false);
            TutorialWorld.stopped(server);
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var s = SESSIONS.get(handler.getPlayer().getUUID());
            if (s != null && s.player == handler.getPlayer()) end(s, false);
        });
        // Recover an interrupted loan even if this account already completed the tutorial.
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> TutorialLoan.restore(handler.getPlayer()));
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, source) -> {
            UUID owner = TARGET_OWNERS.remove(entity.getUUID());
            if (owner == null) return;
            var s = SESSIONS.get(owner);
            if (s != null) targetDown(s, entity, source.getEntity() == s.player);
        });
        ServerLivingEntityEvents.ALLOW_DAMAGE.register((entity, source, amount) ->
                !(entity instanceof ServerPlayer) || !TutorialWorld.isTutorial(entity.level()));
        PlayerBlockBreakEvents.BEFORE.register((level, player, pos, state, entity) -> !TutorialWorld.isTutorial(level));
        AttackBlockCallback.EVENT.register((player, level, hand, pos, dir) ->
                TutorialWorld.isTutorial(level) ? InteractionResult.FAIL : InteractionResult.PASS);
        UseBlockCallback.EVENT.register((player, level, hand, hit) ->
                TutorialWorld.isTutorial(level) ? InteractionResult.FAIL : InteractionResult.PASS);
        CommandRegistrationCallback.EVENT.register((dispatcher, access, env) -> dispatcher.register(
                Commands.literal("튜토리얼").executes(c -> {
                    var p = c.getSource().getPlayerOrException();
                    String error = start(p);
                    if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
                    return 1;
                }).then(Commands.literal("단계").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.argument("step", com.mojang.brigadier.arguments.StringArgumentType.word())
                        .suggests((c, b) -> net.minecraft.commands.SharedSuggestionProvider.suggest(
                                Arrays.stream(Step.values()).map(st -> st.name().toLowerCase(Locale.ROOT)), b))
                        .executes(c -> {
                    var p = c.getSource().getPlayerOrException();
                    var s = SESSIONS.get(p.getUUID());
                    String requested = com.mojang.brigadier.arguments.StringArgumentType.getString(c, "step");
                    int lesson = -1;
                    for (int i = 0; i < TutorialArsenal.LESSONS.size(); i++)
                        if (TutorialArsenal.LESSONS.get(i).family().equals(requested)) lesson = i;
                    Step target;
                    try { target = lesson >= 0 ? Step.ARSENAL : Step.valueOf(requested.toUpperCase(Locale.ROOT)); }
                    catch (IllegalArgumentException e) { c.getSource().sendFailure(Component.literal("알 수 없는 단계입니다.")); return 0; }
                    if (s == null) { c.getSource().sendFailure(Component.literal("먼저 /튜토리얼로 시작하세요.")); return 0; }
                    skipTo(s, target);
                    if (lesson >= 0) { s.lessonIndex = lesson; startLesson(s); }
                    return 1;
                }))).then(Commands.literal("나가기").executes(c -> {
                    var p = c.getSource().getPlayerOrException();
                    var s = SESSIONS.get(p.getUUID());
                    if (s == null) { c.getSource().sendFailure(Component.literal("진행 중인 튜토리얼이 없습니다.")); return 0; }
                    end(s, true);
                    return 1;
                }))));
    }

    // ---- public hooks ----------------------------------------------------------------------------------------

    public static boolean active(ServerPlayer p) { return p != null && SESSIONS.containsKey(p.getUUID()); }

    /** Every account completes this rollout once; class and legacy completion are irrelevant. */
    public static boolean shouldStart(ServerPlayer p) {
        return TutorialEnrollment.required(p.getAttachedOrElse(COMPLETED_REVISION, 0), active(p));
    }

    /** Abilities return piece by piece; each slot unlocks at its own lesson. */
    public static boolean allows(ServerPlayer p, AbilitySlot slot) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.player != p) return true;
        Step need = switch (slot) {
            case JUMP -> Step.TRAVERSE;
            case GRENADE -> Step.GRENADE;
            case MELEE -> Step.MELEE;
            case CLASS_ABILITY -> Step.CLASS_ABILITY;
            case SUPER -> Step.SUPER;
        };
        boolean ok = s.step.ordinal() >= need.ordinal();
        int now = now(p);
        if (!ok && now - s.lockedNoticeAt > 40) {
            s.lockedNoticeAt = now;
            p.sendOverlayMessage(Component.literal("아직 이 능력을 쓸 빛이 돌아오지 않았습니다. 고스트를 따라가세요.").withColor(TutorialUi.GHOST));
        }
        return ok;
    }

    public static void abilityUsed(ServerPlayer p, AbilitySlot slot) {
        var s = SESSIONS.get(p.getUUID());
        if (s == null || s.player != p) return;
        switch (s.step) {
            case TRAVERSE -> { if (slot == AbilitySlot.JUMP) s.flagB = true; }
            case GRENADE -> { if (slot == AbilitySlot.GRENADE) s.flagA = true; }
            case MELEE -> { if (slot == AbilitySlot.MELEE) s.flagA = true; }
            case CLASS_ABILITY -> { if (slot == AbilitySlot.CLASS_ABILITY) s.flagA = true; }
            case SUPER -> { if (slot == AbilitySlot.SUPER) s.flagA = true; }
            default -> { }
        }
    }

    public static String start(ServerPlayer p) {
        if (!p.level().getServer().isSameThread()) return "서버에서 다시 시도하세요.";
        if (!p.isAlive() || p.isSpectator() || p.hasDisconnected()) return "살아 있는 접속 플레이어만 시작할 수 있습니다.";
        if (kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p)) return "시련의 장에 참가 중에는 시작할 수 없습니다.";
        if (AbilityService.inSuper(p)) return "궁극기 사용 중에는 시작할 수 없습니다.";
        var old = SESSIONS.get(p.getUUID());
        if (old != null) end(old, false);
        TutorialLoan.restore(p);
        var course = TutorialWorld.acquire(p.level().getServer());
        course.build();
        cleanupForTeleport(p);
        Vec3 spawn = course.world(TutorialCourse.SPAWN);
        if (!p.teleportTo(course.level(), spawn.x, spawn.y, spawn.z, Set.of(), 0, 0, true)) {
            TutorialWorld.release(course);
            return "튜토리얼 공간으로 이동하지 못했습니다.";
        }
        var s = new Session(p, course);
        s.lastPos = p.position();
        SESSIONS.put(p.getUUID(), s);
        Guardians.data(p).setSuperEnergy(0f);
        CombatHud.update(p);
        enter(s, Step.AWAKEN);
        return null;
    }

    /** GameTest access: an isolated lane, built and ready, without a player session. */
    public static TutorialCourse testCourse(MinecraftServer server) {
        var course = TutorialWorld.acquire(server);
        course.build();
        return course;
    }
    public static void releaseTestCourse(TutorialCourse course) { TutorialWorld.release(course); }
    public static boolean isTutorialLevel(net.minecraft.world.level.Level level) { return TutorialWorld.isTutorial(level); }

    /** QA/admin: jump to a step, opening every earlier gate and moving to its checkpoint. */
    private static void skipTo(Session s, Step target) {
        TutorialLoan.restore(s.player);
        clearTargets(s);
        for (var gate : TutorialCourse.Gate.values()) {
            boolean open = switch (gate) {
                case AWAKEN -> target.ordinal() > Step.WALK.ordinal();
                case CLASS -> target.ordinal() > Step.CLASS.ordinal();
                case LIGHT -> target.ordinal() > Step.LIGHT.ordinal();
                case RANGE -> target.ordinal() > Step.ARSENAL.ordinal();
                case ARENA -> target.ordinal() > Step.CLASS_ABILITY.ordinal();
            };
            if (open) s.course.open(gate); else s.course.close(gate);
        }
        Vec3 at = switch (target) {
            case AWAKEN, WALK -> TutorialCourse.SPAWN;
            case CLASS -> TutorialCourse.CLASS_ENTRY;
            case LIGHT -> TutorialCourse.LIGHT_ENTRY;
            case EQUIP, FIRE, AIM, RELOAD, ARSENAL -> TutorialCourse.RANGE_ENTRY;
            case TRAVERSE -> TutorialCourse.RUN_ENTRY;
            case GRENADE, MELEE, CLASS_ABILITY -> TutorialCourse.ARENA_ENTRY;
            case SUPER, ASCEND -> TutorialCourse.FINALE_ENTRY;
        };
        TutorialVoice.stop(s.player, s.activeVoice);
        s.activeVoice = null;
        s.lineUntil = 0;
        s.lines.clear();
        s.ghost.anchor(target == Step.AWAKEN ? s.course.world(TutorialCourse.GHOST_WAKE) : null);
        teleport(s, at);
        enter(s, target);
    }

    // ---- lifecycle -------------------------------------------------------------------------------------------

    private static int now(ServerPlayer p) { return p.level().getServer().getTickCount(); }

    private static void cleanupForTeleport(ServerPlayer p) {
        AbilityService.cleanup(p);
        WeaponRuntime.cleanup(p);
        if (WeaponScreen.active(p)) WeaponScreen.close(p);
        CameraViews.stop(p);
        p.setCamera(p);
        p.stopRiding();
        p.stopUsingItem();
        p.closeContainer();
        p.resetFallDistance();
        p.setDeltaMovement(Vec3.ZERO);
    }

    private static void end(Session s, boolean toTower) {
        if (!SESSIONS.remove(s.player.getUUID(), s)) return;
        clearTargets(s);
        TutorialLoan.restore(s.player);
        TutorialVoice.stop(s.player, s.activeVoice);
        s.ghost.destroy();
        if (s.flashUntil >= 0) s.player.removePostEffect(FLASH);
        TutorialUi.remove(s.player);
        TutorialWorld.release(s.course);
        if (toTower && !s.player.hasDisconnected()) {
            cleanupForTeleport(s.player);
            if (!TowerSpawnWorld.teleport(s.player)) {
                var spawn = s.player.level().getServer().overworld().getRespawnData().pos();
                s.player.teleportTo(s.player.level().getServer().overworld(), spawn.getX() + .5, spawn.getY(), spawn.getZ() + .5, Set.of(), 0, 0, true);
            }
        }
    }

    private static void tick(MinecraftServer server) {
        if (SESSIONS.isEmpty()) return;
        int now = server.getTickCount();
        TutorialWorld.tickDecorations(now);
        for (var s : List.copyOf(SESSIONS.values())) {
            var p = s.player;
            if (p.hasDisconnected() || p.isRemoved() || !TutorialWorld.isTutorial(p.level())) {
                // Left through /tower or another teleport: retire the lane but keep the player where they are.
                end(s, false);
                continue;
            }
            if (s.finishAt >= 0) {
                s.ghost.tick(now);
                if (now >= s.finishAt) end(s, true);
                else render(s, now);
                continue;
            }
            rescue(s);
            s.ghost.tick(now);
            if (s.flashUntil >= 0 && now >= s.flashUntil) { p.removePostEffect(FLASH); s.flashUntil = -1; }
            if (s.step.ordinal() < Step.SUPER.ordinal()) Guardians.data(p).setSuperEnergy(0f);
            advanceLines(s, now);
            respawnTargets(s, now);
            if (now % 3 == 0) particles(s, now);
            step(s, now);
            if (now % 2 == 0) render(s, now);
        }
    }

    private static void rescue(Session s) {
        var p = s.player;
        if (s.step == Step.TRAVERSE && s.course.inGap(p.position())) {
            teleport(s, TutorialCourse.RUN_RETRY);
            say(s, "괜찮아요, 다시 해요. 주황색 선 끝까지 달려서 뛰어요.");
            return;
        }
        if (p.getY() < TutorialCourse.BASE_Y - 12) teleport(s, s.checkpoint);
    }

    private static void teleport(Session s, Vec3 rel) {
        Vec3 w = s.course.world(rel);
        s.player.teleportTo(s.course.level(), w.x, w.y, w.z, Set.of(), 0, 0, true);
        s.player.resetFallDistance();
        s.player.setDeltaMovement(Vec3.ZERO);
        s.lastPos = s.player.position();
    }

    // ---- dialogue / feedback -------------------------------------------------------------------------------

    private static void say(Session s, String text) {
        s.lines.add(new Line(text, 50 + text.length() * 2, now(s.player), null));
    }
    private static void voice(Session s, String key) {
        var cue = TutorialVoice.cue(key);
        s.lines.add(new Line(cue.text(), cue.ticks(), now(s.player), key));
    }
    private static void advanceLines(Session s, int now) {
        if (now < s.lineUntil) return;
        TutorialVoice.stop(s.player, s.activeVoice);
        s.activeVoice = null;
        var next = s.lines.poll();
        if (next == null) { if (now > s.lineUntil + 60) s.currentLine = null; return; }
        s.currentLine = next.text();
        s.lineUntil = now + next.ticks();
        s.ghost.speak(now + next.ticks());
        s.activeVoice = next.voice();
        if (next.voice() != null) { TutorialVoice.play(s.player, next.voice()); return; }
        kim.biryeong.destiny.sound.DestinySounds.personal(s.player,
                "tutorial.ghost.chirp" + (1 + s.player.level().getRandom().nextInt(3)), .3f);
    }
    private static void toast(Session s, String title, String sub, int color, int ticks) {
        s.toast = new TutorialUi.Toast(title, sub, color);
        s.toastUntil = now(s.player) + ticks;
    }
    private static void chime(Session s) {
        s.player.level().playSound(null, s.player.getX(), s.player.getY(), s.player.getZ(),
                SoundEvents.EXPERIENCE_ORB_PICKUP, SoundSource.PLAYERS, .7f, 1.2f);
    }
    private static void unlockSound(Session s) {
        if (!kim.biryeong.destiny.sound.DestinySounds.ready(s.player))
            s.player.level().playSound(null, s.player.getX(), s.player.getY(), s.player.getZ(),
                    SoundEvents.BEACON_POWER_SELECT, SoundSource.PLAYERS, .8f, 1.3f);
    }
    private static void openGate(Session s, TutorialCourse.Gate gate) {
        s.course.open(gate);
        Vec3 c = s.course.gateCenter(gate);
        var level = s.course.level();
        level.sendParticles(ParticleTypes.END_ROD, c.x, c.y, c.z, 40, .9, .9, .2, .04);
        level.playSound(null, c.x, c.y, c.z, SoundEvents.BEACON_ACTIVATE, SoundSource.BLOCKS, 1f, 1.2f);
    }

    // ---- targets ---------------------------------------------------------------------------------------------

    private static UUID spawnTarget(Session s, Vec3 rel, float health) {
        var level = s.course.level();
        var husk = EntityTypes.HUSK.create(level, EntitySpawnReason.COMMAND);
        if (husk == null) return null;
        Vec3 w = s.course.world(rel);
        float yaw = (float) Math.toDegrees(Math.atan2(s.player.getX() - w.x, w.z - s.player.getZ()));
        husk.snapTo(w.x, w.y, w.z, yaw, 0);
        husk.setYHeadRot(yaw);
        husk.setNoAi(true);
        husk.setSilent(true);
        husk.setPersistenceRequired();
        husk.setCanPickUpLoot(false);
        husk.addTag(TARGET_TAG);
        husk.setGlowingTag(true);
        var max = husk.getAttribute(Attributes.MAX_HEALTH);
        if (max != null) max.setBaseValue(health);
        var armor = husk.getAttribute(Attributes.ARMOR);
        if (armor != null) armor.setBaseValue(0);
        var knock = husk.getAttribute(Attributes.KNOCKBACK_RESISTANCE);
        if (knock != null) knock.setBaseValue(1);
        husk.setHealth(health);
        level.addFreshEntity(husk);
        TARGET_OWNERS.put(husk.getUUID(), s.player.getUUID());
        s.targets.add(husk.getUUID());
        level.sendParticles(ParticleTypes.REVERSE_PORTAL, w.x, w.y + 1, w.z, 20, .3, .6, .3, .02);
        return husk.getUUID();
    }

    private static void clearTargets(Session s) {
        var level = s.course.level();
        for (UUID id : s.targets) {
            TARGET_OWNERS.remove(id);
            Entity e = level.getEntity(id);
            if (e != null) e.discard();
        }
        s.targets.clear();
        s.pending.clear();
        s.count = 0;
    }

    private static void targetDown(Session s, LivingEntity entity, boolean playerKill) {
        s.targets.remove(entity.getUUID());
        Vec3 rel = s.course.local(entity.position());
        switch (s.step) {
            case FIRE -> { s.count++; chime(s); }
            case AIM -> {
                if (WeaponAiming.progress(s.player) >= .85f || !WeaponAiming.handles(s.player)) { s.count++; chime(s); }
                else {
                    say(s, ClientControls.gcb(s.player) ? "우클릭을 누른 채 조준하고 좌클릭으로 쏘세요." : "정조준 상태로 맞혀야 해요. 좌클릭으로 조준하고 쏘세요.");
                    s.pending.add(new Pending(rel, now(s.player) + 30));
                }
            }
            case ARSENAL -> {
                if (playerKill && lessonWeaponHeld(s) && (s.lessonFired || lessonSpentAmmo(s))) {
                    s.count++; chime(s); s.lessonDoneAt = now(s.player);
                } else s.pending.add(new Pending(rel, now(s.player) + 20));
            }
            case SUPER -> { s.count++; chime(s); }
            default -> { }
        }
    }

    private static void respawnTargets(Session s, int now) {
        for (var it = s.pending.iterator(); it.hasNext(); ) {
            var next = it.next();
            if (now >= next.at()) { it.remove(); spawnTarget(s, next.rel(), 20); }
        }
    }

    // ---- steps -----------------------------------------------------------------------------------------------

    private static void enter(Session s, Step step) {
        var p = s.player;
        s.step = step;
        s.stepStart = now(p);
        // A new lesson drops stale advice from the previous one, but keeps this tick's reaction line.
        int tick = now(p);
        s.lines.removeIf(line -> line.at() < tick);
        if (s.activeVoice == null && s.lineUntil > tick + 30) s.lineUntil = tick + 30;
        s.flagA = s.flagB = s.flagC = false;
        s.count = 0;
        s.choiceTicks = 0;
        s.choiceKey = null;
        s.choice = null;
        s.sprinted = 0;
        s.pending.clear();
        String cls = className(p);
        switch (step) {
            case AWAKEN -> {
                s.checkpoint = TutorialCourse.SPAWN;
                s.ghost.anchor(s.course.world(TutorialCourse.GHOST_WAKE));
                p.addEffect(new MobEffectInstance(MobEffects.BLINDNESS, 50, 0, false, false));
                p.addEffect(new MobEffectInstance(MobEffects.DARKNESS, 90, 0, false, false));
                voice(s, "awaken");
                say(s, "놀라지 마세요. 저는 고스트예요. 방금 당신을 되살렸어요.");
                say(s, "눈을 떠요, 수호자. 저를 봐 줄래요?");
            }
            case WALK -> {
                s.ghost.anchor(null);
                voice(s, "walk");
            }
            case CLASS -> {
                s.checkpoint = TutorialCourse.CLASS_ENTRY;
                toast(s, "수호자의 길", "당신은 어떤 수호자였나요?", TutorialUi.WHITE, 70);
                say(s, "빛은 수호자마다 다른 모습으로 깃들어요.");
                say(s, "이 선택은 고정되지 않아요. E 키의 장비 메뉴에서 언제든 직업을 바꿀 수 있어요.");
                say(s, "방벽을 세우는 타이탄, 그림자를 걷는 헌터, 빛을 읽는 워록.");
                say(s, "끌리는 쪽의 원 안에 잠시 서 있어 보세요.");
            }
            case LIGHT -> {
                s.checkpoint = TutorialCourse.LIGHT_ENTRY;
                toast(s, "여행자의 파편", "빛이 아직 이곳에 남아 있습니다", 0xF4F0D8, 70);
                say(s, "여행자의 파편이에요. 빛이 아직 남아 있어요.");
                say(s, "어떤 빛을 품을지 고르세요. 아크, 솔라, 공허.");
            }
            case EQUIP -> {
                s.checkpoint = TutorialCourse.RANGE_ENTRY;
                voice(s, "equip");
                grantStarterWeapon(p);
                say(s, "앞에 적이 있어요. 연습용 자동소총을 손에 쥐여 드렸어요. 발사 버튼을 누르고 있으면 연속 사격해요.");
                say(s, "무기는 E 키의 장비 메뉴에서 언제든 설정하고 바꿀 수 있어요. /메뉴로도 열 수 있어요.");
            }
            case FIRE -> {
                if (WeaponItems.entry(p.getMainHandItem()).isEmpty()) grantStarterWeapon(p);
                toast(s, "사격 훈련", ClientControls.gcb(p) ? "좌클릭으로 사격합니다" : "우클릭으로 사격합니다", TutorialUi.GOLD, 60);
                voice(s, "fire");
                for (Vec3 t : TutorialCourse.NEAR_TARGETS) spawnTarget(s, t, 20);
            }
            case AIM -> {
                say(s, ClientControls.gcb(p) ? "먼 표적은 정조준이 정확해요. 우클릭을 누르는 동안 조준하고 좌클릭으로 쏘세요." : "먼 표적은 정조준이 정확해요. 좌클릭으로 조준을 켜고 꺼요.");
                for (Vec3 t : TutorialCourse.FAR_TARGETS) spawnTarget(s, t, 20);
            }
            case RELOAD -> {
                if (!reloadable(p)) {
                    say(s, "이 무기는 재장전이 필요 없어요. 다음으로 가죠.");
                    s.flagA = true;
                } else say(s, "탄창이 비기 전에 재장전하는 습관을 들여요. Q예요.");
            }
            case ARSENAL -> {
                s.checkpoint = TutorialCourse.RANGE_ENTRY;
                s.lessonIndex = 0;
                startLesson(s);
            }
            case TRAVERSE -> {
                s.checkpoint = TutorialCourse.RUN_ENTRY;
                unlockSound(s);
                toast(s, "빛이 돌아옵니다", abilityName(p, AbilitySlot.JUMP) + " 해금", subclassColor(p), 80);
                say(s, "빛은 몸을 가볍게 해요. 먼저 끝까지 질주해 보세요.");
                say(s, "틈이 넓으면 공중에서 점프를 한 번 더 눌러요. " + abilityName(p, AbilitySlot.JUMP) + "예요.");
            }
            case GRENADE -> {
                s.checkpoint = TutorialCourse.ARENA_ENTRY;
                AbilityService.resetCooldown(p, AbilitySlot.GRENADE);
                unlockSound(s);
                toast(s, "새로운 능력", abilityName(p, AbilitySlot.GRENADE), subclassColor(p), 80);
                say(s, "이제 빛을 무기로 써 볼 차례예요. 수류탄부터.");
                say(s, help(p, AbilitySlot.GRENADE));
                for (Vec3 t : TutorialCourse.GRENADE_TARGETS) spawnTarget(s, t, 20);
            }
            case MELEE -> {
                AbilityService.resetCooldown(p, AbilitySlot.MELEE);
                unlockSound(s);
                toast(s, "새로운 능력", abilityName(p, AbilitySlot.MELEE), subclassColor(p), 80);
                say(s, "가까이 붙은 적에겐 근접 능력이에요. 앞의 표적에 다가가세요.");
                spawnTarget(s, TutorialCourse.MELEE_TARGET, 40);
            }
            case CLASS_ABILITY -> {
                AbilityService.resetCooldown(p, AbilitySlot.CLASS_ABILITY);
                unlockSound(s);
                toast(s, "새로운 능력", abilityName(p, AbilitySlot.CLASS_ABILITY), subclassColor(p), 80);
                say(s, cls + "만의 능력이에요. " + help(p, AbilitySlot.CLASS_ABILITY));
            }
            case SUPER -> {
                s.checkpoint = TutorialCourse.FINALE_ENTRY;
                say(s, "느껴져요? 빛이 넘쳐흘러요. 앞으로 가요.");
            }
            case ASCEND -> {
                toast(s, "임무 완료", "빛의 문을 지나 타워로 향하세요", TutorialUi.GOLD, 80);
                voice(s, "ascend");
                say(s, "이제 빛의 문을 지나 타워로 가요.");
            }
        }
    }

    private static void step(Session s, int now) {
        var p = s.player;
        int age = now - s.stepStart;
        switch (s.step) {
            case AWAKEN -> {
                Vec3 to = s.ghost.position().subtract(p.getEyePosition()).normalize();
                if (age > 60 && p.getLookAngle().dot(to) > .95) s.lookTicks++;
                if (s.lookTicks >= 12) enter(s, Step.WALK);
            }
            case WALK -> {
                Vec3 spawn = s.course.world(TutorialCourse.SPAWN);
                if (p.position().subtract(spawn).horizontalDistance() >= 3.5) {
                    chime(s);
                    openGate(s, TutorialCourse.Gate.AWAKEN);
                    say(s, "문이 열렸어요. 따라오세요.");
                    enter(s, Step.CLASS);
                }
            }
            case CLASS -> choose(s, TutorialCourse.CLASSES, c -> {
                String error = CharacterLoadouts.selectClass(p, c.value());
                if (error != null) { p.sendSystemMessage(Component.literal(error)); return false; }
                toast(s, c.name(), "E 키 메뉴에서 언제든 직업 변경 가능", c.color(), 80);
                voice(s, c.value().getSerializedName());
                openGate(s, TutorialCourse.Gate.CLASS);
                enter(s, Step.LIGHT);
                return true;
            });
            case LIGHT -> choose(s, TutorialCourse.SUBCLASSES, c -> {
                String error = CharacterLoadouts.selectSubclass(p, c.value());
                if (error != null) { p.sendSystemMessage(Component.literal(error)); return false; }
                if (p.addPostEffect(FLASH)) s.flashUntil = now + 12;
                p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.RESPAWN_ANCHOR_CHARGE, SoundSource.PLAYERS, 1f, 1.1f);
                Vec3 w = s.course.world(c.center());
                s.course.level().sendParticles(Fx.dust(c.color(), 2f), w.x, w.y + 1.2, w.z, 80, .6, 1.2, .6, 0);
                toast(s, "빛을 되찾았습니다", c.name() + " · " + className(p), c.color(), 90);
                voice(s, "light");
                openGate(s, TutorialCourse.Gate.LIGHT);
                enter(s, Step.EQUIP);
                return true;
            });
            case EQUIP -> {
                if (age >= 40 && !WeaponScreen.active(p)) {
                    chime(s);
                    enter(s, Step.FIRE);
                }
            }
            case FIRE -> { if (s.count >= TutorialCourse.NEAR_TARGETS.size()) { voice(s, "aim"); enter(s, Step.AIM); } }
            case AIM -> { if (s.count >= TutorialCourse.FAR_TARGETS.size()) enter(s, Step.RELOAD); }
            case RELOAD -> {
                if (WeaponRuntime.reloading(p)) s.flagB = true;
                if ((s.flagB && !WeaponRuntime.reloading(p)) || (s.flagA && age > 40)) {
                    chime(s);
                    enter(s, Step.ARSENAL);
                }
            }
            case ARSENAL -> tickLesson(s, now);
            case TRAVERSE -> {
                Vec3 pos = p.position();
                if (p.isSprinting() && s.course.beyond(pos, 94)) s.sprinted += pos.subtract(s.lastPos).horizontalDistance();
                s.lastPos = pos;
                if (s.sprinted >= 12 && !s.flagA) { s.flagA = true; chime(s); voice(s, "traverse"); }
                if (s.course.acrossChasm(pos) && p.onGround() && !s.flagC) { s.flagC = true; chime(s); }
                if (age == 700 && !s.flagC) {
                    s.course.fallbackBridge(true);
                    say(s, "빛의 다리를 놓아 뒀어요. 공중 도약은 건너편에서도 연습할 수 있어요.");
                }
                if (s.flagA && s.flagB && s.flagC) {
                    say(s, "그거예요! 이제 몸이 기억하네요.");
                    enter(s, Step.GRENADE);
                }
            }
            case GRENADE -> { if (s.flagA && age > 20) { chime(s); voice(s, "grenade"); enter(s, Step.MELEE); } }
            case MELEE -> { if (s.flagA && age > 20) { chime(s); voice(s, "melee"); enter(s, Step.CLASS_ABILITY); } }
            case CLASS_ABILITY -> {
                if (s.flagA && age > 20) {
                    chime(s);
                    clearTargets(s);
                    openGate(s, TutorialCourse.Gate.ARENA);
                    voice(s, "class_ability");
                    enter(s, Step.SUPER);
                }
            }
            case SUPER -> {
                if (!s.flagC && s.course.beyond(p.position(), 166)) {
                    s.flagC = true;
                    Guardians.data(p).setSuperEnergy(1f);
                    CombatHud.update(p);
                    unlockSound(s);
                    toast(s, "궁극기 준비 완료", abilityName(p, AbilitySlot.SUPER), subclassColor(p), 90);
                    voice(s, "super");
                    for (Vec3 t : TutorialCourse.WAVE) spawnTarget(s, t, 30);
                }
                if (s.flagC && s.flagA && s.count >= TutorialCourse.WAVE.size() && !AbilityService.inSuper(p)) {
                    enter(s, Step.ASCEND);
                } else if (s.flagC && s.flagA && s.count >= TutorialCourse.WAVE.size() && age % 40 == 0) {
                    say(s, "마지막 적까지 끝났어요.");
                }
            }
            case ASCEND -> {
                if (s.course.inPortal(p.position())) finish(s, now);
            }
        }
    }

    private interface Pick<T> { boolean apply(TutorialCourse.Choice<T> choice); }

    private static <T> void choose(Session s, List<TutorialCourse.Choice<T>> choices, Pick<T> pick) {
        var p = s.player;
        TutorialCourse.Choice<T> near = null, inside = null;
        double best = 4.5;
        for (var c : choices) {
            double d = p.position().subtract(s.course.world(c.center())).horizontalDistance();
            if (d < best) { best = d; near = c; }
            if (d <= TutorialCourse.CHOICE_RADIUS) inside = c;
        }
        if (inside == null || inside.value() != s.choiceKey) {
            s.choiceTicks = 0;
            s.choiceKey = inside == null ? null : inside.value();
        }
        if (inside != null && p.onGround()) s.choiceTicks++;
        float progress = Math.min(1f, s.choiceTicks / 30f);
        s.choice = near == null ? null : new TutorialUi.Choice(near.name(), near.icon(), near.color(), near.blurb(), near == inside ? progress : 0);
        if (inside != null && s.choiceTicks >= 30) {
            s.choiceTicks = 0;
            pick.apply(inside);
        }
    }

    private static void finish(Session s, int now) {
        var p = s.player;
        p.setAttached(COMPLETED, true);
        p.setAttached(COMPLETED_REVISION, REQUIRED_REVISION);
        s.finishAt = now + 80;
        if (p.addPostEffect(FLASH)) s.flashUntil = now + 12;
        p.level().playSound(null, p.getX(), p.getY(), p.getZ(), SoundEvents.UI_TOAST_CHALLENGE_COMPLETE, SoundSource.PLAYERS, 1f, 1f);
        toast(s, "전설이 되십시오", "튜토리얼 완료 · 언제든 /튜토리얼로 다시 할 수 있습니다", TutorialUi.GOLD, 100);
        TutorialVoice.stop(s.player, s.activeVoice);
        s.activeVoice = null;
        s.lineUntil = 0;
        s.lines.clear();
        s.currentLine = "타워에서 봐요, 수호자.";
        s.lineUntil = now + 80;
        clearTargets(s);
    }

    private static void grantStarterWeapon(ServerPlayer p) {
        TutorialLoan.equip(p, WeaponCatalog.find("halfdan_d").orElseThrow());
    }

    private static boolean reloadable(ServerPlayer p) {
        return WeaponItems.entry(p.getMainHandItem()).map(e -> !e.family().equals("bow") && !e.family().equals("sword")
                && !e.family().equals("glaive") && WeaponProfile.forEntry(e).magazine() > 1).orElse(false);
    }

    private static String className(ServerPlayer p) {
        return switch (Guardians.data(p).guardianClass()) {
            case TITAN -> "타이탄"; case HUNTER -> "헌터"; case WARLOCK -> "워록"; case NONE -> "수호자";
        };
    }
    private static int subclassColor(ServerPlayer p) {
        Element e = CharacterLoadouts.subclass(Guardians.data(p));
        if (e == null) return TutorialUi.WHITE;
        return switch (e) { case ARC -> 0x80D9F3; case SOLAR -> 0xFFAA63; case VOID -> 0xB695FF; default -> TutorialUi.WHITE; };
    }
    private static String abilityName(ServerPlayer p, AbilitySlot slot) {
        return AbilityService.equipped(p, slot).map(Ability::displayName).orElse("능력");
    }
    private static String help(ServerPlayer p, AbilitySlot slot) {
        String text = AbilityService.equipped(p, slot)
                .map(a -> kim.biryeong.destiny.inventory.AbilityHelpText.description(a.id().getPath())).orElse("");
        return text.isEmpty() ? abilityName(p, slot) + "을(를) 써 보세요." : text;
    }

    // ---- presentation ----------------------------------------------------------------------------------------

    private static void particles(Session s, int now) {
        var p = s.player;
        var level = s.course.level();
        List<? extends TutorialCourse.Choice<?>> choices = s.step == Step.CLASS ? TutorialCourse.CLASSES
                : s.step == Step.LIGHT ? TutorialCourse.SUBCLASSES : List.of();
        for (var c : choices) {
            Vec3 w = s.course.world(c.center());
            int n = 28;
            for (int i = 0; i < n; i++) {
                double a = i * Math.PI * 2 / n + now / 30.0;
                level.sendParticles(p, Fx.dust(c.color(), 1.1f), true, true,
                        w.x + Math.cos(a) * TutorialCourse.CHOICE_RADIUS, w.y + .1, w.z + Math.sin(a) * TutorialCourse.CHOICE_RADIUS, 1, 0, 0, 0, 0);
            }
            if (s.choiceKey == c.value() && s.choiceTicks > 0) {
                int steps = Math.round(n * Math.min(1f, s.choiceTicks / 30f));
                for (int i = 0; i < steps; i++) {
                    double a = -Math.PI / 2 + i * Math.PI * 2 / n;
                    for (double y = .2; y < 2.4; y += .55)
                        level.sendParticles(p, Fx.dust(c.color(), 1.4f), true, true,
                                w.x + Math.cos(a) * (TutorialCourse.CHOICE_RADIUS - .3), w.y + y, w.z + Math.sin(a) * (TutorialCourse.CHOICE_RADIUS - .3), 1, 0, 0, 0, 0);
                }
            }
        }
        if (s.step == Step.LIGHT) {
            Vec3 shard = s.course.world(new Vec3(.5, 4.2, 46.5));
            level.sendParticles(p, ParticleTypes.END_ROD, true, false, shard.x, shard.y, shard.z, 2, 1.4, 1.4, 1.4, .01);
        }
        if (s.step == Step.ASCEND || s.finishAt >= 0) {
            Vec3 portal = s.course.world(TutorialCourse.PORTAL);
            for (double y = 0; y < 4.5; y += .5)
                level.sendParticles(p, Fx.dust(0xF4F0D8, 1.6f), true, true, portal.x + (Math.random() - .5) * 2.6, portal.y + y, portal.z, 1, 0, 0, 0, 0);
            level.sendParticles(p, ParticleTypes.END_ROD, true, false, portal.x, portal.y + 2, portal.z, 3, .9, 1.4, .1, .02);
        }
        // Guide beam toward the current destination gate.
        TutorialCourse.Gate gate = switch (s.step) {
            case WALK -> TutorialCourse.Gate.AWAKEN;
            default -> null;
        };
        if (gate != null) {
            Vec3 c = s.course.gateCenter(gate);
            level.sendParticles(p, Fx.dust(TutorialUi.GHOST, 1.2f), true, true, c.x, c.y, c.z - .6, 6, .8, .8, .05, 0);
        }
    }

    private static boolean lessonWeaponHeld(Session s) {
        return TutorialLoan.borrowed(s.player, s.player.getMainHandItem())
                && WeaponItems.entry(s.player.getMainHandItem()).filter(TutorialArsenal.LESSONS.get(s.lessonIndex).weapon()::equals).isPresent();
    }
    private static boolean lessonSpentAmmo(Session s) {
        if (!lessonWeaponHeld(s)) return false;
        var lesson = TutorialArsenal.LESSONS.get(s.lessonIndex);
        return WeaponItems.magazine(s.player.getMainHandItem(), WeaponProfile.forEntry(lesson.weapon())).rounds() < s.lessonInitialRounds;
    }
    private static void startLesson(Session s) {
        clearTargets(s);
        var p = s.player;
        var lesson = TutorialArsenal.LESSONS.get(s.lessonIndex);
        TutorialLoan.equip(p, lesson.weapon());
        teleport(s, TutorialCourse.RANGE_ENTRY);
        s.lessonStarted = now(p); s.lessonDoneAt = -1; s.lessonFired = false;
        s.lessonInitialRounds = WeaponProfile.forEntry(lesson.weapon()).magazine();
        s.lines.clear();
        TutorialVoice.stop(p, s.activeVoice); s.activeVoice = null; s.lineUntil = 0;
        boolean newAmmo = s.lessonIndex == 0 || !TutorialArsenal.LESSONS.get(s.lessonIndex - 1).ammunition().equals(lesson.ammunition());
        if (newAmmo) say(s, TutorialArsenal.ammoExplanation(lesson.ammunition()));
        say(s, lesson.description());
        toast(s, lesson.title() + " · " + (s.lessonIndex + 1) + "/" + TutorialArsenal.LESSONS.size(),
                lesson.weapon().name() + " · " + lesson.ammoLabel(), TutorialUi.GOLD, 100);
        spawnTarget(s, TutorialCourse.RANGE_ENTRY.add(0, 0, lesson.distance()), 20);
    }
    private static void tickLesson(Session s, int now) {
        var p = s.player;
        s.lessonFired |= lessonSpentAmmo(s);
        if (s.lessonDoneAt >= 0 && now >= s.lessonDoneAt + 30 && s.lines.isEmpty() && now >= s.lineUntil
                && !GcbWeaponInput.buttonsDown(p) && !WeaponRuntime.triggerHeld(p)) {
            if (s.lessonIndex + 1 < TutorialArsenal.LESSONS.size()) { s.lessonIndex++; startLesson(s); }
            else {
                TutorialLoan.restore(p);
                boolean needsStarter = WeaponLoadout.equipped(p).isEmpty();
                if (needsStarter) grantStarterWeapon(p);
                clearTargets(s);
                openGate(s, TutorialCourse.Gate.RANGE);
                say(s, needsStarter ? "모든 무기군을 익혔어요. 남은 훈련에도 연습용 자동소총을 쓰세요. 다음은 기동 훈련이에요."
                        : "모든 무기군을 익혔어요. 원래 장비를 돌려드렸어요. 다음은 기동 훈련이에요.");
                enter(s, Step.TRAVERSE);
            }
            return;
        }
        // Recover a lost/stowed loan without replacing any of the player's saved equipment.
        if (!lessonWeaponHeld(s)) {
            if (now - s.lessonStarted > 40 && now % 40 == 0) {
                TutorialLoan.equip(p, TutorialArsenal.LESSONS.get(s.lessonIndex).weapon());
                s.lessonInitialRounds = WeaponProfile.forEntry(TutorialArsenal.LESSONS.get(s.lessonIndex).weapon()).magazine();
                s.lessonFired = false;
            }
            return;
        }
        var profile = WeaponProfile.forEntry(TutorialArsenal.LESSONS.get(s.lessonIndex).weapon());
        var ammo = WeaponItems.magazine(p.getMainHandItem(), profile);
        if (!profile.infiniteReserve() && ammo.total() == 0 && !WeaponRuntime.reloading(p)) {
            // Only marked training gear is refilled. Finite ammunition remains finite outside this room.
            if (profile.reserve() > 0) ammo.addReserve(profile.reserve());
            else ammo.addLoaded(profile.magazine());
            WeaponItems.save(p.getMainHandItem(), ammo);
            p.containerMenu.broadcastChanges();
            say(s, "연습 탄약을 보충했어요. Q로 재장전하고 다시 시도하세요.");
        }
        if (s.currentLine == null && s.lines.isEmpty()) s.currentLine = TutorialArsenal.LESSONS.get(s.lessonIndex).description();
    }

    private static void render(Session s, int now) {
        var p = s.player;
        boolean gcb = ClientControls.gcb(p);
        var objectives = new ArrayList<TutorialUi.Objective>();
        String key = null, action = null;
        switch (s.step) {
            case AWAKEN -> { objectives.add(new TutorialUi.Objective("고스트 바라보기", s.lookTicks >= 12 ? 1 : 0, 1)); key = "마우스"; action = "주위 둘러보기"; }
            case WALK -> { objectives.add(new TutorialUi.Objective("앞으로 걷기", 0, 1)); key = "W A S D"; action = "이동"; }
            case CLASS -> {
                objectives.add(new TutorialUi.Objective("타이탄 · 헌터 · 워록 중 선택", 0, 1));
                key = "E"; action = "직업은 언제든 변경 가능";
            }
            case LIGHT -> objectives.add(new TutorialUi.Objective("아크 · 솔라 · 공허 중 선택", 0, 1));
            case EQUIP -> {
                objectives.add(new TutorialUi.Objective("연습용 자동소총 지급", 1, 1));
                key = "E"; action = "무기 설정 · 변경";
            }
            case FIRE -> {
                objectives.add(new TutorialUi.Objective("가까운 표적 처치", s.count, TutorialCourse.NEAR_TARGETS.size()));
                objectives.add(new TutorialUi.Objective("E 키 · 무기 설정 및 변경", 0, 0));
                key = gcb ? "좌클릭" : "우클릭"; action = "누르고 있으면 연속 사격";
            }
            case AIM -> { objectives.add(new TutorialUi.Objective("정조준으로 먼 표적 처치", s.count, TutorialCourse.FAR_TARGETS.size())); key = gcb ? "우클릭 홀드" : "좌클릭"; action = gcb ? "정조준" : "정조준 켜기 · 끄기"; }
            case RELOAD -> { objectives.add(new TutorialUi.Objective("재장전", s.flagB ? 1 : 0, 1)); key = "Q"; action = "재장전 (몇 발 쏜 뒤)"; }
            case ARSENAL -> {
                var lesson = TutorialArsenal.LESSONS.get(s.lessonIndex);
                objectives.add(new TutorialUi.Objective("무기군 실습", s.lessonIndex + (s.lessonDoneAt >= 0 ? 1 : 0), TutorialArsenal.LESSONS.size()));
                objectives.add(new TutorialUi.Objective(lesson.ammoLabel(), 0, 0));
                objectives.add(new TutorialUi.Objective("대표 무기로 표적 처치", s.count, 1));
                boolean sword = lesson.family().equals("sword");
                key = sword || gcb ? "좌클릭" : "우클릭";
                action = sword ? "가까이서 베기" : switch (lesson.family()) {
                    case "bow" -> "당긴 뒤 놓아 발사";
                    case "fusion_rifle", "linear_fusion_rifle" -> "누른 채 충전 후 발사";
                    default -> "사격 · Q 재장전";
                };
                if (s.lessonDoneAt >= 0) { key = "마우스"; action = "버튼을 놓고 설명 듣기"; }
            }
            case TRAVERSE -> {
                objectives.add(new TutorialUi.Objective("질주", (int) Math.min(12, s.sprinted), 12));
                objectives.add(new TutorialUi.Objective("공중 도약 · " + abilityName(p, AbilitySlot.JUMP), s.flagB ? 1 : 0, 1));
                objectives.add(new TutorialUi.Objective("넓은 틈 건너기", s.flagC ? 1 : 0, 1));
                if (!s.flagA) { key = "Ctrl · W 두 번"; action = "질주"; }
                else { key = "공중에서 Space"; action = abilityName(p, AbilitySlot.JUMP); }
            }
            case GRENADE -> { objectives.add(new TutorialUi.Objective(abilityName(p, AbilitySlot.GRENADE) + " 던지기", s.flagA ? 1 : 0, 1)); key = gcb ? "Z" : "F"; action = "수류탄"; }
            case MELEE -> { objectives.add(new TutorialUi.Objective(abilityName(p, AbilitySlot.MELEE) + " 사용", s.flagA ? 1 : 0, 1)); key = gcb ? "C" : "Shift + 좌클릭"; action = "근접 능력"; }
            case CLASS_ABILITY -> { objectives.add(new TutorialUi.Objective(abilityName(p, AbilitySlot.CLASS_ABILITY) + " 사용", s.flagA ? 1 : 0, 1)); key = gcb ? "V" : "Shift 두 번"; action = "직업 능력"; }
            case SUPER -> {
                if (!s.flagC) objectives.add(new TutorialUi.Objective("최종 훈련장으로 이동", 0, 1));
                else {
                    objectives.add(new TutorialUi.Objective(abilityName(p, AbilitySlot.SUPER) + " 발동", s.flagA ? 1 : 0, 1));
                    objectives.add(new TutorialUi.Objective("적 처치", s.count, TutorialCourse.WAVE.size()));
                    if (!s.flagA) { key = gcb ? "F" : "Shift + F"; action = "궁극기"; }
                    else if (AbilityService.inSuper(p)) { key = "우클릭 · 좌클릭"; action = "궁극기 공격"; }
                }
            }
            case ASCEND -> objectives.add(new TutorialUi.Objective("빛의 문 통과", s.finishAt >= 0 ? 1 : 0, 1));
        }
        var toast = now < s.toastUntil ? s.toast : null;
        TutorialUi.render(p, new TutorialUi.View(s.step.chapter, s.step.ordinal() + 1, Step.values().length, s.step == Step.ARSENAL ? TutorialArsenal.LESSONS.get(s.lessonIndex).title() : s.step.title,
                objectives, key, action, s.currentLine, toast, s.choice, WeaponScreen.active(p)));
    }
}
