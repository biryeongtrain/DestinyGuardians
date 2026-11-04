param([Parameter(Mandatory=$true)][string]$WorkRoot)
$ErrorActionPreference = 'Stop'
$ParserRoot = Join-Path $WorkRoot 'tools\tiger-animation-parser'
$Revision = 'b9fdc3a43dd28118113275624fcc9054b75855f4'
if (Test-Path $ParserRoot) { throw "Already exists: $ParserRoot. Preserve it; inspect or choose a new WorkRoot." }
New-Item -ItemType Directory -Force -Path (Split-Path $ParserRoot) | Out-Null
git clone https://github.com/SolUnshadowed/tiger-animation-parser.git $ParserRoot
if ($LASTEXITCODE -ne 0) { throw 'git clone failed' }
git -C $ParserRoot checkout --detach $Revision
if ($LASTEXITCODE -ne 0) { throw 'git checkout failed' }
py -3.13 -m venv (Join-Path $ParserRoot '.venv')
if ($LASTEXITCODE -ne 0) { throw 'Python 3.13 venv creation failed' }
$Python = Join-Path $ParserRoot '.venv\Scripts\python.exe'
& $Python -m pip install -r (Join-Path $ParserRoot 'requirements.txt') jsonpickle
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $Python -m pip freeze | Set-Content -Encoding utf8 (Join-Path $ParserRoot 'requirements-freeze.txt')
Write-Output "Parser ready at $ParserRoot. Actual extraction/parsing not performed."
