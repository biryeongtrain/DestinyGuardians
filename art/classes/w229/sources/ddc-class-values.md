# DDC Titan / Warlock classic abilities — read-only 근거표

조회: **2026-10-28 11:47:58–11:48:54 UTC (20:47:58–20:48:54 KST)**. 사용자 지정 DDC 원본의 Class Abilities / Arc / Solar / Void와 조건 확인용 Landing / Game Mechanics를 실제 HTTP 200으로 읽었다. 아래는 조회 당시의 **표시값 전사**이며 게임 실측/수치 테스트 결과가 아니다. 메인·worktree·스프레드시트는 수정하지 않았다.

## 기본 쿨다운과 지속시간

단위는 모두 **초(seconds)**. 능력 이름 B열, 설명 D:M 병합셀, cooldown N열. N51:N52처럼 병합된 경우 아래 별도 표기. `—`는 미기재이며 0이 아니다.

| 분류 / 능력 | 원본 탭·행 | 기본 쿨다운 (s) | 지속시간 / 원문 조건 |
|---|---|---:|---|
| Titan Rally Barricade | [class-abilities r22](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=527596209&range=B22:N22) | 55.1 | 방벽 20s; Chunk Scalar 1x. |
| Titan Towering Barricade | [class-abilities r26](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=527596209&range=B26:N26) | 101.3 | 방벽 20s; Chunk Scalar 0.5x. |
| Warlock Empowering Rift | [class-abilities r41](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=527596209&range=B41:N41) | 118.7 | 균열 15s; Chunk Scalar 0.5x. |
| Warlock Healing Rift | [class-abilities r43](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=527596209&range=B43:N43) | 118.7 | 균열 15s; Chunk Scalar 0.5x. |
| Titan Hammer of Sol | [solar r105](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B105:N105) | 556 (Tier 2) | Base Duration 21s; 수동 공격은 에너지를 추가 소모. 망치 투척 간격 1.5s. |
| Titan Hammer of Sol — Sol Invictus Aspect | [solar r107](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B107:N107) | 556 (Tier 2) | 별도 장착 행: Base Duration 16.5s. Sunspot buff는 passive drain 40% 감소 → 27.5s; 투척 간격도 buff 시 1s로 변경. |
| Titan Fists of Havoc | [arc r98](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=618967225&range=B98:N98) | 556 (Tier 2) | Base Duration 25s. N98 원문은 “Tier 2 Super / 556 seconds.”이며 이 셀에는 “Base Cooldown” 문구가 생략되어 있다. |
| Titan Sentinel Shield | [void r96](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B96:N96) | 556 (Tier 2) | Base Duration 17s. 공격/방어/뒤쪽 아군 수에 따라 에너지 소모와 지속시간 변경. 연속 방어 연장은 ?%; Super 중 Shield Throw 간격 3s. |
| Warlock Daybreak | [solar r137](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B137:N137) | 556 (Tier 2) | Base Duration 24s. 투사체 발사 6.5%, 강화 Icarus Dash 4.2% Super Energy 추가 소모. |
| Warlock Stormtrance | [arc r126](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=618967225&range=B126:N126) | 556 (Tier 2) | Base Duration 16s. Light Attack 소모는 ?%; Ionic Blink는 6.25% 추가 소모. |
| Warlock Nova Bomb: Cataclysm | [void r125](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B125:N125) | 500 (Tier 3) | Base Duration 기재 없음. 단발 투사체/폭발/추적체 설명으로 시간제 roaming super와 구분. |
| Warlock Nova Bomb: Vortex | [void r127](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B127:N127) | 500 (Tier 3) | 특이점은 폭발 후 0.43s에 생성, 10s 동안 피해. 이 10s는 **특이점 효과 지속시간**, 시전 동작/roaming super 지속시간이 아님. |
| Titan Throwing Hammer | [solar r99](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1186062409&range=B99:N99) | 131.7 | Chunk Scalar 0.9x. 바닥 10s 후 자동 폭발. 주우면 121.5% Melee Ability Energy; 단순 cooldown 대기와 별도 에너지 회수 경로. |
| Titan Void Suppressor Grenade | [void r45](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B45:N45) | 175.6 | Chunk Scalar 0.625x. Suppression 10 [5]s = PvE 10s / PvP 5s. 수류탄 비행/폭발 지연 시간이 아님. |
| Warlock Void Vortex Grenade | [void r51](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B51:N51) | 219.5 | Chunk Scalar 0.5x. 기본 필드 4s, 원문 작은 보라색 +1은 Remnants 조건(27행). 52행 Chaos Accelerant charged는 별도 4.3+2.3s. cooldown N51:N52 병합. |

## 스탯·강화·모드 해석의 경계

- 위 cooldown은 해당 셀의 “Base Cooldown” 표시 그대로다. **T0/T3/T10 또는 특정 현재 스탯의 실효 쿨다운으로 재명명하지 않았다.** Landing 38행은 Exotic Armors 안내 셀에 “For Ability Regeneration, 100 Stat is considered the Base Regeneration Speed.”라고 적는다. 이는 정확히 보존하되, 각 능력의 Base Cooldown이 모두 100 Stat 실효시간이라는 별도 증거로 확장하지 않는다.
- Game Mechanics 180–190행(Melee/Grenade), 196–199행(Class)은 스탯에 따라 Additional Base Regeneration/Ability Gains가 바뀐다고 설명한다. 0–100 Stat 표의 Stat Scalars는 `-x`, Base Regen Units는 `-`로 비어 있어, 이 조회만으로 임의 스탯 쿨다운 환산식을 확정할 수 없다. Super 194행에도 chunk gains 최대값이 `?%`로 남아 있다.
- Chunk Scalar는 쿨다운이나 지속시간에 곱하는 배율이 아니다. Game Mechanics 17행의 정의는 **정해진 비율의 Ability Energy 회수량**에 적용되는 배율이며, Super는 Chunk Modifiers를 받지 않는다고 적혀 있다.
- Base Duration은 해당 행의 기본/수동 에너지 소모 기준이다. 공격·이동·방어의 추가 소모, Sunspot/Aspect/Exotic은 구분해야 한다. Hammer of Sol 105행의 Phoenix Cradle/Loreley 연장 예시는 100% Sol Invictus buff uptime 가정이라고 명시되어 있어 기본 지속시간 표에 합치지 않았다. 해당 행 수치/서술의 독립적 게임 검증은 수행하지 않았다.
- Nova Bomb의 구현 변형이 Cataclysm인지 Vortex인지 아직 이 조사로 확정하지 않았다. 두 행을 제공하며, Vortex의 10s를 모든 Nova Bomb 공통값으로 쓰면 안 된다.
- Landing 22행의 PvP/PvE 범례와 실제 원본 span 색을 함께 확인했다. 이 표의 Suppression `10 [5]`는 PvE 10 / PvP 5. 기본 cooldown에 대괄호 분기가 없는 항목은 “분기 미표기”로만 취급하며, 모든 활동의 실효시간이 동일하다고 추가 검증한 것은 아니다.
- 작은 보라색 추가량은 조건부 수치다. Vortex Grenade 원문 `4` + 작은 보라색 `+1`은 Void 27행 Remnants 설명(기본 25% 연장)과 함께 읽었다. Charged 52행 `4.3+2.3`도 분리했다. `?`, `5?`, 미기재 지속시간을 추정값으로 대체하지 않았다.

조건 근거: [Landing r22 범례](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1038486120&range=B22:N22), [Landing r38 100 Stat 안내](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1038486120&range=B38:N38), [Game Mechanics r17 Chunk](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1800463143&range=B17:N17), [r180–190 Melee/Grenade](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1800463143&range=B180:N180), [r194 Super](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1800463143&range=B194:N194), [r196–199 Class](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1800463143&range=B196:N196), [Void r27 Remnants](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B27:N27), [Void r52 Charged](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit#gid=1907852650&range=B52:N52).

## HP·게임 환산은 원본값과 분리

Class Abilities 22/26행의 500 Construct HP, 43행의 회복 40 [35] HP/s, 15 Overshield HP는 **Destiny 원본 단위**다. 500 HP를 Minecraft 500 HP로 쓰거나 회복량을 그대로 연결한 값은 원본 검증값이 아니다. 이번 산출물은 Minecraft HP·피해·거리·tick 환산을 생성하지 않았다. 향후 초→tick을 적용할 경우 20 TPS 및 반올림 정책은 별도 구현 결정으로 남겨야 한다. 원본 HP가 필요하면 PvE/PvP, 적 등급, 적용 버프/스탯 조건을 붙여 별도 대조한다.

## 조회본 / provenance

`ddc/class-values-evidence.json`에 선택 행 전체 원문, 병합셀 좌표, 원본 링크, 조회시각, HTTP 상태, 바이트 수, SHA-256 및 읽은 repo 정책/캐시 파일 해시를 기록했다. 원본 HTML은 색상·작은 글씨·취소선 등을 보존하며, JSON plain text만으로 서식을 재해석하지 않는다. HTMLView의 표시값을 읽었으며 셀 수식·미표시 계산 선행 셀은 확보하지 않았다.

기존 docs162 정책을 읽었다. w75 cache와 capture 및 w188 조회 메타데이터는 출처/캐시 맥락용이고, 아래 수치의 직접 근거는 이번 원본 fetch다. 이전 캐시 전체가 최신화/검증되었다고 주장하지 않는다.

| 원본 저장 파일 | gid | HTTP / bytes | SHA-256 |
|---|---:|---:|---|
| `ddc/class-abilities.html` | 527596209 | 200 / 108248 | `3a33c932ee2b357d727c87d55488777c8afeb3c24a6810ce79c484e0e205246d` |
| `ddc/solar.html` | 1186062409 | 200 / 263029 | `a4304fe91d7ea5ebae256464483b169b004797fe0dcb98336c8fafe919bf730b` |
| `ddc/arc.html` | 618967225 | 200 / 225867 | `03c653dbbefa2ca6c12f66155c9f4c4a70a4f825b892af2e2219559fa1e5add0` |
| `ddc/void.html` | 1907852650 | 200 / 243621 | `88db7b9bac67513bd215fb6082c26ead4ca16203e5d0fc7e05ca5c1b8d5e7dc3` |
| `ddc/landing.html` | 1038486120 | 200 / 174889 | `deeb409e92a8a2ac5db1f6be8aca9c0bdfe26629a680b37c048cea709df7c079` |
| `ddc/game-mechanics.html` | 1800463143 | 200 / 485323 | `62af7cfc8acca0c7e8c087a0ee257af6003a931f67ea74434285efedffbbf873` |

범위: 요청에 따라 빠르게 확인 가능한 classic 능력 15행과 조건 행만 발췌했다. 누락된 능력·정확한 스탯별 실효 쿨다운·원게임 재측정은 미검증이다. 수치 테스트·빌드·게임 입력·코드 수정은 하지 않았다. Titan super.fire 미연결이라는 이전 관찰은 사용자 최신 확인에 의해 폐기하며, 본 조사 이슈에 포함하지 않는다.
