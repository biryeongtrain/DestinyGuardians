# R1d 실제 화면에 근거한 Maul 공격 두 클립 R3

REPLACE_ONLY: w230_titan_burning_maul_attack / w230_titan_burning_maul_attack2. 원본 모션이라고 주장하지 않는 명시 authored 보완이다. 실제 R1d light/heavy PNG01..05에서 머리 위에 남는 망치와 약한 공격 궤적을 대상으로 변경했다. 출처 검수는 /private/tmp/destiny-w230-titan/R1d-visual-review.md 및 /private/tmp/destiny-w230-titan/maul-review.jpg이다.

약공격: 자루를 수평에 가깝게 눕힌 넓은 전신 회전. .65초61포즈. 로컬 root yaw는360도에서 마쳐 ready0도와 같은 방향으로 복귀한다. 강공격: 머리 위 준비에서 전방 지면 내려찍기, 접촉 유지, 회복. .9초61포즈. 원래 스킨/팔 길이를 보존하고 양손 손목을 자루 +Y축의4raw 간격 목표점에 IK로 배치한다. 임의 팔 회전을 넣은 뒤 정적인 IK로 덮어쓰던 기존 문제를 제거했다.

현재 TitanExpandedSupers.Maul의 light_contact_ticks6 / heavy_contact_ticks7과 PlayerAnimations의 시작 보간1틱을 읽어 확인했다. 클립 접촉 .25초(5틱)+1=6틱 / .30초(6틱)+1=7틱이며 기존 전체 길이13+1=14틱 /18+1=19틱을 유지한다. 피해/게임플레이/아트는 변경하지 않았다. 61포즈에는 정확 접촉시점의 키를 포함한다.

CAS 기준 R2 full SHA7edd53...의68클립이며 총수는68을 유지한다. Fists authored 약공격 포함 나머지66클립은 deep-equal이다. 원본 시전 및 source library는 변경하지 않았다. full resource 또는 REPLACE_ONLY 두 클립 delta를 master가 병합한다. 새 설치 식별자 제안 guardian_classes_w230_r3. install-if-absent 캐시를 고려해 master가 실제 MODEL_NAME을 정한다.

기본 오프라인 포즈/IK 확인만 수행했으며 중앙 build/game/CU 실행은 없다. 실제 prop display transform, 양손 접촉과 공격 가독성 확정은 master native R2에서 한다. 봉인 후 추가 전수 검사/렌더를 진행하지 않았다.
