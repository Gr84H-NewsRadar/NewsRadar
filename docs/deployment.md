# NewsRadar — Guía de Despliegue

Documento de referencia para construir, desplegar, probar, hacer rollback y operar NewsRadar en distintos entornos.

## Tabla de contenidos

1. [Arquitectura del despliegue](#arquitectura-del-despliegue)
2. [Pipeline DevOps](#pipeline-devops)
3. [Scripts disponibles](#scripts-disponibles)
4. [Entornos](#entornos)
5. [Despliegue local](#despliegue-local)
6. [Despliegue en CI/CD](#despliegue-en-cicd)
7. [Rollback](#rollback)
8. [Monitorización y logs](#monitorización-y-logs)
9. [Backup y restauración](#backup-y-restauración)
10. [Troubleshooting](#troubleshooting)

---

## Arquitectura del despliegue

NewsRadar se compone de tres servicios desplegados como contenedores Docker orquestados por Docker Compose:

```
┌───────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   PostgreSQL 15   │◄───┤   FastAPI App    │───►│     MailHog      │
│   :5432           │    │   :8000          │    │   :1025 / :8025  │
└───────────────────┘    └──────────────────┘    └──────────────────┘
                              │
                              └─► Frontend estático (HTML/JS)
                                  servido en /static
```

- **PostgreSQL** persiste usuarios, alertas, fuentes, canales, noticias, notificaciones y stats.
- **FastAPI** expone el API REST y sirve el frontend estático.
- **MailHog** captura los correos en local sin enviar nada al exterior — para producción se sustituye por un SMTP real.

## Pipeline DevOps

| Fase                         | Herramienta                       | Disparador                          |
| ---------------------------- | --------------------------------- | ----------------------------------- |
| Lint / Formato               | pylint, flake8                    | Pre-commit y CI                     |
| Tests unitarios + funcionales| pytest + pytest-cov               | Cada push o PR a `main`/`develop`   |
| Cobertura mínima 60 %        | pytest-cov                        | CI bloquea PR si baja del umbral    |
| Build de imagen              | Dockerfile multi-stage            | CI tras pasar tests                 |
| Empaquetado y publicación    | docker buildx + GHCR              | Tags `vX.Y.Z`                       |
| Despliegue                   | scripts/deploy.sh                 | Manual o webhook tras tag           |
| Rollback                     | scripts/rollback.sh               | Manual ante incidencia              |

Los pipelines viven en:

- `.github/workflows/ci.yml` — Tests, lint y cobertura en cada push/PR.
- `.github/workflows/cd.yml` — Build y push de imagen al crear un tag.

## Scripts disponibles

Todos los scripts están en la carpeta `scripts/` y son ejecutables (`chmod +x`):

| Script              | Propósito                                                          | Tiempo aproximado |
| ------------------- | ------------------------------------------------------------------ | ----------------- |
| `build.sh`          | Construye las imágenes Docker desde cero                           | 1-3 min           |
| `run.sh`            | Levanta el stack completo (postgres + api + mailhog)               | 30 s              |
| `test.sh`           | Ejecuta la suite de tests con cobertura dentro del contenedor      | 1-2 min           |
| `deploy.sh`         | Build + ejecutar migraciones + arrancar en modo desatendido        | 2-3 min           |
| `rollback.sh`       | Vuelve a la versión anterior (tag previo) en menos de 15 min       | 5-10 min          |

Equivalencia con `Makefile` (mismo resultado, distinta forma):

```bash
make build    # = scripts/build.sh
make run      # = scripts/run.sh
make test     # = scripts/test.sh
make deploy   # = scripts/deploy.sh
make rollback # = scripts/rollback.sh
make clean    # detiene y borra volúmenes
```

## Entornos

| Entorno     | URL                       | Base de datos                 | Notas                              |
| ----------- | ------------------------- | ----------------------------- | ---------------------------------- |
| Local       | http://localhost:8000     | Postgres en contenedor        | Para desarrollo                    |
| CI          | (efímero en GitHub)       | Postgres en contenedor        | Solo para correr tests             |
| Producción  | A definir por el equipo   | Postgres gestionado externo   | SMTP real, secretos en vault       |

## Despliegue local

Caso de uso típico: un evaluador clona el repositorio y necesita verlo funcionando con un solo comando.

```bash
git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git
cd NewsRadar
make deploy
```

`make deploy` ejecuta internamente: `build.sh` → `run.sh` → espera al health check.

Comprobación final:

```bash
curl http://localhost:8000/api/v1/health
# {"status":"ok","timestamp":"..."}
```

## Despliegue en CI/CD

Cada push a `main` lanza el pipeline CI completo:

1. Lint y formato.
2. Build de la imagen.
3. Tests con cobertura ≥ 60 %.
4. Si todo pasa, el commit queda listo para tag.

Para publicar una versión:

```bash
git tag -a v1.0.0 -m "Release 1.0.0 — entrega final"
git push origin v1.0.0
```

El pipeline `cd.yml` se dispara automáticamente y publica la imagen en `ghcr.io/gr84h-newsradar/newsradar:v1.0.0`.

## Rollback

Si un despliegue falla o introduce regresiones, hay dos formas de volver atrás:

### Opción 1 — Script automático (recomendado, < 15 min)

```bash
./scripts/rollback.sh v0.9.0
```

Este script:
1. Detiene el stack actual.
2. Hace pull de la imagen de la versión indicada.
3. Restaura el `docker-compose.yml` de esa versión.
4. Vuelve a arrancar el stack.
5. Verifica el health check.

### Opción 2 — Manual

```bash
docker-compose down
git checkout v0.9.0
docker-compose pull
docker-compose up -d
```

## Monitorización y logs

```bash
# Ver logs en tiempo real
docker-compose logs -f api

# Solo errores
docker-compose logs api | grep ERROR

# Estado de los servicios
docker-compose ps

# Métricas básicas
docker stats
```

Para producción real conviene integrar con Prometheus + Grafana, pero queda fuera del alcance del proyecto académico.

## Backup y restauración

### Backup de la base de datos

```bash
docker-compose exec db pg_dump -U newsradar newsradar > backup_$(date +%Y%m%d).sql
```

### Restauración

```bash
cat backup_20260420.sql | docker-compose exec -T db psql -U newsradar newsradar
```

## Troubleshooting

### El despliegue falla con `port already allocated`

```bash
# Identificar quién usa el puerto
sudo lsof -i :8000   # Linux/Mac
netstat -ano | findstr :8000   # Windows

# Cambia el puerto en docker-compose.yml o detén el proceso conflictivo
```

### Los tests fallan en CI pero pasan en local

Suele ser un problema de variables de entorno. Verifica que `.github/workflows/ci.yml` define todas las variables que `pytest` espera. En particular:

- `DATABASE_URL` debe apuntar al servicio postgres del job CI.
- `SECRET_KEY` puede ser cualquier string fijo en CI.

### La cobertura baja inesperadamente

```bash
# Ver el informe detallado
docker-compose exec api pytest --cov=app --cov-report=html
# El HTML se genera en newsradar_api/htmlcov/index.html
```

### Imágenes Docker corruptas

```bash
make clean
docker system prune -af --volumes
make build
```

## Checklist de despliegue para producción

Antes de pasar a producción real (fuera del scope académico, pero documentado):

- Cambiar `SECRET_KEY` por un valor de 64+ caracteres aleatorios.
- Cambiar credenciales de Postgres y usar volumen persistente externo.
- Sustituir MailHog por un SMTP real (SendGrid, Amazon SES, etc.).
- Configurar HTTPS con certificado válido (Let's Encrypt o similar).
- Activar logs estructurados a un agregador (ELK, Datadog).
- Definir política de backup automatizado diario.
- Habilitar autenticación reforzada para el admin (MFA).
- Revisar reglas de CORS para limitar orígenes permitidos.
