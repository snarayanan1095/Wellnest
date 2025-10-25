# app/services/anomaly_detector.py
from datetime import datetime, timedelta, timezone
from asyncio import Lock
from app.db.mongo import MongoDB
from app.services.ws_manager import manager

class AnomalyDetector:
    CRITICAL_EVENTS = {"door", "sos_button"}
    SCHEDULED_CHECKS = ["09:00", "11:00", "14:00", "22:00"]  # ["HH:MM"]
    ALERT_COOLDOWN_HOURS = 2  # Don't send same alert type within 2 hours

    def __init__(self):
        self.baseline_cache = {}
        self.household_state = {}
        self.last_check_time = {}
        self.recent_alerts = {}  # {household_id: {alert_type: timestamp}}
        self.state_locks = {}  # household_id -> Lock for thread-safe state updates

    async def get_baseline(self, household_id: str):
        if household_id in self.baseline_cache:
            cached = self.baseline_cache[household_id]
            if (datetime.now(timezone.utc) - cached['cached_at']).total_seconds() < 86400:
                return cached['baseline']
        query = {
            "household_id": household_id,
            "baseline_type": "rolling7"
        }
        baselines = await MongoDB.read(
            "routine_baselines",
            query=query,
            sort=[("computed_at", -1)],
            limit=1
        )
        if baselines:
            baseline = baselines[0]
            self.baseline_cache[household_id] = {
                'baseline': baseline,
                'cached_at': datetime.now(timezone.utc)
            }
            return baseline
        return None

    def time_to_minutes(self, time_str: str):
        try:
            h, m = map(int, time_str.split(":"))
            return h * 60 + m
        except:
            return None

    async def update_state_on_event(self, event: dict):
        """Update household daily state; only run anomaly check for critical events."""
        household_id = event["household_id"]

        # Ensure lock exists for this household
        if household_id not in self.state_locks:
            self.state_locks[household_id] = Lock()

        # Use lock to prevent race conditions during concurrent event processing
        async with self.state_locks[household_id]:
            state = await self.get_today_state(household_id)
            self._update_state(state, event)
            self.household_state[household_id] = state

        # Immediate anomaly detection only for critical events
        if event["sensor_type"] in self.CRITICAL_EVENTS:
            await self.check_anomalies(household_id, last_event=event, force=True)

    async def get_today_state(self, household_id: str):
        if household_id not in self.household_state:
            today = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_str = today.strftime("%Y-%m-%dT%H:%M:%S")
            query = {
                "household_id": household_id,
                "timestamp": {"$gte": today_str}
            }
            # Remove arbitrary limit - get ALL today's events, sorted by timestamp
            events = await MongoDB.read("events", query=query, sort=[("timestamp", 1)])
            state = {
                "wake_detected": False,
                "kitchen_visited": False,
                "bathroom_count": 0,
                "last_motion_time": None,
                "last_location": None,
                "door_opened": False,
                "first_kitchen_time": None,
                "wake_up_time": None
            }
            # Events are already sorted by timestamp from MongoDB
            for event in events:
                self._update_state(state, event)
            self.household_state[household_id] = state
        return self.household_state[household_id]

    def _update_state(self, state, event):
        stype = event["sensor_type"]
        loc = event["location"]
        val = event["value"]
        ts = event["timestamp"]
        if stype == "bed_presence" and val in ["False", "false", False]:
            if not state["wake_detected"]:
                state["wake_detected"] = True
                state["wake_up_time"] = ts[11:16]
        if stype == "motion" and loc == "kitchen" and val in ["True", "true", True]:
            if not state["kitchen_visited"]:
                state["kitchen_visited"] = True
                state["first_kitchen_time"] = ts[11:16]
        if stype == "motion" and "bathroom" in loc and val in ["True", "true", True]:
            state["bathroom_count"] += 1
        if stype == "motion" and val in ["True", "true", True]:
            state["last_motion_time"] = ts
            state["last_location"] = loc
        if stype == "door" and loc == "entrance":
            state["door_opened"] = True

    async def check_and_reset_daily_cache(self, household_id: str):
        """Reset state cache if we've crossed midnight"""
        now = datetime.now(timezone.utc)
        last_reset = self.last_check_time.get(household_id)

        if last_reset and last_reset.date() < now.date():
            # It's a new day - reset the state
            if household_id in self.household_state:
                del self.household_state[household_id]
                print(f"♻️ Daily state cache reset for household {household_id}")

        self.last_check_time[household_id] = now

    def should_send_alert(self, household_id: str, alert_type: str) -> bool:
        """Check if enough time has passed since last alert of this type"""
        if household_id not in self.recent_alerts:
            self.recent_alerts[household_id] = {}

        last_sent = self.recent_alerts[household_id].get(alert_type)
        if last_sent:
            hours_since = (datetime.now(timezone.utc) - last_sent).total_seconds() / 3600
            if hours_since < self.ALERT_COOLDOWN_HOURS:
                print(f"⏭️ Skipping duplicate alert: {alert_type} for {household_id} (sent {hours_since:.1f}h ago)")
                return False

        return True

    def mark_alert_sent(self, household_id: str, alert_type: str):
        """Mark that we've sent an alert of this type"""
        if household_id not in self.recent_alerts:
            self.recent_alerts[household_id] = {}
        self.recent_alerts[household_id][alert_type] = datetime.now(timezone.utc)

    async def check_anomalies(self, household_id: str, last_event=None, force=False):
        # Check and reset daily cache if needed
        await self.check_and_reset_daily_cache(household_id)

        baseline = await self.get_baseline(household_id)
        if not baseline:
            print(f"⚠️ No baseline found for {household_id}, skipping anomaly detection")
            return []
        state = await self.get_today_state(household_id)
        if last_event:
            self._update_state(state, last_event)
        anomalies = []
        current_time = datetime.now(timezone.utc)
        current_minutes = current_time.hour * 60 + current_time.minute
        # ---- SAME ANOMALY RULES AS BEFORE ----
        # Missed kitchen visit
        if state["wake_detected"] and not state["kitchen_visited"]:
            kitchen_baseline = baseline.get("first_kitchen_time", {})
            if kitchen_baseline.get("latest"):
                latest_kitchen_mins = self.time_to_minutes(kitchen_baseline["latest"])
                if latest_kitchen_mins and current_minutes > latest_kitchen_mins + 30:
                    anomalies.append({
                        "type": "missed_kitchen_activity",
                        "severity": "medium",
                        "message": f"No kitchen activity detected. Expected by {kitchen_baseline['median']}.",
                        "context": f"Last seen in {state['last_location']}" if state['last_location'] else "Location unknown",
                        "household_id": household_id,
                        "timestamp": current_time.isoformat(),
                        "actionable": "Check on resident or call to confirm well-being"
                    })
        # Prolonged inactivity
        if state["last_motion_time"]:
            last_motion = datetime.fromisoformat(state["last_motion_time"])
            # Make last_motion timezone-aware if it's naive
            if last_motion.tzinfo is None:
                last_motion = last_motion.replace(tzinfo=timezone.utc)
            inactivity_hours = (current_time - last_motion).total_seconds() / 3600
            if inactivity_hours > 2 and current_minutes > 480:
                anomalies.append({
                    "type": "prolonged_inactivity",
                    "severity": "high",
                    "message": f"No motion detected for {inactivity_hours:.1f} hours",
                    "context": f"Last activity in {state['last_location']} at {state['last_motion_time'][11:16]}",
                    "household_id": household_id,
                    "timestamp": current_time.isoformat()
                })
        # Excessive bathroom visits
        bathroom_baseline = baseline.get("bathroom_visits", {})
        if bathroom_baseline.get("max_daily"):
            threshold = bathroom_baseline["max_daily"] + 2
            if state["bathroom_count"] > threshold:
                anomalies.append({
                    "type": "excessive_bathroom_visits",
                    "severity": "medium",
                    "message": f"{state['bathroom_count']} bathroom visits (typical: {bathroom_baseline.get('daily_median', 'unknown')})",
                    "context": "May indicate health concern",
                    "household_id": household_id,
                    "timestamp": current_time.isoformat()
                })
        # Late wake up
        if state["wake_detected"] and state["wake_up_time"]:
            wake_baseline = baseline.get("wake_up_time", {})
            if wake_baseline.get("latest"):
                latest_wake_mins = self.time_to_minutes(wake_baseline["latest"])
                actual_wake_mins = self.time_to_minutes(state["wake_up_time"])
                if actual_wake_mins and latest_wake_mins and actual_wake_mins > latest_wake_mins + 60:
                    anomalies.append({
                        "type": "late_wake_up",
                        "severity": "low",
                        "message": f"Woke up at {state['wake_up_time']} (typical: {wake_baseline.get('median', 'unknown')})",
                        "context": "Later than usual",
                        "household_id": household_id,
                        "timestamp": current_time.isoformat()
                    })
        # Process anomalies with de-duplication
        for anomaly in anomalies:
            alert_type = anomaly["type"]

            # Check in-memory de-duplication
            if not self.should_send_alert(household_id, alert_type):
                continue

            # Check database-level de-duplication for persistence across restarts
            recent_alert = await MongoDB.read(
                "alerts",
                query={
                    "household_id": household_id,
                    "type": alert_type,
                    "timestamp": {"$gte": (current_time - timedelta(hours=self.ALERT_COOLDOWN_HOURS)).isoformat()},
                    "acknowledged": False
                },
                limit=1
            )
            if recent_alert:
                print(f"⏭️ Skipping duplicate alert in DB: {alert_type} for {household_id}")
                continue

            # Send the alert
            await self.save_alert(anomaly)
            await self.push_to_frontend(anomaly)
            self.mark_alert_sent(household_id, alert_type)

        return anomalies

    async def save_alert(self, anomaly: dict):
        anomaly["_id"] = f"{anomaly['household_id']}_{anomaly['timestamp']}_{anomaly['type']}"
        anomaly["acknowledged"] = False
        anomaly["created_at"] = datetime.now().isoformat()
        await MongoDB.write("alerts", anomaly)
        print(f"🚨 Alert saved: {anomaly['type']} for {anomaly['household_id']}")

    async def push_to_frontend(self, anomaly: dict):
        household_id = anomaly["household_id"]
        frontend_alert = {
            "alert_id": anomaly["_id"],
            "type": anomaly["type"],
            "severity": anomaly["severity"],
            "title": self._get_alert_title(anomaly["type"]),
            "message": anomaly["message"],
            "context": anomaly.get("context", ""),
            "actionable": anomaly.get("actionable", ""),
            "timestamp": anomaly["timestamp"],
            "household_id": household_id
        }
        await manager.send_alert(household_id, frontend_alert)
        print(f"📲 Pushed alert to frontend: {anomaly['type']} for {household_id}")

    def _get_alert_title(self, alert_type: str):
        titles = {
            "missed_kitchen_activity": "⚠️ Missed Breakfast Activity",
            "prolonged_inactivity": "🚨 No Movement Detected",
            "excessive_bathroom_visits": "💊 Frequent Bathroom Visits",
            "late_wake_up": "😴 Later Wake-Up Than Usual",
            "unusual_door_activity": "🚪 Door Activity at Unusual Hour"
        }
        return titles.get(alert_type, "🔔 Wellness Alert")

    def reset_daily_state(self):
        self.household_state = {}
        print("♻️ Household state cache reset")

detector = AnomalyDetector()