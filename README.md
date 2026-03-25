# 📰 NEWSRADAR - Sistema de Monitorización de Noticias

> Sistema completo de monitorización de noticias en medios de comunicación y fuentes oficiales

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![License](https://img.shields.io/badge/license-MIT-blue.svg)]()
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116-green.svg)]()

---

## 🚀 Inicio Rápido

### Windows
```bash
# Doble click en:
INICIO_RAPIDO.bat
```

### Linux/Mac
```bash
chmod +x inicio_rapido.sh
./inicio_rapido.sh
```

### Acceso
- **API**: http://localhost:8000
- **Documentación**: http://localhost:8000/docs
- **Email Testing**: http://localhost:8025

**Credenciales**: `admin@newsradar.com` / `admin123`

---

## 📖 Documentación

### 🎯 Empieza Aquí
- **[EMPEZAR_AQUI.md](EMPEZAR_AQUI.md)** ⭐ - Tu primer paso
- **[GUIA_COMPLETA.md](GUIA_COMPLETA.md)** - Guía detallada paso a paso
- **[EJEMPLOS_API.md](EJEMPLOS_API.md)** - Ejemplos de uso de la API
- **[VERIFICACION.md](VERIFICACION.md)** - Cómo verificar que funciona
- **[INDICE_DOCUMENTACION.md](INDICE_DOCUMENTACION.md)** - Índice completo

### 📚 Más Documentación
- **[RESUMEN_FINAL.md](RESUMEN_FINAL.md)** - Resumen del proyecto
- **[PROJECT_STATUS.md](PROJECT_STATUS.md)** - Estado del proyecto
- **[DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)** - Checklist de despliegue
- **[docs/](docs/)** - Documentación técnica y ADRs

---

## Descripción

NEWSRADAR es un sistema completo que permite:
- Monitorizar canales RSS de múltiples medios de comunicación
- Crear alertas basadas en palabras clave
- Clasificar noticias según categorías IPTC
- Recibir notificaciones por email y en la aplicación
- Visualizar estadísticas y análisis en un dashboard

## Arquitectura

El sistema está compuesto por:
- **Backend API**: FastAPI con Python 3.11
- **Base de datos**: PostgreSQL (producción) / SQLite (desarrollo)
- **Frontend**: React (próximamente)
- **Email**: MailHog para desarrollo
- **Contenedores**: Docker y Docker Compose

## Requisitos Previos

- Docker y Docker Compose
- Python 3.11+ (para desarrollo local)
- Node.js 18+ (para frontend)

## Instalación y Ejecución

### Opción 1: Docker Compose (Recomendado)

```bash
# Clonar el repositorio
git clone <repository-url>
cd newsradar

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f api
```

La API estará disponible en: http://localhost:8000
Documentación Swagger: http://localhost:8000/docs
MailHog UI: http://localhost:8025

### Opción 2: Desarrollo Local

```bash
# Backend
cd newsradar_api
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload

# La API estará en http://localhost:8000
```

## Uso

### 1. Autenticación

Usuario administrador por defecto:
- Email: `admin@newsradar.com`
- Password: `admin123`

```bash
# Login
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@newsradar.com","password":"admin123"}'

# Respuesta: {"access_token":"...","token_type":"bearer"}
```

### 2. Crear una Alerta

```bash
curl -X POST http://localhost:8000/api/v1/users/1/alerts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Crisis Energética",
    "keywords": ["energía", "electricidad", "gas"],
    "category_code": "04000000",
    "notify_email": true
  }'
```

### 3. Gestionar Fuentes RSS

```bash
# Listar fuentes
curl -X GET http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer <token>"

# Crear fuente
curl -X POST http://localhost:8000/api/v1/information-sources \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "El País",
    "url": "https://elpais.com"
  }'
```

## Estructura del Proyecto

```
newsradar/
├── docker-compose.yml
├── README.md
├── newsradar_api/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models.py
│   │   ├── schemas.py
│   │   ├── auth.py
│   │   ├── email_service.py
│   │   ├── rss_processor.py
│   │   ├── synonym_service.py
│   │   └── init_db.py
│   └── tests/
└── newsradar_frontend/
    └── (próximamente)
```

## API Endpoints

### Autenticación
- `POST /api/v1/auth/register` - Registrar usuario
- `POST /api/v1/auth/login` - Iniciar sesión
- `GET /api/v1/auth/me` - Obtener usuario actual

### Usuarios
- `GET /api/v1/users` - Listar usuarios
- `GET /api/v1/users/{id}` - Obtener usuario
- `PUT /api/v1/users/{id}` - Actualizar usuario
- `DELETE /api/v1/users/{id}` - Eliminar usuario

### Alertas
- `GET /api/v1/users/{user_id}/alerts` - Listar alertas
- `POST /api/v1/users/{user_id}/alerts` - Crear alerta
- `GET /api/v1/users/{user_id}/alerts/{id}` - Obtener alerta
- `PUT /api/v1/users/{user_id}/alerts/{id}` - Actualizar alerta
- `DELETE /api/v1/users/{user_id}/alerts/{id}` - Eliminar alerta

### Fuentes de Información
- `GET /api/v1/information-sources` - Listar fuentes
- `POST /api/v1/information-sources` - Crear fuente
- `GET /api/v1/information-sources/{id}` - Obtener fuente
- `PUT /api/v1/information-sources/{id}` - Actualizar fuente
- `DELETE /api/v1/information-sources/{id}` - Eliminar fuente

### Canales RSS
- `GET /api/v1/information-sources/{source_id}/rss-channels` - Listar canales
- `POST /api/v1/information-sources/{source_id}/rss-channels` - Crear canal
- `GET /api/v1/information-sources/{source_id}/rss-channels/{id}` - Obtener canal
- `PUT /api/v1/information-sources/{source_id}/rss-channels/{id}` - Actualizar canal
- `DELETE /api/v1/information-sources/{source_id}/rss-channels/{id}` - Eliminar canal

### Categorías
- `GET /api/v1/categories` - Listar categorías IPTC
- `POST /api/v1/categories` - Crear categoría
- `GET /api/v1/categories/{id}` - Obtener categoría

### Noticias
- `GET /api/v1/news` - Listar noticias
- `GET /api/v1/news/{id}` - Obtener noticia

### Notificaciones
- `GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications` - Listar notificaciones
- `GET /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}` - Obtener notificación
- `PUT /api/v1/users/{user_id}/alerts/{alert_id}/notifications/{id}` - Marcar como leída

### Estadísticas
- `GET /api/v1/stats` - Obtener estadísticas globales
- `GET /api/v1/dashboard/stats` - Estadísticas del dashboard

## Testing

```bash
cd newsradar_api
pytest tests/ -v
```

## CI/CD

El proyecto incluye configuración para GitHub Actions con:
- Tests automáticos
- Análisis de código con SonarQube
- Generación de cobertura
- Build de contenedores Docker

## Contribuir

1. Fork el proyecto
2. Crear una rama feature (`git checkout -b feature/AmazingFeature`)
3. Commit cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abrir un Pull Request

## Licencia

Este proyecto es parte del curso "Desarrollo y operación de sistemas software" de la Universidad Carlos III de Madrid.

## Contacto

Proyecto Final - NEWSRADAR
Universidad Carlos III de Madrid
