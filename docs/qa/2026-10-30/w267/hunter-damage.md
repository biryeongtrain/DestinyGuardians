# W267 Hunter PvP ability damage

2026-10-30. 배타 delta에서만 작성. main은 읽기 전용이며 stale worktree 루트는 편집하지 않았다.

## 변경 파일

- `src/main/java/kim/biryeong/destiny/ability/hunter/HunterGrenade.java`
- `src/main/java/kim/biryeong/destiny/ability/hunter/HunterMelee.java`
- `src/main/java/kim/biryeong/destiny/ability/hunter/HunterSuper.java`
- `src/main/java/kim/biryeong/destiny/ability/hunter/HunterExpandedSupers.java`
- `src/main/resources/destiny/abilities/w267-hunter-pvp.json` (신규)
- `docs/qa/2026-10-30/w267/hunter-damage.md` (이 문서)

## 적용 계약

JSON은 `ability.id().getPath()/contact -> raw Destiny HP`인 flat numeric map, 총 16개 키다. 공용 `AbilityDamage.pvp(ability, contact, target, local)`를 실제 대상별 피해 직전에 호출한다. 플레이어는 `raw * target.maxHealth / 230`, 몹은 기존 local 그대로다. 수류탄은 `WeaponAdrenalineJunkie.grenadeDamage`, 근접은 `MeleeWeaponTraits.poweredDamage`에 들어가기 전에 환산한다. 궁극기는 `Combat.damage` 직전에 환산하며 기존 SUPER source 분류를 유지한다.

지연 피해는 Hunter ability 인스턴스 또는 Expanded의 `lease.ability`를 사용한다. 현재 장착 능력을 다시 조회하지 않는다. Golden Gun의 `hitscan`만 같은 인스턴스의 ID를 사용하도록 static을 제거했다. main 소스/테스트 검색에서 호출자는 같은 클래스의 GoldenGun 하나였다. Expanded의 damage/blast helper는 contact를 명시적으로 전달한다.

기존 param/value의 PvE 값·클램프·범위·주기·타격 횟수·모션·쿨다운·애니메이션·scorch_ticks는 유지한다. 이 4개 파일의 피해 경로에는 기존 거리 감쇠식이 없다. 거리 감쇠나 신규 타격을 추가하지 않았다. 원작의 중심 피해/정밀 피해/다단 타격을 현재 코드가 구분하지 않는 부분은 아래에 명시한다.

## 출처 및 contact별 값

출처: [Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4), 제공된 `/private/tmp/destiny-w265/{Arc,Solar,Void}.csv`를 직접 읽었다. 아래 번호는 **헤더 포함 1-based CSV record 번호**이며 실제 Google Sheet 행 번호가 아니다. 능력명은 B열, 설명은 D열이다. 이번 작업에서 HTTPS 재조회는 하지 않았다.

모든 MC HP는 최대 체력 20, 퍽·약화·궁극기 저항·방어·회복 전 원시값이다. 타격 횟수는 단순 누적 기준이며 쿨다운을 건너뛴 실제 DPS 주장이나 인게임 검증 결과가 아니다.

| JSON key (hunter/ 생략) | D2 HP/contact | 20HP 환산 | 근거 / 현재 구현 대응 |
| --- | ---: | ---: | --- |
| arc_flashbang/explosion | 120 | 10.435 | Arc record 29 Flashbang `[120]`. 원작 감쇠는 현재 코드에 없음. |
| solar_incendiary/explosion | 130 | 11.304 | Solar record 35 Incendiary `[130]` 기본 폭발. 1m 이내 `[173]` 별도 보너스는 현재 접촉 구분이 없어 적용하지 않음. scorch 제외. |
| void_vortex/pulse | 38 | 3.304 | **local approximation**. Void record 39 Vortex `[25]` impact + `[20]` × 12 field = 265. 현재 별도 impact 없이 age 0,10,...,60의 7회에 38씩 분배하여 합계 266. 전체 265를 매회 넣지 않음. |
| arc_combination_blow/strike | 116 | 10.087 | **local approximation**. Arc record 41은 stack별 `[23%/51.3%/86%]`만 있고 기본 피해가 없음. 현재 stack 없는 단일 접촉을 2타 처치용 116으로 추정. DDC 확정 기본 피해로 주장하지 않음. |
| solar_knife/knife | 114 | 9.913 | **local approximation**. Solar record 45 Knife Trick body `[38]` × 3 = 114를 현재 단발에 통합. 정밀 합계 `[147]`을 쓰지 않음. 단발 경량 칼 body `[100]`(record 46)과도 다른, scorch를 주는 현재 혼합 구현의 합산 대응. |
| arc_staff/strike | 300 | 26.087 | **local approximation**. Arc record 44 light 피해 `[?]`. 기본 유저 1타 / 저항궁 추가타 목표의 단일 휘두르기. 원작 heavy/palm 콤보를 추가하지 않음. |
| golden_gun/shot | 426 | 37.043 | Solar record 52 Marksman body `[426]`. 현재 3발이므로 Marksman 대응; headshot 2배/Line'Em Up을 추가하지 않음. |
| shadowshot/impact | 300 | 26.087 | **local approximation**. Void record 47 Deadfall impact `[?]`. 기존 착탄 범위 피해 한 번을 300으로 대응. 원작 직격과 주변 피해 구분, tether 공유 피해는 새로 만들지 않음. |
| blade_barrage/impact | 20 | 1.739 | **local approximation**. Solar record 50 impact `[not much?]`; 작은 직격. |
| blade_barrage/explosion | 240 | 20.870 | **local approximation**. 같은 record의 explosion `[generally dead?]`, 합계 `[death]`는 숫자가 아님. 칼 1개의 지연 폭발 240으로 근사. 기존 2×7발 유지; 궁 전체 피해를 칼마다 반복하지 않음. |
| spectral_blades/light | 300 | 26.087 | **local approximation**. Void record 46 light `[?]`. 기본 유저 1타, 보호궁 2타 수준. |
| spectral_blades/heavy | 400 | 34.783 | **local approximation**. 같은 record heavy `[?]`. light와 구분하며 기존 PvE 18과 모션 유지. |
| gathering_storm/impact | 300 | 26.087 | Arc record 45 direct `[300]`, 별도 폭발 `[?]`. 수치는 확정 직격값이나 기존 단일 blast 전체에 대응하는 것은 **local approximation**. 별도 direct/splash 피해를 중복 추가하지 않음. |
| gathering_storm/lightning | 500 | 43.478 | Arc record 45 lightning `[500]`, 현재 기본 40tick 지연(2초)과 대응. |
| gathering_storm/pulse | 60 | 5.217 | Arc record 45 field `[60]`/0.7초. 현재 기본 14tick 주기와 일치. impact/500 lightning을 펄스마다 반복하지 않음. |
| storms_edge/whirl | 300 | 26.087 | **local approximation**. Arc record 46 whirl `[300?]`를 임시 300으로 채택. `?`는 미확정으로 유지. 현재 순간이동 후 1회 휘두르기에 대응, 원작 칼 impact/splash/두 타격을 추가하지 않음. |

## 대표 처치 횟수 및 scorch 합산

- 섬광은 10.435HP로 기본 유저 약 2타, 소이는 직접 11.304HP로 2타에 해당한다. 단독 사용 후 주무기로 마무리할 수 있는 수준이다.
- 연속 타격은 10.087HP로 2타다. 칼 투척은 직접 9.913HP로 직접 피해만 계산하면 3타이며, 두 번의 칼 사이에 scorch 1회 이상이면 2타 분량으로 충분하다.
- 소용돌이는 기본 60tick 수명에서 7회 × 3.304 = 23.130HP. 전부 머물면 7번째 펄스에 기본 유저 처치 가능하다. 첫 펄스부터 마지막까지 60tick(3초); 원작 0.267초/12회/독립 impact와 시간 분포는 다르다. 기간 override는 기존 횟수를 바꾸므로 합계도 달라진다.
- 황금 총은 body 37.043HP로 기본 유저 1발. 상대 Arc Staff의 53% DR 예시에서는 17.410HP이므로 2발이다.
- Arc Staff, Spectral light, Storm's Edge는 26.087HP로 기본 유저 1타. 53% DR 상대 12.261HP, 58% DR 상대 10.957HP이므로 2타다. Spectral heavy는 각각 16.348 / 14.609HP로 여전히 2타다. 방어궁 DR은 기존 공용 경로를 따른다.
- Blade Barrage 칼 하나는 직격+폭발 22.609HP, 폭발만도 20.870HP로 기본 유저 1개 적중에 처치 가능. 53% DR 상대 직격+폭발은 10.626HP로 2개 분량; 58% DR 상대 9.496HP로 3개 분량이다. 실제 여러 칼이 동시에 맞는 분포는 기존 코드 그대로다.
- Gathering Storm은 impact 26.087HP, 2초 후 lightning 43.478HP, field 5.217HP/0.7초. field만 맞는 기본 유저는 4회(첫 pulse 이후 2.1초), 기본 8초 field는 12회 최대 62.609HP다. 53% DR 상대 lightning은 20.435HP로 단독 처치 가능하다.

Master의 후속 공용 scorch 작업을 전제로 후속 피해를 별도 계산한다: 대표 50stack 근사 6.5 D2HP/11tick = **0.5652 MC HP/0.55초**, 바닐라 불 중복 없음, 최소 0.1HP를 남기는 nonlethal, Combat source 귀속. 이는 master가 이 대화에서 알린 통합 예정 계약이며 이 delta에서 구현·검증한 기능이 아니다.

- 소이 `scorch_ticks=100` 기본값 유지: 타이머 위상에 따라 대략 8~10회(9회 대표)로 약 5.09HP 추가. 대표 합계 약 **16.39HP**, 회복 없는 대상 잔여 약 3.61HP. 가장 가까운 거리도 현재 기본 폭발 130 기준이다.
- 칼 `scorch_ticks=80` 기본값 유지: 대략 7~8회(7회 대표)로 약 3.96HP 추가. 대표 합계 약 **13.87HP**, 잔여 약 6.13HP. 직격 114에 scorch 총량을 미리 더하지 않는다.
- Golden Gun 기존 `scorch_ticks=100`도 그대로다. 이미 직접 피해로 처치하면 scorch 추가 계산은 불필요하며, 살아남은 저항 대상에게는 공용 후속 피해가 적용된다.
- 위 수치는 미리 확정한 펄스 개수가 아니다. 첫 pulse 위상/만료 판정과 저항/회복은 master의 최종 구현에 따른다. nonlethal scorch만으로 최종 처치를 보장하지 않는다.

## Shared 잔여점 / 통합 경계

- `Statuses.java`, `AbilityDamage.java`, 등록부, 저항 데이터는 수정하지 않았다. HunterGrenade 소이, HunterMelee 칼, HunterSuper Golden Gun의 기존 `Statuses.scorch` 호출은 유지되므로 master 공용 scorch 변경 대상이다. 초기 열람본에는 바닐라 fire와 고정 2HP/20tick scorch가 있었으며 위 합산은 그 초기 동작이 아닌 master 예정 계약에 대한 값이다.
- 현재 scorch API에는 ability ID/stack 수가 없고 melee/super 경로는 owner만 전달한다. 소이 60stack, Knife Trick 개별 20stack 등의 원작 차이는 공용 50stack 대표 근사와 다르다. 소이 GrenadeToken 전달과 근접 퍽 snapshot은 보존했다.
- Blade Barrage의 원작 scorch는 현 구현에 호출이 없어 미추가. Gathering Storm 원작 impact jolt, Spectral heavy weaken, Combination Blow stack, Golden Gun precision/Line'Em Up, Shadowshot tether 피해 공유도 현 구현과 원작의 차이로 남긴다. 이번 수치 연결에서 동작을 확장하지 않았다.
- 연막은 기존 억제·투명만 유지하고 신규 피해/JSON key를 만들지 않았다. Shadowshot 기존 tether에는 새 펄스 피해를 만들지 않았다.
- Shadowshot weaken은 일반 WEAKENED 공용 경로를 유지하므로 Deadfall 고유 약화 배율과 다르다. 이 부분 및 scorch는 master 공용 검토 범위다.
- 공용 loader는 hunter/titan/warlock JSON 3개를 요구한다. 이 delta는 hunter 한 개만 제공하므로 master 통합 시 다른 두 파일도 함께 존재해야 한다.

## 정적 검토 및 통합 기준선

수치 작업 예외에 따라 빌드/서버/Vision/CU/커밋/추가 agent/개별 테스트 신설/테스트 실행을 하지 않았다. 수행한 것은 main 대비 diff, 호출자·damage sink·contact 연결, JSON 형식과 키, PvE param/value 표현식 및 scorch 호출 보존에 대한 정적 검토다. 런타임 명중·실제 저항 조합·시각 효과 검증을 통과했다고 주장하지 않는다.

초기 delta의 4개 파일은 main 최신과 byte-identical이며 서로 다른 inode임을 확인했다. 다음 SHA-256을 master 통합 전 main과 비교해 drift가 있으면 재검토한다.

| 파일 | 초기 SHA-256 |
| --- | --- |
| HunterGrenade.java | 9d6fed02fb61deceb079c73a9a9532d5abab36e0db86c6cf91e458d1c813d021 |
| HunterMelee.java | 987e29840429dfbeba0ae1e798264eb11bf2039f9ad4f4e2acc82edf35d41574 |
| HunterSuper.java | 69ee99bca920cf88ca328305cb076b87eb48325f542f70b07f3dd62905e09e82 |
| HunterExpandedSupers.java | 2b6ed22fb13cc5e46b2884ca90ca114986bc3568c7499ec795b2825f81299fae |
