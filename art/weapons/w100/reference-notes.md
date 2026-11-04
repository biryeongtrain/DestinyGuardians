# W100 — The Recluse 장전 동작 참고

## 직접 확인한 영상
- [The Legend Himself — Recluse OverUSED in Shadowkeep? Naw Dawg.](https://www.youtube.com/watch?v=nnr9-n3CdhI), 2019-11-11. Bungie forum post 254388422에서 연결된 실제 플레이 영상.
- 첫 90초 720p video-only를 받아 explicit seek 37.10–38.00의 원본 PNG 8장을 직접 검사했다. 해시/다운로드/seek 근거는 `references/gameplay-provenance.json`.
- 37.10: ADS 탄창 0. 37.30–37.40: ADS를 벗어나 총몸이 기울고 총구가 위로 든다. 37.40 하단 우측에 빠지는 작은 직사각형 부품이 보인다. 37.50: 왼손이 탄창/몸체 아래쪽으로 접근, 총은 화면 오른쪽에서 대각선으로 유지. 37.60–37.70: 왼손 삽입/복귀와 탄약 36 표시. 37.80: 총이 정상 준비 자세로 돌아온다. 38.00: 사격/조준 복귀.
- 손과 이펙트가 교체 부품을 상당 부분 가리므로 개별 탄창의 정확한 3D 궤적/회전/길이는 영상만으로 추출하지 않는다. survey fps 필터 contact의 숫자 라벨은 explicit seek와 어긋나 정확한 타임코드로 사용하지 않았다.

## 구현 계약 — 관측과 근사 구분
1. 원본 ripped FBX의 탄창 연결 부품을 확인해 217개 기존 큐브를 보존하며 몸체/탄창으로 분리한다. UV/재질/얼굴은 그대로 두며 부품 경계 혼합 큐브 한계는 audit에 수치로 남긴다.
2. 초기 조준 해제/짧은 기울임 → 아래로 탄창 이탈 → 삽입 → 짧은 정착 → 원래 HIP 복귀의 읽기 쉬운 21 sample을 작성한다. 총몸은 적당히 총구를 들고 옆면을 드러내며, 탄창은 총몸과 함께 움직이다 별도 아래 이탈/복귀를 한다.
3. 영상은 매우 빠른 역사적 Feeding Frenzy 장면이므로 원작 초단위 속도를 복사하지 않는다. 현재 서버의 실제 reload normalized progress에 정규화하며 gameplay duration/ammo/perk/audio/HUD는 변경하지 않는다.
4. 정확 궤적은 로컬 authored approximation이다. 새 손/양팔 IK/원작 animation을 복구했다는 주장은 하지 않는다. firstperson left/right·native/twohand compensation·HIP endpoint 일치를 검사한다.
5. inactive/모든 다른 context는 기존 item graph로 fallback. 기본 모델/texture/기존 reload graph는 불변. 본인 소유 live reload identity에만 새 모델 적용.
