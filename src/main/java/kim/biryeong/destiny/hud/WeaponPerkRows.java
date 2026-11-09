package kim.biryeong.destiny.hud;

import java.util.ArrayList;
import java.util.Collection;
import java.util.HashSet;
import java.util.List;
import java.util.Objects;

/**
 * Stateless projection of actual weapon buffs into a bounded classic-Destiny-inspired feed.
 * This is not a reproduction of the modern game's full HUD categories.
 */
final class WeaponPerkRows {
    static final String PREFIX = "destiny:hud_perk_";
    static final int MAX_ROWS = 4;
    private WeaponPerkRows() {}

    enum Layout {
        TIMER(List.of("marker", "label", "minutes", "colon", "tens", "ones")),
        STACKED_TIMER(List.of("marker", "label", "x", "count", "minutes", "colon", "tens", "ones")),
        COUNT(List.of("marker", "label", "x", "count")),
        DECIMAL_COUNT(List.of("marker", "label", "x", "count_tens", "count")),
        DECIMAL_COUNT_TIMER(List.of("marker", "label", "x", "count_tens", "count", "minutes", "colon", "tens", "ones")),
        FLAG(List.of("marker", "label")),
        COUNT_TIMER(List.of("marker", "label", "x", "count", "minutes", "colon", "tens", "ones"));

        final List<String> suffixes;
        Layout(List<String> suffixes) { this.suffixes = suffixes; }
        boolean timed() { return this == TIMER || this == STACKED_TIMER || this == COUNT_TIMER || this == DECIMAL_COUNT_TIMER; }
        boolean counted() { return this == COUNT || this == DECIMAL_COUNT || this == STACKED_TIMER || this == COUNT_TIMER || this == DECIMAL_COUNT_TIMER; }
    }

    // Preserve legacy enum positions; PRIORITY inserts new damage rows before reload/utility.
    enum Kind {
        MEMENTO_MORI("memento_mori_", "perk_memento_mori_w83", Layout.COUNT),
        HONED_EDGE("honed_edge_", "perk_honed_edge_w84", Layout.COUNT),
        KILL_CLIP("", "perk_kill_clip_w61", Layout.TIMER),
        MULTIKILL_CLIP("multikill_clip_", "perk_multikill_clip_w165", Layout.STACKED_TIMER),
        RAMPAGE("rampage_", "perk_rampage_w66_x", Layout.TIMER),
        ONE_FOR_ALL("one_for_all_", "perk_one_for_all_w109", Layout.TIMER),
        SURROUNDED("surrounded_", "perk_surrounded_w109", Layout.FLAG),
        SWASHBUCKLER("swashbuckler_", "perk_swashbuckler_w110", Layout.STACKED_TIMER),
        OUTLAW("outlaw_", "perk_outlaw_w62", Layout.TIMER),
        ARCHERS_TEMPO("archers_tempo_", "perk_archers_tempo_w73", Layout.TIMER),
        NO_DISTRACTIONS("no_distractions_", "perk_no_distractions_w85", Layout.FLAG),
        RAPID_HIT("rapid_hit_", "perk_rapid_hit_w169", Layout.STACKED_TIMER),
        FEEDING_FRENZY("feeding_frenzy_", "perk_feeding_frenzy_w108", Layout.STACKED_TIMER),
        PERPETUAL_MOTION("perpetual_motion_", "perk_perpetual_motion_w170", Layout.COUNT),
        TAP_THE_TRIGGER("tap_the_trigger_", "perk_tap_the_trigger_w171", Layout.TIMER),
        FRENZY("frenzy_", "perk_frenzy_w172", Layout.TIMER),
        ADRENALINE_JUNKIE("adrenaline_junkie_", "perk_adrenaline_junkie_w173", Layout.COUNT_TIMER),
        FOCUSED_FURY("focused_fury_", "perk_focused_fury_w174", Layout.TIMER),
        STATS_FOR_ALL("stats_for_all_", "perk_stats_for_all_w176", Layout.TIMER),
        HEATING_UP("heating_up_", "perk_heating_up_w177", Layout.COUNT_TIMER),
        THREAT_DETECTOR("threat_detector_", "perk_threat_detector_w178", Layout.COUNT),
        SURPLUS("surplus_", "perk_surplus_w183", Layout.COUNT),
        KILLING_TALLY("killing_tally_", "perk_killing_tally_w199", Layout.COUNT),
        WHIRLWIND_BLADE("whirlwind_blade_", "perk_whirlwind_blade_w199", Layout.DECIMAL_COUNT_TIMER),
        EN_GARDE("en_garde_", "perk_en_garde_w199", Layout.TIMER),
        ASSASSINS_BLADE("assassins_blade_", "perk_assassins_blade_w199", Layout.TIMER),
        DYNAMIC_SWAY("dynamic_sway_", "perk_dynamic_sway_w199", Layout.DECIMAL_COUNT),
        BOX_BREATHING("box_breathing_", "perk_box_breathing_w200", Layout.FLAG),
        PULSE_MONITOR("pulse_monitor_", "perk_pulse_monitor_w200", Layout.FLAG),
        UNRELENTING("unrelenting_", "perk_unrelenting_w200", Layout.FLAG),
        HEADSEEKER("headseeker_", "perk_headseeker_w202", Layout.FLAG),
        STEADY_HANDS("steady_hands_", "perk_steady_hands_w202", Layout.TIMER),
        PRECISION_INSTRUMENT("precision_instrument_", "perk_precision_instrument_w327", Layout.COUNT_TIMER),
        DESPERATE_MEASURES("desperate_measures_", "perk_desperate_measures_w327", Layout.COUNT_TIMER),
        SUCCESSFUL_WARM_UP("successful_warm_up_", "perk_successful_warm_up_w327", Layout.TIMER),
        KEEP_AWAY("keep_away_", "perk_keep_away_w327", Layout.FLAG),
        LONE_WOLF("lone_wolf_", "perk_lone_wolf_w327", Layout.FLAG),
        ENLIGHTENED_ACTION("enlightened_action_", "perk_enlightened_action_w327", Layout.DECIMAL_COUNT_TIMER),
        EDDY_CURRENT("eddy_current_", "perk_eddy_current_w327", Layout.TIMER),
        PERFECT_FLOAT("perfect_float_", "perk_perfect_float_w327", Layout.TIMER),
        OFFHAND_STRIKE("offhand_strike_", "perk_offhand_strike_w327", Layout.TIMER),
        LOOSE_CHANGE("loose_change_", "perk_loose_change_w327", Layout.TIMER),
        HEAL_CLIP("heal_clip_", "perk_heal_clip_w327", Layout.TIMER),
        PERMEABILITY("permeability_", "perk_permeability_w327", Layout.FLAG),
        REPULSOR_BRACE("repulsor_brace_", "perk_repulsor_brace_w327", Layout.TIMER);

        final String key;
        final String label;
        final Layout layout;
        Kind(String key, String label, Layout layout) {
            this.key = key;
            this.label = label;
            this.layout = layout;
        }
        String nodeId(String suffix) { return PREFIX + key + suffix; }
        List<String> nodeIds() { return layout.suffixes.stream().map(this::nodeId).toList(); }
    }

    private static final List<Kind> PRIORITY = priorityOrder();

    private static List<Kind> priorityOrder() {
        var order = new ArrayList<>(List.of(Kind.values()));
        var damage = List.of(Kind.KILLING_TALLY, Kind.WHIRLWIND_BLADE, Kind.EN_GARDE,
                Kind.ASSASSINS_BLADE, Kind.HEADSEEKER);
        order.removeAll(damage);
        order.addAll(order.indexOf(Kind.OUTLAW), damage);
        order.remove(Kind.STEADY_HANDS);
        order.add(order.indexOf(Kind.FEEDING_FRENZY) + 1, Kind.STEADY_HANDS);
        return List.copyOf(order);
    }

    record Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                    int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                    boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                    int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                    int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                    int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                    int tapTheTriggerTicks, int frenzyTicks,
                    int adrenalineJunkieStacks, int adrenalineJunkieTicks, int focusedFuryTicks,
                    int statsForAllTicks, int heatingUpStacks, int heatingUpTicks, int threatDetectorStacks, int surplusCharges,
                    int killingTallyStacks, int whirlwindBladeStacks, int whirlwindBladeTicks,
                    int enGardeTicks, int assassinsBladeTicks, int dynamicSwayStacks,
                    boolean boxBreathingReady, boolean pulseMonitorActive, boolean unrelentingActive,
                    int headseekerTicks, int steadyHandsTicks) {
        // W200 and older callers never invent W202 runtime observations.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks, int adrenalineJunkieStacks,
                 int adrenalineJunkieTicks, int focusedFuryTicks, int statsForAllTicks,
                 int heatingUpStacks, int heatingUpTicks, int threatDetectorStacks, int surplusCharges,
                 int killingTallyStacks, int whirlwindBladeStacks, int whirlwindBladeTicks,
                 int enGardeTicks, int assassinsBladeTicks, int dynamicSwayStacks,
                 boolean boxBreathingReady, boolean pulseMonitorActive, boolean unrelentingActive) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks,
                    rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks,
                    adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks,
                    heatingUpStacks, heatingUpTicks, threatDetectorStacks, surplusCharges,
                    killingTallyStacks, whirlwindBladeStacks, whirlwindBladeTicks,
                    enGardeTicks, assassinsBladeTicks, dynamicSwayStacks,
                    boxBreathingReady, pulseMonitorActive, unrelentingActive, 0, 0);
        }

        // W199 callers preserve their observations; new label-only flags are never inferred.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks, int adrenalineJunkieStacks,
                 int adrenalineJunkieTicks, int focusedFuryTicks, int statsForAllTicks,
                 int heatingUpStacks, int heatingUpTicks, int threatDetectorStacks, int surplusCharges,
                 int killingTallyStacks, int whirlwindBladeStacks, int whirlwindBladeTicks,
                 int enGardeTicks, int assassinsBladeTicks, int dynamicSwayStacks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks,
                    rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks,
                    adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks,
                    heatingUpStacks, heatingUpTicks, threatDetectorStacks, surplusCharges,
                    killingTallyStacks, whirlwindBladeStacks, whirlwindBladeTicks,
                    enGardeTicks, assassinsBladeTicks, dynamicSwayStacks, false, false, false);
        }

        // W183 callers preserve every earlier field; new rows require explicit live observations.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks, int adrenalineJunkieStacks,
                 int adrenalineJunkieTicks, int focusedFuryTicks, int statsForAllTicks,
                 int heatingUpStacks, int heatingUpTicks, int threatDetectorStacks, int surplusCharges) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks,
                    rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks,
                    adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks,
                    heatingUpStacks, heatingUpTicks, threatDetectorStacks, surplusCharges, 0, 0, 0, 0, 0, 0);
        }

        // W178 and earlier callers preserve all fields and observe no unreported ability charges.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                    int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                    boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                    int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                    int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                    int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                    int tapTheTriggerTicks, int frenzyTicks,
                    int adrenalineJunkieStacks, int adrenalineJunkieTicks, int focusedFuryTicks,
                    int statsForAllTicks, int heatingUpStacks, int heatingUpTicks, int threatDetectorStacks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks, mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks, feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks, swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks, adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks, heatingUpStacks, heatingUpTicks, threatDetectorStacks, 0);
        }

        // W177 callers preserve all earlier fields; no inferred Threat Detector proximity.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks, int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge, boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks, int oneForAllTicks, boolean surrounded, int swashbucklerStacks, int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks, int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks, int tapTheTriggerTicks, int frenzyTicks, int adrenalineJunkieStacks, int adrenalineJunkieTicks, int focusedFuryTicks, int statsForAllTicks, int heatingUpStacks, int heatingUpTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks, mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks, feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks, swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks, adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks, heatingUpStacks, heatingUpTicks, 0);
        }

        // Pre-W177 adapters observe no Heating Up without both actual runtime values.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks, int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge, boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks, int oneForAllTicks, boolean surrounded, int swashbucklerStacks, int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks, int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks, int tapTheTriggerTicks, int frenzyTicks, int adrenalineJunkieStacks, int adrenalineJunkieTicks, int focusedFuryTicks, int statsForAllTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks, mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks, feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks, swashbucklerTicks, multikillClipStacks, multikillClipTicks, rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks, adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, statsForAllTicks, 0, 0);
        }

        // Pre-W176 adapters observe no Stats for All until they supply its actual remaining ticks.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks,
                 int adrenalineJunkieStacks, int adrenalineJunkieTicks, int focusedFuryTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks,
                    frenzyTicks, adrenalineJunkieStacks, adrenalineJunkieTicks, focusedFuryTicks, 0);
        }

        // Pre-W174 adapters observe no Focused Fury until they supply its actual remaining ticks.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks,
                 int adrenalineJunkieStacks, int adrenalineJunkieTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks,
                    frenzyTicks, adrenalineJunkieStacks, adrenalineJunkieTicks, 0);
        }

        // Pre-W173 adapters observe no Adrenaline Junkie until both live values are supplied.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks, int frenzyTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, frenzyTicks, 0, 0);
        }

        // Pre-W172 adapters observe no Frenzy until they supply its actual remaining ticks.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks,
                 int tapTheTriggerTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, perpetualMotionStacks, tapTheTriggerTicks, 0);
        }

        // Pre-W171 adapters observe no Tap the Trigger until they supply its live remaining ticks.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks, int perpetualMotionStacks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, perpetualMotionStacks, 0);
        }

        // Pre-W170 adapters observe no Perpetual Motion until they supply its live count.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks,
                 int rapidHitStacks, int rapidHitTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks,
                    rapidHitStacks, rapidHitTicks, 0);
        }

        // Existing adapters observe no Rapid Hit until they explicitly supply its live state.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks, int multikillClipStacks, int multikillClipTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, multikillClipStacks, multikillClipTicks, 0, 0);
        }

        // Pre-MKC adapters default all later perks to zero.
        Snapshot(int killClipTicks, int outlawTicks, int rampageStacks, int rampageTicks,
                 int archerTempoTicks, int mementoMoriRounds, int honedEdgeCharge,
                 boolean noDistractions, int feedingFrenzyStacks, int feedingFrenzyTicks,
                 int oneForAllTicks, boolean surrounded, int swashbucklerStacks,
                 int swashbucklerTicks) {
            this(killClipTicks, outlawTicks, rampageStacks, rampageTicks, archerTempoTicks,
                    mementoMoriRounds, honedEdgeCharge, noDistractions, feedingFrenzyStacks,
                    feedingFrenzyTicks, oneForAllTicks, surrounded, swashbucklerStacks,
                    swashbucklerTicks, 0, 0);
        }
    }

    record Row(Kind kind, int ticks, int count, int slot) {
        // Optional tens node disappears when a live count drops from ten to a single digit.
        List<String> nodeIds() {
            return kind.nodeIds().stream()
                    .filter(id -> count >= 10 || !id.equals(kind.nodeId("count_tens"))).toList();
        }
        int y() { return 778 - 32 * slot; }
        // Ceil remaining ticks; avoid overflow even for an unexpectedly large duration.
        int seconds() { return ticks <= 0 ? 0 : 1 + (ticks - 1) / 20; }
        String label() { return kind == Kind.RAMPAGE ? kind.label + count : kind.label; }
        // Mori is remaining empowered emissions, not seconds; retain the existing six-round display cap.
        int displayCount() { return kind == Kind.MEMENTO_MORI ? Math.min(6, count) : count; }
    }

    static List<Row> project(Snapshot state) {
        Objects.requireNonNull(state, "state");
        var rows = new ArrayList<Row>(MAX_ROWS);
        // Inputs are observed once by the adapter; hidden rows neither pause nor extend a runtime buff.
        for (Kind kind : PRIORITY) {
            int ticks = switch (kind) {
                case KILL_CLIP -> state.killClipTicks();
                case MULTIKILL_CLIP -> state.multikillClipTicks();
                case RAMPAGE -> state.rampageTicks(); // next stack decay, not total buff life
                case ONE_FOR_ALL -> state.oneForAllTicks();
                case SWASHBUCKLER -> state.swashbucklerTicks();
                case OUTLAW -> state.outlawTicks();
                case ARCHERS_TEMPO -> state.archerTempoTicks();
                case RAPID_HIT -> state.rapidHitTicks();
                case FEEDING_FRENZY -> state.feedingFrenzyTicks();
                case TAP_THE_TRIGGER -> state.tapTheTriggerTicks();
                case FRENZY -> state.frenzyTicks();
                case ADRENALINE_JUNKIE -> state.adrenalineJunkieTicks();
                case FOCUSED_FURY -> state.focusedFuryTicks();
                case STATS_FOR_ALL -> state.statsForAllTicks();
                case HEATING_UP -> state.heatingUpTicks();
                case WHIRLWIND_BLADE -> state.whirlwindBladeTicks();
                case EN_GARDE -> state.enGardeTicks();
                case ASSASSINS_BLADE -> state.assassinsBladeTicks();
                case HEADSEEKER -> state.headseekerTicks();
                case STEADY_HANDS -> state.steadyHandsTicks();
                default -> 0;
            };
            int count = switch (kind) {
                case MEMENTO_MORI -> state.mementoMoriRounds();
                case MULTIKILL_CLIP -> state.multikillClipStacks();
                case HONED_EDGE -> state.honedEdgeCharge();
                case RAMPAGE -> state.rampageStacks();
                case SWASHBUCKLER -> state.swashbucklerStacks();
                case RAPID_HIT -> state.rapidHitStacks();
                case FEEDING_FRENZY -> state.feedingFrenzyStacks();
                case PERPETUAL_MOTION -> state.perpetualMotionStacks();
                case ADRENALINE_JUNKIE -> state.adrenalineJunkieStacks();
                case HEATING_UP -> state.heatingUpStacks();
                case THREAT_DETECTOR -> state.threatDetectorStacks();
                case SURPLUS -> state.surplusCharges();
                case KILLING_TALLY -> state.killingTallyStacks();
                case WHIRLWIND_BLADE -> state.whirlwindBladeStacks();
                case DYNAMIC_SWAY -> state.dynamicSwayStacks();
                default -> 0;
            };
            boolean active = switch (kind) {
                case KILLING_TALLY -> count >= 1 && count <= 3;
                case WHIRLWIND_BLADE -> count >= 1 && count <= 10 && ticks >= 1 && ticks <= 70;
                case EN_GARDE -> ticks >= 1 && ticks <= 30;
                case ASSASSINS_BLADE -> ticks >= 1 && ticks <= 100;
                case DYNAMIC_SWAY -> count >= 1 && count <= 10;
                // The short held-source damage window needs a flag, not a seconds countdown.
                case HEADSEEKER -> ticks >= 1 && ticks <= 11;
                // Aggregate observation includes live stowed sources; reset duration comes from runtime.
                case STEADY_HANDS -> ticks >= 1 && ticks <= 170;
                case MEMENTO_MORI -> count > 0;
                case HONED_EDGE -> count >= 2;
                // Movement stages are observed counts, not a duration or expiration estimate.
                case PERPETUAL_MOTION, THREAT_DETECTOR -> count >= 1 && count <= 2;
                // Current equipped single-charge grenade/melee/class ability observations only.
                case SURPLUS -> count >= 1 && count <= 3;
                // Observe only the live 12-tick window; never infer activation or clamp corrupt input.
                case TAP_THE_TRIGGER -> ticks >= 1 && ticks <= 12;
                // Frenzy runtime supplies the actual remaining 144-tick window.
                case FRENZY -> ticks >= 1 && ticks <= 144;
                // Focused Fury exposes only its observed live 220-tick window.
                case FOCUSED_FURY -> ticks >= 1 && ticks <= 220;
                // Only the actual active buff is timed; target progress never produces a row.
                case STATS_FOR_ALL -> ticks >= 1 && ticks <= 200;
                case HEATING_UP -> count >= 1 && count <= 2 && ticks >= 1 && ticks <= 110;
                // Both values are live observations; inconsistent/corrupt state stays hidden.
                case ADRENALINE_JUNKIE -> count >= 1 && count <= 5 && ticks >= 1 && ticks <= 90;
                case MULTIKILL_CLIP -> count >= 1 && count <= 3 && ticks > 0;
                case RAPID_HIT -> count >= 1 && count <= 5 && ticks > 0;
                case RAMPAGE, SWASHBUCKLER, FEEDING_FRENZY -> count > 0 && ticks > 0;
                case SURROUNDED -> state.surrounded();
                case NO_DISTRACTIONS -> state.noDistractions();
                case BOX_BREATHING -> state.boxBreathingReady();
                case PULSE_MONITOR -> state.pulseMonitorActive();
                case UNRELENTING -> state.unrelentingActive();
                default -> ticks > 0;
            };
            if (active) rows.add(new Row(kind, ticks, count, rows.size()));
            if (rows.size() == MAX_ROWS) break;
        }
        return List.copyOf(rows);
    }

    record Extra(String id, int count, int ticks) {}
    /** One bounded feed: actual new observations share the legacy four-row budget. */
    static List<Row> merge(List<Row> legacy, List<Extra> extra) {
        var added = new ArrayList<Row>();
        for (var value : extra) {
            Kind kind;
            try { kind = Kind.valueOf(value.id().toUpperCase(java.util.Locale.ROOT)); }
            catch (IllegalArgumentException ex) { continue; }
            if (!kind.label.endsWith("_w327") || value.count() < 1 || value.count() > 99
                    || (kind.layout.timed() ? value.ticks() <= 0 : value.ticks() != -1)) continue;
            if (added.stream().noneMatch(r -> r.kind() == kind))
                added.add(new Row(kind, Math.min(1180, value.ticks()), value.count(), 0));
        }
        var ordered = new ArrayList<Row>();
        legacy.stream().filter(r -> r.kind() == Kind.MEMENTO_MORI || r.kind() == Kind.HONED_EDGE).forEach(ordered::add);
        added.stream().filter(r -> r.kind() == Kind.PRECISION_INSTRUMENT || r.kind() == Kind.DESPERATE_MEASURES).forEach(ordered::add);
        legacy.stream().filter(r -> r.kind() != Kind.MEMENTO_MORI && r.kind() != Kind.HONED_EDGE).forEach(ordered::add);
        added.stream().filter(r -> r.kind() != Kind.PRECISION_INSTRUMENT && r.kind() != Kind.DESPERATE_MEASURES).forEach(ordered::add);
        var out = new ArrayList<Row>();
        for (var row : ordered) { if (out.size() == MAX_ROWS) break; out.add(new Row(row.kind(),row.ticks(),row.count(),out.size())); }
        return List.copyOf(out);
    }

    /** Remove all old feed nodes not in this projection, including legacy/unknown suffixes. */
    static List<String> nodesToRemove(List<Row> visible, Collection<String> existingIds) {
        var retained = new HashSet<String>();
        for (Row row : visible) retained.addAll(row.nodeIds());
        return existingIds.stream().filter(id -> id.startsWith(PREFIX) && !retained.contains(id))
                .sorted().toList();
    }
}
