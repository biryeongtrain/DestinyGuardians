# W225 독립 검토

담당: Faraday the 2nd. master 와 별도로 실제 26.3 client 의 Player.getItemSwapScale 과 서버 WeaponHandling 을 읽었다. 제품 수정·빌드·native 입력은 수행하지 않았다.

- Austringer/Beloved/Ammit AR2/The Recluse 의 서로 다른 ID 사이 12방향만 자체 STOW/READY 모션이 있다. Austringer↔Beloved 는 W91, 나머지는 W113 경로다.
- 다른 무기·같은 ID 의 다른 stack·일반 item/빈 slot 전환에는 이 자체 swap 경로가 없다.
- Player 의 itemSwapTicker 는 carrier 의 item type 변경에도 초기화된다. 교체 억제 false 로 표시 stack 을 즉시 갱신해도 높이 변화는 별도 경로다.
- scale0은 자체 transform 을 유지하지만, 일반 전환에 남아 있던 바닐라 내림도 없앤다. swap 루트만 scale1로 되돌리면 자체모션에 변위가 중첩되며 일반 전환도 복원하지 못한다.
- native 검증은 W91/W113과 자체모션 없는 carrier 전환을 구분한다. hotbar 키 대신 native offhand 교환을 사용한 경우 그대로 명시한다.

코드 근거: WeaponSwapPresentation.java:25,58 / WeaponHandling.java:54,106 / WeaponCombatItem.java:40 / generate_swap_presentation_w91.py:28. 클라이언트 JAR SHA256:4508d006323f24fa02876310c192d739af56516eb259000ac50f0909a68c9a2d.

이 문서는 소스 감사다. 실화면 합격 여부는 master 의 PNG 검수에 별도로 기록한다.
