# W191 — Full Auto Trigger System

- 사용자 지정 DDC Weapon Perks 행103: 일반 무기는 Full Auto Firing 설정과 같은 반복 입력, 산탄총은 발사 회복 간격 ×0.9. 강화 퍽 제외.
- 고정 공식 manifest의 현재 제품 무기65종 중 정확한10개 소켓. 일반 `4267945040`, 구형 산탄총 `2117683199`를 구분한다. 소켓·pool·currentlyCanRoll 증거와 입력 SHA는 source.json.
- Lonesome +5 Stability는 DDC가 “I guess”라고 적은 비공식 예외를 따른 임시 적용이다. 원작 확정 실측으로 표시하지 않는다. The Last Dance/Last Perdition은 현재 제품 목록 밖이다.
- `WeaponFullAuto`는 실제 장착 원본 객체의 선택 퍽을 조회하고, 접근성 설정을 변경하지 않는다. `heldAutomatic`의 반복 입력 결정과 `fire`의 실제 결제 직전 profile에 연결한다. 산탄총 간격은 fractional cadence를 유지하고 이미 결제된 발사의 deadline은 재계산하지 않는다.
- Lonesome 보너스는 기존 recoil/bloom/flinch Stability 합산 경로에 연결한다. 퍽 숫자만 검증하는 새 테스트는 만들지 않는다.
- 회전·모델·애니메이션 및 클라이언트 변경 없음. 실제 입력 연속 사격은 이번 배치에서 미검증.
