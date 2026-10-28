package kim.biryeong.destiny.weapon;

import com.google.gson.Gson;
import net.minecraft.core.component.DataComponents;
import net.minecraft.nbt.IntTag;
import net.minecraft.nbt.LongTag;
import net.minecraft.nbt.CompoundTag;
import net.minecraft.world.item.ItemStack;
import net.minecraft.world.item.component.CustomData;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import java.util.*;

/** Implemented traits only, selected from the exact weapon's pinned official socket pool.
 * New/legacy stacks have no selected trait. Unsupported/corrupt saved hashes are inert.
 */
public final class WeaponPerks {
    public static final String ID = "auto_loading_holster";
    public static final long HASH = 3300816228L;
    public static final String HASH_KEY = "destiny_weapon_trait_hash";
    public static final String SOCKET_KEY = "destiny_weapon_trait_socket";
    public static final String SLOTS_KEY = "destiny_weapon_trait_sockets";
    public record Roll(String id, long hash, int socket, long perkHash, long plugSetHash) {}
    private record Perk(String id, long hash, int stowedTicks, String timingSource) {}
    private record Data(String stage, Perk perk, Roll[] weapons) {}
    private static final Data DATA = load();
    private WeaponPerks() {}

    private static Data load() {
        var input = WeaponPerks.class.getResourceAsStream("/destiny/weapons/w60-holster.json");
        if (input == null) throw new IllegalStateException("Missing W60 trait pools");
        try (var reader = new InputStreamReader(input, StandardCharsets.UTF_8)) {
            var data = new Gson().fromJson(reader, Data.class);
            if (data == null || !"W60".equals(data.stage) || data.perk == null || !ID.equals(data.perk.id)
                    || data.perk.hash != HASH || data.perk.stowedTicks < 1 || data.perk.stowedTicks > 1200
                    || data.perk.timingSource == null || data.perk.timingSource.isBlank()
                    || data.weapons == null || data.weapons.length == 0)
                throw new IllegalStateException("Invalid W60 trait timing/pool");
            var sockets = new HashSet<String>();
            for (var roll : data.weapons) {
                var entry = WeaponCatalog.find(roll.id).orElseThrow();
                if (roll.hash != WeaponCharacteristics.of(entry).bungieHash() || roll.perkHash != HASH
                        || roll.socket < 0 || roll.socket > 63 || roll.plugSetHash <= 0
                        || WeaponCharacteristics.of(entry).exotic() || entry.family().equals("sword")
                        || !sockets.add(roll.id + ":" + roll.socket))
                    throw new IllegalStateException("Invalid W60 trait socket " + roll);
            }
            return data;
        } catch (java.io.IOException e) { throw new IllegalStateException(e); }
    }
    public static int stowedTicks() { return DATA.perk.stowedTicks; }
    public static List<Roll> rolls() { return List.of(DATA.weapons); }
    public static List<Roll> available(ItemStack stack) {
        return available(stack, ID);
    }
    public static List<Roll> available(ItemStack stack, String id) {
        var entry = WeaponItems.entry(stack);
        var pool = IronGazeProfile.ID.equals(id) ? IronGazeProfile.rolls() : SlickdrawProfile.ID.equals(id) ? SlickdrawProfile.rolls() : GutshotProfile.ID.equals(id) ? GutshotProfile.rolls() : CorneredProfile.ID.equals(id) ? CorneredProfile.rolls() : OsmosisProfile.ID.equals(id) ? OsmosisProfile.rolls() : HipFireGripProfile.ID.equals(id) ? HipFireGripProfile.rolls() : MovingTargetProfile.ID.equals(id) ? MovingTargetProfile.rolls() : HeadseekerProfile.ID.equals(id) ? HeadseekerProfile.rolls() : SteadyHandsProfile.ID.equals(id) ? SteadyHandsProfile.rolls() : PulseMonitorProfile.ID.equals(id) ? PulseMonitorProfile.rolls() : UnrelentingProfile.ID.equals(id) ? UnrelentingProfile.rolls() : WhirlwindBladeProfile.ID.equals(id) ? WhirlwindBladeProfile.rolls() : EnGardeProfile.ID.equals(id) ? EnGardeProfile.rolls() : OpeningShotProfile.ID.equals(id) ? OpeningShotProfile.rolls() : BoxBreathingProfile.ID.equals(id) ? BoxBreathingProfile.rolls() : DynamicSwayProfile.ID.equals(id) ? DynamicSwayProfile.rolls() : AssassinsBladeProfile.ID.equals(id) ? AssassinsBladeProfile.rolls() : KillingTallyProfile.ID.equals(id) ? KillingTallyProfile.rolls() : SympatheticArsenalProfile.ID.equals(id) ? SympatheticArsenalProfile.rolls() : NoDistractionsProfile.ID.equals(id) ? NoDistractionsProfile.rolls() : RelentlessStrikesProfile.ID.equals(id) ? RelentlessStrikesProfile.rolls() : TirelessBladeProfile.ID.equals(id) ? TirelessBladeProfile.rolls() : MulliganProfile.ID.equals(id) ? MulliganProfile.rolls() : AmbitiousAssassinProfile.ID.equals(id) ? AmbitiousAssassinProfile.rolls() : ClownCartridgeProfile.ID.equals(id) ? ClownCartridgeProfile.rolls() : OverflowProfile.ID.equals(id) ? OverflowProfile.rolls() : AdagioProfile.ID.equals(id) ? AdagioProfile.rolls() : ImpulseAmplifierProfile.ID.equals(id) ? ImpulseAmplifierProfile.rolls() : RangefinderProfile.ID.equals(id) ? RangefinderProfile.rolls() : BackupPlanProfile.ID.equals(id) ? BackupPlanProfile.rolls() : EncoreProfile.ID.equals(id) ? EncoreProfile.rolls() : WellRoundedProfile.ID.equals(id) ? WellRoundedProfile.rolls() : WellspringProfile.ID.equals(id) ? WellspringProfile.rolls() : ThreshProfile.ID.equals(id) ? ThreshProfile.rolls() : PugilistProfile.ID.equals(id) ? PugilistProfile.rolls() : FiringLineProfile.ID.equals(id) ? FiringLineProfile.rolls() : FullAutoProfile.ID.equals(id) ? FullAutoProfile.rolls() : IronReachProfile.ID.equals(id) ? IronReachProfile.rolls() : UnderPressureProfile.ID.equals(id) ? UnderPressureProfile.rolls() : CompulsiveReloaderProfile.ID.equals(id) ? CompulsiveReloaderProfile.rolls() : EnsembleProfile.ID.equals(id) ? EnsembleProfile.rolls() : FirmlyPlantedProfile.ID.equals(id) ? FirmlyPlantedProfile.rolls() : ZenMomentProfile.ID.equals(id) ? ZenMomentProfile.rolls() : LeadFromGoldProfile.ID.equals(id) ? LeadFromGoldProfile.rolls() : QuickdrawProfile.ID.equals(id) ? QuickdrawProfile.rolls() : ElementalCapacitorProfile.ID.equals(id) ? ElementalCapacitorProfile.rolls() : SurplusProfile.ID.equals(id) ? SurplusProfile.rolls() : HighImpactReservesProfile.ID.equals(id) ? HighImpactReservesProfile.rolls() : VorpalProfile.ID.equals(id) ? VorpalProfile.rolls() : ThreatDetectorProfile.ID.equals(id) ? ThreatDetectorProfile.rolls() : HeatingUpProfile.ID.equals(id) ? HeatingUpProfile.rolls() : StatsForAllProfile.ID.equals(id) ? StatsForAllProfile.rolls() : FocusedFuryProfile.ID.equals(id) ? FocusedFuryProfile.rolls() : AdrenalineJunkieProfile.ID.equals(id) ? AdrenalineJunkieProfile.rolls() : FrenzyProfile.ID.equals(id) ? FrenzyProfile.rolls() : TapTheTriggerProfile.ID.equals(id) ? TapTheTriggerProfile.rolls() : PerpetualMotionProfile.ID.equals(id) ? PerpetualMotionProfile.rolls() : RapidHitProfile.ID.equals(id) ? RapidHitProfile.rolls() : SubsistenceProfile.ID.equals(id) ? SubsistenceProfile.rolls() : MultikillClipProfile.ID.equals(id) ? MultikillClipProfile.rolls() : SwashbucklerProfile.ID.equals(id) ? SwashbucklerProfile.rolls() : GraveRobberProfile.ID.equals(id) ? GraveRobberProfile.rolls() : OneForAllProfile.ID.equals(id) ? OneForAllProfile.rolls() : SurroundedProfile.ID.equals(id) ? SurroundedProfile.rolls() : FeedingFrenzyProfile.ID.equals(id) ? FeedingFrenzyProfile.rolls() : TrackingProfile.ID.equals(id) ? TrackingProfile.rolls() : DemolitionistProfile.ID.equals(id) ? DemolitionistProfile.rolls() : PayloadProfile.ID.equals(id) ? PayloadProfile.rolls() : DragonflyProfile.ID.equals(id) ? DragonflyProfile.rolls() : ID.equals(id) ? rolls() : KillClipProfile.ID.equals(id) ? KillClipProfile.rolls()
                : ArcherTempoProfile.ID.equals(id) ? ArcherTempoProfile.rolls()
                : OutlawProfile.ID.equals(id) ? OutlawProfile.rolls()
                : RampageProfile.ID.equals(id) ? RampageProfile.rolls()
                : SnapshotAimProfile.ID.equals(id) ? SnapshotAimProfile.rolls() : PrecisionReturnProfile.rolls(id);
        return entry.isEmpty() ? List.of() : pool.stream().filter(r -> r.id.equals(entry.get().id())).toList();
    }
    public static List<String> ids() { return List.of(ID, IronGazeProfile.ID, SlickdrawProfile.ID, GutshotProfile.ID, CorneredProfile.ID, OsmosisProfile.ID, HipFireGripProfile.ID, MovingTargetProfile.ID, HeadseekerProfile.ID, SteadyHandsProfile.ID, PulseMonitorProfile.ID, UnrelentingProfile.ID, WhirlwindBladeProfile.ID, EnGardeProfile.ID, OpeningShotProfile.ID, BoxBreathingProfile.ID, DynamicSwayProfile.ID, AssassinsBladeProfile.ID, KillingTallyProfile.ID, SympatheticArsenalProfile.ID, NoDistractionsProfile.ID, RelentlessStrikesProfile.ID, TirelessBladeProfile.ID, MulliganProfile.ID, AmbitiousAssassinProfile.ID, ClownCartridgeProfile.ID, OverflowProfile.ID, AdagioProfile.ID, ImpulseAmplifierProfile.ID, RangefinderProfile.ID, BackupPlanProfile.ID, EncoreProfile.ID, WellRoundedProfile.ID, WellspringProfile.ID, ThreshProfile.ID, PugilistProfile.ID, FiringLineProfile.ID, FullAutoProfile.ID, IronReachProfile.ID, UnderPressureProfile.ID, CompulsiveReloaderProfile.ID, EnsembleProfile.ID, FirmlyPlantedProfile.ID, ZenMomentProfile.ID, LeadFromGoldProfile.ID, QuickdrawProfile.ID, ElementalCapacitorProfile.ID, SurplusProfile.ID, HighImpactReservesProfile.ID, VorpalProfile.ID, ThreatDetectorProfile.ID, HeatingUpProfile.ID, StatsForAllProfile.ID, FocusedFuryProfile.ID, AdrenalineJunkieProfile.ID, FrenzyProfile.ID, TapTheTriggerProfile.ID, PerpetualMotionProfile.ID, RapidHitProfile.ID, SubsistenceProfile.ID, MultikillClipProfile.ID, KillClipProfile.ID, OutlawProfile.ID, RampageProfile.ID,
            PrecisionReturnProfile.TRIPLE_TAP, PrecisionReturnProfile.FOURTH_TIMES, SnapshotAimProfile.ID, ArcherTempoProfile.ID, DragonflyProfile.ID, PayloadProfile.ID, DemolitionistProfile.ID, TrackingProfile.ID, FeedingFrenzyProfile.ID, OneForAllProfile.ID, SurroundedProfile.ID, SwashbucklerProfile.ID, GraveRobberProfile.ID); }
    public static List<String> choices(ItemStack stack) { return ids().stream().filter(id -> !available(stack, id).isEmpty()).toList(); }
    public static String name(String id) {
        if (IronGazeProfile.ID.equals(id)) return "Iron Gaze";
        if (SlickdrawProfile.ID.equals(id)) return "Slickdraw";
        if (GutshotProfile.ID.equals(id)) return "Gutshot Straight";
        if (CorneredProfile.ID.equals(id)) return "Cornered";
        if (OsmosisProfile.ID.equals(id)) return "Osmosis";
        if (HipFireGripProfile.ID.equals(id)) return "Hip-Fire Grip";
        if (MovingTargetProfile.ID.equals(id)) return "Moving Target";
        if (HeadseekerProfile.ID.equals(id)) return "머리 추적기";
        if (SteadyHandsProfile.ID.equals(id)) return "흔들림 없는 손";
        if (PulseMonitorProfile.ID.equals(id)) return "Pulse Monitor";
        if (UnrelentingProfile.ID.equals(id)) return "Unrelenting";
        if (WhirlwindBladeProfile.ID.equals(id)) return "Whirlwind Blade";
        if (EnGardeProfile.ID.equals(id)) return "En Garde";
        if (OpeningShotProfile.ID.equals(id)) return "Opening Shot";
        if (BoxBreathingProfile.ID.equals(id)) return "Box Breathing";
        if (DynamicSwayProfile.ID.equals(id)) return "Dynamic Sway Reduction";
        if (AssassinsBladeProfile.ID.equals(id)) return "Assassin's Blade";
        if (KillingTallyProfile.ID.equals(id)) return "살육의 기록";
if (SympatheticArsenalProfile.ID.equals(id)) return "공감의 무기고";
if (NoDistractionsProfile.ID.equals(id)) return "방해 금지";
if (RelentlessStrikesProfile.ID.equals(id)) return "끈질긴 강타";
if (TirelessBladeProfile.ID.equals(id)) return "지칠 줄 모르는 칼날";
        if (MulliganProfile.ID.equals(id)) return "멀리건";
        if (AmbitiousAssassinProfile.ID.equals(id)) return "야심찬 암살가";
        if (ClownCartridgeProfile.ID.equals(id)) return "광대 탄약통";
        if (OverflowProfile.ID.equals(id)) return "범람";
        if (AdagioProfile.ID.equals(id)) return "아다지오";
        if (ImpulseAmplifierProfile.ID.equals(id)) return "충격 증폭기";

        if (RangefinderProfile.ID.equals(id)) return "Rangefinder";
        if (BackupPlanProfile.ID.equals(id)) return "Backup Plan";
        if (EncoreProfile.ID.equals(id)) return "Encore";
        if (WellRoundedProfile.ID.equals(id)) return "Well-Rounded";
        if (WellspringProfile.ID.equals(id)) return "Wellspring";
        if (ThreshProfile.ID.equals(id)) return "Thresh";
        if (PugilistProfile.ID.equals(id)) return "Pugilist";
        if (FiringLineProfile.ID.equals(id)) return "Firing Line";
        if (FullAutoProfile.ID.equals(id)) return "Full Auto Trigger System";
        if (IronReachProfile.ID.equals(id)) return "Iron Reach";
        if (UnderPressureProfile.ID.equals(id)) return "Under Pressure";
        if (CompulsiveReloaderProfile.ID.equals(id)) return "Compulsive Reloader";
        if (EnsembleProfile.ID.equals(id)) return "Ensemble";
        if (FirmlyPlantedProfile.ID.equals(id)) return "Firmly Planted";
        if (ZenMomentProfile.ID.equals(id)) return "참선의 순간";
        if (LeadFromGoldProfile.ID.equals(id)) return "황금 탄약";
        if (QuickdrawProfile.ID.equals(id)) return "빠른 무장";
        if (ElementalCapacitorProfile.ID.equals(id)) return "원소 축전지";
        if (SurplusProfile.ID.equals(id)) return "잉여";
        if (HighImpactReservesProfile.ID.equals(id)) return "고충격 예비탄";
        if (VorpalProfile.ID.equals(id)) return "치명적인 무기";
        if (ThreatDetectorProfile.ID.equals(id)) return "위협 감지기";
        if (HeatingUpProfile.ID.equals(id)) return "가열";
        if (StatsForAllProfile.ID.equals(id)) return "모두를 위한 능력치";
        if (FocusedFuryProfile.ID.equals(id)) return "집중된 분노";
        if (AdrenalineJunkieProfile.ID.equals(id)) return "아드레날린 중독자";
        if (FrenzyProfile.ID.equals(id)) return "광폭";
        if (TapTheTriggerProfile.ID.equals(id)) return "방아쇠 당기기";
        if (PerpetualMotionProfile.ID.equals(id)) return "영속적인 움직임";
        if (RapidHitProfile.ID.equals(id)) return "신속 발사";
        if (SubsistenceProfile.ID.equals(id)) return "연명";
        if (MultikillClipProfile.ID.equals(id)) return "다중 처치 탄창";
        if (SwashbucklerProfile.ID.equals(id)) return "무뢰한";
        if (GraveRobberProfile.ID.equals(id)) return "묘지 도굴꾼";
        if (OneForAllProfile.ID.equals(id)) return "모두를 위한 하나";
        if (SurroundedProfile.ID.equals(id)) return "포위";
        if (FeedingFrenzyProfile.ID.equals(id)) return "먹이 쟁탈전";
        if (TrackingProfile.ID.equals(id)) return "추적 모듈";
        if (DemolitionistProfile.ID.equals(id)) return "폭파 전문가";
        if (PayloadProfile.ID.equals(id)) return "폭발 탄약";
        if (DragonflyProfile.ID.equals(id)) return "잠자리";
        if (ArcherTempoProfile.ID.equals(id)) return "Archer's Tempo";
        if (SnapshotAimProfile.ID.equals(id)) return "스냅샷 조준경";
        if (PrecisionReturnProfile.TRIPLE_TAP.equals(id)) return "Triple Tap";
        if (PrecisionReturnProfile.FOURTH_TIMES.equals(id)) return "Fourth Time's the Charm";
        return ID.equals(id) ? "자동 장전 총집" : KillClipProfile.ID.equals(id) ? "살상 탄창" : OutlawProfile.ID.equals(id) ? "무법자" : RampageProfile.ID.equals(id) ? "광란" : id;
    }
    private static long savedHash(CompoundTag tag, int socket) {
        var modern = tag.get(SLOTS_KEY);
        if (modern instanceof CompoundTag slots && slots.contains(Integer.toString(socket)))
            return slots.get(Integer.toString(socket)) instanceof LongTag value ? value.longValue() : -1;
        if (modern != null && !(modern instanceof CompoundTag)) return -1;
        return tag.get(SOCKET_KEY) instanceof IntTag index && index.intValue() == socket
                && tag.get(HASH_KEY) instanceof LongTag hash ? hash.longValue() : -1;
    }
    /** Strict integral types, exact selected weapon and exact permitted trait socket. Read-only. */
    public static Optional<Roll> selected(ItemStack stack) {
        return selected(stack, ID);
    }
    public static Optional<Roll> selected(ItemStack stack, String id) {
        var custom = stack.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return Optional.empty();
        var tag = custom.copyTag();
        return available(stack, id).stream().filter(r -> savedHash(tag, r.socket) == r.perkHash).findFirst();
    }
    /** Socket choice changes no stack identity, ammunition, pose, cooldown, or player lore. */
    public static boolean select(ItemStack stack) {
        return select(stack, ID);
    }
    public static boolean select(ItemStack stack, String id) {
        var choices = available(stack, id);
        if (choices.isEmpty()) return false;
        if (selected(stack, id).isPresent()) return true;
        var slots = new CompoundTag();
        // Migrate only recognized selected traits, and only on a real edit. Reads stay pure.
        for (String other : ids()) selected(stack, other).ifPresent(r -> slots.putLong(Integer.toString(r.socket), r.perkHash));
        var choice = choices.getFirst();
        slots.putLong(Integer.toString(choice.socket), choice.perkHash); // Same socket is exclusive.
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.remove(HASH_KEY); tag.remove(SOCKET_KEY);
        tag.put(SLOTS_KEY, slots);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        WeaponAiming.perksEdited(stack);
        WeaponWhirlwindBlade.edited(stack); WeaponEnGarde.edited(stack); WeaponOpeningShot.edited(stack); WeaponBoxBreathing.edited(stack); WeaponDynamicSway.edited(stack); WeaponAssassinsBlade.edited(stack); WeaponPulseMonitor.edited(stack); WeaponUnrelenting.edited(stack); WeaponHeadseeker.edited(stack); WeaponOsmosis.edited(stack); WeaponSteadyHands.edited(stack); WeaponCornered.edited(stack);
        WeaponKillingTally.edited(stack); WeaponSympatheticArsenal.edited(stack); WeaponRelentlessStrikes.edited(stack); WeaponTirelessBlade.edited(stack);
        WeaponAmbitiousAssassin.edited(stack); WeaponClownCartridge.edited(stack); WeaponAdagio.edited(stack);
        WeaponBackupPlan.edited(stack); WeaponEncore.edited(stack); WeaponWellRounded.edited(stack);
        WeaponEnergyPerks.edited(stack);
        WeaponPugilist.edited(stack);
        WeaponEnsemble.edited(stack);
        WeaponDemolitionist.edited(stack);
        WeaponTracking.edited(stack);
        WeaponFeedingFrenzy.edited(stack);
        WeaponRapidHit.edited(stack);
        WeaponPerpetualMotion.edited(stack);
        WeaponTapTheTrigger.edited(stack); WeaponZenMoment.edited(stack);
        WeaponFrenzy.edited(stack);
        WeaponAdrenalineJunkie.edited(stack);
        WeaponFocusedFury.edited(stack);
        WeaponStatsForAll.edited(stack); WeaponHeatingUp.edited(stack); WeaponThreatDetector.edited(stack); WeaponQuickdraw.edited(stack);
        WeaponOneForAll.edited(stack);
        WeaponSurrounded.edited(stack);
        WeaponSwashbuckler.edited(stack);
        WeaponMultikillClip.edited(stack);
        WeaponSubsistence.edited(stack);
        WeaponGraveRobber.edited(stack);
        return true;
    }
    /** Atomic exact-pool replacement. Validate the whole tuple set before lifecycle or NBT writes. */
    public static boolean replaceSelection(ItemStack stack, List<Roll> selection) {
        if (stack == null || stack.getCount() != 1 || WeaponItems.entry(stack).isEmpty() || selection == null)
            return false;
        var allowed = new HashMap<Roll, String>();
        for (String id : ids()) for (var roll : available(stack, id)) allowed.put(roll, id);
        var sockets = new HashSet<Integer>();
        var traits = new HashSet<String>();
        var hashes = new HashSet<Long>();
        var canonical = new CompoundTag();
        for (var roll : selection) {
            if (roll == null || !allowed.containsKey(roll) || !sockets.add(roll.socket())
                    || !traits.add(allowed.get(roll)) || !hashes.add(roll.perkHash()))
                return false;
            canonical.putLong(Integer.toString(roll.socket()), roll.perkHash());
        }
        var custom = stack.get(DataComponents.CUSTOM_DATA);
        var before = custom == null ? new CompoundTag() : custom.copyTag();
        if (!before.contains(HASH_KEY) && !before.contains(SOCKET_KEY)
                && canonical.equals(before.get(SLOTS_KEY))) return true;
        clear(stack);
        var tag = stack.get(DataComponents.CUSTOM_DATA).copyTag();
        tag.put(SLOTS_KEY, canonical);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        return true;
    }
    public static boolean clear(ItemStack stack) {
        if (WeaponItems.entry(stack).isEmpty()) return false;
        var custom = stack.get(DataComponents.CUSTOM_DATA);
        if (custom == null) return false;
        var tag = custom.copyTag();
        if (!tag.contains(HASH_KEY) && !tag.contains(SOCKET_KEY) && !tag.contains(SLOTS_KEY)) return false;
        tag.remove(HASH_KEY); tag.remove(SOCKET_KEY); tag.remove(SLOTS_KEY);
        stack.set(DataComponents.CUSTOM_DATA, CustomData.of(tag));
        WeaponAiming.perksEdited(stack);
        WeaponWhirlwindBlade.edited(stack); WeaponEnGarde.edited(stack); WeaponOpeningShot.edited(stack); WeaponBoxBreathing.edited(stack); WeaponDynamicSway.edited(stack); WeaponAssassinsBlade.edited(stack); WeaponPulseMonitor.edited(stack); WeaponUnrelenting.edited(stack); WeaponHeadseeker.edited(stack); WeaponOsmosis.edited(stack); WeaponSteadyHands.edited(stack); WeaponCornered.edited(stack);
        WeaponKillingTally.edited(stack); WeaponSympatheticArsenal.edited(stack); WeaponRelentlessStrikes.edited(stack); WeaponTirelessBlade.edited(stack);
        WeaponAmbitiousAssassin.edited(stack); WeaponClownCartridge.edited(stack); WeaponAdagio.edited(stack);
        WeaponBackupPlan.edited(stack); WeaponEncore.edited(stack); WeaponWellRounded.edited(stack);
        WeaponEnergyPerks.edited(stack);
        WeaponPugilist.edited(stack);
        WeaponEnsemble.edited(stack);
        WeaponDemolitionist.edited(stack);
        WeaponTracking.edited(stack);
        WeaponFeedingFrenzy.edited(stack);
        WeaponRapidHit.edited(stack);
        WeaponPerpetualMotion.edited(stack);
        WeaponTapTheTrigger.edited(stack); WeaponZenMoment.edited(stack);
        WeaponFrenzy.edited(stack);
        WeaponAdrenalineJunkie.edited(stack);
        WeaponFocusedFury.edited(stack);
        WeaponStatsForAll.edited(stack); WeaponHeatingUp.edited(stack); WeaponThreatDetector.edited(stack); WeaponQuickdraw.edited(stack);
        WeaponOneForAll.edited(stack);
        WeaponSurrounded.edited(stack);
        WeaponSwashbuckler.edited(stack);
        WeaponMultikillClip.edited(stack);
        WeaponSubsistence.edited(stack);
        WeaponGraveRobber.edited(stack);
        return true;
    }
}
