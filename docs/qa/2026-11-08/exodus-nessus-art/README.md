# Exodus Crash — Nessus art pass

작업 시작 2026-11-08, 서버/블렌더 검토 2026-11-09 KST까지 진행. 기존 베이크 재구축 커밋 `3440ab925` 위에 적용했다. **NBT/서버 검증 통과, 실제 클라이언트 화면 검토는 Mac 잠금 해제 대기** 상태다.

## 아트 기준과 적용

- [Steven Klipowicz — Nessus Natural Palette](https://sklipowicz.artstation.com/projects/O433e): 브라우저에서 실제 작업 이미지를 확인했다. 붉은 잎과 지면, 어두운 수피, 회백색 암석 및 상아색 벡스 표면의 대비를 참고했다.
- [Anthony Pitts — Lost Sectors, Nessus](https://pittskrieg.artstation.com/projects/9bNKN): Carrion Pit의 엑소더스 블랙 내부 이미지를 확인했다. 차가운 금속 표면과 어두운 공간, 따뜻한 잔해/광원 대비를 참고했다.
- [Mike Poe — EDZ and Nessus Relights](https://mjcr24.artstation.com/projects/ELOn5N): 네소스 동굴의 어두운 전경과 밝은 출구, 국소 광원 배치를 확인했다.

참고 이미지를 배포 텍스처로 복사하지 않았다. Downloads의 원본 GLB, Blender 파일 및 베이크 PNG는 수정하지 않았다. 원본 베이크/형상 위에 **Minecraft용으로 저작한 표면·식생·광원**을 적용했으며, 이를 Destiny의 원래 셰이더 출력을 복원한 것으로 간주하지 않는다.

초안에서는 사암이 지나치게 노랗고 crimson roots가 자주색으로 보여 폐기했다. 최종본은 회백색 calcite/quartz 암석, 옅은 청록 벡스 표면, andesite/청록 회색 금속과 어두운 deepslate, 붉은 terracotta 지면 및 바이옴으로 물든 잎을 사용한다. 내부의 기존 청색/적색 페인트와 구리 잔해는 보존한다. 협곡의 선체 잔해까지 숲으로 채우지 않고, 식생은 원본의 야외 자연 지표가 확인되는 후반 외부 구역에 한정했다.

베이크 샘플 77개 타일의 terrain/up/down 분류를 재사용한다. 원래 full/slab/철창/벽/체인 형상을 보존하며, 슬랩의 bottom/top/double 속성도 유지한다. 큰 연속 무늬로 재질을 나눠 작은 무작위 점무늬를 줄였다.

최종 저작량: 붉은 지면 30,721칸, 작은 식생 7,651개, 관목 군집 216개, 나무 33개. 실제 추가 블록은 30,589개다. 경로 주변 반경 4칸과 모든 마커 주변 반경 6칸, 총 28,704개 열에는 새 식생을 넣지 않는다. 기존 길·스폰·발전기·방벽 좌표와 전체 2,488칸 경로는 그대로다.

기존 균일한 level-14 보조광 309개를 level-11로 낮추고, 기존 천장의 full block 40개를 발광 재질로 교체했다. 바닐라 블록 광원은 색을 전파하지 않으므로 실제 색 조명/GI로 표현하지 않는다.

## 실제 런타임 연결

`NbtTemplateChunkGenerator`에 바이옴 키를 받는 공용 생성자만 추가했다. 기존 생성자는 THE_VOID를 유지한다. `ExodusTemplateGenerator`가 Exodus 전용 `destiny:nessus`를 선택한다. NBT의 biome 필드만 바꾸면 생성기의 FixedBiomeSource가 덮어쓰므로 두 곳 모두 연결했다.

26.3 로컬 Minecraft 원본 바이옴 JSON의 현재 codec 형식을 기준으로 `worldgen/biome/nessus.json`을 작성했다. 하늘/안개는 environment attributes, 물/잎/풀 색은 effects를 사용한다. feature/carver/자연 스폰은 비어 있다. 새 클라이언트 텍스처나 외부 셰이더팩은 추가하지 않았다. 기존 활동과 일반 바이옴의 색을 전역으로 바꾸지 않는다.

## 검증

- `compileJava compileGametestJava test --tests '*Exodus*' --tests '*Strike*' jar`: 통과. 이번 실행 XML 기준 8 suite / 28 unit tests, 실패 0. `targeted-tests.json`에 실제 목록을 보관했다.
- `test_baked_source.py`: 3개 통과. 비색인 삼각형/축/UV, 효과 레이어 배제, 알파와 선형색 평균 검사를 유지했다.
- `verify_exodus_map.py`: 실제 NBT 13,686 section의 **모든 블록**을 final.npy와 비교해 일치했다. 7,601,493 non-air blocks. 전체 경로의 바닥/머리 공간, 슬랩 물리 높이, 333 마커, 4개 방벽 좌표 검사를 통과했다. 방벽을 다른 경로로 우회할 수 없다는 전수 인증은 아니다.
- `verify_exodus_finish.py`: 변경 전 배열과 독립 비교. 원래 모든 충돌 형태/슬랩 속성 보존, 경로 배열 동일, 보호 열의 새 형상 0, 추가 물체가 지정 식생 3종뿐임을 확인했다.
- 실제 `runGameTest`, filter `destiny-test:exodus_nbt_game_tests*`: **1개 통과**. 실제 Fantasy 생성/MapTemplate 로드, 시작 구역 경로·입장 좌석의 바닥/머리 공간, 입장 좌석의 Nessus 바이옴을 확인한다. 전체 1.6km를 네이티브 입력으로 이동한 검사는 아니다. XML의 실제 test time은 1.56초이며 172초는 공용 리소스 준비를 포함한 suite time이다.
- 초기 GameTest는 필터 이름을 수정하기 전 선택 0개로 종료했다. 다음 실행은 공용 무기 profile graph 생성이 기본 120초를 넘겨 중단됐다. 최종 실행만 pack 대기 상한 600초를 주었고 통과했다. 제품 코드나 검사를 생략해 이 대기를 우회하지 않았다. 실제 GameTest 작업 폴더는 Loom 기본 격리 QA 경로 `build/run/gameTest`였다. JavaExec workingDir override가 Loom에서 재설정됨을 확인했으며, 별도 시각 QA 서버에는 **loom runDir**를 설정해 `/tmp/exodus-nessus-art/server`임을 lsof로 확인했다.
- 이번 아트 작업에서 전체 unit suite를 다시 실행하지 않았다. 앞선 베이크 재구축 QA의 전체 suite 3개 실패는 그대로 이전 기록에 남아 있으며 이번 targeted 통과로 해소됐다고 주장하지 않는다.

## Blender 검토와 한계

수정 전/후를 같은 지상 카메라 8개로 비교하고, 수관을 보는 지상 시점 1개 및 선체/보스실 역방향 시점 4개를 추가 검토했다. 단일 탑다운 높이 투영을 사용하지 않았다. 검토 중 source-Y 중심 좌표가 한 칸 어긋난 카메라 변환을 수정했다. 최종 camera JSON은 수정된 좌표다. 선체 입구와 보스실 대표 프레임은 잔해/통로 전체를 확인하기 위해 안쪽에서 뒤를 보는 시점을 사용한다.

Blender는 실제 NBT를 독립 파싱하고 설치된 바닐라 블록 PNG, 슬랩 높이, 잎 바이옴 색 및 블록 조명 근사를 표시한다. 철창/벽/체인/계단 일부는 보수적인 대용 형상이다. 원본 베이크는 실제 PNG+UV로 별도 확인했다. 렌더 이미지는 **Minecraft framebuffer 스크린샷이 아니다**. PBR, 유색 광원 전파, volumetric scattering, Destiny의 GI/후처리를 재현하지 않는다.

검토 장면에는 각 카메라 주변의 3D crop이 들어 있다. 전체 맵을 한 번에 포함한 Blender 파일은 아니다. 텍스처가 내장되어 orbit/pan/walk로 주변 내부를 다시 볼 수 있다. 기존 사용자의 미저장 Blender/Blockbench 장면은 덮어쓰지 않았다.

로컬 비교 뷰어와 두 개의 텍스처 내장 장면:

`/Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/nessus-art/index.html`

`.../nessus-art/blender/hull_corridor.blend`, `.../nessus-art/blender/nessus_grove.blend`

## 실제 클라이언트 — 대기

Computer Use로 처음에는 Finder 접근이 가능했으나, 클라이언트 시작 전 screenshot에서 Mac 잠금을 관측했다. 프로젝트의 “이미 잠긴 Mac은 우회하지 않는다” 규칙에 따라 클라이언트를 실행하지 않고 직접 잠금 해제를 요청했다. 새 클라이언트/lease는 생성하지 않았다. 실제 인게임 하늘·안개·잎 색, 선체 밝기, 이동 감각·전투·성능은 아직 수락하지 않았다.

소유 시각 QA 서버: loopback `127.0.0.1:25638`, PID 56065, 작업 폴더 `/tmp/exodus-nessus-art/server`. `keep_awake.py --seconds 1800`이 소유한 caffeinate PID 55960으로 한정했으며 화면 잠금을 우회하지 않는다. 최종 cleanup 상태는 `validation.json`에 기록한다. 일반 Minecraft 프로필/월드를 사용하지 않았다.

자료 정리 후 console `stop`으로 소유 서버를 정상 종료했다. PID 56065와 caffeinate 55960의 종료, 25638 listener 부재를 확인했다. 새 Vision 클라이언트와 입력 lease는 만들지 않았다. 잠금 해제 후의 실제 시각 검토가 남아 있으므로 완료 수락 상태로 표시하지 않는다.

실제 생성 resource pack ZIP은 **211,274,167 bytes**, SHA256 `24b04cc2243a56c3ce414bd4fe5aa9e101942d9c0ffc9038f18a4d902a96c1fe`. 250,000,000바이트 목표 이내다. 이 전체 팩에는 현재 작업 트리의 다른 기존 콘텐츠도 포함되어 있으며, 이 맵만의 용량이 아니다. JAR 크기와 리소스팩 ZIP 크기는 구분한다.

최종 맵 NBT는 **4,655,037 bytes**, SHA256 `e885a92743c9ae0eb83f0648ff6e9a07386417720d962541779ba01dc08dab7d`.

마지막 `jar` 빌드도 통과했다. JAR **420,981,722 bytes** 안의 NBT와 Nessus 바이옴 JSON이 최종 소스 파일과 바이트 단위로 동일함을 확인했다. 이것은 211MB 리소스팩과 별개의 서버 배포 JAR 용량이다.

## 재생성

```sh
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py voxel
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py build
rtk proxy /tmp/venv/bin/python scripts/qa/verify_exodus_map.py
rtk proxy /tmp/venv/bin/python scripts/qa/verify_exodus_finish.py --before /tmp/exodus-nessus-art
```

`voxel`은 read-only Downloads 원본에서 샘플을 만들며 `/tmp/exodus-r3`의 동일 source identity cache만 재사용한다. `build`에서 활동 아트 pass를 자동 실행한다. 마지막 비교 검사는 작업 전 before.npy/before-palette.json/route-before.npy가 필요하며 baseline은 `/tmp/exodus-nessus-art`에 보존했다. 새 환경에서는 voxel 단계를 먼저 실행해야 한다.
