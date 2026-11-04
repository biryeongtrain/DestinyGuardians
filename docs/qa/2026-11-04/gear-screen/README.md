# 캐릭터 장비 화면 QA (2026-11-04)

격리 QA 서버·클라이언트(DevilsQA, Vision :8102)에서 실화면으로 확인했다. 오프라인 QA 계정이라 스킨은 BetterModel 대체 스킨(파랑·분홍)으로 보인다. 실제 계정은 본인 스킨이 나온다.

| 항목 | 결과 | 증거 |
| --- | --- | --- |
| 슬롯·무기 모델 아이콘·방어구/고스트 아이콘 | 통과 | gear-3.png |
| 커서 hover 시 보관 칸 펼침, 2틱 뒤 툴팁(스탯 순서·비교 색·특성) | 통과 | gear-3.png, gear-4.png, player-figure-tooltip.png |
| 보관 칸 클릭 장착 | 통과 (에이스↔듀크) | gear-4.png, player-figure.png |
| 하위직업 화면·옵션 격자 | 통과 | gear-7.png, gear-8.png |
| 악마의 소굴 전투 중 피격 후에도 화면 유지 | 통과 (피해 7, 상태 GEAR) | 상태 명령 출력 |
| 가운데 플레이어 모델(본인 스킨 부위 12개) | 통과 | player-figure.png |
| 손에 장착 기본 무기, 파지(손잡이가 주먹 안, 총구 전방) | 통과 (에이스·듀크) | player-figure.png, player-figure-duke-grip.png, player-figure-grip-side.png |
| 장착 무기 바꾸면 손 무기도 바뀜 | 통과 | player-figure.png |
| 툴팁·보관 칸이 모델 위에 그려짐 | 통과 | player-figure-tooltip.png |
| 강제 퇴장 후 재접속 → 다시 열기 | 통과 | player-figure-rejoin.png |
| 리소스팩 크기 | 188.0 MB (목표 250 MB 이내) | polymer/resource_pack.zip |

미검증: WASD 이동 탐색, OP 테스트 무기고 버튼, E/우클릭 닫기, 실제 스킨 계정 화면, 원본 대기 클립.

전체 게임 테스트(`runGameTest`)는 187개 실패. 대부분 이전 피해 배율 조정·장전 타이밍 관련으로 이번 변경과 무관해 보인다. `weapon_screen_w227`의 "Native click cannot fire or copy weapon" 실패는 관리자 무기고 경로이며 이번 작업의 클릭 경로 변경 여부를 HEAD 비교로 아직 확인하지 않았다.
