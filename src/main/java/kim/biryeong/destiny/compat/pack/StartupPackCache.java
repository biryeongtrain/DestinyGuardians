package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.autohost.impl.AutoHost;
import eu.pb4.polymer.resourcepack.api.*;
import eu.pb4.polymer.resourcepack.impl.PolymerResourcePackMod;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.mixin.ResourcePackCreatorAccessor;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.server.MinecraftServer;
import java.io.*;
import java.net.URI;
import java.nio.file.*;
import java.util.*;
import java.util.concurrent.*;
import java.util.function.Supplier;

/** Reuses completed outputs, including the server selectors that ordinary ZIP reuse would omit. */
public final class StartupPackCache {
    private static volatile Session current;
    private static final class Session {
        final MinecraftServer server;
        final PackCacheStore store;
        volatile String state="CHECKING";
        volatile long epoch;
        volatile CompletableFuture<PackCacheStore.Key> buildInputs;
        final Set<Path> pending=ConcurrentHashMap.newKeySet();
        Session(MinecraftServer server) {
            this.server=server;
            this.store=new PackCacheStore(FabricLoader.getInstance().getGameDir().resolve("polymer/destiny-pack-cache"));
        }
    }
    private StartupPackCache() {}
    static void init() {
        PolymerResourcePackUtils.RESOURCE_PACK_INITIALIZED_EVENT.register(() -> {
            var s=current;
            if(s!=null){s.epoch++;s.state="BUILDING";s.buildInputs=CompletableFuture.supplyAsync(captureInputs(s.server));}
        });
        PolymerResourcePackUtils.RESOURCE_PACK_FINISHED_EVENT.register(result -> {
            var s=current;
            if(s!=null && enabled() && result instanceof OutputGenerator.Result output && !output.hadIssues()) save(s,output);
        });
    }
    static void begin(MinecraftServer server) {
        current=new Session(server);ProfileArmAssets.clear();AutoHost.mainPackResult=null;
    }
    static void stop(MinecraftServer server) {
        var s=current;
        if(s!=null&&s.server==server) {
            current=null;ProfileArmAssets.clear();AutoHost.mainPackResult=null;
            for(var path:s.pending)try{Files.deleteIfExists(path);}catch(IOException ignored){}
            s.pending.clear();
        }
    }
    public static String status(MinecraftServer server) { var s=current;return s!=null&&s.server==server?s.state:"STOPPED"; }
    private static boolean enabled() { return !"false".equalsIgnoreCase(System.getProperty("destiny.packCache.enabled")); }

    static void startOrRestore(MinecraftServer server) {
        var s=current;
        if(s==null||s.server!=server)throw new IllegalStateException("Foreign pack cache server");
        if(!enabled()||Boolean.getBoolean("destiny.packCache.forceBuild")) {
            s.state="BUILDING";AutoHost.startResourcePackGeneration(server);return;
        }
        long epoch=s.epoch,started=System.nanoTime();
        var inputs=captureInputs(server);
        CompletableFuture.runAsync(() -> {
            try {
                var fullKey=inputs.get();String key=fullKey.value();
                var hit=s.store.read(key);
                if(hit.isPresent()) {
                    var cached=hit.orElseThrow();
                    var snapshot=ProfileArmCache.read(cached.profiles());
                    validate(snapshot);
                    // Reuse skips the build that normally publishes the music catalog and pack hash; do it before readiness.
                    kim.biryeong.minigamelib.music.MusicPacks.restore(cached.sha1());
                    if(current!=s||s.epoch!=epoch)return;
                    Path prepared=PackCacheStore.prepare(cached.archive(),PolymerResourcePackUtils.getMainPath());
                    s.pending.add(prepared);
                    if(current!=s||s.epoch!=epoch){s.pending.remove(prepared);Files.deleteIfExists(prepared);return;}
                    server.execute(() -> {
                        try {
                            if(current!=s||s.epoch!=epoch||PolymerResourcePackMod.alreadyGeneration)return;
                            // Only the atomic rename/publication runs here; large copying/parsing stays on the worker.
                            PackCacheStore.install(prepared,PolymerResourcePackUtils.getMainPath());
                            ProfileArmAssets.install(snapshot);
                            PolymerResourcePackMod.useMainPath=true;
                            AutoHost.mainPackResult=new OutputGenerator.Result(PolymerResourcePackUtils.getMainPath(),cached.sha1(),false);
                            s.state="HIT";
                            DestinyGuardians.LOGGER.info("Resource pack cache HIT: restored ZIP, {} routes and {} poses in {} ms; generation skipped",
                                    snapshot.graphs().size(),snapshot.poses().size(),(System.nanoTime()-started)/1_000_000);
                        } catch(IOException e) {
                            DestinyGuardians.LOGGER.warn("Cached ZIP publication failed; regenerating",e);miss(s,epoch,"publication failure");
                        } finally {
                            s.pending.remove(prepared);try{Files.deleteIfExists(prepared);}catch(IOException ignored){}
                        }
                    });
                    return;
                }
                miss(s,epoch,"changed inputs: "+s.store.changedGroups(fullKey.groups())+" (or output absent/invalid)");
            } catch(Exception e) {
                DestinyGuardians.LOGGER.warn("Resource pack cache cannot be restored; generating fresh output",e);
                miss(s,epoch,"restore failure");
            }
        });
    }
    private static void miss(Session s,long epoch,String reason) {
        s.server.execute(() -> {
            if(current!=s||s.epoch!=epoch||PolymerResourcePackMod.alreadyGeneration)return;
            s.state="BUILDING";
            DestinyGuardians.LOGGER.info("Resource pack cache MISS ({}); generating once",reason);
            AutoHost.startResourcePackGeneration(s.server);
        });
    }
    private static void save(Session s,OutputGenerator.Result output) {
        var snapshot=ProfileArmAssets.snapshot();
        long epoch=s.epoch;
        var before=s.buildInputs;
        var inputs=captureInputs(s.server);
        CompletableFuture.runAsync(() -> {
            Path temporary=null;
            try {
                validate(snapshot);
                var fullKey=inputs.get();String key=fullKey.value();
                if(before==null||!key.equals(before.join().value())) {
                    DestinyGuardians.LOGGER.warn("Pack inputs changed during generation ({}); output is live but will not be cached",
                            before==null?"unknown":changed(before.join().groups(),fullKey.groups()));return;
                }
                temporary=Files.createTempFile("destiny-profile-cache-",".gz");
                ProfileArmCache.write(temporary,snapshot);
                if(current!=s||s.epoch!=epoch)return;
                s.store.write(key,fullKey.groups(),output.path(),temporary,output.hash());
                if(current==s&&s.epoch==epoch) {
                    s.state="SAVED";
                    DestinyGuardians.LOGGER.info("Resource pack cache SAVED: ZIP plus {} routes / {} poses; next matching startup reuses them",
                            snapshot.graphs().size(),snapshot.poses().size());
                }
            } catch(Exception e) { DestinyGuardians.LOGGER.warn("Resource pack is live, but its startup cache could not be saved",e); }
            finally { if(temporary!=null)try{Files.deleteIfExists(temporary);}catch(IOException ignored){} }
        });
    }
    private static java.util.List<String> changed(Map<String,String> a,Map<String,String> b) {
        var out=new TreeSet<String>();
        for(var e:b.entrySet())if(!e.getValue().equals(a.get(e.getKey())))out.add(e.getKey());
        for(var k:a.keySet())if(!b.containsKey(k))out.add(k);
        return java.util.List.copyOf(out);
    }
    private static void validate(ProfileArmAssets.Snapshot snapshot) throws IOException {
        if(!ProfileWeaponView.enabled()) {
            if(!snapshot.graphs().isEmpty()||!snapshot.poses().isEmpty())throw new IOException("Unexpected profile-view state");
            return;
        }
        var expected=new HashSet<>(WeaponFirstPersonHands.sources());expected.retainAll(WeaponPackRoots.activeWithSkins());
        if(!snapshot.graphs().keySet().equals(expected)||snapshot.poses().isEmpty())
            throw new IOException("Cached server graphs do not match registered weapon routes");
    }
    /** Capture registration metadata now; all disk reads run on the worker. */
    private static Supplier<PackCacheStore.Key> captureInputs(MinecraftServer server) {
        var loader=FabricLoader.getInstance();
        var paths=new LinkedHashMap<String,Path>();
        // Other mods contribute to the pack only through their assets (and the version covering registration code),
        // so their classes, data and metadata must not invalidate a Destiny pack that would be byte-identical.
        var assetPaths=new LinkedHashMap<String,Path>();
        var values=new TreeMap<String,String>();values.put("schema","destiny-pack-cache-2");
        for(var mod:loader.getAllMods().stream().sorted(Comparator.comparing(m->m.getMetadata().getId())).toList()) {
            String label="mod/"+mod.getMetadata().getId();values.put(label,mod.getMetadata().getVersion().getFriendlyString());
            int index=0;
            for(var root:mod.getRootPaths()) {
                if(root.getFileSystem().provider().getScheme().equals("jar")) {
                    String uri=root.toUri().toString();int end=uri.indexOf("!/");
                    if(!uri.startsWith("jar:")||end<0)throw new IllegalStateException("Unsupported archive root "+uri);
                    root=Path.of(URI.create(uri.substring(4,end)));
                }
                ((mod.getMetadata().getId().equals("destiny")?paths:assetPaths)).put(label+"/"+index++,root);
            }
        }
        // Only configuration that feeds the pack. Other mods' configs are rewritten at runtime and never reach it.
        for(String dir:new String[]{"destiny","bettermodel","minigame-lib"})paths.put("config/"+dir,loader.getConfigDir().resolve(dir));
        paths.put("config/polymer-pack",loader.getConfigDir().resolve("polymer/resource-pack.json"));
        paths.put("polymer-source-assets",loader.getGameDir().resolve("polymer/source_assets"));
        paths.put("bettermodel-output",loader.getConfigDir().resolve("bettermodel/build.zip"));
        var creator=PolymerResourcePackUtils.getInstance();
        int index=0;
        for(var path:((ResourcePackCreatorAccessor)(Object)creator).destiny$sourcePaths().stream().sorted().toList())
            paths.put("registered-source/"+index++,path);
        // Polymer's configured external ZIP paths are inputs too (including absent files later added by an operator).
        Path packConfig=loader.getConfigDir().resolve("polymer/resource-pack.json");
        if(Files.isRegularFile(packConfig))try {
            var config=com.google.gson.JsonParser.parseString(Files.readString(packConfig)).getAsJsonObject();
            var zips=config.getAsJsonArray("include_zips");
            if(zips!=null)for(var zip:zips)paths.put("included-zip/"+zip.getAsString(),loader.getGameDir().resolve(zip.getAsString()));
        } catch(IOException e) { throw new UncheckedIOException(e); }
        for(var entry:System.getProperties().entrySet()) {
            String key=entry.getKey().toString();
            if(key.startsWith("destiny.")&&!key.startsWith("destiny.packCache.")&&!key.startsWith("destiny.gametest."))
                values.put(key,entry.getValue().toString());
        }
        values.put("pack-description",String.valueOf(creator.getPackDescription()));
        values.put("pack-icon",creator.getPackIcon()==null?"none":Base64.getEncoder().encodeToString(creator.getPackIcon()));
        values.put("main-uuid",PolymerResourcePackUtils.getMainUuid().toString());
        return () -> {
            try {
                var inputs=new PackCacheStore.Inputs();
                values.forEach(inputs::text);
                for(var e:paths.entrySet())inputs.path(e.getKey(),e.getValue());
                for(var e:assetPaths.entrySet())inputs.assetsOnly(e.getKey(),e.getValue(),"assets/","pack.mcmeta");
                return inputs.key();
            } catch(IOException e) { throw new UncheckedIOException(e); }
        };
    }
}
