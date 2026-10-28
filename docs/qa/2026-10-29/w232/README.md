# W232 타워 스폰 월드

## 진행 기록

1. 사용자 요청 직후 일반 Minecraft 서버 프로세스가 없음을 확인. 종료 상태 유지.
2. SSD 원본 Courtyard 자료를 읽기 전용으로 조사. 별도 headless Blender에서 GLB를 가져와 중앙광장 조감·지상 뷰 확인. live Blender 미저장 장면 보존.
3. Fantasy 0.8.4+26.3 공개 artifact 확인. 기존 워크트리1·4를 현재 dirty 통합본까지 갱신하고 변환 도구/월드 런타임을 분리 배정.
4. 원경 전체가 아닌 중앙광장을 실제 바닐라 블록으로 변환. crop·스폰은 변환 후 바닥/머리공간과 실제 화면으로 검수 예정.

위 1~4번은 초기 진행 기록이다. 아래 최종 통합·실게임·영구 저장 검증 결과를 함께 참조한다.

5. 사용자 scale2 크기 승인. 실제 voxel payload를 읽는 상부/보행층 미리보기와 3×3 지지면·2블록 머리공간 검사 도구 준비.
6. 새 QA run 폴더에 필요한 설정만 복사. 일반 프로필/월드는 복사하거나 변경하지 않음. Vision 포트8102 및 QA서버25611 미점유 확인. 48시간 caffeinate 유지.

7. 변환 worker delta4개를 CAS 해시로 검증 후 통합. master fixture15개 통과(좌표루트·텍스처알파·천막공기·큰바닥피복·binary/회로NBT순서 포함). 실제SSD전체 변환 시작.

8. 전체변환 성공: 원본배치16,436개 중13,776개가crop교차, 11,266,738삼각형 표면→1,151,116바닐라블록. 변환42초. binary/manifest와Sponge schematic 생성. 원본과 voxel의상부·천막아래 미리보기 직접확인: 중앙화단·계단·캐노피배치 유지.
9. 바닥3×3/머리2칸 오프라인 검사18,073후보. 광장동쪽79.5,70,-49.5를 임시스폰으로설정, 실제충돌검사는아직대기. worldworker9파일CAS통합, 중앙target컴파일시작.

10. source-review/courtyard.png 및 top.png, 변환된 top.png/walkways.png 직접열어원본배치와비교. 표면복셀화는천막/아치속공기를유지하며높이기반전체채우기를하지않음. 새 런타임은기본콘텐츠전체와함께정확26.3컴파일성공(중앙target-r1 진행중).

11. 중앙 target-r1 compile/assemble/JUnit3/3통과. full-r1은2079중2069통과·10실패: 기존6실패+과거/tmp plugsets원본누락4실패. W232decoder3개는통과하며관련원본/consumer변경없음.
12. 정확FAPI/Minecraft소스상manualOnly는headless에서제외됨을확인. 외부QA init으로일반dev서버+gametestclasspath를사용, 정확단일/test run명령3개를성공요약확인후순차실행. world준비/유한청크/안전전송/기존월드분리/모드·cleanup/블록·피해·폭발·화재보호/막힌머리공간거부 3/3통과.

13. R1 실제PNG에서 첫후보가외벽내부빈공간임을발견. 2칸충돌조건만으로사회스폰의시야를보장하지못했음. inspect_walkways에open-sky최상부필터추가. 최종70.5,75,-19.5에서직접PNG확인, native보행/점프경로이동확인. 코드지형자동수리없이manifest스폰만교정. R1client/server종료후좌표·검증메타데이터반영.

14. open-sky회귀 fixture추가: 같은3×3충돌조건을만족하는지하빈틈과노천바닥중후자만선택함을검증. Python전체16/16통과. 새spawn70.5,75,-19.5 yaw150확정. Binary/Schematic지형은동일하며manifest와재변환config만갱신, 최종assemble중.

15. 최종assemble 성공. jar 안Fantasy0.8.4+26.3중첩포함·바이너리해시·최종spawn메타데이터일치확인. 같은QA저장폴더로서버재개성공. 최종스폰으로manual3개재실행3/3통과.

16. 최종Vision R2: 재접속시새스폰70.5,75,-19.5·onGround·selfcamera확인. Native forward40틱으로8.6306블록이동, client상태·서버data get Pos대조. 다른차원fixture→실제/tower명령→새스폰복귀, y=-62낙사fixture→health20새스폰복귀통과. 실제PNG4개확인/보관. HUD숨김은맵조감촬영때만수행후복원, 모든lease/native키중립확인.
17. 영구저장검증용gold_block을원본smooth_stone바닥1칸에console로저장·flush. R2client/server종료, 같은폴더R3서버만재개중. 일반월드/프로필은건드리지않음.

18. R3새JVM에서동일savedworld재개. idle로내려간청크를QA forceload로다시읽은뒤gold_block보존확인. 원본smooth_stone복원·flush·확인, 임시청크ticket해제, 서버종료. binary지형/제품소스변경없음.
19. 최종8102/25611/25565닫힘·Java프로세스없음. 모든QA입력해제, 자체awakewrapper종료. 사용자48시간caffeinate PID79904유지. 고정워크트리1/4보존·worker종료·idle-needs-refresh기록.

## 최종 상태

중앙광장 블록 맵과 Fantasy 스폰 월드 구현 완료. 관련 Python16개·JUnit3개·GameTest3개 통과, Vision 보행·귀환 및 별도 JVM 재시작 후 편집 보존 확인. 서버와 QA 클라이언트는 종료했다. 전체 JUnit은 기존 실패·과거 자료 누락을 포함해10개 실패가 남아 있으며 전체 gate 통과로 간주하지 않는다.
