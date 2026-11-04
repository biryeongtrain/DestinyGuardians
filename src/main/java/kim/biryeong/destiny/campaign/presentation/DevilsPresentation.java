package kim.biryeong.destiny.campaign.presentation;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.activity.presentation.ModelTransport;
import kim.biryeong.destiny.down.GuardianDown;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.strike.devils.*;
import kim.biryeong.minigamelib.displayhud.*;
import kr.toxicity.model.api.animation.AnimationIterator;
import kr.toxicity.model.api.animation.AnimationModifier;
import kr.toxicity.model.api.tracker.EntityTracker;
import kr.toxicity.model.api.tracker.EntityTrackerRegistry;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Holder;
import net.minecraft.core.component.DataComponents;
import net.minecraft.core.particles.ParticleTypes;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.game.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundEvent;
import net.minecraft.sounds.SoundSource;
import net.minecraft.world.entity.Display;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.AttributeModifier;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.entity.player.Abilities;
import net.minecraft.world.item.*;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.ClipContext;
import net.minecraft.world.level.GameType;
import net.minecraft.world.phys.*;
import java.util.*;

/**
 * Session-owned authored staging around source-transformed SP.IN/SP.C anchors. Camera motion and
 * vanilla beacon/portal sound substitutions are authored; the Sepiks skeletal intro is the supplied
 * 80E10752 clip, played at native speed and never cut down to fit the four-second camera lock.
 */
public final class DevilsPresentation implements DevilsLair.Presentation {
    public static final String INTRO_CLIP = "source_80e10752_sepix_intro";
    static final int CAMERA_TICKS = 80;
    static final int CLIP_GRACE_TICKS = 20;
    private static final Map<UUID, View> LOCKS = new HashMap<>();
    private static final String HUD = "destiny:devils_presentation/";
    private final DevilsSession session;
    private final Map<UUID, View> views = new LinkedHashMap<>();
    private final Map<UUID, ServerPlayer> hudAudience = new HashMap<>();
    private final Map<String, Telegraph> telegraphs = new LinkedHashMap<>();
    private final Set<String> problems = new HashSet<>();
    private long generation, clock;
    private DevilsDirector.Phase phase = DevilsDirector.Phase.READY;
    private Intro intro;
    private ModelTransport transport;
    private String transportPack;
    private boolean transportDropStarted;
    private final Map<String, DevilsPlan.Slot> incomingSlots = new HashMap<>();
    private final Set<String> consideredTransports = new HashSet<>();
    private final Set<String> transportRiders = new HashSet<>();
    private boolean closed;
    private record Telegraph(long generation, Vec3 at, boolean flying) { }
    public DevilsPresentation(DevilsSession session) { this.session = Objects.requireNonNull(session); }
    /** Compose with the existing Rising/GuardianDown suppression predicates at init. */
    public static boolean hudHidden(ServerPlayer p) { var v = LOCKS.get(p.getUUID()); return v != null && v.player == p && !v.closed; }
    @Override public boolean hidden(ServerPlayer p) { var v = views.get(p.getUUID()); return v != null && v.player == p && !v.closed; }

    @Override public void phase(DevilsSession ignored, DevilsDirector.Snapshot state) {
        if (closed) return;
        if (generation != state.generation()) cancelGeneration(generation);
        generation = state.generation(); phase = state.phase();
        var pending = new HashSet<String>();
        for (var slot : state.slots()) if (slot.state() == DevilsDirector.SlotState.RESERVED
                || slot.state() == DevilsDirector.SlotState.LOST) pending.add(slot.slot().id());
        incomingSlots.keySet().retainAll(pending);
        transportRiders.retainAll(pending);
        if (transport != null && transportRiders.isEmpty()) transport.delivered();
        if (phase == DevilsDirector.Phase.BRIEFING) {
            releaseViews();
            for (var p : session.players()) if (eligible(p)) addView(p, null);
        } else if (phase == DevilsDirector.Phase.SP_INTRO) {
            releaseViews(); beginIntro();
        } else {
            releaseViews();
            if (intro != null) { intro.cancel(); intro = null; }
        }
    }
    private boolean eligible(ServerPlayer p) { return !p.hasDisconnected() && p.isAlive() && p.level() == session.level()
            && p.connection.hasClientLoaded() && !GuardianDown.active(p) && !p.isSpectator(); }
    private void addView(ServerPlayer p, CameraPath path) {
        if (LOCKS.containsKey(p.getUUID())) { problem("Conflicting cinematic owner for " + p.getUUID()); return; }
        var view = new View(p, path);
        views.put(p.getUUID(), view); LOCKS.put(p.getUUID(), view);
        try { view.begin(); } catch (RuntimeException e) { view.close(); problem("Camera setup failed: " + e.getMessage()); }
    }
    private void beginIntro() {
        var boss = session.level().getEntitiesOfClass(DevilsMob.class,
                new AABB(DevilsWorldBuild.origin(DevilsPlan.Zone.SP)).inflate(256),
                e -> e.kind() == DevilsPlan.Kind.SEPIKS && !e.isRemoved() && e.reference() != null
                        && e.reference().generation() == generation).stream().findFirst().orElse(null);
        if (boss == null) { problem("Sepiks intro actor unavailable"); return; }
        var registry = EntityTrackerRegistry.registry(boss.getUUID());
        EntityTracker tracker = registry == null ? null : registry.tracker("dl_sepiks");
        if (tracker == null || tracker.isClosed() || tracker.renderer().animation(INTRO_CLIP).isEmpty()) {
            problem("Required source Sepiks intro clip unavailable: " + INTRO_CLIP); return;
        }
        int clipTicks = tracker.renderer().animation(INTRO_CLIP).map(a -> (int) Math.ceil(a.length() * 20)).orElse(0);
        intro = new Intro(boss, tracker, generation, clipTicks);
        var run = intro;
        // Only PLAY_ONCE natural exhaustion invokes this callback in BetterModel3.5.1. stopAnimation
        // removes the iterator without invoking it; cancellation still invalidates our gate first.
        boolean accepted = tracker.animate(INTRO_CLIP, AnimationModifier.builder().start(2).end(2)
                .priority(100).type(AnimationIterator.Type.PLAY_ONCE).build(),
                () -> session.level().getServer().execute(() -> run.gate.naturalEnd(run.gate.generation, boss.getUUID())));
        if (!accepted) { run.cancel(); intro = null; problem("Source intro animation rejected"); return; }
        run.gate.started = true;
        Vec3 target = boss.position().add(0, boss.getBbHeight() * .52, 0);
        Vec3 entrance = DevilsMaps.anchor(DevilsPlan.Zone.SP, "SP.IN", DevilsWorldBuild.origin(DevilsPlan.Zone.SP)).pos();
        Vec3 forward = entrance.subtract(target).multiply(1, 0, 1).normalize();
        if (forward.lengthSqr() < .5) forward = new Vec3(0, 0, -1);
        Vec3 right = new Vec3(-forward.z, 0, forward.x);
        CameraPath path = choosePath(target, forward, right);
        for (var p : session.players()) if (eligible(p)) {
            if (path != null) addView(p, path);
            sound(p, "block.beacon.activate", target, .7f, .65f);
        }
        if (path == null) problem("No collision-safe Sepiks camera path; source animation continues in gameplay view");
    }
    private CameraPath choosePath(Vec3 target, Vec3 forward, Vec3 right) {
        for (double side : new double[]{1, -1, 0}) {
            var candidate = new CameraPath(target.add(forward.scale(14)).add(right.scale(side * 3)).add(0, 1.5, 0),
                    target.add(forward.scale(10)).add(right.scale(side * 1.5)).add(0, .5, 0), target);
            boolean valid = true;
            for (int i = 0; i <= CAMERA_TICKS; i++) if (!safeCamera(candidate.at(i), target)) { valid = false; break; }
            if (valid) return candidate;
        }
        return null;
    }
    record CameraPath(Vec3 start, Vec3 end, Vec3 target) {
        Vec3 at(int age) { double t = Math.clamp(age / (double) CAMERA_TICKS, 0, 1); t = t*t*(3-2*t); return start.lerp(end, t); }
    }
    private boolean safeCamera(Vec3 at, Vec3 target) {
        var level = session.level();
        if (!DevilsMaps.contains(DevilsPlan.Zone.SP, DevilsWorldBuild.origin(DevilsPlan.Zone.SP), at)) return false;
        var box = new AABB(at.x-.25, at.y-.25, at.z-.25, at.x+.25, at.y+.25, at.z+.25);
        for (var pos : BlockPos.betweenClosed(BlockPos.containing(box.minX, box.minY, box.minZ), BlockPos.containing(box.maxX, box.maxY, box.maxZ)))
            if (!level.hasChunkAt(pos) || !level.getFluidState(pos).isEmpty()) return false;
        if (level.getBlockCollisions(null, box).iterator().hasNext()) return false;
        return level.clip(new ClipContext(at, target, ClipContext.Block.COLLIDER, ClipContext.Fluid.NONE,
                net.minecraft.world.phys.shapes.CollisionContext.empty())).getType() == HitResult.Type.MISS;
    }
    @Override public void tick(DevilsSession ignored, boolean paused) {
        if (closed) return;
        if (transport != null) {
            try { transport.tick(paused, session.players()); }
            catch (RuntimeException e) { transport.close(); problem("Transport update failed: " + e.getMessage()); }
            if (transport.closed()) { transport = null; transportPack = null; transportRiders.clear(); }
        }
        for (var view : List.copyOf(views.values())) {
            if (!session.member(view.player.getUUID()) || !eligible(view.player)) { view.close(); continue; }
            if (!paused) view.tick();
        }
        views.values().removeIf(v -> v.closed);
        if (intro != null) {
            var run = intro;
            if (run.boss.isRemoved() || !run.boss.isAlive() || run.tracker.isClosed()
                    || run.boss.reference().generation() != generation || phase != DevilsDirector.Phase.SP_INTRO) {
                run.cancel(); intro = null; releaseViews();
            } else if (!paused) {
                run.age++;
                if (run.age >= CAMERA_TICKS) releaseViews();
                if (!run.gate.ended) {
                    run.gate.clipElapsed(run.gate.generation, run.boss.getUUID(), run.age, run.clipTicks);
                    if (run.gate.ended) problem("Sepiks intro callback missing (viewers=" + run.tracker.playerCount() + "); finished after clip length");
                }
                if (run.gate.consume(generation, run.boss.getUUID())) {
                    releaseViews(); intro = null;
                    session.introFinished(generation); // normal animation completion only, never camera duration
                }
            }
        }
        if (paused) return;
        clock++;
        telegraphs.values().removeIf(t -> t.generation != generation);
        if (clock % 4 == 0) { telegraphs.values().forEach(this::drawTelegraph); renderBoss(); }
        if (clock % 10 == 0) waypoint();
    }
    /** Pure callback token: no elapsed-time path can mark an intro successful. */
    static final class IntroGate {
        final long generation; final UUID actor;
        boolean started, ended, cancelled, consumed;
        IntroGate(long generation, UUID actor) { this.generation = generation; this.actor = actor; }
        void naturalEnd(long expected, UUID id) { if (started && !cancelled && expected == generation && actor.equals(id)) ended = true; }
        /** BetterModel stops ticking a tracker with no viewers, so its play-once callback can be lost.
         *  Once the authored clip length has fully elapsed the awakening is over for everyone. */
        void clipElapsed(long expected, UUID id, int age, int clipTicks) {
            if (clipTicks > 0 && age >= clipTicks + CLIP_GRACE_TICKS) naturalEnd(expected, id);
        }
        boolean consume(long expected, UUID id) {
            if (!ended || cancelled || consumed || generation != expected || !actor.equals(id)) return false;
            consumed = true; return true;
        }
        void cancel() { cancelled = true; ended = false; }
    }
    private final class Intro {
        final DevilsMob boss; final EntityTracker tracker; final IntroGate gate; final int clipTicks; int age;
        Intro(DevilsMob boss, EntityTracker tracker, long generation, int clipTicks) {
            this.boss = boss; this.tracker = tracker; this.gate = new IntroGate(generation, boss.getUUID()); this.clipTicks = clipTicks;
        }
        void cancel() { gate.cancel(); if (!tracker.isClosed()) tracker.stopAnimation(INTRO_CLIP); }
    }
    @Override public void incoming(DevilsSession ignored, long gen, List<DevilsPlan.Slot> slots, int lead) {
        if (closed || gen != generation) return;
        for (var slot : slots) incomingSlots.put(slot.id(), slot);
    }
    /** Activity-specific choice only; flight/ownership is shared with other activities. */
    static boolean deliveredBySkiff(DevilsPlan.Slot slot) {
        if (!slot.ordinary() || slot.zone() == DevilsPlan.Zone.RF) return false;
        if (slot.zone() == DevilsPlan.Zone.RY && !"RY-approach-3".equals(slot.packId())) return false;
        return switch (slot.kind()) {
            case DREG, VANDAL, MARAUDER, CAPTAIN -> true;
            default -> false;
        };
    }
    private void considerTransport(DevilsPlan.Slot first, Vec3 pad) {
        if (!deliveredBySkiff(first) || !consideredTransports.add(first.packId())) return;
        if (transport != null && !transport.closed()) return; // At most one prop per session/zone.
        try {
            for (var route : DevilsTransportPaths.candidates(pad)) {
                var candidate = ModelTransport.create(session.level(), DevilsTransportPaths.MODEL, route,
                        DevilsPlan.TELEGRAPH_TICKS, 180, 56, 80);
                if (candidate.isEmpty()) continue;
                transport = candidate.orElseThrow(); transportPack = first.packId(); transportRiders.clear();
                transportDropStarted = false;
                transport.brightness(15, 15); // Match the tutorial skiff's readable presentation lighting.
                transport.animate("idle", true);
                incomingSlots.values().stream().filter(s -> Objects.equals(s.packId(), transportPack) && deliveredBySkiff(s))
                        .forEach(s -> transportRiders.add(s.id()));
                transport.tick(true, session.players());
                return;
            }
            problem("No loaded clear transport corridor for " + first.packId() + "; ground warning remains active");
        } catch (RuntimeException e) {
            if (transport != null) transport.close(); transport = null; transportPack = null; transportRiders.clear();
            problem("Transport creation failed: " + e.getMessage());
        }
    }
    @Override public void spawned(DevilsSession ignored, DevilsDirector.Spawn spawn, Vec3 at) {
        if (closed || spawn.ref().generation() != generation) return;
        incomingSlots.remove(spawn.slot().id());
        if (transport == null || transport.closed() || !Objects.equals(transportPack, spawn.slot().packId())
                || !transportRiders.remove(spawn.slot().id())) return;
        // Observe only accepted actors at their chosen pad; never move a combat actor to match the ship.
        if (!transportDropStarted) { transportDropStarted = true; transport.animate("drop", false); }
        Vec3 from = transport.position().add(0, -2.5, 0);
        if (from.distanceToSqr(at) <= 96 * 96) for (var p : session.players()) if (p.level() == session.level()) {
            for (int i = 0; i <= 12; i++) {
                var point = from.lerp(at.add(0, 1, 0), i / 12.0);
                session.level().sendParticles(p, ParticleTypes.END_ROD, true, false,
                        point.x, point.y, point.z, 1, .04, .04, .04, 0);
            }
        }
        if (transportRiders.isEmpty()) transport.delivered();
    }
    @Override public void spawnTelegraph(DevilsSession ignored, long gen, String slot, Vec3 at, boolean flying) {
        if (closed || gen != generation) return;
        var telegraph = new Telegraph(gen, at, flying);
        telegraphs.put(slot, telegraph);
        drawTelegraph(telegraph);
        var slotDefinition = incomingSlots.get(slot);
        if (slotDefinition != null) considerTransport(slotDefinition, at);
        for (var p : session.players()) if (p.level() == session.level() && p.distanceToSqr(at) < 96*96)
            sound(p, flying ? "entity.enderman.teleport" : "block.beacon.power_select", at, .45f, flying ? .65f : .8f);
    }
    @Override public void cancelSpawnTelegraph(long gen, String slot) {
        if (gen == generation) telegraphs.remove(slot);
    }
    private void drawTelegraph(Telegraph t) {
        for (var p : session.players()) if (p.level() == session.level() && p.distanceToSqr(t.at) < 96*96)
            for (int i = 0; i < 12; i++) {
                double angle = i * Math.PI / 6;
                session.level().sendParticles(p, t.flying ? ParticleTypes.REVERSE_PORTAL : ParticleTypes.ELECTRIC_SPARK,
                        true, false, t.at.x + Math.cos(angle)*1.7, t.at.y+.3, t.at.z+Math.sin(angle)*1.7, 1, 0, .05, 0, .01);
            }
    }
    private void waypoint() {
        String anchor = switch (phase) { case RY_CLEAR -> "RY.OUT"; case RF_DEVICE -> "RF.G";
            case RF_CLEAR -> "RF.EXIT"; case BL_CLEAR -> "BL.EXIT"; default -> null; };
        if (anchor == null) return;
        var zone = phase.zone(); Vec3 at = DevilsMaps.anchor(zone, anchor, DevilsWorldBuild.origin(zone)).pos().add(0, 1.4, 0);
        for (var p : session.players()) if (eligible(p) && !hidden(p)) session.level().sendParticles(p,
                ParticleTypes.END_ROD, true, false, at.x, at.y, at.z, 2, .08, .2, .08, .005);
    }
    private void renderBoss() {
        var snapshot = session.director().snapshot();
        var targets = snapshot.slots().stream().filter(s -> s.slot().kind().boss() && s.state() == DevilsDirector.SlotState.LIVE)
                .sorted(Comparator.comparing(s -> s.slot().id())).toList();
        for (var p : session.players()) {
            if (!eligible(p) || hidden(p) || targets.isEmpty()) { clearHud(p); continue; }
            hudAudience.put(p.getUUID(), p);
            for (int i = 0; i < targets.size(); i++) {
                var actor = targets.get(i); float y = 870 + i * 54;
                String title = switch (actor.slot().kind()) { case SEPIKS -> "몰락자 세픽스 프라임";
                    case WALKER -> "타락자 워커"; case BRIG -> "브리그 " + (actor.slot().index()+1); default -> ""; };
                if (actor.slot().kind() == DevilsPlan.Kind.SEPIKS && snapshot.phase().shieldPhase())
                    title += " · 보호막 연결 " + snapshot.shieldServitors() + "/3";
                label(p, "boss_name_"+i, title, 960, y-24, 19, 0xF4D990);
                float width = (float)(600 * Math.clamp(actor.health() / actor.slot().kind().health(), 0, 1));
                sprite(p, "boss_bg_"+i, 960, y+10, 600, 8, 0x252832);
                sprite(p, "boss_hp_"+i, 660 + width/2, y+10, Math.max(.01f, width), 6,
                        actor.slot().kind() == DevilsPlan.Kind.SEPIKS && snapshot.phase().shieldPhase() ? 0xA9C1E4 : 0xE9B957);
            }
            for (int i = targets.size(); i < 3; i++) for (var key : List.of("boss_name_", "boss_bg_", "boss_hp_")) DisplayHud.removeHud(p, HUD+key+i);
        }
        for (var p : List.copyOf(hudAudience.values())) if (!session.players().contains(p)) clearHud(p);
    }
    private void clearHud(ServerPlayer p) {
        hudAudience.remove(p.getUUID(), p);
        for (var id : List.copyOf(DisplayHud.getHuds(p).keySet())) if (id.startsWith(HUD+"boss_")) DisplayHud.removeHud(p, id);
    }
    private static void label(ServerPlayer p, String key, String value, float x, float y, float size, int color) {
        String id = HUD+key; var existing = DisplayHud.getHud(p,id);
        TextDisplayHud hud = existing instanceof TextDisplayHud t ? t : new TextDisplayHud();
        if (value.equals(hud.getExtraData("value")) && existing != null) return;
        hud.updateWhenDataChanged(false); Component text = ObjectiveTypography.text(value,color,true);
        hud.setText(text); hud.getTextDisplay().setText(Component.literal("\n").append(text));
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER); hud.setBackgroundColor(0); hud.setShadowToggle(true);
        hud.setLineWidth(2000); hud.setScale(size*2,size*2,1); hud.setLocation(x,y+size*1.2f,30);
        hud.setAlignment(DisplayHud.HudAlignment.CENTER); hud.setAboveHand(true); hud.setViewRange(1000);
        hud.setExtraData("value",value); if (existing==null) hud.spawn(p,id); hud.updateWhenDataChanged(true);hud.update();
    }
    private static void sprite(ServerPlayer p,String key,float x,float y,float width,float height,int color) {
        String id=HUD+key;var existing=DisplayHud.getHud(p,id);
        String state=x+":"+y+":"+width+":"+height+":"+color;
        if(existing!=null&&state.equals(existing.getExtraData("shape")))return;
        ItemDisplayHud hud=existing instanceof ItemDisplayHud item?item:new ItemDisplayHud();
        hud.updateWhenDataChanged(false);
        if(existing==null){var stack=new ItemStack(Items.PAPER);stack.set(DataComponents.ITEM_MODEL,DestinyGuardians.id("gui/hud/solid"));
            stack.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(List.of(),List.of(),List.of(),List.of(color)));
            hud.setItem(stack);hud.setItemTransform(ItemDisplayContext.NONE);hud.setAboveHand(true);hud.setViewRange(1000);hud.setAlignment(DisplayHud.HudAlignment.CENTER);}
        else { var stack=hud.getItem().copy();stack.set(DataComponents.CUSTOM_MODEL_DATA,new CustomModelData(List.of(),List.of(),List.of(),List.of(color)));hud.setItem(stack); }
        hud.setScale(width,height,1);hud.setLocation(x,y,25);hud.setExtraData("shape",state);
        if(existing==null)hud.spawn(p,id);hud.updateWhenDataChanged(true);hud.update();
    }
    private static void sound(ServerPlayer p,String event,Vec3 at,float volume,float pitch) {
        if(!p.hasDisconnected())p.connection.send(new ClientboundSoundPacket(Holder.direct(SoundEvent.createVariableRangeEvent(
                Identifier.withDefaultNamespace(event))),SoundSource.PLAYERS,at.x,at.y,at.z,volume,pitch,p.getRandom().nextLong()));
    }
    private final class View implements AutoCloseable {
        final ServerPlayer player; final CameraPath path; final Vec3 anchor; final Display.ItemDisplay camera; final GameType previousMode;
        final Identifier speedId=DestinyGuardians.id("devils_cinematic_speed"),jumpId=DestinyGuardians.id("devils_cinematic_jump");
        AttributeModifier speed,jump; boolean closed, mayfly, ownsMayfly, spoofed; int age;
        View(ServerPlayer p,CameraPath path){player=p;this.path=path;anchor=p.position();previousMode=p.gameMode.getGameModeForPlayer();camera=path==null?null:new Display.ItemDisplay(EntityTypes.ITEM_DISPLAY,session.level());}
        void begin(){
            var s=player.getAttribute(Attributes.MOVEMENT_SPEED);var j=player.getAttribute(Attributes.JUMP_STRENGTH);
            if(s!=null&&!s.hasModifier(speedId)){speed=new AttributeModifier(speedId,-1,AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);s.addTransientModifier(speed);}
            if(j!=null&&!j.hasModifier(jumpId)){jump=new AttributeModifier(jumpId,-1,AttributeModifier.Operation.ADD_MULTIPLIED_TOTAL);j.addTransientModifier(jump);}
            player.stopUsingItem();player.closeContainer();player.setDeltaMovement(Vec3.ZERO);CombatHud.remove(player);
            if(camera!=null){var at=path.at(0);camera.setPos(at);look(at);camera.setNoGravity(true);
                player.connection.send(new ClientboundAddEntityPacket(camera.getId(),camera.getUUID(),at.x,at.y,at.z,camera.getXRot(),camera.getYRot(),camera.getType(),0,Vec3.ZERO,camera.getYRot()));
                var metadata=camera.getEntityData().getNonDefaultValues();if(metadata!=null)player.connection.send(new ClientboundSetEntityDataPacket(camera.getId(),metadata));
                mayfly=player.getAbilities().mayfly;player.getAbilities().mayfly=true;ownsMayfly=true;spoof();player.setCamera(camera);
                // ServerPlayer.setCamera teleports the body in 26.3. Keep it on its safe entrance pad.
                player.connection.teleport(anchor.x,anchor.y,anchor.z,player.getYRot(),player.getXRot());
                sprite(player,"letter_top",960,48,2400,96,0);sprite(player,"letter_bottom",960,1032,2400,96,0);
            }
        }
        void spoof(){spoofed=true;player.connection.send(new ClientboundGameEventPacket(ClientboundGameEventPacket.CHANGE_GAME_MODE,GameType.SPECTATOR.getId()));
            var abilities=new Abilities();abilities.invulnerable=true;abilities.mayfly=true;abilities.flying=true;abilities.setFlyingSpeed(0);abilities.setWalkingSpeed(0);
            player.connection.send(new ClientboundPlayerAbilitiesPacket(abilities));}
        void look(Vec3 at){var d=path.target.subtract(at);camera.setYRot((float)Math.toDegrees(Math.atan2(-d.x,d.z)));camera.setXRot((float)-Math.toDegrees(Math.atan2(d.y,d.horizontalDistance())));}
        void tick(){
            if(closed)return;age++;
            if(player.position().distanceToSqr(anchor)>.04)player.connection.teleport(anchor.x,anchor.y,anchor.z,player.getYRot(),player.getXRot());
            player.setDeltaMovement(Vec3.ZERO);player.resetFallDistance();
            if(camera==null)return;
            if(age>=CAMERA_TICKS){close();return;}
            var at=path.at(age);if(!safeCamera(at,path.target)){close();return;}
            if(player.getCamera()!=camera){close();return;}
            camera.setPos(at);look(at);player.connection.send(ClientboundEntityPositionSyncPacket.of(camera));
            if(age%10==0)spoof();
        }
        @Override public void close(){
            if(closed)return;closed=true;LOCKS.remove(player.getUUID(),this);
            var s=player.getAttribute(Attributes.MOVEMENT_SPEED);if(s!=null&&speed!=null&&s.getModifier(speedId)==speed)s.removeModifier(speedId);
            var j=player.getAttribute(Attributes.JUMP_STRENGTH);if(j!=null&&jump!=null&&j.getModifier(jumpId)==jump)j.removeModifier(jumpId);
            boolean ownedCamera=camera!=null&&player.getCamera()==camera;
            if(ownsMayfly){if(player.gameMode.getGameModeForPlayer()==previousMode)player.getAbilities().mayfly=mayfly;ownsMayfly=false;}
            if(!player.hasDisconnected()){
                if(ownedCamera){
                    player.setCamera(player);
                    if(player.level()==session.level()&&player.isAlive()&&!GuardianDown.active(player)){
                        player.connection.teleport(anchor.x,anchor.y,anchor.z,player.getYRot(),player.getXRot());
                        player.setDeltaMovement(Vec3.ZERO);player.resetFallDistance();
                    }
                }
                if(spoofed&&!GuardianDown.active(player)){player.connection.send(new ClientboundGameEventPacket(ClientboundGameEventPacket.CHANGE_GAME_MODE,player.gameMode.getGameModeForPlayer().getId()));player.onUpdateAbilities();}
                if(camera!=null)player.connection.send(new ClientboundRemoveEntitiesPacket(camera.getId()));
            }
            if(camera!=null)camera.discard();
            DisplayHud.removeHud(player,HUD+"letter_top");DisplayHud.removeHud(player,HUD+"letter_bottom");
        }
    }
    private void releaseViews(){for(var v:List.copyOf(views.values()))v.close();views.clear();}
    @Override public void disconnected(ServerPlayer player){var v=views.remove(player.getUUID());if(v!=null)v.close();clearHud(player);}
    @Override public void cancelGeneration(long gen){
        if(gen!=generation)return;
        if(intro!=null){intro.cancel();intro=null;}releaseViews();telegraphs.clear();
        if(transport!=null){transport.close();transport=null;}
        transportPack=null;transportRiders.clear();incomingSlots.clear();consideredTransports.clear();
        for(var p:List.copyOf(hudAudience.values()))clearHud(p);
    }
    @Override public void close(){if(closed)return;closed=true;cancelGeneration(generation);}
    private void problem(String message){if(problems.add(message))DestinyGuardians.LOGGER.warn("[DevilsPresentation {}] {}",session.id(),message);}
}
