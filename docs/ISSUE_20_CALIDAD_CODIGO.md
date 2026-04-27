## Issue #20: Métricas de Calidad del Código

### Descripción
Integración de análisis de calidad de código con herramientas open source y gratuitas en el pipeline CI. El build falla automáticamente si la calidad cae por debajo de los umbrales definidos.

### Criterios de Aceptación Completados

#### 1. Configuración de Análisis de Calidad
Se implementó un stack gratuito de herramientas en `.github/workflows/ci.yml`:

- **ruff**: Detección de bugs y errores críticos (E, F)
- **pylint**: Análisis profundo de code smells y complejidad
- **radon**: Métricas de complejidad ciclomática y mantenibilidad
- **pytest-cov**: Cobertura de código

#### 2. Integración en Pipeline CI

El job `code-quality` corre después de `test` en el workflow:

```yaml
code-quality:
  runs-on: ubuntu-latest
  needs: test
  steps:
    - ruff check app              # Bugs y errores críticos
    - pylint app --rcfile=.pylintrc --fail-under=8.0
    - radon cc app -s -a          # Complejidad
```

El job `build` depende de ambos `test` y `code-quality`:

```yaml
build:
  needs: [test, code-quality]  # Falla si code-quality no pasa
```

#### 3. Métricas Visibles

**Bugs y errores críticos:**
- ruff genera reportes de errores de síntaxis, imports no usados, etc.
- Reportes guardados en `quality-reports/ruff.txt`

**Code Smells:**
- pylint analiza líneas largas, complejidad de funciones, variables no usadas
- Configuración en `newsradar_api/.pylintrc`
- Reportes guardados en `quality-reports/pylint.txt`

**Duplicación:**
- pylint con flag `--enable=R0801` detecta código duplicado
- radon genera reporte de complejidad ciclomática

**Cobertura:**
- pytest-cov genera cobertura de tests en XML
- Descargado desde CI artifact en job code-quality
- Umbral mínimo: 60% (configurable con env var COVERAGE_MIN)

#### 4. Build Falla si Calidad Cae

El pipeline detiene automáticamente si:

- Cobertura < 60% (COVERAGE_MIN env var)
- Score de pylint < 8.0 (PYLINT_MIN_SCORE env var)
- ruff detecta errores críticos

Ejemplo: Un push con coverage 55% causa:
```
pytest ... --cov-fail-under=60
FAILED: coverage is 55% (minimum 60%)
Job: test FAILED
Build stops
```

### Archivos Modificados

- `.github/workflows/ci.yml`: Jobs lint, test, code-quality, build con gates
- `newsradar_api/.pylintrc`: Configuración de reglas pylint
- `newsradar_api/app/config.py`: Limpieza de whitespace y imports
- `newsradar_api/app/main.py`: Limpieza de líneas largas y final newline

### Variables de Entorno (Configurables)

En `.github/workflows/ci.yml`:
```yaml
env:
  COVERAGE_MIN: "60"        # Umbral de cobertura mínima
  PYLINT_MIN_SCORE: "8.0"   # Score pylint mínimo
```

Para cambiar umbrales, editar estos valores y pushear.

### Cómo Ejecutar Localmente

```bash
cd newsradar_api

# Instalar herramientas
pip install ruff pylint radon black isort pytest pytest-cov

# Ejecutar linting
ruff check app
black --check app
isort --check-only app

# Ejecutar quality gates
pylint app --rcfile=.pylintrc --fail-under=8.0
radon cc app -s -a
```

### Cómo Ejecutar Tests con Cobertura

```bash
cd newsradar_api

# Opción 1: SQLite (sin PostgreSQL)
pytest tests/ -v --cov=app --cov-report=term --cov-fail-under=60

# Opción 2: Con PostgreSQL (CI simulado)
export DATABASE_URL="postgresql://newsradar:newsradar123@localhost:5432/newsradar_test"
pytest tests/ -v --cov=app --cov-report=xml
```

### Artefactos Generados en CI

Después de cada push a main/develop, los reportes están disponibles en GitHub Actions > Run > Artifacts:

- `coverage-report`: coverage.xml
- `quality-reports`: ruff.txt, pylint.txt, radon-cc.txt

### Futuro

Para mejorar (opcional):
- Integrar SonarCloud si presupuesto lo permite (scan más profundo)
- Añadir pre-commit hooks locales para correr checks antes de push
- Dashboard de métricas históricas
