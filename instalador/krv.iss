; Instalador de Kevin Ruiz Valdenegro - Gestion de entrenamiento
;
; Se compila con Inno Setup 6.3 o superior:
;     "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" instalador\krv.iss
; o, mas comodo, con el guion que hace las dos cosas:
;     powershell -ExecutionPolicy Bypass -File construir.ps1
;
; Antes hay que haber empaquetado el programa con PyInstaller: este guion coge
; lo que haya en dist\KevinRuizValdenegro.
;
; Dos cosas que conviene tener presentes al tocar esto:
;
;   1. Los datos del usuario (su Excel, su configuracion, sus copias) viven en
;      Documentos, NO en la carpeta del programa. El instalador no los borra
;      nunca, y el desinstalador tampoco.
;   2. La instalacion es por usuario, sin permisos de administrador. Asi no hay
;      ventana de UAC y la carpeta del programa es escribible.

#define Nombre "Kevin Ruiz Valdenegro"
#define Version "1.0.0"
#define Editor "Kevin Ruiz Valdenegro"
#define Ejecutable "KevinRuizValdenegro.exe"
#define CarpetaDatos "Kevin Ruiz Valdenegro"

[Setup]
AppId={{8E3F1C42-9A7B-4D55-AE10-5C2F7B9D4E31}
AppName={#Nombre}
AppVersion={#Version}
AppVerName={#Nombre} {#Version}
AppPublisher={#Editor}
DefaultDirName={autopf}\{#Nombre}
DefaultGroupName={#Nombre}
DisableProgramGroupPage=yes
; Inno 6 esconde la pagina de bienvenida por defecto, y la pagina de los dos
; modos se coloca justo detras de ella: mejor que exista, y de paso se explica
; que es esto antes de preguntar nada.
DisableWelcomePage=no
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
OutputDir=..\dist
OutputBaseFilename=KevinRuizValdenegro_Instalador_{#Version}
SetupIconFile=..\assets\marca\kevin.ico
UninstallDisplayIcon={app}\{#Ejecutable}
UninstallDisplayName={#Nombre}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
; Sin esto, una actualizacion sobre el programa abierto deja ficheros a medias.
CloseApplications=yes
RestartApplications=no

[Languages]
Name: "spanish"; MessagesFile: "compiler:Languages\Spanish.isl"

[Tasks]
Name: "escritorio"; Description: "Crear un acceso directo en el Escritorio"; \
    GroupDescription: "Accesos directos:"

[Dirs]
; El acceso directo de abajo apunta aqui, asi que tiene que existir ya. El
; programa la usaria igualmente, pero entonces el icono saldria roto.
Name: "{userdocs}\{#CarpetaDatos}"

[Files]
Source: "..\dist\KevinRuizValdenegro\*"; DestDir: "{app}"; \
    Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
; WorkingDir explicito: el programa no deberia depender de desde donde se
; arranque, pero dejarlo al azar es pedir problemas.
Name: "{group}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"; WorkingDir: "{app}"
Name: "{group}\Carpeta de mis datos"; Filename: "{userdocs}\{#CarpetaDatos}"
Name: "{group}\Desinstalar {#Nombre}"; Filename: "{uninstallexe}"
Name: "{autodesktop}\{#Nombre}"; Filename: "{app}\{#Ejecutable}"; \
    WorkingDir: "{app}"; Tasks: escritorio

[Run]
Filename: "{app}\{#Ejecutable}"; Description: "Abrir {#Nombre} ahora"; \
    Flags: nowait postinstall skipifsilent

[Code]
var
  PaginaModo: TInputOptionWizardPage;
  CopiaHecha: String;

{ Los saltos de linea, como funcion y no escritos sueltos.

  El preprocesador de Inno mira la primera letra de cada linea: si es una
  almohadilla, la toma por una directiva suya. Un salto de linea escrito con
  codigos de caracter, al principio de una linea de continuacion, basta para
  que aborte con "Unknown preprocessor directive", y el mensaje no da ninguna
  pista de donde esta el problema. }

function Salto(): String;
begin
  Result := Chr(13) + Chr(10);
end;

function Parrafo(): String;
begin
  Result := Salto() + Salto();
end;

function CarpetaDeDatos(): String;
begin
  Result := ExpandConstant('{userdocs}\{#CarpetaDatos}');
end;

function RutaLibro(): String;
begin
  Result := CarpetaDeDatos() + '\datos_krv.xlsx';
end;

function HayDatos(): Boolean;
begin
  Result := FileExists(RutaLibro());
end;

function ExcelTieneElLibroAbierto(): Boolean;
begin
  { Excel deja un fichero ~$nombre.xlsx mientras lo tiene abierto. }
  Result := FileExists(CarpetaDeDatos() + '\~$datos_krv.xlsx');
end;

function EsInstalacionDesdeCero(): Boolean;
begin
  Result := (PaginaModo <> nil) and (PaginaModo.SelectedValueIndex = 0);
end;

function Sello(): String;
begin
  Result := GetDateTimeString('yyyymmdd_hhnnss', '-', '-');
end;

function CopiaDeSeguridad(): String;
var
  Destino: String;
begin
  Result := '';
  if not HayDatos() then
    Exit;
  Destino := CarpetaDeDatos() + '\datos_krv_antes_de_instalar_' + Sello() + '.xlsx';
  { CopyFile se llamaba FileCopy hasta Inno 6.3. }
  if CopyFile(RutaLibro(), Destino, False) then
    Result := Destino;
end;

procedure InitializeWizard();
begin
  PaginaModo := CreateInputOptionPage(wpWelcome,
    'Que quieres hacer',
    'Hay dos formas de instalar, y tratan tus datos de forma muy distinta.',
    'Elige una:',
    True, False);

  PaginaModo.Add(
    'Instalacion desde cero.' + Salto() +
    'Para un ordenador nuevo. Deja el programa listo con un usuario de ejemplo' + Salto() +
    'que tiene de todo, para poder verlo funcionando. REHACE el libro de datos.');

  PaginaModo.Add(
    'Actualizar la version.' + Salto() +
    'Renueva el programa y NO toca tus datos ni tu configuracion.' + Salto() +
    'Hace una copia de seguridad del libro antes de nada.');

  { Si ya hay datos, lo sensato es actualizar; si no, no hay nada que actualizar. }
  if HayDatos() then
    PaginaModo.SelectedValueIndex := 1
  else
    PaginaModo.SelectedValueIndex := 0;
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID <> PaginaModo.ID then
    Exit;

  if ExcelTieneElLibroAbierto() then
  begin
    MsgBox('Tu libro de datos esta abierto en Excel.' + Parrafo() +
           'Cierralo y vuelve a pulsar Siguiente: mientras este abierto no se ' +
           'puede tocar sin arriesgar los datos.', mbError, MB_OK);
    Result := False;
    Exit;
  end;

  if EsInstalacionDesdeCero() and HayDatos() then
  begin
    if MsgBox('Has elegido la instalacion desde cero, y ya hay un libro de datos:' +
              Parrafo() + RutaLibro() + Parrafo() +
              'Se va a guardar una copia de seguridad con la fecha, y despues el ' +
              'libro se rehara con los datos de ejemplo. Todo lo que tengas dentro ' +
              'dejara de estar en el fichero actual.' + Parrafo() +
              'Quieres seguir?', mbConfirmation, MB_YESNO) <> IDYES then
      Result := False;
  end;

  if (not EsInstalacionDesdeCero()) and (not HayDatos()) then
  begin
    MsgBox('Has elegido actualizar, pero no encuentro ningun libro de datos en:' +
           Parrafo() + CarpetaDeDatos() + Parrafo() +
           'No pasa nada: se instalara el programa igualmente y el primer dia ' +
           'te ofrecera crear el libro.', mbInformation, MB_OK);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
var
  Apartado: String;
begin
  if CurStep = ssInstall then
  begin
    { Copia de seguridad SIEMPRE, en los dos modos. Es barato y evita disgustos. }
    CopiaHecha := CopiaDeSeguridad();

    if EsInstalacionDesdeCero() and HayDatos() then
    begin
      { No se borra: se aparta. El programa vera que no hay libro y creara uno
        nuevo con los datos de ejemplo al arrancar. }
      Apartado := CarpetaDeDatos() + '\datos_krv_reemplazado_' + Sello() + '.xlsx';
      if not RenameFile(RutaLibro(), Apartado) then
        MsgBox('No he podido apartar el libro anterior. Comprueba que no este ' +
               'abierto en Excel.' + Parrafo() +
               'El programa se instalara igual, pero seguira usando el libro de ' +
               'siempre.', mbError, MB_OK);
    end;
  end;
end;

procedure CurPageChanged(CurPageID: Integer);
var
  Texto: String;
begin
  if CurPageID <> wpFinished then
    Exit;

  if EsInstalacionDesdeCero() then
    Texto := 'Al abrirlo te preguntara la cuenta de correo desde la que vas a ' +
             'escribir a tus usuarios. Ten a mano la contrasena de aplicacion de ' +
             'Gmail (16 letras).' + Parrafo() +
             'Dentro encontraras al usuario "Prueba Demostracion" con programas, ' +
             'valoraciones y correos, para ver como funciona todo.'
  else
    Texto := 'Tus datos y tu configuracion siguen como estaban.';

  if CopiaHecha <> '' then
    Texto := Texto + Parrafo() + 'Copia de seguridad del libro:' + Salto() +
             ExtractFileName(CopiaHecha);

  WizardForm.FinishedLabel.Caption := WizardForm.FinishedLabel.Caption +
    Parrafo() + Texto;
end;

function InitializeUninstall(): Boolean;
begin
  Result := True;
  MsgBox('Se va a quitar el programa.' + Parrafo() +
         'Tus datos NO se borran: el libro de Excel, la configuracion y las ' +
         'copias de seguridad se quedan en' + Parrafo() +
         ExpandConstant('{userdocs}\{#CarpetaDatos}'), mbInformation, MB_OK);
end;
