# W221 — 샷건3·로켓·리볼버 장전

상태: W221 범위 수락. 원본 Blender → 61포즈 → FIRST Vision → 동일5 worker 피드백 → SECOND Vision 완료. 전체 무기/HUD 목표는 진행 중.

대상: Ikelos SG, Mindbender’s Ambition Adept, Parcel of Stardust, Pyroclastic Flow, Seventh Seraph Officer Revolver. 실제 원본 Blender를 별도 headless 프로세스에서 먼저 평가하고 source-review.json·source-sheets에 남겼다. 무기 메시·카메라·손가락 IK가 없는 ARMATURE 원본이며 무기별 전용 selector 복구로 주장하지 않는다.

샷건3종은 각 초기/반복/복귀61포즈(CMD4), 나머지는 전체 장전61포즈(CMD1)다. 샷건의 source .35 포즈 유지와 삽입 접촉은 기존 W208 방식의 명시적 보정이다. 추출된 개별 shell 이벤트가 아니다.61포즈는 연속60fps 인증이 아니다. 게임 탄약·장전 타이밍·W219 소리 취소 동작은 바꾸지 않는다.

5개 독립 worker가 각3파일을 반환했다. master가 shared routing·생성·검증·Vision을 소유한다. 최신 지시에 따라 worktree는 고정 슬롯으로 보존한다. 재사용·커밋 절차는 fe0aa96에 기록했다.

단계 기록: [step-log.md](step-log.md). 검수한 W221 변경을 별도 커밋한다. 기존 누적 미커밋 작업과 대용량 QA 캡처는 무분별하게 포함하지 않는다.

검증: targeted16/16 + assemble, native18개씩 두 차례 총36개. SECOND는 문서만 바뀌어 동일 JAR를 재사용했고 테스트16개를 중복 실행한 것으로 세지 않는다. 실제 확인 이미지와 한계는 [visual-review.json](visual-review.json)에 기록했다. 샷건 탄 접촉은 일부 가려지며 리볼버 왼손은 낮거나 화면 밖에 놓이는 원본 포즈가 있다. 연속60fps·음향 청취·모든 시점 검증은 주장하지 않는다.
