# app/services/anomaly_scheduler.py
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.services.anomaly_detector import detector
from app.db.mongo import MongoDB

scheduler = AsyncIOScheduler()

async def scheduled_anomaly_check():
    household_ids = await MongoDB.distinct("events", "household_id")
    for h_id in household_ids:
        try:
            await detector.check_anomalies(h_id)
        except Exception as e:
            print("Error in scheduled anomaly detection:", e)

def start_scheduler():
    times = [(9,0), (11,0), (14,0), (22,0)]
    for hour, minute in times:
        scheduler.add_job(
            scheduled_anomaly_check,
            trigger='cron',
            hour=hour,
            minute=minute,
            id=f'anomaly_check_{hour}_{minute}',
            replace_existing=True
        )
    scheduler.start()
    print("✓ Scheduled anomaly checks started")

def shutdown_scheduler():
    if scheduler.running:
        scheduler.shutdown(wait=True)
        print("✓ Scheduler stopped")
