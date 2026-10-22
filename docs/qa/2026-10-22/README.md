# 헌터 QA — 2026-10-22

기본 헌터 구현의 자동 검증과 실제 프레임버퍼 증거입니다.

## 최신 H14 — VFX 디테일 개정

굵은 분절 고리/막대를 분기 전격·테이퍼 곡선 화염·나선/필라멘트로 재제작했고, 연막은 카메라를 향하는 billow 카드로 바꿨습니다.
아틀라스32→128, 렌더본4~8개 유지. [디테일·비용·제약](../../design/17_헌터_VFX_디테일_개정.md).

- 최종 **GameTest52/52·JUnit10/10, build 성공(13:51:12 KST)**. [실행 로그](vfx-h14-build-gametest.txt) · [에셋 JUnit](vfx-h14-junit-TEST-kim.biryeong.destiny.HunterVfxAssetTest.xml)
- [H13/H14 전후](vfx_h14_before_after.jpg): 같은 Blockbench 카메라/배율/클립 시각. **게임 전후 실측 캡처가 아님**. Smoke 빌보드는 편집기에서 적용되지 않음.
- [실제 시전6종 모음](vfx_h14_overview.jpg), 정상20TPS/1708×956 PNG. Arc 근접은 뒤3인칭, 나머지는1인칭, HUD 유지.
- 수류탄 PNG: [Arc](vfx_h14_ability_arc.png) · [Solar](vfx_h14_ability_solar.png) · [Vortex](vfx_h14_ability_vortex.png)
- 근접 PNG: [연속 타격](vfx_h14_ability_strike.png) · [작은 단검 충돌](vfx_h14_ability_knife.png) · [연막](vfx_h14_ability_smoke.png)
- 움직임 WebP: [Arc](vfx_h14_ability_arc.webp) · [Solar](vfx_h14_ability_solar.webp) · [Vortex](vfx_h14_ability_vortex.webp) · [타격](vfx_h14_ability_strike.webp) · [단검](vfx_h14_ability_knife.webp) · [연막](vfx_h14_ability_smoke.webp)
- [연막 정면](vfx_h14_smoke_front.png) · [90도 측면](vfx_h14_smoke_side.png): 같은 실제 시전 중 카메라 이동, 다인 검증 아님.
- [실제 캡처 간격](vfx-h14-frame-captures.json), WebP/모음은 검토용 축소본. 고정60FPS 영상이나 원작 타이밍 실측이 아님.
- [실제 출력 비용](vfx-h14-generated-pack-budget.json), [연막 미출력 메시 제거 전후 렌더 byte 동등성](vfx-h14-smoke-render-equivalence.json).
- [최종 조건/해시](vfx-h14-validation.json) · [정리 후 화면](vfx_h14_cleanup.png) · [서버](vfx-h14-runtime-server.txt) · [클라이언트](vfx-h14-vision-client.txt)

H143종은 첫 JVM 화면, 연막 최종 빌보드는 세 번째 JVM 화면입니다. 미출력 구체 제거 후 네 번째 서버 팩이 촬영 팩과 같은 출력임을 확인했습니다.
자연 만료 active0/정리·본인 서버 정상종료·본인 클라이언트 SIGTERM143·원래 옵션5157바이트 복구·25565/8102 비점유 확인.
원작 미확인 연막/근접 파생 효과, 카드의 평면감, 메시 상수 tint/음영은 남습니다. bloom/볼류메트릭·다인/24개 부하·밤/동굴·신규 궁극기 VFX는 미검증/범위 밖입니다.
기존 HUD/무기 particle·end_of_frame·OpenGL·오프라인 계정·팩캐시 경고는 남으며 신규 VFX 누락/백엔드 오류와 구분했습니다.

---

## 이전 VFX 개정 H13

수류탄·근접6종에 BetterModel 애니메이션 모델4종을 연결했습니다. 실제 Destiny 참고 기반 로우폴리 재해석이며 원본 게임 에셋이나 블룸 셰이더를 이식한 것은 아닙니다.
[레퍼런스](../../design/15_헌터_VFX_레퍼런스.md) · [구현·한계](../../design/16_헌터_VFX_구현.md).

- 최종 **GameTest52/52·JUnit10/10**, build 성공(13:15:58KST). [실행 로그](vfx-h13-build-gametest.txt)
- [6종 실제 시전 모음](vfx_h13_overview.jpg), 정상20TPS/1708×956 원본 PNG 육안 확인.
- 수류탄: [Arc](vfx_h13_ability_arc.png) · [Solar](vfx_h13_ability_solar.png) · [Vortex](vfx_h13_ability_vortex.png)
- 근접: [연속 타격3인칭](vfx_h13_ability_strike.png) · [단검 작은 충돌](vfx_h13_ability_knife.png) · [연막(잠정)](vfx_h13_ability_smoke.png)
- 움직임 WebP: [Arc](vfx_h13_ability_arc.webp) · [Solar](vfx_h13_ability_solar.webp) · [Vortex](vfx_h13_ability_vortex.webp) · [타격](vfx_h13_ability_strike.webp) · [단검](vfx_h13_ability_knife.webp) · [연막](vfx_h13_ability_smoke.webp)
- WebP/모음은 실제 PNG의 검토용 축소본. [실제 캡처 간격](vfx-h13-frame-captures.json); 고정FPS 동영상이나 원작 시간 실측이 아님.
- [정리 후 실제 화면](vfx_h13_cleanup.png) · [조건/해시/미검증](vfx-h13-validation.json) · [출처/해시](vfx-h13-reference-evidence.json)
- [VFX JUnit](vfx-h13-junit-TEST-kim.biryeong.destiny.HunterVfxAssetTest.xml) · [서버](vfx-h13-runtime-server.txt) · [비전 클라이언트](vfx-h13-vision-client.txt)

자연 만료 active0·속성 변경1→0 확인. 본인 서버 정상 종료/클라이언트SIGTERM(exit143)/원본 옵션 바이트 복구.
새 VFX 누락은 없으나 기존 HUD/장비 particle 참조·end_of_frame·OpenGL·오프라인 계정/팩캐시 경고는 남습니다.
연막/근접 원작 충실도, 다인/48블록 경계/전체24개 부하·밤/동굴·신규 궁극기 VFX는 미검증 또는 후속 범위입니다.

---

## 이전 실제 디자인 교정 H12

H11의 일반 SF 참고작이 아니라, Bungie 표기 헌터 칼 도면/게임 스크린샷과 Flashbang 게임 캡처를 대조해
**나이프160큐브·섬광탄56큐브를 재제작**했습니다. 원본 게임 메시를 획득/재배포한 것이 아닙니다.
소이·소용돌이·연막은 원작 껍질 근거 미확보로 H11 잠정 모델 유지. [출처·한계](../../design/14_헌터_능력_모델.md).

- 새 자동 실행 **GameTest40/40, JUnit8/8**, build 성공(06:31:35KST).
- [실제 게임 비교](props_h12_ingame_gallery.png): 확대 scale2.5, 일반20TPS. 칼의 구멍3개/갈고리 홈/비대칭 실루엣 확인.
- Blockbench: [나이프](props_h12_blockbench_solar_knife.png) · [상면](props_h12_blockbench_solar_knife_top.png) · [섬광탄](props_h12_blockbench_arc_flashbang.png)
- 실제 투척: [섬광탄](props_h12_flight_arc_flashbang.png) · [나이프](props_h12_flight_solar_knife.png)
- [참고 이미지 출처·해시](props-h12-reference-evidence.json) (원본 이미지는 배포물 미포함)
- [새 빌드](props-h12-build-gametest.txt) · [소품JUnit](props-h12-junit-TEST-kim.biryeong.destiny.HunterPropAssetTest.xml) · [기존JUnit](props-h12-junit-TEST-kim.biryeong.destiny.HunterAssetTest.xml)
- [서버](props-h12-runtime-server.txt) · [비전 클라이언트](props-h12-vision-client.txt) · [조건·해시](props-h12-validation.json)

1708×956 실제 프레임버퍼 PNG를 육안 확인. 비행 캡처만1TPS, 원래 모델 스케일 수류탄0.5/칼0.6.
나이프 관찰 카메라는 y-59.4/pitch18로 옮겨 얇은 칼날 면을 확인했습니다. 비행 방향/물리 변경 없음.
일반속도 플레이감·다인/최대 투사체 부하·다른GUI배율 검증은 아님. 20TPS 복구, 자신의 비교 엔티티2개 제거,
원래 스폰/서브클래스 복구 뒤 자신의 서버와 클라이언트 종료. 클라이언트exit143은 의도된SIGTERM 정리.
vsync/포커스 일시정지 옵션 원본 바이트 복구. 새 소품 누락 경고는 없음; 기존 경고는 로그 참조.

---

## 이전 능력 모델 개정 H11

Blockbench MCP로 수류탄3종·태양 단검·공허 연막탄을 새로 제작해 투사체에 연결했습니다.
참고작의 작가·라이선스와 조형 재해석은 [모델 명세](../../design/14_헌터_능력_모델.md)에 기록했습니다.
Arc 연속 타격은 맨손을 유지합니다.

- **최신 검증:** GameTest **40/40**, JUnit **6/6**, build 성공 (05:49:26 KST).
- [Blockbench 모델 5종](props_blockbench_overview.png) · [게임 내 5종 비교](props_ingame_gallery.png)
- 실제 투척: [Arc 섬광](props_flight_arc_flashbang.png) · [Solar 소이](props_flight_solar_incendiary.png) ·
  [Void 소용돌이](props_flight_void_vortex.png) · [Solar 단검](props_flight_solar_knife.png) · [Void 연막](props_flight_void_smoke_bomb.png)
- [자동 빌드](props-build-gametest.txt) · [GameTest 서버](props-gametest-server.txt)
- [기존 에셋 JUnit](props-junit-TEST-kim.biryeong.destiny.HunterAssetTest.xml) · [신규 소품 JUnit](props-junit-TEST-kim.biryeong.destiny.HunterPropAssetTest.xml)
- [실제 서버](props-runtime-server.txt) · [비전 클라이언트](props-vision-client.txt) · [해시/조건](props-validation.json)

정적 비교용 item_display는 **scale=2**입니다. 실제 투척은 기존 크기(수류탄/연막 0.5, 단검 0.6) 그대로이며,
빠른 소품을 잡기 위해 해당 캡처만 서버를 임시 **1TPS**로 낮췄습니다. 성능 측정이나 일반 속도 플레이 영상이 아닙니다.
관찰자는 발사 후 콘솔 tp로 옆으로 이동했고, 기존 속도/중력/피해는 변경하지 않았습니다.
직전 시전의 잔여 파티클이 일부 비행 PNG에 같이 보입니다. 시험 후 20TPS 복구, 비교용 엔티티 제거, 클라이언트 옵션 복구.
실제 PNG는 1708×956. 타 해상도·Vulkan·2인 관찰/애니메이션 연결은 이번에 재검증하지 않았습니다.

### 비행 모델 재현 예시

서버 콘솔, 로컬 테스트 월드에서만 실행:

```text
tick rate 1
guardian subclass solar MinigameQA
guardian reset MinigameQA
tp MinigameQA 100.5 -60 0.5 0 0
guardian action melee MinigameQA
tp MinigameQA 102.5 -60 2.7 90 0
```

두 번째 tp의 로그가 나온 뒤 약 0.8~1.2초에 비전 `/screenshot`을 캡처합니다.
검사 후 반드시 `tick rate 20`으로 복구합니다. 수류탄은 action=grenade, 관찰 z=1.6으로 변경.

---

## 이전 HUD 크기 조정 H10

좌하단 능력·궁극기 HUD를 약 20% 확대했습니다. 타일 53px / 궁극기 80px,
체력 바 두께 7px. 간격도 같이 늘려 기존 여백과 비중첩 배치를 유지합니다.

- **H10 검증:** GameTest 36/36, JUnit 4/4, build 성공.
- [확대 정상 화면](hud_destiny_enlarged.png) · [위험 체력·흡수·수류탄 소모](hud_destiny_enlarged_critical.png)
- [자동 빌드 로그](hud-enlarged-build-gametest.txt) · [JUnit XML](hud-enlarged-junit-results.xml)
- [실제 서버](hud-enlarged-runtime-server.txt) · [클라이언트](hud-enlarged-vision-client.txt)
- [메타데이터/해시](hud-enlarged-validation.json)

실제 1708×956 프레임버퍼를 육안 확인. 다른 해상도·GUI 배율은 재검증하지 않았습니다.
이전 H9의 작은 크기 화면과 증거는 아래에 보존합니다.

## 이전 HUD 개정 H9

사용자 피드백으로 체력 하트를 숨기고 데스티니형 상단 체력 바·좌하단 아이콘 HUD로 변경했습니다.
아래 구판 H1~H8 스크린샷의 텍스트 HUD는 현재 화면이 아닙니다.

- **H9 검증:** GameTest 36/36, JUnit 4/4, build 성공.
- [H9 정상 화면](hud_destiny_full.png) · [50% 체력](hud_destiny_damaged.png)
- [위험 체력·실제 흡수·수류탄 소모](hud_destiny_critical_absorption.png) · [Solar 궁극기 중](hud_destiny_solar_active.png)
- [자동 빌드 로그](hud-build-gametest.txt) · [JUnit XML](hud-junit-results.xml)
- [실제 서버](hud-runtime-server.txt) · [실제 클라이언트](hud-vision-client.txt) · [메타데이터/해시](hud-validation.json)

생존 모드에서 체력20→10→4, 흡수 효과4HP, 회복 및 흡수 제거를 실제 화면으로 확인했습니다.
필수 팩의 하트 44종은 투명하며, 직업 none도 대체 체력 바를 표시합니다.
원작의 전투 UI 구성을 따른 직접 제작 아트입니다. 핫바/배고픔/방어구/경험치는 아직 유지합니다.
로그의 `particle` 미지정 경고는 화면용 평면 아이템에서 사용하지 않는 입자 슬롯입니다.
마젠타를 만들었던 실제 HUD 텍스처 아틀라스 문제는 표준 item/ 경로로 수정 후 재캡처했습니다.

---

아래 결과는 이전 H1~H8 체크포인트이며 당시 JAR 해시/화면을 보존한 기록입니다.

## 결과

- Fabric GameTest **33/33 필수 통과**. 최종 재실행 04:57:44 KST.
- JUnit **2/2 통과** (`test --rerun`으로 별도 재실행, XML에 실행 시각 기록).
- `runGameTest build` **BUILD SUCCESSFUL**. 개발 서버 종료 후 실행.
- 실제 PNG **11장** 저장·육안 확인. 카메라 yaw=0, pitch=15, HUD 켜짐.
- 환경: 26.3 / Java25 / Loader0.20.1 / API0.164.0 / Polymer0.18.4 / BetterModel3.5.1 / minigame-lib2.0.0.

## 증거 파일

| 파일 | 내용 |
|---|---|
| [자동 빌드·GameTest](hunter-build-gametest.txt) | Gradle 전체 콘솔, 33개 통과·build 성공 |
| [GameTest 서버](hunter-gametest-server.txt) | 최종 자동 테스트 서버 로그 |
| [JUnit 실행](hunter-junit.txt) · [결과 XML](hunter-junit-results.xml) | 리소스 테스트 강제 재실행·2개 통과 |
| [실제 서버](hunter-runtime-server.txt) | 접속·팩 생성·능력 시전·정상 종료 |
| [비전 클라이언트](hunter-vision-client.txt) | 리소스팩·렌더러·알려진 경고 |
| [검증 메타데이터](hunter-validation.json) | 수량·JAR 및 PNG SHA-256·미검증 목록 |

로그의 ANSI 색상 코드만 제거했습니다. 개발 모드 오프라인 계정·로컬 경로가 포함되어 있습니다.

## 프레임버퍼

| 화면 | 이미지 |
|---|---|
| 대기 HUD | [hunter_hud_idle.png](hunter_hud_idle.png) |
| Arc 자세·지팡이·청색 화면 | [hunter_arc_model_post.png](hunter_arc_model_post.png) |
| Solar 자세·황금 총·황색 화면 | [hunter_solar_model_post.png](hunter_solar_model_post.png) |
| Void 자세·활·보라색 화면 | [hunter_void_model_post.png](hunter_void_model_post.png) |
| 구르기 | [hunter_roll.png](hunter_roll.png) |
| 1인칭 limb 숨김·손 HUD | [hunter_first_person.png](hunter_first_person.png) |
| Arc 섬광 착탄 | [hunter_arc_flash.png](hunter_arc_flash.png) |
| Solar 소이 착탄 | [hunter_solar_incendiary.png](hunter_solar_incendiary.png) |
| Void 소용돌이 | [hunter_void_vortex.png](hunter_void_vortex.png) |
| Void 연막 | [hunter_void_smoke.png](hunter_void_smoke.png) |
| Void 닻 발사 후 | [hunter_void_tether.png](hunter_void_tether.png) |

기존 `p01_*`, `w1-*` PNG는 이전 PoC이며 이번 헌터 최종 증거 11장에 포함하지 않습니다.
수치·피해·상태 지속의 정확성은 정지 이미지가 아니라 GameTest로 검사했습니다.

## 자동 검증 재현

Java25 및 README에 적힌 소스/모드 의존성 준비 후 저장소 루트에서:

```sh
rtk proxy ./gradlew runGameTest build --console=plain
rtk proxy ./gradlew test --rerun --console=plain
rtk proxy /Users/qf/.codex/skills/minecraft-testing/scripts/validate-test-layout.sh --root .
```

레이아웃 검사: 통과, 경고 1개. 구형 스킬 검사기는 `src/gametest`의 26.3 `.snbt` fixture를 감지하지 못합니다.
실제 33개 GameTest는 Fabric runner가 등록·실행했습니다.

## 실제 화면 재현

개발 서버 `runServer`와 별도 Copper Golem Vision 26.3을 사용합니다.
개발 서버 실행 중 컴파일하지 말고, 변경 시 서버를 종료하고 빌드한 다음 재기동하세요.
테스트 서버는 오프라인 모드의 격리된 로컬 서버였으며 운영 서버 설정으로 권장하지 않습니다.

```sh
rtk proxy /Users/qf/.codex/skills/copper-golem-vision-client-fabric-26-3/scripts/vision_client.sh run 127.0.0.1:25565
rtk curl -fsS http://127.0.0.1:8102/state
rtk curl -fsS 'http://127.0.0.1:8102/perspective?mode=third_front'
```

서버 콘솔 (아래는 콘솔 명령이며 셸 명령이 아님):

```text
tp MinigameQA 0 -60 0 0 15
guardian class hunter MinigameQA
guardian subclass solar MinigameQA
guardian reset MinigameQA
destiny debug owner-view MinigameQA third
guardian super 100 MinigameQA
guardian action super MinigameQA
```

1.5초 뒤 `/screenshot` PNG를 받습니다. Arc·Void는 subclass만 변경합니다.
`subclass` 전환은 시전 세션/작업을 정리하지만 쿨타임은 초기화하지 않으므로 QA는 `reset`을 명시합니다.
공격은 `guardian action primary`, 수류탄/근접/회피는 각각 `grenade`, `melee`, `class_ability`.
구르기는 0.67초 정도이므로 시전 직후 캡처합니다.
1인칭 검사 시 HTTP perspective=first 및 서버 owner-view=first를 함께 설정합니다.
카메라 HTTP API는 실제 공격·이동 입력을 만들지 않습니다.

**owner-view는 시점별 서버 분기 시뮬레이션일 뿐 GCB 통신 증거가 아닙니다.**
바닐라는 시점 정보를 서버에 보내지 않으므로 본인 limb를 숨기는 정책입니다.
인증 스킨·GCB 실클라이언트·2인 관찰자·지연·Vulkan·청음은 미검증입니다.

알려진 경고: 오프라인 401/Realms 인증 오류, OpenGL 미사용 vertex output,
`minecraft:end_of_frame` 없음 경고. 명시적 destiny 궁극기 체인과 모델은 실제 화면에서 표시되었습니다.
소스 구현은 돌아가는 프로토타입이며 일반 총기·스킬 트리·최종 방어구 아트는 별도 범위입니다.
