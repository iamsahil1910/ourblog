from flask import Flask, request
from flask.templating import render_template

app = Flask(__name__)


@app.route('/')
def hello():
    return render_template('index.html')

@app.route('/login')
def login():
    return render_template('login.html')
    

@app.route('/admin')
def admin():
    return render_template('admin.html')


@app.route('/blog')
def blog():
    return render_template('blog.html')


if(__name__ == "__main__"):
    app.run(debug = True)
    



