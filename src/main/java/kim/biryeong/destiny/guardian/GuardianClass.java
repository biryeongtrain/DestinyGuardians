package kim.biryeong.destiny.guardian;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/** 수호자 직업. */
public enum GuardianClass implements StringRepresentable {
    NONE("none"),
    TITAN("titan"),
    HUNTER("hunter"),
    WARLOCK("warlock");

    public static final Codec<GuardianClass> CODEC = StringRepresentable.fromEnum(GuardianClass::values);

    private final String id;

    GuardianClass(String id) {
        this.id = id;
    }

    @Override
    public String getSerializedName() {
        return id;
    }
}
