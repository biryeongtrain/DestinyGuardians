package kim.biryeong.destiny.crucible;

import net.minecraft.server.level.ServerPlayer;

/** Entry point kept for the runtime; the Destiny-style presentation lives in {@link CrucibleUi}. */
public final class CrucibleHud {
    private CrucibleHud() { }
    public static void render(ServerPlayer p, ControlMatch.Snapshot snap, String map, int respawnTicks,
                              CrucibleUi.Roster roster, int nowTick, int introTicks) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(p)) { remove(p); return; }
        CrucibleUi.render(p, snap, map, respawnTicks, roster, nowTick, introTicks);
    }
    public static void remove(ServerPlayer p) { CrucibleUi.remove(p); }
}
