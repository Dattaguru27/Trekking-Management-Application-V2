from flask import Flask
from werkzeug.security import generate_password_hash

from config import Config
from extensions import db
from models import User, Trek, Booking
from routes.auth import auth_bp
from routes.admin import admin_bp
from routes.staff import staff_bp
from routes.user import user_bp

app = Flask(__name__)

# Load configuration
app.config.from_object(Config)

# Connect SQLAlchemy with Flask
db.init_app(app)
app.register_blueprint(auth_bp, url_prefix="/api/auth")
app.register_blueprint(admin_bp, url_prefix="/api/admin")
app.register_blueprint(staff_bp, url_prefix="/api/staff")
app.register_blueprint(user_bp, url_prefix="/api/user")


@app.route("/")
def home():
    return "Trekking Management API is running!"


def create_admin():
    admin = User.query.filter_by(role="admin").first()

    if admin is None:
        admin = User(
            name="Admin",
            email="admin@gmail.com",
            password=generate_password_hash("admin123"),
            role="admin",
            status="approved"
        )

        db.session.add(admin)
        db.session.commit()

        print("Admin user created successfully.")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        create_admin()

    app.run(debug=True)