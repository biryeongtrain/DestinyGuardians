# W239 — Dynamic FOV 활성화

사용자가 Windows에서 무기·팔 표시가 정상임을 확인한 뒤 Dynamic FOV 활성화를 요청했다.

## 적용

- 런타임 설정 `run/server/config/minigame-lib/shaderfx.json`의 `dynamic-fov-shader`를 `true`로 변경했다.
- 변경 전 설정은 같은 폴더의 `shaderfx.before-dynamic-fov-w239.json.bak`에 보관했다.
- 기존 서버를 정상 종료하고 GraalVM JDK 25에서 `./gradlew runServer --offline --no-daemon --console=plain --max-workers=2`로 다시 기동했다.
- `online-mode=true`와 andlist OP 설정을 유지했다. 접속 주소는 `192.168.35.237:25565`다.

## 확인

- 최신 서버 로그에서 서버 기동 및 Polymer 팩 생성 성공을 확인했다. TCP 25565가 열려 있다.
- 생성 팩의 `assets/minecraft/shaders/include/projection.glsl`이 minigame-lib 원본과 바이트 단위로 일치했다.
- 생성 팩 크기: 85,276,558 bytes. SHA-1: `4bcf44d01ba2fe177fc98089b4ddcb646abe7089`.
- `scripts/qa/compile_profile_view_shader_w238.py` 검사: OpenGL/Vulkan entity/item 프로그램 250개 모두 통과했다. 결과: `/private/tmp/destiny-w239/shader-check/result.json`.
- Windows 실제 ADS 줌 동작은 이번 변경 후 직접 확인하지 않았다. 재접속하여 새 팩을 받은 뒤 확인할 수 있다.

설정과 생성 팩은 ignored 런타임 파일이므로 Git에는 이 작업 기록만 커밋한다. 서버는 사용자 테스트를 위해 계속 켜 둔다.
