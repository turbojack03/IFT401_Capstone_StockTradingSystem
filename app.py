# Tips
# WHEN YOU CREATE An @APP.route, you must put it above "app.run"
# DO NOT QUOTE OUT ANY @app.route it will cause errors

# default role on account creation is USER not admin.
#you can change it on line 64 for development purposes
# admin role is required to access /adminpanel and /adminsettings



# QUICK TIPS FOR MYSQL

#use stock_db; SELECT * FROM user; -- to see users
#use stock_db; SELECT * FROM accounts; -- to see accounts/money :) arg arg arg - mr krabs
# to change to admin do in mysql query: UPDATE user SET role='admin' WHERE username='Rootbeer';



from pathlib import Path
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_bootstrap import Bootstrap5  # or Bootstrap if that's the version you installed
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import SET
from sqlalchemy import text, func , case, cast, Float
from datetime import datetime


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:password@localhost/stock_db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your-secret-key'
bootstrap = Bootstrap5(app)

db = SQLAlchemy(app)  #lets u interact with the database

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'  
with app.app_context(): # Create database tables
    db.create_all()
#tables
class Accounts(db.Model):  # Accounts model
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    status = db.Column(
        SET("Banned", "Active", "FlaggedAccount"),
        nullable=False,
        default="Active"
    )
    
    cash_balance = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime)
    account_number = db.Column(db.String(20), unique=True, nullable=False)

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(100), unique=True, nullable=False)
    last_name = db.Column(db.String(100), unique=True, nullable=False)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    role = db.Column(db.String(10), nullable=False, default='user')  # 'user' or 'admin'


class stock_orders(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'),nullable=False)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'),nullable=False)
    buy_or_sell = db.Column(db.String(80),nullable=False)
    order_type = db.Column(db.String(120),nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    executed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(80),nullable=False, default="Pending")
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

class Stocks(db.Model):  # Stock model for stock data
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(5), unique=True, nullable=False)
    company_name = db.Column(db.String(100), nullable=False)
    initial_price = db.Column(db.Float, nullable=False)
    mu = db.Column(db.Float, default=0.05)
    sigma = db.Column(db.Float, default=0.20)
    max_step_pct = db.Column(db.Float, default=1.0)
    volume = db.Column(db.Integer, default=100000)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Market_schdule(db.Model):  # Market schedule model
    id = db.Column(db.Integer, primary_key=True)
    market_name = db.Column(db.String(100), nullable=False)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    is_holiday = db.Column(db.Boolean)


class Price_ticks(db.Model):  # Price ticks model
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'),  nullable=False)
    timestamp = db.Column(db.DateTime)
    price = db.Column(db.Float, nullable=False)

with app.app_context(): # Create database tables
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
            user.last_login_at = datetime.utcnow()
            db.session.commit()            
            login_user(user)
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
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
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
        new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/', methods=["GET", "POST"])
@login_required
def dashboard():
    if request.method == "POST":
        stock_symbol = request.form.get("stockSymbol")
        buy_or_sell = request.form.get("buy_or_sell")
        order_type = request.form.get("orderType")
        quantity = request.form.get("quantity")

        account = Accounts.query.filter_by(user_id=current_user.id).first()
        if not account:
            flash("No account found for this user.", "danger")
            return redirect(url_for("dashboard"))

        stock = Stocks.query.filter_by(ticker=stock_symbol.upper()).first()
        if not stock:
            flash(f"Stock '{stock_symbol}' not found.", "danger")
            return redirect(url_for("dashboard"))

        try:
            new_order = stock_orders(
                account_id=account.id,
                stock_id=stock.id,
                buy_or_sell=buy_or_sell,
                order_type=order_type,
                quantity=int(quantity),
                status="Pending"
            )
            db.session.add(new_order)
            db.session.commit()
            flash("Order submitted successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to submit order: {e}", "danger")

        return redirect(url_for("dashboard"))

    orders = stock_orders.query.all()
    stocks = Stocks.query.filter_by(is_active=True).all()
    return render_template("dashboard.html", orders=orders, stocks=stocks)

@app.route("/portfolio")
@login_required
def portfolio():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        flash("No account found for this user.", "warning")
        return render_template("portfolio.html", portfolio=[])

    orders = (
        db.session.query(
            stock_orders.stock_id,

            # Net shares:
            func.sum(
                case(
                    (stock_orders.buy_or_sell == "BUY", cast(stock_orders.quantity, Float)),
                    else_=-cast(stock_orders.quantity, Float),
                )
            ).label("net_quantity"),

            # Net investment (signed):
            func.sum(
                case(
                    (stock_orders.buy_or_sell == "BUY", cast(stock_orders.quantity, Float) * Price_ticks.price),
                    else_=-cast(stock_orders.quantity, Float) * Price_ticks.price,
                )
            ).label("net_investment"),
        )
        .join(Price_ticks, Price_ticks.stock_id == stock_orders.stock_id)
        .filter(stock_orders.account_id == account.id)
        .group_by(stock_orders.stock_id)
        .all()
    )

    portfolio_data = []
    total_investment = 0
    total_value = 0

    for stock_id, net_quantity, net_investment in orders:
        if net_quantity <= 0:
            continue 

        stock = Stocks.query.get(stock_id)
        latest_price = (
            Price_ticks.query.filter_by(stock_id=stock_id)
            .order_by(Price_ticks.timestamp.desc())
            .first()
        )
        current_price = latest_price.price if latest_price else stock.initial_price

        current_value = net_quantity * current_price
        profit_loss = current_value - net_investment

        total_investment += net_investment
        total_value += current_value

        portfolio_data.append({
            "symbol": stock.ticker,
            "current_price": current_price,
            "shares": net_quantity,
            "investment": net_investment,
            "profit_loss": profit_loss
        })

    total_pl = total_value - total_investment

    return render_template("portfolio.html", portfolio=portfolio_data,total_investment=total_investment,total_value=total_value,total_pl=total_pl)
    
@app.route("/profile")
@login_required
def profile():
    return render_template("profile.html")


@app.route("/changepassword", methods=["GET", "POST"])
@login_required
def changepassword():
    if request.method == "POST":
        new = request.form.get("new_password")
        confrim = request.form.get("confrim_password")

        if new == confrim:
            current_user.password = generate_password_hash(new)
            db.session.commit()
            logout_user()
            return redirect(url_for("login"))
        else:
            return render_template("changepassword.html")
    return render_template("changepassword.html")

@app.route("/accounthistory")
@login_required
def accounthistory():
    return render_template("accounthistory.html")

@app.route("/settings")
@login_required
def settings():
    return render_template("settings.html")

#CRUD routes
@app.route('/add_user', methods=['POST'])
@login_required
def add_user():
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    username = request.form.get('username')
    email = request.form.get('email')
    if not last_name or not first_name or not username or not email:
        flash('Both username and email are required!', 'danger')
        return redirect(url_for('dashboard'))

    existing_user = User.query.filter_by(username=username).first()
    if existing_user:
        flash('Username already exists!', 'danger')
        return redirect(url_for('dashboard'))

    new_user = User(first_name=first_name, last_name=last_name, username=username, email=email, password=generate_password_hash("default123"))  # default password
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
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    username = request.form.get('username')
    email = request.form.get('email')
    if not last_name or not first_name or not username or not email:
        flash('Both username and email are required!', 'danger')
        return redirect(url_for('dashboard'))

    user.first_name = first_name
    user.last_name = last_name
    user.username = username
    user.email = email
    db.session.commit()
    flash(f'User {username} updated successfully!', 'success')
    return redirect(url_for('dashboard'))

@app.route('/availablestock')
def availablestock():

    stocks = Stocks.query.filter_by(is_active=True).all()

    stock_list = []
    for s in stocks:
        stock_list.append({
            'symbol': s.ticker,
            'name': s.company_name,
            'price': s.initial_price,
            'change': 0.0,
            'percent': 0.0,
            'market_cap': '-',
            'volume': '-',
            'sector': '' 
        })
    return render_template('availablestock.html', stocks=stock_list)


# ---- Admin gate ----
from functools import wraps
from flask import abort

def admin_required(view_func):
    @wraps(view_func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin': # if role is not admin dont let them in
            abort(403)
        return view_func(*args, **kwargs)
    return wrapper

# --- ADMIN PANEL ---
@app.route("/adminpanel", methods=["GET", "POST"])
@login_required
@admin_required
def adminpanel():
    if request.method == 'POST':
        company_name = request.form.get('company_name')
        ticker = request.form.get('ticker')
        initial_price = request.form.get('initial_price')
        volume = request.form.get('volume')
        mu = request.form.get('mu')
        sigma = request.form.get('sigma')
        max_step_pct = request.form.get('max_step_pct')

        new_stock = Stocks(
            ticker=ticker,
            company_name=company_name,
            initial_price=initial_price,
            volume=volume,
            mu=mu,
            sigma=sigma,
            max_step_pct=max_step_pct,
            is_active=True 
        )

        try:
            db.session.add(new_stock)
            db.session.commit()
            flash(f"Stock {ticker} added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding stock: {e}", "danger")

        return redirect(url_for('adminpanel'))
    
    stocks = Stocks.query.all()
    return render_template('adminpanel.html', stocks=stocks)

# --- ADMIN SETTINGS (lists users + accounts) ---
@app.route("/adminsettings", methods=["GET"])
@login_required
@admin_required
def adminsettings():
    rows = (
        db.session.query(User, Accounts)
        .outerjoin(Accounts, Accounts.user_id == User.id)
        .order_by(User.id.asc())
        .all()
    )
    # auto-create accounts if missing (optional)
    created_any = False
    for u, a in rows:
        if a is None:
            a = Accounts(user_id=u.id, status="Active", cash_balance=0.0,
                         account_number=f"ACCT-{u.id:06d}")
            db.session.add(a)
            created_any = True
    if created_any:
        db.session.commit()
        rows = (
            db.session.query(User, Accounts)
            .outerjoin(Accounts, Accounts.user_id == User.id)
            .order_by(User.id.asc())
            .all()
        )
    return render_template("adminsettings.html", rows=rows)

# --- UPDATE (status/cash) ---
@app.route("/admin/update/<int:user_id>", methods=["POST"])
@login_required
@admin_required
def admin_update_user(user_id):
    u = User.query.get_or_404(user_id)
    a = Accounts.query.filter_by(user_id=user_id).first()
    if a is None:
        a = Accounts(user_id=user_id, status="Active", cash_balance=0.0,
                     account_number=f"ACCT-{user_id:06d}")
        db.session.add(a)

    new_status = request.form.get("status")
    cash_delta = request.form.get("cash_delta")

    if new_status in {"Active", "Banned", "FlaggedAccount"}:
        a.status = new_status

    try:
        if cash_delta:
            amt = float(cash_delta)
            a.cash_balance = (a.cash_balance or 0.0) + amt
        db.session.commit()
        flash(f"Updated {u.username}.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Update failed: {e}", "danger")

    return redirect(url_for("adminsettings"))















@app.context_processor
def inject_cash_balance():
    if current_user.is_authenticated:
        acct = Accounts.query.filter_by(user_id=current_user.id).first()
        if acct:
            return dict(user_cash=acct.cash_balance)
    return dict(user_cash=0.0)












if __name__ == "__main__":
    app.run(debug=True)



