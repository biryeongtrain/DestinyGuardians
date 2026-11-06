package kim.biryeong.destiny.weapon;

import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.fabricmc.fabric.api.networking.v1.context.PacketContext;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.protocol.game.ClientboundContainerSetSlotPacket;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomModelData;

import java.util.*;
import java.util.concurrent.CompletableFuture;

/** Shared DynamicUV geometry with BetterModel's actual skin pixels; no per-user pack.
 * Only the wire carrier receives the reserved cosmetic CMD fields. */
public final class WeaponSkinArms {
    static final int READY = 8, SLIM = 9, COLOR_START = 64, UPPER_COLOR_START = 320, STRIDE = 128;
    private static final Map<UUID, Request> REQUESTS = new java.util.concurrent.ConcurrentHashMap<>();
    private static boolean initialized;
    private WeaponSkinArms() {}

    record Pixels(boolean slim, List<Integer> right, List<Integer> left,
                  List<Integer> rightUpper, List<Integer> leftUpper) {
        Pixels {
            right = List.copyOf(right); left = List.copyOf(left);
            rightUpper = List.copyOf(rightUpper); leftUpper = List.copyOf(leftUpper);
            int n = slim ? 96 : 112;
            if (right.size() != n || left.size() != n || rightUpper.size() != n || leftUpper.size() != n)
                throw new IllegalArgumentException("Unexpected skin arm layout (both genuine segments required)");
        }
    }
    private record DefaultSkin(boolean slim, List<Integer> right, List<Integer> left,
                               List<Integer> rightBare, List<Integer> leftBare,
                               List<Integer> rightUpper, List<Integer> leftUpper,
                               List<Integer> rightUpperBare, List<Integer> leftUpperBare) {}
    private record Defaults(int schemaVersion, List<DefaultSkin> skins) {}
    private static final class DefaultData {
        static final Defaults DATA = load();
        private static Defaults load() {
            try (var in = Objects.requireNonNull(WeaponSkinArms.class.getResourceAsStream(
                    "/destiny/weapons/w204-default-skin-arms.json"));
                 var reader = new java.io.InputStreamReader(in, java.nio.charset.StandardCharsets.UTF_8)) {
                var data = new com.google.gson.Gson().fromJson(reader, Defaults.class);
                if (data.schemaVersion != 1 || data.skins.size() != 18) throw new IllegalStateException("Invalid default arm data");
                return data;
            } catch (java.io.IOException e) { throw new IllegalStateException(e); }
        }
    }
    static Pixels defaultPixels(UUID id, int parts) {
        var skin = DefaultData.DATA.skins.get(Math.floorMod(id.hashCode(), 18));
        return new Pixels(skin.slim, (parts & 1) != 0 ? skin.right : skin.rightBare,
                (parts & 2) != 0 ? skin.left : skin.leftBare,
                (parts & 1) != 0 ? skin.rightUpper : skin.rightUpperBare,
                (parts & 2) != 0 ? skin.leftUpper : skin.leftUpperBare);
    }
    private static final class Request {
        final ServerPlayer owner;
        final Object profile;
        final int parts;
        final int createdAt;
        final CompletableFuture<Pixels> future;
        volatile Pixels pixels;
        boolean observed;
        Request(ServerPlayer owner) {
            this.owner = owner; profile = owner.getGameProfile(); parts = parts(owner);
            createdAt = owner.level().getServer().getTickCount();
            CompletableFuture<Pixels> requested;
            try { requested = Bridge.fetch(owner); }
            catch (RuntimeException e) { requested = CompletableFuture.failedFuture(e); }
            future = requested.completeOnTimeout(null, 30, java.util.concurrent.TimeUnit.SECONDS).exceptionally(error -> {
                DestinyGuardians.LOGGER.warn("Unable to prepare skin arms for {}", owner.getUUID(), error);
                return null;
            });
        }
    }

    public static void init() {
        WeaponOutboundPresentation.init();
        if (ProfileWeaponView.enabled() || initialized || !FabricLoader.getInstance().isModLoaded("bettermodel")) return;
        initialized = true;
        ServerTickEvents.END_SERVER_TICK.register(WeaponSkinArms::tick);
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> {
            var p = handler.getPlayer(); REQUESTS.computeIfPresent(p.getUUID(), (id, r) -> r.owner == p ? null : r);
        });
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> REQUESTS.clear());
    }

    private static void tick(MinecraftServer server) {
        for (var p : server.getPlayerList().getPlayers()) {
            var r = REQUESTS.get(p.getUUID());
            if (r == null || r.owner != p || !r.profile.equals(p.getGameProfile()) || r.parts != parts(p)
                    || (r.observed && r.pixels == null && server.getTickCount() - r.createdAt >= 1200)) {
                r = new Request(p); REQUESTS.put(p.getUUID(), r);
            }
            if (!r.observed && r.future.isDone()) {
                r.pixels = r.future.getNow(null); r.observed = true;
                // Repaint just the selected inventory slot after the async skin becomes available.
                // No async callback touches player, inventory, or gameplay state.
                if (r.pixels != null && p.isAlive() && !p.hasDisconnected()) {
                    for (int i = 0; i < p.inventoryMenu.slots.size(); i++) {
                        var slot = p.inventoryMenu.slots.get(i);
                        if (slot.container == p.getInventory() && slot.getContainerSlot() == p.getInventory().getSelectedSlot()) {
                            p.connection.send(new ClientboundContainerSetSlotPacket(p.inventoryMenu.containerId,
                                    p.inventoryMenu.incrementStateId(), i, slot.getItem().copy()));
                            break;
                        }
                    }
                }
            }
        }
    }

    static ItemStack project(ItemStack carrier, PacketContext context) {
        var profile = context.get(PacketContext.GAME_PROFILE);
        var connection = context.get(PacketContext.CONNECTION);
        var r = profile == null ? null : REQUESTS.get(profile.id());
        var pixels = r != null && connection != null && connection.getPacketListener() == r.owner.connection
                && context.get(PacketContext.SERVER_INSTANCE) == r.owner.level().getServer()
                && r.profile.equals(profile) ? r.pixels : null;
        carrier.set(DataComponents.CUSTOM_MODEL_DATA, merge(
                carrier.getOrDefault(DataComponents.CUSTOM_MODEL_DATA, CustomModelData.EMPTY), pixels));
        return carrier;
    }

    private static int parts(ServerPlayer p) {
        return (p.isModelPartShown(net.minecraft.world.entity.player.PlayerModelPart.RIGHT_SLEEVE) ? 1 : 0)
                | (p.isModelPartShown(net.minecraft.world.entity.player.PlayerModelPart.LEFT_SLEEVE) ? 2 : 0);
    }

    static CustomModelData merge(CustomModelData old, Pixels pixels) {
        var flags = new ArrayList<>(old.flags());
        while (flags.size() <= SLIM) flags.add(false);
        flags.set(READY, pixels != null); flags.set(SLIM, pixels != null && pixels.slim());
        if (pixels == null) return new CustomModelData(old.floats(), List.copyOf(flags), old.strings(), old.colors());
        var colors = new ArrayList<>(old.colors());
        while (colors.size() < UPPER_COLOR_START + STRIDE * 2) colors.add(0xffffff);
        for (int i = 0; i < pixels.right().size(); i++) colors.set(COLOR_START + i, pixels.right().get(i));
        for (int i = 0; i < pixels.left().size(); i++) colors.set(COLOR_START + STRIDE + i, pixels.left().get(i));
        for (int i = 0; i < pixels.rightUpper().size(); i++) colors.set(UPPER_COLOR_START + i, pixels.rightUpper().get(i));
        for (int i = 0; i < pixels.leftUpper().size(); i++) colors.set(UPPER_COLOR_START + STRIDE + i, pixels.leftUpper().get(i));
        return new CustomModelData(old.floats(), List.copyOf(flags), old.strings(), List.copyOf(colors));
    }

    /** Match BetterModel DynamicUV RGB + COMPLEX_ARGB ordering. Sleeve alpha is
     * composited onto the same block surface, preserving its pixels without extra geometry. */
    static List<Integer> flatten(CustomModelData data, int n, boolean sleeve) {
        return flatten(data, n, sleeve, 0);
    }

    /** BetterModel 3.5.1 rightArm/leftArm(EMPTY) prepend nine armor colors when
     * playerArmor is enabled, even with no chestplate. Forearms have no prefix.
     * Accept only the two actual upper-arm layouts, never a forearm substitute. */
    static List<Integer> flattenUpper(CustomModelData data, int n, boolean sleeve) {
        if (data == null) throw new IllegalArgumentException("Missing BetterModel upper-arm pixels");
        int prefix = data.colors().size() - n * 2;
        if (prefix != 0 && prefix != 9) throw new IllegalArgumentException("BetterModel upper-arm data layout changed");
        return flatten(data, n, sleeve, prefix);
    }

    private static List<Integer> flatten(CustomModelData data, int n, boolean sleeve, int colorOffset) {
        if (data == null || data.colors().size() != colorOffset + n * 2 || data.floats().size() != n)
            throw new IllegalArgumentException("BetterModel arm data layout changed");
        var result = new ArrayList<Integer>(n);
        for (int i = 0; i < n; i++) {
            int base = data.colors().get(colorOffset + i), over = data.colors().get(colorOffset + n + i);
            float alpha = sleeve ? Math.clamp(data.floats().get(i), 0f, 2f) / 2 : 0;
            int rgb = 0;
            for (int shift : new int[]{16, 8, 0}) rgb |= Math.round(((base >> shift) & 255) * (1-alpha)
                    + ((over >> shift) & 255) * alpha) << shift;
            result.add(rgb);
        }
        return List.copyOf(result);
    }

    /** Keep optional BetterModel symbols out of the class's initialization path. */
    private static final class Bridge {
        static CompletableFuture<Pixels> fetch(ServerPlayer p) {
            var profile = kr.toxicity.model.api.profile.ModelProfile.of(
                    kr.toxicity.model.api.mod.platform.ModPlayer.of(p.connection));
            if (profile.skin().skin() == null) return CompletableFuture.completedFuture(defaultPixels(p.getUUID(), parts(p)));
            boolean rightSleeve = p.isModelPartShown(net.minecraft.world.entity.player.PlayerModelPart.RIGHT_SLEEVE);
            boolean leftSleeve = p.isModelPartShown(net.minecraft.world.entity.player.PlayerModelPart.LEFT_SLEEVE);
            return kr.toxicity.model.api.BetterModel.platform().skinManager().complete(profile.asUncompleted())
                    .thenApply(skin -> {
                        if (skin == null) return null;
                        // A missing/failed skin is not silently presented as the user's skin.
                        if (!skin.profile().info().id().equals(profile.info().id())) return null;
                        boolean slim = skin.profile().skin().slim(); int n = slim ? 96 : 112;
                        var right = ((kr.toxicity.model.api.mod.platform.ModItemStack) skin.rightForeArm().itemStack()).source();
                        var left = ((kr.toxicity.model.api.mod.platform.ModItemStack) skin.leftForeArm().itemStack()).source();
                        var emptyArmor = kr.toxicity.model.api.armor.PlayerArmor.EMPTY;
                        var rightUpper = ((kr.toxicity.model.api.mod.platform.ModItemStack) skin.rightArm(emptyArmor).itemStack()).source();
                        var leftUpper = ((kr.toxicity.model.api.mod.platform.ModItemStack) skin.leftArm(emptyArmor).itemStack()).source();
                        return new Pixels(slim, flatten(right.get(DataComponents.CUSTOM_MODEL_DATA), n, rightSleeve),
                                flatten(left.get(DataComponents.CUSTOM_MODEL_DATA), n, leftSleeve),
                                flattenUpper(rightUpper.get(DataComponents.CUSTOM_MODEL_DATA), n, rightSleeve),
                                flattenUpper(leftUpper.get(DataComponents.CUSTOM_MODEL_DATA), n, leftSleeve));
                    });
        }
    }
}
