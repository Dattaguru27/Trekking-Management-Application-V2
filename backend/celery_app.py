
from celery import Celery
from celery.schedules import crontab


celery_app = Celery(
    "trekking_tasks",
    broker="redis://localhost:6379/1",
    backend="redis://localhost:6379/2",
    include=["tasks"]
)

celery_app.conf.update(
    timezone="Asia/Kolkata",
    enable_utc=True
)

# Schedule mandatory background jobs
celery_app.conf.beat_schedule = {
    "daily-trek-reminders": {
        "task": "tasks.send_daily_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    "monthly-admin-report": {
        "task": "tasks.generate_monthly_report",
        "schedule": crontab(
            day_of_month=1,
            hour=8,
            minute=0
        ),
    },
}



@celery_app.task
def test_celery():
    return "Celery and Redis are working!"
