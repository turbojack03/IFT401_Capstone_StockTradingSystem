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


from apscheduler.schedulers.background import BackgroundScheduler 
from pathlib import Path
from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory, jsonify, render_template_string
from flask_bootstrap import Bootstrap5  # or Bootstrap if that's the version you installed
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import or_ 
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.dialects.mysql import SET
from sqlalchemy import text, func , case, cast, Float
from datetime import datetime, time
import plotly.express as px
import pandas as pd
import holidays
import json


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:password@database-1.ct6es408kgrf.us-east-2.rds.amazonaws.com/stock_db'
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
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    status = db.Column(
        SET("Banned", "Active", "FlaggedAccount"),
        nullable=False,
        default="Active"
    )
    
    cash_balance = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow) # removed foreign key constraint because it wouldnt let me run app.py idk why

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
    last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Market_schedule(db.Model):  # Market schedule model
    id = db.Column(db.Integer, primary_key=True)
    open_time = db.Column(db.Time, nullable=False)
    close_time = db.Column(db.Time, nullable=False)
    open_days = db.Column(db.String(20))
    is_holiday = db.Column(db.Boolean)

#*****************Working**************8
class Account_History(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey("accounts.id"), nullable=False)
    order_id = db.Column(db.Integer, db.ForeignKey('stock_orders.id'), nullable=True)
    action = db.Column(db.String(20), nullable=False)  # BUY, SELL, DEPOSIT, WITHDRAW
    stock_symbol = db.Column(db.String(10), nullable=True)
    quantity = db.Column(db.Integer, nullable=True)
    amount = db.Column(db.Float, nullable=False)  # positive=inflow, negative=outflow
    balance_after = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    note = db.Column(db.String(255), nullable=True)

#*****************Working****************


class Price_ticks(db.Model):  # Price ticks model
    id = db.Column(db.Integer, primary_key=True)
    stock_id = db.Column(db.Integer, db.ForeignKey('stocks.id'),  nullable=False)
    timestamp = db.Column(db.DateTime)
    price = db.Column(db.Float, nullable=False)

with app.app_context(): # Create database tables
    db.create_all()


# price sim simulator
import price_simulator
# change the interval 
start_simulator = price_simulator.attach(app, db, Stocks, Price_ticks, interval_seconds=5.0, verbose=True)

_first_time = True

@app.before_request
# will only start once you request something (html, refresh page)
def _run_once_on_first_request():
    global _first_time
    if _first_time:
        _first_time = False
        start_simulator()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def log_activity(account, action, amount, *, stock_symbol=None, quantity=None, order_id=None, note=None):
    try:
        entry = Account_History(
            user_id=account.user_id,
            account_id=account.id,
            order_id=order_id,
            action=action,
            stock_symbol=stock_symbol,
            quantity=quantity,
            amount=float(amount),
            balance_after=float(account.cash_balance),
            note=note
        )
        db.session.add(entry)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Failed to log account history: {e}")
        
def execute_pending_orders():
    from datetime import datetime
    with app.app_context():
        print(f"[{datetime.now()}] Running scheduled order execution...")

        pending_orders = stock_orders.query.filter_by(status="Pending").all()

        for order in pending_orders:
            account = Accounts.query.get(order.account_id)
            stock = Stocks.query.get(order.stock_id)
            
            if not account or not stock:
                continue  # skip if something is missing

            # Get latest stock price
            latest_tick = Price_ticks.query.filter_by(stock_id=stock.id).order_by(Price_ticks.timestamp.desc()).first()
            current_price = latest_tick.price if latest_tick else stock.initial_price

            total_value = current_price * order.quantity

            try:
                if order.buy_or_sell == "BUY":
                    if account.cash_balance >= total_value:
                        account.cash_balance -= total_value
                        order.status = "Executed"
                        order.executed_at = datetime.utcnow()
                        log_activity(
                            account,
                            "BUY",
                            -total_value,
                            stock_symbol=stock.ticker,
                            quantity=order.quantity,
                            order_id=order.id,
                            note="Auto-executed"
                        )
                    else:
                        order.status = "Failed"
                        order.executed_at = datetime.utcnow()
                        log_activity(
                            account,
                            "BUY_FAILED",
                            0,
                            stock_symbol=stock.ticker,
                            quantity=order.quantity,
                            order_id=order.id,
                            note="Insufficient funds"
                        )
                elif order.buy_or_sell == "SELL":
                    # For simplicity, assuming users can sell any pending quantity
                    account.cash_balance += total_value
                    order.status = "Executed"
                    order.executed_at = datetime.utcnow()
                    log_activity(
                        account,
                        "SELL",
                        total_value,
                        stock_symbol=stock.ticker,
                        quantity=order.quantity,
                        order_id=order.id,
                        note="Auto-executed"
                    )
                db.session.commit()
                print(f"Order {order.id} executed: {order.buy_or_sell} {order.quantity} of {stock.ticker} at ${current_price:.2f}")
            except Exception as e:
                db.session.rollback()
                print(f"Failed to execute order {order.id}: {e}")

# Start scheduler
scheduler = BackgroundScheduler()

scheduler.add_job(execute_pending_orders, 'cron', hour=9, minute=0)
scheduler.start()
#fish3
# Routes
@app.route('/frontend/<path:filename>')
def frontend_files(filename):
    return send_from_directory('frontend', filename)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        # Redirect based on role if already logged in
        if current_user.role == 'admin':
            return redirect(url_for('adminpanel'))
        else:
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

            # Redirect based on role
            if user.role == 'admin':
                return redirect(next_page or url_for('adminpanel'))
            else:
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
        return redirect(url_for('dashboard'))

    return render_template('register.html')


def is_market_open(now=None):
    market = Market_schedule.query.first()
    
    if not market:
        return True

    now = datetime.now()
    current_time = now.time()

    if not market.open_time or not market.close_time:
        return True
    
    today = now.date()
    holiday = holidays.US(years=today.year)

    if today in holiday:
        return False
    
    current_day = now.weekday() 
    open_days = [int(d.strip()) for d in market.open_days.split(",")]
    
    if current_day not in open_days:
        return False
    
    open_time = market.open_time
    close_time = market.close_time
    
    if open_time <= close_time:
        return open_time <= current_time <= close_time

    return current_time >= open_time or current_time <= close_time

@app.route('/', methods=["GET", "POST"])
@login_required
def dashboard():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        account = Accounts(
            user_id=current_user.id,
            status="Active",
            cash_balance=0.0,
            account_number=f"ACCT-{current_user.id:06d}",
        )
        db.session.add(account)
        db.session.commit()
        flash("No account found for this user.", "danger")
        return redirect(url_for('login'))

    if request.method == "POST":
        if not is_market_open():
            flash("Market is closed.", "warning")
            return redirect(url_for("dashboard"))

        stock_symbol = request.form.get("stockSymbol")
        buy_or_sell = request.form.get("buy_or_sell", "").upper()
        order_type = request.form.get("orderType")
        quantity = int(request.form.get("quantity", 0))

        if quantity <= 0:
            flash("Quantity must be greater than 0.", "danger")
            return redirect(url_for("dashboard"))

        stock = Stocks.query.filter_by(ticker=stock_symbol.upper()).first()
        if not stock:
            flash(f"Stock '{stock_symbol}' not found.", "danger")
            return redirect(url_for("dashboard"))

        latest_tick = Price_ticks.query.filter_by(stock_id=stock.id).order_by(Price_ticks.timestamp.desc()).first()
        current_price = latest_tick.price if latest_tick else stock.initial_price
        total_cost = current_price * quantity

        if buy_or_sell == "BUY":
            if account.cash_balance < total_cost:
                flash(f"Insufficient balance to buy {quantity} shares of {stock_symbol}.", "danger")
                return redirect(url_for("dashboard"))
            account.cash_balance -= total_cost
                        # log it
            log_activity(
                account,
                "BUY",
                -total_cost,
                stock_symbol=stock_symbol,
                quantity=quantity,
                note="Order submitted"
            )
            order_status = "Pending"
        elif buy_or_sell == "SELL":
            account.cash_balance += total_cost
            # log it
            log_activity(
                account,
                "SELL",
                total_cost,
                stock_symbol=stock_symbol,
                quantity=quantity,
                note="Order submitted"
            )
            order_status = "Pending"
        else:
            flash("Invalid order type.", "danger")
            return redirect(url_for("dashboard"))

        try:
            new_order = stock_orders(
                account_id=account.id,
                stock_id=stock.id,
                buy_or_sell=buy_or_sell,
                order_type=order_type,
                quantity=quantity,
                status=order_status,
                executed_at=datetime.utcnow()
            )
            db.session.add(new_order)
            db.session.commit()
            flash(f"Order {buy_or_sell} {quantity} shares of {stock_symbol} executed at ${current_price:.2f} each.", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to submit order: {e}", "danger")

        return redirect(url_for("dashboard"))

    selected_ticker = request.args.get("selected_stock", default=None)

    top_stocks_query = Stocks.query.filter_by(is_active=True).all()
    top_stocks = []

    for s in top_stocks_query:
        latest_ticks = (
            Price_ticks.query
            .filter_by(stock_id=s.id)
            .order_by(Price_ticks.timestamp.desc())
            .limit(2)
            .all()
        )

        current_price = s.initial_price
        percent_change = 0.0
        if latest_ticks:
            current_price = latest_ticks[0].price
            if len(latest_ticks) > 1:
                previous_price = latest_ticks[1].price
                if previous_price != 0:
                    percent_change = ((current_price - previous_price) / previous_price) * 100

        market_cap = current_price * s.volume

        top_stocks.append({
            "symbol": s.ticker,
            "name": s.company_name,
            "price": current_price,
            "change": round(percent_change, 2),
            "volume": s.volume,
            "market_cap": f"${market_cap:,.2f}"
        })

    top_stocks = sorted(top_stocks, key=lambda x: x["change"], reverse=True)[:10]

    if not selected_ticker and top_stocks:
        selected_ticker = top_stocks[0]["symbol"]

    selected_stock = None
    selected_stock_prices = []

    if selected_ticker:
        selected_stock = Stocks.query.filter_by(ticker=selected_ticker).first()
        if selected_stock:
            selected_stock_prices_raw = (
                Price_ticks.query
                .filter_by(stock_id=selected_stock.id)
                .order_by(Price_ticks.timestamp.asc())
                .all()
            )

            selected_stock_prices = [
                {
                    "timestamp": tick.timestamp.strftime("%H:%M"),
                    "price": tick.price
                }
                for tick in selected_stock_prices_raw
            ]

    orders = stock_orders.query.filter_by(account_id=account.id).all()

    return render_template("dashboard.html", orders=orders, stocks=top_stocks, selected_stock=selected_stock, selected_stock_prices=selected_stock_prices)

@app.route("/portfolio")
@login_required
def portfolio():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        flash("No account found for this user.", "warning")
        return render_template("portfolio.html", portfolio=[], pending_orders=[], executed_orders=[])

    orders = stock_orders.query.filter_by(account_id=account.id).all()

    portfolio_data = []
    total_investment = 0
    total_value = 0
    stock_dict = {}

    for order in orders:
        stock = Stocks.query.get(order.stock_id)
        if not stock:
            continue

        latest_tick = Price_ticks.query.filter_by(stock_id=stock.id).order_by(Price_ticks.timestamp.desc()).first()
        current_price = latest_tick.price if latest_tick else stock.initial_price

        if stock.id not in stock_dict:
            stock_dict[stock.id] = {
                "symbol": stock.ticker,
                "shares": 0,
                "investment": 0.0,
                "current_price": current_price
            }

        qty = order.quantity
        stock_dict[stock.id]["shares"] += qty if order.buy_or_sell == "BUY" else -qty
        stock_dict[stock.id]["investment"] += qty * current_price if order.buy_or_sell == "BUY" else -qty * current_price

    for s in stock_dict.values():
        if s["shares"] <= 0:
            continue
        current_value = s["shares"] * s["current_price"]
        profit_loss = current_value - s["investment"]
        total_investment += s["investment"]
        total_value += current_value

        portfolio_data.append({
            "symbol": s["symbol"],
            "current_price": s["current_price"],
            "shares": s["shares"],
            "investment": s["investment"],
            "profit_loss": profit_loss
        })

    total_pl = total_value - total_investment

    pending_orders_query = (
        stock_orders.query
        .filter_by(account_id=account.id, status="Pending")
        .join(Stocks, Stocks.id == stock_orders.stock_id)
        .add_entity(Stocks)
        .all()
    )

    pending_orders = []
    for order, stock in pending_orders_query:
        order.stock = stock
        pending_orders.append(order)
    


    executed_orders_query = (
        stock_orders.query
        .filter_by(account_id=account.id, status="Executed")
        .join(Stocks, Stocks.id == stock_orders.stock_id)
        .add_entity(Stocks)
        .all()
    )

    executed_orders = []
    stock_data = []
    for order, stock in executed_orders_query:
        order.stock = stock
        executed_orders.append(order)
        
        stock_item = {
            "ticker": stock.ticker,
            "quantity": order.quantity
        }
        stock_data.append(stock_item)

    data_json = json.dumps(stock_data)

    return render_template("portfolio.html", portfolio=portfolio_data, total_investment=total_investment, total_value=total_value, total_pl=total_pl, pending_orders=pending_orders, executed_orders=executed_orders, data_json=data_json)


@app.route('/availablestock', methods=["GET", "POST"])
@login_required
def availablestock():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        # Create a new account if missing
        account = Accounts(
            user_id=current_user.id,
            status="Active",
            cash_balance=0.0,
            account_number=f"ACCT-{current_user.id:06d}",
        )
        db.session.add(account)
        db.session.commit()
        flash("New account created for this user.", "info")
        return redirect(url_for('availablestock'))

    if request.method == "POST":
        if not is_market_open():
            flash("Market is closed.", "warning")
            return redirect(url_for("availablestock"))

        stock_symbol = request.form.get("stockSymbol")
        buy_or_sell = request.form.get("buy_or_sell", "").upper()
        order_type = request.form.get("orderType")
        quantity = int(request.form.get("quantity", 0))

        if not stock_symbol or quantity <= 0:
            flash("Invalid trade details.", "danger")
            return redirect(url_for("availablestock"))

        stock = Stocks.query.filter_by(ticker=stock_symbol).first()
        if not stock:
            flash("Stock not found.", "danger")
            return redirect(url_for("availablestock"))

        latest_tick = (Price_ticks.query.filter_by(stock_id=stock.id).order_by(Price_ticks.timestamp.desc()).first())
        current_price = latest_tick.price if latest_tick else stock.initial_price
        total_cost = current_price * quantity

        if buy_or_sell == "BUY":
            if account.cash_balance < total_cost:
                flash(f"Insufficient funds to buy {quantity} shares of {stock_symbol}.", "danger")
                return redirect(url_for("availablestock"))
            account.cash_balance -= total_cost
            # log it
            log_activity(
                account,
                "BUY",
                -total_cost,
                stock_symbol=stock_symbol,
                quantity=quantity,
                note="Order submitted"
            )
            order_status = "Pending"

        elif buy_or_sell == "SELL":
            account.cash_balance += total_cost
            # log it
            log_activity(
                account,
                "SELL",
                total_cost,
                stock_symbol=stock_symbol,
                quantity=quantity,
                note="Order submitted"
            )
            order_status = "Pending"

        else:
            flash("Invalid transaction type.", "danger")
            return redirect(url_for("availablestock"))

        try:
            new_order = stock_orders(
                account_id=account.id,
                stock_id=stock.id,
                buy_or_sell=buy_or_sell,
                order_type=order_type,
                quantity=quantity,
                status=order_status,
                executed_at=datetime.utcnow(),
            )
            db.session.add(new_order)
            db.session.commit()
            flash(
                f"Order submitted: {buy_or_sell} {quantity} shares of {stock_symbol} at ${current_price:.2f}.",
                "success",
            )
        except Exception as e:
            db.session.rollback()
            flash(f"Failed to submit order: {e}", "danger")

        return redirect(url_for("availablestock"))

    # NEW: simple server-side search
    q = request.args.get("q", "").strip()

    stocks_query = Stocks.query.filter_by(is_active=True)
    if q:
        like = f"%{q}%"
        stocks_query = stocks_query.filter(
            or_(
                Stocks.ticker.ilike(like),
                Stocks.company_name.ilike(like),
            )
        )

    stocks = stocks_query.order_by(Stocks.ticker.asc()).all()
    
    stock_list = []

    for s in stocks:
        latest_ticks = (
            Price_ticks.query.filter_by(stock_id=s.id)
            .order_by(Price_ticks.timestamp.desc())
            .limit(2)
            .all()
        )

        current_price = s.initial_price
        percent_change = 0.0
        if latest_ticks:
            current_price = latest_ticks[0].price
            if len(latest_ticks) > 1:
                previous_price = latest_ticks[1].price
                if previous_price != 0:
                    percent_change = ((current_price - previous_price) / previous_price) * 100

        market_cap = current_price * s.volume

        stock_list.append({
            'symbol': s.ticker,
            'name': s.company_name,
            'price': current_price,
            'change': round(percent_change, 2),
            'volume': s.volume,
            'market_cap': f"${market_cap:,.2f}",
        })

    orders = stock_orders.query.filter_by(account_id=account.id).all()

    return render_template('availablestock.html', stocks=stock_list, orders=orders)


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
        if new != confrim:
            flash("Passwords must match!", "warning")
            return render_template("changepassword.html")
        else:
            
            return render_template("changepassword.html")
            
    return render_template("changepassword.html")

@app.route("/accounthistory")
@login_required
def accounthistory():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        flash("No account found.", "danger")
        return redirect(url_for("dashboard"))
    entries = (Account_History.query
               .filter_by(account_id=account.id)
               .order_by(Account_History.timestamp.desc())
               .all())
    return render_template("accounthistory.html", entries=entries)

@app.route("/settings")
@login_required
def settings():
    market = Market_schedule.query.first()
    open_now = is_market_open()
    return render_template("settings.html", market=market, open_now=open_now)

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


@app.route("/delete_user/<int:user_id>", methods=["POST"])
@login_required
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    if user.id == current_user.id:
        flash("You cannot delete your own account.", "danger")
        return redirect(url_for("adminsettings"))

    try:
        db.session.delete(user)
        db.session.commit()
        flash("User deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete user: {e}", "danger")

    return redirect(url_for("adminsettings"))

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
        try:
            new_stock = Stocks(
                ticker=request.form.get('ticker'),
                company_name=request.form.get('company_name'),
                initial_price=request.form.get('initial_price'),
                volume=request.form.get('volume'),
                mu=request.form.get('mu'),
                sigma=request.form.get('sigma'),
                max_step_pct=request.form.get('max_step_pct'),
                is_active=True
            )
            db.session.add(new_stock)
            db.session.commit()
            flash(f"Stock {new_stock.ticker} added successfully!", "success")
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding stock: {e}", "danger")
    stocks = Stocks.query.all()
    return render_template('adminpanel.html', stocks=stocks)

@app.route("/schedule", methods=["GET", "POST"])
@login_required
@admin_required
def schedule():
    if request.method == 'POST':
        try:
            open_time_str = request.form.get('open_time')
            close_time_str = request.form.get('close_time')

            open_hour, open_min = map(int, open_time_str.split(":"))
            close_hour, close_min = map(int, close_time_str.split(":"))

            open_time_obj = time(open_hour, open_min)
            close_time_obj = time(close_hour, close_min)

            open_days = request.form.getlist("open_day")
            open_days_str = ','.join(open_days)

            schedule = Market_schedule.query.first()
            if not schedule:
                schedule = Market_schedule()

            schedule.open_time = open_time_obj
            schedule.close_time = close_time_obj
            schedule.open_days = open_days_str
            schedule.is_holiday = False

            db.session.add(schedule)
            db.session.commit()
            flash("Market schedule updated successfully.", "success")

        except Exception as e:
            db.session.rollback()
            flash(f"Error updating market schedule: {e}", "danger")

    market = Market_schedule.query.first()
    market_status = "OPEN" if is_market_open() else "CLOSED"
    return render_template('schedule.html', market=market, market_status=market_status)


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

    from sqlalchemy import desc
    rows_enriched = []
    for u, a in rows:
        orders = (
            db.session.query(
                stock_orders.stock_id,
                stock_orders.buy_or_sell,
                stock_orders.executed_at,
                stock_orders.quantity,
                stock_orders.status,
            )
            .filter(stock_orders.account_id == a.id)        # add .filter(stock_ORders.status == "Pending") to limit
            .order_by(desc(stock_orders.executed_at))       # newest first; NULLs last naturally in MySQL 8
            .all()
        )

        # attach a simple list of dicts the template can iterate
        a_orders = []
        for o in orders:
            a_orders.append({
                "stock_id":    o.stock_id,
                "buy_or_sell": o.buy_or_sell,
                "executed_at": o.executed_at,              # can be None for not-yet-executed
                "quantity":    float(o.quantity or 0),
                "status":      o.status,
            })

        setattr(a, "orders", a_orders)  # now available as a.orders in the template
        rows_enriched.append((u, a))

    rows = rows_enriched
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

@app.route("/cancel_order/<int:order_id>", methods=["POST"])
@login_required
def cancel_order(order_id):
    order = stock_orders.query.get_or_404(order_id)
    account = Accounts.query.filter_by(user_id=current_user.id).first()

    if order.account_id != account.id or order.status != "Pending":
        flash("Cannot cancel this order.", "danger")
        return redirect(url_for("portfolio"))

    try:
        db.session.delete(order)
        db.session.commit()
        flash("Pending order cancelled successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to cancel order: {e}", "danger")

    return redirect(url_for("portfolio"))

@app.route("/delete_stock/<int:stock_id>", methods=["POST"])
@login_required
def delete_stock(stock_id):
    stock = Stocks.query.get_or_404(stock_id)

    try:
        db.session.delete(stock)
        db.session.commit()
        flash("Stock deleted successfully.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete stock: {e}", "danger")

    return redirect(url_for("adminpanel"))

@app.route("/force_close", methods=["POST"])
@login_required
def force_close():
    schedule = Market_schedule.query.first()

    try:
        schedule.open_days = (7)
        db.session.commit()
        flash("Market close", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to delete close market: {e}", "danger")

    return redirect(url_for("adminpanel"))

@app.route("/update_cash", methods=["POST"])
@login_required
def update_cash():
    account = Accounts.query.filter_by(user_id=current_user.id).first()
    if not account:
        flash("No account found.", "danger")
        return redirect(url_for("dashboard"))
    
    action = request.form.get("action")
    amount = request.form.get("amount")
    
    try:
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Amount must be positive")
        
        if action == "withdraw":
            if amount > account.cash_balance:
                flash("Insufficient balance.", "danger")
                return redirect(url_for("dashboard"))
            account.cash_balance -= amount

            try:
                log_activity(
                    account,
                    'WITHDRAW',
                    -amount,
                    note='User cash update'
                )
            except Exception as e:
                app.logger.error(f"cash log failed: {e}")

        else: 
            account.cash_balance += amount

            try:
                log_activity(
                    account,
                    'DEPOSIT',
                     amount,
                    note='User cash update'
                )
            except Exception as e:
                app.logger.error(f"cash log failed: {e}")
        
        db.session.commit()
        flash(f"Successfully {action}ed ${amount:.2f}.", "success")
        
    except Exception as e:
        db.session.rollback()
        flash(f"Failed to update balance: {e}", "danger")

    return redirect(url_for("dashboard"))


@app.route("/dashboard/<ticker>")
def stock_chart(ticker):
    df = pd.read_sql(f"""
        SELECT sp.timestamp, sp.price
        FROM stock_prices sp
        JOIN stocks s ON s.id = sp.stock_id
        WHERE s.ticker = '{ticker}'
        ORDER BY sp.timestamp
    """, db.engine)

    fig = px.line(df, x='timestamp', y='price', title=f'{ticker} Stock Price Over Time')
    graph_html = fig.to_html(full_html=False)

    return render_template_string("""
        <html>
            <head><title>{{ ticker }} Chart</title></head>
            <body>
                <h1>{{ ticker }} Price Chart</h1>
                {{ graph|safe }}
            </body>
        </html>
    """, graph=graph_html, ticker=ticker)








@app.context_processor
def inject_cash_balance():
    if current_user.is_authenticated:
        acct = Accounts.query.filter_by(user_id=current_user.id).first()
        if acct:
            return dict(user_cash=acct.cash_balance)
    return dict(user_cash=0.0)












if __name__ == "__main__":
    app.run(debug=True)



