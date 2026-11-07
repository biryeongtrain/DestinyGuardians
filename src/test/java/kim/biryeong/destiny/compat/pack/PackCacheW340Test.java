package kim.biryeong.destiny.compat.pack;

import com.google.gson.JsonParser;
import net.minecraft.resources.Identifier;
import org.joml.Matrix4f;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;
import java.nio.file.*;
import java.nio.file.attribute.FileTime;
import java.util.*;
import java.util.zip.*;
import static org.junit.jupiter.api.Assertions.*;

class PackCacheW340Test {
    @TempDir Path dir;
    private Path zip(String name, String value, long time) throws Exception {
        Path path=dir.resolve(name);
        try(var out=new ZipOutputStream(Files.newOutputStream(path))) {
            var entry=new ZipEntry("pack.mcmeta");entry.setTime(time);out.putNextEntry(entry);out.write(value.getBytes());out.closeEntry();
        }
        return path;
    }
    @Test void matchingOutputsRestoreAndInputChangesMiss() throws Exception {
        var store=new PackCacheStore(dir.resolve("cache"));var pack=zip("generated.zip","{}",100000);
        var profile=dir.resolve("state");Files.writeString(profile,"server data");
        store.write("inputs-a",pack,profile,PackCacheStore.digest(pack,"SHA-1"));
        var hit=store.read("inputs-a").orElseThrow();assertArrayEquals(Files.readAllBytes(pack),Files.readAllBytes(hit.archive()));
        assertTrue(store.read("inputs-b").isEmpty());
        Path target=dir.resolve("polymer/resource_pack.zip");PackCacheStore.replace(hit.archive(),target);
        assertEquals(hit.sha1(),PackCacheStore.digest(target,"SHA-1"));
    }
    @Test void corruptZipOrCompanionNeverReturnsAHit() throws Exception {
        var store=new PackCacheStore(dir.resolve("cache"));var pack=zip("generated.zip","{}",100000);
        var profile=dir.resolve("state");Files.writeString(profile,"state");String hash=PackCacheStore.digest(pack,"SHA-1");
        store.write("key",pack,profile,hash);
        Files.writeString(dir.resolve("cache/profiles.bin.gz"),"broken");assertTrue(store.read("key").isEmpty());
        store.write("key",pack,profile,hash);
        Files.writeString(dir.resolve("cache/pack.zip"),"broken");assertTrue(store.read("key").isEmpty());
    }
    @Test void incompleteOrInvalidManifestsCannotAuthorizeExistingOutput() throws Exception {
        var store=new PackCacheStore(dir.resolve("cache"));assertTrue(store.read("key").isEmpty());
        Files.createDirectories(dir.resolve("cache"));Files.writeString(dir.resolve("cache/manifest.json"),"{");
        assertTrue(store.read("key").isEmpty());
        Files.writeString(dir.resolve("cache/manifest.json"),"null");assertTrue(store.read("key").isEmpty());
    }
    @Test void changedArchiveDuringPublicationCannotReplaceGoodCache() throws Exception {
        var store=new PackCacheStore(dir.resolve("cache"));var pack=zip("generated.zip","{}",100000);
        var profile=dir.resolve("state");Files.writeString(profile,"state");String hash=PackCacheStore.digest(pack,"SHA-1");
        store.write("old",pack,profile,hash);zip("generated.zip","{new}",100000);
        assertThrows(java.io.IOException.class,()->store.write("new",pack,profile,hash));
        assertTrue(store.read("old").isPresent());assertTrue(store.read("new").isEmpty());
    }
    @Test void fingerprintUsesContentAndIgnoresFileAndArchiveTimestamps() throws Exception {
        Path folder=dir.resolve("assets");Files.createDirectories(folder);Path f=folder.resolve("model.json");Files.writeString(f,"aaaa");
        String first=new PackCacheStore.Inputs().path("mod",folder).finish();
        Files.setLastModifiedTime(f,FileTime.fromMillis(10));
        assertEquals(first,new PackCacheStore.Inputs().path("mod",folder).finish());
        Files.writeString(f,"bbbb");Files.setLastModifiedTime(f,FileTime.fromMillis(10));
        assertNotEquals(first,new PackCacheStore.Inputs().path("mod",folder).finish());
        var a=zip("a.zip","{}",100000);var b=zip("b.zip","{}",500000);
        assertEquals(new PackCacheStore.Inputs().path("same",a).finish(),new PackCacheStore.Inputs().path("same",b).finish());
        zip("b.zip","changed",500000);
        assertNotEquals(new PackCacheStore.Inputs().path("same",a).finish(),new PackCacheStore.Inputs().path("same",b).finish());
    }
    @Test void fingerprintsArePortableAndTrackAddedRemovedInputs() throws Exception {
        Path a=dir.resolve("server-a"),b=dir.resolve("server-b");Files.createDirectories(a);Files.createDirectories(b);
        Files.writeString(a.resolve("one"),"same");Files.writeString(b.resolve("one"),"same");
        assertEquals(new PackCacheStore.Inputs().path("config",a).finish(),new PackCacheStore.Inputs().path("config",b).finish());
        String old=new PackCacheStore.Inputs().path("config",a).finish();Files.writeString(a.resolve("two"),"");
        assertNotEquals(old,new PackCacheStore.Inputs().path("config",a).finish());
        Files.delete(a.resolve("two"));assertEquals(old,new PackCacheStore.Inputs().path("config",a).finish());
    }
    @Test void serverCompanionKeepsExactTreesFlagsAndMatrixComponents() throws Exception {
        var id=Identifier.parse("destiny:weapon/test");
        var graph=JsonParser.parseString("{\"type\":\"minecraft:model\",\"model\":\"destiny:pose\"}").getAsJsonObject();
        var right=new Matrix4f().translate(.125f,-.3f,2f).rotateXYZ(.3f,-1.1f,2.8f).scale(.1f,.2f,.3f);
        var left=new Matrix4f().translate(8,-2,3).rotateZ(-.7f);
        var state=new ProfileArmAssets.Snapshot(Map.of(id,graph),Map.of("destiny:pose",new ProfileArmAssets.Pose(right,left,true,false)));
        Path p=dir.resolve("profiles.gz");ProfileArmCache.write(p,state);var loaded=ProfileArmCache.read(p);
        assertEquals(state.graphs(),loaded.graphs());var pose=loaded.poses().get("destiny:pose");
        assertArrayEquals(right.get(new float[16]),pose.right().get(new float[16]));
        assertArrayEquals(left.get(new float[16]),pose.left().get(new float[16]));assertTrue(pose.leftArm());assertFalse(pose.upper());
        byte[] bytes=Files.readAllBytes(p);Files.write(p,Arrays.copyOf(bytes,bytes.length/2));
        assertThrows(java.io.IOException.class,()->ProfileArmCache.read(p));
    }
}
