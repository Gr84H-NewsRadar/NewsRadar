# NewsRadar — Arquitectura

## Visión general

NewsRadar es un sistema de monitorización de noticias en medios de comunicación y fuentes oficiales. La aplicación escucha canales RSS, clasifica noticias en categorías IPTC, permite configurar alertas por palabras clave y envía notificaciones al usuario cuando se detectan coincidencias.

La arquitectura sigue un enfoque por capas y se despliega localmente mediante Docker Compose.

## Diagrama de arquitectura

```text
┌──────────────────────────────────────────────┐
│              Usuario / Navegador             │
└──────────────────────┬───────────────────────┘
                       │ HTTP
                       ▼
┌──────────────────────────────────────────────┐
│          Capa de presentación                │
│  HTML / JavaScript / Bootstrap en /static    │
└──────────────────────┬───────────────────────┘
                       │ REST
                       ▼
┌──────────────────────────────────────────────┐
│              Capa API REST                   │
│                  FastAPI                     │
│        OpenAPI disponible en /docs           │
└──────────────────────┬───────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────┐
│          Capa de lógica de negocio           │
│  Autenticación, alertas, RSS, clasificación, │
│  sinónimos, notificaciones y dashboard       │
└───────────────┬──────────────────────┬───────┘
                │                      │
                ▼                      ▼
┌────────────────────────────┐   ┌────────────────────────────┐
│      Capa de persistencia  │   │      Servicio de correo     │
│ SQLAlchemy + PostgreSQL    │   │ MailHog SMTP en desarrollo  │
└────────────────────────────┘   └────────────────────────────┘
```

## Componentes principales

### 1. Capa de presentación

La interfaz de usuario se sirve desde FastAPI como contenido estático en `/static`.

Incluye las pantallas principales de:

- Login y registro.
- Dashboard.
- Gestión de alertas.
- Gestión de fuentes y canales RSS.
- Visualización de noticias.
- Nubes de palabras.
- Buzón de notificaciones.
- Perfil de usuario.

### 2. Capa API REST

La API está implementada con FastAPI y expone endpoints REST documentados automáticamente con OpenAPI.

La documentación interactiva está disponible en:

```text
http://localhost:8000/docs
```

También está disponible ReDoc en:

```text
http://localhost:8000/redoc
```

Responsabilidades principales:

- Autenticación y registro de usuarios.
- Gestión de usuarios y roles.
- Gestión de alertas.
- Gestión de fuentes de información.
- Gestión de canales RSS.
- Consulta de noticias.
- Consulta de categorías IPTC.
- Consulta de estadísticas del dashboard.
- Consulta de nubes de palabras.
- Gestión de notificaciones.

### 3. Capa de lógica de negocio

Contiene las reglas principales del sistema:

- Procesamiento de canales RSS.
- Detección de noticias coincidentes con alertas.
- Expansión de descriptores mediante sinónimos o palabras relacionadas.
- Clasificación de noticias en categorías IPTC.
- Generación de notificaciones internas.
- Envío de notificaciones por correo.
- Cálculo de estadísticas globales.
- Generación de datos para nubes de palabras.

### 4. Capa de persistencia

La persistencia se implementa con SQLAlchemy sobre PostgreSQL.

PostgreSQL almacena:

- Usuarios.
- Roles.
- Categorías IPTC.
- Alertas.
- Fuentes de información.
- Canales RSS.
- Noticias.
- Notificaciones.
- Datos de verificación y estado de procesamiento.

### 5. Servicios auxiliares

El entorno local se despliega con Docker Compose e incluye:

| Servicio | Descripción | Puerto |
| --- | --- | --- |
| `api` | Aplicación FastAPI y frontend estático | 8000 |
| `db` | Base de datos PostgreSQL 15 | 5432 |
| `mailhog` | Captura de correos en desarrollo | 1025 / 8025 |

MailHog permite verificar correos sin enviarlos realmente al exterior.

## Modelo de datos principal

### User

Representa a un usuario de la plataforma.

Campos y responsabilidades principales:

- Email.
- Nombre y apellidos.
- Organización.
- Contraseña hasheada.
- Estado de verificación.
- Rol asociado.

### Role

Representa los roles del sistema.

Según la adenda del enunciado, el rol lector desaparece como rol operativo. Los nuevos usuarios se crean como gestores automáticamente, aunque el API debe seguir permitiendo la creación y asignación de roles. El rol `admin` debe existir.

Roles principales:

- `admin`: administración del sistema.
- `manager`: usuario gestor de NewsRadar.

### Alert

Representa una alerta configurada por un usuario gestor.

Incluye:

- Nombre de la alerta.
- Palabra clave principal.
- Descriptores relacionados.
- Categoría IPTC.
- Canales RSS asociados.
- Configuración de notificación por correo.
- Configuración de notificación por buzón interno.
- Expresión cron de monitorización.

### InformationSource

Representa un medio de comunicación o fuente oficial.

Ejemplos:

- RTVE.
- El País.
- ABC.
- El Confidencial.
- Marca.
- La Moncloa.

### RSSChannel

Representa un canal RSS perteneciente a una fuente de información.

Incluye:

- URL del feed.
- Fuente asociada.
- Categoría IPTC.
- Estado de actividad.

### NewsItem

Representa una noticia capturada desde un canal RSS.

Incluye:

- Título.
- Enlace.
- Resumen o descripción.
- Fecha de publicación.
- Fuente.
- Canal RSS.
- Categoría IPTC.
- Relación con alertas coincidentes.

### Notification

Representa una notificación generada cuando una noticia coincide con una alerta.

Puede entregarse mediante:

- Buzón interno.
- Correo electrónico.

### Category

Representa una categoría IPTC Media Topics de primer nivel.

Se usa para:

- Clasificar alertas.
- Clasificar canales RSS.
- Clasificar noticias.
- Filtrar estadísticas y nubes de palabras.

## Seguridad

La seguridad se basa en:

- Hashing de contraseñas con bcrypt.
- Autenticación mediante JWT.
- Caducidad de tokens.
- Verificación de correo electrónico.
- Control de acceso por rol.
- Validación de datos mediante Pydantic.
- Separación entre endpoints públicos y endpoints protegidos.

## Procesamiento RSS

El procesamiento de noticias sigue este flujo:

```text
Canal RSS
   │
   ▼
Lectura del feed
   │
   ▼
Extracción de noticias
   │
   ▼
Comparación con alertas activas
   │
   ▼
Clasificación IPTC
   │
   ▼
Persistencia en PostgreSQL
   │
   ▼
Generación de notificaciones
   │
   ├──► Buzón interno
   └──► Correo vía MailHog / SMTP
```

## Despliegue

El despliegue local se realiza con Docker Compose:

```bash
docker compose up -d --build
```

Este comando levanta:

- API FastAPI.
- PostgreSQL.
- MailHog.

Para detener el sistema:

```bash
docker compose down
```

Para limpiar también los volúmenes:

```bash
docker compose down -v
```

## Calidad, pruebas y CI/CD

El proyecto incluye automatización mediante GitHub Actions.

El pipeline de CI valida:

- Instalación de dependencias.
- Análisis de calidad con pylint.
- Tests con pytest.
- Cobertura con pytest-cov.
- Construcción de la imagen Docker.

Los tests internos pueden ejecutarse con:

```bash
docker compose exec api pytest -v --cov=app --cov-report=term-missing
```

La cobertura mínima exigida es del **60 %**.

La calidad mínima esperada con pylint es superior a **8.0/10**.

## Escalabilidad y evolución

El sistema está preparado para evolucionar en varias direcciones:

- Sustituir MailHog por un proveedor SMTP real.
- Ejecutar PostgreSQL como base de datos gestionada.
- Separar el procesamiento RSS en workers independientes.
- Añadir colas de mensajes para procesamiento asíncrono.
- Incorporar métricas externas con Prometheus o Grafana.
- Añadir despliegue en un entorno cloud.

## Decisiones arquitectónicas

Las decisiones arquitectónicas principales están documentadas en `docs/adr/`:

- ADR 001: Uso de FastAPI como framework.
- ADR 002: Uso de PostgreSQL como sistema de persistencia.
- ADR 003: Despliegue mediante Docker.
