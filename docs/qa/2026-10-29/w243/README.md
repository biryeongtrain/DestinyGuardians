# W243 — 에이스 ADS 레드닷과 탑 광장 디테일

1. 에이스 W159 ADS graph·최종 모델·팩 parent는 존재한다. 3개 홀로그램이 단면 south인 상태를 확인했고 profile-view 표시 경로에서 방향/크기/선택을 검증한다.
2. 탑 작업은 최신 dirty 통합본을 반영한 고정 slot4에서 Cicero가 독점 4파일을 담당한다. 원본 voxel/world 편집과 동선을 보존하며 추가 장식을 제한된 tick batch로 적용할 예정이다.
3. 사용자가 접속 중인 runServer는 빌드 전 정상 종료하고 검수 후 같은 설정으로 재개한다.

4. 공식 Danmo 4GB에서 수정 전 native ADS를 두 차례 캡처했다. 레드닷과 괄호가 모두 보이지 않는다(`ace-before.png`). 초기 client가 서버 준비 전 접속해 연결 실패한 것은 종료 후 정상 재기동했다. `gamerule sendCommandFeedback`의 구버전 이름은 syntax 오류였으며 gameplay 검증으로 세지 않는다.
5. south 단면을 north/south 양면으로 변경하며 반대 면 U를 반전해 같은 이미지 방향을 유지했다. 원본 87큐브·텍스처·ADS 문턱 .95·카메라/총 위치는 유지한다. Python 자산 검사 11/11 통과, 실제 26.3 parser JUnit 진행 중. 화면에서 최종 원인 확정 전까지 양면 수정은 가설이다.

6. 26.3 실제 클래스 `QuadInstance` → `LightCoordsUtil.lightCoordsWithEmission` bytecode에서 emission15가 block/sky를 모두15로 올리는 것을 확인했다. 기존 profile item shader는 `UV2.y==192`(sky12)만 인식해 홀로그램이 카메라 공간으로 복원되지 않았다. 음수 Y 전용 marker 범위 안에서 fullbright(240,240)도 허용한다. 기존 세계의 일반 발광 아이템은 범위 밖이므로 대상이 아니다. 실제 MC 클래스 계산을 사용하는 회귀를 추가했다.

7. 발광 marker 수정 후 실제 26.3 파서/광원 계산 targeted JUnit6/6 통과. baseline 보존 PNG와 비교할 수정본 Danmo client를 기동했다. 타워의 기존 영구 차원 파일 7개(11.9MB)를 정상 서버 종료 뒤 외부 ZIP(1.9MB)에 백업했다. 48시간 assertion은 유지하고 이번 QA용 bounded awake coordinator를 별도로 사용한다.

8. 새 팩을 실제 로드한 Danmo4GB에서 ADS→발사→ADS유지→HIP복귀 native 시퀀스가 정상 완료됐다(44PNG). `ace-ads-fixed.png`에서 빨간 점과 양쪽 괄호가 화면 중앙에 나타나고, `ace-return-fixed.png`에서 HIP복귀 시 사라짐을 직접 확인했다. lease/heldKeys/pendingSteps/nativeInput 중립을 확인했다.

9. 사용자 추가 지시에 따라 다섯 구역 모두 보강하고 중앙 도착 광장·수목을 우선 검수한다. worker 초기 delta3파일을 기준 SHA 일치 후 통합했다. 원본 좌표 검사 결과 133조각/907셀: arrival233, garden160, market298, overlook157, service59. Worker targeted2/2 및 기존 voxel 포함5/5 통과. master 최종 전체 JUnit을 실행한다.

10. master 통합본 전체 JUnit **2,144/2,144** 통과(320 suites). Eve Astra의 실제 포트폴리오 이미지 두 장은 담당 worker가 브라우저에서 확인했고 붉은/주황 천막·얇은 금속 난간·바닥 삽입 패널·설비 소품에 반영했다. Marc Thompson은 담당자 설명만 검토했다. 상세 출처 구분은 `tower-worker.md` 참조.

11. 실제 기존 QA 차원에907셀 모두 적용(0skip), 약27초에완료했다. Danmo에서 5구역 before/first PNG를 직접 비교했다. 천막·플랜터·조명·벤치·설비 변화가 보인다. 중앙 수관이 단순해 담당자에게 검수 이미지를 전달하고 원본/동선 범위 안에서 도착부 나무의 비정형 수관 보강을 요청했다. 이미 저장된 ledger는 지우지 않고 신규air셀만 추가해야 한다. HUD숨김은 서버 display HUD까지 숨기는 수단은 아니므로 캡처에 HUD가 남아 있다.
12. 첫 Tower 캡처는 creative모드 ACK문자열 대기만 만료됐다. eligible확인 후 수정해5장완료했다. contact 생성에 시스템Python의Pillow가 없어 bundledPython으로 재실행했다. 이 실패는 제품 검증으로 세지 않는다.

13. `/tower` 정상 도착 뒤 survival에서 native앞16틱/뒤16틱/중립8틱 이동을 수행했다. client몸 z범위 -19.5~-16.373, 바닥Y75·체력20·생존·최종중립을 확인했다. `save-all flush` 성공 후 차원 SavedData 파일 `data/destiny/tower_courtyard_details_v1.dat`(2,139bytes)을 확인했다. 보완본 재기동으로 ledger재사용도 확인할 예정이다.

14. 사용자 지정 Marc Thompson VRWon 아트처럼 회색 비중을 줄이는 재질 pass를 추가한다. 전달 GLB에는754재질 중707개 baseColorTexture가 있으므로 텍스처가 전부 빠진 것은 아니다. extras는 sRGB 대표 diffuse 근사이며 shader blending/lighting 미복원을 명시한다. 기존 converter의 material median 축약과 회색 diffuse가 겹친 상태다. 원본 dye를 복구했다고 주장하지 않고 authored full-block surface zoning으로 보강한다.
15. master generator가 원본 SHA를 고정 검증하고 광장 노출 smooth_stone58,117셀을9종 바닐라 fullblock으로 구분했다(압축143,424bytes의 서버 데이터). 원본 경로·충돌·voxel/manifest·외부 원본은 보존한다. 따뜻한 포장·백색 벽·금속 띠·붉은 상점 fascia·중앙 보행축을 나누고 무작위 얼룩 대신 넓은 패널을 사용했다. 상세 counts는 tower-materials.json. runtime는 실제 현재 블록이 원본과 같을 때만 적용하고 별도 영구 ledger를 사용할 예정이다.

16. Marc Thompson의 동일 프로젝트 artist portfolio에서 실제 이미지 링크를 확인하고031/029/030 세 장을 직접 열어 검토했다. 따뜻한 콘크리트, 대형 주황/붉은 타프, 어두운 금속 바닥, 붉은 난간, 푸른 표지 대비가 보인다. master 재질 데이터에 실제 canopy 위치의 적갈색/황토 패널3,207셀과 구조 리브326셀을 반영했다. 최종10종/58,117셀,142,933bytes. 공개 원본 이미지 자체는 repo에 복제하지 않고 출처 링크만 기록한다.

17. worker 반환을 현재 main의 초기907버전 SHA와 비교한 뒤 소유5파일만 통합했다. 새 수관은 기존907이력을 유지하며54개의 신규air좌표만 추가한다. material은 별도 ledger에 기록하며 디테일 완료 후 시작한다. worker 디테일3/3·재질2/2 통과, 최신10종 실제번들58,117셀 decode 재검사2/2 통과. master는 새 runtime 분기 통합으로 최종 전체 JUnit1회를 실행한다.

18. QA 재기동 전 CU Finder에서 데스크톱/SSD 창을 관측했고8102·25611·25565 포트에 기존 listener가 없음을 확인했다. 일반 프로필과 Blender 미저장 씬은 조작하지 않는다. 독립48시간 caffeinate PID79904는 계속 살아 있으며 이번 bounded coordinator와 구분한다.

19. 최종 통합 전체 JUnit2,147/2,147(321suites), 실패/오류/skip0, BUILD SUCCESSFUL. 초기907버전 전체 gate와 구분해 junit-final.json에 기록했다. 격리 QA 서버를 재개하며 기존907장식/ledger가 있는 영구 차원을 그대로 사용한다.

20. 실제 기존 QA 월드에서 수관54변경/0skip, 재질58,011변경/106skip 완료. 기존 floor inlay106셀은 원본과 달라 유지됐다. 디테일 완료 뒤 재질이 시작됐고 약39초에 재질을 순차 적용했다. Danmo4GB 실제5구역 PNG를 직접 비교해 따뜻한 포장·벽/금속 띠·적갈 canopy·중앙 비정형 수관을 확인하고 worker에게2차검수contact를 전달했다. 예전 창고/외곽의 모든 회색을 없앤 것은 아니며, 선택한 Courtyard 가시 영역에 한정한다.
21. 재질 적용 뒤 /tower→survival native앞16틱/뒤16틱/중립8틱 이동 완료, 체력20·생존·lease/native중립. save-all flush ACK. 영구 ledger는 detail2,248bytes, material135,295bytes. 출처 바이너리/manifest는 그대로다.

22. 최종 통합본에서도 에이스 native ADS→발사→유지→HIP을 다시 실행했다(36PNG, returncode0). 실제sample15에서 중앙 레드닷/괄호를 확인했다. 계수/중립은 ace-vision-final.json. 타워 재시작 검증용으로 QA소유(70,74,-20)의 smooth_quartz를 원본 smooth_stone으로 의도적으로 되돌리고 저장했다. 재시작이 이 편집을 덮어쓰지 않는지 확인 후 QA프로브만 원상 복구할 예정이다.
23. 프로브 첫조건명령은 비어 있는 Fantasy 차원의 청크가 내려간 상태라 ACK가 없었다. /tower로 같은 청크를 로드한 뒤 quartz 조건 ACK를 받고 나서만 프로브를 편집했다. 첫실패를 통과로 세지 않는다. 최종입력중립 확인·QA가추가한 overworld12forcechunks 해제·정상save/stop후 클라이언트를 종료했다.

24. 기존 QA영구월드를 정상 재시작한 뒤 detail0변경/0skip, material0변경/0skip 로그를 확인했다. 별도 ledger가 전체 고려좌표를 기억한다. 전용임시청크1개를 새로 forceload한 ACK 뒤 (70,74,-20)의 의도적 smooth_stone 편집이 재시작 후에도 남은 조건 ACK를 확인했다. 프로브만 quartz로 복구하고 그1개forcechunk를 해제·save/stop했다. 실제로그는 tower-restart.txt. 기존월드 재생성 없이 최초 적용·중복방지·수동편집보존을 확인했다.
25. worker는2차 PNG를 검토하고5구역의 재질/수관 개선과106기존패널 skip이 설계와 일치한다고 반환했다. 추가 제품수정 없이 동결한다.

26. QAclient/QAserver는 정상 종료했고8102/25611/25565 listener가 없다. 마지막native/lease 중립, 추가한forceload12개+재시작프로브1개 모두 회수했다. 이번coordinator의 sleep자식만 종료해 wrapper가 자기caffeinate PID71815를 회수했다. 별도48시간 PID79904는 유지한다. slot4는 idle-needs-refresh로 반환하고 worker종료, worktree는 삭제하지 않았다. 최종검사 후 제품13파일 해시와 원본voxel/manifest SHA가 일치한다.

27. 제품/검수43파일을01012c6b로 선택 커밋했다. 다른 기존 dirty/untracked변경은 포함하지 않았다. 최초 접속용runServer에서는961디테일 완료 뒤 재질 적용 도중 기본 무인60초 pause가 발생했다. 명령 stdin이 닫힌 실행이라 소유 JVM에 SIGTERM을 보내 종료했고 Gradle exit143은 이 운영 종료 결과다. 해당 실행에서 명시save ACK를 받았다고 주장하지 않는다. 다음 실행은 보존된material ledger114,973bytes를 읽어 남은8,664셀만 적용했다.
28. 재기동(session52834)은 명령 stdin을 유지하는TTY로 실행했다. 초기보강 동안 pause-when-empty-seconds만0으로 두었고 완료 뒤 디스크 설정은 기존60으로 복구했다(현재 세션만0 유지). detail0/0, material8,664변경/0skip완료·팩생성 성공·콘솔save-all flush ACK를 확인했다. 최종detail2,248bytes/material135,295bytes.25565 listener·online-mode=true·andlist OP4·dynamic-fov-shader=true 유지. 서버는192.168.35.237:25565에 켜 둔다. production.json참조.
