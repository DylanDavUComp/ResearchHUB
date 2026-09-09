# Sistema de interfaz UCompensar 2026

Usa esta referencia al diseñar o revisar aplicaciones web, portales, dashboards y herramientas internas.

## Tokens base

```css
:root {
  --brand-purple: #6d20e5;
  --brand-purple-dark: #3b0970;
  --brand-orange: #ff7000;
  --brand-green: #00e880;
  --brand-pink: #f979f0;
  --brand-gray: #f4f4f4;
  --brand-white: #ffffff;
  --brand-black: #000000;
  --font-display: "Agrandir Narrow", "Arial Narrow", sans-serif;
  --font-body: "Source Sans 3", "Segoe UI", Arial, sans-serif;
}
```

Adapta nombres de variables al sistema existente. Sustituye gradualmente valores heredados; evita una reescritura visual sin relación con la tarea.

## Jerarquía

- Titular de página: Agrandir Narrow, corto, fuerte y con espacio suficiente.
- Encabezados funcionales: Source Sans 3 Semibold o Agrandir Narrow cuando sean breves.
- Cuerpo, tablas, formularios y ayudas: Source Sans 3.
- Acción primaria: naranja, una por contexto inmediato.
- Acción secundaria: contorno o texto morado.
- Navegación: morado oscuro con contraste AA.

No escales texto según el ancho del viewport. Define tamaños estables y permite salto de línea.

## Composición de producto

- Una aplicación operativa puede ser más densa que una pieza de campaña. Mantén el carácter UCompensar mediante color, jerarquía, copy y acción, sin sacrificar escaneo o comparación.
- Usa secciones sin marco para estructura general. Reserva tarjetas para elementos repetidos, detalles y herramientas que necesitan delimitación.
- Evita tarjetas dentro de tarjetas, decoraciones gratuitas y exceso de badges.
- Usa radios moderados y consistentes. Los círculos se reservan para iconos, progreso, personas o conexiones con función.
- Emplea una cuadrícula y dimensiones estables para tablas, barras de progreso, pasos y controles.

## Estados semánticos

- Morado: estructura, selección y navegación.
- Naranja: acción primaria, atención o etapa actual.
- Verde: éxito o completado; comprueba contraste y acompaña el color con texto o icono.
- Rosado: innovación o creatividad cuando el dominio lo justifique, nunca como estado universal.
- Gris: fondo, descanso y estados neutrales.
- Error: usa un rojo accesible del sistema de producto; no fuerces un color de marca si reduce claridad.

No comuniques estado únicamente mediante color.

## Copy de interfaz

- Nombra acciones con verbo y objeto: `Crear solicitud`, `Publicar modalidad`, `Asignar docente`.
- Usa mensajes de error que indiquen qué ocurrió y cómo corregirlo.
- Evita lenguaje promocional en tareas operativas.
- Conserva los nombres institucionales y de rol aprobados.

## Verificación mínima

1. Prueba al menos un viewport de escritorio y uno móvil.
2. Recorre foco con teclado y confirma nombres accesibles.
3. Revisa contraste WCAG AA y estados de foco visibles.
4. Prueba texto largo, listas vacías, carga, error y permisos restringidos.
5. Comprueba consola y red sin errores inesperados.
6. Captura el resultado y compáralo con el producto existente y las fuentes maestras.
