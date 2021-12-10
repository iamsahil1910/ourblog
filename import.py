from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker


engine = create_engine("postgresql:///temp")
db = scoped_session(sessionmaker(bind=engine))

def main():
    # Create table to import data into
    db.execute("CREATE TABLE admin (user_id  SERIAL PRIMARY KEY, username VARCHAR(30), password VARCHAR(30))")
    db.execute("CREATE TABLE blog (blog_id SERIAL PRIMARY KEY, title VARCHAR NOT NULL, user_id INTEGER, date DATE, content VARCHAR, img VARCHAR, name VARCHAR NOT NULL)")
    db.execute("CREATE TABLE comments (id SERIAL PRIMARY KEY, name VARCHAR NOT NULL, comment VARCHAR NOT NULL, date DATE, blog_id INTEGER NOT NULL REFERENCES blog(blog_id) ON DELETE CASCADE)")
    db.execute("CREATE TABLE likes (id INT PRIMARY KEY, likes_count INTEGER)")

    db.execute("INSERT INTO admin (username, password) VALUES(:username, :password)", {'username': 'admin', 'password': 'admin'})
    db.commit()
if __name__ == "__main__":
    main()
