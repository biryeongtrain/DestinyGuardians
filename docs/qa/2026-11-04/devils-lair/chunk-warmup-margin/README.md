# 구역 도착 시 서버 정지 완화: 시야 거리 청크 사전 준비

1차 3인 실행에서 RY→RF 이동 직후 `Can't keep up` 경고가 한 번(2.1초) 나왔다. 2차 실행의 JFR에서 같은 전환 구간(14:11:39–14:11:50)의 Server thread 샘플 141개를 보면, 가장 많은 46개가 `ChunkMap.createEmptyChunk → ProtoChunk → ChunkAccess.replaceMissingSections`였다. 세 명이 동시에 도착하면 템플릿 경계 밖이면서 시야 거리 10 안에 있는 빈 청크가 한꺼번에 서버 스레드에서 생성된다. 기존 `DevilsChunkWarmup`은 템플릿 경계 안의 청크만 미리 준비했다. 1차 실행 때는 스왑이 14–15GB였으므로 이 생성 비용이 2초까지 늘어난 것으로 판단한다.

## 변경
- `DevilsChunkWarmup`에 여백 파라미터를 추가했다. `DevilsMaps.begin`은 `warmupMargin(view distance) = clamp(view+1, 0, 12)`만큼 템플릿 둘레 청크도 기존과 같은 방식으로 준비한다. 틱당 최대 8개를 요청하고, 공유 빌드 예산을 지키며, 세션 정리 때 자기 티켓만 해제한다.
- 시야 거리 10 기준 준비 열 수는 RY 870, RF 812, BL 930, SP 812다. 인접 구역의 원점은 512블록 떨어져 있으므로 여백 영역이 서로 겹치지 않는다. `DevilsMapsTest.arrivalViewRadiusIsWarmedWithoutReachingAnotherZone`가 이를 검사한다.

## 결과
- devils 단위 테스트와 jar 빌드가 통과했다.
- 3인 실행으로 BRIEFING부터 COMPLETE까지 456초 동안 진행했다(`phases.json`). 서버 시작 직후를 빼면 `Can't keep up` 경고가 없다.
- 이동 4초 뒤의 `tick query`는 RY→RF P95 8.0ms/P99 13.7ms, RF→BL P95 2.6ms/P99 26.0ms, BL→SP P95 4.6ms/P99 12.1ms다(`server-excerpt.txt`).
- 백그라운드 클라이언트 FPS는 29–30이다.
- 2차 실행에서도 정지가 재현되지 않았으므로, 이번 결과만으로 원래 정지가 다시 나지 않는다고 확정할 수는 없다. 원인으로 확인된 청크 생성 작업을 도착 전으로 옮겼다는 근거로 남긴다.
