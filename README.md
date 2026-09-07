# ResearchHub-U

Monolito modular FastAPI para automatizar procesos academicos y de investigacion
universitaria. El primer MVP previsto es la homologacion de trabajo de grado
mediante semillero de investigacion, pero este bootstrap no implementa reglas de
negocio pendientes.

## Requisitos

- Python 3.12
- Docker y Docker Compose
- Make opcional

## Inicio rapido

```bash
cp .env.example .env
docker compose up --build
```

API:

- `GET /health/live`
- `GET /health/ready`
- `GET /api/v1/meta`
- `GET /`
- `GET /docs`

## Desarrollo local sin Docker

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

## Comandos

```bash
make setup
make up
make down
make migrate
make revision
make test
make lint
make check
make logs
```

## Reglas de arquitectura

- Una sola aplicacion desplegable.
- Codigo organizado por modulos de negocio en `app/modules`.
- Direccion de dependencias: `api -> services -> repository -> database`.
- Componentes transversales en `app/core` y `app/shared`.
- Modulos futuros solo documentan alcance hasta que sean aprobados.
