# THIS WILL BE OUR MAIN FILE. ALL SESSION ACTIVTY HAPPENS HERE OR ATLEAST GO THROUGH

from pathlib import Path
from flask import Flask, render_template
from flask_bootstrap import Bootstrap5  # or Bootstrap if that's the version you installed

# Resolve paths
APP_DIR = Path(__file__).resolve().parent      # backend/app
PROJECT_ROOT = APP_DIR.parent.parent           # go up 2 levels to project root

TEMPLATES_DIR = PROJECT_ROOT / "Frontend" / "templates"
STATIC_DIR    = PROJECT_ROOT / "Frontend"

# Debug check (optional, helps confirm paths)
print("Templates folder:", TEMPLATES_DIR)
print("Static folder:", STATIC_DIR)

# Create app
app = Flask(
    __name__,
    template_folder=str(TEMPLATES_DIR),
    static_folder=str(STATIC_DIR),
)

bootstrap = Bootstrap5(app)
#fish3
# Routes
@app.route("/")
def base():
    return render_template("base.html")  

@app.route("/login")
def login():
    return render_template("login.html") 

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/portfolio")
def portfolio():
    return render_template("portfolio.html")
    
@app.route("/profile")
def profile():
    return render_template("profile.html")
<<<<<<< Updated upstream

@app.route("/questionmarkquestionmarkquestionmark")
def questionmarkquestionmarkquestionmark():
    return render_template("questionmarkquestionmarkquestionmark.html")

@app.route("/accounthistory")
def accounthistory():
    return render_template("accounthistory.html")
=======
>>>>>>> Stashed changes

@app.route("/questionmarkquestionmarkquestionmark")
def questionmarkquestionmarkquestionmark():
    return render_template("questionmarkquestionmarkquestionmark.html")




@app.route("/settings")
def settings():
    return render_template("settings.html")
if __name__ == "__main__":
    app.run(debug=True)

