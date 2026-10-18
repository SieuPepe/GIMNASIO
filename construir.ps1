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

function Texto($objeto) {
    <#
        Convierte en texto legible lo que llega de un programa externo.

        Lo que el programa escribe por la salida de errores llega envuelto en un
        objeto de error, y si se pasa a cadena a secas sale
        "System.Management.Automation.RemoteException" en vez del mensaje.
    #>
    if ($objeto -is [System.Management.Automation.ErrorRecord]) {
        if ($objeto.Exception -and $objeto.Exception.Message) {
            return $objeto.Exception.Message
        }
    }
    return "$objeto"
}

function Ejecuta {
    <#
        Lanza un programa externo y devuelve su codigo de salida.

        Hace falta porque Windows PowerShell 5, con ErrorActionPreference en
        'Stop', convierte en error propio TODO lo que el programa escriba por la
        salida de errores, aunque sean mensajes normales y aunque termine bien.
        Y muchos la usan asi: unittest escribe ahi sus puntos, PyInstaller sus
        avisos y pip los suyos. Sin esto, el guion se para en seco en cuanto
        cualquiera de ellos dice algo.

        Con -Mostrar la salida va saliendo en pantalla segun se produce, que es
        lo que se quiere en los pasos largos.
    #>
    param(
        [Parameter(Mandatory = $true)] [string]$Exe,
        [string[]]$Argumentos = @(),
        [switch]$Mostrar
    )
    $previo = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    $global:LASTEXITCODE = 0
    $salida = @()
    $codigo = 0
    try {
        if ($Mostrar) {
            & $Exe @Argumentos 2>&1 | ForEach-Object { Write-Host "   $(Texto $_)" }
        } else {
            $salida = & $Exe @Argumentos 2>&1 | ForEach-Object { Texto $_ }
        }
        $codigo = $LASTEXITCODE
    } catch {
        $salida = @($_.Exception.Message)
        $codigo = -1
    } finally {
        $ErrorActionPreference = $previo
    }
    return @{ Codigo = $codigo; Salida = ($salida -join [Environment]::NewLine) }
}

function Titulo($texto) {
    Write-Host ''
    Write-Host "== $texto" -ForegroundColor Cyan
}
function Escribe($texto, $color = 'Gray') { Write-Host "   $texto" -ForegroundColor $color }

# ------------------------------------------------------------------- python

Titulo 'Comprobaciones'

# De que version se esta construyendo. Compilar sin haber actualizado es un
# clasico, y el error que sale no se parece en nada a la causa.
$git = Get-Command git -ErrorAction SilentlyContinue
if ($git) {
    $commit = (Ejecuta 'git' @('-C', $raiz, 'log', '-1', '--format=%h  %ad  %s',
                               '--date=short')).Salida.Trim()
    if ($commit) { Escribe "Version: $commit" Green }
    $sucio = (Ejecuta 'git' @('-C', $raiz, 'status', '--porcelain')).Salida.Trim()
    if ($sucio) {
        Escribe 'Aviso: hay cambios sin guardar en el repositorio.' Yellow
    }
    # Si la rama no sigue a ninguna remota, esto falla: entonces no hay nada
    # que avisar, y un aviso falso solo confunde.
    $r = Ejecuta 'git' @('-C', $raiz, 'rev-list', '--count', 'HEAD..@{u}')
    if ($r.Codigo -eq 0) {
        $detras = $r.Salida.Trim()
        if ($detras -match '^[1-9]') {
            Escribe "Aviso: te faltan $detras commits por traer. Haz git pull antes" Yellow
            Escribe '       de construir, o estaras empaquetando la version vieja.' Yellow
        }
    }
}

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

if ((Ejecuta $py @('-c', 'import PyInstaller')).Codigo -ne 0) {
    Escribe 'Falta PyInstaller. Lo instalo...' Yellow
    $r = Ejecuta $py @('-m', 'pip', 'install', 'pyinstaller') -Mostrar
    if ($r.Codigo -ne 0) { Escribe 'No he podido instalarlo.' Red; exit 1 }
}
Escribe 'PyInstaller disponible.' Green

# Las pruebas antes de empaquetar: empaquetar algo roto es perder media hora.
Titulo 'Pruebas'
$r = Ejecuta $py @('-m', 'unittest', 'discover', '-s', (Join-Path $raiz 'pruebas'), '-q')
if ($r.Codigo -ne 0) {
    Escribe 'Hay pruebas que fallan. No sigo: arreglalas antes de empaquetar.' Red
    Write-Host $r.Salida
    exit 1
}
Escribe (($r.Salida -split "`n" | Where-Object { $_ -match 'Ran|OK' }) -join ' · ') Green

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
$r = Ejecuta $py @('-m', 'PyInstaller', (Join-Path $raiz 'krv.spec'),
                   '--noconfirm', '--log-level', 'WARN') -Mostrar
if ($r.Codigo -ne 0) { Escribe 'Fallo al empaquetar.' Red; exit 1 }

# $IsWindows no existe en Windows PowerShell 5, donde siempre es Windows.
$enWindows = ($null -eq $IsWindows) -or $IsWindows
$programa = Join-Path $raiz 'dist/KevinRuizValdenegro'
$programa = Join-Path $programa ('KevinRuizValdenegro' + $(if ($enWindows) { '.exe' } else { '' }))
if (-not (Test-Path $programa)) {
    Escribe "He empaquetado, pero no encuentro el ejecutable en:" Red
    Escribe "   $programa" Red
    Escribe 'Mira los avisos de arriba: suele ser que falte alguna dependencia.' Yellow
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

$r = Ejecuta $iscc @((Join-Path $raiz 'instalador\krv.iss')) -Mostrar
if ($r.Codigo -ne 0) { Escribe 'Fallo al montar el instalador.' Red; exit 1 }

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
