# W160 Mori 진단과 Ammit crouch 조사

- 제품 변경: 기존 OP presentation-status의 readonly `mori`/`moriPips`. 획득·장전·렌더 상태를 조회가 만들어내지 않도록 실제 earned/unearned GameTest로 확인.
- Ammit 양손 crouch 때 바닐라가 팔 xRot에 추가하는0.4rad를 기존 standing 보상에서 누락한 근거 발견. 그러나 ADS selector가 남는 release frame에서는 standing이므로 한 정적 회전으로 양쪽을 고치지 않는다.
- `art/weapons/w160/ammit-pose.json`의 후보는 **비활성**이며 원본427모델·FP/geometry/UV/장전/swap/sight는 그대로다. 현재 front+side/어깨 접점 수락 없음.
- 26.3 conditional/select registry에 없는 entity_properties/pose JSON을 지어내지 않는다. 후속 구현은 actual crouch와 ADS progress를 분리해 서버 소유 presentation 상태를 수송하고, unrelated CMD 보존·해제/교체/lifecycle를 테스트한 뒤 대표 native 전환을 본다. local keybind만 읽는 조건으로 다른 플레이어 3인칭을 보정하지 않는다.
- [단계별 검증과 제한](../qa/2026-10-26/w160/README.md). JUnit23/Python12/serverGT18, native0. CU preflight 가용성 문제이며 Mac잠김 판정 아님.
