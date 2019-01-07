from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
import csv

engine = create_engine("postgres://wzhyqownmxotta:996a486a693a09dc9427b75e4787782c71f51ee2416c860b0f753f0dcaadc097@ec2-107-20-250-113.compute-1.amazonaws.com:5432/d3lpaali8o0um2")
db = scoped_session(sessionmaker(bind=engine))

with open('books.csv', 'r') as books:
    reader = csv.reader(books)
    next(reader)
    for row in reader:
        db.execute("INSERT INTO books (isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {'isbn': row[0], 'title':row[1], 'author': row[2], 'year': row[3]})
    db.commit()