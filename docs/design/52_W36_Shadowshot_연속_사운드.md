# W36 — Shadowshot를 나누지 않고 한 번 재생

사용자요청: 준비부터발사/잔향까지음원을나누지않고쭉이어지게한다.
원본17:27.47–17:29.70의연속2.23초를단일Vorbis로사용한다.기존클립5개접합/무음삽입은아니다.
원래영상mix의환경음/충돌소리도함께남을수있으며독립청음으로확정하지않았다.

## 서버
성공한Void발동start이전체파일1회재생. draw/fire/impact/end별도호출없음.
모델모션/7틱자동발사/착탄판정/닻활성화는유지.영상mix충돌잔향은실제거리별로재트리거하지않는다.
취소에도별도end재생없이one-shot자연종료. Arc/Solar는변경없음.
기존phase키는역사/audition호환자산일뿐시전에서재생하지않는다.

## 재현·증거
`rtk proxy python3 scripts/audio/import_shadowshot_w36.py` (원본SHA pin,fetch없음)
`rtk proxy python3 scripts/audio/import_shadowshot_w36.py --check`
W33/W34importer후속실행도W36최종overlay유지.
[QA/단계별검증](../qa/2026-10-23/w36/README.md).
