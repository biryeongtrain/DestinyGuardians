# W225 재현 자료

- `generate.py`: 표시 generator 를 실행한다. 원본 리그/pose 를 수정하는 배치가 아니다.
- `verify_delta.py`: 기준 commit fe4205c1의 생성 manifest 와 비교한다.290개 item root 의 scale 필드 외 모델 바이트 변화가 없음을 확인한다.
- `build.py`: 이번 32개 검사와 assemble 명령이다. 현재 통합 checkout 에는 이전 미커밋 파일이 남아 있으므로 깨끗한 HEAD 만의 빌드 인증으로 간주하지 않는다.
- `runtime-before`: 같은 입력으로 수정 전 발사·장전·ADS 를 캡처한다.
- `runtime-after`: 수정 후 3종의 발사·장전·ADS 를 캡처했다. 끝의 F 교체 시도 3건은 능력 입력으로 처리됐고 fixture 의 load 보호도 있었으므로 교체 검증에서 제외했다.
- `runtime-switch-fixture`: 실제 인벤토리 stack 을 교체해 기존 Handling 과 STOW/READY 루트를 검증한다. selector 를 위조하지 않는다. **번호키 입력 검증은 아니다.**

실행 경로는 각 파일에 명시된 `/private/tmp/destiny-w225-*` 전용 runtime 으로 복사해 사용한다. 임의 일반 프로필에서 실행하지 않는다. loopback QA 서버 25611, Vision8102를 사용하며 소유권과포트부터 확인한다. client token 은 실행 시환경변수로만 생성한다. 일반 프로필설정·월드·비밀번호는 보관하지 않았다. coordinator 를 `scripts/qa/keep_awake.py`로 감싼다.
