# W268 초보 무기군 설명

## 반환 범위

- 읽기 전용 기준: `/Users/qf/IdeaProjects/DestinyGuardians`의 현재 파일 내용. 오래된 worktree 부모 소스를 구현 근거로 사용하지 않았다.
- 반환 루트: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1/w268-delta`.
- 신규 파일: `src/main/java/kim/biryeong/destiny/inventory/WeaponHelpText.java`, `docs/qa/2026-10-30/w268/weapon-help.md`.
- 시작 시 두 소유 경로는 main에 없었고 delta는 비어 있었다. main과 기존 worktree 파일을 수정하거나 복사하지 않았다.

## 구현

1차 검수 뒤 기존 두 파일의 문구와 문서만 압축 교정했다. API와 ID 매핑, 동작 근거는 유지했다.

`WeaponHelpText.family(String id)`는 catalog의 **무기군 ID**를 받아 한국어 설명을 반환한다. 개별 무기 ID를 받는 API가 아니다. 정확히 일치하는 ID만 조회하며 null, 빈 문자열, 공백 문자열, 미등록 ID에는 같은 fallback을 반환한다.

`private static final Map<String, String>`과 `Map.ofEntries`로 매핑을 고정했다. 문자열은 불변이며 맵을 외부로 노출하지 않는다. import는 `java.util.Map`뿐이다. Minecraft, Gson, catalog 초기화, 파일 입출력에 의존하지 않는다.

최신 catalog에는 기본 63개와 경이 2개를 합쳐 무기 65개, family ID **18개**가 있다. [WeaponScreenText.family](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/inventory/WeaponScreenText.java:23)는 `grenade_launcher`와 `heavy_grenade_launcher`에 같은 “유탄 발사기” 이름을 붙여 한국어 표시 이름은 **17종**이다. 실제 ID를 누락하지 않도록 18개를 매핑하고, 두 유탄 ID에는 각 조작에 맞는 문구를 작성했다. [WeaponScreen.refresh](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/inventory/WeaponScreen.java:283)는 표시 이름이 아닌 family ID로 선택지를 구성한다.

화면 연결과 탄약 상세 표시는 master 소유다. 이 delta는 helper만 제공하며 Screen, HUD, 런타임, 프로필, 탄약 규칙, 수류탄을 변경하지 않는다. **현재 특수탄 규칙을 유지하며 2발/30발 변경을 적용하지 않았다.** 사용자 문구에는 탄창·예비탄·지급량 수치를 넣지 않았다. 경량 유탄의 “반 초”는 탄약 수량이 아니라 기존 기폭 대기 시간이다.

## 구현 근거

거리 표현은 현재 프로필과 피해 감쇠를 바탕으로 한 사용 안내다. 원작의 정확한 유효 사거리, 피해량, 처치 보장을 제시하지 않는다.

| 범위 | 확인한 main 코드 | 문구에 반영한 동작 |
|---|---|---|
| catalog·화면 | [WeaponCatalog.load](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponCatalog.java:29), [WeaponExotics.load](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponExotics.java:20), [WeaponScreen.refresh/card](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/inventory/WeaponScreen.java:283) | family ID로 조회. 화면의 탄약 상세는 기존 profile/ammo 경로가 소유 |
| 거리·발사 형태 | [WeaponProfile.forEntry](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java:57), [WeaponBallistics.Profile](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponBallistics.java:15) | 가까운 거리·중거리·먼 거리로 구분. 감쇠와 투사체 궤적을 고려하도록 안내 |
| 총기 조준·발사 | [InputRouter.onPunch](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/input/InputRouter.java:109), [WeaponAiming.toggle](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java:75), [WeaponRuntime.beginUse](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:273) | 좌클릭 조준 전환, 우클릭 발사. 기본 마우스 입력 기준 |
| 자동·점발 | [WeaponFirePolicy](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponFirePolicy.java:17), [WeaponAutoFirePolicy](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponAutoFirePolicy.java:12), [WeaponProfile.forEntry](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java:57) | 자동 소총·기관단총·추적 소총·기관총은 우클릭 유지. 점발은 사격 묶음 동안 조준. 고유 자동 사격과 접근성 설정이 있어 반자동군 전체에 새 클릭 필수를 단정하지 않음 |
| 활 | [WeaponRuntime.releaseUse](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:395), [WeaponBowDraw.shot](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponBowDraw.java:10) | 우클릭 당김 후 해제 발사. 부분 당김은 위력·속도 감소 |
| 융합·선형 융합 | [WeaponRuntime.continueUse](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:379), [WeaponRuntime.releaseUse](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:410) | 버튼 유지 중 충전 완료 발사. 발사 전 해제로 충전 취소. 선형 점발 프레임 구분 |
| 산탄 | [WeaponProfile.forEntry](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java:79), [WeaponRuntime.emit](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:853) | 조준 시 산탄 폭 감소. 정밀 납탄 프레임의 단일 탄과 머리 조준 구분 |
| 추적 소총 | [WeaponProfile.forEntry](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java:70), [WeaponRuntime.emit](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:854) | 조준 방향으로 연속 공격. 사용자가 움직이는 적을 따라 조준 |
| 경량 유탄 | [BreachGrenade.supports/release](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/BreachGrenade.java:17), [WeaponRuntime.releaseRemote](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1282) | 현재 경량 유탄은 `salvager_s_salvo`. 발사 후 버튼 유지, 대기 후 해제 기폭. `ARM_TICKS=10`을 정상 20 TPS 기준 반 초로 표현. 조기 해제는 기폭을 예약하지 않음 |
| 파동 유탄 | [WaveFrameProfile.load](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WaveFrameProfile.java:26), [WeaponRuntime.waveImpact](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1359) | 일반 파동·중화기 압축 파동 모두 지면 접촉 공격. 경량 유탄의 원격 기폭을 중화기 전체에 일반화하지 않음 |
| 중화기 유탄·로켓 | [WeaponProfile.forEntry](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java:71), [WeaponRuntime.tickShot](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1303), [WeaponRuntime.impact](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1394) | 유탄 낙하·로켓 비행·폭발 범위와 벽 확인. 로켓군 전체에 자동 유도를 약속하지 않음 |
| 검 | [WeaponRuntime.onPunch/swordAttack](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:662), [SwordProfile](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/SwordProfile.java:8), [WeaponRuntime.guardDamage](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1455) | 웅크리기 해제 후 좌클릭 약공격·우클릭 강공격, 강공격은 누를 때 시도. 탄약·에너지 조건의 웅크리기 방어 |
| 월도 | [WeaponRuntime.onPunch](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:672), [GlaiveCycle](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/GlaiveCycle.java:4), [WeaponRuntime.chargeGlaive](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1424), [WeaponRuntime.guardDamage](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java:1455) | 무료 근접·원거리 투사체·적중 시 방패 에너지·웅크리기 방어. 검과 월도 방어는 방어 가능한 정면 몹 공격으로 한정 |
| 기관총 | [WeaponTiming](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/weapon/WeaponTiming.java:99), [w46-timing.json](/Users/qf/IdeaProjects/DestinyGuardians/src/main/resources/destiny/weapons/w46-timing.json) | 현재 기관총 3종의 긴 기본 재장전 시간을 반영. 연사 중 탄창과 엄폐 위치 확인 |

## 최종 문구

글자 수는 공백·문장부호를 포함하며 줄바꿈은 없다. 16개 무기군은 2문장, 핸드 캐논과 검은 3문장이다.

| ID | 글자 수 | 설명 |
|---|---:|---|
| `hand_cannon` | 73 | 중거리에서 머리를 노리는 단발 무기입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘세요. 사격 사이에는 가까운 엄폐물에 몸을 숨기세요. |
| `auto_rifle` | 81 | 중거리에서 우클릭을 누른 채 연속 사격하는 소총입니다. 좌클릭으로 조준을 켜고, 연사 중 반동으로 조준이 흐트러지면 버튼을 놓아 사격을 끊으세요. |
| `pulse_rifle` | 81 | 중거리에서 탄을 묶어 쏘는 점발 소총입니다. 좌클릭으로 조준을 켜고 우클릭으로 발사하되, 묶음 사격 도중에도 머리를 겨눠 이어지는 탄을 맞히세요. |
| `scout_rifle` | 81 | 중장거리의 적을 머리 조준으로 상대하는 소총입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘며, 근거리 교전보다 시야가 트인 긴 통로에서 사용하세요. |
| `submachine_gun` | 77 | 근거리에서 우클릭을 유지해 연사하는 무기이며, 적과 멀어지면 피해가 줄어듭니다. 엄폐물로 접근해 사격하고, 조준 화면은 좌클릭으로 켜세요. |
| `sidearm` | 79 | 근거리에서 쓰는 권총형 무기이며, 점발 프레임은 탄을 묶어 쏩니다. 좌클릭으로 조준을 켜고 우클릭으로 발사하며, 가까이 다가온 적을 겨누세요. |
| `bow` | 88 | 중장거리에서 우클릭으로 활을 당긴 뒤 버튼을 놓아 화살을 쏘세요. 당기기를 마치기 전에 놓으면 위력과 속도가 낮아지므로, 먼 적을 노릴 때는 끝까지 당기세요. |
| `sniper_rifle` | 81 | 먼 거리에서 머리를 겨눠 쏘는 정밀 사격 무기입니다. 좌클릭으로 조준경을 켜고 우클릭으로 발사하며, 주변을 살필 때는 좌클릭으로 조준경을 끄세요. |
| `shotgun` | 80 | 근거리에서 우클릭으로 산탄을 쏘며, 좌클릭으로 조준하면 탄이 퍼지는 폭을 줄입니다. 정밀 납탄 프레임은 단일 탄을 쏘므로 적의 머리를 겨누세요. |
| `fusion_rifle` | 85 | 근중거리에서 우클릭을 유지하면 충전을 마친 뒤 탄을 묶어 쏩니다. 발사 전에 버튼을 놓으면 충전을 취소하므로, 적의 몸을 겨누고 발사할 때까지 누르세요. |
| `linear_fusion_rifle` | 86 | 먼 거리에서 좌클릭으로 조준을 켜고 머리를 겨누는 충전 무기입니다. 우클릭을 유지해 충전 후 발사하며, 점발 프레임은 묶음 사격이 끝날 때까지 조준하세요. |
| `trace_rifle` | 82 | 중거리에서 광선을 적에게 대고 연속으로 피해를 주는 무기입니다. 좌클릭으로 조준을 켜고 우클릭을 유지하며, 움직이는 표적은 마우스로 따라 겨누세요. |
| `grenade_launcher` | 81 | 중거리에서 경량 유탄은 우클릭으로 쏜 뒤 반 초 이상 유지하다 놓아 원격 폭발시키세요. 파동 프레임은 적 앞의 땅을 맞혀 지면을 따라 공격하세요. |
| `heavy_grenade_launcher` | 82 | 중거리에서 모인 적에게 우클릭으로 유탄을 쏘되, 아래로 떨어지는 궤적을 고려하세요. 압축 파동 프레임은 적 앞의 땅을 맞혀 지면을 따라 공격하세요. |
| `rocket_launcher` | 81 | 중장거리에서 모여 있는 적을 폭발로 공격하는 무기입니다. 좌클릭으로 조준을 켜고 우클릭으로 쏘되, 로켓의 비행 시간과 앞을 막는 벽을 고려하세요. |
| `machine_gun` | 85 | 중거리에서 우클릭을 유지해 연속 사격하는 중화기입니다. 좌클릭으로 조준을 켜고 사격하되, 기본 재장전 시간이 길어 탄창이 비기 전에 숨을 곳을 잡으세요. |
| `sword` | 99 | 근거리에서 웅크리기를 풀고 좌클릭 약공격, 우클릭 강공격을 하세요. 강공격은 누를 때마다 시도합니다. 탄약과 에너지가 있으면 웅크려 방어 가능한 정면 몹 공격의 피해를 줄이세요. |
| `glaive` | 100 | 근거리에서는 웅크리기를 풀고 좌클릭으로 탄약 없이 찌르고, 중거리에서는 우클릭으로 쏘세요. 사격 적중으로 방패 에너지를 채워 웅크리면 방어 가능한 정면 몹 공격의 피해를 줄입니다. |
| fallback | 32 | 무기군 설명이 없습니다. 무기 이름과 프레임을 확인하세요. |

## stop-slop 교정

[SKILL.md](/Users/qf/.codex/skills/stop-slop/SKILL.md)와 [phrases.md](/Users/qf/.codex/skills/stop-slop/references/phrases.md), [structures.md](/Users/qf/.codex/skills/stop-slop/references/structures.md), [examples.md](/Users/qf/.codex/skills/stop-slop/references/examples.md)의 기준으로 1차 검수 의견을 반영했다.

- 전 항목 3문장 구성을 풀어 16개는 2문장, 핸드 캐논과 검은 3문장으로 작성했다. 무기군 설명은 73~100자, UNKNOWN은 32자다.
- “다음 사격 준비”, “조준점 옮기기”, “적 움직임 따라가기”를 반복한 문장을 제거했다. 점발은 묶음 사격, 추적 소총은 광선 유지처럼 해당 무기군의 사용법에 필요한 내용만 남겼다.
- 활의 부분 당김, 산탄과 정밀 납탄, 파동과 원격 폭발, 검의 강공격 입력과 월도의 무료 근접을 유지했다. 검·월도 방어는 에너지 조건과 방어 가능한 정면 몹 공격 범위를 명시했다.
- UNKNOWN의 일반 전투 조언을 삭제하고 “무기군 설명이 없습니다. 무기 이름과 프레임을 확인하세요.”로 줄였다.
- 기관총은 기본 재장전 시간이 긴 점을 사용법에 연결했다. 현재 timing 자료의 기관총 3종은 기본 재장전 90~106틱이며, 문구에는 수치를 넣지 않았다. 퍽 적용 뒤 시간이나 원작 수치로 일반화하지 않았다.

자체 교정 평가: 직접성 9, 리듬 9, 독자 신뢰 9, 자연스러움 8, 밀도 9, 합계 44/50. 코드 테스트나 사용자 검증 점수가 아니다.

## 정적 확인과 미검증

Python으로 반환 Java 소스와 최신 main JSON을 읽어 확인했다. 검사 스크립트나 생성물을 별도 파일로 남기지 않았다.

- catalog의 65개 무기에서 얻은 family ID 집합과 helper의 18개 key 집합 일치, 중복 key 없음.
- 18개 설명은 **73~100자**로 요청 범위 70~110자 충족. 16개는 2문장, 핸드 캐논·검은 3문장. fallback은 **32자**로 50자 이내.
- 문구에 숫자로 쓴 탄약 수량 없음. 한국어 탄약 지급량·탄창 수량도 넣지 않았으며, “단일 탄”은 산탄과 납탄의 발사 형태 구분이다.
- 공개 API, null 분기, `getOrDefault`, 불변 맵 선언, JDK 전용 import를 소스에서 확인.
- 1차 참조 파일 24개의 SHA-256을 압축 교정 시 다시 비교해 변경 없음 확인. 기관총 근거로 읽은 timing 소스와 자료 2개를 기준선에 추가했다.
- **빌드, javac, Java 실행 테스트, 서버, CU, Vision, 커밋, 추가 에이전트는 실행하지 않았다.** UI 연결·줄바꿈·잘림·인게임 조작 검증은 master 통합 후 확인할 범위다.

## 참조 기준선과 통합

기준선은 2026-10-30 현재 main의 디스크 내용이다. HEAD만을 기준으로 삼지 않았다. 기존 dirty/untracked 변경은 보존했다. 아래 해시는 참고 소스의 drift 확인용이며 반환 파일 복사 대상 목록이 아니다.

| main 상대 경로 | SHA-256 |
|---|---|
| `AGENTS.md` | `72db7a4eb6f7fd2deb2f8955e183b30cb2848cd34a61eb121e84287152015a0b` |
| `docs/qa/WORKTREE_POOL.md` | `dc04fdfd41c081832fca46d68a42891b093b8a901d59c052550054f946773367` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponCatalog.java` | `2414e0863e473fef5b203889027c44d5d27a7fbbbc2d3568daac9a576e236334` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponExotics.java` | `8bc75359ace0e885e10e1b95811b6bb43e3a242cc720e7ce6427b763e3b2a4a7` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponRuntime.java` | `e705a0cb95ad187b215091b1ae15fc511d45a5f2bce812aa2f850d8561d3feb0` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java` | `b16a84f9d93d4537d4be8dbdded2d7a49b766fe169c2a27da7b515531f618ce4` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponFirePolicy.java` | `c7bab48cef0f93683bc56d7da8590b6ff36c5fe384ce10c2076dd08139993822` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponAutoFirePolicy.java` | `3893938e440d02fa98f3154d6a3ee580ac9848b24b50d67413c207025a0f4931` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponAimProfile.java` | `6587f34cd051240330f3209b50a0b383b7e0bd77f7b566882b9acd6fbcccf3b2` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponAiming.java` | `f26ff23fb13d7be84da51210ea908070520e0b175d56d52ce759b2d4bb2a2720` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponBallistics.java` | `379cfcc4db73a1ce0d54686eadfdf90d0140653f7e24815908a7c9a194994a07` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponBowDraw.java` | `182fae2f15281cb15fb5950696b13b06bd0f0a4e7c2802650465d4e8c36be2ee` |
| `src/main/java/kim/biryeong/destiny/weapon/BreachGrenade.java` | `ff93f3c543daf52a73481ad1ac0c57a7d478f77788d745a6d8b6b1ebda7bbbec` |
| `src/main/java/kim/biryeong/destiny/weapon/WaveFrameProfile.java` | `20de4e89fc2221745fb44ea3613f58e8418b0d10e2c7762ca78ee974b0218a89` |
| `src/main/java/kim/biryeong/destiny/weapon/SwordProfile.java` | `7cd2114e387c4e51a85424f1da4ed4edb70a3993825a0cd1c5dfb5586438ad90` |
| `src/main/java/kim/biryeong/destiny/weapon/GlaiveCycle.java` | `2c7ef62def2b338f6904056a95d704a9177ee79cab04277b12039cfdc355adbe` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponCombatItem.java` | `60e1b3e87d71e80bf9de92fd84ea4053ddf2eb9bdba449917c8227059ebc38c9` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponCommands.java` | `263792dbf3c2054158706bd0816af0a38bf5ef39c8a30b6ff29ea75e31d0a0e4` |
| `src/main/java/kim/biryeong/destiny/input/InputRouter.java` | `c622ed9032fd0b16aafa9684341353780d3a3c0788785a6e6b7b37001b8ec8e1` |
| `src/main/java/kim/biryeong/destiny/inventory/WeaponScreen.java` | `46790a42bb6512369e33c243928b5f0873a8cb3b1537da16bab08f706c8b272c` |
| `src/main/java/kim/biryeong/destiny/inventory/WeaponScreenText.java` | `f23cc49e5dbee32fc3283c3e17939db6510f8a8b08db2d36d1242611c6d3bccd` |
| `src/main/resources/destiny/weapons/w30.json` | `2b1026245da2dc33003271e225b5d20de63531ae1321b7e941efae4178b5c68a` |
| `src/main/resources/destiny/weapons/w83-exotics.json` | `bab9f12b8ffb99422a31b927455391d9f292da67ffa226ad3ddc96b0b1283d56` |
| `src/main/resources/destiny/weapons/w84-exotics.json` | `481a6353fb5d3fc040d71977da9c173c9e2fc8754050fe8bb237da5172837d6e` |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponTiming.java` | `b227c76765ba47dfe613a103df71d13c75122333f7eec74e00e9eee7eca2e656` |
| `src/main/resources/destiny/weapons/w46-timing.json` | `e4c3334f528de8c48d1159c94197d9423db7cd94b9daab85889b041bd717dc07` |


최종 목록 검사에서 delta 루트의 `.DS_Store`도 발견했다. 이 작업에서 작성한 파일이 아니므로 보존하고 반환 대상에서 제외했다.

master는 두 신규 파일만 검토해 통합한다. 통합 시 대상 파일이 생겼거나 참조 구현이 바뀌었다면 현재 내용과 비교한다. 재사용 worktree 부모 전체나 다른 delta를 main에 복사하지 않는다.
