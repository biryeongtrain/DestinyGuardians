# 고정 병렬 워크트리

2026-10-28 사용자 지시로 W221부터 5개 슬롯을 보존하고 재사용한다. 경로의 최초 무기명은 슬롯 식별자이며 다음 작업의 소유 기능을 제한하지 않는다. 현재 배정은 [worktree-pool.json](worktree-pool.json)에 기록한다.

| 슬롯 | DestinyGuardians-worktrees 아래 경로 |
|---|---|
| 1 | w221-ikelos_sg_v1_0_1 |
| 2 | w221-mindbender_s_ambition_adept |
| 3 | w221-parcel_of_stardust_fell_to_earth |
| 4 | w221-pyroclastic_flow |
| 5 | w221-seventh_seraph_officer_revolver |

기준 통합 checkout: `/Users/qf/IdeaProjects/DestinyGuardians`. 슬롯 부모: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees`.

1. master가 이전 worker를 종료하고 소유 변경이 main에 통합됐는지 확인한다. 검수 결과와 고유 delta를 보관하며, 슬롯과 격리 dependency/build/run은 보존한다.
2. 다음 배치 manifest에 같은 `destination`, 새 `name`, 정확한 `owned_paths`를 지정한다. master만 갱신 도구를 실행하며 동시에 worker·빌드·다른 갱신을 실행하지 않는다.
3. `scripts/qa/reuse_worktree_batch.py --source <main> --manifest <next.json> --recovery <새 외부 복구 폴더>`를 `rtk proxy python3 -B`로 실행한다. 현재 dirty/untracked 통합본과 별도 dependency 소스의 변경 파일만 복사한다. main HEAD가 바뀌면 슬롯의 detached HEAD/private index만 전진한다. 원격 pull이나 main index 변경은 하지 않는다.
4. 도구는 모든 슬롯을 먼저 검사한다. 미통합 소유 변경, 소유 범위 밖 수정, staged 변경은 갱신을 막는다. 덮어쓸 바이트와 이전 메타데이터는 외부 `before.zip`에 보관한다. 실패 시 incomplete 상태를 해소하기 전 worker를 시작하지 않는다.
5. 모든 슬롯의 ready와 새 기준선 검증 후 다음 worker를 배정하고 registry 상태를 갱신한다. 검수를 마친 배치는 master가 관련 변경을 커밋한다. push는 별도 지시를 따른다.

도구의 작은 임시 저장소 테스트 6개는 변경 파일 갱신·미통합/범위 밖 차단·후속 슬롯 충돌 선검사·HEAD 전진·의존성 격리·복구 바이트·동일 파일 inode 보존을 확인했다. 첫 실제 갱신은 W222에서4개 기존 슬롯에 실행했다. 각18,622개 변경 파일만 반영했고209,230개 입력의 동일 기준선을 확인했다. main은 변경하지 않았고 슬롯을 다시 만들지 않았다. 결과는 [W222 refresh.json](2026-10-28/w222/refresh.json)에 기록했다. 이 갱신은 전체 파일 해시 스캔을 포함하므로 새 배치 준비 시간에 포함된다.
