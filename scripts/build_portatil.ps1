<#
.SYNOPSIS
    Construye SAVIP desde cero y deja el ZIP portatil listo, en una sola orden.

.DESCRIPTION
    1. scripts\build_exe.ps1: comprueba Python 3.12 x64, crea .venv-build en
       esta carpeta, instala requirements-lock.txt y requirements-build.txt
       (versiones exactas), verifica el lock, ejecuta pruebas previas,
       PyInstaller limpio (packaging\SAVIP.spec) y la autocomprobacion.
    2. scripts\empaquetar_portatil.py: ZIP release\SAVIP_<VERSION>_Portatil_Windows_x64.zip
       con SAVIP.exe, _internal\ y LEEME_PORTATIL.txt, CRC verificado y SHA-256.
    3. Extrae el ZIP en una carpeta temporal y ejecuta alli
       SAVIP.exe --autocomprobacion sin variables de Python en el entorno.

.PARAMETER SinPruebas
    Omite las pruebas previas de build_exe.ps1.

.EXAMPLE
    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\build_portatil.ps1
#>
[CmdletBinding()]
param([switch]$SinPruebas)

$ErrorActionPreference = "Stop"
$Raiz = Split-Path -Parent $PSScriptRoot
Set-Location $Raiz

& (Join-Path $PSScriptRoot "build_exe.ps1") -SinPruebas:$SinPruebas

Write-Host "`n-- Empaquetando ZIP portatil --" -ForegroundColor Cyan
& (Join-Path $Raiz ".venv-build\Scripts\python.exe") (Join-Path $PSScriptRoot "empaquetar_portatil.py")
if ($LASTEXITCODE -ne 0) { throw "Fallo el empaquetado del ZIP." }

$Version = (Get-Content (Join-Path $Raiz "VERSION") -Raw).Trim()
$zip = Join-Path $Raiz "release\SAVIP_${Version}_Portatil_Windows_x64.zip"

Write-Host "`n-- Verificando el ZIP extraido --" -ForegroundColor Cyan
$extraido = Join-Path ([IO.Path]::GetTempPath()) ("savip_verificacion_" + [guid]::NewGuid().ToString("N"))
Expand-Archive -Path $zip -DestinationPath $extraido
$exe = Join-Path $extraido "SAVIP_${Version}_Portatil\SAVIP.exe"
# Sin PYTHON*, VIRTUAL_ENV ni CONDA*: el EXE debe valerse solo con _internal.
Get-ChildItem Env: | Where-Object { $_.Name -match '^(PYTHON|VIRTUAL_ENV|CONDA)' } | ForEach-Object { Remove-Item "Env:\$($_.Name)" }
$salida = Join-Path $extraido "autocomprobacion.txt"
$proceso = Start-Process -FilePath $exe -ArgumentList "--autocomprobacion" -WorkingDirectory "$env:SystemDrive\" `
    -Wait -PassThru -NoNewWindow -RedirectStandardOutput $salida -RedirectStandardError "$salida.err"
Get-Content $salida, "$salida.err" -ErrorAction SilentlyContinue | Write-Host
$codigo = $proceso.ExitCode
Remove-Item $extraido -Recurse -Force
if ($codigo -ne 0) { throw "La autocomprobacion del EXE extraido fallo (codigo $codigo)." }

Write-Host "`n== Paquete portatil listo ==" -ForegroundColor Green
Write-Host "ZIP:     $zip"
Write-Host "SHA-256: $((Get-Content "$zip.sha256" -Raw).Trim())"
