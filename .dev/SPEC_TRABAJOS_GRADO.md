---
title: "Spec - Gestión integral de modalidades de trabajo de grado"
document_id: "SPEC-TG-001"
version: "0.3.0"
status: "Implementación incremental con estándar de producto"
language: "es-CO"
project: "ResearchHUB"
capability_map: ".dev/CAPABILITY_MAP_TRABAJOS_GRADO.md"
supersedes: "HOM-01_Etapas_Proceso_Estudiante.md v0.1.0"
---

# Spec: Gestión integral de modalidades de trabajo de grado

## 0. Uso y precedencia

Este documento ajusta el spec de etapas de homologación para cubrir el proceso
completo de trabajo de grado y todas las modalidades definidas en la política.

Orden de prevalencia:

1. Solicitudes explícitas aprobadas por el dueño del producto.
2. `POL-PIT-03 V02 Política modalidades de trabajo de grado`, emitida el
   12 de enero de 2022.
3. `SPEC_Driven_Architecture_Vibecoding.md` y ADR aprobadas del proyecto.
4. El spec anterior `HOM-01_Etapas_Proceso_Estudiante.md`, solo donde no entre en
   conflicto con este documento.

Convenciones:

| Estado | Significado |
|---|---|
| `BASE_POLITICA` | Regla extraída de POL-PIT-03 V02. |
| `APROBADO_USUARIO` | Requisito expresamente solicitado para este producto. |
| `PROPUESTO` | Diseño funcional o técnico pendiente de aprobación. |
| `PENDIENTE` | Ambigüedad que no debe resolverse inventando una regla. |

## 1. Supuestos explícitos

1. `PROPUESTO` El sistema será una aplicación web sobre el monolito modular
   FastAPI y PostgreSQL existentes.
2. `APROBADO_USUARIO` El flujo no se limitará a homologaciones ni a semilleros;
   administrará el ciclo completo de cualquier modalidad de trabajo de grado.
3. `APROBADO_USUARIO` Las modalidades, sus requisitos, rúbricas y flujos serán
   configurables y versionados.
4. `APROBADO_USUARIO` La experiencia y las acciones autorizadas serán diferentes
   para Estudiante, Docente, Director de programa, Administrador y
   Superadministrador.
5. `PROPUESTO` Los comités y áreas mencionados por la política serán responsables
   organizacionales dentro de un paso. La decisión será registrada por un usuario
   autorizado, sin crear inicialmente un rol de acceso por cada comité.
6. `PROPUESTO` Una configuración publicada será inmutable. Los cambios generarán
   una versión nueva y no alterarán casos en curso.
7. `PROPUESTO` “Eliminar” una modalidad publicada significará retirarla de nuevas
   convocatorias. Solo los borradores nunca usados podrán borrarse físicamente.
8. `PENDIENTE` La política entregada se toma como fuente vigente para este spec,
   pero se debe confirmar si existe una versión institucional posterior.

## 2. Objetivo

Construir una capacidad institucional para configurar, ejecutar, controlar y
auditar el proceso de trabajo de grado desde la selección de modalidad hasta el
registro final, respetando las diferencias entre modalidades y los permisos de
cada rol.

El sistema debe permitir:

- Publicar modalidades aplicables por nivel, sede, facultad y programa.
- Validar requisitos de elegibilidad antes de la postulación.
- Crear y tramitar casos individuales o grupales.
- Ejecutar flujos distintos por modalidad sin cambios de código.
- Gestionar documentos, planes, avales, comités, tutorías y correcciones.
- Evaluar con una rúbrica versionada y calcular la nota final.
- Tramitar homologación únicamente cuando la modalidad lo permita.
- Registrar cancelación, rechazo, aprobación, cierre y menciones.
- Conservar trazabilidad de actores, decisiones y versiones de configuración.
- Entregar información para Admisiones y Registro y reportes institucionales.

## 3. Alcance funcional

### 3.1 Incluye

- Catálogo y vigencia de modalidades.
- Constructor restringido de flujos: pasos, transiciones, responsables,
  requisitos, plazos y condiciones.
- Convocatorias u ofertas por periodo académico y programa.
- Casos de trabajo de grado con uno o varios estudiantes según la modalidad.
- Evaluación de elegibilidad, postulación, formalización y ejecución.
- Evidencias y documentos versionados.
- Asignación de docentes, tutores y evaluadores.
- Decisiones, devoluciones para corrección y rechazo motivado.
- Rúbricas, sustentaciones, calificaciones y resultado final.
- Homologación y registro cuando aplique.
- Cancelación según calendario y reglamento aplicable.
- Postulación de menciones meritoria y laureada.
- Auditoría y reportes.

### 3.2 Fuera del primer incremento

- Firma electrónica con validez jurídica, hasta definir proveedor y política.
- Integración automática con SACC, SNIES/HECCA, Admisiones y Registro.
- Almacenamiento definitivo de binarios hasta definir repositorio documental.
- Motor BPMN de propósito general. Se implementará un flujo configurable pero
  limitado al dominio de trabajo de grado.
- Interpretación automática de documentos o decisión mediante IA.

## 4. Catálogo normativo de modalidades

La plataforma debe crear inicialmente diez registros. Cada registro debe poder
activarse, retirarse o versionarse sin desplegar código.

| Código estable | Modalidad | Homologable | Inicio / duración | Integrantes | Estado inicial |
|---|---|---:|---|---|---|
| `PROYECTO_INVESTIGACION` | Proyecto de investigación | No | Último semestre / 16 semanas | 3 a 4 | Activa |
| `PROYECTO_EMPRENDIMIENTO` | Proyecto de emprendimiento | Sí | Séptimo semestre / mínimo 60 horas | 1 a 4 | Activa |
| `PROYECTO_CONSULTORIA` | Proyecto de consultoría | Sí | Séptimo semestre / mínimo 16 semanas | 1 a 4 | Activa |
| `PROYECTO_INTERVENCION_SOCIAL` | Proyecto de intervención social | Sí | Sexto semestre en adelante / mínimo 60 horas | 1 a 4 | Activa |
| `PROYECTO_SEMILLERO_INVESTIGACION` | Proyecto de semillero de investigación | Sí | Cuarto semestre / mínimo 60 horas | Individual | Activa |
| `PASANTIA_INVESTIGACION` | Pasantía de investigación | Sí | Octavo semestre / mínimo 16 semanas | Individual | Activa |
| `PROYECTO_APLICADO` | Proyecto aplicado | Sin definir | Sin definir | Sin definir | Inactiva |
| `CURSO_PROFUNDIZACION` | Curso de profundización | Sí | Ver conflicto TG-Q-002 / mínimo 80 horas | Individual | Activa con observación |
| `INMERSION_INTERNACIONAL` | Inmersión internacional | Sí | Octavo semestre / mínimo 1 semana | Individual | Activa |
| `PROGRAMA_COTERMINAL` | Programa co-terminal | Sí | 70% de créditos y condiciones adicionales / 1 semestre | Individual | Activa |

`PENDIENTE` Proyecto aplicado aparece en los casos y definiciones de la política,
pero no tiene procedimiento ni condiciones en la Tabla 1. Debe permanecer
inactivo hasta completar y aprobar su ficha normativa.

## 5. Reglas diferenciales por modalidad

### 5.1 Proyecto de investigación

- `BASE_POLITICA` El estudiante notifica la selección al programa por el medio
  definido por la facultad.
- `BASE_POLITICA` Requiere aceptación del comité de investigaciones de Facultad,
  preferiblemente antes de iniciar el semestre.
- `BASE_POLITICA` Exige matrícula del curso de trabajo de grado dentro del
  calendario institucional.
- `BASE_POLITICA` No es objeto de homologación.
- `BASE_POLITICA` Requiere trabajo escrito, sustentación, nota final superior a
  3,0, ausencia de procesos disciplinarios por fraude o plagio y cumplimiento del
  calendario.
- `BASE_POLITICA` Rúbrica: escrito 20%, sustentación 25%, tutor 20%, evaluador 1
  15%, evaluador 2 15%, autoevaluación 2,5% y coevaluación 2,5%.

### 5.2 Proyecto de emprendimiento

- `BASE_POLITICA` Se selecciona en Emprendimiento 3 o en la práctica de
  emprendimiento y se notifica por escrito al programa.
- `BASE_POLITICA` El proyecto debe estar en fase productiva y facturando.
- `BASE_POLITICA` Requiere postulación, proyecto en formato institucional, plan
  individual, aval del área de emprendimiento, aval del comité de Facultad,
  presentación y acta aprobatoria del comité general, y acuerdo pedagógico.
- `BASE_POLITICA` Los requisitos deben completarse antes de la matrícula del curso
  y exige pago de los créditos asociados.
- `BASE_POLITICA` Rúbrica: escrito 20%, sustentación 25%, tutor emprendedor 20%,
  dos evaluadores de 15% cada uno, autoevaluación 2,5% y coevaluación 2,5%.

### 5.3 Proyecto de consultoría

- `BASE_POLITICA` El estudiante integra un proyecto contratado por un tercero y
  generador de ingresos para UCompensar.
- `BASE_POLITICA` Requiere postulación, proyecto, plan individual, aval del área
  de educación continuada y consultoría, aval del comité de Facultad, presentación
  y acta del comité general, y acuerdo pedagógico.
- `BASE_POLITICA` Debe acreditar al menos 60 horas y concepto satisfactorio de la
  empresa cliente, aunque la tabla fija una duración mínima de 16 semanas.
- `BASE_POLITICA` Rúbrica: escrito 20%, sustentación 25%, tutor consultor 15%,
  evaluador 15%, empresa cliente 20%, autoevaluación 2,5% y coevaluación 2,5%.

### 5.4 Proyecto de intervención social

- `BASE_POLITICA` Requiere postulación, proyecto, plan individual, aprobación de
  la comunidad o entidad beneficiaria, comité de Facultad, comité general y
  acuerdo pedagógico.
- `BASE_POLITICA` Inicia desde sexto semestre y exige mínimo 60 horas.
- `BASE_POLITICA` Uno de los dos evaluadores representa a la comunidad beneficiaria
  o entidad contratante.
- `BASE_POLITICA` Rúbrica: escrito 20%, sustentación 25%, tutor 20%, dos
  evaluadores de 15% cada uno, autoevaluación 2,5% y coevaluación 2,5%.

### 5.5 Proyecto de semillero de investigación

- `BASE_POLITICA` Exige pertenencia formal a un semillero legalmente constituido,
  plan aprobado, propuesta de entregables, mínimo 60 horas y matrícula desde
  cuarto semestre.
- `BASE_POLITICA` Requiere postulación, proyecto, plan individual, comité de
  Facultad, presentación y acta del comité general, y acuerdo pedagógico.
- `BASE_POLITICA` Es individual.
- `BASE_POLITICA` La tabla extraída define escrito 20%, sustentación 17,5%, tutor
  de semillero 30%, evaluador 1 15%, evaluador 2 15% y autoevaluación 2,5%.
- `PENDIENTE` La ficha nombra un solo evaluador en el equipo, pero asigna dos
  calificaciones de evaluador. Debe aclararse antes de publicar la rúbrica.

### 5.6 Pasantía de investigación

- `BASE_POLITICA` La postulación se realiza por SACC.
- `BASE_POLITICA` Exige convenio con el grupo anfitrión cuando sea externo,
  proyecto, plan individual, aval del investigador principal, comité de Facultad,
  comité general y acuerdo pedagógico.
- `BASE_POLITICA` Es individual, inicia en octavo semestre, dura mínimo 16 semanas
  y no permite tener matriculado el curso de trabajo de grado.
- `BASE_POLITICA` Rúbrica: escrito 20%, sustentación 17,5%, tutor investigador
  30%, evaluador 15%, grupo anfitrión 15% y autoevaluación 2,5%.

### 5.7 Proyecto aplicado

- `BASE_POLITICA` Busca resolver problemas teórico-prácticos de un área de
  conocimiento por solicitud expresa de una entidad externa.
- `PENDIENTE` No se configurarán requisitos, flujo, homologación, duración,
  integrantes ni rúbrica hasta contar con acto o anexo institucional aprobado.

### 5.8 Curso de profundización

- `BASE_POLITICA` Es un curso fuera del plan de estudios, de mínimo 80 horas.
- `BASE_POLITICA` Exige inscripción y matrícula, asistencia superior al 80% y
  calificación superior a 3,5; el estudiante no puede tener matriculado trabajo de
  grado.
- `PENDIENTE` El texto exige séptimo semestre o superior y no estar en último
  semestre, mientras la Tabla 1 indica octavo semestre. La regla de elegibilidad
  debe quedar bloqueada hasta resolver esta contradicción.
- `PENDIENTE` La tabla extraída muestra escrito 30% y competencia 40%, sin completar
  una rúbrica de 100%. Se requiere la rúbrica oficial antes de publicarla.

### 5.9 Inmersión internacional

- `BASE_POLITICA` Requiere postulación en SACC, pago de movilidad, actividades
  preparatorias y acuerdo pedagógico.
- `BASE_POLITICA` Para homologar exige aprobar el proyecto integrador, entregar
  informe de movilidad tipo artículo y socializar la experiencia en evento interno.
- `BASE_POLITICA` Rúbrica: escrito 30%, sustentación 15% e informe cuantitativo y
  cualitativo del docente tutor 55%.

### 5.10 Programa co-terminal

- `BASE_POLITICA` Aplica a estudiantes de pregrado profesional que cursan el primer
  semestre completo de una especialización ofrecida por UCompensar.
- `BASE_POLITICA` Exige matrícula activa o reingreso aprobado, último semestre,
  seis créditos pendientes más la opción de grado, no haber cursado opción de
  grado y acuerdo pedagógico.
- `BASE_POLITICA` La Tabla 1 exige tener aprobado el 70% del plan de estudios; ambas
  condiciones deben parametrizarse de forma acumulativa hasta validación.
- `BASE_POLITICA` El estudiante paga el semestre de especialización, no matricula
  simultáneamente el curso de opción de grado y no realiza pago adicional por el
  registro de la homologación.
- `BASE_POLITICA` Debe aprobar todos los cursos. La nota final es el promedio
  ponderado del primer semestre; reprobar un curso implica reprobar la opción.

## 6. Configuración de modalidades

Cada versión de modalidad debe definir como mínimo:

| Grupo | Campos configurables |
|---|---|
| Identidad | Código estable, nombre, descripción, categoría y estado. |
| Aplicabilidad | Nivel, sede, facultad, programa, periodo, vigencia y cupos. |
| Elegibilidad | Semestre, porcentaje de créditos, matrícula, cursos previos, restricciones disciplinarias y expresiones AND/OR limitadas. |
| Ejecución | Duración, unidad, horas mínimas, participantes mínimos/máximos y modalidad individual/grupal. |
| Homologación | Indicador homologable, pagos, fecha límite y destino del registro. |
| Evidencias | Tipo documental, obligatoriedad, formato, tamaño, firmantes y momento del flujo. |
| Responsables | Rol o permiso requerido, asignación individual, comité o área responsable. |
| Evaluación | Rúbrica, pesos, escala, nota mínima, asistencia y reglas de aprobación. |
| Flujo | Versión publicada del flujo, pasos inicial/final y transiciones permitidas. |
| Gobierno | Fuente normativa, versión, creador, aprobador, fecha de publicación y motivo del cambio. |

### 6.1 Ciclo de vida de configuración

`BORRADOR -> EN_REVISION -> PUBLICADA -> RETIRADA`

- Un borrador se puede editar y borrar si nunca fue referenciado.
- La publicación exige al menos un paso inicial y uno final, conectividad completa,
  responsables válidos, requisitos definidos y rúbrica que sume 100% cuando
  corresponda.
- Una versión publicada no se edita ni se borra.
- Cambiar una modalidad publicada crea una nueva versión en borrador.
- Retirar impide crear casos nuevos, pero conserva y permite terminar los casos
  existentes.
- El código estable de modalidad no se reutiliza para otro significado.

## 7. Definición configurable del flujo

### 7.1 Plantilla común

Las modalidades pueden omitir, repetir o especializar pasos, pero deben poder
representar este ciclo completo:

1. Publicación de oferta o convocatoria.
2. Consulta y validación preliminar de elegibilidad.
3. Selección de modalidad y creación del caso.
4. Conformación del equipo, si aplica.
5. Carga de postulación, proyecto, plan y soportes.
6. Radicación por el estudiante.
7. Validación documental y académica.
8. Devolución para correcciones o rechazo motivado.
9. Avales de áreas, beneficiarios o grupos externos, cuando aplique.
10. Decisión de comité de Facultad.
11. Decisión de comité general, cuando aplique.
12. Firma o registro del acuerdo pedagógico.
13. Formalización de la modalidad.
14. Asignación de tutor, docente o evaluadores.
15. Ejecución y seguimiento de actividades u horas.
16. Entrega de producto escrito y evidencias finales.
17. Evaluación y sustentación, cuando aplique.
18. Correcciones posteriores a evaluación, si están permitidas.
19. Cálculo y aprobación de nota final.
20. Homologación o registro directo, según modalidad.
21. Evaluación de mención, cuando aplique.
22. Reporte institucional y cierre.

### 7.2 Tipos de paso permitidos

- `FORMULARIO`: captura de datos estructurados.
- `DOCUMENTO`: entrega de una o más evidencias.
- `VALIDACION`: revisión con resultado conforme/no conforme.
- `APROBACION`: decisión aprobar, devolver o rechazar.
- `ASIGNACION`: selección de tutor, docente, evaluador o responsable.
- `ACTIVIDAD`: ejecución y registro de avance u horas.
- `EVALUACION`: diligenciamiento de criterio o rúbrica.
- `CALCULO`: resultado determinístico, sin edición manual silenciosa.
- `INTEGRACION`: envío o recepción de un sistema institucional.
- `CIERRE`: finalización con resultado terminal.

Cada paso configura código, nombre, orden visual, tipo, responsable, permiso,
campos, documentos, plazo, obligatoriedad, condiciones de entrada y transiciones.

### 7.3 Estados de ejecución

Caso:

`BORRADOR`, `RADICADO`, `EN_VALIDACION`, `REQUIERE_AJUSTES`, `FORMALIZADO`,
`EN_EJECUCION`, `EN_EVALUACION`, `APROBADO`, `RECHAZADO`, `CANCELADO`,
`PENDIENTE_REGISTRO`, `CERRADO`.

Paso:

`PENDIENTE`, `DISPONIBLE`, `EN_CURSO`, `DEVUELTO`, `COMPLETADO`, `OMITIDO`,
`BLOQUEADO`, `CANCELADO`.

Reglas:

- La transición se valida contra la versión del flujo fijada al caso.
- Toda decisión guarda actor, fecha UTC, resultado, observación y evidencias.
- Rechazar, cancelar, devolver, omitir o forzar una transición exige motivo.
- Una transición repetida con la misma clave de idempotencia devuelve el resultado
  original y no duplica decisiones ni pasos.
- No se permite saltar pasos salvo transición publicada explícita.
- Los plazos vencidos generan alerta; no cambian el estado automáticamente salvo
  que la configuración publicada lo indique.

## 8. Experiencia y autorización por rol

Los roles son códigos canónicos independientes del texto visible:
`ESTUDIANTE`, `DOCENTE`, `DIRECTOR_PROGRAMA`, `ADMINISTRADOR` y
`SUPERADMINISTRADOR`.

La etiqueta actual `Coordinador de programa` debe migrarse o mapearse a
`DIRECTOR_PROGRAMA` solo tras confirmar equivalencia organizacional.

### 8.1 Matriz funcional predeterminada

| Capacidad | Estudiante | Docente | Director programa | Administrador | Superadministrador |
|---|:---:|:---:|:---:|:---:|:---:|
| Consultar modalidades publicadas | Sí | Sí | Sí | Sí | Sí |
| Crear y editar su borrador | Sí | No | Consulta | Soporte controlado | Sí |
| Radicar y responder correcciones | Sí | No | Consulta | Soporte controlado | Sí |
| Ver casos asignados | No | Sí | Sí, de su programa | Sí | Sí |
| Revisar evidencias asignadas | No | Sí | Sí | Solo con permiso | Sí |
| Registrar tutoría o evaluación | No | Sí | Si está asignado | No | Sí |
| Decidir elegibilidad o aval de programa | No | No | Sí | No | Sí |
| Asignar tutores y evaluadores | No | No | Sí | No | Sí |
| Registrar decisiones de comité | No | Solo si se delega | Sí | Solo con permiso | Sí |
| Enviar a registro y cerrar | No | No | Sí | Operación autorizada | Sí |
| Gestionar borradores de modalidad y flujo | No | No | Consulta | Sí | Sí |
| Publicar o retirar configuración | No | No | No | Proponer | Sí |
| Borrar borradores no usados | No | No | No | Sí | Sí |
| Administrar roles, permisos y alcance | No | No | No | Limitado | Sí |
| Consultar auditoría global | Solo su caso | Solo asignados | Su programa | Sí | Sí |

### 8.2 Permisos mínimos

- `degree_work:self:create`, `degree_work:self:read`,
  `degree_work:self:update`, `degree_work:self:submit`.
- `degree_work:assigned:read`, `degree_work:assigned:review`,
  `degree_work:assigned:evaluate`.
- `degree_work:program:read`, `degree_work:program:decide`,
  `degree_work:program:assign`, `degree_work:program:report`.
- `degree_work:any:read`, `degree_work:any:support`,
  `degree_work:any:transition`.
- `modalities:read`, `modalities:create`, `modalities:update`,
  `modalities:delete`, `modalities:publish`, `modalities:retire`.
- `workflows:read`, `workflows:create`, `workflows:update`,
  `workflows:delete`, `workflows:publish`.
- `audit:self:read`, `audit:program:read`, `audit:any:read`.

El backend debe validar permisos y alcance de datos. Ocultar un botón en el
frontend no constituye autorización.

## 9. Modelo de dominio

### 9.1 Agregados y entidades

| Entidad | Propósito |
|---|---|
| `degree_work_modalities` | Identidad estable de una modalidad. |
| `degree_work_modality_versions` | Configuración inmutable por vigencia. |
| `modality_requirements` | Prerrequisitos, documentos y reglas de elegibilidad. |
| `evaluation_rubrics` / `evaluation_criteria` | Criterios, pesos y escala versionados. |
| `workflow_definitions` / `workflow_versions` | Identidad y versión publicada del flujo. |
| `workflow_steps` / `workflow_transitions` | Grafo ejecutable y autorización de cada acción. |
| `degree_work_offerings` | Disponibilidad por periodo, sede, facultad y programa. |
| `degree_work_cases` | Instancia del proceso fijada a versiones de modalidad y flujo. |
| `case_participants` | Estudiantes y condición de participación. |
| `case_step_instances` | Estado y datos de cada paso ejecutado. |
| `case_assignments` | Tutor, docente, evaluador u otro responsable asignado. |
| `case_evidence` / `evidence_versions` | Metadatos y versiones de soportes. |
| `case_decisions` | Aval, devolución, rechazo o aprobación motivada. |
| `case_evaluations` | Puntajes por criterio, evaluador y rúbrica. |
| `grade_records` | Nota calculada, resultado y estado de registro. |
| `honor_mentions` | Postulación, soportes y decisión de mención. |
| `audit_events` | Historial inmutable de acciones relevantes. |
| `idempotency_records` | Protección contra repetición de comandos. |

### 9.2 Restricciones obligatorias

- Un caso referencia exactamente una versión publicada de modalidad y de flujo.
- Los límites de participantes se validan al radicar y al cambiar el equipo.
- Solo existe una instancia de paso por caso y código de paso, salvo que el paso
  esté configurado como repetible.
- Los pesos activos de una rúbrica deben sumar 100%, excepto requisitos no
  calificables marcados explícitamente.
- La nota almacenada se puede reproducir desde sus evaluaciones y fórmula.
- Ningún documento se sobrescribe; una corrección crea una versión.
- Los eventos de auditoría no se actualizan ni eliminan desde la aplicación.
- Las fechas operativas y de auditoría se almacenan en UTC.
- Los casos cerrados son de solo lectura, salvo reapertura excepcional auditada.

## 10. Contrato API propuesto

Se conserva `/api/v1`. Los cuerpos usan `snake_case`, consistente con el backend
Python actual. Todas las listas son paginadas y todos los errores conservan el
formato institucional con código, mensaje, detalle y `trace_id`.

### 10.1 Catálogo y flujos

| Método | Ruta | Permiso principal |
|---|---|---|
| GET | `/api/v1/degree-work-modalities` | Usuario autenticado; filtra publicadas según alcance. |
| POST | `/api/v1/degree-work-modalities` | `modalities:create` |
| GET | `/api/v1/degree-work-modalities/{modality_id}` | `modalities:read` |
| PATCH | `/api/v1/degree-work-modalities/{modality_id}` | `modalities:update`; solo identidad no publicada. |
| POST | `/api/v1/degree-work-modalities/{modality_id}/versions` | `modalities:update` |
| PATCH | `/api/v1/modality-versions/{version_id}` | `modalities:update`; solo borrador. |
| DELETE | `/api/v1/modality-versions/{version_id}` | `modalities:delete`; solo borrador sin referencias. |
| POST | `/api/v1/modality-versions/{version_id}/publication` | `modalities:publish` |
| POST | `/api/v1/modality-versions/{version_id}/retirement` | `modalities:retire` |
| POST | `/api/v1/workflows` | `workflows:create` |
| POST | `/api/v1/workflows/{workflow_id}/versions` | `workflows:update` |
| PATCH | `/api/v1/workflow-versions/{version_id}` | `workflows:update`; solo borrador. |
| POST | `/api/v1/workflow-versions/{version_id}/publication` | `workflows:publish` |

### 10.2 Casos y ejecución

| Método | Ruta | Uso |
|---|---|---|
| POST | `/api/v1/degree-work-cases` | Crear borrador desde una oferta publicada. |
| GET | `/api/v1/degree-work-cases` | Listar por filtros y alcance del usuario. |
| GET | `/api/v1/degree-work-cases/{case_id}` | Consultar detalle autorizado. |
| PATCH | `/api/v1/degree-work-cases/{case_id}` | Editar campos permitidos del borrador. |
| POST | `/api/v1/degree-work-cases/{case_id}/participants` | Incorporar participante según límites. |
| DELETE | `/api/v1/degree-work-cases/{case_id}/participants/{user_id}` | Retirar participante antes de radicar. |
| POST | `/api/v1/degree-work-cases/{case_id}/transitions` | Ejecutar una transición publicada. |
| GET | `/api/v1/degree-work-cases/{case_id}/steps` | Consultar avance y acciones disponibles. |
| POST | `/api/v1/degree-work-cases/{case_id}/evidence` | Crear evidencia y metadatos. |
| POST | `/api/v1/degree-work-cases/{case_id}/assignments` | Asignar responsable. |
| POST | `/api/v1/degree-work-cases/{case_id}/evaluations` | Registrar evaluación según rúbrica. |
| GET | `/api/v1/degree-work-cases/{case_id}/history` | Consultar trazabilidad autorizada. |

`POST /transitions`, publicación, retiro, asignación, evaluación y envío a
registro deben exigir `Idempotency-Key`. La clave se registra de forma atómica con
hash del cuerpo; reutilizarla con otro cuerpo responde `422`, y una operación aún
en curso responde `409`.

El endpoint legado `/api/v1/homologations` no se ampliará para modalidades no
homologables. Su migración o deprecación requiere ADR y compatibilidad temporal.

## 11. Interfaz por rol

- Estudiante: catálogo elegible, “Mi trabajo de grado”, equipo, etapa actual,
  pendientes, documentos, correcciones, evaluaciones publicadas e historial.
- Docente: bandeja de asignaciones, revisión por paso, observaciones, rúbrica,
  sustentaciones y seguimiento de horas o entregables.
- Director de programa: tablero del programa, elegibilidad, avales, asignaciones,
  decisiones, vencimientos, envío a registro y reportes.
- Administrador: catálogo en borrador, editor de requisitos y flujos, periodos,
  soporte de casos y auditoría operativa según permisos.
- Superadministrador: publicación y retiro, permisos, alcance institucional,
  reaperturas excepcionales, configuración global y auditoría completa.

La UI debe mostrar únicamente comandos autorizados y explicar el estado del caso,
pero el servidor siempre recalcula las acciones disponibles.

## 12. Procesos transversales de la política

### 12.1 Cancelación

La cancelación se rige por el reglamento estudiantil y calendario académico. La
plataforma debe parametrizar fecha límite, actor autorizado, motivo y resultado,
sin conceder plazos especiales por modalidad salvo norma aprobada.

### 12.2 Menciones

- `BASE_POLITICA` Meritorio: nota final mayor o igual a 4,6 y confirmación del
  Consejo de Facultad.
- `BASE_POLITICA` Laureado: nota final igual a 5,0 y confirmación del Consejo de
  Facultad.
- La postulación exige conceptos de evaluadores, concepto del responsable
  institucional indicado y evidencia del aporte innovador.
- La elegibilidad automática no concede la mención; crea una postulación pendiente.

### 12.3 Propiedad intelectual

El flujo debe permitir registrar autoría, créditos de dirección, acuerdos de
cesión y convenios con entidades externas. Los documentos de propiedad intelectual
serán requisitos configurables; el sistema no inferirá titularidad.

### 12.4 Reporte institucional

El Director de programa debe disponer de un reporte validable para la Dirección de
investigación y transferencia. La exportación debe conservar modalidad, programa,
participantes, resultado, nota, fechas y estado de registro. La integración con
SNIES/HECCA queda fuera del primer incremento, pero el modelo debe preservar esos
datos.

## 13. Requisitos no funcionales

- Seguridad: mínimo privilegio, autorización por permiso y alcance, y protección
  de documentos y datos personales.
- Auditoría: actor, fecha UTC, IP o contexto de origen, acción, entidad, cambios y
  motivo para toda operación crítica.
- Integridad: transición, decisión, evaluaciones y evento de auditoría se guardan
  en una sola transacción.
- Rendimiento: p95 menor de 500 ms para consultas simples paginadas en entorno de
  prueba; cargas de archivo se miden por separado.
- Accesibilidad: flujos operables con teclado, foco visible, etiquetas y estados no
  comunicados solo por color.
- Concurrencia: actualizaciones sobre casos y borradores usan versión optimista;
  una versión obsoleta responde `409`.
- Observabilidad: logs estructurados sin tokens ni contenido documental.
- Recuperación: configuraciones publicadas, casos y auditoría deben incluirse en
  respaldos verificables.

## 14. Stack y comandos

Stack existente: Python 3.12, FastAPI 0.116, SQLAlchemy 2.0, PostgreSQL 16,
Alembic, PyJWT, HTML/CSS/JavaScript y Docker Compose.

```powershell
# Levantar o reconstruir el entorno
docker compose up -d --build

# Aplicar migraciones dentro del contenedor
docker compose exec api alembic upgrade head

# Ejecutar pruebas
docker compose exec api pytest

# Calidad
docker compose exec api ruff check app tests alembic
docker compose exec api ruff format --check app tests alembic
docker compose exec api mypy app

# Ver logs
docker compose logs -f api
```

## 15. Estructura objetivo

```text
app/modules/trabajos_grado/
  api/             # Rutas y dependencias de autorización
  models/          # Modelos SQLAlchemy del dominio
  schemas/         # Contratos Pydantic de entrada y salida
  repository/      # Persistencia sin reglas de negocio
  services/        # Casos de uso y transacciones
  domain/          # Validación de flujo, elegibilidad y evaluación
tests/
  unit/            # Reglas puras y matrices por modalidad
  integration/     # API + PostgreSQL + permisos
  contract/        # Esquemas, errores, paginación e idempotencia
  e2e/             # Flujos críticos por rol y modalidad
.dev/              # Specs, mapas y planes aprobados
```

`homologaciones` se conserva mientras exista API o datos dependientes. La
separación, migración o adaptación hacia `trabajos_grado` debe documentarse en una
ADR antes de implementar.

## 16. Estilo de código

Las rutas delegan reglas al servicio; el servicio usa repositorios dentro de una
transacción; los repositorios no deciden transiciones.

```python
def transition_case(
    case_id: str,
    transition_code: str,
    actor: User,
    expected_version: int,
) -> DegreeWorkCase:
    case = repository.get_for_update(case_id)
    authorization.ensure_can_transition(actor, case, transition_code)
    workflow.apply(case, transition_code, expected_version=expected_version)
    audit.record_transition(case=case, actor=actor)
    return case
```

- Clases en `PascalCase`; funciones, campos y tablas en `snake_case`.
- Enums persistidos con códigos `UPPER_SNAKE_CASE` estables.
- No comparar etiquetas visibles para autorizar.
- No incluir reglas específicas de una modalidad en rutas o JavaScript; deben
  provenir de la versión publicada y validarse en backend.

## 17. Estrategia de pruebas

### 17.1 Unitarias

- Validación del grafo: inicio/final, pasos huérfanos, ciclos permitidos y rutas.
- Estado y transición válida/inválida.
- Elegibilidad con reglas AND/OR y datos faltantes.
- Validación de participantes, horas, asistencia y fechas.
- Cálculo reproducible de cada rúbrica completa.
- Inmutabilidad de versiones publicadas.
- Casos activos no cambian al publicar una versión nueva.

### 17.2 Integración

- Migración sobre PostgreSQL vacío y actualización desde la versión anterior.
- Matriz RBAC completa: permitido, prohibido y fuera de alcance de programa.
- Transición atómica con decisión, evaluación y auditoría.
- Concurrencia optimista e idempotencia.
- Paginación y filtros de bandejas.
- Eliminación física solo de borradores sin uso y retiro de versiones publicadas.

### 17.3 Contrato y extremo a extremo

- Contratos de entrada, salida y error documentados en OpenAPI.
- Un escenario feliz y uno inválido para cada modalidad activa.
- Proyecto aplicado no puede ofrecerse mientras esté inactivo.
- Recorridos por rol: estudiante radica, docente revisa/evalúa, director decide,
  administrador configura y superadministrador publica.
- Un caso homologable termina en registro por homologación; proyecto de
  investigación termina por registro directo.

## 18. Criterios de aceptación

| ID | Criterio verificable |
|---|---|
| TG-AC-001 | Un superadministrador puede crear, validar, publicar, retirar y versionar modalidades y flujos sin editar código. |
| TG-AC-002 | Un administrador puede gestionar borradores, pero no publicar ni retirar sin el permiso explícito correspondiente. |
| TG-AC-003 | Una versión publicada no se edita y un caso conserva esa versión hasta el cierre. |
| TG-AC-004 | El estudiante solo ve ofertas aplicables a su programa y puede radicar si cumple elegibilidad y documentos. |
| TG-AC-005 | El sistema impide equipos fuera de los límites configurados para la modalidad. |
| TG-AC-006 | Cada transición presenta únicamente acciones permitidas al rol, permiso, asignación y estado actuales. |
| TG-AC-007 | Docentes solo acceden a casos asignados; directores solo a programas dentro de su alcance. |
| TG-AC-008 | Toda devolución, rechazo, cancelación, omisión o reapertura exige motivo y queda auditada. |
| TG-AC-009 | Cada modalidad activa completa su flujo diferencial con sus requisitos, responsables y rúbrica publicada. |
| TG-AC-010 | Las nueve modalidades marcadas homologables pueden terminar en homologación; proyecto de investigación usa registro directo. |
| TG-AC-011 | Proyecto aplicado no se publica hasta completar su ficha normativa. |
| TG-AC-012 | La nota final se calcula desde la rúbrica versionada, suma 100% y no admite cambios sin trazabilidad. |
| TG-AC-013 | La plataforma identifica elegibilidad para mención meritoria o laureada sin concederla automáticamente. |
| TG-AC-014 | Una repetición con igual `Idempotency-Key` no duplica decisiones, evaluaciones ni envíos. |
| TG-AC-015 | Una nueva versión de modalidad o flujo no altera casos ya radicados. |
| TG-AC-016 | Todas las listas operativas están paginadas, filtradas por alcance y responden sin exponer datos de otros usuarios. |
| TG-AC-017 | El historial muestra actor, fecha, acción, resultado y motivo de todas las acciones críticas. |
| TG-AC-018 | El flujo puede configurarse con pasos, devoluciones y responsables distintos sin desplegar una versión nueva de la aplicación. |

## 19. Trazabilidad

| Fuente | Regla | Requisitos relacionados |
|---|---|---|
| POL-PIT-03, secciones 5.1 y 5.2 | Diez modalidades nominales y sus definiciones. | TG-AC-001, TG-AC-009, TG-AC-011 |
| POL-PIT-03, sección 6 | Selección, legalización y requisitos diferenciales. | TG-AC-004, TG-AC-006, TG-AC-009 |
| POL-PIT-03, Tabla 1 | Semestre, duración, participantes, evaluación y aprobación. | TG-AC-005, TG-AC-012 |
| POL-PIT-03, cancelación | Aplicación del reglamento y calendario institucional. | TG-AC-008 |
| POL-PIT-03, menciones | Umbrales, aval y soportes de distinción. | TG-AC-013 |
| POL-PIT-03, propiedad intelectual | Autoría, créditos, cesión y convenios. | Evidencias y pasos configurables |
| POL-PIT-03, reporte | Información a Dirección de investigación y órganos de control. | TG-AC-017 |
| Solicitud del usuario | CRUD de modalidades y flujos. | TG-AC-001, TG-AC-002, TG-AC-003, TG-AC-018 |
| Solicitud del usuario | Comportamiento diferencial por cinco roles. | TG-AC-004, TG-AC-006, TG-AC-007 |

## 20. Límites de trabajo

Siempre:

- Actualizar el spec antes de cambiar una regla funcional.
- Validar entrada en API y autorización en backend.
- Versionar configuraciones publicadas.
- Probar permisos y alcance con casos positivos y negativos.
- Registrar migraciones y mantener trazabilidad requisito-prueba.

Preguntar antes:

- Cambiar los roles canónicos o sus alcances.
- Activar Proyecto aplicado o Curso de profundización con datos incompletos.
- Alterar una rúbrica o condición extraída de la política.
- Integrar SACC, Admisiones y Registro, SNIES/HECCA o firma electrónica.
- Definir retención, eliminación o almacenamiento definitivo de documentos.
- Migrar o retirar endpoints existentes de `homologaciones`.

Nunca:

- Modificar casos en curso al editar una plantilla.
- Borrar configuraciones publicadas, casos, decisiones o auditoría.
- Autorizar por texto visible del rol o únicamente desde el frontend.
- Exponer documentos, tokens, contraseñas o datos personales en logs.
- Inventar el procedimiento faltante de Proyecto aplicado.
- Calcular una nota con una rúbrica incompleta o que no sume 100%.

## 21. Preguntas abiertas

| ID | Pregunta | Bloquea |
|---|---|---|
| TG-Q-001 | ¿POL-PIT-03 V02 continúa vigente o existe una versión posterior? | Publicación del catálogo inicial. |
| TG-Q-002 | ¿Curso de profundización inicia en séptimo u octavo semestre y puede tomarse en último semestre? | Regla de elegibilidad. |
| TG-Q-003 | ¿Cuál es la rúbrica completa de Curso de profundización? | Publicación de su versión. |
| TG-Q-004 | ¿Proyecto semillero usa uno o dos evaluadores? | Equipo y rúbrica. |
| TG-Q-005 | ¿Cuál es el procedimiento completo de Proyecto aplicado? | Activación de modalidad. |
| TG-Q-006 | ¿Coordinador de programa y Director de programa son el mismo rol institucional? | Migración de usuarios y permisos. |
| TG-Q-007 | ¿Qué usuario registra formalmente las decisiones de cada comité y área? | Asignación predeterminada de pasos. |
| TG-Q-008 | ¿Se permiten varios casos activos por estudiante en programas distintos? | Restricción de unicidad. |
| TG-Q-009 | ¿Cuántas rondas de corrección se permiten y qué decisiones son apelables? | Transiciones de devolución y rechazo. |
| TG-Q-010 | ¿Dónde se guardarán binarios y cuánto tiempo deben conservarse? | Evidencias documentales y privacidad. |
| TG-Q-011 | ¿Qué integración y acuse exige Admisiones y Registro? | Cierre y homologación. |
| TG-Q-012 | ¿Qué datos y formato vigentes exige SNIES/HECCA? | Reporte institucional. |
| TG-Q-013 | ¿Qué firmas requieren validez jurídica y cuáles son solo aceptación en plataforma? | Acuerdos y propiedad intelectual. |

## 22. Puertas de control

- `G-TG-0`: mapa de capacidades aprobado.
- `G-TG-1`: catálogo normativo y preguntas TG-Q-001 a TG-Q-007 resueltas.
- `G-TG-2`: matriz de roles, permisos y alcance aprobada.
- `G-TG-3`: modelos y contratos API aprobados.
- `G-TG-4`: plan y tareas por módulo aprobados.
- `G-TG-5`: implementación con pruebas de todas las modalidades activas.
- `G-TG-6`: validación institucional, seguridad, respaldo y salida controlada.

No debe iniciarse implementación funcional antes de aprobar `G-TG-0`. Las
modalidades con pregunta bloqueante no pueden publicarse hasta resolver su puerta
correspondiente.

## 23. Operacion como producto

## 23.1 Condiciones no funcionales de producto

La implementación de este spec se rige por `CONSTRAINTS.md` y
`.dev/PRODUCT_READINESS.md`. Estas condiciones aplican aunque una capacidad se
entregue de forma incremental:

- La API debe permanecer sin estado compartido en memoria y admitir múltiples
  réplicas detrás de un balanceador.
- Las colecciones operativas deben paginarse y filtrar el alcance en PostgreSQL.
- Las transiciones críticas deben ser atómicas, idempotentes, auditables y seguras
  ante concurrencia.
- Cada cambio de esquema debe incluir migración Alembic y evidencia sobre base vacía
  y revisión anterior soportada.
- La observabilidad debe correlacionar solicitud, actor, acción y resultado sin
  registrar tokens, contraseñas, documentos ni datos personales innecesarios.
- Disponibilidad, latencia, continuidad, seguridad y accesibilidad deben cumplir los
  umbrales medibles de `CONSTRAINTS.md` antes de una decisión `GO`.
- Archivos binarios no se almacenarán en el sistema de archivos de una réplica; su
  activación requiere almacenamiento de objetos, análisis antimalware y política de
  retención aprobada.
- Funciones incompletas, integraciones simuladas, usuarios demo y credenciales
  compartidas no forman parte de una versión operativa.

## 23.2 Definición de terminado

Una capacidad se considera terminada cuando sus criterios funcionales tienen
trazabilidad y pruebas, la matriz RBAC cubre permitido y denegado, las migraciones
son reproducibles, existen señales operativas y se entrega evidencia de los gates
aplicables. "Implementado" no significa "aprobado para producción" hasta completar
la lista obligatoria de `.dev/PRODUCT_READINESS.md`.

## 24. Historial

| Versión | Fecha | Cambio |
|---|---|---|
| 0.3.0 | 2026-09-08 | Eleva el spec a estándar de producto operable: escala horizontal, SLO, seguridad, continuidad, observabilidad y definición de terminado verificable. |
| 0.2.0 | 2026-09-07 | Amplía el spec de 11 etapas de semillero a la gestión integral y configurable de todas las modalidades, con flujos versionados y autorización diferencial por rol. |
