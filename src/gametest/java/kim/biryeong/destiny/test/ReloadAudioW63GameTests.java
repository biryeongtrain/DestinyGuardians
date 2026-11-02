package kim.biryeong.destiny.test;

import io.netty.buffer.Unpooled;
import kim.biryeong.destiny.ability.AbilityService;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.Guardians;
import kim.biryeong.destiny.hud.AmmoHud;
import kim.biryeong.destiny.hud.CombatHud;
import kim.biryeong.destiny.sound.DestinySounds;
import kim.biryeong.destiny.sound.ReloadAudio;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.core.Holder;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.RegistryFriendlyByteBuf;
import net.minecraft.network.chat.Component;
import net.minecraft.network.protocol.Packet;
import net.minecraft.network.protocol.game.*;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.sounds.SoundSource;
import net.minecraft.resources.Identifier;
import net.minecraft.world.entity.EntityTypes;
import net.minecraft.world.entity.ai.attributes.Attributes;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.level.GameType;
import net.minecraft.world.level.Level;
import net.minecraft.world.phys.Vec3;

import java.util.ArrayList;
import java.util.List;

/** Accepted gameplay reloads and packets captured from TestPlayers' EmbeddedChannels.
 * No native-input, client-rendering or acoustic-output evidence; no injected kill credit.
 * Owners remain outside the world's player/entity lists; explicit spectator listeners join
 * only level.players(), so fixtures stay stationary and never use a native connection.
 */
public final class ReloadAudioW63GameTests {
    private static final String FLOOR = "destiny-test:floor";
    private static final String PREFIX = "weapon.reload_w63.";
    private static boolean atEye(ClientboundSoundPacket sound,ServerPlayer owner) {
        var expected=DestinySounds.packet("weapon.shotgun.reload_insert",owner.getEyePosition(),SoundSource.PLAYERS,.8f,0);
        return sound.getX()==expected.getX() && sound.getY()==expected.getY() && sound.getZ()==expected.getZ();
    }

    private static Identifier key(ClientboundSoundPacket p) { return p.getSound().value().location(); }
    private static String base(String key) { return key.replaceFirst("\\.direct_[0-9]+$", ""); }

    private static void check(GameTestHelper h, boolean value, String message) {
        h.assertTrue(value, Component.literal(message));
    }

    private static ServerPlayer player(GameTestHelper h, double z) {
        var p = TestPlayers.hunter(h, Element.SOLAR, new Vec3(2.5, 1, z), -90, 0);
        p.setAttached(WeaponLoadout.ENABLED, true);
        p.setOnGround(true);
        TestCleanup.register(h, () -> {
            WeaponRuntime.cleanup(p);
            ReloadAudio.stop(p);
            CombatHud.remove(p);
            TestPlayers.remove(p);
        });
        return p;
    }

    private static ServerPlayer listener(GameTestHelper h, Vec3 position) {
        var p = TestPlayers.create(h, position, 0, 0);
        p.setGameMode(GameType.SPECTATOR);
        h.getLevel().players().add(p);
        TestCleanup.register(h, () -> {
            h.getLevel().players().remove(p);
            // Dimension-eligibility fixtures change only this unregistered fake's level.
            p.setServerLevel(h.getLevel());
            TestPlayers.remove(p);
        });
        TestPlayers.drain(p);
        return p;
    }

    private static WeaponCatalog.Entry entry(ItemStack s) { return WeaponItems.entry(s).orElseThrow(); }
    private static WeaponProfile profile(ItemStack s) { return WeaponProfile.forEntry(entry(s)); }
    private static WeaponMagazine ammo(ItemStack s) { return WeaponItems.magazine(s, profile(s)); }

    private static ItemStack equip(ServerPlayer p, String id, int rounds, int reserve) {
        var e = WeaponCatalog.find(id).orElseThrow();
        var s = WeaponItems.create(e);
        WeaponItems.save(s, new WeaponMagazine(WeaponProfile.forEntry(e), rounds, reserve));
        int slot = WeaponCharacteristics.of(e).slot().hotbar();
        p.getInventory().setItem(slot, s);
        p.getInventory().setSelectedSlot(slot);
        WeaponRuntime.tickPlayer(p);
        TestPlayers.drain(p);
        return s;
    }

    private static <T> List<T> packets(List<Packet<?>> queued, Class<T> type) {
        return queued.stream().filter(type::isInstance).map(type::cast).toList();
    }

    private static List<ClientboundSoundPacket> reloadSounds(List<Packet<?>> queued) {
        return packets(queued, ClientboundSoundPacket.class).stream()
                .filter(p -> p.getSound().value().location().getNamespace().equals("destiny")
                        && (p.getSound().value().location().getPath().startsWith(PREFIX)
                        || p.getSound().value().location().getPath().startsWith("weapon.reload_w83.")
                        || p.getSound().value().location().getPath().startsWith("weapon.reload_w84.")
                        || java.util.Set.of("weapon.reload_w102.aishas_embrace.46", "weapon.reload_w102.blast_furnace.24",
                                "weapon.reload_w102.blast_furnace.43", "weapon.reload_w102.chattering_bone.24",
                                "weapon.reload_w102.chattering_bone.34", "weapon.reload_w102.retrofit_escapade.90")
                                .contains(base(p.getSound().value().location().getPath())))).toList();
    }

    private static boolean removed(List<Packet<?>> queued, Identifier id) {
        return packets(queued, ClientboundStopSoundPacket.class).stream()
                .anyMatch(p -> id.equals(p.getName()) && p.getSource()==SoundSource.PLAYERS);
    }

    private static long removalCount(List<Packet<?>> queued, Identifier id) {
        return packets(queued, ClientboundStopSoundPacket.class).stream()
                .filter(p -> id.equals(p.getName()) && p.getSource()==SoundSource.PLAYERS).count();
    }

    private static void noGlobalStop(GameTestHelper h, List<Packet<?>> queued) {
        check(h, packets(queued, ClientboundStopSoundPacket.class).stream().allMatch(p ->
                        p.getName()!=null && p.getName().getPath().contains(".direct_") && p.getSource()==SoundSource.PLAYERS),
                "Stops target only a reserved reload alias in PLAYERS, never a shared or category-wide sound");
    }

    private static void noAudio(GameTestHelper h, List<Packet<?>> queued) {
        check(h, packets(queued, ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(queued, ClientboundSoundPacket.class).isEmpty()
                        && packets(queued, ClientboundStopSoundPacket.class).isEmpty(),
                "Denied/query-only path queues no entity-bound or legacy sound");
        noGlobalStop(h, queued);
    }

    private static ClientboundSoundPacket started(GameTestHelper h, ServerPlayer owner,
                                                         List<Packet<?>> queued) {
        var sounds = reloadSounds(queued);
        check(h, sounds.size() == 1, "Exactly one timed reload sound on the real connection");
        var sound = sounds.getFirst();
        check(h, packets(queued,ClientboundSoundEntityPacket.class).isEmpty()
                        && packets(queued,ClientboundAddEntityPacket.class).isEmpty(),
                "Reload starts directly without an entity spawn dependency");
        check(h, atEye(sound,owner),
                "Direct sound starts at the quantized owner eye position");
        check(h, sound.getSound().kind() == Holder.Kind.DIRECT && sound.getPitch() == 1f
                        && sound.getVolume() == .8f && sound.getSource() == SoundSource.PLAYERS,
                "Inline fixed-pitch reload event uses the authored player sound channel");
        String old = DestinySounds.weaponKey(entry(owner.getMainHandItem()), "reload");
        check(h, packets(queued, ClientboundSoundPacket.class).stream().noneMatch(p ->
                        p.getSound().value().location().getPath().equals(old)),
                "Accepted timed reload does not also replay its original positional clip");
        noGlobalStop(h, queued);
        return sound;
    }

    private static ClientboundSoundPacket start(GameTestHelper h, ServerPlayer p) {
        TestPlayers.drain(p);
        check(h, WeaponRuntime.reload(p), "Real authoritative reload is accepted");
        return started(h, p, TestPlayers.outbound(p));
    }

    @GameTest(structure = FLOOR, maxTicks = 240, environment = "destiny-test:w90_isolated")
    public void acceptedDirectReloadPaysAmmoOnlyAtDeadlineThenStopsOwnedAlias(GameTestHelper h) {
        var p = player(h, 6.5);
        var gun = equip(p, "beloved", 1, 12);
        var before = ammo(gun);
        int ticks = profile(gun).firstReloadTicks();
        var sound = start(h, p);
        check(h, !profile(gun).shellReload() && !profile(gun).infiniteReserve()
                        && ammo(gun).rounds() == before.rounds() && ammo(gun).reserve() == before.reserve(),
                "Starting audio neither fills the finite magazine nor spends reserve");
        var queued = new ArrayList<Packet<?>>();
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); queued.addAll(TestPlayers.outbound(p)); });
        h.runAfterDelay(ticks - 1, () -> {
            WeaponRuntime.tickPlayer(p); queued.addAll(TestPlayers.outbound(p));
            check(h, WeaponRuntime.reloading(p) && ammo(gun).rounds() == before.rounds()
                            && ammo(gun).reserve() == before.reserve() && !removed(queued, key(sound)),
                    "One tick before the actual deadline, ammo and sound session remain unchanged");
        });
        h.runAfterDelay(ticks, () -> {
            WeaponRuntime.tickPlayer(p); queued.addAll(TestPlayers.outbound(p));
            int moved = profile(gun).magazine() - before.rounds();
            check(h, !WeaponRuntime.reloading(p) && ammo(gun).rounds() == profile(gun).magazine()
                            && ammo(gun).reserve() == before.reserve() - moved && ammo(gun).total() == before.total(),
                    "Only real finishReload transfers exactly the missing finite rounds at its deadline");
            check(h, removalCount(queued, key(sound)) == 1 && reloadSounds(queued).isEmpty(),
                    "Exact gameplay completion removes the sound session once, without replay");
            noGlobalStop(h, queued);
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void queriesTicksAndRejectedDuplicateReloadsNeverReplayAcceptedAudio(GameTestHelper h) {
        var p = player(h, 6.5);
        var gun = equip(p, "duke_mk_44", 8, 0);
        start(h, p);
        int rounds = ammo(gun).rounds(), reserve = ammo(gun).reserve();
        for (int i = 0; i < 12; i++) {
            check(h, WeaponRuntime.reloading(p) && WeaponRuntime.ammunition(p).orElseThrow().reloading(),
                    "Read-only projections observe the live reload");
            AmmoHud.current(p); CombatHud.update(p); WeaponRuntime.tickPlayer(p);
            check(h, !WeaponRuntime.reload(p), "Already-running reload request is rejected");
        }
        noAudio(h, TestPlayers.outbound(p));
        check(h, ammo(gun).rounds() == rounds && ammo(gun).reserve() == reserve,
                "Repeated observation and rejected starts cannot grant ammunition");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void fullMagazineAndFiniteNoReserveDenialsQueueNoSoundOrEntity(GameTestHelper h) {
        var full = player(h, 3.5);
        int capacity = WeaponProfile.forEntry(WeaponCatalog.find("beloved").orElseThrow()).magazine();
        var a = equip(full, "beloved", capacity, 12);
        var emptyReserve = player(h, 9.5);
        var b = equip(emptyReserve, "beloved", 0, 0);
        var savedA = a.copy(); var savedB = b.copy();
        for (var p : List.of(full, emptyReserve)) {
            check(h, !WeaponRuntime.reload(p) && !WeaponRuntime.reloading(p), "Ineligible actual reload is denied");
            WeaponRuntime.tickPlayer(p);
            var queued = TestPlayers.outbound(p);
            noAudio(h, queued);
            check(h, packets(queued, ClientboundAddEntityPacket.class).isEmpty(), "No entity spawn for a denied reload");
        }
        check(h, ItemStack.matches(a, savedA) && ItemStack.matches(b, savedB), "Denied reloads leave actual stacks unchanged");
        h.succeed();
    }

    private static List<String> shellCues(List<Packet<?>> queued, ServerPlayer owner) {
        // Concurrent structures are within the audible radius. Attribute positional cues
        // to this stationary fake's quantized source, rather than another test's shotgun.
        var origin = DestinySounds.packet("weapon.shotgun.reload_insert", owner.getEyePosition(), SoundSource.PLAYERS, .8f, 0);
        var cues = new ArrayList<String>();
        for (var packet : queued) {
            if (packet instanceof ClientboundSoundPacket p
                    && p.getX() == origin.getX() && p.getY() == origin.getY() && p.getZ() == origin.getZ()) {
                String key=p.getSound().value().location().toString();
                if(key.startsWith("destiny:weapon.shotgun.reload"))cues.add(base(key));
            }
        }
        return cues;
    }

    @GameTest(structure = FLOOR, maxTicks = 120, environment = "destiny-test:w90_isolated")
    public void shotgunReserveExhaustionClosesOnlyOnFinalPaidInsert(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(p, "first_in_last_out", 0, 2);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        check(h, WeaponRuntime.reload(p), "Shell reload accepted");
        check(h, shellCues(TestPlayers.outbound(hearer), p).isEmpty(), "No uncancellable whole clip at start");
        int first = profile(gun).firstReloadTicks(), interval = profile(gun).reloadTicks();
        var cues = new ArrayList<String>();
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); cues.addAll(shellCues(TestPlayers.outbound(hearer), p)); });
        h.runAfterDelay(first + 1, () -> {
            check(h, ammo(gun).rounds() == 1 && WeaponRuntime.reloading(p), "First paid shell keeps loading");
            check(h, cues.equals(List.of("destiny:weapon.shotgun.reload_insert")), "Intermediate shell never closes");
        });
        h.runAfterDelay(first + interval + 4, () -> {
            check(h, ammo(gun).rounds() == 2 && ammo(gun).reserve() == 0 && !WeaponRuntime.reloading(p),
                    "Reserve exhaustion is a natural completion with exactly two transfers");
            check(h, cues.equals(List.of("destiny:weapon.shotgun.reload_insert", "destiny:weapon.shotgun.reload_finish")),
                    "One insertion followed by exactly one final insertion/close cue, never legacy reload");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 80, environment = "destiny-test:w90_isolated")
    public void shotgunOneMissingShellClosesOnceAndDuplicateTicksCannotReplayIt(GameTestHelper h) {
        var p = player(h, 6.5);
        var f = WeaponProfile.forEntry(WeaponCatalog.find("first_in_last_out").orElseThrow());
        var gun = equip(p, "first_in_last_out", f.magazine() - 1, 10);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        check(h, WeaponRuntime.reload(p) && !WeaponRuntime.reload(p), "Exactly one accepted partial reload");
        var cues = new ArrayList<String>();
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); WeaponRuntime.tickPlayer(p);
            cues.addAll(shellCues(TestPlayers.outbound(hearer), p)); });
        h.runAfterDelay(f.firstReloadTicks() + 5, () -> {
            check(h, ammo(gun).rounds() == f.magazine() && ammo(gun).reserve() == 9,
                    "Only the missing shell is credited");
            check(h, cues.equals(List.of("destiny:weapon.shotgun.reload_finish")),
                    "Final cue includes the last insertion and close, with no duplicate");
            h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 160, environment = "destiny-test:w90_isolated")
    public void shotgunMidReloadShotNeverSchedulesOrPlaysClosingAction(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(p, "first_in_last_out", 2, 10);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        check(h, WeaponRuntime.reload(p), "Interruptible shell reload accepted");
        int first = profile(gun).firstReloadTicks(), interval = profile(gun).reloadTicks();
        var cues = new ArrayList<String>();
        h.onEachTick(() -> { WeaponRuntime.tickPlayer(p); cues.addAll(shellCues(TestPlayers.outbound(hearer), p)); });
        h.runAfterDelay(first + 1, () -> {
            check(h, ammo(gun).rounds() == 3 && WeaponRuntime.reloading(p), "One shell inserted before interruption");
            check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == 2 && !WeaponRuntime.reloading(p),
                    "Fresh shot interrupts the next phase and spends exactly one shell");
            WeaponRuntime.releaseUse(p, gun);
        });
        h.runAfterDelay(first + interval * 3 + 5, () -> {
            check(h, ammo(gun).rounds() == 2 && ammo(gun).reserve() == 9, "Interrupted phase grants no ammo");
            check(h, cues.equals(List.of("destiny:weapon.shotgun.reload_insert")),
                    "Past the old clip/deadlines: no final close, no full reload, no delayed insert");
            noGlobalStop(h, TestPlayers.outbound(hearer)); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 90, environment = "destiny-test:w90_isolated")
    public void shotgunFinalTailSurvivesReloadFlagThenShotCancelsOnlyItsOwner(GameTestHelper h) {
        var a=player(h,3.5); var b=player(h,9.5);
        var f=WeaponProfile.forEntry(WeaponCatalog.find("first_in_last_out").orElseThrow());
        var gunA=equip(a,"first_in_last_out",f.magazine()-1,10);
        var gunB=equip(b,"first_in_last_out",f.magazine()-1,10);
        var hearer=listener(h,new Vec3(3.5,1,6.5));
        check(h,WeaponRuntime.reload(a)&&WeaponRuntime.reload(b),"Two actual final-shell reloads accepted");
        var queued=new ArrayList<Packet<?>>();
        h.onEachTick(() -> {WeaponRuntime.tickPlayer(a);WeaponRuntime.tickPlayer(b);
            queued.addAll(TestPlayers.outbound(hearer));});
        h.runAfterDelay(f.firstReloadTicks()+1,() -> {
            check(h,!WeaponRuntime.reloading(a)&&!WeaponRuntime.reloading(b),"Last shell completed both real reloads");
            var sounds=packets(queued,ClientboundSoundPacket.class).stream()
                    .filter(p -> base(key(p).getPath()).equals("weapon.shotgun.reload_finish")).toList();
            var idA=sounds.stream().filter(p -> atEye(p,a))
                    .map(ReloadAudioW63GameTests::key).findFirst().orElseThrow();
            var idB=sounds.stream().filter(p -> atEye(p,b))
                    .map(ReloadAudioW63GameTests::key).findFirst().orElseThrow();
            check(h,!idA.equals(idB)&&!removed(queued,idA)&&!removed(queued,idB),"Natural finish tail is not removed by the inactive reload flag");
            check(h,!WeaponRuntime.reload(b),"Full-magazine reload denial leaves B's tail alone");
            WeaponRuntime.tickPlayer(b);
            check(h,!removed(TestPlayers.outbound(hearer),idB),"Denied action does not retire the natural tail");
            check(h,WeaponRuntime.beginUse(a)&&ammo(gunA).rounds()==f.magazine()-1,"A fires after its last shell");
            WeaponRuntime.releaseUse(a,gunA);
            var cancelled=TestPlayers.outbound(hearer);
            check(h,removalCount(cancelled,idA)==1&&!removed(cancelled,idB),"Shot retires A's tail before its delayed clack, leaving B audible");
            var removal=packets(cancelled,ClientboundStopSoundPacket.class).stream().filter(p -> idA.equals(p.getName())).findFirst().orElseThrow();
            var firing=packets(cancelled,ClientboundSoundPacket.class).stream().filter(p -> p.getSound().value().location().getPath().equals("weapon.shotgun.fire")).findFirst().orElseThrow();
            check(h,cancelled.indexOf(removal)<cancelled.indexOf(firing),"Tail retirement packet precedes the accepted fire sound");
            noGlobalStop(h,cancelled);
            h.runAfterDelay(30,() -> {
                check(h,removed(queued,idB)&&!removed(queued,idA),"B expires naturally, without a repeated removal of A");
                check(h,ammo(gunB).rounds()==f.magazine()&&ammo(gunB).reserve()==9,"Audio lifetime never changes paid ammunition");
                noGlobalStop(h,queued);h.succeed();
            });
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void sameEventOwnersUseDistinctAliasesAndCancelOnlyOneWhileOtherContinues(GameTestHelper h) {
        var a = player(h, 3.5); var gunA = equip(a, "duke_mk_44", 8, 0);
        var b = player(h, 9.5); var gunB = equip(b, "duke_mk_44", 8, 0);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        var soundA = start(h, a); var soundB = start(h, b);
        check(h, !key(soundA).equals(key(soundB))
                        && base(key(soundA).getPath()).equals(base(key(soundB).getPath())),
                "Same event across two owners has distinct client sound aliases");
        var heard = TestPlayers.outbound(hearer);
        check(h, reloadSounds(heard).stream().anyMatch(p -> key(p).equals(key(soundA)))
                        && reloadSounds(heard).stream().anyMatch(p -> key(p).equals(key(soundB))),
                "One nearby spectator actually receives both same-key reloads");
        WeaponRuntime.cancelUseForSkill(a);
        var cancelled = TestPlayers.outbound(hearer);
        check(h, removalCount(cancelled, key(soundA)) == 1 && !removed(cancelled, key(soundB))
                        && !WeaponRuntime.reloading(a) && WeaponRuntime.reloading(b),
                "Cancelling owner A removes only A while B retains its actual reload");
        noGlobalStop(h, cancelled);
        b.setPos(b.position().add(1, 0, 0)); WeaponRuntime.tickPlayer(b);
        var following = TestPlayers.outbound(hearer);
        check(h, packets(following, ClientboundTeleportEntityPacket.class).isEmpty()
                        && reloadSounds(following).isEmpty() && !removed(following, key(soundB)),
                "Movement leaves B's one-shot positional sound playing without entity updates");
        noGlobalStop(h, following);
        h.runAfterDelay(profile(gunB).firstReloadTicks(), () -> {
            WeaponRuntime.tickPlayer(a); WeaponRuntime.tickPlayer(b);
            var finished = TestPlayers.outbound(hearer);
            check(h, ammo(gunA).rounds() == 8 && ammo(gunB).rounds() == 9 && !WeaponRuntime.reloading(b)
                            && removed(finished, key(soundB)),
                    "B alone completes; A's cancelled deadline never fills or removes B");
            noGlobalStop(h, finished); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void validatedSameTickSlotAwayAndBackCancelsAudioAndCannotGhostRefill(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(p, "duke_mk_44", 8, 0);
        var sound = start(h, p); int slot = p.getInventory().getSelectedSlot();
        long tick = h.getLevel().getServer().getTickCount();
        p.getInventory().setItem(7, new ItemStack(Items.STONE));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(7));
        p.connection.handleSetCarriedItem(new ServerboundSetCarriedItemPacket(slot));
        WeaponRuntime.tickPlayer(p);
        var queued = TestPlayers.outbound(p);
        check(h, h.getLevel().getServer().getTickCount() == tick && p.getMainHandItem() == gun
                        && !WeaponRuntime.reloading(p) && removalCount(queued, key(sound)) == 1,
                "Validated native packet handler observes same-tick stow/return and removes the captured sound session");
        noGlobalStop(h, queued);
        h.runAfterDelay(profile(gun).firstReloadTicks() + 1, () -> {
            WeaponRuntime.tickPlayer(p); var later = TestPlayers.outbound(p);
            check(h, ammo(gun).rounds() == 8 && !WeaponRuntime.reloading(p)
                            && reloadSounds(later).isEmpty() && !removed(later, key(sound)),
                    "Returned stack never replays audio, receives a ghost refill or repeats removal");
            noGlobalStop(h, later); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void ownerCleanupAndDeadOwnerTickStopOnlyTheirCapturedSounds(GameTestHelper h) {
        var a = player(h, 3.5); var gunA = equip(a, "duke_mk_44", 8, 0);
        var b = player(h, 9.5); var gunB = equip(b, "duke_mk_44", 8, 0);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        var soundA = start(h, a); var soundB = start(h, b); TestPlayers.drain(hearer);
        WeaponRuntime.cleanup(a);
        var cleanup = TestPlayers.outbound(hearer);
        check(h, removed(cleanup, key(soundA)) && !removed(cleanup, key(soundB)) && WeaponRuntime.reloading(b),
                "Owner cleanup removes only that owner's sound session");
        noGlobalStop(h, cleanup);
        b.setHealth(0); WeaponRuntime.tickPlayer(b);
        var death = TestPlayers.outbound(hearer);
        check(h, removed(death, key(soundB)) && !removed(death, key(soundA)) && !WeaponRuntime.reloading(b),
                "Dead-owner validation retires B's sound session and gameplay reload");
        noGlobalStop(h, death);
        WeaponRuntime.cleanup(a); WeaponRuntime.tickPlayer(b);
        var repeated = TestPlayers.outbound(hearer);
        check(h, !removed(repeated, key(soundA)) && !removed(repeated, key(soundB)), "Repeated retirement is idempotent");
        noGlobalStop(h, repeated);
        h.runAfterDelay(profile(gunA).firstReloadTicks() + 1, () -> {
            WeaponRuntime.tickPlayer(a); WeaponRuntime.tickPlayer(b);
            check(h, ammo(gunA).rounds() == 8 && ammo(gunB).rounds() == 8, "Retired deadlines cannot fill either actual stack");
            var later = TestPlayers.outbound(hearer);
            check(h, reloadSounds(later).stream().noneMatch(packet ->
                            (packet.getX()==soundA.getX() && packet.getY()==soundA.getY() && packet.getZ()==soundA.getZ())
                            || (packet.getX()==soundB.getX() && packet.getY()==soundB.getY() && packet.getZ()==soundB.getZ())),
                    "Retired sound sessions never replay; unrelated parallel fixtures may still be audible");
            noGlobalStop(h, later); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void acceptedSuperAndMarksmanDodgeRetireReloadAudioWithoutReplayingIt(GameTestHelper h) {
        var superOwner = player(h, 3.5); var superGun = equip(superOwner, "duke_mk_44", 8, 0);
        var dodgeOwner = player(h, 9.5); var dodgeGun = equip(dodgeOwner, "duke_mk_44", 8, 0);
        var superSound = start(h, superOwner); var dodgeSound = start(h, dodgeOwner);
        Guardians.data(superOwner).setSuperEnergy(1);
        check(h, AbilityService.use(superOwner, AbilitySlot.SUPER) == AbilityService.Result.OK, "Real equipped charged super accepted");
        var superPackets = TestPlayers.outbound(superOwner);
        check(h, removed(superPackets, key(superSound)) && reloadSounds(superPackets).isEmpty()
                        && !WeaponRuntime.reloading(superOwner) && ammo(superGun).rounds() == 8,
                "Accepted super cancels its actual reload and removes its sound session without granting ammo");
        noGlobalStop(h, superPackets);
        check(h, AbilityService.use(dodgeOwner, AbilitySlot.CLASS_ABILITY) == AbilityService.Result.OK, "Real equipped Marksman's Dodge accepted");
        var dodgePackets = TestPlayers.outbound(dodgeOwner);
        check(h, removed(dodgePackets, key(dodgeSound)) && reloadSounds(dodgePackets).isEmpty()
                        && !WeaponRuntime.reloading(dodgeOwner) && ammo(dodgeGun).rounds() == profile(dodgeGun).magazine(),
                "Accepted dodge retires timed audio; only its existing gameplay effect fills the magazine");
        noGlobalStop(h, dodgePackets);
        AbilityService.endSuper(superOwner);
        h.runAfterDelay(profile(superGun).firstReloadTicks() + 1, () -> {
            WeaponRuntime.tickPlayer(superOwner); WeaponRuntime.tickPlayer(dodgeOwner);
            check(h, ammo(superGun).rounds() == 8 && ammo(dodgeGun).rounds() == profile(dodgeGun).magazine(),
                    "Neither cancelled timed deadline gives a later additional transfer");
            check(h, reloadSounds(TestPlayers.outbound(superOwner)).isEmpty()
                            && reloadSounds(TestPlayers.outbound(dodgeOwner)).isEmpty(), "Skill cleanup never replays a reload clip");
            h.succeed();
        });
    }

    private static void precisionKill(GameTestHelper h, ServerPlayer p) {
        double z = p.getZ() - h.absoluteVec(Vec3.ZERO).z;
        var target = h.spawn(EntityTypes.HUSK, new Vec3(8.5, 1, z));
        target.setNoAi(true); target.setNoGravity(true); target.setPersistenceRequired();
        target.getAttribute(Attributes.MAX_HEALTH).setBaseValue(1000);
        target.getAttribute(Attributes.ARMOR).setBaseValue(0);
        target.getAttribute(Attributes.KNOCKBACK_RESISTANCE).setBaseValue(1); target.setHealth(1);
        TestCleanup.register(h, target::discard);
        var origin = h.absoluteVec(Vec3.ZERO); var box = target.getBoundingBox();
        check(h, box.minX > origin.x && box.maxX < origin.x + 16 && box.minY > origin.y
                        && box.maxY < origin.y + 8 && box.minZ > origin.z && box.maxZ < origin.z + 12,
                "Entire head-Husk fixture stays inside the 16x8x12 test bounds");
        WeaponAiming.cleanup(p); p.setYRot(-90); p.setYHeadRot(-90); p.setXRot(0); WeaponAiming.tick(p);
        check(h, p.getEyeY() >= box.maxY - box.getYsize() * .25 && p.getEyeY() < box.maxY,
                "Player-relative y=1 horizontal eye ray crosses Husk upper-quarter precision geometry");
        var gun = p.getMainHandItem(); int rounds = ammo(gun).rounds();
        // Horizontal look alone no longer guarantees a headshot: the paid ray samples dispersion.
        // Inspect one deterministic sample, then replay it through the real paid emission.
        p.getRandom().setSeed(0x5DEECE66DL);
        var from = p.getEyePosition();
        var direction = WeaponAiming.direction(p);
        var hit = box.clip(from, from.add(direction.scale(10))).orElse(null);
        check(h, hit != null && WeaponPrecision.critical(target, from, hit, WeaponBallistics.of(entry(gun)).precision()),
                "The sampled firing ray crosses the intended Husk precision region");
        p.getRandom().setSeed(0x5DEECE66DL);
        check(h, WeaponRuntime.beginUse(p) && ammo(gun).rounds() == rounds - 1,
                "Accepted actual hitscan pays its real cartridge");
        WeaponRuntime.releaseUse(p, gun);
        check(h, target.isDeadOrDying() && target.getHealth() == 0, "Actual one-HP precision final blow, never injected credit");
        target.discard();
    }

    @GameTest(structure = FLOOR, maxTicks = 85, environment = "destiny-test:w90_isolated")
    public void actualPrecisionKillSelectsThirtyThreeTickOutlawClipAgainstFiftyNineTickBaseAtPitchOne(GameTestHelper h) {
        var fast = player(h, 3.5); var fastGun = equip(fast, "duke_mk_44", 9, 0);
        check(h, WeaponPerks.select(fastGun, OutlawProfile.ID), "Select Duke's actual official Outlaw trait");
        var base = player(h, 9.5); var baseGun = equip(base, "duke_mk_44", 9, 0);
        precisionKill(h, fast); precisionKill(h, base);
        check(h, WeaponOutlaw.remaining(fast) == 120 && WeaponOutlaw.remaining(base) == 0,
                "Only the selected real precision-kill trait arms Outlaw");
        var fastSound = start(h, fast); var baseSound = start(h, base);
        check(h, WeaponRuntime.ammunition(fast).orElseThrow().reloadDuration() == 33
                        && WeaponRuntime.ammunition(base).orElseThrow().reloadDuration() == 59
                        && !fastSound.getSound().value().location().equals(baseSound.getSound().value().location())
                        && fastSound.getPitch() == 1f && baseSound.getPitch() == 1f,
                "Actual captured 33/59-tick plans choose different timed clips without pitch shifting");
        var fastPackets = new ArrayList<Packet<?>>(); var basePackets = new ArrayList<Packet<?>>();
        h.onEachTick(() -> {
            WeaponRuntime.tickPlayer(fast); WeaponRuntime.tickPlayer(base);
            fastPackets.addAll(TestPlayers.outbound(fast)); basePackets.addAll(TestPlayers.outbound(base));
        });
        h.runAfterDelay(32, () -> check(h, ammo(fastGun).rounds() == 9 && ammo(baseGun).rounds() == 8
                        && !removed(fastPackets, key(fastSound)) && !removed(basePackets, key(baseSound)),
                "Credit24 has occurred but neither full-duration sound session retires at32"));
        h.runAfterDelay(33, () -> {
            WeaponRuntime.tickPlayer(fast); WeaponRuntime.tickPlayer(base);
            fastPackets.addAll(TestPlayers.outbound(fast)); basePackets.addAll(TestPlayers.outbound(base));
            check(h, ammo(fastGun).rounds() == 9 && ammo(baseGun).rounds() == 8
                            && !WeaponRuntime.reloading(fast) && WeaponRuntime.reloading(base)
                            && removed(fastPackets, key(fastSound)) && !removed(basePackets, key(baseSound)),
                    "Only earned Outlaw reload completes and removes its timed sound session at tick 33");
        });
        h.runAfterDelay(58, () -> check(h, ammo(baseGun).rounds() == 9 && !removed(basePackets, key(baseSound)),
                "Base credit42 retains its full-duration sound session through tick58"));
        h.runAfterDelay(59, () -> {
            WeaponRuntime.tickPlayer(base); basePackets.addAll(TestPlayers.outbound(base));
            check(h, ammo(baseGun).rounds() == 9 && !WeaponRuntime.reloading(base)
                            && removalCount(fastPackets, key(fastSound)) == 1 && removalCount(basePackets, key(baseSound)) == 1
                            && ammo(fastGun).reserve() == 0 && ammo(baseGun).reserve() == 0,
                    "Base completes at 59; both primary reserves remain infinite without fabricated finite ammo");
            noGlobalStop(h, fastPackets); noGlobalStop(h, basePackets); h.succeed();
        });
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void movingSourceDoesNotReplayOrTeleportDirectSound(GameTestHelper h) {
        var p = player(h, 6.5); var gun = equip(p, "duke_mk_44", 8, 0);
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        var sound = start(h, p); TestPlayers.drain(hearer);
        var saved = ammo(gun);
        for (var relative : List.of(new Vec3(3.5, 1, 6.5), new Vec3(4.5, 2, 7.5))) {
            p.setPos(h.absoluteVec(relative)); var position = p.position();
            WeaponRuntime.tickPlayer(p);
            for (var receiver : List.of(p, hearer)) {
                var queued = TestPlayers.outbound(receiver);
                check(h, packets(queued,ClientboundTeleportEntityPacket.class).isEmpty(),
                        "Movement never sends a synthetic entity teleport");
                check(h, reloadSounds(queued).isEmpty() && !removed(queued, key(sound))
                                && packets(queued, ClientboundPlayerPositionPacket.class).isEmpty(),
                        "Following neither replays audio, despawns early nor corrects a player body");
                noGlobalStop(h, queued);
            }
            check(h, p.position().equals(position)
                            && ammo(gun).rounds() == saved.rounds() && ammo(gun).reserve() == saved.reserve(),
                    "Movement audio adds no world entity, player displacement or ammunition cost");
        }
        WeaponRuntime.tickPlayer(p);
        check(h, packets(TestPlayers.outbound(p), ClientboundTeleportEntityPacket.class).isEmpty(),
                "Unchanged source position produces no redundant entity teleport");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void actualBaseReloadPacketsForEverySupportedCatalogWeaponRoundTripInlineVanillaCodec(GameTestHelper h) {
        int tested = 0;
        for (var e : WeaponCatalog.all()) {
            var f = WeaponProfile.forEntry(e);
            if (f.mode() == WeaponProfile.Mode.MELEE || f.shellReload() || e.family().equals("bow")) continue;
            var p = player(h, 6.5); equip(p, e.id(), 0, f.infiniteReserve() ? 0 : f.magazine());
            var packet = start(h, p);
            check(h, WeaponRuntime.ammunition(p).orElseThrow().reloadDuration() == f.firstReloadTicks(),
                    "Accepted catalog base phase selects its real duration: " + e.id());
            var buffer = new RegistryFriendlyByteBuf(Unpooled.buffer(), h.getLevel().registryAccess());
            try {
                ClientboundSoundPacket.STREAM_CODEC.encode(buffer, packet);
                var decoded = ClientboundSoundPacket.STREAM_CODEC.decode(buffer);
                check(h, decoded.getSound().kind() == Holder.Kind.DIRECT
                                && decoded.getSound().value().location().equals(packet.getSound().value().location())
                                && decoded.getX()==packet.getX() && decoded.getY()==packet.getY() && decoded.getZ()==packet.getZ() && decoded.getSource() == packet.getSource()
                                && decoded.getVolume() == packet.getVolume() && decoded.getPitch() == 1f
                                && decoded.getSeed() == packet.getSeed() && buffer.readableBytes() == 0,
                        "Actual accepted inline positional codec preserves event, coordinates, channel, volume, pitch and seed: " + e.id());
            } finally { buffer.release(); }
            WeaponRuntime.cleanup(p);
            tested++;
        }
        check(h, tested > 11, "Exercise the eligible full-magazine catalog, beyond only Outlaw variants");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 20, environment = "destiny-test:w90_isolated")
    public void nearbySpectatorHearsOwnerButDifferentDimensionListenerDoesNot(GameTestHelper h) {
        var p = player(h, 6.5); equip(p, "duke_mk_44", 8, 0);
        var near = listener(h, new Vec3(3.5, 1, 6.5));
        var elsewhere = listener(h, new Vec3(3.5, 1, 6.5));
        var otherLevel = h.getLevel().getServer().getLevel(Level.NETHER);
        check(h, otherLevel != null && otherLevel != h.getLevel(), "A distinct server dimension exists for audience validation");
        elsewhere.setServerLevel(otherLevel); elsewhere.setPos(p.position());
        TestPlayers.drain(near); TestPlayers.drain(elsewhere);
        var sound = start(h, p);
        check(h, !h.getLevel().players().contains(p), "Unregistered source still receives its own sound session and audio");
        var nearStart = TestPlayers.outbound(near);
        check(h, near.isSpectator() && reloadSounds(nearStart).size() == 1
                        && key(reloadSounds(nearStart).getFirst()).equals(key(sound)), "Nearby spectator receives this exact owner's sound session sound");
        check(h, packets(nearStart,ClientboundAddEntityPacket.class).isEmpty(), "Spectator needs no entity spawn");
        for (var denied : List.of(elsewhere)) {
            var queued = TestPlayers.outbound(denied); noAudio(h, queued);
            check(h, packets(queued, ClientboundAddEntityPacket.class).isEmpty(),
                    "Cross-dimension connection receives no entity spawn");
        }
        WeaponRuntime.cancelUseForSkill(p);
        check(h, removed(TestPlayers.outbound(near), key(sound)), "Eligible spectator receives the matching sound session retirement");
        check(h, !removed(TestPlayers.outbound(elsewhere), key(sound)),
                "Ineligible dimension never receives this sound session's removal");
        h.succeed();
    }

    @GameTest(structure = FLOOR, maxTicks = 100, environment = "destiny-test:w90_isolated")
    public void longArmAndBowKeepOriginalPositionalReloadFallbackAndSwordStillDeniesReload(GameTestHelper h) {
        var hearer = listener(h, new Vec3(3.5, 1, 6.5));
        for (String id : List.of("long_arm", "biting_winds")) {
            var p = player(h, 6.5); var e = WeaponCatalog.find(id).orElseThrow(); var f = WeaponProfile.forEntry(e);
            var gun = equip(p, id, 0, f.infiniteReserve() ? 0 : 3);
            TestPlayers.drain(hearer);
            check(h, WeaponRuntime.reload(p), "Existing unsupported timed-audio reload remains accepted: " + id);
            var queued = TestPlayers.outbound(hearer);
            String key = DestinySounds.weaponKey(e, "reload");
            var original = packets(queued, ClientboundSoundPacket.class).stream().filter(packet ->
                    packet.getSound().value().location().getNamespace().equals("destiny")
                            && packet.getSound().value().location().getPath().equals(key)).toList();
            if(id.equals("biting_winds")) {
                check(h, !DestinySounds.has(key) && original.isEmpty(),
                        "The original archive has no bow.reload mapping: preserve silence, never invent a full reload clip");
            } else {
                check(h, DestinySounds.has(key),"Incremental source has its existing named mapping: "+id);
                var expected = DestinySounds.packet(key, p.getEyePosition(), SoundSource.PLAYERS, .8f, 0);
                check(h, original.size() == 1 && original.getFirst().getPitch() == 1f
                                && original.getFirst().getX() == expected.getX() && original.getFirst().getY() == expected.getY()
                                && original.getFirst().getZ() == expected.getZ(), "Original mapped positional fallback is retained: " + id);
            }
            check(h, reloadSounds(queued).isEmpty() && packets(queued, ClientboundSoundEntityPacket.class).isEmpty()
                            && packets(queued, ClientboundAddEntityPacket.class).isEmpty(),
                    "Never stretch a full-source timed sound session across a shell, pair insert or bow phase: " + id);
            noGlobalStop(h, queued);
            if (f.shellReload()) {
                h.runAfterDelay(f.firstReloadTicks(), () -> {
                    WeaponRuntime.tickPlayer(p); var phase = TestPlayers.outbound(p);
                    check(h, ammo(gun).rounds() == f.roundsPerInsert() && WeaponRuntime.reloading(p),
                            "First actual incremental phase transfers only its own insert: " + id);
                    check(h, packets(phase, ClientboundSoundEntityPacket.class).isEmpty(), "First insert never substitutes full-source entity audio");
                    noGlobalStop(h, phase);
                });
                h.runAfterDelay(f.firstReloadTicks() + f.reloadTicks(), () -> {
                    WeaponRuntime.tickPlayer(p); var phase = TestPlayers.outbound(p);
                    check(h, ammo(gun).rounds() == f.roundsPerInsert() * 2,
                            "Second actual incremental phase remains a separate paid insert: " + id);
                    check(h, packets(phase, ClientboundSoundEntityPacket.class).isEmpty(), "Repeat insert never starts full-source entity audio");
                    noGlobalStop(h, phase);
                });
            }
        }
        var swordOwner = player(h, 9.5);
        var swordEntry = WeaponCatalog.all().stream().filter(e -> e.family().equals("sword")).findFirst().orElseThrow();
        equip(swordOwner, swordEntry.id(), 0, 0); TestPlayers.drain(hearer);
        check(h, !WeaponRuntime.reload(swordOwner), "Existing sword gameplay rejects an invented magazine reload");
        noAudio(h, TestPlayers.outbound(swordOwner)); noAudio(h, TestPlayers.outbound(hearer));
        h.runAfterDelay(80, h::succeed);
    }
    @GameTest(structure = FLOOR, maxTicks = 40, environment = "destiny-test:w90_isolated")
    public void saturatedAliasesPlayWithoutStoppingSharedBaseAndReleasedChannelIsReusable(GameTestHelper h) {
        var owners=new ArrayList<ServerPlayer>();
        var keys=new java.util.HashSet<Identifier>();
        for(int i=0;i<33;i++) {
            var p=player(h,6.5);var gun=equip(p,"izanagis_burden",0,20);owners.add(p);
            check(h,ReloadAudio.startHoned(p,entry(gun),61),"Honed audio accepted");
            var sounds=reloadSounds(TestPlayers.outbound(p));
            check(h,sounds.size()==1,"Exactly one direct clip even at saturation");
            keys.add(key(sounds.getFirst()));
        }
        check(h,keys.size()==33 && keys.stream().filter(k -> k.getPath().contains(".direct_")).count()==32,
                "Thirty-two isolated channels plus one audible shared-base fallback");
        ReloadAudio.stop(owners.getLast());
        check(h,packets(TestPlayers.outbound(owners.getLast()),ClientboundStopSoundPacket.class).isEmpty(),
                "Saturated fallback never cuts a shared base event");
        var first=owners.getFirst();ReloadAudio.stop(first);
        var stopped=packets(TestPlayers.outbound(first),ClientboundStopSoundPacket.class);
        check(h,stopped.size()==1,"Reserved alias retires exactly once");
        check(h,ReloadAudio.startHoned(first,entry(first.getMainHandItem()),61),"Released channel reusable");
        check(h,key(reloadSounds(TestPlayers.outbound(first)).getFirst()).equals(stopped.getFirst().getName()),
                "Reuse occurs only after the prior alias stop");
        for(var p:owners)ReloadAudio.stop(p);
        h.succeed();
    }

}
