# ResearchHUB

Producto web institucional para gestionar procesos de investigacion y modalidades
de trabajo de grado. La aplicacion es un monolito modular FastAPI, usa PostgreSQL y
se entrega como contenedor inmutable.

El software se desarrolla con estandares de produccion desde cada iteracion, pero la
autorizacion de salida institucional depende de la evidencia de
`.dev/PRODUCT_READINESS.md`. El alcance funcional de trabajos de grado aun es
parcial frente a `.dev/SPEC_TRABAJOS_GRADO.md`.

## Inicio Local Con Docker

1. Crea `.env` a partir de `.env.example`.
2. Sustituye `POSTGRES_PASSWORD`, `DATABASE_URL` y `SECRET_KEY` por valores locales
   propios. `DATABASE_URL` debe apuntar a PostgreSQL: la aplicacion no arranca con
   otro motor. Toda la informacion, incluidas las sesiones, vive en esa base
   (`docs/adr/ADR-005-estado-solo-en-postgresql.md`).
3. Levanta la aplicacion:

```powershell
docker compose up --build
```

La interfaz queda en `http://localhost:8000`; salud en `/health/live` y
`/health/ready`; OpenAPI local en `/docs`.

La portada permite elegir entre ResearchHUB, ResearchOS, CRIS, CRAI y Servicios y
marketplace.
ResearchHUB y ResearchOS (`/researchos`) comparten la cuenta institucional; cada
usuario entra solo a las aplicaciones que un administrador le asigna en
`Configuracion > Usuarios` (ver `.dev/SPEC_RESEARCH_OS.md`). Los accesos externos se
configuran con URL absolutas y en produccion deben usar HTTPS. CRAI incluye su URL
institucional como valor predeterminado:

```dotenv
CRIS_URL=https://cris.example.edu.co
CRAI_URL=https://crai.ucompensar.edu.co/
RESEARCH_BLOG_URL=https://investigacion.example.edu.co/blog
SERVICES_MARKETPLACE_URL=https://servicios.example.edu.co
```

El carrusel de oportunidades permanece visible con estado `Proximamente` mientras
`RESEARCH_BLOG_URL` no este configurada. Al definirla, los flyers habilitan su
acceso al blog sin modificar el frontend.

El espacio `Servicios y marketplace` permanece en estado `Proximamente` mientras
`SERVICES_MARKETPLACE_URL` no este configurada. Al definirla, habilita el acceso
sin modificar el frontend.

Una base nueva no contiene usuarios predeterminados. Usuarios, contrasenas y
accesos viven solo en PostgreSQL; ninguna credencial se configura en `.env`. Para
crear el primer superadministrador, con la aplicacion en ejecucion:

```powershell
docker compose exec api python -m app.cli.create_superadmin
```

El comando pide nombre, correo y contrasena (oculta y confirmada, 16 o mas
caracteres) en la terminal y guarda solo su hash en PostgreSQL. Rechaza ejecuciones
no interactivas y no modifica una cuenta si el correo ya existe. Las demas cuentas
se crean desde `Configuracion > Usuarios`.

## Desarrollo Sin Docker

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
alembic upgrade head
python -m app.cli.create_superadmin
uvicorn app.main:app --reload
```

Para esta modalidad, `POSTGRES_HOST=localhost` y `DATABASE_URL` debe apuntar al
PostgreSQL accesible desde Windows.

## Verificacion

```powershell
python -m ruff check app tests
python -m mypy app
python -m pytest
docker compose config --quiet
docker compose --env-file .env.production -f compose.production.yaml config --quiet
```

## Produccion

`.env.production.example` documenta el contrato, pero sus marcadores deben venir de
un gestor de secretos. La configuracion de produccion falla al arrancar si habilita
debug, OpenAPI o autorregistro, si omite HSTS o si conserva secretos de ejemplo.

`compose.production.yaml` sirve como referencia endurecida de un solo host. La
topologia institucional debe incluir ingreso TLS, dos o mas replicas de API,
PostgreSQL de alta disponibilidad, observabilidad central y backups con PITR. El
procedimiento completo esta en `.dev/OPERATIONS_RUNBOOK.md`.

## Arquitectura Y Reglas

- Una aplicacion desplegable y modulos de negocio en `app/modules`.
- Dependencias `api -> services -> repository -> database`.
- Componentes transversales en `app/core`.
- Cambios de esquema exclusivamente con Alembic.
- Autorizacion en backend, trazabilidad por `x-trace-id` y logs JSON.
- Contrato de calidad en `CONSTRAINTS.md` y especificaciones funcionales en `.dev`.
