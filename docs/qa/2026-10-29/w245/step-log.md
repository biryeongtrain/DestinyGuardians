# W245 — 원본 타워 머테리얼 베이크와 표면 보강

1. 사용자 SSD의 `Destiny-Tower-Materials-2026-10-29`를 읽었다. 머테리얼753·텍스처806·HLSL404개이며 전달README는 완성된색상복원GLB가아님을 명시한다. DDS는 기존전달과 동일하며, 기존 single-sRGB heuristic은 tint/layer를 적용하지 않았다.
2. live Blender 기본 미저장Scene은 유지하고 별도 headless Blender에 기존 GLB의 Courtyard crop을 가져와 기준4구도를 렌더했다. 원본 mesh UV/material을 기존 노출124,098블록에 매핑했다. 원본voxel/크기/동선은 변경하지 않는다.
3. 고정slot1·4를 재사용했다. 최초refresh는slot4의 과거 master통합4파일이소유범위밖변경으로차단됐다. 모두현재main바이트와동일함을확인하고이전metadata를외부복구폴더에보존한뒤동일파일기준선만조정했다. 재시도refresh성공(23/46파일변경,221,520기준파일),worker는ready이후에만쓰기/빌드를진행한다.
4. slot1은HLSL근거basecolor합성모듈,slot4는기존월드보존형재질갱신을담당한다. master는geometry/UV연결·Blender전후비교·실게임Vision검수를소유한다. 미지원engine/vertex입력은대표근사와구분해기록한다.

5. 1차decode검사에서crop경계의내부블록이노출면으로잘못분류된것을차단했다. 외곽1블록의원본점유정보도읽도록mapper를수정했다. 최종노출매핑122,103셀,지원shader대표베이크103,577셀,제안변경92,298셀로재생성했다. 첫실패는통과로세지않으며기존월드에아직적용하지않았다.

6. shader모듈은24shader/98재질의basecolor식을지원하며,shader역산독립식최대오차2.98e-8(공유sampler/GPU검증아님). CHUNK_MODEL과TEXCOORD8은엔진입력부재를명시하고대표값으로베이크했다. projected_decal은배경합성미지원으로블록치환에서제외했다.
7. main compileJava/compileGametestJava통과. 최종92,298셀/116청크데이터를제품decode로검증했고provenance/duplicate/expected/fullcube거부및ledger codec왕복후사용자편집·나무보존검사가통과했다. 전체과거GameTest실행은이번미술배치수락에사용하지않는다.

8. UV상류확인중시작한1차QA서버는기존QA월드에일부W245를쓰기시작하여중간save/stop했다. 이를최종수락월드로쓰지않는다. 운영서버는W243상태로정상저장·중지돼있으며,그타워차원을새격리QA실행폴더에CoW복제하고적용전snapshot도보존했다. 기존QA/운영월드는삭제·재생성하지않았다.

9. Charm058e2ec StaticPart.cs108–147을추적했다. 이번STATIC VertexTexcoords0는이미scale/translation을적용한뒤Vflip돼있다. GLBconvert는이값을그대로저장하므로PS UV=(U,1−V)로수정했다. 현재crop에는terrain메시가없으며다른terrain자료를무검증재사용하지않도록mapper가거부한다. 수정베이크96,577셀을재생성하고1차UV-identity근사수락값은폐기했다. TEXCOORD8 vertexBuffer는여전히없어명시대표값을사용하며원작완전복원으로보고하지않는다.

10. cooked UV 최종 96,577셀/116청크 데이터로 targetedRuntime을 다시 실행해 통과했다. 이전 92,298셀은 UV 수정 전 중간 결과다. 최종 Blender 4구도 비교 이미지를 교체했고 빨강/황토 천막·바닥 및 벽의 명도 구분을 직접 확인했다. 전용 Danmo4GB QA에서 최종 실제 적용 검수 중이다.

11. Danmo4GB 실게임 최종 적용은96,550변경/27건너뜀이다. 기존 좌표가 expected와 다른27개는 소품/편집 보호 정책에 따라 보존했다. 완료 후5구도 PNG를 직접 열어 중앙 나무·상점·정원·전망·서비스 통로를 검수했다. 어두운 구조체·바닥과 밝은 보행선이 구분되고 기존 소품/나무는 유지된다. 비교표 danmo-material-comparison.jpg의 오른쪽은 완료 후 촬영이다.
12. survival native forward20틱+neutral5틱으로4.3139블록 이동했고 서버Pos와 일치, health20을 유지했다. leaseActive=false/heldKeys=[]/nativeInput중립을 확인했다. 서버 명령은 촬영용 이동/fixture이며 native 보행 근거와 구분한다. save-all flush 후 QA서버·client를 정상 종료했다. 실제OS입력·원작영상색일치·장기성능 인증은 아니다.

13. runtime worker도 완료 후5구도를 직접 검수했다. 새 구멍·누락 텍스처·나무 손상은 없었고 기존market바닥 검은 무늬를 신규회귀로 세지 않았다. 서비스 통로의 색 패치는 거칠게 보이는 한계로 남긴다. 두worker는 소유파일 동결 후 종료했고 slot1/4는 삭제하지 않고 idle-needs-refresh로 반환했다.

14. 운영 적용96,550변경/27보호skip 후 정상저장·종료했다. 새JVM 재시작에서W245 0변경/0건너뜀과팩생성완료를확인했다. online-mode=true·andlistOP4·pause60을유지하고25565를열어두었다. QA8102/25611종료,init복원,이번awake종료와48시간PID79904유지를확인했다.
