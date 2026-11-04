# Windows 실행 절차 (PowerShell)

아래는 경로를 실제 환경에 맞게 채우는 예시다. 실행 전 각 도구 --help를 확인한다. Windows에는 Mac 전용 rtk를 설치할 필요가 없다. 참조 문서의 POSIX 줄연결 `\` 대신 아래 PowerShell 배열 인수를 사용한다.

## 1. 환경과 입력 고정
`D:\DestinyAnimWork` 같은 독립 경로에 tools/extracted/out/return을 둔다. 게임 packages는 읽기 전용으로 취급하고 package 목록·게임 buildID·디스크 용량을 기록한다. Steam 업데이트 중인 packages를 섞어 읽지 않는다.
기존 설치 예시: `C:\Program Files (x86)\Steam\steamapps\common\Destiny 2\packages`. 실제 Steam 라이브러리는 다를 수 있다.

## 2. 다운로드가 필요한 경우
[DepotDownloader3.4.0](https://github.com/SteamRE/DepotDownloader/releases/tag/DepotDownloader_3.4.0)의 Windows 배포를 사용한다. 먼저 manifest-only와 manifest 결과를 확인한다. 예시:

```powershell
$SteamUser = Read-Host 'Steam account name (password is not requested here)'
$DepotTool = 'D:\Tools\DepotDownloader\DepotDownloader.exe'
& $DepotTool -app 1085660 -depot 1085661 -os windows -osarch 64 -username $SteamUser -manifest-only -dir 'D:\DestinyAnimWork\manifest'
```

실제 로그인은 공식 도구의 대화형 절차를 따른다. 비밀번호 인수·인증 transcript를 저장하지 않는다. 자동 인증이 안 되면 사용자에게 맡긴다. manifest에서 필요한 base/patch 파일 경로를 정확히 적은 filelist를 만든 뒤 `-filelist`로 선택 다운로드한다. `0145_2.pkg` 한 파일만으로 충분하다고 가정하지 않는다. skeleton/rig 패키지 위치는 별도로 찾아야 한다.
언어 depot1085662는 실제 의존성이 확인될 때만 받는다. historical manifest는 Charm README의 값이 실제 접근 가능한지 별도 확인한다.

## 3. Charm/QuickTag/tiger-pkg로 태그 확보
Charm 지정 ref와 pinned commit은 data/tool-lock.json 및 evidence/CHARM_USER_VERSION.md 참조. packages path와 export path를 독립 경로로 지정한다. **먼저 Settings → Exporting → Export Animations와 GEAR 화면의 별도 Export Animations를 켠 뒤 무기를 export한다.** 기본 FBX와 `<name>_FirstPerson.fbx`를 원본 그대로 저장한다. Blender에서 실제 animation stack/keys/reload 모션을 확인한다. 직접 FBX 경로가 성공하면 별도 parser가 필수 선행 단계는 아니다.
이어서 raw 보존을 위해 Main Menu → Ctrl+D → hash 입력 → H 경로를 시도한다. `<ExportPath>/temp/`의 실제 bin을 보존하고 clip/skeleton/runtime rig를 각각 확보한다. 파일연결 hex editor가 실행되지 않더라도 bin 작성 여부는 별도 확인한다. 해시 탐색으로 class/entry/reference도 기록한다.
Charm에서 raw3종 확보가 안 되면 QuickTag 또는 tiger-pkg로 전환한다. tiger-pkg의 실제 CLI 도움말부터 확인한다:

```powershell
Set-Location 'D:\DestinyAnimWork\tools\tiger-pkg'
cargo run --release --example unpack_tag -- --help
```

도움말에 나온 `-v` enum값으로 **실제 게임 버전**을 선택한다. parser의 d2_eof가 tiger-pkg에도 동일 문자열이라고 가정하지 않는다. unpack_tag의 positional packages_path/tags, `-o` output을 사용한다. 소스가 `u32::from_be(u32::from_str_radix(...))`를 사용하므로 hash byte order를 확인한다. 추출 로그의 package0145/entry0567 및 크기 등으로 candidate를 대조하되 커뮤니티 보고와 현재 build 차이도 허용·기록한다.
기본/패치 파일은 원래 이름을 유지하며 같은 build로 갖춘다. Oodle DLL은 대응하는 사용자 게임 파일에서 확보하고 이름/버전/해시만 기록한다(반환 ZIP에는 넣지 않는다).

## 4. Python parser 준비
`scripts/setup_parser.ps1 -WorkRoot D:\DestinyAnimWork`는 parser만 clone/venv 설치한다. Steam/Charm/SDK를 자동 설치하지 않는다. vendor의 원본 parser ZIP을 직접 풀어 사용해도 되며 실제 경로를 기록한다.

```powershell
& .\scripts\setup_parser.ps1 -WorkRoot 'D:\DestinyAnimWork'
& .\scripts\run_parser.ps1 -ParserRoot 'D:\DestinyAnimWork\tools\tiger-animation-parser' -Clip 'D:\DestinyAnimWork\extracted\actual-clip.bin' -Skeleton 'D:\DestinyAnimWork\extracted\actual-skeleton.bin' -Rig 'D:\DestinyAnimWork\extracted\actual-rig.bin' -OutputBase 'D:\DestinyAnimWork\out\hc_reload' -GameVersion 'd2_eof'
```

위 actual-* 경로는 예시이며 실제 unpacker 출력명으로 바꾼다. rawJSON/retargetJSON도 각각 다른 output basename으로 보존한다. parser의 실제 `--help` enum을 확인한다. d2_eof는 입력 build 대응 여부를 확인한 경우에만 선택한다. PowerShell7을 권장하며, 실행 정책 때문에 스크립트가 차단되면 내용을 검토해 해당 명령을 직접 실행한다. 시스템 전체 실행 정책을 변경할 필요는 없다.
로그에 예외·unsupported codec/rig branch가 있는지 확인한다. `hc_reload.gltf` 존재만으로 정상 동작을 확정하지 않는다. glTF에 외부 .bin이 있으면 함께 보존한다.

## 5. Blender 시각 확인과 범위 확대
원본 skeleton/animation을 그대로 import해 rest pose, root scale·axis, 손목·무기·탄창·실린더 track을 확인한다.0/25/50/75/100% 프레임과 실제 playback을 저장한다. 매끈해 보이는 수동 보정본이 있다면 원본과 별도 파일로 둔다.
bone hash/부모관계/constraints·손 접촉으로 rig 호환을 판단한다. node 수 일치만으로 확정하지 않는다.1P/3P 및 실제 무기 고유성을 확인할 근거가 부족하면 unknown이다.
P0 성공 후 무기군별 후보를 병렬 분류할 수 있다. 검색한 tag/class/package/버전·성공/실패를 인덱스로 남기고, 이미 같은 rig-family인 65무기를 모두 독립 추출하려고 시간을 쓰지 않는다.

## 6. 반환
RETURN_CONTRACT.md에 따라 `return/manifest.json`과 폴더를 채운 뒤 `py -3.13 .\scripts\pack_return.py D:\DestinyAnimWork\return --output D:\DestinyAnimWork\destiny-animation-return.zip` 실행. 도구가 만든 ZIP을 최종 답변에 첨부한다. 인증 캐시/원본 pkg/DLL은 return에 복사하지 않는다.
