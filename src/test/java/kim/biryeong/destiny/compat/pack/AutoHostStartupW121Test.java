package kim.biryeong.destiny.compat.pack;

import org.junit.jupiter.api.Test;
import org.objectweb.asm.*;
import java.io.IOException;
import java.util.*;
import static org.junit.jupiter.api.Assertions.*;

/** Dependency/adapter bytecode contract, NOT proof of runtime mixin application. */
class AutoHostStartupW121Test {
    private static final String DESC = "(Lnet/minecraft/server/MinecraftServer;)V";
    private static final String TARGET = "Leu/pb4/polymer/autohost/impl/AutoHost;startResourcePackGeneration" + DESC;

    private static void read(String resource, ClassVisitor visitor) throws IOException {
        try (var input = AutoHostStartupW121Test.class.getClassLoader().getResourceAsStream(resource + ".class")) {
            assertNotNull(input, resource);
            new ClassReader(input).accept(visitor, ClassReader.SKIP_DEBUG | ClassReader.SKIP_FRAMES);
        }
    }

    @Test void pinnedAutohostInitStillHasExactlyTwoGenerationSites() throws IOException {
        var calls = new ArrayList<String>();
        read("eu/pb4/polymer/autohost/impl/AutoHost", new ClassVisitor(Opcodes.ASM9) {
            @Override public MethodVisitor visitMethod(int access, String name, String desc, String sig, String[] ex) {
                if (!name.equals("init") || !desc.equals(DESC)) return null;
                assertTrue((access & Opcodes.ACC_STATIC) != 0);
                return new MethodVisitor(Opcodes.ASM9) {
                    @Override public void visitMethodInsn(int op, String owner, String name, String d, boolean itf) {
                        if (owner.equals("eu/pb4/polymer/autohost/impl/AutoHost") && name.equals("startResourcePackGeneration")) {
                            assertEquals(Opcodes.INVOKESTATIC, op);
                            calls.add(d);
                        }
                    }
                };
            }
        });
        assertEquals(List.of(DESC, DESC), calls, "Review dependency lifecycle before changing injection cardinality");
    }

    @Test void redirectIsNarrowAndFailsClosedOnCallsiteDrift() throws IOException {
        var values = new HashMap<String, Object>();
        var methodNames = new ArrayList<String>();
        read("kim/biryeong/destiny/mixin/AutoHostStartupMixin", new ClassVisitor(Opcodes.ASM9) {
            @Override public MethodVisitor visitMethod(int access, String name, String desc, String sig, String[] ex) {
                return new MethodVisitor(Opcodes.ASM9) {
                    @Override public AnnotationVisitor visitAnnotation(String type, boolean visible) {
                        if (!type.equals("Lorg/spongepowered/asm/mixin/injection/Redirect;")) return null;
                        methodNames.add(name);
                        assertTrue((access & Opcodes.ACC_STATIC) != 0);
                        assertEquals(DESC, desc);
                        return new AnnotationVisitor(Opcodes.ASM9) {
                            @Override public void visit(String key, Object value) { values.put(key, value); }
                            @Override public AnnotationVisitor visitArray(String key) {
                                return new AnnotationVisitor(Opcodes.ASM9) {
                                    @Override public void visit(String unused, Object value) { values.put(key, value); }
                                    @Override public AnnotationVisitor visitAnnotation(String unused, String annotationType) {
                                        return new AnnotationVisitor(Opcodes.ASM9) {
                                            @Override public void visit(String k, Object v) { values.put(key + "." + k, v); }
                                        };
                                    }
                                };
                            }
                            @Override public AnnotationVisitor visitAnnotation(String key, String d) {
                                return new AnnotationVisitor(Opcodes.ASM9) {
                                    @Override public void visit(String k, Object v) { values.put(key + "." + k, v); }
                                };
                            }
                        };
                    }
                };
            }
        });
        assertEquals(List.of("destiny$orderStartupPack"), methodNames);
        assertEquals("init" + DESC, values.get("method"));
        assertEquals(2, values.get("require"));
        assertEquals(2, values.get("allow"));
        assertEquals("INVOKE", values.get("at.value"));
        assertEquals(TARGET, values.get("at.target"));
    }
}
