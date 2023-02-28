from flask import Flask

app = Flask(__name__)

@app.route("/login")
def index():
    return render_template("login.html")