#This is going to be used to simulate price

#make this realistic as possible. Have fun with this lol

#class Stocks(db.Model):  # Stock model for stock data
    #id = db.Column(db.Integer, primary_key=True)
    #ticker = db.Column(db.String(5), unique=True, nullable=False)
    #company_name = db.Column(db.String(100), nullable=False)
    #initial_price = db.Column(db.Float, nullable=False)
    #mu = db.Column(db.Float, default=0.05)
    #sigma = db.Column(db.Float, default=0.20)
    #max_step_pct = db.Column(db.Float, default=1.0)
    #volume = db.Column(db.Integer, default=100000)
    #is_active = db.Column(db.Boolean, default=True)
    #created_at = db.Column(db.DateTime, default=datetime.utcnow)
    #last_update = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

# app.py no import here
  # my dumbass put app.py here and  never noticed for half an hour of debugging other things
# price_simulator.py
import os, math, random
from datetime import datetime
from threading import Thread, Event

SECONDS_PER_YEAR = 252 * 6.5 * 3600

def next_price(price, mu, sigma, cap_pct, dt_seconds=30.0): 
    dt = dt_seconds / SECONDS_PER_YEAR
    #random number define
    z  = random.gauss(0.0, 1.0)
    #my attempt at the geometric brownian motion formula
    raw_ret = math.exp((mu - 0.5*sigma*sigma)*dt + sigma*(dt**0.5)*z) - 1.0
    # maximum jump the stocks can do. 
    cap_dec = cap_pct / 100.0
    r = max(-cap_dec, min(cap_dec, raw_ret))
    # price cant go negative
    return max(0.01, price*(1.0 + r)), r

# interval seconds is default
def attach(app, db, Stocks, *, interval_seconds=30.0, verbose=True):
    """Return a starter function that will spin up the background thread."""
    stop_event = Event()
    started = {"ok": False}

    def update_stocks_once():
        rows = Stocks.query.filter_by(is_active=True).all()
        #tells us if there are no active stocks
        if not rows:
            if verbose:
                print("[price_simulator] no active stocks", flush=True)
            return
        ts = datetime.utcnow().strftime("%H:%M:%S")
        #updates each stock one by one
        for s in rows:
            p0 = float(s.initial_price)
            p1, r = next_price(p0, float(s.mu), float(s.sigma), float(s.max_step_pct), dt_seconds=interval_seconds)
            s.initial_price = p1
            if verbose:
                print(f"[{ts}] {s.ticker}: {p0:.2f} -> {p1:.2f} ({r*100:+.2f}%)", flush=True)
        db.session.commit()
    # infinite loop to update stocks every interval_seconds
    def loop():
        # allow DB access outside request context
        with app.app_context():
            while not stop_event.is_set():
                update_stocks_once()
                stop_event.wait(interval_seconds)

    def start(): 
        if not started["ok"] and os.environ.get("WERKZEUG_RUN_MAIN") == "true":
            if verbose:
                print("[price_simulator] starting background loop", flush=True)
            Thread(target=loop, daemon=True).start()
            started["ok"] = True

    return start

