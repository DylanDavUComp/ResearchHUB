---
name: ucompensar-look-and-feel
description: Aplica y verifica la identidad UCompensar 2026 en interfaces, documentos, presentaciones, imágenes y comunicaciones. Usar al crear o modificar cualquier experiencia visual o texto visible de ResarchHUB y otras piezas institucionales UCompensar.
---

# UCompensar Look & Feel

Construye experiencias que se sientan audaces, claras, contemporáneas, prácticas y humanas. La marca debe demostrar acción y conexión con el mundo real, no limitarse a decorar con colores institucionales.

## Fuentes de verdad

Antes de diseñar, consulta [la guía consolidada](../../brand/UCOMPENSAR_BRAND_MD.md). Lee solo las secciones pertinentes al formato. Cuando haga falta comprobar una regla o tomar un activo, usa esta prioridad:

1. `../../brand/V3_BRANDBOOK_UCOMPENSAR 2026.pdf`
2. `../../brand/PPT UCOMPENSAR REARQUITECTURA DE MARCA 12052026 1.pptx`
3. `../../brand/Plantilla Institucional interna- actualizada.pptx`
4. `../../brand/Plantilla Modelo 2.pptx`
5. `../../brand/Fuentes UCompensar.zip`
6. `../../brand/6.  Logos - ADN UCompensar.7z`

El Brandbook 2026 prevalece ante contradicciones. No reutilices automáticamente el descriptor anterior, campañas históricas ni composiciones de plantillas previas.

Para trabajo de interfaz, lee además [la referencia de interfaz](references/interface-system.md).

## Flujo de trabajo

1. Identifica el formato, la audiencia (`Personas`, `Empresas`, `Interna` o `Mixta`) y el objetivo concreto.
2. Reduce la comunicación a una idea principal y elige un tono colaborativo, empoderador o de pertenencia.
3. Inspecciona los activos maestros relevantes. Nunca redibujes ni alteres el logo.
4. Define la jerarquía `titular -> información esencial -> acción`.
5. Aplica como máximo tres colores protagonistas y usa neutros para lectura y estructura.
6. Usa Agrandir Narrow para display y Source Sans 3 para lectura. En interfaces, conserva fallbacks del sistema para disponibilidad y rendimiento.
7. Usa círculos o arcos solo cuando organicen, conecten o enfoquen contenido.
8. Verifica el resultado en su tamaño final, incluyendo estados reales, datos largos y variantes responsive cuando correspondan.

## Invariantes de marca

- Usa `#6D20E5` como morado principal, `#3B0970` como morado oscuro y `#FF7000` como acento de acción.
- Reserva `#00E880` y `#F979F0` para significados claros; no conviertas la pieza en una paleta multicolor.
- Usa `#F4F4F4`, blanco y negro como neutros funcionales.
- Mantén alto contraste, espacio negativo suficiente y un foco inequívoco.
- Mantén el logo maestro con un área libre mínima de `1X`.
- Escribe frases breves, directas y cotidianas. Evita tono burocrático y promesas vacías.
- Prefiere personas reales haciendo, construyendo, analizando, colaborando o aprendiendo.
- Usa iconos simples, geométricos y funcionales; evita 3D, skeuomorfismo y mezcla de familias visuales.

## Interfaces y producto

- Mantén primero la utilidad del flujo: navegación predecible, densidad apropiada y acciones evidentes.
- Usa Source Sans 3 como fuente principal de lectura; usa Agrandir Narrow en títulos breves solo cuando el archivo web autorizado esté disponible.
- Centraliza color, tipografía, espaciado, radios, sombras y estados en tokens. No introduzcas valores casi iguales de forma aislada.
- El naranja identifica la acción primaria o un hito; el morado sostiene navegación y jerarquía; verde y rosado requieren semántica explícita.
- Conserva componentes existentes que ya cumplen el sistema y corrige desviaciones de manera incremental.
- Diseña estados de carga, vacío, error, éxito, foco, deshabilitado y permisos por rol.
- Cumple WCAG AA, interacción por teclado, nombres accesibles y reducción de movimiento.
- Verifica visualmente escritorio y móvil en un navegador real. Revisa consola, red, desbordes, superposiciones y texto truncado.
- Diseña para operacion real: usa paginacion, filtros, confirmaciones, recuperacion
  de errores y estados de permisos cuando el volumen o el riesgo lo requieran.
- Prueba nombres, correos, modalidades y mensajes en su longitud maxima; ninguna
  tabla, accion o cabecera debe depender de datos de demostracion cortos.
- No muestres credenciales de ejemplo, avisos de prototipo ni funciones simuladas en
  una compilacion operativa. Una integracion no disponible debe estar deshabilitada
  o identificada con un estado real, no fingir exito.
- Mantiene estables las dimensiones durante carga y actualizacion, y evita descargar
  activos visuales innecesarios en vistas operativas repetidas.

## Otros formatos

- Presentaciones: usa 16:9 por defecto, una composición principal por diapositiva y máximo dos familias tipográficas en condiciones normales.
- Word e informes: expresa la marca mediante jerarquía y claridad; usa tablas simples y gráficos con significado semántico.
- Social, OOH y pauta: prioriza un titular de 3 a 8 palabras, una imagen en acción, un CTA y el logo.
- Email: define un único objetivo, un CTA visible y bloques breves.

## Control de calidad

Antes de entregar, confirma:

- La pieza comunica práctica, claridad, conexión y acción.
- Hay una sola idea protagonista y no más de tres colores protagonistas.
- La tipografía respeta su rol y no está deformada ni usa negrita sintética.
- El logo proviene de un maestro aprobado, conserva proporción, contraste y protección.
- El contenido se entiende en la primera lectura y el CTA describe una acción concreta.
- El formato final es legible y los activos tienen resolución suficiente.
- En interfaces, no existen errores de consola, solicitudes fallidas, solapamientos ni controles sin nombre accesible.

Si una restricción técnica obliga a apartarse del sistema, conserva primero legibilidad y accesibilidad, usa el fallback autorizado más cercano y documenta la excepción.
