# 실제 화면 회귀 검수

2026-11-10, 격리 서버 `127.0.0.1:25642`와 전용 Fabric 26.3 Vision 클라이언트에서 확인했다. 전역 view32 / simulation6, 탑의 실제 view8이다. `visionControlBackground=true`와 backgroundActive를 확인했으나 캡처 시 windowActive도 true였으므로 비활성 창 입력까지 검증했다고 주장하지 않는다.

- [ADS](visual/scale-ads-1.png): 네이티브 좌클릭으로 조준 모델로 전환됐다.
- [자동 장전](visual/scale-fire-3.png), [복귀](visual/scale-fire-5.png): 네이티브 우클릭 유지 중 탄약 11→0, 장전 모델과 손, 이후 복귀 모델·탄약6을 확인했다. Q 수동 장전 검증은 아니다.
- [수류탄](visual/scale-grenade-1.png), [복귀](visual/scale-grenade-2.png): 네이티브 F로 팔과 수류탄, 무기 숨김·복원 및 재사용 대기 HUD를 확인했다.
- [관전자 장비](visual/scale-observer.png): 정규 무기를 방어구 거치대 손으로 복사해 non-self 장비 패킷 경로의 금색·보라색 Austringer가 실제 렌더링되는 것을 확인했다. 거치대는 제거했다.
- [3인칭](visual/scale-third-clear.png): 무기와 HUD가 표시된다. 최초 캡처는 앞의 거치대에 가려 수락 증거에서 제외했다.
- [체력 비율](visual/scale-health-partial.png): max-health를 일시적으로40으로 올린 fixture에서 체력 막대가 줄어든 것을 확인하고20으로 복원했다. 실제 피해 이벤트나 2틱 치유 보간 시간의 증거는 별도 native 검사다.
- [타이탄 궁극기 카메라](visual/scale-titan-camera-1.png), [자연 종료 후 복귀](visual/scale-camera-return.png): Shift를5틱 먼저 유지한 뒤 F를 입력했다. 실제 camera entity 전환, 주변 지형과 캐릭터 및 종료 후1인칭 복귀를 확인했다.

각 PNG는 전후 상태 JSON과 SHA256 manifest가 있다. `*-input.json`은 실제 입력 영수증과 lease 해제 결과다. 최종 leaseActive=false / heldKeys=[] / pendingSteps=0을 확인했다. 전용 client/server와 coordinator, 소유 caffeinate가 종료됐고8102/25642 listener가 없음을 확인했다. 일반 프로필·인증·운영 서버 설정은 변경하지 않았다.

첫 연결은 전용 autohost forced_address의 `http://` 누락으로 INVALID_URL이었으며 설정을 고쳐 재시작했다. 제품 변경의 실패나 성공으로 세지 않는다. 동시에 Shift/F를 누른 첫 시도는 수류탄이 발동해 사전 Shift 입력으로 수정했다. 원래 입력 기록도 남겼다.

이 검수는 단일 렌더링 클라이언트의 대표 회귀 확인이다. 입력 구간 FPS 스냅샷47–60은 프레임 시간 벤치마크가 아니다. 청취,30개 렌더링 클라이언트, 운영 Windows/WAN, 모든 무기·궁극기 아트는 미검증이다. 탐색 중 황금총은 일반 Austringer와 황금 prop가 함께 보여 전체 황금총 파지·아트 수락으로 세지 않았다. 해당 자산/궁극기 구현은 이 최적화 배치에서 변경하지 않았다.
