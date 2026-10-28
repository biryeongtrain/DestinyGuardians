# W229 R2 native 아트 검수

**판정: 제공된 R2 화면 범위에서 붉은 방벽·균열·Nova는 원본색과 구분되며, 필수 아트 delta는 없습니다.** 정적 fixture의 표시 검수와 실제 시전 샘플 검수를 구분했습니다. 실제 팀/관전자 라우팅, 이동 중 붉은 Nova 발사체의 전체 수명은 이 자료로 승인하지 않습니다.

## 근거와 관찰

| 대상 | 확인한 native 근거 | 판정 |
|---|---|---|
| 방벽 normal/red | gallery 왼쪽 진홍/오른쪽 청색, 원본 해상도와 2배 nearest crop | 두 색 모두 사각 외곽·corner·scan ribs·베이스가 읽힙니다. 구멍 사이로 하늘·지면이 보이며 불투명 사각판으로 막히지 않습니다. 보이는 면에 누락 텍스처, 큰 UV 탈락, 찢어진 외곽 또는 비정상 돌출은 없습니다. 점선/세로 점무늬는 설계된 alpha aperture/scan 패턴입니다. |
| 균열 normal/red | gallery 왼쪽 연홍/오른쪽 백색·청백색 링 | 세 링과 내부 flow가 구분되고, 지면에 눕는 방향이 일치합니다. 원근상 타원은 정상입니다. 적군색도 식별되며 사각 바탕이 불투명하게 드러나지 않습니다. 오른쪽 일부 가림은 1인칭 손과 화면 구도이며 면 소실 근거가 아닙니다. |
| Nova normal/red | gallery 방벽 앞의 진홍/보라색 구체 | 두 구체 모두 같은 계단형 둥근 실루엣과 면별 명암이 보입니다. 큐브 단차는 기존 38요소 임시 VFX 형상이며 텍스처 균열이 아닙니다. 색 구분과 모델 존재는 확인됩니다. 화면상 지름이 약35px이므로 미세 texel 품질이나 모든 후면까지 판정하지 않습니다. |

붉은 방벽은 세로면, 붉은 균열은 지면 링, 붉은 Nova는 떠 있는 구체여서 동일 적군 팔레트 안에서도 형태로 구분됩니다. 보이는 범위에 검정/자홍 checker 누락 텍스처, 넓은 면의 뒤집힘·소실은 없습니다.

## 실제 시전 샘플

- `titan-class-sample-00..09.png` 10장: 00..04에는 방벽이 아직 없고, 05..09에는 청색 방벽이 지속해서 보입니다. 특히08 원본에서 외곽·다수 가는 rib·투과 패턴이 확인되고 뒤의 소와 아이템이 계속 보입니다. 가까운 카메라에서 화면을 크게 채우는 구도이며, 관찰한 샘플 사이에 갑작스러운 면 붕괴나 뒤집힘은 없습니다.
- `warlock-class-sample-00..07.png` 8장: 00 이후01에서 지면 링이 나타나고07까지 유지됩니다. 03 원본에서 백색 외곽·안쪽 링·바닥 위 얇은 높이가 읽힙니다. 화면 아래로 잘린 부분은 카메라에 가까운 지면 영역입니다. 보이는 호가 지면을 벗어나 세로판으로 서거나 큰 사각면으로 막히는 현상은 없습니다.
- `warlock-void-super-start-sample-00..09.png` 10장: 실제 cast 중 캐릭터 동작·보라 입자·화면 색 효과가 주로 보입니다. 01..06은 플레이어와 입자가 투사체 관찰을 가리고,04 원본에서도 전체 구체가 분리된 큰 면적으로 보이지 않습니다. 따라서 이 start 시퀀스를 붉은 발사체의 비행·표면·팀색 전환 성공 근거로 삼지 않았습니다. 구체 아트의 normal/red 판정은 gallery가 직접 근거입니다.

`reviews/class-vfx-review.jpg`는 제공된 대표 프레임 묶음으로 함께 확인했습니다. 보라 입자와 cast 화면색은 모델 PNG와 별도 효과이며 이번 적군 텍스처가 그 효과까지 붉게 바꿨다고 해석하지 않습니다. 샘플 PNG 검수만으로 연속 영상의 모든 순간 반짝임/z-fighting이나 FPS를 보증하지 않습니다.

## 최종 scale/anchor 기록

master가 실제 단위 형상에 맞춰 확정한 값이 앞선 동결 문서의 .18보다 우선합니다. 방벽은 **unit cube bounds `[0,0,0]–[16,16,16]`, anchor `[8,8,8]`, scale `[width,height,THICKNESS]`, 최종 THICKNESS=.12**입니다. width3/height2.4라면 `[3,2.4,.12]`이며 중심배치·+Z normal·NONE 컨텍스트를 유지합니다. 기존 BlockDisplay 모서리 offset을 다시 넣지 않습니다. 형상/UV delta는 필요 없습니다. 앞선 frozen .18 metadata는 보존했으며 이 검수 기록에 최신값을 명시했습니다.

`fixtures/enemy-gallery-spawn.json`은 normal/red 두 방벽 모두 scale `[2.7,2.2,.12]`, 링은 `[5,1,5]`(반경2.5), Nova는 `[1.3,1.3,1.3]`으로 지정한 **정적 전시 fixture**입니다. 따라서 gallery의 화면 크기를 실제 gameplay width3/height2.4·균열 반경4의 실측 증거로 사용하지 않았습니다. 정면 PNG로 .12 두께나 충돌 정합을 수치 실측했다고도 주장하지 않습니다. 실제 균열 반경4는 기존 canonical 반경8에 scale `[8,1,8]`, ground+.04 원점 계약을 유지합니다.

## 반환/변경

**필요 delta 제안: 0.** 현재 증거만으로 색·UV·형상을 다시 바꿀 이유가 없습니다. viewer/team routing은 미검증으로 남깁니다. 공유 build/game/source/asset은 변경하지 않았고 게임·Vision/CU를 조작하거나 재실행하지 않았습니다.

읽기 전용 원본: `/private/tmp/destiny-w229-native-r2/`. 이 검수의 새 출력만 `/private/tmp/destiny-w229-props/final-native-r2-review.md` 및 `/private/tmp/destiny-w229-props/review-r2-native/`에 생성했습니다. 기존 base90+R2 30+Nova12+enemy118, 합계250개 SHA256SUMS 항목은 그대로 검증됐습니다.

## 증거 파일

- [원본 gallery](/private/tmp/destiny-w229-native-r2/frames/enemy-variants-gallery.png)
- [gallery crop 확대](/private/tmp/destiny-w229-props/review-r2-native/native-gallery-closeups.png)
- [Titan class 10장](/private/tmp/destiny-w229-props/review-r2-native/titan-class-contact.png)
- [Warlock class 8장](/private/tmp/destiny-w229-props/review-r2-native/warlock-class-contact.png)
- [Nova start 10장](/private/tmp/destiny-w229-props/review-r2-native/warlock-void-super-start-contact.png)
- [입력 이미지/metadata 해시](/private/tmp/destiny-w229-props/review-r2-native/inputs.json)
- [기존 동결 파일 검증](/private/tmp/destiny-w229-props/review-r2-native/frozen-check.json)
