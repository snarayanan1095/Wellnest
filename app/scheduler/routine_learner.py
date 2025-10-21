from app.db.mongo import MongoDB
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import statistics


# Global scheduler instance
scheduler = AsyncIOScheduler()

def get_yesterday_range():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return yesterday, today

def extract_routine(events):
    wake_up_time, bed_time, first_kitchen = None, None, None
    bathroom_first, bathroom_count = None, 0
    first_bedroom_motion, last_bedroom_motion = None, None
    activity_start, activity_end = None, None

    events_sorted = sorted(events, key=lambda x: x["timestamp"])

    for event in events_sorted:
        ts = event["timestamp"][11:16]  # 'YYYY-MM-DDTHH:MM:SS' -> extract HH:MM
        stype = event["sensor_type"]
        loc = event["location"]
        val = event["value"]

        # Track overall activity window
        if activity_start is None:
            activity_start = ts
        activity_end = ts

        # Bed presence: value is stored as string "True"/"False"
        if stype == "bed_presence":
            if val in ["False", "false", False] and not wake_up_time:
                wake_up_time = ts
            if val in ["True", "true", True]:
                bed_time = ts  # will be overwritten until last

        # Kitchen activity
        if stype == "motion" and loc == "kitchen":
            if val in ["True", "true", True] and not first_kitchen:
                first_kitchen = ts

        # Bathroom activity
        if stype == "motion" and "bathroom" in loc:
            if val in ["True", "true", True]:
                if not bathroom_first:
                    bathroom_first = ts
                bathroom_count += 1

        # Bedroom motion (backup for wake/sleep detection if bed sensor missing)
        if stype == "motion" and "bedroom" in loc:
            if val in ["True", "true", True]:
                if not first_bedroom_motion:
                    first_bedroom_motion = ts
                last_bedroom_motion = ts

    # Use bedroom motion as fallback for wake/bed times
    if not wake_up_time and first_bedroom_motion:
        wake_up_time = first_bedroom_motion
    if not bed_time and last_bedroom_motion:
        bed_time = last_bedroom_motion

    #FUTURE: Add more routine metrics as needed
    return {
        "wake_up_time": wake_up_time,
        "bed_time": bed_time,
        "first_kitchen_time": first_kitchen,
        "bathroom_first_time": bathroom_first,
        "total_bathroom_events": bathroom_count,
        "activity_start": activity_start,
        "activity_end": activity_end,
        "total_events": len(events)
    }

def generate_summary(profile_dict):
    """Generate a human-readable summary of the routine"""
    #FUTURE: Use NIM LLM for better summaries
    parts = []

    if profile_dict.get("wake_up_time"):
        parts.append(f"Woke up at {profile_dict['wake_up_time']}")
    elif profile_dict.get("activity_start"):
        parts.append(f"First activity at {profile_dict['activity_start']}")

    if profile_dict.get("first_kitchen_time"):
        parts.append(f"kitchen activity at {profile_dict['first_kitchen_time']}")

    if profile_dict.get("total_bathroom_events", 0) > 0:
        parts.append(f"{profile_dict['total_bathroom_events']} bathroom visits (first at {profile_dict.get('bathroom_first_time', 'unknown')})")

    if profile_dict.get("bed_time"):
        parts.append(f"went to bed at {profile_dict['bed_time']}")
    elif profile_dict.get("activity_end"):
        parts.append(f"last activity at {profile_dict['activity_end']}")

    if profile_dict.get("total_events"):
        parts.append(f"Total {profile_dict['total_events']} sensor events")

    return ". ".join(parts) + "." if parts else "No significant activity detected"

async def save_profile(household_id, profile_dict, summary_text=""):
    # Generate summary if not provided
    if not summary_text:
        summary_text = generate_summary(profile_dict)

    date = datetime.now().strftime("%Y-%m-%d")

    profile_dict.update({
        "_id": f"{household_id}_{date}",  # Composite key: ensures one routine per household per day
        "household_id": household_id,
        "date": date,
        "summary_text": summary_text
    })
    await MongoDB.write("daily_routines", profile_dict)
    print(f"Saved routine profile for {household_id}: {summary_text}")

async def batch_routine_learner_daily():
    # Fetch yesterday's events once for all households
    start, end = get_yesterday_range()

    # Convert datetime to ISO string format to match MongoDB storage (timestamps are stored as strings)
    start_str = start.strftime("%Y-%m-%dT%H:%M:%S")
    end_str = end.strftime("%Y-%m-%dT%H:%M:%S")
    print(f"🔍 Searching for events between {start_str} and {end_str}", flush=True)

    query = {
        "timestamp": {"$gte": start_str, "$lt": end_str}
    }
    all_events = await MongoDB.read("events", query=query, limit=10000)
    print(f"📊 Found {len(all_events)} total events", flush=True)

    if not all_events:
        print("⚠️ No events found for yesterday. The routine learner needs events to process.", flush=True)
        return {
            "status": "no_data",
            "message": f"No events found between {start_str} and {end_str}",
            "events_found": 0,
            "households_processed": 0
        }

    # Group events by household_id
    events_by_household = {}
    # FUTURE: Get all events has a cap of 10,000. Need to implement pagination for larger datasets.
    for event in all_events:
        h_id = event["household_id"]
        if h_id not in events_by_household:
            events_by_household[h_id] = []
        events_by_household[h_id].append(event)

    print(f"🏠 Processing {len(events_by_household)} households", flush=True)

    # Process each household's events
    processed_count = 0
    for h_id, events in events_by_household.items():
        if not events:
            print(f"No events found for {h_id}", flush=True)
            continue
        print(f"  → Processing household {h_id} with {len(events)} events", flush=True)
        routine = extract_routine(events)
        await save_profile(h_id, routine)
        processed_count += 1

    print("✅ Batch routine learning completed", flush=True)
    return {
        "status": "success",
        "message": f"Processed {processed_count} households",
        "events_found": len(all_events),
        "households_processed": processed_count,
        "time_range": f"{start_str} to {end_str}"
    }

async def aggregate_baselines(n_days=7, baseline_collection="routine_baselines", daily_routines_collection="daily_routines"):
    """
    Aggregate daily routines for each household over the past n_days and save a baseline profile.
    """
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start_period = today - timedelta(days=n_days)
    start_str = start_period.strftime("%Y-%m-%d")
    end_str = today.strftime("%Y-%m-%d")

    # Get distinct households from daily_routines collection
    pipeline = [
        {"$match": {"date": {"$gte": start_str, "$lt": end_str}}},
        {"$group": {"_id": "$household_id"}}
    ]
    households = [d["_id"] for d in await MongoDB.aggregate(daily_routines_collection, pipeline)]

    for h_id in households:
        # Get the last n_days daily routine docs for this household
        query = {
            "household_id": h_id,
            "date": {"$gte": start_str, "$lt": end_str}
        }
        docs = await MongoDB.read(daily_routines_collection, query=query, limit=n_days)
        # if not docs or len(docs) < 3:  # Skip sparse data
        #     print(f"Not enough daily data to aggregate baseline for {h_id}")
        #     continue

        def timestr2minutes(tstr):
            # Converts 'HH:MM' to minutes since midnight
            try:
                h, m = map(int, tstr.split(":"))
                return h * 60 + m
            except:
                return None

        # Helper to get stat summaries for a field
        def stat_summary(data):
            values = [timestr2minutes(x) for x in data if x]
            if not values:
                return {}
            return {
                "median": f"{int(statistics.median(values)//60):02d}:{int(statistics.median(values)%60):02d}",
                "mean": f"{int(statistics.mean(values)//60):02d}:{int(statistics.mean(values)%60):02d}",
                "std_dev_minutes": round(statistics.stdev(values), 2) if len(values) > 1 else 0,
                "earliest": f"{int(min(values)//60):02d}:{int(min(values)%60):02d}",
                "latest": f"{int(max(values)//60):02d}:{int(max(values)%60):02d}"
            }

        # Field aggregations
        wake_times = [d.get("wake_up_time") for d in docs if d.get("wake_up_time")]
        bed_times = [d.get("bed_time") for d in docs if d.get("bed_time")]
        kitchen_times = [d.get("first_kitchen_time") for d in docs if d.get("first_kitchen_time")]
        bathroom_firsts = [d.get("bathroom_first_time") for d in docs if d.get("bathroom_first_time")]
        bathroom_counts = [d.get("total_bathroom_events") for d in docs if d.get("total_bathroom_events") is not None]
        activity_starts = [d.get("activity_start") for d in docs if d.get("activity_start")]
        activity_ends = [d.get("activity_end") for d in docs if d.get("activity_end")]
        total_events = [d.get("total_events") for d in docs if d.get("total_events") is not None]

        baseline_doc = {
            "_id": f"{h_id}_{end_str}_baseline{n_days}",
            "household_id": h_id,
            "baseline_type": f"rolling{n_days}",
            "baseline_period": {
                "days": n_days,
                "start_date": start_str,
                "end_date": end_str
            },
            "computed_at": datetime.now().isoformat(),
            "wake_up_time": stat_summary(wake_times),
            "bed_time": stat_summary(bed_times),
            "first_kitchen_time": stat_summary(kitchen_times),
            "bathroom_first_time": stat_summary(bathroom_firsts),
            "bathroom_visits": {
                "daily_avg": round(statistics.mean(bathroom_counts), 2) if bathroom_counts else None,
                "daily_median": int(statistics.median(bathroom_counts)) if bathroom_counts else None,
                "min_daily": int(min(bathroom_counts)) if bathroom_counts else None,
                "max_daily": int(max(bathroom_counts)) if bathroom_counts else None,
                "std_dev": round(statistics.stdev(bathroom_counts),2) if len(bathroom_counts) > 1 else 0
            },
            "activity_duration": {
                "avg_minutes": round(statistics.mean([timestr2minutes(e)-timestr2minutes(s) 
                    for s, e in zip(activity_starts, activity_ends) 
                    if s and e]),2) if activity_starts and activity_ends else None,
                "median_minutes": round(statistics.median([timestr2minutes(e)-timestr2minutes(s) 
                    for s, e in zip(activity_starts, activity_ends) 
                    if s and e]),2) if activity_starts and activity_ends else None,
                "earliest_start": stat_summary(activity_starts).get("earliest"),
                "latest_end": stat_summary(activity_ends).get("latest")
            },
            "total_daily_events": {
                "avg": round(statistics.mean(total_events), 2) if total_events else None,
                "median": int(statistics.median(total_events)) if total_events else None,
                "min": int(min(total_events)) if total_events else None,
                "max": int(max(total_events)) if total_events else None,
                "std_dev": round(statistics.stdev(total_events),2) if len(total_events) > 1 else 0
            },
            "data_quality": {
                "days_with_complete_data": len(docs),
                "days_with_missing_wake": sum([1 for t in wake_times if not t]),
                "days_with_missing_kitchen": sum([1 for t in kitchen_times if not t]),
                "reliability_score": round(len(docs)/n_days,2)
            }
        }

        await MongoDB.write(baseline_collection, baseline_doc)
        print(f"✓ Saved baseline profile for {h_id} covering {start_str} to {end_str}")

async def batch_routine_learner_and_baseline():
    await batch_routine_learner_daily()
    await aggregate_baselines(n_days=7)  # Run baseline aggregation right after daily routines
    print("✅ Daily routine learning and baseline aggregation completed")

def start_scheduler():
    """
    Start the APScheduler for routine learning.
    Schedules batch_routine_learner to run daily at 1 AM.
    """
    if not scheduler.running:
        # Schedule the job to run daily at 1:00 AM
        scheduler.add_job(
            batch_routine_learner_and_baseline,
            trigger='cron',
            hour=1,
            minute=0,
            id='daily_routine_learner',
            name='Daily Routine Learning Job',
            replace_existing=True
        )
        scheduler.start()
        print("✓ Routine learner scheduler started (runs daily at 1:00 AM)")
    else:
        print("⚠ Scheduler is already running")

def shutdown_scheduler():
    """Stop the APScheduler"""
    if scheduler.running:
        scheduler.shutdown(wait=True)
        print("✓ Routine learner scheduler stopped")
    else:
        print("⚠ Scheduler is not running")


"""FUTURE: Algorithm improvements
- Modular Sensor Mapping:
Set up flexible mappings for sensor types, rooms, and residents so you can easily handle new devices or spaces in the future.

- Time Window Filters:
Track activity within relevant time ranges (e.g., “first kitchen visit in morning hours”) to avoid counting outlier events.

- Event Sequence Tracking:
Save the order of key activities (wake, bathroom, kitchen) for richer routine analysis and anomaly detection.

- Multi-Resident Support:
Process and store routines for each individual when event data includes resident IDs.

- Missing Activity Alerts:
Flag and log any days with missing expected events to help catch sensor failures or absences.
"""

