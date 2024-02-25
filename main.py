from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo
from flask_login import UserMixin, LoginManager, login_user, logout_user, login_required, current_user
import mysql.connector

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'jd12'
app.config['MYSQL_DB'] = 'social'

mysql_conn = mysql.connector.connect(
    host=app.config['MYSQL_HOST'],
    user=app.config['MYSQL_USER'],
    password=app.config['MYSQL_PASSWORD'],
    database=app.config['MYSQL_DB']
)
cursor = mysql_conn.cursor()

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, username, email):
        self.id = id
        self.username = username
        self.email = email

@login_manager.user_loader
def load_user(user_id):
    cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user_data = cursor.fetchone()
    if user_data:
        return User(user_data[0], user_data[1], user_data[2])
    return None

class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')

class ProfileUpdateForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    bio = TextAreaField('Bio')
    phone_number = StringField('Phone Number')
    submit = SubmitField('Update Profile')

@app.route("/")
@app.route("/home")
def home():
    cursor.execute("SELECT * FROM posts")
    posts = cursor.fetchall()
    return render_template('home.html', posts=posts)

@app.route("/register", methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        cursor.execute("SELECT * FROM users WHERE username = %s", (form.username.data,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash('Username already exists!', 'danger')
        else:
            cursor.execute("INSERT INTO users (username, email, password) VALUES (%s, %s, %s)", (form.username.data, form.email.data, form.password.data))
            mysql_conn.commit()
            flash('Your account has been created! You are now able to log in', 'success')
            return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        cursor.execute("SELECT * FROM users WHERE username = %s", (form.username.data,))
        user = cursor.fetchone()
        if user and user[3] == form.password.data:  # Assuming password is stored at index 3
            login_user(User(user[0], user[1], user[2]))
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        else:
            flash('Login unsuccessful. Please check username and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route("/create_post", methods=['GET', 'POST'])
@login_required
def create_post():
    form = PostForm()
    if form.validate_on_submit():
        cursor.execute("INSERT INTO posts (title, content, author) VALUES (%s, %s, %s)", (form.title.data, form.content.data, current_user.id))
        mysql_conn.commit()
        flash('Post created successfully!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='Create Post', form=form)

@app.route("/dashboard")
@login_required
def dashboard():
    cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
    user_data = cursor.fetchone()
    if user_data:
        user = User(user_data[0], user_data[1], user_data[2])
    else:
        flash('User not found!', 'danger')
        return redirect(url_for('home'))
    return render_template('dashboard.html', title='Dashboard', user=user)

@app.route("/update_profile", methods=['GET', 'POST'])
@login_required
def update_profile():
    form = ProfileUpdateForm()
    if form.validate_on_submit():
        cursor.execute("UPDATE users SET email = %s, bio = %s, phone_number = %s WHERE id = %s", (form.email.data, form.bio.data, form.phone_number.data, current_user.id))
        mysql_conn.commit()
        flash('Your profile has been updated!', 'success')
        return redirect(url_for('dashboard'))
    elif request.method == 'GET':
        cursor.execute("SELECT * FROM users WHERE id = %s", (current_user.id,))
        user_data = cursor.fetchone()
        if user_data:
            form.email.data = user_data[2]
            form.bio.data = user_data[3]
            form.phone_number.data = user_data[4]
    return render_template('update_profile.html', title='Update Profile', form=form)

if __name__ == '__main__':
    app.run(debug=True)
