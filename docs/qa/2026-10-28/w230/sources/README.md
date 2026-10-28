# W230 source / DDC / audio 전달

소유·작성 범위는 `/private/tmp/destiny-w230-sources`만이다. main/worktree/중앙 build/game/CU/live Blender/SSD 쓰기, 외부 메시지, 추가 agent 호출은 수행하지 않았다.

## DDC

- `early-cooldown-duration.md`: 11종 기본 CD·지속시간 선행표.
- `ddc-values.json`: ID/class/element/CD/duration tick 및 exact_cells·URL·조회시각·SHA.
- `ddc-conditions.json`: 관련 용어·aspect 조건 15행 원문.
- `ddc/*.html`, `*-fetch.json`, `*-rows.json`: 새 HTTP 조회 근거.
- 초→20TPS tick만 직접 환산. 피해·거리·HP는 D2=MC 동일 환산하지 않는다. `?`, 괄호 PvP와 조건은 유지한다.
- Storm's Edge 지속/드레인은 DDC 미확정. Spectral 23.5초는 은신 드레인 기준이며 비은신 50% 빠른 소모다.
- Gathering은 단발 시전 뒤 2초 낙뢰, 추가1.2초 뒤 8초 field다. field 길이를 cast 길이로 사용하지 않는다.
- Ward/Well은 기본30초와 Super Stat200 최대40초를 구분한다. Maul은 기본25초와 Sol Invictus42초를 구분한다.
- game-mechanics 행17: Supers do not experience Chunk Modifiers. Chunk Scalar를 기본 CD에 곱하지 않는다.

## 오디오 fragment

원본은 `downloads/`에 보존(저장소 밖). 런타임 OGG만 `output/payload/assets/destiny/sounds/classes_w230/`에 두었다. `output/sounds-additions.json`은 **기본 28키** 병합용 fragment이며 기존 sounds.json을 덮어쓰지 않는다. 모델 helper/normal-red path는 이 담당 범위가 아니다. 신규 sound key는 `<class>.<element>.<super>.start|fire|impact|end`, Super suffix 없는 ID다.

`output/sounds-ward-optional-NOT-default.json`의4키는 Sentinel 동일 직업/속성 후보이며 Ward 고유 음원으로 식별되지 않았다. **기본 병합 제외**. master가 명시 수락할 때만 시험 연결한다.
`output/audio-provenance.json`: 32개 원본 경로·Drive ID/URL·SHA·선택 구간·processing·confidence·auditioned=false. `output/listening-table.html`로 청취 가능.

| family | 기본 연결 키 | 상태 |
|---|---|---|
| `blade_barrage` | start, fire, impact, end | 전용 폴더/숫자 역할 tentative |
| `spectral_blades` | start, fire, impact, end | 전용 폴더/숫자 역할 tentative |
| `gathering_storm` | start, impact | 명명된 역할 우선; 청취 전 |
| `storms_edge` | 없음 | 승인 Drive에서 식별 안 됨 |
| `thundercrash` | start, impact | 명명된 역할 우선; 청취 전 |
| `burning_maul` | start, fire, impact, end | 전용 폴더/숫자 역할 tentative |
| `ward_of_dawn` | 없음 | 동일 Titan Void Sentinel 4후보만; Ward 원작 여부 미확정, 기본 제외 |
| `well_of_radiance` | start | 계열명 composite start 임시; phase 미분리 |
| `chaos_reach` | start, fire, end | 명명된 역할 우선; 청취 전 |
| `nova_warp` | start, fire, impact, end | 전용 폴더/숫자 역할 tentative |
| `fists_of_havoc` | start, fire, impact, end | 전용 폴더/숫자 역할 tentative |

모든 파일 mono Vorbis 실제 decode/유한값/프레임수 확인. 최대8초, 전체 런타임 약1.29MB. 긴 원본은 첫8초만 취하고 마지막25ms fade를 적용한다. 원본은 보존하며 원작 onset을 식별했다는 뜻이 아니다. 정규화·임의 gain·리샘플은 하지 않았다.
숫자 후보의 start/fire/impact/end 순서는 선택용 임시 배치이며 실제 동작 대응을 청취/원작 Wwise로 확인하지 않았다. 같은 clip을 소모·피해 tick마다 반복하지 않는다.
Gathering impact에는 pulse가 함께 들어 있으므로 embed에1회만 재생한다. Thundercrash impact는 명명 Far variant이므로 Nearby와 같은 mix라고 주장하지 않는다. Well은 composite 첫8초만 start에 연결하고 fire/end를 임의 분리하지 않는다.
Chaos Reach pre-fire/fire/end는 명명 파일이다. 별도 impact는 찾지 못해 빔 피해 tick에 fire를 중복 연결하지 않는다.

## 미확보 sound 역할

아래 키는 무음 fallback/기존 vanilla fallback을 제품에서 선택하되, 엉뚱한 궁극기 음원을 원본처럼 배정하지 않는다.
- `hunter.arc.gathering_storm.fire`
- `hunter.arc.gathering_storm.end`
- `hunter.arc.storms_edge.start`
- `hunter.arc.storms_edge.fire`
- `hunter.arc.storms_edge.impact`
- `hunter.arc.storms_edge.end`
- `titan.arc.thundercrash.fire`
- `titan.arc.thundercrash.end`
- `warlock.solar.well_of_radiance.fire`
- `warlock.solar.well_of_radiance.impact`
- `warlock.solar.well_of_radiance.end`
- `warlock.arc.chaos_reach.impact`

승인 Drive `_SUPERS`22개 folder metadata와 `__UNSORTED`2505개 metadata를 새로 조회했고, 전용 Storm's Edge/Ward 명명 파일은 확인되지 않았다. 이것은 Drive 전체 모든 경로의 부재 증명이 아니다. 다음 Windows 소스 전달 시 Storm's Edge 원작 및 Ward 고유 음원, 기타 미분리 end 역할을 요청할 수 있다.

## 원작 모션 범위

`source-clip-scope.md`에 인덱스 기준 추가10궁극기40clip+Fists6clip의 확보 범위를 명시했다. 실제 포팅/리깅 검증은 animation leader가 소유하며 authored fallback와 원본을 구분해야 한다.

## 통합

1. 필요한 OGG를 `output/payload/assets/`에서 main `src/main/resources/assets/`로 복사.
2. `output/sounds-additions.json`의28 top-level 키만 additive merge. `sounds-ward-optional-NOT-default.json`은 기본 제외.
3. master가 신규 궁극기 ID별 action을 명시 dispatch. 기존 `<class>.<element>.super.*`와 다르므로 기존 helper 호출만으로 자동 연결됐다고 가정하지 않는다.
4. source docs와 provenance만 선택 보관. downloads/HTML 원본/token/live게임파일은 저장소에 넣지 않는다.
5. 청취/실게임/packet timing은 master 검증 대기. 이 작업에서 검증한 것은 source/hash/codec/키 resolve다.
