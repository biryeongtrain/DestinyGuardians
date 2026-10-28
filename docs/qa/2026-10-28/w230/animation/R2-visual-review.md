# R2 실제 PNG 검수 — Maul/Fists 한정

2026-10-28. R3 authored asset 동결 유지. main/source/game/build 변경 없음. master 보고의 native11/11 gameplay/cleanup 통과와 별도로, 아래 판단은 실제 PNG를 열어 확인한 범위다.

- Maul light: `burning_maul-light-sample-01..06.png`. 준비 시 머리 위에 있던 헤드가 02~03에서 몸 옆 허리 높이로 내려오며, 05에서는 반대편에 보인다. 자루의 수평 휘두르기와 몸 회전이 읽힌다. R1의 머리 위 수직 고정 문제는 이 표본에서 해소됐다.
- Maul heavy: `burning_maul-heavy-sample-03.png`는 머리 위 헤드, 04~05는 상체가 앞으로 숙여지고 헤드가 우측 하체 옆으로 내려온다. 위→아래 공격 전이는 확인했다. 전방으로 뻗은 자루/헤드 대부분이 후방 카메라의 몸에 가려져, 정확한 지면 접촉점과 양손의 연속 접촉을 완전 수용했다고 표시하지 않는다.
- Fists ground: `fists_of_havoc-ground-light-sample-00..06.png`, raw01/02/03. 준비·팔 각도 변화와 전진 타격/회복은 보인다. 특히 타격 순간의 오른팔/주먹은 몸과 전기 파티클에 상당히 가려진다. R1과 달리 팔 자세 변화는 있으나, 최대 전방 신전의 명료함은 후방 표본만으로 확정하지 않는다.
- Fists air: `fists_of_havoc-air-slam-sample-02.png`의 공중 자세에서 06/09의 몸을 숙이고 무릎을 굽힌 착지 자세로 전이한다. 지상 접촉 FX와 착지 동작은 읽힌다.

실제 contact sheet `r2-action-contact.jpg`와 위 raw PNG를 함께 검수했다. 신규 수정이 필요한 확정 결함은 이 표본에서 추가로 발견하지 않았다. 기존 파일/SHA 동결을 유지한다. 프레임 간 속도감의 연속성, 반복 flip 부재, 정확한6/7틱 시각 동기와 양손 연속 그립은 이 정지 표본만으로 검증 완료라고 주장하지 않는다. 추가 조치가 필요하면 후속 검증에서 측면 시점/저파티클 장면으로 제한해 확인하면 된다.
