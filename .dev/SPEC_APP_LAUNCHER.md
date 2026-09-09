---
document_id: "SPEC-PORTAL-001"
version: "1.4.0"
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
