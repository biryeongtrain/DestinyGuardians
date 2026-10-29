# W253 수류탄 원본 리핑 요청

현재 필요한 것은 **Fusion / Storm / Vortex / Solar 4종의 능력별 투척물 원본 또는 실제 렌더링 구성**이다. 독립 메시 존재 여부부터 확인하고, 에너지 효과를 임의의 고유 껍질로 만들지 않는다. 궁극기 전체 조사는 요청하지 않는다.

## 1. 우선 확보할 4종

| 우선 대상 | 현재 제품 능력 ID → 임시 모델 | Windows에서 확인·전달할 대상 |
|---|---|---|
| Fusion Grenade | `titan/solar_grenade` → Explosion | 손에 든 상태·비행·부착 상태의 entity/model/material 연결. 별도 메시가 없으면 실제 particle/sprite 구성을 전달. |
| Storm Grenade | `warlock/arc_grenade` → Pulse | 투척물과 착탄 후 번개/폭풍 효과를 분리. Pulse 공유 여부도 태그 참조로 확인. |
| Vortex Grenade | `hunter/void_vortex`, `warlock/void_grenade` → Explosion | 투척물과 착탄 후 소용돌이/활성장을 분리. 두 직업이 같은 원본을 쓰면 공통 원본 한 벌과 공유 근거만 전달. |
| Solar Grenade | `warlock/solar_grenade` → Explosion | 투척물과 착탄 후 지속 화염/광구를 분리. Incendiary·Fusion과 혼동하지 않도록 능력 태그를 연결. |

4종의 전용 리핑 메시를 현재 확인한 로컬 자료에서 확보하지 못했다. 기존 `ability_w252/grenade/`의 8종 큐브 자산은 참조 기반 재구성이며, 전용 원본 확보 증거가 아니다. Wiki 이미지도 Fusion은 비행 불씨, Vortex/Storm/Solar는 주로 폭발·에너지 참고이므로 메시 존재/형태를 확정하지 못한다.

## 2. 이미 확보함 — 같은 파일 재추출 불필요

[Drive의 Misc/Four Grenade Types.7z](https://drive.google.com/file/d/1yEfOLn_FJGT2tY5Q5oRNtA0OCnjkt2fQ/view) 로컬 캐시를 직접 목록 확인했다. **Explosion / Pulse / Magnetic / Spike 각각 FBX·Diffuse·Normal**, 그리고 `Grenades.blend`가 들어 있다. Magnetic/Spike는 현재 W252 8종에 직접 매핑되지 않으므로 이번 신규 요청에서 제외한다. 일반/적군 색상별 메시도 중복 추출할 필요 없다.

Explosion/Pulse는 실제 정점·loop UV·Diffuse를 변환해 제품에 적용한 상태다. 현재 변환기는 Normal/PBR을 사용하지 않지만 원본 Normal은 이미 archive 안에 있다.

| 확보 원본 | 확인된 식별 정보 | 아직 필요한 것은 파일이 아닌 용도 근거 |
|---|---|---|
| Explosion Grenade | object `f3eab080_0`, material `Grenade02` | Flashbang 이미지와 실루엣 대응은 있으나 정확한 능력별 entity/model 태그 연결은 미확정. Flashbang·Incendiary·Suppressor가 실제 공유하는지 확인. |
| Pulse Grenade | objects `20f2b080_0`, `20f2b080_6`, materials `Grenade01`, `Grenade01Emi` | archive 이름은 Pulse. Titan Pulse 및 다른 능력과의 실제 entity/model/material 연결·게임 버전은 미확정. Storm 전용 원본으로 확정한 것은 아님. |

위 object 문자열은 **메시명에 들어 있는 표기 그대로**이며, 검증된 정규 Tag32/Tag64 값으로 단정하지 않는다. 바이트 순서와 태그 종류를 함께 확인해 달라. SHA-256은 파일 동일성 확인용으로, 게임 자산 태그와 별개다.

Incendiary(`hunter/solar_incendiary`)와 Suppressor(`titan/void_grenade`)도 현재 Explosion 대용이다. **먼저 기존 Explosion 공유 여부만 확인**하고, 다른 원본을 쓴다는 근거가 나온 경우에만 해당 전용 메시/재질을 추가 전달한다. Flashbang도 기존 Explosion과 다르다고 확인된 경우에만 새 파일이 필요하다. Pulse의 동일 원본 재전달은 불필요하다.

## 3. Windows 전달 요구사항

- **메시·UV:** 새로 확인된 대상만 FBX 또는 GLB로 전달. 가능하면 텍스처 연결된 `.blend`도 포함. 원본 정점/면·loop UV·normal/tangent·submesh/재질 슬롯·분리 부품과 object transform을 보존하고, 전달 전 임의 decimate·재중심·크기 정규화는 하지 않는다. 중복 모델은 한 벌만 두고 참조로 공유한다.
- **텍스처·재질:** 원본 Diffuse/BaseColor, Normal, 확보되는 material/PBR·mask·emissive·alpha/opacity 텍스처와 매핑을 포함. 재질별 사용 파일, 채널 packing·색공간·normal 방향, opaque/cutout/additive 등 확인된 blend/depth/cull 정보를 기록. 모르는 채널은 미확정으로 표시하며 Diffuse alpha를 임의 투명도로 해석하지 않는다. 기존 archive의 동일 텍스처는 재추출하지 않는다.
- **메시 없는 효과:** `no_independent_mesh`로 명시하고, 실제 particle/sprite/flipbook·UV/프레임 배열·발광/alpha 재질 및 emitter 연결 등 확보된 구성을 대신 전달. 활성장의 스크린샷만으로 비행체 메시를 대신하지 않는다.
- **태그·출처:** manifest(JSON/CSV)에 능력명/ID → 단계(`held`, `projectile`, `attached`, `active_field`, `detonation`) → entity/model/material/texture 원본 경로와 Tag32/Tag64, 태그 간 참조 근거를 기록. 게임/플랫폼·Steam build·추출 도구/버전·추출일, 파일별 SHA-256도 포함. 같은 자산 공유는 같은 태그로 증명하고 이름 추정은 별도 표시한다.
- **scale·pivot:** 원본 단위·축/handedness·앞/위 방향, unit scale, object/world matrix, AABB 크기, pivot 및 확인 가능한 grip/socket을 기록. 투척물 원점과 활성장/착탄 위치 원점을 구분한다. 제품의 현재 `(8,8,8)` 중심·최대 0.5블록·FP 약 0.25~0.3블록은 변환 목표이며 원본 실측값이 아니다.
- **preview:** 텍스처 연결된 조립체의 정면/측면/사선 PNG와 UV 배치 미리보기. 원작에서 손에 든 상태·비행·부착/착탄·활성장을 구분한 캡처(또는 짧은 영상)를 능력명/시점과 함께 전달. 미확인 단계는 미확인으로 표시한다. 신규 애니메이션 리핑은 이번 요청의 필수 항목이 아니다.

최소 전달 단위: `능력명/원본메시 + textures/ + preview/ + manifest`이며, 기존 원본과 같으면 파일 대신 해당 원본 참조·용도 증거만 전달하면 된다. 활성장에 별도 자산이 실제 존재할 때만 그 단계의 자료를 추가한다.

## 4. 이번에 직접 확인한 로컬 근거

- [현재 API 매핑](/Users/qf/IdeaProjects/DestinyGuardians/src/main/java/kim/biryeong/destiny/fx/GrenadeModels.java), [리핑 적용 문서](/Users/qf/IdeaProjects/DestinyGuardians/docs/qa/2026-10-29/w252/ripped-grenades.md), [리핑 manifest](/Users/qf/IdeaProjects/DestinyGuardians/art/abilities/w252/ripped-grenade-manifest.json), [기존 참조 manifest](/Users/qf/IdeaProjects/DestinyGuardians/art/abilities/w252/grenade-manifest.json).
- 캐시 [Four Grenade Types.7z](</private/tmp/destiny-w252/ripped-source/Four Grenade Types.7z>)의 실제 내부 목록과 아래 파일 SHA-256을 재확인했다. Drive 온라인 목록을 이번에 다시 조사한 것은 아니다.
- SSD [README](/Volumes/qf-ssd/Destiny-Light-Abilities-2026-10-28/README.md), [MOTIONS](/Volumes/qf-ssd/Destiny-Light-Abilities-2026-10-28/MOTIONS.md), export-results 및 ability-inventory를 읽었다. 수류탄 투척/충전 리그·애니메이션 전달은 확인되지만 4종의 독립 prop 메시 확보 근거는 찾지 못했다. inventory의 `Nova Bomb: Vortex`는 궁극기이므로 Vortex Grenade 태그로 사용하지 않는다. SSD 전체 자산 부재를 증명한 것은 아니다.

| 로컬 입력 | SHA-256 |
|---|---|
| Four Grenade Types.7z | `b3183e471b5ce992a463e4b779a2ce9f0530aab538f770fd21c908ea772bb75f` |
| explosion.fbx | `d4833b00b30efea11d0a8e9fccdea75d7d2874a66c1d394a32b79136c6c7a9cc` |
| explosion-diffuse.png | `e4a657a0ef9960a4aa4bbd20582cd612c84f0b2ce41c37ffb61804c9f439c1ef` |
| pulse.fbx | `1ed683efe866ec5e4611390fd3872e1b1663e4e7cdef71558dfd1179c4f08df0` |
| pulse-diffuse.png | `b4a9f460c91c4af1001e778c2055e6a873e6fc8ddfeb881879786e53e5825ae4` |

이 문서는 W253 신규 리핑 요청서다. main·SSD·기존 slot4와 W252 산출물은 수정하지 않았다.
