# Guardian Rises — Fallen 오디오 (W300 r6)

상태: 파일·키·디코딩·게이트 로직은 오프라인 검증. **청취·인게임 미검증** — master가 Vision/청취로 확인한다.

## 출처

`/Users/qf/Downloads/Rising-Guardian-Fallen-AV-2026-11-01/Rising-Guardian-Fallen-AV-2026-11-01` (읽기 전용). Steam 빌드 25932352,
`cosmo.mission_launchpad / 80C87171`, Charm 3.5.0 추출(README). `sound-events.csv`의 이벤트 → WEM, `sound-media.csv`의 OGG.

- **linked**: 액터 클립·시퀀스·컴포넌트에서 추적된 이벤트. **name-hash**: Wwise 뱅크 이름의 FNV-1 해시만 일치(임무에서 실제 재생되는지
  미확인). Fallen 언어 대사(`fallen_<unit>_*`)는 전부 name-hash다 — 대사 뱅크라 클립에 직접 연결되지 않는다.
- 변형 선택: 이벤트당 최대 8개. 청취 없이 고르므로 "깨끗한" 기준은 **풀의 중앙값 길이에 가까운 변형**(긴 꼬리/이상치 제외)으로 대체했다.
  레이어(근거리/원거리 꼬리 등)와 변형이 섞여 있을 수 있다(README). 순서 의미 없음, 클라이언트가 무작위 선택.
- 변환: 모노 원본은 바이트 그대로 복사. 스테레오/4채널(무기·워커 대부분)은 **모노로 다운믹스**(libvorbis q4, 48 kHz) —
  Minecraft는 모노 사운드만 위치/거리 감쇠를 적용하므로 필수. 길이 보존(최대 차 0.027 s), 343개 전부 오류 없이 디코딩.
- 같은 WEM 풀을 공유하는 이벤트: `pinned`=`under_fire`(dreg), `surprise`=`target_sighted`(dreg/vandal/captain),
  `fallen_vandal_kill`=`fallen_vandal_dive_evade`, `wire_rifle_thwack_lethal`=`wire_rifle_thwack`,
  `fallen_sword_generic_telegraph`=`vandal_sword_melee_any`, `fallen_captain_shield_pop`=`fallen_captain_under_fire`.
  중복 파일을 만들지 않고 한 이벤트를 재사용(텔레그래프는 sounds.json 별칭 키).
- 산출: 이벤트 56개(별칭 1), 파일 343개, **6.77 MB** (상한 25 MB).
  재현: `w300-evidence/fallen/r6/curate.py`, 파일별 원본/출력 sha256: `w300-evidence/fallen/r6/provenance.json`.

## 이벤트 ↔ 훅

| 키(`guardian_rises.fallen.*`) | D2 태그 | 그룹 | 근거 | 풀 | 사용 | KB | WEM | 훅 |
|---|---|---|---|---:|---:|---:|---|---|
| `shock_pistol_fire` | `80D4856D` | weapons | linked | 13 | 8 | 173 | 80D61C1D, 80D61C1F, 80D61C21, 80D61C23, 80D61C25, 80D61C27, 80D61C28, 80D61C29 | Dreg/Shank bolt fire |
| `wire_rifle_fire` | `80D484B7` | weapons | linked | 10 | 8 | 219 | 80D61C79, 80D61C7A, 80D61C7D, 80D61C7E, 80D61C7F, 80D61C80, 80D61C81, 80D61C82 | Vandal wire-rifle burst fire |
| `shrapnel_launcher_fire` | `80D48A97` | weapons | linked | 10 | 8 | 203 | 80D68583, 80D68584, 80D68586, 80D68587, 80D68588, 80D68589, 80D6858A, 80D6858C | Captain shock blast fire (slow splash orb) |
| `flyby_fallen_generic` | `80D48B71` | weapons | linked | 13 | 8 | 65 | 80D67FA0, 80D67FA2, 80D67FA3, 80D67FA4, 80D67FA5, 80D67FA9, 80D67FAA, 80D67FAB | infantry/shank bolt near-miss at the player |
| `fallen_generic_thwack` | `80D48A8B` | linked | linked | 8 | 8 | 95 | 80D61CF8, 80D61CF9, 80D61CFA, 80D61CFB, 80D61CFC, 80D61CFD, 80D61CFE, 80D61CFF | Dreg/Shank bolt or melee hits the player |
| `fallen_generic_thwack_lethal` | `80D48A8E` | linked | linked | 9 | 8 | 106 | 80D61D00, 80D61D01, 80D61D02, 80D61D03, 80D61D04, 80D61D05, 80D61D06, 80D61D07 | same, killing hit |
| `wire_rifle_thwack` | `80D48AC8` | weapons | linked | 9 | 8 | 97 | 80D6864D, 80D6864E, 80D6864F, 80D68650, 80D68651, 80D68652, 80D68653, 80D68654 | Vandal bolt hits the player (lethal shares the WEM pool) |
| `shrapnel_launcher_thwack` | `80D48F2E` | weapons | linked | 8 | 8 | 83 | 80D68644, 80D68645, 80D68646, 80D68647, 80D68648, 80D68649, 80D6864A, 80D6864B | Captain blast hits the player |
| `shrapnel_launcher_thwack_lethal` | `80D48F2C` | weapons | linked | 9 | 8 | 92 | 80D68655, 80D68656, 80D68658, 80D68659, 80D6865A, 80D6865B, 80D6865C, 80D6865D | same, killing hit |
| `dreg_melee_swing` | `80D48ACB` | dreg | linked | 4 | 4 | 52 | 80D61CCC, 80D61CCD, 80D61CCE, 80D61CCF | Dreg shock-blade swing (layer 1) |
| `shock_blade_melee_swish` | `80D48B89` | linked | linked | 6 | 6 | 89 | 80D62F77, 80D62F78, 80D62F79, 80D62F7A, 80D62F7B, 80D62F7C | Dreg shock-blade swing (layer 2) |
| `vandal_sword_melee_any` | `80D48D58` | vandal | linked | 7 | 7 | 71 | 80D62F62, 80D62F63, 80D62F64, 80D62F65, 80D62F66, 80D62F67, 80D62F68 | Vandal melee swing |
| `fallen_sword_generic_telegraph` | `80D48B74` | linked | linked | 7 | 7 | 0 | alias → `vandal_sword_melee_any` (same WEM pool) | melee wind-up telegraph (identical pool to vandal_sword_melee_any) |
| `fallen_captain_melee_attack` | `80A64CA3` | captain | name-hash | 6 | 6 | 91 | 80B6338F, 80B63391, 80B63393, 80B63394, 80B63395, 80B63397 | Captain melee swing grunt |
| `fallen_dreg_target_sighted` | `80A64D2D` | dreg | name-hash | 4 | 4 | 83 | 80B63244, 80B63245, 80B63246, 80B63247 | Dreg first sight bark (surprise shares the pool) |
| `fallen_dreg_taunt` | `80A64D42` | dreg | name-hash | 31 | 8 | 180 | 80B63227, 80B6322D, 80B63230, 80B6323B, 80B632EF, 80B632F5, 80B632FB, 80B632FC | Dreg taunt clip bark |
| `fallen_dreg_under_fire` | `80A64D27` | dreg | name-hash | 13 | 8 | 133 | 80B63216, 80B63217, 80B63219, 80B6321A, 80B6321C, 80B6321F, 80B63220, 80B63221 | Dreg hurt bark (pinned shares the pool) |
| `fallen_dreg_dive_evade` | `80A64D4B` | dreg | name-hash | 20 | 8 | 87 | 80B6328D, 80B63294, 80B63336, 80B63338, 80B6333F, 80B63341, 80B63343, 80B63345 | Dreg evade bark |
| `fallen_dreg_death` | `80A64D86` | dreg | name-hash | 7 | 7 | 129 | 80B63384, 80B63385, 80B63386, 80B63387, 80B63388, 80B63389, 80B6338A | Dreg death cry |
| `fallen_dreg_kill` | `80A64D60` | dreg | name-hash | 8 | 8 | 197 | 80B6334F, 80B63350, 80B63351, 80B63352, 80B63353, 80B63354, 80B63355, 80B63356 | Dreg bark when its damage downs a Guardian |
| `fallen_vandal_target_sighted` | `80A64F2B` | vandal | name-hash | 5 | 5 | 127 | 80B63517, 80B63518, 80B63519, 80B6351A, 80B6351B | Vandal first sight bark |
| `fallen_vandal_under_fire` | `80A64F28` | vandal | name-hash | 18 | 8 | 90 | 80B63506, 80B63507, 80B63509, 80B6350C, 80B6350D, 80B63511, 80B63513, 80B63516 | Vandal hurt bark |
| `fallen_vandal_dive_evade` | `80A64F1C` | vandal | name-hash | 9 | 8 | 176 | 80B634A9, 80B634AA, 80B634AB, 80B634AC, 80B634AD, 80B634AE, 80B634AF, 80B634B0 | Vandal blink bark (kill shares the pool) |
| `fallen_vandal_death` | `80A64F22` | vandal | name-hash | 7 | 7 | 123 | 80B634D4, 80B634D5, 80B634D6, 80B634D7, 80B634D8, 80B634D9, 80B634DA | Vandal death cry |
| `fallen_captain_target_sighted` | `80A64C9B` | captain | name-hash | 4 | 4 | 74 | 80B633EF, 80B633F0, 80B633F1, 80B633F2 | Captain first sight bark |
| `fallen_captain_under_fire` | `80A64C8D` | captain | name-hash | 10 | 8 | 106 | 80B6338F, 80B63391, 80B63392, 80B63393, 80B63394, 80B63395, 80B63396, 80B63398 | Captain hurt / shield-pop bark |
| `fallen_captain_death` | `80A64C90` | captain | name-hash | 5 | 5 | 96 | 80B63399, 80B6339A, 80B6339B, 80B6339C, 80B6339D | Captain death cry |
| `fallen_captain_kill` | `80A64CB9` | captain | name-hash | 15 | 8 | 263 | 80B6342B, 80B6342C, 80B6342E, 80B6342F, 80B63432, 80B63435, 80B63437, 80B63438 | Captain bark when its damage downs a Guardian |
| `fallen_shank_target_sighted` | `80A64D7D` | shank | name-hash | 4 | 4 | 191 | 80B6338B, 80B6338C, 80B6338D, 80B6338E | Shank first sight chirp |
| `fallen_shank_pain` | `80A64D66` | shank | name-hash | 8 | 8 | 245 | 80B63347, 80B63348, 80B63349, 80B6334A, 80B6334B, 80B6334C, 80B6334D, 80B6334E | Shank hurt chirp |
| `fallen_shank_death` | `80A64D81` | shank | name-hash | 10 | 8 | 167 | 80B6337B, 80B6337C, 80B6337D, 80B6337E, 80B6337F, 80B63380, 80B63382, 80B63383 | Shank death chirp |
| `fallen_shank_shoot` | `80A64D70` | shank | name-hash | 5 | 5 | 131 | 80B6336A, 80B6336B, 80B6336C, 80B6336D, 80B6336E | Shank attack chirp |
| `shank_explode` | `80D48572` | shank | name-hash | 8 | 8 | 333 | 80D61C32, 80D61C33, 80D61C34, 80D61C35, 80D61C36, 80D61C37, 80D61C38, 80D61C39 | Shank death explosion |
| `dreg_evade_spin` | `80D48ACE` | dreg | linked | 5 | 5 | 113 | 80D61CB0, 80D61CB1, 80D61CB2, 80D61CB3, 80D61CB4 | Dreg evade roll foley |
| `dreg_shortmove` | `80D48ADA` | dreg | linked | 8 | 8 | 108 | 80D61CBA, 80D61CBB, 80D61CBC, 80D61CBD, 80D61CBE, 80D61CBF, 80D61CC0, 80D61CC1 | Dreg evade step foley |
| `fallen_dreg_bodyfall` | `80D48E17` | dreg | name-hash | 5 | 5 | 94 | 80D67FAD, 80D67FAE, 80D67FAF, 80D67FB0, 80D67FB1 | Dreg/Shank-less infantry body fall |
| `fallen_captain_bodyfall` | `80D4891E` | captain | name-hash | 5 | 5 | 78 | 80D62F4C, 80D62F4D, 80D62F4E, 80D62F4F, 80D62F50 | Captain body fall |
| `fallen_base_death_mvmt` | `80D48E49` | linked | linked | 5 | 5 | 115 | 80D62F14, 80D62F15, 80D62F16, 80D62F17, 80D62F18 | Vandal death movement / fall |
| `teleport_begin` | `80D48DF9` | linked | linked | 3 | 3 | 78 | 80D6863C, 80D6863D, 80D6863E | Vandal blink out |
| `teleport_end` | `80D48DF6` | linked | linked | 5 | 5 | 107 | 80D6863F, 80D68640, 80D68641, 80D68642, 80D68643 | Vandal blink in |
| `generic_dissolve` | `80A61C32` | linked | linked | 3 | 3 | 80 | 80D63686, 80D63687, 80D63688 | end of the ether death dissolve |
| `spidertank_cannon_fire` | `80D4CA32` | walker | linked | 2 | 2 | 39 | 80D663D9, 80D663DA | Walker main cannon fire |
| `spidertank_cannon_explo` | `80D4C9A5` | walker | linked | 18 | 8 | 283 | 80D68D9B, 80D68D9D, 80D68DA1, 80D69691, 80D69692, 80D69695, 80D69697, 80D69698 | Walker cannon shell explosion |
| `spidertank_nose_fire` | `80D49320` | walker | linked | 13 | 8 | 41 | 80D66329, 80D6632A, 80D6632B, 80D6632C, 80D66330, 80D66331, 80D66332, 80D66333 | Walker anti-personnel bolt fire |
| `spidertank_nose_barrel_open` | `80D4931D` | walker | name-hash | 1 | 1 | 20 | 80D66327 | Walker anti-personnel telegraph |
| `spidertank_nose_thwack` | `80D4847A` | walker | linked | 9 | 8 | 99 | 80D61E86, 80D61E88, 80D61E89, 80D61E8A, 80D61E8B, 80D61E8C, 80D61E8D, 80D61E8E | Walker AP bolt hits the player |
| `spidertank_nose_thwack_lethal` | `80D4847D` | walker | linked | 8 | 8 | 98 | 80D61E8F, 80D61E90, 80D61E91, 80D61E92, 80D61E93, 80D61E94, 80D61E95, 80D61E96 | same, killing hit |
| `flyby_fallen_spidertank_turret` | `80D48477` | walker | linked | 20 | 8 | 117 | 80D61E72, 80D61E73, 80D61E74, 80D61E77, 80D61E7C, 80D61E7D, 80D61E83, 80D61E84 | Walker AP bolt near-miss |
| `spidertank_step_front` | `80D4C9DF` | walker | name-hash | 10 | 8 | 126 | 80D66365, 80D66366, 80D66367, 80D66368, 80D66369, 80D6636A, 80D6636B, 80D6636D | Walker footstep |
| `spidertank_step_rumble` | `80D4CA0B` | walker | linked | 6 | 6 | 126 | 80D66397, 80D66398, 80D66399, 80D6639A, 80D6639B, 80D6639C | Walker footstep low rumble (every other step) |
| `spidertank_leg_explo` | `80D4CA1A` | walker | name-hash | 11 | 8 | 208 | 80D663AB, 80D663AE, 80D663AF, 80D663B0, 80D663B1, 80D663B2, 80D663B3, 80D663B4 | Walker leg armour breaks / death chain pops |
| `spidertank_expose_weakspot_exit` | `80D4CA17` | walker | linked | 4 | 4 | 92 | 80D663A7, 80D663A8, 80D663A9, 80D663AA | Walker weakpoint closes (RECOVER) |
| `spidertank_voice_intimidate` | `80D4CA08` | walker | linked | 9 | 8 | 280 | 80D6638E, 80D66390, 80D66391, 80D66392, 80D66393, 80D66394, 80D66395, 80D66396 | Walker roar: fight start and after recovery |
| `spidertank_explode_1` | `80D4C9FB` | walker | linked | 1 | 1 | 140 | 80D6638B | Walker destroyed |
| `spidertank_land` | `80D4CA01` | walker | linked | 1 | 1 | 80 | 80D6638D | Walker arrival |
| `spider_tank_impact` | `80D4C9E2` | linked | linked | 1 | 1 | 21 | 80D6636F | shots deflecting off Walker armour |
| `skiff_flyover` | `80D56F80` | skiff | name-hash | 6 | 6 | 474 | 80D78017, 80D78018, 80D78019, 80D7801A, 80D7801B, 80D7801C | Skiff arrives over a reinforcement wave (r7, stream) |
| `skiff_enemy_spawner` | `80D48441` | skiff | linked | 1 | 1 | 35 | 80D67DE1 | Skiff drops/tractors the wave riders (r7) |

## 재생 규칙 (`FallenSounds`)

- 위치형 `HOSTILE` 패킷(고정 감쇠 거리 이벤트, `Holder.direct`) — 범위 내 플레이어에게만 전송.
  범위: 총성 48 m(생크 폭발 포함), 바크 24 m, 근접 24 m, 폴리 20 m, 피격(thwack) 16 m, 근접 통과(flyby) 12 m, 워커·스키프 64 m.
- 피치 변화: 카테고리별 ±4–8 %. 생크 사격은 쇼크 피스톨을 1.15배 피치(README: 생크 시퀀스 80CEA1DB가 shock_pistol_fire 사용).
- 바크 예산(`BarkGate`, 순수·테스트): 같은 몹 50틱(2.5 s)에 1회, 같은 몹·같은 이벤트 140틱, **24 m 이내 20틱(1 s)당 최대 2회**.
  사망 외침은 우선(몹 쿨다운 무시, 예산 +1). 넘친 바크는 버림(큐 없음).
- flyby: 볼트 선분이 플레이어 눈에서 2.5 m 안을 지나갔는데 맞지 않았을 때 그 플레이어에게만, 볼트당 1회.
- thwack: 실제 피해가 들어간 경우 피해자 위치, 쓰러뜨렸으면 lethal 변형 + 공격자 kill 바크(우선).
- 폴백: sounds.json에 키가 없으면 기존 바닐라 소리(있는 경우)를 재생. 몹의 바닐라 hurt/death 소리는 D2 키가 있을 때 꺼진다.

## 바닐라로 남긴 것 (대응 D2 이벤트 없음/부적합)

- 원거리 공격 충전 텔레그래프(BEACON_POWER_SELECT): 추출에 와이어 라이플/쇼크 블라스트 충전음 없음. 가독성 신호라 유지.
- 캡틴 구체 폭발(FIREWORK_ROCKET_LARGE_BLAST): 파편 발사기 폭발 이벤트 없음(thwack만 있음).
- 보호막 피격/파괴/재생(AMETHYST/BEACON): `fallen_captain_shield_pop`은 under_fire 대사 풀과 동일해 효과음이 아님.
- 워커: 다리 장갑 피격 틱(IRON_GOLEM_HURT), 약점 노출(BEACON_ACTIVATE), 노출 종료 경고(NOTE_BLOCK_BIT), 주포 충전(WARDEN_SONIC_CHARGE).
  `spidertank_emp_charge`(9 s)는 1.5 s 충전에 맞지 않고, EMP 공격은 구현돼 있지 않아 미사용.
- 미사용 후보: `shock_rifle_fire`(캡틴이 구체 발사기 역할을 맡아 대신 shrapnel_launcher 사용 — 원작 장착 선택 미확정),
  `spidertank_emp_*`, `spidertank_voice_emp`, `throw_grenade`(수류탄 없음), 캡틴 evade(캡틴 회피 없음).
- 스키프(r7): `skiff_flyover`·`skiff_enemy_spawner`는 위 표에 추가(스테레오→모노 다운믹스 q4, 64 m, `Cat.SKIFF` 피치 ±3 %).
  `skiff_flyover`는 6.8–13.8 s라 `stream: true`. `skiff_manuever`(80A61BAD)는 추출에 WEM이 0개라 **넣을 수 없다**.
  `skiff_turret_fire`/`skiff_turret_explo`는 스키프 포격을 구현하지 않아 미사용. 큐레이션: `w300-evidence/fallen/r7/curate_skiff.py`.

## 불확실

- name-hash 이벤트(대사 전체, `spidertank_step_front`, `spidertank_leg_explo`, `spidertank_nose_barrel_open`, `shank_explode`, bodyfall)는
  임무 재생 여부가 증명되지 않았다. 이름이 일치하는 뱅크 후보다.
- 변형/레이어 구분 없이 중앙값 길이로 골랐으므로 꼬리만 있는 레이어가 섞였을 수 있다 — 청취 후 교체 필요.
- 워커 `spidertank_explode_1`(16.8 s), `spidertank_land`(9.2 s)는 길다. 최초 1회만 재생.
- `skiff_flyover`는 name-hash 후보(임무 재생 미증명)이며 원작이 루프/거리 레이어인지 불명 — 접근 1회 재생으로 썼다. 청취 확인 필요.
