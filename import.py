import os
import time
import requests
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

SUBJECTS = [
    'fiction', 'science_fiction', 'mystery', 'biography',
    'history', 'fantasy', 'romance', 'thriller', 'horror',
    'poetry', 'philosophy', 'science', 'travel', 'cooking',
]
BOOKS_PER_SUBJECT = 400

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
db = scoped_session(sessionmaker(bind=engine))

# Ensure the `books` table exists before inserting
db.execute(
    text(
        """
        CREATE TABLE IF NOT EXISTS books (
            isbn TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            author TEXT,
            year TEXT
        )
        """
    )
)
db.commit()

seen_isbns = set()
total = 0

for subject in SUBJECTS:
    print(f"Fetching subject: {subject}")
    res = requests.get(
        "https://openlibrary.org/search.json",
        params={
            "subject": subject,
            "fields": "isbn,title,author_name,first_publish_year",
            "limit": BOOKS_PER_SUBJECT,
        },
        timeout=15,
    )
    res.raise_for_status()

    for doc in res.json().get("docs", []):
        isbns = doc.get("isbn", [])
        if not isbns:
            continue
        isbn = isbns[0]
        if isbn in seen_isbns:
            continue

        title = doc.get("title", "")
        authors = doc.get("author_name", [])
        author = authors[0] if authors else "Unknown"
        year = str(doc.get("first_publish_year", ""))

        if not all([isbn, title, year]):
            continue

        seen_isbns.add(isbn)
        db.execute(
            text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year) ON CONFLICT (isbn) DO NOTHING"),
            {"isbn": isbn, "title": title, "author": author, "year": year},
        )
        total += 1

    db.commit()
    print(f"  {total} books inserted so far")
    time.sleep(1)  # be polite to Open Library's API

print(f"Done. {total} books inserted.")
