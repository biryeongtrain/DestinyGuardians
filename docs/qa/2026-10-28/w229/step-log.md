# W229 타이탄·워록 작업 기록

1. 기존3직업 enum·헌터 능력 서비스·명령과 원본 자료 위치를 확인했다. 태양·전기·공허3속성을 우선하며 추가 속성은 이번 범위가 아니다.
2. 고정 슬롯4·5를219937파일 기준선으로 갱신했고581개 변경을 각각 반영했다. 원본/dirty main은 보존하고 외부 복구본을 남겼다. 타이탄·워록 구현과 Drive/SSD 원본 조사를 병렬 배정했다. master는 공유 연결·HUD·표현·중앙 검사·Vision을 소유한다.
3. 각 worker에 배타19개 경로와 lifecycle/전투/인벤토리보존 계약을 전달했다. 실제 원본이 없는 모션을 헌터 애니메이션으로 대체하지 않는다. 수치 기본값은 출처 확정 전 Minecraft 잠정환산으로 표시한다.
4. 세 직업 공통 preset·class/slot검증·명령·lifecycle을 연결하고 새직업 전용 HUD10종을 추가했다. 기존 헌터 기본장착과 황금총1인칭은 보존한다.
5. SSD에서 망치·파수병·새벽칼날·폭풍몰입·신성폭탄72본 action자료와 Drive 정적소품3종·음원 후보를 실제 확인했다. 원본retarget와 소품아트산출을 추가 병렬화했다. Fists of Havoc는 미식별이다.
6. Computer Use에서 Finder 데스크톱 접근가능, 전용포트8102/25611 비점유와48시간assertion PID79904유지를 확인했다. 일반앱입력·설정은 변경하지 않았다.

## 7. 원본 조사 반환과 중앙 통합 준비
- 5계열 46궁극기 action과 일반 능력 후보67개를 실제 headless Blender에서 평가했다. Fists of Havoc는 미식별이다. 숫자 음원 역할은 tentative로 구분한다.
- super.fire는 실제 release/contact에서 한 번만 내도록 presentation/전투 역할을 정리했다. worker 조기 검수에 Storm 무입력 발사와 Nova 준비 구간을 전달했다.

## 8. 두 직업·원본 모션·음원 통합
- 고정슬롯4/5의 배타19개씩을 기준선 ABSENT 확인 후 통합했다. Warlock19개는 반환SHA256도 일치한다.
- source-derived14개 애니메이션(실제동작11+명시hold3),18음원매핑/17고유OGG를 가산 통합했다. 숫자파일역할은tentative이며 청취미확정이다.
- 대혼란의 주먹 원본은 사용자가 작업후 다른궁극기와함께 전달하기로 답변했다.

## 9. 중앙 컴파일 수정 및 QA 준비
- 첫 compile은 새 presentation의 구버전 swing(1인자) 호출에서 실패했다.26.3 SwingAnimation/boolean 인자로 수정했으며 리핑모션에는 바닐라 swing을 중복하지 않는다. 다음 compileJava는 통과했다.
- target-compile 첫 JSON의21tests는 이전 XML을 단순읽은 stale집계다. 실제이번검사는 실행되지 않았으며 후속runner에서 test task가있는경우에만집계하도록 수정했다.
- Computer Use로 Finder 데스크톱 접근가능/잠금해제 확인,48시간caffeinate79904유지 확인. 검증은 승인된격리profile/서버에한정한다.

## 10. 컴파일 및 자산 targeted 검사
- compileJava/assemble/compileGametestJava 완료(exit0). 리소스 전체재처리와패키징 포함209.8초.
- 실제 ClassAssetsW229Test 3개통과: 전체 스킨리그보존·애니메이터remap/61pose·없는모션대체방지·새HUD native26codec확인. 서버동작은별도GameTest진행중.

## 11. 첫 서버 동작 검사와 원인분석 병렬화
- fresh GameTest23개중12통과/11실패. Rift/방벽의 grounded/supportfixture, fakecamera40tickwatchdog, wall/aimdamage시나리오를담당worker에반환했다. 실패를통과로기록하지않으며 수정원인을분리한다.
- 원본소품3종9파일및2meleealias통합.221/342/211출력요소로상한1000이하, 원본UV를재투영한의미입체이다. 실제PNG판정은첫native세션에서진행한다.

## 12.1차 native 결과 및 사용자 추가검수 반영
- 격리native batch는궁극기6종rear camera전환/직업취소복귀,2직업class/jump,6grenade/melee입력을마쳤다. 실제PNG와상태/서버oracles를담당worker에전달했다. 서버/client소유wrapper모두0종료,lease/native중립확인.
- 사용자추가: 신성폭탄·방벽·균열전용모델과타이탄/새벽칼날이동모션. Nova38cube임시자체VFX를통합했고방벽·균열을추가아트위임했다. 기존staticcasthold의하체고정은결함으로간주하고진짜idle/이동source재탐색및별도gait분리를진행한다.
- per-instance SimProjectile.cancel 추가로궁극기flight만취소하고ordinaryflight존재시시전거절하는임시제약을제거한다.

## 13. 대기·이동 분리와 두 번째 검증 준비
- SSD 전체 source query에서 파수병 전용 sprint80A8A9AD를 식별했다. sword_catch_idle80A8B370/hammer_catch_idle80A8AD1E는 실제 별도 loop지만 궁극기 전용 연결은 미확정이다. 새벽칼날 발동 snapshot을 최종 idle로 유지하지 않으며 source 후보를 원본 Blender에서 평가한다.
- 실제 충돌 후 수평 변위로 idle/move를 선택하고 airborne은 air를 우선한다. start/attack one-shot 구간은 locomotion이 덮어쓰지 않는다. 없는 원본을 제작 모션과 혼동하지 않도록 산출 provenance를 분리한다.
- R1 melee는 동시 sneak+attack으로 서버 cooldown이0이었다. 따라서 전송 성공과 능력 수락을 구분하고 R2에서 sneak2tick 준비·근접 새 표적·서버 cooldown을 함께 확인한다.
- DDC15행의 최신 기본 cooldown/duration 근거를 확보했다. 원작 초 단위와 MC피해·거리 환산은 구분하고 담당 worker에 직접 시간값 적용을 전달했다. 단순 시간값 개별 테스트는 추가하지 않는다.

## 14. R2 통합 동결
- Titan13/Warlock12개 변경을 R1 main파일 SHA 기준선과 반환SHA를 대조해 통합했다. 1차 idle13개·start/attack/end는 보존하고, 새벽칼날 sword-catch idle 교체와 locomotion6개를 합친20클립 R2를 versioned 모델로 적용했다.
- 방벽89/균열101요소 모델6자산을 통합했다. 최종 방벽 canonical은 단위1x1x1이므로 master가 구 thin-plane scale공식을 실제폭/높이/두께 직접scale로 보정했다. 균열은diameter16/anchor8,수평scale8로 반경4를 맞춘다. 두 모델은 자체 제작 임시VFX다.
- TitanArc authored 임시ready에 실제무기 표시가 남지 않도록 empty-hands override를 공유 표현에 추가했다. 원본Fists attack/start를 추가했다고 주장하지 않는다.
- 신규직업 궁극기 cooldown 메타데이터가 기존공유180초passive경로에 쓰이지 않는 점을 수정했다. Titan/Warlock은 장착궁극기 tuning의tick값을 기본충전에 적용하고Hunter기존경로를 보존한다. kill추가충전/스탯환산과 기본DDC시간은 구분한다.
- source/locomotion공유Java compile/assemble/compileGametestJava는exit0였으나 이후통합R2·passive연결변경은별도다. 현재 R2자산/컴파일 targeted 검사 진행중.

## 15. R2 서버 실패3개 원인 분리 및 추가 적군 자산
- R2 서버20/23통과. 나머지는 표적Husk 몸이벽에0.3block겹친2개 fixture와 상향투사체가높이8의GameTest BARRIER천장에충돌하는1개 fixture였다. 전자는 피해량집계/실제LOS/몸충돌 분리근거를남기고벽밖이면서피해반경안으로이동했으며HP100기대는유지한다. 후자는해당시나리오만skyAccess=true로변경하고flight공존·개별취소기대를유지한다.
- R2다리parent 가정오류4clip을worker의별도CAS수정본으로통합했다. 이미생성된모델보존을위해설치ID r3로변경했다. 기존16clip은불변이다.
- 사용자추가요청: 향후PvP용붉은적군텍스처. 타이탄·워록과기존헌터능력/VFX를병렬아트범위로추가했고별도파일로원본geometry/UV/alpha를보존한다. 실제PvP팀판정이나관전자별표시가이미완성된것으로보고하지않는다. presentation용명시boolean선택API만추가한다.

## 16. 적군 변형 통합 및 R3 서버 통과
- 타이탄/워록20자산과헌터37자산을반환manifest SHA/기존sourceSHA와대조해가산통합했다. 헌터8 enemy BM모델도설치목록에추가하고기존보존테스트의고정8개기대만실제목록크기로바꿨다. geometry/animation/UV/alpha불변이며실제팀별라우팅은후속PvP범위다.
- R3 GameTest23개전부통과(exit0). 수정한fixture 기대를약화하지않고벽LOS·flight소유권·cast후Vortex수명까지확인했다. secret/입력은사용하지않는서버검사다.
- corrected20clip/적군자산을포함한두번째native격리세션을시작했다. 실제PNG/상태결과를확인하기전최종수락으로표시하지않는다.

## 17. 2차 실게임 입력·화면 및 담당 검수
- 수정 후 native 배치를 완료했다. 수류탄·근접 6종씩은 서버 cooldown, 궁극기 6종은 실제 rear camera·공격·직업 전환 cleanup을 확인했다. 1차 melee 전송/수락 불일치가 재현되지 않았다.
- 타이탄 3종과 새벽칼날은 실제 body 변위 동안 `_move`, 정지 후 `_idle`로 복귀했다. 새벽칼날의 짧은 점프에서는 `_air`와 착지 복귀를 확인했다. master가 실제 PNG를 확인하고 animation worker에 48장과 oracle을 반환해 재검수받았다. 필수 추가 delta는 없었다. 전용 Daybreak idle 미식별과 짧은 공중 검수 범위는 유지한다.
- 방벽·균열 시전과 일반/적군 방벽·균열·Nova 전시를 직접 확인했다. 아트 worker도 원본 PNG를 검수했으며 필수 수정은 없었다. 적군용 실제 비행·팀별 라우팅·속성 파티클 변색까지 완료한 것으로 보고하지 않는다.
- lease/native 중립, 소유 server/client wrapper exit0, 포트 8102/25611 해제를 확인했다. 별도 48시간 caffeinate PID79904는 계속 유지한다.

## 18. 최종 회귀와 패키징
- 전체 단위 2,075개 중 2,069개 통과, 실패 6개는 W228과 같은 검사 집합이다. 일부 실패 메시지는 이번 음원·HUD 추가 개수를 반영하므로 동일 메시지라고 쓰지 않는다. 신규 실패 집합은 없으며 기존 gate를 초록색으로 위장하지 않았다.
- test 실패로 이어지는 assemble이 실행되지 않아 패키징만 별도로 수행했고 성공했다. 전체 검사는 반복하지 않았다. 단순 DDC 시간 수치마다 별도 테스트를 늘리지 않았다.
- 담당 agent 5명을 종료했다. 슬롯4의 master 방벽 scale 변경 1파일을 worker 종료 후 역동기화했고, 슬롯4/5는 W229 수락 및 다음 배치 갱신 대기로 보존했다. 이전 dirty 변경을 reset/stash/clean하지 않았다.

## 19. 커밋 범위 확정
- W229 소스·능력 데이터·HUD·소품·적군 자산·음원·대표 QA와 명시적 기존 애니메이션 지원 파일을 선택했다. 전체 checkout이나 원본 22만 파일을 일괄 stage하지 않는다.
- 초기화·GameTest 등록·mixin 등록·워크트리 상태 4파일은 W229 및 필요한 지원 등록만 부분 stage하며, 나머지 기존 변경은 작업본에 보존한다. 다른 공유 소스는 현재 통합 스냅샷을 포함하므로 기존 dirty API 전제를 `commit-prerequisite-review.md`에 명시했다. 이 커밋을 깨끗한 HEAD만의 독립 빌드 인증으로 보고하지 않는다.
- 최종 경로·개수·제외 범위는 `commit-scope.json`에 기록한다. 관련 커밋 후 원격 push는 수행하지 않는다.
