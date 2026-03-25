# ADR 002: Use PostgreSQL as Primary Database

## Status
Accepted

## Context
We need a reliable database system that can:
- Handle relational data with complex relationships
- Support JSON fields for flexible data storage
- Scale for production workloads
- Provide ACID guarantees
- Work well with SQLAlchemy ORM

## Decision
We will use PostgreSQL as the primary database for production, with SQLite for development and testing.

## Consequences

### Positive
- Robust and mature RDBMS with excellent reliability
- Native JSON/JSONB support for flexible schema
- Strong ACID compliance
- Excellent performance for read-heavy workloads
- Great tooling and monitoring options
- Free and open source
- Works seamlessly with SQLAlchemy

### Negative
- Requires separate database server (more complex deployment)
- Higher resource usage than SQLite
- Need to manage database migrations

## Alternatives Considered
- **MySQL**: Similar features but PostgreSQL has better JSON support
- **MongoDB**: NoSQL would simplify some queries but lose relational integrity
- **SQLite only**: Too limited for production use, no concurrent writes
