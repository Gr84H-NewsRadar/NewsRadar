# ADR 002: Uso de PostgreSQL como base de datos principal

## Estado

Aceptado

## Contexto

NewsRadar necesita un sistema de persistencia para almacenar entidades relacionadas entre sí, como usuarios, roles, alertas, fuentes de información, canales RSS, noticias, categorías IPTC y notificaciones.

El sistema de base de datos debe cumplir los siguientes requisitos:

- Gestionar datos relacionales con integridad referencial.
- Soportar relaciones entre usuarios, alertas, fuentes, canales, noticias y notificaciones.
- Ofrecer garantías ACID.
- Funcionar correctamente con SQLAlchemy.
- Poder ejecutarse en local mediante Docker Compose.
- Ser adecuado para un posible despliegue en producción.
- Permitir consultas eficientes para dashboard, filtros y estadísticas.

## Decisión

Se utilizará **PostgreSQL** como base de datos principal de NewsRadar.

En el entorno local, PostgreSQL se ejecuta como servicio Docker definido en `docker-compose.yml`.

El servicio de base de datos se levanta junto con la API y MailHog mediante:

```bash
docker compose up -d --build
```

## Consecuencias

### Positivas

- Sistema gestor de base de datos robusto y maduro.
- Buen soporte para datos relacionales e integridad referencial.
- Garantías ACID.
- Buen rendimiento para consultas y filtros.
- Integración directa con SQLAlchemy.
- Disponible como imagen Docker oficial.
- Adecuado para desarrollo local, CI y despliegues más cercanos a producción.
- Facilita mantener el mismo tipo de base de datos en distintos entornos.

### Negativas

- Requiere levantar un servicio adicional frente a alternativas embebidas como SQLite.
- Consume más recursos que una base de datos ligera.
- Requiere gestionar volúmenes de datos en Docker.
- Puede necesitar tareas de backup, restauración y mantenimiento en entornos persistentes.

## Alternativas consideradas

### SQLite

Base de datos ligera y sencilla de usar. Se descartó como base principal porque no representa bien un entorno de producción, tiene limitaciones de concurrencia y no es la mejor opción para un sistema con múltiples entidades relacionadas y despliegue mediante contenedores.

### MySQL / MariaDB

Sistemas relacionales maduros y ampliamente utilizados. Se descartaron porque PostgreSQL ofrece una integración muy sólida con SQLAlchemy, buen soporte para consultas complejas y características avanzadas útiles para evolución futura.

### MongoDB

Base de datos NoSQL flexible. Se descartó porque el dominio de NewsRadar contiene muchas relaciones claras entre entidades, y una base de datos relacional permite mantener mejor la integridad de usuarios, alertas, noticias, canales, fuentes y notificaciones.

## Estado de implementación

PostgreSQL está definido como servicio `db` en `docker-compose.yml`.

La aplicación FastAPI se conecta a PostgreSQL mediante SQLAlchemy y almacena en él las entidades principales del sistema.
