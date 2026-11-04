# W194 Mulligan

- 사용자 DDC Weapon Perks 150행. 기본 hash3513791699: Primary 빗나감 시 35%, Special/Heavy 20% 확률로 탄창에 1발 생성. 강화판 제외.
- 현재 catalog65 실제 풀은 Patron of Lost Causes socket3, Hammerhead socket4다. 정의·소켓 증거·DDC 원문/해시는 source.json, 생성기는 `scripts/build_mulligan_w194.py --verify`.
- 실제로 탄약을 지불한 hitscan 발사마다 토큰 하나를 획득하고 모든 탄도 판정 뒤 한 번만 결정한다. 입력/질의/공격 거절은 추첨하지 않는다.
- 적합한 LivingEntity 기하 접촉은 실제 피해가 거절돼도 명중으로 판정한다. 벽 또는 허공 충돌은 빗나감이다. 이 충돌 경계와 정수 percentile 난수는 명시적 로컬 구현 정책이며 원작 내부 판정 코드를 확인한 것은 아니다.
- 생성 보상은 기본 탄창 상한까지만 채우며 예비탄을 소비하거나 재장전 발동/타이머를 만들지 않는다. 소유자·원본 스택·선택 롤·현재 서버 틱을 검증하고 같은 토큰은 결과와 관계없이 한 번만 소비한다.
