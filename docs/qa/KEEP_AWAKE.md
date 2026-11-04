# Mac 인게임 QA 잠자기 방지

사용자 승인: 부재중 일반 Computer Use 복구 및 인게임 QA 중 자동 잠금 방지. **암호 보호/인증은 끄거나 우회하지 않는다.** Mac이 이미 잠겼다면 이 helper는 잠금을 풀지 못한다.

다음 QA부터 client/배치 실행을 아래 wrapper로 감싼다. 시작 전 CU로 잠금 해제를 관측하고 기존 client/port 소유권을 확인한다.

프로젝트 `AGENTS.md`에도 이 실행 규칙을 기록했다. 운영 helper의 offline lifecycle 검증은 `rtk proxy python3 scripts/qa/test_keep_awake.py -v`로 실행한다. 제품 JUnit과는 별도인 6개 운영 테스트다. W107 실제 QA에서도 bounded assertion의 시작·소유 PID·종료를 [검증 기록](2026-10-25/w107/native-visual-review.md)에 남겼다.

```sh
rtk proxy python3 scripts/qa/keep_awake.py --seconds 43200 -- rtk proxy python3 /tmp/OWNED-QA/run_client.py
```

`caffeinate -dimsu`의 UserIsActive·idle display/system sleep assertion을 최대12시간 유지하며 command 종료 시 자신의 caffeinate만 해제한다. `pmset -g assertions`로 실제 PID/남은 시간을 확인해 QA에 남긴다. 비밀번호/화면보호기/전원 설정·일반 프로필을 영구 수정하지 않는다. 수동 잠금, OS 정책, 덮개 닫힘, 시스템 재시작까지 막는 보장은 아니다. 작업이12시간을 넘으면 현재 상태와 소유권을 다시 확인하고 새 bounded session을 시작한다.

장시간 master QA가 server/client를 따로 띄울 때는 소유한 caffeinate session/PID를 기록하고 마지막 입력/관측 종료 후 그 PID만 정리한다. `killall caffeinate`나 다른 session 종료를 사용하지 않는다.

## 한 배치 안의 수정·재시작 사이

W170에서는 첫 client wrapper가 정상 종료되면서 자기 assertion도 해제했고, 수정·자동 회귀 뒤의 두 번째 CU preflight에서 Mac 잠금이 확인됐다. 이후 같은 배치를 재시작할 예정이면 **전체 master QA coordinator를 한 bounded wrapper로 감싼다.** coordinator 안에서 자기 client/server를 완전히 종료하고, 재빌드·gate·새 preflight·재기동을 순차 수행한다. client 종료와 master 배치 종료를 혼동하지 않는다. master 종료 시에는 남은 자기 runtime과 assertion을 모두 회수한다.

`keep_awake.py --seconds 1800 -- <master coordinator command>`처럼 예상 배치 길이로 제한한다. 무한 sleep/상시 daemon, 일반 프로필 변경, 암호 보호 해제로 대체하지 않는다. 이 절차도 수동 잠금·OS 정책을 우회하거나 이미 잠긴 Mac을 해제하지 못한다.
