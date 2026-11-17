from flask import Blueprint, jsonify, session, request
from extensions import db
from models import User, Trek, Booking
from werkzeug.security import generate_password_hash
from cache_utils import invalidate_trek_cache
from datetime import date

admin_bp = Blueprint("admin", __name__)


@admin_bp.route("/dashboard", methods=["GET"])
def admin_dashboard():

    # Check whether the user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Check the current user's role in the database
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Your session is no longer valid."
        }), 401

    if user.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Count database records
    total_users = User.query.filter_by(role="user").count()

    total_staff = User.query.filter_by(role="staff").count()

    total_treks = Trek.query.count()

    total_bookings = Booking.query.count()

    return jsonify({
        "message": "Admin dashboard data fetched successfully.",
        "total_users": total_users,
        "total_staff": total_staff,
        "total_treks": total_treks,
        "total_bookings": total_bookings
    }), 200

@admin_bp.route("/treks", methods=["POST"])
def add_trek():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check approved Admin
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Receive trek information
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide trek details in JSON format."
        }), 400

    name = data.get("name")
    location = data.get("location")
    difficulty = data.get("difficulty")
    duration = data.get("duration")
    available_slots = data.get("available_slots")

    # New fields for daily reminders
    start_date_value = data.get("start_date")
    instructions = data.get("instructions")

    # Step 4: Validate required fields
    if (
        not isinstance(name, str) or not name.strip()
        or not isinstance(location, str) or not location.strip()
        or not isinstance(difficulty, str) or not difficulty.strip()
        or not isinstance(duration, str) or not duration.strip()
    ):
        return jsonify({
            "message": "All trek details are required."
        }), 400

    if (
        type(available_slots) is not int
        or available_slots < 0
    ):
        return jsonify({
            "message": "Available slots must be a non-negative integer."
        }), 400

    # Step 5: Validate start date
    trek_start_date = None

    if start_date_value is not None and start_date_value != "":
        if not isinstance(start_date_value, str):
            return jsonify({
                "message": "Start date must be in YYYY-MM-DD format."
            }), 400

        try:
            trek_start_date = date.fromisoformat(start_date_value)
        except ValueError:
            return jsonify({
                "message": "Invalid start date. Use YYYY-MM-DD."
            }), 400

    # Step 6: Validate instructions
    if instructions is not None and not isinstance(instructions, str):
        return jsonify({
            "message": "Instructions must be text."
        }), 400

    # Step 7: Create trek
    new_trek = Trek(
        name=name.strip(),
        location=location.strip(),
        difficulty=difficulty.strip(),
        duration=duration.strip(),
        available_slots=available_slots,
        status="Open",
        start_date=trek_start_date,
        instructions=instructions.strip() if instructions else None
    )

    # Step 8: Save to SQLite
    db.session.add(new_trek)
    db.session.commit()

    # Step 9: Clear Redis cache
    invalidate_trek_cache()

    # Step 10: Return response
    return jsonify({
        "message": "Trek added successfully.",
        "trek": {
            "id": new_trek.id,
            "name": new_trek.name,
            "location": new_trek.location,
            "difficulty": new_trek.difficulty,
            "duration": new_trek.duration,
            "available_slots": new_trek.available_slots,
            "status": new_trek.status,
            "start_date": (
                new_trek.start_date.isoformat()
                if new_trek.start_date else None
            ),
            "instructions": new_trek.instructions
        }
    }), 201



@admin_bp.route("/treks", methods=["GET"])
def view_all_treks():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Get all treks
    treks = Trek.query.order_by(Trek.id.asc()).all()

    # Step 4: Convert trek records into JSON
    trek_list = []

    for trek in treks:
        trek_list.append({
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "status": trek.status,
            "assigned_staff_id": trek.assigned_staff_id,

            # New fields for daily reminders
            "start_date": (
                trek.start_date.isoformat()
                if trek.start_date else None
            ),
            "instructions": trek.instructions
        })

    # Step 5: Return the result
    return jsonify({
        "message": "Treks fetched successfully.",
        "total_treks": len(trek_list),
        "treks": trek_list
    }), 200


@admin_bp.route("/treks/<int:trek_id>", methods=["PUT"])
def edit_trek(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 4: Receive updated details
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    # Step 5: Validate text fields
    text_fields = ["name", "location", "difficulty", "duration"]

    for field in text_fields:
        if field in data:
            value = data[field]

            if not isinstance(value, str) or not value.strip():
                return jsonify({
                    "message": f"{field} must be a non-empty string."
                }), 400

    # Validate available slots
    if "available_slots" in data:
        slots = data["available_slots"]

        if type(slots) is not int or slots < 0:
            return jsonify({
                "message": "Available slots must be a non-negative integer."
            }), 400

    # Validate status
    if "status" in data:
        if data["status"] not in ["Open", "Closed", "Completed"]:
            return jsonify({
                "message": "Invalid trek status."
            }), 400

    # Step 6: Validate new fields
    new_start_date = trek.start_date

    if "start_date" in data:
        start_date_value = data["start_date"]

        if start_date_value is None or start_date_value == "":
            new_start_date = None

        elif not isinstance(start_date_value, str):
            return jsonify({
                "message": "Start date must be in YYYY-MM-DD format."
            }), 400

        else:
            try:
                new_start_date = date.fromisoformat(start_date_value)
            except ValueError:
                return jsonify({
                    "message": "Invalid start date. Use YYYY-MM-DD."
                }), 400

    new_instructions = trek.instructions

    if "instructions" in data:
        instructions_value = data["instructions"]

        if instructions_value is not None and not isinstance(
            instructions_value, str
        ):
            return jsonify({
                "message": "Instructions must be text."
            }), 400

        new_instructions = (
            instructions_value.strip()
            if instructions_value else None
        )

    # Step 7: Apply validated changes
    for field in text_fields:
        if field in data:
            setattr(trek, field, data[field].strip())

    if "available_slots" in data:
        trek.available_slots = data["available_slots"]

    if "status" in data:
        trek.status = data["status"]

    if "start_date" in data:
        trek.start_date = new_start_date

    if "instructions" in data:
        trek.instructions = new_instructions

    # Step 8: Save changes
    db.session.commit()

    # Clear Redis cache
    invalidate_trek_cache()

    return jsonify({
        "message": "Trek updated successfully.",
        "trek": {
            "id": trek.id,
            "name": trek.name,
            "location": trek.location,
            "difficulty": trek.difficulty,
            "duration": trek.duration,
            "available_slots": trek.available_slots,
            "status": trek.status,
            "start_date": (
                trek.start_date.isoformat()
                if trek.start_date else None
            ),
            "instructions": trek.instructions
        }
    }), 200


@admin_bp.route("/treks/<int:trek_id>", methods=["DELETE"])
def delete_trek(trek_id):

    # Step 1: Check whether the user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    user = db.session.get(User, user_id)

    if user is None or user.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if user.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 4: Check whether bookings exist
    existing_booking = Booking.query.filter_by(
        trek_id=trek_id
    ).first()

    if existing_booking:
        return jsonify({
            "message": "Cannot delete a trek with booking history. Close the trek instead."
        }), 409

    # Step 5: Remember the trek name
    trek_name = trek.name

    # Step 6: Delete the trek
    db.session.delete(trek)
    db.session.commit()
    invalidate_trek_cache()

    return jsonify({
        "message": "Trek deleted successfully.",
        "deleted_trek": trek_name
    }), 200

@admin_bp.route("/staff", methods=["POST"])
def create_staff():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    admin = db.session.get(User, user_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Receive Staff information
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    name = data.get("name")
    email = data.get("email")
    password = data.get("password")

    # Step 4: Validate information
    if (
        not isinstance(name, str) or not name.strip()
        or not isinstance(email, str) or not email.strip()
        or not isinstance(password, str) or not password
    ):
        return jsonify({
            "message": "Name, email and password are required."
        }), 400

    name = name.strip()
    email = email.strip().lower()

    if len(password) < 8:
        return jsonify({
            "message": "Password must contain at least 8 characters."
        }), 400

    # Step 5: Check duplicate email
    existing_staff = User.query.filter_by(email=email).first()

    if existing_staff:
        return jsonify({
            "message": "Email already registered."
        }), 409

    # Step 6: Create Staff
    new_staff = User(
        name=name,
        email=email,
        password=generate_password_hash(password),
        role="staff",
        status="approved"
    )

    # Step 7: Save to SQLite
    db.session.add(new_staff)
    db.session.commit()

    return jsonify({
        "message": "Staff created successfully.",
        "staff": {
            "id": new_staff.id,
            "name": new_staff.name,
            "email": new_staff.email,
            "role": new_staff.role,
            "status": new_staff.status
        }
    }), 201

@admin_bp.route("/staff", methods=["GET"])
def view_all_staff():

    # Step 1: Check whether the user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    admin = db.session.get(User, user_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Fetch all Staff accounts
    staff_members = User.query.filter_by(
        role="staff"
    ).order_by(User.id.asc()).all()

    # Step 4: Convert Staff records into JSON
    staff_list = []

    for staff in staff_members:
        staff_list.append({
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "role": staff.role,
            "status": staff.status
        })

    # Step 5: Return the result
    return jsonify({
        "message": "Staff fetched successfully.",
        "total_staff": len(staff_list),
        "staff": staff_list
    }), 200

@admin_bp.route("/treks/<int:trek_id>/assign-staff", methods=["PUT"])
def assign_staff(trek_id):

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Check Admin permission
    admin = db.session.get(User, user_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 3: Find the trek
    trek = db.session.get(Trek, trek_id)

    if trek is None:
        return jsonify({
            "message": "Trek not found."
        }), 404

    # Step 4: Receive Staff ID
    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        return jsonify({
            "message": "Please provide valid JSON data."
        }), 400

    staff_id = data.get("staff_id")

    if type(staff_id) is not int or staff_id <= 0:
        return jsonify({
            "message": "Valid Staff ID is required."
        }), 400

    # Step 5: Find the Staff member
    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        return jsonify({
            "message": "Staff member not found."
        }), 404

    # Step 6: Check Staff status
    if staff.status != "approved":
        return jsonify({
            "message": "Only approved Staff can be assigned."
        }), 403

    # Step 7: Assign Staff to Trek
    trek.assigned_staff_id = staff.id

    # Step 8: Save changes
    db.session.commit()

    return jsonify({
        "message": "Staff assigned to trek successfully.",
        "trek": {
            "id": trek.id,
            "name": trek.name,
            "assigned_staff_id": staff.id,
            "assigned_staff_name": staff.name
        }
    }), 200

@admin_bp.route("/users", methods=["GET"])
def view_all_users():

    # Step 1: Check login
    user_id = session.get("user_id")

    if not user_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, user_id)

    if admin is None or admin.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Fetch all registered Trekkers
    users = User.query.filter_by(
        role="user"
    ).order_by(User.id.asc()).all()

    # Step 5: Prepare user information
    user_list = []

    for user in users:
        user_list.append({
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "role": user.role,
            "status": user.status
        })

    # Step 6: Return JSON response
    return jsonify({
        "message": "Users fetched successfully.",
        "total_users": len(user_list),
        "users": user_list
    }), 200

@admin_bp.route("/users/<int:user_id>/blacklist", methods=["PUT"])
def blacklist_user(user_id):

    # Step 1: Check Admin login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Find the User
    user = db.session.get(User, user_id)

    if user is None or user.role != "user":
        return jsonify({
            "message": "User not found."
        }), 404

    # Step 5: Check existing status
    if user.status == "blacklisted":
        return jsonify({
            "message": "User is already blacklisted."
        }), 409

    # Step 6: Blacklist User
    user.status = "blacklisted"

    # Step 7: Save changes
    db.session.commit()

    return jsonify({
        "message": "User blacklisted successfully.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "status": user.status
        }
    }), 200

@admin_bp.route("/users/<int:user_id>/unblacklist", methods=["PUT"])
def unblacklist_user(user_id):

    # Step 1: Check Admin login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Find User
    user = db.session.get(User, user_id)

    if user is None or user.role != "user":
        return jsonify({
            "message": "User not found."
        }), 404

    # Step 5: Check current status
    if user.status != "blacklisted":
        return jsonify({
            "message": "User is not blacklisted."
        }), 409

    # Step 6: Restore User account
    user.status = "approved"

    # Step 7: Save changes
    db.session.commit()

    return jsonify({
        "message": "User unblacklisted successfully.",
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "status": user.status
        }
    }), 200

@admin_bp.route("/staff/<int:staff_id>/blacklist", methods=["PUT"])
def blacklist_staff(staff_id):

    # Step 1: Check Admin login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Find Staff member
    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        return jsonify({
            "message": "Staff member not found."
        }), 404

    # Step 5: Check current status
    if staff.status == "blacklisted":
        return jsonify({
            "message": "Staff is already blacklisted."
        }), 409

    # Step 6: Blacklist Staff
    staff.status = "blacklisted"

    # Step 7: Save changes
    db.session.commit()

    return jsonify({
        "message": "Staff blacklisted successfully.",
        "staff": {
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "status": staff.status
        }
    }), 200

@admin_bp.route("/staff/<int:staff_id>/unblacklist", methods=["PUT"])
def unblacklist_staff(staff_id):

    # Step 1: Check Admin login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Find Staff member
    staff = db.session.get(User, staff_id)

    if staff is None or staff.role != "staff":
        return jsonify({
            "message": "Staff member not found."
        }), 404

    # Step 5: Check current status
    if staff.status != "blacklisted":
        return jsonify({
            "message": "Staff is not blacklisted."
        }), 409

    # Step 6: Restore Staff account
    staff.status = "approved"

    # Step 7: Save changes
    db.session.commit()

    return jsonify({
        "message": "Staff unblacklisted successfully.",
        "staff": {
            "id": staff.id,
            "name": staff.name,
            "email": staff.email,
            "status": staff.status
        }
    }), 200

@admin_bp.route("/search", methods=["GET"])
def search_users_and_staff():

    # Step 1: Check Admin login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Step 2: Find logged-in Admin
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()

        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    # Step 3: Check Admin role
    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Step 4: Read search parameters
    name = request.args.get("name", "").strip()
    user_id = request.args.get("id", "").strip()
    role = request.args.get("role", "").strip().lower()

    # Step 5: Search Users and Staff only
    query = User.query.filter(
        User.role.in_(["user", "staff"])
    )

    # Step 6: Filter by name
    if name:
        query = query.filter(
            User.name.ilike(f"%{name}%")
        )

    # Step 7: Filter by ID
    if user_id:
        if not user_id.isdigit():
            return jsonify({
                "message": "ID must be a positive integer."
            }), 400

        if int(user_id) <= 0:
            return jsonify({
                "message": "ID must be a positive integer."
            }), 400

        query = query.filter(
            User.id == int(user_id)
        )

    # Step 8: Filter by role
    if role:
        if role not in ["user", "staff"]:
            return jsonify({
                "message": "Role must be user or staff."
            }), 400

        query = query.filter(
            User.role == role
        )

    # Step 9: Fetch matching records
    results = query.order_by(User.id.asc()).all()

    # Step 10: Prepare response
    account_list = []

    for account in results:
        account_list.append({
            "id": account.id,
            "name": account.name,
            "email": account.email,
            "role": account.role,
            "status": account.status
        })

    # Step 11: Return JSON
    return jsonify({
        "message": "Search completed successfully.",
        "total_results": len(account_list),
        "results": account_list
    }), 200

@admin_bp.route("/bookings", methods=["GET"])
def view_all_bookings():
    # Check login
    admin_id = session.get("user_id")

    if not admin_id:
        return jsonify({
            "message": "Please login first."
        }), 401

    # Check Admin permission
    admin = db.session.get(User, admin_id)

    if admin is None or admin.status != "approved":
        session.clear()
        return jsonify({
            "message": "Session is no longer valid."
        }), 401

    if admin.role != "admin":
        return jsonify({
            "message": "Access denied. Admin only."
        }), 403

    # Fetch all bookings with user and trek details
    records = (
        db.session.query(Booking, User, Trek)
        .outerjoin(User, Booking.user_id == User.id)
        .outerjoin(Trek, Booking.trek_id == Trek.id)
        .order_by(Booking.id.desc())
        .all()
    )

    booking_list = []

    for booking, user, trek in records:
        booking_list.append({
            "id": booking.id,
            "user_id": booking.user_id,
            "user_name": user.name if user else "Unknown User",
            "trek_id": booking.trek_id,
            "trek_name": trek.name if trek else "Unknown Trek",
            "location": trek.location if trek else "N/A",
            "booking_date": booking.booking_date,
            "status": booking.status
        })

    return jsonify({
        "message": "All bookings fetched successfully.",
        "total_bookings": len(booking_list),
        "bookings": booking_list
    }), 200
