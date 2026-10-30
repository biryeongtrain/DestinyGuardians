# W265 궁극기 피해 감소

## 범위와 근거

사용자 지정 [Destiny Data Compendium](https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4/edit)을 2026-10-30 직접 조회했다. 요청 URL의 탭은 챔피언 설명이어서 같은 문서의 Arc/Solar/Void 탭을 사용했다. CSV 반환 행 번호와 실제 셀 주소를 혼동하지 않는다.

- 기본 궁극기 9종과 확장 10종의 피해 감소를 분리한다. 괄호 밖 PvE와 대괄호 안 PvP 값을 구분한다.
- `?`가 붙은 수치는 확정값으로 채우지 않는다. 칼날 장전 PvE와 새벽의 수호물 시전 PvE는 미확정이므로 새 감소를 부여하지 않는다. 스펙트럼 칼날은 확인된 기본 PvP 58%만 적용하며, 은신 59?%의 추가 1%는 적용하지 않는다.
- 황금총은 PvP 0% / PvE 60%. 시트의 Deadshot 전용 Knock 'Em Down 계수를 현재 3발 Marksman에 옮기지 않는다.

## 구현

1. 운영 서버 접속자 0명 확인 후 정상 종료. 4GB 설정 보존.
2. 궁극기 시작 시 선택된 궁극기 ID, 정확한 세션 객체와 월드를 고정한다. 피해 시점의 새 로드아웃을 조회해 다른 궁극기의 감소율을 빌려오지 않는다.
3. 실제 `hurtServer` 경로에서 약화 다음에 궁극기 감소를 한 번 적용한다. 무기 가드와 바닐라 방어·흡수 처리는 기존 경로를 유지한다. PvP 전용 DamageType이 바닐라 Resistance를 우회해도 이 감소는 적용된다.
4. 피해 원인이 플레이어면 PvP, 다른 LivingEntity면 PvE로 판정한다. 투사체는 DamageSource의 소유자를 따른다. 출처 없는 환경 피해, 낙하/공허, 관리자 강제 사망, 자기 피해는 별도 전투원 감소를 추정하지 않는다.
5. 종료·취소·사망·접속 종료·차원 변경에는 효과가 남지 않는다. 신성폭탄은 투사체 수명 동안 시전자 감소를 연장하지 않고 시전 모션 구간만 보호한다. 혼돈 범위도 채널 종료 뒤 회복 모션에는 감소를 연장하지 않는다.
6. 빛의 샘은 시전 감소와 별개로 실제 살아 있는 샘 안의 시전자·아군에게 적용한다. PvP 주무기 40%, 특수·중화기·능력 50%; PvE 전투원 20%, 보스 10%. 겹친 샘은 중복되지 않으며, 궁극기 자체 감소와는 남은 피해를 곱한다. 현재 샘의 범위·수명·가시성 조건은 기존 구현을 유지한다.
7. 무기 종류는 발사 시점의 AmmoGeneration attribution을 DamageSource에 보존한다. 투사체가 닿기 전에 다른 무기를 들어도 샘 감소율이 바뀌지 않는다. PvE 보스는 기존 서버 분류와 맞춰 Wither/EnderDragon 또는 `destiny_boss` 태그를 사용한다.

## 병렬 작업과 검증

master: 피해 경로·세션·샘 통합 및 서버 운영. 고정 슬롯 1: 수치와 근거 신규 JSON, 슬롯 3: 세션/피해 GameTest, 슬롯 2: 샘/피해 GameTest. stale worktree는 현재 main API를 읽어 신규 파일만 반환하며 전체 sync·빌드 성공으로 간주하지 않는다.

사용자 지시에 따라 개별 수치마다 테스트를 만들지 않는다. 데이터와 실제 적용 지점을 대조하고, 테스트는 피해 경로·세션 종료·상태 변경·샘 이탈 등 동작에 집중한다. `minecraft-testing` 스킬을 적용했다.

## 적용 수치

| 궁극기 | PvP 감소 | PvE 감소 | 출처 셀 |
|---|---:|---:|---|
| Arc Staff | 53% | 90% | Arc D64 |
| Golden Gun: Marksman | 0% | 60% | Solar D79 |
| Shadowshot: Deadfall | 53% | 90% | Void D69 |
| Blade Barrage | 49% | 미확정·미적용 | Solar D75 |
| Spectral Blades | 58% | 90% | Void D67 |
| Gathering Storm | 49% | 90% | Arc D66 |
| Storm's Edge | 45% | 90% | Arc D68 |
| Fists of Havoc | 58% | 90% | Arc D98 |
| Hammer of Sol | 51% | 90% | Solar D105 |
| Sentinel Shield | 53% | 90% | Void D96 |
| Thundercrash | 25% | 90% | Arc D100 |
| Burning Maul | 53% | 90% | Solar D103 |
| Ward of Dawn | 26.5% | 미확정·미적용 | Void D100 |
| Stormtrance | 58% | 90% | Arc D126 |
| Daybreak | 51% | 90% | Solar D137 |
| Nova Bomb: Vortex | 49% | 90% | Void D127 |
| Well of Radiance | 미확정·미적용 | 미확정·미적용 | Solar D139 |
| Chaos Reach | 55% | 90% | Arc D124 |
| Nova Warp | 58% | 90% | Void D129 |

빛의 샘 행의 미확정은 **시전 모션 자체의 감소**를 뜻한다. 샘 내부 피해 감소는 위 별도 규칙으로 적용한다. 스펙트럼 은신 증가분 등 조건별 불확실값은 원문과 함께 JSON에 보존했다.

## 검사 기록

- 관련 JUnit 33개 및 첫 GameTest 클래스 컴파일 통과.
- 최초 CU 확인은 Mac 잠금이었으나, 사용자 잠금 해제 답변 뒤 Finder 데스크톱 접근을 확인하고 Vision 검증을 재개했다.

- 전체 JUnit: 2,301개 중 2,297개 통과, 기존 모델/UV 회귀 4개 실패 유지. 이번 변경의 새 실패 없음. `full-gate.json`에 정확한 이름을 기록했다. GameTest 컴파일 별도 통과.
- 서버 GameTest 신규 3개 + 기존 W263 PvP 피해·사망/리스폰·특수탄약 회귀 1개 통과. 첫 시도는 평화로움 난이도에서 Husk 생성이 거부돼 실패했다. COMMAND 생성과 보통 난이도로 검사 후 원래 평화로움으로 복원했다. 이 두 PvE fixture는 보통 이상의 난이도가 전제다.
- Vision 26.3 + 기존 격리 Danmo에서 리소스팩 로드 확인. `sneak + swap_offhand` 네이티브 입력으로 실제 아크 궁극기를 시작했다. 서버 명령의 동일한 Husk 귀속 4 피해가 일반 상태 20→16, 궁극기 중 20→19.6, 자연 종료 후 19.6→15.6으로 적용됐다. 적 AI의 자연 공격이나 실제 PvP 두 클라이언트 전투 검사는 아니다.
- 실제 PNG에서 일반 피격, 궁극기 3인칭·HUD, 종료 후 1인칭과 줄어든 체력바를 검수했다. 일반 피격 직후 client state는 전송 전 값20이라 서버 HP 로그를 판정 근거로 사용했다. 오디오는 청취하지 않았다.
- lease 해제·가상 키/대기 입력0·native 이동키 중립 확인. 소유 client wrapper 종료(-2), awake wrapper 정상 종료(0), QA 서버 정상 종료(0). 자신이 만든 Husk 정리와 테스트 계정 탑 복귀 후 종료했다.

## 커밋 범위

기존 미커밋 자산/구현은 보존했다. HEAD에 없는 SuperSession 탄약 메서드와 LivingEntityMixin의 기존 sword guard/타워 후킹을 이번 커밋으로 가져오지 않고, 이번 피해 감소 변경만 HEAD 문맥에 맞춰 stage했다. 실제 검증 대상은 기존 dirty 구현을 포함한 통합 working tree이다. clean clone 독립 빌드 인증은 아니다. 원격 push와 worktree 삭제는 하지 않는다.

운영용 테스트 서버는 `runServer`로 재개했고 리소스팩 생성까지 성공했다. `192.168.35.237:25565`, online-mode=true, andlist OP4, 실제 JVM `-Xmx4g`를 확인했다.
