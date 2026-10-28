# W222 — 활2·Long Arm·월도 원본 체인

상태: W222 범위 수락. 원본 Blender → 61포즈 → FIRST Vision → 동일4worker 피드백/수정 → SECOND Vision 완료. 전체 무기/HUD 목표는 진행 중이다.

대상: Biting Winds, Whispering Slab, Long Arm, Nezarec’s Whisper. 별도 Blender에서 실제 원본 .blend를 먼저 평가한 뒤 고정 worktree4개를 갱신·재사용했다. master만 공유 리깅·생성·빌드·Vision·통합 커밋을 수행했다.

활2종·월도는 전체61포즈, Long Arm은 초기/반복/복귀 각각61포즈다. 활의 W50시위 이동·낮춘 왼손 접촉과 기존 게임플레이 타이밍을 유지한다. Long Arm의 쌍탄 삽입·source .35유지는 명시적 보정이다.

FIRST13시퀀스 후 월도가 화면 밖으로 벗어나는 축 정합 문제를 발견해 동일 담당자에게 캡처를 돌려보냈다. 원본과 모델의 두 파지점으로 고정 직교회전을 계산하고 무기·손·팔에 함께 적용했다. 동작 감쇠·팔 숨김·카메라 맞춤을 사용하지 않는다. Long Arm의 숨겨진 탄 particle참조도 수정했다.

자동검사: 각 제품 빌드 targeted16/16 + assemble, 최종 Python4/4. native13개씩 두 차례 총26개. 실제 확인 이미지·잔여 가림·원본 한계는 [visual-review.json](visual-review.json) 및 [review-second.json](review-second.json)에 기록했다.61포즈를 연속60fps로 주장하지 않는다.

단계 기록: [step-log.md](step-log.md). 검수한 W222 변경만 커밋하고 기존 누적 변경은 보존한다.5개 worktree슬롯과 별도48시간 awake assertion은 유지한다.
