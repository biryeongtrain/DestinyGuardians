# W254 수류탄·근접능력 손 겹침 수정

상태: 수정·관련 자동 검사·Danmo 실화면 검수 완료. 운영 서버 재개 완료.

1. 실제 Danmo4GB/OpenGL+Vision 기준 화면을 먼저 확인했다. 수류탄 age4·14에서 HUD 총은 숨겨져 있지만 별도의 바닐라 오른손이 표시됐다. BetterModel 소유자 슬롯/장비 숨김이 비어 있는 아이템을 전달해 바닐라 맨손 렌더 분기를 타는 경로를 확인했다. 회복 age18에는 cached lastGun도 재표시됐다.
2. 수류탄에 기존 SwordHandPackets의 소유자 논리 아이템 보호를 재사용한다. 실제 인벤토리를 비우지 않고 nonempty·보이지 않는 논리 carrier를 유지하며, observer BetterModel 장비 숨김은 유지한다. grenade를 ownsSwordHand에 섞지 않아 투척 HUD는 유지한다.
3. FP 수류탄은 기존 원본 FK 투척 팔 두 세그먼트만 표시하고 반대쪽 파지 팔을 내린다. 총은 전체20틱 동안 숨기고 종료 후 현재 선택 무기와 파지 팔을 함께4틱에 걸쳐 올린다. cached gun을 중간 회복에 다시 표시하지 않는다. 원본 리그·61pose·투사체 시점은 변경하지 않았다.
4. 헌터 근접은 별도3P 클립 동안 고정 FP 총·파지 팔을 숨겨 native 맨손 하나와 겹치지 않게 한다. Arc의 EMPTY는 live weapon 복원 대신 explicit bare hands를 사용하고, Solar/Void prop도 contact 이후 양손 bare를 유지한다. 클립 종료·취소 시 현재 장비로 복원한다. 손가락·새 임의 리핑 모션을 추가하지 않았다.
5. 헌터 근접 클립 중 사격/ADS를 막아 보이지 않는 무기로 발사하는 경로를 막는다. 타이탄·워록 근접은 현재 별도 limb/FP 팔 모션을 시작하지 않는다. 따라서 동일3중 팔 경로는 없으나 전용 시전 모션 구현 완료로 간주하지 않는다. 직업능력 방벽·균열 모션도 별도 미구현 범위다.
6. 읽기전용 검수 worker Curie는 main/SSD/worktree·Minecraft를 수정/조작하지 않고 원인·lifecycle를 독립 검토했다. master만 공유 표시 경로·자동검사·게임 검증을 소유한다.
7. 첫 컴파일은26.3 swing 메서드의 인자 변경을 놓쳐 실패했다. 기존 사용례의 SwingAnimation/boolean 인자로 수정 후 재검사한다. 이 실패를 테스트 통과로 세지 않는다.

기준 증거: `/private/tmp/destiny-w254/qa/`, 수정 전 바이트: `/private/tmp/destiny-w254/before/`. 운영0명 확인 후 콘솔save-all flush/stop ACK와 종료0을 확인하고 빌드했다. 검수 종료 후 운영서버를 재개한다.

## 추가 확인 — 스킨 어깨/손목 방향

사용자의 스킨 방향 지적을 받아 native26.3 `SkullModel`, `ModelPart.Cube/Polygon`, `PlayerHeadSpecialRenderer`와 기존 W204 팔 배치를 대조했다. 일반 무기 팔은 native Y=-0.5가 proximal, Y=0이 distal인데, 수류탄 FK와 공통 shader는 반대 규약을 사용했다. shader 단독 flip으로 끝내면 투척 팔은 다시 뒤집히므로 다음을 함께 수정한다.

- 공통 shader side V 반전 제거, elbow cap discard 방향 수정.
- 투척 FK는 +Y를 shoulder→elbow / elbow→wrist로 회전하고 distal에 원점을 둔다.
- 투척 진입 blend의 관절 추출과 수류탄 prop 부착점을 같은 규약으로 바꾼다.
- 원본 FK 좌표·61pose·타이밍·일반 무기 파지 위치는 보존한다.
- QA 전용 `destiny.qa.skinLandmarks=true`는 default skin에 shoulder 빨강, upper 노랑, elbow 초록, wrist 파랑을 덧씌워 실제 PNG에서 검수한다. gametest source set에만 존재하며 운영 팩에는 포함하지 않는다.

## 검사 이력

- targeted-r3: 단위18/18 및 compileGametestJava 통과.
- R1 Danmo4GB/OpenGL+Vision: 3직업 F 투척·헌터3속성 sneak+attack 입력을 기록했다. grenade-age4에서 투척 팔 한 개와 prop만 보이며 여분 native fist와 gun이 사라졌다. 헌터 Arc 중에도 고정 gun/grip이 사라졌다. Solar 일부 frame의 근접 물체는 추가 검수 중이다.
- R1 GameTest: 기존 투척/취소2개는 통과. 신규 HUD 검사는 연결되지 않은 TestPlayers가 PlayerList END tick을 받지 않는 fixture 문제로 실패했다. 실 updater를 test tick에 명시 호출하고 pack graph 준비 후 실행하도록 고쳤다. 아직 이 수정의 런타임 결과를 통과로 간주하지 않는다.
- full-gate: 전체2198 중2194 통과,4실패,0error/skip. 기존 Austringer/Mindbender/WeaponSurfaceW115/WeaponSilhouetteW112 자산 일치 실패4종이며 이번 수정에서 새로 발생한 실패는 없다. 전체 gate 성공으로 표기하지 않는다.

## 최종 수락

- targeted-r5: 단위20/20, compileGametestJava 성공. R4의 QA 도우미가 존재하지 않는 PackResource.fromBytes를 사용한 컴파일 오류는 실제 API `of(byte[])`로 수정했다. 실패 로그를 통과로 세지 않았다.
- R2 GameTest5/5: 투척1회 방출, 하위직업 변경 취소, 권위 인벤토리 객체 보존+총/반대팔 숨김, 취소 후 현재 무기 복구, 헌터 근접 중 총/고정팔 숨김·사격 금지·복귀.
- R2 native6/6: 세 직업 F 투척과 헌터 Arc/Solar/Void sneak+attack은 실제 Vision 입력을 거쳤다. 각각 leaseActive=false, heldKeys=[]로 해제됐다. 타이밍 고정 age1/2/4/8/14/18/24는 별도 server tick fixture이며 native 입력 증거와 혼동하지 않는다.
- 실제 PNG: `grenade-age4.png`는 어깨 빨강→상완 노랑→팔꿈치 초록→손목 파랑, prop이 파란 손목에 닿는다. age1 진입·age18 복귀도 손목 방향 유지. `hunter-restored.png`의 손잡이에도 파란 손목이 온다. `arc-melee-sample-04.png`는 native 팔 하나만 남는다. 캡처에 노출되지 않은 어깨 cap까지 실화면에서 확인했다고 주장하지 않는다.
- Curie가 수정된 endpoint/shader/blend/prop 규약과 R2 실제 PNG를 재검토하여 겹침/세로 UV 수정에 blocker 없음으로 반환했다. worker는 게임 입력/빌드를 하지 않았다.
- native 중립 확인 후 QA client만 SIGINT로 종료(-2), fixture save-all flush/stop ACK 후 서버 종료0. 일반 사용자 프로필·스킨·SSD 원본은 변경하지 않았다.

## 남은 범위

타이탄/워록의 전용 근접·방벽/균열 limb 모션은 여전히 별도 작업이다. Solar knife가 eye origin에서 발사되어 첫 렌더 순간 카메라와 교차할 수 있는 기존 near-clip 위험도 발견했다. 이는 기존 SimProjectile/발사 원점 경로이며 이번 UV/겹침 수정에서 충돌 검사를 건너뛰는 원점 이동으로 덮지 않았다. R2 Solar/ Void 후속 프레임은 정상 발사체가 앞쪽으로 이동하는 것을 확인했다. 이를 완전 해결로 표시하지 않는다.

커밋은 관련 파일만 선택한다. WeaponRuntime의 기존 Cornered 미커밋 변경은 제외한다. HunterAbilityVisuals의 기존 미커밋 시전 helper와 미추적 WeaponOutboundPresentation은 이번 시전/소유자 projection 변경의 전제이므로 해당 파일의 현재 구현을 포함한다. 다른 기존 dirty/untracked는 보존한다.

## 배포 상태

assemble 성공. 운영 runServer에서 Done·BetterModel startup·Profile skin view·Polymer pack success와 live list ACK를 확인했다. `192.168.35.237:25565`, online-mode=true, andlist OP4 유지. 운영 팩의 수정 entity shader를 직접 확인했고 QA 색분할 기본 스킨18종 override는 포함되지 않았다. 사용자 일반 스킨이 적용된다. 운영용 JAR에도 QA SkinLandmarks 도우미가 없다. 격리 QA coordinator는 종료했고 별도 사용자48시간 caffeinate는 건드리지 않았다.
