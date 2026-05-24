# NewsRadar — Planificación del proceso de desarrollo

## Metodología

El desarrollo del proyecto se organizó siguiendo una metodología iterativa tipo Scrum/Kanban, usando GitHub como herramienta principal para la gestión del trabajo, control de versiones, trazabilidad de tareas e integración continua.

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
