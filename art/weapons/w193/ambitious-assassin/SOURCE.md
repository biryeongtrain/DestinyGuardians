# W193 Ambitious Assassin

- 기준: 사용자 DDC Weapon Perks 16행, 기본 퍽 hash 2010801679. 원문 HTML/입력 해시는 source.json에 보존.
- Primary 처치당 기본 탄창의 20%, Special/Heavy 10%; 최대 **150% 증가 = 총 250%**, 올림.
- 강화판 +5 Reload는 제외. 처치 카운터는 무기 교체로 지우지 않으며 임의 만료 시간을 만들지 않는다.
- 현재 고정 Bungie manifest의 실제 기본 Trait 13소켓만 노출. 생성기 `scripts/build_ambitious_assassin_w193.py --verify`로 재현.
- 양의 실제 피해를 준 유료 무기 최종타만 집계한다. 직접/폭발은 같은 emission 토큰·시체 중복 억제를 공유한다.
- 수동/자동 timed reload의 탄약 지급 시점에 카운터를 소비한다. 취소·회피·자동 장전집·능력 장전은 발동하지 않는다.
- 유한 탄약은 예비/기존 보존 탄약에서만 옮긴다. 초과 탄창은 legacy overflow debt와 구분해 저장한다.
