# W230 DDC 기본 수치 — 선행 전달

11종 모두 HTTP 200으로 새로 조회. 충전시간은 DDC Base Cooldown이며 스탯·처치·활동별 실제 충전시간을 의미하지 않는다. Chunk Scalar를 곱하지 않는다.
지속시간은 기본 무공격 상한/설치물 수명이며 발동 애니메이션 길이와 구분한다. DDC 피해·HP·미터를 Minecraft와 1:1 환산하지 않는다.

| ID | 기본 CD 초 / 20TPS tick | 기본 지속 초 / tick | 조건 | DDC 행 |
|---|---:|---:|---|---|
| `blade_barrage` | 455 / 9100 | 단발·후속 효과 별도 | instant two volleys; 14 knives baseline; Knock Em Down 20 knives; embed-to-detonation 0.5s | [solar 75](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1186062409&range=A75:O75) |
| `spectral_blades` | 556 / 11120 | 23.5 / 470 | 23.5s while invisible; passive drain +50% while visible; light removes invisibility, heavy grants invisibility; attack costs marked ? by source | [void 67](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1907852650&range=A67:O67) |
| `gathering_storm` | 500 / 10000 | 단발·후속 효과 별도 | persistent field: strike after 2s; field begins 1.2s after strike and lasts 8s; not an 8s roaming super | [arc 66](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=618967225&range=A66:O66) |
| `storms_edge` | 625 / 12500 | 미확정 | DDC base duration and energy per throw unknown; maximum 3 throws; do not invent source-backed duration | [arc 68](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=618967225&range=A68:O68) |
| `thundercrash` | 556 / 11120 | 4.5 / 90 | up to 4.5s flight; detonates on impact; aftershocks start +0.75s and last 4s | [arc 100](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=618967225&range=A100:O100) |
| `burning_maul` | 500 / 10000 | 25 / 500 | baseline 25s; Sol Invictus lowers passive drain 40%, source says 42s; light 4%, heavy 8% energy; light delay 0.67s; cyclone 4s | [solar 103](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1186062409&range=A103:O103) |
| `ward_of_dawn` | 455 / 9100 | 30 / 600 | persistent dome 30s; Super Stat up to 40s at 200; core pickup after 3s, twice per cast; projectile exceptions and construct/core health are separate mechanics | [void 100](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1907852650&range=A100:O100) |
| `well_of_radiance` | 455 / 9100 | 30 / 600 | persistent well 30s; Super Stat up to 40s at 200; leaving aura gives Radiant 8+4s; caster weapon damage counts as Super Ability Damage | [solar 139](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1186062409&range=A139:O139) |
| `chaos_reach` | 455 / 9100 | 4 / 80 | channel 4s; first 0.67s does not deal damage; ticks 0.13s; manual early cancel refund at most 30% | [arc 124](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=618967225&range=A124:O124) |
| `nova_warp` | 556 / 11120 | 24.5 / 490 | 24.5s base; hold fire 0.6s charge; light 5% and Dark Blink 3.5% energy; charge increases damage AND radius by 120% | [void 129](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=1907852650&range=A129:O129) |
| `fists_of_havoc` | 556 / 11120 | 25 / 500 | 25s base; light 6%, heavy 12% energy; cast slam has no aftershocks; >=1s directional slam adds hits | [arc 98](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/htmlview/sheet?headers=true&gid=618967225&range=A98:O98) |

## 원문과 조건

각 full row는 `ddc-values.json` exact_cells, 원본 HTML·해시·조회시각은 `ddc/`에 보존한다. 원문 `?`, 대괄호 PvP 수치, aspect/stat 조건은 확정 숫자로 치환하지 않는다.
