# 떠오르는 수호자 · 몰락자 드레그 인수인계

**서버에 설치할 파일은 [dreg_combat.bbmodel](dreg_combat.bbmodel)입니다.** 모델 ID는 `dreg_combat`입니다. 이 한 파일에 19본 모델, 2048×2048 텍스처, 드레그 원본에서 옮긴 13개 동작이 들어 있습니다. `damage`는 피격 동작 `hurt`에 붙인 별칭이어서 편집기에는 이름이 14개 보입니다.

검증 환경은 Minecraft Java Edition 26.3, Fabric Loader 0.20.1, BetterModel 3.6.0, Polymer 0.18.5입니다. 처음 받았다면 먼저 게임에서 도발 동작을 재생해 아래 영상과 비교하세요. [바닐라 클라이언트 촬영 GIF · 7개 동작](animations/dreg-original-ingame.gif)

## 1. 서버에 설치하고 도발 재생하기

1. 기존 서버의 `config/bettermodel/models/`에 `dreg_combat.bbmodel`을 복사합니다. 이전 버전을 쓰고 있다면 같은 이름의 파일을 교체합니다. 텍스처는 모델에 내장돼 있습니다.
2. 권한이 있는 플레이어로 아래 두 명령을 차례로 실행합니다. 첫 명령의 리로드 완료 메시지를 확인한 뒤 두 번째 명령을 실행합니다.

   ```mcfunction
   /bettermodel reload
   /polymer generate-pack
   ```

3. 로컬 테스트에서는 **서버**의 `polymer/resource_pack.zip`을 **클라이언트**의 `resourcepacks/`에 복사하고 리소스 팩 화면에서 활성화했습니다. 자동 배포를 쓰는 서버에서는 새로 생성한 팩을 그 서버의 배포 경로로 적용합니다.
4. 인게임 채팅에서 다음 명령을 실행합니다.

   ```mcfunction
   /bettermodel test dreg_combat taunt
   ```

   정상이라면 플레이어 앞에 드레그가 나타나 약 1.77초 동안 도발 동작을 한 뒤 사라집니다. 계속 월드에 둘 개체를 소환할 때는 `/bettermodel spawn dreg_combat`을 사용합니다. 기본 개체는 허스크입니다.

**문제가 생기면** 모델을 찾을 수 없다는 메시지는 서버의 파일명·설치 폴더·리로드 로그부터 확인합니다. 모델은 소환되는데 외형이 잘못 보이면 클라이언트에서 활성화한 ZIP이 이번에 생성한 것인지 확인합니다. 테스트 명령으로는 투척 자세까지 보이는데 수류탄이 날아가지 않는 경우, 다음 절의 전투 로직 연결이 남아 있습니다.

## 2. 전투 로직에서 사용할 이름

| 용도 | 클립 ID | 연결 메모 |
|---|---|---|
| 대기 · 이동 | `idle`, `walk` | 반복 재생. 두 이름은 발의 움직임과 반복 주기를 보고 지정했습니다. |
| 권총 사격 | `fire` | 약 0.23초의 반동. 서버의 발사 이벤트에서 호출합니다. |
| 피격 | `damage`, `hurt` | 동일한 원본 피격 동작. BetterModel이 피해 이벤트에서 `damage`를 재생하므로 같은 타격에 `hurt`까지 호출하면 중복됩니다. |
| 도발 · 경계 | `taunt`, `surprise_front` | 등장이나 적 발견 연출에 쓸 수 있습니다. |
| 근접 공격 · 수류탄 | `melee`, `throw_grenade` | 각각 약 1.33초, 2.07초. 피해 적용과 투사체 생성 시점은 서버 전투 코드에서 정합니다. |
| 왼쪽 · 오른쪽 회피 | `evade_left`, `evade_right` | 약 0.83초의 회피 스텝. |
| 왼쪽 · 오른쪽 다이빙 | `dive_left`, `dive_right` | 크게 몸을 던지는 회피. 실제 개체 이동과 충돌은 서버에서 처리합니다. |
| 사망 | `death` | 앞으로 쓰러지는 원본 클립 `land_dead_front`를 사용합니다. |

**예시 A — 소환한 드레그의 피격 확인.** 주변 허스크와 분리된 테스트 장소에서 실행합니다. 두 번째 명령은 플레이어 기준 5블록 안의 가장 가까운 허스크 한 마리를 대상으로 합니다. 드레그가 피해를 받고 움츠렸다가 대기로 돌아오면 외형과 피격 이벤트가 함께 연결된 상태입니다.

```mcfunction
/bettermodel spawn dreg_combat
/damage @e[type=minecraft:husk,distance=..5,sort=nearest,limit=1] 2 minecraft:generic
```

**예시 B — 이미 소환된 드레그가 수류탄을 던지는 동작.** 아래 메서드는 해당 드레그를 생성할 때 받은 BetterModel `EntityTracker`를 인자로 받습니다. 전투 AI가 투척 상태에 진입할 때 한 번 호출합니다. 반환값은 애니메이션이 시작됐는지를 뜻합니다. 투사체 생성은 이 메서드와 별도로 구현해야 하며, 원본의 정확한 손 이탈 프레임은 확인하지 못했습니다.

```java
import kr.toxicity.model.api.tracker.EntityTracker;

class DregCombatActions {
    static boolean beginGrenadeThrow(EntityTracker dreg) {
        return dreg.animate("throw_grenade");
    }
}
```

이 코드는 BetterModel 3.6.0 배포 JAR에 포함된 API로 컴파일을 확인했습니다. 실제 AI의 상태 전이와 투사체 호출은 프로젝트에 연결해야 합니다.

## 3. 원본을 확인하거나 동작을 추가할 때

Blender에서 [Dreg_77bone.fbx](animations/Dreg_77bone.fbx)를 가져온 뒤 아마추어를 선택하고 **Dope Sheet → Action Editor**에서 액션을 바꿉니다. 이 FBX에는 애니메이션용 본 77개와 액션 13개가 있습니다. Blockbench에서는 `dreg_combat.bbmodel`의 **Animate** 탭에서 같은 동작을 19본 모델로 확인할 수 있습니다. 예를 들어 게임의 `taunt`와 비교할 FBX 액션은 이름에 **80E115EC**가 들어간 항목입니다. FBX에는 다른 쿼리명인 `new_target`이 붙어 있어 해시로 찾는 편이 정확합니다. [클립별 태그·길이·본 대응표](animations/original-clips.json)

Charm 3.5.0에서 확인한 경로는 엔티티 `80E1AFCF` → 애니메이션 컴포넌트 `80E1324E` → 공유 컨테이너 `80E12ABC`입니다. 스켈레톤은 `80E10CFB`, 런타임 리그는 `80E132EF`입니다. 컨테이너에 연결된 715개 중 현재 전투 모델에 맞는 동작을 골랐습니다. `fire`와 `hurt`는 대기 클립 `80E115E0`의 첫 자세 위에 가산 레이어를 합성했습니다.

**예시 C — 스키프 하차 동작 추가.** 현재 전달본에는 없는 확장 예시입니다. 기존 개발 워크스페이스에서 `work/dreg-motion/paths.json`의 `skiff_exit`를 열면 권총 분기는 `80E114D5`, 소총 분기는 `80E1149F`입니다. 권총 드레그에는 첫 번째 태그를 사용합니다.

1. 기존 작업 루트 `C:\Users\kb100\Documents\Codex\2026-10-31\new-chat`에서 진행합니다. 이 절은 로컬 Charm 런타임·게임 패키지·변환 스크립트가 있는 개발 환경용입니다. 해당 환경에는 선택한 클립의 프레임 파일 `work/dreg-motion/80E114D5.json`이 있습니다.
2. `work/dreg_retarget.py`의 `clips` 목록에 다음 한 줄을 추가합니다.

   ```python
   ('skiff_exit', '80E114D5', 'skiff_exit', 'pistol'),
   ```

3. 작업 루트에서 `rtk proxy python work/dreg_retarget.py`를 실행합니다. 결과는 `work/dreg-motion/dreg_combat.bbmodel`과 같은 폴더의 `original-clips.json`입니다. 변환기는 원본 포즈를 30fps로 평가하고, 부모 기준의 19본 위치·회전을 만들어 키를 줄입니다.
4. 생성된 BBModel을 테스트 서버에 복사하고 1절대로 리로드·팩 적용 후 `/bettermodel test dreg_combat skiff_exit`로 확인합니다. 착지할 때 발이 지면과 맞는지, 동작이 끝났을 때 서버 개체 위치와 모델 위치가 맞는지 봅니다.
5. 채택하면 배포 BBModel, 클립 목록, 원본 FBX, 검증 기록을 함께 갱신합니다. 기존 `work/dreg_motion_deliver.py`는 13개 원본과 별칭 1개를 전제로 검사하므로 새 클립을 넣을 때 기대 개수도 바꿔야 합니다.

문서 작성 시 이 예시를 별도 작업 사본에서 변환해 `skiff_exit`가 3.20초 클립으로 생성되는 것까지 확인했습니다. 이 추가 클립의 인게임 재생은 미검증입니다.

## 4. 인수 기준과 남은 작업

- **모델 식별.** 서버에 복사한 BBModel의 SHA-256은 `96afa5f0e97f5478b4fb769b71ae45fde0e76e4a53b494f820b8bdd5944e3510`입니다. 생성 팩에서 본별 모델 19개, 텍스처가 있는 사각 면 1,864개를 확인했습니다. [검증 기록](validation.json)
- **재생 검증.** 로컬 바닐라 클라이언트에서 13개 클립을 각각 실행했고, 소환한 허스크에서 실제 피해를 받은 뒤 피격 → 대기 전환도 확인했습니다. 원본과 대조한 19개 관절 중심의 최대 오차는 원본 샘플 시각에서 0.004블록 미만입니다. 손가락과 천의 개별 변형은 19본 모델에서 생략했습니다.
- **다음 구현 범위.** 실제 전투에 붙일 때는 사격·근접·투척의 AI 조건, 피해 판정, 투사체 생성, 회피 중 개체 이동을 연결해야 합니다. 원본 13클립을 적용한 버전의 다수 전투 FPS·서버 MSPT와 운영 서버 팩 자동 배포는 미검증입니다. 이전 정지 모델의 10마리 측정값은 현재 버전의 전투 성능 기준으로 쓰기 어렵습니다.
