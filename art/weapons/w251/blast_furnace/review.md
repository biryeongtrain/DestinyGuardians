# W251 용광로 미술 검수

기본 안료 사진 `/tmp/destiny-weapons-w31/references/blast_furnace.jpg`와 로컬 FBX·diffuse를 직접 열어 확인했다.
원본 좌표·분할 provenance는 design.json의 source, input_sha256, raw_input_sha256에 기록한다.
원본 전체 비례와 긴 연속 질량을 유지하고 다음 부위를 다시 설계했다.

- 긴 앞 외장·receiver를 넓은 면과 실제 사선 어깨로 재구성하고 빨간 총열의 양옆 빈 공간은 유지했다.
- 볼받침의 둥근 단면과 낮은 앞 경사·뒤쪽 내려오는 경사를 원본 사진·rip에 맞춰 추가했다.
- 손 파지 축을 유지한 그립과 기울어진 탄창에 둥근 단면을 넣고 가늠쇠 상단을 사선 어깨로 연결했다.
- Black Armory 패널·쌍열 각인·총구 vent·올리브 탄창 채널과 대각 홈을 world 연속 UV에 그렸다.

실제 출력: body 163, magazine 15, full 178.
full은 분할 부품의 정확한 합계다. 삼각 adapter 0, alpha 윤곽판 0, 1,000 요소 상한 준수.
면 1068개에 명시 UV, 1024 atlas, 2px bleed, 밀도 22 texel/unit.
같은 평면에서 겹치는 solid 조각의 페인트는 world 좌표로 이어진다.
이전 모든 면 사각 테두리·반복 얼룩 대신 제한된 패널선·홈·재질 대비를 사용한다.
밝은 모서리·중간 금속 면·짙은 홈은 재질 정보이며 shader full-bright 보상은 없다.

원본 canonical display 사전은 exact 보존하고 부품 display는 추가하지 않았다.
[8,8,8] carrier·원본 scale·탄창 local 좌표·cover hinge를 유지했다.
손 리깅·ADS display·모션·타이밍·canonical/reload는 변경하지 않았다.
inspection.bbmodel은 별도 검사 파일이며 사용자 DCC scene을 조작하지 않았다.

comparison.png는 실제 기본 안료 사진 + 원본 rip + 이전 semantic 재생성 + W251이다.
측면·앞/뒤 사선·receiver/stock 및 포구 근접을 동일 광원·동일 카메라로 비교한다.
legacy axis/angle은 XYZ로 정규화한 후 렌더한다. 원본 diffuse/부위별 참고색은 PBR 복원이 아니다.
CPU 그림을 직접 확인했다. 이는 native parser·광원·인게임 합격 근거가 아니다.
파싱·유효 좌표·출력 수·면별 UV/opaque texel·texture 경로·assembly·display 및 --verify byte 일치를 확인한다.
중앙 Gradle·서버·Vision·CU는 실행하지 않았다.

통합 시 master는 shared surface manifest의 이 무기 replacementSha256을 새 출력으로 갱신해야 한다.
shared manifest는 소유 범위 밖이므로 수정하지 않았다. 필요한 값은 W251 manifest.json의
required_surface_manifest_updates에 있다. 기존 routing과 canonical sourceSha256은 읽기 전용으로 확인했다.

남은 master native QA:

- 공통 조명 수정 뒤 밝은/어두운 위치에서 금속 면·홈 대비 확인.
- 1/3인칭 휴대·ADS에서 외곽·시야 구멍·손 접촉 확인.
- 탄창 분리/재삽입, 해머헤드는 cover hinge·탄띠와 receiver 접합 확인.
- 10~20개 표시에서 깨짐·눈에 띄는 끊김 관측. 성능 보증 미실시.

재현 명령:

```sh
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/refine_weapon_w251_blast_furnace.py
rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/refine_weapon_w251_blast_furnace.py --verify
```

변경 경로:

- `art/weapons/w251/blast_furnace/comparison.png`
- `art/weapons/w251/blast_furnace/design.json`
- `art/weapons/w251/blast_furnace/inspection.bbmodel`
- `art/weapons/w251/blast_furnace/manifest.json`
- `art/weapons/w251/blast_furnace/review.md`
- `scripts/refine_weapon_w251_blast_furnace.py`
- `src/main/resources/assets/destiny/models/weapon_surface_w123/blast_furnace.json`
- `src/main/resources/assets/destiny/models/weapon_surface_w123/blast_furnace_body.json`
- `src/main/resources/assets/destiny/models/weapon_surface_w123/blast_furnace_magazine.json`
- `src/main/resources/assets/destiny/textures/item/weapon/w123/blast_furnace.png`
