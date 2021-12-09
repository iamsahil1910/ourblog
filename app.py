import os
from flask import Flask, request, render_template, redirect, session, flash
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



# Set up database
engine = create_engine("postgresql:///temp")
db = scoped_session(sessionmaker(bind=engine))

@app.route('/')
def hello():

    blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()
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

app.config["UPLOAD_PATH"] = '/static/images'

@app.route('/admin', methods=['GET', 'POST'])
def admin():

    if session.get("user_id") is None:

        return redirect('/login')

    if request.method == "GET":

        blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()


        return render_template('admin.html', blogs=blogs)

    else:
        if not request.form.get("title"):
            return render_template("admin.html", message = "Title Missing")
        if not request.form.get("name"):
            return render_template("admin.html", message = "Name Missing")
        if not request.form.get("content"):
            return render_template("admin.html", message = "Content Missing")
        file = request.files['filename']
        filename = secure_filename(file.filename)
        
        file.save(os.path.join('static/images/',filename))

        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
       
        print(request.form.get("filename"))
        db.execute("INSERT INTO blog (title, user_id, date, content, img, name) VALUES(:title, :user_id, :date, :content, :img, :name)", {
            'title': request.form.get("title"), 'user_id': session["user_id"], 'date': time, 'content': request.form.get("content"), 'img': secure_filename(file.filename), 'name': request.form.get('name')
        })

        db.commit()

        return redirect('/admin')
        
        
@app.route('/blog/<int:blog_id>')
def blog(blog_id):

    blog = db.execute("SELECT * FROM blog WHERE blog_id = :blog_id", {'blog_id': blog_id}).fetchone()
    count = db.execute("SELECT COUNT(*) FROM blog").fetchone()
    recent_blogs = ''
    if count[0] < 5:
        recent_blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()
    else:
        recent_blogs = db.execute("SELECT * FROM blog LIMT 5 ORDER BY blog_id DESC").fetchall()

    return render_template('blog.html', blog=blog, recent_blogs=recent_blogs)


@app.route('/delete-blog', methods=['GET', 'POST'])
def delete_blog():

    if session.get("user_id") is None:

        return redirect('/login')

    if request.method == "GET":

        return '''
                <h2>Not a right way to come here</h2>
                <a href="/">Go to Home page</a>
            '''

    else:

        blog_id = int(request.form.get("blog"))

        db.execute("DELETE FROM blog WHERE blog_id = :blog_id", {
            'blog_id': blog_id
        })

        db.commit()
        flash('One Blog Deleted!')

        return redirect('/admin')
@app.route("/search",methods=["GET", "POST"])
def search():
    if request.method =="POST":
        if not request.form.get("search"):
           return render_template("search.html", message = " Enter something for search")
        row = db.execute("SELECT * FROM blog WHERE LOWER(title)  LIKE :query " , {'query': '%' + request.form.get("search").lower() + '%'}).fetchall()
    
        if len(row)==0:
            return render_template('search.html', message = 'No Result Found')
       

        return render_template("search.html",row=row)


if(__name__ == "__main__"):
    app.run(debug = True, port=8080)
    



