# ADR 001: Uso de FastAPI para la API REST

## Estado

Aceptado

## Contexto

NewsRadar necesita exponer una API REST para gestionar usuarios, roles, alertas, fuentes de información, canales RSS, noticias, categorías IPTC, notificaciones y estadísticas del dashboard.

El sistema debe cumplir los siguientes requisitos técnicos:

- Ofrecer documentación OpenAPI de forma automática.
- Permitir validación de datos de entrada y salida.
- Facilitar el desarrollo de endpoints REST.
- Soportar operaciones asíncronas cuando sea necesario.
- Integrarse correctamente con Python, SQLAlchemy y Pydantic.
- Ser adecuado para despliegue mediante Docker.

## Decisión

Se utilizará **FastAPI** como framework principal para implementar la API REST de NewsRadar.

La documentación interactiva de la API estará disponible en:

```text
http://localhost:8000/docs
```

También se expondrá documentación alternativa mediante ReDoc:

```text
http://localhost:8000/redoc
```

## Consecuencias

### Positivas

- Generación automática de documentación OpenAPI/Swagger.
- Integración nativa con Pydantic para validación de datos.
- Buen soporte para anotaciones de tipos de Python.
- Soporte para programación asíncrona con `async`/`await`.
- Desarrollo rápido de endpoints REST.
- Sistema de inyección de dependencias integrado.
- Buena integración con pruebas mediante `pytest` y `httpx`.
- Encaja con el despliegue mediante Docker Compose.

### Negativas

- Es un framework más reciente que alternativas como Django.
- El equipo debe mantener disciplina en la organización del código para evitar concentrar demasiada lógica en los endpoints.
- El uso de operaciones asíncronas requiere cuidado para evitar mezclar código bloqueante con código async.

## Alternativas consideradas

### Django REST Framework

Framework muy maduro y con amplio ecosistema. Se descartó por ser más pesado para el alcance del proyecto y porque FastAPI proporciona documentación OpenAPI y validación de datos de forma más directa.

### Flask

Framework simple y flexible. Se descartó porque requiere más configuración manual para validación, documentación OpenAPI, serialización y estructura de API.

### Express.js

Framework popular en Node.js. Se descartó para mantener el stack principal en Python y aprovechar bibliotecas del ecosistema Python para RSS, procesamiento de datos, testing y backend.
