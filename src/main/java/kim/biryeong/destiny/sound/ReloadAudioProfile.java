package kim.biryeong.destiny.sound;

import com.google.gson.Gson;
import kim.biryeong.destiny.weapon.*;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Offline pitch-preserving full-magazine variants; never treats a whole reload as one shell insert. */
public final class ReloadAudioProfile {
    public record Clip(String id, int ticks, String event, String sourceEvent, String sourceSha256, String asset) {}
    private record Data(String stage, Clip[] entries) {}
    private static final Map<String, Clip> CLIPS = load();
    private ReloadAudioProfile() {}
    private static String key(String id,int ticks) { return id+":"+ticks; }
    private static Map<String, Clip> load() {
        var in=ReloadAudioProfile.class.getResourceAsStream("/destiny/sounds/w63-reload.json");
        if(in==null)throw new IllegalStateException("Missing W63 timed reload sounds");
        try(var reader=new InputStreamReader(in,StandardCharsets.UTF_8)) {
            var data=new Gson().fromJson(reader,Data.class);
            if(data==null || !"W63".equals(data.stage) || data.entries==null || data.entries.length==0)
                throw new IllegalStateException("Invalid W63 audio profile");
            var result=new HashMap<String,Clip>();
            for(var inherited:WeaponExotics.append(data.entries,"reloadAudio",Clip.class)) {
                var c=NamedReloadAudioW102.overlay(inherited);
                var entry=WeaponCatalog.find(c.id).orElseThrow();var p=WeaponProfile.forEntry(entry);
                if(p.mode()==WeaponProfile.Mode.MELEE || p.shellReload() || entry.family().equals("bow")
                        || c.ticks<1 || c.ticks>1200 || c.event==null || !(NamedReloadAudioW102.isReplacement(c) || c.event.startsWith("weapon.reload_w63.") || WeaponExotics.ace(entry) && c.event.startsWith("weapon.reload_w83.") || WeaponExotics.izanagi(entry) && c.event.startsWith("weapon.reload_w84."))
                        || !DestinySounds.has(c.event) || !DestinySounds.weaponKey(entry,"reload").equals(c.sourceEvent)
                        || c.sourceSha256==null || !c.sourceSha256.matches("[a-f0-9]{64}")
                        || c.asset==null || !(NamedReloadAudioW102.isReplacement(c) || c.asset.startsWith("assets/destiny/sounds/w63/reload/") || WeaponExotics.ace(entry) && c.asset.startsWith("assets/destiny/sounds/w83/reload/") || WeaponExotics.izanagi(entry) && c.asset.startsWith("assets/destiny/sounds/w84/reload/"))
                        || !c.asset.endsWith(".ogg") || c.asset.contains("..")
                        || result.put(key(c.id,c.ticks),c)!=null)
                    throw new IllegalStateException("Invalid timed reload clip "+c);
                boolean normal=c.ticks==p.firstReloadTicks();
                boolean outlaw=OutlawProfile.rolls().stream().anyMatch(row->row.id().equals(c.id))
                        && c.ticks==OutlawProfile.reload(entry).firstTicks();
                boolean firefly=WeaponExotics.ace(entry) && c.ticks==WeaponAce.fireflyReloadTicks(entry);
                if(!normal&&!outlaw&&!firefly)throw new IllegalStateException("Unknown effective reload duration "+c);
            }
            // Fail closed if an eligible base weapon or an implemented modifier was accidentally omitted.
            for(var entry:WeaponCatalog.all()) {
                var p=WeaponProfile.forEntry(entry);
                if(p.mode()==WeaponProfile.Mode.MELEE || p.shellReload() || entry.family().equals("bow"))continue;
                if(!result.containsKey(key(entry.id(),p.firstReloadTicks())))throw new IllegalStateException("Missing base reload "+entry.id());
                if(OutlawProfile.rolls().stream().anyMatch(row->row.id().equals(entry.id()))
                        && !result.containsKey(key(entry.id(),OutlawProfile.reload(entry).firstTicks())))
                    throw new IllegalStateException("Missing Outlaw reload "+entry.id());
            }
            for(var entry:WeaponCatalog.all()) if(WeaponExotics.ace(entry)
                    && !result.containsKey(key(entry.id(),WeaponAce.fireflyReloadTicks(entry))))
                throw new IllegalStateException("Missing Firefly reload " + entry.id());
            return Map.copyOf(result);
        }catch(java.io.IOException e){throw new IllegalStateException(e);}
    }
    public static Optional<Clip> find(WeaponCatalog.Entry entry,int ticks) {
        return entry==null || !WeaponCatalog.find(entry.id()).filter(entry::equals).isPresent()
                ?Optional.empty():Optional.ofNullable(CLIPS.get(key(entry.id(),ticks)));
    }
    public static Collection<Clip> all() { return CLIPS.values(); }
}
