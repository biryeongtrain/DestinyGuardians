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
수류탄3종·태양 단검·공허 연막탄은 Blockbench 소품으로 표시합니다.
H12에서 칼·섬광탄을 실제 Destiny 시각 자료에 맞춰 재제작했습니다. 소이·소용돌이·연막은 원작 외형 미확인 잠정 모델입니다.
[능력 모델·레퍼런스](docs/design/14_헌터_능력_모델.md) · [편집 원본](art/blockbench/hunter/)

H13 기반/H14 디테일 개정: 수류탄·근접6종에 **BetterModel 애니메이션 VFX4종**을 연결했습니다. Arc 분기 전격·겹친 곡선 화염·Void 나선/필라멘트·텍스처 연무로 표시합니다.
32→128 아틀라스, Arc/Solar/Vortex 메시720~1024삼각형+19~45카드, 연막30빌보드 카드, 렌더본4~8개를 사용합니다.
[시각 레퍼런스](docs/design/15_헌터_VFX_레퍼런스.md) · [구현·한계](docs/design/16_헌터_VFX_구현.md) · [H14 디테일·비용](docs/design/17_헌터_VFX_디테일_개정.md) · [VFX 원본](art/blockbench/vfx/)
연막과 근접 파생 효과는 잠정 해석입니다. H15에서는 궁극기 전용 장비4종, BetterModel 버스트·닻,
Polymer 화염 궤적·움직이는 공허 연결선과 화면 펄스를 추가했습니다.
방향별 회피와 궁극기 준비/공격/회복 클립도 연결했습니다.
[고도화 로드맵](docs/design/18_헌터_고도화_로드맵.md) · [장비](docs/design/20_헌터_궁극기_장비.md) · [궁극기 VFX](docs/design/22_궁극기_VFX_구현.md)

BetterModel 기본 리그에서 `config/bettermodel/players/guardian_hunter_h15.bbmodel`을 최초 생성하며,
기존 파일은 덮어쓰지 않습니다. 방향별 `h15_roll_*`, 속성별 `h15_super_*`·`h15_super_*_attack` 및
아이템 bone 계약은 [애니메이션 명세](docs/design/19_헌터_애니메이션_개정.md)를 따릅니다.
구형 `guardian_hunter`와 기본 리그는 폴백입니다. 오프라인 QA 계정은 limb 재생 중 기본 템플릿 색으로
바뀌는 현상이 남으며, 인증 계정 개인 스킨은 미검증입니다.
바닐라는 본인 limb를 숨기며, GCB 시점 이벤트가 있어야 본인 3인칭 표시를 구분합니다.

GCB 어댑터는 빌드 시 `gcb_server_dir`(기본 `../GCB-server`) 소스가 있어야 포함됩니다.
없어도 바닐라 입력 빌드는 가능하지만, 그 JAR에 GCB-server만 나중에 추가해도 어댑터가 생기지는 않습니다.
빌드 의존성 모드들은 JAR에 내장되지 않으므로 서버에 별도 설치해야 합니다.

## 전투 HUD

- 상단 중앙: 흰 체력 바(실제 HP), 30% 이하는 빨간색. 실제 흡수량이 있을 때만 청색 보조 바.
- 좌하단: 능력 실루엣 3개와 충전 밑줄, 궁극기 다이아몬드·가로 게이지. 준비/활성은 황금색.
- H17: 새 충전 완료에 `SUPER CHARGED` 배너·황금 확산/스윕, 준비 아이콘 채움과 속성별 발동 액센트. 재접속100%는 정적 준비 상태만 표시합니다.
- [궁극기 준비 연출](docs/design/24_궁극기_준비_HUD_연출.md) · [H17 실제 화면/검증](docs/qa/2026-10-22/h17/README.md).
- 필수 팩은 하트 44변형을 숨깁니다. 직업 none 플레이어에게도 대체 체력 바가 표시됩니다.
- 기본 핫바·배고픔·방어구·경험치는 아직 유지하며, 일반 무기 탄약 수치를 꾸며 넣지 않습니다.
- H17 배너/발동 그래픽은 `scripts/generate_super_hud_assets.py`(Pillow)로 재생성합니다.
- 직접 제작한 HUD 에셋 재생성: Pillow 설치 후 `scripts/generate_hud_assets.py` 실행(26.3 로컬 클라이언트 JAR 필요).

## 자동 검증

최신 H19: **GameTest104/104 · JUnit59/59**, build 성공. 공허 활 당김→단발 릴리스와
연결 wrapper를 거친 카메라 이동 회귀를 포함합니다. 실제 native 입력·PNG와 저속 틱 한계는
[H19 QA](docs/qa/2026-10-22/h19/README.md)에 분리했습니다. 아래 H17/H16 수치는 당시 기록입니다.

Java 25에서:

```sh
rtk proxy ./gradlew runGameTest build --console=plain
```

H17 필수 GameTest **90/90**, JUnit **37/37**(실패·오류·스킵 0), build 성공.
실제 렌더링은 별도 Copper Golem Vision26.3에서 검증했습니다. H17은 준비 배너·좌하단 확산/스윕·세 속성 발동 액센트와 정리를 확인했습니다.
아래 성능 수치는 H16 당시 측정이며 H17에서 다시 계측하지 않았습니다.
로드맵1~3 구현에 이어4번은 실제2인·거리·야간/차폐 공간·성능 검증 완료입니다.
2인8닻+8선 fixture에서 전체 tickServer P95 2.883ms, 두 클라이언트119~120FPS(120 제한).
실제6인 이상/글로벌 최대 부하 성능 보증은 아니며,5번 일반 총기·재장전은 미착수입니다.
원작 블룸·볼류메트릭·GCB 실제 통신을 검증했다고 간주하지 않습니다.
개발 서버 실행 중 소스 재컴파일은 하지 말고, 서버를 중지한 뒤 빌드하고 새 JVM에서 검증하세요.

## 문서

- [기획서](docs/Destiny_Guardians.md)
- [세부 문서 안내](docs/design/00_문서_안내.md)
- [작업 계획 – 기본 시스템](docs/design/11_작업_계획.md)
- [헌터 구현 로그·검증 범위](docs/design/13_헌터_구현_로그.md)
- [헌터 QA 증거](docs/qa/2026-10-22/README.md)
- [H16 다인·거리·전체 틱/FPS/패킷 결과](docs/design/23_다인_거리_성능_검증.md)
- [H19 공허 활 사격 연출·출처·제약](docs/design/28_H19_궁극기_활_연출.md)

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
