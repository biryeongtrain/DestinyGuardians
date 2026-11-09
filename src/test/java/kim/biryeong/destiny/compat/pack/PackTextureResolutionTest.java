package kim.biryeong.destiny.compat.pack;

import org.junit.jupiter.api.Test;
import javax.imageio.ImageIO;
import java.awt.image.BufferedImage;
import java.io.*;
import static org.junit.jupiter.api.Assertions.*;

class PackTextureResolutionTest {
    private static byte[] png(BufferedImage image)throws IOException {
        var out=new ByteArrayOutputStream();ImageIO.write(image,"png",out);return out.toByteArray();
    }
    @Test void respectsModelPolicyAndLeavesTextUiAndSmallImagesByteExact()throws Exception {
        assertEquals(1024,PackTextureResolution.limit("assets/bettermodel/textures/item/renamed.png"));
        assertEquals(1024,PackTextureResolution.limit("assets/destiny/textures/item/weapon/w350/whisper_of_the_worm.png"));
        assertEquals(0,PackTextureResolution.limit("assets/destiny/textures/item/hud/scope_w45_beloved_frame.png"));
        assertEquals(0,PackTextureResolution.limit("assets/destiny/textures/font/ui.png"));
        assertEquals(0,PackTextureResolution.limit("assets/minigamelib/textures/item/menu.png"));
        byte[] small=png(new BufferedImage(32,16,BufferedImage.TYPE_INT_ARGB));
        assertSame(small,PackTextureResolution.resize(small,1024));
    }
    @Test void preservesAspectAndOpaqueColorWithoutChangingInput()throws Exception {
        var image=new BufferedImage(8,4,BufferedImage.TYPE_INT_ARGB);
        for(int y=0;y<4;y++)for(int x=0;x<8;x++)image.setRGB(x,y,0xff40a0f0);
        byte[] source=png(image),pin=source.clone();
        var out=ImageIO.read(new ByteArrayInputStream(PackTextureResolution.resize(source,4)));
        assertEquals(4,out.getWidth());assertEquals(2,out.getHeight());
        for(int y=0;y<2;y++)for(int x=0;x<4;x++)assertEquals(0xff40a0f0,out.getRGB(x,y));
        assertArrayEquals(pin,source);
    }
    @Test void retainsThinAlphaCoverageWithoutTransparentColorFringe()throws Exception {
        var image=new BufferedImage(2,2,BufferedImage.TYPE_INT_ARGB);
        image.setRGB(0,0,0xffffffff);image.setRGB(1,0,0x00ff0000);
        image.setRGB(0,1,0x00000000);image.setRGB(1,1,0x000000ff);
        var out=ImageIO.read(new ByteArrayInputStream(PackTextureResolution.resize(png(image),1)));
        assertEquals(0x40ffffff,out.getRGB(0,0));
    }
}
