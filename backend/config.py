import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "trekking-management-secret-key")

    SQLALCHEMY_DATABASE_URI = "sqlite:///trek.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Redis Configuration
    REDIS_HOST = "localhost"
    REDIS_PORT = 6379

    # Email configuration for Celery notifications
    SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USERNAME = os.environ.get("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.environ.get("SMTP_PASSWORD", "")
    SMTP_SENDER = os.environ.get("SMTP_SENDER", "")

