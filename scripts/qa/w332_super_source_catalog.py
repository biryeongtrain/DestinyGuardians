#!/usr/bin/env python3
"""Read-only W332 super/source catalog; writes only the two owned review docs."""
import hashlib
import json
import math
import re
from pathlib import Path

WORKER = Path(__file__).resolve().parents[2]
MAIN = Path('/Users/qf/IdeaProjects/DestinyGuardians')
LIGHT = Path('/Users/qf/Downloads/Destiny-Light-Abilities-2026-10-28/Destiny-Light-Abilities-2026-10-28')
OUT = WORKER/'docs/qa/2026-11-07/w332-super-review'
ANIM = MAIN/'src/main/resources/destiny/animation'


def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_text())


SPECS = [
    ('hunter/arc_staff','ARC','아크 지팡이','hunter_arc_staff','h15_super_arc','HunterSuper.java',400),
    ('hunter/golden_gun','SOLAR','황금 총',None,'h15_super_solar','HunterSuper.java',200),
    ('hunter/shadowshot','VOID','그림자 사격','hunter_shadowshot','h15_super_void','HunterSuper.java',8),
    ('hunter/blade_barrage','SOLAR','칼날 장전','hunter_blade_barrage','w230_hunter_blade_barrage','HunterExpandedSupers.java',None),
    ('hunter/gathering_storm','ARC','폭풍결집','hunter_gathering_storm','w230_hunter_gathering_storm','HunterExpandedSupers.java',None),
    ('hunter/storms_edge','ARC','폭풍의 칼날','hunter_storms_edge','w230_hunter_storms_edge','HunterExpandedSupers.java',400),
    ('hunter/spectral_blades','VOID','스펙트럼 칼날','hunter_spectral_blades','w230_hunter_spectral_blades','HunterExpandedSupers.java',470),
    ('titan/arc_super','ARC','대혼란의 주먹','titan_fists_of_havoc','w229_titan_arc','TitanSuper.java',500),
    ('titan/solar_super','SOLAR','태양의 망치','titan_hammer_of_sol','w229_titan_solar','TitanSuper.java',420),
    ('titan/void_super','VOID','파수병 방패','titan_sentinel_shield','w229_titan_void','TitanSuper.java',340),
    ('titan/thundercrash','ARC','천둥충돌','titan_thundercrash','w230_titan_thundercrash','TitanExpandedSupers.java',None),
    ('titan/burning_maul','SOLAR','불타는 망치','titan_burning_maul','w230_titan_burning_maul','TitanExpandedSupers.java',500),
    ('titan/ward_of_dawn','VOID','새벽의 수호물','titan_ward_of_dawn','w230_titan_ward_of_dawn','TitanExpandedSupers.java',600),
    ('warlock/arc_super','ARC','폭풍몰입','warlock_stormtrance','w229_warlock_arc','WarlockSuper.java',320),
    ('warlock/solar_super','SOLAR','여명','warlock_daybreak','w229_warlock_solar','WarlockSuper.java',480),
    ('warlock/void_super','VOID','신성 폭탄','warlock_nova_bomb','w229_warlock_void','WarlockSuper.java',None),
    ('warlock/well_of_radiance','SOLAR','빛의 샘','warlock_well_of_radiance','w230_warlock_well_of_radiance','WarlockExpandedSupers.java',600),
    ('warlock/chaos_reach','ARC','혼돈 범위','warlock_chaos_reach','w230_warlock_chaos_reach','WarlockExpandedSupers.java',80),
    ('warlock/nova_warp','VOID','신성 차원','warlock_nova_warp','w230_warlock_nova_warp','WarlockExpandedSupers.java',490),
]

# W229 tags come from the pinned timing manifest. W330 tags come from its own
# direct evaluation manifests. Other W230 candidates are named-source/length
# matches; that distinction is deliberately retained rather than fabricated.
W230_CANDIDATES = {
    'w229_titan_arc_start':'80A8AD9A','w229_titan_arc_start_air':'80A8AD9B','w229_titan_arc_land':'80A8AD9C','w229_titan_arc_air':'80A8A6AA',
    'w230_hunter_blade_barrage_start':'80A8AD86','w230_hunter_gathering_storm_start':'80A8ABF2',
    'w230_hunter_storms_edge_start':'80A8ACCE','w230_hunter_storms_edge_blink':'80A8ACF0',
    'w230_titan_burning_maul_start':'80A8AAF7','w230_titan_burning_maul_start_air':'80A8AB1A',
    'w230_titan_thundercrash_start':'80A8AAD4','w230_titan_thundercrash_start_air':'80A8AAE7',
    'w230_titan_thundercrash_idle':'80A8AAE6','w230_titan_thundercrash_air':'80A8AAE6',
    'w230_titan_thundercrash_end':'80A8AAFC','w230_titan_thundercrash_end_wall':'80A8AAED',
    'w230_titan_ward_of_dawn_start':'80A8ADA0','w230_titan_ward_of_dawn_start_air':'80A8AD98',
    'w230_titan_ward_of_dawn_air':'80A8AD95','w230_titan_ward_of_dawn_land':'80A8ADA2',
    'w230_warlock_chaos_reach_start':'80A8AABC','w230_warlock_chaos_reach_idle':'80A8AAD8','w230_warlock_chaos_reach_end':'80A8AADF',
    'w230_warlock_nova_warp_start':'80A8A9AE','w230_warlock_nova_warp_start_air':'80A8A9A2',
    'w230_warlock_well_of_radiance_start':'80A8AAC6','w230_warlock_well_of_radiance_start_air':'80A8AACA','w230_warlock_well_of_radiance_land':'80A8AACB',
}


NOTES = {
 'hunter/arc_staff': ('baseline_W330_W331', 'Ground/air cast + 3 ground lights + air light + four source dodges. Existing ready/move/end are legacy authored poses; heavy/uppercut/slam source actions are available but not a registered runtime primary/heavy contract.', 'Shift+F; wait1.6s; left click x3 with1.6s gaps; direction + Shift twice for all four directions (modless DoubleSneak); GCB uses its separate dodge binding; jump then left click; idle and move; expiry.', 'Ground + grounded dodge; raised launch pad for air cast/air attack.', 24),
 'hunter/golden_gun': ('P2_source_gap', 'No Golden Gun animation group exists in the supplied Light package. Current start.45/shot.35/end.35 and ready loop2s are authored H15 motion, not an original extraction.', 'Shift+F; wait.6s; left click x3 with.5s gaps; retain final dissolve/recovery. Repeat air activation once.', 'Ground and falling from a low platform.', 12),
 'hunter/shadowshot': ('P1_retarget_retime', 'Source ground AD97/air AD8A are1.3s. W199 attack.9s retimes lower body and forces endpoint toward ready; upper body preserves authored bow/cheek/nock. Air source inspected but deferred; release stays fixed7ticks. This is a partial adaptation, not full original source motion.', 'Shift+F only; automatic draw/release; no click should duplicate it. Aim level/up/down; observe bow grip and recovery. Repeat while falling.', 'Ground; falling cast above safe landing floor.', 5),
 'hunter/blade_barrage': ('P2_native_pending', 'Single complete cast1.9667s source; two automatic volleys at15/29ticks. No separate source attack/end identified in this supplied group. Common end path invokes vanilla WHACK when _end is missing.', 'Shift+F; no primary input required; observe both knife volleys and full recovery. Repeat falling.', 'Ground and falling; clear forward target volume.', 5),
 'hunter/gathering_storm': ('P2_native_pending', 'Complete cast1.6333s; automatic release5ticks is a provisional gameplay cue, not a decoded source event. Hand prop explicitly released; flight/field outlive cast. No independent end clip; generic end swing fallback.', 'Shift+F; no attack click; aim at owned target/wall; observe staff release and return, field remains.', 'Ground + falling cast; target within projectile range.', 13),
 'hunter/storms_edge': ('P1_phase_gap', 'Original dagger cast1.6667s and blink-enter.0667s exist. No _attack clip: each extra charge explicitly reuses _start. Native blink-enter only covers2/30s, not an invented full spin. No end source, generic swing fallback.', 'Shift+F automatic first throw; wait2s; left click twice with2s gaps; aim at safe wall/owned enemy so each throw can collide and blink. Observe charges0 and exit.', 'Ground and falling; safe blink destination required.', 9),
 'hunter/spectral_blades': ('baseline_W330', 'Nine directly evaluated original actions + source final guard idle/air + mixed authored lower-body gait. Full duration, continuous quaternion metadata. Source contact beats explicitly provisional. Heavy uses Shift+left click; no invented light2-air clip.', 'Shift+F; wait1.8s; left click x3 at1.9s gaps; Shift+left click heavy; observe invisibility. Repeat cast/light/heavy in air; walk/run and blocked walk.', 'Ground; raised platform fall for air actions; long enough air hang for selection.', 25),
 'titan/arc_super': ('P1_authored_attack_source_gap', 'Ground/air cast/landing source retained. Independent light _attack.5s and ready/move loops are authored; Light source group has casts/air idle but no verified light punch. Air primary selects air/landing pose; do not relabel a cast as original light attack.', 'Shift+F; wait1.7s; left click x2 at.9s gaps; jump and click to slam; land. Repeat air activation from platform; expire/cancel.', 'Ground; platform fall with solid landing floor for _land.', 28),
 'titan/solar_super': ('P2_air_source_unused', 'Ground cast1.2667s and throw1.5667s are full source. Source air cast/air melee exist but no product _start_air or air-throw selector. Idle source hold; move includes authored lower gait.', 'Shift+F; wait1.5s; left click x2 at1.8s gaps; walk; repeat activation/throw falling. Observe hammer item recovery and expiry.', 'Ground + falling; safe projectile target.', 24),
 'titan/void_super': ('P2_air_source_unused', 'Ground cast1.4s + throw1.3333s + Sentinel sprint composition. Original air cast1.3333s/throw.8s and weak combos exist but product has only ground cast/throw contract; no claim of original melee combos.', 'Shift+F; wait1.6s; left click x2 at1.6s gaps; walk; repeat falling cast/throw.', 'Ground + falling; owned enemy + wall for shield flight.', 20),
 'titan/thundercrash': ('P2_native_pending', 'Ground/air enter.8s, source single-frame flight extended to.2s hold, normal exit.8333s and wall exit.6667s. Source hold period is authored, not duration compression. Steering/impact are runtime, not clip translation.', 'Shift+F; steer camera into floor/owned enemy; second activation into vertical wall to cover end_wall; third air activation. No primary attack needed.', 'Ground/air start; safe floor and wall in bounded flight corridor.', 8),
 'titan/burning_maul': ('P1_attack_source_gap', 'Only original ground/air casts1.3s are in Light group. Product light.65s/heavy.9s and idle/move/air.8s are authored adapters; no matching original attack extraction is present. Shift-heavy only accepted while supported.', 'Shift+F; wait1.5s; left click x2 with1s gaps; Shift+left click heavy; observe wave and full recovery; air activation + normal light; walk.', 'Ground for heavy; falling cast with safe landing for air variant.', 28),
 'titan/ward_of_dawn': ('P2_native_pending', 'Source ground1.4/air-enter.4333/air-loop.9/land1.1s exist. Field installs only on support; player cast/camera is released while independent field remains. No separate end action required.', 'Shift+F on floor; observe dome and weapon return. Repeat falling from platform; observe air-enter/loop/land then dome; no click.', 'Ground + falling; solid landing required; avoid floating-field fixture.', 8),
 'warlock/arc_super': ('P2_air_source_unused', 'Ground cast1.2333/attack-enter.4667/attack-idle.5/end.3333s full source. Air cast1.2667 and blink source exist but not selected. Attack is repeated enter pulses rather than complete enter→hold→exit channel state machine.', 'Shift+F; wait1.5s; repeated left click for2s to sustain channel; release and observe end; move; repeat falling activation.', 'Ground and falling; owned target within10blocks.', 19),
 'warlock/solar_super': ('P2_air_source_unused', 'Ground cast1.5667s + event-linked slash1.0333s are pinned source; source air cast exists but not installed/selected. Idle/move use generic sword-catch Replacement source, not confirmed Daybreak ready; air lower body uses generic glide. Slash2 source reviewed previously but not selected.', 'Shift+F; wait1.8s; left click x2 at1.3s gaps; walk; jump/glide and click; repeat air activation; observe sword/camera recovery.', 'Ground and falling/glide with safe floor.', 27),
 'warlock/void_super': ('P2_air_source_unused', 'Source ground cast1.3s occupies _attack, auto-selected on first tick; _start/_idle absent intentionally. Source air AD81 also1.3s but not installed/selected. Release15ticks (14+entry1); visual duration27ticks. Common end swing fallback.', 'Shift+F automatic Nova; no click; observe release and complete follow-through until projectile impact. Repeat falling.', 'Ground + falling; clear target within projectile lifetime.', 6),
 'warlock/well_of_radiance': ('P2_native_pending', 'Complete source ground1.7667/air-enter.5667/land1.0667. Landed sword planted after full landing phase; independent Well remains600ticks, player returns to weapon immediately after planting.', 'Shift+F on floor; observe sword plant/weapon return. Repeat platform fall; observe air-enter, supported landing, sword plant. No attack click.', 'Ground + falling with solid landing support; field cannot plant midair.', 8),
 'warlock/chaos_reach': ('P2_native_pending', 'Complete source enter.7333/end.4; original loop is single frame and product hold.0667. Alternate source exit.8 exists but variant is not proven required. Runtime plays exit before end() cleanup, so do not misclassify the final stop as skipped exit.', 'Shift+F; aim beam at owned target; no click; observe channel and.4s exit; repeat air activation.', 'Ground + falling/air;24block beam lane.', 6),
 'warlock/nova_warp': ('P1_source_attack_unused', 'Ground/air cast2.0333s exist. Product burst attack.6s and idle/move/air.8s are authored. Original charge-exit A99D1.2667s and single-frame charge-idle A99C are unused. Replacing visual must retain gameplay charge12/recovery6 and damage epoch semantics until explicitly revised.', 'Shift+F; wait2.3s; left click to charge/burst; wait1.2s; Shift+left click blink; walk; repeat falling activation/burst. Observe burst recovery + expiry.', 'Ground + falling; safe unobstructed blink landing.', 28),
}


def collect_sources():
    sources={}
    for folder in sorted((LIGHT/'animations').iterdir()):
        if not (folder/'clips.json').exists():continue
        inspection=read(folder/'inspection.json') if (folder/'inspection.json').exists()else{}
        actions={a['tag']:a for a in inspection.get('actions',[])}
        labels={}
        for line in (folder/'CLIPS.md').read_text().splitlines():
            if line.startswith('| 80'):
                fields=[v.strip()for v in line.split('|')]
                labels[fields[1]]=fields[2]
        sources[folder.name]={'path':str(folder),'blendExists':(folder/'source.blend').exists(),'blendSha256':sha(folder/'source.blend')if(folder/'source.blend').exists()else None,'evaluationThisTask':'not opened; pre-existing delivered inspection.json metadata only','actions':[]}
        for c in read(folder/'clips.json'):
            a=actions.get(c['tag'],{})
            sources[folder.name]['actions'].append({'tag':c['tag'],'name':labels.get(c['tag'],a.get('name')),'frameCount':c.get('FrameCount'),'sourceDurationSeconds':a.get('duration',(c.get('FrameCount',1)-1)/30),'layer':c.get('layer'),'preexistingInspection':a,'events':c.get('events',[])})
    return sources


def main():
    sources=collect_sources()
    resources=['hunter_w199.animation.json','classes_w230.animation.json','arc_staff_w330.animation.json','spectral_blades_w330.animation.json']
    clips={};clipresource={}
    for resource in resources:
        for c in read(ANIM/resource)['animations']:
            clips[c['name']]=c;clipresource[c['name']]=resource
    w229={c['name']:c for c in read(MAIN/'art/classes/w229/animation/timing-manifest.json')['clips']}
    spectral={c['clip']:c for c in read(MAIN/'art/animation/w330/spectral_blades/manifest.json')['clips']}
    arcmanifest=read(MAIN/'art/animation/w330/arc_staff/manifest.json')
    arcraw=arcmanifest['clips']
    arcrecords=list(arcraw.values())if isinstance(arcraw,dict)else arcraw
    arcmapping={}
    for c in arcrecords:
        name=c.get('name',c.get('clip'))
        if name:arcmapping[name]=c
    superrecords=[]
    for path,element,korean,group,prefix,runtime,default_duration in SPECS:
        cls=path.split('/')[0]; priority,note,inputs,air,duration=NOTES[path]
        records=[]
        for name,c in clips.items():
            if not (name==prefix or name.startswith(prefix+'_')):continue
            suffix=name[len(prefix):].removeprefix('_')or'idle'
            tag=None;status='authored_or_unpinned';kind='source attribution not pinned in this catalog';source_group=group
            if name in w229:
                tag=w229[name].get('actionTag');kind=w229[name].get('kind');status='pinned existing timing-manifest'
            if name in W230_CANDIDATES:
                tag=W230_CANDIDATES[name];status='semantic-name + exact-length candidate; per-clip W230 provenance not found';kind='source candidate, not newly re-evaluated'
            if name in spectral:
                s=spectral[name];tag=s.get('tag',s.get('sourceGuardTag'));status='W330 direct Blender evaluation manifest';kind=s.get('policy','source motion')
            if name in arcmapping:
                s=arcmapping[name];tag=s.get('tag',s.get('source_tag',s.get('sourceTag')));status='W330 direct Blender evaluation manifest';kind='source motion'
            if path=='hunter/shadowshot'and suffix=='attack':tag='80A8AD97';status='W199 retarget PLAN + sealed source sample';kind='partial source lower-body + authored bow upper-body / retimed'
            if path=='hunter/arc_staff'and suffix.startswith('dodge_'):
                tag={'dodge_forward':'80A8A938','dodge_backward':'80A8A93C','dodge_left':'80A8A93E','dodge_right':'80A8A93F'}[suffix];status='W331 direct Blender source review';kind='source dodge'
            action=next((a for a in sources.get(source_group,{}).get('actions',[])if a['tag']==tag),None)
            if action is None and tag:
                for candidate,g in sources.items():
                    found=next((a for a in g['actions']if a['tag']==tag),None)
                    if found:source_group=candidate;action=found;break
            source_seconds=action['sourceDurationSeconds']if action else ((w229[name]['sourceRange'][1]-w229[name]['sourceRange'][0])/w229[name].get('sourceFps',30) if name in w229 and w229[name].get('sourceRange') else None)
            source_comparison='unresolved/no single motion source'
            if source_seconds is not None:
                if source_seconds==0:source_comparison='single original pose extended into hold; not a retimed motion'
                elif any(x in str(kind).lower()for x in ['hold','gait','composition','catch','ready']):source_comparison='hold or composite; clip period is authored, not source playback speed'
                else:source_comparison='full source span matched'if abs(c['length']-source_seconds)<1e-7 else'length differs from source (retime/partial adaptation)'
            records.append({'phase':suffix,'clip':name,'resource':clipresource[name],'exists':True,'clipSeconds':c['length'],'clipTicksCeil':math.ceil(c['length']*20-1e-9),'onceOrLoop':c['loop'],'originalGroup':source_group,'originalTag':tag,'originalSeconds':source_seconds,'attribution':status,'kind':kind,'sourceComparison':source_comparison,'quaternionSampling':c.get('destiny_quaternion_sampling',False),'entryBlendTicks':c.get('destiny_entry_blend_ticks',1 if c['loop']!='loop'else None),'exitBlendTicks':c.get('destiny_exit_blend_ticks',0 if c['loop']!='loop'else None),'contactSeconds':c.get('destiny_contact_seconds'),'contactProvisional':c.get('destiny_contact_provisional')})
        tuning_path=MAIN/'src/main/resources/data/destiny/destiny_ability'/f'{path}.json'
        tuning=read(tuning_path).get('params',{})if tuning_path.exists()else{}
        runtime_path=f'src/main/java/kim/biryeong/destiny/ability/{cls}/{runtime}'
        used={r['originalTag']for r in records if r['originalTag']}
        source_actions=sources.get(group,{}).get('actions',[])
        superrecords.append({'id':'destiny:'+path,'class':cls,'element':element,'displayName':korean,'equipEligible':True,'eligibilityEvidence':['AbilityRegistry.register -> '+runtime_path,'CharacterLoadouts.options: matching class/element/SUPER; supported ARC/SOLAR/VOID'],'runtimeSource':runtime_path,'runtimeSourceSha256':sha(MAIN/runtime_path),'sourceGroup':group,'originals':sources.get(group),'productPrefix':prefix,'phases':records,'availableSourceTagsNotMappedToProductClip':[{'tag':a['tag'],'name':a['name'],'seconds':a['sourceDurationSeconds']}for a in source_actions if a['tag']not in used],'classification':priority,'reviewNote':note,'configuredParams':tuning,'defaultOrConfiguredSessionTicks':tuning.get('duration_ticks',default_duration),'nativeReviewStatus':'W330/W331 evidence exists; W332 interpolation recheck still pending'if priority.startswith('baseline')else'W332 native review pending; metadata/catalog is not motion acceptance','nativeScenario':{'setup':[f'/guardian class {cls}',f'/guardian subclass {element.lower()}',f'/guardian equip destiny:{path}','/guardian super 100 (OP; verified GuardianCommands.java)' ],'activate':'native Shift+F','inputs':inputs,'airCondition':air,'minimumCaptureSeconds':duration,'observe':['ground/air phase selection','hip/chest separation and wrist/item attachment','full recovery and return to normal gear','no neutral snap, no duplicate cast, no stale delayed action','2tick display interpolation, gameplay timings unchanged']}})
    evidence_files=['src/main/java/kim/biryeong/destiny/guardian/CharacterLoadouts.java','src/main/java/kim/biryeong/destiny/guardian/Element.java','src/main/java/kim/biryeong/destiny/fx/ClassSuperModelAssets.java','src/main/java/kim/biryeong/destiny/fx/ClassAbilityEffects.java','src/main/java/kim/biryeong/destiny/fx/PlayerAnimations.java','src/main/java/kim/biryeong/destiny/fx/ShadowshotTiming.java','scripts/build_shadowshot_source_w199.py','art/classes/w229/animation/provenance.json','art/classes/w229/animation/timing-manifest.json','docs/qa/2026-11-07/w330-melee-super-motion/README.md']
    for cls in ['hunter','titan','warlock']:evidence_files.append(f'src/main/java/kim/biryeong/destiny/ability/{cls}/{cls.capitalize()}Abilities.java')
    source_evidence=[{'path':f,'sha256':sha(MAIN/f)}for f in evidence_files if(MAIN/f).exists()]
    result={'schemaVersion':1,'task':'W332 whole implemented super source/runtime catalog','date':'2026-11-07','mainReadOnly':str(MAIN),'counts':{'all':len(superrecords),'hunter':7,'titan':6,'warlock':6},'scope':'registered and selectable on the current ARC/SOLAR/VOID classes; not every original Destiny super','verification':'read-only current source, JSON and prior source-review provenance; no original blend opened in this task; no new native acceptance; W330 direct evaluations are cited as prior evidence','interpolationRequirement':'2 server ticks of display interpolation duration. Preserve gameplay contact/cooldowns/entry blend/phase lengths. Do not interpret this as changing SwordTiming.START_TICKS. GCB supported display interpolation capability is owned by interpolation worker/master.','originalRootChecks':{'Light':{'path':str(LIGHT),'exists':LIGHT.exists()},'Dark':{'downloadsTopLevelMatches':[p.name for p in Path('/Users/qf/Downloads').iterdir()if'Dark' in p.name and'Abilit' in p.name],'note':'No Dark Abilities package found in Downloads top level; current selectable Element has no Stasis/Strand.'},'WindowsReturn':[{'path':s,'exists':Path(s).exists()}for s in ['/Volumes/qf-ssd/DestinyGuardians-Super-Animation-VFX-2026-10-27/destiny-animation-return','/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return']],'unavailablePriorSources':['warlock_daybreak_event_linked slash1/slash2 and generic sword_catch/glide remain pinned in W229 provenance, but that external staged root is not currently mounted; no claim of new blend review']},'runtimeFallbacks':{'class-prefixed':'No fallback to Hunter/Steve for missing w229/w230 source clip; missing phase is explicit absence. ClassAbilityEffects.attack/end use vanilla WHACK 4tick if corresponding clip absent.','hunter-base':'Resolver tries current Hunter -> legacy H15 -> guardian_hunter -> steve; it does not substitute a roll for a super. Distinguish graceful failure from exact source motion.','storm-edge':'Missing _attack explicitly reuses _start for additional charges.','sourceDurationUnits':'(FrameCount-1)/30 from supplied Blender inspection, not independently measured live Destiny playback speed. Event startFrame is0-based vs Blender1-based.','loopPeriods':'Source single-pose loops and sampled guard holds have authored nonzero repeat periods; do not classify those as source duration compression.'},'priorityOrder':['P1_retarget_retime','P1_source_attack_unused','P1_phase_gap','P1_attack_source_gap','P1_authored_attack_source_gap','P2_air_source_unused','P2_source_gap','P2_native_pending','baseline_W330','baseline_W330_W331'],'nextProductScopeProposal':{'shadowshot':['NEW art/animation/w332/shadowshot/**','NEW scripts/art/w332_shadowshot.py','HunterSuper.java ground/air selector','HunterModelAssets.java named overlay','ShadowshotTiming/phase bridge only if needed; preserve current release7tick until separately authorized'],'novaWarp':['NEW art/animation/w332/nova_warp/**','NEW scripts/art/w332_nova_warp.py','ClassSuperModelAssets.java named overlay','WarlockExpandedSupers.java charge/exit/air visual mapping; preserve gameplay charge12/recovery6 and session ownership'],'airFollowup':['TitanSuper.java / WarlockSuper.java selectors','new named overlay clips in class assets; source cast/throw semantic confirmation before integration'],'unavailableSourceFollowup':['Golden Gun exact original action unavailable in current Light delivery','Burning Maul light/heavy and Fists independent light source missing from corresponding Light groups; do not label authored substitutes as original']},'sourceEvidence':source_evidence,'animationResources':[{'path':str(ANIM/f),'sha256':sha(ANIM/f)}for f in resources],'supers':superrecords}
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'source-catalog.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
    lines=['# W332 구현 궁극기 원본·런타임 검토 목록','','현재 장착 가능한 궁극기는 **19개: Hunter7 / Titan6 / Warlock6**다. `AbilityRegistry` 등록과 `CharacterLoadouts`의 직업·속성·SUPER 필터가 기준이다. Stasis/Strand/Twilight Arsenal/Song of Flame은 이 구현의 선택 가능한 목록이 아니다.','','이 문서는 코드·리소스·기존 원본 평가 기록을 대조한 catalog다. **이번 작업에서 추가 `.blend`를 열거나 인게임 모션을 검증하지 않았다.** Arc/Spectral은 기존 W330/W331 직접 평가·native 기록을 참조한다. 나머지의 실제 외형·파지·프레임 연속성은 master가 아래 시나리오로 확인해야 한다.','','사용자 요구의 **2틱은 display interpolation duration**이다. gameplay contact, cooldown, entry blend, clip 길이 변경으로 해석하지 않는다. GCB 지원 경로는 별도 구현 담당이 확인한다.','','## 원본 가용성','','- Light 전달본 `'+str(LIGHT)+'`의 source.blend/CLIPS.md/inspection.json을 읽기 전용으로 목록화했다. 초 단위 길이는 원본30fps 액션 범위이며 실제 Destiny 재생 배속까지 검증한 수치는 아니다.','- 지정 WindowsReturn 두 `/Volumes/qf-ssd/...` 원본은 현재 마운트되어 있지 않다. Downloads 최상위에 Dark Abilities 전달본은 없었다. 없는 원본을 확인했다고 표시하지 않는다.','- W229 Daybreak slash1/2, sword-catch/glide는 기존 provenance에 해시가 남아 있으나 현재 Light 그룹에 모두 포함되어 있지는 않다. 기존 source evaluation과 이번 재평가를 구분한다.','','## 우선순위와 전체 시나리오','','| 우선순위 | Super ID / 직업·속성 | 현재 문제·판단 | native 입력 / 최소 캡처 |','|---|---|---|---|']
    for s in sorted(superrecords,key=lambda s:(result['priorityOrder'].index(s['classification']),s['id'])):
        lines.append(f"| {s['classification']} | `{s['id']}` / {s['class']}·{s['element']} | {s['reviewNote']} | {s['nativeScenario']['inputs']} / {s['nativeScenario']['minimumCaptureSeconds']}s |")
    lines+=['','## 각 궁극기의 실제 클립과 원본 대응','','숫자는 clip 본체의 길이다. entry/exit blend는 JSON의 별도 필드로 남겼다. W229는 timing-manifest가 출처이고, W330은 직접 Blender 평가 manifest가 출처다. 그 밖의 W230 tag는 **이름 의미 + 동일 길이로 좁힌 후보**이며, 별도의 per-clip provenance를 찾지 못한 경우 원본 대응 확정으로 표시하지 않았다. hold/composite의 반복 주기는 원본 움직임의 배속으로 비교하지 않는다.']
    for s in superrecords:
        lines+=['',f"### {s['displayName']} — `{s['id']}`",'',f"Runtime: `{s['runtimeSource']}`. 분류: **{s['classification']}**. 설정: `{json.dumps(s['configuredParams'],ensure_ascii=False,separators=(',',':'))}`.",'','| phase | runtime clip seconds | source tag / source seconds | 출처·상태 |','|---|---:|---|---|']
        for c in s['phases']:
            src=f"{c['originalTag'] or 'unresolved'} / {c['originalSeconds']}"
            lines.append(f"| {c['phase']} | {c['clipSeconds']:.6f} | {src} | {c['sourceComparison']}; {c['attribution']} |")
        lines+=['',s['reviewNote'],'',f"미연결 원본 후보: "+'; '.join(f"{a['tag']} {a['name']} ({a['seconds']:.6f}s)"for a in s['availableSourceTagsNotMappedToProductClip']),f"\nNative: {s['nativeScenario']['inputs']} 조건: {s['nativeScenario']['airCondition']} 최소 {s['nativeScenario']['minimumCaptureSeconds']}s. 장착은 직업→속성→`/guardian equip {s['id']}` 후 super energy100, 실제 Shift+F. 에너지는 OP `/guardian super 100` 등록을 확인했다."]
    lines+=['','## 공용 fallback과 다음 수정 배정','','- `w229_`/`w230_` missing clip은 Hunter/Steve 클립으로 대체되지 않는다. 다만 ClassAbilityEffects의 missing attack/end는 vanilla WHACK4tick이다. 별도 end가 없는 단발 cast를 원본 end 완료라고 기록하지 않는다.','- Hunter base의 current→legacy H15→Steve 탐색은 회복 경로이며 원본 fidelity의 근거가 아니다. Storm’s Edge 추가 throw는 missing attack 때문에 start를 다시 선택한다.','- Chaos Reach는 tickChaos에서 먼저 end를 재생하고 exit 길이만큼 기다린다. 최종 end()의 stop만 보고 exit 누락이라고 판단하면 잘못이다.','- Shadowshot 우선 제안: 새 named source overlay/generator + HunterSuper ground/air 선택 + HunterModelAssets 설치. 원본 표시1.3초와 기존7tick release를 분리하고 bow/nock 접촉을 native로 확인한다.','- Nova Warp 우선 제안: 새 charge-idle/charge-exit source overlay/generator + ClassSuperModelAssets 설치 + WarlockExpandedSupers 시각 phase mapping. source1.267초를 gameplay charge12/recovery6에 무조건 대입하지 않는다.','- Hammer/Sentinel/Daybreak/Stormtrance/NovaBomb air selector는 다음 배치 후보. 새로운 art clip과 정확한 phase/출처를 함께 반환한다.','- Golden Gun, Maul attack, Fists light는 이번 원본에서 확인되지 않은 범위다. 원본 확보 또는 명시적 approximation 승인으로 분리하며 임의 cast 재사용을 original attack으로 부르지 않는다.','','## 검사 경계','','19개 ID 중복 없음, 현재 source/resource JSON 파싱 및 클립 길이 대조, 입력 시나리오 생성만 수행했다. 새 native QA·Blender 평가·렌더·모션 수락은 수행하지 않았다. main/prod/asset 변경 없음. 전체 원본 tag·event·hash와 실제 clip 목록은 source-catalog.json에 보관했다.']
    (OUT/'source-catalog.md').write_text('\n'.join(lines)+'\n')
    print('W332 catalog:',len(superrecords),'supers',sum(len(s['phases'])for s in superrecords),'phase clips')


if __name__=='__main__':main()
