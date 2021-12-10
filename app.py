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

        blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()

        if not request.form.get("title"):
            return render_template("admin.html", message = "Title Missing", blogs=blogs)
        if not request.form.get("name"):
            return render_template("admin.html", message = "Name Missing", blogs=blogs)
        if not request.form.get("content"):
            return render_template("admin.html", message = "Content Missing", blogs=blogs)

        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        filename = 'NULL'
        if (request.files['filename']):
            types = ['image/png', 'image/jpg', 'image/jpeg']
            file = request.files['filename']
            filename = secure_filename(file.filename)
            filetype = file.content_type
            filename = str(time) + filename
            if not filetype in types:
                return render_template("admin.html", message = "File/Image type not allowed", blogs=blogs)
            
            file.save(os.path.join('static/images/',filename))
       
        db.execute("INSERT INTO blog (title, user_id, date, content, img, name) VALUES(:title, :user_id, :date, :content, :img, :name)", {
            'title': request.form.get("title"), 'user_id': session["user_id"], 'date': time, 'content': request.form.get("content"), 'img': filename, 'name': request.form.get('name')
        })

        db.commit()

        flash('New Blog Added')
        return redirect('/admin')
        
        
@app.route('/blog/<int:blog_id>')
def blog(blog_id):

    blog = db.execute("SELECT * FROM blog WHERE blog_id = :blog_id", {'blog_id': blog_id}).fetchone()

    if blog == None:
        flash("No blog with that id")
        return redirect("/")

    count = db.execute("SELECT COUNT(*) FROM blog").fetchone()
    recent_blogs = ''
    if count[0] < 5:
        recent_blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()
    else:
        recent_blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC LIMIT 5").fetchall()

    comments = db.execute("SELECT * FROM comments WHERE blog_id = :blog_id ORDER BY id DESC", {
        'blog_id': blog_id
    }).fetchall()
    
    comments_count = len(comments)

    if (comments_count > 5):
        comments_count = 5

    return render_template('blog.html', blog=blog, recent_blogs=recent_blogs, comments=comments, comments_count=comments_count)


@app.route('/delete-blog', methods=['GET', 'POST'])
def delete_blog():

    if session.get("user_id") is None:
        flash('To delele please login as admin')
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

        
@app.route("/search",methods=['GET', 'POST'])
def search():

    if request.method == "POST":

        if not request.form.get("search"):
           return render_template("search.html", message = "No Query Provided")

        row = db.execute("SELECT * FROM blog WHERE LOWER(title)  LIKE :query " , {'query': '%' + request.form.get("search").lower() + '%'}).fetchall()
    
        if len(row) == 0:
            return render_template('search.html', query=request.form.get("search"))
    
        return render_template("search.html", row=row, query=request.form.get("search"))


@app.route("/edit/<int:blog_id>")
def edit(blog_id):

    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    blog = db.execute("SELECT * FROM blog WHERE blog_id = :blog_id", {
        'blog_id': blog_id
    }).fetchone()

    return render_template('edit.html', blog=blog)

        


@app.route("/edit-blog", methods=["POST"])
def edit_blog():

    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    if not request.form.get("title"):
        return render_template("edit.html", message = "Title Missing")

    if not request.form.get("content"):
        return render_template("edit.html", message = "Content Missing")

    blog_id = request.form.get("blog_id")

    db.execute("UPDATE blog SET title = :title, content = :content WHERE blog_id = :blog_id", {
        'blog_id': blog_id, 'title': request.form.get("title"), 'content': request.form.get("content")
    })

    db.commit()

    flash('Blog is updated!')

    return redirect('/blog/' + str(blog_id))


@app.route('/comment', methods=['POST'])
def comment():

    if not request.form.get("name"):
        flash("Sorry, Annoymous comments are not allowed.")
        return redirect("/")
    if not request.form.get("comment"):
        flash("Comment was empty")
        return redirect("/")

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    db.execute("INSERT INTO comments (name, comment, date, blog_id) VALUES(:name, :comment, :date, :blog_id)",{
        'name': request.form.get("name"), 'comment': request.form.get("comment"), 'date': time, 'blog_id': request.form.get("blog_id") 
    })

    db.commit()

    flash("You comment is posted")

    return redirect("/blog/" + str(request.form.get("blog_id")))


@app.route('/delete-comment', methods=['POST'])
def delete_comment():

    comment_id = request.form.get("comment_id")
    blog_id = request.form.get("blog_id")

    db.execute("DELETE FROM comments WHERE id = :comment_id", {
        'comment_id': comment_id
    })

    db.commit()

    flash('One Comment Deleted')

    return redirect('/blog/' + str(blog_id))


@app.route('/change-image', methods=['POST'])
def change_image():

    old_image = request.form.get("old-img")
    blog_id = request.form.get("blog_id")

    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    filename = 'NULL'
    if (request.files['filename']):
        types = ['image/png', 'image/jpg', 'image/jpeg']
        file = request.files['filename']
        filename = secure_filename(file.filename)
        filetype = file.content_type
        filename = str(time) + filename

        if not filetype in types:
            flash('Invalid File/Image Type')
            return redirect("/blog/" + str(blog_id))

    if not old_image == "NULL":
        
        os.remove(os.path.join('static/images/', old_image))

    file.save(os.path.join('static/images/',filename))

    db.execute("UPDATE blog SET img = :filename WHERE blog_id = :blog_id", {
       'filename': filename, 'blog_id': blog_id
    })

    db.commit()

    flash('Image Changed')
    return redirect("/blog/" + str(blog_id))

    

if(__name__ == "__main__"):
    app.run(debug = True, port=8080)
    



