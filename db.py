import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

database_url = os.getenv("DATABASE_URL", "")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url, pool_pre_ping=True)
db = scoped_session(sessionmaker(bind=engine))


def init_db():
    try:
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS books (
                isbn   TEXT PRIMARY KEY,
                title  TEXT NOT NULL,
                author TEXT,
                year   TEXT
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password TEXT NOT NULL
            )
        """))
        db.execute(text("""
            CREATE TABLE IF NOT EXISTS reviews (
                username TEXT NOT NULL REFERENCES users(username),
                isbn     TEXT NOT NULL REFERENCES books(isbn),
                rating   INTEGER,
                comments TEXT,
                PRIMARY KEY (username, isbn)
            )
        """))
        db.execute(text("ALTER TABLE books ADD COLUMN IF NOT EXISTS genre TEXT"))
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.remove()
