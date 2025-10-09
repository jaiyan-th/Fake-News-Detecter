from flask import Flask, render_template, request, redirect, url_for, session
from flask_pymongo import PyMongot
from werkzeug.security import generate_password_hash, check_password_hash
import pickle
import os
import datetime

# Text preprocessing
from preprocess.text_cleaning import clean_text

# Load model and vectorizer
with open(os.path.join("model", "model.pkl"), "rb") as f:
    model = pickle.load(f)

with open(os.path.join("model", "vectorizer.pkl"), "rb") as f:
    vectorizer = pickle.load(f)

app = Flask(__name__)
app.secret_key = "secret_key"

# MongoDB config
app.config["MONGO_URI"] = "mongodb://localhost:27017/fake_news_app"
mongo = PyMongo(app)

# Home
@app.route("/")
def home():
    return render_template("index.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        users = mongo.db.users
        login_user = users.find_one({"username": request.form["username"]})

        if login_user and check_password_hash(login_user["password"], request.form["password"]):
            session["username"] = request.form["username"]
            return redirect(url_for("home"))
        return "Invalid username/password!"
    return render_template("login.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        users = mongo.db.users
        existing_user = users.find_one({"username": request.form["username"]})

        if existing_user is None:
            hashpass = generate_password_hash(request.form["password"])
            users.insert_one({"username": request.form["username"], "password": hashpass})
            return redirect(url_for("login"))
        return "That username already exists!"
    return render_template("register.html")

# Predict
@app.route("/predict", methods=["POST"])
def predict():
    if "username" not in session:
        return redirect(url_for("login"))

    news = request.form["news"]
    cleaned = clean_text(news)
    transformed = vectorizer.transform([cleaned])
    prediction = model.predict(transformed)[0]
    result = "FAKE" if prediction == "FAKE" else "REAL"

    mongo.db.predictions.insert_one({
        "username": session["username"],
        "news": news,
        "prediction": result,
        "timestamp": datetime.datetime.now()
    })

    return render_template("index.html", prediction=result, news=news)

# History
@app.route("/history")
def history():
    if "username" not in session:
        return redirect(url_for("login"))

    records = list(mongo.db.predictions.find({"username": session["username"]}).sort("timestamp", -1))
    return render_template("history.html", records=records)

# Clear History
@app.route("/clear_history", methods=["POST"])
def clear_history():
    if "username" not in session:
        return redirect(url_for("login"))

    mongo.db.predictions.delete_many({"username": session["username"]})
    return redirect(url_for("history"))

# Admin View (restricted)
@app.route("/admin")
def admin():
    if "username" not in session:
        return redirect(url_for("login"))
    
    if session["username"] != "admin":
        return "Access denied. Admins only."

    records = list(mongo.db.predictions.find().sort("timestamp", -1))
    return render_template("admin.html", records=records)

# Logout
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)
