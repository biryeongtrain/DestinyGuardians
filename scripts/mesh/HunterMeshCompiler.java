import com.google.gson.*;
import io.github.toxicity188.javamesh.*;
import org.joml.Vector3f;
import java.nio.file.*;
import java.util.*;

/** Offline compiler; raw item units -> BetterModel's java-mesh convention. */
public class HunterMeshCompiler {
    public static void main(String[] args) throws Exception {
        JsonObject source = JsonParser.parseString(Files.readString(Path.of(args[0]))).getAsJsonObject();
        JsonArray vertices = source.getAsJsonArray("vertices");
        JsonArray triangles = source.getAsJsonArray("triangles");
        if (triangles.size() > 2400) throw new IllegalArgumentException("H28 triangle budget exceeded");
        Map<String, MeshImage> colors = new HashMap<>();
        MeshBuilder builder = MeshBuilder.of(MeshTriangleName.of(args[2], args[2]));
        List<MeshShape> shapes = new ArrayList<>();
        for (JsonElement entry : triangles) {
            JsonObject triangle = entry.getAsJsonObject();
            int color = triangle.get("color").getAsInt();
            String key = Integer.toHexString(color);
            colors.computeIfAbsent(key, ignored -> new MeshImage() {
                public int width() { return 1; }
                public int height() { return 1; }
                public int rgb(int x, int y) { return color; }
            });
            List<MeshPoint> points = new ArrayList<>();
            for (JsonElement index : triangle.getAsJsonArray("v")) {
                JsonArray v = vertices.get(index.getAsInt()).getAsJsonArray();
                float x = v.get(0).getAsFloat(), y = v.get(1).getAsFloat(), z = v.get(2).getAsFloat();
                if (!Float.isFinite(x + y + z)) throw new IllegalArgumentException("Nonfinite vertex");
                // MeshMath flips X/Z and adds .5; vanilla ItemTransform subtracts .5.
                points.add(new MeshPoint(new Vector3f(-(x - 8) / 16, (y - 8) / 16, -(z - 8) / 16)));
            }
            if (points.size() != 3) throw new IllegalArgumentException("Expected triangles");
            shapes.add(new MeshShape(points, key));
        }
        builder.image(colors);
        // Both sides explicit: hand mirroring must never make a thin blade disappear.
        for (MeshShape shape : shapes) builder.load(shape, MeshFace.DOUBLE);
        JsonObject model = builder.toJson();
        JsonArray parts = model.getAsJsonArray("models");
        if (parts.size() != triangles.size() * 3) throw new IllegalStateException("Dropped geometry");
        for (JsonElement part : parts) for (JsonElement v : part.getAsJsonObject().getAsJsonArray("transformation")) {
            if (!Float.isFinite(v.getAsFloat())) throw new IllegalStateException("Nonfinite output matrix");
        }
        // MeshMath's first matrix maps a unit right triangle to the source triangle.
        // The stock builder tiles three opaque half-size quads. Our full-size quad
        // has a high-resolution triangular alpha mask, keeping exactly one layer
        // per source triangle, without any further geometry decimation.
        JsonArray cutout = new JsonArray();
        for (int i = 0; i < parts.size(); i += 3) cutout.add(parts.get(i));
        model.add("models", cutout);
        Files.writeString(Path.of(args[1]), model + "\n");
    }
}
