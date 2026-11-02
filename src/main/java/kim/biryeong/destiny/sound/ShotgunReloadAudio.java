package kim.biryeong.destiny.sound;

import kim.biryeong.destiny.weapon.WeaponCatalog;
import kim.biryeong.destiny.weapon.WeaponProfile;
import net.minecraft.server.level.ServerPlayer;

/** Short shell cues follow real ammo transfers, never an uncancellable full-reload recording.
 * The final cue contains one insertion followed by the closing action, on a cancellable
 * owner-specific direct sound. No delayed callback
 * or generic "not reloading" edge can mistake a shot/swap/skill cancellation for completion.
 */
public final class ShotgunReloadAudio {
    private ShotgunReloadAudio() {}

    public static boolean handles(WeaponCatalog.Entry entry) {
        return entry.family().equals("shotgun") && WeaponProfile.forEntry(entry).shellReload();
    }

    /** Called only after an authoritative, positive shell transfer in the active weapon tick. */
    public static void inserted(ServerPlayer player, WeaponCatalog.Entry entry, boolean continuing) {
        if (!handles(entry)) return;
        if (continuing) DestinySounds.weapon(player, "shotgun", "reload_insert");
        else ReloadAudio.startShotgunFinish(player, entry);
    }
}
