#requires -Version 5.1
<#
.SYNOPSIS
Capture a bounded Java 25 server JFR profile and before/after heap summaries.
.EXAMPLE
.\server_scale_capture.ps1 -ServerPid 12345 -OutputDirectory 'D:\Destiny QA' -JcmdPath 'C:\Java\jdk-25\bin\jcmd.exe'
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][ValidateRange(1, 2147483647)][int]$ServerPid,
    [Parameter(Mandatory = $true)][ValidateNotNullOrEmpty()][string]$OutputDirectory,
    [ValidateRange(1, 300)][int]$DurationSeconds = 120,
    [string]$JcmdPath
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$Utf8NoBom = [System.Text.UTF8Encoding]::new($false)

function Write-Utf8([string]$Path, [string]$Text) {
    [System.IO.File]::WriteAllText($Path, $Text, $Utf8NoBom)
}

function ConvertTo-WindowsArgument([string]$Value) {
    # .NET Framework/Windows PowerShell 5.1 has no ProcessStartInfo.ArgumentList.
    $Escaped = [regex]::Replace($Value, '(\\*)"', '$1$1\"')
    $Escaped = [regex]::Replace($Escaped, '(\\+)$', '$1$1')
    return '"' + $Escaped + '"'
}

function Invoke-NativeTool([string]$Executable, [string[]]$NativeArguments, [int]$TimeoutSeconds = 20) {
    $Info = [System.Diagnostics.ProcessStartInfo]::new()
    $Info.FileName = $Executable
    $Info.UseShellExecute = $false
    $Info.CreateNoWindow = $true
    $Info.RedirectStandardOutput = $true
    $Info.RedirectStandardError = $true
    if ($null -ne $Info.PSObject.Properties['ArgumentList']) {
        foreach ($Value in $NativeArguments) { [void]$Info.ArgumentList.Add($Value) }
    } else {
        $Info.Arguments = (($NativeArguments | ForEach-Object { ConvertTo-WindowsArgument $_ }) -join ' ')
    }
    $ToolProcess = [System.Diagnostics.Process]::new()
    $ToolProcess.StartInfo = $Info
    try {
        [void]$ToolProcess.Start()
        $StdoutTask = $ToolProcess.StandardOutput.ReadToEndAsync()
        $StderrTask = $ToolProcess.StandardError.ReadToEndAsync()
        if (-not $ToolProcess.WaitForExit($TimeoutSeconds * 1000)) {
            # Only the diagnostic child started above; never the supplied server process.
            $ToolProcess.Kill()
            [void]$ToolProcess.WaitForExit(2000)
            throw 'Diagnostic tool timed out. The server was not stopped; any recording retains its native duration limit.'
        }
        return [pscustomobject]@{
            ExitCode = $ToolProcess.ExitCode
            StandardOutput = $StdoutTask.GetAwaiter().GetResult()
            StandardError = $StderrTask.GetAwaiter().GetResult()
        }
    } finally { $ToolProcess.Dispose() }
}

function Assert-TargetIdentity {
    $Current = Get-Process -Id $ServerPid -ErrorAction Stop
    if ($Current.ProcessName -notin @('java', 'javaw') -or $Current.StartTime.ToUniversalTime().Ticks -ne $TargetStartTicks) {
        throw 'The selected Java process exited or its PID was reused. No further attach command will be sent.'
    }
}

function Invoke-TargetCommand([string[]]$CommandArguments) {
    Assert-TargetIdentity
    $Result = Invoke-NativeTool $JcmdExe (@([string]$ServerPid) + $CommandArguments)
    if ($Result.ExitCode -ne 0) {
        # Do not echo arbitrary target output: VM.command_line can include credentials.
        throw "jcmd failed for $($CommandArguments[0]) (exit $($Result.ExitCode)). Check JDK 25 and same-user attach access."
    }
    return $Result
}

if ($env:OS -ne 'Windows_NT') { throw 'This helper targets Windows PowerShell 5.1 or PowerShell 7 on Windows.' }
$TargetProcess = Get-Process -Id $ServerPid -ErrorAction Stop
if ($TargetProcess.ProcessName -notin @('java', 'javaw')) { throw 'ServerPid must identify java.exe or javaw.exe.' }
$TargetStartTicks = $TargetProcess.StartTime.ToUniversalTime().Ticks
if ([string]::IsNullOrWhiteSpace($JcmdPath)) {
    if ($env:JAVA_HOME) {
        $Candidate = Join-Path $env:JAVA_HOME 'bin\jcmd.exe'
        if (Test-Path -LiteralPath $Candidate -PathType Leaf) { $JcmdPath = $Candidate }
    }
    if ([string]::IsNullOrWhiteSpace($JcmdPath)) {
        $Found = Get-Command 'jcmd.exe' -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
        if ($null -ne $Found) { $JcmdPath = $Found.Source }
    }
}
if ([string]::IsNullOrWhiteSpace($JcmdPath) -or -not (Test-Path -LiteralPath $JcmdPath -PathType Leaf)) {
    throw 'JDK jcmd.exe was not found. Supply -JcmdPath from an existing JDK 25 installation; nothing is installed automatically.'
}
$JcmdExe = (Resolve-Path -LiteralPath $JcmdPath).ProviderPath
if ([System.IO.Path]::GetFileName($JcmdExe) -ine 'jcmd.exe') { throw 'JcmdPath must identify the existing JDK jcmd.exe executable.' }
$Version = Invoke-TargetCommand @('VM.version')
if ($Version.StandardOutput -notmatch '(?m)^\s*JDK\s+25(?:[.\s+]|$)') { throw 'The target JVM is not Java 25.' }
$Identity = Invoke-TargetCommand @('VM.command_line')
if ($Identity.StandardOutput -notmatch '(?m)^\s*java_command:\s+\S' -or
        $Identity.StandardOutput -match '(?i)net\.minecraft\.client\.main\.Main|KnotClient') {
    throw 'The selected target has no recognizable Java command or appears to be a Minecraft client.'
}
# Validation only: never display, serialize or persist the command line or its stderr.
$Identity.StandardOutput = $null
$Identity.StandardError = $null
$Identity = $null
$Existing = Invoke-TargetCommand @('JFR.check')
if ($Existing.StandardOutput -notmatch 'No available recordings') {
    throw 'A JFR recording already exists, or its status could not be verified. This helper will not stop or alter it.'
}
$Existing = $null

$PathProvider = $null
$PathDrive = $null
$OutputRoot = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath(
    $OutputDirectory, [ref]$PathProvider, [ref]$PathDrive)
if ($PathProvider.Name -ne 'FileSystem') { throw 'OutputDirectory must use the local FileSystem provider.' }
if ($OutputRoot.StartsWith('\\') -or $OutputRoot.StartsWith('//') -or $OutputRoot -match '[\x00-\x1f"]|%[pt]') {
    throw 'Use a local output path without control characters, quotes, UNC shares or JFR %p/%t expansion tokens.'
}
$OutputDrive = [System.IO.DriveInfo]::new([System.IO.Path]::GetPathRoot($OutputRoot))
if ($OutputDrive.DriveType -eq [System.IO.DriveType]::Network) { throw 'OutputDirectory must not use a mapped network drive.' }
$Stamp = [DateTime]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$Suffix = [guid]::NewGuid().ToString('N').Substring(0, 8)
$RecordingName = "destiny_scale_${ServerPid}_${Stamp}_${Suffix}"
$RunDirectory = Join-Path $OutputRoot $RecordingName
[void][System.IO.Directory]::CreateDirectory($RunDirectory)
$JfrPath = Join-Path $RunDirectory 'recording.jfr'
$CommandFile = Join-Path $RunDirectory 'start.jcmd'
$MetadataPath = Join-Path $RunDirectory 'capture.json'
$DisabledEvents = @('jdk.JVMInformation', 'jdk.InitialSystemProperty', 'jdk.InitialEnvironmentVariable', 'jdk.SystemProcess', 'jdk.ProcessStart')
$Metadata = [ordered]@{
    schemaVersion = 1; serverPid = $ServerPid; targetStartTicksUtc = $TargetStartTicks
    targetJavaMajor = 25; powerShellVersion = $PSVersionTable.PSVersion.ToString()
    startedAtUtc = [DateTime]::UtcNow.ToString('o'); requestedDurationSeconds = $DurationSeconds
    recordingName = $RecordingName; settings = 'profile'; maxSize = '256m'
    disabledSensitiveEvents = $DisabledEvents; recording = $JfrPath; status = 'preparing'
    commandLinePersisted = $false; gcLogFlagsChanged = $false
}
try {
    Write-Utf8 (Join-Path $RunDirectory 'vm-version.txt') $Version.StandardOutput
    $Before = Invoke-TargetCommand @('GC.heap_info')
    Write-Utf8 (Join-Path $RunDirectory 'heap-before.txt') $Before.StandardOutput
    # A command file keeps quotes intact across PS5.1/PS7 native argument handling.
    # Forward slashes are valid Windows Java paths and avoid backslash escape ambiguity.
    $QuotedDestination = '"' + $JfrPath.Replace('\', '/') + '"'
    $Settings = ($DisabledEvents | ForEach-Object { "${_}#enabled=false" }) -join ' '
    $StartCommand = "JFR.start name=$RecordingName settings=profile duration=${DurationSeconds}s filename=$QuotedDestination maxsize=256m path-to-gc-roots=false $Settings"
    Write-Utf8 $CommandFile ($StartCommand + "`n")
    $Clock = [System.Diagnostics.Stopwatch]::StartNew()
    $StartResult = Invoke-TargetCommand @('-f', $CommandFile)
    Write-Utf8 (Join-Path $RunDirectory 'jfr-start.txt') $StartResult.StandardOutput
    if ($StartResult.StandardOutput -notmatch 'Started recording' -or $StartResult.StandardOutput -match '(?i)warning|does not exist|unknown') {
        throw 'The bounded recording was not confirmed with the requested settings. No stop command will be issued.'
    }
    $Metadata.status = 'recording'
    Write-Utf8 $MetadataPath ($Metadata | ConvertTo-Json -Depth 5)
    $Complete = $false
    while ($Clock.Elapsed.TotalSeconds -lt ($DurationSeconds + 15)) {
        if ($Clock.Elapsed.TotalSeconds -ge $DurationSeconds -and (Test-Path -LiteralPath $JfrPath -PathType Leaf)) {
            try {
                $Stream = [System.IO.File]::Open($JfrPath, 'Open', 'Read', 'None')
                try { $Complete = $Stream.Length -gt 0 } finally { $Stream.Dispose() }
            } catch [System.IO.IOException] { $Complete = $false }
            if ($Complete) { break }
        }
        Start-Sleep -Milliseconds 500
    }
    if (-not $Complete) { throw 'The bounded recording did not finish writing within its duration plus 15 seconds. The server was not stopped.' }
    $After = Invoke-TargetCommand @('GC.heap_info')
    Write-Utf8 (Join-Path $RunDirectory 'heap-after.txt') $After.StandardOutput
    $JfrExe = Join-Path (Split-Path -Parent $JcmdExe) 'jfr.exe'
    if (Test-Path -LiteralPath $JfrExe -PathType Leaf) {
        $Gc = Invoke-NativeTool $JfrExe @('print', '--json', '--events', 'jdk.GarbageCollection,jdk.GCPhasePause,jdk.GCHeapSummary', $JfrPath) 30
        if ($Gc.ExitCode -eq 0) { Write-Utf8 (Join-Path $RunDirectory 'gc-events.json') $Gc.StandardOutput }
    }
    $Metadata.status = 'complete'
    $Metadata['jfrBytes'] = (Get-Item -LiteralPath $JfrPath).Length
    $Metadata['jfrSha256'] = (Get-FileHash -LiteralPath $JfrPath -Algorithm SHA256).Hash.ToLowerInvariant()
} catch {
    $Metadata.status = 'failed'
    throw
} finally {
    $Metadata['finishedAtUtc'] = [DateTime]::UtcNow.ToString('o')
    Write-Utf8 $MetadataPath ($Metadata | ConvertTo-Json -Depth 5)
}
Write-Host "Capture complete: $RunDirectory"
