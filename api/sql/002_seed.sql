-- ============================================================================
-- 002_seed.sql — Datos iniciales de lecturas
-- Tipologías: Descriptivo, Narrativo, Argumentativo, Expositivo, Instructivo
-- ============================================================================

-- ────────────────────────────────────────────────────────────────────────────
-- DESCRIPTIVO (2 textos reales del proyecto)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO readings (title, typology, content) VALUES
(
    'Baños de Agua Santa: Naturaleza, aventura y espiritualidad en el corazón del Ecuador',
    'Descriptivo',
    'Ubicada en la provincia de Tungurahua, a pocos kilómetros de la ciudad de Ambato, la ciudad de Baños de Agua Santa se levanta como un destino turístico privilegiado por su extraordinaria combinación de paisajes andinos, exuberante vegetación subtropical y una profunda tradición religiosa. Situada entre la cordillera de los Andes y la entrada a la Amazonía ecuatoriana, Baños constituye un punto de encuentro entre climas, culturas y ecosistemas.

La ciudad se encuentra a los pies del imponente Volcán Tungurahua, cuya silueta domina el horizonte con su figura cónica y majestuosa. Aunque su actividad volcánica ha marcado distintos momentos en la historia local, también ha contribuido a la fertilidad de los suelos y a la presencia de aguas termales que brotan desde las entrañas de la tierra. Estas aguas, ricas en minerales, alimentan varios complejos de piscinas termales que constituyen uno de los principales atractivos del lugar.

El clima de Baños es templado y húmedo, con temperaturas promedio que oscilan entre los 15 y 25 grados centígrados. Durante la mañana, la neblina suele descender suavemente por las montañas, cubriendo los bosques con un velo blanco que lentamente se disipa para dar paso a un cielo despejado. En las tardes, las nubes pueden acumularse nuevamente, generando lluvias breves que intensifican el verdor del paisaje.

Uno de los recorridos más emblemáticos es la Ruta de las Cascadas, un trayecto que conecta a Baños con la región amazónica. A lo largo del camino, el visitante puede observar una sucesión de caídas de agua que descienden con fuerza entre paredes rocosas cubiertas de musgo y vegetación. Entre ellas destaca el Pailón del Diablo, una impresionante cascada cuyo estruendo se escucha a varios metros de distancia. El agua cae con potencia formando una nube de vapor que humedece el ambiente y crea pequeños arcoíris cuando los rayos del sol atraviesan la bruma.

El centro urbano de Baños presenta calles estrechas y ordenadas, con edificaciones de dos o tres pisos que combinan arquitectura tradicional y moderna. En los alrededores del parque central se ubican cafeterías, restaurantes y tiendas de artesanías donde se exhiben productos elaborados en madera, cuero y tejidos andinos. El aroma de la melcocha recién preparada —un dulce tradicional elaborado con panela estirada manualmente— se mezcla con el olor del café y el chocolate caliente que se ofrece a los visitantes.

En el corazón de la ciudad se encuentra la Basílica de Nuestra Señora del Rosario de Agua Santa, templo que refleja la devoción religiosa de sus habitantes. Sus paredes interiores están decoradas con murales que representan relatos de fe y agradecimiento. Peregrinos provenientes de distintas regiones del país llegan cada año para rendir homenaje a la Virgen, considerada protectora de la ciudad.

Baños también es reconocida por su amplia oferta de actividades de aventura. Los alrededores montañosos permiten la práctica de senderismo, ciclismo, canopy y rafting en el río Pastaza. Los puentes colgantes, suspendidos sobre profundas quebradas, ofrecen vistas panorámicas del valle y del curso del río, que serpentea entre formaciones rocosas.

Uno de los miradores más visitados es la llamada "Casa del Árbol", ubicada en las zonas altas. Desde allí, el visitante puede observar el volcán y balancearse en un columpio que se proyecta hacia el vacío, creando la sensación de flotar sobre el paisaje andino. La experiencia combina adrenalina y contemplación, pues el entorno natural invita tanto a la emoción como a la reflexión.

La economía local gira en gran medida en torno al turismo. Hoteles familiares, hostales juveniles y complejos turísticos se distribuyen por toda la ciudad. La hospitalidad de sus habitantes se manifiesta en la atención cercana y en la disposición para orientar a los visitantes. Durante los fines de semana y feriados, la ciudad adquiere un ritmo más dinámico: las calles se llenan de turistas nacionales y extranjeros que recorren sus atractivos.

El entorno natural que rodea Baños es un mosaico de tonalidades verdes. Bosques húmedos, montañas escarpadas y ríos caudalosos configuran un paisaje que cambia según la hora del día y la estación del año. La presencia constante del agua —en cascadas, ríos, lluvias y aguas termales— otorga al lugar una atmósfera de frescura y movimiento continuo.

Visitar Baños de Agua Santa implica recorrer un espacio donde convergen naturaleza, tradición y aventura. Cada rincón ofrece una imagen distinta: la quietud de un templo, el estruendo de una cascada, el bullicio del parque central o el silencio de un sendero rodeado de vegetación. Este destino ecuatoriano se presenta así como un escenario diverso y vibrante que refleja la riqueza geográfica y cultural del país.'
),
(
    'La Crónica del Cruce: El Orden, el Olvido y la Niebla',
    'Descriptivo',
    'En tiempos remotos, el paraje que hoy conocemos simplemente como el Cruce de la Niebla y el Roble no era más que una maraña impenetrable de maleza y árboles viejos. La leyenda local, susurrada en los pueblos del este y temida por los mineros del oeste, contaba que el bosque servía de barrera natural para separar dos mundos que no debían mezclarse. El cruce surgió de la necesidad de un tratado frágil: un punto de encuentro neutral marcado por el poste de señalización central, donde los cazadores podían intercambiar pieles por el metal de las cuevas sin tener que adentrarse demasiado en el territorio prohibido de los demás. No había adoquines, solo barro y desconfianza.

La cabaña con el tejado rojo fue construida mucho después por un guardabosques solitario llamado Elian. Elian odiaba el desorden y la improvisación. Él mismo talló los adoquines grises que hoy cubren los caminos principales, no por estética, sino para asegurar que el barro no impidiera el comercio, incluso durante las lluvias más intensas. Elian también detestaba mojarse las botas, por lo que dedicó un verano entero a tallar y colocar el puente de piedra arqueado sobre el río, uniendo la zona comercial con lo que él esperaba que se convirtiera en un puesto avanzado de civilización. Su obsesión por el orden le llevó a plantar el huerto próspero y a mantener la hoguera siempre encendida, símbolo de que el cruce era un lugar seguro y habitado.

Pero no todo en el cruce seguía las leyes de Elian. Al suroeste, el camino de tierra batida parecía resistirse a la piedra, serpenteando hacia un claro que el guardabosques nunca se atrevió a domar. Allí, el tiempo funcionaba de manera diferente. Un antiguo tocón de árbol, que se rumoreaba que había caído el mismo día que nació la primera neblina del valle, estaba rodeado por un círculo de hongos rojos y blancos perfectamente formado, un anillo de hadas. Elian, a pesar de su pragmatismo, nunca tocó esa zona, respetando el pacto implícito con los espíritus antiguos que habitaban la roca musgosa principal del noroeste, manteniendo el equilibrio entre la civilización que intentaba imponer y el misterio que siempre había existido en el bosque.

Con el paso de las décadas, Elian desapareció y la paz del tratado original se enfrió. Los adoquines comenzaron a agrietarse y el musgo a cubrirlos, mientras la niebla reclamaba partes del camino que antes eran seguras. El huerto quedó descuidado, aunque sorprendentemente, seguía dando frutos vibrantes. La hoguera se apagó, dejando solo cenizas frías y troncos vacíos. El poste de señalización central se inclinó con el tiempo, y las palabras se volvieron casi ilegibles, convirtiendo el cruce en un lugar de duda más que de dirección para los pocos viajeros que se atrevían a pasar por allí.

Un nuevo viajero ha llegado hoy al cruce, deteniéndose ante el poste inclinado. Su presencia es el primer signo de cambio en generaciones. Se fija en los troncos de madera junto a la hoguera apagada, imaginando las historias compartidas en otros tiempos. Observa el hacha y la cuerda que aún descansan junto a la cabaña vacía, herramientas listas para reabrir caminos o construir barreras. El viajero sabe que cada elemento tiene una historia, y que restaurar el equilibrio entre el orden del guardabosques y el misterio del claro de hongos es la clave para desvelar los secretos que la niebla ha ocultado celosamente durante años.'
);

-- ────────────────────────────────────────────────────────────────────────────
-- NARRATIVO (3 textos generados — relatos breves en español)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO readings (title, typology, content) VALUES
(
    'El reloj de la estación abandonada',
    'Narrativo',
    'Martina encontró el reloj de bolsillo entre los escombros del andén sur, justo donde las vías del tren se curvaban hacia el puente de hierro que nadie cruzaba desde hacía veinte años. El objeto estaba cubierto de óxido, pero sus manecillas aún se movían con un tic-tac obstinado que desafiaba el silencio de la estación abandonada.

Lo recogió con cuidado, limpiándolo con la manga de su chaqueta. La esfera tenía grabada una fecha: 15 de marzo de 1962. Aquella fecha le resultaba familiar. Su abuela, doña Carmen, solía hablar de un tren que nunca llegó, de un viajero que prometió volver y de una estación que dejó de funcionar el mismo día en que la esperanza se marchitó como las flores del jardín trasero.

Martina llevó el reloj a la casa de su abuela, que vivía al final de la calle empedrada, junto al río que dividía el pueblo en dos mitades que apenas se hablaban. Doña Carmen tomó el reloj entre sus manos arrugadas y lo acercó a su oído. Sus ojos, que habían olvidado cómo llorar, se humedecieron lentamente.

—Era de tu abuelo —susurró—. Lo dejó en el andén el día que partió. Dijo que mientras el reloj siguiera andando, él volvería.

Martina miró el reloj y luego a su abuela. El tic-tac llenaba la habitación como un corazón que se negaba a detenerse. Aquella tarde, por primera vez en décadas, doña Carmen caminó hasta la estación, se sentó en el banco de madera desgastado y esperó. No esperaba a nadie en particular, quizá solo al sonido del tren que alguna vez prometió llevarla a un lugar mejor.

El sol se puso detrás de las montañas y la estación se tiñó de tonos anaranjados. Martina se sentó junto a su abuela y ambas escucharon el viento silbar entre los rieles oxidados. No hacía falta decir nada. El reloj seguía su marcha y, con él, la certeza de que algunas promesas, aunque incumplidas, mantienen vivo algo que merece ser recordado.'
),
(
    'La carta que llegó con la lluvia',
    'Narrativo',
    'El cartero del pueblo dejó de repartir correspondencia un martes de noviembre, cuando la última familia con buzón se mudó a la ciudad. Don Esteban, que había recorrido las calles de tierra durante treinta y dos años con su bolsa de cuero gastado al hombro, se quedó sin caminos que transitar y sin puertas en las que tocar.

Sin embargo, una mañana de diciembre, mientras la lluvia golpeaba las tejas de su casa con una cadencia persistente, encontró una carta deslizada bajo su propia puerta. El sobre no tenía remitente ni sello postal. Solo su nombre, escrito con una caligrafía que le recordó a la de su madre, fallecida cuando él era apenas un niño.

Abrió el sobre con manos temblorosas. La carta decía: "Querido Esteban, el pueblo no ha muerto. Las casas vacías guardan historias que nadie ha contado todavía. Camina una vez más y escucha. Las paredes hablan cuando alguien se detiene a prestarles atención."

Don Esteban dobló la carta, se puso su sombrero y salió bajo la lluvia. Recorrió cada calle del pueblo, deteniéndose frente a cada casa abandonada. En la primera, escuchó el eco de una canción de cuna que alguna madre entonó hace tiempo. En la segunda, el crujido de una mecedora que seguía balanceándose con la brisa. En la tercera, el aroma de pan recién horneado que se filtraba por una ventana rota.

Al regresar a su casa, empapado pero con el pecho lleno de algo que no sabía nombrar, tomó un cuaderno y comenzó a escribir. Escribió sobre cada sonido, cada olor y cada imagen que las casas le habían regalado. Y así, sin proponérselo, Don Esteban se convirtió en el cronista de un pueblo que el mundo había olvidado, pero que seguía latiendo entre sus paredes agrietadas y sus jardines silvestres.

La lluvia no cesó durante tres días, y durante esos tres días, Don Esteban llenó un cuaderno entero. Cuando el sol finalmente apareció, colocó el cuaderno en su bolsa de cuero y salió a caminar de nuevo. Esta vez, no como cartero, sino como guardián de las memorias que nadie más podía entregar.'
),
(
    'El puente de los espejos',
    'Narrativo',
    'En el valle de Miradores existía un puente que los habitantes del lugar llamaban el Puente de los Espejos. No era un puente común: su superficie estaba cubierta de pequeños fragmentos de cristal pulido que reflejaban el cielo, las nubes y los rostros de quienes se atrevían a cruzarlo. La leyenda decía que quien caminara por el puente vería no solo su reflejo presente, sino también un instante de su futuro.

Sofía, una joven maestra que acababa de llegar al valle para ocupar la plaza de la escuela rural, escuchó la historia durante su primera cena en la posada del pueblo. Los comensales hablaban del puente con una mezcla de reverencia y temor. Ninguno admitía haberlo cruzado, pero todos conocían a alguien que sí lo había hecho.

Una tarde de domingo, cuando el valle se sumergía en un silencio espeso que solo rompían los pájaros y el viento, Sofía caminó hasta el puente. Lo encontró más pequeño de lo que imaginaba: apenas diez metros de largo, suspendido sobre un arroyo cristalino. Los fragmentos de espejo brillaban bajo el sol como escamas de un pez enorme.

Dio el primer paso y miró hacia abajo. Su reflejo le devolvió una sonrisa que ella no había dibujado. Dio otro paso y vio algo que la hizo detenerse: en el cristal, junto a su imagen, aparecía un aula llena de niños que la miraban con atención. Uno de ellos levantaba la mano. Otro escribía en un cuaderno. Una niña del fondo sonreía.

Sofía cruzó el puente con pasos cada vez más seguros. Al llegar al otro lado, se dio la vuelta y miró los espejos una última vez. Ya no mostraban nada extraordinario, solo el cielo azul y el agua del arroyo. Pero ella sabía lo que había visto: no era el futuro, era la razón por la que había venido al valle.

El lunes siguiente, cuando abrió la puerta de la escuela y vio a sus alumnos sentados en sus pupitres, reconoció cada rostro. Eran los mismos del puente. Y la niña del fondo, la que sonreía, fue la primera en decir: "Buenos días, maestra. La estábamos esperando."'
);

-- ────────────────────────────────────────────────────────────────────────────
-- ARGUMENTATIVO (3 textos generados — opinión con tesis y evidencia)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO readings (title, typology, content) VALUES
(
    'La lectura en papel: una práctica que no debe desaparecer',
    'Argumentativo',
    'En la era de las pantallas digitales, la lectura en papel ha sido relegada al ámbito de lo anticuado. Tabletas, lectores electrónicos y teléfonos inteligentes han transformado la manera en que accedemos a la información y consumimos textos literarios. Sin embargo, existen argumentos sólidos que respaldan la vigencia de la lectura en formato físico, no como un acto de nostalgia, sino como una práctica con beneficios cognitivos y emocionales comprobados.

En primer lugar, diversos estudios en neurociencia de la lectura han demostrado que la comprensión de textos largos es significativamente mejor cuando se realiza en papel. Una investigación publicada por la Universidad de Stavanger en Noruega concluyó que los lectores de textos impresos recuerdan con mayor precisión el orden de los eventos y los detalles del contenido en comparación con quienes leen el mismo texto en pantalla. Este fenómeno se atribuye a la experiencia táctil del papel: el grosor de las páginas leídas y por leer proporciona al cerebro una referencia espacial que facilita la ubicación de la información.

En segundo lugar, la lectura en papel reduce la fatiga visual. Las pantallas emiten luz azul que, tras períodos prolongados de exposición, genera cansancio ocular, dolores de cabeza y alteraciones del sueño. El papel, al no emitir luz propia, permite sesiones de lectura más extensas sin los efectos negativos asociados a los dispositivos electrónicos. Este aspecto resulta especialmente relevante en contextos educativos, donde los estudiantes dedican varias horas diarias a la lectura académica.

Además, el libro físico carece de notificaciones, enlaces y distracciones digitales que fragmentan la atención del lector. La lectura sostenida y profunda, aquella que permite la reflexión, el análisis y la conexión emocional con el texto, se ve favorecida por un soporte que no compite por la atención del usuario con aplicaciones, redes sociales o correos electrónicos.

No se trata de rechazar la tecnología ni de negar las ventajas del formato digital, que facilita el acceso masivo y el almacenamiento de grandes volúmenes de texto. Se trata de reconocer que el papel ofrece cualidades únicas que complementan, y en ciertos aspectos superan, la experiencia digital. Defender la lectura en papel es defender una forma de atención plena que la sociedad contemporánea necesita con urgencia.

Por todo lo anterior, las instituciones educativas, las bibliotecas públicas y las familias deben promover activamente la lectura en papel como una herramienta fundamental para el desarrollo cognitivo y el bienestar emocional. La convivencia entre lo digital y lo impreso no solo es posible, sino deseable.'
),
(
    'Los videojuegos como herramienta educativa: más allá del entretenimiento',
    'Argumentativo',
    'Durante décadas, los videojuegos han sido objeto de críticas que los señalan como una distracción perjudicial para el aprendizaje. Padres, educadores y medios de comunicación han sostenido que el tiempo dedicado a los videojuegos resta horas de estudio y fomenta conductas pasivas o violentas. Sin embargo, la evidencia científica acumulada en los últimos quince años demuestra que los videojuegos, cuando son diseñados y utilizados con criterio pedagógico, constituyen una herramienta educativa de gran potencial.

El primer argumento a favor de los videojuegos educativos es su capacidad para generar motivación intrínseca. Los sistemas de recompensas, niveles progresivos y retroalimentación inmediata que caracterizan el diseño de videojuegos activan los circuitos de dopamina del cerebro, generando un estado de compromiso que los métodos tradicionales de enseñanza difícilmente alcanzan. Un estudiante que resuelve problemas matemáticos dentro de un juego no percibe la actividad como una obligación, sino como un desafío voluntario.

El segundo argumento se relaciona con el aprendizaje situado. Los videojuegos crean entornos simulados donde el jugador debe aplicar conocimientos para resolver problemas contextualizados. Juegos como Minecraft Education Edition permiten explorar conceptos de geometría, química y programación dentro de un mundo virtual que el estudiante construye y modifica. Esta experiencia práctica y manipulativa refuerza la comprensión conceptual de maneras que una clase magistral no puede replicar.

Adicionalmente, los videojuegos multijugador fomentan habilidades sociales como la cooperación, la comunicación y la negociación. Los juegos de estrategia requieren que los jugadores coordinen acciones, distribuyan recursos y tomen decisiones colectivas bajo presión temporal. Estas competencias, conocidas como habilidades del siglo XXI, son altamente valoradas en el ámbito laboral y difíciles de desarrollar mediante ejercicios académicos convencionales.

Los críticos argumentan que la adicción y la violencia en los videojuegos representan riesgos reales. Estos riesgos existen, pero están asociados al uso indiscriminado y sin supervisión, no al medio en sí mismo. La mediación parental y la selección de contenidos apropiados son factores determinantes. Del mismo modo que un libro puede ser formativo o perjudicial según su contenido, un videojuego puede ser educativo o dañino según su diseño y el contexto de uso.

En conclusión, los videojuegos no deben ser descartados ni demonizados por el sistema educativo. Al contrario, deben ser integrados como un recurso didáctico complementario que aprovecha la familiaridad de los estudiantes con la tecnología para transformar el aprendizaje en una experiencia significativa, participativa y memorable.'
),
(
    '¿Por qué debemos proteger los páramos andinos?',
    'Argumentativo',
    'Los páramos andinos, ecosistemas de alta montaña ubicados por encima de los 3.000 metros de altitud, enfrentan una amenaza creciente por la expansión agrícola, la minería y el cambio climático. A pesar de ocupar una superficie relativamente pequeña en la geografía sudamericana, estos ecosistemas cumplen funciones ecológicas vitales que justifican su protección urgente e innegociable.

El argumento más contundente a favor de la conservación de los páramos es su función como fábricas de agua. Los suelos esponjosos de los páramos, ricos en materia orgánica, absorben el agua de la lluvia y la niebla, liberándola gradualmente hacia ríos y acuíferos que abastecen a millones de personas en ciudades como Bogotá, Quito y Mérida. La destrucción de un páramo no solo elimina un paisaje, sino que compromete el suministro de agua potable de poblaciones enteras.

En segundo lugar, los páramos albergan una biodiversidad única y altamente especializada. Especies como el frailejón, planta endémica que puede tardar un siglo en alcanzar su tamaño adulto, no existen en ningún otro ecosistema del planeta. La extinción de estas especies representaría una pérdida irreversible para el patrimonio natural y genético de la humanidad. Además, muchas de estas plantas poseen propiedades medicinales que aún no han sido estudiadas en profundidad.

En tercer lugar, los páramos funcionan como sumideros de carbono. Su suelo almacena cantidades significativas de dióxido de carbono, contribuyendo a mitigar el calentamiento global. La transformación de páramos en tierras de cultivo o pastoreo libera este carbono a la atmósfera, agravando el problema climático que la comunidad internacional intenta resolver mediante costosos acuerdos multilaterales.

Quienes se oponen a la protección estricta de los páramos argumentan que las comunidades locales dependen económicamente de la agricultura y la ganadería en estas zonas. Este argumento es legítimo, pero no invalida la necesidad de protección. La solución reside en programas de compensación económica y en el desarrollo de alternativas productivas sostenibles, como el ecoturismo y la producción de artesanías, que permitan a las comunidades mantener sus medios de vida sin destruir el ecosistema.

La protección de los páramos andinos no es un lujo ambientalista, sino una necesidad estratégica para la supervivencia hídrica, biológica y climática de la región. Los gobiernos, las organizaciones internacionales y la sociedad civil deben actuar de manera coordinada para garantizar que estos ecosistemas sobrevivan a las presiones del presente y continúen prestando sus servicios esenciales a las generaciones futuras.'
);

-- ────────────────────────────────────────────────────────────────────────────
-- EXPOSITIVO (3 textos generados — informativos sobre temas educativos)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO readings (title, typology, content) VALUES
(
    'El sistema solar: una visión general de nuestro vecindario cósmico',
    'Expositivo',
    'El sistema solar es el conjunto de cuerpos celestes que orbitan alrededor del Sol, una estrella de tipo espectral G2V ubicada en uno de los brazos espirales de la Vía Láctea. Compuesto por ocho planetas, cinco planetas enanos reconocidos oficialmente, más de doscientas lunas naturales, millones de asteroides y miles de millones de cometas, el sistema solar se extiende a lo largo de aproximadamente 4.500 millones de kilómetros desde el Sol hasta la órbita de Neptuno.

Los planetas del sistema solar se dividen en dos categorías principales. Los planetas interiores o rocosos —Mercurio, Venus, Tierra y Marte— se caracterizan por tener superficies sólidas, tamaños relativamente pequeños y pocas o ninguna luna natural. La Tierra destaca entre ellos por ser el único cuerpo conocido que alberga vida, gracias a la presencia de agua líquida en su superficie y una atmósfera rica en nitrógeno y oxígeno.

Los planetas exteriores o gigantes —Júpiter, Saturno, Urano y Neptuno— son considerablemente más grandes que los interiores y están compuestos principalmente por gases y hielos. Júpiter, el mayor de todos, tiene una masa equivalente a 318 veces la de la Tierra y posee al menos 95 lunas conocidas. Saturno es reconocido por su espectacular sistema de anillos, formados por partículas de hielo y roca que orbitan el planeta en un plano ecuatorial.

Entre las órbitas de Marte y Júpiter se encuentra el cinturón de asteroides, una región poblada por millones de cuerpos rocosos de tamaños diversos. El mayor de ellos, Ceres, fue reclasificado como planeta enano en 2006 por la Unión Astronómica Internacional. Más allá de Neptuno se extiende el cinturón de Kuiper, donde residen Plutón y otros objetos transneptunianos.

El Sol, centro gravitacional del sistema, contiene el 99.86 por ciento de la masa total del sistema solar. Su energía, producida por reacciones de fusión nuclear en las que átomos de hidrógeno se combinan para formar helio, viaja a la velocidad de la luz y tarda aproximadamente ocho minutos en llegar a la Tierra. Esta energía es la fuente primaria de calor y luz que sustenta la vida en nuestro planeta.

El estudio del sistema solar ha avanzado significativamente gracias a misiones espaciales como Voyager, Cassini y New Horizons, que han proporcionado imágenes detalladas y datos científicos de planetas, lunas y otros cuerpos que antes solo podían observarse desde telescopios terrestres. Cada nueva misión amplía nuestro entendimiento del vecindario cósmico en el que habitamos y nos acerca a responder preguntas fundamentales sobre el origen y la evolución del universo.'
),
(
    'La fotosíntesis: el proceso que sostiene la vida en la Tierra',
    'Expositivo',
    'La fotosíntesis es el proceso bioquímico mediante el cual los organismos autótrofos, principalmente las plantas, las algas y ciertas bacterias, convierten la energía lumínica del sol en energía química almacenada en moléculas de glucosa. Este proceso es fundamental para la vida en la Tierra, ya que produce el oxígeno que respiran la mayoría de los seres vivos y constituye la base de las cadenas alimenticias de casi todos los ecosistemas.

El proceso de la fotosíntesis ocurre principalmente en los cloroplastos, orgánulos celulares que contienen un pigmento verde llamado clorofila. La clorofila tiene la capacidad de absorber la luz solar, especialmente las longitudes de onda correspondientes al rojo y al azul del espectro visible, reflejando la luz verde, lo que explica el color característico de la vegetación.

La fotosíntesis se desarrolla en dos fases complementarias. La primera, conocida como fase lumínica o fase clara, ocurre en las membranas tilacoides del cloroplasto. Durante esta fase, la energía de la luz solar se utiliza para romper moléculas de agua en un proceso llamado fotólisis, liberando oxígeno como subproducto. La energía capturada se almacena temporalmente en moléculas de ATP y NADPH, que servirán como combustible para la segunda fase.

La segunda fase, denominada ciclo de Calvin o fase oscura, se desarrolla en el estroma del cloroplasto y no requiere luz directa para funcionar. En esta etapa, el dióxido de carbono absorbido de la atmósfera se combina con las moléculas energéticas producidas en la fase lumínica para sintetizar glucosa. La glucosa resultante es utilizada por la planta como fuente de energía para sus procesos metabólicos o como material de construcción para el crecimiento celular.

La ecuación general de la fotosíntesis puede resumirse de la siguiente manera: seis moléculas de dióxido de carbono más seis moléculas de agua, en presencia de luz solar, producen una molécula de glucosa y seis moléculas de oxígeno. Aunque la ecuación parece sencilla, el proceso involucra decenas de reacciones químicas intermedias catalizadas por enzimas específicas.

La importancia de la fotosíntesis trasciende el ámbito biológico. Los combustibles fósiles que la humanidad utiliza como principal fuente de energía —petróleo, carbón y gas natural— son el resultado de la fotosíntesis realizada por organismos que vivieron hace millones de años. Los esfuerzos actuales por desarrollar tecnologías de fotosíntesis artificial buscan replicar este proceso natural para producir combustibles limpios y reducir la dependencia de los recursos no renovables.'
),
(
    'El ciclo del agua: un viaje continuo entre cielo y tierra',
    'Expositivo',
    'El ciclo del agua, también conocido como ciclo hidrológico, es el proceso continuo de circulación del agua a través de los diferentes componentes del sistema terrestre: la atmósfera, la superficie terrestre, el subsuelo y los océanos. Este ciclo, impulsado por la energía del sol y la fuerza de la gravedad, no tiene un punto de inicio ni un punto final, sino que se repite de manera constante desde hace miles de millones de años.

El proceso comienza habitualmente con la evaporación, fenómeno mediante el cual el agua líquida de los océanos, ríos, lagos y superficies húmedas se transforma en vapor de agua al absorber energía solar. Los océanos, que cubren aproximadamente el 71 por ciento de la superficie terrestre, son la principal fuente de evaporación. A este proceso se suma la transpiración de las plantas, que liberan vapor de agua a través de pequeños poros en sus hojas llamados estomas. La combinación de evaporación y transpiración se conoce como evapotranspiración.

El vapor de agua asciende a la atmósfera, donde las bajas temperaturas provocan su condensación en torno a pequeñas partículas de polvo, sal o contaminantes llamadas núcleos de condensación. Las diminutas gotas de agua o cristales de hielo resultantes se agrupan formando nubes. La forma, altitud y densidad de las nubes dependen de las condiciones atmosféricas locales.

Cuando las gotas de agua en las nubes alcanzan un tamaño suficiente, caen a la superficie en forma de precipitación: lluvia, nieve, granizo o aguanieve. La precipitación es el principal mecanismo de transferencia de agua desde la atmósfera hacia la superficie terrestre. La cantidad y distribución de las precipitaciones varía enormemente según la ubicación geográfica, la altitud y los patrones climáticos estacionales.

Una vez en la superficie, el agua sigue diferentes caminos. Parte de ella se infiltra en el suelo, alimentando las aguas subterráneas y los acuíferos. Otra parte fluye sobre la superficie como escorrentía, formando arroyos y ríos que eventualmente desembocan en lagos o en el océano. En regiones frías, el agua puede acumularse en forma de hielo en glaciares y casquetes polares, donde puede permanecer almacenada durante miles de años antes de derretirse y reincorporarse al ciclo.

La comprensión del ciclo del agua es esencial para la gestión de los recursos hídricos, la predicción meteorológica, la agricultura y la planificación urbana. En un contexto de cambio climático, las alteraciones en los patrones de precipitación y evaporación tienen consecuencias directas sobre la disponibilidad de agua dulce, la frecuencia de eventos extremos como inundaciones y sequías, y la estabilidad de los ecosistemas que dependen del equilibrio hídrico.'
);

-- ────────────────────────────────────────────────────────────────────────────
-- INSTRUCTIVO (3 textos generados — guías paso a paso)
-- ────────────────────────────────────────────────────────────────────────────

INSERT INTO readings (title, typology, content) VALUES
(
    'Cómo preparar un herbario escolar paso a paso',
    'Instructivo',
    'Un herbario es una colección organizada de plantas secas y prensadas, montadas sobre hojas de cartulina e identificadas con su nombre común y científico. La elaboración de un herbario escolar es una actividad práctica que permite a los estudiantes conocer la flora de su entorno, desarrollar habilidades de observación y familiarizarse con la clasificación botánica. A continuación se describen los pasos necesarios para elaborar un herbario correctamente.

Paso 1: Recolección de muestras. Seleccione un área de recolección, preferiblemente un parque, un jardín o una zona rural cercana a la institución educativa. Recoja muestras completas de plantas que incluyan hojas, flores y, cuando sea posible, raíces. Utilice tijeras de podar o una navaja y corte las muestras con cuidado para no dañar la planta madre. Coloque cada muestra dentro de una bolsa plástica con una etiqueta que indique la fecha, el lugar de recolección y una descripción breve del hábitat.

Paso 2: Prensado de las muestras. Coloque cada muestra entre dos hojas de papel periódico, asegurándose de que las hojas, pétalos y tallos queden extendidos y sin sobreponerse. Apile las muestras con hojas de periódico entre cada una y colóquelas dentro de una prensa botánica o entre dos tablas de madera sujetas con cintas o cuerdas. Aplique peso uniforme sobre la pila utilizando libros pesados o ladrillos. Cambie el papel periódico cada dos días para evitar la aparición de hongos.

Paso 3: Secado. Mantenga las muestras prensadas en un lugar seco y ventilado durante un período de una a tres semanas, dependiendo del grosor de las muestras y las condiciones ambientales. Las muestras estarán listas cuando se sientan completamente rígidas y crujientes al tacto. Si alguna muestra presenta manchas oscuras o mal olor, descártela y reemplace con una nueva recolección.

Paso 4: Montaje. Pegue cada muestra seca sobre una hoja de cartulina blanca de tamaño carta utilizando cinta adhesiva transparente o pequeñas tiras de papel engomado. Evite utilizar pegamento líquido, ya que puede humedecer y deteriorar las muestras. En la esquina inferior derecha de cada cartulina, adhiera una etiqueta con la siguiente información: nombre común de la planta, nombre científico, familia botánica, lugar y fecha de recolección, y nombre del recolector.

Paso 5: Organización y conservación. Ordene las cartulinas por familia botánica o por orden alfabético del nombre científico. Guárdelas en carpetas o cajas rígidas que protejan las muestras de la humedad, el polvo y los insectos. Puede añadir bolitas de naftalina o sobres de gel de sílice para absorber la humedad residual. Revise el herbario periódicamente y reemplace las muestras dañadas.

Un herbario bien elaborado puede conservarse durante décadas si se almacena correctamente. Además de su valor pedagógico, constituye un registro botánico del entorno local que puede enriquecerse con nuevas muestras cada ciclo escolar.'
),
(
    'Guía para escribir un ensayo argumentativo',
    'Instructivo',
    'El ensayo argumentativo es un texto académico en el que el autor expone una tesis sobre un tema determinado y la defiende mediante argumentos lógicos, evidencias y razonamientos. Su propósito es persuadir al lector de la validez de una posición específica. A continuación se presenta una guía detallada para escribir un ensayo argumentativo de calidad.

Paso 1: Selección del tema. Elija un tema que sea debatible, es decir, que admita posiciones a favor y en contra. Evite temas sobre los cuales existe consenso universal, ya que no permiten construir una argumentación interesante. Asegúrese de que el tema le resulte relevante y de que exista información suficiente para respaldar su posición. Algunos ejemplos de temas argumentativos son: el uso de uniformes escolares, la prohibición de plásticos de un solo uso o la implementación del voto electrónico.

Paso 2: Investigación y documentación. Antes de comenzar a escribir, investigue el tema en fuentes confiables: libros académicos, artículos de revistas especializadas, informes de organismos oficiales y estudios estadísticos. Registre las ideas principales, los datos relevantes y las citas textuales que podrían servir como evidencia. Organice la información en un esquema que distinga los argumentos a favor de su tesis y los posibles contraargumentos.

Paso 3: Formulación de la tesis. Redacte una oración clara y concisa que exprese su posición sobre el tema. La tesis debe ser específica y verificable. Evite tesis vagas como "la educación es importante" y opte por formulaciones precisas como "la incorporación de metodologías activas en la educación secundaria mejora significativamente los resultados académicos de los estudiantes". La tesis será la columna vertebral de su ensayo y cada párrafo deberá contribuir a sustentarla.

Paso 4: Estructura del ensayo. Organice su ensayo en tres secciones principales. La introducción debe presentar el tema, contextualizar la problemática y enunciar la tesis. El desarrollo debe contener al menos tres párrafos argumentativos, cada uno con una idea principal respaldada por evidencias, ejemplos o datos. Incluya un párrafo dedicado a presentar y refutar un contraargumento, lo cual demuestra rigor intelectual. La conclusión debe sintetizar los argumentos presentados, reafirmar la tesis y proponer una reflexión final o una llamada a la acción.

Paso 5: Redacción y revisión. Escriba un primer borrador sin preocuparse excesivamente por la perfección. Luego, revise el texto prestando atención a la coherencia lógica entre los párrafos, la claridad de las ideas, la corrección gramatical y ortográfica, y la adecuación del tono académico. Solicite a un compañero o docente que lea el ensayo y ofrezca retroalimentación. Realice las correcciones necesarias y redacte la versión final.

Un ensayo argumentativo bien escrito no solo demuestra conocimiento sobre el tema, sino también capacidad de análisis crítico, habilidad para estructurar ideas de manera coherente y competencia comunicativa. Estas destrezas son fundamentales en el ámbito académico y profesional.'
),
(
    'Primeros auxilios básicos: qué hacer ante una quemadura leve',
    'Instructivo',
    'Las quemaduras leves, clasificadas médicamente como quemaduras de primer grado, son lesiones superficiales de la piel causadas por la exposición al calor, el sol, líquidos calientes o el contacto breve con superficies calientes. Aunque generalmente no representan un riesgo grave para la salud, requieren atención inmediata y adecuada para aliviar el dolor, prevenir infecciones y facilitar la recuperación. A continuación se describen los pasos que deben seguirse ante una quemadura leve.

Paso 1: Retire la fuente de calor. Aleje a la persona afectada de la fuente que causó la quemadura. Si la ropa está en contacto con la zona afectada y no está adherida a la piel, retírela con cuidado. Si la ropa está pegada a la quemadura, no intente desprenderla, ya que podría agravar la lesión.

Paso 2: Enfríe la quemadura con agua. Coloque la zona afectada bajo un chorro suave de agua fresca, no fría, durante un período de diez a veinte minutos. El agua ayuda a reducir la temperatura de la piel, alivia el dolor y limita la extensión del daño tisular. No utilice hielo, agua helada ni sustancias caseras como mantequilla, pasta de dientes o aceite, ya que pueden empeorar la quemadura o provocar infecciones.

Paso 3: Evalúe la gravedad. Una quemadura de primer grado se caracteriza por enrojecimiento de la piel, dolor moderado e hinchazón leve. No presenta ampollas ni pérdida de piel. Si la quemadura presenta ampollas, coloración blanca o marrón, o si afecta una superficie mayor que la palma de la mano de la persona afectada, se trata de una quemadura de segundo o tercer grado que requiere atención médica inmediata.

Paso 4: Aplique un apósito protector. Una vez que la quemadura se ha enfriado, cubra la zona con una gasa estéril o un apósito limpio y no adherente. Fije el apósito con cinta adhesiva médica, sin ejercer presión sobre la quemadura. El apósito protege la zona afectada del roce, el polvo y las bacterias. Cámbielo cada veinticuatro horas o cuando se ensucie.

Paso 5: Alivie el dolor. Si el dolor persiste, puede administrarse un analgésico de venta libre como ibuprofeno o paracetamol, siguiendo las indicaciones del envase y respetando las dosis recomendadas según la edad y el peso de la persona. Evite aplicar cremas anestésicas sin indicación médica.

Paso 6: Vigile la evolución. Observe la quemadura durante los días siguientes. Si aparecen signos de infección como aumento del enrojecimiento, pus, fiebre o dolor creciente, acuda a un centro de salud. Una quemadura leve tratada correctamente suele sanar en un plazo de siete a diez días sin dejar cicatrices.

La prevención es siempre la mejor estrategia. Mantenga los mangos de las ollas hacia el interior de la cocina, use protector solar en actividades al aire libre, supervise a los niños cerca de fuentes de calor y mantenga los productos inflamables fuera del alcance de los menores.'
);
