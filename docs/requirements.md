# NewsRadar — Especificación final de requisitos

## Requisitos funcionales

| ID | Requisito | Implementación | Pruebas |
| --- | --- | --- | --- |
| RF01 | Registro de usuarios con correo, nombre, apellidos y organización | `auth.py`, `main.py`, `models.py` | `test_api.py::test_register` |
| RF02 | Login mediante usuario y contraseña | `auth.py`, endpoint `/api/v1/auth/login` | `test_api.py::test_login` |
| RF03 | Gestión de alertas por usuario | Endpoints `/api/v1/users/{id}/alerts` | `test_api.py::test_alerts_*` |
| RF04 | Recomendación de sinónimos o descriptores relacionados | `synonym_service.py` | `test_api.py::test_synonyms` |
| RF05 | Gestión de fuentes de información y canales RSS | Endpoints de fuentes y canales RSS | `test_api.py::test_sources_*` |
| RF06 | Procesamiento de canales RSS | `rss_processor.py` | `test_api.py::test_rss` |
| RF07 | Clasificación de noticias en categorías IPTC | `models.py`, `rss_processor.py`, `main.py` | Tests funcionales de API |
| RF08 | Uso de categorías IPTC de primer nivel | `Category`, datos iniciales | Tests funcionales y verificación manual |
| RF09 | Generación de notificaciones por alerta | `rss_processor.py`, `models.py` | `test_api.py::test_notifications` |
| RF10 | Notificaciones por buzón interno y correo | `email_service.py`, `Notification` | Tests funcionales y MailHog |
| RF11 | Gestión de usuarios y roles | `auth.py`, `models.py`, endpoints de usuarios/roles | `test_api.py::test_rbac` |
| RF12 | Dashboard con estadísticas globales | `main.py`, `dashboard.html` | Tests funcionales y verificación manual |
| RF13 | Nubes de palabras por categoría | `main.py`, `wordcloud.html` | Verificación manual |
| RF14 | Interfaz gráfica de usuario | `app/static/` | Verificación manual |
| RF15 | API REST documentada con OpenAPI | FastAPI `/docs` y `/redoc` | Verificación manual |

## Requisitos no funcionales

| ID | Requisito | Implementación |
| --- | --- | --- |
| RNF01 | Despliegue reproducible | Docker Compose |
| RNF02 | Base de datos persistente | PostgreSQL 15 |
| RNF03 | Documentación versionada | `README.md`, `docs/`, `docs/adr/` |
| RNF04 | Integración continua | `.github/workflows/ci.yml` |
| RNF05 | Empaquetado y distribución | `.github/workflows/cd.yml` |
| RNF06 | Cobertura mínima del 60 % | `pytest-cov` |
| RNF07 | Calidad mínima 8.0/10 | `pylint` |
| RNF08 | API documentada | OpenAPI generado por FastAPI |
| RNF09 | Configuración de entorno | `.env.example`, Docker Compose |
| RNF10 | Trazabilidad | README, documentación y tabla de requisitos |
