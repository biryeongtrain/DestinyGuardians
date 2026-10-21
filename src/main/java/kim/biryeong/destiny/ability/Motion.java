package kim.biryeong.destiny.ability;

import net.minecraft.network.protocol.game.ClientboundSetEntityMotionPacket;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.player.Input;
import net.minecraft.world.phys.Vec3;

/** 플레이어 이동 보조. 서버에서 속도를 바꾸면 클라이언트에 바로 보낸다. */
public final class Motion {
    private Motion() {
    }

    public static void setVelocity(ServerPlayer player, Vec3 velocity) {
        player.setDeltaMovement(velocity);
        player.connection.send(new ClientboundSetEntityMotionPacket(player));
    }

    /** 수평 시선 방향 (y=0, 정규화). */
    public static Vec3 horizontalLook(ServerPlayer player) {
        Vec3 look = player.getLookAngle();
        Vec3 flat = new Vec3(look.x, 0, look.z);
        return flat.lengthSqr() < 1.0E-6 ? new Vec3(0, 0, 1) : flat.normalize();
    }

    /** 마지막 이동 입력(WASD) 방향. 입력이 없으면 시선 방향. */
    public static Vec3 inputDirection(ServerPlayer player, Input input) {
        int forward = (input.forward() ? 1 : 0) - (input.backward() ? 1 : 0);
        int strafe = (input.left() ? 1 : 0) - (input.right() ? 1 : 0);
        Vec3 look = horizontalLook(player);
        if (forward == 0 && strafe == 0) {
            return look;
        }
        Vec3 left = new Vec3(look.z, 0, -look.x);
        return look.scale(forward).add(left.scale(strafe)).normalize();
    }
}
