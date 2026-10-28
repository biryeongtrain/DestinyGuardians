# W234 퍽 검증용 원본 보존

W170·W171·W172·W176 검사가 삭제 가능한 `/tmp` 경로를 직접 읽던 문제를 수정했다. 기존 sourcePins의 전체 원본 SHA-256과 바이트 수는 그대로 검증한다. 선택 레코드만 추출한 파일을 전체 원본으로 간주하거나, 자료가 없을 때 검사를 건너뛰지 않는다.

4종의 완전한 원본을 `pinned-original-sources.zip` 하나에 보존했다. 원본 합계211,847,806바이트를9,035,688바이트로 무손실 압축했다. 압축본 SHA-256은 `c39000dc1396093af0779d46081d79bcd6858400cc87091030a0e9e29e2fb134`이다. 테스트 전용 art 자료이므로 서버 JAR·리소스팩에 포함되지 않는다.

| 원본 | 바이트 | 전체 원본 SHA-256 |
|---|---:|---|
| inventory | 199128691 | `b47bba01acdcb7c08e28726647864efefea8ffe73a7098d1c725c7118545b94c` |
| plugSets | 10438797 | `8e3e4625cefca0fcec28524b2de7e65020fe1a7111fa38aa079ad4974cd67959` |
| manifest | 188873 | `bf6fd27036df7d87a2ea03d0e688b7c0b7cc76a9c3ff783ad14b3f14f4d07dce` |
| clarity | 2091445 | `881ed03880ad1869f4c82e2f0c879cacc3f5e9feae21b2d51ae80a2002175384` |

inventory는 남아 있던 W30 원본, plugSets는 당시 Bungie 컴포넌트 URL에서 복구한 동일 원본이다. manifest와 Clarity는 보존된 W83 원본과 일치한다. 최신 Manifest 응답으로 예전 자료를 대체하지 않는다. 정확한 URL·복구 근거·압축 entry는 `pinned-sources.json`을 따른다.

검증기는 상대 경로의 저장소 자료는 해당 파일에서 직접 검증한다. 예전 절대 경로는 출처 식별자로만 사용하고 `/tmp` 파일을 읽지 않는다. 명시한 해시 캐시 → 저장소 보존 사본 → 압축본 순으로 찾으며, 존재하는 자료가 변조됐다면 다른 자료로 조용히 넘어가지 않고 실패한다. W83 사본이 없어도 압축본에4종이 모두 있어 오프라인 검증할 수 있다. 원본 전체를 스트리밍으로 해시하여 큰 JSON을 메모리에 한꺼번에 올리지 않는다.

```sh
rtk proxy python3 -B scripts/qa/verify_profile_sources_w234.py --self-test
```

위 명령은 네트워크나 원본 쓰기 없이87개 source pin·생성기4개·출력14개를 검증한다. 임시/W83 원본이 없는 격리 검사와 변조·길이·누락 등9개 거부 사례도 포함한다. JUnit에서도 실제 원본4종의 압축본만 사용하는 경로를 검사한다.

캐시를 별도로 만들 때만 다음 명령을 명시적으로 실행한다.

```sh
rtk proxy python3 -B scripts/qa/verify_profile_sources_w234.py --populate-cache --cache-dir /absolute/cache
```

이후 `DESTINY_PROFILE_SOURCE_CACHE`로 캐시를 지정할 수 있다. 검증기는 자동 다운로드하지 않는다. 압축본 재생성은 catalog의 reproduce 명령으로 수행하며, 동일 원본·고정 ZIP timestamp·순서·압축 설정에서 바이트가 같은지 검증한다. `--recover`는 명시적인 재생성에서만 네트워크 복구를 허용하며, 원본 해시와 크기는 계속 필수다.

기존 생성기·역사적 manifest·출력 수치·게임 로직은 변경하지 않았다. 전체 회귀·빌드 결과는 `docs/qa/2026-10-29/w234/README.md`에 기록한다.
