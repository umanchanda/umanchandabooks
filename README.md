# umanchandabooks

A Flask book review web app backed by PostgreSQL. Users can search a catalog of books, leave ratings and comments, and see community ratings sourced from the Open Library API.

## Features

- User registration and login with hashed passwords
- Search books by title, author, ISBN, or year
- Submit and update reviews (rating + comments) per book
- Community average rating per book
- `/api/<isbn>` JSON endpoint returning book metadata and Open Library ratings
- Session-based authentication

## Tech stack

- **Framework**: Flask
- **Database**: PostgreSQL (via SQLAlchemy 2.0)
- **Package management**: uv
- **External API**: [Open Library](https://openlibrary.org/developers/api)
- **Deployment**: Gunicorn

## Setup

### Prerequisites

- [uv](https://docs.astral.sh/uv/)
- A PostgreSQL database (e.g. [Neon](https://neon.tech))

### Install dependencies

```bash
uv sync
```

### Environment variables

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string |

### Seed the database

Run once to populate the `books` table by fetching from the Open Library API:

```bash
DATABASE_URL=<your-db-url> uv run python import.py
```

### Run locally

```bash
DATABASE_URL=<your-db-url> uv run flask --app application run
```
