# Titan R2 최소 delta

TitanSuper.java 한 파일만 CAS 교체. main/build/game 미실행. 수정 후 독립 javac exit0. shared phase helper 변경 불필요.

공중 primary에서 ground attack helper 대신 원본 shared air idle 사용. 실제 supported 착지에만 원본 land(80A8AD9C)를 재생하고 해당 duration+blend 동안 공격/이동 회복 gate. 기존 하강속도, 20tick 공중 대기 제한, 피해량/피해모드/세션정리 보존. windup 중 먼저 착지해도 모션만 land로 변경하고 기존 ground payload 유지. onGround flag만으로 공중 피해가 발생하지 않도록 기존 startup supported() 사용. 지상 punch는 master R2 authored clip 사용하며 원본이라고 표기하지 않음.

R1 검수: ../R1d-visual-review.md. 화염파 yaw delta없음, 임의방향 측면 검수는 R2 필요.
