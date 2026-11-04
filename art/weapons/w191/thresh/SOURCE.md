# W191 Thresh 출처와 적용

- 사용자 지정 DDC Weapon Perks 227행의 `<td>` 이름 `Thresh` 완전 일치로 원문을 선택했다. raw HTML·텍스트·입력 SHA-256은 `source.json`에 보관한다.
- 공식 manifest `245114.26.10.13.2000-1-bnet.66137`의 로컬 inventory/plugsets와 지정 `sockets.json`을 사용했다. 전체 manifest를 새로 내려받지 않았다. 정확한 6개 무기의 trait category `4241085061`, 실제 randomized pool, `isFakePlugSet=false`, `currentlyCanRoll=true`와 기본 특성 해시를 재확인했다. 각 소켓·매칭 plug 증거를 보관한다.
- 기본 궁극기 에너지 1%, 융합 소총·글레이브·산탄총·저격총은 1.5%를 `setSuperEnergy`로 더하고 1에 제한한다. 선형 융합 소총·유탄 발사기에는 예외 수치를 적용하지 않는다.
- 탄약을 실제 소비한 검 공격도 해당한다. 글레이브 근접은 제외한다. 기존 공통 처치 궁극기 보상은 그대로 별개로 유지되며 여기서 `AbilityService.onKill`을 호출하지 않는다. 강화 1.33%/2%는 제외한다.
- 실제 탄약 지불 후 `capture(p)`하고 동일 토큰을 직격·payload/splash에 전달한다. 양수 실제 피해로 확정된 최종 처치만 `killed(p,token,corpse)`에 전달하며 토큰별 시체 객체 중복을 막는다. 원래 소유자·차원·runtime/data/직업·스택·정확한 선택 롤을 확인한다. 원래 무기를 여전히 소유하면 비행 중 보관을 허용한다.
- master 통합: 공유 trait 등록, DamageTraits 토큰, 실제 피해/처치 연결 및 update/편집/제거/궁극기/직업/차원/종료 cleanup 훅이 필요하다. 샘플 사이의 보이지 않는 제거 후 재획득은 추적하지 못하므로 실제 변경 훅은 `changed`/`edited`/`cleanup`을 호출해야 한다. 읽기 경로는 첨부 데이터/runtime을 만들지 않는다. HUD는 실제 에너지 변화 때만 갱신한다.
- 생성: `rtk proxy python3 scripts/build_thresh_w191.py --root <이 워크트리 절대 경로>`. 생성기는 조회·증거 검증·소유 산출물 작성만 한다. 게임/Vision/UI 검증은 이 워크트리에서 실행하지 않는다.
