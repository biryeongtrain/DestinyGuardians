# W252 슬롯4 — 수류탄 자산 반환

소유 worktree: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow`.
`/private/tmp/destiny-w252/refresh/report.json` 생성과 master ready 통지를 확인한 뒤 편집했다.
SSD 원본·main·다른 슬롯을 수정하지 않았으며 Gradle/Minecraft/Vision/CU/commit/stash/reset/clean/push를 실행하지 않았다.

## 구현과 연결

- `fx/GrenadeModels.java`: `item(GuardianClass, Element)`와 `item(Identifier)` 제공. 새 PAPER stack의 `ITEM_MODEL`은 `destiny:ability_w252/grenade/<name>`이다. unknown ID·다른 namespace·null은 `ItemStack.EMPTY`. NONE/KINETIC 조합도 EMPTY.
- Java 파일은 master의 중앙 compile 선행 요청에 따라 동결을 선언했다. 이후 수정하지 않았다. 호출부/투척 애니메이션/발사 로직은 master 소유다.
- 기존 `AbilityVisualVariants.item(stack, hostile)`가 `<name>_enemy`를 선택할 수 있도록 일반/적군 16개 item definition·model·PNG를 제공한다. 적군 관계 판정은 추가하지 않았다.
- 생성기 `scripts/art/build_grenades_w252.py`와 `art/abilities/w252/grenade-manifest.json`에 geometry·텍스처·크기·원본 해시·산출물 해시·한계를 기록했다. 8종 모두 새로 설계한 큐브와 atlas이며, FBX 삼각형이나 ripped PNG 픽셀을 제품에 복사하지 않았다.

| 능력 ID | 외형 |
|---|---|
| `hunter/arc_flashbang` | flashbang |
| `hunter/solar_incendiary` | incendiary |
| `hunter/void_vortex`, `warlock/void_grenade` | vortex |
| `titan/arc_grenade` | pulse |
| `titan/solar_grenade` | fusion |
| `titan/void_grenade` | suppressor |
| `warlock/arc_grenade` | storm |
| `warlock/solar_grenade` | solar |

## 실루엣 근거와 provenance

공유 Drive의 Ability Weapons/Hunter/Titan/Warlock에는 요청한 8종 개별 원본이 없었다. 추가 조사에서 [Misc/Four Grenade Types.7z](https://drive.google.com/file/d/1yEfOLn_FJGT2tY5Q5oRNtA0OCnjkt2fQ/view)를 확보했다. 2,370,535 bytes, SHA256 `b3183e471b5ce992a463e4b779a2ce9f0530aab538f770fd21c908ea772bb75f`.

이 archive에 Explosion/Pulse/Magnetic/Spike의 FBX·Diffuse/Normal과 `Grenades.blend`가 있다. 원본 FBX는 메모리에서 파싱해 정점/면을 확인했고 Diffuse PNG와 무텍스처 소프트웨어 투영 이미지를 열어 비교했다. **Blender 원본 scene 평가나 FBX scene transform/material 재현은 하지 않았다.** 투영 이미지의 각 Geometry는 개별 정규화되므로 조립체의 정확한 배치 증거로 사용하지 않는다. master가 평가한 `80A8A67C`는 투척 애니메이션 근거이며, 이 문서의 prop 메시 검토와 별개다.

| 외형 | 요소 수 | 확인 근거 및 확정 수준 |
|---|---:|---|
| flashbang | 87 | 실제 `Explosion Grenade.fbx`의 둥근 어두운 하부·밝은 어깨/콘·옆 레버를 검토한 재구성. [Flashbang 비행 이미지](https://destiny.wiki.gallery/images/thumb/0/0a/Flashbang_Grenade.jpg/350px-Flashbang_Grenade.jpg)와 형태 대응. archive 명칭은 Explosion이며 Flashbang이라는 개별 tag 매핑은 미확정. |
| pulse | 80 | 실제 `Pulse Grenade.fbx` 검토 재구성. 긴 캡슐·중앙 드럼·극 캡·바깥 전극 보존. 원형 에너지 구체로 대체하지 않음. |
| incendiary | 88 | Explosion 계열의 **잠정 응용**. 좁은 퓨즈·뜨거운 적도 띠. 게임 참고 이미지는 폭발 장면이라 전용 껍질 형태를 증명하지 못함. |
| suppressor | 88 | Explosion 계열의 **잠정 응용**. 넓고 낮은 본체·낮은 퓨즈·void 띠. 전용 ripped 메시를 확보했다고 주장하지 않음. |
| vortex | 65 | 게임 에너지 참조 기반의 어두운 핵과 교차하는 열린 violet arc. **projectile 메시 구조 미확정**. |
| fusion | 59 | 비행 중 작은 밝은 불씨와 뾰족한 corona 참고. 작은 핵·비대칭 여섯 갈래. **ripped 메시 미확보**. |
| storm | 57 | 게임 번개 에너지 참조 기반의 밝은 핵과 갈라진 arc. **projectile 메시 구조 미확정**. |
| solar | 61 | 게임 태양 에너지 참조 기반의 큰 둥근 광구·불꽃 돌출부·열린 flare. **ripped 메시 미확보**. |

직접 변환한 실제 리핑 제품 모델은 **0종**이다. 실제 리핑 메시를 검토해 새 큐브로 재구성한 것은 Flashbang/Pulse 2종이며, 나머지 6종은 위 수준의 근거만 있다. 모든 8종이 원작과 정확히 일치한다고 보고하지 않는다. archive의 ripper·게임 빌드·추출 시점은 명시되지 않았다. 원작 디자인은 Bungie 소유이며 커뮤니티 자료를 공식 배포물로 표기하지 않는다.

FBX source SHA256:

- Explosion: `d4833b00b30efea11d0a8e9fccdea75d7d2874a66c1d394a32b79136c6c7a9cc`. Geometry `f3eab080_0`, 정점570·polygon index2538.
- Pulse: `1ed683efe866ec5e4611390fd3872e1b1663e4e7cdef71558dfd1179c4f08df0`. Geometry `20f2b080_0`, `_6`, 정점614/198·polygon index2610/486.

Wiki의 실제 게임 이미지 8개 URL·SHA256은 manifest에 있다. Flashbang은 물체가 보이는 비행 장면, Fusion은 밝은 비행 불씨이며, 다른 이미지들은 주로 폭발/에너지 참고다. 원 URL의 403 응답 후 공개 350px thumbnail을 확보했다. `/Volumes/qf-ssd/Destiny-Light-Abilities-2026-10-28`는 읽기 전용으로 목록 확인했으며 별도로 이름 붙은 grenade prop 메시를 찾지 못했다. 이 SSD를 prop 원본 사용 근거로 적지 않았다.

## 크기와 재질

- 모든 회전 적용 AABB 중심은 `(8,8,8)`, 16 model units = 1블록. 기본 `NONE` 문맥의 최대 길이는 **8 units = 0.5블록**이다. 모델별 X/Y/Z 실측은 manifest `dimensions_blocks_none_scale1`에 있다.
- master의 FP prop scale **0.5~0.6** 적용 시 최대 길이 **0.25~0.3블록**. 런타임 scale 중복 적용을 피하도록 NONE/hand display transform은 넣지 않았다. GUI에만 회전/1.55배 미리보기 transform이 있다.
- 기계형/Pulse의 긴 방향은 +Y. 파지 기준은 중심이며 별도 손바닥/손목 offset은 없다. 왼손 부착·6tick release·20tick 회복과 실제 손 간섭은 master 검증 대상이다.
- 26.3의 `rotation: {origin,x,y,z,rescale:false}`를 사용한다. 큐브만 출력하며 임의 vertices/triangles 필드를 만들지 않았다. 실루엣은 faceted shell·돌출 레버/전극·열린 arc로 구분한다. 종간 단순 동일 기하 색상 치환이 아니며 일반/적군 한 쌍의 기하는 의도적으로 같다.
- 128×64 RGBA atlas 16개. 면별 UV를 명시하고 표면 체결부/패널선은 텍스처로 처리했다. 일반 opaque 텍스처이며 native emissive·additive bloom·움직이는 particle이 아니다. 실제 발광 인상은 master의 display brightness/이펙트에서 검증해야 한다.
- 적군 Flashbang은 흰 퓨즈의 붉은 점 패턴 대신 **기존 적도 띠의 연속 붉은 경고색**으로 구분했다. 기하를 늘리지 않았다. 이는 발광처럼 읽히는 색 띠이며 자체 발광 셰이더를 추가한 것이 아니다.

## 검사와 master 피드백

생성기 실행/`--check` 바이트 일치, 32 JSON 파싱, 16 PNG 디코드, item→model→texture 참조, 전체 회전 AABB 중심/최대 크기, 유한 좌표·양의 큐브 크기·면별 UV, 종간 8개 서로 다른 기하 fingerprint, 일반/적군 기하 동일성·PNG 차이를 확인했고 **통과했다**. 48개 산출물의 manifest SHA256도 실제 파일과 일치했다. 생성 대상은 48자산+manifest49개이고 전체 소유 파일은52개다.

Java 동결 SHA256: `5d10dc901c0e04579be53230b574e0c9d091c0e95078e4faafc1cee0e0564460`. 생성기 Python AST 파싱도 통과했다. 최종 적군 띠 수정 이후 제품 PNG를 다시 열어 흰 퓨즈의 붉은 점 제거와 연속 경고 띠를 확인했다. 전체 반환은 52개 소유 경로만 대상으로 하며, 중앙 compile/실게임 결과는 포함하지 않는다.

명령:

```sh
rtk proxy python3 scripts/art/build_grenades_w252.py
rtk proxy python3 scripts/art/build_grenades_w252.py --check
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 scripts/art/build_grenades_w252.py --check --preview /private/tmp/destiny-w252/assets/grenade-preview.png
```

원본 검토 이미지: [Explosion 3방향](/private/tmp/destiny-w252/assets/explosion-source-views.png), [Pulse 3방향](/private/tmp/destiny-w252/assets/pulse-source-views.png). 제품의 실제 출력 JSON/atlas를 rasterize한 [일반/적군 사선·옆면 프리뷰](/private/tmp/destiny-w252/assets/grenade-preview.png).

master는 **PNG 자산 미리보기**에서 8종의 기계/에너지 실루엣 차이·배색/디테일을 검수해 수락하고, provenance 구분과 적군 Flashbang의 붉은 노이즈 정돈을 요청했다. 이것은 **실게임 Vision 검수가 아니다**. 피드백 이후 붉은 노이즈를 기존 띠로 정리했다.

**미검증:** Java compile·실제 팩 로드·클라이언트 renderer/shader·1/3인칭 파지·FP 손과 release의 일치·적군 viewer 판정·10~20개 동시 표시 성능·실게임 Vision. 모두 master가 통합 후 취합한다. 오프라인 프리뷰를 native/실게임 성공으로 보고하지 않는다.

## Windows 추가 추출 요청

우선 Incendiary/Suppressor/Vortex/Fusion/Storm/Solar 6종의 held/projectile entity 메시와 능력별 태그/hash/원본명/게임 버전이 필요하다. Explosion을 Flashbang/Incendiary/Suppressor 중 어느 능력이 공유하는지 확인하고, Pulse의 정확한 entity/material 연결도 보강해야 한다.

FBX/GLB 또는 Blender scene, basecolor·normal·material/UV를 포함한다. Vortex/Fusion/Storm/Solar는 particle sprite/flipbook·emissive·alpha 텍스처/셰이더 연결도 필요하다. 별도 물리 메시가 없는 경우 그 사실과 투척 전·비행 중 3방향 gameplay 캡처를 요청한다. 검토된 두 메시도 원본 scene 평가 없이 정확한 조립·PBR 복원을 보증하지 않는다.
