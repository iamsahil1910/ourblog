import os
from flask import Flask, request, render_template, redirect, session
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

UPLOAD_FOLDER = '/static/images/'

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# Set up database
engine = create_engine("postgresql:///temp")
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')
def hello():

    blogs = db.execute("SELECT * FROM blog;").fetchall()
    print(blogs)

    return render_template('index.html', blogs=blogs)

@app.route("/login", methods=['GET', 'POST'])
def login():

    session.clear()

    if request.method == "GET":

        return render_template("login.html")

    else:

        if not request.form.get("username"):
            return render_template("login.html", message = "Username Missing")
        if not request.form.get("password"):
            return render_template("login.html", message = "Password Missing")

        row = db.execute("SELECT * FROM admin WHERE username = :username AND password = :password" , {'username': request.form.get("password"), 'password': request.form.get("username")}).fetchone()
        
        if row == None:
            return render_template('login.html', message = 'Wrong Username or Password')
        session["user_id"] = row["user_id"]

        return redirect("/admin")


@app.route('/logout')
def logout():
    session.clear()

    return redirect('/login')

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if session.get("user_id") is None:

        return redirect('/login')

    if request.method == "GET":

        return render_template('admin.html')

    else:
        if not request.form.get("title"):
            return render_template("admin.html", message = "Title Missing")
        if not request.form.get("name"):
            return render_template("admin.html", message = "Name Missing")
        # if not request.form.get("filename"):
        #     return render_template("admin.html", message = "File Missing")
        if not request.form.get("content"):
            return render_template("admin.html", message = "Content Missing")
        file = request.files['filename']
        print(file)
        filename = secure_filename(file.filename)
        file.save(filename)

        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
        print(request.form.get("filename"))
        db.execute("INSERT INTO blog (title, user_id, date, content, img, name) VALUES(:title, :user_id, :date, :content, :img, :name)", {
            'title': request.form.get("title"), 'user_id': session["user_id"], 'date': time, 'content': request.form.get("content"), 'img': secure_filename(file.filename), 'name': request.form.get('name')
        })

        db.commit()

        return redirect('/admin')
        
        

        
@app.route('/blog')
def blog():
    return render_template('blog.html')


if(__name__ == "__main__"):
    app.run(debug = True)
    



