<#
    Construye el instalador completo de Kevin Ruiz Valdenegro.

        powershell -ExecutionPolicy Bypass -File construir.ps1

    Hace dos cosas, en este orden:

      1. Empaqueta el programa con PyInstaller, segun krv.spec. Sale una carpeta
         dist\KevinRuizValdenegro con el ejecutable y todo lo que necesita.
         A partir de ahi, el ordenador de destino NO necesita tener Python.

      2. Monta el instalador con Inno Setup, segun instalador\krv.iss. Sale un
         unico fichero dist\KevinRuizValdenegro_Instalador_1.0.0.exe, que es lo
         que se lleva al otro ordenador.

    Esto se ejecuta en el ordenador de desarrollo, no en el del usuario final.
    Hace falta:
      - Python 3.11 o superior con las dependencias instaladas.
      - Inno Setup 6, de https://jrsoftware.org/isdl.php

    Con -SoloPrograma se queda en el paso 1, util para probar el ejecutable sin
    montar el instalador entero.
#>

param(
    [switch]$SoloPrograma,
    [switch]$Limpiar
)

$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot

function Titulo($texto) {
    Write-Host ''
    Write-Host "== $texto" -ForegroundColor Cyan
}
function Escribe($texto, $color = 'Gray') { Write-Host "   $texto" -ForegroundColor $color }

# ------------------------------------------------------------------- python

Titulo 'Comprobaciones'

$py = Join-Path $raiz '.venv\Scripts\python.exe'
if (-not (Test-Path $py)) {
    $suelto = Get-Command python -ErrorAction SilentlyContinue
    if (-not $suelto) {
        Escribe 'No encuentro Python. Crea antes el entorno virtual:' Red
        Escribe '   python -m venv .venv' Yellow
        Escribe '   .\.venv\Scripts\Activate.ps1' Yellow
        Escribe '   pip install -r requirements.txt' Yellow
        exit 1
    }
    $py = $suelto.Source
    Escribe 'Aviso: uso el Python del sistema, no el del entorno virtual.' Yellow
}
Escribe "Python: $py" Green

& $py -c "import PyInstaller" 2>$null
if ($LASTEXITCODE -ne 0) {
    Escribe 'Falta PyInstaller. Lo instalo...' Yellow
    & $py -m pip install pyinstaller --quiet
    if ($LASTEXITCODE -ne 0) { Escribe 'No he podido instalarlo.' Red; exit 1 }
}
Escribe 'PyInstaller disponible.' Green

# Las pruebas antes de empaquetar: empaquetar algo roto es perder media hora.
Titulo 'Pruebas'
& $py -m unittest discover -s (Join-Path $raiz 'pruebas') -q
if ($LASTEXITCODE -ne 0) {
    Escribe 'Hay pruebas que fallan. No sigo: arreglalas antes de empaquetar.' Red
    exit 1
}
Escribe 'Todas en verde.' Green

# ------------------------------------------------------------------ limpieza

if ($Limpiar) {
    Titulo 'Limpieza'
    foreach ($carpeta in @('build', 'dist')) {
        $ruta = Join-Path $raiz $carpeta
        if (Test-Path $ruta) { Remove-Item $ruta -Recurse -Force; Escribe "borrado $carpeta" }
    }
}

# --------------------------------------------------------------- 1. programa

Titulo '1 de 2 · Empaquetando el programa'
Escribe 'Esto tarda unos minutos la primera vez.'
& $py -m PyInstaller (Join-Path $raiz 'krv.spec') --noconfirm --log-level WARN
if ($LASTEXITCODE -ne 0) { Escribe 'Fallo al empaquetar.' Red; exit 1 }

$programa = Join-Path $raiz 'dist\KevinRuizValdenegro\KevinRuizValdenegro.exe'
if (-not (Test-Path $programa)) {
    Escribe "No encuentro $programa" Red
    exit 1
}
$tamano = [math]::Round((Get-ChildItem (Split-Path $programa) -Recurse |
    Measure-Object -Property Length -Sum).Sum / 1MB, 1)
Escribe "Listo: dist\KevinRuizValdenegro ($tamano MB)" Green

if ($SoloPrograma) {
    Write-Host ''
    Write-Host '  Hecho. Pruebalo con:' -ForegroundColor Green
    Write-Host "     $programa"
    Write-Host ''
    exit 0
}

# ------------------------------------------------------------- 2. instalador

Titulo '2 de 2 · Montando el instalador'

$iscc = $null
foreach ($candidato in @(
    "${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe",
    "$env:ProgramFiles\Inno Setup 6\ISCC.exe")) {
    if (Test-Path $candidato) { $iscc = $candidato; break }
}
if (-not $iscc) {
    $suelto = Get-Command ISCC.exe -ErrorAction SilentlyContinue
    if ($suelto) { $iscc = $suelto.Source }
}
if (-not $iscc) {
    Escribe 'No encuentro Inno Setup 6.' Red
    Escribe 'Bajalo de https://jrsoftware.org/isdl.php, instalalo y repite.' Yellow
    Escribe '' 
    Escribe 'Mientras tanto, el programa empaquetado ya esta listo en:' Yellow
    Escribe '   dist\KevinRuizValdenegro' Yellow
    Escribe 'Se puede copiar tal cual a otro ordenador y funciona.' Yellow
    exit 1
}
Escribe "Inno Setup: $iscc" Green

& $iscc (Join-Path $raiz 'instalador\krv.iss')
if ($LASTEXITCODE -ne 0) { Escribe 'Fallo al montar el instalador.' Red; exit 1 }

$instalador = Get-ChildItem (Join-Path $raiz 'dist') -Filter '*Instalador*.exe' |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1

Write-Host ''
Write-Host '  Instalador listo:' -ForegroundColor Green
Write-Host "     $($instalador.FullName)"
Write-Host "     $([math]::Round($instalador.Length / 1MB, 1)) MB"
Write-Host ''
Write-Host '  Eso es lo unico que hay que llevarse al otro ordenador.'
Write-Host '  No necesita que alli haya Python ni nada instalado.'
Write-Host ''
