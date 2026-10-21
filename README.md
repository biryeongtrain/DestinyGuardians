# Destiny Guardians

데스티니 가디언즈의 직업·무기·레이드를 마인크래프트 야생에 옮기는 **Minecraft 26.3 / Fabric 서버사이드 모드**입니다. 플레이어는 바닐라 클라이언트로 접속하고, 커스텀 외형은 Polymer 서버 리소스팩으로 받습니다.

## 구성

| 의존성 | 버전 | 역할 |
|---|---|---|
| Fabric Loader / API | 0.20.1 / 0.164.0+26.3 | |
| Polymer | 0.18.4+26.3 | 서버사이드 아이템·엔티티, 리소스팩 생성·호스팅 |
| BetterModel | 3.5.1 | 플레이어 limb·적·보스 모델과 애니메이션 |
| minigame-lib | 2.0.0+26.3 (`libs/minigame-lib` submodule) | DisplayHud, ShaderFX, FOV, 시네마틱, 음악 |
| Java | 25 | |

## 시작하기

```sh
git clone --recurse-submodules <repo-url>
# 이미 받은 경우
git submodule update --init --recursive

./gradlew build        # build/libs/destiny-guardians-*.jar
./gradlew runServer    # run/server. 첫 실행 시 run/server/eula.txt 에 eula=true 필요
./gradlew runClient    # 개발 클라이언트 (싱글플레이 테스트)
```

minigame-lib은 Maven 저장소 대신 submodule 소스를 `includeBuild`로 직접 빌드합니다. 새 버전을 쓰려면:

```sh
cd libs/minigame-lib && git fetch && git checkout <tag> && cd ../..
git add libs/minigame-lib && git commit -m "chore: bump minigame-lib to <tag>"
```

## 서버에 설치

`build/libs/destiny-guardians-<버전>.jar`와 함께 다음 모드를 서버에 넣습니다: Fabric API, Polymer(core·resource-pack·virtual-entity·autohost), BetterModel(+ Fabric Language Kotlin), minigame-lib.

## 헌터 시작하기

서버에서 리소스팩 수락 후 실행합니다. 아래 명령은 본인 대상으로 쓸 수 있고,
OP는 마지막에 플레이어 이름을 붙일 수 있습니다.

```text
/guardian class hunter
/guardian subclass arc          # solar / void 도 선택 가능
/guardian info
```

| 동작 | 바닐라 입력 | GCB-mod 선택 설치 시 |
|---|---|---|
| 공중 점프 | 공중에서 Space 다시 누르기 | 동일 |
| 회피 | Shift 두 번 (7틱 이내) | C |
| 수류탄 | F | Z |
| 근접 능력 | Shift + 좌클릭 | V |
| 궁극기 | Shift + F (게이지 100%) | X |
| 궁극기 공격 | 좌클릭 | 좌클릭 |

헌터는 F 손 교환을 능력 입력으로 사용합니다. `/guardian class none`으로 해제하면 바닐라 동작이 유지됩니다.
일반 총기·탄약 및 명사수 회피의 재장전 연동은 아직 없습니다.
BetterModel 기본 리그에서 `config/bettermodel/players/guardian_hunter.bbmodel`을 최초 생성하며,
기존 파일은 덮어쓰지 않습니다. 최종 아트로 교체할 때 `roll`, `super_arc`, `super_solar`, `super_void`
애니메이션과 `pri_right_item` bone 계약을 유지해야 합니다.
바닐라는 본인 limb를 숨기며, GCB 시점 이벤트가 있어야 본인 3인칭 표시를 구분합니다.

GCB 어댑터는 빌드 시 `gcb_server_dir`(기본 `../GCB-server`) 소스가 있어야 포함됩니다.
없어도 바닐라 입력 빌드는 가능하지만, 그 JAR에 GCB-server만 나중에 추가해도 어댑터가 생기지는 않습니다.
빌드 의존성 모드들은 JAR에 내장되지 않으므로 서버에 별도 설치해야 합니다.

## 자동 검증

Java 25에서:

```sh
rtk proxy ./gradlew runGameTest build --console=plain
```

헌터 GameTest 33개, JUnit 리소스 테스트 2개. 실제 렌더링은 별도 Copper Golem Vision 26.3으로 검증했습니다.
개발 서버 실행 중 소스 재컴파일은 하지 말고, 서버를 중지한 뒤 빌드하고 새 JVM에서 검증하세요.

## 문서

- [기획서](docs/Destiny_Guardians.md)
- [세부 문서 안내](docs/design/00_문서_안내.md)
- [작업 계획 – 기본 시스템](docs/design/11_작업_계획.md)
- [헌터 구현 로그·검증 범위](docs/design/13_헌터_구현_로그.md)
- [헌터 QA 증거](docs/qa/2026-10-22/README.md)

## 작업 규칙

- 브랜치: `main`에 직접 커밋하지 않고 `feat/<이슈ID>-<설명>`, `fix/...`, `docs/...`에서 작업
- 커밋: [Conventional Commits](https://www.conventionalcommits.org/) + 이슈 ID. 예: `feat(input): W2-03 input router`

| 패키지 (`kim.biryeong.destiny`) | 역할 |
|---|---|
| `data` | JSON 데이터 등록부 |
| `guardian` | 수호자 상태(직업·능력·쿨타임·게이지) |
| `input` | 바닐라 입력 → 능력 이벤트 |
| `ability` | 능력 실행 |
| `weapon` | 사격·반동·재장전·정조준 |
| `hud` | DisplayHud HUD·UI |
| `fx` | VFX, 포스트 이펙트 |
| `enemy` | 적·보스 |
| `mixin` | Mixin |
