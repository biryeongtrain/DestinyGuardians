# 공식 Danmo 4.6_263c staging 조사

- Modrinth project: xmplRWXx / version: TL0AN9Uv / version_number: 4.6_263c
- 원본 파일: Fabric 26.3 1.0.0.mrpack. 내부 index name/versionId는 Fabric 26.3 / 1.0.0이다.
- 대상: Minecraft 26.3 / Fabric Loader 0.19.5. Mac의 1.21.8 Danmo는 사용하지 않았다.
- 범위: 이 전용 폴더에만 다운로드·staging·보고서 작성. active QA/main/일반 프로필 변경·기동 없음.

## 다운로드 및 안전한 복사

- index mods 61개: index에 제공된 모든 SHA 및 파일 크기 검증 완료.
- overrides mods 1개 포함 총 62개 JAR, 327,169,950 bytes.
- 원본 mrpack은 Modrinth SHA-1/SHA-512와 크기를 검증했다. overrides는 검증된 archive의 CRC 및 개별 SHA를 확인했다.
- archive/index 경로의 절대경로, 상위 이동, 역슬래시, 드라이브 구문, 중복, symlink를 거부했다. 압축 전체를 추출하지 않았다.
- 계정/auth/e4mc/Via 관련 설정은 복사하지 않았다. 모든 index 모드 JAR 다운로드는 사용자 지정 범위에 포함한다.
- 렌더 config 허용 목록: iris/renderscale/sodium/moreculling/entityculling/packforge/eg_stop.
- 실제 복사한 config: 0개. archive에는 imblocker 설정과 빈 options.txt만 있으며 둘 다 제외했다. staged/config는 빈 폴더다.

## 사용자 실행 로그와 주요 버전 차이

| 모드 ID | 사용자 로그 | 공식 팩 metadata | 판정 |
|---|---|---|---|
| gcbmod | 4.0.0 | 4.0.0 | 일치 |
| iris | 1.11.6+mc26.3 | 1.11.7+mc26.3 | 다름 |
| sodium | 0.9.2+mc26.3 | 0.9.2+mc26.3 | 일치 |
| renderscale | 1.4.0-alpha.6 | 없음 | 로그에만 있음 |
| packforge | 1.4 | 1.4.1 | 다름 |
| polymer-bundled | 0.18.2+26.3 | 0.18.4+26.3 | 다름 |
| polymer-qol | 없음 | 1.0.3+26.3 | 공식 팩에만 있음 |
| fabric-api | 0.161.0+26.3 | 0.163.0+26.3 | 다름 |
| entityculling | 1.11.2 | 1.11.3 | 다름 |
| trender | 1.0.17 | 1.0.17 | 일치 |
| moreculling | 1.9.0-beta.1 | 1.9.0 | 다름 |
| eg_stop_unloading_my_shaders | 1.6.0+26.3-rc-1 | 1.6.0+26.3-rc-1 | 일치 |

- 공식 변경 기록: `Removed RenderScale (*Resource pack compatibility issue)`.
- 따라서 공식 4.6_263c staging은 사용자 로그의 완전 동일 복제가 아니다. 위 변경 기록은 이 서버 문제의 원인 확정 증거가 아니다.
- trender 등 중첩 JAR는 metadata를 재귀 조회했다. 전체 버전 비교는 user-version-comparison.json에 있다.

## GCB exact 4.0.0

- 공식 mrpack의 overrides/mods/gcbmod-4.0.0.jar에 실제 포함돼 있다. Modrinth metadata에도 embedded dependency로 등록돼 있다.
- JAR의 fabric.mod.json: id=gcbmod, version=4.0.0, Minecraft ~26.3, Fabric Loader >=0.19.0.
- SHA-256: `c281d17909ca6dd7422be24b89b325d7e83608ff89f9e0f76e94782871206d11`
- metadata 공식 소스: https://github.com/eiqq/GCB-mod
- 공식 release: https://github.com/eiqq/GCB-mod/releases/tag/v4.0.0
- GitHub 공식 release asset digest가 위 SHA-256과 정확히 일치한다.
- 공식 release JAR를 staged-extras/gcbmod-4.0.0.jar에 별도로 직접 다운로드했다. 69,810 bytes이며 공식 digest 및 mrpack override와 byte 단위로 일치한다.
- 별도 다운로드 URL/크기/SHA-1/SHA-256/SHA-512는 staged-extras/download-manifest.json에 기록했다. staged/mods에 이미 동일 JAR가 있으므로 extras를 중복 설치할 필요는 없다.
- source tag/commit: v4.0.0 / `479382323474dafc5163f4dc089a37cbf18b29e6`
- 고정 source tree: https://github.com/eiqq/GCB-mod/tree/479382323474dafc5163f4dc089a37cbf18b29e6
- work/gcbmod 4.1.1은 exact 증거로 사용하지 않았다. 사용자 설치 JAR의 해시가 없으므로 사용자 바이너리와의 byte 동일성은 별도 확인 대상이다.

## 반환 파일

- download-manifest.json: 각 index URL/예상 SHA/실제 SHA/크기, override provenance, 제외 경로.
- archive-inventory.json / modrinth.index.json / version.json: 원본 구조·공식 metadata.
- mod-inventory.json / user-version-comparison.json: root 및 중첩 모드 metadata와 로그 대조.
- gcb-source-provenance.json / gcb-4.0.0-proof.json: 공식 release/tag metadata 및 digest 일치 증거.
- SHA256SUMS: staged 모든 파일 및 반환 문서 SHA-256.
