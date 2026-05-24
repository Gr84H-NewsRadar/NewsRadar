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

NewsRadar permite escuchar canales RSS de medios de comunicación y fuentes oficiales, organizar la información en categorías IPTC y monitorizar palabras clave mediante alertas configurables. Cuando se detecta una noticia que coincide con una alerta, el sistema notifica al usuario por correo electrónico y por buzón interno.

## Ejecución del proyecto

### Requisitos previos

Antes de ejecutar el proyecto, asegúrate de tener instalado y abierto:

- Docker Desktop
- Docker Compose
- Python 3.10 o superior
- Git

> Si Docker Desktop no está abierto, puede aparecer un error similar a:
>
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
├── newsradar_api/
├── docs/
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

| Objetivo | Funcionalidad                                                                 |
| -------- | ----------------------------------------------------------------------------- |
| 1        | Gestión de alertas hasta 20 por usuario, con descriptores y categoría IPTC    |
| 2        | Clasificación automática de noticias en categorías IPTC de primer nivel       |
| 3        | Notificaciones a buzón interno y correo electrónico                           |
| 4        | Gestión de fuentes con 10 medios, más de 100 canales RSS y cobertura IPTC     |
| 5        | Roles `admin` y `manager`/gestor, con soporte de API para gestión de roles    |
| 6        | Dashboard con estadísticas globales, nubes de palabras y panel UI completo    |

## Arquitectura

Arquitectura de 5 capas como exige el enunciado:

1. **Capa de presentación** — Frontend HTML/JS/Bootstrap servido por FastAPI en `/static/`.
2. **Capa de API REST** — FastAPI con OpenAPI 3.1 documentado en `/docs`.
3. **Capa de lógica de negocio** — Servicios Python: procesamiento RSS, sinónimos, autenticación, notificaciones y dashboard.
4. **Capa de persistencia** — SQLAlchemy sobre PostgreSQL.
5. **Capa de datos** — PostgreSQL 15 en contenedor.

Decisiones arquitectónicas documentadas en [`docs/adr/`](docs/adr/):

- ADR 001: Uso de FastAPI como framework.
- ADR 002: Uso de PostgreSQL como sistema de persistencia.
- ADR 003: Despliegue mediante Docker Compose.

## API REST

API REST documentada con OpenAPI. Endpoints principales:

```text
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

Lista completa:

```text
http://localhost:8000/docs
```

## Tests y calidad

Cobertura mínima exigida: **60 %**. La suite actual alcanza aproximadamente un **61 %** de cobertura.

Con los contenedores levantados:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

Métricas de calidad de código:

```bash
docker compose exec api pylint app/
```

El score esperado es superior a **8.0/10**. En la ejecución actual, el proyecto obtiene aproximadamente **9.11/10**.

## Documentación

| Documento                                      | Contenido                                      |
| ---------------------------------------------- | ---------------------------------------------- |
| [`docs/quickstart.md`](docs/quickstart.md)     | Guía rápida de inicio                          |
| [`docs/deployment.md`](docs/deployment.md)     | Despliegue, CI/CD, rollback y troubleshooting  |
| [`docs/architecture.md`](docs/architecture.md) | Arquitectura, componentes y flujos principales |
| [`docs/api-examples.md`](docs/api-examples.md) | Ejemplos de uso del API                        |
| [`docs/requirements.md`](docs/requirements.md) | Especificación final de requisitos y trazabilidad |
| [`docs/planning.md`](docs/planning.md)         | Planificación, sprints, milestones y tablero Kanban |
| [`docs/prompts.md`](docs/prompts.md)           | Trazabilidad del uso de IA generativa          |
| [`docs/adr/`](docs/adr/)                       | Decisiones arquitectónicas                     |

## Trazabilidad

| Requisito | Implementación                                    | Tests asociados                   | Issue |
| --------- | ------------------------------------------------- | --------------------------------- | ----- |
| RF01      | `auth.py`, `email_service.py`                     | `test_api.py::test_register`      | #5    |
| RF02      | `auth.py::create_access_token`                    | `test_api.py::test_login`         | #6    |
| RF03      | `main.py` endpoints `/users/{id}/alerts`          | `test_api.py::test_alerts_*`      | #10   |
| RF04      | `synonym_service.py`                              | `test_api.py::test_synonyms`      | #11   |
| RF05      | `main.py` endpoints `/information-sources/*`      | `test_api.py::test_sources_*`     | #8    |
| RF06      | `rss_processor.py::process_rss_channels`          | `test_api.py::test_rss`           | #12   |
| RF08      | `models.py::Category` con código IPTC             | —                                 | #13   |
| RF09      | `rss_processor.py::create_alert_notification`     | `test_api.py::test_notifications` | #14   |
| RF10      | `models.py::Alert.notify_email/notify_inbox`      | —                                 | #15   |
| RF11      | `email_service.py::send_alert_notification`       | —                                 | #16   |
| RF13      | `main.py::get_dashboard_stats` + `dashboard.html` | —                                 | #23   |
| RF14      | `main.py::get_wordcloud` + `wordcloud.html`       | —                                 | #24   |
| RF15      | `auth.py::require_manager`                        | `test_api.py::test_rbac`          | #7    |
| RF16      | Frontend completo en `app/static/`                | —                                 | #25   |
| RF17      | `main.py::list_news` con filtros                  | —                                 | #26   |
| RNF01-12  | Ver [`docs/`](docs/) y workflows de CI/CD         | —                                 | #1-21 |

## Correspondencia con los requisitos de entrega

Esta tabla resume dónde queda cubierta cada exigencia técnica y documental del enunciado dentro del repositorio NewsRadar.

| Exigencia del enunciado | Evidencia en este proyecto |
| --- | --- |
| Repositorio único y versionado | Todo el código, configuración y documentación se encuentra en este repositorio |
| Clonado del proyecto | `git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git` |
| Construcción del sistema | `docker compose up --build` construye la imagen de la API definida en `newsradar_api/Dockerfile` |
| Despliegue en entorno limpio | `docker compose up --build` levanta desde cero los servicios `api`, `db` y `mailhog` |
| Ejecución de la aplicación | La aplicación queda disponible en `http://localhost:8000` |
| Base de datos persistente | PostgreSQL 15 se ejecuta como servicio `db` en `docker-compose.yml` |
| Servicio de correo en local | MailHog captura los correos de prueba en `http://localhost:8025` |
| API REST documentada | FastAPI genera OpenAPI automáticamente en `http://localhost:8000/docs` |
| Pruebas internas | `docker compose exec api pytest -v --cov=app --cov-report=term-missing` |
| Verificación funcional externa | `cd devops_verifica-main && python run_tests.py --all` |
| Cobertura de pruebas | `pytest-cov` genera el informe de cobertura y valida el umbral mínimo configurado |
| Calidad de código | `docker compose exec api pylint app/` y workflow de CI |
| Integración continua | `.github/workflows/ci.yml` |
| Empaquetado / distribución | `.github/workflows/cd.yml` |
| Documentación de ejecución | `README.md` y `docs/quickstart.md` |
| Documentación de despliegue | `docs/deployment.md` |
| Arquitectura del sistema | `docs/architecture.md` |
| Decisiones arquitectónicas | `docs/adr/` |
| Especificación de requisitos | `docs/requirements.md` |
| Planificación del desarrollo | `docs/planning.md` |
| Trazabilidad de uso de IA generativa | `docs/prompts.md` |
| Ejemplos de uso del API | `docs/api-examples.md` |

## Licencia

MIT. Ver [`LICENSE`](LICENSE).

## Equipo

Grupo Gr84H — UC3M, curso 2025/2026.
