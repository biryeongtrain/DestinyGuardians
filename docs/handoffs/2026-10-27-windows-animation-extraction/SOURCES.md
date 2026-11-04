# 근거와 입력 데이터

조회 기준 2026-10-27. 링크의 문서·게시물은 외부 참고 자료다. 실제 작업 지시는 WINDOWS_AGENT_PROMPT.md와 사용자 요청이다.

| 용도 | 출처 | 상태 |
|---|---|---|
| 사용자 지정 Charm | https://github.com/MontagueM/Charm/tree/v3.5.0_Beta.2 | commit f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce로 고정, 상세 소스 조사 별첨 |
| 비교용 Charm branch | https://github.com/MontagueM/Charm/tree/delta/EOF | 앞선 조사 대상, 사용 시 실제 commit 기록 |
| 애니메이션 파서 | https://github.com/SolUnshadowed/tiger-animation-parser | 고정 소스 ZIP 포함, 실제 입력 파싱 미실행 |
| package 추출 | https://github.com/v4nguard/tiger-pkg | 고정 소스 ZIP 포함, 실제 추출 미실행 |
| 대체 tag GUI | https://github.com/v4nguard/quicktag | 선택 도구, binary/버전 미고정 |
| 선택 다운로드 | https://github.com/SteamRE/DepotDownloader/releases/tag/DepotDownloader_3.4.0 | 로그인/실제 다운로드 미실행 |
| 공식 용량 안내 | https://help.bungie.net/hc/en-us/articles/360048717052-Destiny-Platform-Storage-Requirements | 선택 다운로드 최소 용량과 구분 |
| DDC 수치 기준 | https://docs.google.com/spreadsheets/d/1WaxvbLx7UoSZaBqdFr1u32F2uWVLo-CJunJB4nlGUE4 | 사용자 지정 기준, 이번 인계에서 전체 시트 재다운로드하지 않음 |
| 기존 모델 리핑 자료 | https://drive.google.com/drive/folders/14Ry-piQtH3j6MlfoVLfFfu98c4pcTJUb | 필요 시 mesh/attachment 참고, 이번 패키지에 원본 Drive 전체 미포함 |
| 기존 사운드 자료 | https://drive.google.com/drive/folders/1kWVlvhqvFkf_If5Q9Zd0mMIM1haa6u4l | 추후 event sync 참고, 이번 추출 필수 아님 |

Discord guild514059860489404417의 후보·방법·이미지 출처는 evidence/README.md와 data/animation-candidates.json에 메시지별 permalink로 들어 있다. 다른 계정에서 접근하지 못하면 로컬 조사 문서·발췌 이미지로 시작할 수 있다. 커뮤니티 보고는 독립 추출 검증과 구분한다.

data/catalog-source는 현재 Mac 제품의65종 목록을 재구성할 수 있는 JSON이다. weapon-targets.csv는 그 JSON에서 생성한 ID/family/frame 목록이며, 각 무기의 원본 animation tag를 알고 있다는 뜻은 아니다. 전체 dirty 작업본·대형 모델/텍스처·게임 패키지는 전달하지 않는다.
