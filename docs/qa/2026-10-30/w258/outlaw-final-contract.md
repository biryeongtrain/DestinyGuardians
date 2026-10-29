# W258 W62 Outlaw 단일 파일 반환

소유 파일: `src/gametest/java/kim/biryeong/destiny/test/WeaponOutlawW62GameTests.java` 하나만 편집. 기존20개 및 W176 재편집 없음. main은 읽기 전용.

기준 SHA256: `4a45b1c7dac527cb5a8fda19dec7713441fc6078fcf68255d581e9a35f13d0ca`
결과 SHA256: `fceb9ef25c9b209f31170b6963a65be0333b5750eb54885d9b14b29a01edfd4f`

`repair.patch`는 현재 main 기준본 대비 delta. `baseline/`, `slot-before/`, `result/`, `manifest.json` 포함.

## 실패 근거와 수정

final-run.log:629/636에서 `actualNonlethalHeadshotDealsPrecisionDamageButDoesNotActivate`의 실제 HP 손실이 `8.049988/8.049988`, tick0로 동일했다. 기존 head/body helper는 수평 시선의 높이만 확인했지만 WeaponAiming.direction은 W241 무작위 hip/air cone을 사용하므로 실제 유료 ray의 precision 여부를 보장하지 않았다.

공통 shot helper에서 target과 기대 precision 여부를 명시적으로 받도록 했다. reaim 후 `0x5DEECE66DL` seed로 실제 direction을 미리 샘플링한다. target AABB .03 확장과 실제 precision classifier로 기대 몸통/머리 여부를 검증하고, block collider가 없는 corridor인지 확인한다. 실제 WeaponRuntime.beginUse 직전에 같은 seed를 재설정해 그 ray를 재생한다. ADS 전환이나 AE 수정 없이 기존 hip-fire/recoil reset 계약을 유지한다.

이 클래스 실제 발사 호출 10곳이 해당 helper를 사용한다. precisionKill 기반 인접 처치/장전/소유권 테스트, body final blow, 비치명 정밀 대조군, 능력 처치 후 비치명 정밀 발사, Outlaw 단독 동일 피해, Kill Clip1.25 피해 비교까지 같은 원인의 flake를 방지한다. 모든 실제 ammo payment/HP/precision multiplier/Outlaw credit은 production 경로를 사용한다.

## 보존과 정적 확인

- 기존 GameTest 14개 이름·annotation·timeout 동일. 새 테스트/disabled/manual 전환 없음.
- 기존 check assertion 77개 모두 원문 그대로 보존했음을 AST multiset으로 확인. tolerance .002, 정밀>몸통, 정확한 배율,120틱,33/59틱 장전,24/42틱 credit 및 finite ammo 조건 불변.
- 기준본에 git apply --check 통과. Java tree-sitter 문법 파싱 통과. 명시 target/precision 인자 누락 없음. main 현재 SHA256 기준본과 동일.
- 빌드/Gradle/게임 런타임/Vision/CU 미실행. 타입 컴파일 및 실제 통과는 master의 최종 full 후 관련 targeted 실행으로 확인 필요.
