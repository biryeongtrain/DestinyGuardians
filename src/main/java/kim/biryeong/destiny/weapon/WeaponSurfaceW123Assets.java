package kim.biryeong.destiny.weapon;

import com.google.gson.JsonParser;
import eu.pb4.polymer.resourcepack.api.PackResource;
import eu.pb4.polymer.resourcepack.api.PolymerResourcePackUtils;
import eu.pb4.polymer.resourcepack.api.ResourcePackBuilder;

import java.io.IOException;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

/** Low-element W126-W150 weapon art, including existing moving reload parts.
 * This separate output migration leaves W115 and historical source assets alone.
 */
public final class WeaponSurfaceW123Assets {
    static final Set<String> TARGETS = Set.of(
            "assets/destiny/models/weapon/auto_rifle/ammit_ar2.json",
            "assets/destiny/models/weapon_reload_w69/ammit_ar2_body.json",
            "assets/destiny/models/weapon_reload_w69/ammit_ar2_magazine.json",
            "assets/destiny/models/weapon/submachine_gun/the_recluse.json",
            "assets/destiny/models/weapon_reload_w100/the_recluse_body.json",
            "assets/destiny/models/weapon_reload_w100/the_recluse_magazine.json",
            "assets/destiny/models/weapon/sniper_rifle/beloved.json",
            "assets/destiny/models/weapon_reload_w47/beloved_body.json",
            "assets/destiny/models/weapon_reload_w47/beloved_magazine.json",
            "assets/destiny/models/weapon/machine_gun/hammerhead.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_body.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_magazine.json",
            "assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_cover.json",
            "assets/destiny/models/weapon/pulse_rifle/blast_furnace.json",
            "assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_body.json",
            "assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json",
            "assets/destiny/models/weapon/hand_cannon/duke_mk_44.json",
            "assets/destiny/models/weapon_reload_w64/duke_mk_44_body.json",
            "assets/destiny/models/weapon_reload_w64/duke_mk_44_cylinder.json",
            "assets/destiny/models/weapon/auto_rifle/gnawing_hunger.json",
            "assets/destiny/models/weapon/pulse_rifle/chattering_bone.json",
            "assets/destiny/models/weapon/shotgun/dust_rock_blues.json",
            "assets/destiny/models/weapon/auto_rifle/halfdan_d.json",
            "assets/destiny/models/weapon/hand_cannon/austringer.json",
            "assets/destiny/models/weapon/submachine_gun/antiope_d.json",
            "assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes.json",
            "assets/destiny/models/weapon/fusion_rifle/erentil_fr4.json",
            "assets/destiny/models/weapon/rocket_launcher/bad_omens.json",
            "assets/destiny/models/weapon/sidearm/lonesome.json",
            "assets/destiny/models/weapon/machine_gun/fixed_odds.json",
            "assets/destiny/models/weapon/rocket_launcher/code_duello.json",
            "assets/destiny/models/weapon/scout_rifle/distant_relation.json",
            "assets/destiny/models/weapon/shotgun/first_in_last_out.json",
            "assets/destiny/models/weapon/auto_rifle/steelfeather_repeater.json",
            "assets/destiny/models/weapon/pulse_rifle/bygones.json",
            "assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox.json",
            "assets/destiny/models/weapon/sword/falling_guillotine.json",
            "assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver.json",
            "assets/destiny/models/weapon/shotgun/ikelos_sg_v1_0_1.json",
            "assets/destiny/models/weapon/machine_gun/retrofit_escapade.json",
            "assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit.json",
            "assets/destiny/models/weapon/sword/crown_splitter.json",
            "assets/destiny/models/weapon/pulse_rifle/cold_denial.json",
            "assets/destiny/models/weapon/pulse_rifle/claws_of_the_wolf.json",
            "assets/destiny/models/weapon/scout_rifle/frontier_justice.json",
            "assets/destiny/models/weapon/submachine_gun/bug_out_bag.json",
            "assets/destiny/models/weapon/sniper_rifle/apostate.json",
            "assets/destiny/models/weapon/sword/abide_the_return.json",
            "assets/destiny/models/weapon/sword/goldtusk.json",
            "assets/destiny/models/weapon/sword/temptation_s_hook.json",
            "assets/destiny/models/weapon/sidearm/allied_demand.json",
            "assets/destiny/models/weapon/scout_rifle/aishas_embrace.json",
            "assets/destiny/models/weapon/scout_rifle/long_arm.json",
            "assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1.json",
            "assets/destiny/models/weapon/sidearm/farewell.json",
            "assets/destiny/models/weapon/sidearm/dead_man_walking_xx7463.json",
            "assets/destiny/models/weapon/sidearm/high_albedo.json",
            "assets/destiny/models/weapon/sidearm/brass_attacks.json",
            "assets/destiny/models/weapon/glaive/nezarec_s_whisper.json",
            "assets/destiny/models/weapon/fusion_rifle/null_composure.json",
            "assets/destiny/models/weapon/fusion_rifle/hollow_words.json",
            "assets/destiny/models/weapon/fusion_rifle/coriolis_force.json",
            "assets/destiny/models/weapon/fusion_rifle/dream_breaker.json",
            "assets/destiny/models/weapon/shotgun/parcel_of_stardust_fell_to_earth.json",
            "assets/destiny/models/weapon/shotgun/mindbender_s_ambition_adept.json",
            "assets/destiny/models/weapon/bow/biting_winds.json",
            "assets/destiny/models/weapon/bow/whispering_slab.json",
            "assets/destiny/models/weapon_bow_w50/biting_winds_body_hip.json",
            "assets/destiny/models/weapon_bow_w50/whispering_slab_body_hip.json",
            "assets/destiny/models/weapon/heavy_grenade_launcher/canis_major.json",
            "assets/destiny/models/weapon/heavy_grenade_launcher/dimensional_hypotrochoid.json",
            "assets/destiny/models/weapon/grenade_launcher/deafening_whisper.json",
            "assets/destiny/models/weapon/grenade_launcher/salvager_s_salvo.json",
            "assets/destiny/models/weapon/trace_rifle/retraced_path.json",
            "assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand.json",
            "assets/destiny/models/weapon/linear_fusion_rifle/stormchaser.json",
            "assets/destiny/models/weapon/rocket_launcher/bellowing_giant.json",
            "assets/destiny/models/weapon/rocket_launcher/pyroclastic_flow.json",
            "assets/destiny/models/weapon_scope_w45/line_in_the_sand_geometry.json",
            "assets/destiny/models/weapon_scope_w45/stormchaser_geometry.json");
    private static boolean initialized;

    private WeaponSurfaceW123Assets() {}

    public static synchronized void init() {
        if (initialized) return;
        PolymerResourcePackUtils.RESOURCE_PACK_CREATION_EVENT.register(WeaponSurfaceW123Assets::configure);
        initialized = true;
    }

    static void configure(ResourcePackBuilder builder) {
        configure(builder, Boolean.getBoolean("destiny.weapon.surface.w115"));
    }

    /** Explicit legacy W115 retains only its two weapons; all other targets still migrate.
     * Do not feed already transformed W115 bytes to the canonical W127 converter.
     */
    static void configure(ResourcePackBuilder builder, boolean legacyW115) {
        var rules = rules();
        var activeTargets = new java.util.HashSet<>(TARGETS);
        if (legacyW115) activeTargets.removeAll(WeaponSurfaceAssets.TARGETS);
        builder.addResourceConverter((path, resource) -> activeTargets.contains(path)
                ? convert(path, resource, rules) : resource);
        builder.addPreFinishTask(pack -> {
            for (String path : activeTargets) {
                if (pack.getResource(path) == null) throw incompatible(path, "missing emitted model");
                convert(path, pack.getResource(path), rules);
            }
        });
    }

    record Rule(String sourceSha256, String replacementSha256, String replacement) {}

    static Map<String, Rule> rules() {
        var manifest = JsonParser.parseString(read("weapon_surface_w123/manifest.json")).getAsJsonObject();
        if (manifest.get("schema").getAsInt() != 1 || !"W123".equals(manifest.get("stage").getAsString()))
            throw incompatible("manifest", "unknown schema/stage");
        var rules = new LinkedHashMap<String, Rule>();
        for (var element : manifest.getAsJsonArray("targets")) {
            var row = element.getAsJsonObject();
            String path = row.get("path").getAsString();
            String replacement = row.get("replacement").getAsString();
            String expected = "assets/destiny/models/weapon_surface_w123/" + path.substring(path.lastIndexOf('/') + 1);
            if (!TARGETS.contains(path) || rules.containsKey(path) || !replacement.equals(expected))
                throw incompatible(path, "unexpected target/replacement");
            String text = read(replacement);
            String replacementSha = row.get("replacementSha256").getAsString();
            if (!WeaponSurfaceAssets.sha256(text).equals(replacementSha))
                throw incompatible(path, "replacement changed");
            rules.put(path, new Rule(row.get("sourceSha256").getAsString(), replacementSha, text));
        }
        if (!rules.keySet().equals(TARGETS)) throw incompatible("manifest", "incomplete targets");
        return Map.copyOf(rules);
    }

    static PackResource convert(String path, PackResource resource, Map<String, Rule> rules) {
        if (!TARGETS.contains(path)) return resource;
        var rule = rules.get(path);
        if (resource == null || rule == null) throw incompatible(path, "missing model/rule");
        String current = WeaponSurfaceAssets.sha256(resource.asString());
        if (current.equals(rule.replacementSha256())) return resource;
        if (!current.equals(rule.sourceSha256())) throw incompatible(path, "source changed");
        return PackResource.fromString(rule.replacement());
    }

    private static String read(String path) {
        try (var input = WeaponSurfaceW123Assets.class.getResourceAsStream("/" + path)) {
            if (input == null) throw incompatible(path, "missing resource");
            return new String(input.readAllBytes(), StandardCharsets.UTF_8);
        } catch (IOException e) {
            throw new IllegalStateException("Cannot read W123 resource " + path, e);
        }
    }

    private static IllegalStateException incompatible(String path, String reason) {
        return new IllegalStateException("W123 model migration rejected " + path + ": " + reason);
    }
}
