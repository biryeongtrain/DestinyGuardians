package kim.biryeong.destiny.fireteam;

import kim.biryeong.destiny.campaign.RisingCampaign;
import kim.biryeong.destiny.strike.devils.DevilsLair;
import net.minecraft.server.level.ServerPlayer;

import java.util.List;

/**
 * The finder's current content. New activities (another strike, a dungeon, a raid) add a category if needed and an
 * {@link ActivityCatalog.Activity} with an adapter to their own start/entered/participating hooks here.
 */
final class FinderActivities {
    private FinderActivities() { }

    static void register() {
        ActivityCatalog.category(new ActivityCatalog.Category("strikes", "공격전",
                "화력팀과 함께 적의 거점을 공략하고 우두머리를 처치하세요.", "fireteam/mode_strikes", "fireteam/banner_strikes", 10));
        ActivityCatalog.category(new ActivityCatalog.Category("campaign", "캠페인",
                "수호자의 이야기를 따라가는 임무입니다.", "fireteam/mode_story", "fireteam/banner_story", 20));

        ActivityCatalog.activity(new ActivityCatalog.Activity("devils_lair", "strikes", "악마의 소굴", "공격전 · 우주선 발사 기지",
                "악마의 소굴로 들어가 발사 기지의 몰락자 세력을 약화시키세요.", "fireteam/banner_devils_lair",
                "fireteam/icon_devils_lair", 1, 3, 10, new ActivityCatalog.Launcher() {
            @Override public String check(List<ServerPlayer> fireteam) { return DevilsLair.check(fireteam); }
            @Override public String launch(List<ServerPlayer> fireteam) { return DevilsLair.start(fireteam); }
            @Override public boolean entered(ServerPlayer p) { return DevilsLair.entered(p); }
            @Override public boolean participating(ServerPlayer p) { return DevilsLair.participating(p); }
        }));

        // The Guardian Rises mission runs one private instance per Guardian: a one-person fireteam.
        ActivityCatalog.activity(new ActivityCatalog.Activity("guardian_rises", "campaign", "눈을 뜨세요, 수호자", "캠페인 · 떠오르는 수호자",
                "옛 러시아를 돌파하여 탈출하세요.", "fireteam/banner_guardian_rises", "fireteam/mode_story", 1, 1, 10,
                new ActivityCatalog.Launcher() {
            @Override public String check(List<ServerPlayer> fireteam) {
                return fireteam.size() != 1 ? "이 임무는 1인 전용입니다." : RisingCampaign.check(fireteam.getFirst());
            }
            @Override public String launch(List<ServerPlayer> fireteam) { return RisingCampaign.start(fireteam.getFirst(), false); }
            @Override public boolean entered(ServerPlayer p) { return RisingCampaign.entered(p); }
            @Override public boolean participating(ServerPlayer p) { return RisingCampaign.participating(p); }
        }));
    }
}
