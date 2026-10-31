package kim.biryeong.destiny.input;

import kim.biryeong.destiny.guardian.Guardians;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerLifecycleEvents;
import net.fabricmc.fabric.api.event.lifecycle.v1.ServerTickEvents;
import net.fabricmc.fabric.api.networking.v1.ServerPlayConnectionEvents;
import net.minecraft.ChatFormatting;
import net.minecraft.network.chat.ClickEvent;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;

import java.net.URI;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;
import java.util.function.Function;

/** Connection-scoped input capability: death and dimension changes must not re-enable fallback keys. */
public final class ClientControls {
    public static final String DOWNLOAD_URL = "https://github.com/eiqq/GCB-mod/releases";
    private static final int HANDSHAKE_GRACE_TICKS = 100;
    private static final Map<UUID, Session> SESSIONS = new HashMap<>();
    private static Function<ServerPlayer, Capability> detector = player -> new Capability(false, "");

    public record Capability(boolean installed, String version) {
        /** Legacy peers may report a version without setting the separate presence flag. */
        public boolean detected() { return installed || !versionLabel(version).isEmpty(); }
    }

    private static final class Session {
        final int joined;
        boolean installed, recommended, announced;
        String version = "";
        Session(int joined) { this.joined = joined; }
    }

    private ClientControls() { }

    public static void init() {
        ServerPlayConnectionEvents.JOIN.register((handler, sender, server) -> {
            forget(handler.getPlayer());
            SESSIONS.put(handler.getPlayer().getUUID(), new Session(server.getTickCount()));
        });
        ServerPlayConnectionEvents.DISCONNECT.register((handler, server) -> forget(handler.getPlayer()));
        ServerLifecycleEvents.SERVER_STOPPED.register(server -> SESSIONS.clear());
        ServerTickEvents.END_SERVER_TICK.register(server -> {
            for (ServerPlayer player : server.getPlayerList().getPlayers()) {
                gcb(player);
                Session session = SESSIONS.get(player.getUUID());
                boolean graceElapsed = server.getTickCount() - session.joined >= HANDSHAKE_GRACE_TICKS;
                if (session.installed && !session.announced && (!session.version.isEmpty() || graceElapsed)) {
                    session.announced = true;
                    server.getPlayerList().broadcastSystemMessage(installedMessage(player.getName(), session.version), false);
                } else if (!session.installed && !session.recommended && graceElapsed) {
                    session.recommended = true;
                    player.sendSystemMessage(recommendation());
                }
            }
        });
    }

    /** The optional GCB bridge supplies protocol state, never a client name or debug camera flag. */
    public static void setDetector(Function<ServerPlayer, Capability> source) { detector = source; }

    public static boolean gcb(ServerPlayer player) {
        Session session = SESSIONS.computeIfAbsent(player.getUUID(),
                ignored -> new Session(player.level().getServer().getTickCount()));
        Capability current = detector.apply(player);
        if (current.detected()) {
            if (!session.installed) Guardians.runtime(player).lastShiftPressTick = Integer.MIN_VALUE / 2;
            session.installed = true;
            String version = versionLabel(current.version());
            if (!version.isEmpty()) session.version = version;
        }
        // GuardianRuntime is reset on death/dimension change; this session lasts until disconnect.
        if (session.installed) Guardians.runtime(player).gcbClient = true;
        return session.installed;
    }

    public static void forget(ServerPlayer player) { SESSIONS.remove(player.getUUID()); }

    /** The existing 4.2 client predicts server-authoritative Mob mounts automatically. */
    public static boolean mountPrediction(ServerPlayer player) {
        if (!gcb(player)) return false;
        String version = SESSIONS.get(player.getUUID()).version;
        var match = java.util.regex.Pattern.compile("^(\\d+)\\.(\\d+)(?:\\.|$|[+\\-]).*").matcher(version);
        if (!match.matches()) return false;
        try {
            int major = Integer.parseInt(match.group(1)), minor = Integer.parseInt(match.group(2));
            return major > 4 || major == 4 && minor >= 2;
        } catch (NumberFormatException ignored) { return false; }
    }

    static String versionLabel(String raw) {
        if (raw == null || raw.isBlank() || raw.equalsIgnoreCase("unknown")) return "";
        // A client-provided version is plain bounded text, not formatting or a click target.
        String plain = raw.replaceAll("[^a-zA-Z0-9._+\\-]", "");
        return plain.substring(0, Math.min(64, plain.length()));
    }

    static Component installedMessage(Component name, String version) {
        return Component.empty().append(name.copy()).append(" 유저가 GCB 모드 ")
                .append(Component.literal(version.isEmpty() ? "버전 미확인" : version).withStyle(ChatFormatting.BLUE))
                .append(" 를 설치했습니다.");
    }

    static Component recommendation() {
        return Component.literal("능력 전용 키를 사용하려면 GCB 모드 설치를 권장합니다. ")
                .append(Component.literal("[GCB 다운로드]").withStyle(style -> style
                        .withColor(ChatFormatting.BLUE).withUnderlined(true)
                        .withClickEvent(new ClickEvent.OpenUrl(URI.create(DOWNLOAD_URL)))))
                .append(" 설치 전에는 HUD에 표시된 기본 키로 플레이할 수 있습니다.");
    }
}
