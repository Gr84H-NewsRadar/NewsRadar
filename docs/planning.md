# NewsRadar — Planificación del proceso de desarrollo

## Metodología

El desarrollo del proyecto se organizó siguiendo una metodología iterativa tipo Scrum/Kanban, usando GitHub como herramienta principal para la gestión del trabajo, el control de versiones, la trazabilidad de tareas y la integración continua.

El equipo trabajó con un tablero Kanban en GitHub Projects para visualizar el estado de las tareas durante todo el desarrollo. Las issues se organizaron por prioridad, sprint y área funcional, y se fueron moviendo entre columnas como `Backlog`, `To Do`, `In Progress`, `Review` y `Done`.

## Herramientas

- GitHub Issues para tareas, requisitos y seguimiento del trabajo.
- GitHub Projects como tablero Kanban del equipo.
- GitHub Milestones para agrupar issues por sprint.
- GitHub Actions para CI/CD.
- Pull requests para revisión e integración de cambios.
- Ramas `main` y `develop`.
- Ramas de feature para tareas concretas.
- Documentación versionada en `docs/`.
- Docker Compose para construcción y ejecución local del sistema.

## Organización del trabajo

El trabajo se dividió en issues asociadas a funcionalidades, tareas técnicas, documentación, pruebas y DevOps.

Cada issue incluía, cuando era necesario:

- Descripción de la tarea.
- Objetivo funcional o técnico.
- Criterios de aceptación.
- Sprint o milestone asociado.
- Relación con requisitos del proyecto.
- Referencias a commits o pull requests.

Las issues se cerraban desde GitHub o directamente desde la terminal mediante commits y pull requests, usando mensajes con referencias como:

```text
Closes #5
Fixes #10
Resolves #14
```

De esta forma, al integrar los cambios en la rama correspondiente, GitHub cerraba automáticamente las issues relacionadas y mantenía la trazabilidad entre tarea, commit y código implementado.

## Sprints y milestones

El proyecto se planificó en **5 sprints principales**, representados como milestones en GitHub.

Cada milestone agrupaba un conjunto de issues relacionadas con una fase del desarrollo.

| Sprint | Objetivo | Resultado |
| --- | --- | --- |
| Sprint 1 | Inicialización del proyecto, estructura base y API mínima | FastAPI, estructura del repositorio, modelos iniciales y health check |
| Sprint 2 | Autenticación, usuarios y roles | Registro, login, JWT, usuarios, roles `admin` y `manager` |
| Sprint 3 | Alertas, fuentes de información y canales RSS | Gestión de alertas, fuentes, canales RSS y categorías IPTC |
| Sprint 4 | Procesamiento RSS, clasificación y notificaciones | Procesamiento de noticias, coincidencias con alertas, buzón interno y MailHog |
| Sprint 5 | Dashboard, frontend, DevOps, pruebas y documentación | Interfaz completa, estadísticas, nubes de palabras, CI/CD, Docker Compose, ADRs y documentación final |

## Tablero Kanban

El tablero Kanban permitió controlar visualmente el avance del proyecto.

Las columnas utilizadas fueron:

| Columna | Significado |
| --- | --- |
| Backlog | Tareas identificadas pero aún no planificadas para el sprint actual |
| To Do | Tareas seleccionadas para el sprint |
| In Progress | Tareas en desarrollo |
| Review | Tareas pendientes de revisión, pruebas o validación |
| Done | Tareas completadas e integradas |

El tablero se revisaba periódicamente para reasignar prioridades, detectar bloqueos y comprobar el avance de cada sprint.

## Estrategia de ramas

La estrategia de ramas fue sencilla para facilitar la integración continua y evitar divergencias innecesarias:

- `main`: versión estable y entregable del proyecto.
- `develop`: integración de cambios antes de pasar a `main`.
- Ramas de feature: cambios concretos asociados a issues.

Ejemplos de ramas de feature:

```text
feature/auth-login
feature/alerts-crud
feature/rss-processing
feature/dashboard
feature/docker-compose
docs/update-readme
```

Los cambios importantes se integraban mediante pull requests o commits revisados por el equipo.

## Integración continua

El proyecto utiliza GitHub Actions para automatizar validaciones del sistema.

El pipeline de CI ejecuta tareas como:

- Instalación de dependencias.
- Ejecución de tests.
- Generación de informe de cobertura.
- Verificación de cobertura mínima.
- Análisis de calidad con pylint.
- Construcción de imagen Docker.

Esto permitió detectar errores antes de integrar cambios en la rama estable.

## Criterios de finalización

Una tarea se considera terminada cuando:

- El código está implementado.
- La funcionalidad puede ejecutarse con Docker Compose.
- Los tests relacionados pasan correctamente.
- La cobertura no baja del mínimo exigido.
- La calidad de código cumple el umbral definido.
- La documentación relacionada está actualizada.
- La issue asociada queda cerrada.
- El cambio queda integrado en el repositorio.

## Relación con los entregables

La planificación del trabajo se relaciona con los entregables del proyecto de la siguiente forma:

| Entregable | Evidencia en el repositorio |
| --- | --- |
| Código fuente completo | `newsradar_api/` |
| Documentación versionada | `README.md` y `docs/` |
| ADRs | `docs/adr/` |
| API REST documentada | FastAPI OpenAPI en `/docs` |
| Automatización de ejecución | `docker-compose.yml` |
| Automatización de pruebas | `pytest`, `pytest-cov`, GitHub Actions |
| Calidad de código | `pylint`, GitHub Actions |
| CI/CD | `.github/workflows/` |
| Trazabilidad | Issues, milestones, commits, PRs y documentación |
