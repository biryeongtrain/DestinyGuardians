package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import net.minecraft.resources.Identifier;
import org.joml.Matrix4f;
import java.io.*;
import java.nio.charset.StandardCharsets;
import java.nio.file.*;
import java.util.*;
import java.util.zip.*;

/** Server-only companion data: exact selector trees and exact 32-bit matrix components. */
final class ProfileArmCache {
    private static final int MAGIC = 0x44475031, MAX_ENTRIES = 1_000_000, MAX_STRING = 64 * 1024 * 1024;
    static void write(Path path, ProfileArmAssets.Snapshot snapshot) throws IOException {
        try (var out = new DataOutputStream(new BufferedOutputStream(new GZIPOutputStream(Files.newOutputStream(path))))) {
            out.writeInt(MAGIC);
            out.writeInt(snapshot.graphs().size());
            for (var e : new TreeMap<>(snapshot.graphs()).entrySet()) {
                string(out, e.getKey().toString()); string(out, e.getValue().toString());
            }
            out.writeInt(snapshot.poses().size());
            for (var e : new TreeMap<>(snapshot.poses()).entrySet()) {
                string(out, e.getKey()); var p = e.getValue();
                matrix(out, p.right()); matrix(out, p.left()); out.writeBoolean(p.leftArm()); out.writeBoolean(p.upper());
            }
        }
    }
    static ProfileArmAssets.Snapshot read(Path path) throws IOException {
        try (var in = new DataInputStream(new BufferedInputStream(new GZIPInputStream(Files.newInputStream(path))))) {
            if (in.readInt() != MAGIC) throw new IOException("Unknown server pose cache schema");
            var graphs = new HashMap<Identifier, com.google.gson.JsonObject>();
            int count = count(in);
            for (int i=0;i<count;i++) {
                var id = Identifier.parse(string(in)); var graph = JsonParser.parseString(string(in)).getAsJsonObject();
                if (graphs.put(id, graph) != null) throw new IOException("Duplicate cached graph");
            }
            var poses = new HashMap<String, ProfileArmAssets.Pose>();
            count = count(in);
            for (int i=0;i<count;i++) {
                String id = string(in);
                var pose = new ProfileArmAssets.Pose(matrix(in), matrix(in), in.readBoolean(), in.readBoolean());
                if (poses.put(id, pose) != null) throw new IOException("Duplicate cached pose");
            }
            if (in.read() != -1) throw new IOException("Unexpected server pose cache data");
            return new ProfileArmAssets.Snapshot(graphs, poses);
        } catch (IllegalArgumentException | IllegalStateException e) { throw new IOException("Invalid server pose cache", e); }
    }
    private static int count(DataInputStream in) throws IOException {
        int n = in.readInt(); if (n<0 || n>MAX_ENTRIES) throw new IOException("Invalid cache entry count"); return n;
    }
    private static void string(DataOutputStream out, String value) throws IOException {
        byte[] bytes=value.getBytes(StandardCharsets.UTF_8); out.writeInt(bytes.length); out.write(bytes);
    }
    private static String string(DataInputStream in) throws IOException {
        int length=in.readInt(); if(length<0 || length>MAX_STRING) throw new IOException("Invalid cache string length");
        byte[] bytes=in.readNBytes(length); if(bytes.length!=length) throw new EOFException();
        return new String(bytes,StandardCharsets.UTF_8);
    }
    private static void matrix(DataOutputStream out, Matrix4f matrix) throws IOException {
        for(float f:matrix.get(new float[16])) out.writeFloat(f);
    }
    private static Matrix4f matrix(DataInputStream in) throws IOException {
        float[] values=new float[16];
        for(int i=0;i<16;i++){values[i]=in.readFloat();if(!Float.isFinite(values[i]))throw new IOException("Nonfinite cached pose");}
        return new Matrix4f().set(values);
    }
}
