---
document_id: "SPEC-ROS-001"
version: "0.1.0"
status: "Implementado (estructura); modulos pendientes de aprobacion"
language: "es-CO"
project: "ResearchHUB"
---

# ResearchOS: acceso compartido y espacio de trabajo

## Objetivo

Ofrecer ResearchOS, la aplicacion de investigacion aplicada, capacidades,
resultados y transferencia, dentro del mismo producto que ResearchHUB, con una
cuenta institucional unica y acceso concedido por aplicacion.

## Alcance de esta version

Incluye login, sesion compartida, control de acceso por aplicacion, inicio y
navegacion. No incluye modulos funcionales: `Proyectos aplicados`, `Capacidades`,
`Resultados de investigacion` y `Transferencia` se publican como `Próximamente`
hasta que su spec sea aprobado.

## Reglas de acceso

1. Una cuenta institucional sirve para todas las aplicaciones. El token prueba
   identidad; no concede acceso a ninguna aplicacion por si mismo.
2. El acceso se registra en `usuario_aplicaciones` (`research_hub`,
   `research_os`) con fecha y usuario que lo otorgo.
3. El backend exige el acceso en cada solicitud: los procesos de ResearchHUB
   (trabajos de grado, homologaciones) requieren `research_hub`; las rutas
   `/api/v1/research-os/*` requieren `research_os`. La respuesta sin acceso es
   `403 auth.application_forbidden`.
4. El login acepta `application`. Con credenciales validas pero sin acceso
   responde `403 users.application_forbidden`, no emite token e informa en
   `details.applications` las aplicaciones disponibles para la cuenta.
   Credenciales invalidas siguen respondiendo `401` sin revelar accesos.
5. El Super administrador accede a todas las aplicaciones.
6. La migracion `20261019_0004` asigna `research_hub` a todo usuario existente y
   no asigna `research_os` a nadie. Las cuentas nuevas reciben `research_hub`
   salvo que el administrador indique otra cosa.
7. Los usuarios con permiso `users:update` asignan o retiran aplicaciones en
   `Configuracion > Usuarios`, disponible con el mismo comportamiento en
   ResearchHUB y ResearchOS. Nadie puede modificar sus propios accesos
   (`users.self_access_change`): ni concederse una aplicacion ni bloquearse.

## Experiencia

1. `/researchos` presenta el login de ResearchOS con la identidad UCompensar y sin
   controles simulados (sin Microsoft, recordarme ni recuperacion de contrasena
   mientras no existan).
2. Si existe una sesion valida con acceso, entra directo al inicio.
3. Si la sesion es valida pero sin acceso, muestra `Tu cuenta no tiene acceso a
   ResearchOS`, ofrece `Ir a ResearchHUB` cuando corresponde e `Ingresar con otra
   cuenta`.
4. ResearchHUB aplica la misma regla: una sesion de ResearchOS sin acceso a HUB
   muestra el login de HUB con el motivo.
5. Cerrar sesion en cualquiera de las dos aplicaciones revoca en PostgreSQL la
   sesion compartida y vuelve al portal (ADR-005).
6. ResearchOS replica la navegacion de ResearchHUB: Inicio, grupo
   `Investigacion aplicada` con sus areas, `Reportes`, `Configuracion` (con
   `settings:manage`), `Aplicaciones` y `Cerrar sesion`. Lo que aun no opera
   se muestra deshabilitado como `Próximamente`; no hay notificaciones ni
   soporte simulados.
7. El portal habilita `Ingresar` de ResearchOS hacia `/researchos`. La variable
   `RESEARCH_OS_URL` se retira.

## Criterios de aceptacion

- Pruebas positivas y negativas de login por aplicacion, sesion compartida,
  rutas protegidas, superadministrador, asignacion, revocacion y autobloqueo.
- Migracion probada desde base vacia y desde `20261014_0003` con usuarios.
- Recorridos verificados a 320, 768 y 1440 px sin desplazamiento horizontal.

## Pendientes

- Spec y aprobacion de cada modulo de ResearchOS.
- Auditoria inmutable de cambios de acceso (hoy se conserva quien y cuando otorgo
  el acceso vigente, no el historial de retiros).
