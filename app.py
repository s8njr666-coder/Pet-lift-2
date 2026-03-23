import os
from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import get_db, close_db, init_db, get_user_by_email, get_user_by_id, User

app = Flask(__name__)
app.secret_key = "petlift-secret-2026"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

@login_manager.user_loader
def load_user(user_id):
    return get_user_by_id(int(user_id))

@app.before_request
def setup():
    init_db()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        role = request.form["role"]
        hashed = generate_password_hash(password)
        db = get_db()
        try:
            db.execute(
                "INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                (name, email, hashed, role)
            )
            db.commit()
            user = get_user_by_email(email)
            login_user(user)
            if role == "rescuer":
                return redirect(url_for("rescuer_home"))
            else:
                return redirect(url_for("driver_home"))
        except:
            flash("An account with that email already exists.")
            return redirect(url_for("signup"))
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        db = get_db()
        cur = db.execute(
            "SELECT * FROM users WHERE email = ?", (email,)
        )
        row = cur.fetchone()
        if row and check_password_hash(row["password"], password):
            user = User(row["user_id"], row["name"], row["email"], row["role"])
            login_user(user)
            if row["role"] == "rescuer":
                return redirect(url_for("rescuer_home"))
            else:
                return redirect(url_for("driver_home"))
        flash("Invalid email or password.")
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("index"))

@app.route("/rescuer", methods=["GET", "POST"])
@login_required
def rescuer_home():
    db = get_db()
    if request.method == "POST":
        pickup = request.form["pickup_loc"]
        clinic = request.form["dropoff_clinic"]
        crates = int(request.form["crate_count"])
        reason = request.form.get("reason", "")
        db.execute("""
            INSERT INTO transport_requests
            (rescuer_id, pickup_loc, dropoff_clinic, crate_count, reason)
            VALUES (?, ?, ?, ?, ?)
        """, (current_user.id, pickup, clinic, crates, reason))
        db.commit()
        return redirect(url_for("rescuer_home"))
    cur = db.execute("""
        SELECT request_id, pickup_loc, dropoff_clinic,
               crate_count, reason, status
        FROM transport_requests
        WHERE rescuer_id = ?
        ORDER BY created_at DESC
    """, (current_user.id,))
    my_requests = cur.fetchall()
    return render_template("rescuer_home.html", requests=my_requests)

@app.route("/driver")
@login_required
def driver_home():
    db = get_db()
    cur = db.execute("""
        SELECT request_id, pickup_loc, dropoff_clinic, crate_count, reason
        FROM transport_requests
        WHERE status = 'open'
        ORDER BY created_at ASC
    """)
    open_requests = cur.fetchall()
    cur2 = db.execute("""
        SELECT t.trip_id, t.status,
               r.pickup_loc, r.dropoff_clinic, r.crate_count, r.reason
        FROM trips t
        JOIN transport_requests r ON t.request_id = r.request_id
        WHERE t.driver_id = ? AND t.status != 'done'
        ORDER BY t.trip_id DESC
    """, (current_user.id,))
    active_trips = cur2.fetchall()
    return render_template("driver_home.html",
                           open_requests=open_requests,
                           active_trips=active_trips)

@app.route("/driver/claim/<int:request_id>", methods=["POST"])
@login_required
def claim_request(request_id):
    db = get_db()
    db.execute("""
        INSERT INTO trips (request_id, driver_id, status)
        VALUES (?, ?, 'scheduled')
    """, (request_id, current_user.id))
    db.execute("""
        UPDATE transport_requests SET status = 'claimed'
        WHERE request_id = ?
    """, (request_id,))
    db.commit()
    return redirect(url_for("driver_home"))

@app.route("/trip/<int:trip_id>/status", methods=["POST"])
@login_required
def update_trip_status(trip_id):
    new_status = request.form["status"]
    db = get_db()
    db.execute("UPDATE trips SET status = ? WHERE trip_id = ?",
               (new_status, trip_id))
    if new_status == "done":
        db.execute("""
            UPDATE transport_requests SET status = 'done'
            WHERE request_id = (
                SELECT request_id FROM trips WHERE trip_id = ?
            )
        """, (trip_id,))
    db.commit()
    return redirect(url_for("driver_home"))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)