---
name: researchhub-production-engineering
description: Aplica las condiciones de producto operable y escalable de ResearchHub-U. Usar en todo cambio de codigo, API, datos, seguridad, infraestructura, observabilidad, pruebas o despliegue del proyecto.
---

# ResearchHub Production Engineering

Trata cada iteracion como software institucional de larga vida. No introduzcas
atajos de demostracion, datos ficticios en runtime ni afirmaciones de produccion sin
evidencia.

## Fuentes obligatorias

1. Lee `../../../CONSTRAINTS.md` para conocer los limites no negociables.
2. Lee `../../PRODUCT_READINESS.md` antes de declarar una version desplegable.
3. Lee el spec funcional y el mapa de capacidades afectados.
4. Para interfaz o texto visible, aplica tambien
   `../ucompensar-look-and-feel/SKILL.md`.

## Flujo de cambio

1. Traza el cambio a un requisito y define criterios observables.
2. Escribe primero pruebas positivas, negativas, de permisos y concurrencia segun el
   riesgo.
3. Conserva limites `api -> service -> repository -> database`; evita estado local
   del servidor que impida replicas horizontales.
4. Diseña migraciones compatibles, idempotencia, paginacion y limites de entrada.
5. Protege secretos, datos personales, alcance por rol y registros de auditoria.
6. Añade señales operativas: errores estables, trace ID, logs sin datos sensibles,
   metricas y health checks cuando aplique.
7. Verifica lint, tipos, pruebas, migraciones y recorridos reales antes de cerrar.
8. Actualiza readiness y runbook cuando cambien riesgos o procedimientos.

## Reglas de escala

- Usa PostgreSQL como fuente de verdad; no uses memoria del proceso para estado
  compartido, locks distribuidos, sesiones ni rate limits de produccion.
- Pagina toda coleccion no acotada y filtra en base de datos.
- Diseña escrituras reintentables con idempotencia y concurrencia explicita.
- Mantiene presupuesto de conexiones, tiempos limite y backpressure.
- Separa migraciones del arranque de replicas de API.
- Guarda binarios en almacenamiento de objetos; PostgreSQL conserva metadatos.

## Definicion de terminado

Un cambio termina cuando tiene trazabilidad, pruebas, seguridad, observabilidad,
documentacion operativa y evidencia de los gates aplicables. Una pantalla funcional
o una prueba manual aislada no equivale a producto terminado.
