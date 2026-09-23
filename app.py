import os
import re
from pathlib import Path
from uuid import uuid4
from functools import wraps

from dotenv import load_dotenv
from flask import (
    Flask,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)

from supabase import create_client
from werkzeug.security import check_password_hash, generate_password_hash
from werkzeug.utils import secure_filename


# -------------------------------------------------
# Load environment variables
# -------------------------------------------------

load_dotenv()


# -------------------------------------------------
# Supabase configuration
# -------------------------------------------------

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError(
        "SUPABASE_URL and SUPABASE_KEY are required in .env"
    )

supabase = create_client(
    SUPABASE_URL,
    SUPABASE_KEY
)

# Supabase Storage bucket
STORAGE_BUCKET = "uploads"


# -------------------------------------------------
# App configuration
# -------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent

DOWNLOAD_FOLDER = BASE_DIR / "downloads"
DOWNLOAD_FOLDER.mkdir(exist_ok=True)

ALLOWED_EXTENSIONS = {
    "pdf",
    "png",
    "jpg",
    "jpeg"
}

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv(
    "SECRET_KEY",
    "change-this-secret-key"
)

app.config["MAX_CONTENT_LENGTH"] = 10 * 1024 * 1024


# -------------------------------------------------
# Helper functions
# -------------------------------------------------

def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )


def clean_name_for_filename(name):
    clean_name = secure_filename(
        name.replace(" ", "_")
    )

    return clean_name or "user"


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):

        if "user_id" not in session:

            flash(
                "Please log in first.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        return view(*args, **kwargs)

    return wrapped_view


def validate_signup_data(
    name,
    age,
    address,
    email,
    mobile,
    password
):

    if not name or not age or not address or not email or not mobile or not password:
        return "All fields are required."

    if not name.replace(" ", "").isalpha():
        return "Name must contain only letters and spaces."

    try:
        age_number = int(age)

        if age_number < 18 or age_number > 120:
            return "Age must be between 18 and 120."

    except ValueError:
        return "Age must be a valid number."

    # Email validation
    if not re.fullmatch(
        r"[^@\s]+@[^@\s]+\.[^@\s]+",
        email
    ):
        return "Enter a valid email address."

    # Mobile validation
    if not re.fullmatch(
        r"[0-9]{10,15}",
        mobile
    ):
        return "Mobile number must contain 10 to 15 digits."

    # Password validation
    if len(password) < 8:
        return "Password must contain at least 8 characters."

    return None


# -------------------------------------------------
# Login
# -------------------------------------------------

@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        if not email or not password:

            flash(
                "Email and password are required.",
                "error"
            )

            return redirect(
                url_for("login")
            )

        try:

            # Find user
            response = (
                supabase
                .table("users")
                .select(
                    "id,name,email,password_hash"
                )
                .eq("email", email)
                .limit(1)
                .execute()
            )

            users = response.data

            if not users:

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            user = users[0]

            # Check password
            if not check_password_hash(
                user["password_hash"],
                password
            ):

                flash(
                    "Invalid email or password.",
                    "error"
                )

                return redirect(
                    url_for("login")
                )

            # Create session
            session["user_id"] = user["id"]
            session["user_name"] = user["name"]
            session["user_email"] = user["email"]

            flash(
                "Login successful.",
                "success"
            )

            return redirect(
                url_for("dashboard")
            )

        except Exception as error:

            print(
                "Login error:",
                error
            )

            flash(
                "Unable to log in right now.",
                "error"
            )

            return redirect(
                url_for("login")
            )

    return render_template(
        "login.html"
    )


# -------------------------------------------------
# Signup
# -------------------------------------------------

@app.route("/signup", methods=["GET", "POST"])
def signup():

    if "user_id" in session:

        return redirect(
            url_for("dashboard")
        )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        age = request.form.get(
            "age",
            ""
        ).strip()

        address = request.form.get(
            "address",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        mobile = request.form.get(
            "mobile",
            ""
        ).strip()

        password = request.form.get(
            "password",
            ""
        )

        # Validate
        validation_error = validate_signup_data(
            name,
            age,
            address,
            email,
            mobile,
            password
        )

        if validation_error:

            flash(
                validation_error,
                "error"
            )

            return redirect(
                url_for("signup")
            )

        try:

            # Check whether email already exists
            response = (
                supabase
                .table("users")
                .select("id")
                .eq("email", email)
                .limit(1)
                .execute()
            )

            if response.data:

                flash(
                    "This email is already registered. Please log in.",
                    "error"
                )

                return redirect(
                    url_for("signup")
                )

            # Hash password
            password_hash = generate_password_hash(
                password
            )

            # Insert user
            supabase.table("users").insert({
                "name": name,
                "age": int(age),
                "address": address,
                "email": email,
                "mobile": mobile,
                "password_hash": password_hash
            }).execute()

            flash(
                "Signup successful. Please log in.",
                "success"
            )

            return redirect(
                url_for("login")
            )

        except Exception as error:

            print(
                "Signup error:",
                error
            )

            flash(
                "Unable to create the account. Please try again.",
                "error"
            )

            return redirect(
                url_for("signup")
            )

    return render_template(
        "signup.html"
    )


# -------------------------------------------------
# Dashboard
# -------------------------------------------------

@app.route("/dashboard")
@login_required
def dashboard():

    return render_template(
        "dashboard.html",
        user_name=session.get("user_name"),
        user_email=session.get("user_email")
    )


# -------------------------------------------------
# File download
# -------------------------------------------------

@app.route("/download")
@login_required
def download_file():

    test_file = DOWNLOAD_FOLDER / "test_file.txt"

    if not test_file.exists():

        test_file.write_text(
            "This is the test download file for the assessment project.\n",
            encoding="utf-8"
        )

    return send_from_directory(
        str(DOWNLOAD_FOLDER),
        "test_file.txt",
        as_attachment=True
    )


# -------------------------------------------------
# File upload
# -------------------------------------------------

@app.route("/upload", methods=["POST"])
@login_required
def upload_files():

    # Get ONE file from dashboard
    uploaded_file = request.files.get("file")

    # No file selected
    if not uploaded_file or not uploaded_file.filename:

        flash(
            "Please select a file.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    # Check file type
    if not allowed_file(
        uploaded_file.filename
    ):

        flash(
            "Only PDF, PNG, JPG, and JPEG files are allowed.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )

    try:

        # Get logged-in user's details
        user_name = clean_name_for_filename(
            session["user_name"]
        )

        user_id = session["user_id"]

        # Original filename
        original_filename = secure_filename(
            uploaded_file.filename
        )

        # File extension
        extension = original_filename.rsplit(
            ".",
            1
        )[1].lower()

        # Generate unique filename
        stored_filename = (
            f"{user_name}_{uuid4().hex}.{extension}"
        )

        # Path inside Supabase Storage
        storage_path = (
            f"{user_id}/{stored_filename}"
        )

        # Read file
        file_data = uploaded_file.read()

        # Content type
        content_type = (
            uploaded_file.content_type
            or "application/octet-stream"
        )

        # -----------------------------------------
        # Upload file to Supabase Storage
        # -----------------------------------------

        supabase.storage.from_(
            STORAGE_BUCKET
        ).upload(
            storage_path,
            file_data,
            {
                "content-type": content_type,
                "upsert": False
            }
        )

        # -----------------------------------------
        # Save file information in database
        # -----------------------------------------

        supabase.table(
            "uploaded_files"
        ).insert({
            "user_id": user_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_type": extension
        }).execute()

        # -----------------------------------------
        # Success message
        # -----------------------------------------

        flash(
            "File uploaded successfully!",
            "success"
        )

        # Go back to Dashboard
        return redirect(
            url_for("dashboard")
        )

    except Exception as error:

        print(
            "Upload error:",
            error
        )

        flash(
            "File upload failed. Please try again.",
            "error"
        )

        return redirect(
            url_for("dashboard")
        )
        

        # -----------------------------------------
        # Upload actual file to Supabase Storage
        # -----------------------------------------

        supabase.storage.from_(
            STORAGE_BUCKET
        ).upload(
            storage_path,
            file_data,
            {
                "content-type": content_type,
                "upsert": False
            }
        )

        # -----------------------------------------
        # Save file information in database
        # -----------------------------------------

        supabase.table(
            "uploaded_files"
        ).insert({
            "user_id": user_id,
            "original_filename": original_filename,
            "stored_filename": stored_filename,
            "file_type": extension
        }).execute()

        # -----------------------------------------
        # Success
        # -----------------------------------------

        flash(
            "File uploaded successfully!",
            "success"
        )

        # Stay on dashboard
        return redirect(
            url_for("dashboard")
        )

    except Exception as error:

        print(
            "Upload error:",
            error
        )

        flash(
            "File upload failed. Please try again.",
            "error"
        )

        # Return to dashboard instead of upload page
        return redirect(
            url_for("dashboard")
        )


# -------------------------------------------------
# Logout
# -------------------------------------------------

@app.route("/logout")
@login_required
def logout():

    session.clear()

    flash(
        "You have been logged out.",
        "success"
    )

    return redirect(
        url_for("login")
    )


# -------------------------------------------------
# File size error
# -------------------------------------------------

@app.errorhandler(413)
def file_too_large(error):

    flash(
        "File is too large. Maximum upload size is 10 MB.",
        "error"
    )

    return redirect(
        url_for("dashboard")
    )


# -------------------------------------------------
# Start application
# -------------------------------------------------

if __name__ == "__main__":

    app.run(
        debug=True
    )