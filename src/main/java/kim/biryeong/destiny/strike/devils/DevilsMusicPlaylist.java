package kim.biryeong.destiny.strike.devils;

import com.google.gson.JsonObject;
import java.util.*;

/** Lazy Wwise playlist tree: Loop=0 is unbounded, never eagerly expanded. */
final class DevilsMusicPlaylist {
    private final Random random;
    private final Deque<Frame> stack = new ArrayDeque<>();
    private final Map<Integer,Deque<Integer>> recent = new HashMap<>();
    private final Map<Integer,Integer> steps = new HashMap<>();
    private final Map<Integer,List<JsonObject>> shuffleBags = new HashMap<>();
    private static final class Frame {
        final JsonObject node;
        int iteration, child;
        boolean emitted;
        List<JsonObject> children;
        Frame(JsonObject node) { this.node=node; }
    }
    DevilsMusicPlaylist(JsonObject tree, long seed) { this(tree,seed,0); }
    DevilsMusicPlaylist(JsonObject tree, long seed, int jump) {
        random=new Random(seed);
        if(jump==0){stack.push(new Frame(tree));return;}
        var path=new ArrayList<JsonObject>();
        if(!pathTo(tree,jump,path))throw new IllegalArgumentException("Missing playlist jump "+jump);
        for(int i=0;i<path.size();i++) {
            var node=path.get(i);var frame=new Frame(node);stack.push(frame);
            if(i+1<path.size()) {
                var selected=path.get(i+1);int type=number(node,"eRSType");
                var all=new ArrayList<JsonObject>();node.getAsJsonArray("children").forEach(x->all.add(x.getAsJsonObject()));
                int index=all.indexOf(selected);
                if(type==0) {frame.children=all;frame.child=index+1;}
                else {frame.children=List.of(selected);frame.child=1;}
                if(type==1)steps.put(number(node,"playlistItemID"),index+1);
            }
        }
    }
    private static boolean pathTo(JsonObject node,int jump,List<JsonObject> path) {
        path.add(node);
        if(number(node,"playlistItemID")==jump)return true;
        for(var child:node.getAsJsonArray("children"))if(pathTo(child.getAsJsonObject(),jump,path))return true;
        path.removeLast();return false;
    }
    Integer next() {
        for (int budget=0;budget<10000 && !stack.isEmpty();budget++) {
            var f=stack.peek();
            int segment=number(f.node,"SegmentID");
            if(segment!=0 && !f.emitted) {f.emitted=true;return segment;}
            if(segment==0) {
                if(f.children==null)f.children=children(f.node);
                if(f.child<f.children.size()) {stack.push(new Frame(f.children.get(f.child++)));continue;}
            }
            int loops=number(f.node,"Loop");
            if(loops==0 || ++f.iteration<loops) {f.emitted=false;f.child=0;f.children=null;}
            else stack.pop();
        }
        if(!stack.isEmpty())throw new IllegalStateException("Music playlist contains an empty infinite cycle");
        return null;
    }
    private List<JsonObject> children(JsonObject n) {
        var all=new ArrayList<JsonObject>();n.getAsJsonArray("children").forEach(x->all.add(x.getAsJsonObject()));
        if(all.isEmpty())return all;
        int type=number(n,"eRSType"), id=number(n,"playlistItemID");
        if(type==1) {int step=steps.getOrDefault(id,0);steps.put(id,step+1);return List.of(all.get(step%all.size()));}
        if(type!=2&&type!=3)return all;
        var history=recent.computeIfAbsent(id,k->new ArrayDeque<>());
        int avoid=Math.min(number(n,"wAvoidRepeatCount"),all.size()-1);
        while(history.size()>avoid)history.removeFirst();
        List<JsonObject> pool=all;
        if(number(n,"bIsShuffle")==1) {
            pool=shuffleBags.computeIfAbsent(id,k->new ArrayList<>());
            if(pool.isEmpty())pool.addAll(all);
        }
        var choices=pool.stream().filter(c->!history.contains(number(c,"playlistItemID"))).toList();
        // Exhausting a shuffle bag takes precedence over a larger avoid-repeat window.
        if(choices.isEmpty())choices=List.copyOf(pool);
        int total=choices.stream().mapToInt(c->number(n,"bIsUsingWeight")==1?Math.max(1,number(c,"Weight")):1).sum();
        int pick=random.nextInt(total);JsonObject selected=choices.getLast();
        for(var c:choices) {pick-=number(n,"bIsUsingWeight")==1?Math.max(1,number(c,"Weight")):1;if(pick<0){selected=c;break;}}
        if(number(n,"bIsShuffle")==1)pool.remove(selected);
        history.addLast(number(selected,"playlistItemID"));return List.of(selected);
    }
    static int number(JsonObject n,String key) {return n.get(key).getAsInt();}
}
