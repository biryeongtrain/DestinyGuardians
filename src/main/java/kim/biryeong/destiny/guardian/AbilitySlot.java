package kim.biryeong.destiny.guardian;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/** 능력 슬롯. */
public enum AbilitySlot implements StringRepresentable {
    SUPER("super"),
    GRENADE("grenade"),
    MELEE("melee"),
    CLASS_ABILITY("class_ability"),
    JUMP("jump");

    public static final Codec<AbilitySlot> CODEC = StringRepresentable.fromEnum(AbilitySlot::values);

    private final String id;

    AbilitySlot(String id) {
        this.id = id;
    }

    @Override
    public String getSerializedName() {
        return id;
    }
}
