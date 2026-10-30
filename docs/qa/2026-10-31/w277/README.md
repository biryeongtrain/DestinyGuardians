# W277 ADS 속도·줌 반응·좌클릭 누락 수정

## 원인
- 줌: 서버가 ADS 진행도를 틱마다 선형으로 올리며 이동속도(바닐라 FOV) 목표를 조금씩 바꾸고, 클라이언트도 FOV를 따로 보간해 지연이 두 번 겹침.
- ADS 시간 자체가 5~10틱(0.25~0.5초)으로 길었음.
- 좌클릭 누락: 바닐라 클라이언트는 허공 클릭 뒤 10틱(0.5초) 동안 좌클릭 자체를 보내지 않음(missTime). 서버 디바운스 3틱도 겹침.

## 수정
- `WeaponAiming.ADS_TIME_SCALE = 0.6`: 모든 무기 ADS 진입·해제 시간 60%(최소 2틱). 퍽 보정은 그대로 적용된 뒤 곱함.
- ADS 입력이 받아들여진 첫 틱에 이동속도(줌) 목표를 최종값으로 바로 보냄. 클라이언트의 프레임 단위 FOV 보간만 남음.
- GCB 사용자는 GCB가 보내는 실제 공격 키 이벤트로 ADS를 토글(missTime 영향 없음). 같은 클릭의 punch 패킷 중복은 무시. 바닐라 punch 경로 디바운스 3→2틱.

## 검증
- ADS 관련 게임테스트 69개 클래스 실행. ADS 타이밍을 고정값으로 검사하던 테스트(W68, W70, W75, W93, Surplus, ThreatDetector, Quickdraw, FirmlyPlanted, ElementalCapacitor)는 새 시간(`WeaponAiming.fast`)과 즉시 줌 목표에 맞게 기대값 수정.
- 남은 실패(reload_credit_w65, bow_presentation_w50, inventory_wire_w92, izanagi_presentation_w91, izanagi_w84, legacy_wire_w93 장전 2건, W70 활 nock 1건)는 이번 변경 전 코드로 같은 서버에서 돌려도 동일하게 실패(기존 장전/활 선택자 문제).
- 실게임 손맛·GCB 클릭은 Vision으로 확인하지 않음.
