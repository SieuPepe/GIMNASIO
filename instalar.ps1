<#
    Instalador de Kevin Ruiz Valdenegro - Gestion de entrenamiento

        powershell -ExecutionPolicy Bypass -File instalar.ps1

    Dos modos:

      BLANCO       Instalacion desde cero. Deja el programa listo con un usuario
                   de ejemplo que tiene de todo, para poder verlo funcionando.
                   PISA el libro de datos (haciendo copia antes) y pregunta la
                   cuenta de correo al arrancar.

      ACTUALIZAR   Solo renueva el programa. NO toca el libro de datos ni la
                   configuracion. Hace copia de seguridad del libro antes de
                   nada, y le anade las columnas nuevas si las hubiera.

    El libro de Excel es el unico sitio donde viven los datos, asi que todo lo
    que lo toca pide confirmacion y hace copia antes.
#>

param(
    [ValidateSet('blanco', 'actualizar')]
    [string]$Modo,
    [switch]$SinPreguntar
)

$ErrorActionPreference = 'Stop'
$raiz = $PSScriptRoot
$nombre = 'Kevin Ruiz Valdenegro'

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

function Escribe($texto, $color = 'Gray') { Write-Host $texto -ForegroundColor $color }
function Titulo($texto) {
    Write-Host ''
    Write-Host "== $texto" -ForegroundColor Cyan
}

function Pregunta($texto) {
    if ($SinPreguntar) { return $true }
    $respuesta = Read-Host "$texto [s/N]"
    return $respuesta -match '^[sSyY]'
}

# ---------------------------------------------------------------- comprobaciones

function Busca-Python {
    <# El primer Python 3.11 o superior que haya. Devuelve exe y argumentos
       por separado: montarlos a mano con un rango 1..0 los invierte. #>
    $candidatos = @(
        @{ Exe = 'py';     Args = @('-3.13') },
        @{ Exe = 'py';     Args = @('-3.12') },
        @{ Exe = 'py';     Args = @('-3.11') },
        @{ Exe = 'python'; Args = @() },
        @{ Exe = 'python3'; Args = @() }
    )
    foreach ($candidato in $candidatos) {
        if (-not (Get-Command $candidato.Exe -ErrorAction SilentlyContinue)) { continue }
        $argumentos = @($candidato.Args) + @(
            '-c', "import sys; print('%d.%d' % sys.version_info[:2])")
        $r = Ejecuta $candidato.Exe $argumentos
        if ($r.Codigo -ne 0 -or -not $r.Salida) { continue }
        $version = ($r.Salida -split "`n" | Select-Object -First 1).Trim()
        if ($version -as [version] -and [version]$version -ge [version]'3.11') {
            return @{ Exe = $candidato.Exe; Args = $candidato.Args; Version = $version
                      Etiqueta = (@($candidato.Exe) + $candidato.Args) -join ' ' }
        }
    }
    return $null
}

function Ruta-Libro {
    <# El libro que dice config.toml, o el de por defecto. #>
    $config = Join-Path $raiz 'config.toml'
    if (Test-Path $config) {
        foreach ($linea in Get-Content $config) {
            if ($linea -match '^\s*libro\s*=\s*"(.+?)"') {
                $valor = $Matches[1]
                if ([System.IO.Path]::IsPathRooted($valor)) { return $valor }
                return (Join-Path $raiz $valor)
            }
        }
    }
    return (Join-Path $raiz 'datos_krv.xlsx')
}

function Excel-Abierto($libro) {
    <# Excel deja un fichero ~$nombre.xlsx mientras lo tiene abierto. #>
    if (-not (Test-Path $libro)) { return $false }
    $carpeta = Split-Path -Parent $libro
    $bloqueo = Join-Path $carpeta ('~$' + (Split-Path -Leaf $libro))
    return (Test-Path $bloqueo)
}

function Copia-Libro($libro) {
    if (-not (Test-Path $libro)) { return $null }
    $sello = Get-Date -Format 'yyyyMMdd_HHmmss'
    $base = [System.IO.Path]::GetFileNameWithoutExtension($libro)
    $extension = [System.IO.Path]::GetExtension($libro)
    $destino = Join-Path (Split-Path -Parent $libro) `
        "$base`_antes_de_instalar_$sello$extension"
    Copy-Item $libro $destino
    return $destino
}

# --------------------------------------------------------------------- el modo

if (-not $Modo) {
    Write-Host ''
    Write-Host "  $nombre - Gestion de entrenamiento" -ForegroundColor White
    Write-Host '  ---------------------------------------------' -ForegroundColor DarkGray
    Write-Host ''
    Write-Host '  1) Instalacion desde cero' -ForegroundColor White
    Write-Host '     Para un ordenador nuevo. Deja el programa listo con un usuario'
    Write-Host '     de ejemplo que tiene de todo, para verlo funcionando.'
    Write-Host '     Pisa el libro de datos si ya hubiera uno (copia antes).' -ForegroundColor Yellow
    Write-Host ''
    Write-Host '  2) Actualizar la version' -ForegroundColor White
    Write-Host '     Renueva el programa y no toca tus datos ni tu configuracion.'
    Write-Host '     Hace copia del libro antes de nada.'
    Write-Host ''
    $eleccion = Read-Host '  Que quieres hacer? [1/2]'
    switch ($eleccion) {
        '1' { $Modo = 'blanco' }
        '2' { $Modo = 'actualizar' }
        default { Escribe 'No has elegido nada. Lo dejo.' Yellow; exit 1 }
    }
}

Titulo "Modo: $(if ($Modo -eq 'blanco') { 'instalacion desde cero' } else { 'actualizacion' })"

# ------------------------------------------------------------------- python

Titulo 'Python'
$python = Busca-Python
if (-not $python) {
    Escribe 'No encuentro Python 3.11 o superior.' Red
    Escribe 'Instalalo desde https://www.python.org/downloads/ y marca' Yellow
    Escribe '"Add python.exe to PATH" durante la instalacion.' Yellow
    exit 1
}
Escribe "   Python $($python.Version) ($($python.Etiqueta))" Green

# ------------------------------------------------------- el libro, con cuidado

$libro = Ruta-Libro
Titulo 'Libro de datos'
Escribe "   $libro"

if (Excel-Abierto $libro) {
    Escribe '   Ese libro esta abierto en Excel.' Red
    Escribe '   Cierralo y vuelve a lanzar el instalador: mientras este abierto' Yellow
    Escribe '   no se puede tocar sin arriesgar los datos.' Yellow
    exit 1
}

$copia = $null
if (Test-Path $libro) {
    $copia = Copia-Libro $libro
    Escribe "   Copia de seguridad: $(Split-Path -Leaf $copia)" Green
} else {
    Escribe '   No habia libro todavia.' Gray
}

if ($Modo -eq 'blanco' -and (Test-Path $libro)) {
    Escribe ''
    Escribe '   ATENCION: la instalacion desde cero va a REHACER ese libro.' Yellow
    Escribe '   Todo lo que tenga dentro desaparecera del fichero actual.' Yellow
    Escribe "   La copia de seguridad de arriba se queda, por si acaso." Gray
    if (-not (Pregunta '   Seguro que quieres rehacerlo?')) {
        Escribe '   Lo dejo sin tocar nada. La copia creada puedes borrarla.' Yellow
        exit 1
    }
}

# --------------------------------------------------------------- entorno virtual

Titulo 'Entorno e instalacion de dependencias'
$venv = Join-Path $raiz '.venv'
if (-not (Test-Path (Join-Path $venv 'Scripts\python.exe'))) {
    Escribe '   Creando el entorno virtual...'
    $r = Ejecuta $python.Exe (@($python.Args) + @('-m', 'venv', $venv))
    if ($r.Codigo -ne 0) {
        Escribe '   No he podido crear el entorno virtual.' Red
        Write-Host $r.Salida
        exit 1
    }
}
$py = Join-Path $venv 'Scripts\python.exe'
Escribe '   Instalando dependencias (tarda un poco la primera vez)...'
Ejecuta $py @('-m', 'pip', 'install', '--upgrade', 'pip', '--quiet') | Out-Null
$r = Ejecuta $py @('-m', 'pip', 'install', '-r',
                   (Join-Path $raiz 'requirements.txt')) -Mostrar
if ($r.Codigo -ne 0) {
    Escribe '   Fallo al instalar las dependencias.' Red
    exit 1
}
Escribe '   Dependencias listas.' Green

# ------------------------------------------------------------------ los datos

if ($Modo -eq 'blanco') {
    Titulo 'Datos de partida y usuario de ejemplo'
    $r = Ejecuta $py @((Join-Path $raiz 'herramientas\crear_demo.py'),
                       '--salida', $libro, '--nuevo', '--forzar') -Mostrar
    if ($r.Codigo -ne 0) { Escribe '   Fallo al preparar los datos.' Red; exit 1 }

    if (-not (Test-Path (Join-Path $raiz 'config.toml'))) {
        Copy-Item (Join-Path $raiz 'config.ejemplo.toml') (Join-Path $raiz 'config.toml')
        Escribe '   config.toml creado a partir de la plantilla.' Green
    }
} else {
    Titulo 'Revision del libro'
    if (Test-Path $libro) {
        $r = Ejecuta $py @((Join-Path $raiz 'herramientas\migrar_libro.py'), $libro) -Mostrar
        if ($r.Codigo -ne 0) {
            Escribe '   No se ha podido revisar el libro. Tus datos siguen intactos' Yellow
            Escribe "   y tienes la copia en $(Split-Path -Leaf $copia)." Yellow
        }
    } else {
        Escribe '   No hay libro que revisar. Si es un equipo nuevo, usa el modo' Yellow
        Escribe '   de instalacion desde cero.' Yellow
    }
    Escribe '   Tus datos y tu configuracion no se han tocado.' Green
}

# -------------------------------------------------------------- acceso directo

Titulo 'Acceso directo'
$r = Ejecuta 'powershell' @('-ExecutionPolicy', 'Bypass', '-File',
                            (Join-Path $raiz 'herramientas\crear_acceso_directo.ps1')) -Mostrar
if ($r.Codigo -ne 0) {
    Escribe '   No se ha podido crear el acceso directo. Puedes arrancar con ARRANCAR.bat.' Yellow
}

# ----------------------------------------------------------------------- final

Write-Host ''
Write-Host '  Listo.' -ForegroundColor Green
if ($Modo -eq 'blanco') {
    Write-Host ''
    Write-Host '  Al arrancar te preguntara la cuenta de correo desde la que vas a'
    Write-Host '  escribir a tus usuarios. Ten a mano la contrasena de aplicacion'
    Write-Host '  de Gmail (16 letras, se genera en la cuenta de Google, en'
    Write-Host '  Seguridad - Contrasenas de aplicacion).'
    Write-Host ''
    Write-Host '  Dentro encontraras al usuario "Prueba Demostracion" con programas,'
    Write-Host '  valoraciones, asignaciones y correos, para ver como funciona todo.'
    Write-Host '  Se puede borrar cuando ya no haga falta.'
} else {
    Write-Host ''
    Write-Host "  Copia de seguridad del libro: $(if ($copia) { Split-Path -Leaf $copia } else { 'no hacia falta' })"
}
Write-Host ''
Write-Host '  Arranca con el icono del Escritorio, o con ARRANCAR.bat.'
Write-Host ''
