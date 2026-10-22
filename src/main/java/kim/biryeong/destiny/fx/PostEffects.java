package kim.biryeong.destiny.fx;

import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.guardian.Element;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.server.level.ServerPlayer;

import java.util.HashMap;
import java.util.Map;
import java.util.Objects;
import java.util.UUID;

/**
 * 26.3 포스트 이펙트 켜기·끄기 (docs/design/07, 21).
 * 모든 호출은 서버 스레드에서 한다. 서버는 클라이언트의 실제 적용 여부를 알 수 없다.
 */
public final class PostEffects {
    public static final int ACTIVATION_PULSE_TICKS = 10;
    public static final int IMPACT_PULSE_TICKS = 4;

    // UUID당 한 슬롯. 지속 궁극기 효과 및 다른 소유자의 효과 목록은 관리하지 않는다.
    private static final Map<UUID, Pulse> PULSES = new HashMap<>();

    private PostEffects() {
    }

    public static Identifier superEffect(Element element) {
        return DestinyGuardians.id("super/" + element.getSerializedName() + "_active");
    }

    public static void enter(ServerPlayer player, Element element) {
        player.addPostEffect(superEffect(element));
    }

    public static void exit(ServerPlayer player, Element element) {
        player.removePostEffect(superEffect(element));
    }

    /**
     * Arc/Solar/Void의 발동(false) 또는 명중(true) 펄스를 요청한다. Kinetic은 무시한다.
     * 중복 요청은 수명을 연장하지 않는다. 명중은 발동을 한 번 선점할 수 있다.
     * 실제로 새로 추가한 ID만 소유하므로 이미 수동으로 켠 같은 ID도 나중에 지우지 않는다.
     */
    public static void pulse(ServerPlayer player, Element element, boolean impact) {
        Objects.requireNonNull(player, "player");
        Objects.requireNonNull(element, "element");
        if (element == Element.KINETIC) {
            return;
        }
        if (!eligible(player)) {
            cancel(player);
            return;
        }

        MinecraftServer server = player.level().getServer();
        UUID uuid = player.getUUID();
        Pulse current = PULSES.get(uuid);
        if (current != null && (current.player() != player || current.level() != player.level()
                || current.expired(server) || !player.getPostEffects().contains(current.effect()))) {
            PULSES.remove(uuid);
            current.remove();
            current = null;
        }
        if (current != null) {
            if (!impact || current.impact()) {
                return;
            }
            // 명중 피드백이 발동 플래시에 가려지지 않도록 교체한다. 중복 명중은 위에서 억제한다.
            cancel(player);
        }

        Identifier effect = DestinyGuardians.id("super/" + element.getSerializedName()
                + (impact ? "_impact_pulse" : "_activation_pulse"));
        if (player.addPostEffect(effect)) {
            PULSES.put(uuid, new Pulse(player, player.level(), effect, impact, server.getTickCount(),
                    impact ? IMPACT_PULSE_TICKS : ACTIVATION_PULSE_TICKS));
        }
    }

    /** 서버당 END_SERVER_TICK에서 한 번 호출한다. 차원·플레이어 교체·사망·접속 종료도 검사한다. */
    public static void tick(MinecraftServer server) {
        var iterator = PULSES.entrySet().iterator();
        while (iterator.hasNext()) {
            var entry = iterator.next();
            Pulse pulse = entry.getValue();
            if (pulse.level().getServer() != server) {
                continue;
            }
            ServerPlayer player = pulse.player();
            ServerPlayer online = server.getPlayerList().getPlayer(entry.getKey());
            if (!eligible(player) || player.level() != pulse.level()
                    // 연결된 임베디드 테스트 플레이어는 PlayerList에 없을 수 있다.
                    || (online != null && online != player)
                    || pulse.expired(server) || !player.getPostEffects().contains(pulse.effect())) {
                pulse.remove();
                iterator.remove();
            }
        }
    }

    /** 이 인스턴스가 소유한 펄스만 취소한다. 지속 궁극기 효과는 exit로 따로 종료한다. */
    public static void cancel(ServerPlayer player) {
        Pulse pulse = PULSES.get(player.getUUID());
        if (pulse != null && pulse.player() == player) {
            PULSES.remove(player.getUUID());
            pulse.remove();
        }
    }

    /** 서버 종료/모드 정리 시 호출한다. 소유한 펄스 ID만 제거하고 참조를 모두 해제한다. */
    public static void clearAll() {
        PULSES.values().forEach(Pulse::remove);
        PULSES.clear();
    }

    private static boolean eligible(ServerPlayer player) {
        return player.isAlive() && !player.isRemoved() && !player.hasDisconnected();
    }

    private record Pulse(ServerPlayer player, ServerLevel level, Identifier effect, boolean impact,
                         int startedAt, int duration) {
        private boolean expired(MinecraftServer server) {
            // 짧은 구간의 차이만 사용하므로 tick 카운터 int 래핑에도 안전하다. 월드 시간과 독립적이다.
            return server.getTickCount() - startedAt >= duration;
        }

        private void remove() {
            player.removePostEffect(effect);
        }
    }
}
