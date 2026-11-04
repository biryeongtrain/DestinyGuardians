param(
 [Parameter(Mandatory=$true)][string]$ParserRoot,
 [Parameter(Mandatory=$true)][string]$Clip,
 [Parameter(Mandatory=$true)][string]$Skeleton,
 [Parameter(Mandatory=$true)][string]$Rig,
 [Parameter(Mandatory=$true)][string]$OutputBase,
 [Parameter(Mandatory=$true)][string]$GameVersion,
 [ValidateSet('gltf_retarget','json_retarget','json_raw')][string]$Target='gltf_retarget'
)
$ErrorActionPreference='Stop'
$Python=Join-Path $ParserRoot '.venv\Scripts\python.exe'
foreach($File in @($Python,$Clip,$Skeleton,$Rig)) {
 if (!(Test-Path -LiteralPath $File -PathType Leaf)) { throw "Missing input: $File" }
}
$OutputBase=[IO.Path]::GetFullPath($OutputBase)
New-Item -ItemType Directory -Force -Path (Split-Path $OutputBase) | Out-Null
if (Get-ChildItem -Path ($OutputBase + '.*') -ErrorAction SilentlyContinue) { throw 'Output basename already exists; choose a new basename to preserve prior outputs.' }
$ArgsList=@((Join-Path $ParserRoot 'parser.py'),'-v',$GameVersion,'--clip',$Clip,'--skeleton',$Skeleton,'--rig',$Rig,'-t',$Target,'--name-convention','blender','--animation-space','local','-o',$OutputBase)
Push-Location $ParserRoot
try {
 & $Python @ArgsList 2>&1 | Tee-Object -FilePath ($OutputBase+'.log')
 $ParserExit=$LASTEXITCODE
} finally { Pop-Location }
if ($ParserExit -ne 0) { throw "Parser exit $ParserExit; retain log and raw tags" }
if ($Target -eq 'gltf_retarget' -and !(Test-Path -LiteralPath ($OutputBase+'.gltf'))) { throw 'No expected glTF; inspect rawJSON fallback and parser log.' }
Write-Output 'Command returned. Inspect actual animation channels/keys and Blender playback before claiming success.'
