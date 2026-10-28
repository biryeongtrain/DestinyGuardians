# Windows 추가 추출 요청 — W229

## 지금 반드시 필요한 범위

**타이탄 전기 Fists of Havoc / 대혼란의 주먹의 정확한 원본 모션 식별·추출.** 두 SSD 전달본을 모두 확인했다. Super 전달본의 `super-coverage.json`은 이 계열을 `not_individually_identified`로 기록한다. 전체 2171 clip의 이름·그룹·이벤트에서 `fist/fists/havoc/striker`를 확인한 결과 Hunter fist 근접 3개만 매치한다. 미분류 clip 안에 있을 가능성은 남으며, 파일 자체가 없다고 단정하지 않는다. Thundercrash, Burning Maul, Hunter fist로 대체하지 않는다.

- 필요한 동작 의미: 지상/공중 시전, 유지/이동, 약공격(어깨 돌진) 및 연계·복귀, 강공격(도약/하강/지면 충격/착지 복귀), 정상 종료. 원하는 항목명이 원본 action 이름이라는 뜻은 아니다. 실제 source action/query 이름·clip tag/hash를 함께 보내 달라.
- 리그: 원래 3P full-body skeleton/runtime rig, bone index/name/parent/rest bind matrix, root motion·scale·축·단위. 기존 source는 player entity `80C304B9`, skeleton `80C3ABDE`, runtime rig `80C3AC72`, 72 bones이다. 일치 여부를 검증하고 다르면 해당 전용 rig를 함께 제공. 무기 1P 또는 Hunter rig로 치환 금지.
- 시간: 원본 clip 전 프레임, native FPS, 원래 start/end frame, 시전·공격 활성·충돌·종료 markers의 frame 및 초, ground/air와 Base/Replacement layer 구분. 30fps로 강제 재표본하거나 없는 구간을 보간해 만들어 보내지 말 것. 원본이 30fps인 경우 그대로 유지.
- 증거: `.blend`/FBX + 원본 raw clip/skeleton/runtime bytes, manifest, SHA256/bytes, 게임 build/package/tag/query provenance. 원본 선택 상태가 보이는 bone 또는 mesh playback MP4와 cast/attack/exit별 확인 시점. Hunter 같은 이름의 clip을 Fists로 재명명하지 말 것.
- 오디오: Fists 시전/약공격/강공격 충격/유지/종료의 Wwise event path·ID → 실제 media ID/file 관계, 원본 WAV/OGG(가능한 원본 codec 보존), loop begin/end와 gain. 현재 `Titan_Striker`의 숫자 음원은 확보했으므로 동일 파일 재전송보다 정확 매핑만 우선해도 됨.
- 텍스처/VFX: 손·팔 번개/지면 충격 emitter에 실제 참조되는 mesh/material/texture 원본, UV, diffuse/albedo·normal·mask/packed channel·emissive·opacity, 채널 의미/색공간, attach bone/offset와 event frame. 임의 스킨·다른 궁극기의 VFX를 원본으로 간주하지 말 것.

## 추가 원본 재요청이 아니라 매핑/완전성 확인이 필요한 범위

다섯 궁극기(망치/방패/새벽칼날/폭풍몰입/신성폭탄)의 리그·실제 action은 이미 SSD에서 확보·평가했다. 이 다섯 전체를 다시 뽑아 달라는 요청은 아니다. 기존 `partial_source_association`은 완전한 시전/유지/공격/종료 세트나 gameplay variant의 독점적 대응을 보증하지 않는다. retarget 담당자가 특정 구간의 부족을 확정할 때 그 action만 추가 요청한다.

방벽, 균열, lift/glide, 일반 근접·수류탄 throw의 source-named 모션도 이미 발견했다. `80A8A9EB/80A8A9EC`는 Hunter/Titan/Warlock alias가 섞여 전용 증거로 사용하지 않으며, grenade charge의 `80A8A9BC/80A8ACAB/80A8ACB5`는 5시점 평가가 정적이어서 유효 동작으로 승인하지 않는다. 현재 11종 ability에 charge가 필요하지 않으면 이 세 clip 추가 요청은 불필요.

방벽(시전/유지/파괴/종료), 치유·강화 균열(시전/유지/종료), Titan lift/Warlock glide(활성/유지/비활성/착지), 전기·태양 수류탄의 **정확한 사운드 식별**은 미해결. 승인 Drive `__Supers & Abilities` 12개 하위 항목과 `__UNSORTED` 2505개 metadata 전체 페이지를 확인했으나 의미 있는 전용 파일명은 없었다. 없는 파일이라고 단정하지 않으며, 숫자 media의 Wwise event → media/file 매핑 또는 해당 cue만 이름 붙인 원본 export를 요청한다. 사용자 허용에 따라 여섯 궁극기의 숫자 start/fire 후보는 `tentative` 상태로 준비했다.

소품 3종과 Scatter의 `.blend`/FBX/텍스처는 이미 확보했으므로 재추출 요청 불필요. 소품 스튜디오 HDRI 누락은 게임 asset 누락으로 세지 않는다. 소품 MRC 등의 정확 packed channel 의미/셰이더 동등성이 필요하면 채널 문서/원본 material metadata만 추가 요청한다.
