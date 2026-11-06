package kim.biryeong.destiny.loot;

import com.mojang.brigadier.arguments.StringArgumentType;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.inventory.gear.GearAcquisition;
import kim.biryeong.destiny.inventory.gear.GearIcons;
import kim.biryeong.destiny.inventory.WeaponScreenText;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.fabricmc.fabric.api.command.v2.CommandRegistrationCallback;
import net.fabricmc.fabric.api.entity.event.v1.ServerLivingEntityEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.commands.Commands;
import net.minecraft.commands.arguments.EntityArgument;
import net.minecraft.network.chat.Component;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.entity.LivingEntity;
import net.minecraft.world.entity.monster.Enemy;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.phys.Vec3;

import java.util.*;

/**
 * Shared loot service (strikes, dungeons, raids and the open world): table rolls, personal world drops, reward
 * chests, the engram inventory, starter gear and acquisition notices. Weapons always enter the Guardian's storage
 * through {@link GearAcquisition#store}; activities only name tables (see {@link LootTables}).
 */
public final class Loot {
    public static final AttachmentType<LootProfile> PROFILE = AttachmentRegistry.create(DestinyGuardians.id("loot_profile"),
            b -> b.persistent(LootProfile.CODEC).copyOnDeath().initializer(() -> LootProfile.EMPTY));
    static final int LEGENDARY = 0x522F65, EXOTIC = 0xCEAE33;
    /** Starter loadout after Guardian Rises: the two mission weapons (with their skins) and a grenade launcher. */
    public static final List<String[]> STARTER = List.of(
            new String[]{kim.biryeong.destiny.campaign.RisingLoadout.RIFLE, kim.biryeong.destiny.campaign.RisingLoadout.RIFLE_SKIN},
            new String[]{kim.biryeong.destiny.campaign.RisingLoadout.SHOTGUN, kim.biryeong.destiny.campaign.RisingLoadout.SHOTGUN_SKIN},
            new String[]{"edge_transit", null});
    /** Untagged enemies: max health at or below this is minor, at or below {@link #MAJOR_HEALTH} major, above boss. */
    static final float MINOR_HEALTH = 60, MAJOR_HEALTH = 500;

    private static final List<WorldDrop> DROPS = new ArrayList<>();
    private static final List<LootChest> CHESTS = new ArrayList<>();
    /** Guardians who damaged each living enemy (Destiny rolls loot per contributor). Weak: removed enemies drop out. */
    private static final Map<LivingEntity, Set<UUID>> CONTRIBUTORS = new WeakHashMap<>();
    /** Fireteam members this close to a kill also roll (Destiny shares kills inside the fireteam's area). */
    static final double FIRETEAM_SHARE = 64;
    private static final String ENGRAM_TAG = "destiny_engram";

    private Loot() { }

    public static void init() {
        ServerTickEvents.END_SERVER_TICK.register(Loot::tick);
        ServerLivingEntityEvents.AFTER_DEATH.register(Loot::died);
        ServerLivingEntityEvents.AFTER_DAMAGE.register((entity, source, base, taken, blocked) -> {
            if (entity instanceof ServerPlayer || !(entity instanceof Enemy)) return;
            var who = source.getEntity() instanceof ServerPlayer sp ? sp : null;
            if (who != null) CONTRIBUTORS.computeIfAbsent(entity, k -> new HashSet<>()).add(who.getUUID());
        });
        ServerPlayConnectionEvents.DISCONNECT.register((h, s) -> LootToast.forget(h.getPlayer()));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var c : List.copyOf(CHESTS)) c.close(true);
            for (var d : List.copyOf(DROPS)) d.close(true);
            DROPS.clear(); CHESTS.clear();
        });
        CommandRegistrationCallback.EVENT.register((dispatcher, registry, env) -> dispatcher.register(Commands.literal("destiny")
                .then(Commands.literal("loot").requires(Commands.hasPermission(Commands.LEVEL_GAMEMASTERS))
                        .then(Commands.literal("roll").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("table", StringArgumentType.word()).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String t = StringArgumentType.getString(c, "table");
                                    if (LootTables.table(t).isEmpty()) { c.getSource().sendFailure(Component.literal("테이블 없음: " + t)); return 0; }
                                    int n = grantTable(p, t, "관리자 지급");
                                    c.getSource().sendSuccess(() -> Component.literal(t + " → 보상 " + n + "개"), false);
                                    return n;
                                }))))
                        .then(Commands.literal("drop").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("table", StringArgumentType.word()).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    var t = LootTables.table(StringArgumentType.getString(c, "table"));
                                    if (t.isEmpty()) return 0;
                                    var at = inFront(p, 3);
                                    int n = 0;
                                    for (var r : LootRoller.roll(t.get(), p.getRandom())) { drop(p, at, r); n++; }
                                    return n;
                                }))))
                        .then(Commands.literal("chest").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("table", StringArgumentType.word()).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String t = StringArgumentType.getString(c, "table");
                                    if (LootTables.table(t).isEmpty()) return 0;
                                    chest(p, inFront(p, 4), t, 0, "보상 상자");
                                    return 1;
                                })
                                .then(Commands.argument("glimmer", com.mojang.brigadier.arguments.IntegerArgumentType.integer(0, 100000)).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String t = StringArgumentType.getString(c, "table");
                                    if (LootTables.table(t).isEmpty()) return 0;
                                    chest(p, inFront(p, 4), t, com.mojang.brigadier.arguments.IntegerArgumentType.getInteger(c, "glimmer"), "보상 상자");
                                    return 1;
                                })))))
                        .then(Commands.literal("complete").then(Commands.argument("activity", StringArgumentType.word()).executes(c -> {
                            String a = StringArgumentType.getString(c, "activity");
                            if (LootTables.activity(a).isEmpty()) { c.getSource().sendFailure(Component.literal("활동 없음: " + a)); return 0; }
                            var p = c.getSource().getPlayerOrException();
                            activityComplete(a, List.of(p), "QA 활동");
                            return 1;
                        })))
                        .then(Commands.literal("engram").then(Commands.argument("player", EntityArgument.player())
                                .then(Commands.argument("tier", StringArgumentType.word()).executes(c -> {
                                    var p = EntityArgument.getPlayer(c, "player");
                                    String tier = StringArgumentType.getString(c, "tier");
                                    if (LootTables.engramTable(tier).isEmpty()) return 0;
                                    return collect(p, LootRoller.Reward.engram(tier), "관리자 지급") ? 1 : 0;
                                }))))
                        .then(Commands.literal("decode").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            String error = decode(p, 0);
                            if (error != null) { c.getSource().sendFailure(Component.literal(error)); return 0; }
                            return 1;
                        })))
                        .then(Commands.literal("status").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            var pr = profile(p);
                            long drops = DROPS.stream().filter(d -> d.owner == p && !d.done).count();
                            long chests = CHESTS.stream().filter(x -> x.owner == p && !x.done).count();
                            c.getSource().sendSuccess(() -> Component.literal("starter=" + pr.starter() + " engrams=" + pr.engrams()
                                    + " drops=" + drops + " chests=" + chests), false);
                            return 1;
                        })))
                        .then(Commands.literal("starter").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            return grantStarter(p) ? 1 : 0;
                        })))
                        .then(Commands.literal("reset_starter").then(Commands.argument("player", EntityArgument.player()).executes(c -> {
                            var p = EntityArgument.getPlayer(c, "player");
                            p.setAttached(PROFILE, new LootProfile(false, profile(p).engrams()));
                            return 1;
                        }))))));
    }

    public static LootProfile profile(ServerPlayer p) { return p.getAttachedOrElse(PROFILE, LootProfile.EMPTY); }

    // ---------------------------------------------------------------- activity hooks

    /**
     * An activity was cleared: every participant immediately receives the completion table and gets a personal
     * reward chest {@code chestAt} (null: in front of them). Unknown activity ids do nothing.
     */
    public static void activityComplete(String activity, List<ServerPlayer> players, String title) {
        activityComplete(activity, players, title, null, 0);
    }

    /**
     * As above with the chest at a fixed spot ({@code chestYaw}: the way its front faces). Every participant gets
     * their own chest there; each only sees their own (Destiny's personal loot).
     */
    public static void activityComplete(String activity, List<ServerPlayer> players, String title, Vec3 chestAt, float chestYaw) {
        var hook = LootTables.activity(activity);
        if (hook.isEmpty()) return;
        for (var p : players) {
            if (hook.get().completion() != null) grantTable(p, hook.get().completion(), title + " 완료");
            if (hook.get().chest() != null) {
                long glimmer = hook.get().rollGlimmer(p.getRandom());
                if (chestAt != null) CHESTS.add(new LootChest(p, chestAt, chestYaw, hook.get().chest(), glimmer, title + " 보상 상자"));
                else CHESTS.add(new LootChest(p, inFront(p, 3), p.getYRot() + 180, hook.get().chest(), glimmer, title + " 보상 상자"));
                p.sendSystemMessage(Component.literal("보상 상자가 나타났습니다.").withStyle(net.minecraft.ChatFormatting.GOLD));
            }
        }
    }

    /** The activity is closing: unopened chests are delivered, uncollected drops go to the postmaster. */
    public static void activityClosed(List<ServerPlayer> players) {
        for (var c : List.copyOf(CHESTS)) if (players.contains(c.owner)) c.close(true);
        for (var d : List.copyOf(DROPS)) if (players.contains(d.owner)) d.close(true);
    }

    // ---------------------------------------------------------------- engrams as items (postmaster mail)

    /** A mail-able engram: claiming it puts the engram back into the engram inventory. */
    public static ItemStack engramToken(String tier) {
        var s = new ItemStack(net.minecraft.world.item.Items.PAPER);
        s.set(net.minecraft.core.component.DataComponents.ITEM_MODEL, WorldDrop.engramModel(tier));
        s.set(net.minecraft.core.component.DataComponents.CUSTOM_NAME, Component.literal(engramName(tier))
                .withStyle(st -> st.withItalic(false).withColor(color(LootRoller.Reward.engram(tier)))));
        var tag = new net.minecraft.nbt.CompoundTag(); tag.putString(ENGRAM_TAG, tier);
        s.set(net.minecraft.core.component.DataComponents.CUSTOM_DATA, net.minecraft.world.item.component.CustomData.of(tag));
        return s;
    }
    public static Optional<String> engramTier(ItemStack s) {
        var data = s.get(net.minecraft.core.component.DataComponents.CUSTOM_DATA);
        if (data == null) return Optional.empty();
        var tier = data.copyTag().getStringOr(ENGRAM_TAG, "");
        return tier.isEmpty() ? Optional.empty() : Optional.of(tier);
    }
    /** Null when one more engram fits, else why not. */
    public static String engramRoom(ServerPlayer p) {
        return profile(p).engrams().size() >= LootProfile.ENGRAM_CAP ? "엔그램은 " + LootProfile.ENGRAM_CAP + "개까지 보관할 수 있습니다. 먼저 해독하세요." : null;
    }
    public static String storeEngram(ServerPlayer p, String tier) {
        String why = engramRoom(p);
        if (why != null) return why;
        p.setAttached(PROFILE, profile(p).plus(tier));
        announce(p, LootRoller.Reward.engram(tier), "우편함");
        return null;
    }
    /** The uncollected reward as a stack for the postmaster. */
    static ItemStack mailStack(LootRoller.Reward r) { return r.engram() != null ? engramToken(r.engram()) : r.weapon().copy(); }

    // ---------------------------------------------------------------- grants

    /** Roll {@code table} and give every reward to {@code p}. Returns the number of rewards. */
    public static int grantTable(ServerPlayer p, String table, String source) {
        var t = LootTables.table(table);
        if (t.isEmpty()) { DestinyGuardians.LOGGER.warn("Unknown loot table {}", table); return 0; }
        int n = 0;
        for (var r : LootRoller.roll(t.get(), p.getRandom())) if (collect(p, r, source)) n++;
        return n;
    }

    /**
     * Put one reward into the Guardian's possession. A weapon whose storage bucket is full is kept as a legendary
     * engram instead (Destiny's postmaster role); an engram beyond the cap is decoded on the spot.
     * @return false only when nothing could be kept.
     */
    public static boolean collect(ServerPlayer p, LootRoller.Reward r, String source) {
        if (r.weapon() != null) {
            String error = GearAcquisition.store(p, r.weapon());
            if (error == null) { announce(p, r, source); LootSounds.pickup(p); return true; }
            if (exotic(r) || profile(p).engrams().size() >= LootProfile.ENGRAM_CAP) {
                p.sendOverlayMessage(Component.literal(error));
                return false;
            }
            String tier = rarity(r).id();
            p.setAttached(PROFILE, profile(p).plus(tier));
            p.sendSystemMessage(Component.literal(error + " 무기를 " + engramName(tier) + "으로 보관했습니다."));
            announce(p, LootRoller.Reward.engram(tier), source);
            return true;
        }
        if (profile(p).engrams().size() >= LootProfile.ENGRAM_CAP) {
            var weapon = decodeRoll(p, r.engram());
            return weapon != null && collect(p, LootRoller.Reward.weapon(weapon), "엔그램 해독");
        }
        p.setAttached(PROFILE, profile(p).plus(r.engram()));
        announce(p, r, source);
        LootSounds.pickup(p);
        return true;
    }

    /** Decode the held engram at {@code index} into a weapon. Null on success, otherwise the reason. */
    public static String decode(ServerPlayer p, int index) {
        var engrams = profile(p).engrams();
        if (index < 0 || index >= engrams.size()) return "해독할 엔그램이 없습니다.";
        var weapon = decodeRoll(p, engrams.get(index));
        if (weapon == null) return "엔그램 보상을 만들 수 없습니다.";
        String error = GearAcquisition.store(p, weapon);
        if (error != null) return error;
        p.setAttached(PROFILE, profile(p).minus(index));
        LootSounds.decode(p);
        announce(p, LootRoller.Reward.weapon(weapon), "엔그램 해독");
        return null;
    }

    private static ItemStack decodeRoll(ServerPlayer p, String tier) {
        var table = LootTables.engramTable(tier).flatMap(LootTables::table);
        if (table.isEmpty()) return null;
        for (int attempt = 0; attempt < 8; attempt++)
            for (var r : LootRoller.roll(table.get(), p.getRandom())) if (r.weapon() != null) return r.weapon();
        return null;
    }

    /** One-time starter gear: the two Guardian Rises weapons and a grenade launcher, equipped where slots are free. */
    public static boolean grantStarter(ServerPlayer p) {
        if (profile(p).starter()) return false;
        for (var spec : STARTER) {
            var entry = WeaponCatalog.find(spec[0]);
            if (entry.isEmpty()) continue;
            var stack = LootRoller.create(entry.get(), spec[1], p.getRandom());
            var slot = WeaponLoadout.slot(p, stack, entry.get());
            var inv = p.getInventory();
            if (inv.getItem(slot.hotbar()).isEmpty()) { inv.setItem(slot.hotbar(), stack); p.setAttached(WeaponLoadout.ENABLED, true); }
            else if (GearAcquisition.store(p, stack) != null) continue;
            announce(p, LootRoller.Reward.weapon(stack), "수호자 기본 무장");
        }
        p.getInventory().setChanged();
        p.containerMenu.broadcastChanges();
        WeaponHandling.update(p);
        p.setAttached(PROFILE, profile(p).withStarter());
        LootSounds.pickup(p);
        return true;
    }

    private static boolean starterDue(ServerPlayer p) {
        boolean cleared = p.getAttachedOrElse(kim.biryeong.destiny.campaign.RisingCampaign.COMPLETED_REVISION, 0) > 0
                || p.getAttachedOrElse(kim.biryeong.destiny.tutorial.Tutorial.COMPLETED_REVISION, 0) >= kim.biryeong.destiny.tutorial.Tutorial.REQUIRED_REVISION;
        return !profile(p).starter() && cleared
                && !kim.biryeong.destiny.tutorial.TutorialLoan.active(p) && p.isAlive() && !p.isSpectator();
    }

    // ---------------------------------------------------------------- world drops and chests

    /** A personal world drop; several drops at one point fan out around it (Destiny's loot spray). */
    public static void drop(ServerPlayer owner, Vec3 at, LootRoller.Reward r) {
        long near = DROPS.stream().filter(d -> !d.done && d.owner == owner && d.pos.distanceToSqr(at) < 1.5 * 1.5).count();
        Vec3 pos = at;
        if (near > 0) {
            double angle = near * 2.4, radius = .9 + .25 * (near / 6);
            pos = at.add(Math.cos(angle) * radius, 0, Math.sin(angle) * radius);
        }
        DROPS.add(new WorldDrop(owner, pos, r));
    }

    /** A personal reward chest facing {@code owner}. */
    public static void chest(ServerPlayer owner, Vec3 at, String table, long glimmer, String source) {
        CHESTS.add(new LootChest(owner, at, owner.getYRot() + 180, table, glimmer, source));
    }
    public static void chest(ServerPlayer owner, Vec3 at, String table, String source) { chest(owner, at, table, 0, source); }

    /** A personal world drop exactly at {@code at} (the chest burst has already spread them). */
    static void dropAt(ServerPlayer owner, Vec3 at, LootRoller.Reward r) { DROPS.add(new WorldDrop(owner, at, r, LANDED_PICKUP_DELAY)); }
    /** Burst rewards stay on the ground briefly so the Guardian sees what dropped before walking it up. */
    static final int LANDED_PICKUP_DELAY = 16;

    /** Standing point on the first floor at or below {@code at} within {@code depth} blocks, null if none. */
    public static Vec3 floor(net.minecraft.server.level.ServerLevel level, Vec3 at, int depth) {
        var pos = net.minecraft.core.BlockPos.containing(at.x, at.y + .5, at.z);
        if (!level.getBlockState(pos).getCollisionShape(level, pos).isEmpty()) pos = pos.above();
        for (int i = 0; i <= depth; i++, pos = pos.below()) {
            var below = pos.below();
            var shape = level.getBlockState(below).getCollisionShape(level, below);
            if (!shape.isEmpty() && level.getBlockState(pos).getCollisionShape(level, pos).isEmpty())
                return new Vec3(at.x, below.getY() + shape.max(net.minecraft.core.Direction.Axis.Y), at.z);
        }
        return null;
    }

    static Vec3 inFront(ServerPlayer p, double distance) {
        var look = Vec3.directionFromRotation(0, p.getYRot());
        var at = p.position().add(look.scale(distance));
        // Settle onto the floor below/at the point; stay at the player's height when there is none nearby.
        var level = p.level();
        var pos = net.minecraft.core.BlockPos.containing(at.x, p.getY() + 1, at.z);
        for (int i = 0; i < 4; i++, pos = pos.below())
            if (!level.getBlockState(pos.below()).getCollisionShape(level, pos.below()).isEmpty()) return new Vec3(at.x, pos.getY(), at.z);
        return new Vec3(at.x, p.getY(), at.z);
    }

    private static void died(LivingEntity entity, DamageSource source) {
        var contributors = CONTRIBUTORS.remove(entity);
        if (entity instanceof ServerPlayer || !(entity instanceof Enemy)) return;
        ServerPlayer killer = source.getEntity() instanceof ServerPlayer sp ? sp
                : entity.getKillCredit() instanceof ServerPlayer sp ? sp : null;
        var tier = entity instanceof LootTagged t ? t.lootTier()
                : entity.getMaxHealth() <= MINOR_HEALTH ? LootTagged.Tier.MINOR
                : entity.getMaxHealth() <= MAJOR_HEALTH ? LootTagged.Tier.MAJOR : LootTagged.Tier.BOSS;
        var enemies = LootTables.enemies();
        if (enemies.isEmpty() || tier == LootTagged.Tier.NONE) return;
        String table = switch (tier) {
            case MINOR -> enemies.get().minor(); case MAJOR -> enemies.get().major(); case BOSS -> enemies.get().boss(); case NONE -> null;
        };
        var t = LootTables.table(table);
        if (t.isEmpty()) return;
        var at = entity.position();
        // Every Guardian who hit it, the killer, and the killer's fireteam nearby each roll their own loot.
        for (var p : recipients(entity, killer, contributors)) {
            for (var r : LootRoller.roll(t.get(), p.getRandom())) drop(p, at, r);
            long glimmer = switch (tier) { case MINOR -> p.getRandom().nextInt(3) == 0 ? 1 : 0; case MAJOR -> 3; case BOSS -> 20; case NONE -> 0; };
            kim.biryeong.destiny.economy.Economy.reward(p, glimmer, "처치");
        }
    }

    /** Distinct living Guardians in the enemy's level who earned a roll; never Crucible participants. */
    static List<ServerPlayer> recipients(LivingEntity entity, ServerPlayer killer, Set<UUID> contributors) {
        var server = entity.level().getServer();
        var out = new LinkedHashMap<UUID, ServerPlayer>();
        if (killer != null) out.put(killer.getUUID(), killer);
        if (contributors != null) for (var id : contributors) {
            var p = server.getPlayerList().getPlayer(id);
            if (p != null) out.putIfAbsent(id, p);
        }
        for (var p : List.copyOf(out.values()))
            kim.biryeong.destiny.fireteam.Fireteams.team(p).ifPresent(team -> {
                for (var id : team.members()) {
                    var m = server.getPlayerList().getPlayer(id);
                    if (m != null && m.level() == entity.level() && m.distanceToSqr(entity) <= FIRETEAM_SHARE * FIRETEAM_SHARE) out.putIfAbsent(id, m);
                }
            });
        out.values().removeIf(p -> p.hasDisconnected() || !p.isAlive() || p.isSpectator() || p.level() != entity.level()
                || kim.biryeong.destiny.crucible.CrucibleRuntime.participating(p));
        return List.copyOf(out.values());
    }

    private static void tick(MinecraftServer server) {
        DROPS.removeIf(d -> !d.tick());
        CHESTS.removeIf(c -> !c.tick());
        LootToast.tick(server);
        if (server.getTickCount() % 40 == 0)
            for (var p : server.getPlayerList().getPlayers()) if (starterDue(p)) grantStarter(p);
    }

    // ---------------------------------------------------------------- presentation

    static boolean exotic(LootRoller.Reward r) { return rarity(r) == WeaponRarity.EXOTIC; }
    /** W325 tier of a reward: an engram's tier, or the weapon's (skin tier first). */
    public static WeaponRarity rarity(LootRoller.Reward r) {
        if (r.engram() != null) return WeaponRarity.parse(r.engram()).orElse(WeaponRarity.LEGENDARY);
        return WeaponRarity.of(r.weapon());
    }
    static int color(LootRoller.Reward r) { return rarity(r).color(); }
    static String engramIcon(String tier) { return GearIcons.engram(tier).orElse("bungie/engram_legendary"); }
    public static String engramName(String tier) {
        return switch (tier) { case "exotic" -> "경이 엔그램"; case "rare" -> "희귀 엔그램"; case "uncommon" -> "고급 엔그램";
            case "common" -> "일반 엔그램"; case "prime" -> "최상급 엔그램"; default -> "전설 엔그램"; };
    }

    private static void announce(ServerPlayer p, LootRoller.Reward r, String source) {
        if (r.engram() != null) {
            LootToast.show(p, engramIcon(r.engram()), null, engramName(r.engram()), source, band(rarity(r)));
            return;
        }
        var entry = WeaponItems.entry(r.weapon());
        if (entry.isEmpty()) return;
        var skin = WeaponSkins.of(r.weapon());
        String name = skin.map(WeaponSkins.Skin::display).orElse(WeaponScreenText.weapon(entry.get().id(), entry.get().name()));
        String icon = GearIcons.weapon(skin.map(WeaponSkins.Skin::id).orElse(entry.get().id())).orElse(null);
        var tier = rarity(r);
        LootToast.show(p, icon, entry.get().id(), name, source + "  ·  " + tier.label() + " " + WeaponScreenText.family(entry.get().family()),
                band(tier));
    }

    /** Toast/tile band colour; legendary/exotic keep their established Destiny values. */
    static int band(WeaponRarity tier) {
        return switch (tier) { case EXOTIC -> EXOTIC; case LEGENDARY -> LEGENDARY; default -> tier.band(); };
    }
}
