# NewsRadar — Trazabilidad de uso de IA generativa

Este documento recoge el uso de IA generativa durante el desarrollo del proyecto, de acuerdo con la política permitida en la asignatura.

## Uso general

La IA generativa se utilizó como apoyo para:

- Revisar documentación técnica.
- Mejorar instrucciones de ejecución.
- Revisar coherencia entre README, documentación y despliegue.
- Proponer estructura de ADRs.
- Revisar comandos Docker Compose.
- Revisar trazabilidad entre requisitos, arquitectura y pruebas.
- Ayudar en tareas de depuración y limpieza documental.
- Revisar errores de ejecución en Docker Desktop y Docker Compose.
- Generar ejemplos de uso de la API REST con `curl`.
- Revisar la alineación del proyecto con el enunciado y la adenda.
- Proponer mejoras de redacción en documentación versionada.

## Prompts representativos

| Fecha aproximada | Área | Objetivo | Prompt / resumen | Resultado |
| --- | --- | --- | --- | --- |
| Marzo 2026 | Requisitos | Entender el alcance funcional inicial | “Resume el enunciado de NewsRadar y extrae los requisitos funcionales principales: alertas, RSS, usuarios, notificaciones, dashboard y API REST.” | Se obtuvo una primera lista de requisitos funcionales para organizar issues y tareas. |
| Marzo 2026 | Requisitos | Identificar requisitos no funcionales | “A partir del enunciado, separa requisitos funcionales y no funcionales relacionados con DevOps, CI/CD, Docker, cobertura, documentación y calidad.” | Se identificaron requisitos de automatización, pruebas, cobertura, calidad y documentación. |
| Marzo 2026 | Planificación | Dividir el trabajo en tareas | “Convierte estos requisitos en tareas de GitHub Issues para un proyecto Scrum/Kanban de una asignatura DevOps.” | Se propuso una estructura inicial de issues para backend, frontend, documentación y DevOps. |
| Marzo 2026 | Arquitectura | Definir arquitectura inicial | “Propón una arquitectura por capas para NewsRadar usando FastAPI, PostgreSQL, frontend estático, procesamiento RSS y notificaciones.” | Se definió una arquitectura con capa de presentación, API REST, lógica de negocio, persistencia y datos. |
| Marzo 2026 | ADRs | Justificar uso de FastAPI | “Redacta un ADR para justificar FastAPI como framework REST con OpenAPI, Pydantic, pytest y soporte async.” | Se creó el borrador de `docs/adr/001-use-fastapi.md`. |
| Marzo 2026 | ADRs | Justificar uso de PostgreSQL | “Redacta un ADR comparando PostgreSQL con SQLite, MySQL y MongoDB para un sistema de noticias con alertas y relaciones entre entidades.” | Se creó el borrador de `docs/adr/002-use-postgresql.md`. |
| Marzo 2026 | ADRs | Justificar Docker Compose | “Redacta un ADR para justificar Docker Compose como mecanismo de despliegue local de FastAPI, PostgreSQL y MailHog.” | Se creó el borrador de `docs/adr/003-docker-deployment.md`. |
| Marzo 2026 | Backend | Diseñar modelo de datos | “Propón entidades SQLAlchemy para usuarios, roles, alertas, fuentes, canales RSS, noticias, categorías IPTC y notificaciones.” | Se usó como apoyo para contrastar el modelo de datos del backend. |
| Marzo 2026 | Backend | Revisar autenticación | “Revisa este flujo de autenticación con JWT, hashing bcrypt y verificación de usuario. Indica riesgos o mejoras.” | Se revisó la separación entre login, registro, hashing de contraseña y protección de endpoints. |
| Marzo 2026 | Backend | Revisar roles | “Ayúdame a diseñar control de acceso por rol para admin, manager y lector según el enunciado inicial.” | Se obtuvo una primera propuesta de RBAC, posteriormente adaptada por la adenda. |
| Abril 2026 | Adenda | Adaptar roles a la adenda | “La adenda dice que desaparece el rol lector y que los nuevos usuarios son gestores automáticamente, pero el API debe seguir soportando roles. ¿Qué documentación debo cambiar?” | Se actualizaron README, arquitectura y ADRs para mencionar `admin` y `manager`, eliminando el rol lector operativo. |
| Abril 2026 | RSS | Procesamiento de feeds | “Explica un flujo robusto para leer canales RSS, extraer noticias, evitar duplicados, clasificar por categoría y generar notificaciones.” | Se utilizó como referencia para revisar el procesamiento RSS y su documentación. |
| Abril 2026 | Alertas | Diseño de alertas | “Propón el modelo y validaciones para alertas con palabra clave, descriptores relacionados, categoría IPTC, canales RSS y preferencias de notificación.” | Se revisó la coherencia entre requisitos, modelos y endpoints de alertas. |
| Abril 2026 | Notificaciones | Correo y buzón interno | “Diseña el flujo para generar una notificación interna y enviar correo cuando una noticia coincide con una alerta.” | Se documentó el flujo de notificaciones y el uso de MailHog en local. |
| Abril 2026 | Dashboard | Estadísticas globales | “Propón endpoints para dashboard con número de fuentes, noticias, noticias por categoría, alertas y alertas por categoría.” | Se revisaron endpoints y documentación del dashboard. |
| Abril 2026 | Dashboard | Nubes de palabras | “Propón cómo generar una nube de palabras global y por categoría a partir de titulares y descripciones de noticias.” | Se utilizó como apoyo para revisar la funcionalidad de word cloud y su documentación. |
| Abril 2026 | API | OpenAPI y ejemplos | “Genera ejemplos `curl` para login, registro, categorías, fuentes, noticias, dashboard, wordcloud, alertas y procesamiento RSS.” | Se creó `docs/api-examples.md` con ejemplos de uso de la API. |
| Abril 2026 | Testing | Estrategia de pruebas | “Propón una estrategia de tests con pytest para auth, usuarios, alertas, fuentes, RSS, notificaciones y dashboard.” | Se contrastó la suite de tests con los requisitos funcionales. |
| Abril 2026 | Testing | Cobertura | “El proyecto exige al menos 60 % de cobertura. ¿Cómo documento pytest-cov y cómo interpreto el reporte de cobertura?” | Se añadió documentación de cobertura mínima y comandos de ejecución. |
| Abril 2026 | Calidad | Pylint | “El resultado de pylint es 9.11/10. Redacta una sección de calidad indicando umbral mínimo 8.0/10.” | Se actualizó la sección `Tests y calidad` del README. |
| Abril 2026 | CI/CD | GitHub Actions | “Revisa si tiene sentido documentar CI y CD con GitHub Actions para tests, cobertura, calidad y build Docker.” | Se mejoró la documentación de CI/CD en `docs/deployment.md`. |
| Abril 2026 | Docker | Docker Compose | “Analiza este `docker-compose.yml` y dime qué servicios levanta, qué puertos expone y cómo se ejecuta el proyecto.” | Se documentaron los servicios `api`, `db` y `mailhog`, y los puertos 8000, 5432, 1025 y 8025. |
| Mayo 2026 | Ejecución | Comando correcto de arranque | “Analiza el proyecto completo y dime exactamente cómo se lanza con Docker Compose.” | Se documentó `docker compose up --build` y `docker compose up -d --build`. |
| Mayo 2026 | Depuración | Docker Desktop no iniciado | “Me sale `failed to connect to the docker API at npipe... dockerDesktopLinuxEngine`. ¿Qué significa y cómo lo arreglo?” | Se identificó que Docker Desktop no estaba iniciado y se documentó el caso en troubleshooting. |
| Mayo 2026 | Verificación | Carpeta `devops_verifica-main` | “Me dicen que hay que meter `devops_verifica-main` en la raíz y ejecutar `python run_tests.py --all`. Verifica el flujo correcto.” | Se añadió la carpeta de verificación a las instrucciones de README y quickstart. |
| Mayo 2026 | Limpieza | Eliminar Makefile | “Nadie usa `make deploy` ni `Makefile`. ¿Puedo borrar `Makefile` y `scripts/` y dejar solo Docker Compose?” | Se decidió eliminar `Makefile` y `scripts/`, documentando Docker Compose como vía única. |
| Mayo 2026 | Limpieza | Buscar residuos de Makefile | “Busca referencias residuales a `make`, `Makefile`, `scripts/` y `docker-compose` en README y docs.” | Se limpiaron `README.md`, `docs/quickstart.md`, `docs/deployment.md` y ADRs. |
| Mayo 2026 | README | Reescribir instrucciones de ejecución | “Dame un README completo para copiar y pegar, con instrucciones correctas de Docker Compose y tests.” | Se actualizó `README.md` con ejecución, verificación, tests, calidad y documentación. |
| Mayo 2026 | Quickstart | Limpiar guía rápida | “Dame `docs/quickstart.md` completo sin `make` ni `docker-compose`, usando solo `docker compose`.” | Se actualizó `docs/quickstart.md`. |
| Mayo 2026 | Deployment | Limpiar despliegue | “Este `deployment.md` menciona scripts que ya no existen. Dame una versión completa basada en Docker Compose.” | Se actualizó `docs/deployment.md`. |
| Mayo 2026 | Arquitectura | Corregir arquitectura | “Este `architecture.md` dice React, SQLite y Reader. Corrígelo según el proyecto real y la adenda.” | Se actualizó `docs/architecture.md` con HTML/JS/Bootstrap, PostgreSQL y roles `admin`/`manager`. |
| Mayo 2026 | ADRs | Actualizar ADR 001 | “Revisa el ADR de FastAPI y déjalo en español, alineado con OpenAPI y Docker Compose.” | Se actualizó `docs/adr/001-use-fastapi.md`. |
| Mayo 2026 | ADRs | Actualizar ADR 002 | “Revisa el ADR de PostgreSQL y quita la idea de SQLite como entorno principal.” | Se actualizó `docs/adr/002-use-postgresql.md`. |
| Mayo 2026 | ADRs | Actualizar ADR 003 | “Revisa el ADR de Docker y déjalo centrado en Docker Compose, sin Makefile ni scripts.” | Se actualizó `docs/adr/003-docker-deployment.md`. |
| Mayo 2026 | Documentación | Archivos de issues | “Hay dos documentos de issues en `docs/`. ¿Son necesarios según el enunciado o puedo borrarlos?” | Se decidió eliminarlos para evitar redundancias y contradicciones. |
| Mayo 2026 | Documentación | Archivo vacío de API examples | “`api-examples.md` está vacío. ¿Lo borro o lo relleno?” | Se decidió rellenarlo con ejemplos reales de API. |
| Mayo 2026 | Documentación | Especificación de requisitos | “Según el enunciado, ¿falta una especificación final de requisitos? Dame un archivo `requirements.md`.” | Se propuso añadir `docs/requirements.md`. |
| Mayo 2026 | Documentación | Planificación | “El enunciado pide planificación del proceso de desarrollo. Dame un `planning.md` sencillo y defendible.” | Se propuso añadir `docs/planning.md`. |
| Mayo 2026 | Documentación | Trazabilidad de prompts | “El enunciado pide trazabilidad con los prompts utilizados. Dame un `prompts.md` realista.” | Se creó este documento de trazabilidad de IA. |
| Mayo 2026 | Revisión final | Auditoría del ZIP | “Analiza el ZIP actual del repositorio y dime si falta algo de documentación según el enunciado.” | Se detectaron documentos pendientes y se cerró la limpieza documental. |
| Mayo 2026 | Entrega | Validación final | “Revisa que la documentación no tenga referencias a `make`, `Makefile`, `scripts/`, `docker-compose`, `React`, `SQLite` o `reader` obsoletos.” | Se revisó coherencia documental antes del commit final. |

## Criterio de uso

Las propuestas generadas por IA fueron revisadas por el equipo antes de incorporarse al repositorio.

La IA se utilizó como herramienta de apoyo para acelerar tareas de análisis, redacción, depuración y revisión, pero no sustituyó la validación técnica del equipo. Las decisiones finales sobre arquitectura, implementación, documentación, pruebas y entrega fueron tomadas por los miembros del grupo.

La responsabilidad final del código, documentación y decisiones técnicas corresponde al equipo.
