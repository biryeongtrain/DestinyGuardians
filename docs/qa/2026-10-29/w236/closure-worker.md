# W236 resource-pack model closure sidecar

2026-10-29. Worker worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`.
새 파일 세 개만 소유하며 commit하지 않았다.

- `scripts/qa/pack_model_closure_w236.py`
- `scripts/qa/test_pack_model_closure_w236.py`
- `docs/qa/2026-10-29/w236/closure-worker.md`

## 검사 범위와 메모리

표준 Python 라이브러리만 사용하는 standalone ZIP 검사기다. ZIP을 `r` 모드로 열고
`assets/<namespace>/items/**/*.json`의 모든 분기를 순회한다. 기본 namespace를
생략한 `model`/`special` 타입도 Minecraft 타입으로 처리한다. Geometry 타입의
문자열 `model`, special 타입의 문자열 `base`만 geometry 참조로 수집하고, custom
모델의 일반 `parent`를 끝까지 추적한다. 선택기와 special renderer의 객체형
`model`을 경로로 변환하지 않는다. 잘못된 참조 타입·JSON, parent cycle, 중복
item/model ZIP 경로, 아이템이 없는 입력은 실패로 보고한다.

`minecraft:` 참조는 vanilla 외부 의존성으로 건너뛴다. ZIP에 Minecraft namespace
모델이 있더라도 그 모델의 내부 parent는 검사하지 않는다. 무명 resource location의
namespace는 소유 item namespace가 아니라 `minecraft`다. Custom 누락에는 예상 ZIP
경로, 최초 발견 item, parent chain을 기록한다. 같은 누락은 한 번만 보고한다.

아이템은 ZIP stream에서 **파일 하나씩** `json.load`하고 다음 아이템 전에 JSON과
loop subtree 참조를 해제한다. 도달한 모델도 하나씩 파싱하고 **parent 문자열만**
캐시한다. 전체 모델 JSON tree나 전체 아이템 JSON 집합은 보관하지 않는다. ZIP
중앙 디렉터리, unique ref set, 아이템별 작은 수치 행은 메모리에 남는다. 단일
아이템 JSON 자체는 메모리에 파싱하므로 token 단위 상수 메모리 파서는 아니다.

보고서는 ZIP SHA-256/bytes/entry count/raw bytes, 전체 아이템 raw/compressed bytes와
개수, geometry/special/ref 발생 수, 고유 직접 참조 수, tint source 발생 수와 타입,
아이템당 최대 크기·고유 참조·tint 수와 각각 상위 10개, 폴더별 bytes/count, custom
closure 및 누락·오류를 포함한다. 최대값 동률은 경로순으로 안정적으로 정렬한다.
Tint는 geometry의 `tints` 배열 원소 발생 수이며 unique 색상/인덱스 수가 아니다.

## 실행과 최적화 전후 비교

아래 명령은 지정 worker worktree에서 실행한다. 출력 파일의 부모 디렉터리는
미리 존재해야 한다. `--report`가 없으면 전체 JSON을 stdout에 출력한다.

```sh
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 scripts/qa/test_pack_model_closure_w236.py -v
rtk proxy env PYTHONDONTWRITEBYTECODE=1 /usr/bin/time -l python3 scripts/qa/pack_model_closure_w236.py /Users/qf/IdeaProjects/DestinyGuardians/run/server/polymer/resource_pack.zip --report /tmp/w236-pack-model-closure-baseline.json
rtk proxy env PYTHONDONTWRITEBYTECODE=1 python3 scripts/qa/pack_model_closure_w236.py /tmp/master-optimized-pack.zip --compare /tmp/w236-pack-model-closure-baseline.json --report /tmp/w236-pack-model-closure-optimized.json
```

`--compare`는 같은 schema의 baseline JSON을 읽고 정수 지표의 current-minus-baseline
delta와 missing added/resolved를 추가한다. 입력 ZIP이나 baseline report를 출력으로
덮어쓰는 요청은 거부한다. 종료 코드는 `0` closure 정상, `1` 누락/데이터 오류,
`2` CLI/I/O 오류다. Baseline과 최적화팩 각각의 closure 정상 여부도 확인해야 한다.

이 도구는 ZIP에 남아 있는 모든 item을 검사한다. Java optimizer의 runtime exact
root 목록, 삭제된 item의 runtime 필요성, selector 동등성은 master 소유다. 모델의
texture/override/blockstate 의존성이나 클라이언트 렌더링·OOM 해결 여부는 이
geometry/base/parent 검사 범위에 포함하지 않는다. 최적화팩은 아직 제공되지
않았으며 이 worker가 검사했다고 주장하지 않는다.

## 원본 baseline 실측

- 입력: `/Users/qf/IdeaProjects/DestinyGuardians/run/server/polymer/resource_pack.zip`
- SHA-256: `09314656691c188495a8080768886967c6994e2c32e6317cd8326e765187cf6f`
- ZIP: **183,520,674 bytes**, **167,692 entries**, **1,851,217,319 raw bytes**.
- Items: **1,119**, **1,569,744,537 raw bytes**, **47,156,869 compressed bytes**.
- `assets/destiny/items/weapon_hands_w201`: **297 items**, **1,537,916,857 raw bytes**.
  요청의 414개 예상과 달라 실제 ZIP 기준 수치와 해시를 명시한다.
- Geometry/ref 발생: **395,587**; special base: **0**; unique 직접 custom ref: **163,548**.
- Tint source 발생 합계: **21,183,748**; 단일 item 최대: **928,512**.
- Custom closure: **163,841**개 모델 로드, **222,806,185 raw bytes**, **157,892 parent edges**.
- Vanilla unique ref skip: **1**; custom 누락 **0**, 오류 **0**, 종료 코드 **0**.
- `/usr/bin/time -l`: **22.48s real**, **21.48s user**, **0.95s sys**;
  maximum RSS **882,442,240 bytes** (약 **841.56 MiB**), swap **0**.
  이 RSS는 Python 검사기 측정값이며 Minecraft 클라이언트 heap 측정값이 아니다.
- 실행 중 input device/inode/size/mtime/ctime 변화 없음. 별도 사후 SHA-256도 대조한다.

최대 항목:

| 지표 | item ZIP 경로 | 값 |
|---|---|---:|
| Raw bytes | `assets/destiny/items/weapon_hands_w201/weapon_sight_w148/whispering_slab_bow.json` | 67,629,921 |
| Unique refs | `assets/destiny/items/weapon_hands_w201/weapon_izanagi_w91/izanagis_burden.json` | 4,602 |
| Tint source count | `assets/destiny/items/weapon_hands_w201/weapon_aim_w70/biting_winds_bow.json` | 928,512 |

상세 결과와 증거는 `/tmp`에 보관한다.

- `/tmp/w236-closure-baseline-input.json`: 실행 전 원본 bytes/mtime/SHA-256.
- `/tmp/w236-pack-model-closure-baseline.json`: 전체 baseline 보고서.
- `/tmp/w236-pack-model-closure-baseline.stdout`: baseline summary.
- `/tmp/w236-pack-model-closure-baseline.time`: 시간·메모리 측정.
- `/tmp/w236-closure-worker-tests.log`: 4개 테스트 실행 결과.
- `/tmp/w236-closure-worker-verification.json`: 사후 원본 hash 및 소유 세 파일 hash/검사.
- `/tmp/w236-closure-worker-sha256.txt`: 소유 세 파일 SHA-256 manifest.
- `/tmp/w236-closure-worker-delta.tar.gz`: 위 세 파일만 포함한 반환 delta.

## 검증과 제약 반환

의미 있는 합성 ZIP 테스트 **4개 통과**: 중첩 geometry 누락과 vanilla skip·객체형
model 오인 방지, parent 누락/성공/cycle과 unreachable model 제외, special base의
parent 추적과 객체형 renderer/잘못된 base 타입, bytes/ref/tint 수치·비교 report·CLI
실패 코드·입력 ZIP 보존. 테스트 ZIP은 OS 임시 디렉터리만 사용하며 종료 시 정리한다.

소유 세 파일은 시작 시 모두 없었다. 반환 manifest에는 신규 파일의 SHA-256을
기록한다. 이 세 파일 이외 worktree 파일은 작성·수정하지 않았다. main·실서버·client·
프로젝트 fixture·소스 모델·기존 generator·Java optimizer를 변경하지 않았다. 모델
삭제, ZIP 수정/재생성, Java build/test, GUI/Vision QA, git index 변경, commit, stash,
reset, clean, push를 수행하지 않았다. 원본 ZIP은 읽기만 했고 별도 server/client를
시작하거나 종료하지 않았다.
