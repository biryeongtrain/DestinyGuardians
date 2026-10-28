# W229 commit prerequisite review (read-only)

조회 UTC: 2026-10-28T12:41:22.357966+00:00 / 비교 HEAD: `f5e304c` / main: `/Users/qf/IdeaProjects/DestinyGuardians` / baseline: `/private/tmp/destiny-w229/master-before`.

**결론:** 공유 Java만의 W229 delta는 기존 dirty API에 의존한다. 아래 기존 직접 의존 Java 10개와 최소 runtime support 7개는 현재 디스크에 존재하지만 HEAD에는 없다. W229 자체 신규 공유 Java 4개도 별도 포함 대상이다. 이는 **현재 통합본의 명시적 prerequisite 목록**이며 clean HEAD 재현/전체 transitive closure 검증이 아니다. staging 목록으로 자동 적용하지 않는다.

방법: 범위 제한 `git diff --name-only`, `rg --files`/직접 소스 읽기, `git ls-tree --name-only`와 선택 경로 `git cat-file -e f5e304c:<path>`로 HEAD 포함 여부 확인. 전체 git status/전체 untracked 목록은 출력하지 않았다. 아래 경로는 모두 repo 상대경로.

## 기존 직접 의존 API — 현재 있음 / HEAD 없음

| 정확한 경로 | 현재 참조 근거 / baseline 구분 |
|---|---|
| `src/main/java/kim/biryeong/destiny/fx/SwordStance.java` | PlayerAnimations:126/373; baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/fx/SwordPoseW146Assets.java` | PlayerAnimations:228; baseline:227에도 참조 |
| `src/main/java/kim/biryeong/destiny/fx/ServerAnimationClock.java` | PlayerAnimations:246/268/325/347/409/510; baseline에도 cast/API 호출 |
| `src/main/java/kim/biryeong/destiny/fx/SwordHandPackets.java` | PlayerAnimations:66/212/234/266/276/277/464/465; baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/fx/LimbEquipment.java` | PlayerAnimations:64/68/235; baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/fx/EquipmentDisplaySamples.java` | PlayerAnimations:458/525; baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/weapon/SwordItems.java` | PlayerAnimations:117/127 + SuperCamera:113; 두 baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/weapon/SwordTiming.java` | PlayerAnimations:48; baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponLoadout.java` | PlayerAnimations:118/128/418 + SuperCamera:114/226; 두 baseline에도 참조 |
| `src/main/java/kim/biryeong/destiny/sound/DestinySounds.java` | ClassAbilityEffects:10/174; baseline CombatHud:135에도 참조 |

위 9개 PlayerAnimations/SuperCamera API는 master-before의 해당 Java에서도 참조된다. DestinySounds 역시 baseline CombatHud에서 사용한다. 따라서 이들을 W229가 새로 만든 API라고 묶지 말고 **이전 dirty prerequisite**로 구분해야 한다. baseline은 선택 파일 사본이므로, 사본에 없는 파일을 모두 W229 신규라고 추정하지 않았다.

## W229 자체 HEAD-없는 공유 Java

| 정확한 경로 | 직접 연결 |
|---|---|
| `src/main/java/kim/biryeong/destiny/fx/ClassAbilityEffects.java` | 신규 공유 presentation root 자체 |
| `src/main/java/kim/biryeong/destiny/fx/ClassSuperModelAssets.java` | PlayerAnimations:284 + ClassAbilityEffects:69 등 |
| `src/main/java/kim/biryeong/destiny/fx/ClassAbilityAssets.java` | ClassAbilityEffects:163 |
| `src/main/java/kim/biryeong/destiny/fx/AbilityVisualVariants.java` | ClassAbilityEffects:169; enemy presence/resource 선택 API |

## 위 API를 유지할 때 필요한 좁은 runtime/build support

| 정확한 경로 (모두 HEAD 없음) | 연결 근거 |
|---|---|
| `src/main/java/kim/biryeong/destiny/fx/ServerEquipmentMapping.java` | LimbEquipment.bind의 명시 cast target |
| `src/main/java/kim/biryeong/destiny/fx/ServerPoseSampling.java` | EquipmentDisplaySamples.record + BetterModel clock/pose mixin의 scope |
| `src/main/java/kim/biryeong/destiny/fx/SwordModelAssets.java` | SwordPoseW146Assets.buildModel의 호출 대상 |
| `src/main/java/kim/biryeong/destiny/mixin/BetterModelClockMixin.java` | ServerAnimationClock 실제 구현; interface만 포함해서는 cast 성립 안 함 |
| `src/main/java/kim/biryeong/destiny/mixin/BetterModelPoseMixin.java` | ServerPoseSampling/EquipmentDisplaySamples의 실제 publication/recording 경로 |
| `src/main/java/kim/biryeong/destiny/mixin/BetterModelEquipmentMixin.java` | ServerEquipmentMapping 실제 구현 |
| `src/main/java/kim/biryeong/destiny/mixin/BetterModelSwordHandMixin.java` | 기존 SwordHandPackets native 손 보호 연동 |

`src/main/resources/destiny.mixins.json`은 HEAD에 **있지만 현재 수정됨**. 위 BetterModel mixin 4개의 등록은 HEAD 버전에 없으므로, Java/interface 파일만 선별하고 현재 mixin 등록을 누락하면 같은 통합본이 아니다. 그 파일에는 다른 기존 dirty mixin 등록도 있어, W229만의 새 등록이라고 통째로 설명하면 안 된다.

추가 compile 경계: 기존 `SwordItems` / `WeaponLoadout` 소스는 다음 HEAD-없는 기존 타입에 직접 의존한다. 경로는 확인했지만 이들의 전체 무기 구현/카탈로그 closure는 이번 범위가 아니다:
- `src/main/java/kim/biryeong/destiny/weapon/WeaponItems.java` — 현재 존재, HEAD 없음.
- `src/main/java/kim/biryeong/destiny/weapon/WeaponCharacteristics.java` — 현재 존재, HEAD 없음.
- `src/main/java/kim/biryeong/destiny/weapon/WeaponProfile.java` — 현재 존재, HEAD 없음.
- `src/main/java/kim/biryeong/destiny/weapon/WeaponCatalog.java` — 현재 존재, HEAD 없음.

## 필수 리소스 경계 (현재 있음 / HEAD 없음)

| 정확한 경로 | 소비자 / 구분 |
|---|---|
| `src/main/resources/destiny/animation/classes_w229.animation.json` | ClassSuperModelAssets.RESOURCE:21 / ClipIndex / prepare; W229 자체 필수 |
| `src/main/resources/destiny/animation/hunter_w199.animation.json` | 현재 HunterModelAssets:25/34; tracked Java지만 HEAD는 hunter_h19를 가리키므로 현재 W199 Java+resource 묶음 필요 |
| `src/main/resources/destiny/animation/sword_w146.animation.json` | SwordPoseW146Assets.RESOURCE:16 / prepare |
| `src/main/resources/destiny/animation/sword_w53.animation.json` | 기존 SwordModelAssets.prepare가 entrypoint baseline에서 호출됨; W146 builder 자체의 JSON 입력은 W146이며 W53과 구분 |
| `src/main/resources/assets/destiny/sounds.json` | DestinySounds.load:26; 미존재 시 IllegalStateException. master-before에도 파일 존재(기존 dirty + W229 추가 매핑을 함께 보존). |

`/steve.bbmodel`은 이 main의 `src/main/resources/steve.bbmodel`에 존재하지 않으며 HEAD에도 없다. 현재 코드는 외부 BetterModel classpath 템플릿을 사용한다. 가짜 repo 파일을 추가할 대상이 아니며, 외부 라이브러리/리소스 공급은 이 감사에서 독립 재검증하지 않았다. `CameraViews`도 `libs/minigame-lib` composite dependency로 W229 repo 신규 Java 목록과 구분한다.

W229 자산은 이미 통합 manifest의 정확 파일집합을 사용한다. `ClassAbilityAssets.has` / `AbilityVisualVariants`는 없는 모델을 fallback하지만, R3에서 관측한 외관을 보존하려면 해당 class_ability + enemy 아이템/모델/PNG 및 BM 8종 `_enemy` 의존성을 기존 동결 manifest 그대로 유지해야 한다. Hunter enemy는 **37개 동결 payload**로 이미 경계가 정해져 있다. 이 조사 때문에 전체 `assets`/원본 SSD/무기 카탈로그를 포함할 필요는 없다.

ClassAbilityEffects.sound가 사용하는 W229 18개 sound event는 현재 sounds.json에서 실제 **17개 OGG**를 가리킨다(공유 Hammer cue 포함). 정확한 W229 파일 목록:

- `src/main/resources/assets/destiny/sounds/classes_w229/titan_arc_super_fire.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_arc_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_solar_hammer_impact.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_solar_hammer_throw.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_solar_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_void_super_fire.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_void_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_void_suppressor_impact.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/titan_void_suppressor_throw.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_arc_super_fire.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_arc_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_solar_super_fire.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_solar_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_void_super_fire.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_void_super_start.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_void_vortex_impact.ogg`
- `src/main/resources/assets/destiny/sounds/classes_w229/warlock_void_vortex_throw.ogg`

아래 범위는 수행하지 않았다: git add/commit/index 변경, main/SSD 변경, build/test/game 실행, 전체 22만 dirty 자산 감사, 선택된 기존 무기 API의 전이 closure 재현. 본 문서 외 파일을 쓰지 않았다.
