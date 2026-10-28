# W223 — 월도 팔 방향과 적중·처치 HUD

상태: 이번 범위 수락. 전체 무기 시스템/HUD 목표는 계속 진행 중이다.

월도의 원본 Blender 어깨·팔꿈치·손목·무기 체인을 다시 평가하고, rest축 관례를 보존하는 강체 정합으로 대기/ADS에서 팔이 화면 중앙을 가리던 문제를 수정했다. 원본61포즈·무기/손 접촉·소스 관절 길이·기존 시간/오디오는 유지한다. 팔 포함 최대694요소다. 장전 중 왼쪽 아래 팔/HUD 가림과 원본의 빠른 관절 전환은 남아 있다. 원작 카메라 복원이나 연속60fps 완성을 주장하지 않는다.

실제 HP+흡수 체력 감소를 관측한 무기 피해에 흰 적중 확인, 처치에는 붉은 확인 표시를 추가했다. 0피해·무적·빗맞음에는 표시하지 않는다. 소유 플레이어의 노드1개로 제한하고 만료/정리와 kill우선순위를 처리한다. 일반 플레이어도 사용한다. 그림·크기·4/7tick 지속시간은 참조 기반 자체 제작/튜닝이며 원작 추출 수치가 아니다.

필수 흐름: 실제 Blender →61poses →FIRST Vision →동일2worker 검수/무변경 근거 →SECOND Vision. FIRST는6시퀀스 완료, 처치는 실제 표시 후 physical_user_input으로 중단되어 통과로 세지 않았다. SECOND는7시퀀스 모두 완료·중립, 피해100→93/무적100유지/각1발 소모/처치와 표시 만료를 확인했다. master가 실제 PNG도 검수했다. 흰 적중 표시는 FIRST에 보였고 SECOND는 짧은 표시가 선명하게 포착되지 않아 서버 model/피해/만료 확인과 구분했다. 붉은 처치 표시는 SECOND에도 확인했다.

JUnit23/23 + assemble, provenance 정리 후 Python source contract2/2 통과. worker feedback은 출처 경로/문서만 변경했고125377팩 출력과 tested JAR가 동일하여 빌드/JUnit을 반복하지 않았다. 실제 폭발 퍽/흡수 체력만의 타격/다인 접속 교체는 이번 native 범위가 아니다.

검수: [2차 결과](review-second.json), [1차 중단 기록](review-first.json), [단계 로그](step-log.md), [2차 서버 판정](vision2/native-validation.json), [검수 이미지](vision2/screenshots/hit-confirmation-review.png). 세부 설계: `docs/design/194_W223_월도_팔과_적중_HUD.md`.

관련 파일만 master가 커밋한다. 관련 shared Java 파일은 기존 구현이 포함된 파일 스냅샷이며 정확한 이번 추가분은 `master-integration.patch`에 별도 기록했다. 저장소의 누적 미커밋 전체를 정리하거나 clean-checkout build를 인증한 것은 아니다. 고정5worktree와 별도48시간 awake assertion은 보존한다. 원격 push는 하지 않는다.
