from flask import Blueprint, jsonify, session, request

from extensions import db
from models import User, Trek, Booking
from cache_utils import invalidate_trek_cache

staff_bp = Blueprint("staff", __name__)


@staff_bp.route("/dashboard", methods=["GET"])
def staff_dashboard():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find the logged-in user
    staff = db.session.get(User, user_id)

    if staff is None or staff.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Staff permission
    if staff.role != "staff":
        return jsonify({
            "message": "Access denied. Staff only."
        }), 403

    # Step 4: Fetch only assigned treks
    assigned_treks = Trek.query.filter_by(
        assigned_staff_id=staff.id
    ).order_by(Trek.id.asc()).all()

    # Step 5: Prepare trek information
    trek_list = []

    for trek in assigned_treks:
        trek_list.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "status": trek.status
        })

    # Step 6: Return dashboard information
    return jsonify({
        "message": "Staff dashboard fetched successfully.",
        "staff_name": staff.name,
        "total_assigned_treks": len(trek_list),
        "assigned_treks": trek_list
    }), 200

@staff_bp.route("/treks/<int:trek_id>/slots", methods=["PUT"])
def update_trek_slots(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find the logged-in user
    staff = db.session.get(User, user_id)

    if staff is None or staff.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Staff permission
    if staff.role != "staff":
        return jsonify({
            "message": "Access denied. Staff only."
        }), 403

    # Step 4: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 5: Check whether this trek is assigned to Staff
    if trek.assigned_staff_id != staff.id:
        return jsonify({
            "message": "You are not assigned to this trek."
        }), 403

    # Step 6: Receive updated slots
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    available_slots = data.get("available_slots")

    # Step 7: Validate slots
    if type(available_slots) is not int or available_slots < 0:
        return jsonify({
            "message": "Available slots must be a non-negative integer."
        }), 400

    # Step 8: Update slots
    trek.available_slots = available_slots

    # Step 9: Save changes
    db.session.commit()

    # Step 10: Clear Redis cache
    invalidate_trek_cache()

    return jsonify({
        "message": "Trek slots updated successfully.",
        "trek": {
            "id": trek.id,
            "name": trek.name,
            "available_slots": trek.available_slots
        }
    }), 200

@staff_bp.route("/treks/<int:trek_id>/status", methods=["PUT"])
def update_trek_status(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Staff
    staff = db.session.get(User, user_id)

    if staff is None or staff.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Staff role
    if staff.role != "staff":
        return jsonify({
            "message": "Access denied. Staff only."
        }), 403

    # Step 4: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 5: Check Staff assignment
    if trek.assigned_staff_id != staff.id:
        return jsonify({
            "message": "You are not assigned to this trek."
        }), 403

    # Step 6: Receive new status
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    new_status = data.get("status")

    # Step 7: Validate status
    allowed_statuses = ["Open", "Closed", "Completed"]

    if not isinstance(new_status, str) or new_status not in allowed_statuses:
        return jsonify({
            "message": "Status must be Open, Closed, or Completed."
        }), 400

    # Step 8: Prevent reopening a completed trek
    if trek.status == "Completed" and new_status != "Completed":
        return jsonify({
            "message": "A completed trek cannot be reopened."
        }), 409

    # Step 9: Update trek status
    trek.status = new_status

    # Step 10: Save to SQLite
    db.session.commit()
    invalidate_trek_cache()

    return jsonify({
        "message": "Trek status updated successfully.",
        "trek": {
            "id": trek.id,
            "name": trek.name,
            "status": trek.status
        }
    }), 200

@staff_bp.route("/treks/<int:trek_id>/participants", methods=["GET"])
def view_trek_participants(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Staff
    staff = db.session.get(User, user_id)

    if staff is None or staff.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Staff role
    if staff.role != "staff":
        return jsonify({
            "message": "Access denied. Staff only."
        }), 403

    # Step 4: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 5: Check Staff assignment
    if trek.assigned_staff_id != staff.id:
        return jsonify({
            "message": "You are not assigned to this trek."
        }), 403

    # Step 6: Fetch active bookings
    bookings = Booking.query.filter_by(
        trek_id=trek.id,
        status="Booked"
    ).order_by(Booking.id.asc()).all()

    # Step 7: Prepare participant information
    participant_list = []

    for booking in bookings:

        participant = db.session.get(User, booking.user_id)

        if participant is None:
            continue

        participant_list.append({
            "booking_id": booking.id,
            "user_id": participant.id,
            "name": participant.name,
            "email": participant.email,
            "booking_date": booking.booking_date,
            "booking_status": booking.status
        })

    # Step 8: Return response
    return jsonify({
        "message": "Trek participants fetched successfully.",
        "trek_id": trek.id,
        "trek_name": trek.name,
        "total_participants": len(participant_list),
        "participants": participant_list
    }), 200