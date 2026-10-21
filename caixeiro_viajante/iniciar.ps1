$ErrorActionPreference = 'Stop'
$raizProjeto = $PSScriptRoot
$pythonProjeto = Join-Path $raizProjeto '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonProjeto)) {
    Write-Host 'Crie o ambiente virtual e instale requirements.txt conforme o README.'
    exit 1
}
Push-Location -LiteralPath $raizProjeto
try {
    & $pythonProjeto (Join-Path $raizProjeto 'main.py') @args
} finally {
    Pop-Location
}

