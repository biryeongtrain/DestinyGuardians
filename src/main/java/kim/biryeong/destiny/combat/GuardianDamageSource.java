package kim.biryeong.destiny.combat;

import kim.biryeong.destiny.weapon.AmmoGeneration;
import net.minecraft.core.Holder;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.damagesource.DamageSource;
import net.minecraft.world.damagesource.DamageType;

/** The paid shot's source kind survives delayed impacts and later weapon swaps. */
public final class GuardianDamageSource extends DamageSource {
    private final AmmoGeneration.Kind kind;
    public GuardianDamageSource(Holder<DamageType> type, ServerPlayer source, AmmoGeneration attribution) {
        super(type, source);
        kind = attribution.kind();
    }
    public AmmoGeneration.Kind kind() { return kind; }
}
