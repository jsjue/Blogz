from flask import Flask, request, redirect, render_template, session, flash, url_for
from flask_sqlalchemy import SQLAlchemy
''''from models import User'''
'''from forms import SignupForm, LoginForm, Blogform'''



app = Flask(__name__)
app.config['DEBUG'] = True
                                        
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://blogz:chair@localhost:8889/build-a-blog'
app.config['SQLALCHEMY_ECHO'] = True
db = SQLAlchemy(app)

app.secret_key = 'abracadabra'

class Blog(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255))
    body = db.Column(db.Text)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'))

    def __init__(self, title, body, owner):
        self.title = title
        self.body = body
        self.owner = owner


class User(db.Model):

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    blogs = db.relationship('Blog', backref='owner')

    def __init__(self, username, password):
        self.username = username
        self.password = password


@app.before_request
def require_login():
    """specifies routes user is allowed to see without being logged in"""

    allowed_routes = ['login', 'signup', 'show_posts', 'index', 'static']
    if request.endpoint not in allowed_routes and 'username' not in session:
        return redirect('/login')


@app.route('/home')
def index():
    """displays all registered users of Blogz"""

    users = User.query.all()
    return render_template('index.html', users=users)

@app.route('/login', methods=['POST', 'GET'])
def login():
    """form handler for login form: if username and password valid, logs user in; otherwise, displays appropriate errors"""

    # processes form data; queries database for existing user
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        # if username in database and password matches entered password, log user in
        if user and user.password == password:
            session['username'] = username
            flash("Successfully logged in!", 'logged_in')
            #print(session)
            return redirect('/newpost')
        # if username in database but password invalid:
        elif user and not user.password == password:
            flash('Invalid password', 'invalid_password')
            #print(session)
            return redirect('/login')
        # if username not in database:
        else:
            flash('Invalid username', 'invalid_username')
            return redirect('/login')

    return render_template('login.html')

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    """form handler for signup form: validates form and displays appropriate errors; if no errors, creates new user and saves to session and database"""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        verify = request.form['verify']

        username_error = ""
        password_error = ""
        verify_error = ""

        existing_user = User.query.filter_by(username=username).first()

        # Form Validation
        # if either username, password, or verify are blank, display error message that affected fields are invalid
        # if either len(username) < 3 or len(password) <3, display 'invalid username' or 'invalid password' message
        # if password and verify don't match, display error message that passwords don't match

        if not username:
            username_error = "This field cannot be empty"
            username = ""
        else:
            username_len = len(username)
            if  username_len < 3:
                username_error = "Username must 3 or more characters"
                username = ""

        if not verify:
            verify_error = "This field cannot be empty"
            verify = ""
        else:
            if verify != password:
                verify_error = "Passwords must match"
                verify = ""

        if not password:
            password_error = "This field cannot be empty"
            password = ""
        else:
            password_len = len(password)
            if  password_len < 3:
                password_error = "Password must be 3 or more characters"
                password = ""

        # if user is not in database and one or more validation errors are generated, re-serve form with appropriate error messages:
        if not existing_user and username_error or password_error or verify_error:
            return render_template ("signup.html",
            username=username,
            username_error=username_error, password_error=password_error, verify_error=verify_error)

        # if user is not in database and no validation errors are generated (i.e. all form data is valid), create new user and save in database and session variable:
        elif not existing_user and not username_error and not password_error and not verify_error:
            new_user = User(username, password)
            db.session.add(new_user)
            db.session.commit()
            session['username'] = username
            return redirect('/newpost')

        # if username is already in database (i.e. duplicate user):
        else:
            flash('That username is already in use. Please choose another.', 'duplicate_username')
            return redirect('/signup')

    return render_template('signup.html')

@app.route('/logout')
def logout():
    """logs user out; deletes user data from session"""
    del session['username']
    return redirect('/blog')

@app.route('/blog', methods=['POST', 'GET'])
def show_posts():
    """displays blog posts: single, single-user, and all"""

    # displays single blog post
    if request.method == 'GET' and request.args.get('id'):
        blog_id = request.args.get('id')
        blog = Blog.query.get(blog_id)
        user_id = blog.owner_id
        user = User.query.get(user_id)
        return render_template('singleuser.html', title='Blogz', user=user, blog=blog)

    # displays all blog posts for an individual user
    if request.method == 'GET' and request.args.get('userID'):
        user_id = request.args.get('userID')
        user = User.query.get(user_id)
        user_blogs = Blog.query.filter_by(owner_id=user_id).all()
        return render_template('singleuser.html', title='Blogz', user=user, user_blogs=user_blogs)

    # displays all blog posts
    if request.method == 'GET' or request.method == 'POST':
        blogs = Blog.query.all()
        return render_template('post.html', title='Blogz', blogs=blogs)

@app.route('/newpost', methods=['POST', 'GET'])
def add_blog():
    """form handler for new posts; if no form validation errors, redirects to blog post page"""

    # displays the add a post form
    if request.method == 'GET':
        return render_template('add_blog.html', title="Blogz")

    # form handler for new posts
    if request.method == 'POST':
        blog_title = request.form['title']
        blog_body = request.form['body']
        owner = User.query.filter_by(username=session['username']).first()
        error = "This field cannot be left blank."
        title_error, body_error = "", ""

        # if blog title is missing, render error
        if not blog_title:
            title_error = error
            return render_template('add_blog.html', title="Build A Blog", title_error=title_error, blog_body=blog_body)

        # if blog body is missing, render error
        if not blog_body:
            body_error = error
            return render_template('add_blog.html', title="Build A Blog", body_error=body_error, blog_title=blog_title)

        # if no errors are generated, create new blog post
        if not title_error and not body_error:
            new_blog = Blog(blog_title, blog_body, owner)
            db.session.add(new_blog)
            db.session.commit()
            blog_id = new_blog.id
    return redirect("/home?id={}".format(blog_id))

if __name__ == '__main__':
    app.run()