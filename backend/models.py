from extensions import db


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    email = db.Column(db.String(120), unique=True, nullable=False)

    password = db.Column(db.String(200), nullable=False)

    role = db.Column(db.String(20), nullable=False, default="user")

    status = db.Column(db.String(20), nullable=False, default="approved")


class Trek(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    name = db.Column(db.String(100), nullable=False)

    location = db.Column(db.String(100), nullable=False)

    difficulty = db.Column(db.String(30), nullable=False)

    duration = db.Column(db.String(50), nullable=False)

    available_slots = db.Column(db.Integer, nullable=False, default=0)

    status = db.Column(db.String(20), nullable=False, default="Open")

    assigned_staff_id = db.Column(db.Integer, nullable=True)

    start_date = db.Column(db.Date, nullable=True)

    instructions = db.Column(db.Text, nullable=True)



class Booking(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, nullable=False)

    trek_id = db.Column(db.Integer, nullable=False)

    booking_date = db.Column(db.String(50), nullable=False)

    status = db.Column(db.String(20), nullable=False, default="Booked")


class BookingExport(db.Model):
    __tablename__ = "booking_export"

    id = db.Column(db.Integer, primary_key=True)

    task_id = db.Column(
        db.String(100),
        unique=True,
        nullable=False
    )

    user_id = db.Column(
        db.Integer,
        nullable=False
    )
