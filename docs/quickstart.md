# NewsRadar — Guía Rápida de Inicio

> Despliega NewsRadar de cero a en marcha en menos de 5 minutos.

## Requisitos previos

- Docker Desktop ≥ 24.0
- Docker Compose ≥ 2.20
- Git ≥ 2.40
- 4 GB RAM libres
- Puertos libres: 8000 (API), 5432 (Postgres), 1025 y 8025 (MailHog)

## Despliegue en 4 pasos

### 1) Clonar el repositorio

```bash
git clone https://github.com/Gr84H-NewsRadar/NewsRadar.git
cd NewsRadar
```

### 2) Configurar variables de entorno

```bash
cp newsradar_api/.env.example newsradar_api/.env
```

El fichero `.env` ya viene con valores por defecto válidos para entorno local. Para producción cambia `SECRET_KEY` y las credenciales de la base de datos.

### 3) Levantar todos los servicios

Con `make` (recomendado):

```bash
make build
make run
```

Sin `make` (Windows / sistemas sin Make):

```bash
docker-compose up -d --build
```

### 4) Verificar que todo funciona

```bash
# Health check
curl http://localhost:8000/api/v1/health

# Respuesta esperada:
# {"status":"ok","timestamp":"..."}
```

## Acceso al sistema

| Servicio              | URL                                    | Notas                                |
| --------------------- | -------------------------------------- | ------------------------------------ |
| Frontend (Dashboard)  | http://localhost:8000                  | Redirige a /static/index.html        |
| API REST              | http://localhost:8000/api/v1           | Endpoints REST                       |
| Documentación Swagger | http://localhost:8000/docs             | OpenAPI interactiva                  |
| Documentación ReDoc   | http://localhost:8000/redoc            | Vista alternativa                    |
| MailHog (correos)     | http://localhost:8025                  | Buzón de correos de verificación     |

## Credenciales por defecto

Al levantar el sistema por primera vez, se crea automáticamente:

- **Email**: `admin@newsradar.com`
- **Contraseña**: `admin123`
- **Rol**: `admin`

## Ejecutar pruebas

```bash
# Con make
make test

# Con docker-compose directamente
docker-compose exec api pytest -v --cov=app --cov-report=term-missing
```

Cobertura mínima exigida: **60%**.

## Procesar canales RSS manualmente

Por defecto NewsRadar procesa los canales RSS según una expresión cron por alerta. Para forzar un procesamiento inmediato y poblar la base de datos con noticias:

```bash
# Obtén un token primero (login)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=admin@newsradar.com&password=admin123"

# Llama al endpoint con el token
curl -X POST http://localhost:8000/api/v1/process-rss \
  -H "Authorization: Bearer <TOKEN>"
```

## Detener el sistema

```bash
# Detener manteniendo datos
make stop

# Detener y borrar volúmenes (BD limpia)
make clean
```

## Solución de problemas frecuentes

| Síntoma                                             | Causa probable                                     | Solución                                                                                  |
| --------------------------------------------------- | -------------------------------------------------- | ----------------------------------------------------------------------------------------- |
| `port is already allocated`                         | Otro proceso usa el puerto 8000 o 5432             | Detén el proceso o cambia el puerto en `docker-compose.yml`                               |
| Login devuelve 401                                  | El admin no se ha creado todavía (BD nueva)        | Espera 10 segundos al primer arranque para que se ejecute `init_db.py`                    |
| Dashboard vacío                                     | No hay noticias procesadas todavía                 | Ejecuta `POST /api/v1/process-rss` o espera al cron                                       |
| `connection refused` al hacer health check         | Los contenedores aún están arrancando              | `docker-compose ps` para verificar el estado, espera 20-30 s al primer arranque           |
| Word cloud no muestra nada                          | Hay menos de 10 noticias en BD                     | Procesa más canales RSS o reduce el `MIN_FREQUENCY` en `main.py`                          |

## Siguiente paso

Una vez levantado, accede a http://localhost:8000 y verás la pantalla de login. Inicia con las credenciales de admin para configurar fuentes, alertas y empezar a monitorizar.

Para documentación más detallada del despliegue en distintos entornos (CI, producción, rollback), ver [`docs/deployment.md`](deployment.md).
