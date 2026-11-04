# Destiny 원본 장전 애니메이션 추출 조사 — 2026-10-27

후속 보완: 사용자가 지정한 Charm v3.5.0_Beta.2의 소스를 추가 확인한 결과, 실제 무기 animation curve와 별도 FirstPerson FBX export가 구현돼 있다. [추가 조사와 Windows 실행 경로](../../handoffs/2026-10-27-windows-animation-extraction/evidence/CHARM_USER_VERSION.md)를 먼저 참조한다. 따라서 Windows에서는 Charm 직접 FBX를 우선하고 raw태그+별도 parser 경로를 보존/대안으로 사용한다. 아래 본문은 앞선 조사 기록이며 실제 추출 미실행이라는 상태는 그대로다.

결론: 사용자가 제안한 게임 패키지 → 원본 애니메이션 파싱은 현재 영상 모사보다 정확한 모션 원천을 얻을 수 있는 유망한 경로다. Discord에 실제 태그 조합과 Blender export 성공 보고가 있다. 다만 다운로드, 패키지 압축 해제, clip 해석, 게임용 retarget/bake는 서로 다른 단계다. 이번 작업은 조사이며 실제 게임/태그 추출·설치·Minecraft 검증은 실행하지 않았다.

## Discord에서 실제 확인한 근거

사용자가 지정한 Destiny Model Rips 서버를 로그인된 Chrome UI로 읽기 전용 검색했다. 메시지를 보내거나 가입/권한을 바꾸지 않았다. 채널 전체 조사라고 주장하지 않는다. `tiger-animation-parser` 검색6건과 `"runtime rig"` 검색23건, 해당 `#other-help` 문맥을 중심으로 확인했다.

| 근거 | 확인 내용 |
|---|---|
| [Nethock 10월4일 핸드캐논 장전](https://discord.com/channels/514059860489404417/592620497985077256/1556259957546942565) | clip `80A8A567`, package `w64_sr_sandbox_anims_0145_2.pkg`, skeleton `80C3C215`, runtime rig `80C3C216` 조합을 게시했다. 80 joints/240 channels/127 keys/4.2초/61,345bytes라고 보고한다. 게시자도 오래된 버전일 가능성을 언급한다. |
| [10월5일 탐색 방법](https://discord.com/channels/514059860489404417/592620497985077256/1556404696888123454) | clip의 node/control 수와 rig 구조로 후보를 좁히고 parser로 glTF export한 뒤 Blender에서 동작을 시각 분류했다고 설명한다. 후속 답변은 같은 무기군의 rig 구조를 탐색 단서로 사용했다는 내용이다. 개수 일치만으로 호환을 확정하는 검사는 아니다. |
| [시연 영상 게시물](https://discord.com/channels/514059860489404417/592620497985077256/1556396598135750777) / [태그 목록 이미지](https://discord.com/channels/514059860489404417/592620497985077256/1556398290646343762) | Blender 시연 첨부와 태그 목록을 확인했다. 이번 UI에서 video 재생 메타데이터가 time0/길이 미확인에 머물러 영상 모션을 독립 검증했다고 쓰지 않는다. preview에는 팔이 보이지만 1P/3P 구분과 전체 모션은 실제 추출물에서 확인해야 한다. |
| [제작자 v2 설명,7월13일](https://discord.com/channels/514059860489404417/514419766799237120/1525881270532309042) | 대응 skeleton과 runtime rig를 확보하면 retarget 가능한 범위가 넓어졌다는 설명이다. 제작자도 모든 캐릭터에 대한 표현을 이론적인 범위로 한정했다. |
| [제작자 clip/rig 설명,6월26일](https://discord.com/channels/514059860489404417/1085149357256482856/1520014670964981823) | 당시 D2 clip class `80808BE0`와 runtime-control을 skeleton transform으로 푸는 과정의 필요성을 설명한다. 최신 모든 build에서의 고정 class라고 확정하지 않는다. |

![게시된 태그 목록의 실제 화면 발췌](community-handcannon-tag-list.png)

이미지에서 `80A8A53D`(선택된 HC reload), `80A8A55A`(HC reload), `80A8A554`(Special HC reload), equip/recoil 후보도 읽을 수 있다. **텍스트의 `567`과 이미지의 `53D`는 다른 clip이다.** 텍스트의 skeleton/rig 호환 보고를 이미지의 모든 clip에 전이하지 않는다. 어떤 후보도 Ace 고유 장전으로 확인된 것은 아니다. 4.2초/127키도 특정 원본 clip 보고값이지 Ace의 실제 gameplay 장전시간이 아니다.

## parser 코드 확인

[tiger-animation-parser](https://github.com/SolUnshadowed/tiger-animation-parser)의 조사 revision은 `b9fdc3a43dd28118113275624fcc9054b75855f4`이다. Python3.13+, animated codec0–3/static3, rawJSON·retargetJSON·retargetglTF를 제공한다. glTF는 armature+animation이며 기존 정돈된 큐브 무기 mesh를 자동 생성하거나 Minecraft에 바로 설치하는 도구가 아니다.

- [CLI](https://github.com/SolUnshadowed/tiger-animation-parser/blob/b9fdc3a43dd28118113275624fcc9054b75855f4/cli/cli_parser.py)는 clip·skeleton·rig 세 파일을 요구한다. `.pkg` 다운로드/압축 해제/무기별 clip 탐색 기능은 없다. raw 모드도 CLI의 세 파일 존재 검사를 통과해야 한다.
- [requirements](https://github.com/SolUnshadowed/tiger-animation-parser/blob/b9fdc3a43dd28118113275624fcc9054b75855f4/requirements.txt)에 numpy/scipy/pygltflib/pyglm이 있지만 [export 모듈](https://github.com/SolUnshadowed/tiger-animation-parser/blob/b9fdc3a43dd28118113275624fcc9054b75855f4/animation_export/export_animation.py)의 `jsonpickle` import가 빠져 있다. 격리 venv를 만들 때 이 의존성을 보완해야 한다.
- export는 skeleton/rig 로드가 실패하면 rawJSON으로 fallback할 수 있다. [entrypoint](https://github.com/SolUnshadowed/tiger-animation-parser/blob/b9fdc3a43dd28118113275624fcc9054b75855f4/parser.py)는 내부 예외를 로그에 남긴 뒤 exit0에 이를 수 있다. 성공 판정은 종료코드와 함께 실제 `.gltf` 존재·animation channel·유효 key값·Blender 재생까지 확인한다.
- [glTF exporter](https://github.com/SolUnshadowed/tiger-animation-parser/blob/b9fdc3a43dd28118113275624fcc9054b75855f4/animation_export/gltf_export.py)는 `fps=30`을 사용한다. 출력초수와 실제 원작 장전 완료/취소 가능 시점은 별도 대조한다. 특정 rig 기능에는 경고/미지원 처리가 있으므로 모든 clip의 정확한 재현을 보장하지 않는다.
- `d2_eof` 및 코드상의 `d2_sk` 레이아웃이 있다. 최신 공개 패키지가 자동으로 호환된다는 뜻은 아니다. 하나의 manifest/build에서 얻은 clip/skeleton/rig를 묶고 parser revision·package hash도 기록한다.

추출 후의 예시 명령(이번에 실행하지 않음):

```sh
rtk proxy python3 parser.py -v d2_eof \
  --clip extracted/80A8A567.bin \
  --skeleton extracted/80C3C215.bin \
  --rig extracted/80C3C216.bin \
  -t gltf_retarget --name-convention blender --animation-space local \
  -o out/handcannon_reload_candidate
```

위 파일명은 예시다. unpacker의 실제 출력 이름과 대응 build를 확인한 뒤 사용한다.

## Mac에서의 현실적인 경로

1. **Windows 파일 확보:** [DepotDownloader](https://github.com/SteamRE/DepotDownloader/releases/tag/DepotDownloader_3.4.0)는 macOS ARM64/x64 배포와 `-os windows`, `-manifest-only`, `-depot`, `-manifest`, `-filelist`를 지원한다. Destiny2 app1085660의 계정 entitlement와 Steam Guard가 필요할 수 있다. F2P라는 이유로 anonymous 다운로드가 보장되지는 않는다. 암호를 명령행/문서에 넣지 않는다.
2. **처음에는 manifest만:** 먼저 main depot1085661의 목록을 확인하고 `0145` 애니메이션 패키지 묶음과 skeleton/rig의 실제 소속 패키지 및 patch/base 의존성을 찾는다. 파일명 `_2.pkg` 하나로 충분하다고 가정하지 않는다. skeleton/rig가 들어 있는 패키지를 아직 독립 확인하지 않았다. 특정 manifest ID와 실제 byte 절감량은 이번 조사에서 확정하지 않았다.
3. **압축 해제는 별도 환경:** [tiger-pkg](https://github.com/v4nguard/tiger-pkg)의 조사 revision `657f41c0851001b2d371592b2f7a5cb9c686ddb4` [Oodle 소스](https://github.com/v4nguard/tiger-pkg/blob/657f41c0851001b2d371592b2f7a5cb9c686ddb4/src/oodle.rs)는 macOS에서 명시적 compile_error를 낸다. Linux `.so` 또는 Windows DLL 경로는 있으나 Mac native 지원으로 읽으면 안 된다. [최신 Charm branch](https://github.com/MontagueM/Charm/tree/delta/EOF)도 Windows .NET desktop/VC++ 기반이며 Wine에서는 custom renderer가 동작하지 않는다고 적혀 있다. 이번 PoC는 Windows 또는 지원 Linux 환경의 태그 추출이 가장 현실적이다. 가용 VM/원격 머신·Linux decoder 아키텍처는 아직 확인하지 않았다. Docker를 설치하기만 하면 해결된다는 주장도 하지 않는다.
4. **Mac으로 돌아와 Python parser → Blender:** 추출된 raw tag 세트를 Mac에서 읽어 glTF를 만들 수 있는 구조다. 패키지 decoder를 Mac으로 포팅할 필요와 분리한다. Python 의존성 설치/파싱 자체는 아직 실제 실행하지 않았다.

[Bungie 공식 용량 안내](https://help.bungie.net/hc/en-us/articles/360048717052-Destiny-Platform-Storage-Requirements)의 Steam 설치량은 최대180.90GB다. 353GB는 기존 설치+사전 다운로드 상황의 수치이므로 fresh 선택 다운로드 필수량과 섞지 않는다. 선택 패키지로 시작해 추출물/캐시 용량을 실제 측정한다.

## 현재 Minecraft 제품으로 연결하는 방법

추천 PoC는 **일반 핸드캐논 후보 하나**다. source rig에서 총기/탄창/실린더/양팔의 월드·로컬 기준과 부모관계를 확인하고 Blender에서 bake한 뒤, 기존 큐브 무기의 의미 있는 부품 group에 transform을 매핑한다. 원본 고밀도 mesh로 현재 정돈된 큐브 모델을 대체할 필요는 없다. 필요 시 원본 팔 모션을 별도 리깅할 수 있지만 바닐라 1인칭 양팔 renderer가 glTF를 자동 재생하지는 않는다.

현재 `WeaponReloadPresentation`은 서버가 수락한 실제 장전 상태에서 FP 표현을 제공한다. import된 transform은 이 기존 장전 상태·진행률에 매핑하며 탄약 지급/취소 권한을 animation에 맡기지 않는다. source clip의 30fps 시간축을 런타임 진행률로 매핑하고 gameplay 장전 시간은 사용자 지정 DDC/실측에 따른다. 3P BetterModel에는 별도의 player-bone retarget 및 무기 부착 변환이 필요하다. 1P/3P clip을 혼용하지 않는다.

첫 수락 기준은 원본 rig가 Blender에서 정상 재생되고, 손·실린더/탄창 접촉이 맞으며, Minecraft 한 무기에서 대표 FP/ADS복귀/장전취소·실탄 완료를 확인하는 것이다. 이 경로가 성공한 다음 rig-family 인덱스로 다른 clip을 확대한다. node/control 수는 후보 필터이며 실제 bone hash/constraints/시각 재생 확인을 대체하지 않는다.

## 작업 기록과 확인하지 않은 부분

- master: Discord 검색·메시지 문맥·태그 목록 이미지·parser/Oodle 코드 확인 및 현재 제품 연결 분석.
- 병렬 연구 agent1명: DepotDownloader/SteamCMD·계정/용량/manifest 공식 자료 조사, 완료 후 종료. 공유 runtime/UI를 조작하지 않았다.
- 설치·Steam 로그인·대용량 게임 다운로드·태그 decoding·새 Minecraft 코드 변경·native QA는0회다. 기존 W189 봉인 QA는 변경하지 않았다.
- Discord UI 검색어 교체에서 처음 append된 검색을 clear 후 바로잡았다. 영상 UI 재생 실패는 새로운 소스로 우회해 실제 모션 확인했다고 쓰지 않았다.
