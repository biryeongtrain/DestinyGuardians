package kim.biryeong.destiny.ability.warlock;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.jump.JumpAbilities;
import kim.biryeong.destiny.ability.jump.JumpPhysics;
import kim.biryeong.destiny.guardian.*;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/** Bounded cancellable glide carries existing ascent; Void Blink is a separate option. */
public final class WarlockJump extends Ability {
    private final JumpPhysics.Mode mode;
    public WarlockJump(Identifier id) { this(id, "균형 활공", JumpPhysics.Mode.WARLOCK_BALANCED); }
    public WarlockJump(Identifier id, String name, JumpPhysics.Mode mode) {
        super(id, GuardianClass.WARLOCK, AbilitySlot.JUMP,
                mode == JumpPhysics.Mode.WARLOCK_BLINK ? Element.VOID : Element.KINETIC, 0, name);
        this.mode = mode;
    }
    public JumpPhysics.Mode mode() { return mode; }
    @Override public boolean activate(ServerPlayer player) { return JumpAbilities.activate(player, this, mode); }
    static void tick() { JumpAbilities.tickLegacyWarlock(); }
    static void cleanup(ServerPlayer player) { JumpAbilities.cleanup(player); }
    public static boolean active(ServerPlayer player) { return JumpAbilities.active(player, JumpPhysics.Kind.GLIDE); }
}
