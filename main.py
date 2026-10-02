import os
import psycopg2
from psycopg2.extras import RealDictCursor
from flask import Flask, render_template, request, redirect, url_for, session, flash
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("29e1b7a26cee8b0ccc1facb534c067d5489b6420792391b2981956b84dc7ffb1", "kisan-seva-secret-key")
DATABASE_URL = os.getenv("postgresql://postgres:anurag%40ucb@db.xxxxxx.supabase.co:5432/postgres")

def get_db():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=RealDictCursor)
    return conn


# ---------------- HOME ----------------

@app.route("/")
def index():
    return render_template("index.html")


# ---------------- FARMER LOGIN ----------------

@app.route("/auth", methods=["GET", "POST"])
def auth():
    if request.method == "POST":
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "").strip()

        if not phone or not password:
            flash("Please enter phone number and password.", "error")
            return redirect(url_for("auth"))

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM farmers WHERE phone = %s AND password = %s",
            (phone, password)
        )
        farmer = cur.fetchone()

        cur.close()
        conn.close()

        if farmer:
            session["farmer_id"] = farmer["id"]
            session["farmer_name"] = farmer["name"]
            return redirect(url_for("farmer_dashboard"))

        flash("Invalid phone number or password.", "error")
        return redirect(url_for("auth"))

    return render_template("auth.html")


# ---------------- FARMER SIGNUP ----------------

@app.route("/signup", methods=["POST"])
def signup():
    name = request.form.get("name", "").strip()
    phone = request.form.get("phone", "").strip()
    village = request.form.get("village", "").strip()
    password = request.form.get("password", "").strip()

    if not name or not phone or not village or not password:
        flash("Please fill all required fields.", "error")
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT id FROM farmers WHERE phone = %s", (phone,))
    existing = cur.fetchone()

    if existing:
        cur.close()
        conn.close()
        flash("Phone number already registered.", "error")
        return redirect(url_for("auth"))

    cur.execute(
        """
        INSERT INTO farmers (name, phone, village, password)
        VALUES (%s, %s, %s, %s)
        """,
        (name, phone, village, password)
    )

    conn.commit()
    cur.close()
    conn.close()

    flash("Account created successfully. Please login.", "success")
    return redirect(url_for("auth"))


# ---------------- FARMER DASHBOARD ----------------

@app.route("/farmer_dashboard", methods=["GET"])
def farmer_dashboard():
    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM farmers WHERE id = %s", (session["farmer_id"],))
    farmer = cur.fetchone()

    cur.execute(
        """
        SELECT bookings.*, crops.name AS crop_name, centres.name AS centre_name
        FROM bookings
        JOIN crops ON bookings.crop_id = crops.id
        JOIN centres ON bookings.centre_id = centres.id
        WHERE bookings.farmer_id = %s
        ORDER BY bookings.id DESC
        """,
        (session["farmer_id"],)
    )
    bookings = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("farmer_dashboard.html", farmer=farmer, bookings=bookings)


# ---------------- FARMER BOOKING ----------------

@app.route("/farmer/booking", methods=["GET", "POST"])
def farmer_booking():
    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor()

    if request.method == "POST":
        crop_id = request.form.get("crop_id")
        weight = request.form.get("weight")
        centre_id = request.form.get("centre_id")

        if not crop_id or not weight or not centre_id:
            cur.close()
            conn.close()
            flash("Please complete all booking details.", "error")
            return redirect(url_for("farmer_booking"))

        cur.execute(
            "SELECT COALESCE(MAX(token_number), 0) AS max_token FROM bookings WHERE centre_id = %s",
            (centre_id,)
        )
        last_token = cur.fetchone()["max_token"]
        token_number = last_token + 1

        cur.execute(
            """
            INSERT INTO bookings (farmer_id, crop_id, weight, centre_id, token_number, status)
            VALUES (%s, %s, %s, %s, %s, %s)
            RETURNING id
            """,
            (session["farmer_id"], crop_id, weight, centre_id, token_number, "Waiting")
        )

        booking_id = cur.fetchone()["id"]

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("farmer_token", booking_id=booking_id))

    cur.execute("SELECT * FROM crops")
    crops = cur.fetchall()

    cur.execute("SELECT * FROM centres")
    centres = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("farmer_booking.html", crops=crops, centres=centres)


# ---------------- TOKEN ----------------

@app.route("/farmer/token/<int:booking_id>")
def farmer_token(booking_id):
    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT bookings.*,
               crops.name AS crop_name,
               centres.name AS centre_name,
               centres.location AS centre_location
        FROM bookings
        JOIN crops ON bookings.crop_id = crops.id
        JOIN centres ON bookings.centre_id = centres.id
        WHERE bookings.id = %s AND bookings.farmer_id = %s
        """,
        (booking_id, session["farmer_id"])
    )
    booking = cur.fetchone()

    cur.close()
    conn.close()

    if not booking:
        return "Booking not found", 404

    return render_template("farmer_token.html", booking=booking)


# ---------------- LOGOUT ----------------

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


# ---------------- CENTRE LOGIN ----------------

@app.route("/centre/login", methods=["GET", "POST"])
def centre_login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "").strip()

        conn = get_db()
        cur = conn.cursor()

        cur.execute(
            "SELECT * FROM centres WHERE username = %s AND password = %s",
            (username, password)
        )
        centre = cur.fetchone()

        cur.close()
        conn.close()

        if centre:
            session["centre_id"] = centre["id"]
            session["centre_name"] = centre["name"]
            return redirect(url_for("centre_dashboard"))

        flash("Invalid centre credentials.", "error")

    return render_template("centre_login.html")


# ---------------- CENTRE DASHBOARD ----------------

@app.route("/centre/dashboard")
def centre_dashboard():
    if "centre_id" not in session:
        return redirect(url_for("centre_login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM centres WHERE id = %s", (session["centre_id"],))
    centre = cur.fetchone()

    cur.execute(
        """
        SELECT bookings.*,
               farmers.name AS farmer_name,
               farmers.phone AS farmer_phone,
               farmers.village,
               crops.name AS crop_name
        FROM bookings
        JOIN farmers ON bookings.farmer_id = farmers.id
        JOIN crops ON bookings.crop_id = crops.id
        WHERE bookings.centre_id = %s
        ORDER BY bookings.token_number ASC
        """,
        (session["centre_id"],)
    )
    tokens = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("centre_dashboard.html", centre=centre, tokens=tokens)


# ---------------- PROCESS TOKEN ----------------

@app.route("/centre/process/<int:booking_id>", methods=["GET", "POST"])
def centre_process(booking_id):
    if "centre_id" not in session:
        return redirect(url_for("centre_login"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        """
        SELECT bookings.*,
               farmers.name AS farmer_name,
               farmers.phone AS farmer_phone,
               crops.name AS crop_name,
               centres.name AS centre_name
        FROM bookings
        JOIN farmers ON bookings.farmer_id = farmers.id
        JOIN crops ON bookings.crop_id = crops.id
        JOIN centres ON bookings.centre_id = centres.id
        WHERE bookings.id = %s AND bookings.centre_id = %s
        """,
        (booking_id, session["centre_id"])
    )
    booking = cur.fetchone()

    if not booking:
        cur.close()
        conn.close()
        return "Token not found", 404

    if request.method == "POST":
        status = request.form.get("status")
        allowed_statuses = ["Waiting", "Called", "Processing", "Completed", "Rejected"]

        if status not in allowed_statuses:
            cur.close()
            conn.close()
            flash("Invalid status.", "error")
            return redirect(url_for("centre_process", booking_id=booking_id))

        cur.execute(
            """
            UPDATE bookings
            SET status = %s
            WHERE id = %s AND centre_id = %s
            """,
            (status, booking_id, session["centre_id"])
        )

        conn.commit()
        cur.close()
        conn.close()

        return redirect(url_for("centre_dashboard"))

    cur.close()
    conn.close()

    return render_template("centre_process.html", booking=booking)


if __name__ == "__main__":
    app.run(debug=True)