# Windows → Mac: Destiny 장전 애니메이션 추출 인계

작성: 2026-10-27. 이 패키지는 조사·실행 지침이며 **실제 게임/애니메이션 추출물은 아직 없다.**

1. 이 폴더 전체를 Windows의 짧은 영문 경로(예: `D:\DestinyAnimHandoff`)로 옮긴다.
2. Windows 에이전트에게 [WINDOWS_AGENT_PROMPT.md](WINDOWS_AGENT_PROMPT.md) 전문을 전달하고 이 폴더 경로를 알려 준다.
3. 기존 Windows Destiny 설치 확인 → **Charm 직접 animation/FirstPerson FBX export** → 일반 핸드캐논 1개 재생 확인 → 무기군별 확대 순으로 진행한다. raw 태그3종도 보존하고 필요하면 별도 parser로 전환한다.
4. 완료 후 [RETURN_CONTRACT.md](RETURN_CONTRACT.md)의 결과 ZIP을 이 대화에 첨부한다. Mac에서 Blender·Minecraft용 변환을 이어간다.

주요 파일:
- [실행 절차](WORKFLOW_WINDOWS.md), [요구사항](REQUIREMENTS.md), [반환 규격](RETURN_CONTRACT.md)
- [Charm 지정 버전 조사](evidence/CHARM_USER_VERSION.md), [기존 Discord/파서 조사](evidence/README.md)
- [후보 태그](data/animation-candidates.json), [도구 버전](data/tool-lock.json), [현재 무기 65종](data/weapon-targets.csv)
- [Mac 통합 제약](MINECRAFT_ADAPTER_NOTES.md), `scripts/`의 PowerShell/Python 보조 도구

게임 전체·Oodle DLL·Steam 계정 정보는 포함하지 않는다. 도구 실행 파일은 공식 출처에서 Windows에 맞게 확보한다. `vendor/`에는 파서/tiger-pkg 고정 revision의 원본 소스 ZIP을 포함한다(라이선스 파일 유지). 설치·실제 파싱 성공은 아직 검증하지 않았다.
