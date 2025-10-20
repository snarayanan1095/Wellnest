from app.db.mongo import MongoDB
from datetime import datetime, timedelta
event_col = "events"
async def get_events_for_household(household_id: str, start_time: datetime, end_time: datetime, limit: int = 1000):
    """
    Get events for a household within a time range.
    """
    query = {
        "household_id": household_id,
        "timestamp": {"$gte": start_time, "$lt": end_time}
    }
    return await MongoDB.read("events", query=query, limit=limit)

def get_yesterday_range():
    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    yesterday = today - timedelta(days=1)
    return yesterday.isoformat(), today.isoformat()

def extract_routine(events):
    # Initialize trackers
    wake_up_time, bed_time, first_kitchen = None, None, None
    bathroom_first, bathroom_count = None, 0

    events_sorted = sorted(events, key=lambda x: x["timestamp"])

    for event in events_sorted:
        ts = event["timestamp"][11:16]  # 'YYYY-MM-DDTHH:MM:SS'
        stype = event["sensor_type"]
        loc = event["location"]
        val = event["value"]

        if stype == "bed_presence" and val is False and not wake_up_time:
            wake_up_time = ts
        if stype == "bed_presence" and val is True:
            bed_time = ts  # will be overwritten until last
        if stype == "motion" and loc == "kitchen" and not first_kitchen:
            first_kitchen = ts
        if stype == "motion" and "bathroom" in loc:
            if not bathroom_first:
                bathroom_first = ts
            bathroom_count += 1

    return {
        "wake_up_time": wake_up_time,
        "bed_time": bed_time,
        "first_kitchen_time": first_kitchen,
        "bathroom_first_time": bathroom_first,
        "total_bathroom_events": bathroom_count
    }

def save_profile(household_id, profile_dict, summary_text=""):
    profile_dict.update({
        "household_id": household_id,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "summary_text": summary_text
    })
    profiles_col="routines"
    #TODO:         inserted_id = await MongoDB.write("events", event_dict)
    # profiles_col.update_one(
    #     {"household_id": household_id, "date": profile_dict["date"]},
    #     {"$set": profile_dict},
    #     upsert=True
    # )
    print(f"Saved routine profile for {household_id}: {profile_dict}")

def routine_learner_for_household(household_id):
    start, end = get_yesterday_range()
    events = get_events_for_household(household_id, start, end)
    if not events:
        print(f"No events found for {household_id}")
        return
    routine = extract_routine(events)
    save_profile(household_id, routine)

def batch_routine_learner():
    household_ids = events_col.distinct("household_id")
    for h_id in household_ids:
        routine_learner_for_household(h_id)

if __name__ == "__main__":
    batch_routine_learner()
#TODO: Figure out how to do cronjob or scheduler to run daily