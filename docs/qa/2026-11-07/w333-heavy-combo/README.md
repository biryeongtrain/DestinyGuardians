# W333 근접 궁극기 입력/강공격

Arc Staff와 Spectral Blades는 좌클릭 약공격 / 우클릭 강공격이다. Shift를 눌러도 좌클릭은 약공격이다. 강공격은 실제 수락 시점부터60서버틱(3초) 독립 쿨타임이며, 일반 공격은 앞 동작의 원본 종료 시점부터 가능하다. 회복 마지막1–2틱의 다음 입력만 한 번 버퍼링한다. 표시 보간2틱/exit blend를 게임플레이 공격 잠금에 추가하지 않는다. Arc Staff 회피는 기존40틱(2초) 독립 쿨타임을 유지한다.

기본 클라이언트 air/block/entity 우클릭은 DEFAULT 이전의 공용 InputRouter 콜백을 통해 해당 세션만 opt-in한다. 일반 무기/음식/활/다른 궁극기/offhand/GUI는 기존 경로를 유지한다. 기존 GCB KEY_USE도 같은 서버 경로를 이용한다. 실제 GCB 클라이언트 네트워크 검증으로 계산하지 않는다.

## 실제 서버 결과

`rmb-gametest.xml`: 제품2개+프레임워크1개3/3통과. 실제 Fabric EVENT.invoker air/block/entity/custom-phase, 기존 GCB onKey entrypoint, Shift+좌클릭, 회복 종료 연계, 강공격 T59거절/T60수락, 약공격과 강공격 독립, 보통 총기 탄약 보존, offhand/GUI/일반 아이템/태양 궁극기 opt-out, 두 live target에 공격별 한 번의 피해와 dead-owner 거절을 검증했다.

초기2실패는 공격 전 target HP1000→999였다. 초기 로그에 DamageSource/BB가 없어 원인을 inWall로 확정하지 않았다. 목표를 caster의 순간 Y로 매 틱 이동시키던 fixture를 명시적인 floorY+1.25와3칸 빈 머리 공간에 고정하고 X/Z만 따라가도록 수정했다. noCollision/isInWall/HP1000/once/reach 검사를 엄격히 유지하고 실패 시 BB·eye·바닥/주변BlockState·DamageSource를 출력하도록 했다. 수정 후 실제 서버2개가 통과했다. 체력을 보정하거나 무적/NoPhysics로 통과시킨 검사가 아니다.

초기 통합27개 중 통과25개와 위 수정2개로 이번 관련 제품26개가 실제 서버에서 통과했다. 프레임워크 항목은 제품 수에서 제외한다. 최종 본별 미술 변경의 검사와 native 검수는 아래 최종 결과에 추가한다.

## 출처/사용자 조정

Arc 강공격은 지상933/공중985 원본이다. 접촉 프레임은 첫 유효 sweep에 맞춘 임시 Minecraft 판정이며 추출한 Destiny 피해 이벤트가 아니다. 일반 heavy DDC 비율79/54를 기존 Minecraft 약공격16에 적용한 값은 현지 환산이다. Palm Strike(L-L-H)2950은 별도 원작 콤보이므로 일반 heavy에 사용하지 않는다. Spectral 기존11/18 수치는 유지한다. 상세 `ddc-findings.md`.

사용자가 사운드 동기화를 위해 배속 변경을 거절했다. 제안했던 공격1.25/시전1.15 배속 코드는 main에 통합하지 않았으며 원본 길이/접촉/사운드를 유지한다. 현재 수정 방향은 원본에서 빠졌던 본별 이동·비틀림 복원이다.

최종 수락은 W334의 본별 이동 복원과 W335의 기본 클라이언트 빈손 우클릭 전달 수정까지 포함한다. 원본 배속 유지, 실제 Gradle build/단위31개 통과, 관련 실제 서버 제품26개 통과. 기본 클라이언트에서 두 궁극기 각각 지상5회 연계와 공중 우클릭1회·Arc4방향 회피·장비/카메라/입력 복귀를 master가 확인했다. 상세 한계와 증거는 ../w334-articulated-super-motion/native-acceptance.json 및 ../w335-super-rmb-carrier/README.md.
