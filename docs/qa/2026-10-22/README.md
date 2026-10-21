# 헌터 QA — 2026-10-22

기본 헌터 구현의 자동 검증과 실제 프레임버퍼 증거입니다.

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
