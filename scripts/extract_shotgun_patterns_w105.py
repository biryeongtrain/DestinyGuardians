#!/usr/bin/env python3
"""W105 shotgun historical-source extraction. Offline; Python standard library only.

--verify reads and compares all output bytes without writing. --self-test runs
bounded in-memory source and output tamper fixtures, bypassing SHA pins only
inside those fixtures to exercise semantic validation independently of checksums.
No network, builds, Java, tests, registry, runtime or assets are touched.
"""
import sys
sys.dont_write_bytecode = True
import argparse
import copy
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = 'scripts/extract_shotgun_patterns_w105.py'
TARGET = 'src/main/resources/destiny/weapons/w105-shotgun-patterns.json'
REF = 'art/weapons/w105/references/'
VERSION = '245114.26.10.13.2000-1-bnet.66137'
SUFFIX = 'e677f6ea-2a1e-48d4-a8c8-700a39a62585.json'
INTRINSIC_CATEGORY = 3956125808
ROSTER = [
 ('mindbender_s_ambition_adept', 912150785, 'aggressive', 3983457027, 96,
  "Mindbender's Ambition (Adept)", 'Aggressive Frame',
  'Hard-hitting, high recoil. Increases rate of fire after final blows.', 'fixed_evenly_distributed_cone'),
 ('dust_rock_blues', 636912560, 'precision', 1636108362, 17,
  'Dust Rock Blues', 'Precision Frame',
  "This weapon's recoil pattern is more predictably vertical.", 'vertical_oval'),
 ('first_in_last_out', 3616586446, 'pinpoint_slug', 918679156, 4,
  'First In, Last Out', 'Pinpoint Slug Frame',
  "Fires a single-slug round. This weapon's recoil pattern is more predictably vertical.", 'single_slug'),
 ('parcel_of_stardust_fell_to_earth', 2217366863, 'lightweight', 1458010786, 47,
  'Parcel of Stardust', 'Lightweight Frame',
  'Superb handling. Move faster with this weapon equipped.', 'diamond'),
 ('ikelos_sg_v1_0_1', 1887808042, 'rapid_fire', 996573084, 48,
  'IKELOS_SG_v1.0.1', 'Rapid-Fire Frame',
  'Fires full auto with deeper ammo reserves. Faster reload when weapon is empty.', 'square'),
]
PINS = {'inventory': {'path': 'run/private-sources/w105/official/inventory.json',
               'sha256': 'b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c',
               'originalReadPath': '/tmp/destiny-weapons-w30/bungie-items.json'},
 'plugSets': {'path': 'run/private-sources/w105/official/plugSets.json',
              'sha256': '8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959',
              'originalReadPath': '/tmp/destiny-weapons-w60/bungie-plugsets.json'},
 'manifest': {'path': 'run/private-sources/w105/official/manifest.json',
              'sha256': 'bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce',
              'originalReadPath': '/tmp/destiny-weapons-w60/manifest.json'},
 'selected': {'path': 'run/private-sources/w105/official/selected.json',
              'sha256': '5d27e02c073de0b348ba15312643cc7029a044ed5617a801dbfed2d86cd8f9a1',
              'originalReadPath': 'art/weapons/w40/definitions.json'},
 'catalog': {'path': 'run/private-sources/w105/official/catalog.json',
             'sha256': '2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a',
             'originalReadPath': 'src/main/resources/destiny/weapons/w30.json'},
 'w40Provenance': {'path': 'run/private-sources/w105/official/w40Provenance.json',
                   'sha256': '281bba3a34ec308b9f7b64d09c7d2b012925bcee1a4b02fac12a99ca9d730d42',
                   'originalReadPath': 'art/weapons/w40/provenance.json'},
 'research1': {'path': 'run/private-sources/w105/research1.json',
               'sha256': 'c1c593e35dfb9b67302b2f6e0a1f4a00d22ce3afc3ec61c4651fdecf8708a6a2'},
 'research2': {'path': 'run/private-sources/w105/research2.json',
               'sha256': 'dd8c408a2f0555185dbecca65c810ae58bb6cfa0a1efb7fc478a7fb4b80605df'},
 'research3': {'path': 'run/private-sources/w105/research3.json',
               'sha256': '0fc21035a48155341f19d290d570f53708b08d01eacbb8ff0e98db3a7c1cba6e'},
 'research4': {'path': 'run/private-sources/w105/research4.json',
               'sha256': 'fa7a921495b439fb19525f4ca55ff680d1bc048ac2809aa4cc0d97df04461d06'},
 'research5': {'path': 'run/private-sources/w105/research5.json',
               'sha256': '08b149635f6c9f306c639d8b3daa7e00c81838a8934b07fb13f16b187686b599'},
 'research6': {'path': 'run/private-sources/w105/research6.json',
               'sha256': '151b207e993a151230712bd4ade2aef718a64e9dfe84654cf550875df9288a42'},
 'research7': {'path': 'run/private-sources/w105/research7.json',
               'sha256': '02b413cd3cc7254199cece8aec00dfae637680a90aa305484951aca336b52cdc'},
 'aggressiveImage': {'path': 'run/private-sources/w105/aggressive.png',
                     'sha256': 'af97f626d2652043263750561ce300b133f41814921c9d9b2ce7c835a71d79fe'},
 'precisionImage': {'path': 'run/private-sources/w105/precision.png',
                    'sha256': '27882f386298fa0e6624309550e304bb9b0ae0894c2e0d6102207da34cb7c157'},
 'lightweightImage': {'path': 'run/private-sources/w105/lightweight.png',
                      'sha256': 'fc15943e99e082e0ed6c4c14986359fdb2d0f5c8597ce2d689d518f99304e60a'},
 'rapid_fireImage': {'path': 'run/private-sources/w105/rapid_fire.png',
                     'sha256': 'e31a992ecadba08dbe2407bc6a18f1038cf0844b897a4bfc5dc93058f62f8f47'},
 'httpRetrieval': {'path': 'run/private-sources/w105/http-retrieval.json',
                   'sha256': '47c77983c05e13bcd09c1b8c023196ad452f493a7c1d7cc29f0d049723e38aa7'},
 'observations': {'path': 'run/private-sources/w105/visual-observations.json',
                  'sha256': '0efe730280b4e22942d9426e39127213759d7673299267ee6353d46426474d25'}}
URLS = {
 's15_count':'https://www.bungie.net/7/en/News/article/50572',
 's19_shapes':'https://www.bungie.net/7/en/News/article/51999',
 's20_reticles':'https://www.bungie.net/7/en/News/article/s20-weapon-tuning-preview',
 's21_lightweight':'https://www.bungie.net/7/en/News/Article/weapon_tuning_s21_mid_season',
 'ads2020':'https://www.bungie.net/7/en/News/article/48743',
 'patch2026':'https://static01.bungie.net/7/en/News/Article/destiny_update_9_7_0',
 'secondary2020':'https://www.reddit.com/r/CruciblePlaybook/comments/fi4l1y',
 'secondary2023':'https://www.reddit.com/r/CrucibleGuidebook/comments/18i77mt',
}
UNKNOWN = {
 'currentPelletCount':None, 'currentPatternUnchangedSinceS19':None,
 'genericAdsShrinksPelletSpread':None, 'genericAdsSpreadMultiplier':None,
 'pelletCoordinates':None, 'baseSpreadAngleDegrees':None, 'patternAspectRatios':None,
 'sourceDamagePerPellet':None, 'sourceDamageScalars':None,
}
LOCAL = {
 'ownedBy':'master_integration', 'historicalCountAdoptedForExactFourPelletWeapons':True,
 'preserveExistingTotalHpBudget':True,
 'damageBudgetMethod':'old_count_divided_by_new_count; local Minecraft tuning only',
 'retainExistingGenericAdsFactor':True,
 'adsFactorDescription':'existing 1 - .35 * ADS; unconfirmed local tuning, not source-derived',
 'assumeFullChokeEquipped':False,
 'geometry':'master-authored historical image-informed estimated impact centers; not exact engine coordinates; physical spread remains local tuning',
 'reticleOutlines':'four master-authored historical image-informed outlines; visual estimates, not exact pixels or current engine geometry',
}
LIMITATIONS = [
 'Identity is proven for the pinned October 2026 official manifest and exact selected hashes, not every same-name weapon edition.',
 'Twelve pellets is primary historical evidence: explicit August 2021 Bungie text and visual count in all four December 2022 S19 illustrations. No inspected source independently reconfirms live 2026 count.',
 'The 2021 randomized wedge/ring rule is superseded by S19 fixed patterns; it is not adopted as geometry.',
 'S19 is a dated preview. July 2023 explicitly retunes lightweight outer horizontal spread; unchanged current geometry is not established.',
 'Generic ADS spread reduction and its magnitude remain unresolved even for S19. Range/falloff, aim assist, zoom and reticle size are distinct from physical pellet spread.',
 'Community ADS assertions conflict and are secondary reports only. Full Choke and Shot Package are conditional effects, not a universal ADS rule or a default-equipped barrel claim.',
 'No original coordinates, spread angles, aspect ratios, damage values or generic ADS scalars are authored. Unknown source values remain null.',
 'Original official PNGs are private research inputs. Human inspection establishes the recorded visible arrangement; offline validation checks bytes and observation consistency, not fresh automated image understanding.',
 'Illustration-relative reconstruction can preserve historical marker arrangement but cannot establish physical spread angles or unchanged live tuning.',
 'Master adopts historical twelve only for the exact four non-slug rows, retains its existing local ADS factor and preserves local total HP budget; none of these local integration policies is an original Destiny damage claim.',
 'No Java/tests/shared docs/registry/build/runtime/CU or visual assets are changed by this extractor; no child work is claimed.',
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def encoded(value):
    return (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False)+'\n').encode()


def load_sources(root):
    data, pins = {}, {}
    for key, pin in PINS.items():
        relative = Path(pin['path'])
        require(not relative.is_absolute() and '..' not in relative.parts, 'Nonportable source path')
        raw = (root/relative).read_bytes()
        require(digest(raw) == pin['sha256'], 'Source SHA256 mismatch: '+key)
        pins[key] = {**pin, 'bytes':len(raw)}
        data[key] = raw if key.endswith('Image') else json.loads(raw)
    return data, pins


def evidence(data, capture, url, fragments):
    # Match title URL, never an unrelated link or a similarly named mirrored page.
    content = '\n'.join(b.get('text','') for b in data[capture]['response']['content'])
    blocks = content.replace('\xa0',' ').split('--------------------------------------------------------------------------------')
    matches = [b for b in blocks if '('+url+')' in b.lstrip().split('\n',1)[0]
               and all(fragment in b for fragment in fragments)]
    require(bool(matches), 'Missing URL-bound evidence: '+url)
    return matches[0]


def validate_definition(item, h, name, kind, description, category):
    require(item['hash']==h and item['itemType']==19
            and item['itemTypeDisplayName']==kind
            and item['displayProperties']['name']==name
            and item['displayProperties']['description']==description
            and not item['redacted'] and not item['blacklisted']
            and not item['plug']['isDummyPlug']
            and item['plug']['plugCategoryHash']==category,
            'Exact definition drift: '+str(h))


def validate(data):
    cat, selected, inv, pools = data['catalog'],data['selected'],data['inventory'],data['plugSets']
    require(len(cat)==len(selected)==63 and len({w['id'] for w in cat})==63
            and len({w['id'] for w in selected})==63
            and len({w['bungieHash'] for w in selected})==63, 'Expected 63 unique selections')
    require({w['id'] for w in cat}=={w['id'] for w in selected}, 'Catalog/selection drift')
    manifest=data['manifest'];components=manifest['Response']['jsonWorldComponentContentPaths']['en']
    path='/common/destiny2_content/json/en/DestinyInventoryItemDefinition-'+SUFFIX
    require(manifest['ErrorCode']==1 and manifest['Response']['version']==VERSION
            and components['DestinyInventoryItemDefinition']==path
            and components['DestinyPlugSetDefinition']==path.replace('InventoryItem','PlugSet'),
            'Matching official manifest components drift')
    prov=data['w40Provenance']
    require(prov['manifest']=={'version':VERSION,'path':path}
            and prov['cachedInventorySha256']==PINS['inventory']['sha256']
            and prov['source']=='https://www.bungie.net'+path, 'Selected provenance drift')
    cat_by_id={w['id']:w for w in cat};selected_by_id={w['id']:w for w in selected}
    official_shotguns=[];scans=[]
    for w in selected:
        item=inv[str(w['bungieHash'])];catalog=cat_by_id[w['id']]
        require(item['hash']==w['bungieHash'] and item['itemType']==3
                and not item['redacted'] and not item['blacklisted']
                and {k:v['value'] for k,v in item['stats']['stats'].items()}==w['stats']
                and item['equippingBlock']['ammoType']=={'PRIMARY':1,'SPECIAL':2,'HEAVY':3}[w['ammo']],
                'Selected official identity/stat/ammo drift: '+w['id'])
        is_shotgun=item['itemSubType']==7 and item['itemTypeDisplayName']=='Shotgun'
        require((catalog['family']=='shotgun')==is_shotgun, 'Official/catalog shotgun classification mismatch')
        scans.append({'id':w['id'],'hash':item['hash'],'family':catalog['family'],
                      'officialItemType':item['itemTypeDisplayName'],'officialItemSubType':item['itemSubType'],
                      'selectedShotgun':is_shotgun})
        if is_shotgun:official_shotguns.append(w['id'])
    require(official_shotguns==[r[0] for r in ROSTER], 'Exact five-shotgun roster/order drift')
    proof=[]
    for id,h,frame,ih,ph,name,iname,description,pattern in ROSTER:
        w=selected_by_id[id];c=cat_by_id[id];item=inv[str(h)]
        require(w['bungieHash']==h and c['frame']==frame and c['family']=='shotgun'
                and item['displayProperties']['name']==name and not w['exotic']
                and c['source_frame_label']==iname, 'Exact selected frame/name/hash drift: '+id)
        if id=='parcel_of_stardust_fell_to_earth':
            require(c['name']=='Parcel of Stardust (Fell to Earth)', 'Parcel local alias drift')
        else:require(c['name']==name, 'Catalog official name drift')
        sockets=item['sockets'];categories=[x for x in sockets['socketCategories']
                                           if x['socketCategoryHash']==INTRINSIC_CATEGORY]
        require(len(categories)==1 and categories[0]['socketIndexes']==[0], 'Intrinsic socket category drift')
        socket=sockets['socketEntries'][0]
        require(socket['socketTypeHash']==INTRINSIC_CATEGORY and socket['singleInitialItemHash']==ih
                and socket.get('reusablePlugSetHash')==ph and not socket.get('randomizedPlugSetHash')
                and socket['reusablePlugItems']==[], 'Initial intrinsic socket drift: '+id)
        intrinsic=inv[str(ih)]
        validate_definition(intrinsic,ih,iname,'Intrinsic',description,1744546145)
        require(intrinsic['plug']['plugCategoryIdentifier']=='intrinsics', 'Intrinsic category identifier drift')
        pool=pools[str(ph)]
        require(pool['hash']==ph and pool['isFakePlugSet'] is True and not pool['redacted']
                and not pool['blacklisted'] and len(pool['reusablePlugItems'])==1
                and pool['reusablePlugItems'][0]['plugItemHash']==ih
                and pool['reusablePlugItems'][0]['currentlyCanRoll'] is True,
                'Intrinsic reusable pool corroboration drift')
        proof.append({'id':id,'hash':h,'frame':frame,'officialName':name,'catalogName':c['name'],
                      'socket':0,'socketCategoryHash':INTRINSIC_CATEGORY,'socketEntry':socket,
                      'intrinsicHash':ih,'intrinsicType':'Intrinsic','intrinsicName':iname,
                      'intrinsicDescription':description,'reusablePool':pool,
                      'proofMode':'initial_intrinsic; fake reusable pool is corroboration, not a randomized roll'})
    for h,kind in [(1047830412,'Barrel'),(3311319252,'Enhanced Barrel')]:
        validate_definition(inv[str(h)],h,'Full Choke',kind,
            'Tightened barrel. Reduces projectile spread when aiming down sights at the cost of precision damage.',2833605196)
    validate_definition(inv['3054949324'],3054949324,'Shot Package','Intrinsic',
        'Aggressive frame Shotgun modified to have decreased pellet spread while aiming down sights.',1744546145)
    queries=[q['q'] for n in range(1,8) for q in data['research'+str(n)]['request'].get('system2_search_query',[])]
    require(len(queries)==len(set(queries))==8,'Focused web query bound drift')
    count_block=evidence(data,'research5',URLS['s15_count'],['A Shotgun shot contains 12 pellets'])
    count_match=re.search(r'A Shotgun shot contains (\d+) pellets',count_block)
    require(count_match and int(count_match.group(1))==12,'Primary historical count drift')
    evidence(data,'research1',URLS['s19_shapes'],[
        'Aggressive: fixed, evenly distributed cone','Precision (includes Duality hip-fire): vertical oval',
        'Lightweight: diamond','Rapid-Fire: square'])
    evidence(data,'research3',URLS['s20_reticles'],['Shotgun reticles now change in size proportional to spread angle.'])
    evidence(data,'research3',URLS['s21_lightweight'],['Reduced the spread angle of the outer horizontal pellets by 15%.'])
    evidence(data,'research4',URLS['ads2020'],['Shotguns','Aiming down sights no longer adjusts effective range for this weapon archetype.'])
    evidence(data,'research4',URLS['patch2026'],['Shot Package intrinsic','Decreased pellet spread by 2.5% in ADS'])
    evidence(data,'research5',URLS['patch2026'],['Jun 9, 2026'])
    evidence(data,'research6',URLS['secondary2020'],['you still benefit from tightening the cone'])
    evidence(data,'research6',URLS['secondary2023'],[
        'It used to, but that got removed a long time ago.','It does slightly tighten spread still.'])
    obs=data['observations']
    require(obs['automatedPelletDetection'] is False and obs['geometryCoordinatesExtracted'] is False
            and obs['currentSandboxClaim'] is False,'Visual observation claim promoted')
    require([o['frame'] for o in obs['frames']]==['aggressive','precision','lightweight','rapid_fire']
            and all(o['visiblePelletMarks']==12 for o in obs['frames']), 'S19 visual count drift')
    for o in obs['frames']:
        image_key=o['imageKey'];raw=data[image_key];retrieval=data['httpRetrieval'][o['frame']]
        require(image_key==o['frame']+'Image' and raw[:8]==b'\x89PNG\r\n\x1a\n'
                and int.from_bytes(raw[16:20],'big')==250 and int.from_bytes(raw[20:24],'big')==250
                and retrieval['sha256']==digest(raw) and retrieval['url']==o['imageUrl']
                and retrieval['status']=='IMAGE_RETRIEVED' and retrieval['adoptedAsEvidence'] is True,
                'Official S19 image pin/link drift')
        evidence(data,'research5',o['imageUrl'],['<<ImageDisplayed>>'])
    for key in ['s19','s15','s20','s21','ads2020','patch2026']:
        retrieval=data['httpRetrieval'][key]
        require(retrieval['status']=='HTTP_200_SHELL_ONLY'
                and retrieval['articleTextRetrieved'] is False and retrieval['adoptedAsEvidence'] is False,
                'JavaScript shell falsely promoted to article evidence')
    return proof,scans,int(count_match.group(1)),queries


def profile(count):
    rows=[]
    for id,h,frame,ih,ph,name,iname,description,pattern in ROSTER:
        slug=frame=='pinpoint_slug'
        rows.append({'id':id,'hash':h,'frame':frame,'intrinsicHash':ih,'socket':0,'pattern':pattern,
            'pelletCount':None if slug else count,
            'pelletCountScope':'not_applicable_single_slug' if slug else 'historical_2021_text_and_2022_S19_illustrations',
            'singleSlugRound':slug,'slugProjectileCount':1 if slug else None,
            'evidenceIds':['manifest_intrinsics'] if slug else ['s19_shapes','s15_count','s19_illustrations']})
    return {'stage':'W105','schemaVersion':1,'manifestVersion':VERSION,
            'patternScope':'historical_S19_2022_12_01_qualitative_only',
            'weapons':rows,'sourceRules':copy.deepcopy(UNKNOWN),'localPolicy':copy.deepcopy(LOCAL),
            'evidencePath':REF+'evidence.json'}


def validate_profile(value):
    # Exact schema deliberately rejects extra geometry, broader family matching,
    # null-to-default coercion, temporal promotion, or implicit Full Choke.
    require(value==profile(12), 'Runtime contract/schema/temporal/unknown/local-policy drift')
    require(all(type(w['hash']) is int and type(w['intrinsicHash']) is int
                and type(w['socket']) is int
                and (w['pelletCount'] is None or type(w['pelletCount']) is int)
                and type(w['singleSlugRound']) is bool for w in value['weapons']),
                'Runtime contract types drift')


def extract(data,pins,script_sha):
    proofs,scans,count,queries=validate(data)
    resource=profile(count);validate_profile(resource)
    records=[
      {'id':'manifest_intrinsics','sourceClass':'primary_official_manifest','revision':VERSION,
       'summary':'Exact five selected item hashes and initial intrinsic sockets distinguish four pellet frames from the explicit single slug.'},
      {'id':'s15_count','sourceClass':'primary_official_article','url':URLS['s15_count'],'published':'2021-08-19',
       'historicalPelletCount':count,'currentPelletCountConfirmed':False,
       'summary':'Bungie explicitly states twelve. The contemporaneous randomized wedge/ring distribution is superseded; only the count is used.'},
      {'id':'s19_shapes','sourceClass':'primary_official_preview','url':URLS['s19_shapes'],'published':'2022-12-01',
       'revision':'S19 preview','summary':'Qualitative fixed shapes differ by pellet frame. Slug has a distinct precision reticle, not a pellet pattern.',
       'currentUnchangedGeometryConfirmed':False},
      {'id':'s19_illustrations','sourceClass':'primary_official_illustrations_with_human_observation',
       'url':URLS['s19_shapes'],'published':'2022-12-01','observations':data['observations'],
       'images':[{'frame':o['frame'],'url':o['imageUrl'],'cachePath':PINS[o['imageKey']]['path'],
                  'sha256':PINS[o['imageKey']]['sha256']} for o in data['observations']['frames']],
       'currentPelletCountConfirmed':False},
      {'id':'s20_reticles','sourceClass':'primary_official_preview','url':URLS['s20_reticles'],'published':'2023-02-01',
       'summary':'Reticle size begins responding to spread angle. This is a HUD change, not a generic ADS multiplier.'},
      {'id':'s21_lightweight','sourceClass':'primary_official_preview','url':URLS['s21_lightweight'],'published':'2023-07-06',
       'summary':'Later reduction to lightweight outer horizontal spread prevents treating the S19 image as an unchanged current numeric layout.',
       'adoptedAsGeometryScalar':False},
      {'id':'ads2020','sourceClass':'primary_official_preview','url':URLS['ads2020'],'published':'2020-02-20',
       'summary':'ADS effective-range wording and subtype cone/range-stat separation do not resolve generic ADS spread shrink or its magnitude.'},
      {'id':'patch2026','sourceClass':'primary_official_patch','url':URLS['patch2026'],'published':'2026-06-09',
       'revision':'Destiny 2 Update 9.7.0',
       'summary':'Full Choke and Shot Package receive conditional spread changes. The Shot Package ADS change does not apply merely by being aggressive.',
       'shotPackageIntrinsicHash':3054949324,'selectedInitialShotPackageCount':0,
       'adoptedAsGenericAdsScalar':False,'currentPelletCountConfirmed':False},
      {'id':'full_choke','sourceClass':'primary_official_manifest','revision':VERSION,
       'definitions':[{'hash':h,'type':data['inventory'][str(h)]['itemTypeDisplayName'],
                       'description':data['inventory'][str(h)]['displayProperties']['description']}
                      for h in [1047830412,3311319252]],
       'summary':'An equipped conditional barrel effect; selected/equipped eligibility is outside this source profile.',
       'assumeEquipped':False},
      {'id':'secondary_ads_2020','sourceClass':'secondary_community_testing_report','url':URLS['secondary2020'],
       'published':None,'revisionContext':'2020 patch report before S19',
       'dateBasis':'Exact post timestamp not verified; revision context follows the report and its linked February 2020 Bungie article.',
       'summary':'Author reports testing and ADS cone tightening after the 2020 patch. No original datasets or calibration were inspected.',
       'adoptedAsExactRule':False},
      {'id':'secondary_ads_2023','sourceClass':'secondary_community_discussion','url':URLS['secondary2023'],
       'published':None,'revisionContext':'Later discussion, indexed as about three years old at capture',
       'dateBasis':'Exact post timestamp not verified; web capture supplies approximate relative ages only.',
       'summary':'Participants disagree about whether generic ADS still tightens spread; no resolved measurement is adopted.',
       'adoptedAsExactRule':False},
    ]
    evidence_file={'stage':'W105','records':records,'unknownSourceRules':copy.deepcopy(UNKNOWN),
                   'contradictionsAndLimitations':LIMITATIONS}
    provenance={'stage':'W105','generator':SCRIPT,'generatorSha256':script_sha,
        'manifestVersion':VERSION,'sourcePins':pins,'queryStrings':queries,'targetedQueries':len(queries),
        'queryBound':8,'laterWebCalls':'Only opens/finds/clicks of discovered sources; no additional queries.',
        'sourceAcquisition':'Official manifest components copied unchanged from W104 pins to W105 private cache. Text evidence is URL-bound metadata-discovered web-tool capture. Direct article HTTP shells are excluded.',
        'offline':True,'standardLibraryOnly':True,'byteFormat':'UTF-8 JSON indent=2 trailing newline; source selection order',
        'childWorkClaimed':False,'reproduce':'rtk proxy python3 '+SCRIPT+' --verify --self-test',
        'reproduceElsewhere':'rtk proxy python3 '+SCRIPT+' --source-root <source-root> --output-root <disjoint-output-root>',
        'requiredPrivateInputs':'All sourcePins paths under the source root. No /tmp cache or live network is required.',
        'limitations':LIMITATIONS}
    return {TARGET:resource,REF+'evidence.json':evidence_file,
            REF+'roster-proof.json':{'stage':'W105','selectedCount':63,'shotgunCount':5,
                'pelletWeaponCount':4,'slugWeaponCount':1,'allSelectedClassificationScan':scans,'shotguns':proofs},
            REF+'provenance.json':provenance}


def negative_fixtures(data):
    cases=[]
    def check(name,mutate,output=False):
        value=profile(12) if output else dict(data)
        mutate(value)
        try:
            validate_profile(value) if output else validate(value)
        except (ValueError,KeyError,TypeError,IndexError) as error:
            cases.append({'fixture':name,'status':'REJECTED','reason':str(error)})
        else:raise ValueError('Mutation wrongly accepted: '+name)
    def item_change(d,h,change):
        d['inventory']=dict(d['inventory']);i=copy.deepcopy(d['inventory'][str(h)])
        change(i);d['inventory'][str(h)]=i
    check('slug-substituted-same-name-precision',lambda d:item_change(d,3616586446,
        lambda i:i['sockets']['socketEntries'][0].update(singleInitialItemHash=1636108362)))
    check('intrinsic-outside-intrinsic-category',lambda d:item_change(d,912150785,
        lambda i:i['sockets']['socketCategories'][0].update(socketCategoryHash=4241085061)))
    check('intrinsic-definition-is-trait',lambda d:item_change(d,3983457027,
        lambda i:i.update(itemTypeDisplayName='Trait')))
    check('wrong-official-edition-same-name',lambda d:item_change(d,912150785,
        lambda i:i.update(hash=912150786)))
    def catalog_change(d,id,change):
        d['catalog']=copy.deepcopy(d['catalog']);change(next(i for i in d['catalog'] if i['id']==id))
    check('wrong-frame-on-exact-shotgun',lambda d:catalog_change(d,'dust_rock_blues',lambda i:i.update(frame='pinpoint_slug')))
    check('family-classifier-broadens-roster',lambda d:catalog_change(d,'bad_omens',lambda i:i.update(family='shotgun')))
    def capture_change(d,key,old,new):
        d[key]=copy.deepcopy(d[key])
        for block in d[key]['response']['content']:
            if 'text' in block:block['text']=block['text'].replace(old,new)
    check('historical-count-eight',lambda d:capture_change(d,'research5','contains 12 pellets','contains 8 pellets'))
    check('mirror-url-masquerades-as-primary',lambda d:capture_change(d,'research1',URLS['s19_shapes'],'https://example.org/copied-twab'))
    def ninth(d):
        d['research7']=copy.deepcopy(d['research7']);d['research7']['request']['system2_search_query']=[{'q':'forbidden ninth query'}]
    check('ninth-search-query',ninth)
    def observation(d):
        d['observations']=copy.deepcopy(d['observations']);d['observations']['frames'][0]['visiblePelletMarks']=8
    check('illustration-count-tamper',observation)
    check('current-count-silently-promoted',lambda p:p['sourceRules'].update(currentPelletCount=12),True)
    check('unknown-ads-coerced-to-local-factor',lambda p:p['sourceRules'].update(genericAdsSpreadMultiplier=0.65),True)
    check('invented-coordinate-array',lambda p:p['sourceRules'].update(pelletCoordinates=[[0,0]]),True)
    check('slug-incorrectly-given-twelve-pellets',lambda p:p['weapons'][2].update(pelletCount=12),True)
    check('full-choke-assumed-equipped',lambda p:p['localPolicy'].update(assumeFullChokeEquipped=True),True)
    return cases


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--verify',action='store_true')
    parser.add_argument('--self-test',action='store_true')
    parser.add_argument('--source-root',type=Path,default=ROOT)
    parser.add_argument('--output-root',type=Path)
    args=parser.parse_args()
    try:
        require(not(args.verify and args.output_root),'--verify cannot write to --output-root')
        root=args.source_root.resolve();output=(args.output_root or root).resolve()
        data,pins=load_sources(root)
        outputs=extract(data,pins,digest(Path(__file__).read_bytes()))
        cases=negative_fixtures(data) if args.self_test else []
        result={}
        for relative,value in outputs.items():
            raw=encoded(value);p=output/relative
            if args.verify:require(p.read_bytes()==raw,'Generated output differs: '+relative)
            else:p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(raw)
            result[relative]={'sha256':digest(raw),'bytes':len(raw)}
        print(json.dumps({'stage':'W105','status':'VERIFY_PASS' if args.verify else 'GENERATED',
                          'selected':63,'shotguns':5,'historicalPelletWeapons':4,'slugWeapons':1,
                          'targetedQueries':8,'outputs':result,'negativeFixtures':cases},indent=2))
    except (OSError,ValueError,KeyError,TypeError,IndexError) as error:
        print('W105 extraction failed: '+str(error),file=sys.stderr);return 1
    return 0


if __name__=='__main__':
    raise SystemExit(main())
