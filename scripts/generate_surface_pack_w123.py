#!/usr/bin/env python3
"""W150: eighty scoped substitutions via the existing W123 migration namespace.

No geometry simplification or performance certification. --verify is read-only.
"""
import argparse, hashlib, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
MAX_ELEMENTS = 1000
RES = ROOT / 'src/main/resources'
PINS = {'assets/destiny/models/weapon/auto_rifle/ammit_ar2.json': 'b531f95f712e369098043ebb73a91065130bf7f6dcaeac185ad550d9d9f3ebf9', 'assets/destiny/models/weapon_reload_w69/ammit_ar2_body.json': 'ca45508409c2316dbdd6d0b415e56f28f2942e7c5a8632a7836c4057c790f443', 'assets/destiny/models/weapon_reload_w69/ammit_ar2_magazine.json': '328d2f6bfd66937e3e8339658d30f09c52bb84e6216dee9c98013b8deeb45785', 'assets/destiny/models/weapon/submachine_gun/the_recluse.json': 'b338c341d40234e39356ca70f47594e5d625c6521f102ea417a06956d33f73ae', 'assets/destiny/models/weapon_reload_w100/the_recluse_body.json': '74d624d9329cd6becf763bf53781269fd072c1c718d097c3a57d578b6cd3b641', 'assets/destiny/models/weapon_reload_w100/the_recluse_magazine.json': '1e8b5044599909a46cb68adb22c3b516b42ae2cd83ee648de9155f9951094103'}
PINS.update({
    'assets/destiny/models/weapon/sniper_rifle/beloved.json': '9c404f594392862390288a35c0aa0aa1943e5e5b6cdb3b36e843b8bf45a70bee',
    'assets/destiny/models/weapon_reload_w47/beloved_body.json': '0a88c34581c197a975a33ee064429464b91d5bc5bed02b245844e560ca6e55dd',
    'assets/destiny/models/weapon_reload_w47/beloved_magazine.json': 'e6b6677011effb80c9e615371665efadb96f770e8a95b886c42df336f91529f9',
})

PINS.update({'assets/destiny/models/weapon/machine_gun/hammerhead.json': '7890eb2e60dc2a6547c7af7278a079b9e28575fd186683769c41f3c725c990bb', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_body.json': '35fac0b51a7d6ece2b0f88bbf1820f7418cbc248391063b280dd3c2eb52d79e6', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_magazine.json': 'e3558d5db3528e6637781d618ef80cd004d5faf937641497ef67423988b62d7e', 'assets/destiny/models/weapon_reload_w114_hammerhead/hammerhead_cover.json': 'b82174b32e72d7395d73d22960e6500398bfc6be6b87d7374909bad95193d57b', 'assets/destiny/models/weapon/pulse_rifle/blast_furnace.json': 'f3922a28cc58de8c7a7f965ba3464aeb5841d1a53bde72bf74d58e48aca39706', 'assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_body.json': '1c92741af670629976269083b2c054efd6d9d28087da61e19b6226c255ff665a', 'assets/destiny/models/weapon_reload_w114_blast_furnace/blast_furnace_magazine.json': '32e31c399e609adaea4319ca17208420d0b62e44b624cc2de8e1742d4baa5397', 'assets/destiny/models/weapon/hand_cannon/duke_mk_44.json': 'c933fdbc7abff648419552b326ce028dc9e0ddc389c53e7b1b515e13c90e790b', 'assets/destiny/models/weapon_reload_w64/duke_mk_44_body.json': 'bfa87423f0eeb90e83f514a3ff5d68ad645e99d0f9fce3c59af1f7fa944a7144', 'assets/destiny/models/weapon_reload_w64/duke_mk_44_cylinder.json': 'e108a66f8af0747f3a87774ad237f611142dff129e93e109219fd9f7a02f2d36'})

PINS.update({'assets/destiny/models/weapon/auto_rifle/gnawing_hunger.json': '42232ad07e5b2d133f22c9179139f9b304945f1453cf76de4d914c59067e4b4d', 'assets/destiny/models/weapon/pulse_rifle/chattering_bone.json': '1deb2f9752952ac28cb59dbe1b6a2ef528ccfae5b42b7aa0ff040c81e0b589a1', 'assets/destiny/models/weapon/shotgun/dust_rock_blues.json': '66bc71d5fea8102694cc1c080b017aa5db03ef82d436bbfeb7037bff77651696'})

PINS.update({'assets/destiny/models/weapon/auto_rifle/halfdan_d.json': 'a6c1fa0e4084403c66e8136179f320ace92bd4b7962f0bc59ae648df0830f378', 'assets/destiny/models/weapon/hand_cannon/austringer.json': '386c940d7e18bda739d7d7e77664c27db7e2e5d964fb79e0a6d32e8bc3ba0312', 'assets/destiny/models/weapon/submachine_gun/antiope_d.json': 'c3154796e5b5dc0605f6ba385b6d8b703e755b71498135ecf6b5a5470bd8469a'})

PINS.update({'assets/destiny/models/weapon/scout_rifle/patron_of_lost_causes.json': 'd1086431cad2a610031c46f4c6990c3ae9680b605a44990b3cd9adf428bfdae8', 'assets/destiny/models/weapon/fusion_rifle/erentil_fr4.json': '10649eb8b62d80ad7837f7bfa3595e7be1dc338db60bcd333a7c289a130642e2', 'assets/destiny/models/weapon/rocket_launcher/bad_omens.json': 'ef85cfffd28a597c5683ef9b6682d23ef151d46f3069c6c2ce18bfd9db97d40c', 'assets/destiny/models/weapon/sidearm/lonesome.json': '91c2a950f979dee2e22afe74f75206bf53a451ab725ebb837b025bd52b4c0872'})

PINS.update({'assets/destiny/models/weapon/machine_gun/fixed_odds.json': 'dd60ee6cb61a0911bdd984b0d61fae42c326a4e79306f25584a76038baea84d7', 'assets/destiny/models/weapon/rocket_launcher/code_duello.json': 'cb749df662d293747c44124ceb010554b4664a49d3d36bd9be9e3d16ddcae5ba', 'assets/destiny/models/weapon/scout_rifle/distant_relation.json': '126bd1a3aea23bbbb77ae010441e102a751a281defd4e59f6aa6f46ba2ae4801', 'assets/destiny/models/weapon/shotgun/first_in_last_out.json': 'ab1bbe5ef209d292324877ac38b79ba2cf8d55ceeaebff0133cb8149f452ae47'})

PINS.update({'assets/destiny/models/weapon/auto_rifle/steelfeather_repeater.json': '81e3b4a3330b92f4c31438e2c3f3700934da59e473b19105f4f327e7235a2af0', 'assets/destiny/models/weapon/pulse_rifle/bygones.json': 'b31399847f5affb868891e360ad595a0dce6ef839f31101464aa0784a87c953c', 'assets/destiny/models/weapon/sniper_rifle/bite_of_the_fox.json': '00dce3691476617a9a0e9d98e7c18cc486a0c80f637a8ec6ad101cc76a261154', 'assets/destiny/models/weapon/sword/falling_guillotine.json': '324e1e54a8b6b70ab91be37286a4c172a42abdb9fe8716b9d6a76e721ba931b6'})

PINS.update({'assets/destiny/models/weapon/hand_cannon/seventh_seraph_officer_revolver.json': '54769897a32bc162e895ae2dac586527494cd898e0a744aef3832d196d5004a5', 'assets/destiny/models/weapon/shotgun/ikelos_sg_v1_0_1.json': '529fd1bf0cdda904bf8a98782f0eb3a6a4e477b2d5c8e54758c7bec3d8cf81bd', 'assets/destiny/models/weapon/machine_gun/retrofit_escapade.json': '5487264f6226b82d50fdab909ebfdc32376ccb88a66c7609bc4e736aceaf7490', 'assets/destiny/models/weapon/heavy_grenade_launcher/edge_transit.json': '36a302124a0c4ab1cc88b1caad77d07fb1a021e150d6118a9656ea3cee2509f9', 'assets/destiny/models/weapon/sword/crown_splitter.json': '50c519fa916a61e749ed7c72c29cf9fc4f173e93d8bbeaad98ad330dabfc3cdf'})

PINS.update({'assets/destiny/models/weapon/pulse_rifle/cold_denial.json': 'c32362ff284793572dffbe216fa9d4cc43ceec07baa93cfdb788125b1fb04ee6', 'assets/destiny/models/weapon/pulse_rifle/claws_of_the_wolf.json': '2fa34678453eeb3af2d0279d115a60458d7eadefe660c8edf9453d831a039e93', 'assets/destiny/models/weapon/scout_rifle/frontier_justice.json': '627c054e6dcd501c87a74e06597012f53874c2145a8f05be7e6cbaa7132e7418', 'assets/destiny/models/weapon/submachine_gun/bug_out_bag.json': '3af4ff02566ddbb869b485338dede5eb80d1c5f252b4b0e155de18d72b08e6fa', 'assets/destiny/models/weapon/sniper_rifle/apostate.json': 'b5a2400a8cbe5d281783dd5f4850ac6d3f5847aa84db16b029288ec9c0b63923'})

PINS.update({'assets/destiny/models/weapon/sword/abide_the_return.json': '8f6f9593d9a8dbd84022d4fe726152f799b71a55ae253e3f636e0bc5f46534c8', 'assets/destiny/models/weapon/sword/goldtusk.json': 'ca9d5e0f093983cf833417408fef8cb6a70a130fbb442938cb1b5a8d3be980f0', 'assets/destiny/models/weapon/sword/temptation_s_hook.json': 'f5c48f76395c7b969fbb6867d75fd3b0bf038e1f1d6a73992d91e94a01b92277', 'assets/destiny/models/weapon/sidearm/allied_demand.json': '00ed0806b2a65cf8591c4b1dce9017cb92383c0e54b2fbace794f999d9060fec'})

PINS.update({'assets/destiny/models/weapon/scout_rifle/aishas_embrace.json': 'e0a4ade39771807977d770da6f5ad7204be2a23112477556dbf47534d0b8642f', 'assets/destiny/models/weapon/scout_rifle/long_arm.json': 'd166bc28532cf9461c5cb2e568f532bbceba1d3d0d0d7e43afc82408f9390ed0', 'assets/destiny/models/weapon/submachine_gun/ikelos_smg_v1_0_1.json': 'd0b5f0be06846af78d9c207889e33226694343f896e1bd4028776754df28bec8', 'assets/destiny/models/weapon/sidearm/farewell.json': '020ec70acfbeca358e00418b8c7b666f7983b2627c65af41ced43cc52cced3bc'})

PINS.update({'assets/destiny/models/weapon/sidearm/dead_man_walking_xx7463.json': '703b70280d0cbe4b5bfe50547589aeaa4f2f69bb2cbdecf33b1f1d174af70c57', 'assets/destiny/models/weapon/sidearm/high_albedo.json': '8a8b8f38c8332ce63bf953c29de7c4e651a17c12549670bfb336ca9885ec412d', 'assets/destiny/models/weapon/sidearm/brass_attacks.json': '225ab67eb09f06d81f4c962736f3a726974f8a9653e24d5907c96043efab145a', 'assets/destiny/models/weapon/glaive/nezarec_s_whisper.json': '07253570fd45d964c3e4427ba11b2807cefc3887c8767c5a3001455ed5fa8a7d'})

PINS.update({'assets/destiny/models/weapon/fusion_rifle/null_composure.json': 'e5e5ead55de6a921d9bb452c9ea460c573f36150c625a526df7db10d04c5bc75', 'assets/destiny/models/weapon/fusion_rifle/hollow_words.json': 'eaf326afdc1711f6ae642c178398f39ef75038b83f705128e11963636a267fb5', 'assets/destiny/models/weapon/fusion_rifle/coriolis_force.json': '70c6f30447cbae2a42dd7c6a3553e352aa6c6d7b61bd900180e8e8e37eaa2eac', 'assets/destiny/models/weapon/fusion_rifle/dream_breaker.json': 'c76b3daea47cdc06ed707bc178884f78a669762f6fea35d3fc811422269ddf42'})

PINS.update({'assets/destiny/models/weapon/shotgun/parcel_of_stardust_fell_to_earth.json': '1ee28a19e2a902ef17fe820923a1920c0a700c7860aaf4142a4fa7a5512a529f', 'assets/destiny/models/weapon/shotgun/mindbender_s_ambition_adept.json': '3ee94558c88b7a1a072eb2adfb77f89e207834dca46a63d537cfebcd5ca13375', 'assets/destiny/models/weapon/bow/biting_winds.json': '6e3146acd14e4e5d04332eea1b0ad2e89d9c88abf65b85fc1a894f73f05b4c6e', 'assets/destiny/models/weapon/bow/whispering_slab.json': 'e4b262f49e49adb4266b100afb51a7f85e3a88daa1e55ec2a5421e9a7643510a', 'assets/destiny/models/weapon_bow_w50/biting_winds_body_hip.json': 'ce081b7a7b21f54d277631531478956bd5c9340ec985a7f25e685ab796898c35', 'assets/destiny/models/weapon_bow_w50/whispering_slab_body_hip.json': '3ca18cffe3366a567f9b9604f86c6e49e83bdfab485e12fa1f97bd52466ec742'})

EXTRA_FULL_ONLY = ('canis_major', 'dimensional_hypotrochoid', 'deafening_whisper', 'salvager_s_salvo', 'retraced_path', 'line_in_the_sand', 'stormchaser', 'bellowing_giant', 'pyroclastic_flow')
PINS.update({'assets/destiny/models/weapon/heavy_grenade_launcher/canis_major.json': '9ce553cae9c1142bbb3f1d0258a2b70397976d734a36d02e2b1fb8cd8c0bd4fe', 'assets/destiny/models/weapon/heavy_grenade_launcher/dimensional_hypotrochoid.json': 'c585b37bc0a630ee446b244225ed6ddc96b76e27ecf0483b2f267e817d3c1ff6', 'assets/destiny/models/weapon/grenade_launcher/deafening_whisper.json': '43eb5e6647bb878ee9c5722021a64f45ddc79573407d1d891306ee1cffa345e6', 'assets/destiny/models/weapon/grenade_launcher/salvager_s_salvo.json': 'd174d66d6ba08248c4b7866cda333e923c7b888e3a4964178d0b9e7226bb7e69'})

PINS.update({'assets/destiny/models/weapon/trace_rifle/retraced_path.json': '06207f9900a181f0bdf6f2d5be60583a0e47fce0e58cb95ddf688ee390a50cbf', 'assets/destiny/models/weapon/linear_fusion_rifle/line_in_the_sand.json': 'b77783d88d521fa77e58269f38c86a073fd7953c00b55425cb133750c3bcf09b', 'assets/destiny/models/weapon/linear_fusion_rifle/stormchaser.json': 'dae7be8060d539e03da89a2008862b2e5bd1a68bd7a4441bca1c57f4fb4bba25', 'assets/destiny/models/weapon/rocket_launcher/bellowing_giant.json': 'e7a12634a512901893865bc41d5e23218741d03c2b0e3b8455a567358fb37a8b', 'assets/destiny/models/weapon/rocket_launcher/pyroclastic_flow.json': '77e259d2246a7008be0d898977e506614b6fdf81824966d355c5598d3e59c59f'})

PINS.update({'assets/destiny/models/weapon_scope_w45/line_in_the_sand_geometry.json': '7c556a696e0467775c957523001e68fe2b284d2eac2e17f695a8d82207056ceb', 'assets/destiny/models/weapon_scope_w45/stormchaser_geometry.json': '7bcc3f90966b7d71b7ede299ad383f26476c8ed07e9412b4b3e1171eaea8a0bd'})

def generate():
    # Count one assembled weapon, not full + duplicate reload resources.
    for weapon in EXTRA_FULL_ONLY + ('ammit_ar2', 'the_recluse', 'beloved', 'hammerhead', 'blast_furnace', 'duke_mk_44', 'gnawing_hunger', 'chattering_bone', 'dust_rock_blues', 'halfdan_d', 'austringer', 'antiope_d', 'patron_of_lost_causes', 'erentil_fr4', 'bad_omens', 'lonesome', 'fixed_odds', 'code_duello', 'distant_relation', 'first_in_last_out', 'steelfeather_repeater', 'bygones', 'bite_of_the_fox', 'falling_guillotine', 'seventh_seraph_officer_revolver', 'ikelos_sg_v1_0_1', 'retrofit_escapade', 'edge_transit', 'crown_splitter', 'cold_denial', 'claws_of_the_wolf', 'frontier_justice', 'bug_out_bag', 'apostate', 'abide_the_return', 'goldtusk', 'temptation_s_hook', 'allied_demand', 'aishas_embrace', 'long_arm', 'ikelos_smg_v1_0_1', 'farewell', 'dead_man_walking_xx7463', 'high_albedo', 'brass_attacks', 'nezarec_s_whisper', 'null_composure', 'hollow_words', 'coriolis_force', 'dream_breaker', 'parcel_of_stardust_fell_to_earth', 'mindbender_s_ambition_adept', 'biting_winds', 'whispering_slab'):
        base = RES / 'assets/destiny/models/weapon_surface_w123'
        full = json.loads((base / f'{weapon}.json').read_bytes())['elements']
        parts = ('body', 'cylinder') if weapon == 'duke_mk_44' else ('body', 'magazine', 'cover') if weapon == 'hammerhead' else ('body', 'magazine')
        assembled = (full if weapon in EXTRA_FULL_ONLY or weapon in ('gnawing_hunger', 'chattering_bone', 'dust_rock_blues', 'halfdan_d', 'austringer', 'antiope_d', 'patron_of_lost_causes', 'erentil_fr4', 'bad_omens', 'lonesome', 'fixed_odds', 'code_duello', 'distant_relation', 'first_in_last_out', 'steelfeather_repeater', 'bygones', 'bite_of_the_fox', 'falling_guillotine', 'seventh_seraph_officer_revolver', 'ikelos_sg_v1_0_1', 'retrofit_escapade', 'edge_transit', 'crown_splitter', 'cold_denial', 'claws_of_the_wolf', 'frontier_justice', 'bug_out_bag', 'apostate', 'abide_the_return', 'goldtusk', 'temptation_s_hook', 'allied_demand', 'aishas_embrace', 'long_arm', 'ikelos_smg_v1_0_1', 'farewell', 'dead_man_walking_xx7463', 'high_albedo', 'brass_attacks', 'nezarec_s_whisper', 'null_composure', 'hollow_words', 'coriolis_force', 'dream_breaker', 'parcel_of_stardust_fell_to_earth', 'mindbender_s_ambition_adept', 'biting_winds', 'whispering_slab') else
                     sum((json.loads((base / f'{weapon}_{part}.json').read_bytes())['elements'] for part in parts), []))
        if full != assembled or not 0 < len(full) <= MAX_ELEMENTS:
            raise ValueError(f'{weapon}: assembled cube+triangle elements {len(full)}; limit {MAX_ELEMENTS}')
    # W150: the LFR scope path historically cloned rigid W30 geometry. Keep its
    # overlay/wrapper transforms while substituting the same accepted new assembly.
    targets = []
    for path, expected in PINS.items():
        before = (RES / path).read_bytes()
        if hashlib.sha256(before).hexdigest() != expected:
            raise ValueError('Historical input changed: ' + path)
        replacement = 'assets/destiny/models/weapon_surface_w123/' + path.rsplit('/', 1)[1]
        after = (RES / replacement).read_bytes()
        old, new = json.loads(before), json.loads(after)
        if old.get('display') != new.get('display'):
            raise ValueError('Accepted display pose changed: ' + path)
        if not new.get('elements'):
            raise ValueError('Missing model geometry: ' + replacement)
        targets.append(dict(path=path, sourceSha256=expected, replacement=replacement,
                            replacementSha256=hashlib.sha256(after).hexdigest()))
    value = dict(schema=1, stage='W123', targets=targets,
                 maxAssembledElements=MAX_ELEMENTS,
                 policy='Cubes and triangle/contour elements combined <=1000 per weapon, not a target count. W126-W150 semantic sixty-three-weapon art, preserving existing dynamic bow string/arrow and moving magazine/cover/cylinder and generic reload paths; original item graphs, display poses, timing, sounds and ammo unchanged.')
    return (json.dumps(value, indent=2, ensure_ascii=False) + '\n').encode()

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    data = generate()
    output = RES / 'weapon_surface_w123/manifest.json'
    if args.verify:
        if not output.is_file() or output.read_bytes() != data:
            raise SystemExit('W123 manifest differs')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(data)
    print(json.dumps(dict(targets=len(PINS), verified=args.verify)))
