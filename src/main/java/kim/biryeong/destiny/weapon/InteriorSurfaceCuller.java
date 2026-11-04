package kim.biryeong.destiny.weapon;

import com.google.gson.JsonArray;
import com.google.gson.JsonElement;
import com.google.gson.JsonObject;

import java.awt.image.BufferedImage;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Set;
import java.util.function.Function;

/** Conservative pack-output optimization, NOT a mesh simplifier. Call once per
 * rigid moving part, never across magazine/cover boundaries. Authoring data stays
 * untouched. A full opaque closed box must enclose ALL eight rendered corners,
 * not merely triangle support or alpha texel centers. Unsupported data stays.
 */
final class InteriorSurfaceCuller {
    private static final Set<String> FACES = Set.of("north", "south", "east", "west", "up", "down");
    private static final double CLEARANCE = 0.0001; // model units; deliberately above double roundoff
    record Removal(String name, String container, double minClearance) {}
    record Result(JsonObject model, List<Removal> removals) {}
    private record Box(JsonObject source, double[] lo, double[] hi, double[] origin, double[][] matrix) {
        double[][] corners() {
            var out = new double[8][3];
            for (int i=0;i<8;i++) {
                double[] p = {(i&1)==0?lo[0]:hi[0], (i&2)==0?lo[1]:hi[1], (i&4)==0?lo[2]:hi[2]};
                for (int a=0;a<3;a++) {
                    out[i][a]=origin[a];
                    for (int b=0;b<3;b++) out[i][a]+=matrix[a][b]*(p[b]-origin[b]);
                }
            }
            return out;
        }
        double clearance(double[][] world) {
            double result=Double.POSITIVE_INFINITY;
            for (var p:world) for (int a=0;a<3;a++) {
                double local=origin[a];
                for (int b=0;b<3;b++) local+=matrix[b][a]*(p[b]-origin[b]);
                result=Math.min(result,Math.min(local-lo[a],hi[a]-local));
            }
            return result;
        }
        double volume() { return (hi[0]-lo[0])*(hi[1]-lo[1])*(hi[2]-lo[2]); }
    }

    static Result cull(JsonObject input, Function<String, BufferedImage> textureLoader) {
        var output=input.deepCopy();
        var removals=new ArrayList<Removal>();
        // Parent geometry, unsupported render modes or exotic fields need separate review.
        if (input.has("parent") || !input.has("elements") || !input.has("textures")
                || input.has("render_type")) return new Result(output,List.of());
        var elements=input.getAsJsonArray("elements");
        var boxes=new ArrayList<Box>();
        var closed=new ArrayList<Integer>();
        var names=new HashSet<String>();
        for (var element:elements) {
            Box b=box(element);
            if (b==null || !b.source.has("name") || !names.add(b.source.get("name").getAsString()))
                return new Result(output,List.of()); // provenance must stay unambiguous
            boxes.add(b);
            if (b.volume()>0 && opaqueClosed(b.source,input.getAsJsonObject("textures"),textureLoader))
                closed.add(boxes.size()-1);
        }
        // Choose a maximal-volume enclosing box. A removed container can only lead
        // to a larger one, so no cycles; resolve to a retained root for auditability.
        int[] owner=new int[boxes.size()];
        java.util.Arrays.fill(owner,-1);
        for (int i=0;i<boxes.size();i++) {
            var corners=boxes.get(i).corners(); double best=-1;
            for (int j:closed) {
                if (i==j || boxes.get(j).volume()<=best) continue;
                if (boxes.get(j).clearance(corners)>CLEARANCE) {
                    owner[i]=j;best=boxes.get(j).volume();
                }
            }
        }
        var kept=new JsonArray();
        for (int i=0;i<boxes.size();i++) {
            if (owner[i]<0) {kept.add(elements.get(i).deepCopy());continue;}
            int root=owner[i],steps=0;
            while (owner[root]>=0 && steps++<boxes.size()) root=owner[root];
            if (steps>=boxes.size()) throw new IllegalStateException("Interior culling containment cycle");
            double margin=boxes.get(root).clearance(boxes.get(i).corners());
            if (!(margin>CLEARANCE)) throw new IllegalStateException("Interior culling lost retained containment");
            removals.add(new Removal(boxes.get(i).source.get("name").getAsString(),
                    boxes.get(root).source.get("name").getAsString(),margin));
        }
        output.add("elements",kept);
        return new Result(output,List.copyOf(removals));
    }

    private static Box box(JsonElement value) {
        try {
            var e=value.getAsJsonObject();
            if (!Set.of("name","from","to","rotation","faces","shade","light_emission").containsAll(e.keySet())) return null;
            double[] lo=vector(e.getAsJsonArray("from")),hi=vector(e.getAsJsonArray("to")),origin={0,0,0},angles={0,0,0};
            int dimensions=0;
            for (int a=0;a<3;a++) {if (hi[a]<lo[a]) return null;if (hi[a]>lo[a]) dimensions++;}
            if (dimensions<2) return null;
            if (e.has("rotation")) {
                var r=e.getAsJsonObject("rotation");origin=vector(r.getAsJsonArray("origin"));
                if (r.has("rescale") && r.get("rescale").getAsBoolean()) return null;
                if (r.has("axis")) {
                    if (!Set.of("origin","axis","angle","rescale").containsAll(r.keySet())) return null;
                    int a="xyz".indexOf(r.get("axis").getAsString());
                    if (a<0 || r.get("axis").getAsString().length()!=1) return null;
                    angles[a]=r.get("angle").getAsDouble();
                } else {
                    if (!Set.of("origin","x","y","z","rescale").containsAll(r.keySet())) return null;
                    for (int a=0;a<3;a++) if (r.has(""+"xyz".charAt(a))) angles[a]=r.get(""+"xyz".charAt(a)).getAsDouble();
                }
            }
            for (double a:angles) if (!Double.isFinite(a)) return null;
            double x=Math.toRadians(angles[0]),y=Math.toRadians(angles[1]),z=Math.toRadians(angles[2]);
            double cx=Math.cos(x),sx=Math.sin(x),cy=Math.cos(y),sy=Math.sin(y),cz=Math.cos(z),sz=Math.sin(z);
            // Installed 26.3 ELEMENT order, not the display/ItemTransform order.
            double[][] matrix={{cz*cy,cz*sy*sx-sz*cx,cz*sy*cx+sz*sx},
                    {sz*cy,sz*sy*sx+cz*cx,sz*sy*cx-cz*sx},{-sy,cy*sx,cy*cx}};
            return new Box(e,lo,hi,origin,matrix);
        } catch (RuntimeException unsupported) {return null;}
    }

    private static double[] vector(JsonArray array) {
        if (array.size()!=3) throw new IllegalArgumentException("Not a vector");
        double[] p=new double[3];
        for (int i=0;i<3;i++) {p[i]=array.get(i).getAsDouble();if (!Double.isFinite(p[i])) throw new IllegalArgumentException("Nonfinite vector");}
        return p;
    }

    private static boolean opaqueClosed(JsonObject element,JsonObject textures,Function<String,BufferedImage> loader) {
        try {
            var faces=element.getAsJsonObject("faces");
            if (!faces.keySet().equals(FACES)) return false;
            for (var value:faces.entrySet()) {
                var face=value.getValue().getAsJsonObject();
                if (!Set.of("texture","uv","rotation").containsAll(face.keySet())) return false;
                String texture=face.get("texture").getAsString();var visited=new HashSet<String>();
                while (texture.startsWith("#")) {
                    if (!visited.add(texture) || !textures.has(texture.substring(1))) return false;
                    texture=textures.get(texture.substring(1)).getAsString();
                }
                if (!texture.matches("[a-z0-9_.-]+:[a-z0-9_./-]+") || texture.contains("..")) return false;
                var image=loader.apply(texture);if (image==null) return false;
                var uv=face.getAsJsonArray("uv");if (uv.size()!=4) return false;
                double[] p=new double[4];
                for (int i=0;i<4;i++) {p[i]=uv.get(i).getAsDouble();if (!Double.isFinite(p[i]) || p[i]<0 || p[i]>16) return false;}
                if (p[0]==p[2] || p[1]==p[3]) return false;
                // One extra texel outside the UV rectangle: conservative for filtering
                // at the current atlas edge, rather than just checking its center.
                int x0=Math.max(0,(int)Math.floor(Math.min(p[0],p[2])*image.getWidth()/16)-1);
                int x1=Math.min(image.getWidth()-1,(int)Math.ceil(Math.max(p[0],p[2])*image.getWidth()/16));
                int y0=Math.max(0,(int)Math.floor(Math.min(p[1],p[3])*image.getHeight()/16)-1);
                int y1=Math.min(image.getHeight()-1,(int)Math.ceil(Math.max(p[1],p[3])*image.getHeight()/16));
                for (int yy=y0;yy<=y1;yy++) for (int xx=x0;xx<=x1;xx++) if ((image.getRGB(xx,yy)>>>24)!=255) return false;
            }
            return true;
        } catch (RuntimeException unsupported) {return false;}
    }
}
