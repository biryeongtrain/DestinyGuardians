# 엑소더스 맵 베이크 재생성 · 2026-11-08

요청: Blender에서 탑다운만 보지 않고 외부→입구→선체 내부→보스방을 이동하며 확인하고 NBT 재생성. 추가 지시: 회색 재질 대신 머티리얼 베이크로 확인.

## 원인과 변경

- 기존 입력은 `maps_glb/*.textured.glb`의 초기 색 후보 미리보기였다. 전달된 `maps_baked/Exodus_Crash_Continuous.baked.glb`와 실제 PNG/BakedColorUV로 교체했다. 원본 `.blend` 두 파일은 별도 background Blender에서 읽었고 Downloads 파일은 저장하지 않았다. 기존 라이브 Blender의 미저장 파일은 덮어쓰거나 종료하지 않았다.
- 구역별 사각형 열 소유권으로 지형을 잘라 이어 붙이던 처리를 제거했다. 원본 공통 좌표의 연속 조립본을 한 번 복셀화한다. GLB 표시용 root 축 변환은 source Z-up 샘플러에 중복 적용하지 않는다.
- 비색상/마스크를 표면색으로 사용하지 않는다. 실제 베이크 PNG를 알파 커버리지 0.5로 검사하고, 선형 RGB 평균 후 팔레트에 대응한다. `forward_or_decal_requires_scene` 및 `no_visible_pixels_in_extracted_state`는 고체에서 제외한다. `native_shader_scene_defaults`는 실제 구조물 형상을 보존하며 색상 불확실성을 유지한다.
- Cosmodrome용 기존 팔레트에는 충분한 파랑·빨강이 없었다. Exodus 전용 팔레트 어댑터에 도색/금속색 12개를 더했다. 신규 리소스팩 텍스처는 없다. 모든 사용 블록 ID가 로컬 Minecraft client JAR에 존재함을 확인했다.
- 맵 크기 `[1115, 231, 1680]` (x,y,z), origin `[256, 32, 256]`. 높은 구조물과 남쪽 구조물을 보존하도록 기존 높이/남쪽 crop을 확장했다.
- 도착 발판 외에 경계 인공 경사로·보스방 전체 평탄화는 사용하지 않는다. 3D 경유점으로 참호 바닥과 선체 내부를 지나 보스방에 들어간다. 원본 임무 actor parent 위치는 힌트이며, 실제 연결된 바닥과 Blender 화면을 우선했다.
- 발판 보정 23칸: `{'stable one-block support instead of a decorative rod/wall': 18, 'half-block correction for rise<=1.25/drop<=3': 5}`. 정확한 before/after와 source 좌표는 런타임 manifest의 adaptations에 기록했다. 실제 slab 바닥 높이를 사용하여 상승 ≤1.25, 하강 ≤3을 확인한다. 철창/체인/담장은 걸을 바닥으로 삼지 않는다.
- 12개 구간의 trigger·spawn·generator·gate 및 안내 경로를 새 동선에 맞춰 함께 생성했다. 4개 방벽 양끝은 지형에 닿는다. 전체 gameplay 흐름 자체를 원작과 일치시켰다는 주장은 하지 않는다.

## 실제 검토

처음 Solid/회색으로 찍은 화면은 색상 판단 근거에서 제외했다. 라이브 앱 연결 작업은 응답하지 않아 별도 소유 headless Blender를 사용했다. 이후 베이크 PNG와 UV를 Cycles emission으로 연결해 검토했다. 카메라가 기둥/벽을 보는 지점에서는 시점과 방향을 이동해 재검토했다. 지붕 위로만 내려다보는 이미지로 내부 확인을 대신하지 않았다.

최종 8개 눈높이 카메라의 원본/새 NBT를 대조했다. 카메라는 실제 slab 바닥 높이 +1.62에서 경로 앞쪽을 본다. `cameras.json`에 위치·방향을 기록했다. NBT 렌더는 실제 `world.nbt`를 독립 파서로 읽은 프록시이며 slab 높이는 반영하지만, 담장·철창·계단의 정확한 Minecraft 모델/텍스처/조명은 아니다.

[8시점 비교 갤러리](/Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/exodus-review/index.html) · [선체 통로 Blender](/Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/exodus-review/final-source/hull_corridor.blend) · [보스 입구 Blender](/Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/exodus-review/final-source/boss_entry.blend)

| 위치 | 베이크 원본 | NBT 프록시 |
|---|---|---|
| 선체 통로 | ![](final-source-hull_corridor.png) | ![](final-nbt-hull_corridor.png) |
| 보스방 입구 | ![](final-source-boss_entry.png) | ![](final-nbt-boss_entry.png) |
| 보스방 내부 | ![](final-source-boss_room.png) | ![](final-nbt-boss_room.png) |

## 검증

- Python bake 입력 회귀 3개 통과: 비인덱스 삼각형, 축/UV 유지, 효과층 제외, 알파 커버리지, 선형 색상.
- 독립 NBT 파서 round trip: 13,635 sections / 7,570,904 blocks 전부 생성 grid와 일치. NBT 5,680,544 bytes. 해시는 provenance.json.
- 최종 경로 2,488칸 전체의 바닥·머리 공간·이동 간격·실제 slab 상승/하강 확인. 마커 333개 및 4개 방벽 배치 확인. 검사 시 닫힌 방벽은 열림 상태로 해석한다.
- `./gradlew test --tests "kim.biryeong.destiny.strike.*" --offline` 통과. 최종 팔레트 재생성 뒤 같은 관련 검사와 JAR 패키징을 다시 확인했다.
- 전체 unit suite를 1회 실행: 2825개 중 2822 통과 / 3 실패. 이 실행은 최종 팔레트 전용 재출력 전이며 Java 변경은 동일했다. 실패 상세는 full-suite-summary.json: `MinorPveBalanceW342Test` CYCLOPS 수치, `FireVariantsW98Test`의 삭제된 11/03 음악 inventory, `GoldenGunHudW122AssetTest`의 삭제된 WeaponFeedbackW112GameTests 참조. 이 작업에서 관련 파일을 고치거나 검사를 제거하지 않았다.
- 실제 Minecraft 클라이언트 플레이·적 전투·방벽 해제·밝기·인게임 성능은 미검증. GameTest/server/client를 실행하지 않았다. 이번 결과를 인게임 통과로 확대하지 않는다.
- 방벽 끝점 단면 검사는 통과했지만 옆길/점프를 통한 우회 불가까지 검증한 것은 아니다. 최종 JAR 안의 NBT 바이트가 현재 소스 NBT와 정확히 일치함을 확인했다.

## 재현

```sh
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py voxel
rtk proxy /tmp/venv/bin/python scripts/strikes/build_exodus_maps.py build
rtk proxy /tmp/venv/bin/python scripts/qa/test_baked_source.py
rtk proxy /tmp/venv/bin/python scripts/qa/verify_exodus_map.py
rtk proxy /Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/strikes/review_exodus_blender.py -- --output /tmp/exodus-source-review --cameras /Users/qf/.codex/visualizations/2026/11/08/01a1bb4b-8931-7be3-b87a-826e42e53584/exodus-review/final-cameras.json
```

중간 데이터는 `/tmp/exodus-r3`입니다. 원시 선형색 surface samples를 tile별로 저장하므로 팔레트 변경 시 `voxel --recolor`로 재사용할 수 있습니다. source/sampler identity가 달라진 cache는 거부합니다. 검토용 blend는 Downloads의 읽기 전용 베이크 PNG를 참조합니다.
