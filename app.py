import os
from flask import Flask, render_template, request, redirect, url_for
from models import get_db, close_db, init_db

app = Flask(__name__)
app.secret_key = "petlift-secret"

@app.before_request
def setup():
    init_db()

@app.teardown_appcontext
def teardown_db(exception):
    close_db()

RESCUER_ID = 1
DRIVER_ID = 2

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/rescuer", methods=["GET", "POST"])
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
        """, (RESCUER_ID, pickup, clinic, crates, reason))
        db.commit()
        return redirect(url_for("rescuer_home"))
    cur = db.execute("""
        SELECT request_id, pickup_loc, dropoff_clinic,
               crate_count, reason, status
        FROM transport_requests
        WHERE rescuer_id = ?
        ORDER BY created_at DESC
    """, (RESCUER_ID,))
    my_requests = cur.fetchall()
    return render_template("rescuer_home.html", requests=my_requests)

@app.route("/driver")
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
    """, (DRIVER_ID,))
    active_trips = cur2.fetchall()
    return render_template("driver_home.html",
                           open_requests=open_requests,
                           active_trips=active_trips)

@app.route("/driver/claim/<int:request_id>", methods=["POST"])
def claim_request(request_id):
    db = get_db()
    db.execute("""
        INSERT INTO trips (request_id, driver_id, status)
        VALUES (?, ?, 'scheduled')
    """, (request_id, DRIVER_ID))
    db.execute("""
        UPDATE transport_requests SET status = 'claimed'
        WHERE request_id = ?
    """, (request_id,))
    db.commit()
    return redirect(url_for("driver_home"))

@app.route("/trip/<int:trip_id>/status", methods=["POST"])
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