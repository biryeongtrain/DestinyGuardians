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

## 문서

- [기획서](docs/Destiny_Guardians.md)
- [세부 문서 안내](docs/design/00_문서_안내.md)
- [작업 계획 – 기본 시스템](docs/design/11_작업_계획.md)

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
