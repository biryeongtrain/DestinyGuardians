# W229 2차 실게임 검수

최종 제품 코드와 수정된 20클립, 일반/적군 변형을 하나의 격리 서버·Vision client 세션에서 확인했다. 능력 발동은 native 입력으로 수행했으며 서버 명령은 fixture 준비·상태 조회에 사용했다.

- 타이탄·워록의 수류탄 6종과 근접 6종은 서버 cooldown으로 수락을 확인했다. 1차에서 실패했던 동시 sneak+attack 대신 sneak 2tick 준비 후 공격했다.
- 궁극기 6종의 후방 카메라 전환·공격·직업 변경 후 정리를 확인했다. 신성폭탄은 자동 단발 cast이므로 카메라가 먼저 끝나는 상태와 시작 프레임을 구분한다.
- 타이탄 3종은 실제 전진 중 `_move`, 정지 후 `_idle`로 복귀했다. PNG에서 다리 자세가 번갈아 바뀌며, 서버 body 변위와 clip 기록이 이를 뒷받침한다.
- 새벽칼날은 발동 snapshot 대신 칼 든 대기로 복귀한다. 이동 `_move`, 점프 중 `_air`, 착지·정지 후 `_idle`을 확인했다. Daybreak 전용 idle 원본의 state 연결까지 식별한 것은 아니다.
- 방벽·균열의 실제 시전 표시를 확인했다. 일반/붉은 방벽·균열·신성폭탄의 텍스처 비교는 `enemy-variants-gallery.png`의 정적 fixture다. 실제 팀 판정, 관전자별 색 선택, 붉은 발사체 비행은 검증하지 않았다.

대표 화면은 `locomotion-review.jpg`, `class-vfx-review.jpg`다. 전체 원본 프레임은 `runtime-pointer.json`의 외부 runtime에 보존했다. 샘플 PNG로 전체 연속 영상의 FPS·모든 순간 보간을 인증하지 않는다. 오디오는 packet 연결과 실제 청취를 구분한다.

`final-neutral.json`에서 lease 비활성, heldKeys/pendingSteps 0, native 방향·점프·sneak/sprint 해제를 확인했다. 서버/client 소유 wrapper는 모두 exit0으로 종료했고 포트 8102/25611도 해제됐다. 별도 48시간 caffeinate PID79904는 유지했다.
