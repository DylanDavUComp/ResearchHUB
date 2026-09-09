# Mapa de capacidades: Gestión de modalidades de trabajo de grado

Estado: `PROPUESTO_PARA_VALIDACION`

Este mapa descompone la iniciativa antes de implementar. Los identificadores son
estables y deben usarse en specs, tareas, pruebas y commits.

| ID de módulo | Responsabilidad | Depende de |
|---|---|---|
| `identidad-acceso` | Autenticación, usuarios, roles, permisos y alcance por programa. | - |
| `catalogo-modalidades` | Catálogo versionado de modalidades, requisitos, rúbricas y vigencias. | `identidad-acceso` |
| `definicion-flujos` | Diseñador y publicación de flujos versionados, pasos, transiciones y responsables. | `identidad-acceso` |
| `casos-trabajo-grado` | Solicitudes, participantes, elegibilidad, selección de modalidad y ejecución del caso. | `catalogo-modalidades`, `definicion-flujos` |
| `evidencias-documentales` | Metadatos, carga, versiones, validación y retención de evidencias. | `casos-trabajo-grado` |
| `revision-evaluacion` | Asignaciones, conceptos, correcciones, rúbricas, sustentación y nota final. | `casos-trabajo-grado`, `evidencias-documentales` |
| `homologacion-registro` | Legalización, homologación cuando aplique y entrega a Admisiones y Registro. | `revision-evaluacion` |
| `auditoria-reportes` | Historial inmutable, seguimiento, menciones y reportes institucionales. | `casos-trabajo-grado`, `revision-evaluacion`, `homologacion-registro` |

Orden de construcción:

1. `identidad-acceso`.
2. `catalogo-modalidades` y `definicion-flujos`, en paralelo.
3. `casos-trabajo-grado`.
4. `evidencias-documentales`.
5. `revision-evaluacion`.
6. `homologacion-registro`.
7. `auditoria-reportes`.

## Límites

- `catalogo-modalidades` describe qué exige una modalidad; no administra casos.
- `definicion-flujos` publica plantillas inmutables; no cambia directamente el
  estado de un caso.
- `casos-trabajo-grado` fija la versión de modalidad y flujo al crear el caso.
- `revision-evaluacion` calcula resultados desde una rúbrica versionada; no
  modifica el catálogo publicado.
- `homologacion-registro` solo se activa cuando la modalidad indica que es objeto
  de homologación.
- `auditoria-reportes` consume eventos de los otros módulos y no puede alterar su
  estado operativo.

## Puerta de control

Este mapa debe ser aprobado antes de convertir cada módulo en un plan de
implementación. La aprobación debe confirmar los límites, las dependencias y el
orden de construcción.
