# W238 PROFILE arm selector — worker 반환

작업본: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`

소유 파일은 다음 세 개뿐이다. Main checkout, shader/runtime/pack generation, 원본 asset, commit/push는 수정·실행하지 않았다.

- `src/main/java/kim/biryeong/destiny/weapon/ProfileArmGraph.java`
- `src/test/java/kim/biryeong/destiny/weapon/ProfileArmGraphTest.java`
- 이 문서

## API와 책임

`ProfileArmGraph.armsOnly(JsonObject source)`는 item definition의 **`model` 객체**를 받는다. 전체 item definition wrapper를 넘기지 않는다. `minecraft:model`의 `model` 값이 `destiny:skin_arm_w204/poses/`로 시작하면 leaf를 보존하고 `tints`를 복사하지 않는다. 다른 model과 명시적 empty는 `minecraft:empty`로 투영한다. 반환 JSON은 원본과 가변 객체를 공유하지 않는다.

지원하는 selector는 composite, select(display_context 또는 CMD strings[0]), condition(CMD flags[0,1,8,9]), range_dispatch(CMD floats[1..6])다. 생략 가능한 CMD index의 native 기본값은 0이다. 따라서 condition/string select의 index 생략은 지원하지만 float range의 index 생략은 지원 범위 밖인 0이므로 실패한다.

정규화는 empty composite 제거, 단일 child composite 제거, 중첩 composite 평탄화, 동일 condition 분기 제거, fallback과 같은 select case 제거, 같은 결과의 select case 병합, 인접한 같은 range 결과 제거를 수행한다. composite의 출력 순서와 중복 leaf는 유지한다. `transformation`은 보존하며 상위 transformation을 잃는 selector/composite 제거는 하지 않는다. matrix 해석·변환은 수행하지 않는다.

`ProfileArmGraph.select(JsonObject graph, CustomModelData data, boolean slim, boolean leftHand)`는 **컴파일된 graph**를 평가하여 불변 `List<String>`을 반환한다. 원본 JSON과 CMD 목록을 변경하지 않는다. missing CMD는 `null` 또는 `CustomModelData.EMPTY`로 전달할 수 있다.

- flags[8]은 항상 true, flags[9]는 `slim`으로 가상 override한다. 물리 CMD를 변경하지 않는다.
- flags[0,1]은 CMD를 사용하고 missing은 false다.
- strings[0] missing은 null이므로 빈 문자열 case와 구분하여 fallback으로 간다.
- display_context는 `leftHand`에 따라 `firstperson_lefthand` 또는 `firstperson_righthand`다. LEFT는 selector 문맥 선택만 수행한다.
- 일반 실제 route는 최대 네 pose를 반환한다. 임의 composite를 4개로 잘라내는 동작은 없다.
- `armsOnly`는 선택되지 않을 분기도 전부 검증한다. `select`는 컴파일 결과를 전제로 선택 경로를 평가하며 매 tick 전체 원본을 재컴파일하지 않는다.

## native range 조사

현재 26.3 client JAR(`/Users/qf/.gradle/caches/fabric-loom/26.3/minecraft-client.jar`)를 `javap -p -c`로 읽어 다음을 확인했다. 게임 프로세스를 실행하지 않았다.

1. `properties.numeric.CustomModelDataProperty.get`: component 또는 해당 float 누락이면 0f.
2. `RangeSelectItemModel$Unbaked` codec: scale은 `Codec.FLOAT`, 기본값 1f.
3. `RangeSelectItemModel.update`: **float 곱셈 후** `Float.isNaN` 검사. NaN이면 검색하지 않고 fallback.
4. `lastIndexLessOrEqual`: 16개 미만은 첫 `threshold > value` 직전 entry, 16개 이상은 `Arrays.binarySearch(float[], float)`의 exact/insertion-point floor.
5. `Unbaked.bake`는 원래 threshold를 정렬하지만, 이 worker는 사용자 지정 정렬 불변식에 따라 이미 정렬된 입력만 받으며 역순·동일 float threshold를 자동 수정하지 않고 예외를 낸다.

scale의 NaN/±∞도 float 연산을 그대로 따른다. 예를 들어 `∞ * 0`과 `0 * ∞`는 NaN이므로 fallback이다. finite 값 overflow, ±∞ CMD 값, 음수 scale도 별도 clamp하지 않는다. threshold는 finite 및 `Float.compare` 기준 strictly increasing을 강제하고, JSON number가 float로 변환되며 겹치는 경우도 실패한다.

**signed zero:** native의 두 검색 방식은 `-0.0`과 threshold `+0.0`에서 결과가 다를 수 있다. 동일 range 결과를 제거하면서 16개 경계를 넘을 때 zero threshold가 있으면 기존 entry 수를 유지하여 그 차이를 보존한다. 모두 fallback과 같은 경우에는 NaN을 포함해 어느 입력도 결과가 같으므로 전체 selector를 제거한다.

native fallback이 생략되면 클라이언트는 missing model 진단을 사용한다. 이 투영은 팔 pose만 다루므로 해당 경로는 empty다. 무기용 fallback과 기타 weapon leaf도 같은 이유로 empty가 된다.

미지원 type/property/index/field, 잘못된 JSON shape, select 중복 label, 알 수 없는 display context, threshold 정렬 불변식 위반은 `IllegalArgumentException`으로 실패한다.

## targeted 검증

적용 skill: `/Users/qf/.codex/skills/minecraft-testing/SKILL.md`의 순수 JUnit 방식. registry Bootstrap, client/server 실행, Vision/CU, fixture 쓰기를 사용하지 않았다.

```sh
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home \
  ./gradlew test --tests kim.biryeong.destiny.weapon.ProfileArmGraphTest \
  -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow/libs/gcb-server \
  --offline --no-daemon --max-workers=2
```

`compileJava` 1차 성공. NaN/∞ scale 보강 후 같은 targeted 명령의 최종 실행도 **BUILD SUCCESSFUL (32s), JUnit 12개 성공, 실패/오류/skip 0**이다. 결과 파일은 `build/test-results/test/TEST-kim.biryeong.destiny.weapon.ProfileArmGraphTest.xml`이다.

검증 내용:

- 작은 fixture의 projection/tint 제거, nested/empty composite, 중복·순서, graph/CMD read-only, 불변 반환 목록.
- condition 기본값, flags[8,9] 물리값과 다른 가상 override, flags[0,1], string scalar/array/missing/빈 문자열/fallback, 좌우 문맥.
- floats[1..6], 기본 scale, 음수·0·NaN·∞ scale, missing, NaN, ±∞, floor exact/nextDown/nextUp.
- 실제 native private floor 메서드를 reflection 호출하여 2/15/16/61 entry와 signed zero를 비교.
- 실제 원본 route 그래프를 별도 oracle로 평가하여 컴파일 결과와 비교. oracle에는 flags[8,9]를 물리 CMD로 넣으며 production override를 재사용하지 않는다.
- Pyroclastic Flow의 고유 61 threshold 확인. frame 0/1/2/15/16/29/30/59/60의 nextDown/exact/nextUp, classic/slim, LEFT/RIGHT를 비교하고 NaN fallback도 확인.
- 미지원 selector/property/index/field, 선택되지 않는 미지원 branch, 중복 case, 역순/중복/nonfinite/float 반올림 충돌 threshold의 failfast.

대표 route compact JSON 문자 수(같은 Gson `toString()` 기준; 패키징 용량이나 client render 성능 수치가 아님):

| 실제 wrapper route | 원본 | armsOnly |
| --- | ---: | ---: |
| `weapon/ace_of_spades` | 603,855 | 15,285 |
| `weapon_reload_w221_pyroclastic_flow/pyroclastic_flow` | 8,544,500 | 135,656 |
| `weapon_reload_w222_biting_winds/biting_winds` | 8,941,519 | 154,574 |
| `weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1` | 23,794,886 | 576,835 |

각 route에서 hip/ads/inspect/scope/unknown × classic/slim × LEFT/RIGHT를 확인했고 결과는 모두 1..4개였다. 전체 wrapper 전수 평가나 전체 61프레임 전수 실화면 검증은 수행하지 않았다.

## 소유권·drift·통합

소유 두 Java 파일을 제외한 `src/main/java`, `src/test/java`, `src/gametest/java`, `libs/gcb-server/src`, `scripts` 및 `build.gradle`, `settings.gradle`, `gradle.properties`, `AGENTS.md`의 **1,736파일 SHA-256**을 작업 시작 후/반환 전 비교했다. 추가·삭제·변경 drift는 0이다. 이 검사는 source/config 범위이며 build 산출물, 전체 asset/QA 바이너리의 무변경 전수 인증을 뜻하지 않는다. 테스트에서 읽은 네 원본 wrapper는 읽기 전용으로 사용했다.

Master 제공 `/private/tmp/destiny-w238/worker-first-sha.txt`의 1차 class snapshot SHA와 최종 class SHA는 현재 동일하다:

```text
0a8ab3c93362a0f8f7d722077a3732650d60aa0286720fcd6510b9fbe5c4a636  ProfileArmGraph.java
072fdc34f3be0fb7906e4454bfdebd90ceb6edd56843f37928b23e5e85f9faaa  ProfileArmGraphTest.java
```

따라서 현재 snapshot 대비 class 추가 수정은 없고, 최종 반환에는 test와 이 문서를 함께 검토하면 된다. Master의 main 파일은 worker가 복사하거나 수정하지 않았다.

## 한계·다음 검수

shader marker, PROFILE 렌더링, 실제 four display lifetime, exact display matrix, skin slim/classic 매핑, pack에서 pose 실물 제거, 서버/runtime 연결은 master 소유이며 이 JUnit으로 인증하지 않는다. 아래 master 제공 PNG를 읽어 hip/ADS/F5 settled 정지 화면을 검토했다. 실제 장전 시퀀스와 통합 후 2차 Vision 전체 수락은 미수행이다.

## R2 실제 PNG 리뷰 — 2026-10-29

Worker는 아래 PNG를 실제 열고 비교했다. 화면 조작·게임 입력·server/client 실행은 하지 않았다. 모든 경로의 공통 부모는 `/private/tmp/destiny-w235/qa/frames/`다.

- 새 hip: `w238-r2-ace-hip.png`
- 새 ADS: `w238-r2-ace-ads-fire-sample-06.png`
- 새 F5 settled: `w238-r2-ace-f5-settled.png`
- 최종 비교 기준 ADS: `w236-ace-anchor-sample-04.png` (ADS route라는 master 메타 확인을 채택)
- 최종 비교 기준 hip: `w236-ace-return-anchor.png`
- 최초 확인한 `danmo-official-ace-hip.png`는 파지부가 OneConfig popup에 가려져 있다. `baseline-ace-ads-sample-06.png`는 pixel hands 준비 전일 수 있다는 master 정정에 따라 팔 회귀 판정 근거에서 제외했다.

### 판정과 구체적인 master 후속 사항

**ADS 피부 돌출은 W236 기준에 없던 시각 차이이며, 정상 리그 접촉으로 수락하지 않는다.** 새 ADS 화면의 약 x=940..1195, y=765..950에서 피부 면이 오른쪽 위로 뻗는다. 총/가늠쇠 자체의 중앙 배치와 실루엣은 대체로 유지되므로 총 전체 이동보다 팔 표면의 clipping 문제를 먼저 확인할 근거가 있다. 정지 화면만으로 그 면의 실제 left/right/upper marker를 확정하지는 못한다.

유력 원인: `src/main/resources/destiny/profile_view/main.vsh:8..10`의 `w=max(-p.z,0.001)` 및 `p.z >= -0.025` 정점을 `vec4(2,2,2,1)`로 치환하는 처리. 이 방식은 triangle 전체를 버리는 것이 아니다. 한 head face의 일부 정점만 경계 뒤에 있으면 남은 정점과 치환점 사이에 새 삼각형이 생겨 화면 오른쪽 위 쪽으로 피부 면이 뻗을 수 있다. 픽셀별 작은 면에서 한 장의 큰 head quad로 바뀌면서 같은 bbox라도 이 차이가 커질 수 있다.

읽기 전용 source 계산에서도 native grip/ADS/classic의 lower arm 8개 bbox corner 중 right 4개, left 3개가 해당 치환 조건에 걸렸다. Source display matrix와 공통 hand translation을 적용한 z 범위는 각각 약 `[-0.30703, +0.20610]`, `[-0.30331, +0.10671]`이다. 이는 정적 native grip 분기의 진단이며 실제 캡처 tick의 marker/동적 recoil 값을 수집한 것은 아니다. 따라서 clipping이 강한 원인 후보지만 실제 GPU 삼각형 추적에 의한 확정은 아니다.

Master 수정 후보는 **각 정점의 x/y와 signed homogeneous w를 보존하고, backend의 depth 범위에 맞는 near-plane clipping을 쓰는 것**이다. `if`만 삭제하고 `w=max(...)`를 남기면 뒤쪽 정점도 양의 w가 되어 올바른 동차 clipping이 되지 않는다. 같은 처리 패턴이 `main.item.vsh`에도 있으므로 두 shader를 함께 검토해야 한다. Worker는 shader/runtime을 수정하지 않았다. 현재 자료에서 selector/pose ID를 바꿔 해결할 근거는 없다.

**Cap 위치 회귀는 찾지 못했다.** 원본 W204 classic pixelmesh를 읽어 lower는 `up` y=9 cap 16면, upper는 `down` y=0.5 cap 16면만 유지함을 확인했다. Native head의 y=-8..0을 현재 변환에 넣으면 shader가 유지하는 lower head-down은 y=9, upper head-up은 y=0.5에 대응하여 원본 유지 면과 일치한다. Master가 확인한 x/z=6.8..9.2, lower y=1.5..9, upper y=0.5..8 bbox 일치 사실과 모순되지 않는다. PNG만으로 내부 cap 노출 또는 새 구멍을 확정하지 못했다.

**Texture는 결손/atlas checker/명백한 다른 신체 부위 샘플링을 발견하지 못했지만 완전 동등성을 수락하지 않는다.** R2 hip의 넓은 피부 단색 면과 W236 hip의 픽셀 명암 차이가 보인다. 촬영 광원·시간과 기존 tint 경로가 달라 색 자체를 직접 동등 비교하기 어렵고, 이 피부의 적은 무늬로 face별 회전/반전까지 판정할 수 없다. 오른쪽 대각선 돌출은 texture 주소만 바꿔 해결할 성질의 화면 외곽 변화가 아니다.

**Hip 접촉:** 새 화면에서 손과 그립 사이에 명백한 공중 간격은 보이지 않고 총 장식/슬라이드의 큰 위치 이탈도 보이지 않는다. W236 대비 피부 표면 차이는 위 한계를 유지한다. **F5 settled:** 제공된 settled PNG에서는 큰 first-person 총/팔 overlay가 사라져 있다. Immediate capture 잔류 시간과 전환 지연의 상한은 이 정지 화면으로 검증하지 않았다.

Master 전달 결과는 shader 250/250 통과, GC 후 used `2,191,489 KiB` 대 기존 `3,123,389 KiB`다. Worker의 재실행·재측정 결과로 기재하지 않는다. Compile/link 성공은 위 clipping/화면 접촉의 수락 근거를 대신하지 않는다. QA 입력 충돌로 자동조작이 중지되었다는 상황을 유지하며 장전 추가 검수는 아직 없다.

이번 리뷰 반환 delta는 이 문서뿐이다. Graph/test/compile CLI는 변경하지 않았고 Main checkout은 읽기만 했다. 추가 구현 변경 없이 현재 소유 delta와 본 리뷰를 master에게 반환한다.

## R5 최종 시각 검수

Harvey가 7종 hip/ADS와 장전3장을 직접 열어 nativecharged 복구와 총기 framing을 수락했다. Ammit/Recluse의 조준 중앙 및 hip 화면 복귀, Mindbender settled sample08 정렬, Ace 돌출 해소, Izanagi 2D스코프와 총/팔 숨김, Nezarec 손잡이의 큰 gap 부재를 확인했다. Biting Winds 팔의 큰 하단 가림은 잔여 구도이며 무결점 판정이 아니다. 장전3장의 해당 순간에서 강한 파지 이탈·늘어진 피부 면·큰 돌출은 발견되지 않았다. 연속 영상 또는 전 프레임 접촉 검증으로 확대하지 않는다.
