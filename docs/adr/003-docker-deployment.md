# ADR 003: Despliegue mediante Docker Compose

## Estado

Aceptado

## Contexto

NewsRadar necesita un mecanismo de despliegue que permita construir y ejecutar el sistema de forma reproducible en una máquina limpia.

El sistema está formado por varios servicios:

- API FastAPI y frontend estático.
- Base de datos PostgreSQL.
- Servicio MailHog para capturar correos en desarrollo y verificación.

El enunciado del proyecto exige que un evaluador pueda clonar el repositorio, construir el sistema, ejecutar las pruebas, desplegar la aplicación y ejecutarla con la mínima intervención manual posible.

Además, el despliegue debe integrarse con los pipelines de CI/CD y ser portable entre entornos de desarrollo.

## Decisión

Se utilizará **Docker** para contenerizar la aplicación y **Docker Compose** para orquestar los servicios necesarios en local.

El despliegue local se realiza desde la raíz del proyecto con:

```bash
docker compose up -d --build
```

Este comando construye la imagen de la API y levanta los servicios definidos en `docker-compose.yml`.

Los servicios principales son:

| Servicio | Descripción | Puerto |
| --- | --- | --- |
| `api` | Aplicación FastAPI y frontend estático | 8000 |
| `db` | PostgreSQL 15 | 5432 |
| `mailhog` | Captura de correos en local | 1025 / 8025 |

## Consecuencias

### Positivas

- Entorno reproducible en distintas máquinas.
- Menos problemas de dependencias locales.
- La API, la base de datos y MailHog se levantan de forma coordinada.
- Facilita la verificación por parte de evaluadores.
- Permite ejecutar pruebas dentro del mismo entorno que la aplicación.
- Se integra correctamente con GitHub Actions.
- Facilita limpiar y recrear el entorno mediante volúmenes Docker.

### Negativas

- Requiere tener Docker Desktop o Docker Engine instalado.
- En Windows es necesario que Docker Desktop esté iniciado antes de ejecutar `docker compose`.
- Consume más recursos que ejecutar la aplicación directamente en local.
- Requiere conocer comandos básicos de Docker Compose.
- Hay que gestionar volúmenes para preservar o limpiar los datos de PostgreSQL.

## Alternativas consideradas

### Ejecución local sin contenedores

Consistiría en instalar Python, PostgreSQL y dependencias directamente en la máquina del usuario. Se descartó porque aumenta el riesgo de diferencias entre entornos, problemas de versiones y configuración manual.

### Máquinas virtuales

Proporcionan aislamiento, pero son más pesadas, tardan más en arrancar y complican el flujo de desarrollo frente a Docker.

### Kubernetes

Es una opción válida para sistemas de mayor escala, pero se considera excesiva para el alcance académico y local del proyecto. Docker Compose cubre suficientemente las necesidades actuales.

## Operaciones habituales

Levantar el sistema:

```bash
docker compose up -d --build
```

Ver el estado de los servicios:

```bash
docker compose ps
```

Ver logs de la API:

```bash
docker compose logs -f api
```

Ejecutar pruebas internas:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

Detener el sistema:

```bash
docker compose down
```

Detener el sistema y borrar volúmenes:

```bash
docker compose down -v
```

## Estado de implementación

El repositorio incluye un archivo `docker-compose.yml` en la raíz.

Este archivo define los servicios necesarios para ejecutar NewsRadar en local:

- `api`
- `db`
- `mailhog`

La documentación de ejecución se encuentra en:

- `README.md`
- `docs/quickstart.md`
- `docs/deployment.md`
