# W229 타이탄·워록 원본 조사 결과

모델 4종 원본 archive + 미리보기 4개, 오디오 원본 40개를 선별 확보했다. 다섯 궁극기 계열 46 action과 일반 능력 후보 67 clip을 별도 headless Blender에서 평가했다. **대혼란의 주먹은 source family 미식별**, 나머지 다섯은 부분 source association이다. 숫자 음원 역할은 사용자 허용에 따른 `tentative`이며 청취 확정이 아니다.

- 원본/파생물/파일ID·bytes·SHA256·provenance: [sources.json](sources.json).
- 소품 mesh/UV/material/texture 실측: [mesh-texture-index.json](evidence/mesh-texture-index.json).
- mono OGG 40개: [audio-index.json](processed/audio-index.json), [선택표 JSON](processed/selection.json), [청취용 HTML](processed/audio-review.html).
- 원본 action 선택 목록: [action-index.json](ssd/action-index.json), [5시점 실제 pose](ssd/action-poses.json).
- Windows에 보낼 정확 요청: [windows-request.md](windows-request.md).

## 소품 원본과 실측

| 원본 | Drive 파일 ID / bytes | mesh / vertices / triangles | UV / 주요 텍스처 |
|---|---|---|---|
| [Hammer of Sol.rar](https://drive.google.com/file/d/1wz_-zxoxhrzjAStmtOpEaneRcAQu2ZqK/view) | `1wz_-zxoxhrzjAStmtOpEaneRcAQu2ZqK` / 2,429,130 B | 1 mesh / 721 vertices / 1,094 triangles | uv3; Diffuse + Normal 1024×1024 |
| [Sentinel Shield (ripped by Ginsor).rar](https://drive.google.com/file/d/1YEzR-13z_iSCYCT89P2pzX_DLO1-WtE0/view) | `1YEzR-13z_iSCYCT89P2pzX_DLO1-WtE0` / 2,171,959 B | 1 mesh / 1,591 vertices / 2,606 triangles | UVMap; Diffuse + Normal + MRC 512×1024 |
| [Dawnblade Sword (ripped by Ginsor).rar](https://drive.google.com/file/d/1ATLIQYxjjDRBKHvDdB9D95eFqKGxNR9Y/view) | `1ATLIQYxjjDRBKHvDdB9D95eFqKGxNR9Y` / 1,479,287 B | 1 mesh / 6,282 vertices / 8,476 triangles | UVMap; Diffuse + Normal + MRC + Emission 256×512 |
| [Scatter Grenade (ripped by riflesniper).7z](https://drive.google.com/file/d/1LhQ066YTQXh_vDAIhTrPY7K8cMlg8YLQ/view) | `1LhQ066YTQXh_vDAIhTrPY7K8cMlg8YLQ` / 723,361 B | 3 meshes / 808 vertices / 768 triangles | uv0 + uv1; base color 80C3C18E.png + normal 80C3C190.png, 512×128 |

압축 해제 원본은 `extracted/` 아래에 있다. `.blend`/FBX와 필요한 텍스처만 선택 추출했고 Scatter `.blend1` 백업은 추출하지 않았다. archive와 모든 추출 member 해시/용량은 `sources.json`에 있다. 미리보기는 Drive 원본 PNG이며 새로 만든 모델 이미지가 아니다.

네 소품 모두 **armature 0, action 0, vertex group 0, armature modifier 0**. Scatter Closed 196 / Lights 32 / Open 540 triangles이며 Closed·Open을 동시에 하나의 상태로 표시하지 않는다. 고유 states와 lights를 합한 source 총합은 768이다.

소품 3종의 world dimensions(X/Y/Z): 망치 0.092829 / 0.261169 / 0.444133, 방패 0.510079 / 0.067564 / 0.510107, 검 0.168268 / 0.042412 / 0.936289. 이는 source scene 단위의 실측이며 Minecraft 크기 환산값이 아니다.

실제 source PNG로 실루엣을 확인했다. 망치의 새 머리·손잡이, 방패의 원형 테두리·중앙 문양, 검의 가늘고 긴 칼날·가드 형태를 살린 cube+triangle 재구현은 가능 후보이다. 원본 triangles를 그대로 1요소씩 옮기면 망치/방패/검은 1,000 상한을 넘는다. 큰 입체와 면 UV를 다시 설계해야 하며, **이번에 1,000 이하 아트 산출/검증을 했다는 뜻은 아니다**. Scatter는 원본 삼각형 총합부터 768이지만 최종 어댑터 요소 수/성능/UV 보존은 별도 검증 대상이다. 제품 모델·아트 생성은 하지 않았다.

Ginsor 모델에는 외부 studio HDRI 참조가 있으나 전달 archive에 없다. 이는 조명 배경 누락으로 별도 게임 texture 누락으로 세지 않는다. Scatter의 일부 dummy/iridescence image는 `.blend` 내부 packed 상태이며 크기·SHA256을 index에 기록했다. unused helper material/image 경로가 있어 전체 원본 shader 동등성을 보증하지 않는다. MRC 채널 의미는 이름만으로 확정하지 않았다.

## 실제 SSD 궁극기 리그

Super 전달본: `/Volumes/qf-ssd/DestinyGuardians-Super-Animation-VFX-2026-10-27/destiny-animation-return`.
기존 추출 provenance: game build 25932352 / version 245114.26.10.13.2000.v500_live.main, 3P player entity 80C304B9, skeleton 80C3ABDE, runtime rig 80C3AC72. **72 bones / 30 fps / mesh 0**.

| ability | group / 실제 action 수 | 대표 실제 action | frame range / duration |
|---|---|---|---|
| titan/solar_super | `titan_hammer_of_sol` / 7 | `Armature|80A8A8FE_hammer_cast|Base` | [1.0, 39.0] / 1.266667s |
| titan/void_super | `titan_sentinel_shield` / 14 | `Armature|80A8A928_titan_sentinel_shield_cast_enter|Base` | [1.0, 43.0] / 1.400000s |
| warlock/solar_super | `warlock_daybreak + event_linked` / 12 | `Armature|80A8A921_warlock_archangel_cast|Base` | [1.0, 48.0] / 1.566667s |
| warlock/arc_super | `warlock_stormtrance` / 9 | `Armature|80A8A8B0_warlock_stormcaller_lightning_cast_enter|Base` | [1.0, 38.0] / 1.233333s |
| warlock/void_super | `warlock_nova_bomb` / 4 | `Armature|80A8AD80_warlock_voidwalker_novabomb_cast|Base` | [1.0, 40.0] / 1.300000s |
| titan/arc_super | **Fists of Havoc 미식별** | Thundercrash/Hunter fist 대체 금지 | 원본 미확정 |

46개 action 모두 5시점 pose 행렬이 유한하고 변화가 확인됐다. source `.blend`를 열어 실제 action/slot/armature를 평가했으며 cache JSON만 본 결과가 아니다. 시점 변화 확인은 원작 gameplay의 시전/충돌/종료 또는 retarget 품질 수락과 다르다. 원본 `.blend` 해시는 읽기 전후 일치했고 전달 FILE_HASHES와도 일치한다.

일반 능력 source-named 후보도 67 clip 식별했다: 방벽 `80A8AD7C/80A8AD79`, 치유 균열 `80A8AA08/80A8AA01/80A8A9FE`, 강화 균열 `80A8AA04/80A8AA03/80A8AA06`, lift `80A8A668`, glide 활성 `80A8A738`/유지 `80A8A6A6`, 망치 근접 throw `80A8AB1D`, 방패 throw `80A8ABCA` 등.

전체 평가 113 clip 중 110개는 5시점 행렬 변화가 있고, charge 관련 `80A8A9BC/80A8ACAB/80A8ACB5` 3개는 정적이다. `80A8A9EB/80A8A9EC` 두 개에는 Hunter/Titan/Warlock alias가 혼재하므로 전용 모션 근거로 사용하지 않는다. 추정 애니메이션이나 retarget 산출물은 만들지 않았다. 필요한 113 raw clip + skeleton/runtime rig 2개를 `ssd/raw/`에 복사했고, 6개 궁극기 group의 원본 `.blend`/FBX/clip metadata도 `ssd/`에 복사했다. 일반 능력 `.blend`는 SSD 원본 경로와 해시를 참조한다.

두 번째 `/Volumes/qf-ssd/DestinyGuardians-Animation-Return-2026-10-27/destiny-animation-return`은 32 group / 332 clip+rig 조합의 무기 reload/ready/fire 전달본이다. target Titan/Warlock super 전용 group은 없다. `hammerhead`처럼 무기 이름 때문에 발생한 substring match를 Fists/Hammer of Sol 발견으로 세지 않았다. [두 번째 SSD 조사](evidence/second-ssd.json).

## 오디오 선택표

원본 40개 → mono OGG/Vorbis 40개, 총 1,334,445 B. 원본 decode → 채널 산술 평균 → OGG, 자르기·리샘플링·gain 조절·정규화 없음. 모든 OGG를 재decode하여 1채널/샘플레이트/정확 프레임 수/유한 샘플을 확인했다. Vorbis는 손실 압축이며 원본은 별도로 보존했다. 망치 명명 파일은 **44.1kHz**이며 숫자 supers 후보는 주로 48kHz다. 앞선 중간 업데이트의 망치 48kHz 표기는 정정한다.

아래 시간은 **원본 파일에서 사용 가능한 전체 sample 구간**이다. 제품 start/fire 이벤트 발생 즉시(상대 0초) 재생하는 검토 후보이며, 원작 애니메이션의 실제 sound onset과 매칭됐다는 뜻이 아니다. 숫자 파일은 전부 `tentative_folder_family_only`, 청취 미수행.

| ability / role | source / ID | source 구간(초) | mono OGG |
|---|---|---|---|
| titan/solar_super / start **tentative** | `0215-000016E1.mp3` / `1u6cxrYTgaP_BDQn_8T-Q2ijiVtNu8U3O` | 0–5.472000 | [0215-000016E1.ogg](processed/ogg/sound-sunbreaker/0215-000016E1.ogg) |
| titan/solar_super / fire **tentative** | `0215-000016E2.mp3` / `1Je2htqfix1749FgpA_8jc5p8f2TI9bHe` | 0–5.328000 | [0215-000016E2.ogg](processed/ogg/sound-sunbreaker/0215-000016E2.ogg) |
| titan/arc_super / start **tentative** | `0215-0000164C.mp3` / `1TBRCnBWs7kYHl6UvfMekFd6X13BQDh9p` | 0–1.488000 | [0215-0000164C.ogg](processed/ogg/sound-striker/0215-0000164C.ogg) |
| titan/arc_super / fire **tentative** | `0215-0000164D.mp3` / `1lucBGl3DZrriWoOOHsycuiBoh1kOpb4J` | 0–1.800000 | [0215-0000164D.ogg](processed/ogg/sound-striker/0215-0000164D.ogg) |
| titan/void_super / start **tentative** | `0215-000016EA.mp3` / `1cpGj1P-iC7QR5pqUuux0ki7FhkXcZfox` | 0–1.632000 | [0215-000016EA.ogg](processed/ogg/sound-sentinel/0215-000016EA.ogg) |
| titan/void_super / fire **tentative** | `0215-000016FF.mp3` / `1E9XrL3hP5J7dQ7oZA3gIC6HzL1I5yJAl` | 0–1.152000 | [0215-000016FF.ogg](processed/ogg/sound-sentinel/0215-000016FF.ogg) |
| warlock/solar_super / start **tentative** | `0215-0000173A.mp3` / `1tMQ8guZ4kng8JJbFJXMhQ0-MHhoDsPYW` | 0–4.080000 | [0215-0000173A.ogg](processed/ogg/sound-dawnblade/0215-0000173A.ogg) |
| warlock/solar_super / fire **tentative** | `0215-0000173B.mp3` / `1REU9RJBW0TprG0yO09LFD7cGi90O4lIH` | 0–3.240000 | [0215-0000173B.ogg](processed/ogg/sound-dawnblade/0215-0000173B.ogg) |
| warlock/arc_super / start **tentative** | `0215-000015CD.mp3` / `1HFABKo3tl3GbZATCq0gzUDDFlc8FDJRv` | 0–1.464000 | [0215-000015CD.ogg](processed/ogg/sound-stormtrance/0215-000015CD.ogg) |
| warlock/arc_super / fire **tentative** | `0215-000015CE.mp3` / `1LPc3pRjHZjUJ6WarAGXpNLelXwN-qzcy` | 0–1.968000 | [0215-000015CE.ogg](processed/ogg/sound-stormtrance/0215-000015CE.ogg) |
| warlock/void_super / start **tentative** | `0215-000016D4.mp3` / `12CmGQ3pr-6x6ctSKlZhiX6Clykve4OAI` | 0–4.056000 | [0215-000016D4.ogg](processed/ogg/sound-novabomb/0215-000016D4.ogg) |
| warlock/void_super / fire **tentative** | `023D-0000123B.mp3` / `1d94XyY5eFicqbdHqM-IDKFW1caqhLTmF` | 0–2.496000 | [023D-0000123B.ogg](processed/ogg/sound-novabomb/023D-0000123B.ogg) |

### 망치 명명 cue — 파일명 역할 확인

`Titan - Throwing Hammer` source folder의 명명 원본이다. throw/entity impact/ground impact 역할 이름을 그대로 연결할 수 있으나, **이 원본은 근접 투척 망치 폴더이며 Hammer of Sol 궁극기와의 Wwise media 대응까지 증명한 것은 아니다**. 궁극기에도 같은 cue를 쓰면 명시적 공유/임시 선택으로 기록한다.

| role | 원본 / ID | source 구간 / sample rate | mono OGG |
|---|---|---|---|
| throw | `Hammer_Throw_1.mp3` / `1qrGnUvUoYh1JZ9OPzLhez6gPB6-dZzOa` | 0–1.071020s / 44100Hz | [Hammer_Throw_1.ogg](processed/ogg/sound-throwing-hammer/Hammer_Throw_1.ogg) |
| entity_impact | `Hammer_Impact_1.mp3` / `1tvqLYL6ej8tj2zWFGQP-3DGQ8WZl1IRh` | 0–2.142041s / 44100Hz | [Hammer_Impact_1.ogg](processed/ogg/sound-throwing-hammer/Hammer_Impact_1.ogg) |
| ground_impact | `Hammer_Ground_Impact_1.mp3` / `1XZHVkqprISOIvKv1S6Mhun29iIdOBBya` | 0–1.802449s / 44100Hz | [Hammer_Ground_Impact_1.ogg](processed/ogg/sound-throwing-hammer/Hammer_Ground_Impact_1.ogg) |
| fly_by | `Hammer_Fly_By_1.mp3` / `1N5cC5ruMR_fg1jxR16he3vq91agyJJno` | 0–2.089796s / 44100Hz | [Hammer_Fly_By_1.ogg](processed/ogg/sound-throwing-hammer/Hammer_Fly_By_1.ogg) |
| explosion | `Hammer_Exp_1.mp3` / `14qiUT2tAXUPw52gKut__M-CKSYGH42jj` | 0–2.821224s / 44100Hz | [Hammer_Exp_1.ogg](processed/ogg/sound-throwing-hammer/Hammer_Exp_1.ogg) |

명명 원본 추가 확보: Ball Lightning `Ball_Proj_1`와 Void Axion/Magnetic/Scatter/Suppressor/Vortex의 throw·explosion 각 1개. 실제 구현한 수류탄 종류와 일치하는 파일을 선택한다. 전용 방벽·균열·lift/glide·전기/태양 수류탄의 정확한 사운드 매핑은 아직 식별하지 못했다. 일반 Jump Landing의 `File1906-broken.wav` 1개는 diagnostic용으로만 확보했다. 파일명에 broken이 있으나 afinfo 및 실제 decode는 성공하며, 특정 직업 이동 cue로 승인하지 않는다.

원본 source event 근거: Hammer throw action `80A8A8AE`에는 `thermal_hammer_throw.wwise_event` frame 0과 `thermal_hammer_spawn.wwise_event` frame 15(0.5s)가 있다. Sentinel throw `80A8A924`에는 `void_shield_throw.wwise_event` frame 0이 있다. 이 event들과 Drive 숫자/명명 음원의 media ID 대응은 확보하지 못했으므로 음원 frame 매칭 확정으로 쓰지 않는다.

## 탐색 범위·남은 요청

승인 Drive 두 루트와 필요한 Titan/Warlock 소품 폴더를 실제 HTTP200으로 조회했다. 오디오는 public Drive metadata API의 pagination을 끝까지 소비하여 Supers & Abilities 12, UNSORTED 2,505(3 pages), Sunbreaker 57, Sentinel 44, Dawnblade 50, Stormtrance 53, Striker 16, Novabomb 35, Jump Landing 416 항목을 확인했다. metadata 목록 확보와 대량 원본 다운로드를 구분했다. 실제 다운로드는 선별된 40음원·4소품 archive·4미리보기뿐이다. HTML 첫 50개만 보고 나머지가 없다고 판단하지 않았다.

**모션 family 단위로 미식별인 궁극기는 Fists of Havoc 하나**다. 다섯 기존 궁극기도 완전한 시전/유지/종료 세트 인증은 아니며, 일반 능력의 정확 오디오 매핑과 packed texture/원작 shader 의미는 별도 미확정이다. 추가 원본 요청을 Fists에 집중하고, 다른 것은 필요한 cue/action의 ID 매핑·누락 구간만 좁혀 요청한다. [복사 가능한 Windows 요청문](windows-request.md).

main/worktree 파일·게임 입력·빌드·커밋·live Blender 변경 없음. 모든 shell command는 rtk prefix. 별도 headless `--factory-startup --disable-autoexec`, `open_mainfile(load_ui=False,use_scripts=False)`로 원본만 평가하고 저장하지 않았다. 사용자 지시 변경 후 SSD retarget 중복 작업은 하지 않았다. 자식 agent를 생성하지 않았으며 user-owned 다른 chat으로 메시지를 보내지 않았다.

## 추가 수락 작업 — 복사 가능한 사운드 fragment

`processed/installed-assets/`에 `assets/destiny/sounds/classes_w229/*.ogg`, `sounds-additions.json`, `provenance-mapping.json`, `listening-table.html/md/csv`를 작성했다. [설치용 ZIP](processed/installed-assets.zip), [병합 안내](processed/installed-assets/README.md), [실제 mapping](processed/installed-assets/provenance-mapping.json).

18 event key(12 super.start/fire + solar hammer melee.cast/impact + Titan suppressor throw/impact + Warlock vortex throw/impact), 17 unique mono OGG. Solar super.fire는 짧은 명명 Hammer_Throw_1을 melee.cast와 의도적으로 공유하고 super Wwise 미확정을 표시했다. Numeric super 11개 역할은 tentative. Ball Lightning → Chain Lightning 연결은 없다. key/path/hash/decode 검증을 완료했고 main/worktree는 수정하지 않았다. Titan super.fire의 runtime hook은 읽은 코드 snapshot에서 미연결이어서 master 통합 메모에 남겼다.
