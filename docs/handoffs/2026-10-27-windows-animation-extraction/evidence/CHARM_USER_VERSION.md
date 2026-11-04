# Charm v3.5.0_Beta.2 추가 조사 — 2026-10-27

사용자 지정 [ref](https://github.com/MontagueM/Charm/tree/v3.5.0_Beta.2)의 현재 commit은 **f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce**(2026-10-24)다. README뿐 아니라 구현을 확인했다. **무기 animation을 FBX curve로 export하는 경로와 별도 FirstPerson FBX 경로가 구현돼 있다.** 따라서 Windows에서는 Charm 직접 export를 먼저 시도하고, raw3tag 확보 및 별도 parser를 보존·대안 경로로 병행한다. 특정 무기의 reload를 실제 실행해 성공했다는 뜻은 아니다.

## 직접 FBX export

- [Investment.GetWeaponAnimationEntity, L880](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Schema/Investment/InvestmentHandler.cs#L880-L909)는 weapon animation entity와 FirstPersonAnimID를 찾는다.
- [ExportInventoryItem, L1291](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Schema/Investment/InvestmentHandler.cs#L1291-L1313)는 exportAnims를 받아 animation 정보를 exporter에 전달한다.
- [FbxExporter.Export, L40](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Exporters/FbxExporter.cs#L40-L65)는 weapon-skeleton animation을 기본 FBX에 넣고 [ExportFirstPersonRig, L177](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Exporters/FbxExporter.cs#L177-L217)에서 **`<name>_FirstPerson.fbx`**를 만든다. 이 경로에는 전체 animation skeleton·weapon meshes·clips가 들어간다.
- [FbxAnimationWriter.Write](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Exporters/Animation/FbxAnimationWriter.cs#L14-L55)는 animation stack과 translation/rotation/scale curve를 실제 작성한다. 단순 mesh·rest skeleton export만 있는 것이 아니다.

소스에서 확인한 UI 경로(실기동 미검증):

1. Settings → Exporting → **Export Animations** 활성화. 실험 기능이며 기본 false: [설정 소스](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/Settings/GeneralConfigView.xaml.cs#L110-L119).
2. Main Menu → **GEAR** → 무기 선택 → 화면의 별도 **Export Animations** 토글 활성화 → Export: [UI](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/API/DareView2.xaml#L695-L712), [핸들러](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/API/DareView2.xaml.cs#L468-L507).
3. 기본 FBX와 `_FirstPerson.fbx`를 모두 보존하고 Blender Action/animation stack을 확인한다. 파일 suffix만으로 모든 action이 실제1P reload라고 확정하지 않는다.
4. renderer에는 clip별 export checkbox와 Ctrl-click 선택도 있다: [고정 renderer 소스](https://github.com/DeltaDesigns/Charm-Renderer/blob/ae62181789aaddad360548475731a9adb9e4fd4f/Renderer/Viewport/RendererViewport.Animation.cs#L86-L170).

제한: [AddAnimations](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Exporters/FbxExporter.cs#L273-L374)는 skeleton/runtime rig/resources를 요구하며 bone count mismatch, incompatible control group, excluded clip, evaluation 실패를 거른다. [GetWeaponAnimations](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Schema/Entity/EntityAnimation.cs#L79-L120)의 selector 실패 시 전체 clips export로 fallback할 수 있다. 이름이 hash로 남을 수도 있다. export 파일 유무 외에 action별 reload 분류·정상 key·손/무기 정렬을 확인해야 한다.

## raw tag 추출

Main Menu → **Ctrl+D** → file hash 입력 → **H**: [TagHashBoxKeydown](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/Views/DevView.xaml.cs#L105-L138)가 [OpenHxD](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/Views/DevView.xaml.cs#L371-L400)를 호출해 `<ExportPath>/temp/<strategy>_<pkgid>_<reference>_<hash>.bin`을 작성한 뒤 파일 연결 프로그램을 연다. hex editor 실행 성공과 raw dump 작성 성공은 구분한다. **R**은 해당 시 referenced file을 dump한다. clip/skeleton/runtime rig 각각의 정확한 hash로 세 파일을 확보한다.

library의 [Tag<T>.Dump(savePath)](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Core/Tag.cs#L65-L71)는 `<hash>.bin`을 쓴다. [Package.GetFileBytes](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Tiger/Package/IPackage.cs#L516-L570)는 block·patch를 조합해 entry payload를 복원한다. 일반 package→directory 전체 raw export UI나 animation/raw dump용 CLI는 이번 소스 조사에서 찾지 못했다. Dev의 Batch Export는 일반 raw태그 일괄 export로 간주하지 않는다.

## 실행·빌드

README runtime은 .NET8 Desktop x64 및 VC++ Redistributable. 소스 빌드는 [global.json](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/global.json)의 SDK8.0.408/8.x feature-band rollforward와 [Charm.csproj](https://github.com/MontagueM/Charm/blob/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce/Charm/Charm.csproj#L1-L19)의 net8.0-windows/WPF/WinForms/x64를 따른다. runtime만으로 소스 빌드가 되는 것은 아니다. renderer submodule **ae62181789aaddad360548475731a9adb9e4fd4f**와 원래 native DLL을 보존한다.

Windows PowerShell 소스 빌드 예시(미실행):

```powershell
git clone https://github.com/MontagueM/Charm.git D:\DestinyAnimWork\tools\Charm
Set-Location D:\DestinyAnimWork\tools\Charm
git checkout --detach f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce
git submodule update --init --recursive
dotnet build Charm.sln -c Release -p:Platform=x64
```

명령별 성공 여부를 확인한다. 선택 ref와 동일 이름의 release binary가 존재하거나 일치한다고 보장하지 않는다. 실제 binary version/SHA256을 기록한다. README는9.5.0.4+와 여러 historical manifest를 나열하지만 현재 계정의 manifest 접근·특정 clip layout 호환은 별도 검증이다.

## delta/EOF와 비교

조사 시 delta/EOF head는 **7e42ddbc2992f216b35066ad23dc0f1902c24f45**, 사용자 ref보다3commits 앞이다. [고정 비교](https://github.com/MontagueM/Charm/compare/f37fc7c9102e86c9bc35ebaed837eb6f2a8693ce...7e42ddbc2992f216b35066ad23dc0f1902c24f45)상 funding/README/texture plate sizing/renderer submodule 업데이트가 있으며 main repo의 위 animation/export 구현 파일은 바뀌지 않았다. 새 renderer 내부 변경은 별도 조사하지 않았다. 지정 ref를 우선하고 필요할 때만 이유를 적어 head를 대안으로 사용한다.

이 추가 조사는 소스만 확인했다. Windows 설치·실행·실제 FBX/raw 추출·Blender playback은 수행하지 않았다. 앞선 연구에서 Charm을 package/model 탐색 중심으로 다룬 부분을 이 문서로 보완한다.
