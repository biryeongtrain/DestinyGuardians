package kim.biryeong.destiny.test;

import com.google.gson.*;
import com.mojang.serialization.Codec;
import com.mojang.serialization.JsonOps;
import kim.biryeong.destiny.world.TowerBakedMaterialPass;
import kim.biryeong.destiny.world.TowerVoxelMap;
import net.fabricmc.fabric.api.gametest.v1.GameTest;
import net.minecraft.SharedConstants;
import net.minecraft.commands.arguments.blocks.BlockStateParser;
import net.minecraft.core.BlockPos;
import net.minecraft.core.Direction;
import net.minecraft.core.registries.BuiltInRegistries;
import net.minecraft.gametest.framework.GameTestHelper;
import net.minecraft.server.Bootstrap;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;

import java.io.*;
import java.lang.reflect.*;
import java.nio.charset.StandardCharsets;
import java.util.*;
import java.util.function.*;
import java.util.zip.GZIPInputStream;
import java.util.zip.GZIPOutputStream;

/** Small deterministic fixtures; main() also runs without a game server, world, ports or live Tower. */
public final class TowerBakedMaterialW245GameTests {
    private static final String SOURCE = "55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d";
    private static final String PRIOR = "a0ecb154be54569b4bb183fdbc33dd03b750da6c97a4024f0fd7e79b5ad429f4";
    private static final String RESOURCE = "/data/destiny/tower/courtyard-materials-w243.json.gz";
    private record Cell(BlockPos pos, String expected) {}
    private record Fixture(TowerVoxelMap map, byte[] prior, List<Cell> priorCells, Cell original) {}

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100, manualOnly=true)
    public void provenanceDuplicatesAndExpectedAreRejected(GameTestHelper helper) throws Exception {
        validateRejections(fixture());
        helper.succeed();
    }

    @GameTest(structure="destiny-test:floor", environment="destiny-test:w90_isolated", maxTicks=100, manualOnly=true)
    public void restartPreservesUserChangesAndProps(GameTestHelper helper) throws Exception {
        validateRestart(fixture());
        helper.succeed();
    }

    public static void main(String[] args) throws Exception {
        SharedConstants.tryDetectVersion();
        Bootstrap.bootStrap();
        Fixture fixture = fixture();
        validateRejections(fixture);
        validateRestart(fixture);
        if (args.length == 1) {
            try (InputStream input = new FileInputStream(args[0])) {
                List<?> pieces = decode(fixture, input.readAllBytes(), SOURCE, fixture.prior());
                int count = 0;
                for (Object piece : pieces) count += ((List<?>)access(piece,"edits")).size();
                check(count > 0, "Shipped baked overlay is nonempty");
                System.out.println("W245_SHIPPED_OK cells=" + count + " chunks=" + pieces.size());
            }
        }
        System.out.println("W245_TARGETED_OK provenance/duplicate/expected/fullcube + persisted-ledger restart/edit/prop preservation");
    }

    private static Fixture fixture() throws Exception {
        TowerVoxelMap map = TowerVoxelMap.loadBundled();
        byte[] prior;
        try (InputStream input = Objects.requireNonNull(TowerBakedMaterialW245GameTests.class.getResourceAsStream(RESOURCE))) {
            prior = input.readAllBytes();
        }
        JsonObject json;
        try (var gzip = new GZIPInputStream(new ByteArrayInputStream(prior))) {
            json = JsonParser.parseString(new String(gzip.readAllBytes(), StandardCharsets.UTF_8)).getAsJsonObject();
        }
        var palette = json.getAsJsonArray("palette");
        List<Cell> samples = new ArrayList<>();
        Set<Long> occupied = new HashSet<>();
        for (var item : json.getAsJsonArray("cells")) {
            var row = item.getAsJsonArray();
            BlockPos pos = new BlockPos(row.get(0).getAsInt(), row.get(1).getAsInt(), row.get(2).getAsInt());
            occupied.add(pos.asLong());
            if (samples.size() < 3) samples.add(new Cell(pos, palette.get(row.get(3).getAsInt()).getAsString()));
        }
        check(samples.size() == 3, "Three W243 cells available");
        Cell[] original = {null};
        // Only one known courtyard chunk; never scan the entire source map.
        map.forChunk(4, -2, (x,y,z,index) -> {
            if (original[0] != null || occupied.contains(new BlockPos(x,y,z).asLong())
                    || !map.palette().get(index).equals("minecraft:smooth_stone")) return;
            BlockPos pos = new BlockPos(x,y,z);
            for (Direction direction : Direction.values()) {
                BlockPos adjacent = pos.relative(direction);
                if (map.paletteIndexAt(adjacent.getX(), adjacent.getY(), adjacent.getZ()) < 0) {
                    original[0] = new Cell(pos, "minecraft:smooth_stone");
                    break;
                }
            }
        });
        check(original[0] != null, "One exposed source cell outside W243 in bounded chunk");
        return new Fixture(map, prior, samples, original[0]);
    }

    private static void validateRejections(Fixture f) throws Exception {
        Cell prior = f.priorCells().getFirst();
        String palette = "\"" + prior.expected() + "\",\"minecraft:white_concrete\"";
        String row = row(prior.pos(), 0, 1);
        check(!decode(f, payload(palette, row, PRIOR), SOURCE, f.prior()).isEmpty(), "W243 replacement accepted as expected");
        check(!decode(f, payload("\"minecraft:smooth_stone\",\"minecraft:white_concrete\"",
                row(f.original().pos(),0,1), PRIOR), SOURCE, f.prior()).isEmpty(), "Original expected accepted outside W243");
        reject(() -> decode(f, payload(palette,row,"bad"),SOURCE,f.prior()), "declared prior hash");
        byte[] corrupt = f.prior().clone(); corrupt[0] ^= 1;
        reject(() -> decode(f,payload(palette,row,PRIOR),SOURCE,corrupt), "actual prior hash");
        reject(() -> decode(f,payload(palette,row,PRIOR),"bad",f.prior()), "actual source hash");
        reject(() -> decode(f,payload(palette,row + "," + row,PRIOR),SOURCE,f.prior()), "duplicate coordinate");
        String wrong = prior.expected().equals("minecraft:gold_block") ? "minecraft:diamond_block" : "minecraft:gold_block";
        reject(() -> decode(f,payload("\""+wrong+"\",\"minecraft:white_concrete\"",row,PRIOR),SOURCE,f.prior()), "W243 expected mismatch");
        reject(() -> decode(f,payload("\"minecraft:gold_block\",\"minecraft:white_concrete\"",
                row(f.original().pos(),0,1),PRIOR),SOURCE,f.prior()), "original expected mismatch");
        reject(() -> decode(f,payload("\""+prior.expected()+"\",\"minecraft:stone_slab\"",row,PRIOR),SOURCE,f.prior()), "non-full replacement");
        reject(() -> decode(f,payload(palette,row(new BlockPos(0,319,0),0,1),PRIOR),SOURCE,f.prior()), "non-source target");
    }

    @SuppressWarnings("unchecked")
    private static void validateRestart(Fixture f) throws Exception {
        String palette = "\""+f.priorCells().get(0).expected()+"\",\""+f.priorCells().get(1).expected()
                +"\",\""+f.priorCells().get(2).expected()+"\",\"minecraft:white_concrete\"";
        List<String> rows = new ArrayList<>();
        for (int i=0;i<3;i++) rows.add(row(f.priorCells().get(i).pos(),i,3));
        List<?> pieces = decode(f,payload(palette,String.join(",",rows),PRIOR),SOURCE,f.prior());
        List<Object> edits = new ArrayList<>();
        for (Object piece : pieces) edits.addAll((List<?>)access(piece,"edits"));
        Class<?> ledgerType = Class.forName("kim.biryeong.destiny.world.TowerDetailPass$Ledger");
        var constructor = ledgerType.getDeclaredConstructor(); constructor.setAccessible(true);
        Object ledger = constructor.newInstance();
        var field = ledgerType.getDeclaredField("CODEC"); field.setAccessible(true);
        Codec<Object> codec = (Codec<Object>)field.get(null);
        Object detailsLedger = constructor.newInstance(), materialLedger = constructor.newInstance();
        var consider = ledgerType.getDeclaredMethod("consider", BlockPos.class); consider.setAccessible(true);
        consider.invoke(detailsLedger, f.original().pos()); consider.invoke(materialLedger, f.priorCells().getFirst().pos());
        var detailsBefore = codec.encodeStart(JsonOps.INSTANCE,detailsLedger).getOrThrow();
        var materialsBefore = codec.encodeStart(JsonOps.INSTANCE,materialLedger).getOrThrow();
        var apply = Class.forName("kim.biryeong.destiny.world.TowerDetailPass").getDeclaredMethod("apply",
                Class.forName("kim.biryeong.destiny.world.TowerDetailPass$Edit"), ledgerType, BooleanSupplier.class,
                Function.class, Function.class, BiPredicate.class);
        apply.setAccessible(true);
        Map<BlockPos,BlockState> world = new HashMap<>();
        BlockPos changed = (BlockPos)access(edits.get(0),"pos"), prop = (BlockPos)access(edits.get(1),"pos"), user = (BlockPos)access(edits.get(2),"pos");
        world.put(changed,parse((String)access(edits.get(0),"expected")));
        world.put(prop,Blocks.OAK_LOG.defaultBlockState()); world.put(user,Blocks.GOLD_BLOCK.defaultBlockState());
        Function<BlockPos,BlockState> read = world::get;
        Function<String,BlockState> parse = TowerBakedMaterialW245GameTests::parse;
        BiPredicate<BlockPos,BlockState> write = (pos,state) -> { world.put(pos,state); return true; };
        int count=0;
        for(Object edit:edits) if((boolean)apply.invoke(null,edit,ledger,(BooleanSupplier)()->true,read,parse,write)) count++;
        check(count==1 && world.get(changed).equals(parse("minecraft:white_concrete")), "Only matching expected is replaced");
        check(world.get(prop).is(Blocks.OAK_LOG) && world.get(user).is(Blocks.GOLD_BLOCK), "Tree prop and user edit preserved");
        Object reopened = codec.parse(JsonOps.INSTANCE,codec.encodeStart(JsonOps.INSTANCE,ledger).getOrThrow()).getOrThrow();
        world.put(changed,Blocks.AIR.defaultBlockState());
        // Even skipped conflicts remain consumed if the administrator later restores their expected material.
        world.put(prop,parse((String)access(edits.get(1),"expected")));
        world.put(user,parse((String)access(edits.get(2),"expected")));
        BiPredicate<BlockPos,BlockState> forbiddenWrite = (pos,state) -> { throw new AssertionError("Consumed coordinate replayed"); };
        for(Object edit:edits) check(!(boolean)apply.invoke(null,edit,reopened,(BooleanSupplier)()->true,read,parse,forbiddenWrite), "No replay after ledger round trip");
        check(world.get(changed).isAir(), "User removal survives restart");
        world.put(changed,parse((String)access(edits.get(0),"expected")));
        check(!(boolean)apply.invoke(null,edits.get(0),reopened,(BooleanSupplier)()->true,read,parse,forbiddenWrite), "User revert to expected survives restart");
        check(detailsBefore.equals(codec.encodeStart(JsonOps.INSTANCE,detailsLedger).getOrThrow())
                && materialsBefore.equals(codec.encodeStart(JsonOps.INSTANCE,materialLedger).getOrThrow()), "Older ledgers unchanged");
    }

    private static List<?> decode(Fixture f, byte[] baked, String source, byte[] prior) throws Exception {
        var method = TowerBakedMaterialPass.class.getDeclaredMethod("decode",InputStream.class,TowerVoxelMap.class,String.class,byte[].class);
        method.setAccessible(true);
        try { return (List<?>)method.invoke(null,new ByteArrayInputStream(baked),f.map(),source,prior); }
        catch(InvocationTargetException e) { if(e.getCause() instanceof Exception exception) throw exception; throw e; }
    }
    private static Object access(Object object,String name) throws Exception {
        var method=object.getClass().getDeclaredMethod(name); method.setAccessible(true); return method.invoke(object);
    }
    private static BlockState parse(String name) {
        try { return BlockStateParser.parseForBlock(BuiltInRegistries.BLOCK,name,false).blockState(); }
        catch(Exception e) { throw new IllegalArgumentException(name,e); }
    }
    private static byte[] payload(String palette,String cells,String prior) throws IOException {
        String json="{\"schema\":1,\"sourceVoxelSHA256\":\""+SOURCE+"\",\"priorMaterialSHA256\":\""+prior+"\",\"palette\":["+palette+"],\"cells\":["+cells+"]}";
        var bytes=new ByteArrayOutputStream();
        try(var gzip=new GZIPOutputStream(bytes)) { gzip.write(json.getBytes(StandardCharsets.UTF_8)); }
        return bytes.toByteArray();
    }
    private static String row(BlockPos p,int expected,int replacement) { return "["+p.getX()+","+p.getY()+","+p.getZ()+","+expected+","+replacement+"]"; }
    private interface Checked { void run() throws Exception; }
    private static void reject(Checked action,String reason) throws Exception {
        try { action.run(); } catch(IOException expected) { return; }
        throw new AssertionError("Expected rejection: "+reason);
    }
    private static void check(boolean condition,String reason) { if(!condition) throw new AssertionError(reason); }
}
