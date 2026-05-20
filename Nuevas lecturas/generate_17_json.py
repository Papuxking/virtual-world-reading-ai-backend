import json
import PyPDF2
import os

pdf_path = r'c:\Users\Kevin\Desktop\Proyecto Godot Prácticas\PROYECTO\Docker\Nuevas lecturas\LECTURAS TIPOLOGÍAS TEXTUALES.pdf'

# Metadata de las 17 lecturas: títulos, tipologías, y las preguntas
readings_meta = [
    {
        "title": "U.S.A. que te usa",
        "typology": "narrativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿A qué ciudad de Estados Unidos planea viajar Manuel?",
                "ans": [
                    "A) Nueva York",
                    "B) Miami",
                    "C) Chicago",
                    "D) Los Ángeles"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué sentimiento predomina en Manuel al abandonar su país natal?",
                "ans": [
                    "A) Alegría inmensa por el éxito de su tía Raquel.",
                    "B) Tristeza, frustración y deseo desesperado de escapar de su estancamiento personal.",
                    "C) Indiferencia absoluta hacia su familia y costumbres.",
                    "D) Miedo a fracasar en su trabajo como escritor."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué simboliza la \"verdadera vida\" a la que aspira el protagonista al final del fragmento?",
                "ans": [
                    "A) Conseguir el antiguo puesto de su jefe.",
                    "B) Encontrar un árbol plateado de Navidad.",
                    "C) La búsqueda de su identidad propia y libertad, al margen de las expectativas y fracasos de su entorno.",
                    "D) El deseo de ganar mucho dinero para presumir en su país."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "¿Qué familiar de Manuel vive en Chicago y le escribe a su madre sobre sus éxitos?",
                "ans": [
                    "A) Su novia",
                    "B) Su tía Raquel",
                    "C) Su abuela",
                    "D) Su hermana"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué la tía Raquel le dice a Manuel que solo podrá quedarse «unos días»?",
                "ans": [
                    "A) Porque su casa es muy pequeña.",
                    "B) Porque en ese país cada cual debe vivir su propia vida y valerse por sí mismo.",
                    "C) Porque no le agrada su sobrino.",
                    "D) Porque su marido gringo no acepta visitas."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué crítica social se puede inferir sobre la visión idealizada de la migración en el texto?",
                "ans": [
                    "A) Que el extranjero es un paraíso donde todos triunfan sin esfuerzo.",
                    "B) Que el éxito migratorio muchas veces esconde individualismo y soledad.",
                    "C) Que las familias siempre apoyan económicamente a sus parientes en el exterior.",
                    "D) Que el trabajo en el país natal es más duro que en Estados Unidos."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Madame Bovary",
        "typology": "narrativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Con quién se encontró León en la fonda al ir a cenar?",
                "ans": [
                    "A) Monsieur Homais",
                    "B) Binet",
                    "C) Justin",
                    "D) Madame Bovary"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué impresión interna causó en León la conversación de dos horas que tuvo la noche anterior con la dama?",
                "ans": [
                    "A) Le provocó indiferencia y lo hizo volver a sus acuarelas.",
                    "B) Le generó un gran impacto y asombro al descubrir que podía expresarse y dialogar mucho mejor de lo que creía.",
                    "C) Lo hizo sentir avergonzado por su timidez extrema.",
                    "D) Le hizo desear estudiar más música."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "Según la descripción que hace el autor, ¿cómo se percibe el carácter de León en la sociedad de Yonville?",
                "ans": [
                    "A) Como un joven rebelde, peligroso y políticamente exaltado.",
                    "B) Como un charlatán interesado únicamente en escalar de clase.",
                    "C) Como un joven educado, respetuoso, algo tímido y dotado de aficiones refinadas.",
                    "D) Como un campesino tosco y sin habilidades."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "¿De qué tareas se encargaba Justin, además del cuidado de los niños?",
                "ans": [
                    "A) De pintar acuarelas",
                    "B) De la contabilidad del notario",
                    "C) De ayudar en las tareas domésticas y la botica",
                    "D) De enseñar música"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué sugiere la mención a que los hijos del matrimonio Homais salían «un poco linfáticos» a su madre?",
                "ans": [
                    "A) Que heredaron el talento musical de su madre.",
                    "B) Que tenían una constitución débil y un carácter similar al de ella.",
                    "C) Que eran deportistas y llenos de energía.",
                    "D) Que eran hijos adoptados."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué revela la actitud de León sobre los estereotipos de la época?",
                "ans": [
                    "A) Que los hombres debían ser toscos para ser respetados.",
                    "B) Que la sensibilidad y el gusto literario eran vistos como cualidades peculiares pero bien consideradas.",
                    "C) Que a los jóvenes se les prohibía leer literatura.",
                    "D) Que la política exaltada era requisito social."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Cuando los guayacanes florecían",
        "typology": "narrativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Qué hacían los niños en las calles después de bañarse en la lluvia?",
                "ans": [
                    "A) Se secaban rápidamente para evitar resfriados.",
                    "B) Se amontonaban en las bocacalles a jugar con barquichuelos de papel en las cunetas.",
                    "C) Ayudaban a arrancar de raíz las matas de plátano.",
                    "D) Atrapaban a las víboras que subían a las casas."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué efecto principal produce la llegada de las primeras lluvias en el entorno natural y social descrito?",
                "ans": [
                    "A) Genera una sequía extrema que marchita el monte verde.",
                    "B) Revitaliza la naturaleza provocando crecientes feroces en los ríos, al mismo tiempo que desata la vitalidad infantil en el lodo.",
                    "C) Ahuyenta a todos los insectos e impide que las chicharras canten.",
                    "D) Destruye por completo las viviendas de la ciudad."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Cómo utiliza el autor el flujo del agua como elemento narrativo en este pasaje?",
                "ans": [
                    "A) Demostrando que los humanos siempre controlan la naturaleza.",
                    "B) Como una fuerza reveladora que, por un lado, desnuda la basura y el desaseo del pueblo, y por el otro, arrastra la vegetación demostrando su inmenso poder.",
                    "C) Explicando científicamente el ciclo hidráulico de los ríos.",
                    "D) Criticando exclusivamente el pésimo alcantarillado de la ciudad."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿Qué encontraban las mujeres y niños en las hamacas y rincones de las casas durante esta época?",
                "ans": [
                    "A) Chicharras",
                    "B) Barquichuelos de papel",
                    "C) Víboras",
                    "D) Cucarachas"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué sugiere la costumbre de los niños de sacar los «coco-chiles» del lodo y comerlos?",
                "ans": [
                    "A) Su extrema higiene",
                    "B) La conexión profunda y silvestre de la infancia con la naturaleza que renace tras la lluvia",
                    "C) Una escasez absoluta de alimentos en las casas",
                    "D) El miedo a los animales peligrosos"
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿De qué manera la descripción del entorno natural refleja la identidad cultural y social de la comunidad?",
                "ans": [
                    "A) Muestra una ciudad hiperindustrializada ajena al clima.",
                    "B) Evidencia cómo la vida cotidiana del pueblo está íntimamente entrelazada con los ciclos de la naturaleza tropical.",
                    "C) Critica la educación formal de los niños.",
                    "D) Idealiza el verano seco como la única época feliz."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Una noche intranquila",
        "typology": "narrativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Qué animal escondió una pata de pollo en la sala para comerla después?",
                "ans": [
                    "A) El gato Iván Ivánich.",
                    "B) El amo.",
                    "C) El perro llamado \"Tío\".",
                    "D) El cerdo en el cobertizo."
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué originó verdaderamente el pánico de \"Tío\" en medio de la oscuridad?",
                "ans": [
                    "A) El sonido del amo suspirando profundamente.",
                    "B) El gruñido habitual del cerdo.",
                    "C) Un grito salvaje, estridente y antinatural emitido por Iván Ivánich.",
                    "D) El recuerdo del portero con la escoba en su pesadilla."
                ],
                "corr": "C"
            },
            {
                "level": "Crítico",
                "q": "¿Qué recurso literario destaca en el relato al ponerle pensamientos sobre esconder comida al perro?",
                "ans": [
                    "A) Personificación, ya que dota al animal de procesos de razonamiento, preocupaciones y emociones casi humanas.",
                    "B) Sátira política dirigida contra los dueños de mascotas.",
                    "C) Metáfora abstracta sobre el miedo a la muerte en la oscuridad.",
                    "D) Una crítica social al maltrato animal en el siglo XIX."
                ],
                "corr": "A"
            },
            {
                "level": "Literal",
                "q": "¿Qué hizo el Tío al sentir que le invadía el terror en la oscuridad?",
                "ans": [
                    "A) Huyó al cobertizo",
                    "B) Le entraron ganas de ladrar y gruñó",
                    "C) Se escondió bajo la cama",
                    "D) Atacó a Iván Ivánich"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué el Tío prefería cerrar los ojos y dormirse pronto tras asustarse?",
                "ans": [
                    "A) Porque sabía por experiencia que al dormir llegaría antes la mañana",
                    "B) Porque la pata de pollo le daba sueño",
                    "C) Porque así no vería a los ladrones",
                    "D) Porque el amo se lo había ordenado"
                ],
                "corr": "A"
            },
            {
                "level": "Crítico",
                "q": "¿Cómo contribuye el contraste entre la tranquilidad inicial y el grito estridente a la atmósfera del relato?",
                "ans": [
                    "A) Produce un efecto cómico exagerado.",
                    "B) Transforma una simple noche de descanso en una experiencia de terror psicológico desde la perspectiva animal.",
                    "C) Demuestra que los animales no sienten miedo.",
                    "D) Hace que el lector pierda el interés."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Sobre el círculo de la comprensión",
        "typology": "argumentativo",
        "questions": [
            {
                "level": "Literal",
                "q": "Según el texto, ¿qué proceso es necesario antes de tratar de comprender las distintas partes de una frase en una lengua extranjera?",
                "ans": [
                    "A) Olvidar la lengua materna.",
                    "B) \"Construir\" una frase regida por una expectativa de sentido derivada del contexto.",
                    "C) Buscar todas las palabras en el diccionario simultáneamente.",
                    "D) Memorizar palabras al azar."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿A qué se refiere el autor con que la comprensión discurre \"del todo a la parte y de nuevo al todo\"?",
                "ans": [
                    "A) A que un libro debe leerse siempre desde la última página hacia la primera.",
                    "B) A que el sentido de una palabra individual depende del contexto general, y al entender la palabra, se retroalimenta y amplía el entendimiento del contexto completo.",
                    "C) A que el traductor debe ignorar las partes que no entiende.",
                    "D) A que el conocimiento literario es un ciclo repetitivo inútil."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Por qué resulta fundamental la distinción de Schleiermacher entre la vertiente objetiva y subjetiva al analizar un texto?",
                "ans": [
                    "A) Porque demuestra que las obras de todos los escritores significan lo mismo.",
                    "B) Porque establece que un texto no solo es una pieza lingüística dentro de un género (objetivo), sino también la manifestación de la vida interior y creativa del autor (subjetivo).",
                    "C) Porque argumenta que la psicología es más importante que la gramática.",
                    "D) Porque prueba que la retórica antigua carece de utilidad en la literatura moderna."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿De qué antigua disciplina procede la regla hermenéutica mencionada por el autor?",
                "ans": [
                    "A) De la matemática pura",
                    "B) De la retórica antigua",
                    "C) De la astronomía",
                    "D) De la medicina"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Si el texto entra en conflicto con nuestra expectativa de sentido previa, ¿qué acción debemos tomar según el autor?",
                "ans": [
                    "A) Desechar el texto por considerarlo erróneo.",
                    "B) Reajustar la expectativa original para hacer confluir el texto en una nueva unidad de pensamiento.",
                    "C) Cambiar las palabras del texto.",
                    "D) Ignorar el contexto anterior."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué implicaciones tiene el «fracaso de la comprensión» mencionado en el texto para la labor de traducción?",
                "ans": [
                    "A) Que el traductor nunca debe intentar comprender la obra completa.",
                    "B) Que si los detalles no se integran de manera lógica en la totalidad, la interpretación resultante será inválida o fragmentaria.",
                    "C) Que todas las lenguas son imposibles de aprender.",
                    "D) Que el sentido subjetivo del autor no importa."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "El laberinto de la soledad",
        "typology": "argumentativo",
        "questions": [
            {
                "level": "Literal",
                "q": "Según el texto, ¿en qué etapa de la vida se nos suele revelar nuestra existencia como algo particular e intransferible?",
                "ans": [
                    "A) En la niñez temprana.",
                    "B) En la adolescencia.",
                    "C) En la adultez.",
                    "D) En la vejez."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué paralelo conceptual establece el autor entre el adolescente y los \"pueblos en trance de crecimiento\"?",
                "ans": [
                    "A) Ambos viven en la ignorancia feliz sin preocuparse del mañana.",
                    "B) Ambos experimentan un momento crítico de reflexión y auto-interrogación para descubrir su verdadera identidad y singularidad.",
                    "C) Ambos ignoran por completo las consecuencias de sus acciones en la historia.",
                    "D) Ambos se rebelan violentamente contra las tradiciones impuestas."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Cuál es el significado profundo de la aseveración \"Despertar a la historia significa adquirir conciencia de nuestra singularidad\"?",
                "ans": [
                    "A) Que el verdadero desarrollo de una nación comienza cuando asume reflexivamente quién es frente al mundo y define su propia ruta.",
                    "B) Que es necesario memorizar las fechas de las batallas históricas para ser ciudadano.",
                    "C) Que los pueblos solo avanzan si olvidan por completo su pasado y sus tradiciones.",
                    "D) Que la historia es inmutable y ya todo está escrito."
                ],
                "corr": "A"
            },
            {
                "level": "Literal",
                "q": "¿Qué actitud toman los niños y los adultos para trascender su soledad y olvidarse de sí mismos?",
                "ans": [
                    "A) Leer libros de historia",
                    "B) Aislarse en sus habitaciones",
                    "C) A través del juego o el trabajo",
                    "D) Llorando en silencio"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "Cuando el autor menciona que «la máscara del viejo es la historia de unas facciones amorfas», ¿a qué se refiere?",
                "ans": [
                    "A) A que la historia de un pueblo empieza de forma confusa pero adquiere identidad y «rostro» consolidado a lo largo del tiempo.",
                    "B) A que los ancianos suelen usar máscaras reales.",
                    "C) A que el pasado histórico siempre es oculto.",
                    "D) A que la juventud es la única etapa valiosa."
                ],
                "corr": "A"
            },
            {
                "level": "Crítico",
                "q": "¿Qué cuestiona el texto acerca del concepto de «carácter nacional» o «genio de los pueblos»?",
                "ans": [
                    "A) Que es un mandato divino inalterable.",
                    "B) Que a menudo no es inmutable, sino una serie de respuestas y reacciones a circunstancias cambiantes.",
                    "C) Que no existe en absoluto.",
                    "D) Que es exactamente igual en todos los continentes."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Prohibido prohibir",
        "typology": "argumentativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Dónde se encontraba el liceo cuya problemática protagonizaba el documental que vio el autor?",
                "ans": [
                    "A) En el centro histórico de París.",
                    "B) En las afueras de París.",
                    "C) En el Magreb.",
                    "D) En América Latina."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué la actitud de la profesora que afirmaba «ahora todo anda bien, pero hay que saber arreglárselas» causó un fuerte impacto en el autor?",
                "ans": [
                    "A) Porque revelaba su inmenso amor y vocación por la pedagogía tradicional.",
                    "B) Porque demostraba una triste resignación docente, al considerar un logro sobrevivir diariamente a la violencia en lugar de dedicarse verdaderamente a educar.",
                    "C) Porque comprobó que el nivel académico de los alumnos era excelente gracias a ella.",
                    "D) Porque la profesora logró desarmar a los delincuentes sin ayuda policial."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué crítica implícita hace el texto frente a las \"soluciones\" implementadas en el colegio (detectores de metales, patrullas docentes, psicólogos de urgencia)?",
                "ans": [
                    "A) Aplaude estas medidas como el modelo ideal para todas las escuelas del futuro.",
                    "B) Denuncia que la institución educativa ha perdido su esencia formativa, transformándose en un espacio donde lo primordial es la supervivencia policial.",
                    "C) Sugiere que es el único método válido para educar estudiantes de distintos orígenes raciales.",
                    "D) Celebra el éxito rotundo del director al pacificar el colegio definitivamente."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿Qué medida específica se instaló en el colegio para evitar el ingreso de armas y que el director mostraba con satisfacción?",
                "ans": [
                    "A) Un muro eléctrico",
                    "B) Un detector de metales en la entrada",
                    "C) Cámaras de vigilancia",
                    "D) Perros policías"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué se dictó la disposición de que ni profesores ni alumnos circularan solos por el colegio?",
                "ans": [
                    "A) Para fomentar la amistad.",
                    "B) Para evitar ser víctimas de asaltos, violaciones y emboscadas en los pasillos.",
                    "C) Para ahorrar electricidad.",
                    "D) Para que no se perdieran."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué reflexiona el autor sobre el papel de la educación contemporánea basándose en este caso?",
                "ans": [
                    "A) Que la escuela se ha convertido en un espacio donde prima la supervivencia sobre la formación académica.",
                    "B) Que la disciplina militar enseña mejor.",
                    "C) Que la tecnología soluciona los problemas educativos.",
                    "D) Que la violencia es un mito."
                ],
                "corr": "A"
            }
        ]
    },
    {
        "title": "La Redención de Juan Montalvo",
        "typology": "argumentativo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿De qué año está fechado el anuncio sobre la venta de un niño esclavizado vinculado a los antepasados de Montalvo?",
                "ans": [
                    "A) 1851",
                    "B) 1604",
                    "C) 1840",
                    "D) 2019"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "Según el autor, ¿por qué dicho anuncio no representa una \"mancha\" sino el verdadero punto de partida de la grandeza del escritor?",
                "ans": [
                    "A) Porque con esa venta Montalvo financió la publicación de sus ensayos.",
                    "B) Porque haber presenciado la esclavitud en su entorno familiar motivó su despertar de conciencia y su férrea voluntad de abolirla de por vida.",
                    "C) Porque fue el propio Montalvo quien escribió y firmó el documento comercial.",
                    "D) Porque gracias al anuncio, conoció al General José María Urbina."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué lección ética principal intenta destacar el texto acerca de la figura histórica de Juan Montalvo frente a su legado familiar?",
                "ans": [
                    "A) Que siempre el fin justifica los medios en política.",
                    "B) Que la verdadera altura moral consiste en tener la valentía para juzgar y corregir los errores e injusticias presentes en nuestras propias raíces.",
                    "C) Que es lícito mantener esclavos si las leyes del momento lo permiten.",
                    "D) Que los próceres nunca se equivocan."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿Quién fue el General con el que Juan Montalvo formó una alianza para apoyar la abolición de la esclavitud?",
                "ans": [
                    "A) Simón Bolívar",
                    "B) Eloy Alfaro",
                    "C) José María Urbina",
                    "D) Antonio José de Sucre"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿A qué se refiere la frase: «Montalvo es el hombre que nació entre cadenas y decidió dedicar su vida entera a fundirlas»?",
                "ans": [
                    "A) A que era herrero.",
                    "B) A que, pese a nacer en una élite que poseía esclavos, usó su intelecto para combatir ese sistema.",
                    "C) A que fue prisionero de guerra.",
                    "D) A que escapó de su casa."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Por qué la acción de Montalvo se califica como «la libertad intelectual de todo un continente»?",
                "ans": [
                    "A) Porque no hablaba de política.",
                    "B) Porque transformó un decreto administrativo en un postulado ético universal que inspiró el pensamiento libertario.",
                    "C) Porque compró la libertad de todos los esclavos.",
                    "D) Porque redactó la constitución."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "¿Qué es una lengua?",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿A qué compara el autor el \"continuo de diferenciación\" que poseen las lenguas humanas en la parte final del texto?",
                "ans": [
                    "A) A las especies animales.",
                    "B) Al hecho de que todos los seres humanos somos simples variantes de una misma especie genéticamente idéntica.",
                    "C) A los dialectos que se hablan en Huelva y Albacete.",
                    "D) A los programas de inteligencia artificial."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué el autor argumenta que resulta imposible traducir una obra a un \"lenguaje animal\"?",
                "ans": [
                    "A) Porque los animales no tienen voz para responder.",
                    "B) Porque los sistemas de comunicación animal carecen de la potente base estructural común y humana que permite la inter-traducción.",
                    "C) Porque el español no tiene palabras para describir los sonidos salvajes.",
                    "D) Porque no se ha estudiado lo suficiente a los animales."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Cómo desmonta el autor la idea de una separación estricta entre \"razas\" y entre \"lenguas\"?",
                "ans": [
                    "A) Afirmando que el español de Madrid es el único idioma universal y puro.",
                    "B) Evidenciando que tanto en la genética humana como en la lingüística, las variaciones son graduales (un continuo) pero descansan sobre una innegable matriz única común.",
                    "C) Exigiendo que en el futuro todos hablemos un solo idioma para evitar conflictos.",
                    "D) Asegurando que el ruso y el español son, de hecho, el mismo idioma."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿Qué ejemplos de profesiones cita el autor para demostrar que todas las lenguas humanas se parecen bastante entre sí?",
                "ans": [
                    "A) Biólogos y genetistas",
                    "B) Traductores e intérpretes",
                    "C) Arqueólogos e historiadores",
                    "D) Profesores y estudiantes"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Según el texto, ¿qué sucede si dos personas definen de forma distinta lo que constituye «una lengua»?",
                "ans": [
                    "A) Terminarán hablando un nuevo dialecto.",
                    "B) Los resultados al intentar contar o hacer un recuento de cuántas lenguas existen serán diferentes.",
                    "C) La RAE intervendrá.",
                    "D) Se creará una raza humana distinta."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿De qué manera el concepto de «continuo de diferenciación» desafía los purismos lingüísticos?",
                "ans": [
                    "A) Fomenta fronteras estrictas.",
                    "B) Al evidenciar que las fronteras entre dialectos y lenguas son difusas, desmiente la idea de lenguas puras o aisladas.",
                    "C) Exige un idioma internacional.",
                    "D) Demuestra que el lenguaje animal es igual."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Los colores en la física",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Qué demostró el físico Isaac Newton mediante el uso de un prisma triangular en 1676?",
                "ans": [
                    "A) Que el espectro solar está compuesto únicamente de púrpura.",
                    "B) Que la luz solar blanca puede descomponerse en los colores del espectro.",
                    "C) Que la música y la luz viajan a la misma velocidad.",
                    "D) Que los colores nacen de la fluorescencia del sol."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Según el experimento, ¿qué ocurre cuando se separa un color del prisma (por ejemplo, el amarillo) y se mezclan todos los demás colores restantes?",
                "ans": [
                    "A) Se obtiene la luz blanca originaria.",
                    "B) Desaparece la luz por completo debido a la refracción.",
                    "C) Da como resultado el color violeta, que es precisamente su color complementario.",
                    "D) Se crea el color verde."
                ],
                "corr": "C"
            },
            {
                "level": "Crítico",
                "q": "¿Qué limitación sensorial humana subraya el texto al comparar nuestra percepción visual con la percepción auditiva del músico?",
                "ans": [
                    "A) Que la física es más exacta que la música en términos de ondas.",
                    "B) Que el ojo humano es incapaz de identificar los colores individuales mezclados dentro del color blanco, a diferencia del oído entrenado capaz de aislar las notas de un acorde.",
                    "C) Que los músicos no entienden los principios físicos de Newton.",
                    "D) Que la luz blanca suena como un silencio absoluto."
                ],
                "corr": "B"
            },
            {
                "level": "Literal",
                "q": "¿Cuál es el único color fundamental que NO está contenido en el espectro solar descompuesto por el prisma?",
                "ans": [
                    "A) El verde",
                    "B) El amarillo",
                    "C) El púrpura",
                    "D) El azul"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "Si se divide la franja espectral en dos partes y se unen con lentes, ¿qué sucede al mezclar los dos colores mixtos resultantes?",
                "ans": [
                    "A) Producen un tono gris opaco",
                    "B) Generan nuevamente luz blanca",
                    "C) Provocan calor",
                    "D) Crean oscuridad"
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué relevancia tiene la refracción explicada por Newton para disciplinas artísticas como la pintura?",
                "ans": [
                    "A) Ninguna, pues la física y el arte nunca se relacionan.",
                    "B) Proporciona una base científica empírica sobre los colores complementarios y la formación del blanco.",
                    "C) Obliga a usar solo luz blanca.",
                    "D) Demuestra que la pintura es inferior."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "Distribución de las tierras y de las aguas",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "Según los datos del texto, ¿qué porcentaje de la superficie de la Tierra ocupan las aguas de mares y océanos?",
                "ans": [
                    "A) 29,25%",
                    "B) 50%",
                    "C) 70,75%",
                    "D) 100%"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué se menciona que el Océano Glacial Ártico presenta serias dificultades para la navegación comercial o general?",
                "ans": [
                    "A) Porque sus aguas se mezclan con las de la Antártida.",
                    "B) Porque su profundidad media excede los 3.500 metros, provocando naufragios.",
                    "C) Debido a que está situado en el Polo Norte y sus aguas permanecen cubiertas de hielo durante gran parte del año.",
                    "D) Porque no está comunicado con el Océano Pacífico."
                ],
                "corr": "C"
            },
            {
                "level": "Crítico",
                "q": "¿Cuál es el propósito central al presentar las cifras y límites de manera tan exacta en el texto?",
                "ans": [
                    "A) Convencer a los turistas de viajar al Glacial Antártico.",
                    "B) Demostrar que América del Norte es más grande que Europa.",
                    "C) Proporcionar un panorama geográfico preciso, objetivo e informativo sobre la morfología física del planeta y sus cuerpos de agua.",
                    "D) Advertir sobre el futuro descongelamiento de los polos y el fin del mundo."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "¿Con qué océanos se comunica el Océano Glacial Ártico?",
                "ans": [
                    "A) Únicamente con el Índico.",
                    "B) Con el Pacífico (estrecho de Behring) y el Atlántico (estrechos de Davis y Smith).",
                    "C) Con el Océano Antártico de manera directa.",
                    "D) Con el Mar Mediterráneo."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Si el Océano Glacial Antártico «no tiene límites precisos» y es la continuación de otros océanos, ¿qué se infiere sobre la geografía acuática?",
                "ans": [
                    "A) Que el agua de la Tierra es un sistema continuo e interconectado sin barreras físicas reales.",
                    "B) Que el Polo Sur no tiene agua.",
                    "C) Que es imposible medir el porcentaje de agua.",
                    "D) Que el agua dulce y salada no se mezclan."
                ],
                "corr": "A"
            },
            {
                "level": "Crítico",
                "q": "¿De qué manera la predominancia del agua (70,75%) debería influir en nuestra concepción del planeta «Tierra»?",
                "ans": [
                    "A) Invita a reflexionar que somos predominantemente un mundo oceánico, dependiente del equilibrio marino.",
                    "B) Sugiere que debemos secar los océanos.",
                    "C) Demuestra que el agua es infinita.",
                    "D) Prueba que los continentes son irrelevantes."
                ],
                "corr": "A"
            }
        ]
    },
    {
        "title": "¿Qué es la creatividad?",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿A qué figura se cita en el texto como un gran ejemplo de generar gracia o creatividad sin necesidad de usar palabras habladas?",
                "ans": [
                    "A) Galileo Galilei.",
                    "B) Isaac Newton.",
                    "C) Charles Chaplin.",
                    "D) La Real Academia Española."
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "Según lo descrito, ¿por qué se afirma que la creatividad no es un rasgo exclusivo del arte o de los artistas?",
                "ans": [
                    "A) Porque los científicos también saben pintar cuadros hermosos.",
                    "B) Porque se manifiesta como la capacidad de producir ideas nuevas para resolver problemas cotidianos, proponer teorías complejas o ingeniar dispositivos útiles.",
                    "C) Porque cualquiera puede buscar definiciones en el diccionario.",
                    "D) Porque todos los humanos nacen tocando un instrumento."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "Tomando en cuenta las características ligadas a la creatividad (autonomía y dedicación profunda), ¿qué se requiere esencialmente para romper un paradigma preestablecido?",
                "ans": [
                    "A) Ser conformista y aceptar todo lo que dicta el dominio científico.",
                    "B) Invertir la misma cantidad de horas en muchas disciplinas simultáneamente sin enfocarse.",
                    "C) Ejercer independencia de pensamiento para desafiar lo convencional, respaldada por la práctica rigurosa en una disciplina.",
                    "D) Hablar el mismo idioma que Charles Chaplin."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "Según la Real Academia de la Lengua citada en el texto, ¿qué es la creatividad?",
                "ans": [
                    "A) El talento de los pintores",
                    "B) La facultad de crear o la capacidad de creación",
                    "C) Un don divino",
                    "D) Resolver matemáticas"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Si una persona practica música y posee un alto grado de autonomía intelectual, ¿qué probabilidad tiene según el texto?",
                "ans": [
                    "A) De fracasar socialmente",
                    "B) De volverse conformista",
                    "C) De desarrollar un alto nivel de pensamiento creativo e innovación en su área",
                    "D) De perder la creatividad"
                ],
                "corr": "C"
            },
            {
                "level": "Crítico",
                "q": "¿Por qué la autonomía y el no conformismo son esenciales para los avances científicos como los de Galileo?",
                "ans": [
                    "A) Porque la obediencia estricta a dogmas vigentes frena la formulación de teorías innovadoras que cuestionan lo establecido.",
                    "B) Porque los científicos deben ser rebeldes sin causa.",
                    "C) Porque la creatividad científica requiere anarquía.",
                    "D) Porque la física depende de la suerte."
                ],
                "corr": "A"
            }
        ]
    },
    {
        "title": "La toga no hace al juez",
        "typology": "descriptivo",
        "questions": [
            {
                "level": "Literal",
                "q": "En el Índice del Estado de Derecho 2019 de World Justice Project, ¿cuántos puntos obtuvo Ecuador sobre 100?",
                "ans": [
                    "A) 87",
                    "B) 71",
                    "C) 68",
                    "D) 48"
                ],
                "corr": "D"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué significa el refrán adaptado \"la toga no hace al juez\" dentro del contexto del artículo?",
                "ans": [
                    "A) Que los jueces carecen de gusto para vestir adecuadamente en sus juicios.",
                    "B) Que la simple imposición de un atuendo simbólico (como la toga negra) no restaurará por sí sola la probidad ni el estado de derecho frente a la ciudadanía.",
                    "C) Que la vestimenta negra absorbe el calor en un país tropical como Ecuador.",
                    "D) Que es preferible que los jueces utilicen un uniforme blanco como los doctores."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué acciones concretas y sistémicas postula la autora como verdaderos pilares para devolver el prestigio al sistema de justicia nacional?",
                "ans": [
                    "A) Adquirir togas inglesas de mejor calidad para todos los juzgados.",
                    "B) Subir a Ecuador del puesto 87 al 70 en los índices comprando jurados.",
                    "C) Eliminar la corrupción, evitar retrasos injustificados y garantizar una aplicación de la ley ajena a influencias y favores políticos.",
                    "D) Expulsar inmediatamente a todos los jueces nombrados en la década pasada."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "¿Qué autoridad decretó que es obligatorio que los magistrados utilicen toga negra?",
                "ans": [
                    "A) El World Justice Project",
                    "B) El Consejo de la Judicatura",
                    "C) El Ministerio de Salud",
                    "D) La presidencia"
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué la autora compara la toga de los jueces con el uniforme blanco de los médicos?",
                "ans": [
                    "A) Porque ambos son de algodón.",
                    "B) Porque ambos representan un símbolo externo de autoridad y probidad inherente a su profesión.",
                    "C) Porque los médicos dictan sentencias.",
                    "D) Porque ambos gremios tienen el mismo salario."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué argumento sostiene la autora contra la medida tomada por el Consejo de la Judicatura?",
                "ans": [
                    "A) Que las reformas estéticas son insuficientes y encubren los verdaderos problemas estructurales (corrupción, impunidad) que minan la confianza.",
                    "B) Que el color negro es triste.",
                    "C) Que la toga debió ser inventada en América.",
                    "D) Que es muy caro."
                ],
                "corr": "A"
            }
        ]
    },
    {
        "title": "Otavalo, una joya para visitar",
        "typology": "descriptivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿A qué distancia aproximada de la ciudad de Otavalo se encuentran las tres lagunas mencionadas en el texto?",
                "ans": [
                    "A) A 1,5 km.",
                    "B) A 3,3 km.",
                    "C) A 40 minutos.",
                    "D) A 10 grados centígrados de distancia."
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Por qué el centro de rescate de aves rapaces desempeña un papel más allá de ser un simple mirador?",
                "ans": [
                    "A) Porque está ubicado cerca del monte Imbabura.",
                    "B) Porque asume un rol pedagógico vital mediante charlas para concienciar sobre la conservación de especies endémicas amenazadas.",
                    "C) Porque permite cazar cóndores y gavilanes libremente.",
                    "D) Porque el cóndor fue usado para la conquista española."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿De qué manera la descripción física de elementos como la cascada de Peguche fortalece el atractivo cultural del texto?",
                "ans": [
                    "A) Al ilustrar que no es solo agua que cae, sino un verdadero epicentro espiritual y ceremonial profundamente ligado a la cosmovisión andina y purificación.",
                    "B) Al advertir que las dimensiones (30 metros) la hacen peligrosa para el baño.",
                    "C) Al promover la venta de botellas de agua natural cerca de Faccha Llacta.",
                    "D) Al mostrar que las lagunas son exclusivamente para aclimatación de andinistas extranjeros."
                ],
                "corr": "A"
            },
            {
                "level": "Literal",
                "q": "¿Cuál es el nombre de la cascada que sirve de centro ceremonial de purificación en las faldas del Imbabura?",
                "ans": [
                    "A) Cascada de Cuicocha",
                    "B) Cascada de San Pablo",
                    "C) Cascada de Peguche",
                    "D) Cascada de Faccha Llacta"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué función utilitaria tiene la zona de las tres lagunas para los montañistas?",
                "ans": [
                    "A) Les sirve como balneario termal.",
                    "B) Se considera el sitio ideal para la aclimatación física antes de iniciar un ascenso a montañas como el Fuya Fuya.",
                    "C) Funciona como mercado de equipo.",
                    "D) Es lugar de caza."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Por qué es fundamental rescatar y divulgar el simbolismo ancestral del cóndor en estos centros turísticos?",
                "ans": [
                    "A) Porque permite cobrar más dinero.",
                    "B) Porque revaloriza la identidad indígena, integrando la conservación ambiental con el respeto por la cosmovisión histórica.",
                    "C) Porque el cóndor ataca si no se le respeta.",
                    "D) Porque es el único pájaro de la zona."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "El barrio de Valencia que puede convertirse en un ejemplo mundial",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Cuál es el nombre de la distinción otorgada por ONU-Hábitat al proyecto ubicado en el barrio de Orba?",
                "ans": [
                    "A) Premio Nacional de Urbanismo.",
                    "B) Premio Internacional de Rehabilitación Urbana en Edificaciones Masivas.",
                    "C) Galardón Europeo de Cohousing y Vivienda.",
                    "D) Reconocimiento al Desarrollismo de los Años Sesenta."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "Según los diseñadores, ¿qué beneficio mutuo (para el habitante y la comunidad) tiene reducir el tamaño de algunos de los pisos privados de 90 metros?",
                "ans": [
                    "A) El constructor Alfredo Corral puede vender esos metros adicionales al extranjero.",
                    "B) Garantiza que todas las fachadas luzcan idénticas a las de Sevilla.",
                    "C) El propietario rebaja sus gastos de mantenimiento y se liberan espacios para destinarlos a zonas comunitarias útiles (como lavanderías o salas de estudio).",
                    "D) Convierte los edificios homogéneos en rascacielos."
                ],
                "corr": "C"
            },
            {
                "level": "Crítico",
                "q": "¿Por qué la \"revitalización de un barrio obsoleto\" presentada es catalogada como revolucionaria a escala global?",
                "ans": [
                    "A) Porque demuestra que las soluciones de vivienda no siempre implican destruir y construir de cero, sino adaptar, compartir y optimizar infraestructuras preexistentes con lógica colaborativa.",
                    "B) Porque es el primer barrio de Valencia en tener techos y terrazas.",
                    "C) Porque prueba que los proyectos arquitectónicos de los años sesenta eran superiores a los actuales.",
                    "D) Porque obliga a los vecinos a abandonar la propiedad privada por completo."
                ],
                "corr": "A"
            },
            {
                "level": "Literal",
                "q": "¿Qué características arquitectónicas comparten el barrio de Orba y el Parque Alcosa en Sevilla?",
                "ans": [
                    "A) Fueron construidos por el mismo promotor, con los mismos planos y el mismo nombre originario.",
                    "B) Ambos poseen rascacielos ecológicos.",
                    "C) Se sitúan frente al mar.",
                    "D) Cuentan con túneles subterráneos."
                ],
                "corr": "A"
            },
            {
                "level": "Inferencial",
                "q": "¿A qué se refiere el término «vivienda colaborativa» en el contexto de la propuesta?",
                "ans": [
                    "A) A que duermen todos en un salón.",
                    "B) A un modelo que combina privacidad con socialización y gestión conjunta de espacios infrautilizados.",
                    "C) A la demolición de los edificios.",
                    "D) A compartir salario."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿De qué manera este proyecto representa una crítica al «desarrollismo de los sesenta»?",
                "ans": [
                    "A) Fomenta la construcción masiva.",
                    "B) Contrarresta la visión de los bloques de viviendas como meros dormitorios homogéneos, devolviéndoles la dimensión humana y comunitaria.",
                    "C) Afirma que fue la mejor época.",
                    "D) Destruye el patrimonio histórico."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "¿Cada cuánto debes cambiar cepillos, esponjas y otros objetos?",
        "typology": "descriptivo",
        "questions": [
            {
                "level": "Literal",
                "q": "Según la lectura, ¿cada cuánto tiempo aconsejan los odontólogos reemplazar el cepillo de dientes?",
                "ans": [
                    "A) Semanalmente.",
                    "B) Cada tres meses.",
                    "C) Cada año exacto.",
                    "D) Cada siete años."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "A partir del texto, ¿por qué lavar la esponja de la cocina con vinagre o meterla al microondas resulta ser insuficiente?",
                "ans": [
                    "A) Porque el vinagre destruye químicamente el material plástico de la esponja.",
                    "B) Porque elimina la proliferación de bacterias apenas de forma temporal, sin suprimir la necesidad ineludible de cambiar la herramienta periódicamente.",
                    "C) Porque las esponjas estallan al recibir ondas de calor directo.",
                    "D) Porque los restos de comida nunca pueden desprenderse con métodos caseros."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué paradigma doméstico busca desafiar o actualizar principalmente este texto?",
                "ans": [
                    "A) La idea errónea de que barrer, fregar y que las cosas \"luzcan\" limpias por fuera es sinónimo de verdadera higiene bacteriológica.",
                    "B) El mito de que los desinfectantes cuestan demasiado dinero y son inservibles.",
                    "C) La creencia de que los ácaros mejoran la firmeza de los colchones con el paso de las décadas.",
                    "D) La costumbre de comprar colchones nuevos cada mes, la cual resulta excesivamente costosa para la familia."
                ],
                "corr": "A"
            },
            {
                "level": "Literal",
                "q": "¿Con qué frecuencia específica recomiendan reemplazar las esponjas para lavar la loza?",
                "ans": [
                    "A) Cada mes",
                    "B) Cada tres días",
                    "C) Cada semana",
                    "D) Cada vez que cambien de color"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "Según el texto, ¿qué consecuencias colaterales tiene postergar el cambio de un colchón por más de siete años?",
                "ans": [
                    "A) Mejora la postura corporal.",
                    "B) Al acumular polvo y perder firmeza, afecta la calidad del descanso y puede comprometer la salud física.",
                    "C) Aumenta su valor de colección.",
                    "D) Obliga a cambiar de cama."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Cómo refleja el texto la relación entre el hiperconsumismo y la necesidad de salud preventiva?",
                "ans": [
                    "A) Promueve comprar compulsivamente.",
                    "B) Establece que el reemplazo no obedece a modas estéticas, sino a criterios biológicos vitales para prevenir focos de contaminación.",
                    "C) Sugiere limpiar todo con químicos.",
                    "D) Defiende que todo sea desechable."
                ],
                "corr": "B"
            }
        ]
    },
    {
        "title": "El plátano verde traspasó fronteras llegando de la Costa a la Sierra",
        "typology": "expositivo",
        "questions": [
            {
                "level": "Literal",
                "q": "¿Cuáles de las siguientes variedades de plátano verde son señaladas como las de mayor consumo?",
                "ans": [
                    "A) Maduro, guineo y orito.",
                    "B) Barraganete, maqueño y dominico.",
                    "C) Chifle, patacón y tigrillo.",
                    "D) Cazuela, bolón y empanada."
                ],
                "corr": "B"
            },
            {
                "level": "Inferencial",
                "q": "¿Qué indica la proliferación de platos como bolones, empanadas y tigrillos en la Sierra Central acerca de la cultura ecuatoriana?",
                "ans": [
                    "A) Indica una división geográfica insalvable, donde cada región come exclusivamente lo suyo.",
                    "B) Demuestra un proceso dinámico de integración e intercambio gastronómico, donde los insumos trascienden su clima originario.",
                    "C) Sugiere que los habitantes de la Sierra son incapaces de cultivar sus propios alimentos.",
                    "D) Refleja la desaparición de la comida tradicional andina por culpa de productos invasores."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "Sumado a su exquisita adaptabilidad cultural, ¿por qué el consumo del plátano verde resulta altamente recomendable desde la perspectiva nutricional?",
                "ans": [
                    "A) Porque es un carbohidrato hueco ideal para subir de peso muy rápido y económicamente.",
                    "B) Porque cura enfermedades contagiosas por sus vitaminas de origen costeño.",
                    "C) Porque actúa como un aliado metabólico al aportar fibras y un almidón específico que regula los picos de glucosa y los niveles de colesterol nocivo.",
                    "D) Porque su sabor sustituye la necesidad de ingerir grasas animales diarias."
                ],
                "corr": "C"
            },
            {
                "level": "Literal",
                "q": "¿Qué platos de la Costa que se degustan en la Sierra utilizan masa de plátano rellenas con queso, pollo o carne?",
                "ans": [
                    "A) Los ceviches",
                    "B) Los secos de gallina",
                    "C) Las empanadas de verde",
                    "D) Los encocados"
                ],
                "corr": "C"
            },
            {
                "level": "Inferencial",
                "q": "¿De qué forma contribuye el almidón del plátano verde a la salud del consumidor?",
                "ans": [
                    "A) Cura la diabetes tipo 1.",
                    "B) Facilita el control de la glucemia, el peso corporal y la disminución de niveles de colesterol.",
                    "C) Incrementa la retención de líquidos.",
                    "D) Bloquea vitaminas."
                ],
                "corr": "B"
            },
            {
                "level": "Crítico",
                "q": "¿Qué impacto sociológico puede tener el hecho de que un producto endémico de una región se convierta en símbolo gastronómico nacional?",
                "ans": [
                    "A) Fomenta la rivalidad regional.",
                    "B) Actúa como puente de cohesión e identidad nacional, difuminando barreras culturales a través de la comida compartida.",
                    "C) Provoca quiebras agrícolas.",
                    "D) Elimina costumbres culinarias autóctonas."
                ],
                "corr": "B"
            }
        ]
    }
]

def main():
    reader = PyPDF2.PdfReader(pdf_path)
    output_readings = []
    
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        
        # Omitimos líneas de encabezado como "NARRATIVO", "ARGUMENTATIVO", etc. si aparecen solas al inicio.
        lines = text.split('\n')
        clean_lines = []
        for line in lines:
            trimmed = line.strip().upper()
            if trimmed in ["NARRATIVO", "EXPOSITIVO", "DESCRIPTIVO", "ARGUMENTATIVO", ""]:
                continue
            clean_lines.append(line.strip())
        
        content_text = " ".join(clean_lines)
        
        # En el formato de import_json_readings, text es un array de párrafos
        text_array = [content_text]
        
        meta = readings_meta[i]
        
        activities = []
        for q_idx, q_data in enumerate(meta['questions']):
            activities.append({
                "question_id": q_idx + 1,
                "comprehension_level": q_data["level"],
                "question": q_data["q"],
                "correct_answer": q_data["corr"],
                "justification": "",
                "answers": q_data["ans"]
            })
            
        reading_entry = {
            "title": meta["title"],
            "typology": meta["typology"].capitalize(),
            "type": None,
            "text": text_array,
            "activites": activities  # Nota: el script original busca "activites"
        }
        
        output_readings.append(reading_entry)
        
    final_json = {"readings": output_readings}
    
    out_path = r'c:\Users\Kevin\Desktop\Proyecto Godot Prácticas\PROYECTO\Docker\Nuevas lecturas\lecturas_17.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(final_json, f, ensure_ascii=False, indent=2)
        
    print(f"JSON generado exitosamente en {out_path}")

if __name__ == "__main__":
    main()
