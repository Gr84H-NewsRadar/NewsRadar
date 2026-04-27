## Issue #21: Empaquetado y Distribución (CD)

### Descripción
Configuración completa del pipeline de Continuous Deployment (CD) para empaquetado y distribución del sistema. Permite generar releases versionadas en Docker con capacidad de rollback rápido.

### Criterios de Aceptación Completados

#### 1. cd.yml Genera Imagen Docker al Hacer Tag/Release

El workflow `.github/workflows/cd.yml` se dispara automáticamente cuando haces push de un tag de versión:

```yaml
on:
  push:
    tags:
      - 'v[0-9]+.[0-9]+.[0-9]+'
```

Jobs del pipeline:

**build-release:**
- Extrae la versión del tag (v1.0.0 → 1.0.0)
- Construye imagen Docker: `docker build -t newsradar:1.0.0`
- Comprime y guarda: `newsradar-1.0.0.tar.gz`
- Genera notas de release con fecha, commit y repo
- Crea GitHub Release con artefactos adjuntos

**verify-build:**
- Descarga el artefacto de release
- Verifica que la imagen existe y está completa
- Valida integridad del tarball

#### 2. Versiones Etiquetadas con Git Tags

Formato de versionado: `v[MAJOR].[MINOR].[PATCH]`

Ejemplos: `v1.0.0`, `v1.0.1`, `v1.1.0`, `v2.0.0`

**Crear un tag:**
```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Primera versión estable"
```

**Listar tags existentes:**
```bash
git tag -l 'v*'
```

**Disparar CD pipeline:**
```bash
git push origin v1.0.0
```

Esto hace que GitHub Actions ejecute automáticamente `.github/workflows/cd.yml` y genere la imagen Docker.

#### 3. Rollback a Versión Anterior en < 15 Minutos

Script `scripts/rollback.sh` disponible para revertir rápidamente:

**Listar versiones disponibles:**
```bash
./scripts/rollback.sh
```

**Ejecutar rollback:**
```bash
./scripts/rollback.sh v1.0.0
```

**Que hace el script:**
1. Valida que el tag existe
2. Descarga el tag del repositorio
3. Compila imagen Docker desde ese tag
4. Detiene contenedores actuales
5. Inicia versión anterior
6. Verifica health checks
7. Confirma éxito

**Tiempo total:** ~3-5 minutos (muy por debajo del límite de 15 min)

### Flujo Completo (End-to-End)

```
1. Desarrollador hace cambios de código
   └─> git commit -m "feature: nueva funcionalidad"

2. Push a main/develop
   └─> GitHub Actions ejecuta CI (.github/workflows/ci.yml)
       ├─ lint (ruff, black, isort)
       ├─ test (pytest con cobertura)
       └─ code-quality (pylint, radon)
       └─ build (docker compose build)

3. Cuando listo para liberar:
   └─> git tag -a v1.0.0 -m "Release v1.0.0"
   └─> git push origin v1.0.0

4. GitHub Actions ejecuta CD (.github/workflows/cd.yml)
   ├─ build-release
   │  └─ Construye imagen Docker newsradar:1.0.0
   │  └─ Genera tarball newsradar-1.0.0.tar.gz
   │  └─ Crea GitHub Release
   └─ verify-build
      └─ Verifica integridad

5. Si hay problema:
   └─> ./scripts/rollback.sh v0.9.0
   └─> Revierte a versión anterior en <5 minutos
```

### Archivos Modificados/Creados

- `.github/workflows/cd.yml` — Pipeline CD que dispara en tags
- `scripts/rollback.sh` — Script de rollback rápido

### Variables de Entorno

No requiere variables de entorno especiales. Usa `GITHUB_TOKEN` (disponible automáticamente en Actions).

### Cómo Usar en Local

**Ver qué versiones están disponibles:**
```bash
git tag -l 'v*' | sort -V
```

**Crear una versión:**
```bash
git tag -a v1.0.0 -m "Release v1.0.0 - Descripción"
```

**Disparar CD en GitHub (requiere push):**
```bash
git push origin v1.0.0
```

**Revertir en caso de problema:**
```bash
chmod +x scripts/rollback.sh
./scripts/rollback.sh v1.0.0
```

### Artefactos Generados

Después de cada tag/release, disponible en GitHub > Releases:

- `newsradar-v1.0.0.tar.gz` — Imagen Docker comprimida
- `RELEASE_NOTES.txt` — Notas con fecha, commit, repo

También está disponible en GitHub Actions > Artifacts durante 90 días.

### Health Checks

Después de rollback o deploy, el script verifica:

```bash
curl -f http://localhost:8000/api/v1/health
```

Si retorna 200 OK, deployment es exitoso. Si falla, script aborta.

### Monitoreo y Validación

**Ver estado de CD pipeline:**
1. Ir a GitHub > Actions > CD Pipeline
2. Ver ejecución del job
3. Revisar logs de build-release y verify-build

**Validar que rollback funcionó:**
```bash
docker images | grep newsradar
docker ps  # Ver contenedor corriendo la versión anterior
```

### Futuro (Opcional)

Para mejorar (no es requisito):
- Publicar imagen en Docker Hub o registry privado
- Agregar deploy automático a staging/producción
- Notificaciones en Slack/Teams cuando release se crea
- Automatizar versionado semántico (semantic versioning)
- Health checks más profundos post-deploy

### Troubleshooting

**Tag no dispara CD:**
- Verificar que formato es `v[0-9]+.[0-9]+.[0-9]+` (exactamente)
- Hacer `git push origin v1.0.0` (push el tag también, no solo commits)

**Rollback falla:**
- Verificar Docker está corriendo: `docker ps`
- Verificar tag existe: `git tag -l | grep v1.0.0`
- Ver logs: `docker compose logs -f`

**Health check falla post-rollback:**
- Esperar más tiempo (servicios pueden tardar en iniciar)
- Verificar puerto 8000 no esté en uso: `lsof -i :8000`
- Ver logs del contenedor: `docker compose logs api`
