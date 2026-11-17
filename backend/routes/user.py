from flask import Blueprint, jsonify, session, request
from datetime import datetime, timezone
from sqlalchemy.exc import IntegrityError
from cache_utils import get_cached_treks, set_cached_treks
from cache_utils import invalidate_trek_cache
from extensions import db
from models import User, Trek, Booking, BookingExport
import os
from flask import send_from_directory
from celery.result import AsyncResult

user_bp = Blueprint("user", __name__)



@user_bp.route("/treks", methods=["GET"])
def view_available_treks():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find the logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Check Redis cache
    cached_treks = get_cached_treks()

    if cached_treks is not None:
        print("REDIS CACHE HIT")

        return jsonify({
            "message": "Available treks fetched successfully.",
            "total_available_treks": len(cached_treks),
            "treks": cached_treks
        }), 200

    # Step 5: Cache MISS - fetch from SQLite
    print("REDIS CACHE MISS")

    available_treks = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    ).order_by(Trek.id.asc()).all()

    # Step 6: Prepare trek information
    trek_list = []

    for trek in available_treks:
        trek_list.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "status": trek.status
        })

    # Step 7: Save trek list in Redis
    set_cached_treks(trek_list)

    # Step 8: Return JSON response
    return jsonify({
        "message": "Available treks fetched successfully.",
        "total_available_treks": len(trek_list),
        "treks": trek_list
    }), 200


@user_bp.route("/treks/search", methods=["GET"])
def search_treks():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Get search and filter values
    search = request.args.get("search", "").strip()
    location = request.args.get("location", "").strip()
    difficulty = request.args.get("difficulty", "").strip()

    # Step 5: Start with available treks
    query = Trek.query.filter(
        Trek.status == "Open",
        Trek.available_slots > 0
    )

    # Step 6: Filter by trek name
    if search:
        query = query.filter(
            Trek.name.ilike(f"%{search}%")
        )

    # Step 7: Filter by location
    if location:
        query = query.filter(
            Trek.location.ilike(f"%{location}%")
        )

    # Step 8: Filter by difficulty
    if difficulty:
        query = query.filter(
            Trek.difficulty.ilike(difficulty)
        )

    # Step 9: Fetch matching treks
    treks = query.order_by(Trek.id.asc()).all()

    # Step 10: Prepare JSON response
    trek_list = []

    for trek in treks:
        trek_list.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "status": trek.status
        })

    return jsonify({
        "message": "Treks searched successfully.",
        "total_results": len(trek_list),
        "treks": trek_list
    }), 200

@user_bp.route("/treks/<int:trek_id>/book", methods=["POST"])
def book_trek(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 5: Check trek status
    if trek.status != "Open":
        return jsonify({
            "message": "This trek is not open for booking."
        }), 400

    # Step 6: Check available slots
    if trek.available_slots <= 0:
        return jsonify({
            "message": "No slots available for this trek."
        }), 400

    # Step 7: Prevent duplicate active bookings
    existing_booking = Booking.query.filter_by(
        user_id=user.id,
        trek_id=trek.id,
        status="Booked"
    ).first()

    if existing_booking:
        return jsonify({
            "message": "You have already booked this trek."
        }), 409

    # Step 8: Reduce slots only if a slot is still available
    updated_rows = Trek.query.filter(
        Trek.id == trek.id,
        Trek.status == "Open",
        Trek.available_slots > 0
    ).update({
        Trek.available_slots: Trek.available_slots - 1
    }, synchronize_session=False)

    if updated_rows == 0:
        db.session.rollback()
        return jsonify({
            "message": "No available slots or trek is closed."
        }), 409

    # Step 9: Create booking
    booking = Booking(
        user_id=user.id,
        trek_id=trek.id,
        booking_date=datetime.now(timezone.utc).isoformat(),
        status="Booked"
    )

    db.session.add(booking)

    # Step 10: Save booking and slot update together
    try:
        db.session.commit()
        invalidate_trek_cache()
    except IntegrityError:
        db.session.rollback()
        return jsonify({
            "message": "Booking could not be completed."
        }), 409

    db.session.refresh(trek)

    # Step 11: Return response
    return jsonify({
        "message": "Trek booked successfully.",
        "booking": {
            "id": booking.id,
            "user_id": booking.user_id,
            "trek_id": booking.trek_id,
            "trek_name": trek.name,
            "booking_date": booking.booking_date,
            "status": booking.status
        },
        "remaining_slots": trek.available_slots
    }), 201

@user_bp.route("/bookings", methods=["GET"])
def view_booking_history():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Fetch only this user's bookings
    bookings = Booking.query.filter_by(
        user_id=user.id
    ).order_by(Booking.id.desc()).all()

    # Step 5: Prepare booking history
    booking_list = []

    for booking in bookings:

        trek = db.session.get(Trek, booking.trek_id)

        booking_list.append({
            "booking_id": booking.id,
            "trek_id": booking.trek_id,
            "trek_name": trek.name if trek else "Trek unavailable",
            "location": trek.location if trek else None,
            "difficulty": trek.difficulty if trek else None,
            "duration": trek.duration if trek else None,
            "trek_status": trek.status if trek else None,
            "booking_date": booking.booking_date,
            "booking_status": booking.status
        })

    # Step 6: Return response
    return jsonify({
        "message": "Booking history fetched successfully.",
        "total_bookings": len(booking_list),
        "bookings": booking_list
    }), 200

@user_bp.route("/bookings/<int:booking_id>/cancel", methods=["PUT"])
def cancel_booking(booking_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Find only this user's booking
    booking = Booking.query.filter_by(
        id=booking_id,
        user_id=user.id
    ).first()

    if booking is None:
        return jsonify({
            "message": "Booking not found."
        }), 404

    # Step 5: Check booking status
    if booking.status != "Booked":
        return jsonify({
            "message": "This booking is already cancelled or inactive."
        }), 409

    # Step 6: Find the trek
    trek = db.session.get(Trek, booking.trek_id)

    if trek is None:
        return jsonify({
            "message": "Associated trek not found."
        }), 404

    # Step 7: Prevent cancellation after completion
    if trek.status == "Completed":
        return jsonify({
            "message": "Cannot cancel a completed trek."
        }), 409

    # Step 8: Atomically change booking status
    updated_rows = Booking.query.filter(
        Booking.id == booking.id,
        Booking.user_id == user.id,
        Booking.status == "Booked"
    ).update({
        Booking.status: "Cancelled"
    }, synchronize_session=False)

    if updated_rows == 0:
        db.session.rollback()
        return jsonify({
            "message": "Booking is no longer active."
        }), 409

    # Step 9: Restore one available slot
    Trek.query.filter(
        Trek.id == trek.id
    ).update({
        Trek.available_slots: Trek.available_slots + 1
    }, synchronize_session=False)

    # Step 10: Save both changes together
    try:
        db.session.commit()
        invalidate_trek_cache()
    except Exception:
        db.session.rollback()
        return jsonify({
            "message": "Cancellation could not be completed."
        }), 500

    # Step 11: Return updated information
    db.session.refresh(booking)
    db.session.refresh(trek)

    return jsonify({
        "message": "Booking cancelled successfully.",
        "booking": {
            "id": booking.id,
            "trek_id": booking.trek_id,
            "status": booking.status
        },
        "available_slots": trek.available_slots
    }), 200

@user_bp.route("/profile", methods=["GET"])
def view_profile():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Return profile details
    return jsonify({
        "message": "Profile fetched successfully.",
        "profile": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }), 200

@user_bp.route("/profile", methods=["PUT"])
def update_profile():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check User role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Read JSON data
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    # Step 5: Allow only name and email updates
    allowed_fields = {"name", "email"}

    if not data or not set(data.keys()).issubset(allowed_fields):
        return jsonify({
            "message": "Only name and email can be updated."
        }), 400

    # Step 6: Validate name
    if "name" in data:
        if not isinstance(data["name"], str):
            return jsonify({
                "message": "Name must be text."
            }), 400

        name = data["name"].strip()

        if not name or len(name) > 100:
            return jsonify({
                "message": "Name must contain 1 to 100 characters."
            }), 400

    else:
        name = user.name

    # Step 7: Validate email
    if "email" in data:
        if not isinstance(data["email"], str):
            return jsonify({
                "message": "Email must be text."
            }), 400

        email = data["email"].strip().lower()

        if (
            not email
            or len(email) > 120
            or email.count("@") != 1
            or "." not in email.split("@")[1]
        ):
            return jsonify({
                "message": "Please provide a valid email address."
            }), 400

        # Check if another account uses this email
        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:
            return jsonify({
                "message": "Email is already registered."
            }), 409

    else:
        email = user.email

    # Step 8: Update profile
    user.name = name
    user.email = email

    # Step 9: Save changes
    try:
        db.session.commit()

    except IntegrityError:
        db.session.rollback()

        return jsonify({
            "message": "Email is already registered."
        }), 409

    # Step 10: Return updated profile
    return jsonify({
        "message": "Profile updated successfully.",
        "profile": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        }
    }), 200

@user_bp.route("/bookings/export", methods=["POST"])
def request_booking_export():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check user role
    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 4: Import the task after Flask has started
    from tasks import export_booking_history

    
    # Step 5: Start Celery background task
    task = export_booking_history.delay(user.id)

    # Step 6: Save task ownership in SQLite
    export_record = BookingExport(
        task_id=task.id,
        user_id=user.id
    )

    try:
        db.session.add(export_record)
        db.session.commit()

    except Exception:
        db.session.rollback()

        return jsonify({
            "message": "Could not save export request."
        }), 500

    # Step 7: Return task ID
    return jsonify({
        "message": "Booking history export started.",
        "task_id": task.id
    }), 202



@user_bp.route("/bookings/export/<task_id>/status", methods=["GET"])
def check_booking_export_status(task_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Verify logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 3: Verify export ownership
    export_record = BookingExport.query.filter_by(
        task_id=task_id,
        user_id=user.id
    ).first()

    if export_record is None:
        return jsonify({
            "message": "Export task not found."
        }), 404

    # Step 4: Check Celery task status
    from celery_app import celery_app

    task = AsyncResult(task_id, app=celery_app)

    if task.state == "SUCCESS":
        result = task.result

        if not isinstance(result, dict) or "filename" not in result:
            return jsonify({
                "message": "Export did not produce a CSV file.",
                "status": "FAILED"
            }), 500

        return jsonify({
            "message": "Booking history CSV is ready.",
            "status": "SUCCESS",
            "filename": result["filename"]
        }), 200

    if task.state == "FAILURE":
        return jsonify({
            "message": "CSV export failed.",
            "status": "FAILURE"
        }), 500

    return jsonify({
        "message": "CSV export is processing.",
        "status": task.state
    }), 200

@user_bp.route("/bookings/export/<task_id>/download", methods=["GET"])
def download_booking_export(task_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Verify logged-in user
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "user":
        return jsonify({
            "message": "Access denied. Users only."
        }), 403

    # Step 3: Verify CSV export belongs to this user
    export_record = BookingExport.query.filter_by(
        task_id=task_id,
        user_id=user.id
    ).first()

    if export_record is None:
        return jsonify({
            "message": "Export not found."
        }), 404

    # Step 4: Check Celery task
    from celery_app import celery_app

    task = AsyncResult(task_id, app=celery_app)

    if task.state != "SUCCESS":
        return jsonify({
            "message": "CSV export is not ready.",
            "status": task.state
        }), 409

    # Step 5: Get generated filename
    result = task.result

    if not isinstance(result, dict):
        return jsonify({
            "message": "Invalid export result."
        }), 500

    filename = result.get("filename")

    if not filename:
        return jsonify({
            "message": "CSV file was not generated."
        }), 500

    # Step 6: Verify the expected filename
    expected_prefix = f"booking_history_{user.id}_"

    if (
        not filename.startswith(expected_prefix)
        or not filename.endswith(".csv")
        or os.path.basename(filename) != filename
    ):
        return jsonify({
            "message": "Invalid CSV filename."
        }), 500

    # Step 7: Locate CSV file
    from app import app

    export_folder = os.path.join(
        app.instance_path,
        "exports"
    )

    file_path = os.path.join(export_folder, filename)

    if not os.path.isfile(file_path):
        return jsonify({
            "message": "CSV file not found."
        }), 404

    # Step 8: Download CSV
    return send_from_directory(
        export_folder,
        filename,
        as_attachment=True,
        download_name="booking_history.csv",
        mimetype="text/csv"
    )
