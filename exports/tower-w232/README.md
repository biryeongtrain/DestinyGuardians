# 타워 중앙광장 블록 맵

SSD의 `Tower-Courtyard-Assets-2026-10-28` 정적 Courtyard 추출본을 별도 Blender 장면에서 확인하고, 중앙광장·천막·계단·화단·주변 외벽을 바닐라 블록으로 변환했다. 원본 GLB 단위당 2블록, Minecraft Y 오프셋 +40을 적용한다.

- `courtyard.schem`: Sponge v2 schematic. 바닐라 블록만 사용하며 원래 절대 최소 좌표를 Offset에 기록한다. 큰 지도이므로 빈 월드에서 불러온 뒤 배치 위치를 확인한다.
- 서버 모드는 `data/destiny/tower/courtyard.vox.gz`와 `courtyard.json`을 읽어 Fantasy 영구 월드 `destiny:tower`를 자동으로 연다. 서버에 원본 GLB나 Blender가 필요하지 않다.
- 플레이어는 `/tower`로 이동한다. 새 유저 첫 접속과 사망 후 복귀도 연결된다. 기존 유저의 다른 월드 로그인 위치는 보존한다.
- 타워 안에서만 일반 유저의 블록 변경·피해·폭발·화재를 막는다. 건축 편집은 관리자 권한이 있는 크리에이티브 플레이어에게 허용된다.
- 다른 QA나 기존 월드 운영에서 타워를 끄려면 JVM에 `-Ddestiny.tower.enabled=false`를 지정한다.

이 지도는 중앙광장의 정적 지형을 옮긴 것이다. 격납고·시장·별관, NPC, 원작의 충돌/navmesh·조명·움직이는 장식은 포함하지 않는다. 원본 추출본의 색상도 추정 base color이므로 원작 shader/dye/PBR을 완전히 복원한 결과는 아니다. 원경은 잘랐고, 곡선·얇은 장식과 작은 계단은 블록 단위로 근사한다.

변환 도구는 `scripts/tower/voxelize_courtyard.py`, 지형 검사 도구는 같은 폴더의 `preview_map.py`·`inspect_walkways.py`다. 자세한 구현·실행 결과는 `docs/design/W232_Tower_스폰월드.md`와 `docs/qa/2026-10-29/w232/`에 남긴다.

재변환 예시(NumPy·Pillow 필요):

```sh
rtk proxy python3 -B scripts/tower/voxelize_courtyard.py \
  --input /Volumes/qf-ssd/Tower-Courtyard-Assets-2026-10-28/maps/tower_courtyard.textured.glb \
  --output /tmp/tower-rebuild \
  --crop-min -85 -48 -125 --crop-max 110 70 45 --scale 2 --offset 0 40 0 \
  --config scripts/tower/courtyard-config.json
```

변환기는 안전 스폰을 검증 완료했다고 자동 표시하지 않는다. 재변환 시 새 지형의 바닥과 머리 공간을 다시 확인한 뒤 배포한다.
