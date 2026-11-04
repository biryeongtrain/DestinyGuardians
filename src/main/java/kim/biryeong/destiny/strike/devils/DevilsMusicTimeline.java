package kim.biryeong.destiny.strike.devils;

import com.google.gson.*;

/** Pure per-listener score clock; all times are monotonic nanoseconds. */
final class DevilsMusicTimeline {
    record Change(boolean stop, Integer segment, boolean transition) {
        static final Change NONE=new Change(false,null,false);
    }
    private final JsonObject data;
    private final long seed;
    private DevilsMusicPlaylist playlist;
    private int section=-1, pending=-1;
    private Integer segment;
    private JsonObject pendingRule;
    private long startedAt, nextAt, switchAt, serial;
    private boolean finished;
    DevilsMusicTimeline(JsonObject data,long seed) {this.data=data;this.seed=seed;}
    int section(){return section;}
    Change update(int desired,long now) {
        if(desired<0) {boolean stop=segment!=null;reset();return new Change(stop,null,false);}
        if(section<0) {start(desired,rule(-1,desired),now);return advance(now);}
        if(desired==section) {pending=-1;pendingRule=null;}
        else if(desired!=pending) {
            pending=desired;pendingRule=rule(section,desired);
            switchAt=segment==null?now:synchronization(clip(segment),startedAt,now,
                    pendingRule.getAsJsonObject("source").get("eSyncType").getAsInt());
        }
        if(pending>=0 && now>=switchAt) {
            int wanted=pending;var selected=pendingRule;
            start(wanted,selected,now);
            var transition=selected.get("transition_segment_id");
            if(transition!=null&&!transition.isJsonNull()) {
                segment=transition.getAsInt();startedAt=now;nextAt=now+duration(segment);
                return new Change(true,segment,true);
            }
            var change=advance(now);return new Change(true,change.segment(),false);
        }
        if(!finished && now>=nextAt)return advance(now);
        return Change.NONE;
    }
    private Change advance(long now) {
        boolean stop=segment!=null;
        segment=playlist.next();finished=segment==null;
        if(segment!=null){startedAt=now;nextAt=now+duration(segment);}
        return new Change(stop,segment,false);
    }
    private void start(int wanted,JsonObject rule,long now) {
        section=wanted;pending=-1;pendingRule=null;segment=null;nextAt=now;finished=false;
        int container=container(wanted);JsonObject tree=null;
        for(var row:data.getAsJsonArray("playlists")) {
            var obj=row.getAsJsonObject();if(obj.get("container_id").getAsInt()==container)tree=obj.getAsJsonObject("tree");
        }
        if(tree==null)throw new IllegalStateException("Missing playlist "+wanted);
        int jump=rule.getAsJsonObject("destination").get("uJumpToID").getAsInt();
        playlist=new DevilsMusicPlaylist(tree,seed+serial++,jump);
    }
    private int container(int state) {
        if(state<0)return 0;
        String name="section_%02d".formatted(state);
        for(var row:data.getAsJsonArray("sections")) {
            var s=row.getAsJsonObject();if(name.equals(s.get("section").getAsString()))return s.get("container_id").getAsInt();
        }
        throw new IllegalArgumentException("Unknown music section "+state);
    }
    /** Wwise evaluates the last matching rule first, including segment-specific silence overrides. */
    private JsonObject rule(int from,int to) {
        var rules=data.getAsJsonArray("transitions");int source=container(from),destination=container(to);
        for(int i=rules.size()-1;i>=0;i--) {
            var rule=rules.get(i).getAsJsonObject();
            if(matches(rule.getAsJsonArray("source_ids"),source,segment==null?0:segment)
                    &&matches(rule.getAsJsonArray("destination_ids"),destination,destination))return rule;
        }
        throw new IllegalStateException("No music transition "+from+" -> "+to);
    }
    private static boolean matches(JsonArray ids,int container,int segment) {
        for(var id:ids){int value=id.getAsInt();if(value==-1||value==container||value==segment)return true;}
        return false;
    }
    private JsonObject clip(int id){return data.getAsJsonObject("segments").getAsJsonObject(Integer.toString(id));}
    private long duration(int id){return Math.max(1,(long)(clip(id).get("seconds").getAsDouble()*1e9));}
    static long synchronization(JsonObject clip,long start,long now,int sync) {
        double elapsed=Math.max(0,(now-start)/1e6),end=clip.get("seconds").getAsDouble()*1000;
        double at=elapsed;
        switch(sync) {
            case 0 -> {return now;}
            case 1,2 -> {
                double entry=0;
                for(var item:clip.getAsJsonArray("markers")) {
                    var m=item.getAsJsonObject();if(m.get("id").getAsInt()==43573010)entry=m.get("fPosition").getAsDouble();
                }
                double period=sync==1?clip.get("grid_period_ms").getAsDouble():
                        60000/clip.get("tempo").getAsDouble()*clip.get("beats_per_bar").getAsInt()*4/clip.get("beat_value").getAsInt();
                double origin=entry+(sync==1?clip.get("grid_offset_ms").getAsDouble():0);
                if(!(period>0)||!Double.isFinite(period))throw new IllegalStateException("Invalid score meter");
                at=origin+(Math.floor((elapsed-origin)/period)+1)*period;
            }
            case 4,7 -> {
                at=end;
                for(var item:clip.getAsJsonArray("markers")) {
                    var m=item.getAsJsonObject();int id=m.get("id").getAsInt();
                    double pos=m.get("fPosition").getAsDouble();
                    if(id==43573010||sync==7&&id!=1539036744)continue;
                    if(pos>elapsed+.000001)at=Math.min(at,pos);
                }
            }
            default -> throw new IllegalStateException("Unsupported score synchronization "+sync);
        }
        return Math.max(now,start+(long)(Math.min(at,end)*1e6));
    }
    void reset(){playlist=null;section=pending=-1;segment=null;pendingRule=null;finished=false;}
}
