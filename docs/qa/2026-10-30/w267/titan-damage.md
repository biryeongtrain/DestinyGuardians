# W267 Titan PvP damage delta — 2026-10-30

## 범위 및 적용 계약

배타 쓰기 루트: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-mindbender_s_ambition_adept/w267-delta`.
메인 `/Users/qf/IdeaProjects/DestinyGuardians`은 읽기 전용으로 참조했다. stale worktree 루트 파일은 편집하지 않았다.

변경 파일은 아래 6개뿐이다.

- `src/main/java/kim/biryeong/destiny/ability/titan/TitanGrenade.java`
- `src/main/java/kim/biryeong/destiny/ability/titan/TitanMelee.java`
- `src/main/java/kim/biryeong/destiny/ability/titan/TitanSuper.java`
- `src/main/java/kim/biryeong/destiny/ability/titan/TitanExpandedSupers.java`
- `src/main/resources/destiny/abilities/w267-titan-pvp.json` (신규)
- `docs/qa/2026-10-30/w267/titan-damage.md` (본 문서)

JSON은 `ability.id().getPath() + "/" + contact`를 키로 하는 flat numeric map, 총 15개다. 값은 Minecraft HP가 아닌 raw Destiny PvP HP다.
공통 `AbilityDamage.pvp(ability, contact, target, local)`가 실제 타격 대상의 maxHealth / 230으로 플레이어만 환산한다. 몹은 기존 local 인수를 그대로 반환한다.
지연 타격은 이미 보관된 ability/Owner 또는 TitanMelee 인스턴스를 사용한다. 타격 시 현재 로드아웃으로 출처를 다시 결정하지 않는다.
수류탄/근접은 `WeaponAdrenalineJunkie.grenadeDamage` / `MeleeWeaponTraits.poweredDamage`보다 먼저 환산하고, 궁은 `Combat.damage(..., AmmoGeneration.SUPER)` 직전에 환산한다.
기존 local 수치, 모션, 범위, 타격 횟수/간격, 쿨다운, 애니메이션, LOS, 적 판정, once-hit 집합은 보존했다. 이 4파일의 기존 피해식에는 거리 falloff가 없다. 새 falloff/거리 배율은 추가하지 않았다.

## 출처와 20HP 환산

출처: [Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4), 로컬 스냅샷 `/private/tmp/destiny-w265/{Arc,Solar,Void}.csv`.
아래 행 번호는 multiline CSV를 `csv.reader`로 읽은 1-based 레코드 번호다. 대괄호는 PvP 수치이며 `[?]`를 확정 수치로 취급하지 않았다. 별도 HTTPS 재조회는 하지 않았다.
20HP 수치는 `raw / 11.5`, 보호막/회복/퍽/약화/저항 적용 전이다. 예상 타격 수는 모든 접촉이 유효하고 회복이 없는 경우다.

| JSON key | Raw PvP | 20HP 피해 | 근거 및 예상 타격 |
|---|---:|---:|---|
| titan/arc_grenade/detonation | 50 | 4.348 | Arc r34 Pulse Grenade 초기 `[50]` |
| titan/arc_grenade/pulse | 80 | 6.957 | Arc r34 후속 `[80]`; 초기+후속 3회=290 raw/25.217HP, 4번째 접촉에 처치 |
| titan/solar_grenade/explosion | 130 | 11.304 | Solar r31 Fusion Grenade `[130]`; 단독 한방 아님, 동일 폭발 2회 |
| titan/void_grenade/pulse | 37.5 | 3.261 | Void r36 Suppressor `[150]`를 기본 4회에 분배한 **local approximation**; 1회 시전 총13.043HP |
| titan/arc_melee/strike | 120 | 10.435 | Arc r58 Thunderclap 미충전 `[120]`; 2회 |
| titan/solar_melee/impact | 90 | 7.826 | Solar r61 Throwing Hammer 기본 `[90]`; 3회 |
| titan/void_melee/impact | 70 | 6.087 | Void r57 Shield Throw `[70]`; 4회 |
| titan/arc_super/light | 275 | 23.913 | Arc r60 `[?]`; **local approximation**, 일반 유저 1회 |
| titan/arc_super/slam | 350 | 30.435 | Arc r60 `[?]`; **local approximation**, 시전/착지 slam 공용, 일반 유저 1회 |
| titan/solar_super/impact | 300 | 26.087 | Solar r64 Hammer of Sol `[?]`; **local approximation**, 일반 유저 1회 |
| titan/void_super/impact | 300 | 26.087 | Void r59 Sentinel Shield throw `[?]`; **local approximation**, 일반 유저 1회 |
| titan/thundercrash/impact | 800 | 69.565 | Arc r61 impact/explosion `[?]`; **local approximation**, 한방 shutdown 타격 |
| titan/thundercrash/aftershock | 45 | 3.913 | Arc r61 aftershock `[?]`; **local approximation**, 1초마다 4회 합180 raw/15.652HP |
| titan/burning_maul/spin | 275 | 23.913 | Solar r63 light `[?]`; **local approximation**, 로컬 1접촉에 spin 묶음, 일반 유저 1회 |
| titan/burning_maul/wave | 350 | 30.435 | Solar r63 impact `[?]`, cyclone `[16]`; **local approximation**, 파동당 1접촉, 일반 유저 1회 |

기본 능력은 주무기 피해와 조합하도록 한방 미만이다. roaming 궁의 raw275/300/350은 53% 저항 대상에 각각 11.239/12.261/14.304HP, 58% 저항 대상에 10.043/10.957/12.783HP여서 이 조건에서는 모두 2회가 필요하다. 천둥충돌 raw800은 58% 저항 이후에도 29.217HP로 1회다. 더 강한 방어/추가 보호막에서는 달라진다. 이 계산은 실제 인게임 검증 결과가 아니다.

## 원작과 로컬 구현 차이 / local approximation

- Pulse Grenade: CSV는 초기50, 후속80, 간격0.7초다. 로컬은 기본 duration80 ticks, interval20 ticks이므로 최초+후속3회, 총290 raw다. 주기는 그대로 두고 접촉별 명시 PvP 값을 적용했다. CSV의 총량 표기530/690과 `5+2` 추가 펄스 설명도 단순 산술상 일치하지 않아 원작 총량 복제를 주장하지 않는다. 로컬 네 번째 접촉(정상 tick 기준 최초 이후3초) 처치가 목표다.
- Suppressor: 원작은 150 폭발 1회지만 로컬은 기본4초/1초 반복장이다. 150을 매 펄스마다 적용하지 않고 37.5×4로 총량을 맞췄다. 늦게 들어온 대상은 남은 펄스만 받는다. duration/pulse tuning을 별도로 바꾸면 횟수와 총량도 달라진다. 이를 동적으로 재분배하거나 타이밍을 바꾸지 않았다.
- Fusion: 기존 지연 폭발만130으로 연결. DDC x40(+20) scorch는 기존 TitanGrenade에 호출이 없어 본 변경의 피해 합계에 포함하지 않는다.
- Thunderclap: 현재 즉시 원뿔 타격에 충전 입력이 없으므로 미충전120을 사용했다. 완충240을 즉시 부여하지 않았다.
- Throwing Hammer: 현재 거리별 최대36% 증가/회수/10초 후60 폭발이 없으므로 기존 직접 접촉90만 적용했다. Shield Throw의 ricochet/overshield도 새로 만들지 않았다.
- Fists of Havoc: 원작 light/heavy/aftershocks의 PvP가 `[?]`; 현재 light와 시전/공중착지 slam을 275/350으로 구분했다. 현재 구현에 없는 보너스 타격/aftershock를 추가하지 않았다.
- Hammer of Sol: 현재 단일 투사체의 주변 폭발만 존재하므로 raw300으로 일반 유저 1회/보호궁 추가타격을 맞췄다. 별도 shrapnel을 만들어 총량을 중첩하지 않았다.
- Sentinel Shield: 현재 주공격은 방패 투사체 AoE이다. raw300은 이 접촉의 근사값이며 원작 grounded combo/block barrier damage의 확정값이 아니다.
- Thundercrash: 현재 impact 한 번이 직접 충돌+폭발을 대표하므로 raw800으로 묶었다. 근접 비행 스침 피해는 기존 독립 contact가 없어 추가하지 않았다. 후속 aftershock는 impact 전체량이 아니라45씩4회이며 기존0.75초 시작 지연/1초 간격/4초 길이를 보존했다.
- Burning Maul: 원작 light4 hits를 로컬 spin1 contact로 표현하므로 묶음275. heavy는 원작 impact+4초 cyclone(16/0.2초)을 로컬 once-hit wave350으로 압축한 근사다. 16을 wave의 매 tick마다 넣거나350을 반복 적용하지 않는다. 기존 hit UUID 집합이 같은 wave의 재타격을 막는다. 지속장/추적/Scorch를 추가하지 않았다.
- Ward of Dawn에는 원래 공격 contact가 없으므로 JSON 피해 항목이나 피해 호출을 추가하지 않았다. Ward의 구조물 내구도 소모는 공격 피해 환산 대상이 아니다.

## 공용 처리 및 통합 잔여사항

- `AbilityDamage.java`, `Statuses.java`, Combat, 퍽 wrappers 및 master 파일은 수정하지 않았다. helper가 hunter/titan/warlock JSON을 모두 요구하므로 master의 전체 배치와 함께 통합해야 한다.
- 조회 시점의 공용 `Statuses`에는 플레이어 scorch 6.5 raw / 11ticks, 비치사 budget 경로가 이미 보인다. master 동시 작업의 읽기 전용 스냅샷이다. stack/ignition 및 개별 능력 출처별 값은 여전히 별도 검토 대상이며 본 delta에서 수정하지 않는다.
- Titan Fusion 자체에는 `Statuses.scorch` 호출이 없다. Burning Maul cyclone/scorch도 구현되어 있지 않다. PvE 동작 보존 범위 때문에 새로 연결하지 않았다.
- Hunter scorch 누락 여부는 이 배타 Titan 범위에서 검수하지 않았다. master/Hunter 담당자가 실제 호출자와 공용 tick의 출처 전달을 확인해야 한다.
- 기존 Suppressor는 slowness/weakness와 Mob target 해제로 구현되며, DDC의 플레이어 능력 사용 억제 전체를 구현한 것은 아니다. 수치 외 상태 동작은 보존했다.
- 조회한 `WeaponAdrenalineJunkie.grenadeKilled`의 기존 Mob-only 제한도 보존했다. PvP 처치에서 해당 퍽 보상이 필요한지는 master의 공용 경로 검토 대상이다.

## 정적 검토

네 Java의 모든 기존 damage 호출을 확인했다: grenade wrapper 1곳, powered melee wrapper 2곳, 기본 super Combat 1곳, expanded super 공용 Combat 1곳(impact/aftershock/spin/wave 4 caller). 총 15개 ability/contact 조합이 JSON에 대응한다.
기본 super의 ARC light/slam과 SOLAR/VOID impact 분기를 구분했고, grenade 최초/후속 판정은 기존 fired=true 설정 전에 계산한다. 이후 타격 횟수, loop, cooldown, lifetime은 변경하지 않았다.
메인 대비 diff에서 기존 local 인수와 비피해 동작 보존을 확인했고 JSON 파싱 및 유한한 비음수 값/키 연결을 정적으로 검토했다. 빌드, 서버, Vision, CU, 커밋, 추가 agent, 개별 수치 테스트 신설/실행, 전수 gate는 수행하지 않았다.

## 통합 기준 SHA-256

시작 시 네 delta 파일은 메인과 byte-equal였고 link count는 각각1이었다. 아래는 편집 전 메인/복사본 기준 해시다. master는 통합 직전 메인 drift를 확인해야 한다.

| 파일 | 편집 전 SHA-256 |
|---|---|
| TitanGrenade.java | 660ff029041f6ae8e9eaf915ea77f3a4f99b814b34d8df79a1da37357989ef43 |
| TitanMelee.java | 9b2aac90bf3394b82acbfea14400c751155ec8fab1146093424e0d288d06cc60 |
| TitanSuper.java | 96e8e069bf53de30fb941021a99b943c5d1d37debc5740d3f62fff57922f9471 |
| TitanExpandedSupers.java | bd6c2e3acec57b7318e575b61501d2cfc3a5144af4213e2499caa92141916c8a |
