-- ============================================================================
-- 002_seed.sql — Lectura inicial: Baños de Agua Santa + 12 preguntas
-- Las demás lecturas se importan desde los JSON con import_json_readings.py
-- ============================================================================

INSERT INTO readings (title, typology, type, content) VALUES
(
    'Baños de Agua Santa: Naturaleza, aventura y espiritualidad en el corazón del Ecuador',
    'Descriptivo',
    'Texto descriptivo geográfico-cultural',
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
);

-- Obtener el ID de la lectura recién insertada
DO $$
DECLARE
    v_reading_id INTEGER;
    v_q_id INTEGER;
BEGIN
    SELECT id INTO v_reading_id FROM readings
    WHERE title = 'Baños de Agua Santa: Naturaleza, aventura y espiritualidad en el corazón del Ecuador'
    LIMIT 1;

    -- ── LITERAL (4 preguntas) ────────────────────────────────────────────

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 1, 'Literal', '¿En qué provincia se encuentra la ciudad de Baños de Agua Santa?', 'B',
            'El primer párrafo indica que está ubicada en la provincia de Tungurahua.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Cotopaxi'),
        (v_q_id, 'B', 'Tungurahua'),
        (v_q_id, 'C', 'Chimborazo'),
        (v_q_id, 'D', 'Pastaza');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 2, 'Literal', '¿Qué volcán domina el horizonte de la ciudad?', 'C',
            'El texto señala que la ciudad se encuentra a los pies del Volcán Tungurahua.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Cotopaxi'),
        (v_q_id, 'B', 'Sangay'),
        (v_q_id, 'C', 'Tungurahua'),
        (v_q_id, 'D', 'Chimborazo');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 3, 'Literal', '¿Cuál es la cascada más destacada en la Ruta de las Cascadas?', 'A',
            'Se menciona explícitamente el Pailón del Diablo como la más impresionante.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'El Pailón del Diablo'),
        (v_q_id, 'B', 'La Cascada de San Jorge'),
        (v_q_id, 'C', 'El Manto de la Novia'),
        (v_q_id, 'D', 'La Cascada del Río Verde');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 4, 'Literal', '¿Qué dulce tradicional se menciona en el texto?', 'D',
            'Se describe la melcocha como un dulce elaborado con panela estirada manualmente.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Empanadas de viento'),
        (v_q_id, 'B', 'Dulce de guayaba'),
        (v_q_id, 'C', 'Colaciones'),
        (v_q_id, 'D', 'Melcocha');

    -- ── INFERENCIAL (4 preguntas) ────────────────────────────────────────

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 5, 'Inferencial', '¿Cuál es el tema principal del texto?', 'B',
            'Todo el texto describe las características geográficas, culturales y turísticas de Baños.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'La historia del Volcán Tungurahua'),
        (v_q_id, 'B', 'La descripción integral de Baños como destino turístico'),
        (v_q_id, 'C', 'Los problemas ambientales de la Amazonía'),
        (v_q_id, 'D', 'La economía agrícola de Tungurahua');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 6, 'Inferencial', '¿Por qué la actividad volcánica ha sido beneficiosa para Baños?', 'C',
            'El texto relaciona la actividad volcánica con la fertilidad del suelo y las aguas termales.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Porque atrae vulcanólogos internacionales'),
        (v_q_id, 'B', 'Porque genera energía eléctrica'),
        (v_q_id, 'C', 'Porque ha contribuido a la fertilidad de los suelos y a las aguas termales'),
        (v_q_id, 'D', 'Porque ha formado nuevas montañas');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 7, 'Inferencial', '¿Qué relación establece el texto entre las lluvias y el paisaje?', 'B',
            'Se indica que las lluvias breves intensifican el verdor del paisaje.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Las lluvias destruyen la vegetación'),
        (v_q_id, 'B', 'Las lluvias intensifican el verdor del paisaje'),
        (v_q_id, 'C', 'Las lluvias impiden el turismo'),
        (v_q_id, 'D', 'Las lluvias generan inundaciones frecuentes');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 8, 'Inferencial', '¿Qué idea resume mejor el último párrafo?', 'A',
            'El cierre presenta a Baños como un espacio diverso que refleja la riqueza del país.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Baños es un destino diverso que refleja la riqueza geográfica y cultural del país'),
        (v_q_id, 'B', 'Baños necesita más infraestructura turística'),
        (v_q_id, 'C', 'El turismo ha destruido la naturaleza local'),
        (v_q_id, 'D', 'Solo los ecuatorianos deberían visitar Baños');

    -- ── CRÍTICO (4 preguntas) ────────────────────────────────────────────

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 9, 'Critico', '¿Por qué el autor describe la neblina matutina que "se disipa"?', 'C',
            'La neblina que se levanta simboliza el paso del misterio a la claridad, recurso descriptivo del autor.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Para informar sobre el pronóstico del clima'),
        (v_q_id, 'B', 'Para advertir sobre peligros naturales'),
        (v_q_id, 'C', 'Para crear un contraste entre misterio y claridad en el paisaje'),
        (v_q_id, 'D', 'Para explicar el ciclo del agua');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 10, 'Critico', '¿Qué función cumple la mención de la Basílica en el texto?', 'B',
            'La Basílica aporta la dimensión espiritual al texto, complementando lo natural y lo aventurero.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Promover una religión específica'),
        (v_q_id, 'B', 'Destacar la dimensión espiritual y cultural de Baños'),
        (v_q_id, 'C', 'Criticar las tradiciones religiosas'),
        (v_q_id, 'D', 'Describir la arquitectura colonial del Ecuador');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 11, 'Critico', '¿Por qué el autor enfatiza que la economía "gira en torno al turismo"?', 'A',
            'Se evidencia la dependencia económica del turismo como motor principal de la ciudad.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'Para evidenciar la importancia económica del turismo para la ciudad'),
        (v_q_id, 'B', 'Para criticar la falta de industria'),
        (v_q_id, 'C', 'Para sugerir que el turismo debe eliminarse'),
        (v_q_id, 'D', 'Para comparar Baños con otras ciudades');

    INSERT INTO questions (reading_id, question_number, comprehension_level, question_text, correct_answer, justification)
    VALUES (v_reading_id, 12, 'Critico', '¿Cuál es el mensaje implícito del texto?', 'C',
            'El texto invita al lector a valorar la convergencia de naturaleza, cultura y tradición en Ecuador.')
    RETURNING id INTO v_q_id;
    INSERT INTO answers (question_id, letter, answer_text) VALUES
        (v_q_id, 'A', 'El volcán Tungurahua es peligroso para los habitantes'),
        (v_q_id, 'B', 'Los turistas extranjeros prefieren otros destinos'),
        (v_q_id, 'C', 'La riqueza natural y cultural de Ecuador merece ser valorada y conocida'),
        (v_q_id, 'D', 'Baños solo es interesante por sus aguas termales');

END $$;
