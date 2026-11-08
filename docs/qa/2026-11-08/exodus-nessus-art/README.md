# Exodus Crash — Nessus art and native review

2026-11-09 KST 최종 수락. 베이크 재구축 `3440ab925`, 아트 초안 `828471243` 위에서 실제 클라이언트 검토와 수정을 마쳤다. 최종 데이터 식별자와 검증 범위는 `validation.json`, 카메라와 이동 증거는 `native-review.json`에 있다.

## 적용한 모습

- 붉은 바이옴 잔디·잎과 어두운 수피, 회백색 암석, 옅은 청록 벡스 표면을 배치했다. 선체는 회색 금속과 어두운 토양/잔해, 국소 광원으로 구분했다. 원본의 청색·적색 페인트와 구리 잔해는 보존했다.
- 식생은 원본 베이크 샘플의 야외 자연 지표가 있는 후반 외부 구역에 한정했다. 협곡과 선체 잔해 전체를 숲으로 덮지 않았다.
- 초기 dead bush/terracotta 지표를 실제 `short_grass`/`grass_block`으로 바꿨다. 최종 풀 6,838개의 생존 지지 블록을 모두 검사했다. 처음 배치한 7,651개 중 일부는 뒤이어 배치한 관목/나무와 겹쳐 대체됐다.
- 붉은 지표 30,721칸, 관목 216군집, 나무 33개. 추가 식생 블록은 30,589개다. 경로 반경 4칸과 마커 반경 6칸, 총 28,704개 보호 열에 새 식생은 없다.
- 전용 Nessus 바이옴의 청록 하늘/안개와 붉은 풀/잎 색을 실제 클라이언트에서 확인했다. 바닐라의 평평한 구름은 이 바이옴에서 투명하게 처리했다. 새 클라이언트 텍스처나 외부 셰이더팩은 추가하지 않았다.
- 보스실의 약 55블록 위 천장을 종전 46블록 높이 제한이 놓쳐 조명이 빠지는 결함을 실제 화면에서 발견했다. 전체 높이의 불투명 천장 판정으로 수정했다. 보조광은 총 354개이며 보스 구역 86개는 level 13, 나머지는 level 11이다. 기존 천장 블록 40개를 발광 재질로 교체했다. 이전 베이크 재구축본 대비 새 비충돌 light 셀은 45개다.

기존 full/slab/철창/벽/체인의 형상 및 slab bottom/top/double 속성, 경로 2,488칸과 마커 333개, 방벽 4개의 좌표는 유지했다. Downloads 원본 GLB/Blender/베이크 PNG는 읽기 전용으로 사용했다. 사용자의 미저장 Blender/Blockbench 장면은 덮어쓰지 않았다.

## 실제 시각 레퍼런스

- [Steven Klipowicz — Nessus Natural Palette](https://sklipowicz.artstation.com/projects/O433e): 붉은 식생, 어두운 수피, 밝은 암석과 벡스 표면.
- [Anthony Pitts — Lost Sectors, Nessus](https://pittskrieg.artstation.com/projects/9bNKN): 엑소더스 블랙 계열 내부의 차가운 금속과 따뜻한 국소 광원.
- [Mike Poe — EDZ and Nessus Relights](https://mjcr24.artstation.com/projects/ELOn5N): 어두운 전경과 밝은 개구부, 국소 조명 위계.
- [KeerPlays — Exodus Crash 실제 보스실, 22:20](https://www.youtube.com/watch?v=uzYYadj8jxk&t=1340s): 브라우저에서 실제 재생 화면을 확인했다. 어두운 외곽과 읽을 수 있는 플랫폼/광원 대비를 참고했다. 플레이어 능력 효과의 보라색을 환경 고유색으로 간주하지 않았다.

참고 이미지를 게임 텍스처로 복사하지 않았다. 원본 베이크/형상 위에 Minecraft용 표면·식생·광원을 저작했다. 바닐라 블록 광원은 유색 GI/volumetric scattering/원작 후처리를 재현하지 않는다.

## 실제 클라이언트 검토

사용자가 Mac을 직접 잠금 해제한 뒤 Computer Use로 잠금 해제를 확인했다. 격리된 서버/클라이언트에서 최종 NBT와 바이옴을 로드했다. 실제 인게임 9개 시점의 1708×960 PNG 및 상태 JSON을 `native/`에 보관했다. 진입/협곡, 선체 안팎, 후반 외부, 보스실 진입/역방향, 수관을 보는 지상 시점이다. 텔레포트는 카메라 및 이동 사례의 시작 위치를 정하는 fixture 용도다.

| 실제 포그라운드 입력 | 수평 이동 | 결과 |
| --- | ---: | --- |
| 협곡 걷기 | 9.710m | 지면 전환 후 정지 |
| 선체 내부 걷기 | 5.392m | 통로 통과 후 정지 |
| 입구 전진+점프 | 4.200m, 높이 +2.5m | 경사/슬랩 진입 후 정지 |

모든 사례에서 `nativeInput`이 실제 활성화됐고 서버의 최종 위치와 일치했다. 종료 후 lease 비활성, heldKeys 비어 있음, 모든 nativeInput false를 확인했다. 증거는 `native/*/evidence.json`, 서버 위치/바이옴 확인은 `native/server-events.log`에 있다. 전체 전투 완주, 전 경로 네이티브 주행, 오디오 또는 성능 벤치마크 수락은 아니다. FPS는 순간 스냅샷일 뿐이다.

최종 dimension: `destiny:exodus_crash/4557c6bf-6a9e-4409-8f15-74aabf1a7afd`.

## Blender와 베이크 검토

실제 baked GLB의 PNG+UV를 확인하고, NBT를 독립 파싱해 바닐라 PNG/바이옴 색/조명 근사로 검토했다. 탑다운 최대 높이 투영이 아닌 내부/천장을 포함한 3D crop을 사용했다. 지상 시점 9개, 선체/보스실의 다른 방향도 확인했다. source-Y 중심의 한 칸 카메라 변환과 풀 옆면 overlay도 수정했다.

최종 `blender-verified/*.blend` 9개는 실제 텍스처를 내장해 orbit/pan/walk로 볼 수 있다. 전체 맵을 한 파일에 넣은 장면은 아니다. 철창/벽/체인/계단 일부는 대용 형상이고 조명은 근사다. 갤러리의 인게임 PNG와 Blender 이미지는 명확히 구분했다.

갤러리: `/Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/nessus-art/index.html`

이전 봉인 QA `exodus-map-baked-rebuild/`는 수정하지 않았다.

## 데이터·코드 검증

- 최종 NBT 13,686 sections / 7,601,538 non-air 블록 전부를 final.npy와 비교해 일치했다. 전체 경로의 바닥/머리 공간, 실제 slab 높이, 마커/방벽 검사를 통과했다. 방벽의 모든 우회 가능성을 전수 인증한 검사는 아니다.
- 변경 전 배열과 비교해 기존 충돌 형상 및 slab 속성 전부 유지, 경로 배열 동일, 보호 열의 새 충돌 형상 0을 확인했다. 추가 geometry는 지정 식생뿐이며 light 셀은 별도 집계한다.
- 높은 천장과 얇은 장식/유리/비가시 광원의 구분 회귀 테스트 2개 통과. 베이크 reader 테스트 3개 통과.
- `compileJava compileGametestJava test --tests '*Exodus*' --tests '*Strike*' jar`: Java 통합 변경에 대해 8 suite / 28개 unit tests, 실패 0. 이후 변경은 아트 데이터/오프라인 Python이며 Java 통합 코드는 동일하다.
- 실제 GameTest 1개 통과는 이전 WIP NBT SHA `e885a92743c9ae0eb83f0648ff6e9a07386417720d962541779ba01dc08dab7d`를 대상으로 했다. Fantasy 생성/템플릿 로드/입장 좌석 경로와 Nessus 바이옴을 확인했다. 최종 아트 데이터를 대상으로 같은 GameTest를 재실행했다고 주장하지 않는다. 최종 데이터는 위 실제 서버/클라이언트에서 별도로 로드하고 검토했다.
- GameTest 초기에 잘못된 filter로 0개가 선택됐고, 다음 실행은 공용 에셋 준비가 기본 120초를 넘겨 중단됐다. 올바른 filter와 준비 상한 600초의 최종 실행이 통과했다. 기존 XML의 test time은 1.56초, 공용 준비를 포함한 suite time은 172초다.
- 이전 전체 unit suite의 무관한 3개 실패는 앞선 베이크 QA 기록에 남아 있다. 이번 작업에서 전체 suite를 재실행하거나 이 실패가 해결됐다고 보고하지 않는다.
- 77개 완료 타일 중 30개 빈 타일의 샘플 캐시가 저장되지 않던 재개 결함을 수정했다. 47개 nonempty+30개 empty 캐시를 모두 저장했고, raw world.npy SHA `f86f81a472373140b01f0497dab643e919ce2f616c8a74106b4320eecd0c0aff`는 이전/이후 동일하다.

`NbtTemplateChunkGenerator`의 공용 바이옴 생성자를 Exodus 어댑터가 사용한다. 기존 생성자는 THE_VOID를 유지한다. 전용 바이옴은 설치된 26.3 원본 codec에 맞췄고 feature/carver/자연 스폰은 비어 있다.

## 산출물·정리

- NBT: 4,656,318 bytes, SHA256 `330e172b37db7509342ba6916289ba677d916725284f64f38b05b6e51e4aab3c`.
- 서버 JAR: 420,983,017 bytes, SHA256 `0a68bc240918bd323873353329423c30239f68944e7a72b43902d3076acdd62e`. 포함된 NBT와 바이옴 JSON은 최종 소스와 바이트 단위로 동일하다.
- 실제 전체 리소스팩 ZIP: 211,274,167 bytes, SHA256 `24b04cc2243a56c3ce414bd4fe5aa9e101942d9c0ffc9038f18a4d902a96c1fe`. 250MB 목표 이내다. JAR/팩에는 현재 작업 트리의 다른 기존 콘텐츠도 포함된다.

QA는 `/tmp/exodus-nessus-art/{server,client}`와 loopback 25638/8102만 사용했다. `keep_awake.py --seconds 3600`으로 전체 master 배치를 감쌌다. 검토 후 소유 client/server/master 및 자체 caffeinate를 종료했고 두 포트 listener 부재를 확인했다. 일반 프로필/월드나 시스템 보안 설정은 변경하지 않았다. 정리는 `cleanup-final.json`에 있다.

## 재생성

```sh
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py voxel
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py build
rtk proxy /tmp/venv/bin/python scripts/qa/verify_exodus_map.py
rtk proxy /tmp/venv/bin/python scripts/qa/verify_exodus_finish.py --before /tmp/exodus-nessus-art
rtk proxy /tmp/venv/bin/python scripts/qa/test_surface_finish.py
```

동일 source identity 캐시만 재사용한다. 새 환경에서는 voxel 단계를 먼저 실행한다. 비교 검사는 보존한 `before.npy/before-palette.json/route-before.npy` baseline이 필요하다. `build` 단계가 아트 pass를 자동 적용한다.
