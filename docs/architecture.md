# NewsRadar Architecture

## System Overview

NewsRadar is a news monitoring system built with a microservices-oriented architecture using modern DevOps practices.

## Architecture Diagram

```
┌─────────────┐
│   Frontend  │
│   (React)   │
└──────┬──────┘
       │ HTTP/REST
       ▼
┌─────────────┐
│   API       │
│  (FastAPI)  │
└──────┬──────┘
       │
       ├──────────┐
       │          │
       ▼          ▼
┌──────────┐  ┌──────────┐
│PostgreSQL│  │ MailHog  │
│          │  │  (SMTP)  │
└──────────┘  └──────────┘
```

## Components

### 1. API Layer (FastAPI)
- RESTful API with OpenAPI documentation
- JWT-based authentication
- Role-based access control (Manager/Reader)
- Request validation with Pydantic

### 2. Business Logic Layer
- RSS feed processing
- Alert matching engine
- Synonym recommendation service
- Email notification service
- News classification (IPTC categories)

### 3. Data Layer
- PostgreSQL for production
- SQLite for development
- SQLAlchemy ORM
- Alembic for migrations

### 4. Background Processing
- APScheduler for cron jobs
- Async RSS feed fetching
- Batch news processing

## Data Model

### Core Entities

1. **User**
   - Authentication and profile
   - Role assignments
   - Email verification

2. **Role**
   - Manager: Full access
   - Reader: Read-only access
   - Admin: System administration

3. **Alert**
   - Keywords and synonyms
   - Category filters
   - RSS channel selection
   - Notification preferences

4. **InformationSource**
   - Media outlet information
   - Multiple RSS channels

5. **RSSChannel**
   - Feed URL
   - Category assignment
   - Fetch status

6. **NewsItem**
   - Title, link, description
   - Publication date
   - Category classification
   - Alert matching

7. **Notification**
   - Alert-based notifications
   - Email and inbox delivery
   - Processing statistics

8. **Category**
   - IPTC Media Topics
   - First-level categories

## Security

- Password hashing with bcrypt
- JWT tokens with expiration
- Email verification required
- Role-based authorization
- Input validation and sanitization

## Scalability Considerations

- Stateless API design
- Database connection pooling
- Async I/O for RSS fetching
- Horizontal scaling ready
- Docker containerization

## Monitoring and Logging

- Structured logging
- Processing statistics
- Error tracking
- Health check endpoints

## Technology Stack

- **Backend**: Python 3.11, FastAPI
- **Database**: PostgreSQL 15
- **ORM**: SQLAlchemy 2.0
- **Authentication**: python-jose, passlib
- **Email**: aiosmtplib
- **RSS**: feedparser
- **Testing**: pytest, httpx
- **Containerization**: Docker, Docker Compose
- **CI/CD**: GitHub Actions
