from flask import Flask, render_template, request, redirect, session, send_file
import mysql.connector
from mysql.connector import IntegrityError
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
import re
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)

# Change this before deploying
app.secret_key = os.getenv("SECRET_KEY")

# Upload settings
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"pdf", "png", "jpg", "jpeg"}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)


# ---------------- DATABASE ----------------

db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)


# ---------------- HELPERS ----------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS
    )


# ---------------- HOME ----------------

@app.route("/")
def home():
    return redirect("/signup")


# ---------------- SIGNUP ----------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if request.method == "POST":

        name = request.form["name"].strip()
        age_text = request.form["age"].strip()
        address = request.form["address"].strip()
        email = request.form["email"].strip()
        mobile = request.form["mobile"].strip()
        password = request.form["password"]

        # Age validation
        try:
            age = int(age_text)
        except ValueError:
            return "Please enter a valid age."

        if age < 1 or age > 120:
            return "Please enter a valid age."

        # Email validation
        email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"

        if not re.match(email_pattern, email):
            return "Please enter a valid email address."

        # Mobile validation
        if not mobile.isdigit() or len(mobile) != 10:
            return "Please enter a valid 10-digit mobile number."

        # Password validation
        if len(password) < 6:
            return "Password must contain at least 6 characters."

        # Hash password
        password_hash = generate_password_hash(password)

        cursor = db.cursor()

        query = """
        INSERT INTO users
        (name, age, address, email, mobile, password_hash)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            name,
            age,
            address,
            email,
            mobile,
            password_hash
        )

        try:
            cursor.execute(query, values)
            db.commit()

        except IntegrityError:
            cursor.close()
            return "Email already registered. Please use another email."

        cursor.close()

        return redirect("/login")

    return render_template("signup.html")


# ---------------- LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form["email"].strip()
        password = request.form["password"]

        cursor = db.cursor(dictionary=True)

        query = "SELECT * FROM users WHERE email = %s"

        cursor.execute(query, (email,))

        user = cursor.fetchone()

        cursor.close()

        if user and check_password_hash(
            user["password_hash"],
            password
        ):

            session["user_id"] = user["id"]
            session["user_name"] = user["name"]

            return redirect("/dashboard")

        return "Invalid email or password."

    return render_template("login.html")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
def dashboard():

    if "user_id" not in session:
        return redirect("/login")

    return render_template(
        "dashboard.html",
        user_name=session["user_name"]
    )


# ---------------- FILE UPLOAD ----------------

@app.route("/upload", methods=["POST"])
def upload_file():

    if "user_id" not in session:
        return redirect("/login")

    if "file" not in request.files:
        return "No file selected."

    file = request.files["file"]

    if file.filename == "":
        return "No file selected."

    if not allowed_file(file.filename):
        return "Only PDF, PNG and JPEG files are allowed."

    user_id = session["user_id"]
    user_name = session["user_name"]

    original_filename = secure_filename(file.filename)

    filename = user_name + "_" + original_filename

    file_path = os.path.join(
        app.config["UPLOAD_FOLDER"],
        filename
    )

    file.save(file_path)

    file_type = file.content_type

    cursor = db.cursor()

    query = """
    INSERT INTO uploaded_files
    (user_id, filename, file_type)
    VALUES (%s, %s, %s)
    """

    values = (
        user_id,
        filename,
        file_type
    )

    cursor.execute(query, values)

    db.commit()

    cursor.close()

    return "File uploaded successfully."


# ---------------- FILE DOWNLOAD ----------------

@app.route("/download")
def download_file():

    if "user_id" not in session:
        return redirect("/login")

    file_path = os.path.join(
        "downloads",
        "test.txt"
    )

    return send_file(
        file_path,
        as_attachment=True
    )


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/login")


# ---------------- RUN APP ----------------

if __name__ == "__main__":
    app.run(debug=True)