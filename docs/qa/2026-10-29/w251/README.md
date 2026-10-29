# W251 무기 입체·명암 보강

## 요청과 범위

2026-10-29 사용자: 스페이드 에이스·이자나기의 짐과 달리 나머지 무기가 명암이 약하고 너무 네모나 보인다. 첫 배치는 은둔자·매사냥꾼·망치머리·용광로·정신왜곡자의 야망 5종. 원작 기본 안료 사진·리핑 원본을 참고하며 1,000개 상한 안에서 실루엣, 단면, 표면 구분을 보강한다. 앞선 W250의 검·궁극기 3인칭 유저 스킨 요청은 미완료 대기로 보존한다.

## 단계 기록

1. 에이스87·이자나기79개 큐브와 실제 atlas를 기준으로 기존 비교 이미지를 검토했다. 큰 receiver/stock를 상자로 단순화한 부분, 얕은 재질 명도차를 확인했다.
2. 공통 1인칭 셰이더 `profile_view/main.item.vsh`가 vanilla directional lighting 결과를 `Color`로 덮는 것을 확인했다. 모델별 아트와 별도로 복구한다. 손의 skin remap, HUD 투영과 fog 우회는 별개로 유지한다.
3. 기존 작업의 고정 worktree1·4를 재사용했다. 이전 owned delta와 main의 차이는 main의 후속 기능·문서 보강임을 diff로 확인하고 `/private/tmp/destiny-w251/previous-slot-deltas`에 보존 후 갱신했다. slot5에는 미통합 Warlock delta가 있어 재배정하지 않았다. source221,589개 입력의 dirty/untracked 기준선과 복구 archive를 사용한다. worker는 아트2종씩, master는 공통 셰이더·샷건·팩 연결·중앙 QA를 맡는다.
4. 예전 `/tmp` rip/photo 캐시가 비어 원래 catalog의 Drive id로 5개 archive를 복원했다. 원본은 실행하지 않고 데이터로만 읽는다. 기본 안료 사진5종은 `references.json`의 SHA256과 일치했다.

## 검증

실제 PNG와 native 입력/서버 fixture 및 CPU 미리보기를 구분하여 기록한다. 모델 변경에는 61프레임/손 리깅 변경이 없으며 기존 장전 타이밍과 파지·ADS transform을 유지한다.

5. 공통 셰이더에서 무기192 marker의 native 조명 계산을 복원하고 손208 marker의 UV 재해석용 색 처리는 유지했다. 기존 projection·near-plane·fog·HUD/FOV 경로는 바꾸지 않았다. 운영 서버 생성팩에 두 조각만 교체한 비교 후보를 만들어 glslang으로 OpenGL14개 대표 프로그램(item/entity, OIT, per-face/no-cardinal/emissive)을 compile+link했고14/14 통과했다. 최종 QA 생성팩의 core shader4개 SHA256이 최종 컴파일 후보와 일치했다. 전체250경로 인증·Vulkan GPU 성공 주장은 하지 않는다.
6. 운영 서버가 빈 상태임을 로그로 확인 후 save-all flush/stop, BUILD SUCCESSFUL과25565 해제를 확인했다. Mac은 CU Finder의 데스크톱 UI로 잠금 해제 상태를 관측했다. 기존48시간 assertion PID79904를 유지하고 이번 master QA는 별도 bounded7200초 wrapper로 감쌌다.

7. 독립 읽기 전용 검토에서 상위 DisplayHUD도 먼저 `vertexColor=Color`로 덮으므로 단순 제거만으로는 복구되지 않는 결함을 발견했다. weapon snippet 안에서 vanilla `minecraft_mix_light`를 다시 수행하고 entity PER_FACE·NO_CARDINAL 분기도 원본 계산대로 복원했다. skin208은 그대로 두었다. 수정본의 OpenGL 대표14개 compile/link가 모두 통과했으며 독립 재검토도 추가 결함 없이 종료했다. 초기 후보의 컴파일 성공은 명암 복구의 증거로 사용하지 않는다.

8. worker 소유39경로를 baseline hash와 main drift 검사 후 통합했다. 5종의 display 사전은 exact 보존하며 출력은 은둔자66→143(body129+mag14), 매사냥꾼126→170, 망치머리163→245(body147+mag79+cover19), 용광로97→178(body163+mag15), 정신왜곡자104→189다. 삼각 adapter는 모두0이며 1,000상한 안이다. 모든 atlas1024²를 유지하고 노이즈 대신 의미 있는 홈·패널 UV를 사용한다. 공통80target manifest를 재생성했다.

9. targeted JUnit9/9(WeaponSurfaceW1236, NativeParser1, ProfileArmAssets2)을 통과했다. QA 팩84,994,694 bytes에 새 canonical/장전 모델12개 hash가 모두 일치했다. 셰이더4개도 glslang14개에 사용한 후보와 정확히 일치했다. 생성팩84.99MB는 전체 팩 크기이며 이번 증가량이나 GPU메모리량이 아니다.
10. Danmo4GB·26.3·macOS OpenGL에서 Vision client 한 세션으로5종을 확인했다. 처음0,0장소의 기존 검은 QA오브젝트를 발견해 원본 캡처는 보존하고1000,1000의 새 조명/배경에서5종 hip·ADS·native fire·3P·서버장전fixture를 수집했다. ADS/fire10시퀀스 및 neutral장전관찰5시퀀스 모두 completed, 클릭 소비/탄창 감소, 최종 lease 해제·heldKeys빈값·pending0·nativeInput중립을 확인했다. Q키 입력 성공으로 주장하지 않는다.
11. native-hip/ads/third/reload.jpg는 실제 framebuffer를 자르거나 축소한 검수판이다. sources.json은 원본 경로, native-summary.json은 제어·서버 근거다. 명암·단면·홈·ADS 통공을 직접 확인했다. 3P는 정면 휴대 확인 범위이며 전각도 접촉/모든 장전 프레임을 인증하지 않는다. 망치머리 덮개/탄창이 움직이며 장전 뒤 복귀하는 것을 관측했다. 기존 모션·손리깅을 이번에 고친 것으로 보고하지 않는다. Vulkan/Windows·음원 청취·10~20동시표시 성능 인증·실내 전각도는 이번 검증 범위 밖이다. 성능 전수gate로 확대하지 않았다.

12. 실제4개 검수판을 아트 담당 두 worker에게 다시 전달했다. 은둔자·매사냥꾼·망치머리·용광로 모두 새 형상/UV 결함 없이 수락 의견을 받았다. master도 정신왜곡자 원본/비교/실게임을 검토했다. worktree1·4는 삭제하지 않고 idle-needs-refresh/W251로 반환했다. Vision lease 중립을 확인 후 소유 QA클라이언트를 종료하고 QA서버를 저장·종료했다. QA플레이어는 탑으로 돌려보냈다. Ace 교체는 주손 아이템 보호에 막혀 마지막 QA무기 Austringer를 보존했다. 개인 프로필·다른 세션·기존48시간 assertion은 건드리지 않았다.

13. 운영 runServer를 online-mode=true/25565·andlist OP4 설정으로 다시 열고 Done/Polymer 팩생성 성공을 확인했다. 운영팩의 핵심셰이더4개+교체모델12개 bytes hash가 QA팩과 일치했다. 기존 dirty/untracked는 보존하고 W251 소유파일과 pool1·4 delta만 커밋한다. 운영서버는 계속 실행한다.
