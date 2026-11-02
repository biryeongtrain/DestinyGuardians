# 다음 버그 수정 작업용 기록 — 2026-11-02

이번 목표 HUD 범위 밖에서 발견한 검사 실패입니다. 전체 검사 전 기준 실행을 하지 않았으므로
HUD 변경 전에도 동일하게 실패했는지는 별도 재현이 필요합니다. 이번 작업에서 이 파일들을 수정하지 않았습니다.

- `ReloadW168AustringerTest.exactSourceElementsAndUvPartitionWithoutDuplication()`
- `WeaponSilhouetteW112AssetTest.currentSourceInputsAndAllOutputBytesMatchManifestHashes()`
- `WeaponSurfaceW115Test.everyExistingAimGripInspectAndReloadPoseResolvesToExactlyOneReplacedGeometry()`
- `InsertW179MindbenderTest.canonicalBodyAndUvsExactAndConnectedHiddenShellBudget()`
- `GoldenGunHudW122AssetTest.allCurrentInputsAndFourOutputHashesAreExact()`
- `GoldenGunHudW122AssetTest.dedicatedTransportPreservesTintAndOnlySuperSelectedBranchChanges()`

실패 요약: 골든건 입력/출력 해시 및 전송 분기 계약, 무기 실루엣 manifest 해시,
Mindbender 본체/UV 계약, Austringer 분리 메시/UV 계약, 무기 표면 pose 해시.
자세한 메시지는 `full-test-result.json` 참조. 기대값을 새 해시로 덮어 통과시키지 않았습니다.

추가 런타임 로그: `destiny:profile_arm` 모델의 누락 texture 참조 경고.
목표 HUD의 폰트·레이어 로딩 오류는 발견하지 않았습니다.
이 경고가 실제 팔 표시에 주는 영향은 다음 버그 재현에서 확인해야 합니다.

사용자가 플레이하며 발견한 버그는 이후 전달받아 이 목록과 함께 우선순위를 정합니다.
