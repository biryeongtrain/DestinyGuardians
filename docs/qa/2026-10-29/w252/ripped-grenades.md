# W252 실제 리핑 수류탄 임시 적용

기존 큐브 8종은 보존한다. 이번 반환은 `GrenadeModels.java` 1개 변경과 신규15파일이다. main·중앙Gradle·Minecraft·CU·Vision을 실행하지 않았다. Blender는 `--background --factory-startup`의 별도 소유 프로세스에서만 실행했다. live scene·SSD 원본·외부 archive 내부 스크립트는 실행/수정하지 않았다.

## 실제 원본과 변환

[커뮤니티 Drive / Misc / Four Grenade Types.7z](https://drive.google.com/file/d/1yEfOLn_FJGT2tY5Q5oRNtA0OCnjkt2fQ/view), SHA256 `b3183e471b5ce992a463e4b779a2ce9f0530aab538f770fd21c908ea772bb75f`에서 **Explosion Grenade.fbx / Pulse Grenade.fbx와 각각의 원본 Diffuse.PNG**를 직접 읽었다. 원작 디자인은 Bungie 소유이며 ripper·게임 빌드·추출 시점은 archive에 명시되지 않았다. FBX/PNG별 해시는 새 manifest에 있다.

재현 생성기 `scripts/art/build_ripped_grenades_w252.py`:

1. archive와 4입력의 고정 해시를 검증한다. allowlist의 FBX·Diffuse만 `/private/tmp/destiny-w252/ripped-source`에 풀며 archive 스크립트는 실행하지 않는다.
2. headless Blender 5.4.0 Alpha에서 실제 FBX를 import하고 object world matrix·material·loop UV를 평가한다. 원본 삼각형을 별도로 보관한다. Pulse는 2개 source mesh의 실제 transform/material/UV를 합친다.
3. 위치 중복 정점을 weld하고 Blender COLLAPSE decimation을 적용한다. loop UV가 보존/보간된 490삼각형 이하 메시를 추출한다. Blender world `(x,z,-y)`를 native Y-up으로 매핑하고 원본 AABB 중심을 `(8,8,8)`, 최대 길이를8units로 정규화한다.
4. 기존 `scripts/mesh/native_triangle_elements_w115.py`의 실제 함수를 사용해 삼각형당 최대2개 회전 평면을 출력한다. native rotation은 **Rz·Ry·Rx / rotationZYX**이다. 출력 평면 정점과 원본 fragment 정점의 최대 오차를 검사한다.
5. fragment의 3D 위치를 decimated source triangle의 barycentric 좌표로 되돌려 **원본 loop UV로 원본 Diffuse RGB를 bilinear 샘플링**한다. 1024² atlas의 각32² island에 원본 색과 삼각형 alpha mask를 베이크한다. 원본 PNG alpha를 투명도로 직접 쓰면 본체가 사라지므로 Diffuse RGB는 opaque로 사용하고 출력 alpha는 삼각형 coverage에서 생성한다. 원본 alpha/PBR 채널의 정확한 용도를 복원했다는 주장은 하지 않는다.
6. 적군은 원본 Diffuse 베이크에 명시적 붉은 presentation tint만 적용한다. geometry/UV/alpha는 동일하며 기존 `AbilityVisualVariants`가 `_enemy`를 선택한다.

| archive 원본 | 원본 삼각형 | decimation 후 | 실제 출력 요소 | fragment 위치 최대 오차 |
|---|---:|---:|---:|---:|
| Explosion | 846 | 474 | 948 | 약1.1e-14 units |
| Pulse | 1,032 | 475 | 950 | 약2.9e-14 units |

이 제품은 **실제 리핑 정점/UV/Diffuse를 사용한 decimated derivative**다. 이전 큐브 재구성과 다르며, 원본 토폴로지·UV를 무변경 그대로 보존한 모델도 아니다. normal map·PBR·동적 발광은 복원하지 않았다. atlas 유한 해상도와 반 texel coverage 여유가 있다.

## API와 임시 매핑

두 `item` API는 유지한다. unknown·다른 namespace·null은 EMPTY, NONE/KINETIC 조합도 EMPTY다. 새 item 모델 prefix는 `destiny:ability_w252/ripped_grenade/`.

| 능력 | 모델 | 근거/대용 상태 |
|---|---|---|
| hunter/arc_flashbang | explosion | 실제 Explosion 원본. Flashbang 게임 이미지와 실루엣 대응하나 archive의 개별 능력 명칭은 Explosion이다. |
| titan/arc_grenade | pulse | archive에서 Pulse Grenade로 명명한 실제 원본. |
| warlock/arc_grenade (Storm) | pulse | **Storm 전용 원본이 아닌 임시 대용**. |
| hunter/solar_incendiary, hunter/void_vortex | explosion | **각 능력 전용 원본이 아닌 임시 대용**. |
| titan/solar_grenade (Fusion), titan/void_grenade (Suppressor) | explosion | **각 능력 전용 원본이 아닌 임시 대용**. |
| warlock/solar_grenade, warlock/void_grenade | explosion | **Solar/Vortex 전용 원본이 아닌 임시 대용**. |

능력 효과·피해·투척 타이밍은 변경하지 않는다. 없는 리핑의 추가 추출 요청은 중단한다. 기존 `ability_w252/grenade/` 자산과 이전 generator/manifest/doc는 보존한다. 기본 최대 길이0.5블록, FP scale0.5~0.6에서0.25~0.3블록 기준이며 renderer의 손 offset은 master 소유다.

## 검사와 PNG 증거

[원본 FBX/UV/Diffuse → 실제 출력 JSON/atlas → 적군 → decimated source 비교 PNG](/private/tmp/destiny-w252/assets/ripped-grenade-preview.png). 같은 카메라·광원·배율의 **오프라인 소프트웨어 렌더**이며 실게임 Vision이 아니다. 출력 JSON의 회전 평면·UV·alpha atlas를 직접 읽어 그렸다. 원본/변환 후 본체·퓨즈·레버·캡슐·원본 표면 디테일 대응을 확인했다.

재현/검사 명령:

```sh
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/art/build_ripped_grenades_w252.py --refresh-blender --preview /private/tmp/destiny-w252/assets/ripped-grenade-preview.png
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/art/build_ripped_grenades_w252.py --refresh-blender --check
```

입력 해시·출력 해시·Python AST·8 JSON/4 PNG 파싱·item/model/texture 참조·980요소 이하·유한 좌표·삼각형 mask·일반/적군 기하/UV/alpha 동일성·기존51파일 보존을 확인했고 **모두 통과했다**. Blender를 새로 실행한 `--refresh-blender --check`도13개 산출물 바이트가 일치해 통과했다. 외부 원본/평가 cache는 제품 파일이 아니다. 실제 import된 모든 source material의 diffuse alpha와 Principled alpha는1.0이었다. 원본 PNG alpha를 cutout으로 쓰지 않은 정책은 이 opaque material 평가와 일치한다.

최종 Java SHA256: `9d13c9167dda1ea3b084c1fe9bf35e2fea50802382025b0a4a0e123a00b6dfc9`.
최종 비교 PNG SHA256: `e996e85507e4c6b30990d80c9647492a1bc2f4f00d34782093b687d5bf75b177`.

**미검증:** 중앙 Java compile·native resource-pack alpha/culling/filtering·1/3인칭 실제 파지·팔과 간섭·실게임 Vision·10~20개 동시 표시 성능. 이전 큐브 Flashbang 파지 Vision 피드백은 이 새 ripped 자산의 native 검증으로 승계하지 않는다.

## 반환 파일 — 이 목록만 통합

변경1개:

- `src/main/java/kim/biryeong/destiny/fx/GrenadeModels.java`

신규15개:

- `scripts/art/build_ripped_grenades_w252.py`
- `art/abilities/w252/ripped-grenade-manifest.json`
- `docs/qa/2026-10-29/w252/ripped-grenades.md`
- `src/main/resources/assets/destiny/items/ability_w252/ripped_grenade/explosion.json`
- `src/main/resources/assets/destiny/items/ability_w252/ripped_grenade/explosion_enemy.json`
- `src/main/resources/assets/destiny/items/ability_w252/ripped_grenade/pulse.json`
- `src/main/resources/assets/destiny/items/ability_w252/ripped_grenade/pulse_enemy.json`
- `src/main/resources/assets/destiny/models/item/ability_w252/ripped_grenade/explosion.json`
- `src/main/resources/assets/destiny/models/item/ability_w252/ripped_grenade/explosion_enemy.json`
- `src/main/resources/assets/destiny/models/item/ability_w252/ripped_grenade/pulse.json`
- `src/main/resources/assets/destiny/models/item/ability_w252/ripped_grenade/pulse_enemy.json`
- `src/main/resources/assets/destiny/textures/item/ability_w252/ripped_grenade/explosion.png`
- `src/main/resources/assets/destiny/textures/item/ability_w252/ripped_grenade/explosion_enemy.png`
- `src/main/resources/assets/destiny/textures/item/ability_w252/ripped_grenade/pulse.png`
- `src/main/resources/assets/destiny/textures/item/ability_w252/ripped_grenade/pulse_enemy.png`
