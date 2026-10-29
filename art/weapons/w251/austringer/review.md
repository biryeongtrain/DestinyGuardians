# W251 매사냥꾼 미술 보강

실제 출력 170 큐브 / 1020 UV 면 / 1024² atlas. full 전용이며 1,000 상한 이내다.

기본 안료 사진·원본 AFrame diffuse·실제 복구 FBX 15,680삼각면을 확인했다. 금색 shroud의 큰 직육면체를 넓은 연속 면과 사선 단면으로 교체하고, nose flanks는 좁아지는 회전 부품으로 만들었다. 네 bezel의 모서리를 둥글려 보라 inset과 단차를 연결했다. 그립의 전후 단면과 특히 heel의 측면 윤곽을 실제 형상으로 둥글리고, 원통 약실에는 두 개의 넓은 bearing land를 추가했다.

원본 triangle recess·보라 inset·wrap 무늬는 유지한다. 금속 하단 홈과 밝은 lip, 약실의 긴 flute·고무 접촉 경계를 면별 연속 UV에 넣었다. 무작위 오염·노이즈·전역 contrast 필터나 full-bright 보상은 없다. 보라 무늬는 기존 정적 해석이며 원본 동적 shader 복원이 아니다.

비교 그림: 실제 기본안료 사진 + 실제 local rip 중립 diffuse 참고 + 마스터 변경 전 snapshot과 W251의 동일광원/동일카메라/동일배율 측면·앞뒤사선·그립 확대. legacy axis/angle도 XYZ로 정규화했다. CPU 그림은 native 수락 근거가 아니다.

검사: JSON parse·요소/면 count·UV 범위·texture ref·exact display·FBX source pin·--verify 재생성. 기존 모션·ADS display·손 파지점·canonical 및 장전 graph는 보존한다.

실행: `rtk proxy /Users/qf/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B scripts/refine_weapon_w251_austringer.py` 및 같은 명령의 `--verify`. 두 W251 스크립트의 공용 읽기 전용 helper를 사용하며 원본 semantic design에서 매번 재생성한다.

남은 master native QA: shader 수정 후 실내/주간 1·3인칭 재질 대비, 그립 손 접촉·ADS notch 통공, 일반 장전 복귀, 10~20개 표시의 틈·깜박임·끊김. 미세 곡률은 팔각 단순화이며 native 성능은 미측정이다.
