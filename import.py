import os
import csv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import scoped_session, sessionmaker

if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

database_url = os.getenv("DATABASE_URL")
if database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)

engine = create_engine(database_url)
db = scoped_session(sessionmaker(bind=engine))

with open('books.csv', 'r') as books:
    reader = csv.reader(books)
    next(reader)
    for row in reader:
        db.execute(text("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)"), {'isbn': row[0], 'title': row[1], 'author': row[2], 'year': row[3]})
    db.commit()
