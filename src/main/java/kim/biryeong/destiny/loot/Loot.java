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

    private Loot() { }

    public static void init() {
        ServerTickEvents.END_SERVER_TICK.register(Loot::tick);
        ServerLivingEntityEvents.AFTER_DEATH.register(Loot::died);
        ServerPlayConnectionEvents.DISCONNECT.register((h, s) -> LootToast.forget(h.getPlayer()));
        ServerLifecycleEvents.SERVER_STOPPING.register(server -> {
            for (var d : List.copyOf(DROPS)) d.close();
            for (var c : List.copyOf(CHESTS)) c.close(false);
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
                                    chest(p, inFront(p, 5), t, "보상 상자");
                                    return 1;
                                }))))
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
        var hook = LootTables.activity(activity);
        if (hook.isEmpty()) return;
        for (var p : players) {
            if (hook.get().completion() != null) grantTable(p, hook.get().completion(), title + " 완료");
            if (hook.get().chest() != null) {
                chest(p, inFront(p, 3), hook.get().chest(), title + " 보상 상자");
                p.sendSystemMessage(Component.literal("보상 상자가 나타났습니다.").withStyle(net.minecraft.ChatFormatting.GOLD));
            }
        }
    }

    /** The activity is closing: unopened chests are delivered, personal drops vanish. */
    public static void activityClosed(List<ServerPlayer> players) {
        for (var c : List.copyOf(CHESTS)) if (players.contains(c.owner)) c.close(true);
        for (var d : List.copyOf(DROPS)) if (players.contains(d.owner)) d.close();
    }

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

    public static void chest(ServerPlayer owner, Vec3 at, String table, String source) {
        CHESTS.add(new LootChest(owner, at, owner.getYRot(), table, source));
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
        if (entity instanceof ServerPlayer || !(entity instanceof Enemy)) return;
        ServerPlayer killer = source.getEntity() instanceof ServerPlayer sp ? sp
                : entity.getKillCredit() instanceof ServerPlayer sp ? sp : null;
        if (killer == null || killer.level() != entity.level() || kim.biryeong.destiny.crucible.CrucibleRuntime.participating(killer)) return;
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
        for (var r : LootRoller.roll(t.get(), killer.getRandom())) drop(killer, at, r);
        // Glimmer income: every combatant kill pays a little (Destiny's on-kill Glimmer).
        long glimmer = switch (tier) { case MINOR -> killer.getRandom().nextInt(3) == 0 ? 1 : 0; case MAJOR -> 3; case BOSS -> 20; case NONE -> 0; };
        kim.biryeong.destiny.economy.Economy.reward(killer, glimmer, "처치");
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
