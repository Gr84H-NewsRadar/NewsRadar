# NewsRadar — Guía de Despliegue

Documento de referencia para construir, desplegar, probar, hacer rollback y operar NewsRadar mediante Docker Compose.

## Tabla de contenidos

1. [Arquitectura del despliegue](#arquitectura-del-despliegue)
2. [Pipeline DevOps](#pipeline-devops)
3. [Entornos](#entornos)
4. [Despliegue local](#despliegue-local)
5. [Despliegue en CI/CD](#despliegue-en-cicd)
6. [Rollback](#rollback)
7. [Monitorización y logs](#monitorización-y-logs)
8. [Backup y restauración](#backup-y-restauración)
9. [Troubleshooting](#troubleshooting)
10. [Checklist de despliegue para producción](#checklist-de-despliegue-para-producción)

---

## Arquitectura del despliegue

NewsRadar se compone de tres servicios desplegados como contenedores Docker orquestados por Docker Compose:

```text
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL 15   │◄───┤   FastAPI App    │───►│     MailHog      │
│   :5432           │    │   :8000          │    │   :1025 / :8025  │
└───────────────────┘    └──────────────────┘    └──────────────────┘
                              │
                              └─► Frontend estático servido en /static
```

- **PostgreSQL** persiste usuarios, alertas, fuentes, canales, noticias, notificaciones y estadísticas.
- **FastAPI** expone el API REST y sirve el frontend estático.
- **MailHog** captura los correos en local sin enviarlos al exterior. En producción se sustituiría por un SMTP real.

## Pipeline DevOps

| Fase | Herramienta | Disparador |
| --- | --- | --- |
| Lint y calidad | pylint | Push o pull request |
| Tests unitarios y funcionales | pytest + pytest-cov | Push o pull request |
| Cobertura mínima 60 % | pytest-cov | CI bloquea si baja del umbral |
| Calidad mínima 8.0/10 | pylint | CI bloquea si baja del umbral |
| Build de imagen | Dockerfile + Docker Compose | Local y CI |
| Release | GitHub Actions | Tag `vX.Y.Z` |

Los pipelines viven en:

- `.github/workflows/ci.yml` — Tests, lint, calidad y cobertura.
- `.github/workflows/cd.yml` — Build y publicación de artefactos al crear un tag.

## Entornos

| Entorno | URL | Base de datos | Notas |
| --- | --- | --- | --- |
| Local | http://localhost:8000 | PostgreSQL en contenedor | Para desarrollo y evaluación |
| CI | Efímero en GitHub Actions | PostgreSQL en contenedor | Para tests automáticos |
| Producción | A definir por el equipo | PostgreSQL gestionado o contenedor persistente | Requiere SMTP real y secretos seguros |

## Despliegue local

Caso de uso típico: un evaluador clona el repositorio y necesita verlo funcionando con Docker Compose.

```bash
git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git
cd NewsRadar
docker compose up -d --build
```

Este comando construye y levanta los servicios necesarios:

- API de NewsRadar
- Base de datos PostgreSQL
- MailHog para pruebas de correo

Comprobación final:

```bash
curl http://localhost:8000/api/v1/health
```

Respuesta esperada:

```json
{"status":"ok","timestamp":"..."}
```

URLs principales:

| Servicio | URL |
| --- | --- |
| Frontend | http://localhost:8000 |
| Swagger / OpenAPI | http://localhost:8000/docs |
| ReDoc | http://localhost:8000/redoc |
| MailHog | http://localhost:8025 |

Credenciales por defecto:

```text
Email: admin@newsradar.com
Contraseña: admin123
```

## Ejecutar pruebas

Con los contenedores levantados:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

Cobertura mínima exigida: **60 %**.

Para ejecutar la verificación externa proporcionada en Magistral:

```bash
cd devops_verifica-main
python run_tests.py --all
```

También se puede indicar explícitamente la URL del servicio:

```bash
python run_tests.py --service http://localhost:8000 --all
```

## Despliegue en CI/CD

Cada push o pull request ejecuta el pipeline CI:

1. Lint y calidad de código.
2. Tests unitarios y funcionales.
3. Validación del umbral mínimo de cobertura.
4. Validación del umbral mínimo de calidad.
5. Build de la imagen Docker.

Para publicar una versión:

```bash
git tag -a v1.0.0 -m "Release 1.0.0 — entrega final"
git push origin v1.0.0
```

El pipeline CD se dispara automáticamente al crear un tag con formato `vX.Y.Z`.

## Rollback

Para volver manualmente a una versión anterior:

```bash
docker compose down
git checkout v0.9.0
docker compose pull
docker compose up -d --build
```

Después verificar:

```bash
curl http://localhost:8000/api/v1/health
```

Si el health check responde correctamente, el rollback se considera completado.

## Monitorización y logs

Ver logs en tiempo real de la API:

```bash
docker compose logs -f api
```

Ver logs de todos los servicios:

```bash
docker compose logs -f
```

Ver estado de los contenedores:

```bash
docker compose ps
```

Ver uso de recursos:

```bash
docker stats
```

Para producción real conviene integrar con una solución de monitorización como Prometheus, Grafana, ELK o similar, pero queda fuera del alcance académico del proyecto.

## Backup y restauración

### Backup de la base de datos

```bash
docker compose exec db pg_dump -U newsradar newsradar > backup_$(date +%Y%m%d).sql
```

### Restauración

```bash
cat backup_20260420.sql | docker compose exec -T db psql -U newsradar newsradar
```

## Troubleshooting

### Docker Desktop no está iniciado

En Windows puede aparecer:

```text
failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine
```

Solución:

1. Abrir Docker Desktop.
2. Esperar a que el motor esté iniciado.
3. Reintentar el comando `docker compose`.

### El despliegue falla con `port already allocated`

Identificar quién usa el puerto:

```bash
sudo lsof -i :8000
```

En Windows:

```powershell
netstat -ano | findstr :8000
```

Después, detener el proceso conflictivo o cambiar el puerto en `docker-compose.yml`.

### Los tests fallan en CI pero pasan en local

Suele ser un problema de variables de entorno o de inicialización de servicios. Verifica que `.github/workflows/ci.yml` define todas las variables necesarias y que PostgreSQL está disponible antes de ejecutar los tests.

### La cobertura baja inesperadamente

Generar informe detallado:

```bash
docker compose exec api pytest --cov=app --cov-report=html
```

El informe HTML se genera en:

```text
newsradar_api/htmlcov/index.html
```

### Imágenes Docker corruptas o entorno inconsistente

Limpiar recursos Docker locales:

```bash
docker compose down -v
docker system prune -af --volumes
docker compose up -d --build
```

## Checklist de despliegue para producción

Antes de pasar a producción real:

- Cambiar `SECRET_KEY` por un valor seguro.
- Cambiar credenciales de PostgreSQL.
- Usar volúmenes persistentes o una base de datos gestionada.
- Sustituir MailHog por un SMTP real.
- Configurar HTTPS con certificado válido.
- Activar logs estructurados.
- Definir política de backup automatizado.
- Revisar reglas de CORS.
- Revisar permisos y credenciales del usuario administrador.
