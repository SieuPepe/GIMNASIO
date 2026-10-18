/**
 * Crea en tu cuenta de Google los tres formularios que usa el programa, con
 * todas sus preguntas, y escribe las direcciones ya listas para pegar.
 *
 * COMO SE USA
 *
 *   1. Entra en https://script.google.com con la cuenta donde quieres los
 *      formularios (ojo: la cuenta importa, los formularios quedan en su Drive).
 *   2. «Nuevo proyecto».
 *   3. Borra lo que haya y pega este fichero entero.
 *   4. Arriba, elige la funcion «crearFormularios» y dale a «Ejecutar».
 *   5. La primera vez Google pide permiso para crear formularios en tu cuenta.
 *      Es tu propio guion creando tus propios formularios; hay que aceptarlo.
 *   6. Cuando termine, abajo sale el «Registro de ejecucion» con las tres
 *      direcciones. Esas son las que se pegan en el programa, en
 *      Correo -> «Plantillas de correo...» -> «URL del formulario».
 *
 * Las direcciones salen ya con los marcadores {{id_usuario}} y {{id_envio}}
 * puestos, que es lo que el programa necesita para atar cada respuesta a su
 * persona. No hay que editarlas a mano.
 *
 * Se puede ejecutar mas de una vez: cada vez crea formularios nuevos. Si te
 * equivocas, borra los que sobren desde tu Drive.
 */

/** Las dos preguntas de identificacion que llevan los tres formularios. */
var ID_USUARIO = 'ID_Usuario';
var ID_ENVIO = 'ID_Envio';

var AVISO_OCULTO = 'No lo toques: lo rellena el programa automaticamente.';


function crearFormularios() {
  var resultados = [];
  resultados.push(crearConsentimiento());
  resultados.push(crearEncuesta());
  resultados.push(crearCheckin());

  Logger.log('');
  Logger.log('========================================================');
  Logger.log('  LISTO. Pega cada direccion donde dice, en el programa:');
  Logger.log('  Correo -> Plantillas de correo... -> URL del formulario');
  Logger.log('========================================================');
  for (var i = 0; i < resultados.length; i++) {
    var r = resultados[i];
    Logger.log('');
    Logger.log('--- ' + r.titulo);
    Logger.log('    Plantilla(s): ' + r.plantillas);
    Logger.log('    Para editarlo: ' + r.edicion);
    Logger.log('    DIRECCION A PEGAR:');
    Logger.log('    ' + r.enlace);
  }
  Logger.log('');
  Logger.log('Recuerda: la direccion de la encuesta va en DOS plantillas,');
  Logger.log('«Encuesta T-14» y «Recordatorio», porque el recordatorio es un');
  Logger.log('segundo aviso de la misma encuesta.');
  return resultados;
}


/** Formulario 1: la autorizacion para tratar sus datos y escribirle. */
function crearConsentimiento() {
  var f = FormApp.create('Autorizacion de datos — Kevin Ruiz Valdenegro');
  f.setDescription(
      'Para poder llevar tu entrenamiento necesito guardar tus datos de '
      + 'contacto, tus objetivos y los resultados de tus valoraciones, y '
      + 'escribirte sobre tu programa. Nada mas, y nunca a terceros.');

  var ocultas = anadirOcultas(f);

  f.addMultipleChoiceItem()
      .setTitle('¿Autorizas que tratemos tus datos y te escribamos?')
      .setChoiceValues(['Si, autorizo', 'No'])
      .setRequired(true);

  f.setConfirmationMessage('Gracias. Ya esta todo listo.');

  return {
    titulo: 'Consentimiento',
    plantillas: 'CONSENTIMIENTO',
    edicion: f.getEditUrl(),
    enlace: enlaceConMarcadores(f, ocultas)
  };
}


/** Formulario 2: la encuesta de fin de ciclo, 14 preguntas. */
function crearEncuesta() {
  var f = FormApp.create('¿Como ha ido tu ciclo? — Kevin Ruiz Valdenegro');
  f.setDescription(
      'Dos minutos. Lo que contestes aqui es lo que uso para montar tu '
      + 'proximo ciclo, asi que cuanto mas sincero, mejor te va a salir.');

  var ocultas = anadirOcultas(f);

  // -- Bloque 1: sensacion fisica
  f.addPageBreakItem().setTitle('Como te encuentras');

  f.addScaleItem()
      .setTitle('¿Como te sientes fisicamente ahora mismo?')
      .setBounds(1, 10)
      .setLabels('Fatal', 'Estupendamente')
      .setRequired(true);

  f.addMultipleChoiceItem()
      .setTitle('Tu nivel de energia en el dia a dia, comparado con el inicio')
      .setChoiceValues(['Peor', 'Igual', 'Mejor']);

  f.addScaleItem()
      .setTitle('¿Como estas descansando y durmiendo?')
      .setBounds(1, 10)
      .setLabels('Muy mal', 'Muy bien');

  f.addMultipleChoiceItem()
      .setTitle('¿Has tenido molestias o dolores durante el programa?')
      .setChoiceValues(['No', 'Leves', 'Si'])
      .showOtherOption(true)
      .setRequired(true);
  f.addParagraphTextItem()
      .setTitle('Si has marcado molestias, cuentame donde y cuando aparecen')
      .setHelpText('Opcional, pero es lo que me permite corregirlo a tiempo.');

  // -- Bloque 2: el programa
  f.addPageBreakItem().setTitle('El programa');

  f.addParagraphTextItem()
      .setTitle('¿Que es lo que mas te ha gustado?');
  f.addParagraphTextItem()
      .setTitle('¿Que es lo que menos te ha gustado?');

  f.addMultipleChoiceItem()
      .setTitle('La dificultad general del programa ha sido')
      .setChoiceValues(['Demasiado facil', 'Adecuada',
                        'Dura pero llevadera', 'Excesiva']);

  f.addScaleItem()
      .setTitle('¿Te han resultado claros los ejercicios y como ejecutarlos?')
      .setBounds(1, 5)
      .setLabels('Nada claros', 'Muy claros');

  // -- Bloque 3: adherencia
  f.addPageBreakItem().setTitle('Como te ha encajado');

  f.addMultipleChoiceItem()
      .setTitle('Aproximadamente, ¿que porcentaje de las sesiones has podido '
                + 'completar?')
      .setChoiceValues(['Menos del 25 %', 'Entre el 25 y el 50 %',
                        'Entre el 50 y el 75 %', 'Mas del 75 %'])
      .setRequired(true);

  f.addCheckboxItem()
      .setTitle('Si te has saltado sesiones, ¿cual ha sido el motivo?')
      .setChoiceValues(['Falta de tiempo', 'Horario incompatible',
                        'Falta de motivacion', 'Molestias o lesion',
                        'Viajes o trabajo', 'Se me hacia aburrido'])
      .showOtherOption(true)
      .setRequired(true);

  f.addMultipleChoiceItem()
      .setTitle('¿Que duracion de sesion te encaja mejor?')
      .setChoiceValues(['30 minutos', '45 minutos', '60 minutos',
                        '75 minutos o mas']);
  f.addCheckboxItem()
      .setTitle('¿Que dias te encaja mejor entrenar?')
      .setChoiceValues(['Lunes', 'Martes', 'Miercoles', 'Jueves', 'Viernes',
                        'Sabado']);
  f.addMultipleChoiceItem()
      .setTitle('¿Y en que franja horaria?')
      .setChoiceValues(['Manana', 'Mediodia', 'Tarde', 'Noche', 'Me da igual']);

  // -- Bloque 4: objetivo y lo que viene
  f.addPageBreakItem().setTitle('Lo que viene');

  f.addMultipleChoiceItem()
      .setTitle('¿Mantienes el objetivo con el que empezaste?')
      .setChoiceValues(['Lo mantengo', 'Lo cambio']);
  f.addParagraphTextItem()
      .setTitle('Si lo cambias, ¿cual es ahora tu objetivo?');

  f.addCheckboxItem()
      .setTitle('¿Que te gustaria trabajar o probar en el proximo ciclo?')
      .setChoiceValues(['Mas fuerza', 'Mas resistencia', 'Perdida de grasa',
                        'Movilidad y flexibilidad', 'Trabajo de core',
                        'Entrenar en casa', 'Clases o grupo',
                        'Nuevos ejercicios y variedad'])
      .showOtherOption(true);

  f.addMultipleChoiceItem()
      .setTitle('¿Quieres que hablemos para preparar tu proximo ciclo?')
      .setChoiceValues(['Si, quiero', 'Todavia no']);

  f.setConfirmationMessage(
      'Gracias. Con esto monto tu proximo ciclo; nos vemos en la sala.');

  return {
    titulo: 'Encuesta de fin de ciclo',
    plantillas: 'ENCUESTA_T14 y RECORDATORIO (la misma direccion en las dos)',
    edicion: f.getEditUrl(),
    enlace: enlaceConMarcadores(f, ocultas)
  };
}


/** Formulario 3: el check-in de mitad de ciclo. Corto a proposito. */
function crearCheckin() {
  var f = FormApp.create('¿Como va? — Kevin Ruiz Valdenegro');
  f.setDescription('Treinta segundos, para ver si hay que ajustar algo antes '
                   + 'de que termine el ciclo.');

  var ocultas = anadirOcultas(f);

  f.addScaleItem()
      .setTitle('¿Como te sientes fisicamente ahora mismo?')
      .setBounds(1, 10)
      .setLabels('Fatal', 'Estupendamente')
      .setRequired(true);

  f.addMultipleChoiceItem()
      .setTitle('¿Has tenido molestias o dolores?')
      .setChoiceValues(['No', 'Leves', 'Si'])
      .showOtherOption(true)
      .setRequired(true);

  f.addMultipleChoiceItem()
      .setTitle('¿Quieres que hablemos?')
      .setChoiceValues(['Si, quiero', 'Todavia no']);

  f.setConfirmationMessage('Gracias. Seguimos.');

  return {
    titulo: 'Check-in de mitad de ciclo',
    plantillas: 'CHECKIN_MITAD',
    edicion: f.getEditUrl(),
    enlace: enlaceConMarcadores(f, ocultas)
  };
}


/**
 * Anade las dos preguntas de identificacion y las devuelve.
 *
 * No son obligatorias a proposito: las rellena el programa por la direccion
 * del enlace, y si fueran obligatorias quien abriera el formulario a pelo se
 * quedaria atascado.
 */
function anadirOcultas(formulario) {
  var usuario = formulario.addTextItem()
      .setTitle(ID_USUARIO)
      .setHelpText(AVISO_OCULTO)
      .setRequired(false);
  var envio = formulario.addTextItem()
      .setTitle(ID_ENVIO)
      .setHelpText(AVISO_OCULTO)
      .setRequired(false);
  return { usuario: usuario, envio: envio };
}


/**
 * La direccion prerrellenada, con los marcadores que espera el programa.
 *
 * Google codifica las llaves al construir la direccion ({{ se convierte en
 * %7B%7B), asi que hay que devolverlas a su sitio: el programa busca
 * {{id_usuario}} tal cual.
 */
function enlaceConMarcadores(formulario, ocultas) {
  var respuesta = formulario.createResponse();
  respuesta = respuesta.withItemResponse(
      ocultas.usuario.createResponse('{{id_usuario}}'));
  respuesta = respuesta.withItemResponse(
      ocultas.envio.createResponse('{{id_envio}}'));

  var url = respuesta.toPrefilledUrl();
  return url.replace(/%7B%7B/gi, '{{').replace(/%7D%7D/gi, '}}');
}
