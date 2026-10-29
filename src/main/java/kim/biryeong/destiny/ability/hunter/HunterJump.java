package kim.biryeong.destiny.ability.hunter;

import kim.biryeong.destiny.ability.Ability;
import kim.biryeong.destiny.ability.jump.JumpAbilities;
import kim.biryeong.destiny.ability.jump.JumpPhysics;
import kim.biryeong.destiny.guardian.AbilitySlot;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerPlayer;

/** Hunter impulses and Arc-only Blink, backed by the shared airborne budget. */
public final class HunterJump extends Ability {
    private final JumpPhysics.Mode mode;
    private final double defaultStrength;

    public HunterJump(Identifier id, String name, int extraJumps, double strength) {
        this(id, name, extraJumps == 2 ? JumpPhysics.Mode.HUNTER_TRIPLE : JumpPhysics.Mode.HUNTER_HIGH, strength);
    }
    public HunterJump(Identifier id, String name, JumpPhysics.Mode mode) {
        this(id, name, mode, mode.impulse);
    }
    private HunterJump(Identifier id, String name, JumpPhysics.Mode mode, double strength) {
        super(id, GuardianClass.HUNTER, AbilitySlot.JUMP,
                mode == JumpPhysics.Mode.HUNTER_BLINK ? Element.ARC : Element.KINETIC, 0, name);
        this.mode = mode;
        this.defaultStrength = strength;
    }
    public int extraJumps() { return mode == JumpPhysics.Mode.HUNTER_TRIPLE ? 2 : 1; }
    public JumpPhysics.Mode mode() { return mode; }
    public double strength() { return JumpPhysics.finite(param("strength", defaultStrength), defaultStrength, .1, .9); }
    @Override public boolean activate(ServerPlayer player) { return JumpAbilities.activate(player, this, mode); }
}
