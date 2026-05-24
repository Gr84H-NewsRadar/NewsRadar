# NewsRadar — Ejemplos de uso del API

Este documento contiene ejemplos básicos para probar la API REST de NewsRadar desde terminal usando `curl`.

La documentación interactiva completa está disponible con la aplicación levantada en:

```text
http://localhost:8000/docs
```

## Requisitos previos

Antes de ejecutar estos ejemplos, levanta la aplicación desde la raíz del proyecto:

```bash
docker compose up -d --build
```

La API estará disponible en:

```text
http://localhost:8000
```

## Health check

Comprueba que la API está funcionando:

```bash
curl http://localhost:8000/api/v1/health
```

Respuesta esperada:

```json
{
  "status": "ok",
  "timestamp": "..."
}
```

## Login

Obtén un token JWT usando el usuario administrador por defecto:

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin@newsradar.com&password=admin123"
```

La respuesta incluye un `access_token`.

Ejemplo:

```json
{
  "access_token": "<TOKEN>",
  "token_type": "bearer"
}
```

Para los siguientes ejemplos, guarda el token en una variable:

### Linux / macOS

```bash
TOKEN="<TOKEN>"
```

### Windows PowerShell

```powershell
$TOKEN="<TOKEN>"
```

## Registro de usuario

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "usuario@example.com",
    "password": "password123",
    "first_name": "Usuario",
    "last_name": "Demo",
    "organization": "UC3M"
  }'
```

Los nuevos usuarios se crean con rol gestor por defecto. El rol `admin` existe para administración del sistema.

## Listar categorías IPTC

```bash
curl http://localhost:8000/api/v1/categories
```

## Listar fuentes de información

```bash
curl http://localhost:8000/api/v1/information-sources
```

## Listar noticias

```bash
curl http://localhost:8000/api/v1/news
```

Con búsqueda por texto:

```bash
curl "http://localhost:8000/api/v1/news?q=tecnologia"
```

Con filtro por categoría:

```bash
curl "http://localhost:8000/api/v1/news?category_id=1"
```

Con rango de fechas:

```bash
curl "http://localhost:8000/api/v1/news?date_from=2026-01-01&date_to=2026-12-31"
```

## Consultar estadísticas del dashboard

```bash
curl http://localhost:8000/api/v1/dashboard/stats
```

## Consultar nube de palabras

Nube de palabras global:

```bash
curl http://localhost:8000/api/v1/dashboard/wordcloud
```

Nube de palabras por categoría:

```bash
curl "http://localhost:8000/api/v1/dashboard/wordcloud?category_id=1"
```

## Crear una alerta

Ejemplo usando autenticación con token.

### Linux / macOS

```bash
curl -X POST http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Alerta tecnología",
    "keyword": "inteligencia artificial",
    "category_id": 1,
    "notify_email": true,
    "notify_inbox": true,
    "cron_expression": "0 */6 * * *"
  }'
```

### Windows PowerShell

```powershell
curl.exe -X POST http://localhost:8000/api/v1/users/1/alerts `
  -H "Authorization: Bearer $TOKEN" `
  -H "Content-Type: application/json" `
  -d "{
    `"name`": `"Alerta tecnología`",
    `"keyword`": `"inteligencia artificial`",
    `"category_id`": 1,
    `"notify_email`": true,
    `"notify_inbox`": true,
    `"cron_expression`": `"0 */6 * * *`"
  }"
```

## Listar alertas de un usuario

```bash
curl http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer $TOKEN"
```

## Procesar canales RSS manualmente

Fuerza el procesamiento manual de canales RSS:

```bash
curl -X POST http://localhost:8000/api/v1/process-rss \
  -H "Authorization: Bearer $TOKEN"
```

Este proceso puede generar:

- Nuevas noticias.
- Clasificación en categorías IPTC.
- Notificaciones en el buzón interno.
- Correos capturados por MailHog.

## Consultar MailHog

Los correos enviados en local se capturan en MailHog:

```text
http://localhost:8025
```

## Ejecutar tests de API

Con los contenedores levantados:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

Para ejecutar las pruebas externas de verificación:

```bash
cd devops_verifica-main
python run_tests.py --all
```

O indicando explícitamente la URL del servicio:

```bash
python run_tests.py --service http://localhost:8000 --all
```

## Detener el entorno

```bash
docker compose down
```

Para detener y borrar volúmenes:

```bash
docker compose down -v
```
