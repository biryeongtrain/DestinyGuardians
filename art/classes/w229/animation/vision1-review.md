W229 1차 native 검수 반환 — R2 수정 근거

5계열의 start/attack contact sheet와 sequence JSON을 읽기 전용으로 검수했다. 총10개 sequence의 이미지 해시·client tick bracket은 vision1-frame-evidence.json에 있다. TitanArc는 R1 source clip 부재로 원본 모션 적합 판정 대상이 아니다. master의 6종 native 시나리오 통과 보고와 아트 적합 판정은 구분한다.

확인한 결함: Titan Solar/Void의 fullbody ready snapshot으로 이동 시 다리가 고정된다. Daybreak는 cast frame28을 idle로 되돌려 start의 낮아진 회복 자세에서 들어올린 준비 자세로 재전환되며 이동도 고정된다. 따라서 blanket 양호 판정을 하지 않았다. R2는 Daybreak idle을 별도 sword-catch 루프로 교체하고 move/air를 추가한다. TitanArc도 source 없는 authored fallback 두 개를 추가한다.

시전·공격: Hammer crouch/raise/throw/recovery, Shield left-hand carry/throw, Daybreak right-hand slash, Stormtrance 전방 양손, Nova 전체 cast의 큰 단계와 좌우/축은 원본 retarget storyboard에 대응한다. 해상도·FX가 허용하는 범위에서 손에 붙은 prop shaft/socket의 뚜렷한 분리나 단독180도 flip은 확인되지 않았다. 개별 손가락 접촉을 판정할 수 있는 rig는 아니며 sparse PNG로 연속 보간/모든 축을 수락하지 않는다. Shield attack07→08 deep crouch→09 carry는 경계 재검수 대상으로 기록하고 attack 원본을 임의 수정하지 않았다.

Hammer attack03/04에서 prop이 비고05에서 돌아오는 구간은 숨김/재장착 창과 정성적으로 맞지만 정확 tick6/10 증명은 아니다. source startFrame15 thermal_hammer_spawn 오디오 marker는 15/30=0.5초=10clip tick, Blender f16이다. 적용은 product provisional cosmetic cue이며 mesh spawn/damage 해독으로 승격하지 않는다. 기존 start/attack contact:null 및 kinematic productProvisional 값은 유지했다.

Nova는 sequence 이름 super-start의 실제 화면에 _attack 전체 cast가 있다. 이후 super-attack capture의 vanilla 자세와 camera 잔류는 master가 명시한 현재 설계다. 이를 누락 idle/end 결함으로 처리하지 않았다. 첫1인칭→limb camera 전환도 clip key 자체의 flip 근거가 아니다.

보간 한계: R1 source midpoint 최대 방향8.682도/world회전8.726도/floor0.391 model unit의 설명은 원보고서에 보존한다. 특히 Daybreak start f11~12, Sentinel start f16~18은 빠른 구간이다. 약4clienttick 간격·20~26fps 수준의 이미지와 서버 phase telemetry 부재로 60fps 연속성, 접촉 tick, source frame 정확 동시성을 인증하지 않는다. cast/attack 수정 없이 R2 movement와 idle 경계를 같은 배치에서 재검수한다.

2차 Vision 우선순위: Daybreak 장착 sword의 바른 carry와 start→idle→move→air→idle, Titan Solar/Void 실제변위 중 leg swing과 idle 복귀, TitanArc authored ready/move, 이동중 start/attack 우선권, 벽에 막힌 입력에서 idle 유지. 가능하면 동일 loop2회 이상의 정면/측면 PNG로 관절 flip·경계·발 접지·장비 파지를 비교한다. 게임/서버/CU는 master만 운영한다.
