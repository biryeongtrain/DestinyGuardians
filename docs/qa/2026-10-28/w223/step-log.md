# W223 단계 기록

- 직전 goal turn은 정책 재확인으로 no progress. 이번 배치는 실제 제품 결함 월도 팔 방향/standalone 무기 HUD를 수정한다.
- 새 원본 Blender 평가: scripts disabled, 별도 background scene, shoulder/elbow/wrist/weapon61 poses, prior-cache error0, source unchanged. 원본 체인 sheet를 master가 직접 확인했다.
- 고정 슬롯1/4를 재생성 없이 갱신. 각19628 changed files,218816-file baseline. 미커밋/untracked 통합 상태 포함, main 변경 없음.
- Iron Grip은 사용자 DDC Weapon Perks128행 +20Stability/-20Reload를 확인했지만, 현재 exact catalog hash들의 소켓에 기본/강화형 모두 없으므로 미등록. 새로운 무기에 임의 부여하지 않는다.
- 슬롯1을 standalone HUD cleanup, 슬롯4를 source-world-axis preserving glaive registration으로 배정. Worker writes are disjoint; master owns integration/build/Vision/commit.

- HUD 초기 cleanup 가설을 실제 PREFIX와 대조하여 기각: reticle/scope는 destiny:hud_ 바깥이므로 현행 cleanup에 지워지지 않는다. 불필요한 변경 취소. 슬롯1은 미구현인 실제 피해/처치 확인 HUD로 재배정한다.

- Master 통합: 실제 HP+absorption 감소 확인 직후 apply transaction당 cue1회 연결, CombatHud update/remove 수명 연결. Debug status는 읽기 전용 hitHud 노드 목록만 추가한다.

- WeaponRuntime 공통 경로를 쓰지 않는 Dragonfly/Firefly 폭발도 기존 실제 피해/처치 결과를 관측하여 같은 cue API로 연결. 재귀 피해/퍽 credit/오디오에는 변경 없음. 해당 2차 폭발의 실화면 검증은 별도 표시한다.

- Hands pass1 생성 완료(196.79s), 월도 팔 포함 assembled694. HUD6 assets 재현/transparent center 확인. 서버 종료 clearAll 연결 및 read-only glyph model 진단 추가. targeted23+assemble 진행 중.

- Build pass1 targeted23/23 + assemble 통과. Artifact ca43d20ea59582e7a1bf8046f5d78cb3292184cde5c34481fb441906433122fc (173994419 bytes). CU는 일반 Finder desktop/unlocked를 관측했고 입력하지 않음. FIRST coordinator1800s bounded awake wrapper로 시작, 별도48h PID79904 보존.

- FIRST 기동 중 격리 서버 whitelist가 비어 offline QA 접속 거절. 이름 명령은 소문자 profile을 만들어 정확 대소문자 offline UUID8583dfe4-45e8-3bbb-8779-d6922dadf018을 격리 whitelist에 추가/reload. 일반 프로필·외부 서버 접근 설정 변경 없음. 아직 native 입력 없음.

- CU surfaces에는 Java app이 없어 직접 버튼 복구를 수행하지 않았다. 접속 거절 원인 수정 뒤 owned coordinator에 SIGINT, finally server/client exit0 확인. 입력 전 실패 기록 보존 후 새 bounded retry runtime으로 재접속한다. 무작정 반복 기동이 아니라 확인된 whitelist 수정의 재검증이다.

- FIRST: 월도 fire/reload/ADS 및 hit/protected/miss 6시퀀스 완료·중립 확인. kill은 실제처치·redmodel·5PNG 확보 후 physical_user_input으로 취소, expiry oracle 없음. 전체7통과로 세지 않음. 담당 동일2worker에 실제 이미지와 정확 실패/원본 한계를 전달했다. SECOND는 새로운 독립 fixture로 7개 재검수한다.

- 동일2worker가 FIRST 이미지를 직접 검수. 양쪽 제품 수정을 추가할 근거 없음으로 반환했다. 월도 profile의 원본 평가/캐시/sheet/제안 경로만 저장소 내부 증거로 교체하고 한계 기록 보강. generator125 outputs 중124pack파일은 byte-identical, art manifest만 갱신. Hands는 input provenance map의 재현성을 위해 pass2생성 중이며 제품 output digest가 동일하면 동일 jar로 SECOND검수한다. 불필요한 JUnit 반복은 하지 않는다.

- Hands pass2 182.99s. 125377 output digest map이 pass1과 모두 동일, 입력 profile hash만 출처 경로 갱신을 반영. 동일 tested jar를 SECOND에 사용하며 재빌드/JUnit 반복하지 않음. provenance 변경 후 source registration 계약의 짧은 Python2/2도 통과했다.

- SECOND7/7 native 완료(90PNGs), 전부 release/native중립. actualHP100→93/무적100/각1발 지급·소모/kill표시·expiry 확인. Master가 실제 review/reload/HUD sheet와 rawpostreload/hit01을 검수: hip/ADS중앙 가림 해소, 하단팔 가림 보존. 흰cue는 SECOND에서 선명하게 분리되지 않아 FIRST실화면과 SECOND서버 증거를 구분, redkill은 SECOND에서도 보임. 서버/client ownedwrappers0, ports8102/25611free, PID79904유지. 동일 worker에게 SECOND문서 마감을 요청했다.

- SECOND동일worker 문서 반환을 해시 검수/통합, 둘 다 종료. 최초 doc통합 시 ledger 파일명 정렬이 최신feedback을 이전hash로 덮는 도구 오류로 차단됐으며(main write전), 명시적 단계순으로 고쳐 원래hash검사를 유지한 채 통합했다. 소유delta+metadata를 recoveryZIP에 보관하고 slots1/4를 idle-needs-refresh로 전환,5worktree는 유지. 수락파일 목록·index를 검수해 자동커밋한다.

- 커밋 범위 검사: hands 출력은664개 추가/변경뿐 아니라 generator가 더 이상 참조되지 않는 기존 pose536/framing118(총654개 tracked)을 제거한 것도 확인. 해당 삭제도 생성 그래프의 이번 delta로 명시해 커밋한다. fixed worktree/외부 원본 삭제와 무관하다.
