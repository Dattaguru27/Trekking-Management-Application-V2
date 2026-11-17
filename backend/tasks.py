
from datetime import date, timedelta

from celery_app import celery_app
from app import app
from extensions import db
from models import Trek, Booking, User
from email_utils import send_email
from calendar import month_name
from html import escape
import csv
import os



@celery_app.task(name="tasks.send_daily_reminders")
def send_daily_reminders():

    tomorrow = date.today() + timedelta(days=1)

    with app.app_context():

        upcoming_treks = Trek.query.filter(
            Trek.start_date == tomorrow,
            Trek.status == "Open"
        ).all()

        total_sent = 0
        total_failed = 0
        total_skipped = 0

        for trek in upcoming_treks:

            bookings = Booking.query.filter_by(
                trek_id=trek.id,
                status="Booked"
            ).all()

            for booking in bookings:

                user = db.session.get(User, booking.user_id)

                if (
                    user is None
                    or user.role != "user"
                    or user.status != "approved"
                    or not user.email
                ):
                    total_skipped += 1
                    continue

                subject = f"Trek Reminder: {trek.name}"

                body = f"""Hello {user.name},

This is a reminder about your upcoming trek.

Trek Name: {trek.name}
Location: {trek.location}
Start Date: {trek.start_date.isoformat()}

Instructions:
{trek.instructions or "No special instructions."}

Please arrive on time and follow the instructions.

Thank you,
Trekking Management Team
"""

                try:
                    send_email(
                        to_email=user.email,
                        subject=subject,
                        body=body
                    )
                    total_sent += 1

                except Exception as error:
                    total_failed += 1
                    print(
                        f"Reminder failed for booking "
                        f"{booking.id}: {error}"
                    )

        return {
            "message": "Daily reminder task completed.",
            "date": tomorrow.isoformat(),
            "total_sent": total_sent,
            "total_failed": total_failed,
            "total_skipped": total_skipped
        }


@celery_app.task(name="tasks.generate_monthly_report")
def generate_monthly_report():

    # Find the previous calendar month
    today = date.today()
    first_day_this_month = today.replace(day=1)
    last_day_previous_month = (
        first_day_this_month - timedelta(days=1)
    )

    report_year = last_day_previous_month.year
    report_month = last_day_previous_month.month

    first_day = last_day_previous_month.replace(day=1)
    last_day = last_day_previous_month

    with app.app_context():

        # Find completed treks scheduled in the report month
        completed_treks = Trek.query.filter(
            Trek.status == "Completed",
            Trek.start_date >= first_day,
            Trek.start_date <= last_day
        ).all()

        
        # Count unique participating users
        participant_ids = set()

        # Count bookings for each completed trek
        popular_treks = []

        for trek in completed_treks:

            bookings = Booking.query.filter_by(
                trek_id=trek.id,
                status="Booked"
            ).all()

            for booking in bookings:
                participant_ids.add(booking.user_id)

            popular_treks.append({
                "trek_name": trek.name,
                "participants": len(bookings)
            })

        # Rank treks by number of bookings
        popular_treks.sort(
            key=lambda trek: trek["participants"],
            reverse=True
        )

        # Create HTML table rows for popular treks
        trek_rows = ""

        for trek in popular_treks:
            trek_rows += f"""
            <tr>
                <td>{escape(trek['trek_name'])}</td>
                <td>{trek['participants']}</td>
            </tr>
            """

        if not trek_rows:
            trek_rows = """
            <tr>
                <td colspan="2">No completed treks this month.</td>
            </tr>
            """

        # Generate the HTML monthly report
        html_report = f"""
        <html>
        <body style="font-family: Arial, sans-serif; padding: 20px;">

            <h2>Trekking Management - Monthly Activity Report</h2>

            <h3>{month_name[report_month]} {report_year}</h3>

            <p><b>Total Treks Conducted:</b> {len(completed_treks)}</p>

            <p><b>Total Participants:</b> {len(participant_ids)}</p>

            <h3>Popular Treks</h3>

            <table border="1" cellpadding="10"
                   style="border-collapse: collapse; width: 100%;">
                <tr>
                    <th>Trek Name</th>
                    <th>Number of Bookings</th>
                </tr>
                {trek_rows}
            </table>

            <p>Generated automatically by Trekking Management Application.</p>

        </body>
        </html>
        """

        # Find approved Admin accounts
        admins = User.query.filter_by(
            role="admin",
            status="approved"
        ).all()

        emails_sent = 0
        emails_failed = 0

        for admin in admins:
            if not admin.email:
                continue

            try:
                send_email(
                    to_email=admin.email,
                    subject=f"Monthly Trek Activity Report - {month_name[report_month]} {report_year}",
                    body=html_report,
                    html=True
                )

                emails_sent += 1

            except Exception as error:
                emails_failed += 1
                print(f"Monthly report email failed for admin {admin.id}: {error}")



        return {
            "message": "Monthly report data fetched successfully.",
            "report_month": month_name[report_month],
            "report_year": report_year,
            "total_completed_treks": len(completed_treks),
            "total_participants": len(participant_ids),
            "popular_treks": popular_treks,
            "emails_sent": emails_sent,
            "emails_failed": emails_failed
        }


@celery_app.task(name="tasks.export_booking_history")
def export_booking_history(user_id):

    with app.app_context():

        # Find the user
        user = db.session.get(User, user_id)

        if user is None or user.role != "user" or user.status != "approved":
            return {
                "message": "Invalid or inactive user."
            }

        # Fetch all bookings belonging to this user
        bookings = Booking.query.filter_by(
            user_id=user_id
        ).order_by(Booking.id.desc()).all()

        # Create the exports folder
        export_folder = os.path.join(
            app.instance_path,
            "exports"
        )

        os.makedirs(export_folder, exist_ok=True)

        # Create a unique CSV filename
        from uuid import uuid4

        filename = f"booking_history_{user_id}_{uuid4().hex}.csv"

        file_path = os.path.join(export_folder, filename)

        # Generate CSV
        with open(file_path, "w", newline="", encoding="utf-8-sig") as file:

            writer = csv.writer(file)

            writer.writerow([
                "User ID",
                "Trek Name",
                "Location",
                "Booking Status",
                "Booking Date",
                "Trek Start Date"
            ])

            for booking in bookings:

                trek = db.session.get(Trek, booking.trek_id)

                writer.writerow([
                    user_id,
                    trek.name if trek else "Trek unavailable",
                    trek.location if trek else "",
                    booking.status,
                    booking.booking_date,
                    trek.start_date.isoformat() if trek and trek.start_date else ""
                ])

        return {
            "message": "Booking history CSV generated successfully.",
            "filename": filename,
            "total_bookings": len(bookings)
        }

