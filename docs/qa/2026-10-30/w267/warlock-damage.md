# W267 워록 PvP 피해 연결 — 2026-10-30

## 범위와 적용 계약

배타 쓰기 루트: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-parcel_of_stardust_fell_to_earth/w267-delta`.
메인 `/Users/qf/IdeaProjects/DestinyGuardians`은 읽기 전용으로 참조했다. 부모 worktree의 stale 소스는 편집하지 않았다.

수정 6파일:

- `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockGrenade.java`
- `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockMelee.java`
- `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockSuper.java`
- `src/main/java/kim/biryeong/destiny/ability/warlock/WarlockExpandedSupers.java`
- `src/main/resources/destiny/abilities/w267-warlock-pvp.json` (신규)
- `docs/qa/2026-10-30/w267/warlock-damage.md` (신규, 본 문서)

메인 `AbilityDamage.pvp(Ability, String, LivingEntity, float)` API와 등록 ID를 확인했다.
JSON은 14개 `<ability.id.getPath()>/<contact>` 숫자 항목이다. 타격 직전 helper가 플레이어만 `raw * target.maxHealth / 230`으로 환산하며, 몹에는 기존 local 인수를 그대로 반환한다.
수류탄과 근접은 각각 `WeaponAdrenalineJunkie.grenadeDamage` 및 `MeleeWeaponTraits.poweredDamage` **앞에서** 환산한다. 궁은 기존 `AmmoGeneration.SUPER`를 보존한다. burn은 기존 일반 ability attribution을 보존하고 근접 퍽을 새로 발동시키지 않는다.
지연 burn/Vortex에는 발동 당시 ability를 보관한다. 현재 로드아웃에서 피해 ID를 다시 찾지 않는다.
기존 코드에 거리별 피해 falloff는 없으며 새로 넣지 않았다. PvE 인수, 타격/펄스 주기, 수명, 모션, 범위, 쿨다운, 애니메이션, 취소/소유권 조건은 그대로다. Well에는 피해를 추가하지 않았다.

## 출처와 근사

[Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4) CSV 스냅샷 `/private/tmp/destiny-w265/{Arc,Solar,Void}.csv`를 읽었다. 아래 번호는 헤더 포함 1-based **CSV 논리 레코드**이며, 셀 내부 줄바꿈 때문에 텍스트 파일 줄 번호와 다르다. 별도 실시간 HTTPS 재조회는 하지 않았다. 대괄호 PvP 값과 `?`를 구분한다.

| 항목 | 실제 CSV 근거 | 적용 및 차이 |
|---|---|---|
| 폭풍 수류탄 | Arc 37: 초기 [70], 후속 [50], Guardian 총 120 | **local approximation**: 현재 60틱/15틱 = 4펄스에 30씩, 총 120. 원작 2회 타격을 장판 4회로 분산. |
| 태양 수류탄 | Solar 36: 충격 [20], 장판 [25] × 13 = [325] | **local approximation**: 현재 충격 피해 접점이 없어 80틱/10틱 = 8펄스에 (20+325)/8 = 43.125씩, 총 345. 원작 첫 지연/주기 및 Scorch는 재현하지 않음. |
| 소용돌이 수류탄 | Void 39: 충격 [25], 장판 [20] × 12 = 240 (강화 380과 마지막 불명 틱 제외) | **local approximation**: 현재 8펄스에 (25+240)/8 = 33.125씩, 총 265. 충격 분리/원작 지연은 없음. |
| 연쇄 번개 | Arc 70: 직격 [100], 전이 [54] | 첫 타격 100, 후속 타깃 54. 기존 최대 3명, 방문한 적 재타격 금지 유지. Jolt/Amplified 추가 효과는 없음. |
| 소각의 손가락 튕기기 | Solar 76: 불꽃 [27?] × 5, 최대 [135?] | **local approximation**: 현재 한 대상은 불꽃 5개 중 1번만 직접 타격. 직격 120 + 기존 burn 3회 × 5 = 총 135로 배분. 원작 불꽃 1개 피해가 아니며, 135 자체도 잠정치. 실제 Scorch 스택/점화 대신 기존 burn 사용. 한 불꽃만 닿아도 합산 예산을 받는 차이 있음. |
| 소형 특이점 | Void 69: 폭발 [60] | 현재 단일 충돌 타깃에 60. 기존 밀치기 유지. 원작 범위 폭발/Volatile은 새로 추가하지 않음. |
| 폭풍몰입 | Arc 73: light attack [90]/0.34초, 최대 +65% 램프 | 90/기존 타격으로 기본 3타 유지. 현재 약 11틱 간격(입력/애니메이션 조건 포함), 램프·시전 폭발·seeker 없음. 원작 DPS/TTK 재현이 아닌 기본 타격 수 기준의 **local approximation**. |
| 새벽칼날 | Solar 79: impact/splash/flame streak PvP 모두 [?] | **local approximation**: 현재 단일 sword blast 300. 일반 1타, 55% DR 궁 2타를 목표로 선택. 원작 확정값으로 주장하지 않음. |
| 신성 폭탄: Vortex | Void 72: 폭발 [?], 장판 [?]/0.13초 | **local approximation**: 폭발 800, 기존 10틱 장판 펄스 60. 폭발은 58% DR에도 한방, 장판만은 일반 4펄스. 장판에 폭발 800을 매번 적용하지 않음. 200틱 장판 최대 20펄스/총 1200. Cataclysm/seeker로 간주하지 않음. |
| 혼돈 범위 | Arc 72: beam [?]/0.13초 | **local approximation**: 기존 3틱 펄스 90, 일반 3회(첫 적중 후 0.30초), 55% DR 6회. 7-hit Jolt strike는 현재 없으므로 추가하지 않음. |
| 신성 차원 | Void 73: light [200], 0.6초 충전 시 피해 +120% | 현재 항상 12틱 완충 후 폭발하므로 200 × 2.2 = 440. 일반 1타, 55% DR 2타. 원작 무충전/최대50% falloff/Volatile/블링크 seeker는 현재 없어 재현하지 않음. 기존 고정 반경의 **local approximation**. |

수류탄 합산은 현재 메인 resource의 duration/pulse 설정 기준이다. 이후 주기나 수명을 조정하면 이 per-contact JSON의 합산 예산도 재검토해야 한다. 중도 진입·이탈, 가시선 상실, 죽음/취소는 실제 누적 피해를 낮춘다.

## 20HP 환산과 예상 타격 수

방어/흡수/회복/퍽/약화가 없는 20 최대HP 대상의 산술값이다. 오른쪽은 **예시 55% 피해저항**만 추가했을 때이며, 모든 궁의 저항이 55%라는 뜻이 아니다. 게임 실행 결과가 아니다. 수류탄의 필요 펄스 수는 한 번 시전으로 가능한 횟수와 구분한다.

| JSON key | raw/contact | 20HP 피해/contact | 일반 필요 타격 | 55% DR 필요 타격 |
|---|---:|---:|---:|---:|
| `warlock/arc_grenade/field_pulse` | 30 | 2.609 | 8 | 18 |
| `warlock/solar_grenade/field_pulse` | 43.125 | 3.750 | 6 | 12 |
| `warlock/void_grenade/field_pulse` | 33.125 | 2.880 | 7 | 16 |
| `warlock/arc_melee/direct` | 100 | 8.696 | 3 | 6 |
| `warlock/arc_melee/chain` | 54 | 4.696 | 5 | 10 |
| `warlock/solar_melee/direct` | 120 | 10.435 | 2 | 5 |
| `warlock/solar_melee/burn_pulse` | 5 | 0.435 | 46 | 103 |
| `warlock/void_melee/direct` | 60 | 5.217 | 4 | 9 |
| `warlock/arc_super/chain_pulse` | 90 | 7.826 | 3 | 6 |
| `warlock/solar_super/sword_blast` | 300 | 26.087 | 1 | 2 |
| `warlock/void_super/nova_blast` | 800 | 69.565 | 1 | 1 |
| `warlock/void_super/vortex_pulse` | 60 | 5.217 | 4 | 9 |
| `warlock/chaos_reach/beam_pulse` | 90 | 7.826 | 3 | 6 |
| `warlock/nova_warp/charged_blast` | 440 | 38.261 | 1 | 2 |

- 폭풍 수류탄은 시전당 4회/총 10.435HP라 단독 처치 불가. 태양은 최대 8회/총 30HP 중 6회, 소용돌이는 최대 8회/총 23.043HP 중 7회로 일반 대상 처치 가능.
- 소각 근접은 한 번 시전으로 직격 10.435 + burn 0.435 × 3 = 11.739HP. 근접/burn 표의 필요 횟수는 반복 적중 산술이며 한 번 시전 안에서 반복되지 않는다.
- 새벽칼날/신성 차원은 58% DR 상대에도 각각 2타가 필요하고, 신성 폭탄 800은 58% DR 후 29.217HP로 1타다. 폭풍몰입/혼돈 범위는 채널형이라 일반 3펄스, 58% DR에는 7펄스가 필요하다.

## 정적 검토와 공유 잔여 사항

네 클래스의 모든 기존 직접 피해 호출과 내부 damage helper 호출을 대조했다. 수류탄 3종, 근접 직격 3종/전이/burn, 기본 궁 3종/Vortex, 확장 궁 2종의 14개 key가 연결된다. Well은 치유/버프만 유지한다. 새 JSON은 flat numeric이며 helper가 읽는 정확한 경로에 배치했다.

- 메인 helper/master/Statuses 및 기존 data resource 파일은 수정하지 않았다. 신규 테스트, 빌드, 서버, Vision, Computer Use, 커밋, 추가 agent를 실행하지 않았다. 컴파일/실전 결과는 미검증이다.
- 공용 `Statuses.tick()`은 확인 당시 `onFire()`로 매 20틱 `2f`를 직접 피해 처리하고 vanilla fire도 설정한다. caster ability/contact를 저장하지 않아 이 워록 JSON 환산과 독립적이다. master가 공용 소각/vanilla fire/킬 귀속을 함께 검토해야 한다.
- 읽기 전용 확인: `HunterGrenade`의 solar, `HunterMelee`의 solar 및 `HunterSuper`의 SCORCHED keyword가 `Statuses.scorch(...)`를 호출한다. 이 지연 소각 경로는 직접 타격 환산만으로 덮이지 않는 shared 잔여 사항이다. 헌터 소스는 수정하지 않았다.
- 워록 burn은 `Statuses`가 아닌 `WarlockMelee.Burn`의 별도 3펄스라 이번 작업에서 환산했다. 워록 현재 미구현 Jolt/Volatile/Scorch/점화·추가 seeker/flame streak를 새로 추가하지 않았다. 원작 전체 피해 동작의 복제 완료로 간주하지 않는다.
- 피해 수신 이후 저항/약화/퍽 경로는 기존 구현에 맡긴다. master 통합 시 hunter/titan JSON도 함께 있어야 공용 helper 초기화의 필수 resource 계약을 만족한다.

## 통합 기준선

처음 확인할 때 네 delta 사본은 메인과 byte-identical이며 inode가 달랐다. 아래는 수정 전 SHA-256이다. 통합 전 master가 메인 drift를 다시 확인해야 한다.

| 파일 | 수정 전 SHA-256 |
|---|---|
| `WarlockGrenade.java` | `a84b81ef97f78075f7ed156ce1d14890d187102ea156b6af51c82e37731732a0` |
| `WarlockMelee.java` | `6689f9ab8d71a475b6e9ff3cf5b105937a8f37b19bede720a9fa2459702a52ff` |
| `WarlockSuper.java` | `4e1e1477c6eec4e136e0a2bb4b896e13bcebbcc95645a1a318fd1c16b1aaee38` |
| `WarlockExpandedSupers.java` | `ceda4d05bf342a74f0d39dfa2befda1fb0bb2e3c8602fade965d6e532fb0a54a` |
