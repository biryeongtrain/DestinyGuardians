# W244 줌 이동 배율 worker

작업일: 2026-10-29 (KST). 작업본: `/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1`.
시작 HEAD: `ec038a8fbcc83d0e3322fb1fbc6fe834e5d83a95`. 제공받은 현재 dirty snapshot을 그대로 사용했다. HEAD만으로 현재 제품을 대표하지 않는다.

## 한국어 계약

- `public final WeaponNativeZoom`은 상태와 Minecraft 런타임 의존성이 없는 유틸리티이며 생성자는 private이다.
- 공개 API: `public static double movementScalar(double baseAdsScalar, double effectiveZoom, double progress)`.
- 계산: `lerp(1, baseAdsScalar / max(1, effectiveZoom), clamp(progress, 0, 1))`.
- 세 입력은 모두 유한해야 한다. 기본 ADS 배율은 `(0, 1]`이어야 하며 위반 시 진행률이 0이어도 `IllegalArgumentException`을 던진다.
- 유한한 줌 값이 1 미만이면 음수·0을 포함해 1로 취급한다. 유한한 진행률은 `[0, 1]`로 제한한다.
- 결과는 유한한 `(0, 1]`이다. 극소 기본값/극대 줌의 나눗셈이 0으로 언더플로하면 `Double.MIN_VALUE`로 포화한다. `(1-t) + t*target` 보간으로 완전 ADS 부근의 상쇄를 피한다.
- 호출자(master)가 이 배율을 구한 **뒤에 MovingTarget을 정확히 한 번 적용**한다. 이 유틸리티는 MovingTarget을 처리하지 않는다.
- 이 공식은 사용자가 지정한 **Minecraft 적응 방식**이다. DDC 원작 확정 줌/이동 수치로 제시하지 않는다. DDC 기본 ADS 프로필과 피해 falloff는 변경하지 않았다.
- 바닐라 지상 이동 속도 기반 FOV는 FOV 효과 100%에서 `(1 + speedRatio) / 2`이며 속도비를 0에 가깝게 줄여도 하한은 `0.5`다. 따라서 이동 배율을 그대로 카메라 확대율 또는 역줌으로 해석하지 않는다. 다른 FOV 효과 설정·비행 등의 최종 화면값은 이 계약의 검증 범위 밖이다.
- 예: 기본 `.8`, 줌 `1.25`의 완전 ADS 배율은 `.64`이고 해당 조건의 FOV 계수는 `.82`다. 줌 `4`는 이동 `.2`, FOV `.6`이다. 이 예는 MovingTarget 등 후처리 전 계산이다.

## 배타적 변경 및 해시

시작 시 아래 세 경로는 모두 `ABSENT`였다. 통합 시 master의 현재 대상 경로도 부재인지 확인하고, 이미 생성된 파일이 있으면 자동 덮어쓰지 않는다.

| 경로 | 시작 상태 | 반환 SHA-256 |
| --- | --- | --- |
| `src/main/java/kim/biryeong/destiny/weapon/WeaponNativeZoom.java` | ABSENT | `eccdc8ad3c65b9447376511d2a21e5be8b58dca63dbbd4c561dabd9e853c55ef` |
| `src/test/java/kim/biryeong/destiny/weapon/WeaponNativeZoomW244Test.java` | ABSENT | `1b92992a2c3784b455f17e92db843d4f1f60e507348a53f2f3914c7859003913` |
| `docs/qa/2026-10-29/w244/zoom-worker.md` | ABSENT | 자기 참조 해시는 문서 밖 최종 반환에 기록 |

제품/테스트/보고서의 명시적 편집은 위 세 경로뿐이다. Gradle은 격리 작업본의 통상 build/cache 출력을 생성한다. 공유 main, DDC 데이터, 호출부, 토글 좌클릭·런타임 lifecycle, 서버/클라이언트 소스는 편집하지 않았다. 커밋하지 않았다.

## 전용 검증

Java: `/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home` (`Oracle GraalVM 25+37.1`, `25+37-LTS-jvmci-b01`).
GCB는 CLI로 지정한 작업본 내부 `libs/gcb-server`이며 realpath도 동일하다. 기존 composite dependency substitution을 유지했다.

실행 명령:

```sh
rtk proxy env JAVA_HOME=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home PATH=/Users/qf/Library/Java/JavaVirtualMachines/graalvm-jdk-25/Contents/Home/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin ./gradlew -Pgcb_server_dir=/Users/qf/IdeaProjects/DestinyGuardians-worktrees/w221-ikelos_sg_v1_0_1/libs/gcb-server test --tests kim.biryeong.destiny.weapon.WeaponNativeZoomW244Test --console=plain --max-workers=2
```

결과: **PASS**. 프로세스 종료 코드 `0`, `BUILD SUCCESSFUL in 1m 49s`, 13 actionable tasks executed. 전용 JUnit XML `build/test-results/test/TEST-kim.biryeong.destiny.weapon.WeaponNativeZoomW244Test.xml`에서 테스트 **6개, 실패 0, 오류 0, 건너뜀 0**을 확인했다. 이 클래스만 실행했으며 전체 gate는 실행하지 않았다. 기존 소스의 deprecated/unchecked 및 Gradle 10 호환성 경고가 출력되었으나 빌드 실패는 없었다.

테스트 6개는 저배율/고배율 전환과 양 끝점, 진행률·줌 제한, 기본값 범위 위반, 세 입력의 NaN/양·음 무한대 거부, 극소 양수 보존을 확인한다. 수치 조합 전수 행렬은 만들지 않았다.

서버·QA fixture·CU·Vision·클라이언트는 실행/조작하지 않았다. native client FOV 화면이나 입력을 입증한 결과가 아니며, 호출부 MovingTarget 순서와 좌클릭 토글/lifecycle의 통합 검증은 master 범위다.
