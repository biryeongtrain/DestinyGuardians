#!/usr/bin/env python3
"""W201 explicit authored hand contacts. No model edits, runtime imports or subprocesses.

Coordinates below are intentional per-weapon choices, never inferred from whole-model
bounds. Geometry is read only to retain/check evidence. Re-run without flags to write
contacts.json and the report; --verify compares deterministic bytes without writing.
"""
import argparse
import ast
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUTPUT = Path("art/weapons/w201/contacts.json")
REPORT = Path("docs/qa/2026-10-27/w201/contacts-report.md")

# id | right xyz/rxyz | left xyz/rxyz | reload xyz/rxyz | policy | partHint |
# actual right, left, reload geometry names | individual rationale.
# Euler degrees, Rx Ry Rz. Fore-end palm faces upward at Z=-85; Y=90 aligns the forearm back along +Z.
# These are authored placements; raw element Euler angles are NOT glove rotations.
AUTHORED = r"""
duke_mk_44|8,9.4,7.92,-21,0,0|7.3,9.02,8.18,-21,0,-20|6.75,12.6,4.65,0,0,-80|cylinder|cylinder|Grip_palm_wood|Grip_palm_wood|Cylinder_shell_6|Wood palm below upper wood/web; cupped offhand; cylinder left wall, not crane pivot.
austringer|8,9.25,7.58,-25,0,0|7.28,8.88,7.88,-25,0,-20|6.85,12.35,4.8,0,0,-80|cylinder|moving|Grip_palm|Grip_palm|Cylinder_0|Palm block below neck; cup right hand; cylinder flank beside rear band, away from hinge.
seventh_seraph_officer_revolver|8,8.18,8.72,-26,0,0|7.3,7.8,9.02,-26,0,-20|7,11.9,5.7,0,0,-80|cylinder|cylinder|grip_core|grip_core|rear_chamber|Middle of sloped grip below neck; cup right; chamber left wall, authored box-cylinder approximation.
halfdan_d|8,8.55,8.55,-16,0,0|7.8,9.72,-1.8,0,90,-85|7.4,7.65,3.12,-3,0,0|magazine|magazine|Pistol_grip|Handguard_lower|Magazine_body|Grip below root; palm under lower handguard; detachable box side below feed neck.
ammit_ar2|8,8.95,8.3,-28,0,0|7.8,8.72,-3.8,0,90,-85|7.4,6.85,2.68,-16,0,0|magazine|magazine|Grip_backstrap|Lower_blue_beam|Magazine_body|Rubber grip center below tang; lower blue fore-end underside; magazine middle side corroborated by source Magazine landmark.
gnawing_hunger|8,8.65,8.28,-19,0,0|7.8,9.42,-1.4,0,90,-85|7.4,6.7,3.35,12,0,0|magazine|moving|grip/core|foreend/lower-spine|magazine/middle|Cloth grip center below generator web GRIP; under fore-end rail; curved magazine middle side.
steelfeather_repeater|8,8.22,8.25,-33,0,0|7.8,8.78,-1.6,0,90,-85|7.35,7.65,3.3,0,0,0|magazine|moving|pistol_grip|forearm_rubber|magazine_core|Sloping pistol grip middle; rubber forearm underside; magazine core side below fixed magwell.
cold_denial|8,8.62,8.35,-25,0,0|7.8,9.42,-1.2,0,90,-85|7.3,8.1,12.15,0,0,0|magazine|moving|grip_core|lower_handguard|magazine_core|Middle below web rather than stock; lower handguard underside; rear bullpup magazine side.
bygones|8,8.55,8.45,-25,0,0|7.8,9.12,-1.9,0,90,-85|7.35,7.65,12.2,11,0,0|magazine|moving|walnut_grip|forewood_core|magazine|Walnut middle below receiver; palm under forewood; rear magazine side follows its slant.
chattering_bone|8,8.15,8.67,-33,0,0|7.8,9.78,-1.6,0,90,-85|7.45,7.7,11.95,15,0,0|magazine|moving|grip_main|forearm_violet_core|magazine_main|Grip main below wrist, not receiver wrist core; violet forearm underside; rear magazine side below root.
blast_furnace|8,8.4,8.27,-29,0,0|7.8,9.45,-.5,0,90,-85|7.4,8,11.78,-8,0,0|magazine|magazine|Grip_core|Lower_foregrip|Magazine_core|Grip below root; lower foregrip physical underside after beam rotation; rear box magazine side.
claws_of_the_wolf|8,8.18,7.98,-17,0,0|7.8,9.22,-1.4,0,90,-85|7.35,7.95,11.36,11,0,0|magazine|moving|grip_core|lower_forging|magazine_core|Sloped grip center; palm below forging rather than claw tip; rear magazine flank.
frontier_justice|8,8.4,7.8,-29,0,0|7.8,9.22,-.8,0,90,-85|7.45,7.45,12.4,0,0,0|magazine|magazine|grip_core|forearm_belly|magazine|Grip below receiver; forearm belly underside; rear magazine side, no independently verified reload binding.
distant_relation|8,8.62,8.35,-22,0,0|7.8,9.05,-.4,0,90,-85|7.55,6.65,10.68,35,0,0|magazine|magazine|stock_grip|forewood_main|magazine_body|Stock wrist center; narrow forewood underside; small slanted magazine flank rather than floor center.
patron_of_lost_causes|8,7.8,8.72,-26,0,0|7.8,8.9,.3,0,90,-85|7.2,6.85,12.14,-8,0,0|magazine|magazine|pistol_grip|lower_silver_forearm|magazine_body|Lower pistol grip below silver shoulder; silver forearm underside; rear bullpup magazine broad side.
aishas_embrace|8,8.8,10.42,-24,0,0|7.8,9.48,.2,0,90,-85|7.35,6.7,10.8,27,0,0|magazine|moving|grip_frontstrap|forebody_core|magazine_curve|Frontstrap and palm block define rear grip; front underside support; magazine curve side below fixed palm, not entire palm assembly.
long_arm|8,8.65,8.8,38,0,0|7.8,7.83,1.5,0,90,-85|8.55,9.2,5.6,0,15,-80|shell|loading_port|stock_wrist|forewood_swell|receiver_main|Straight stock wrist requires swept hand pitch; forewood underside; side loading-port estimate on receiver, not a detachable tube.
antiope_d|8,9.3,9.48,-6,0,0|8,8.85,3.5,-27,0,0|7.5,5.8,8.68,0,0,0|magazine|magazine|grip_core|foregrip_body|magazine_core|Grip middle below upper web; offhand wraps actual angled vertical foregrip; narrow magazine side beneath grip.
bug_out_bag|8,9.08,7.43,-6,0,0|8,9.65,2.45,-50,0,-12|7.55,6.1,7.57,0,0,0|magazine|moving|grip_core|foregrip_diagonal|magazine_core|Grip middle; diagonal skeleton foregrip wrap rather than receiver underside; lower magazine side.
ikelos_smg_v1_0_1|8,8.4,8.25,0,0,0|7.8,9,3.6,-54,0,-20|7.5,4.55,8.26,0,0,0|magazine|magazine|grip_diagonal_lower|frame_grip_diagonal_-1|magazine|Skeleton rear grip between top and heel webs; angled forward frame; magazine side below well. Open-frame fingers need tuning.
the_recluse|8,8.2,3.88,-21,0,0|7.35,7.75,3.72,-21,0,-20|7.3,7.85,8.82,19,0,0|magazine|magazine|foregrip/core|foregrip/core|magazine/core|Named foregrip/core is the trigger-side sloped grip ahead of rear magazine; compact offhand cup avoids grasping exposed barrel.
allied_demand|8,9.15,8.88,-12,0,0|7.25,8.75,9.16,-12,0,-20|7.35,7.35,8.85,-12,0,0|magazine|magazine|green_grip_core|green_grip_core|magazine_lower|Small pistol: cup firing hand below web; lower magazine side, not slide or whole grip.
farewell|8,9.3,8.18,-14,0,0|7.22,8.9,8.45,-14,0,-20|7.2,7.02,8.83,-14,0,0|magazine|magazine|grip_core|grip_core|heel|Small pistol cupped support; heel side is visible proxy for authored whole-magazine assembly, not a recovered magazine shaft.
lonesome|8,9.45,8.8,-10,0,0|7.18,9.02,9.1,-10,0,-20|7.2,6.45,9.25,-10,0,0|magazine|moving|grip_core|grip_core|heel|Tall pistol grip middle below throat; cupped support; heel flank is limited visible magazine proxy, not proven full magazine geometry.
dead_man_walking_xx7463|8,9.55,6.85,-23,0,0|7.05,9.1,7.18,-23,0,-20|6.95,7,7.75,-6,0,0|magazine|magazine|filled_grip|filled_grip|heel_core|Broad pistol filled grip below throat; offhand cup; heel-side magazine estimate with no audited detachable shaft.
high_albedo|8,8.75,7.82,-17,0,0|7.2,8.32,8.1,-17,0,-20|7.15,5.98,8.67,-17,0,0|magazine|magazine|grip_core|grip_core|magazine_base|Compact burst pistol grip center; cupped support; base side follows existing added shaft assembly only while held.
brass_attacks|8,10.1,8.37,-19,0,0|7.05,9.65,8.72,-19,0,-20|7.1,6.62,9.34,-19,0,0|magazine|moving|grip_core|grip_core|magazine_base|Large burst pistol middle below wrist; cup right hand; magazine base side remains a short visible extraction proxy.
biting_winds|8,10.25,12.23,0,0,0|8.1,12.1,7.48,0,0,0|7.85,10.25,11.85,0,0,0|bow|moving|@string|hand_pad|@string|Bow exception: left holds hand pad, right pinches string at arrow height; reload contact is nocking reach, not left bow grip or detachable magazine.
whispering_slab|6.38,17.4,6.95,0,0,0|6.38,15.85,3.92,-15,0,0|6.2,17.4,6.65,0,0,0|bow|moving|@string|grip_spine|@string|Bow exception: left holds offset grip, right draws string behind arrow shelf. Preserve offset X=6.38; nocking point needs bow-specific hand routing.
bite_of_the_fox|8,8.05,8.34,-17,0,0|7.8,8.62,-1.8,0,90,-85|7.55,8.25,4.88,0,0,0|magazine|magazine|pistol_grip|forearm_lower_armor|magazine|Short grip middle; support under forearm armor away from blade heel; small magazine side ahead of trigger.
beloved|8,8.4,8.32,-27,0,0|7.8,8.98,.2,0,90,-85|7.55,7.5,5.25,0,0,0|magazine|magazine|stock_wrist|forearm_lower_spine|magazine_main|Stock wrist center; forearm lower spine underside; magazine side below socket, not bolt handle.
apostate|8,8.16,8.14,-15,0,0|7.8,8.92,-1.6,0,90,-85|7.35,7.95,3.1,0,0,0|magazine|magazine|grip/core|foreend/lower-spine|magazine/main|Grip core middle lower than carrier GRIP; support under filled fore-end; magazine broad side ahead of guard.
mindbender_s_ambition_adept|8,8.15,8.28,-27,0,0|7.8,9.58,-2.2,0,90,-85|7.4,10.4,5.5,0,0,-80|shell|loading_port|grip_palm|forebone_core|loading_tray|Palm below root, not bone spur; forebone underside; left shell feed at tray edge. Loading port stays with body, not pump.
dust_rock_blues|8,7.9,11.42,-31,0,0|7.8,8.52,.7,0,90,-85|7.3,9.15,7.1,0,0,-80|shell|loading_port|Ivory_grip|Foreend_black_core|Loading_floor|Ivory grip below web; black pump underside; fixed loading-floor edge ahead of guard, not detachable fore-end.
first_in_last_out|8,8.82,8.55,-18,0,0|7.8,9.2,-2.5,0,90,-85|7.35,10.1,5.6,0,0,-80|shell|loading_port|grip_core|foreend_belly|receiver_core|Grip below receiver; fore-end belly underside; receiver underside shell-port estimate. Existing shell path needs native clearance tuning.
parcel_of_stardust_fell_to_earth|8,9,9.18,-25,0,0|7.8,9.1,-.8,0,90,-85|7.35,10.1,3.3,0,0,-80|shell|loading_port|wood_grip|wooden_pump_core|loading_elevator|Wood wrist center; palm under wooden pump; fixed elevator edge for shell insertion, not tube midpoint.
ikelos_sg_v1_0_1|8,8.65,8.88,-23,0,0|7.8,8.98,-2.8,0,90,-85|7.35,10.2,5.8,0,0,-80|shell|loading_port|grip_front|foregrip_core|lower_receiver_rear|Skeleton rear grip between front and back rails; foregrip underside; loading-port approximation on receiver, not open grip void.
erentil_fr4|8,8.1,2.86,17,0,0|7.8,10.05,-4.6,0,90,-85|7.35,4.35,3.12,-14,0,0|magazine|magazine|Grip_main|Lower_support_rail|Cartridge_base|Tall forward-sloped grip center below root; rail underside support; cartridge base side, distinct from fixed grip heel.
hollow_words|8,7.2,2.55,22,0,0|7.8,9.05,-4.6,0,90,-85|7.3,4.35,3.7,22,0,0|magazine|magazine|grip_front_solid|lower_long_housing|under_grip_cell|Front solid grip, not lower brace; forward lower receiver underside; under-grip cell flank, not entire grip assembly.
dream_breaker|8,8.05,9.1,-26,0,0|7.8,10.08,-4.4,0,90,-85|7.15,7.3,3.57,0,0,0|magazine|magazine|lattice_stile_0|forward_filled_core|powerpack_full|Rear lattice grip below root; forward solid underside; powerpack flank. Open lattice and rope clearance are estimates.
null_composure|8,8.5,5.35,-26,0,0|7.8,9.35,-5.2,0,90,-85|7.1,7.1,.27,0,0,0|magazine|magazine|Grip_main|Forearm_lower_chamfer_-1|Battery_keel_solid|Grip middle below root; underside along long forearm chamfer after rotation; battery keel broad side below receiver.
coriolis_force|8,9.15,7.52,-18,0,0|7.8,10.78,-6,0,90,-85|7.4,8.2,.02,0,0,0|magazine|magazine|rear_grip|handguard_lower|cartridge_solid|Use actual rear grip middle below haunch instead of high carrier GRIP; fore-end underside; cartridge side, not anchor at feed top.
line_in_the_sand|8,8.28,8,-29,0,0|8,7.25,-.79,-14,0,0|7.2,5.6,6.8,0,0,0|magazine|magazine|pistol_grip|foregrip|lower_battery|Rear pistol grip middle; offhand wraps small sloped vertical foregrip; long lower battery flank rather than stock.
stormchaser|8,8.25,8.02,-24,0,0|7.8,9.12,-2.3,0,90,-85|7.25,6.78,7.61,-24,0,0|magazine|magazine|pistol_grip|lower_forebody|power_shoe|Grip center; forward body underside; power-shoe side is whole battery assembly proxy, not trigger guard.
retraced_path|8,9.1,9.62,-9,0,0|7.8,8.25,-1.5,0,90,-85|7.25,6.9,4,13,0,0|magazine|moving|pistol_grip|lower_broad_casing_-1|magazine_well|Rear pistol grip middle; lower forearm underside; magazine-well beam is existing moving pack proxy, mechanics remain inferred.
salvager_s_salvo|8,8.18,8.24,-32,0,0|8,8.9,-2.14,0,0,0|7.15,12.2,4.6,0,0,-80|shell|loading_port|grip_main|foregrip_0|breech_plug_0|Rear grip middle; actual vertical foregrip; shell approach beside fixed breech, not a detachable breech plug or automatic barrel attachment.
deafening_whisper|8,9.32,7.63,-28,0,0|8,9.65,-3.04,0,0,0|6.4,12.85,9.8,0,0,-80|shell|loading_port|pistol_grip|front_grip|breech_0|Grip middle; vertical front grip; breech left edge is shell-loading reach estimate, separate from fore-end break motion.
edge_transit|8,8.4,8.73,-28,0,0|8,7.95,-2.35,-21,0,0|5.8,10.1,3.1,0,0,-80|magazine|magazine|pistol_grip|front_grip_upper|drum_core_0|Grip below neck; angled vertical front grip; left drum flank, not hinge pivot. Follow hinged drum only during handling.
canis_major|8,8.65,7.8,-30,0,0|8,8.6,-3.25,-31,0,0|5.45,10.05,1.8,0,0,-80|magazine|magazine|pistol_grip|front_grip|drum_core_0|Rear grip center; long angled forward grip; left drum side, no audited per-weapon detached-drum motion claimed.
dimensional_hypotrochoid|8,8.2,9.05,-17,0,0|8,7.9,-2.7,-26,0,0|5.65,10.1,2.6,0,0,-80|magazine|magazine|grip_front|foregrip|drum_solid_0|Rear skeleton grip center between rails; sloped vertical foregrip; drum left flank near latch, not whole-model midpoint.
bad_omens|8,8.3,8.12,-12,0,0|8,8.9,1.88,0,0,0|7.1,12.2,17,90,0,0|shell|magazine|pistol_wood|front_grip_wood|aft_tube_0|Pistol wood below mount; vertical forward wood grip; rear loading mouth and incoming rocket side, payload is authored rather than a detachable tube.
bellowing_giant|8,8.35,7.83,-25,0,0|8,8.95,2.17,0,0,0|7,12.05,.4,90,0,0|shell|magazine|Pistol_grip|Foregrip_body|Launch_chamber_heart|Pistol grip below mount; vertical foregrip; front incoming rocket grip at generator insertion anchor, not rear breech. Reload-only payload proxy.
code_duello|8,8.45,8.15,-17,0,0|8,9.15,2,0,0,0|7,12,7.5,90,0,0|magazine|magazine|Pistol_grip|Foregrip|Tube_solid_heart|Cleaned pistol grip wins over generator carrier GRIP at Z16; vertical foregrip; canister side inside tube near rear extraction end.
pyroclastic_flow|8,7.7,14.53,-47,0,0|7.8,9.38,7.5,0,90,-85|7.05,10.6,17.5,90,0,0|shell|loading_port|pistol_grip|receiver_cradle|rear_socket_floor|Rear slanted pistol grip; cradle underside ahead of trigger; rear loading-mouth reach estimate, no detached rocket transform audited.
fixed_odds|8,8.75,8.28,-29,0,0|7.8,9.05,-2,0,90,-85|10.6,8.9,3,0,0,-80|magazine|magazine|pistol_grip|rear_forearm_swell|ammo_box_front|Grip center; rear forearm swell underside; LEFT hand crosses to actual right-mounted ammunition-box front face, not a central phantom magazine.
hammerhead|8,8.5,7.98,-18,0,0|7.8,9.75,-3.8,0,90,-85|4.4,8.4,3.9,0,0,-80|magazine|magazine|pistol_grip|gas_cylinder|drum_0_horizontal_core|Narrow pistol grip middle; support below gas/forearm assembly; near drum outer left wall, both drums form one reload assembly.
retrofit_escapade|8,8.55,8.48,-24,0,0|7.8,8.85,-1.3,0,90,-85|4.5,8.45,3.92,0,0,-80|magazine|magazine|pistol_grip|foregrip_body|drum_solid_core|Grip middle; broad foregrip underside; left offset drum outer wall, not center or cover hinge; connected belt follows same feed assembly.
nezarec_s_whisper|8,8.7,8,0,0,0|8,12,8,0,0,0|7.55,6.35,8,0,0,0|fixed|loading_port|bare_fluted_shaft_core|ivory_bound_grip_core|magenta_front_cell_-1|Glaive: lower right shaft hold, upper left ivory hold; left reload reach at stock cell side is a fixed-port approximation. No detachable cell or original reload hand recovered.
ace_of_spades|8,8.05,7.98,-22.5,0,0|7.3,7.65,8.25,-22.5,0,-20|6.95,10.4,4.72,0,0,-80|cylinder|cylinder|@82|@82|@31|Original unnamed cube82 rotates to center8,8,8; place below upper web rather than blindly using W157 carrier GRIP. Cup right hand; drum left side from audited DRUM_CENTER.
izanagis_burden|8,7.9,8,-12,0,0|7.8,7.6,1.1,0,90,-85|7.5,6.85,6.92,0,0,0|magazine|magazine|@53|@23|@26|Original unnamed cube53 rotates to center8,8,8; modest grip pitch is authored between wrist and lower grip. Lower frame under fore-end support; magazine26 left side confirmed by W91 partition.
"""

RELOAD = {
 'ace_of_spades': 'generate_ace_reload_w157.py',
 'izanagis_burden': 'generate_izanagi_presentation_w91.py',
 'ammit_ar2': 'generate_reload_models_w69.py',
 'beloved': 'generate_reload_models_w47.py',
 'the_recluse': 'generate_reload_models_w100.py',
 'hammerhead': 'generate_reload_w114_hammerhead.py',
 'blast_furnace': 'generate_reload_w114_blast_furnace.py',
 'gnawing_hunger': 'generate_reload_w164_gnawing_hunger.py',
 'lonesome': 'generate_reload_w164_lonesome.py',
 'bug_out_bag': 'generate_reload_w166_bug_out_bag.py',
 'steelfeather_repeater': 'generate_reload_w166_steelfeather_repeater.py',
 'cold_denial': 'generate_reload_w167_cold_denial.py',
 'austringer': 'generate_reload_w168_austringer.py',
 'bygones': 'generate_reload_w168_bygones.py',
 'duke_mk_44': 'generate_reload_w169_duke_mk_44.py',
 'retraced_path': 'generate_reload_w170_retraced_path.py',
 'aishas_embrace': 'generate_reload_w171_aishas_embrace.py',
 'chattering_bone': 'generate_reload_w172_chattering_bone.py',
 'salvager_s_salvo': 'generate_reload_w173_salvager_s_salvo.py',
 'claws_of_the_wolf': 'generate_reload_w174_claws_of_the_wolf.py',
 'brass_attacks': 'generate_reload_w176_brass_attacks.py',
 'bad_omens': 'generate_reload_w177_bad_omens.py',
 'bite_of_the_fox': 'generate_reload_w177_bite_of_the_fox.py',
 'dream_breaker': 'generate_reload_w178_dream_breaker.py',
 'null_composure': 'generate_reload_w179_null_composure.py',
 'fixed_odds': 'generate_reload_w179_fixed_odds.py',
 'edge_transit': 'generate_reload_w180_edge_transit.py',
 'halfdan_d': 'generate_reload_w180_halfdan_d.py',
 'seventh_seraph_officer_revolver': 'generate_reload_w181_seventh_seraph_officer_revolver.py',
 'retrofit_escapade': 'generate_reload_w181_retrofit_escapade.py',
 'antiope_d': 'generate_reload_w182_antiope_d.py',
 'ikelos_smg_v1_0_1': 'generate_reload_w182_ikelos_smg_v1_0_1.py',
 'high_albedo': 'generate_reload_w183_high_albedo.py',
 'patron_of_lost_causes': 'generate_reload_w183_patron_of_lost_causes.py',
 'distant_relation': 'generate_reload_w184_distant_relation.py',
 'farewell': 'generate_reload_w184_farewell.py',
 'apostate': 'generate_reload_w185_apostate.py',
 'hollow_words': 'generate_reload_w185_hollow_words.py',
 'bellowing_giant': 'generate_reload_w187_bellowing_giant.py',
 'code_duello': 'generate_reload_w187_code_duello.py',
 'line_in_the_sand': 'generate_reload_w188_line_in_the_sand.py',
 'stormchaser': 'generate_reload_w188_stormchaser.py',
 'coriolis_force': 'generate_reload_w189_coriolis_force.py',
 'erentil_fr4': 'generate_reload_w189_erentil_fr4.py',
 'biting_winds': 'generate_bow_models_w50.py',
 'whispering_slab': 'generate_bow_models_w50.py',
}
ASSET = Path('src/main/resources/assets/destiny')
COMMON_LIMITS = [
 'Authored contact estimates; medium geometry-placement confidence is not native verification. All glove rotations, clearance and timing require visual tuning.',
 'No dynamic player skin, no original extracted hands, no native verified contact, no recovered finger IK. No live DCC or game was opened.',
 'Positions are canonical weapon model units; place glove local center [8,8,8] here, then apply exactly the selected leaf/body display. Do not reuse the body rotation pivot as the palm center.',
 'Reload contact is a LEFT-hand handling target in neutral model space. Follow its actual moving-part transform only while that hand handles that part; release before recovery. Static port hints must stay on body.',
]


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def geometries(value):
    """Support list/dict parts, solids, geometry and original element variants."""
    if isinstance(value, dict):
        if 'from' in value and 'to' in value:
            yield value
        else:
            for key, child in value.items():
                if key not in ('source', 'source_landmarks', 'input_sha256', 'raw_input_sha256'):
                    yield from geometries(child)
    elif isinstance(value, list):
        for child in value:
            yield from geometries(child)


def catalog():
    rows = read(Path('src/main/resources/destiny/weapons/w30.json'))
    for stage in (83, 84):
        for exotic in read(Path(f'src/main/resources/destiny/weapons/w{stage}-exotics.json')):
            extra = exotic['catalog']
            rows.extend(extra if isinstance(extra, list) else [extra])
    assert len(rows) == 65 and len({row['id'] for row in rows}) == 65
    assert sum(row['family'] == 'sword' for row in rows) == 5
    return {row['id']: row for row in rows if row['family'] != 'sword'}


def snapshot(geo, index=None):
    data = {key: geo[key] for key in ('name', 'from', 'to', 'rotation') if key in geo}
    if index is not None:
        data['elementIndex'] = index
    return data


def literal_anchors(path):
    result = {}
    for node in ast.walk(ast.parse((ROOT / path).read_text())):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id in (
                    'GRIP', 'HINGE', 'PIVOT', 'DRUM_CENTER', 'MAG_ANCHOR',
                    'MAGAZINE_ANCHOR', 'PACK_INSERTION_ANCHOR'):
                    try:
                        result[target.id] = ast.literal_eval(node.value)
                    except (ValueError, TypeError):
                        pass
    return result


def generate():
    rows = catalog()
    weapons = {}
    summary = []
    for line in AUTHORED.strip().splitlines():
        (weapon, right, left, reload, policy, hint, right_name,
         left_name, reload_name, rationale) = line.split('|')
        assert weapon in rows and weapon not in weapons, weapon
        family = rows[weapon]['family']
        exotic = weapon in ('ace_of_spades', 'izanagis_burden')
        model_id = ('item/weapon/' if exotic else 'weapon_surface_w123/') + weapon
        model_path = ASSET / f'models/{model_id}.json'
        model = read(model_path)
        design_path = Path(f'art/weapons/w123/{weapon}/design.json')
        design = {} if exotic else read(design_path)
        named = {geo['name']: geo for geo in geometries(design) if 'name' in geo}
        evidence = []
        for role, text, name in [('right', right, right_name), ('left', left, left_name),
                                  ('reload', reload, reload_name)]:
            values = [float(v) for v in text.split(',')]
            assert len(values) == 6 and all(math.isfinite(v) for v in values), weapon
            assert all(-32 <= v <= 48 for v in values[:3]), weapon
            assert all(-180 <= v <= 180 for v in values[3:]), weapon
            if name == '@string':
                original_path = ASSET / f'models/weapon/bow/{weapon}.json'
                index = 128 if weapon == 'biting_winds' else 114
                source_geo = read(original_path)['elements'][index]
                # Retain the real original index; never give an unnamed mesh a semantic hash.
                source, geo = original_path, snapshot(source_geo, index)
                confidence = 'low'
            elif name.startswith('@'):
                index = int(name[1:])
                source, geo = model_path, snapshot(model['elements'][index], index)
                confidence = 'medium'
            else:
                assert name in named, f'{weapon}: actual design geometry missing: {name}'
                assert any(e.get('name') == name for e in model['elements']), f'{weapon}: canonical leaf missing {name}'
                source, geo = design_path, snapshot(named[name])
                confidence = 'medium'
            if role == 'reload' and (policy in ('shell', 'fixed') or weapon not in RELOAD or
                                     weapon in ('lonesome','brass_attacks','farewell','high_albedo','retraced_path')):
                confidence = 'low'
            evidence.append(dict(role=role, source=str(source), sourceSha256=sha(source),
                                 geometry=geo, confidence=confidence,
                                 status='authored_approximation', rationale=rationale))
        if design.get('source_landmarks'):
            evidence.append(dict(role='source_landmarks', source=str(design_path),
                                 confidence='reference_only',
                                 observation='Verbatim source names and bounds; no guessed semantic relabeling or anatomical anchor claim.',
                                 landmarks=design['source_landmarks']))
        reload_path = Path('scripts') / RELOAD[weapon] if weapon in RELOAD else None
        if reload_path:
            evidence.append(dict(role='reloadMotion', source=str(reload_path),
                                 sourceSha256=sha(reload_path), confidence='reference_only',
                                 auditedConstants=literal_anchors(reload_path),
                                 observation='Existing generator anchor/partition reference only; carrier GRIP/HINGE is not necessarily glove contact. No generator executed.'))
        limitations = list(COMMON_LIMITS)
        if weapon not in RELOAD:
            limitations.append('No dedicated per-weapon moving-part generator audited. Hint is semantic intent; fall back to body until a matching moving part is resolved.')
        if family == 'bow':
            limitations.append('Bow handedness exception: right is draw/string hand; left is fixed riser grip. Reload.contact is a nocking reach for a future bow-specific route. Do not drag the left riser hand onto moving string through the generic reload blend; full draw requires W50 draw displacement.')
        if policy in ('shell','fixed'):
            limitations.append('Fixed loading-port target is approximate; never parent it to pump/barrel/cylinder merely because that leaf moves. Incoming payload hints need visibility and handling phases, not full-reload attachment.')
        if weapon == 'code_duello':
            limitations.append('W187 GRIP=[8,7.4,16] is a body carrier pivot, not the cleaned Pistol_grip at [8,8.45,8.15]. Right uses actual cleaned grip; master must transform through the body display without changing that display pivot.')
        if weapon == 'ace_of_spades':
            limitations.append('W157 GRIP=[8,8.234410476,6.728186918] differs from original cube82 rotated center [8,8,8]; chosen grip uses original dimensions below web. Drum contact uses W157 DRUM_CENTER, offset to left flank; apply cylinder rotation about HINGE only during handling.')
        if weapon in ('fixed_odds','hammerhead','retrofit_escapade'):
            limitations.append('Magazine policy includes ammunition box/drums and belt; LEFT hand may cross center. Do not attach to separately moving cover or charging handle.')
        def pose(text):
            values = [float(v) for v in text.split(',')]
            return dict(position=values[:3], rotation=values[3:])
        reload_pose = pose(reload)
        weapons[weapon] = dict(family=family, canonicalModel='destiny:'+model_id,
                               right=pose(right), left=pose(left),
                               reload=dict(contact=reload_pose['position'], rotation=reload_pose['rotation'],
                                           partHint=hint, policy=policy),
                               evidence=evidence, limitations=limitations)
        summary.append((weapon, right_name, left_name, reload_name, policy,
                        '/'.join(e['confidence'] for e in evidence[:3])))
    assert set(weapons) == set(rows) and len(weapons) == 60
    data = dict(schemaVersion=1, weapons=dict(sorted(weapons.items())))
    report = report_text(data, summary)
    return (json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode(), report.encode()


def report_text(data, summary):
    lines = [
        '# W201 authored weapon hand contacts', '',
        '60 contacts cover the CURRENT canonical65 catalog: WeaponCatalog loads w30.json (63) and WeaponExotics appends w83/w84 (2). Five sword entries are excluded; BetterModel fullbody owns sword first-person suppression. Includes two bows and one glaive.', '',
        'Only contacts.json, this generator, and this report are authored. No main/shared/runtime/assets edits, native/Gradle, live DCC, children, dynamic player skin, original extracted hands, or native verified contact. Master owns graph routing and visual tuning.', '',
        'Read AGENTS.md, RTK.md, the minecraft-weapon-art-design skill and its Ace/Izanagi study. Current local geometry and generator evidence are recorded per role in contacts.json; the historical study is guidance, not current native evidence.', '',
        'All 180 positions and 180 rotations are explicit authored constants. No whole-model bounds midpoint heuristic is used. The generator reads all design variants to validate actual geometry names and emit verbatim bounds/rotations; those checks do not prove visual contact. Original unnamed Ace/Izanagi elements use real numeric indices, never invented names. source_landmarks retain actual source names without guessing semantic hashes.', '',
        'Coordinate contract: absolute weapon model units, +Y up, muzzle -Z. Transform glove local center [8,8,8] to each position, apply authored degree rotation Rx Ry Rz, then exactly the selected weapon leaf/body display (including pivot compensation). Right palm outside +X; mirrored left outside -X. Most fore-end supports use Y=90/Z=-85: palm upward and forearm back along +Z after native Ammit inspection. Vertical foregrips/shaft holds stay upright; small pistols cup the right hand. Do not copy a source beam Euler rotation directly to the glove.', '',
        'Confidence: medium = named solid/original dimension supports the neighborhood; low = port, nock, hidden shaft, mechanism or handling estimate. Every rotation and all fit/clearance remain authored and need native visual tuning. reference_only anchors/landmarks are evidence, not verified grip positions.', '',
        'Master current generic reload blend: support to contact p=.05..20, hold through .78, return by .98. This is an initial routing contract, not verified per-weapon timing. Contacts are neutral model-space targets, not already opened/transformed coordinates. Apply an existing moving-part transform exactly once, only during its handling phase. Fixed loading_port hints remain on primary body. Never use the support glove as an always-attached moving-part child.', '',
        'Priority native tuning: bows must retain left riser grip and use right string/nock routing instead of generic left-magazine logic; W50 full draw adds string displacement. Cylinder handling needs release before flick-close. Shell loaders retain fixed port contact or follow a visible incoming round only while held. Bellowing Giant uses a reload-only front-inserted payload; Code Duello uses the canister. Fixed Odds crosses left hand to the right-mounted box; Hammerhead/Retrofit use offset drum feed assemblies, not covers. No phase alignment is claimed from the static data.', '',
        'Known carrier/contact differences: Code Duello W187 GRIP [8,7.4,16] vs cleaned Pistol_grip [8,8.45,8.15]; keep existing body pivot and use the latter for the glove. Ace W157 GRIP [8,8.234410476,6.728186918] vs original cube82 rotated center [8,8,8]; grip follows original cube neighborhood, drum uses audited DRUM_CENTER/HINGE. Other generator GRIPs are retained in evidence even when a lower palm-center choice differs.', '',
        'Verification: run `rtk proxy python3 scripts/art/build_weapon_hand_contacts_w201.py --verify` from this worktree. It checks exact canonical65-minus-swords coverage, 60 entries, source names in cleaned design AND canonical leaf, original indices, finite xyz/Euler values, model-unit range [-32,48], rotation range [-180,180], and deterministic JSON/report bytes. No tests beyond this generator sanity verification were requested or run. No native, pack-load, motion or performance success is claimed.', '',
        '| Weapon | Right evidence | Left evidence | Reload evidence | Policy | Confidence R/L/reload |',
        '|---|---|---|---|---|---|',
    ]
    for weapon, r, l, reload, policy, confidence in sorted(summary):
        lines.append(f'| {weapon} | {r} | {l} | {reload} | {policy} | {confidence} |')
    lines += ['', '`@N` means original unnamed element index N; `@string` means original W50 string index (Biting Winds128, Whispering Slab114), not a guessed geometry name. Per-weapon rationale, source hashes, actual bounds and limitations are in contacts.json.', '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true', help='Compare deterministic outputs without writing')
    args = parser.parse_args()
    payload, report = generate()
    for path, content in ((OUTPUT, payload), (REPORT, report)):
        if args.verify:
            if not (ROOT/path).exists() or (ROOT/path).read_bytes() != content:
                raise SystemExit(f'Generated output differs: {path}')
        else:
            (ROOT/path).parent.mkdir(parents=True, exist_ok=True)
            (ROOT/path).write_bytes(content)
    print(('VERIFIED' if args.verify else 'WROTE') + ' W201: 60 non-sword canonical contacts; finite explicit poses; source evidence; deterministic JSON/report')


if __name__ == '__main__':
    main()
