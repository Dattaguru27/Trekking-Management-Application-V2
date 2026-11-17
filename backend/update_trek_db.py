
from app import app
from extensions import db
from sqlalchemy import text

with app.app_context():

    # Use the same database as the Flask application
    database_path = db.engine.url.database
    print("Database:", database_path)

    # Check existing columns
    columns = db.session.execute(
        text("PRAGMA table_info(trek)")
    ).fetchall()

    existing_columns = [column[1] for column in columns]

    if not existing_columns:
        raise RuntimeError(
            "Trek table not found. Check the database path."
        )

    # Add start_date if missing
    if "start_date" not in existing_columns:
        db.session.execute(
            text("ALTER TABLE trek ADD COLUMN start_date DATE")
        )
        print("start_date column added")
    else:
        print("start_date already exists")

    # Add instructions if missing
    if "instructions" not in existing_columns:
        db.session.execute(
            text("ALTER TABLE trek ADD COLUMN instructions TEXT")
        )
        print("instructions column added")
    else:
        print("instructions already exists")

    db.session.commit()

    print("Database updated successfully!")
