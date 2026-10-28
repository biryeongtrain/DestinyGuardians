# W225 발사·장전 기본 손 내림 억제

2026-10-28. W224 조사에 이어 무기 표시 루트에 `swap_animation_scale=0`을 적용했다. 탄약 저장, 장전 61pose, 손 리그, 입력과 전투 코드는 변경하지 않았다.

## 변경

`build_first_person_hands_w201.py`가 297개 손 모델 루트에 `hand_animation_on_swap=false`와 `swap_animation_scale=0`을 함께 출력한다. 이미 scale0이던 7개를 제외한 290개가 변경됐다. 나머지 125,087개 생성 파일의 해시는 같고, 큐브·팔 좌표·장전 자세의 추가/삭제도 없다. [생성 delta](generated-delta.json).

교체 억제 false 만으로 막히지 않던 26.3 `itemUsed` 손 높이 초기화의 시각 변위를 없앤다. 기존 자체 반동·장전·교체 transform 은 남는다. 손 모델의 기본·장전·삽입·ADS·복귀 경로에 같은 정책을 적용했다.

## 검증

- [빌드](build.json): 실제 26.3 ClientItem codec 과 기존 장전·교체 관련 32개 JUnit, assemble 통과. 대표 root 의 속성이 실제 codec 에서 false/0으로 해석되는지 검사했다. 현재 dirty/untracked 통합본의 빌드이며 깨끗한 HEAD 만의 재현 인증은 아니다.
- [생성 pack](pack-after.json): 실제 서버 pack ZIP 의 297개 root 설정을 확인했다.
- [수정전](before-native-validation.json): Ammit AR2·Ace of Spades 의 6개 발사/장전/ADS native 시퀀스. 실제 PNG 에서 첫 사용의 큰 내림을 관찰했다.
- [수정후](after-native-validation.json): 위 2종과 Dust Rock Blues 의 9개 발사/장전/ADS native 시퀀스를 수락했다. 서버 탄약 감소와 장전 true→false, 최종 회복을 확인했다. 각 lease 와 가상키/nativeInput 이 중립으로 복귀했다.
- [교체 fixture](switch-fixture-validation.json): 실제 인벤토리 stack 을 교체해 W91/W113 양방향 4개루트의 STOW/READY/종료를 관찰했다. 일반조합 2방향도 확인했다. selector 를 위조하지 않았고, native 번호키 검증으로 세지 않았다.
- [실화면검수](review.json): master 가 원본 PNG 와 아래 시트를 확인했다. 캡처는 틱 구간으로 묶인 표본이며 정확한 동일 프레임이나 연속 60fps 영상이 아니다.

![발사 첫 표본 비교](vision/fire-first-frame-comparison.jpg)

[발사 전후 전체 표본](vision/fire-before-after.jpg) · [장전](vision/reload-after.jpg) · [ADS](vision/ads-after.jpg) · [교체 fixture](vision/switch-fixture.jpg).

## 무효화한 검증

첫 교체 시도의 F native 입력 3건은 능력으로 처리돼 수류탄을 발동했다. fixture 의 기존 combat item 을 덮는 load 도 보호 규칙에 막혔다. 입력 transport 가 완료됐어도 무기교체 합격이 아니다. [무효화사유](switch-input-correction.json)와 실패 이미지를 보존했다.

별도 소유 standby 클라이언트에서 CU 실제 번호키를 시도하려 했지만, CU 앱 목록이 실행 중인 Java/Minecraft 를 노출하지 않았다. 다른 foreground 앱에 키를 보내지 않았다. 이후 서버 fixture 로 실제 렌더 경로만 검증했다. [CU 기록](native-app-attempt.json).

## 남은 한계

- 자체 모션이 없는 무기 조합은 즉시 바뀌어 보인다. Handling 의 게임플레이 대기시간은 유지된다.
- 일부 실제 stack 교체의 첫 표본에서 새 무기 idle 이 잠깐 보인 뒤 서버의 이전 무기 STOW 가 도착한다. 이 초기 전환 문제는 해결했다고 하지 않는다.
- 정적 item-model pose 의 서버 약 20Hz 단계감과 연속 보간은 별도 문제다. 이번에 Blender 리그나 61pose 를 수정했다고 하지 않는다.
- native 번호키, 전무기조합, 다인 성능, 오디오 청취는 이번 검증 범위가 아니다. 전체 무기/HUD goal 은 계속 active 다.

## 재현·정리

[실행자료](reproduce/README.md), [단계기록](step-log.md), [종료확인](postflight.json). 모든 소유 client/server 는 정상 종료했고 8102/25611은 비었다. 별도 48시간 awake PID79904와 기존 5개 worktree 는 보존했다. 일반 프로필/월드와 외부 리핑 원본은 변경하지 않았다.
