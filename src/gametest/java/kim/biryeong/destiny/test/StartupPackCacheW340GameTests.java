package kim.biryeong.destiny.test;

import kim.biryeong.destiny.compat.pack.StartupPackCache;
import kim.biryeong.destiny.compat.pack.ProfileArmAssets;
import eu.pb4.polymer.autohost.impl.AutoHost;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import java.io.*;
import java.nio.file.*;
import java.security.*;
import java.util.*;
import java.util.zip.ZipFile;

public final class StartupPackCacheW340GameTests {
    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=200000)
    public void startupRestoresCompleteServerSelectorsAndHostedArchive(GameTestHelper h) {
        long deadline=System.nanoTime()+java.util.concurrent.TimeUnit.SECONDS.toNanos(180);
        String expected=System.getProperty("destiny.gametest.packCacheExpected","SAVED");
        h.onEachTick(()->{
            String status=StartupPackCache.status(h.getLevel().getServer());
            h.assertTrue(System.nanoTime()<deadline,Component.literal("Pack cache publication timed out: "+status));
            if(!(status.equals(expected)||expected.equals("SAVED")&&status.equals("HIT"))) {
                if(status.equals("HIT")||status.equals("SAVED"))h.fail(Component.literal("Expected "+expected+", got "+status));
                java.util.concurrent.locks.LockSupport.parkNanos(1_000_000);return;
            }
            var graph=ProfileArmAssets.graph(Identifier.parse("destiny:weapon/ace_of_spades"));
            h.assertTrue(graph!=null,Component.literal("Server selectors must be published with cached ZIP"));
            int poses=verifyPoses(graph);
            h.assertTrue(poses>0,Component.literal("Cached selectors retain their exact hand pose leaves"));
            h.assertTrue(AutoHost.mainPackResult!=null,Component.literal("AutoHost readiness is genuinely published"));
            Path path=AutoHost.getPath(AutoHost.DEFAULT_PATH);
            h.assertTrue(path.toAbsolutePath().normalize().equals(PolymerResourcePackUtils.getMainPath().toAbsolutePath().normalize()),
                    Component.literal("AutoHost serves the actual main archive"));
            try(var zip=new ZipFile(path.toFile())) {
                h.assertTrue(zip.getEntry("pack.mcmeta")!=null&&zip.getEntry("assets/destiny/items/profile_arm.json")!=null,
                        Component.literal("Restored archive includes client pack metadata and arm route"));
                var digest=MessageDigest.getInstance("SHA-1");
                try(var in=new DigestInputStream(Files.newInputStream(path),digest)){in.transferTo(OutputStream.nullOutputStream());}
                h.assertTrue(HexFormat.of().formatHex(digest.digest()).equals(AutoHost.mainPackResult.hash()),
                        Component.literal("Announced client SHA1 matches actual downloadable ZIP bytes"));
            }catch(Exception e){throw new IllegalStateException(e);}
            kim.biryeong.destiny.DestinyGuardians.LOGGER.info("[PackCache QA] {} verified {} pose references, archive {}",status,poses,AutoHost.mainPackResult.hash());
            h.succeed();
        });
    }
    private static int verifyPoses(com.google.gson.JsonElement value) {
        if(value.isJsonArray()){int count=0;for(var child:value.getAsJsonArray())count+=verifyPoses(child);return count;}
        if(!value.isJsonObject())return 0;
        var object=value.getAsJsonObject();
        if(object.has("type")&&"minecraft:model".equals(object.get("type").getAsString())) {
            var pose=ProfileArmAssets.pose(object.get("model").getAsString());
            if(pose==null)throw new IllegalStateException("Cached graph refers to an absent server pose");
            for(float f:pose.right().get(new float[16]))if(!Float.isFinite(f))throw new IllegalStateException("Invalid right matrix");
            for(float f:pose.left().get(new float[16]))if(!Float.isFinite(f))throw new IllegalStateException("Invalid left matrix");
            return 1;
        }
        int count=0;for(var e:object.entrySet())count+=verifyPoses(e.getValue());return count;
    }
}
