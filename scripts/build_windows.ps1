param(
    [switch]$SkipInstaller,
    [string]$PythonPath
)

$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
Set-Location $ProjectRoot

function Find-Python {
    if ($PythonPath) {
        if (!(Test-Path $PythonPath)) {
            throw "PythonPath does not exist: $PythonPath"
        }
        return $PythonPath
    }

    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) {
        return $python.Source
    }

    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        return $py.Source
    }

    throw "Python 3.12+ was not found. Install Python and add it to PATH."
}

function Find-InnoSetup {
    $candidates = @(
        "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
        "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
        "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe"
    )

    foreach ($candidate in $candidates) {
        if (Test-Path $candidate) {
            return $candidate
        }
    }

    $iscc = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($iscc) {
        return $iscc.Source
    }

    return $null
}

$Python = Find-Python
$VenvPython = Join-Path $ProjectRoot ".venv-build\Scripts\python.exe"

if (!(Test-Path $VenvPython)) {
    & $Python -m venv .venv-build
}

& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -e ".[build]"

& $VenvPython -m PyInstaller `
    --noconfirm `
    --clean `
    --windowed `
    --name LegacyPokemonTransfer `
    --paths src `
    packaging\windows\launcher.py

Write-Host "Built app folder: dist\LegacyPokemonTransfer"

if ($SkipInstaller) {
    Write-Host "Skipped installer build."
    exit 0
}

$InnoSetup = Find-InnoSetup
if (!$InnoSetup) {
    Write-Host "Inno Setup was not found. Install Inno Setup 6 to build LegacyPokemonTransferSetup.exe."
    Write-Host "Download: https://jrsoftware.org/isdl.php"
    exit 0
}

New-Item -ItemType Directory -Force -Path installer | Out-Null
& $InnoSetup packaging\windows\LegacyPokemonTransfer.iss
Write-Host "Built installer: installer\LegacyPokemonTransferSetup.exe"
