# Windows Java 25 서버 JFR·GC 캡처

13600KF / Java25 / 최대 힙8GiB 서버의 CPU·GC 정체를 Spark나 WMI 없이 조사하는 도구다. **스크립트 제작만 완료했으며 Windows 실행 검증은 아직 하지 않았다.** 서버를 실제로 조작하거나 캡처한 결과가 아니다.

## 실행

서버와 같은 Windows 컴퓨터, 같은 Windows 사용자로 실행한다. 이미 설치된 JDK25의 `jcmd.exe`가 필요하다. JRE만 있거나 attach 권한이 없으면 중단하며, 설치·관리자 자동 승격·실행 정책 변경을 하지 않는다. Windows PowerShell5.1 또는 Windows의 PowerShell7을 대상으로 작성했다.

PID는 직접 지정한다. 다음 명령은 실행 인자를 출력하지 않는다.

```powershell
Get-Process -Name java,javaw -ErrorAction SilentlyContinue |
    Select-Object Id, ProcessName, StartTime
```

게임 클라이언트나 다른 Java 도구의 PID를 고르지 않는다. PowerShell의 `$PID`는 현재 PowerShell 자체의 읽기 전용 변수다. 이 도구의 매개변수는 별개의 **`-ServerPid`** 이다.

접속자가 많아 문제가 재현되는 구간에 아래처럼 실행한다. `-OutputDirectory`는 서버 컴퓨터의 로컬 저장 경로다. 공백이 있는 경로도 허용한다.

```powershell
.\scripts\qa\server_scale_capture.ps1 `
    -ServerPid 12345 `
    -JcmdPath 'C:\Program Files\Java\jdk-25\bin\jcmd.exe' `
    -OutputDirectory 'D:\Destiny QA' `
    -DurationSeconds 120
```

`-JcmdPath`를 생략하면 기존 `JAVA_HOME\bin\jcmd.exe`, 다음으로 PATH의 `jcmd.exe`를 찾는다. 기본 녹화120초, 허용 범위1–300초다. 녹화 종료 파일을 확인하는 유예15초와 진단 명령 실행 시간은 별도다. 입력한 경로 아래 고유한 UTC 시각·PID·난수 하위 폴더를 만들어 기존 파일을 덮어쓰지 않는다. `%p`/`%t`를 포함한 경로, UNC 공유, 따옴표·제어문자가 포함된 경로는 거부한다.

가능하면 같은 접속자 수·활동·이동 조건에서 변경 전/후 각각 캡처하고, 녹화 UTC 시각에 해당하는 서버 로그와 TPS/MSPT 관측을 함께 대조한다. JFR만으로 인터넷 업로드 대역폭·압축 TCP 바이트·30명 수용 능력까지 입증하지 않는다.

## 수집 범위와 동작

- OS 프로세스 이름과 시작 시각, `VM.version`, 메모리 안에서만 읽는 `VM.command_line`으로 지정한 Java25 프로세스를 확인한다. 프로세스가 종료되거나 PID가 재사용되면 추가 attach를 중단한다. 원시 VM 실행 인자와 stderr를 화면/파일에 출력하지 않는다.
- 이미 JFR 녹화가 있으면 중단한다. 다른 녹화를 정지·재설정하지 않는다. 여러 녹화의 이벤트 설정은 영향을 공유할 수 있어 민감 이벤트를 확실히 줄이기 위한 제한이다.
- 고유 이름의 `JFR.start`에 `settings=profile`, 지정한 `duration`, `maxsize=256m`, 따옴표로 감싼 출력 파일을 지정한다. UTF8 BOM 없는 `start.jcmd`를 `jcmd <ServerPid> -f <파일>`로 전달해 PowerShell5.1/7의 중첩 따옴표 차이를 피한다. 서버 종료·재시작이나 `JFR.stop`은 호출하지 않는다. 녹화는 자체 duration으로 종료된다.
- 실행 인자/환경/다른 프로세스 명령을 담을 수 있는 `jdk.JVMInformation`, `jdk.InitialSystemProperty`, `jdk.InitialEnvironmentVariable`, `jdk.SystemProcess`, `jdk.ProcessStart` 이벤트를 이 녹화에서 비활성화한다. 원시 JFR에는 여전히 파일 경로·IP·스레드/클래스 이름 등이 들어갈 수 있으므로 로컬 진단 자료로 취급하고 공유 전에 검토한다. 자동 업로드나 Git 추가는 하지 않는다.
- 녹화 전/후 `GC.heap_info`를 각각1회 읽는다. 강제 GC·힙 덤프·클래스 히스토그램은 실행하지 않는다. `GC.heap_info`는 중간 영향도의 진단 명령이며, profile 설정도 기본 설정보다 비용이 크다. 전후 heap 읽기는 녹화 구간 밖에 둔다.
- 같은 JDK에 `jfr.exe`가 있으면 완료된 파일을 오프라인으로 읽어 GC·GC pause·heap summary 이벤트만 JSON으로 추출한다. 없는 도구를 설치하지 않는다.
- 진단 자식 프로세스에 제한 시간을 둔다. 시간 초과 때 종료하는 것은 도구가 만든 jcmd/jfr 자식뿐이며, `-ServerPid`의 서버를 종료하지 않는다. JVM 정지나 심한 GC로 파일 완성이 늦어지면 실패로 기록하고 기다림을 끝낸다.

출력은 `recording.jfr`, `capture.json`, `vm-version.txt`, `heap-before.txt`, `heap-after.txt`, `start.jcmd`, `jfr-start.txt`, 그리고 가능하면 `gc-events.json`이다. JFR 최대 크기256MiB에 도달하면 기록의 앞부분이 빠질 수 있으므로 요청120초를 항상 저장된 이벤트 시간 범위로 간주하지 않는다. 완료 시 JFR 파일 크기와 SHA256을 기록한다.

## 별도: 다음 예정된 서버 시작 때 GC 로그

현재 실행 중인 서버의 로깅 설정을 이 도구로 바꾸지 않는다. 아래는 운영자가 **다음 예정된 JVM 시작 명령에 별도로 검토해 추가할 수 있는 예시**다. 이 문서 때문에 서버를 재시작할 필요는 없다. 기존 힙 크기·GC 종류·네트워크 설정을 바꾸라는 지시도 아니다.

```text
"-Xlog:gc*,safepoint:file=logs/gc-%p-%t.log:time,uptime,level,tags:filecount=5,filesize=20M"
```

해당 시작 명령의 작업 폴더에 `logs` 디렉터리가 있어야 한다. PowerShell 시작 명령에서는 위 표기를 쓰고, `.bat`/`.cmd` 파일에 넣을 때는 `%p`/`%t`를 `%%p`/`%%t`로 이스케이프한다. 시작 시부터 GC pause/힙 추이를 남기는 로그이며 JFR profile 구간과는 범위가 다르다. 이미 쓰는 `-Xlog` 옵션과 충돌하지 않는지 운영자가 확인한다.

## 근거와 검증 한계

[JDK25 jcmd 문서](https://docs.oracle.com/en/java/javase/25/docs/specs/man/jcmd.html)의 동일 사용자 attach, `-f`, JFR 시간·파일·이벤트 설정 및 진단 영향도를 기준으로 작성했다. [Java25 실행 옵션 문서](https://docs.oracle.com/en/java/javase/25/docs/specs/man/java.html)는 GC 로그 예시의 근거다. 로컬 JDK25 `profile.jfc`에서도 위5개 민감 이벤트의 기본 활성화를 확인했다.

제작 환경에 `pwsh`가 없어 PowerShell 파서 검사와 Windows 실행·attach·공백 경로·JFR 자동 종료는 **미검증**이다. 서버 프로세스에 이 도구를 실행하지 않았다. 이 문서/스크립트의 정적 검토를 실제 Windows 캡처 성공으로 보고하지 않는다.

별도 로컬 JDK25 프로브에서 같은 `jcmd -f` 명령과 공백 경로로2초 녹화 파일(281,380바이트)을 생성했고, 비활성화한5개 이벤트가0개임을 확인했다. 이는 macOS JVM 명령 구문 검증이며 PowerShell/Windows 실행 검증을 대신하지 않는다.
