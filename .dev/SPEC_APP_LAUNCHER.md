---
document_id: "SPEC-PORTAL-001"
version: "1.4.13"
status: "Implementado"
language: "es-CO"
project: "ResearchHUB"
---

# Selector de aplicaciones de investigacion

## Objetivo

Ofrecer una entrada institucional unica y responsive para elegir entre:

- `ResearchHUB`: investigacion formativa, semilleros, modalidades de trabajo de
  grado y procesos academicos de investigacion.
- `ResearchOS`: investigacion aplicada, capacidades, resultados y transferencia.
- `CRIS`: informacion cientifica institucional de investigadores, grupos,
  proyectos, productos, capacidades e indicadores.
- `CRAI`: recursos bibliograficos, digitales y servicios de apoyo para el
  aprendizaje y la investigacion.
- `Servicios y marketplace`: catalogo institucional de servicios, capacidades y
  conexiones entre la universidad y sus aliados.

## Comportamiento

1. La portada es la primera vista, exista o no una sesion de ResearchHUB.
2. El control `Ingresar` de ResearchHUB abre el login o reutiliza una sesion
   valida.
3. `ResearchOS` y `CRIS` solo se habilitan cuando `RESEARCH_OS_URL` y `CRIS_URL`,
   respectivamente, contienen una URL absoluta.
4. `CRAI_URL` tiene como valor institucional predeterminado
   `https://crai.ucompensar.edu.co/` y puede reemplazarse o deshabilitarse por
   ambiente.
5. En produccion, todas las URL externas deben usar HTTPS o el servicio no arranca.
6. Los controles disponibles comunican `Ingresar`. Sin URL configurada, el
   control permanece deshabilitado y comunica `Próximamente`; no simula
   navegacion ni disponibilidad.
7. Cerrar sesion en ResearchHUB devuelve al selector de aplicaciones.
8. Un carrusel de oportunidades se alinea, en escritorio, con la parte superior e
   inferior de la cuadricula de aplicaciones y muestra tres flyers institucionales.
9. El carrusel permite navegacion anterior, siguiente y directa; rota cada 4
   segundos, se detiene con foco o puntero y respeta movimiento reducido.
10. Los flyers usan `RESEARCH_BLOG_URL`. Sin URL, comunican `Próximamente` y no
    ejecutan navegacion.
11. `Servicios y marketplace` ocupa un panel alto equivalente al carrusel de
    oportunidades y usa `SERVICES_MARKETPLACE_URL` para habilitar su acceso.
12. Sin URL de marketplace, el panel comunica `Próximamente` y no ejecuta
    navegacion.
13. En pantallas anchas con menos de 700 px de alto, el selector reduce su
    densidad sin recortar filas, textos o acciones.
14. Las imagenes de los espacios de trabajo, oportunidades y marketplace siguen
    la direccion fotografica UCompensar 2026: personas reales en accion, practica,
    colaboracion y un maximo de tres colores de marca dominantes por pieza.
15. ResearchHUB muestra estudiantes trabajando en un aula; ResearchOS muestra
    docentes investigadores en un laboratorio IoT; CRIS muestra un dashboard con
    informacion consolidada de la investigacion institucional.
16. La portada se presenta como un portal institucional corporativo: cabecera de
    marca en una superficie blanca, identificacion explicita del portal, jerarquia
    contenida, superficies planas y naranja reservado para la accion principal.
17. Los accesos se organizan como un directorio editorial continuo, agrupado en
    `Espacios de trabajo` y `Actualidad y conexiones`. Las divisiones se expresan
    mediante ritmo, alineacion y separadores, no mediante tarjetas independientes.
18. `Espacios de trabajo` presenta sus cuatro aplicaciones como una lista vertical
    continua. Cada fila alinea miniatura, informacion y accion en columnas estables;
    no usa una matriz de paneles ni contenedores visualmente independientes.
19. El directorio adopta una composicion editorial de alto contraste: los cuatro
    espacios comparten una superficie morada continua, numeracion secuencial y
    ventanas fotograficas de practica real. El naranja conduce la accion principal
    y la actualidad permanece en una columna blanca diferenciada.
20. La numeracion `01` a `04` ocupa una franja propia a la izquierda de cada
    fotografia. Nunca se superpone al contenido ni compite visualmente con la
    accion de ingreso o disponibilidad.
21. Las fotografias de los espacios son circulares y operan como controles de
    seleccion accesibles. Seleccionar la imagen o la accion marca toda la fila en
    naranja, mantiene texto morado de alto contraste y desmarca las demas filas.
22. Al pasar el puntero por cualquier parte de una fila, o al enfocar uno de sus
    controles con teclado, toda la superficie adopta temporalmente el mismo estado
    naranja. Al retirar el puntero o foco recupera el estado seleccionado vigente.
23. Mientras una fila distinta esta en hover o foco, la seleccion persistente se
    muestra temporalmente en morado. Solo una fila puede actuar como protagonista
    naranja durante la exploracion.
24. Cada espacio usa una fotografia semanticamente exclusiva y legible dentro del
    recorte circular: prototipado estudiantil para ResearchHUB, laboratorio IoT
    para ResearchOS, red consolidada de investigadores y resultados para CRIS, y
    biblioteca fisica-digital con acompanamiento experto para CRAI.
25. R2C2, asistente visual de investigacion, patrulla unicamente el corredor blanco
    disponible entre el titular y el texto de apoyo. Se oculta si no existe espacio
    seguro, respeta movimiento reducido y, al seleccionarlo, se detiene y presenta
    el primer saludo `Hola.` en una burbuja de dialogo.
26. Mientras no existe interaccion, R2C2 elige aleatoriamente entre patrullar,
    descansar, jugar, investigar, estudiar, prototipar, experimentar en laboratorio,
    programar, analizar datos, crear, innovar, emprender, colaborar, presentar
    resultados, jugar futbol, graduarse, entrar a la Matrix, construir robots e
    idear soluciones. Cada actividad se representa sin texto ni escenografia,
    mediante objetos contextuales grandes y reconocibles que acompanian al robot.
    En futbol aparece un balon animado; laboratorio usa instrumental, graduacion
    usa birrete y diploma, y las demas acciones emplean objetos equivalentes. Cada
    actividad dura entre 10 y 15 segundos. Seleccionar el asistente interrumpe su
    actividad, presenta una respuesta breve y reinicia una espera de 60 segundos;
    al cumplirse ese periodo sin nuevas interacciones, retoma su rutina autonoma.

## Criterios de aceptacion

- La portada identifica el logo institucional y las cinco aplicaciones en el primer
  recorrido de lectura.
- El layout no presenta desplazamiento horizontal a 320, 390, 768 o 1440 px.
- Los controles tienen foco visible, nombres accesibles y estado deshabilitado
  semantico.
- ResearchHUB mantiene su autenticacion, roles y navegacion existentes.
- El endpoint `/api/v1/meta` publica disponibilidad y URL sin exponer secretos.
- Las integraciones externas se configuran por ambiente, no editando JavaScript.
- El carrusel es operable con teclado, anuncia cambios manuales y excluye del foco
  los controles de diapositivas no visibles.
- La portada aplica los colores, tipografias y jerarquia del Brandbook UCompensar
  2026 sin sombras decorativas, gradientes ni alteraciones del logo maestro.
- Los espacios de trabajo y contenidos del ecosistema se leen como secciones
  continuas, sin contenedores flotantes ni apariencia de mosaico de tarjetas.
