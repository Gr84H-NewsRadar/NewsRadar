# NewsRadar

[![CI](https://github.com/Gr84H-NewsRadar/NewsRadar/actions/workflows/ci.yml/badge.svg)](https://github.com/Gr84H-NewsRadar/NewsRadar/actions/workflows/ci.yml)
[![CD](https://github.com/Gr84H-NewsRadar/NewsRadar/actions/workflows/cd.yml/badge.svg)](https://github.com/Gr84H-NewsRadar/NewsRadar/actions/workflows/cd.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Sistema de monitorización de noticias en medios de comunicación y fuentes oficiales.

> Proyecto final de la asignatura **Desarrollo y Operación de Sistemas Software** propuesto por el GRUPO-H.

## Índice

- [Descripción](#descripción)
- [Ejecución del proyecto](#ejecución-del-proyecto)
- [Funcionalidades](#funcionalidades)
- [Arquitectura](#arquitectura)
- [API REST](#api-rest)
- [Tests y calidad](#tests-y-calidad)
- [Documentación](#documentación)
- [Trazabilidad](#trazabilidad)

## Descripción

NewsRadar permite escuchar canales RSS de medios de comunicación y fuentes oficiales, organizar la información en categorías IPTC, y monitorizar palabras clave mediante alertas configurables. Cuando se detecta una noticia que coincide con una alerta, el sistema notifica al usuario por correo y por buzón interno.

## Ejecución del proyecto

### Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado y abierto:

- Docker Desktop
- Docker Compose
- Python 3.10 o superior
- Git

> Si Docker Desktop no está abierto, puede aparecer un error similar a:
> ```bash
> failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
> ```

---

### 1. Clonar el repositorio

```bash
git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git
cd NewsRadar
```

### 2. Añadir la carpeta de verificación

Copiar la carpeta `devops_verifica-main` proporcionada en Magistral dentro de la raíz del proyecto.

La estructura final debe ser similar a:

```text
NewsRadar/
├── docker-compose.yml
├── Makefile
├── newsradar_api/
├── docs/
├── scripts/
└── devops_verifica-main/
    ├── run_tests.py
    ├── requirements.txt
    ├── tests/
    └── test_data/
```

### 3. Levantar la aplicación con Docker Compose

Desde la raíz del proyecto:

```bash
docker compose up --build
```

También se puede ejecutar en segundo plano con:

```bash
docker compose up -d --build
```

Este comando construye y levanta los servicios necesarios:

- API de NewsRadar
- Base de datos PostgreSQL
- MailHog para pruebas de correo

### 4. Comprobar que la aplicación está funcionando

Una vez levantados los contenedores, la aplicación estará disponible en:

```text
http://localhost:8000
```

La documentación interactiva de la API estará disponible en:

```text
http://localhost:8000/docs
```

MailHog estará disponible en:

```text
http://localhost:8025
```

También se puede comprobar el estado de la API con:

```bash
curl http://localhost:8000/api/v1/health
```

### 5. Credenciales por defecto

Para acceder como administrador:

```text
Email: admin@newsradar.com
Contraseña: admin123
```

### 6. Ejecutar las pruebas de verificación

Con la aplicación ya levantada, abrir otra terminal y entrar en la carpeta de verificación:

```bash
cd devops_verifica-main
```

Ejecutar todas las pruebas:

```bash
python run_tests.py --all
```

Si se quiere indicar explícitamente la URL del servicio:

```bash
python run_tests.py --service http://localhost:8000 --all
```

### 7. Parar la aplicación

Para detener los contenedores:

```bash
docker compose down
```

Para detenerlos y eliminar también los volúmenes de datos:

```bash
docker compose down -v
```

## Funcionalidades

| Objetivo | Funcionalidad                                                                      |
| -------- | ---------------------------------------------------------------------------------- |
| 1        | Gestión de alertas (hasta 20 por usuario) con descriptores y categoría IPTC        |
| 2        | Clasificación automática de noticias en categorías IPTC primer nivel               |
| 3        | Notificaciones a buzón interno y correo electrónico                                |
| 4        | Gestión de fuentes (10 medios, 100+ canales RSS, 17 categorías IPTC cubiertas)     |
| 5        | Roles `admin`, `manager` (gestor) y `reader` (lector) con permisos diferenciados   |
| 6        | Dashboard con estadísticas globales, nubes de palabras y panel UI completo         |

## Arquitectura

Arquitectura de 5 capas como exige el enunciado:

1. **Capa de presentación** — Frontend HTML/JS/Bootstrap servido por FastAPI en `/static/`.
2. **Capa de API REST** — FastAPI con OpenAPI 3.1 documentado en `/docs`.
3. **Capa de lógica de negocio** — Servicios Python (rss_processor, synonym_service, email_service).
4. **Capa de persistencia** — SQLAlchemy + PostgreSQL.
5. **Capa de datos** — PostgreSQL 15 en contenedor.

Decisiones arquitectónicas documentadas en [`docs/adr/`](docs/adr/):

- ADR 001: Uso de FastAPI como framework
- ADR 002: PostgreSQL como sistema de persistencia
- ADR 003: Despliegue mediante Docker

## API REST

API REST documentada con OpenAPI. Endpoints principales:

```
GET  /api/v1/health
POST /api/v1/auth/login
POST /api/v1/auth/register
GET  /api/v1/users
GET  /api/v1/users/{id}/alerts
POST /api/v1/users/{id}/alerts
GET  /api/v1/categories
GET  /api/v1/information-sources
GET  /api/v1/news?q=...&category_id=...&date_from=...&date_to=...
GET  /api/v1/dashboard/stats
GET  /api/v1/dashboard/wordcloud?category_id=...
```

Lista completa: http://localhost:8000/docs

## Tests y calidad

Cobertura mínima exigida y verificada en CI: **60 %**.

```bash
make test                  # Suite completa con cobertura
docker-compose exec api pytest -v   # Solo tests
```

Métricas de calidad de código:

```bash
docker-compose exec api pylint app/   # Score esperado ≥ 8.0
```

## Documentación

| Documento                                                | Contenido                                                  |
| -------------------------------------------------------- | ---------------------------------------------------------- |
| [`docs/quickstart.md`](docs/quickstart.md)               | Guía rápida de inicio                                      |
| [`docs/deployment.md`](docs/deployment.md)               | Despliegue, CI/CD, rollback, troubleshooting               |
| [`docs/architecture.md`](docs/architecture.md)           | Diagramas de arquitectura y flujos                         |
| [`docs/api-examples.md`](docs/api-examples.md)           | Ejemplos de uso del API                                    |
| [`docs/adr/`](docs/adr/)                                 | Decisiones arquitectónicas (ADRs)                          |

## Trazabilidad

| Requisito | Implementación                                       | Tests asociados                  | Issue |
| --------- | ---------------------------------------------------- | -------------------------------- | ----- |
| RF01      | `auth.py`, `email_service.py`                        | `test_api.py::test_register`     | #5    |
| RF02      | `auth.py::create_access_token`                       | `test_api.py::test_login`        | #6    |
| RF03      | `main.py` endpoints `/users/{id}/alerts`             | `test_api.py::test_alerts_*`     | #10   |
| RF04      | `synonym_service.py`                                 | `test_api.py::test_synonyms`     | #11   |
| RF05      | `main.py` endpoints `/information-sources/*`         | `test_api.py::test_sources_*`    | #8    |
| RF06      | `rss_processor.py::process_rss_channels`             | `test_api.py::test_rss`          | #12   |
| RF08      | `models.py::Category` con código IPTC                | —                                | #13   |
| RF09      | `rss_processor.py::create_alert_notification`        | `test_api.py::test_notifications`| #14   |
| RF10      | `models.py::Alert.notify_email/notify_inbox`         | —                                | #15   |
| RF11      | `email_service.py::send_alert_notification`          | —                                | #16   |
| RF13      | `main.py::get_dashboard_stats` + `dashboard.html`    | —                                | #23   |
| RF14      | `main.py::get_wordcloud` + `wordcloud.html`          | —                                | #24   |
| RF15      | `auth.py::require_manager`                           | `test_api.py::test_rbac`         | #7    |
| RF16      | Frontend completo en `app/static/`                   | —                                | #25   |
| RF17      | `main.py::list_news` con filtros                     | —                                | #26   |
| RNF01-12  | Ver [`docs/`](docs/) y workflows de CI/CD            | —                                | #1-21 |

## Licencia

MIT. Ver [`LICENSE`](LICENSE).

## Equipo

Grupo Gr84H — UC3M, curso 2025/2026.
