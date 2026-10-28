# W230 Titan R1d 실제 화면 검수

검수 입력: `/private/tmp/destiny-w230-native-r1d/r1-cast-contact.png`, frames PNG, sequences 캡처 tick, oracles parsed 상태. 제품 수정 0, main/build/game 실행 0. slot4와 main TitanExpandedSupers SHA 일치: `b5f809b2c487b469ee0334cc8fc20ddcb0d7fe6a446066937813c79016acfa05`.

## 범위 내 런타임 delta

`changed_paths=[]`. 현재 증거로 확정된 Titan gameplay runtime 결함은 없음. 기존 frozen R1b manifest/payload 유지. 아래 애니메이션 피드백은 다른 담당자 소유로 직접 수정하지 않음.

## 화염파 방향: fixed-yaw 의심 재현 안 됨, 임의 방향 화면 검수는 미완료

main/slot 모두 TitanExpandedSupers.java:320 에서 `Motion.horizontalLook(owner)`로 방향을 채취하고 :323 에서 `rotationTo(+Z,direction).rotateY(PI)`를 설정함. 따라서 yaw 설정 자체 누락이라는 초기 의심은 현재 코드와 다름. art CANONICAL_CONTRACT.md:15의 +Z 모델과 NONE 네이티브 Y180 보정을 반영한 구현임. 중복 회전 추가 금지.

R1d heavy 캡처 00~06은 모두 yaw=0. oracle에서 attack2 pending=true → waves=1/pending=false 전이가 확인됨. 화면은 플레이어/대상/화염에 가려 모델 앞뒤 식별이 불충분함. 이 자료만으로 arbitrary yaw 시각 검수를 통과했다고 표시하지 않음.
R2 권고: 열린 평지, 대상 없이 yaw90 또는45에서 heavy 1회. wave 생성 후 옆으로 이동하거나 관찰자 측면 프레임 확보. 모델의 길이축/진행축/앞뒤와 실제 파티클 진행이 일치하는지만 확인. 제품 회전 delta는 현 단계 없음.

## Maul 양손/공격: animation 담당자 피드백

cast 06~08에서 오른손과 망치 손잡이는 연결되어 보이고 이중 망치 없음. 왼손은 후방 카메라에서 몸/오른팔에 가려 계속 접촉한다고 확정하기 어려움. cast08 하나만으로 양손 접촉 실패로 판정하지 않음. `superItem(...,false)`는 올바른 오른손 장비이며 true는 양손 토글이 아니라 활 왼손 옵션이므로 변경 금지.

실제 보완 필요: light 00~05와 heavy 00~06에서 망치가 대체로 머리 위 수직 상태로 남아 light의 넓은 회전, heavy의 머리 위 들기→바닥 접촉이 약하게 보임. heavy oracle은 실제 attack2 재생과 wave 생성까지 확인되어 입력 실패가 아님. authored provisional clip의 동작 크기/prop 축 검수를 animation 담당자에게 권고. 애니메이션 소유 파일은 여기서 수정하지 않음.
- 기준 PNG: burning_maul-light-sample-01..05, burning_maul-heavy-sample-01..05.
- `w230_titan_burning_maul_attack`: 길이 .65s, 팔/전완/아이템 로컬회전은 고정이고 chest/waist yaw 위주. 실제 화면에서 큰 원형 spin이 잘 읽히지 않음. root/body sweep과 두 손 그립을 함께 유지하도록 조정 필요.
- `w230_titan_burning_maul_attack2`: 길이 .9s. 화면에서 해머 헤드가 지면 가까이 내려오는 포즈가 관찰되지 않음. 내려찍기/접촉 포즈를 명확히 하고 현재 게임 contact7tick(plus shared blend 정책)과 animation contact를 함께 검수. 다른 궁극기 cast를 공격으로 재사용하지 말 것.
- 소유 외 동작 변경이므로 runtime contact 임의 조정 없음. animation 수정 후 실제 모델 좌우 손 접촉은 측면/전방 R2 확인 필요.

## Thundercrash

cast-sample05에서 몸 주변 파란 가지형 aura 표시. cast oracle distance1→7, flight=true, clip air이며 다음 sample06 부근 impact/end_wall 전이. 비행 중 aura가 몸 주변에 붙어 있는 것은 실제 PNG로 확인. locomotion oracle은 이미 impact 후(aftershock=true, inSuper=false)이므로 지속 비행 화면으로 오인하지 않음. 현재 증거에서 aura 런타임 수정 없음. 현 자료는 짧은 직진 비행이므로 선회 중 모습까지 검수한 것은 아님.

## Ward

persistent-dome.png / move-idle.png에서 바닥 테두리와 돔 표시, 내부에서 외부 대상 식별 가능. after-cast oracle camera inactive/inSuper=false/ward=true, move 이후에도 field 유지, cleaned ward=false. 시전 뒤 1인칭 복귀와 독립 field 수명 정상. 이미지의 촘촘한 보라색 격자는 아트 외형 검토 대상으로 남길 수 있으나 scale2R=8을 잘못된 런타임 스케일로 단정할 증거는 없음. 외부 전체 반구 실루엣은 이번 내부 카메라에서 미검수.

## Fists ground-light 추가 검수

primary-damage oracle 실제 체력400→376, native 입력 후 실제 감소 확인. ground-light sample02 전진/아크 파티클, oracle body z .5→2.706으로 이동. 원본 independent weak-attack clip이 없는 현 authored/native fallback 제한은 유지.
시각 피드백: ground-light oracle clip은 idle→air→move→idle로만 보이며 별도 공격 clip 없음. 후방 PNG에서 명확한 주먹 뻗기 포즈가 잘 읽히지 않음. shared ClassAbilityEffects.attack의 clip 없음 fallback을 실제 BetterModel rig에서도 잘 보이게 할 authored fast punch clip은 animation 담당자 작업으로 권고. 원본 cast-forward를 독립 공격 원본이라고 표시하지 말 것. damage/권한/시작 gate 제품 delta는 없음.

## 첨부 비교 시트

- maul-review.jpg: 실제 PNG 중앙 crop 비교, 합성 포즈가 아님.
- thunder-fists-review.jpg: 실제 PNG 중앙 crop 비교.

다음 검증은 master 중앙 R2 소유. 여기서는 게임/빌드 재실행하지 않음.
