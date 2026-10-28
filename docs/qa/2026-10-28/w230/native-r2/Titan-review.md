# Titan R2 최종 검수 — 현재 플레이 가능 범위 승인

입력: /private/tmp/destiny-w230-native-r2/r2-action-contact.jpg 및 실제 frames PNG, oracle JSON, assertions.json. 읽기 전용 검수, 제품 수정/빌드/게임 실행 없음.

판정: 현재 W230 Titan 플레이 가능 패키지 수용. 추가 런타임 delta 없음. 이는 원작 모션/아트 완전 일치 또는 전 구간 양손 접촉 검수 완료를 뜻하지 않음.

## 승인 근거

- native assertions 요청11/완료11, Titan 포함 결과 serverOracles matched, cleanup true. 이 worker가 11종 전체 아트를 개별 승인했다는 의미는 아님.
- Fists 지상: ground-light oracle idle→w229_titan_arc_attack→idle. 실제 sample01~03에서 공격 자세 변화와 전진/아크 접촉 표시. primary 피해400→376. 해당 ground attack은 authored이며 추출 원본 펀치로 표기하지 않음.
- Fists 공중: air-slam oracle air→land→idle 확인. 실제 sample01~03 공중, sample05~07 낮아진 자세/착지 포즈 확인. R1에서 빠져 있던 land 모션 연결 수용. 각 타격의 물리 접지 순간을 sub-tick 단위로 영상만으로 증명한 것은 아님.
- Maul 약공격: light sample01의 들기에서 sample02~06 몸과 망치의 큰 회전/가로 휘두르기가 보임. R1의 거의 수직으로 고정된 인상은 개선됨. oracle attack 재생 및 idle 복귀.
- Maul 강공격: heavy sample03 망치가 머리 위에 있다가 sample04~05 바닥 가까이 내려옴. oracle attack2/pending→waves1 전이. R1 대비 내려찍기 구분 가능.
- Maul heavy 캡처 yaw45 전 구간 확인. 현재 프레임에서 고정 세계축 방향 오류로 확정할 근거 없음. 따라서 기존 회전 추가 수정 없음.
- Ward 외부: field-inspection-outside.png에 바닥 링과 바닥에 붙은 반구 전체 실루엣 표시. 반구 안 대상도 보이고 시전자는 1인칭으로 자유 이동. 외부 검사로 R1의 내부 시점만 확인했던 한계 해소.
- Fists/Maul/Ward cleaned oracle 모두 inSuper=false,limbClip=none,ward=false. 현 캡처 시나리오 정리 승인.

## 명시적 한계 — 현 패키지 차단 사유 아님

1. Fists 주먹 접촉 순간은 아크 파티클이 팔을 많이 가림. authored clip의 실제 재생은 oracle로 확인했지만 전방/측면에서 주먹 끝 궤적까지 확정하지 않음. 독립 원본 ground punch 부재는 여전함.
2. Maul 두 손은 light sample05 등 일부 프레임에서 손잡이 근처에 모여 있지만, 후방/회전/이펙트로 가려 전체 61포즈의 지속 접촉을 승인하지 않음. 순수 360도 회전량이나 원작과 동일한 타이밍도 PNG 표본만으로 확정하지 않음.
3. Maul 화염파는 yaw45 실제 시전/파생 field 발생을 확인했으나 모델이 플레이어 전방 몸에 가려 세부 +Z 앞뒤와 손잡이 방향처럼 명확한 측면 실루엣 판별이 어려움. 현재 코드의 rotationTo+Ypi와 모순되는 오류가 확인된 것은 아님. arbitrary yaw 전부 검증 완료로 표기하지 않음.
4. Ward 외부 표면은 촘촘한 보라색 격자가 많아 원거리에서 모아레/와이어프레임처럼 복잡하게 보임. 반구 위치/크기 연결 문제와 구분되는 아트 개선 후보. 현 단계에 새 수정 요청 또는 런타임 변경을 추가하지 않음.
5. 본 검수는 실제 R2 표본 시나리오 수용. 다인 PvP의 모든 관계/투사체, 임의 지형, 장시간 반복 성능까지 검수한 것으로 확장하지 않음. 기존 중앙 GameTest 결과는 master 소유이며 여기서 재실행하지 않음.

결론: 최종 패키지 진행 가능. 추가 scoped delta 0. 이후 개선 backlog에는 지속 양손 접촉 측면 검수, 화염파 옆 시점 실루엣, Ward 격자 단순화를 남길 수 있음.
