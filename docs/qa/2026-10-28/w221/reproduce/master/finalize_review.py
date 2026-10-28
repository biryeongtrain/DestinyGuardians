from pathlib import Path
import hashlib, json, datetime, shutil

r = Path('/Users/qf/IdeaProjects/DestinyGuardians')
q = r/'docs/qa/2026-10-28/w221'
weapons = ['ikelos_sg_v1_0_1', 'mindbender_s_ambition_adept', 'parcel_of_stardust_fell_to_earth', 'pyroclastic_flow', 'seventh_seraph_officer_revolver']
viewed = [q/'vision2/screenshots'/f'{w}-{kind}.png' for w in weapons for kind in ('review','reload')]
viewed += [q/'second-post-reload-review.png']
viewed += [q/'vision2/frames'/f'w221-{w}-reload-sample-{n}.png' for w,n in [(weapons[0],'03'), (weapons[2],'13'), (weapons[3],'12'), (weapons[4],'08')]]
assert len(viewed) == 15 and all(p.is_file() for p in viewed)
build = json.loads((q/'build-pass1.json').read_text())
assert hashlib.sha256(Path(build['jar']).read_bytes()).hexdigest() == build['sha256']
native = [json.loads((q/p/'native-validation.json').read_text()) for p in ('vision1','vision2')]
assert all(d['sequences'] == 18 and d['neutralAfter'] for d in native)
assert all(len(d['partialInterrupts']) == 3 and all(x['paidShotEvents'] and not x['reloading'] for x in d['partialInterrupts']) for d in native)
review = {
    'accepted': True,
    'scope': 'W221 five-weapon sampled first-person reload, ADS and recovery acceptance; broader goal remains active',
    'at': datetime.datetime.now().astimezone().isoformat(),
    'workflow': ['original Blender evaluated', '61 poses generated', 'FIRST Vision', 'same five workers reviewed feedback and returned justified no-change', 'SECOND Vision'],
    'firstReview': 'review-first.json',
    'secondMasterViewed': [{'path': str(p.relative_to(r)), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest()} for p in viewed],
    'nativeReports': ['vision1/native-validation.json', 'vision2/native-validation.json'],
    'nativeSequencesTotal': 36,
    'targetedTestsExecuted': 16,
    'secondPhaseTestsRerun': False,
    'jarSha256': build['sha256'],
    'findings': [
        'Sampled sight apertures are visible; all five weapons return to their held pose after reload.',
        'All five reload completions and three shotgun paid-fire interruptions are supported by native/server reports in both passes.',
        'No additional product change was identified in SECOND sampled images; worker feedback only changed review documentation.'
    ],
    'limits': [
        'Shotgun cartridges are often occluded by receiver or LEFT palm; sampled PNGs do not certify every seat/disappearance instant. Shell contacts and .35 hold are authored calibration, not recovered shell events.',
        'Seventh Seraph LEFT hand is low or partly offscreen in several poses under inherited calibration; no camera or hand mesh was available in the source.',
        'Pyro projectile carry/release/seat/socket closure uses authored geometry-based approximation; source is armature-only.',
        '61 poses and sampled captures do not certify continuous60fps, exact render-phase synchronization, acoustic listening, or all-view correctness.',
        'Build and QA used the current integrated dirty checkout; inherited pre-W221 changes remain uncommitted, so this does not certify a clean-checkout build from the W221 commit alone.'
    ]
}
(q/'visual-review.json').write_text(json.dumps(review, indent=2)+'\n')
readme = q/'README.md'
s = readme.read_text().replace('상태: 61포즈 통합 완료, FIRST/SECOND Vision 대기. 완료 수락 아님.', '상태: W221 범위 수락. 원본 Blender → 61포즈 → FIRST Vision → 동일5 worker 피드백 → SECOND Vision 완료. 전체 무기/HUD 목표는 진행 중.')
s = s.replace('최종 수락 후 검수한 W221 변경을 별도 커밋한다.', '검수한 W221 변경을 별도 커밋한다.')
s += '\n검증: targeted16/16 + assemble, native18개씩 두 차례 총36개. SECOND는 문서만 바뀌어 동일 JAR를 재사용했고 테스트16개를 중복 실행한 것으로 세지 않는다. 실제 확인 이미지와 한계는 [visual-review.json](visual-review.json)에 기록했다. 샷건 탄 접촉은 일부 가려지며 리볼버 왼손은 낮거나 화면 밖에 놓이는 원본 포즈가 있다. 연속60fps·음향 청취·모든 시점 검증은 주장하지 않는다.\n'
readme.write_text(s)
with (q/'step-log.md').open('a') as f:
    f.write('\n- SECOND Vision18/18 native sequences PASS; master reviewed10 sheets, postreload sheet and4 raw frames. Scoped acceptance in visual-review.json; both passes total36 sequences, targeted16 executed once. Source/contact/visibility limits retained. Broader goal remains active.\n')
poolpath = r/'docs/qa/worktree-pool.json'
pool = json.loads(poolpath.read_text())
for slot in pool['slots']:
    slot['status'] = 'idle-needs-refresh'
    slot['lastAcceptedBatch'] = 'W221'
poolpath.write_text(json.dumps(pool, indent=2)+'\n')
for name in ('finalize_review.py', 'commit_plan.py', 'archive_workers.py', 'postflight.py'):
    shutil.copy2(Path(__file__).parent/name, q/'reproduce/master'/name)
print({'accepted': True, 'secondViewedImages': len(viewed), 'nativeSequences': 36, 'slotsRetained': len(pool['slots'])})
