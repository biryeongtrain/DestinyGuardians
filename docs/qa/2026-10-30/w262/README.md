# W262 탑·시련의 장 음악

요청: 샤크스 음성과 별도로 시련의 장 음악 연결, Destiny-Tower-BGM 전달본을 탑에 적용.

1. 원본 README/태그/음원 목록을 확인. 탑 26개는 완성곡 목록이 아닌 세그먼트 묶음이다. 자벨린 인트로 원본3개 후보 확인. 공식 결과 BGM은 확인되지 않아 편집용 마무리 음악으로 구분한다.
2. 접속자0명 확인. 이전 운영 relay 소켓이 사라졌지만 소유 Java PID21720이 남아 있어 SIGTERM으로 종료했다(exit143). 저장 완료 로그는 남지 않아 정상 stop 완료로 주장하지 않는다. 빌드 전 종료 확인. 운영/QA4GB 유지.
3. 슬롯4 전체 갱신은 기존 소유범위 밖 변경 때문에 거부됨. 해당 파일은 main과 같지만 과거 baseline 범위 밖이므로 임의 reset/clean하지 않는다. 이번 음원9개는 양쪽 모두 없는 신규 경로이며 SSD 읽기전용 입력만 필요하므로 슬롯4에서 배타 작성 후 파일별 해시로 통합한다. 전체 checkout 갱신 성공으로 보고하지 않는다.
4. master는 음악 수명주기/중앙검증, Aquinas는 새 음원/재현 스크립트/출처를 소유한다. 탑4트랙 반복·인트로/결과1회·팩완료대기·퇴장/리스폰/종료 정지를 구현 중.

5. 1차 Java25 컴파일과 targeted JUnit35개(음악상태7·점령27·음성cue1) 통과. 시퀀스는 nanoTime 기반으로 실제 음원 길이를 사용하고, 탑은3초간격 반복·인트로/결과는1회 재생한다.
6. 샤크스 음성도 CameraViews 전송·청자/카메라 엔티티 앵커로 변경. 인트로 카메라 생성 후 소개대사를 보내며, 화면용 패킷필터나 실제몸과 카메라간 거리로 대사가 사라지는 경로를 피한다. 음성과 음악은 각각 VOICE/MUSIC 채널.
7. CU에서 Finder 데스크톱 확인, 포트8102/25611/25565 비어있음. bounded2시간 master awake coordinator를 시작했다. 기존 격리 Danmo QA 프로필만 재사용한다.

8. 음원6개 통합: stereo48kHz Vorbis, 합계4,386,786 bytes, stream:true. 탑4개(144.231/99.556/67.200/64.615초), 자벨린C1 인트로12.382초, 같은C1 마지막8초를 편집한 결과용 outro. 공식 승리곡 복원이 아니다. 원본해시/편집구간/페이드/음량측정은 art/audio/w262/provenance.json. 디코드·샘플수 검증은 청취검수와 다르다.

9. 전체JUnit2288개 중5개 실패: 기존 W112/W115/W168/W179 자산불일치4개와 새음원6개를 아직 허용하지 않은 W98 목록검사1개. W98은 과거음원을 그대로 검증하면서 W2626개 출처해시를 추가했다. 나머지4개는 이번 음악변경과 무관하며 보존한다.
10. worker의 pack재로드 후1회성음악 재시작 지적을 수락. 같은장면에서 이미 시작/완료된 인트로·결과는 중단 후 재시작하지 않도록 수정하고 회귀검사를 추가했다. 탑은 팩재로드 후 현재트랙 처음부터 재시작한다.

11. 사용자 추가지시로 음악재생은 minigame-lib API로 전환했다. r1 QA서버는 클라이언트 접속 전에 console stop으로 정상종료(exit0)했다. 라이브 소스 변경 없이 API통합 후 r2로 검증한다. 라이브러리 `MusicService.playSound`는 이미팩에포함된 이벤트/길이/볼륨을 받아 기존 Channel/Playback/음악타이머/팩준비/카메라전송/정지를 재사용한다. 파일복제·두벌팩 없음. Destiny는 씬선택·탑순환간격3초만 관리하고 실제음원종료는 Playback.done()을 따른다.

12. API전환 후 Destiny targeted45개와 minigame-lib MusicTest4개 통과. 추가 검수에서 중대지적 없음. r2 서버를4GB로 기동했고 신규6음원 스트리밍팩과 실제 Danmo 클라이언트 검증을 시작한다. 전체gate4개 기존미해결은 그대로 별도기록한다.

## 최종 검증

- 라이브러리 API반영 targeted JUnit49개 통과. 전체gate는2288개 중기존자산4개와 새목록1개 실패였으며 새목록은수정후통과, 기존4개는미해결로분리했다. 최종 전체gate 재반복은하지 않았다.
- Danmo/OpenGL·서버/클라이언트4GB. 실제클라이언트가 새팩로드를확인한뒤 탑→입장→전투→기권결과→탑복귀 GameTest1290틱/65.9초 통과. API가12.382초 인트로와8초결과음악을자동종료하고 탑곡을재개했다.
- 실제native전진5틱+중립3틱, 최종lease=false/heldKeys=[]/pendingSteps=0/native중립 확인. [결과](vision-r2/result.json), [입장](vision-r2/intro-music.png), [승리](vision-r2/result-music.png), [탑귀환](vision-r2/tower-return.png).
- 클라이언트 음원관련로드오류 없음. 파일전수디코드·팩ACK·서버/API전환·실제PNG는 확인했지만 녹음/청취검수와4트랙전체순환을실시간으로보지는않았다.
- 실제팩67,925,308bytes, 이전63,726,887bytes 대비4,198,421bytes증가(약4.2MB). 음원6개만포함, 모든음악stream:true. [팩기록](pack-r2.json).
- 초기경기장준비에서2.126초밀림1회 기록. 지속부하벤치마크나오디오끊김청취확인으로해석하지않는다.
- QA서버console stop exit0, client소유wrapper stop -2, master awake coordinator exit0. 소유입력·창·서버·잠자기방지정리완료. worktree는보존.

## 커밋

- minigame-lib `c0900ef`: 기존팩음원 재생 API.
- Destiny `70ec79ff`: 탑/시련 음악 연결·음원·회귀검사·실게임검증.
- 기존 main dirty/untracked 변경은 보존했고 관련파일만 커밋했다. 원격 push는 하지 않았다.

운영 runServer 재개: **192.168.35.237:25565**, online-mode=true, andlist OP4, 실제JVM4GB 확인. 운영팩은68,090,200bytes(약68.1MB), 이전운영팩대비4,363,313bytes 증가. QA팩과 생성환경차이는 server-start.json에별도기록했고, 신규음원6개의해시는수락본과모두같다. [운영기록](server-start.json).
