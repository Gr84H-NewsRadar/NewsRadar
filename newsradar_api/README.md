# NewsRadar API

API REST de NewsRadar implementada con FastAPI y versionada bajo `/api/v1`.

Este directorio contiene la aplicación backend principal del proyecto, incluyendo:

- Endpoints REST.
- Modelos de datos.
- Esquemas Pydantic.
- Servicios de lógica de negocio.
- Procesamiento RSS.
- Servicio de notificaciones.
- Frontend estático servido por FastAPI.
- Tests internos.

## Ejecución recomendada

La forma recomendada de ejecutar el proyecto completo es desde la raíz del repositorio mediante Docker Compose:

```bash
docker compose up -d --build
```

No es necesario crear un entorno virtual ni ejecutar manualmente `uvicorn` para la ejecución normal del proyecto.

## URLs principales

Con los contenedores levantados, la aplicación estará disponible en:

```text
http://localhost:8000
```

Documentación interactiva Swagger/OpenAPI:

```text
http://localhost:8000/docs
```

Documentación ReDoc:

```text
http://localhost:8000/redoc
```

OpenAPI JSON:

```text
http://localhost:8000/openapi.json
```

Health check:

```bash
curl http://localhost:8000/api/v1/health
```

## Credenciales por defecto

Usuario administrador inicial:

```text
Email: admin@newsradar.com
Contraseña: admin123
```

## Autenticación

El login se realiza mediante:

```text
POST /api/v1/auth/login
```

El endpoint devuelve un token JWT. Para acceder a endpoints protegidos, se debe enviar el token en la cabecera `Authorization`:

```text
Authorization: Bearer <TOKEN>
```

Ejemplo de login:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@newsradar.com&password=admin123"
```

## Flujo de URLs principales

| Recurso | Endpoint |
| --- | --- |
| Health check | `GET /api/v1/health` |
| Login | `POST /api/v1/auth/login` |
| Registro | `POST /api/v1/auth/register` |
| Usuarios | `GET /api/v1/users` |
| Alertas de usuario | `GET /api/v1/users/{user_id}/alerts` |
| Crear alerta | `POST /api/v1/users/{user_id}/alerts` |
| Categorías IPTC | `GET /api/v1/categories` |
| Fuentes de información | `GET /api/v1/information-sources` |
| Canales RSS de una fuente | `GET /api/v1/information-sources/{source_id}/rss-channels` |
| Noticias | `GET /api/v1/news` |
| Estadísticas del dashboard | `GET /api/v1/dashboard/stats` |
| Nube de palabras | `GET /api/v1/dashboard/wordcloud` |
| Procesamiento RSS manual | `POST /api/v1/process-rss` |

## Entidades principales

- Usuarios.
- Roles.
- Alertas.
- Categorías IPTC.
- Notificaciones.
- Fuentes de información.
- Canales RSS.
- Noticias.
- Estadísticas del dashboard.

## Ejecutar tests internos

Con los contenedores levantados desde la raíz del repositorio:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

## Calidad de código

Con los contenedores levantados:

```bash
docker compose exec api pylint app/
```

El score esperado es superior a **8.0/10**.

## Estructura principal

```text
newsradar_api/
├── app/
│   ├── auth.py
│   ├── config.py
│   ├── database.py
│   ├── email_service.py
│   ├── init_db.py
│   ├── main.py
│   ├── models.py
│   ├── rss_processor.py
│   ├── schemas.py
│   ├── synonym_service.py
│   └── static/
├── tests/
├── Dockerfile
└── requirements.txt
```

## Nota sobre ejecución local directa

La ejecución directa con Python y `uvicorn` puede utilizarse para depuración puntual, pero no es el flujo recomendado para evaluación ni entrega.

El flujo oficial del proyecto es ejecutar desde la raíz del repositorio:

```bash
docker compose up -d --build
```
