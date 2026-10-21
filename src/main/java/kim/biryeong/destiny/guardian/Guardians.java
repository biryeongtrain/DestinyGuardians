package kim.biryeong.destiny.guardian;

import kim.biryeong.destiny.DestinyGuardians;
import net.fabricmc.fabric.api.attachment.v1.AttachmentRegistry;
import net.fabricmc.fabric.api.attachment.v1.AttachmentType;
import net.minecraft.server.level.ServerPlayer;

import java.util.Map;
import java.util.UUID;
import java.util.concurrent.ConcurrentHashMap;

/** 수호자 상태 접근점. */
public final class Guardians {
    public static final AttachmentType<GuardianData> DATA = AttachmentRegistry.create(
            DestinyGuardians.id("guardian"),
            builder -> builder.persistent(GuardianData.CODEC).copyOnDeath().initializer(GuardianData::new));

    private static final Map<UUID, GuardianRuntime> RUNTIME = new ConcurrentHashMap<>();

    private Guardians() {
    }

    public static void init() {
        // 클래스 로딩으로 첨부 타입을 등록한다.
    }

    public static GuardianData data(ServerPlayer player) {
        return player.getAttachedOrCreate(DATA);
    }

    public static GuardianRuntime runtime(ServerPlayer player) {
        return RUNTIME.computeIfAbsent(player.getUUID(), id -> new GuardianRuntime());
    }

    public static void forget(ServerPlayer player) {
        RUNTIME.remove(player.getUUID());
    }

    public static boolean isGuardian(ServerPlayer player) {
        return data(player).guardianClass() != GuardianClass.NONE;
    }
}
