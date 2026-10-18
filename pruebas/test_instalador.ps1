<#
    Pruebas de las funciones del instalador.

        pwsh -File pruebas\test_instalador.ps1

    No ejecuta la instalacion: carga solo sus funciones y las comprueba una a
    una. Lo que se vigila es lo que toca ficheros, que es lo delicado: de donde
    sale la ruta del libro, si Excel lo tiene abierto y que la copia de
    seguridad se haga de verdad.
#>
$ErrorActionPreference = 'Stop'
$texto = Get-Content (Join-Path (Split-Path -Parent $PSScriptRoot) 'instalar.ps1') -Raw
# Desde la definicion de Ejecuta, que es de la que dependen las demas.
$desde = $texto.IndexOf('function Texto')
$hasta = $texto.IndexOf('# --------------------------------------------------------------------- el modo')
Invoke-Expression $texto.Substring($desde, $hasta - $desde)

$fallos = 0
function Comprueba($que, $esperado, $obtenido) {
    if ($esperado -eq $obtenido) { Write-Host "OK    $que" -ForegroundColor Green }
    else { Write-Host "FALLA $que : esperaba '$esperado', obtuve '$obtenido'" -ForegroundColor Red
           $script:fallos++ }
}

# -- Busca-Python
$python = Busca-Python
if ($python) { Write-Host "OK    Busca-Python -> $($python.Etiqueta) $($python.Version)" -ForegroundColor Green }
else { Write-Host 'FALLA Busca-Python: no encuentra ninguno' -ForegroundColor Red; $fallos++ }

# -- Texto: sin esto, lo que el programa escribe por la salida de errores
#    sale como "System.Management.Automation.RemoteException".
$registro = New-Object System.Management.Automation.ErrorRecord(
    (New-Object System.Exception 'mensaje de verdad'), 'id', 'NotSpecified', $null)
Comprueba 'Texto: saca el mensaje del error' 'mensaje de verdad' (Texto $registro)
Comprueba 'Texto: deja pasar lo normal' 'hola' (Texto 'hola')

# -- Ejecuta: lo que rompio construir.ps1 en Windows PowerShell 5.
#    Ahi, con ErrorActionPreference en 'Stop', lo que un programa escribe por la
#    salida de errores se convierte en error de PowerShell aunque termine bien.
#    unittest, pip y PyInstaller escriben ahi sus mensajes normales.
$r = Ejecuta 'python3' @('-c', 'print("hola")')
Comprueba 'Ejecuta: programa correcto' 0 $r.Codigo
Comprueba 'Ejecuta: captura la salida' 'hola' $r.Salida.Trim()

$r = Ejecuta 'python3' @('-c', 'import sys; sys.stderr.write("aviso\n")')
Comprueba 'Ejecuta: stderr no es un fallo' 0 $r.Codigo
Comprueba 'Ejecuta: stderr se captura' 'aviso' $r.Salida.Trim()

$r = Ejecuta 'python3' @('-c', 'import sys; sys.exit(3)')
Comprueba 'Ejecuta: devuelve el codigo de error' 3 $r.Codigo

$r = Ejecuta 'no_existe_este_programa_12345'
Comprueba 'Ejecuta: programa inexistente' -1 $r.Codigo

Comprueba 'Ejecuta: no deja tocado el ErrorActionPreference' 'Stop' $ErrorActionPreference

# -- Ruta-Libro: con y sin config.toml, con ruta relativa y absoluta
$banco = Join-Path ([System.IO.Path]::GetTempPath()) ('inst_' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $banco | Out-Null
$raiz = $banco
Comprueba 'Ruta-Libro sin config' (Join-Path $banco 'datos_krv.xlsx') (Ruta-Libro)

Set-Content (Join-Path $banco 'config.toml') "[datos]`nlibro = `"mis_datos.xlsx`"`n"
Comprueba 'Ruta-Libro relativa' (Join-Path $banco 'mis_datos.xlsx') (Ruta-Libro)

Set-Content (Join-Path $banco 'config.toml') "[datos]`nlibro = `"/tmp/absoluto.xlsx`"`n"
Comprueba 'Ruta-Libro absoluta' '/tmp/absoluto.xlsx' (Ruta-Libro)

# -- Excel-Abierto
$libro = Join-Path $banco 'datos_krv.xlsx'
Set-Content $libro 'contenido'
Comprueba 'Excel-Abierto sin bloqueo' $false (Excel-Abierto $libro)
Set-Content (Join-Path $banco '~$datos_krv.xlsx') 'bloqueo'
Comprueba 'Excel-Abierto con bloqueo' $true (Excel-Abierto $libro)
Remove-Item (Join-Path $banco '~$datos_krv.xlsx')
Comprueba 'Excel-Abierto: libro inexistente' $false (Excel-Abierto (Join-Path $banco 'no.xlsx'))

# -- Copia-Libro
$copia = Copia-Libro $libro
if ($copia -and (Test-Path $copia)) {
    Write-Host "OK    Copia-Libro -> $(Split-Path -Leaf $copia)" -ForegroundColor Green
    Comprueba 'la copia conserva el contenido' 'contenido' (Get-Content $copia -Raw).Trim()
    Comprueba 'el original sigue ahi' $true (Test-Path $libro)
    if ((Split-Path -Leaf $copia) -match '^datos_krv_antes_de_instalar_\d{8}_\d{6}\.xlsx$') {
        Write-Host 'OK    el nombre de la copia lleva la fecha' -ForegroundColor Green
    } else {
        Write-Host "FALLA nombre de copia raro: $(Split-Path -Leaf $copia)" -ForegroundColor Red
        $fallos++
    }
} else { Write-Host 'FALLA Copia-Libro' -ForegroundColor Red; $fallos++ }
Comprueba 'Copia-Libro sin original' $null (Copia-Libro (Join-Path $banco 'no.xlsx'))

Remove-Item $banco -Recurse -Force
Write-Host ''
if ($fallos) { Write-Host "$fallos fallos" -ForegroundColor Red; exit 1 }
Write-Host 'INSTALADOR: 0 fallos' -ForegroundColor Green
