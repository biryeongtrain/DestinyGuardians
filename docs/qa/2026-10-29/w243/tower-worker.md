# W243 타워 디테일 작업자 — 1차 Vision 인계

초기 인계 기록: 제품·테스트 3개 파일을 master 통합과 1차 Vision 검수를 위해 고정했던 시점의 내용이다. 최신 수관·재질 변경과 현재 해시는 아래 추가 절을 우선한다. 다섯 공간을 구현했으며, 중앙 광장 수목의 크기와 시각적 위계는 화면 피드백 후 판단한다. 최종 Vision 수락 완료를 뜻하지 않는다. 작업자 수정 범위는 아래 3개 파일과 이 문서뿐이다. 원본 main은 읽기 전용으로 사용했으며, 게임·클라이언트·lease·서버·월드 백업/적용 및 commit/reset/clean/stash/push는 수행하지 않았다.

## 출처와 실제로 검토한 근거

- [Eve Astra — Destiny 2: The Tower, Courtyard District](https://ninehydras.artstation.com/projects/JqOba): 작가 설명에서 Courtyard의 환경 제작·마무리, 상점 공간, 외벽·협곡 담당을 확인했다. **설명에서 추정한 것이 아니라, 브라우저에서 실제 포트폴리오 이미지 두 장을 보았다.** 첫 장은 산을 배경으로 한 파손된 타워 외벽으로, 주황·붉은 천 띠, 노출 배관, 가는 금속 난간이 보인다. 둘째 장은 어두운 지붕 아래 광장 진입부로, 중앙 바닥 패널, 오른쪽 붉은 상점 커튼, 왼쪽 파란 표지, 낮은 난간, 장비 상자, 머리 위 케이블이 보인다. 두 이미지 모두 Bungie/Destiny 2 표기가 보였다. 산업적인 재료, 천 색띠, 바닥 패널과 정비 소품의 근거로 사용했다. 별도 캡처 파일은 저장하지 않았으며, 이 채팅의 브라우저 도구가 반환한 화면을 검토한 기록이다.
- [Marc Thompson — Destiny 2: The Tower Social Space](https://marcthompson.artstation.com/projects/VRWon): Brandon Campbell과의 구성·매스 배치·건축 구성·마무리 협업이라는 **설명만 확인**했다. 프로젝트 실제 이미지는 시각 검토하지 않았으므로 이미지 근거로 세지 않는다.
- 배정 시 ArtStation Python fetch의 403 실패가 전달됐다. 웹 추출은 작가 설명만 반환했고, 일반 이미지 검색에서는 해당 작가 이미지와의 신뢰할 수 있는 연결을 확보하지 못했다. 위 Eve 브라우저 이미지 열람은 성공했다. Marc 이미지는 미확인이다. 추가 조사는 인계를 막지 않으며, 필요한 공식 이미지 UI 조사는 master가 진행한다.
- 직접 열어 본 기존 로컬 이미지: `docs/qa/2026-10-29/w232/final-spawn.png`, `top.png`, `walkways.png`, `source-review/courtyard.png`. 마지막은 기존 원본 GLB 검토 이미지로, 길게 이어진 식재 구역, 콘크리트 가장자리 녹지, 중앙 동선, 천막과 산업 시설형 테라스를 확인했다. 작업자는 해당 PNG를 보았으며 **GLB를 새로 열거나 다시 렌더링하지 않았다.** 플랜터·수목·정원 보행로·테라스 해석에 사용했다.
- 원본 코드·문서: `TowerVoxelMap`, `TowerChunkGenerator`, `TowerSpawnWorld`, 디코더 테스트, `docs/design/W232_Tower_스폰월드.md`, manifest와 기존 카메라·보행로 기록을 검토했다. 바이너리를 읽기 전용으로 해석해 바닥 후보를 찾았으며, 실제 Java 배치 계획은 모든 바닥·목표 좌표에 `TowerVoxelMap.paletteIndexAt`을 사용한다.

## 구현과 실제 배치 계획 개수

| 공간 | 후보 블록 수 | 구현 구성 |
| --- | ---: | --- |
| 도착부·중앙 광장 앞 | 233 | 흰색 슬래브 테두리 플랜터와 수목 2개, 벤치, 따뜻한 금속 조명 2개, 바닥 패널. 스폰 `(70.5,75,-19.5)`, yaw150 유지. |
| 북쪽 상점 전면 | 298 | x28/43/58의 붉은색·주황색 천막 3개, 카운터, 청록 화면 포인트, 장비 상자, 전면 바닥 패널, 조명 1개. |
| 서쪽 하단 정원 보행로 | 160 | 수목 플랜터, 꽃 플랜터, 벤치, 따뜻한 조명, 바닥 패널. |
| 남쪽 전망 휴게 공간 | 157 | 수목 플랜터, 벤치 2개, 가는 휴게 구역 난간, 조명, 바닥 패널. |
| 동쪽 하단 정비 공간 | 59 | 상자 묶음 2개, 낮은 배선 덮개, 정비 작업대, 작업 조명 2개. 원래 어두운 바닥 유지. |
| **합계** | **907** | **133개 조각. 다섯 구역 모두 실제 계획에 포함.** |

이 수치는 결정론적 배치 계획의 후보 좌표 수이며, 실제 서버에서 쓰기에 성공한 개수는 아니다. 초기의 엄격한 통째 배치 검사에서 정비 공간 배선·조명이 부적합한 원본 좌표 때문에 제외되어, 검증된 바닥으로 옮긴 뒤 타깃 검사를 통과했다. 최종 구성에는 다섯 공간 모두 포함된다. 북쪽 상점 동쪽 조명 등 원본과 겹치는 후보는 의도적으로 제외되며, 억지로 배치하려고 빈 바닥을 메우지 않는다.

`TowerDetailPass.java`는 측정한 불변 배치 계획, 조건부 분할 적용, 차원 SavedData 이력을 담당한다. `TowerSpawnWorld.java`는 시작·틱·종료 연결을 추가한다. `TowerDetailPassTest.java`에는 필요한 검사 2개를 넣었다. 수목은 도착부 서쪽·동쪽, 하단 정원, 남쪽 전망 구역에 총 4개다. 중앙 수목의 시각적 위계는 1차 Vision에서 우선 확인하며, 피드백 전 제품 파일은 수정하지 않는다.

## 원본·편집 보존과 실행 방식

- 원본 **1,151,116개** 복셀과 번들 바이너리·manifest·생성기·건물·계단·스폰은 유지한다. 제한된 노출 smooth_stone 바닥 좌표만 높이를 유지하는 온전한 블록으로 재질을 바꾼다.
- 추가 소품은 모든 목표 좌표가 원본 공기여야 하며, 해당 바닥은 원본 smooth_stone·black_concrete·iron_block 중 하나여야 한다. 원본과 충돌하면 소품 전체를 제외한다. 바닥 패널은 원본 smooth_stone이고 위 두 칸이 공기일 때만 허용한다. 중복 목표와 스폰·귀환 후보 주변 x/z ±8 사각형은 제외한다.
- 신규·기존 영구 타워 모두 소품 적용 전 실제 `getBlockState`를 원본 예상 상태와 정확히 비교하고, 각 쓰기 직전에도 재확인한다. 바닥이나 목표 블록을 편집했다면 그 편집을 우선한다. 기존 월드 초기화·공기 비우기·재생성·전면 교체는 없다.
- 차원별 `destiny:tower_courtyard_details_v1` SavedData에 검토한 좌표를 기록하며, 충돌로 건너뛴 좌표도 포함한다. 정상 저장·재시작 뒤에도 삭제한 장식을 다시 만들거나 건너뛴 편집 좌표를 재시도하지 않는다. 미술을 강제로 재적용하려고 이 이력을 삭제하지 않는다. 저장되지 않은 강제 종료는 정상 저장 보장 범위 밖이며 실제 강제 종료 검사는 하지 않았다.
- 틱당 **최대 48개 미처리 좌표**, 쓰기 루프에는 2ms 예산을 둔다. 틱당 새 비동기 FULL 청크 티켓 요청은 최대 1개다. 메인 스레드를 막는 `getChunkFuture`나 백만 블록을 한 틱에 쓰는 루프는 없다. 작업 전용 비영구 티켓으로 작업 중 차원을 유지하고, 조각 완료·서버 종료 시작 시 해제한다. 2ms는 루프 예산이며 청크 요청·개별 블록 갱신까지 실측 보장한 상한은 아니다.
- 영구 월드 백업·적용과 CU/Vision은 master만 담당한다. master가 `/private/tmp/destiny-w243/production-tower-before.zip` 백업과 `/private/tmp/destiny-w243/tower-main-before.json` 기준선을 보고했으며, 작업자는 그 파일을 수정하거나 검증하지 않았다.

## 필요한 타깃 검사

격리 환경에서 성공한 명령이며 전체 gate는 실행하지 않았다.

```sh
rtk proxy ./gradlew -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow/libs/gcb-server test --tests kim.biryeong.destiny.world.TowerDetailPassTest --tests kim.biryeong.destiny.world.TowerVoxelMapTest --console=plain --max-workers=2
```

- 디테일 검사 **2/2**, 기존 디코더 검사 **3/3**, 합계 **5/5 통과**. master도 14:50경 최종 디테일 XML의 2/2 통과를 별도로 확인했다. 컴파일은 격리된 `libs/gcb-server`·`libs/minigame-lib`를 사용했으며 공유 원본 의존성을 빌드하지 않았다.
- 실제 번들 맵의 구역별 개수, 중복 없는 목표, 원본 바닥·공기 조건, 노출 바닥만 교체하는 조건, 바닐라 블록 상태 파싱, 스폰 보호 사각형, 틱 작업 상한 상수, 조건부 쓰기, 편집 블록·제거된 바닥 거부, 삭제·건너뛴 좌표를 보존하는 이력 codec 왕복을 검사했다.
- 초기 컴파일에서 26.3의 `ChunkPos` 생성자와 색상 블록 상수 차이를 발견해 수정했다. 첫 개수 검사는 정비 공간이 16블록뿐이어서 올바르게 실패했고, 측정 좌표로 이동·작업대 추가 후 59블록이 됐다. 실패한 실행을 통과로 표시하지 않는다.
- 작업자는 신규 GameTest·Minecraft 세션·전체 gate·GLB 재렌더링·벤치마크를 수행하지 않았다. 초기 인계를 위해 추가 검사·조사는 필요하지 않다. 이후 master가 전체 JUnit 통과와 통합 1차 Vision 시작을 보고했다. 이는 master 보고이며 작업자가 별도 재실행한 결과는 아니다.

## master용 카메라 좌표 5개

아래는 발 좌표와 시선이다. 원본 복셀 바닥과 발·머리 두 칸의 공기를 읽기 전용으로 확인했으며, **실제 충돌·화면 수락 결과는 아니다.** `destiny:tower`에서 적용 완료 로그를 확인한 뒤 판단한다. 실제 월드의 편집·조건부 건너뛰기로 적용 수가 줄 수 있다.

| 공간 | 발 x,y,z | Yaw | Pitch | 검토 대상 |
| --- | --- | ---: | ---: | --- |
| 도착부·중앙 | `70.5,75,-19.5` | 150 | 0 | 원래 스폰 구도, 서쪽 수목64/-38. 동쪽을 돌아 두 번째 수목78/-32와 중앙 동선 확인. |
| 북쪽 상점 | `43.5,75,-88.5` | 180 | 0 | 천막 3개, 카운터, 조명, 전면 바닥 패턴. |
| 서쪽 정원 | `23.5,73,-32.5` | 90 | 0 | 수목17/-38, 꽃17/-22, 벤치20/-30, 통행 공간. |
| 남쪽 전망 | `80.5,75,-5.5` | -15 | 0 | 수목85/3, 벤치, 가는 휴게 구역 난간, 테라스 구분. |
| 동쪽 정비 | `78.5,71,-58.5` | 180 | 0 | 작업대78/-70, 상자, 배선 덮개, 따뜻한 작업 조명. |

master Vision 미검증 목록: 다섯 공간의 실제 렌더링과 중앙 수목 강조, 보행·계단·스폰 여유, 실제 청크 티켓 완료와 눈에 띄는 프리즈, 기존 월드 편집 건너뛰기, 재시작 디스크 저장·삭제 보존, 1차 피드백 반영과 2차 Vision 수락. 작업자는 1차 피드백에 대응할 수 있도록 대기하며, 이 절차 전 최종 완료로 보고하지 않는다.

## 통합용 SHA256

편집 전 TowerSpawnWorld의 기준 해시는 읽기 전용 main과 갱신된 worktree가 일치했다. 신규 파일은 없던 상태였다. 아래 해시의 제품·테스트 파일을 고정한다.

| 파일 | 변경 전 | 변경 후 |
| --- | --- | --- |
| `src/main/java/kim/biryeong/destiny/world/TowerDetailPass.java` | `신규 파일(없음)` | `8454c85daf7ae560086fee2366c3b8a432cb9eaaeda570a81ddb81c8a849f69b` |
| `src/main/java/kim/biryeong/destiny/world/TowerSpawnWorld.java` | `9d8c56d6298d600703b98ef0c9445da836415a1f14e3e4fcce3e58d7575b67c1` | `eaa0456c0898c99c36024249213049f8bad62829166a627eb6ea414f087e7b35` |
| `src/test/java/kim/biryeong/destiny/world/TowerDetailPassTest.java` | `신규 파일(없음)` | `c6c7e18616af72875dd8236e21f29bd8c32c3304f524d967a3a886270891bf3d` |

변경 없는 번들 manifest SHA256: `6911100020651d60ced0e992461055d0fd6f70e6d8c06ba8507c3aecc70e1484`.

변경 없는 번들 복셀 SHA256: `55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d`.

제품·테스트 3개 파일을 고정한 뒤에는 이 문서만 작성·한국어 번역했다. 자기 자신을 참조하는 해시를 피하기 위해 문서 해시는 별도로 반환한다.


## 1차 Vision 검토와 수관·재질 런타임 추가 — 최신 인계

### 실제 화면 검토와 판단

첨부 `/private/tmp/destiny-w243/tower-contact-first.jpg`를 실제로 열어 5개 공간의 전후를 검토했다. 상점 천막·카운터, 정원 식재, 전망 휴게 구성, 정비 소품은 그대로 수락한다. 도착부는 줄기 위에 대칭 수관이 얹힌 형태가 단순해 보여, 도착부 두 나무만 비대칭 옆가지·수관을 추가했다. master가 1차 실행에서 **907 변경·0 건너뜀, 약27초 완료, 이후 프리즈 미관찰**을 보고했다. 이는 master의 실행 결과이며 작업자의 독립 성능 측정이 아니다.

- 기존 배치 계획을 `initialPlan`으로 그대로 보존했다. 원래 133개 조각·907개 좌표의 순서와 내용이 동일함을 검사했다.
- 끝에 도착부 서쪽·동쪽 수관 조각만 추가했다. **나무당27개, 총54개** 새 공기 좌표이며, 이 중 각4개는 수평 옆가지다. 수관의 최대 가로 폭은 기존5칸에서7칸으로 늘고, 서로 높이가 다른 잎 덩어리와 작은 상부 돌출로 대칭을 줄였다.
- 새 좌표는 원본 공기·원본 지지 바닥을 확인하고, 실제 기존 줄기 `oak_log[axis=y]`도 읽기 전용 부착 조건으로 확인한다. 최소 y78로 보행 높이와 스폰 ±8 사각형을 침범하지 않는다.
- 기존 디테일 ledger를 그대로 사용한다. 기존907좌표는 재적용하지 않고 새54좌표만 고려한다. 기존 잎·줄기를 삭제하거나 교체하지 않는다. 줄기를 편집·제거했다면 해당 확장을 건너뛴다.
- 현재 디테일 계획 합계 **135개 조각·961좌표**: 도착부287, 상점298, 정원160, 전망157, 정비59. 다른4구역의 계획은 변경하지 않았다. 새 수관의 실제 모양은 2차 Vision 대기다.

### 재질 런타임 계약과 순서

사용자 추가 배정으로 `TowerMaterialPass.java`, `TowerMaterialPassTest.java`를 신설했다. `TowerDetailPass.java`의 제한 적용 드라이버를 최소 일반화해 티켓·저장 이력·조건부 쓰기를 재사용한다. 기존 소품은 통째 조건 검사, 재질은 **좌표별 조건 검사**를 사용하므로 패널 한 칸 때문에 청크 전체가 제외되지 않는다.

- 입력: `/data/destiny/tower/courtyard-materials-w243.json.gz`. gzip UTF-8 JSON의 `schema:1`, `sourceVoxelSHA256`, `palette`, `cells:[[x,y,z,paletteIndex],...]` 계약이다. 데이터·오프라인 생성기·VRWon 이미지 기반 색 구역 설계는 master 소유이며 작업자는 수정하지 않았다.
- 헤더 SHA와 실제 번들 `.vox.gz`의 SHA256이 모두 `55425ec1d14bc970ba05e90338e10a34468498d8a655d49ebc014d633996098d`와 일치해야 한다. **최대100000좌표**, JSON 최대16MiB, 중복·범위·정수·팔레트 인덱스·바닐라 상태를 검증한다.
- 모든 대상은 원본 상태가 정확히 `minecraft:smooth_stone`이고, 원본의 여섯 인접 방향 중 하나 이상이 공기인 노출면이어야 한다. 재질 팔레트는 충돌 모양이 온전한 한 블록이고 유체·공기·블록 엔티티가 없는 상태만 허용한다. 충돌 형상을 바꾸지 않는다.
- 압축 입력·SHA·전체 기하 검사는 비동기로 준비한다. 검증 실패·자료 누락 시 재질 적용만 생략하며 기존 월드를 바꾸지 않는다. 미완료 future를 기다리며 틱을 막지 않는다.
- 디테일 드라이버가 성공적으로 종료한 뒤에만 재질 쓰기를 시작한다. 따라서 원본 바닥이 먼저 칠해져 소품·옆가지 지지 조건이 실패하지 않는다. 재질은 **128좌표/틱·쓰기 루프2ms** 상한과 전용 비영구 비동기 청크 티켓을 사용한다.
- 별도 SavedData ID는 `destiny:tower_courtyard_materials_v1`이다. 디테일 이력을 초기화·변경하지 않는다. 실제 블록도 정확히 smooth_stone일 때만 쓰며, 기존907소품·패널과 사용자 편집이 다른 상태라면 해당 좌표만 건너뛰고 이력에 기록한다. 정상 저장·재시작 뒤 사용자가 원래 smooth_stone으로 되돌려도 재도색하지 않는다.

### 이번 타깃 검사와 미검증 범위

```sh
rtk proxy ./gradlew -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow/libs/gcb-server test --tests kim.biryeong.destiny.world.TowerDetailPassTest --tests kim.biryeong.destiny.world.TowerMaterialPassTest --console=plain --max-workers=2
```

**BUILD SUCCESSFUL, 디테일3/3 + 재질2/2 = 5/5 통과.** 전체 gate는 실행하지 않았다. 새 검사는 계약·SHA·팔레트·공기/비노출 대상·중복·상한 거부, 기존 패널/편집 건너뛰기, 재질 이력 재시작 왕복·되돌림 보존·디테일 이력 분리를 확인한다. 디테일 검사는 실제907이력을 다시 읽은 상태에서 새54좌표가 적용되고 기존907좌표가 유지됨을 확인한다.

최초 코드 타깃 검사 때는 master 재질 데이터가 없어 인메모리 gzip 계약 입력을 사용했다. 이후 master가 제공한 실제 데이터·감사 파일 2개만 허가대로 작업본에 동일 바이트로 복사했다. 실제 데이터의 최종 검증 결과는 아래 수신 데이터 절에 기록한다. 실제 서버의 건너뜀/변경 개수와 2차 Vision은 별도로 필요하다. 라이브 서버·월드·CU 조작은 수행하지 않았다. 5개 검수 카메라는 위 표와 동일하게 사용할 수 있다.

### 이번 통합 기준선과 작업자 결과 SHA256

아래 기준선은 초기 HEAD가 아니라 이번 반환 직전 읽은 **현재 main의 실제 파일**이다. 새 파일은 아직 없었다. master는 복사 직전 같은 해시인지 확인하고 소유 경로만 통합한다.

| 소유 파일 | 현재 main 기준선 | 작업자 결과 |
| --- | --- | --- |
| `src/main/java/kim/biryeong/destiny/world/TowerDetailPass.java` | `8454c85daf7ae560086fee2366c3b8a432cb9eaaeda570a81ddb81c8a849f69b` | `1334eb0d4afd86bea52175629a16c608a840d217ac1634a344c37800ea80b1c7` |
| `src/main/java/kim/biryeong/destiny/world/TowerSpawnWorld.java` | `eaa0456c0898c99c36024249213049f8bad62829166a627eb6ea414f087e7b35` | `6a787879a321dc947cd6e438195dade0d7557b642c1de21e70a459f0e4b73302` |
| `src/test/java/kim/biryeong/destiny/world/TowerDetailPassTest.java` | `c6c7e18616af72875dd8236e21f29bd8c32c3304f524d967a3a886270891bf3d` | `bce58b6eca6e8a48e07356208d081e761fa58bb15571c8760ce87fecc2fbbf20` |
| `src/main/java/kim/biryeong/destiny/world/TowerMaterialPass.java` | `없음` | `053d31c8b7493d3b34185e94e3891429dbbfa01fb0b8506aea9a9e68f8aa1d50` |
| `src/test/java/kim/biryeong/destiny/world/TowerMaterialPassTest.java` | `없음` | `1994e30ba8f3608047844c76c4593f468e9e050d533a20bf5d868d3c82af71ba` |

인계 문서는 계속 한국어로 유지한다. 원본 바이너리·manifest·master 생성기·재질 데이터는 작업자가 수정하지 않았다. 첫3개 제품 파일 동결은 사용자 수관/재질 수정 배정으로 이 절 범위에서만 해제되었다.


### master 재질 데이터 수신 — 최종 천막 구획 포함본

- 작업자가 새로 복사한 master 소유 파일은 허가된 `src/main/resources/data/destiny/tower/courtyard-materials-w243.json.gz`와 `docs/qa/2026-10-29/w243/tower-materials.json` 두 개뿐이다. 내용은 수정하지 않았다.
- 실제 데이터: **58,117좌표·142,933바이트·팔레트10종**, bounds `[-15,65,-125]`~`[125,111,22]`.
- 재질 분포: gray_concrete14,866, light_gray_concrete5,810, smooth_sandstone8,652, polished_andesite2,237, cut_sandstone4,618, white_terracotta14,539, orange_terracotta1,407, red_terracotta1,949, smooth_quartz3,196, polished_deepslate843. 색 구역 설계·자료의 미술 근거는 master 소유 감사 파일을 따른다. 작업자가 VRWon 실제 이미지를 새로 보았다는 뜻은 아니다.
- gzip SHA256 `a0ecb154be54569b4bb183fdbc33dd03b750da6c97a4024f0fd7e79b5ad429f4`, 감사 JSON SHA256 `44328100348baa6d244ddeec6e9763c85243b0afc69b81a70dbbc222023f10bf`. main/작업본의 동일 바이트를 확인했다.
- 실행 완료 로그: `타워 디테일 적용 완료` 뒤 `타워 재질 적용 완료`. 후자의 변경·건너뜀 숫자가 실제 적용 결과다. 준비 로그의 후보58117을 실제 변경수로 간주하지 않는다. 디테일은 기존907이력 뒤 새54좌표를 추가하고, 재질은 별도 이력으로 시작한다.

- 최종 데이터에는 천막 구획의 황토색 패널1,407좌표·산화 적색 패널1,800좌표·구조 띠326좌표가 포함된다. 기존 원본 노출 smooth_stone을 높이·구역별로 칠하는 오버레이이며, **원본 덤프의 정확한 dye·PBR·텍스처 복원이라고 주장하지 않는다.**
- master는 Marc VRWon 실제 이미지3장을 `/private/tmp/destiny-w243/references/marc-0.jpg`, `marc-1.jpg`, `marc-2.jpg`에서 확인했고 주황 타프·붉은 난간·크림 콘크리트·어두운 데크를 근거로 삼았다고 보고했다. 이는 master의 이미지 검토 보고다. 작업자는 이번 런타임 변경 중 해당 이미지를 새로 열람하지 않았으며, 앞의 작업자 직접 열람 범위와 구분한다.


### 최종 확인

최신 천막 구획 포함 gzip(10종·142,933바이트, SHA `a0ecb154be54569b4bb183fdbc33dd03b750da6c97a4024f0fd7e79b5ad429f4`)을 실제 번들 리소스로 읽는 최종 재질 타깃 검사 **2/2 통과, BUILD SUCCESSFUL**.


최종 실행은 위 명령의 `--tests kim.biryeong.destiny.world.TowerMaterialPassTest`만 지정했다. 자료가 갱신되어 실제 번들 입력만 다시 검증한 것이며 제품 코드는 변경하지 않았다. 그 직전 동일 제품·테스트 코드의 수관3/3·재질2/2 총5/5가 통과했다. 최종 출력:

```text
[15:13:58] [Test worker/INFO]: [STDOUT]: TOWER_MATERIAL_SHIPPED_CELLS=58117 chunks=87
```

전체58,117좌표를 파싱하고 실제 번들 원본 SHA·노출 smooth_stone·팔레트 full-block을 통과했다. 이는 실제 월드 변경수 확인이 아니다. 디테일·수관961좌표(기존907+추가54)와 재질58,117후보를 master의 같은 배치로 통합할 수 있다. 현재 main의 기준 해시는 위 표와 여전히 일치하며, 신규 재질 파일2개는 main에 아직 없다. 제품·테스트5파일과 이 문서를 반환하며 이후 피드백 전까지 고정한다. 실제 변경/건너뜀 로그·기존 월드 재시작 보존·2차 Vision은 master 검수 대기다.
