# NewsRadar — Guía Rápida de Inicio

> Despliega NewsRadar en local usando Docker Compose.

## Requisitos previos

- Docker Desktop ≥ 24.0
- Docker Compose ≥ 2.20
- Git ≥ 2.40
- Python 3.10 o superior
- 4 GB RAM libres
- Puertos libres: 8000 (API), 5432 (Postgres), 1025 y 8025 (MailHog)

> En Windows es necesario tener Docker Desktop iniciado antes de ejecutar `docker compose`.

## Despliegue en 4 pasos

### 1) Clonar el repositorio

```bash
git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git
cd NewsRadar
```

### 2) Añadir la carpeta de verificación

Copiar la carpeta `devops_verifica-main` proporcionada en Magistral dentro de la raíz del proyecto.

La estructura debe quedar de forma similar a:

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

### 3) Levantar todos los servicios

Desde la raíz del proyecto:

```bash
docker compose up --build
```

También se puede ejecutar en segundo plano:

```bash
docker compose up -d --build
```

Este comando construye y levanta los servicios necesarios:

- API de NewsRadar
- Base de datos PostgreSQL
- MailHog para pruebas de correo

### 4) Verificar que todo funciona

```bash
curl http://localhost:8000/api/v1/health
```

Respuesta esperada:

```json
{"status":"ok","timestamp":"..."}
```

## Acceso al sistema

| Servicio              | URL                                    | Notas                                |
| --------------------- | -------------------------------------- | ------------------------------------ |
| Frontend              | http://localhost:8000                  | Interfaz web                         |
| API REST              | http://localhost:8000/api/v1           | Endpoints REST                       |
| Documentación Swagger | http://localhost:8000/docs             | OpenAPI interactiva                  |
| Documentación ReDoc   | http://localhost:8000/redoc            | Vista alternativa                    |
| MailHog               | http://localhost:8025                  | Buzón de correos de prueba           |

## Credenciales por defecto

Al levantar el sistema por primera vez, se crea automáticamente:

- **Email**: `admin@newsradar.com`
- **Contraseña**: `admin123`
- **Rol**: `admin`

## Ejecutar pruebas internas

Con los contenedores levantados:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

Cobertura mínima exigida: **60 %**.

## Ejecutar pruebas de verificación

Con la aplicación ya levantada, abrir otra terminal y entrar en la carpeta de verificación:

```bash
cd devops_verifica-main
```

Ejecutar todas las pruebas:

```bash
python run_tests.py --all
```

También se puede indicar explícitamente la URL del servicio:

```bash
python run_tests.py --service http://localhost:8000 --all
```

## Procesar canales RSS manualmente

Por defecto, NewsRadar procesa los canales RSS según una expresión cron por alerta. Para forzar un procesamiento inmediato y poblar la base de datos con noticias, primero obtén un token:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@newsradar.com&password=admin123"
```

Después llama al endpoint con el token obtenido:

```bash
curl -X POST http://localhost:8000/api/v1/process-rss \
  -H "Authorization: Bearer <TOKEN>"
```

## Detener el sistema

Para detener los contenedores manteniendo los datos:

```bash
docker compose down
```

Para detener los contenedores y borrar también los volúmenes:

```bash
docker compose down -v
```

## Solución de problemas frecuentes

| Síntoma                                      | Causa probable                                      | Solución                                                                       |
| -------------------------------------------- | --------------------------------------------------- | ------------------------------------------------------------------------------ |
| `failed to connect to the docker API`        | Docker Desktop no está iniciado                     | Abre Docker Desktop y espera a que esté iniciado                               |
| `port is already allocated`                  | Otro proceso usa el puerto 8000 o 5432              | Detén el proceso o cambia el puerto en `docker-compose.yml`                    |
| Login devuelve 401                           | El admin no se ha creado todavía                    | Espera unos segundos tras el primer arranque                                   |
| Dashboard vacío                              | No hay noticias procesadas todavía                  | Ejecuta `POST /api/v1/process-rss` o espera al cron                            |
| `connection refused` al hacer health check   | Los contenedores aún están arrancando               | Ejecuta `docker compose ps` y espera unos segundos                             |
| Word cloud no muestra nada                   | Hay pocas noticias en la base de datos              | Procesa más canales RSS                                                        |

## Siguiente paso

Una vez levantado, accede a http://localhost:8000 e inicia sesión con las credenciales de administrador.

Para documentación más detallada del despliegue en distintos entornos, CI/CD, rollback y troubleshooting, ver [`docs/deployment.md`](deployment.md).
