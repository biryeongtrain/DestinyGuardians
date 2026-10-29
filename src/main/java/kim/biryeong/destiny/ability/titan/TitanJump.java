package kim.biryeong.destiny.ability.titan;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.jump.JumpAbilities;
import kim.biryeong.destiny.ability.jump.JumpPhysics;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.MinecraftServer;
import net.minecraft.server.level.ServerPlayer;

/** Legacy and common hooks share one engine and one per-player tick guard. */
public final class TitanJump extends Ability {
    private final JumpPhysics.Mode mode;
    public TitanJump() { this(TitanAbilities.JUMP, "제어 리프트", JumpPhysics.Mode.TITAN_STRAFE); }
    public TitanJump(Identifier id, String name, JumpPhysics.Mode mode) {
        super(id, GuardianClass.TITAN, AbilitySlot.JUMP, Element.KINETIC, 0, name);
        this.mode = mode;
    }
    public JumpPhysics.Mode mode() { return mode; }
    @Override public boolean activate(ServerPlayer player) { return JumpAbilities.activate(player, this, mode); }
    static void tick(MinecraftServer server) { JumpAbilities.tick(server); }
    public static boolean active(ServerPlayer player) { return JumpAbilities.active(player, JumpPhysics.Kind.LIFT); }
    static void cleanup(ServerPlayer player) { JumpAbilities.cleanup(player); }
    static void clearAll() { JumpAbilities.clearAll(); }
}
