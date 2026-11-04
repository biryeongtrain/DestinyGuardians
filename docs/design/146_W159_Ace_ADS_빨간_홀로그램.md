# W159 Ace ADS 빨간 홀로그램

사용자실제플레이프레임과D2기본Ace원본Reticle을대조해철제가늠쇠대신붉은괄호두개+중앙점을적용한다. 스코프후드/유리/파란장식은추가하지않는다.

- source mask green→transparent alpha, source red→sRGB255,33,31. 괄호는source근거,중앙점은사용자프레임근거의authored추가.
- canonical87elements+발광면3=90. emission15,26.3 shade_direction_override,actualitematlas texture경로. 원작PBR/bloom/parallax복원은아님.
- slot3 ADS21sample중19/20에서만점등. ordinaryHIP/third/inspect/reload는원본그대로. native/twohand구도지원.
- 재생성: bundledPillowPython으로scripts/generate_ace_hologram_w159.py [--verify]. art/weapons/w159/source와manifest로오프라인재생성가능.
- 실제26.3파싱·packbake·Vision화면/입력검증과첫atlas실패/fixture실패는[W159 QA](../qa/2026-10-26/w159/README.md)에구분기록.
