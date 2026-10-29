package kim.biryeong.destiny.test;

import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import java.awt.image.BufferedImage;
import java.io.ByteArrayOutputStream;
import javax.imageio.ImageIO;

/** Opt-in isolated QA skin. Never included by the production source set. */
final class SkinLandmarksW254 {
    static void register() {
        if (!Boolean.getBoolean("destiny.qa.skinLandmarks")) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(builder -> {
            try {
                var image = new BufferedImage(64,64,BufferedImage.TYPE_INT_ARGB);
                for(int y=0;y<64;y++) for(int x=0;x<64;x++) image.setRGB(x,y,0xff909090);
                // Skin UV Y increases from shoulder to wrist. Opaque sleeves use
                // the same landmarks so neither sleeve visibility setting conceals it.
                for(int base : new int[]{16,32,48}) {
                    int minX=base==48?32:40, maxX=base==48?64:56;
                    for(int y=base+4;y<base+16;y++) for(int x=minX;x<maxX;x++) {
                        int row=y-base-4;
                        int color=row<2?0xffff3030:row<4?0xffffdd20:row<8?0xff30ee50:0xff3070ff;
                        image.setRGB(x,y,color);
                    }
                }
                // The left sleeve island is X48..63 rather than X32..47; the
                // wide range above covers both; shoulder and wrist caps are explicit.
                for(int base:new int[]{16,32,48}) for(int x=0;x<64;x++)
                    if((base==48&&x>=36)||(base!=48&&x>=44&&x<52))
                        for(int y=base;y<base+4;y++) image.setRGB(x,y,x<(base==48?40:48)?0xffff3030:0xff3070ff);
                var bytes=new ByteArrayOutputStream();ImageIO.write(image,"png",bytes);
                for(String body:new String[]{"wide","slim"})
                    for(String name:new String[]{"alex","ari","efe","kai","makena","noor","steve","sunny","zuri"})
                        builder.addData("assets/minecraft/textures/entity/player/"+body+"/"+name+".png",PackResource.of(bytes.toByteArray()));
            } catch (java.io.IOException error) { throw new IllegalStateException(error); }
        });
    }
}
