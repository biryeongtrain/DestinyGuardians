from pathlib import Path
import json, shutil, sys, hashlib
r=Path('/Users/qf/IdeaProjects/DestinyGuardians');s=Path(__file__).parent;q=r/'docs/qa/2026-10-28/w222'
q.mkdir()
ids=['biting_winds','whispering_slab','long_arm','nezarec_s_whisper']
groups={'bow_6239be39':ids[:2],'scout_rifle_e4c9ea6c':[ids[2]],'glaive_f9784d8f':[ids[3]]}
actions={ids[0]:'80A8A207',ids[1]:'80A8A207',ids[2]:'80A8A345',ids[3]:'80A8A440'}
slots=json.loads((r/'docs/qa/worktree-pool.json').read_text())['slots']
features=[]
for i,w in enumerate(ids):
    mode='insert' if w=='long_arm' else 'reload'
    features.append({'name':'w222-'+w,'destination':slots[i]['path'],'owned_paths':['scripts/generate_'+mode+'_w222_'+w+'.py','art/weapons/w222/'+w+'/profile.json','art/weapons/w222/'+w+'/review.md']})
selection={'ids':ids,'groups':groups,'actions':actions,'limits':['Source armature only; no weapon mesh/camera/finger IK. Long Arm scout action is generic full reload, not recovered two-cartridge loops. Bow nocking is RIGHT-hand handling; preserve LEFT riser contact.']}
for name,d in [('selection.json',selection),('worktrees.json',{'features':features})]:
    for folder in (s,q):(folder/name).write_text(json.dumps(d,indent=2)+'\n')
shutil.copy2(s/'source-review.json',q/'source-review.json');shutil.copytree(s/'sheets',q/'source-sheets')
for group in groups:
    p=r/'art/weapons/w222/rigs'/(group+'.json');p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(s/(group+'.json'),p)
sys.path.insert(0,str(r/'scripts'));import rig_arms_w205 as rig
rows=[]
for group,ws in groups.items():
    d=json.loads((s/(group+'.json')).read_text());a=d['actions'][actions[ws[0]]];frames=a['frames'];rest=frames[0]['joints']
    def relative(j,side):
        b=rig.transpose(rig.weapon_basis(j));p=rig.sub(rig.pos(j[side+'Wrist']),rig.pos(j['weapon']));return [rig.dot(row,p) for row in b]
    origins={side:relative(rest,side) for side in ('left','right')}
    excursions={side:max(rig.norm(rig.sub(relative(f['joints'],side),origins[side])) for f in frames) for side in origins}
    rows.append({'group':group,'weapons':ws,'action':actions[ws[0]],'range':[a['start'],a['end']],'samples':len(frames),'maximumWeaponRelativeWristExcursion':excursions,'sourceCacheSha256':hashlib.sha256((s/(group+'.json')).read_bytes()).hexdigest()})
(q/'source-handling-evidence.json').write_text(json.dumps({'rows':rows,'limits':selection['limits']},indent=2)+'\n')
(q/'README.md').write_text('# W222 — 활2·Long Arm·월도 원본 체인\n\n상태: 원본 Blender 평가 완료, 구현/두 차례 Vision 대기. 완료 수락 아님.\n\n무기4종을 독립 고정 worktree에 배정한다. master가 공유 리깅·생성·검증·Vision을 취합한다. 원본 평가/수정/각 검증 결과를 step-log.md에 남긴다. Long Arm 반복 삽입과 source camera 부재를 원작 복원이라고 주장하지 않는다. 전체 무기/HUD 목표는 진행 중이다.\n')
(q/'step-log.md').write_text('# W222 단계 기록\n\n- W221 product13f4f63 and policyfe0aa96 are committed. Previous goal turn is progress. Main dirty baseline preserved.\n- Actual3 original .blend evaluated in separate Blender5.4Alpha with scripts disabled. Shoulder/elbow/wrist/weapon,61 samples, previous-cache error0; all source bytes unchanged. Master viewed3 actual source chain sheets.\n- Preserve W219 audio and existing ammo/cadence/draw/guard/input mechanics. No numeric-perk tests or broad60fps claim. Four fixed slots selected; refresh must complete before workers start.\n')
print({'selection':selection,'sourceWristEvidence':rows})
