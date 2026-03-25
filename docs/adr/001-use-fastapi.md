# ADR 001: Use FastAPI for REST API

## Status
Accepted

## Context
We need to build a REST API for the NewsRadar system that:
- Provides OpenAPI documentation
- Supports async operations for RSS fetching
- Has good performance
- Is easy to develop and maintain
- Has strong typing support

## Decision
We will use FastAPI as the web framework for our REST API.

## Consequences

### Positive
- Automatic OpenAPI/Swagger documentation generation
- Native async/await support for better performance
- Pydantic integration for request/response validation
- Type hints provide better IDE support and catch errors early
- Fast development with automatic data validation
- Built-in dependency injection system
- Active community and good documentation

### Negative
- Relatively newer framework (less mature than Flask/Django)
- Smaller ecosystem compared to Django
- Team needs to learn async programming patterns

## Alternatives Considered
- **Django REST Framework**: More mature but heavier, less performant for async operations
- **Flask**: Simpler but requires more manual setup for OpenAPI docs and validation
- **Express.js (Node.js)**: Would require different tech stack, team has Python expertise
