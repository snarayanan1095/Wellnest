# app/api/routine_comparison.py
from fastapi import APIRouter, HTTPException
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from app.db.mongo import MongoDB
from app.services.nim_llm_service import NIMLLMService
from app.api.dashboard_endpoints import calculate_daily_score

router = APIRouter()

def clean_ai_summary(summary: str) -> str:
    """Clean up AI-generated summary formatting"""
    import re

    # Remove markdown formatting
    summary = re.sub(r'\*\*', '', summary)  # Remove bold markers
    summary = re.sub(r'^\*\*Analysis:\*\*\s*', '', summary, flags=re.IGNORECASE)  # Remove Analysis: header
    summary = re.sub(r'^Analysis:\s*', '', summary, flags=re.IGNORECASE)  # Remove Analysis: header without markdown

    # Clean up numbered points
    summary = re.sub(r'^\d+\.\s+', '', summary, flags=re.MULTILINE)  # Remove numbered list prefixes

    # Split by numbered points and rejoin with clean formatting
    lines = summary.strip().split('\n')
    cleaned_lines = []

    for line in lines:
        # Clean each line
        line = line.strip()
        if line:
            # Remove leading numbers and dots
            line = re.sub(r'^\d+\.\s*', '', line)
            # Remove excess whitespace
            line = ' '.join(line.split())
            cleaned_lines.append(line)

    # Join with proper spacing
    if len(cleaned_lines) > 1:
        # Format as separate paragraphs
        result = ' '.join(cleaned_lines[:1])  # First paragraph
        if len(cleaned_lines) > 1:
            result += '\n\n' + ' '.join(cleaned_lines[1:])  # Second paragraph
    else:
        result = ' '.join(cleaned_lines)

    return result.strip()

def time_to_minutes(time_str: str) -> int:
    """Convert HH:MM time string to minutes since midnight"""
    if not time_str or time_str == "N/A":
        return 0
    try:
        hours, minutes = map(int, time_str.split(':'))
        return hours * 60 + minutes
    except:
        return 0

def format_time_difference(today_time: str, baseline_time: str) -> Dict[str, Any]:
    """Calculate difference between two time strings"""
    today_mins = time_to_minutes(today_time)
    baseline_mins = time_to_minutes(baseline_time)
    diff_mins = today_mins - baseline_mins

    return {
        "today": today_time,
        "baseline": baseline_time,
        "difference_minutes": diff_mins,
        "difference_formatted": f"{'+' if diff_mins > 0 else ''}{diff_mins} min",
        "status": "normal" if abs(diff_mins) < 30 else "warning" if abs(diff_mins) < 60 else "alert"
    }

@router.get("/routine-comparison/{household_id}")
async def get_routine_comparison(household_id: str):
    """Get routine comparison between today and baseline"""
    try:
        # Get today's date
        today = datetime.utcnow().strftime("%Y-%m-%d")

        # Fetch today's routine
        daily_routine_id = f"{household_id}_{today}"
        today_routine = await MongoDB.read(
            "daily_routines",
            query={"_id": daily_routine_id},
            limit=1
        )

        if not today_routine:
            # If no data for today, use yesterday
            yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
            daily_routine_id = f"{household_id}_{yesterday}"
            today_routine = await MongoDB.read(
                "daily_routines",
                query={"_id": daily_routine_id},
                limit=1
            )
            if today_routine:
                today = yesterday

        # Fetch latest baseline (rolling 7-day)
        baseline = await MongoDB.read(
            "routine_baselines",
            query={
                "household_id": household_id,
                "baseline_type": "rolling7"
            },
            sort=[("computed_at", -1)],
            limit=1
        )

        if not today_routine or not baseline:
            return {
                "error": "Insufficient data",
                "message": "No routine data available for comparison"
            }

        today_data = today_routine[0]
        baseline_data = baseline[0]

        # Calculate activity duration for today
        if today_data.get("activity_start") and today_data.get("activity_end"):
            today_duration_mins = time_to_minutes(today_data["activity_end"]) - time_to_minutes(today_data["activity_start"])
        else:
            today_duration_mins = 0

        # Prepare comparison data
        comparison = {
            "date": today,
            "household_id": household_id,
            "metrics": {
                "wake_up_time": format_time_difference(
                    today_data.get("wake_up_time", "N/A"),
                    baseline_data.get("wake_up_time", {}).get("median", "N/A")
                ),
                "bed_time": format_time_difference(
                    today_data.get("bed_time", "N/A"),
                    baseline_data.get("bed_time", {}).get("median", "N/A")
                ),
                "first_kitchen_time": format_time_difference(
                    today_data.get("first_kitchen_time", "N/A"),
                    baseline_data.get("first_kitchen_time", {}).get("median", "N/A")
                ),
                "bathroom_visits": {
                    "today": today_data.get("total_bathroom_events", 0),
                    "baseline": baseline_data.get("bathroom_visits", {}).get("daily_avg", 0),
                    "difference": today_data.get("total_bathroom_events", 0) - baseline_data.get("bathroom_visits", {}).get("daily_avg", 0),
                    "percentage_change": round(
                        ((today_data.get("total_bathroom_events", 0) - baseline_data.get("bathroom_visits", {}).get("daily_avg", 0))
                         / max(baseline_data.get("bathroom_visits", {}).get("daily_avg", 1), 1)) * 100, 1
                    ),
                    "status": "normal" if abs(today_data.get("total_bathroom_events", 0) - baseline_data.get("bathroom_visits", {}).get("daily_avg", 0)) < 20 else "warning"
                },
                "total_events": {
                    "today": today_data.get("total_events", 0),
                    "baseline": baseline_data.get("total_daily_events", {}).get("avg", 0),
                    "difference": today_data.get("total_events", 0) - baseline_data.get("total_daily_events", {}).get("avg", 0),
                    "percentage_change": round(
                        ((today_data.get("total_events", 0) - baseline_data.get("total_daily_events", {}).get("avg", 0))
                         / max(baseline_data.get("total_daily_events", {}).get("avg", 1), 1)) * 100, 1
                    ),
                    "status": "normal"
                },
                "activity_duration": {
                    "today_minutes": today_duration_mins,
                    "baseline_minutes": baseline_data.get("activity_duration", {}).get("avg_minutes", 0),
                    "today_hours": round(today_duration_mins / 60, 1),
                    "baseline_hours": round(baseline_data.get("activity_duration", {}).get("avg_minutes", 0) / 60, 1),
                    "difference_hours": round((today_duration_mins - baseline_data.get("activity_duration", {}).get("avg_minutes", 0)) / 60, 1),
                    "status": "normal"
                }
            },
            "baseline_period": baseline_data.get("baseline_period", {}),
            "summary_text": today_data.get("summary_text", "")
        }

        return comparison

    except Exception as e:
        print(f"Error in routine comparison: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/routine-summary/{household_id}")
async def get_routine_summary(household_id: str):
    """Get AI-generated summary of routine comparison"""
    try:
        # First get the comparison data
        comparison = await get_routine_comparison(household_id)

        if "error" in comparison:
            return comparison

        # Prepare data for LLM
        metrics = comparison["metrics"]

        # Format the prompt
        prompt = f"""Analyze this elderly resident's routine for {comparison['date']}:

TIMING CHANGES:
- Wake up: {metrics['wake_up_time']['today']} (usual: {metrics['wake_up_time']['baseline']}, {metrics['wake_up_time']['difference_formatted']})
- Bed time: {metrics['bed_time']['today']} (usual: {metrics['bed_time']['baseline']}, {metrics['bed_time']['difference_formatted']})
- First kitchen visit: {metrics['first_kitchen_time']['today']} (usual: {metrics['first_kitchen_time']['baseline']})

ACTIVITY PATTERNS:
- Bathroom visits: {metrics['bathroom_visits']['today']} (usual: {metrics['bathroom_visits']['baseline']}, {metrics['bathroom_visits']['percentage_change']:+.1f}%)
- Total activity: {metrics['total_events']['today']} events (usual: {metrics['total_events']['baseline']})
- Active hours: {metrics['activity_duration']['today_hours']} hours (usual: {metrics['activity_duration']['baseline_hours']} hours)

Provide a brief 2-3 sentence analysis focusing on:
1. Most significant changes from baseline
2. Any concerning patterns that caregivers should monitor
Keep it concise and actionable."""

        # Get today's routine data for score calculation
        today = comparison["date"]
        daily_routine_id = f"{household_id}_{today}"
        today_routine = await MongoDB.read(
            "daily_routines",
            query={"_id": daily_routine_id},
            limit=1
        )

        # Calculate score
        score = 0.0
        if today_routine and len(today_routine) > 0:
            score = calculate_daily_score(today_routine[0])

        # Use the NIM LLM service
        try:
            raw_summary = NIMLLMService.get_custom_summary(prompt, max_tokens=150, temperature=0.7)

            # Clean up the summary formatting
            summary = clean_ai_summary(raw_summary)

            # Identify key deviations
            deviations = []
            if abs(metrics['wake_up_time']['difference_minutes']) > 60:
                deviations.append(f"Wake time shifted by {metrics['wake_up_time']['difference_formatted']}")
            if abs(metrics['bathroom_visits']['percentage_change']) > 25:
                deviations.append(f"Bathroom visits {metrics['bathroom_visits']['percentage_change']:+.1f}% from normal")
            if abs(metrics['activity_duration']['difference_hours']) > 2:
                deviations.append(f"Activity duration changed by {metrics['activity_duration']['difference_hours']:+.1f} hours")

            return {
                "household_id": household_id,
                "date": comparison["date"],
                "score": score,
                "summary": summary,
                "deviations": deviations,
                "comparison_data": comparison
            }
        except Exception as llm_error:
            print(f"Error calling NIM LLM service: {llm_error}")
            # Fallback to rule-based summary if LLM fails
            fallback_result = generate_fallback_summary(comparison)
            fallback_result["score"] = score
            return fallback_result

    except Exception as e:
        print(f"Error generating summary: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def generate_fallback_summary(comparison: Dict) -> Dict:
    """Generate a rule-based summary if LLM is unavailable"""
    metrics = comparison["metrics"]

    deviations = []
    concerns = []

    # Check wake time
    if abs(metrics['wake_up_time']['difference_minutes']) > 60:
        deviations.append(f"Waking {abs(metrics['wake_up_time']['difference_minutes'])} minutes {'earlier' if metrics['wake_up_time']['difference_minutes'] < 0 else 'later'} than usual")

    # Check bathroom visits
    if metrics['bathroom_visits']['percentage_change'] > 30:
        concerns.append(f"Bathroom visits increased by {metrics['bathroom_visits']['percentage_change']:.0f}%")
    elif metrics['bathroom_visits']['percentage_change'] < -30:
        concerns.append(f"Bathroom visits decreased by {abs(metrics['bathroom_visits']['percentage_change']):.0f}%")

    # Check activity duration
    if metrics['activity_duration']['difference_hours'] < -2:
        concerns.append(f"Less active today ({metrics['activity_duration']['difference_hours']:.1f} hours)")

    # Generate clean summary without excessive formatting
    summary_parts = []
    if deviations:
        summary_parts.append(f"Routine shows changes: {', '.join(deviations)}.")
    if concerns and summary_parts:
        summary_parts.append(f"\n\nMonitor: {', '.join(concerns)}.")
    elif concerns:
        summary_parts.append(f"Monitor: {', '.join(concerns)}.")
    if not deviations and not concerns:
        summary_parts.append("Routine is consistent with baseline patterns. No significant deviations detected.")

    summary = "".join(summary_parts)

    return {
        "household_id": comparison["household_id"],
        "date": comparison["date"],
        "summary": summary,
        "deviations": deviations + concerns,
        "comparison_data": comparison,
        "fallback": True
    }