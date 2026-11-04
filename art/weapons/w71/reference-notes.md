# W71 — Long Arm 반복 장전 모션의 출처와 한계

[W48 영상 근거](../w48/reload-policy-evidence.json)와 동일한 EndgameXpress의[Long Arm 플레이](https://www.youtube.com/watch?v=XPB6leAQKuQ)(2022-12-18)를 다시 확인했다. 원본 private영상·info SHA를 유지한다([이번 관측](references/gameplay.json)).
처음 input fast-seek는 reference picture 오류와 HUD시간 불일치를 보여 버렸다. **처음부터 decode 후 output seek**한 프레임으로10.0..10.2초의 총 올림/기울임,10.2..13.4초의 유지 자세/반복 손 접촉을 확인했다. 13.6초에는 스킬로 중단되어 자연 완료 자세는 측정하지 못했다.

원작은 손으로2발을 넣는다. 이번 구현은 **총 몸체의 올림·기울어진 유지·삽입 접촉에 따른 작은 반응·복귀만** 작성했다. 손/실제 카트리지 소품/움직이는 레버/원작 rig는 포함하지 않는다. 모든 cube/UV/texture를 보존한256큐브 모델이므로 추가 탄약 cube를 억지로 더하거나 body 디테일을 지우지 않았다. [원본 감사](references/original-model-audit.md)에서7bone기계rig는확인했지만저장animationclip은없다. W30의lever접촉36cube중22개가고정body와섞여있어일부만움직이면찢어진다. 실제source쌍Bullet메시는있지만현재cube에서는모두mixed여서별도완전카트리지소품으로사용하지않았다.

initial/loop/return 각21샘플의 수치·시간은 작성 근사이며 원작 애니메이션 추출/정확한 곡선/IK가 아니다. loop 경계는 유지 자세로 연결하며 매2발마다HIP로 되돌아가지 않는다. return6tick은 원작 측정값이 아니라 **게임플레이를 막지 않는 외형 복귀 정책**이다.
실제 20tick 첫2발/13tick 반복2발/14발기본탄창 및취소 후 기삽입탄 유지 정책은 W48을 그대로 사용한다. 영상의16발 탄창이나 미상버프를 가져오지 않는다.

[Blockbench 비교](../../../docs/qa/2026-10-24/w71/long-arm-phases-contact.jpg)는 별도 inspection프로젝트의 raw mesh에 native ItemTransform을 적용한 offscreen render이다. 종류 공통bbox로 프레임간 변화를 보존한다. 실제 Minecraft의 투영·손·FOV·픽셀/클리핑을 검증하지 않는다. 원래 unsaved3프로젝트/카메라/mode를 확인해 복원했다([복원](../../../docs/qa/2026-10-24/w71/blockbench-restoration.json)). 추가 Minecraft/Vision client는 실행하지 않았다.
