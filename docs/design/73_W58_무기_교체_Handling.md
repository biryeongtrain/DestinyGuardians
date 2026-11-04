# W58 — 무기 교체 Handling

## 목적과 원작 근거

기존 무기는 사격 간격·장전·ADS에는 시간이 필요했지만, 선택을 바꾼 즉시 새 무기를 사용할 수 있었다.
이번 단계는 **이전 무기 stow → 새 무기 ready**를 서버 틱으로 연결한다.
공식 W40 캐시의 선택 아이템별 Handling stat(943549884)과 기존에 고정한 Oracle Engine ready/stow 곡선을 사용한다.
[데이터 출처·고정 commit·단위·제한](../../art/weapons/w58/README.md), [63개 추출 근거](../../art/weapons/w58/extraction.json).

공식 stat은 2026-10-13 Manifest, community 곡선은 2026-05-20 고정 commit이다.
Handling 설명은 “The speed with which the weapon can be readied and aimed.” 이며 ready/stow 수식의 출력 단위는 초다.
발사 burst용 30fps 단위를 혼동하지 않는다. `ceil(seconds*20)` 및 source의 stow-at-100 floor를 보존한다.
현재 D2의 모든 중간 패치를 새로 조사하거나 정확한 원작 애니메이션 길이를 실측했다고 주장하지 않는다.

- 58개 원거리/월도: 실제 공식 Handling과 해당 family/category 곡선으로 계산.
- 5개 검: 공식 Handling/curve가 없어 명시적으로 unknown(null). 임의 시간을 만들지 않는다.
- Austringer 준비7틱/수납8틱, Beloved 준비8틱/수납7틱, Nezarec’s Whisper 준비7틱/수납8틱.
- Perk·방어구·마스터워크·enhanced roll·속성 버프는 아직 계산에 포함하지 않는다.

## 런타임

`WeaponHandlingProfile`은 데이터 검증/조회, `WeaponSwapCycle`은 순수 identity 기반 두 phase,
`WeaponHandling`은 실제 플레이어·dimension·ItemStack과 서버 시계를 소유한다.
기존 사격 cycle과 별도이므로 스킬/회피가 교체 시간을 초기화하지 않는다. 예비탄/아이템 복사나 예약 task는 없다.

1. 유효한 바닐라 selected-slot 패킷이 실제 선택을 바꾸기 직전 source/target을 관찰한다.
2. `/destiny loadout select`도 같은 경로로 처리하며, 장비 command/인벤토리 참조 변경은 다음 실제 입력/서버tick에서 관찰한다.
3. 교체가 발견되면 이전 장전·burst·charge·held 후보/모델 scope·가드·검 contact를 취소한다.
   이미 발사돼 비행 중인 투사체는 없애거나 환불하지 않는다.
4. 준비 완료 전 발사·charge·Q 장전·일반 무기 근접·가드·ADS 진입을 막는다. 일반 Guardian 스킬과 명사수 즉시 재장전은 가능하다.
5. 타이머 종료만으로 발사/장전하지 않는다. 기존 실제 입력 경로가 다시 진행해야 하며, crossbow heartbeat는 실제 갱신 입력에서 재시도한다.
6. Holding crouch는 준비 완료 뒤 기존 ADS transition을 시작할 수 있다. 교체 시간을 이용해 미리 scope/ADS를 완성하지 못한다.

## 인터럽트 및 fallback 정책

정확한 원작 중간 프레임 전환을 확보하지 못했으므로 다음 규칙은 **자체 정책**이다.

- 서버 session의 첫 관찰은 이미 든 상태로 취급한다(login/spawn/fixture에 불필요한 가상 교체 없음).
- 같은 실제 참조를 다시 선택하면 연장/초기화하지 않는다. 같은 컴포넌트의 다른 ItemStack은 실제 교체다.
- 수납 중 다시 선택하면 남은 수납 시간을 유지하고 마지막 선택 무기의 ready만 적용한다.
- ready 도중 다른 무기를 선택하면 진행 중인 draw를 취소하고 그 아이템의 stow부터 계산한다.
- 건축 아이템·프리뷰 자체는 막지 않는다. 돌아오는 총기는 알려진 incoming ready와 남은 stow를 지불한다.
- 검의 unknown ready/stow는 추가하지 않지만, 상대쪽 총기의 알려진 phase는 여전히 적용한다.
- 궁극기 임시 장비는 일반 무기 교체로 관찰하지 않는다. 기존 native 황금총 방향/발수·아크/공허 카메라는 변경하지 않는다.
- death/disconnect/dimension/server-stop의 기존 cleanup에 연결한다. 스킬 취소/명사수 회피는 deadline을 리셋하지 않는다.
- 기존 W46 shared firing cadence 정책은 보존한다. 원작의 무기별 ready/발사 회복 인터럽트까지 완전히 재현한 것은 아니다.

## HUD·모델·사운드

교체 중에도 실제 선택 무기 현재탄·예비탄·보조 두 줄을 표시한다. 가짜 재장전이나 원작에 없는 “교체 진행바”를 만들지 않는다.
기존 vanilla hotbar equip 표현은 유지한다. 별도의 원작 손/본 stow-draw 클립을 확보·이식한 것은 아니며 다음 시각 작업으로 남는다.
새 무기 geometry·텍스처·음원·황금총 변환을 변경하지 않는다.

## 검증

[W58 QA](../qa/2026-10-24/w58/README.md)에 테스트·현재 JAR·리소스·source pin·한계를 기록한다.
기존 W40/W47/W50 중 즉시 교체 후 장전/활 draw를 기대하던 시험은 **실제로 준비 시간을 기다린 뒤 동일한 검증을 수행**하도록 변경했다.
실패 gate도 보존하며, cleanup 이후 bow presentation이 임의 재바인딩되지 않는 기존 보장은 유지했다.
현재 클라이언트 화면·수신팩·실청취·다인 거리성능은 이 서버 테스트와 별개의 미검증 항목이다.

최종 Gate3/4 각각 **427 GameTest·397 JUnit**, fail/error/skip0·20task 강제실행 성공.
현재177sourcepin·640client리소스·10server-only·207mainclass·542원본무기/황금총에셋을 검사했다.
동일JAR SHA256 `4ef35aaed2926f63318a67df3ac9eb19adabef70169d4ac7e25969380a3894be`.
독립 Decimal 계산도58known/5unknown·15sourcehash 일치. 실제화면/native/청취 검증은 별도 미완료다.
