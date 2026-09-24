from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = "kisan-seva-secret-key"

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
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

        farmer = conn.execute(
            """
            SELECT * FROM farmers
            WHERE phone = ? AND password = ?
            """,
            (phone, password)
        ).fetchone()

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

    existing = conn.execute(
        "SELECT id FROM farmers WHERE phone = ?",
        (phone,)
    ).fetchone()

    if existing:
        conn.close()
        flash("Phone number already registered.", "error")
        return redirect(url_for("auth"))

    conn.execute(
        """
        INSERT INTO farmers (name, phone, village, password)
        VALUES (?, ?, ?, ?)
        """,
        (name, phone, village, password)
    )

    conn.commit()
    conn.close()

    flash("Account created successfully. Please login.", "success")
    return redirect(url_for("auth"))


# ---------------- FARMER DASHBOARD ----------------

@app.route("/farmer_dashboard", methods=["GET"])
def farmer_dashboard():

    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()

    farmer = conn.execute(
        "SELECT * FROM farmers WHERE id = ?",
        (session["farmer_id"],)
    ).fetchone()

    bookings = conn.execute(
        """
        SELECT bookings.*, crops.name AS crop_name,
               centres.name AS centre_name
        FROM bookings
        JOIN crops ON bookings.crop_id = crops.id
        JOIN centres ON bookings.centre_id = centres.id
        WHERE bookings.farmer_id = ?
        ORDER BY bookings.id DESC
        """,
        (session["farmer_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "farmer_dashboard.html",
        farmer=farmer,
        bookings=bookings
    )


# ---------------- FARMER BOOKING ----------------

@app.route("/farmer/booking", methods=["GET", "POST"])
def farmer_booking():

    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()

    if request.method == "POST":

        crop_id = request.form.get("crop_id")
        weight = request.form.get("weight")
        centre_id = request.form.get("centre_id")

        if not crop_id or not weight or not centre_id:
            conn.close()
            flash("Please complete all booking details.", "error")
            return redirect(url_for("farmer_booking"))

        # Get next serial number for this centre
        last_token = conn.execute(
            """
            SELECT MAX(token_number)
            FROM bookings
            WHERE centre_id = ?
            """,
            (centre_id,)
        ).fetchone()[0]

        token_number = (last_token or 0) + 1

        conn.execute(
            """
            INSERT INTO bookings
            (
                farmer_id,
                crop_id,
                weight,
                centre_id,
                token_number,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                session["farmer_id"],
                crop_id,
                weight,
                centre_id,
                token_number,
                "Waiting"
            )
        )

        booking_id = conn.execute(
            "SELECT last_insert_rowid()"
        ).fetchone()[0]

        conn.commit()
        conn.close()

        return redirect(
            url_for(
                "farmer_token",
                booking_id=booking_id
            )
        )

    crops = conn.execute(
        "SELECT * FROM crops"
    ).fetchall()

    centres = conn.execute(
        "SELECT * FROM centres"
    ).fetchall()

    conn.close()

    return render_template(
        "farmer_booking.html",
        crops=crops,
        centres=centres
    )


# ---------------- TOKEN ----------------

@app.route("/farmer/token/<int:booking_id>")
def farmer_token(booking_id):

    if "farmer_id" not in session:
        return redirect(url_for("auth"))

    conn = get_db()

    booking = conn.execute(
        """
        SELECT bookings.*,
               crops.name AS crop_name,
               centres.name AS centre_name,
               centres.location AS centre_location
        FROM bookings
        JOIN crops ON bookings.crop_id = crops.id
        JOIN centres ON bookings.centre_id = centres.id
        WHERE bookings.id = ?
        AND bookings.farmer_id = ?
        """,
        (booking_id, session["farmer_id"])
    ).fetchone()

    conn.close()

    if not booking:
        return "Booking not found", 404

    return render_template(
        "farmer_token.html",
        booking=booking
    )


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

        centre = conn.execute(
            """
            SELECT * FROM centres
            WHERE username = ? AND password = ?
            """,
            (username, password)
        ).fetchone()

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

    centre = conn.execute(
        """
        SELECT * FROM centres
        WHERE id = ?
        """,
        (session["centre_id"],)
    ).fetchone()

    tokens = conn.execute(
        """
        SELECT bookings.*,
               farmers.name AS farmer_name,
               farmers.phone AS farmer_phone,
               farmers.village,
               crops.name AS crop_name
        FROM bookings
        JOIN farmers ON bookings.farmer_id = farmers.id
        JOIN crops ON bookings.crop_id = crops.id
        WHERE bookings.centre_id = ?
        ORDER BY bookings.token_number ASC
        """,
        (session["centre_id"],)
    ).fetchall()

    conn.close()

    return render_template(
        "centre_dashboard.html",
        centre=centre,
        tokens=tokens
    )


# ---------------- PROCESS TOKEN ----------------

@app.route("/centre/process/<int:booking_id>", methods=["GET", "POST"])
def centre_process(booking_id):

    if "centre_id" not in session:
        return redirect(url_for("centre_login"))

    conn = get_db()

    booking = conn.execute(
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
        WHERE bookings.id = ?
        AND bookings.centre_id = ?
        """,
        (booking_id, session["centre_id"])
    ).fetchone()

    if not booking:
        conn.close()
        return "Token not found", 404

    if request.method == "POST":

        status = request.form.get("status")

        allowed_statuses = [
            "Waiting",
            "Called",
            "Processing",
            "Completed",
            "Rejected"
        ]

        if status not in allowed_statuses:
            conn.close()
            flash("Invalid status.", "error")
            return redirect(
                url_for(
                    "centre_process",
                    booking_id=booking_id
                )
            )

        conn.execute(
            """
            UPDATE bookings
            SET status = ?
            WHERE id = ?
            AND centre_id = ?
            """,
            (
                status,
                booking_id,
                session["centre_id"]
            )
        )

        conn.commit()
        conn.close()

        return redirect(url_for("centre_dashboard"))

    conn.close()

    return render_template(
        "centre_process.html",
        booking=booking
    )


if __name__ == "__main__":
    app.run(debug=True)