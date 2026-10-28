# W225 단계 기록

1. W224는 실제 26.3 바이트코드와 297개루트조사로다음수정을정했으므로이전 goal turn 은 progress 다. full weapon/HUD goal 을축소하거나완료처리하지않았다.
2. RTK/AGENTS 및 Polymer·Vision·Minecraft Testing 지침을참조했다. master 는표시 generator·통합·native/CU 를소유하고 sidecar 는실제교체영향을읽기전용감사했다. 작은공유메타데이터변경이므로새 worktree 를만들거나기존 5슬롯을갱신하지않았다.
3. CU 에서잠금해제데스크톱과 QA 포트공석을확인했다. 기존소유 QA 서버 fixture,새격리 client-run,keep_awake coordinator 를사용하고별도 48시간 assertion 을보존했다.
4. 수정전 6개 native 발사/장전/ADS 시퀀스를확인했다. Ammit/Ace 의첫사용표본에서큰손내림을관찰했다.
5.297개 wrapper 에 false/scale0정책을적용했다.290개 root 외 125,087개생성파일해시는같았다. 리그·61pose·전투/탄약코드는수정하지않았다.
6. 실제 ClientItem root codec 검사를기존테스트에추가했다.8개 class 의 32개 JUnit 과 assemble 이통과했다. 서버 pack 의 297개 root 도확인했다.
7. 수정후 3종 9개 native 발사/장전/ADS 시퀀스를수락했다. 첫발사내림억제와장전·ADS·복귀를 PNG 로확인하고서버탄약/장전상태와중립입력도대조했다.
8. F 교체시도 3건은능력입력과 fixture load 보호때문에실제교체가아니므로무효화했다. CU 목록은 live Java 앱을조작대상으로노출하지않아번호키입력도보내지않았다.
9. 별도실제인벤토리교체 fixture 로 W91/W113의 STOW/READY4방향과일반 2방향을검수했다. 이는 native hotbar 검증이아니다. 자체모션없는조합의즉시전환과일부새무기선노출은잔여한계로남겼다.
10. 소유 runtime4개모두정상종료,포트공석,별도 48시간 awake 유지,기존워크트리보존을확인했다. 수락한표시정책·관련테스트·생성 root·증거만범위지정커밋한다. 기존미커밋작업은보존한다.
