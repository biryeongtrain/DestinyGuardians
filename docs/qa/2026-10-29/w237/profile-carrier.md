# W237 native PROFILE 팔 carrier — 작업자 반환

## 소유 범위와 통합

Jason은 고정 worktree슬롯4(w221-pyroclastic_flow)를 재사용했다. refresh.json은 main HEAD5b17a2fa·dirty/untracked 포함·mainModified=false를 확인한다. 소유 신규 파일은 ProfileSkinArmCarrier.java, ProfileSkinArmCarrierTest.java와 이 문서3개다. master만 서버·Vision·셰이더·lifecycle을 조작했다. 작업자 변경 전 비소유 source903개 SHA는 반환 때 모두 같았다. 원본 반환 아카이브와 해시는 worker-result.json에 보존했다. 이 문서는 master가 한국어로 정리했다.

## carrier 계약

createCarrier(GameProfile)은 새 PLAYER_HEAD ItemStack에 ITEM_MODEL=destiny:probe/profile_arm과 PROFILE=ResolvableProfile.createResolved(ownerProfile)을 설정한다. native profile의 텍스처 property와 서명은 그대로 전달하며 PlayerSkin.Patch.EMPTY를 유지한다. helper는 인벤토리 변경·네트워크 조회·profile logging을 하지 않는다. client의 native skin cache/fetch는 별도이며 factory 성공만으로 이미지 로드가 증명되지 않는다.

owner-only 전송과 차원·사망·disconnect·만료 정리는 호출자 소유다. 이 helper를 일반 held projection에 연결하지 않는다. null profile은 거부한다. CMD를 읽지 않는 player_head special renderer에 맞춰 불필요한 CMD merge·slim detector·관련 테스트를 최종본에서 제거했다. 공개 API는 createCarrier(GameProfile), marker(id), markerId(packed)뿐이다.

## 실제 native 밝기 전달 경로

Brightness.pack은 (block<<4)|(sky<<20)이다. Polymer는 이 packed int를 metadata로 보내지만, client DisplayRenderer.getBlock/skyLightLevel은 LightCoordsUtil.block/sky의 &15 mask를 거친다. EntityRenderer는 그 값을 다시 pack한다. 따라서 block128+id/sky173 같은 큰 값은 끝까지 유지되지 않는다. 최종 marker는 block=id0..15, sky=13의 정상 값이다.

markerId는 정상 canonical packed 값만 ID로 복원하며 그 외에는 -1을 준다. 높은 비트가 이미 native mask로 사라진 뒤의 origin은 복구할 수 없다. shader는 반드시 정상 밝기 외에 전용 Position.y=-10,000,000 lane도 확인한다. master의 최종 gate는 -11,000,000<y<-9,000,000 및 UV2.y=208이다. 일반 월드의 sky13만으로 팔로 오인하지 않는다. 의미 ID는 bit0=left, bit1=upper, bit2=slim, bit3=sleeve다.

## 작업자 검사

최종 격리 JUnit4개 통과(실패·오류·skip0). native PROFILE JSON/stream codec에서 unsigned texture property와 empty patch 보존, 독립 fresh carrier와 null 거부, 정상16개 marker의 native mask/repack 보존, 다른 sky·불필요한 bit·잘못된 ID 거부를 확인했다. 초안6개 테스트 결과는 최종본의 수치로 사용하지 않는다.

실행은 작업자 worktree의 독립 libs/gcb-server를 -Pgcb_server_dir로 명시했다. 임시 init-script는 processResources 대량 복사 대신 src/main/resources를 test classpath에 직접 사용했다. 최초에는 classpath를 너무 일찍 설정해 JUnit Platform 로드가 실패했으며 afterEvaluate 설정 후 수정했다.26.3 순수 JUnit은 datapack item defaults가 없어 테스트에서 아직 components가 없는 PLAYER_HEAD holder에만 empty component map을 bind했다. 실제 datapack/스킨 화면 인증과 구분한다. 전체 통합 검사2106개 결과는 master junit-result.json에 있다.

## 1차 PNG 검수와 한계

작업자는 w237-danmo-classic-visible.png(SHA2564604c80d4ced564ac191db444c5b1acf89ed4d214bb69b248bb23002aaa8b3be)를 읽기 전용으로 검수했다. 중앙4조각은 기존 오른쪽 아래 총/팔과 별도로 보인다. native26.3 wide/efe.png의 오른팔 금색 팔찌·왼팔의 비대칭과 화면이 일치하며, 몸쪽 청록 소매→말단 피부 방향도 맞았다. 전체6면 UV·소매off·두 번째 계정 observer isolation까지 인증한 검사는 아니다.

master가 이후 forearm의 wrist pivot 때문에 elbow가 벌어지는 것을 발견해 회전 translation을 수정했다. 수정 후2차 Vision 수락은 master README와 최종 PNG에 기록한다. 이 실험은 독립 hinge sweep이며 실제 무기 파지·원본 장전 애니메이션의 최종 수락을 뜻하지 않는다.
