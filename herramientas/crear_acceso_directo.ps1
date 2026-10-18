<#
    Crea un acceso directo en el Escritorio para arrancar la aplicacion con un
    solo clic, con el icono del logotipo y sin ventana negra detras.

        powershell -ExecutionPolicy Bypass -File herramientas\crear_acceso_directo.ps1

    Usa pythonw.exe en lugar de python.exe: es el mismo interprete pero sin
    consola, que es lo que hace que no aparezca el cmd.
#>

$ErrorActionPreference = 'Stop'

$raiz = Split-Path -Parent $PSScriptRoot
$nombre = 'Kevin Ruiz Valdenegro'
$icono = Join-Path $raiz 'assets\marca\kevin.ico'

# El interprete sin consola: primero el del entorno virtual del proyecto
$interprete = Join-Path $raiz '.venv\Scripts\pythonw.exe'
if (-not (Test-Path $interprete)) {
    $suelto = Get-Command pythonw.exe -ErrorAction SilentlyContinue
    if (-not $suelto) {
        Write-Host "No encuentro pythonw.exe." -ForegroundColor Red
        Write-Host "Crea antes el entorno virtual:" -ForegroundColor Yellow
        Write-Host "    python -m venv .venv; .\.venv\Scripts\Activate.ps1; pip install -r requirements.txt"
        exit 1
    }
    $interprete = $suelto.Source
    Write-Host "Aviso: uso el pythonw del sistema, no el del entorno virtual." -ForegroundColor Yellow
}

if (-not (Test-Path $icono)) {
    Write-Host "No encuentro el icono en $icono; el acceso directo saldra sin el." -ForegroundColor Yellow
    $icono = $null
}

$escritorio = [Environment]::GetFolderPath('Desktop')
$destino = Join-Path $escritorio "$nombre.lnk"

$shell = New-Object -ComObject WScript.Shell
$enlace = $shell.CreateShortcut($destino)
$enlace.TargetPath = $interprete
$enlace.Arguments = '-m krv'
$enlace.WorkingDirectory = $raiz
$enlace.Description = "$nombre - Gestion de entrenamiento"
if ($icono) { $enlace.IconLocation = "$icono,0" }
$enlace.Save()

Write-Host ""
Write-Host "Acceso directo creado en el Escritorio:" -ForegroundColor Green
Write-Host "   $destino"
Write-Host ""
Write-Host "Si algun dia no arranca y no ves ningun error, usa ARRANCAR.bat:"
Write-Host "ese si deja la ventana abierta para leer el fallo."
