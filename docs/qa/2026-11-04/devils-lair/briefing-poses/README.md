# 공격전 브리핑 착륙 포즈 (Crota's End cin_728_rai)

사용자가 고른 `Destiny-Raid-Briefing-Poses-2026-11-04`의 pla01(중앙)·pla03(왼쪽, 손 들기)·pla06(오른쪽) 266프레임 클립을 Blender로 읽기 전용 평가하고, 기존 W260 리타게팅(같은 72본 리그, rest 오차 < 1e-5)으로 `h15_intro_brief_*`를 만들었다. 생성기는 `scripts/animation/build_briefing_poses.py`, 출처·해시는 `art/strikes/briefing/briefing-poses-provenance.json`이다.

- 공용 코드: `ActivityCast`(브리핑·인트로 배우 캐스트), `BriefingFormation`(3자리 배치·카메라), `TransmatArrival`(전송 이펙트), `CinematicHands`(무기 숨김)는 `activity/presentation`에 두었다. 악마의 소굴은 BRIEFING 단계에서 RY.IN 기준으로 호출만 한다.
- 착지 전 숨김: 각 역할은 원본에서 화면에 들어오는 프레임(pla01 1, pla06 81, pla03 141)부터 재생된다. 그 전까지 몸은 보이지 않고, 등장 12틱 전부터 빛 기둥·하강 링이 모인 뒤 섬광과 전송음으로 나타난다.
- 방향: 마지막 가슴 방향을 루트 회전에 구워 세 명 모두 카메라 정면을 본다(보정 pla03 70.9°, pla01 112.5°, pla06 34.7°).
- 무기: 브리핑 동안 손에 든 슬롯을 빈 슬롯으로 옮기고 1인칭 무기 표시를 카메라 송신 범위 안에서 제거한다. 인벤토리 내용은 바꾸지 않으며 단계가 끝나면 원래 슬롯으로 돌아온다.
- 실화면: 격리 서버 3인으로 확인했다. `before-facing-fix.jpg`는 중앙 수호자가 옆을 보던 상태, `before-weapon-fix.jpg`는 1인칭 무기가 남던 상태, `final-sheet-qa*.jpg`가 수정 후다.
- 남은 한계: 브리핑 첫 프레임은 카메라 청크 로딩으로 검게 나온다. 손가락·손목·발목은 현재 16그룹 리그로 재현되지 않는다.

## 1인 브리핑 · 브리핑 중 재접속 (추가 검증)
- 1인 시작에서도 중앙 자리 1명으로 캐스트가 만들어지고 전송 이펙트 후 착지한다(`solo-briefing.jpg`).
- 결함: 브리핑 중 접속을 끊었다 다시 들어오면 빈 슬롯이 선택된 채 저장되어 손이 비어 있었다(`rejoin-before-fix-empty-hand.jpg`). Fabric DISCONNECT 이벤트가 플레이어 데이터 저장보다 늦게 와서, 그 시점의 복원은 저장되지 않는다.
- 수정: 숨긴 슬롯 번호를 플레이어 attachment(`destiny:cinematic_stowed_slot`)로 저장하고, 접속 시 남아 있으면 원래 슬롯으로 되돌린다. 수정 후 재접속하면 무기와 탄약 HUD가 돌아온다(`rejoin-after-fix-weapon.jpg`).
