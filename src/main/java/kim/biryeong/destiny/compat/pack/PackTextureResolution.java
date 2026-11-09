package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;
import kim.biryeong.destiny.DestinyGuardians;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/** Display-size policy for model textures. Authored PNGs, normalized UVs and font/UI art stay intact. */
public final class PackTextureResolution {
    private static boolean initialized;
    private PackTextureResolution() { }

    public static synchronized void init() {
        if (initialized) return;
        initialized = true;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder -> builder.addPreFinishTask(PackTextureResolution::prepare));
    }

    static int limit(String path) {
        if (!path.endsWith(".png")) return 0;
        return path.startsWith("assets/bettermodel/textures/item/")
                || path.startsWith("assets/destiny/textures/item/weapon/w350/")
                || path.startsWith("assets/destiny/textures/item/class_ability/")
                || path.equals("assets/destiny/textures/item/tutorial/ghost.png") ? 1024 : 0;
    }

    private static void prepare(ResourcePackBuilder builder) {
        var animated = new HashSet<String>();
        builder.forEachResource((path,data) -> {
            if (path.endsWith(".png.mcmeta")) {
                try {
                    if (JsonParser.parseString(data.asString()).getAsJsonObject().has("animation"))
                        animated.add(path.substring(0,path.length()-7));
                } catch (RuntimeException malformedMetadata) {
                    animated.add(path.substring(0,path.length()-7));
                }
            }
        });
        // Cache belongs to this pack build, including lazily converted upstream bytes.
        var cache = new ConcurrentHashMap<String,byte[]>();
        var changed = new ArrayList<String>();
        long[] pixels = {0,0};
        builder.forEachResource((path,data) -> {
            int cap=limit(path);
            if(cap==0||animated.contains(path))return;
            byte[] src=data.readAllBytes(), out=resize(src,cap);
            cache.put(PackAtlasRouting.sha256(src),out);
            if(!Arrays.equals(src,out)) {
                changed.add(path);
                pixels[0]+=area(src);pixels[1]+=area(out);
            }
        });
        builder.addResourceConverter((path,data) -> {
            if(data==null||limit(path)==0||animated.contains(path))return data;
            byte[] src=data.readAllBytes();
            byte[] out=cache.computeIfAbsent(PackAtlasRouting.sha256(src),ignored -> resize(src,limit(path)));
            return Arrays.equals(src,out)?data:PackResource.of(out);
        });
        DestinyGuardians.LOGGER.info("Model texture resolution: {} planned reductions, {} -> {} pixels; original art retained: {}",
                changed.size(),pixels[0],pixels[1],changed);
    }

    private static long area(byte[] png) {
        return (long)integer(png,16)*integer(png,20);
    }
    private static int integer(byte[] b,int p) {
        return ((b[p]&255)<<24)|((b[p+1]&255)<<16)|((b[p+2]&255)<<8)|(b[p+3]&255);
    }

    /** Area filter in premultiplied-alpha space: transparent RGB cannot darken a bone/leaf edge. */
    static byte[] resize(byte[] png,int maximum) {
        if(maximum<1)throw new IllegalArgumentException("Positive texture limit required");
        if(png.length<24||png[0]!=(byte)137||png[1]!='P'||png[2]!='N'||png[3]!='G')return png;
        int width=integer(png,16),height=integer(png,20);
        if(width<=maximum&&height<=maximum)return png;
        try {
            var source=ImageIO.read(new ByteArrayInputStream(png));
            if(source==null)return png;
            double scale=maximum/(double)Math.max(width,height);
            int w=Math.max(1,(int)Math.round(width*scale)),h=Math.max(1,(int)Math.round(height*scale));
            var result=new BufferedImage(w,h,BufferedImage.TYPE_INT_ARGB);
            for(int y=0;y<h;y++)for(int x=0;x<w;x++) {
                int x0=x*width/w,x1=(x+1)*width/w,y0=y*height/h,y1=(y+1)*height/h;
                long alpha=0,red=0,green=0,blue=0;
                for(int sy=y0;sy<y1;sy++)for(int sx=x0;sx<x1;sx++) {
                    int c=source.getRGB(sx,sy),a=c>>>24;alpha+=a;
                    red+=(long)((c>>>16)&255)*a;green+=(long)((c>>>8)&255)*a;blue+=(long)(c&255)*a;
                }
                int samples=(x1-x0)*(y1-y0),a=(int)((alpha+samples/2)/samples);
                int color=alpha==0?0:(a<<24)|((int)((red+alpha/2)/alpha)<<16)
                        |((int)((green+alpha/2)/alpha)<<8)|(int)((blue+alpha/2)/alpha);
                result.setRGB(x,y,color);
            }
            var out=new ByteArrayOutputStream();
            if(!ImageIO.write(result,"png",out))throw new IOException("No PNG writer");
            return out.toByteArray();
        } catch(IOException e) {throw new UncheckedIOException("Cannot resize model texture",e);}
    }
}
