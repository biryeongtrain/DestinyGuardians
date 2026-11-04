# 반환 파일 규격

`templates/manifest.json`을 `return/manifest.json`으로 복사해 실제 값으로 채운다. template:true는 실제 결과에서 false로 바꾼다. 미확인 필드는 null/unknown으로 유지하고 실패 원인을 기록한다. 템플릿 자체를 성공 결과로 제출하지 않는다.

```text
return/
  manifest.json                # 전체 상태·빌드·도구·clip별 데이터
  REPORT.md                    # 성공/실패/미확인, 다음 조치
  steps.md                     # 단계 기록(인증정보 제외)
  clips/<stable-clip-id>/
    source/clip.bin            # 원본 bytes, 실제 원래 파일명은 manifest에 매핑
    source/skeleton.bin
    source/runtime_rig.bin
    decoded/weapon.fbx         # Charm 직접 export 성공 시
    decoded/weapon_FirstPerson.fbx
    decoded/animation.gltf     # parser 성공했을 때만, 참조 .bin 포함
    decoded/raw.json           # 있으면 제공
    decoded/retarget.json      # 있으면 제공
    blender/source.blend       # 가능할 때, 원본과 보정본 분리
    preview/playback.mp4       # 실제 decoded 동작
    preview/contact-sheet.png
    bone-map.json
    events.json
    parse.log
  provenance/packages.json     # 실제 사용 package 파일명/해시/base-patch 의존
  provenance/tool-versions.json
  provenance/requirements-freeze.txt
  provenance/patches/           # 직접 수정한 parser/unpacker diff
```

전체/clip별 status: `not_attempted`, `blocked_auth`, `tag_not_found`, `raw_extracted`, `parse_failed`, `decoded_unverified`, `verified_in_blender`, `partial`. 부분 성공은 clips별로 분리한다. 시각 검증을 못 해도 raw를 반환하면 Mac에서 이어갈 수 있다. skeleton/rig 미확보는 세트 완성으로 세지 않는다.

Charm FBX를 실제 재생 확인했지만 raw3종 일부가 없으면 status=partial, verification.blenderPlayback=true로 기록하고 누락을 적는다. FBX를 우선 반환한다. files.weaponFbx / files.firstPersonFbx에 경로를 추가할 수 있다. 별도 parser 결과가 없다고 직접 FBX 성공을 실패로 처리하지 않는다.

clip별 필수 메타데이터:
- source tag 문자열/실제 tool 입력/endianness, packageID/entry 및 실제 package들, skeleton/rig 대응, hash와 size.
- 같은 build에서 추출했는지, 게임 buildID·depot/manifestID(모르면 null+확인 방법), tool commit/release/binary hash·명령·변경점.
- family, weapon identity와 confidence, action/variant, perspective와 evidence. 일반HC→Ace 고유로 무단 격상하지 않는다.
- joints/channels/key count·fps 출처·start/end·duration, 좌표/scale/local-world 설명, bone/attachment map와 중요한 손·부품 접촉 event.
- glTF 채널/키 확인 및 Blender 실제 재생 결과·warning·미지원 branch. README의 보고127keys/4.2초를 측정값 칸에 그대로 복사하지 않는다.

원본 게임 전체·.pkg/.dll/.exe·Steam 인증 캐시·계정 토큰은 ZIP에서 제외한다. 필요한 작은 raw3tag와 decoded 파일·프리뷰·문서만 넣는다. pack_return.py는 파일목록/해시와 기본 구조를 점검하고 ZIP을 만든다. 결과의 동작 정확성이나 로그의 비밀정보 부재를 자동 보증하지 않으므로 REPORT와 로그를 직접 검토한다. 실패 상태를 숨기지 않는다. 수십GB의 mesh/texture/게임 복제본은 필요 없다.

Mac으로 보내기: 최종 ZIP+옆의 .sha256을 이 대화에 첨부하면 된다. 별도 서버 업로드/Discord 메시지 발송은 필요 없다.
