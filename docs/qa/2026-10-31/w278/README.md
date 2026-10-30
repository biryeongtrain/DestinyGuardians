# W278 장전 종료 순간이동 수정

## 증상
장전이 끝나고 기본 자세로 돌아갈 때 총과 팔이 한 프레임에 옆으로 튀었다.

## 원인
- 장전 뱅크 61포즈 자체는 마지막 포즈가 기본 자세와 일치했다(모델 수치 측정, `/private/tmp/w278/m6.py`).
- 양손 무기(석궁 운반체)의 1인칭 뷰는 `ProfileWeaponView.handMatrix`에서 석궁 보정(X -0.64, Y축 10°)을 항상 뺐다.
- 그런데 W207 이후 장전·삽입 뱅크 대부분은 양손 분기에도 한손(native) 그립 포즈를 그대로 넣었다. 기본 자세 그래프만 양손 전용 포즈를 갖는다.
- 그래서 장전 중에는 보정이 이중으로 적용돼 전체가 0.64블록 옆으로 밀려 있다가, 기본 경로로 돌아오는 순간 원위치로 점프했다(`ammit-before-jump.png`).

## 수정
- `ProfileWeaponView.carrierCompensated`: 현재 CMD로 양손/한손 그립 포즈를 각각 평가해 같으면 석궁 보정을 빼지 않는다. 양손 힙 X 위치는 유지.
- 보정 여부가 바뀌는 프레임은 보간하지 않고 즉시 적용(모델 경로가 같은 틱에 바뀌므로).
- 단위 테스트 `ProfileViewFramingTest.carrierOnlyForRoutesWithDistinctTwoHandPoses`.

## 검증
- 단위: ProfileViewFramingTest 3/3, WeaponFireMotionW242Test 10/10.
- Vision(틱레이트 5, 6~8 fps 캡처): Ammit AR2, IKELOS SMG는 장전 끝에서 기본 자세로 연속 이동(`ammit-after.png`, `ikelos-after.png`). 스페이드 에이스(한손, 기존 경로)는 변화 없음.
