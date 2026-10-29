# W248 아이콘 자산 작업 보고 — FROZEN

재사용 slot1에서 master의 WRITE-READY 이후 지정된 21개 파일만 작성했다. 완료 시점부터 worker 쓰기를 중단했고, 최종 한국어 기록은 master가 통합했다.

## 자산과 출처

- 헌터·타이탄·워록: Destiny Item Manager 커밋 `60581be6c7063e7115a40e5939a791d58d3448f4`의 `src/app/shell/icons/custom/{Hunter,Titan,Warlock}.ts`에 있는 SVG polygon 경로를 사용했다. Bungie 공식 직업 아이콘 다운로드라고 주장하지 않으며, 수작업 재작성도 아니다. 비율을 유지한 56px 장축을 64px 캔버스 중앙에 두고 8배 해상도에서 그린 뒤 Lanczos로 축소했다. DIM MIT 고지는 생성기와 manifest에 포함했다.
- 전기·태양·공허: Bungie 공식 `DestinyDamageTypeDefinition.transparentIconPath`의 `arc_trans.png`, `thermal_trans.png`, `void_trans.png`를 사용했다. 96×96 원본 알파를 zlib/base85로 손실 없이 생성기에 내장하고 64×64로 축소했다. 출력은 크기 변환된 자산이며 원본 PNG와 바이트 동일하다고 주장하지 않는다.
- 6종 모두 흰색 RGBA64×64 mask이며 색상을 미리 굽지 않았다. master HUD가 `CUSTOM_MODEL_DATA` color index 0으로 색을 적용한다.
- GUI 모델은 기존 `solid.json`과 같은 z=8 평면, north/south 두 면이며 `tintindex:0`을 쓴다. item definition은 `minecraft:custom_model_data`의 index 0과 흰색 fallback을 쓴다.
- `art/ui/w248/manifest.json`에 출처 URL, 고정 커밋, 원본·알파·SVG 경로·산출물 SHA-256, 변환 방식, 생성기 해시, Pillow 버전과 고지를 기록했다. 생성기는 입력을 내장해 네트워크 없이 재생성한다.

## 자산 검증

- 6개 고유 mask, RGBA64×64, RGB=(255,255,255), 투명 배경과 안티앨리어싱 확인.
- 18개 texture/model/item 경로 및 tint/color index 0 확인.
- 3개 원소의 출력 알파가 공식 원본에 선언한 축소 방식을 적용한 결과와 정확히 일치했다.
- socket 생성을 차단한 두 번째 실행에서도 생성 출력 19개(18개 자산+manifest)가 바이트 단위로 같았다. Pillow 12.3.0.
- 62px root, 58px option, 40px sidebar, 28px header와 16px 축소 미리보기를 확인했고 master가 채택했다. 미리보기는 실게임 캡처와 구분했다.
- master가 Danmo4GB/OpenGL 실제 framebuffer에서 여섯 문양·tint·금색 선택 표시를 확인했다. 자산 수정 요청 없이 수용했다.
- worker는 Java·빌드·게임 입력·commit·stash·reset·clean·push를 수행하지 않았다. master의 범위 검사에서 21개 소유 변경, 범위 밖 변경 0개였다.

## 재생성

```sh
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/generate_character_icons_w248.py
```

동결된 slot을 바꾸지 않으려면 `--root /private/tmp/destiny-w248/recheck`를 지정한다. 생성기는 6개 PNG, 12개 모델/item JSON, 출처 manifest만 쓰며 이 보고서는 수정하지 않는다.

## 소유 파일 21개

- `scripts/generate_character_icons_w248.py`
- `docs/qa/2026-10-29/w248/asset-worker.md`
- `art/ui/w248/manifest.json`
- `src/main/resources/assets/destiny/textures/item/hud/class_hunter_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/class_hunter_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/class_hunter_w248.json`
- `src/main/resources/assets/destiny/textures/item/hud/class_titan_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/class_titan_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/class_titan_w248.json`
- `src/main/resources/assets/destiny/textures/item/hud/class_warlock_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/class_warlock_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/class_warlock_w248.json`
- `src/main/resources/assets/destiny/textures/item/hud/subclass_arc_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/subclass_arc_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/subclass_arc_w248.json`
- `src/main/resources/assets/destiny/textures/item/hud/subclass_solar_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/subclass_solar_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/subclass_solar_w248.json`
- `src/main/resources/assets/destiny/textures/item/hud/subclass_void_w248.png`
- `src/main/resources/assets/destiny/models/gui/hud/subclass_void_w248.json`
- `src/main/resources/assets/destiny/items/gui/hud/subclass_void_w248.json`
