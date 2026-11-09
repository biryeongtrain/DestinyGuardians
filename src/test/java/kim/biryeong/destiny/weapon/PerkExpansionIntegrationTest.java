package kim.biryeong.destiny.weapon;

import org.junit.jupiter.api.Test;
import org.objectweb.asm.*;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Native damage stage contract, not proof that a live Minecraft mixin transformed successfully. */
class PerkExpansionIntegrationTest {
    @Test void pinnedPlayerDamageHasExactlyOnePostMagicPreAbsorptionInsertionPoint() throws Exception {
        List<String> calls = new ArrayList<>();
        try (var input = getClass().getClassLoader().getResourceAsStream("net/minecraft/world/entity/player/Player.class")) {
            assertNotNull(input);
            new ClassReader(input).accept(new ClassVisitor(Opcodes.ASM9) {
                @Override public MethodVisitor visitMethod(int access,String name,String descriptor,String sig,String[] ex) {
                    if (!name.equals("actuallyHurt")) return null;
                    return new MethodVisitor(Opcodes.ASM9) {
                        @Override public void visitMethodInsn(int opcode,String owner,String name,String descriptor,boolean itf) {
                            calls.add(owner+";"+name+descriptor);
                        }
                    };
                }
            },ClassReader.SKIP_FRAMES|ClassReader.SKIP_DEBUG);
        }
        String owner="net/minecraft/world/entity/player/Player;";
        String armor=owner+"getDamageAfterArmorAbsorb(Lnet/minecraft/world/damagesource/DamageSource;F)F";
        String magic=owner+"getDamageAfterMagicAbsorb(Lnet/minecraft/world/damagesource/DamageSource;F)F";
        String absorption=owner+"getAbsorptionAmount()F";
        assertEquals(1,Collections.frequency(calls,magic));
        assertTrue(calls.indexOf(armor)>=0 && calls.indexOf(armor)<calls.indexOf(magic));
        assertTrue(calls.indexOf(magic)<calls.indexOf(absorption));
    }
}
