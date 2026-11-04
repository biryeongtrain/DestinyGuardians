# 작성 기록 — 2026-10-27

- 기존 Discord/파서/다운로드 조사3파일을 보존해 복사했다.
- 사용자 지정 Charm ref를 GitHub에서 현재 commit f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce로 resolve하고 README를 고정했다. 상세 소스 조사 결과는 evidence/CHARM_USER_VERSION.md에 반영한다.
- 병렬 read-only 조사에서 실제 animation/FirstPerson FBX 및 raw dump 구현·UI·제약을 확인했다. Charm 직접 FBX를 우선 경로로 반영했고, raw 미확보라도 유효한 FBX를 partial로 우선 반환하도록 했다. 조사 agent는 종료했다.
- 현재 카탈로그 65종의 family/frame/id와 원본 JSON, 장전 presentation 참고 소스를 묶었다.
- Windows PowerShell 예시·parser 준비/실행 도구·반환 packager·manifest template을 작성했다.
- Windows 도구 설치/게임 다운로드/태그 추출/Blender 재생/Minecraft QA는 이 인계 작업에서 수행하지 않았다. 과거 봉인 QA는 수정하지 않았다.
- 단순 스탯 퍽은 출처·적용 경로만 확인하고 반복 테스트를 줄이는 최신 사용자 방침을 제품 AGENTS.md와 DDC 정책에 반영했다.
- JSON 파싱·Python syntax·합성 입력의 반환 ZIP 생성·미작성 템플릿 거절을 확인했다. PowerShell/Windows 실행 검증은 수행하지 않았다. 최종 ZIP은 CRC·내부 해시·상대 링크를 확인한다.
