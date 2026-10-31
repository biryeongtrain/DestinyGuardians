package kim.biryeong.destiny.tutorial;

import eu.pb4.polymer.virtualentity.api.ElementHolder;
import eu.pb4.polymer.virtualentity.api.attachment.ChunkAttachment;
import eu.pb4.polymer.virtualentity.api.elements.BlockDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.ItemDisplayElement;
import eu.pb4.polymer.virtualentity.api.elements.TextDisplayElement;
import kim.biryeong.destiny.guardian.Element;
import kim.biryeong.destiny.guardian.GuardianClass;
import net.minecraft.core.BlockPos;
import net.minecraft.core.component.DataComponents;
import net.minecraft.network.chat.Component;
import net.minecraft.resources.Identifier;
import net.minecraft.server.level.ServerLevel;
import net.minecraft.util.Brightness;
import net.minecraft.world.entity.Display;
import net.minecraft.world.item.DyeColor;
import net.minecraft.world.item.ItemDisplayContext;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.Items;
import net.minecraft.world.item.component.CustomModelData;
import net.minecraft.world.level.block.Block;
import net.minecraft.world.level.block.Blocks;
import net.minecraft.world.level.block.state.BlockState;
import net.minecraft.world.phys.AABB;
import net.minecraft.world.phys.Vec3;
import org.joml.Quaternionf;
import org.joml.Vector3f;

import java.util.ArrayList;
import java.util.List;

/**
 * One self-contained tutorial lane. Everything is built procedurally relative to a lane origin, so
 * each player walks an identical, private course: awakening chamber → class hall → Traveler shard →
 * firing range → traversal run → ability arena → finale arena → light portal.
 * The player walks along +Z (yaw 0). Feet stand at {@link #BASE_Y}; the floor is one block below.
 */
public final class TutorialCourse {
    public static final int BASE_Y = 80;
    public static final int LANE_SPACING = 128;
    public static final int LENGTH = 194;

    /** Stations, in travel order. Positions are relative to the lane origin (feet level). */
    public static final Vec3 SPAWN = new Vec3(.5, 0, 3.5);
    public static final Vec3 GHOST_WAKE = new Vec3(.5, 1.7, 7.5);
    public static final Vec3 CLASS_ENTRY = new Vec3(.5, 0, 17.5);
    public static final Vec3 LIGHT_ENTRY = new Vec3(.5, 0, 34.5);
    public static final Vec3 RANGE_ENTRY = new Vec3(.5, 0, 56.5);
    public static final Vec3 RUN_ENTRY = new Vec3(.5, 0, 96.5);
    public static final Vec3 RUN_RETRY = new Vec3(.5, 0, 110.5);
    public static final Vec3 ARENA_ENTRY = new Vec3(.5, 0, 142.5);
    public static final Vec3 FINALE_ENTRY = new Vec3(.5, 0, 164.5);
    public static final Vec3 PORTAL = new Vec3(.5, 0, 189.5);

    public static final double CHOICE_RADIUS = 1.6;
    /** The traversal chasm (air) spans these relative z values; the far side stands at y -1. */
    public static final int CHASM_START = 125, CHASM_END = 131;
    public static final Vec3 FAR_SIDE = new Vec3(.5, -1, 135.5);

    public record Choice<T>(T value, Vec3 center, int color, String name, String icon, String blurb) { }

    public static final List<Choice<GuardianClass>> CLASSES = List.of(
            new Choice<>(GuardianClass.TITAN, new Vec3(6.5, 0, 26.5), 0xE57575, "타이탄", "class_titan_w248",
                    "최전선을 지키는 방패. 방벽을 세우고 적진을 부숩니다."),
            new Choice<>(GuardianClass.HUNTER, new Vec3(.5, 0, 26.5), 0x79B9DF, "헌터", "class_hunter_w248",
                    "그림자 속의 사냥꾼. 회피로 위기를 벗어나고 빈틈을 찌릅니다."),
            new Choice<>(GuardianClass.WARLOCK, new Vec3(-5.5, 0, 26.5), 0xEDCE79, "워록", "class_warlock_w248",
                    "빛을 연구하는 학자. 균열로 아군을 치유하고 힘을 북돋습니다."));
    public static final List<Choice<Element>> SUBCLASSES = List.of(
            new Choice<>(Element.ARC, new Vec3(6.5, 0, 40.5), 0x80D9F3, "아크", "subclass_arc_w248",
                    "번개처럼 빠르게. 연쇄 전기 피해와 기동력."),
            new Choice<>(Element.SOLAR, new Vec3(.5, 0, 40.5), 0xFFAA63, "솔라", "subclass_solar_w248",
                    "불꽃처럼 강하게. 소각 피해와 회복."),
            new Choice<>(Element.VOID, new Vec3(-5.5, 0, 40.5), 0xB695FF, "공허", "subclass_void_w248",
                    "어둠을 다루는 빛. 약화와 은신, 보호막."));

    public static final List<Vec3> NEAR_TARGETS = List.of(new Vec3(-3.5, 0, 68.5), new Vec3(.5, 0, 69.5), new Vec3(4.5, 0, 68.5));
    public static final List<Vec3> FAR_TARGETS = List.of(new Vec3(-2.5, 2, 88.5), new Vec3(3.5, 2, 88.5));
    public static final List<Vec3> GRENADE_TARGETS = List.of(new Vec3(-.8, 0, 154.5), new Vec3(.5, 0, 155.5), new Vec3(1.8, 0, 154.5));
    public static final Vec3 MELEE_TARGET = new Vec3(.5, 0, 148.5);
    public static final List<Vec3> WAVE = List.of(new Vec3(-8.5, 0, 178.5), new Vec3(-4.5, 0, 182.5), new Vec3(.5, 0, 180.5),
            new Vec3(5.5, 0, 182.5), new Vec3(9.5, 0, 178.5), new Vec3(.5, 0, 185.5));

    /** Gates in order: awakening, class hall, shard, range, ability arena. */
    public enum Gate {
        AWAKEN(12), CLASS(31), LIGHT(51), RANGE(93), ARENA(161);
        public final int z;
        Gate(int z) { this.z = z; }
    }

    private final ServerLevel level;
    private final BlockPos origin;
    private final List<ElementHolder> decorations = new ArrayList<>();
    private BlockDisplayElement shard, shardCore;
    private boolean built;

    TutorialCourse(ServerLevel level, int lane) {
        this.level = level;
        this.origin = new BlockPos(lane * LANE_SPACING, BASE_Y, 0);
    }

    public BlockPos origin() { return origin; }
    public ServerLevel level() { return level; }
    public Vec3 world(Vec3 rel) { return new Vec3(origin.getX() + rel.x, origin.getY() + rel.y, origin.getZ() + rel.z); }
    public Vec3 local(Vec3 world) { return world.subtract(origin.getX(), origin.getY(), origin.getZ()); }
    public AABB bounds() {
        return new AABB(origin.getX() - 16, origin.getY() - 20, origin.getZ() - 4,
                origin.getX() + 16, origin.getY() + 24, origin.getZ() + LENGTH + 4);
    }

    private BlockPos at(int x, int y, int z) { return origin.offset(x, y, z); }
    private void set(int x, int y, int z, BlockState state) { level.setBlock(at(x, y, z), state, Block.UPDATE_CLIENTS | Block.UPDATE_KNOWN_SHAPE); }
    private void set(int x, int y, int z, Block block) { set(x, y, z, block.defaultBlockState()); }
    private void box(int x0, int y0, int z0, int x1, int y1, int z1, Block block) {
        for (int x = Math.min(x0, x1); x <= Math.max(x0, x1); x++)
            for (int y = Math.min(y0, y1); y <= Math.max(y0, y1); y++)
                for (int z = Math.min(z0, z1); z <= Math.max(z0, z1); z++) set(x, y, z, block);
    }
    private static Block dye(DyeColor color) { return Blocks.CONCRETE.pick(color); }
    private static Block glass(DyeColor color) { return Blocks.STAINED_GLASS.pick(color); }

    /** Section floor with seam lights, two-tone walls and an optional ceiling. */
    private void room(int x0, int x1, int z0, int z1, int wallHeight, Block floor, Block trim, boolean ceiling) {
        for (int x = x0; x <= x1; x++) for (int z = z0; z <= z1; z++) {
            boolean seam = (x == x0 || x == x1 || z == z0 || z == z1);
            boolean light = !seam && Math.floorMod(z - z0, 6) == 3 && (x == x0 + 1 || x == x1 - 1);
            set(x, -1, z, light ? Blocks.SEA_LANTERN : seam ? trim : floor);
            set(x, -2, z, Blocks.POLISHED_DEEPSLATE);
        }
        for (int z = z0 - 1; z <= z1 + 1; z++) for (int y = -2; y < wallHeight; y++) {
            Block wall = y < 2 ? Blocks.POLISHED_BLACKSTONE_BRICKS : Blocks.TUFF_BRICKS;
            if (y == wallHeight - 1) wall = Blocks.POLISHED_DEEPSLATE;
            set(x0 - 1, y, z, wall); set(x1 + 1, y, z, wall);
        }
        if (ceiling) box(x0 - 1, wallHeight, z0 - 1, x1 + 1, wallHeight, z1 + 1, Blocks.POLISHED_DEEPSLATE);
    }
    /** Cross wall at z with an opening x -1..1, y 0..2 (the gate). */
    private void crossWall(int z, int halfWidth, int height) {
        for (int x = -halfWidth; x <= halfWidth; x++) for (int y = -2; y < height; y++) {
            if (Math.abs(x) <= 1 && y >= 0 && y <= 2) continue;
            set(x, y, z, y < 2 ? Blocks.POLISHED_BLACKSTONE_BRICKS : Blocks.TUFF_BRICKS);
        }
        set(-2, 3, z, Blocks.SEA_LANTERN); set(2, 3, z, Blocks.SEA_LANTERN);
    }

    public void build() {
        destroyDecorations();
        if (!built) {
            buildStatic();
            built = true;
        }
        for (Gate gate : Gate.values()) close(gate);
        fallbackBridge(false);
        decorate();
    }

    private void buildStatic() {
        // A. Awakening chamber: closed, dim, a single shaft of light.
        room(-5, 5, 0, 11, 5, Blocks.POLISHED_DEEPSLATE, Blocks.DEEPSLATE_TILES, true);
        set(0, 5, 7, Blocks.SEA_LANTERN);
        crossWall(-1, 6, 6);
        crossWall(Gate.AWAKEN.z, 6, 6);
        // corridor
        room(-2, 2, 13, 15, 4, Blocks.DEEPSLATE_TILES, Blocks.POLISHED_DEEPSLATE, true);
        // B. Class hall.
        room(-10, 10, 16, 30, 6, Blocks.DEEPSLATE_TILES, Blocks.POLISHED_DEEPSLATE, false);
        crossWall(15, 11, 6);
        crossWall(Gate.CLASS.z, 11, 6);
        DyeColor[] classDyes = {DyeColor.RED, DyeColor.LIGHT_BLUE, DyeColor.YELLOW};
        for (int i = 0; i < CLASSES.size(); i++) pad(CLASSES.get(i).center(), classDyes[i], 29);
        // C. Traveler shard.
        room(-11, 11, 32, 50, 7, Blocks.POLISHED_TUFF, Blocks.DEEPSLATE_TILES, false);
        crossWall(Gate.LIGHT.z, 12, 7);
        DyeColor[] lightDyes = {DyeColor.LIGHT_BLUE, DyeColor.ORANGE, DyeColor.PURPLE};
        for (int i = 0; i < SUBCLASSES.size(); i++) pad(SUBCLASSES.get(i).center(), lightDyes[i], 43);
        box(-2, -1, 45, 2, -1, 47, Blocks.CALCITE);
        // D. Firing range.
        room(-9, 9, 52, 92, 5, Blocks.DEEPSLATE_TILES, Blocks.POLISHED_DEEPSLATE, false);
        crossWall(Gate.RANGE.z, 10, 5);
        box(-8, -1, 58, 8, -1, 58, dye(DyeColor.YELLOW));
        for (Vec3 t : NEAR_TARGETS) set((int) Math.floor(t.x), -1, (int) Math.floor(t.z), Blocks.TARGET);
        box(-6, 0, 85, 6, 1, 91, Blocks.POLISHED_BLACKSTONE_BRICKS);
        box(-6, 1, 85, 6, 1, 85, Blocks.POLISHED_DEEPSLATE);
        for (int x : new int[]{-8, 8}) { box(x, 0, 53, x, 2, 55, Blocks.IRON_BARS); set(x, 3, 54, Blocks.LANTERN); }
        // E. Traversal run: sprint lane, a short gap, then a chasm too wide without the jump ability.
        // The far side sits one block lower, so a glide, lift or double jump all reach it.
        room(-3, 3, 94, 139, 7, Blocks.DEEPSLATE_TILES, Blocks.POLISHED_DEEPSLATE, false);
        for (int z = 98; z <= 114; z += 4) box(-2, -1, z, 2, -1, z, dye(DyeColor.WHITE));
        box(-3, -2, 117, 3, -1, 119, Blocks.AIR);
        box(-2, -1, 116, 2, -1, 116, dye(DyeColor.ORANGE));
        box(-3, -2, CHASM_START, 3, -1, CHASM_END, Blocks.AIR);
        box(-3, -1, CHASM_START - 1, 3, -1, CHASM_START - 1, dye(DyeColor.LIGHT_BLUE));
        box(-3, -1, CHASM_END + 1, 3, -1, 139, Blocks.AIR);
        box(-3, -2, CHASM_END + 1, 3, -2, 139, Blocks.DEEPSLATE_TILES);
        box(-3, -3, CHASM_END + 1, 3, -3, 139, Blocks.POLISHED_DEEPSLATE);
        box(-3, -2, CHASM_END + 1, 3, -2, CHASM_END + 1, dye(DyeColor.LIGHT_BLUE));
        // F. Ability arena.
        room(-10, 10, 140, 160, 6, Blocks.DEEPSLATE_TILES, Blocks.POLISHED_DEEPSLATE, false);
        crossWall(Gate.ARENA.z, 14, 7);
        for (int x = 4; x <= 11; x++) for (int y = -2; y < 6; y++) { set(x, y, 139, Blocks.POLISHED_BLACKSTONE_BRICKS); set(-x, y, 139, Blocks.POLISHED_BLACKSTONE_BRICKS); }
        // G. Finale arena and the light portal.
        room(-13, 13, 162, 190, 7, Blocks.POLISHED_TUFF, Blocks.DEEPSLATE_TILES, false);
        crossWall(191, 14, 7);
        box(-1, 0, 191, 1, 2, 191, Blocks.POLISHED_BLACKSTONE_BRICKS);
        for (int y = 0; y <= 4; y++) { set(-2, y, 189, Blocks.QUARTZ_PILLAR); set(2, y, 189, Blocks.QUARTZ_PILLAR); }
        box(-2, 5, 189, 2, 5, 189, Blocks.CHISELED_QUARTZ_BLOCK);
        box(-1, -1, 188, 1, -1, 190, Blocks.SEA_LANTERN);
        for (int[] c : new int[][]{{-9, 168}, {9, 168}, {-9, 184}, {9, 184}}) box(c[0], 0, c[1], c[0] + 1, 1, c[1] + 1, Blocks.POLISHED_BLACKSTONE_BRICKS);
    }

    private void pad(Vec3 center, DyeColor dye, int pillarZ) {
        int cx = (int) Math.floor(center.x), cz = (int) Math.floor(center.z);
        box(cx - 1, -1, cz - 1, cx + 1, -1, cz + 1, dye(dye));
        set(cx, -1, cz, Blocks.SEA_LANTERN);
        for (int y = 0; y <= 3; y++) set(cx, y, pillarZ, glass(dye));
        set(cx, 4, pillarZ, Blocks.SEA_LANTERN);
    }

    public void open(Gate gate) {
        for (int x = -1; x <= 1; x++) for (int y = 0; y <= 2; y++) set(x, y, gate.z, Blocks.AIR);
    }
    public void close(Gate gate) {
        for (int x = -1; x <= 1; x++) for (int y = 0; y <= 2; y++) set(x, y, gate.z, Blocks.TINTED_GLASS);
    }
    public Vec3 gateCenter(Gate gate) { return world(new Vec3(.5, 1.5, gate.z + .5)); }

    /** Ghost-opened helper bridge across the chasm, for anyone the jump ability cannot carry. */
    public void fallbackBridge(boolean present) {
        for (int z = CHASM_START; z <= CHASM_END; z++)
            for (int x = -1; x <= 1; x++) set(x, -2, z, present ? Blocks.STAINED_GLASS.pick(DyeColor.LIGHT_BLUE) : Blocks.AIR);
    }

    public boolean acrossChasm(Vec3 world) {
        Vec3 l = local(world);
        return l.z > CHASM_END + .5 && l.z <= 139.9 && l.y >= -1.1 && l.y <= .2 && Math.abs(l.x - .5) <= 4;
    }
    public boolean inGap(Vec3 world) {
        Vec3 l = local(world);
        return l.z > 94 && l.z < 140 && l.y < -4;
    }
    public boolean inPortal(Vec3 world) {
        Vec3 l = local(world);
        return Math.abs(l.x - .5) <= 1.6 && l.z >= 187.5 && l.z <= 190.5 && l.y >= -.5 && l.y <= 3;
    }
    public boolean beyond(Vec3 world, double z) { return local(world).z >= z; }

    // ---- decorations (display entities) ----------------------------------------------------------------------
    private void decorate() {
        for (var c : CLASSES) label(c.center().add(0, 2.6, 0), c.icon(), c.color(), c.name());
        for (var c : SUBCLASSES) label(c.center().add(0, 2.6, 0), c.icon(), c.color(), c.name());
        // Traveler shard: a slowly turning pale monolith with a lit core.
        var holder = new ElementHolder();
        shard = new BlockDisplayElement(Blocks.CALCITE.defaultBlockState());
        shard.setScale(new Vector3f(2.2f));
        shard.setInterpolationDuration(4);
        shard.setBrightness(new Brightness(15, 15));
        shard.setViewRange(4);
        shardCore = new BlockDisplayElement(Blocks.SEA_LANTERN.defaultBlockState());
        shardCore.setScale(new Vector3f(1.1f));
        shardCore.setInterpolationDuration(4);
        shardCore.setBrightness(new Brightness(15, 15));
        spin(shard, new Quaternionf(), 1.1f);
        spin(shardCore, new Quaternionf(), .55f);
        holder.addElement(shard);
        holder.addElement(shardCore);
        ChunkAttachment.ofTicking(holder, level, world(new Vec3(.5, 4.2, 46.5)));
        decorations.add(holder);
        text(new Vec3(.5, 3.6, 89.5), "정조준 표적", 0xF2C14E, 1.0f);
        text(new Vec3(.5, 3.2, 128.5), "공중 도약으로 건너세요", 0x80D9F3, 1.1f);
        text(new Vec3(.5, 6.2, 189.5), "타워로", 0xF4F6F8, 1.4f);
    }

    private void label(Vec3 rel, String icon, int color, String name) {
        var holder = new ElementHolder();
        var stack = new ItemStack(Items.PAPER);
        stack.set(DataComponents.ITEM_MODEL, Identifier.fromNamespaceAndPath("destiny", "gui/hud/" + icon));
        stack.set(DataComponents.CUSTOM_MODEL_DATA, new CustomModelData(List.of(), List.of(), List.of(), List.of(color)));
        var item = new ItemDisplayElement(stack);
        item.setItemDisplayContext(ItemDisplayContext.NONE);
        item.setBillboardMode(Display.BillboardConstraints.CENTER);
        item.setScale(new Vector3f(1.1f));
        item.setBrightness(new Brightness(15, 15));
        holder.addElement(item);
        var text = new TextDisplayElement(Component.literal(name).withStyle(s -> s.withColor(color).withBold(true)));
        text.setBillboardMode(Display.BillboardConstraints.CENTER);
        text.setBackground(0x50000000);
        text.setScale(new Vector3f(1.2f));
        text.setOffset(new Vec3(0, -1.0, 0));
        holder.addElement(text);
        ChunkAttachment.ofTicking(holder, level, world(rel));
        decorations.add(holder);
    }

    private void text(Vec3 rel, String value, int color, float scale) {
        var holder = new ElementHolder();
        var text = new TextDisplayElement(Component.literal(value).withStyle(s -> s.withColor(color).withBold(true)));
        text.setBillboardMode(Display.BillboardConstraints.CENTER);
        text.setBackground(0x50000000);
        text.setScale(new Vector3f(scale));
        holder.addElement(text);
        ChunkAttachment.ofTicking(holder, level, world(rel));
        decorations.add(holder);
    }

    void tickDecorations(long tick) {
        if (shard == null || tick % 4 != 0) return;
        float a = tick / 40f;
        spin(shard, new Quaternionf().rotateY(a).rotateX(.6f), 1.1f);
        spin(shardCore, new Quaternionf().rotateY(-a * 1.7f).rotateZ(.7f), .55f);
    }

    /** Rotate a scaled unit cube about its own centre: translation = -R * half. */
    private static void spin(BlockDisplayElement e, Quaternionf rotation, float half) {
        e.setLeftRotation(rotation);
        e.setTranslation(rotation.transform(new Vector3f(-half, -half, -half)));
        e.startInterpolation();
    }

    public void destroyDecorations() {
        decorations.forEach(ElementHolder::destroy);
        decorations.clear();
        shard = null;
        shardCore = null;
    }
}
