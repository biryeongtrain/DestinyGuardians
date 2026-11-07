package kim.biryeong.destiny.compat.pack;

import eu.pb4.polymer.autohost.impl.AutoHost;
import eu.pb4.polymer.resourcepack.api.*;
import eu.pb4.polymer.resourcepack.impl.PolymerResourcePackMod;
import kim.biryeong.destiny.DestinyGuardians;
import kim.biryeong.destiny.mixin.ResourcePackCreatorAccessor;
import kim.biryeong.destiny.weapon.*;
import net.fabricmc.loader.api.FabricLoader;
import net.minecraft.server.MinecraftServer;
import net.minecraft.world.level.storage.LevelResource;
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
        volatile CompletableFuture<String> buildInputs;
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
                String key=inputs.get();
                var hit=s.store.read(key);
                if(hit.isPresent()) {
                    var cached=hit.orElseThrow();
                    var snapshot=ProfileArmCache.read(cached.profiles());
                    validate(snapshot);
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
                miss(s,epoch,"inputs changed or completed output is absent/invalid");
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
                String key=inputs.get();
                if(before==null||!key.equals(before.join())) {
                    DestinyGuardians.LOGGER.warn("Pack inputs changed during generation; output is live but will not be cached");return;
                }
                temporary=Files.createTempFile("destiny-profile-cache-",".gz");
                ProfileArmCache.write(temporary,snapshot);
                if(current!=s||s.epoch!=epoch)return;
                s.store.write(key,output.path(),temporary,output.hash());
                if(current==s&&s.epoch==epoch) {
                    s.state="SAVED";
                    DestinyGuardians.LOGGER.info("Resource pack cache SAVED: ZIP plus {} routes / {} poses; next matching startup reuses them",
                            snapshot.graphs().size(),snapshot.poses().size());
                }
            } catch(Exception e) { DestinyGuardians.LOGGER.warn("Resource pack is live, but its startup cache could not be saved",e); }
            finally { if(temporary!=null)try{Files.deleteIfExists(temporary);}catch(IOException ignored){} }
        });
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
    private static Supplier<String> captureInputs(MinecraftServer server) {
        var loader=FabricLoader.getInstance();
        var paths=new LinkedHashMap<String,Path>();
        var values=new TreeMap<String,String>();values.put("schema","destiny-pack-cache-1");
        for(var mod:loader.getAllMods().stream().sorted(Comparator.comparing(m->m.getMetadata().getId())).toList()) {
            String label="mod/"+mod.getMetadata().getId();values.put(label,mod.getMetadata().getVersion().getFriendlyString());
            int index=0;
            for(var root:mod.getRootPaths()) {
                if(root.getFileSystem().provider().getScheme().equals("jar")) {
                    String uri=root.toUri().toString();int end=uri.indexOf("!/");
                    if(!uri.startsWith("jar:")||end<0)throw new IllegalStateException("Unsupported archive root "+uri);
                    root=Path.of(URI.create(uri.substring(4,end)));
                }
                paths.put(label+"/"+index++,root);
            }
        }
        paths.put("config",loader.getConfigDir());
        paths.put("polymer-source-assets",loader.getGameDir().resolve("polymer/source_assets"));
        paths.put("bettermodel-output",loader.getConfigDir().resolve("bettermodel/build.zip"));
        paths.put("datapacks",server.getWorldPath(LevelResource.DATAPACK_DIR));
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
                return inputs.finish();
            } catch(IOException e) { throw new UncheckedIOException(e); }
        };
    }
}
