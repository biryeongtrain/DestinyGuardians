package kim.biryeong.destiny.crucible;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.inventory.WeaponScreen;
import kim.biryeong.destiny.world.TowerSpawnWorld;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerEntityLevelChangeEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.entity.event.v1.ServerPlayerEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.core.Holder;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.Entity;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.ai.attributes.Attribute;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.Vec3;
import java.util.*;

/** One authoritative, uncapped Control session. All mutation stays on the server thread. */
public final class CrucibleRuntime {
    private static final Identifier FREEZE = DestinyGuardians.id("crucible_phase");
    private static final Map<UUID, Member> MEMBERS = new LinkedHashMap<>();
    private static ControlMatch match = new ControlMatch();
    private static MinecraftServer server;
    private static CrucibleWorld.Arena arena;
    private static CrucibleIntro intro;
    private static final Map<ServerPlayer, Boolean> INTRO_GRAVITY = new IdentityHashMap<>();
    private static ControlMatch.Phase observed = ControlMatch.Phase.WAITING;
    private static final Map<UUID, ServerPlayer> PENDING_RETURNS = new LinkedHashMap<>();
    private static boolean initialized;
    private static int transferring;
    private static final class Member {
        ServerPlayer player;
        final GameType previousMode;
        final String previousTeam;
        int respawnAt, protectedUntil, arrivalAfter;
        boolean needsArrival;
        Member(ServerPlayer p) {
            player = p; previousMode = p.gameMode();
            previousTeam = p.getTeam() == null ? null : p.getTeam().getName();
        }
    }
    private CrucibleRuntime() { }

    public static void init() {
        if (initialized) return;
        initialized = true;
        CrucibleWorld.init();
        CrucibleRecovery.init();
        CommandRegistrationCallback.EVENT.register((dispatcher, access, env) -> {
            dispatcher.register(Commands.literal("시련의장")
                    .executes(c -> join(c.getSource().getPlayerOrException()) ? 1 : 0)
                    .then(Commands.literal("참가").executes(c -> join(c.getSource().getPlayerOrException()) ? 1 : 0))
                    .then(Commands.literal("나가기").executes(c -> leave(c.getSource().getPlayerOrException(), true) ? 1 : 0))
                    .then(Commands.literal("상태").executes(c -> {
                        c.getSource().sendSuccess(() -> Component.literal(new com.google.gson.Gson().toJson(match.snapshot())), false); return 1;
                    })));
            dispatcher.register(Commands.literal("crucible")
                    .executes(c -> join(c.getSource().getPlayerOrException()) ? 1 : 0)
                    .then(Commands.literal("leave").executes(c -> leave(c.getSource().getPlayerOrException(), true) ? 1 : 0)));
        });
        ServerTickEvents.END_SERVER_TICK.register(CrucibleRuntime::tick);
        ServerLivingEntityEvents.ALLOW_DAMAGE.register(CrucibleRuntime::allowDamage);
        ServerLivingEntityEvents.AFTER_DEATH.register((entity, damage) -> {
            if (entity instanceof ServerPlayer p) died(p, damage);
        });
        ServerPlayerEvents.AFTER_RESPAWN.register((old, next, alive) -> {
            Member member = MEMBERS.get(old.getUUID());
            if (member == null || member.player != old) {
                if (CrucibleRecovery.pending(next)) PENDING_RETURNS.put(next.getUUID(), next);
                return;
            }
            // ServerPlayer.restoreFrom consults the NEW respawn world's keep_inventory.
            // Native respawn can construct in overworld (false) before we return to the arena
            // (true). Transfer only our confirmed arena member, after death retention ran.
            if (!alive && arena != null && old.level() == arena.level()) {
                next.getInventory().replaceWith(old.getInventory());
                next.experienceLevel = old.experienceLevel;
                next.totalExperience = old.totalExperience;
                next.experienceProgress = old.experienceProgress;
                next.setScore(old.getScore());
            }
            CrucibleTeamVisuals.remove(old);
            member.player = next;
            // Native respawn may still complete its own position/connection restoration.
            // Apply the arena transfer after that stack unwinds, before combat is enabled.
            member.needsArrival = true;
            member.arrivalAfter = sTick(next) + 1;
        });
        ServerEntityLevelChangeEvents.AFTER_PLAYER_CHANGE_LEVEL.register((p, from, to) -> {
            Member member = MEMBERS.get(p.getUUID());
            if (transferring == 0 && member != null && !member.needsArrival
                    && arena != null && to != arena.level()) leave(p, false);
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, s) -> {
            PENDING_RETURNS.remove(handler.getPlayer().getUUID());
            leave(handler.getPlayer(), false);
        });
        ServerPlayConnectionEvents.JOIN.register((handler, sender, s) -> {
            var p = handler.getPlayer();
            // JOIN precedes native level registration. Return on END_SERVER_TICK instead.
            if (CrucibleRecovery.pending(p) || CrucibleWorld.isArena(p.level()))
                PENDING_RETURNS.put(p.getUUID(), p);
        });
        ServerLifecycleEvents.SERVER_STOPPING.register(s -> {
            if (server != s) return;
            closeIntro();
            for (Member member : List.copyOf(MEMBERS.values())) leave(member.player, true);
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(s -> {
            if (server == s) { closeIntro(); CrucibleTeamVisuals.clear(); CrucibleAmmo.clear(); PENDING_RETURNS.clear(); MEMBERS.clear(); match = new ControlMatch(); server = null; arena = null; observed = match.phase(); }
        });
        kim.biryeong.destiny.sound.ActivityMusic.init();
    }

    public static boolean participating(ServerPlayer p) { return p != null && MEMBERS.containsKey(p.getUUID()); }
    /** Identity only: arrival/respawn may legitimately precede canAct becoming true. */
    public static boolean currentParticipant(ServerPlayer p) {
        var m = p == null ? null : MEMBERS.get(p.getUUID());
        return m != null && m.player == p;
    }
    public static ControlMatch.Team team(ServerPlayer p) { return p == null ? null : match.team(p.getUUID()); }
    /** Viewer relationship independent of invulnerability or match phase. */
    public static boolean enemies(ServerPlayer owner, ServerPlayer viewer) {
        return owner != null && viewer != null && owner != viewer && owner.level() == viewer.level()
                && team(owner) != null && team(viewer) != null && team(owner) != team(viewer);
    }
    public static boolean friendly(ServerPlayer owner, ServerPlayer other) {
        if (participating(owner) || participating(other))
            return owner.level() == other.level() && team(owner) != null && team(owner) == team(other);
        return owner == other || owner.isAlliedTo(other) || owner.getTeam() == null && other.getTeam() == null;
    }
    public static boolean canAct(ServerPlayer p) {
        Member m = MEMBERS.get(p.getUUID());
        return m == null || m.player == p && !m.needsArrival && !match.paused() && match.phase() == ControlMatch.Phase.PLAYING
                && match.alive(p.getUUID()) && now() >= m.respawnAt && arena != null && p.level() == arena.level();
    }
    public static boolean canFight(ServerPlayer source, ServerPlayer target) {
        Member victim = MEMBERS.get(target.getUUID());
        return enemies(source, target) && canAct(source) && canAct(target)
                && victim != null && now() >= victim.protectedUntil;
    }
    public static ControlMatch.Snapshot snapshot() { return match.snapshot(); }
    public static boolean viewingIntro(ServerPlayer p) { return intro != null && intro.viewing(p); }

    private static void startIntro() {
        closeIntro();
        var alpha = MEMBERS.values().stream().map(m -> m.player).filter(p -> team(p)==ControlMatch.Team.ALPHA).toList();
        var bravo = MEMBERS.values().stream().map(m -> m.player).filter(p -> team(p)==ControlMatch.Team.BRAVO).toList();
        List<CrucibleIntro.Shot> shots = new ArrayList<>();
        for (var shot : arena.manifest().shots()) {
            Vec3 from=CrucibleWorld.vec(shot.camera()),target=CrucibleWorld.vec(shot.target());
            shots.add(new CrucibleIntro.Shot(from,from.add(target.subtract(from).normalize().scale(3)),target,50));
            if(shots.size()==2)break;
        }
        if(shots.isEmpty())throw new IllegalStateException("맵 소개 카메라 경로가 없습니다.");
        if(shots.size()==1) {var first=shots.getFirst();shots.set(0,new CrucibleIntro.Shot(first.from(),first.to(),first.lookAt(),100));}
        try {
            var stage = CrucibleIntro.confrontationStage(arena.level());
            shots.addAll(CrucibleIntro.confrontationShots(arena.level(), stage));
            intro=CrucibleIntro.begin(alpha,bravo,arena.level(),shots,
                    stage,
                    CrucibleIntro.cameraViews(), new CrucibleIntro.ActorAudience() {
                        @Override public boolean sync(ServerPlayer actor, ServerPlayer viewer, String clip) {
                            return kim.biryeong.destiny.fx.PlayerAnimations.syncIntroViewer(actor,viewer,clip);
                        }
                        @Override public void remove(ServerPlayer actor, ServerPlayer viewer, String clip) {
                            kim.biryeong.destiny.fx.PlayerAnimations.removeIntroViewer(actor,viewer,clip);
                        }
                    });
            for(var actor:intro.actorPlacements()) {
                ServerPlayer p=actor.player();INTRO_GRAVITY.put(p,p.isNoGravity());p.setNoGravity(true);
                Vec3 at=actor.position();
                if (!p.teleportTo(arena.level(),at.x,at.y,at.z,Set.of(),actor.yaw(),0,false))
                    throw new IllegalStateException("Intro actor teleport refused");
                p.setYHeadRot(actor.yaw()); p.yBodyRot = actor.yaw();
                p.setDeltaMovement(Vec3.ZERO); p.fallDistance = 0;
            }
            for(var m:MEMBERS.values()) {
                kim.biryeong.destiny.weapon.ProfileWeaponView.hideForCamera(m.player);
                intro.start(m.player);
            }
        } catch(RuntimeException failure) {
            closeIntro();
            DestinyGuardians.LOGGER.error("시련의 장 인트로 시작 실패",failure);
        }
    }
    private static void closeIntro() {
        if(intro!=null) {intro.close();intro=null;}
        INTRO_GRAVITY.forEach((p,previous)->p.setNoGravity(previous));
        INTRO_GRAVITY.clear();
    }

    public static boolean join(ServerPlayer player) {
        if (participating(player)) return true;
        if (CrucibleRecovery.pending(player)) return false;
        if (!player.isAlive() || player.hasDisconnected() || player.isSpectator() || player.isPassenger()) return false;
        if (!Guardians.isGuardian(player)) {
            player.sendSystemMessage(Component.literal("메뉴의 캐릭터 창에서 직업과 하위직업을 먼저 선택하세요.")); return false;
        }
        MinecraftServer current = player.level().getServer();
        if (server != null && server != current) return false;
        try {
            arena = CrucibleWorld.open(current); server = current;
            Member member = new Member(player);
            CrucibleRecovery.remember(player);
            WeaponScreen.close(player); AbilityService.cleanup(player);
            MEMBERS.put(player.getUUID(), member); match.join(player.getUUID());
            player.setGameMode(GameType.ADVENTURE);
            arrive(member, true);
            if (intro != null && match.phase() == ControlMatch.Phase.INTRO) intro.start(player);
            refreshTeamVisuals();
            player.sendSystemMessage(Component.literal("시련의 장 · 점령에 참가했습니다. /시련의장 나가기 로 탑에 돌아갑니다."));
            return true;
        } catch (RuntimeException error) {
            if (participating(player)) leave(player, true);
            else if (CrucibleRecovery.pending(player)) PENDING_RETURNS.put(player.getUUID(), player);
            DestinyGuardians.LOGGER.error("시련의 장 참가 실패", error);
            player.sendSystemMessage(Component.literal("시련의 장을 준비하지 못했습니다. 서버 기록을 확인해 주세요."));
            return false;
        }
    }

    public static boolean leave(ServerPlayer p, boolean returnToTower) {
        Member m = MEMBERS.get(p.getUUID());
        if (m == null || m.player != p) return false;
        if (intro != null) intro.cancel(p);
        Boolean gravity=INTRO_GRAVITY.remove(p);if(gravity!=null)p.setNoGravity(gravity);
        AbilityService.cleanup(p);
        MEMBERS.remove(p.getUUID()); match.leave(p.getUUID());
        CrucibleHud.remove(p); CrucibleSounds.stop(p); thaw(p);
        CrucibleHealth.leave(p);
        CrucibleAmmo.leave(p);
        var scoreboard = p.level().getServer().getScoreboard();
        if (p.getTeam() != null && p.getTeam().getName().startsWith("dg_control_")) {
            scoreboard.removePlayerFromTeam(p.getScoreboardName());
            if (m.previousTeam != null && scoreboard.getPlayerTeam(m.previousTeam) != null)
                scoreboard.addPlayerToTeam(p.getScoreboardName(), scoreboard.getPlayerTeam(m.previousTeam));
        }
        // Restore the departing connection only after its authoritative team has been restored.
        CrucibleTeamVisuals.remove(p);
        refreshTeamVisuals();
        p.setGameMode(m.previousMode);
        CrucibleRecovery.restore(p);
        p.setDeltaMovement(Vec3.ZERO); p.fallDistance = 0;
        if (returnToTower && !p.hasDisconnected() && p.isAlive()) {
            transferring++;
            try {
                if (TowerSpawnWorld.teleport(p)) CrucibleRecovery.finish(p);
                else PENDING_RETURNS.put(p.getUUID(), p);
            } finally { transferring--; }
        }
        if (!returnToTower && !p.hasDisconnected() && !CrucibleWorld.isArena(p.level()))
            CrucibleRecovery.finish(p);
        if (MEMBERS.isEmpty()) { closeIntro(); observed = match.phase(); }
        return true;
    }

    private static void arrive(Member m, boolean fresh) {
        ServerPlayer p = m.player;
        AbilityService.cleanup(p);
        var position = arena.spawn(team(p), MEMBERS.keySet().stream().toList().indexOf(p.getUUID()));
        transferring++;
        try {
            if (!p.teleportTo(arena.level(), position.position().x, position.position().y, position.position().z,
                    Set.of(), position.yaw(), 0, false)) throw new IllegalStateException("Crucible teleport refused");
        } finally { transferring--; }
        p.setDeltaMovement(Vec3.ZERO); p.fallDistance = 0; p.clearFire();
        p.setHealth(p.getMaxHealth()); p.setAbsorptionAmount(0);
        CrucibleHealth.arrive(p);
        CrucibleAmmo.arrive(p, fresh);
        p.getFoodData().setFoodLevel(20);
        p.setGameMode(GameType.ADVENTURE);
        if (fresh) {
            Guardians.data(p).setSuperEnergy(0);
            for (AbilitySlot slot : AbilitySlot.values()) Guardians.data(p).setCooldown(slot, 0);
        }
        if (now() >= m.respawnAt) match.respawn(p.getUUID());
        m.protectedUntil = Math.max(now(), m.respawnAt) + 40;
        assignScoreboardTeam(p);
        p.inventoryMenu.broadcastFullState();
    }

    private static void assignScoreboardTeam(ServerPlayer p) {
        var scoreboard = p.level().getServer().getScoreboard();
        String name = "dg_control_" + team(p).name().toLowerCase(Locale.ROOT);
        var t = scoreboard.getPlayerTeam(name);
        if (t == null) t = scoreboard.addPlayerTeam(name);
        t.setAllowFriendlyFire(false); t.setSeeFriendlyInvisibles(true);
        t.setCollisionRule(net.minecraft.world.scores.Team.CollisionRule.NEVER);
        scoreboard.addPlayerToTeam(p.getScoreboardName(), t);
        CrucibleTeamVisuals.invalidate();
    }

    private static boolean allowDamage(LivingEntity entity, DamageSource source, float amount) {
        if (!(entity instanceof ServerPlayer target)) return true;
        ServerPlayer attacker = source.getEntity() instanceof ServerPlayer p ? p : null;
        if (!participating(target)) return attacker == null || !participating(attacker);
        Member m = MEMBERS.get(target.getUUID());
        if (!canAct(target) || now() < m.protectedUntil) return false;
        return attacker == null || canFight(attacker, target);
    }
    private static void died(ServerPlayer p, DamageSource source) {
        Member m = MEMBERS.get(p.getUUID());
        if (m == null || m.player != p) return;
        CrucibleAmmo.died(p);
        Entity killer = source.getEntity();
        if (!(killer instanceof ServerPlayer)) killer = p.getLastHurtByPlayer();
        UUID id = killer instanceof ServerPlayer k && enemies(k, p) ? k.getUUID() : null;
        match.kill(id, p.getUUID(), match.life(p.getUUID()));
        m.respawnAt = now() + 100;
        if (intro != null) intro.cancel(p);
        CrucibleHud.remove(p);
    }

    private static void tick(MinecraftServer s) {
        for (ServerPlayer p : List.copyOf(PENDING_RETURNS.values())) {
            if (p.level().getServer() != s || p.hasDisconnected()) { PENDING_RETURNS.remove(p.getUUID(), p); continue; }
            if (participating(p)) { PENDING_RETURNS.remove(p.getUUID(), p); continue; }
            if (!p.isAlive() || p.isRemoved() || s.getPlayerList().getPlayer(p.getUUID()) != p
                    || p.level().getEntity(p.getId()) != p) continue;
            CrucibleRecovery.restore(p); thaw(p);
            if (TowerSpawnWorld.teleport(p)) {
                CrucibleRecovery.finish(p); PENDING_RETURNS.remove(p.getUUID(), p);
            }
        }
        if (s != server || arena == null || MEMBERS.isEmpty()) return;
        for (Member member : List.copyOf(MEMBERS.values())) {
            ServerPlayer p = member.player;
            if (p.hasDisconnected()) { leave(p, false); continue; }
            if (member.needsArrival) {
                if (now() < member.arrivalAfter || !p.isAlive()
                        || s.getPlayerList().getPlayer(p.getUUID()) != p) continue;
                arrive(member, false);
                member.needsArrival = false;
            }
            if (p.isDeadOrDying()) {
                if (now() >= member.respawnAt) {
                    transferring++;
                    try {
                        // The vanilla handler also replaces connection.player, resets movement
                        // bookkeeping and restarts the load timer; PlayerList.respawn alone does not.
                        p.connection.handleClientCommand(new net.minecraft.network.protocol.game.ServerboundClientCommandPacket(
                                net.minecraft.network.protocol.game.ServerboundClientCommandPacket.Action.PERFORM_RESPAWN));
                    }
                    finally { transferring--; }
                }
                continue;
            }
            if (p.level() != arena.level()) { leave(p, false); continue; }
            if (now() >= member.respawnAt && !match.alive(p.getUUID())) match.respawn(p.getUUID());
            if (p.getY() < arena.returnBelowY()) {
                // Void is a real life loss during play; warmup/intro only rescues.
                if (match.phase() == ControlMatch.Phase.PLAYING) p.hurtServer(p.level(), p.damageSources().fellOutOfWorld(), 10000);
                else arrive(member, false);
            }
            CrucibleHealth.tick(p);
            CrucibleAmmo.tick(p);
            if (canAct(p) || match.phase() == ControlMatch.Phase.WAITING) thaw(p); else freeze(p);
            p.getFoodData().setFoodLevel(20);
        }
        Map<String, Set<UUID>> occupants = new HashMap<>();
        for (var zone : arena.zones()) {
            Set<UUID> inside = new HashSet<>();
            for (Member m : MEMBERS.values()) if (canAct(m.player) && m.player.isAlive()
                    && Math.abs(m.player.getY() - zone.position().y) < 2.5
                    && m.player.position().multiply(1,0,1).distanceToSqr(zone.position().multiply(1,0,1)) <= zone.radius()*zone.radius()) inside.add(m.player.getUUID());
            occupants.put(zone.id(), inside);
        }
        var before = match.snapshot();
        match.tick(occupants);
        var after = match.snapshot();
        CrucibleAmmo.tickArena(arena, after);
        if (before.phase() == ControlMatch.Phase.PLAYING && after.phase() == ControlMatch.Phase.PLAYING)
            for (Member m : MEMBERS.values()) CrucibleSounds.zones(m.player, before, after);
        var phase = match.phase();
        if (phase != observed) {
            if (phase == ControlMatch.Phase.INTRO) {
                for (Member m : MEMBERS.values()) { arrive(m, true); freeze(m.player); }
                startIntro();
                for (Member m : MEMBERS.values()) CrucibleSounds.play(m.player, "control");
            } else if (phase == ControlMatch.Phase.PLAYING) {
                closeIntro();
                for (Member m : MEMBERS.values()) { arrive(m, false); thaw(m.player); CrucibleSounds.play(m.player, "start"); }
            } else if (phase == ControlMatch.Phase.RESULTS) {
                closeIntro();
                for (Member m : MEMBERS.values()) { AbilityService.cleanup(m.player); freeze(m.player); CrucibleSounds.play(m.player, match.snapshot().winner() == team(m.player) ? "victory" : "defeat"); }
            } else if (observed == ControlMatch.Phase.RESULTS) {
                for (Member m : List.copyOf(MEMBERS.values())) leave(m.player, true);
            } else closeIntro();
            observed = phase;
        }
        if (intro != null) kim.biryeong.minigamelib.cinematic.CameraViews.sending(intro::tick);
        refreshTeamVisuals();
        if (s.getTickCount() % 5 == 0) {
            var snap = match.snapshot();
            for (Member m : MEMBERS.values()) if (m.player.isAlive()) {
                // HUD displays are owned UI in the cinematic world; its packet filter must
                // not silently discard the new content while the HUD caches it as delivered.
                kim.biryeong.minigamelib.cinematic.CameraViews.sending(() ->
                        CrucibleHud.render(m.player, snap, arena.name(), Math.max(0, m.respawnAt-now())));
            }
            arena.updateZones(snap);
        }
    }
    private static void refreshTeamVisuals() {
        CrucibleTeamVisuals.refresh(MEMBERS.values().stream().filter(m -> !m.needsArrival).map(m -> m.player).toList());
    }
    private static int sTick(ServerPlayer player) { return player.level().getServer().getTickCount(); }
    private static int now() { return server == null ? 0 : server.getTickCount(); }
    private static void freeze(ServerPlayer p) {
        for (Holder<Attribute> type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = p.getAttribute(type);
            if (attr != null && !attr.hasModifier(FREEZE))
                attr.addTransientModifier(new AttributeModifier(FREEZE, -1, AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL));
        }
        p.setSprinting(false); p.setDeltaMovement(Vec3.ZERO);
    }
    private static void thaw(ServerPlayer p) {
        for (var type : List.of(Attributes.MOVEMENT_SPEED, Attributes.JUMP_STRENGTH)) {
            var attr = p.getAttribute(type); if (attr != null) attr.removeModifier(FREEZE);
        }
    }
}
