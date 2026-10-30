# W267 — 누락 15종 PvP 근사 보완

2026-10-30. 최신 사용자 지시 “데스티니처럼 유저체력20하에 대충맞게”에 따른 **포팅 근사값**이다. DDC 확정 원작 수치와 혼동하지 않는다. 메인 checkout은 읽기 전용으로 참조했고 이 delta의 JSON과 본 문서만 작성했다. 기존 50개 엔트리의 키·값·직렬화 텍스트를 보존하고 실제 catalog 차집합 15개만 뒤에 추가했다. Catalog 65개 = w30 63개 + w83/w84 exotic 2개.

## 단위와 선택값

모든 숫자는 `rawDestinyHP` 단위. `CrucibleDamage.base`는 `local / WeaponProfile.forEntry(entry).damage() * body / 230 * target.maxHealth`를 적용한다. 아래 환산 열은 maxHealth=20, local/profile=1일 때의 값이다. 피해저항·보호막·퍽·재생·거리감쇠 없는 산술이며 인게임 측정이 아니다. 추가 15종 모두 precision=body로 정밀 배율은 1이다. 검만 melee=230을 함께 둔다. **explosion 필드는 추가하지 않는다.**

| ID | body = precision (raw) | 기본 환산 HP | component |
|---|---:|---:|---|
| `coriolis_force` | 49.37142857 | 4.2932 | `per_bolt` |
| `salvager_s_salvo` | 260 | 22.6087 | `per_projectile_radial_total` |
| `deafening_whisper` | 130 | 11.3043 | `per_wave_base` |
| `edge_transit` | 280.5 | 24.3913 | `per_projectile_radial_total` |
| `canis_major` | 270 | 23.4783 | `per_projectile_radial_total` |
| `dimensional_hypotrochoid` | 230 | 20.0000 | `per_wave_base` |
| `bad_omens` | 424.193 | 36.8863 | `per_projectile_radial_total` |
| `bellowing_giant` | 424.193 | 36.8863 | `per_projectile_radial_total` |
| `code_duello` | 390.291 | 33.9383 | `per_projectile_radial_total` |
| `pyroclastic_flow` | 366.326 | 31.8544 | `per_projectile_radial_total` |
| `abide_the_return` | 230 | 20.0000 | `per_melee_light` |
| `goldtusk` | 230 | 20.0000 | `per_melee_light` |
| `crown_splitter` | 230 | 20.0000 | `per_melee_light` |
| `falling_guillotine` | 230 | 20.0000 | `per_melee_light` |
| `temptation_s_hook` | 230 | 20.0000 | `per_melee_light` |

`component`는 문자열 메타데이터이며 reader는 비어 있지 않은지만 확인한다. 이름이 별도 피해 계산을 실행하지 않는다. `per_projectile_radial_total`은 현재 런타임의 단일 방사 피해 예산이고, 분리된 직격 피해가 아니다. `per_wave_base`는 direct 0.2 / wave 1.0에 들어가는 기준값이다. `per_melee_light`는 유탄·총알이나 검 강공격 전체 피해가 아닌 유료 일반 베기 1회의 목표값이다.

## 출처와 근사 근거

기존 메인 `docs/qa/2026-10-30/w263/unresolved-damage-evidence.json` (조회시각 2026-10-30T06:39:11Z)을 재사용했다. 새 웹 리서치는 하지 않았다. 이 캐시는 현재 DDC와 오래된 Oracle 표를 구분하며, 아래 역사값을 현재 원작 확정값으로 승격하지 않는다.

- **Coriolis Force:** DDC Weapon Perks C316: 28.8/펠릿, 3점사 × 4펠릿 = 345.6/탄약. 현 `w46-timing.json`은 7볼트, 간격0, sharedBurstAmmo=true이고 `WeaponProfile`은 fusion pellets=1로 바꾼다. 따라서 **345.6 / 7 = 49.3714285714/현재 볼트**로 총량을 보존하는 임시 포팅이다. 28.8을 7볼트에 그대로 넣으면 총201.6으로 완전 명중도 20HP 처치가 안 된다. 역사 Oracle 53.989/7볼트보다 현재 DDC 총량을 우선했다. 실제 3×4 패턴으로 수정할 때 반드시 body/precision=28.8, component=per_pellet로 함께 변경해야 한다. 이 값은 원작 볼트 실측값이 아니다.
- **Salvager's Salvo:** 역사 Oracle 200과 캐시에 적힌 Bungie 2024-04-04 직격+40%, 총량 약+15%를 참고한 기준 약230. 현 방사 피해는 직격 대상에도 감쇠되므로 f=0.9에서 약1발 처치가 되도록 230/0.9를 올림한 **260**을 선택했다. 현재 정확한 impact/splash 실측값이 아닌 근접 명중 보정 근사다. 반경3 내 원거리 폭발까지 1발 처치로 만들지 않는다.
- **Deafening Whisper:** 역사 Oracle WaveFrame 130을 **파동 1회 기준**으로 재사용. 현재값 확정 아님. 직격은 0.2×130=26, 파동은130, 같은 적에게 둘 다 닿아도156으로 230 미만이다.
- **Edge Transit:** 역사 Oracle Adaptive heavy GL **280.5**를 현재 단일 방사 피해 예산으로 재사용. 현재 직격/폭발 분할은 검증되지 않았다.
- **Canis Major:** 역사 Oracle Rapid-Fire heavy GL 240.75는 f=0.9에서216.675로 처치 문턱 미달이다. 근접 명중 약1발 목표를 위해 240.75/0.9=267.5를 둥글게 **270**으로 선택했다. 원작 피해 변경을 주장하지 않는다.
- **Dimensional Hypotrochoid:** 캐시의130은 특수탄 WaveFrame을 중화기 Compressed Wave에 잘못 대응한 `reject_mapping`이라 사용하지 않았다. 중화기 파동1회 처치 목표의 **230**을 추정했다. 직격46 + 파동230 = 최대276, 기본 환산24HP다. 숫자가 같다는 이유로 다른 라이플 배율을 적용하지 않았다.
- **Bad Omens / Bellowing Giant / Code Duello / Pyroclastic Flow:** 역사 Oracle 각 프레임 **424.193 / 424.193 / 390.291 / 366.326**을 각각 한 발 방사 피해 예산으로 재사용. DDC C317/C313/C327/C334의 직격:폭발 비율1:3.5 또는1:8.7은 확인됐으나 현재 절대값 증거가 아니고 현재 reader도 분리하지 않아 혼합 적용하지 않았다.
- **검 5종:** 현재 절대 PvP 일반 베기값은 캐시에 없다. 유료 일반 베기1회로 20HP 처치하도록 **body=precision=melee=230**을 추정했다. 같은 1회 처치 문턱을 의도적으로 사용했으며 프레임별 속도·범위·강공격 배율은 기존 코드에 남긴다. Manifest Impact나 PvE 값을 원작 PvP로 오인하지 않는다. 실제 적용 누락은 아래에 별도로 기록한다.

원본 링크: [DDC](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit), [Oracle 고정 스냅샷](https://github.com/d2foundry/oracle_engine/blob/dcd0c7d302b056ffbb532edcb711d724a17ca8c1/build_resources/weapon_formulas.json), [Coriolis 변경](https://www.bungie.net/7/en/News/Article/destiny_update_8_2_0), [유탄 변경](https://www.bungie.net/7/en/news/article/this-week-in-destiny-04-04-24). Oracle 커밋 날짜는 sandbox 검증 날짜가 아니다.

## 대표 20HP 처치 횟수

- Coriolis: 볼트당4.2932HP, **5/7볼트** =21.4658HP, 전탄30.0522HP. 탄약1개 안에 처치. 현재 원작 8/12펠릿 처치를 현 패턴에 근사한 것이며 실제3점사 타이밍은 재현하지 않는다.
- Salvo: f=0.9이면20.3478HP → **1발**, f=0.5이면11.3043HP → **2발**. 직격+폭발2회 합산 없음.
- Deafening: 파동11.3043HP → **2회**; 직격+파동13.5652HP도 **2발**. 직격만은2.2609HP →9회.
- Edge Transit: f=0.9이면21.9522HP → **1발**, f=0.5이면12.1957HP → **2발**.
- Canis Major: f=0.9이면21.1304HP → **1발**, f=0.5이면11.7391HP → **2발**.
- Dimensional: 파동20HP → **1회**; 직격만4HP →5회; 직격+파동24HP. 파동1회의 다중 segment 접촉은 재합산되지 않는다.
- 로켓4종: f=0.9에서 각각33.1977 /33.1977 /30.5445 /28.6690HP → **1발**. f=0.5에서는18.4432 /18.4432 /16.9692 /15.9272HP → **2발**.
- 검 목표: 유료 일반 베기20HP → **1회**. **현재 코드에서는 아직 그렇게 되지 않는다.** 현 일반 베기는 Abide/Crown/Falling/Temptation **2회**, Goldtusk **3회**(9.5+9.5+11.875), 빈 탄약 베기는3HP →7회. 아래 누락 수정 전에는 이 현행 횟수가 유지된다.

방사 피해 f = max(0.3, 1 - 폭심에서 표적 몸 중심까지의 거리 / 반경). f=0.9는 비교용 근접 시나리오이지 모든 직격에서 보장되는 계수가 아니다. 감쇠·위치에 따라 위 횟수는 달라진다. 실제 1발 처치 문턱 f는 Salvo0.8846, Edge0.8200, Canis0.8519, Bad/Bellow0.5422, Code0.5893, Pyro0.6279다.

## 실제 reader와 코드 연결 누락 — master 소유, 수정하지 않음

1. `WeaponCatalog.load`는 `/destiny/weapons/w30.json` + `WeaponExotics.append`(w83/w84)를 읽는다. `CrucibleWeaponDamage.load`는 정확히 `w263-pvp-damage.json`에서 body/precision/component와 optional explosion/melee를 읽는다. `CrucibleDamage.base`는 ServerPlayer에만 maxHealth/230을 적용한다. PvE는 기존 local 값을 반환한다.
2. `WeaponRuntime.emit`의 pellets 루프는 **펠릿마다** base를 계산하고 target별 합산한다. fusion은 timing의 볼트별 emit, pulse/sidearm/linear burst도 각 발 단위다. 기존50행은 per_pellet/per_bolt/per_bullet 의미 그대로 보존했다. 총 점사 피해를 각 발에 반복 적용하지 않았다.
3. 이 메인 `src/main/java`에는 `ProjectileWeapons` 클래스/참조가 없다. 실제 투사체 처리는 `WeaponRuntime.Shot`, `tickShot`, `impact`, `waveImpact`에 있다. `BreachGrenade.supports`는 Salvo만 선택하며 블록 충돌은 반사, 해제/수명 종료는 detonateBreach→impact, 엔티티 접촉은 impact 한 번이다.
4. `WeaponRuntime.impact`(확인 시1393–1423행)는 blastRadius>0일 때 target당 **base×falloff 한 번**을 적용한다. `else if`의 직접 명중 경로는 추가 실행되지 않는다. `explosion`은 파싱만 되고 계산 reader가 없다. 이번 JSON에 explosion을 넣거나 body에 별도 추가 배율을 적용하지 않았다. 나중에 direct/splash 분리를 구현할 때 현재 body 총량에 explosion을 그대로 더하면 이중 계상되므로 반드시 데이터 의미도 함께 바꿔야 한다. 현 직격 감쇠 문제를 정확히 해결하려면 코드 변경이 필요하다.
5. `WaveFrameProfile`→`w78-wave.json` 두 무기 모두 directMultiplier=.2, waveMultiplier=1. `waveImpact`의 directContacts는 직격 중복을 막고 `WeaponWavefront.touched`는 파동 재접촉을 막는다. 두 집합은 별개여서 한 표적이 직격+파동을 받을 수 있다. **상한1.2×body**를 이미 예산에 포함했다. 방사 폭발은 이 경로에서 발생하지 않는다.
6. **검 일반 베기 전5종 미연결:** `WeaponRuntime.swordContact` 일반 베기 분기(확인 시750–759행)는 `apply(..., damage, ...)`로 곧장 들어가 CrucibleDamage를 거치지 않는다. Crown SLAM / Falling VORTEX 강공격(774–782행)도 동일하다. JSON 엔트리 추가만으로 해결되지 않는다. master는 대상별 PvP 환산을 이 분기에 연결하되 유료/빈탄약, combo, 약한 강공격 조건을 유지해야 한다.
7. **검 일부 강공격 연결 및 약공격 조건 손실:** Abide UPPERCUT / Goldtusk DASH는 emit→`CrucibleDamage.melee`로 들어간다. 이번 melee=230은 이 두 경로에서20HP가 되지만 helper는 glaive용으로 local 값을 무시하므로 **충전 강공격과 에너지0의 약한 강공격 모두20HP/1회**가 된다. 단일 melee 값으로 둘을 따로 보정할 수 없다. master는 검 전용 배율 보존 분기를 구현하고 glaive의 기존7/14 콤보 억제 정책과 구분해야 한다. 이 연결 결함을 고치지 않고 검5종 보정 완료로 승인하면 안 된다.
8. Temptation CASTER 강공격은 projectile→impact→base를 거쳐 정상적으로 local/base=2.4(무에너지 .84)를 보존한다. 이번 body230으로 충전48×f HP(예: f=.5에서24HP/1회), 무에너지16.8×f HP(같은 f=.5에서8.4HP/3회). 이것은 한 발 한 번의 피해이며 melee230을 추가 합산하지 않는다. 현재 Crown/Falling 강공격은 여전히 local40.25/29HP, 무에너지14.0875/10.15HP다.
9. `CrucibleDamage` / `CrucibleWeaponDamage` 주석의 “추정 없음”은 이번 명시적 사용자 근사 허용 이후 데이터 설명과 맞지 않는다. 코드 소유자가 필요시 주석도 갱신해야 한다. 이 worker는 Java 파일을 변경하지 않았다.

## 정적 확인과 통합 기준

빌드·서버·테스트·새 수치 테스트·다른 agent·커밋은 실행하지 않았다. 수행한 것은 JSON 파싱, catalog 차집합 비교, 기존50개 텍스트/값 보존 비교와 코드 읽기 및 산술 계산뿐이다. 라이브 피해/인게임 QA 통과를 주장하지 않는다.

- 복사본 입력 및 읽은 main JSON SHA-256: `8efe9951fc9c4e60810f562037b6d73ab4d48af8ad7f7860ccfdde96db05ebc2`
- 출력 JSON SHA-256: `2e567486c785fc6def4bc4f6278ac7c4743424c90d04d14a5b4472cfc4263e4b`
- 결과65행, 신규15행, catalog 누락0, 불필요 ID0. 메인 통합 시 입력 hash가 달라졌으면 이 전체 파일로 덮어쓰지 말고 신규15행 delta만 재검토한다.
- 반환 파일: `src/main/resources/destiny/weapons/w263-pvp-damage.json`, `docs/qa/2026-10-30/w267/weapon-approximations.md`.

## Master 통합 수정

위 reader 누락 목록은 worker가 반환한 **수정 전 진단**이다. W267 master가 `WeaponRuntime.swordContact`의 유료 일반 베기와 SLAM/VORTEX에 대상별 환산을 연결했다. `CrucibleDamage.melee`의 sword 분기는 `base`를 사용하여 local/base 배율을 보존한다. UPPERCUT/DASH의 에너지0 배율도 유지되며 CASTER는 기존 projectile/base 경로를 유지한다. 빈 탄약 일반 베기는 기존 3MC HP를 그대로 두었다. Glaive의 별도 melee 값과 기존 콤보 억제는 바꾸지 않았다.

따라서 방어 없는 기본20HP 대상의 유료 일반 베기는5종 모두1타이고, 탄약0 베기는 기존7타다. 강공격은 프레임별 배율과 에너지0의0.35배를 적용한다. 일부 프레임은 에너지가 없어도 원래 강공격 배율이 높아1타가 될 수 있으며 이는 모든 약한 강공격을 강제로 동일하게 만드는 것과 다르다. 위의 “아직 연결되지 않음” 진단은 최종 동작 설명이 아니다.
