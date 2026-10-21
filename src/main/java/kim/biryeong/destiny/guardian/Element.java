package kim.biryeong.destiny.guardian;

import com.mojang.serialization.Codec;
import net.minecraft.util.StringRepresentable;

/** 속성. 색 값은 docs/design/01 팔레트와 같다. */
public enum Element implements StringRepresentable {
    KINETIC("kinetic", 0xE8E8E8, 0xFFFFFF),
    ARC("arc", 0x5FC8FF, 0xC8F4FF),
    SOLAR("solar", 0xFF7A1A, 0xFFD38A),
    VOID("void", 0xA86BFF, 0xE2C8FF);

    public static final Codec<Element> CODEC = StringRepresentable.fromEnum(Element::values);

    private final String id;
    private final int color;
    private final int glow;

    Element(String id, int color, int glow) {
        this.id = id;
        this.color = color;
        this.glow = glow;
    }

    public int color() {
        return color;
    }

    public int glow() {
        return glow;
    }

    @Override
    public String getSerializedName() {
        return id;
    }
}
