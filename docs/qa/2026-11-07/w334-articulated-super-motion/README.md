# W334 원본 속도를 유지한 본별 동작 복원

사용자 요청에 따라 재생속도를 바꾸지 않고, Arc Staff와 Spectral Blades 변환 과정에서 빠졌던 관절별 움직임을 복원했다. 공격1.25/시전1.15 배속 제안은 main에 통합하지 않았으며 worker의 해당3파일도 확인된 원상태로 돌렸다.

## 변경과 근거

원본72본을 분할된 Minecraft 리그로 바꾸는 기존 변환이 어깨를 고정하고 팔꿈치를 단일 hinge로 계산했다. 회전 키는 있었지만 어깨·쇄골·허리·흉곽의 원본 로컬 위치 경로가 누락되어 팔과 몸통의 동세가 줄었다. 동일한 키를 더 많이 만드는 대신 빠진 위치 채널을 기존 본에 복원했다.

- Arc: 실제 척추/쇄골→waist/chest/shoulder 경로를16u/m로 변환하고 움직인 어깨에서 IK를 다시 계산했다. 최대 로컬 이동2.634u, 팔꿈치 경로 변화3.335u. 기존 두 손목/머리의 world 위치는 float32 오차 안에서 유지해 파지와 기존 머리 여유를 보존했다. 단일 hinge의 독립 전완 비틀림 제약은 남는다.
- Spectral: 어깨/허리/흉곽 경로를 복원하고 IK·item 변환을 보정했다. 최대 어깨 이동 약2.25u, 허리1.65u. 손목/칼 world 잔차4.1e-15u, 각도1.71e-6도. 원본 axial roll은 최대 약0.32도로 작아 과장하지 않았다.
- 골반의 큰 이동은 기존 root/게임플레이 도약·돌진과 중복될 수 있어 추가하지 않았다. 리그 geometry/UUID/UV/요소 개수는 늘리지 않았다.

`timing-preservation.json`에서 두 리소스 각각12클립의 length·loop·contact/recovery·entry/exit를 이전 검증본과 master가 독립 비교했다. 배속 없음. 기존40Hz 평가/20Hz 표시 갱신과2틱 보간, 원본 사운드 재생 타이밍, 강공격60틱/회피40틱은 유지한다. 오디오 스피커 청취 수락을 뜻하지 않는다.

## 검증

원본 .blend 직접 평가와 source/before/after 그림, 원본 hash 불변은 두 작업자 manifest에 기록했다. Master도 전후 그림을 직접 확인했다. 최종 실제 Gradle assemble/compileGametestJava 및 관련 모션/시계 단위17개와 패킷 단위14개, 총31개가 통과했고 JAR의 ZIP CRC와 세 animation 리소스가 통합본과 정확히 일치한다. 실제 서버 입력/타격 회귀 결과는 W332/W333의 XML과 보고서를 참조한다.

최종 native 화면 검수 수락: 기본 클라이언트에서 Arc/Spectral 각각 지상 좌클릭3회→우클릭 강공격→좌클릭으로5회 공격을 확인했다. 공중 시작 후 점프+우클릭 단독도 각각1회 발동했고 Arc4방향 회피를 재검수했다. Master가 실제 시트와 Arc 공중 강공격 full PNG를 직접 보았다. 표시된 관절 연결·파지에서 눈에 띄는 새 분리/미싱 텍스처는 없었다. native-acceptance.json과 native/에 증거를 보존한다.

시점/장비 복귀 후 실제 crossbow 표시·cameraIsPlayer=true·usingItem=false·heldKeys=[]·leaseActive=false·HUD숨김해제를 확인했다. 활성 궁극기 중 server clear maxCount0은 실제 STICK 없음으로 답했다. 화면의 운반용 STICK은 논리 인벤토리에 들어가지 않는다.

한계: Spectral heavy는 접촉 뒤 기존 은신이 다시 적용돼 후반 몸체가 가려진다. 그 구간까지 완전히 보이는 모션으로 인증하지 않는다. Arc 공중 강공격은 과거18개source key의 머리/shaft proxy 교차가 남아 있으며 샘플 화면이 모든 프레임 무관통 증명이 아니다. 독립 전완 비틀림의 기존 hinge 제약도 남는다. Speaker청취·GCB실클라이언트·60fps 인증은 하지 않았다. 강공격 입력이 너무 이르게 간 첫 Arc native 연계는 수락으로 계산하지 않고 원본 회복보다 넉넉한 간격으로 다시5회를 확인했다. 정확한 즉시 연계/2틱 버퍼/60틱은 실제 서버 회귀에서 따로 검증했다.
