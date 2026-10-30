package kim.biryeong.destiny.crucible;

import kim.biryeong.minigamelib.displayhud.DisplayHud;
import kim.biryeong.minigamelib.displayhud.TextDisplayHud;
import net.minecraft.network.chat.Component;
import net.minecraft.server.level.ServerPlayer;
import net.minecraft.world.entity.Display;
import java.util.Locale;

/** Top-centre score, timer and three capture diamonds, colored relative to the viewer's team. */
public final class CrucibleHud {
    private static final String ID = "destiny:crucible_control";
    private static final int FRIEND = 0x7BCBEF, ENEMY = 0xFF6262, NEUTRAL = 0xE5E3DB;
    private CrucibleHud() { }
    public static void render(ServerPlayer p, ControlMatch.Snapshot snap, String map, int respawnTicks) {
        if (kim.biryeong.destiny.inventory.WeaponScreen.active(p)) { remove(p); return; }
        var own = snap.members().get(p.getUUID());
        if (own == null) { remove(p); return; }
        var foe = own == ControlMatch.Team.ALPHA ? ControlMatch.Team.BRAVO : ControlMatch.Team.ALPHA;
        int seconds = (snap.remainingTicks()+19)/20;
        var text = Component.empty();
        switch (snap.phase()) {
            case WAITING -> text.append(Component.literal("점령 · " + map + "\n상대 수호자를 기다리는 중 · " + snap.members().size() + "명").withColor(NEUTRAL));
            case INTRO -> text.append(Component.literal("시련의 장  /  점령\n" + map).withColor(NEUTRAL));
            case RESULTS -> text.append(Component.literal(snap.winner() == null ? "무승부" : snap.winner() == own ? "승리" : "패배")
                    .withColor(snap.winner() == own ? FRIEND : ENEMY))
                    .append(Component.literal("  " + snap.scores().get(own) + " : " + snap.scores().get(foe)
                            + "\n" + seconds + "초 후 탑으로 복귀").withColor(NEUTRAL));
            case PLAYING -> {
                text.append(Component.literal(String.valueOf(snap.scores().get(own))).withColor(FRIEND))
                        .append(Component.literal(String.format(Locale.ROOT, "     %d:%02d     ", seconds/60, seconds%60)).withColor(NEUTRAL))
                        .append(Component.literal(String.valueOf(snap.scores().get(foe))).withColor(ENEMY)).append("\n");
                for (String id : ControlMatch.ZONE_IDS) {
                    var zone = snap.zones().get(id);
                    int color = zone.owner() == null ? NEUTRAL : zone.owner() == own ? FRIEND : ENEMY;
                    String progress = zone.contested() ? " 경합" : zone.capturingTeam() != null ? " " + (int)(zone.progress()*100) + "%" : "";
                    text.append(Component.literal("  ◇ " + id + progress + "  ").withColor(color));
                }
                if (snap.paused()) text.append(Component.literal("\n상대 팀 복귀 대기 · "
                        + (snap.forfeitRemainingTicks()+19)/20 + "초").withColor(NEUTRAL));
                if (respawnTicks > 0) text.append(Component.literal("\n부활 준비 " + (respawnTicks+19)/20).withColor(NEUTRAL));
            }
        }
        var existing = DisplayHud.getHud(p, ID);
        if (existing != null && text.equals(existing.getExtraData("content"))) return;
        TextDisplayHud hud = existing instanceof TextDisplayHud h ? h : new TextDisplayHud();
        hud.updateWhenDataChanged(false); hud.setLineWidth(512);
        hud.setTextAlignment(Display.TextDisplay.Align.CENTER);
        hud.setText(text); hud.getTextDisplay().setText(Component.literal("\n").append(text));
        hud.setScale(120,120,1); hud.setAlignment(DisplayHud.HudAlignment.CENTER);
        hud.setLocation(960,200,30); hud.setBackgroundColor(0); hud.setShadowToggle(true);
        hud.setOpacity(255); hud.setAboveHand(true); hud.setViewRange(1000); hud.removeWhenPlayerDied(true);
        hud.setExtraData("content",text);
        if (existing == null) hud.spawn(p, ID);
        hud.update();
    }
    public static void remove(ServerPlayer p) { DisplayHud.removeHud(p,ID); }
}
