# W230 헌터 R1d 원본 검수 반환

- 동결 revision: visual-r4, 기준 fixture-r3. 슬롯 owned runtime/문서2개만 변경. GameTest6개/JSON4개 그대로.
- 확인 문제: Gathering 착탄 후에도 손 지팡이가 잔류. 원본 cast-sample-02/05/07. throwStaff()에서 master releaseHand(owner,path) 호출1개 추가.
- 필요한 shared API: ClassAbilityEffects.releaseHand(ServerPlayer,String). player/path 일치 presentation에만 released를 유지하고 BM 손/fallback prop를 cleanup까지 비운다. 실제 인벤토리 보존. EMPTY superItem 금지(실장비 복구이기 때문).
- Gathering embedded-after-lightning의 지면 식립은 정상. 비행축은 근거리 즉시 착탄으로 분리 확인 불가. 투척 후보5틱·충돌·피해·필드·공유 회전 변경 없음.
- Barrage 원본01/02/08/10/15에서 3인칭 rig가 보이지 않음. cameraIsPlayer=false metadata와 실제 PNG를 구분하며 모션 통과를 주장하지 않음. master 짧은 재캡처 필요.
- Spectral start05에 쌍칼, 약공격1/2에 자세 확인. heavy04/air04는 rig 미표시로 손·공중 자세 판정 제한. 임의 수정 없음.
- Storm start03/throw2-06/throw3-09에서 동작·피격·복귀 확인. 후속 손 단검은 charge/회오리 구간과 구분 근거가 부족해 수정하지 않음.
- Java25 parse-only PASS이며 compile/runtime 재검증이 아님. 중앙 server-r2 Hunter6/6 PASS는 master 확인의 기존 revision 결과.
- R2: 투척 전 지팡이, 발사 후 빈 손 유지, field 식립/지속, cleanup/장비 복귀. 추가 원거리 축 이미지와 Barrage 3P 필요.

CAS delta: /private/tmp/destiny-w230-hunter/delta-visual-r4.json
Payload: /private/tmp/destiny-w230-hunter/payload/
Patch: /private/tmp/destiny-w230-hunter/visual-r4.patch
