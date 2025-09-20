from pathlib import Path
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bootstrap import Bootstrap5  # or Bootstrap if that's the version you installed
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/stock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
bootstrap = Bootstrap5(app)

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  

with app.app_context():
    db.create_all()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

#fish3
# Routes
@app.route('/frontend/<path:filename>')
def frontend_files(filename):
    return send_from_directory('frontend', filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')

    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully', 'success')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        if not username or not email or not password:
            flash('All fields are required!', 'danger')
            return redirect(url_for('register'))

        existing_user = User.query.filter_by(username=username).first()
        if existing_user:
            flash('Username already exists!', 'danger')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password)
        new_user = User(username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/')
@login_required
def dashboard():
    users = User.query.all()
    return render_template('dashboard.html', users=users)

@app.route("/portfolio")
@login_required
def portfolio():
    return render_template("portfolio.html")
    
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")

@app.route("/accounthistory")
@login_required
def accounthistory():
    return render_template("accounthistory.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

@app.route("/questionmarkquestionmarkquestionmark")
@login_required
def questionmarkquestionmarkquestionmark():
    return render_template("questionmarkquestionmarkquestionmark.html")



@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        flash('Both username and email are required!', 'danger')
        return redirect(url_for('dashboard'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists!', 'danger')
        return redirect(url_for('dashboard'))

    new_user = User(username=username, email=email, password=generate_password_hash("default123"))  # default password
    db.session.add(new_user)
    db.session.commit()
    flash(f'User {username} added successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/delete_user/<int:user_id>')
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)
    db.session.delete(user)
    db.session.commit()
    flash(f'User {user.username} deleted successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/read_user/<int:user_id>')
@login_required
def read_user(user_id):
    user = User.query.get_or_404(user_id)
    return f"User Details: ID: {user.id}, Username: {user.username}, Email: {user.email}"

@app.route('/update_user/<int:user_id>', methods=['POST'])
@login_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    username = request.form.get('username')
    email = request.form.get('email')
    if not username or not email:
        flash('Both username and email are required!', 'danger')
        return redirect(url_for('dashboard'))

    user.username = username
    user.email = email
    db.session.commit()
    flash(f'User {username} updated successfully!', 'success')
    return redirect(url_for('dashboard'))


if __name__ == "__main__":
    app.run(debug=True)

