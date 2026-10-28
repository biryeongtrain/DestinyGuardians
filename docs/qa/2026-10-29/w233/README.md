# W233 빛 능력 사운드

1. SSD 전달본 README/큐시트/이벤트 근거 확인. 469개 능력별 행, 원본 프레임 연결26행, 숫자 미확정280행.
2. W232 고정 슬롯1·4를 현재 dirty 통합본으로 갱신하고 헌터/타이탄 선정을 병렬 배정. 기존 worker 문서의 master 추가분은 외부 보관 후 갱신.
3. master는 워록11개 실제 호출 연결 선정. 신성 폭탄 release 중복음 억제와 착탄 위치의 사운드 전송 준비.

초기 준비 단계의 기록이며, 최종 검증 결과는 아래11~14번을 따른다.

4. 중앙 compileJava/compileGametestJava 통과(33초). 별도 폭풍몰입 impact 호출이 없는 항목은 미사용 등록을 하지 않고 retained에 기록. 실제 재생 검증은 아직 대기.

5. 헌터9/타이탄8/워록11개 실제 호출 연결 통합. 첫 Vorbis 인코딩에서 전기 지팡이 출력 peak1.01087을 발견해 거부. gain0.65→0.5로 낮춰 재변환하며, 원본 길이·속도는 유지. 이 실패를 통과로 처리하지 않음.

6. gain0.5 재변환 및 --check 통과: 28개 연결/25개 고유 모노48kHz Vorbis, 전부 끝까지 디코딩, 길이 유지, 최대 peak0.926633. 원본 프레임 연결10개/이름 후보18개. 매핑 audit81개 class 이벤트 중 변경28개 외 보존 확인. 방벽·점프·숫자 후보와 확장 궁극기 일부는 retained로 남김.

7. 타이탄 투사체/강타의 impact도 center로 전송하도록 연결. 두 worker는 종료했고 고정 슬롯은 유지. 새 QA run은 loopback25611/whitelist, 전용 Vision8102, tower비활성·soundQA로그 활성으로 준비. 일반 서버/프로필/월드 보존.

8. 전체 JUnit2079개 중2069통과/10실패. W232와 실패 ID집합 동일. 기존 음원 closed-inventory/옛 정의 hash assertion은 의도한 새 매핑도 거부하므로 전체 성공으로 표시하지 않음. Shadowshot 연속음/기존 W34와 타워 decoder 관련 suite는 통과. 별도 assemble/compileGametestJava로 패키지 gate를 마무리.

9. 첫 수동 패킷 GameTest에서 fake player를 level.players에 등록하지 않아 수신자가0명인 fixture 오류 발견. 실패 원본을 보존하고 서버를 정상 종료한 뒤 listener 등록/제거를 추가. 제품 소스·음원은 변경하지 않음. 테스트만 재컴파일하여 재검증.

10. 수정한 수동 패킷GameTest2/2통과: 신성폭탄 cast1회/release무중복/착탄위치, 칼날장전 throw1회/워록 균열고유key. 처음 floor 생성은 idle청크 미로드로 거부되어 QA forceload후3721+549블록 설치성공. 팩 내28정의/25음원 바이트가 소스와 일치. Vision클라이언트 기동중.
11. 새28개 이벤트 모두 운영자 재생 명령 성공과 실제 서버 사운드 패킷 전송을 확인. 실제 제공된 Polymer 팩의28개 정의·25개 OGG가 소스와 바이트 단위로 일치한다. 이는 독립 청취 판정은 아니다.

12. Vision native 입력5개 시나리오 통과: 헌터 전기 지팡이·황금총, 타이탄 태양의 망치, 워록 신성 폭탄·치유 균열. 각 runner 종료0/입력 cleanup 성공과 실제 PNG를 확인. 신성 폭탄은 start1회→착탄 impact1회이며 fire 중복 없음. 망치·신성 폭탄의 실제 벽 착탄 위치(z14.875)에서 impact 전송. 황금총 탄약3→2도 확인.

13. 클라이언트 OpenAL이 MacBook Pro 스피커에서 초기화되고 sound engine 시작. 음원/OGG/Vorbis 로드 오류·경고 없음. 독립적인 스피커 청취·원작 A/B 비교, Wwise 레이어 전체 복원은 미검증. 원본 프레임 근거10개와 이름 후보18개는 계속 구분한다. 사용자 확인용 MP32개와 전체 적용 OGG 목록은 exports/light-abilities-w233에 저장.

14. QA 종료 완료. 입력 lease/held key/pending step을 해제하고 직업·사운드·forceload를 정리한 뒤 전용 client/server 정상 종료. 포트8102/25611/25565 닫힘·Java프로세스 없음 확인. 사용자48시간 caffeinate PID79904는 유지. 제품 소스·음원은 QA 중 동결 상태로 유지됐으며 별도 assemble/compileGametestJava와 JAR 자산 일치 검사는 통과했다. 전체 JUnit은8번의 기존10실패가 남아 있으므로 전체 gate 통과로 보고하지 않는다.
