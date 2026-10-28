# W235 모델 worker 반환 기록

- 작업 위치: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-pyroclastic_flow` (고정 슬롯4).
- 소유권: `/private/tmp/destiny-w235/worktrees-model-owned.json`의 `features[0].owned_paths` 정확12개.
- 기록 시각: 2026-10-28T18:54:25.120269+00:00.
- main은 읽기만 했다. 중앙 Gradle/Vision, 서버/client 조작, 팩 생성, 생성기 전체 실행, commit은 하지 않았다.

## 변경

산탄총5종의 숨김 탄피 root에 `textures.particle`을 각 무기의 기존 `destiny:item/weapon/w123/<weapon>`로 추가했다. `elements: []`는 유지했다. 생성기5곳에도 `source['textures']['particle']`을 사용해 같은 출력을 지속하도록 반영했다.

생성기의 이번 변경을 역으로 제거한 바이트는 시작 시점 SHA-256과 모두 일치한다. JSON에서 추가 textures만 제거한 바이트도 시작 시점 SHA-256과 일치한다. 따라서10개 기존 소유 파일의 변경은 이 출력 정의와 particle 슬롯뿐이다. 기하·타이밍·다른 생성 결과·ParticleTextureFallbacks는 수정하지 않았다.

## 검사

실행: `rtk proxy python3 -B scripts/qa/test_hidden_shells_w235.py -v`

결과: **7 tests OK, skipped0** (최종 실행0.379초).

- 숨김 root5개: 정확히 해당 무기의 particle과 빈 elements만 존재하고 실제 PNG가 존재한다.
- 생성기5개: AST에서 숨김 모델 emit 인자만 평가한다. 실제 source particle과 대체 source particle 모두 동일 계약을 만족한다. 생성기를 import하거나 전체 실행하지 않는다.
- 실제 사용자 로그 `/private/tmp/destiny-user-0U2mtrD.log` (SHA-256 `d0b89257db274e89ed52917921420cf95977eef3b9eaab17495cf051ce560ade`)의 고유 경고2284개를 사용했다. 모두 누락 슬롯은 particle이다.
- 원래의 빈 root5개를 메모리에 복원하면2284개 모두 particle 해석 실패한다. 수정된 worktree source에서는2284개 모두 올바른 무기 PNG로 해석되고, 상속된 elements는 비어 있다.
- 경고 구성: framing1142 + Dust236 + FILO230 + IKELOS242 + Mindbender210 + Parcel224. 최종 root별 합계는 각각472/460/484/420/448이다.
- 음성 검사: 원래 particle 없는 빈 root, 누락 parent, parent cycle, 누락 texture alias, alias cycle, 잘못된 sprite ID, 누락 PNG. child texture override와 빈 geometry override도 검증했다.

## 증거 경계 및 master 후속

클라이언트 로그는 Minecraft26.3/Fabric Loader0.19.5를 명시한다. 서버팩이 리로드 목록에 포함되고 atlas 생성까지 진행됐다. 조사 당시 생성 ZIP SHA-1은 로그 요청값 `bc35f51202d5ad2a1bba94158cc67a720b5f9e02`와 일치했다. pack meta는 min_format `[97,1]`, max_format `97`이다.

이번 검사는 수정 source와 실제 과거 로그 ID의 부모 체인에 대한 검사다. 수정된 최종 ZIP/client runtime 검증은 수행하지 않았다. 기존2284개는 숨김 geometry의 particle 경고로, 전체 visible 모델 깨짐의 원인이라고 주장하지 않는다. 서버 JOIN/차원 이동·카메라 runtime은 master 담당이다.

master가 CAS 통합 후 최종 팩을 생성하고 particle 경고 소멸·실제 표시를 확인한다. 이 기록 시점에는 main의 기존10개 대상이 모두 아래 시작 해시와 일치했다. 신규 검사와 이 문서는 main에 없었다. 통합 직전에는 다시 확인해야 한다.

## CAS용 SHA-256

아래 경로는 작업 위치 기준이다. `ABSENT`는 작업 시작 시 없는 신규 파일이다. 이 문서 자체의 최종 해시는 반환 메시지에 제공한다.

| 경로 | 시작 SHA-256 | 결과 SHA-256 |
|---|---|---|
| `scripts/qa/test_hidden_shells_w235.py` | `ABSENT` | `7adbd3f6ff83f4f7c5f2fa1fef8ad9150ff16a7ba53fa1669c1d3f8f5caf9c98` |
| `scripts/generate_insert_w207_dust_rock_blues.py` | `e683b173f8931592b798e018e7dcc2b335232e6654c386017936b44c2e6c994a` | `998003df078cb4dcff2b0c45989fa834823a9cfdc348dc99ecc5d038a190c1db` |
| `src/main/resources/assets/destiny/models/weapon_insert_w207_dust_rock_blues/dust_rock_blues_shell_hidden.json` | `8a14f3d181d0260c6814ddce0173d3109f979970d6399a72b5e4b82e0e62862b` | `5ea3353ba7ad6295ed3d4aaada4d7ed434ea53744ce3c6b49520f370ae67d57f` |
| `scripts/generate_insert_w208_first_in_last_out.py` | `c63a9c31d1bc56de58edf1cad7dd1df0bc83583b0f460dcc8e64439ee7627f34` | `e3ea5258db910e991a7be6b5488ea65ac54957a2f2b326cb63be08a1c5b14019` |
| `src/main/resources/assets/destiny/models/weapon_insert_w208_first_in_last_out/first_in_last_out_shell_hidden.json` | `8a14f3d181d0260c6814ddce0173d3109f979970d6399a72b5e4b82e0e62862b` | `7f58b8a3b6d2e68bc987ca1d320b9f6e5bb4e438683b8e5b5d7a47c29d6484b5` |
| `scripts/generate_insert_w221_ikelos_sg_v1_0_1.py` | `2082c9b3115a6f839c54ae7e925571fb038b85d91a111433e9b65c104e8fc261` | `3c90d29a59eb9f1ae30e7e5e154ad1f7e6b630736890932cda9abbfa26834596` |
| `src/main/resources/assets/destiny/models/weapon_insert_w221_ikelos_sg_v1_0_1/ikelos_sg_v1_0_1_shell_hidden.json` | `8a14f3d181d0260c6814ddce0173d3109f979970d6399a72b5e4b82e0e62862b` | `597105433370c8e090e14247ec85a875dfd9e2121b757d4809e7db1a127e04c2` |
| `scripts/generate_insert_w221_mindbender_s_ambition_adept.py` | `24489327e3ecf549cefaa3c0fcc3d85145307155c7b34ec5aa2fe79504a17760` | `07862a74635ca74ca53016e980ab19d38b9a59337f8d7f082d9b1be06772b860` |
| `src/main/resources/assets/destiny/models/weapon_insert_w221_mindbender_s_ambition_adept/mindbender_s_ambition_adept_shell_hidden.json` | `8a14f3d181d0260c6814ddce0173d3109f979970d6399a72b5e4b82e0e62862b` | `c623e536031935b7546e766a325266d15dbcb6a2eb301a0ce296e317430adf8e` |
| `scripts/generate_insert_w221_parcel_of_stardust_fell_to_earth.py` | `9720eb47276cce986ae649b52855c679cf14aad5ec7f96aa110ff3fea8874fa5` | `a32db4fa9bcb1c14445a6232e0e9c5da8ecd9345f9a30418db308c7f66d233d7` |
| `src/main/resources/assets/destiny/models/weapon_insert_w221_parcel_of_stardust_fell_to_earth/parcel_of_stardust_fell_to_earth_shell_hidden.json` | `8a14f3d181d0260c6814ddce0173d3109f979970d6399a72b5e4b82e0e62862b` | `4c966a40c849a61ca055a690ae69dc820d2068780de6eb4b90305dbe8c2eb767` |
| `docs/qa/2026-10-29/w235/model-worker.md` | `ABSENT` | 반환 메시지 참조 |
