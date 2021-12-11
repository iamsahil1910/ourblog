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


# Route for Home page
@app.route('/')
def hello():

    # Get all blogs 
    blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()

    return render_template('index.html', blogs=blogs)


# Route to Login
@app.route("/login", methods=['GET', 'POST'])
def login():

    # Delete session
    session.clear()

    if request.method == "GET":

        return render_template("login.html")

    else:

        # Form validation
        if not request.form.get("username"):
            return render_template("login.html", message = "Username Missing")
        if not request.form.get("password"):
            return render_template("login.html", message = "Password Missing")
        
        # Check if username and password is correct
        row = db.execute("SELECT * FROM admin WHERE username = :username AND password = :password" , {'username': request.form.get("password"), 'password': request.form.get("username")}).fetchone()
        
        if row == None:
            return render_template('login.html', message = 'Wrong Username or Password')

        # Start session (Admin access)
        session["user_id"] = row["user_id"]

        return redirect("/admin")


# Route to logout admin
@app.route('/logout')
def logout():

    # Session clear
    session.clear()

    return redirect('/login')

app.config["UPLOAD_PATH"] = '/static/images'


# Route for admin part (adding blogs) and direct access to delete and edit (admin access)
@app.route('/admin', methods=['GET', 'POST'])
def admin():

    # Check for access (admin access)
    if session.get("user_id") is None:

        return redirect('/login')

    if request.method == "GET":

        # Fetch all blogs
        blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()


        return render_template('admin.html', blogs=blogs)

    else:

        blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()

        # Form Validation
        if not request.form.get("title"):
            return render_template("admin.html", message = "Title Missing", blogs=blogs)
        if not request.form.get("name"):
            return render_template("admin.html", message = "Name Missing", blogs=blogs)
        if not request.form.get("content"):
            return render_template("admin.html", message = "Content Missing", blogs=blogs)

        # Get current time and date
        time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Check if file is being uploaded
        filename = 'NULL'
        if (request.files['filename']):

            types = ['image/png', 'image/jpg', 'image/jpeg']
            file = request.files['filename']
            filename = secure_filename(file.filename)
            filetype = file.content_type
            
            # Modify file name
            filename = str(time) + filename

            # If file is not image give error
            if not filetype in types:
                return render_template("admin.html", message = "File/Image type not allowed", blogs=blogs)
            
            # Save image
            file.save(os.path.join('static/images/',filename))
       
        # Create blog
        db.execute("INSERT INTO blog (title, user_id, date, content, img, name) VALUES(:title, :user_id, :date, :content, :img, :name)", {
            'title': request.form.get("title"), 'user_id': session["user_id"], 'date': time, 'content': request.form.get("content"), 'img': filename, 'name': request.form.get('name')
        })

        db.commit()

        # Show message blog is added
        flash('New Blog Added')
        return redirect('/admin')
        

# Route to view blog       
@app.route('/blog/<int:blog_id>')
def blog(blog_id):

    # Get blogs
    blog = db.execute("SELECT * FROM blog WHERE blog_id = :blog_id", {'blog_id': blog_id}).fetchone()

    # If direct accessed through url with non existing blog give error
    if blog == None:
        flash("No blog with that id")
        return redirect("/")

    # Get blog Counts
    count = db.execute("SELECT COUNT(*) FROM blog").fetchone()
    recent_blogs = ''

    # Check if blogs more than five then return only 5
    if count[0] < 5:
        recent_blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC").fetchall()
    else:
        recent_blogs = db.execute("SELECT * FROM blog ORDER BY blog_id DESC LIMIT 5").fetchall()

    # Get comments
    comments = db.execute("SELECT * FROM comments WHERE blog_id = :blog_id ORDER BY id DESC", {
        'blog_id': blog_id
    }).fetchall()
    
    comments_count = len(comments)

    if (comments_count > 5):
        comments_count = 5

    return render_template('blog.html', blog=blog, recent_blogs=recent_blogs, comments=comments, comments_count=comments_count)


# Route to delete Blog (admin access)
@app.route('/delete-blog', methods=['POST'])
def delete_blog():

    # Its not required for more security check if admin is logged In
    if session.get("user_id") is None:
        flash('To delele please login as admin')
        return redirect('/login')

    # Get blog Id from form
    blog_id = int(request.form.get("blog"))
    old_image = request.form.get("img")
    print(old_image)
    # If there is old image in blog delete it
    if not old_image == "NULL":
        
        os.remove(os.path.join('static/images/', old_image))

    # Delete blog
    db.execute("DELETE FROM blog WHERE blog_id = :blog_id", {
        'blog_id': blog_id
    })

    db.commit()
    flash('One Blog Deleted!')
    return redirect('/admin')


# Route to handle search       
@app.route("/search",methods=['POST'])
def search():

    if request.method == "POST":

        # If search query is entered
        if not request.form.get("search"):
           return render_template("search.html", message = "No Query Provided")

        # Get all blog with title matching query
        row = db.execute("SELECT * FROM blog WHERE LOWER(title)  LIKE :query " , {'query': '%' + request.form.get("search").lower() + '%'}).fetchall()
    
        if row == None:
            return render_template('search.html', query=request.form.get("search"))
    
        return render_template("search.html", row=row, query=request.form.get("search"))


# Route to go to edit page (admin access)
@app.route("/edit/<int:blog_id>")
def edit(blog_id):

    # Check for admin access
    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    # Get blog and put values in blog form to edit
    blog = db.execute("SELECT * FROM blog WHERE blog_id = :blog_id", {
        'blog_id': blog_id
    }).fetchone()

    return render_template('edit.html', blog=blog)


# Route to edit the blog hanlder part (admin access)
@app.route("/edit-blog", methods=["POST"])
def edit_blog():

    # Check for admin access
    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    # Validation
    if not request.form.get("title"):
        return render_template("edit.html", message = "Title Missing")

    if not request.form.get("content"):
        return render_template("edit.html", message = "Content Missing")

    blog_id = request.form.get("blog_id")

    # Update blog with new title and content
    db.execute("UPDATE blog SET title = :title, content = :content WHERE blog_id = :blog_id", {
        'blog_id': blog_id, 'title': request.form.get("title"), 'content': request.form.get("content")
    })

    db.commit()

    flash('Blog is updated!')
    return redirect('/blog/' + str(blog_id))


# Route to add comments
@app.route('/comment', methods=['POST'])
def comment():

    # Comment form validation
    if not request.form.get("name"):
        flash("Sorry, Annoymous comments are not allowed.")
        return redirect("/")
    if not request.form.get("comment"):
        flash("Comment was empty")
        return redirect("/")

    # Get current time
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Add new comment
    db.execute("INSERT INTO comments (name, comment, date, blog_id) VALUES(:name, :comment, :date, :blog_id)",{
        'name': request.form.get("name"), 'comment': request.form.get("comment"), 'date': time, 'blog_id': request.form.get("blog_id") 
    })

    db.commit()

    flash("You comment is posted")

    # Redirect to same blog
    return redirect("/blog/" + str(request.form.get("blog_id")))


# Route to delete comments (admin access)
@app.route('/delete-comment', methods=['POST'])
def delete_comment():

    # Check for admin access, not required tho
    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    # Get comment and blog id
    comment_id = request.form.get("comment_id")
    blog_id = request.form.get("blog_id")

    # Delete the comment
    db.execute("DELETE FROM comments WHERE id = :comment_id", {
        'comment_id': comment_id
    })

    db.commit()

    flash('One Comment Deleted')
    return redirect('/blog/' + str(blog_id))


# Route to change/upload image for blogs (admin access)
@app.route('/change-image', methods=['POST'])
def change_image():

    # Check for admin access / Not required tho
    if session.get("user_id") is None:
        flash('To edit please login as admin')
        return redirect('/login')

    # Get old image detail and blog id
    old_image = request.form.get("old-img")
    blog_id = request.form.get("blog_id")

    # current time
    time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if file is added
    filename = 'NULL'
    if (request.files['filename']):
        types = ['image/png', 'image/jpg', 'image/jpeg']
        file = request.files['filename']
        filename = secure_filename(file.filename)
        filetype = file.content_type
        filename = str(time) + filename

        # Check for valid image type
        if not filetype in types:
            flash('Invalid File/Image Type')
            return redirect("/blog/" + str(blog_id))

    # If there is old image in blog delete it
    if not old_image == "NULL":
        
        os.remove(os.path.join('static/images/', old_image))

    # Save new image
    file.save(os.path.join('static/images/',filename))

    # Update blog image.
    db.execute("UPDATE blog SET img = :filename WHERE blog_id = :blog_id", {
       'filename': filename, 'blog_id': blog_id
    })

    db.commit()

    flash('Image Changed')
    return redirect("/blog/" + str(blog_id))


# Route to handle errors
@app.errorhandler(405)
@app.errorhandler(404)
def handle_404(e):

    return render_template('error.html', e=e)

    
if(__name__ == "__main__"):
    app.run()
    



