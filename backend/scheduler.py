import math
from datetime import datetime, timedelta
from intelligent_scoring import ContextDetector, SlotSelector

DIRENESS_RANK = {"emergency": 4, "critical": 3, "urgent": 2, "routine": 1}
GROWTH_TYPE = {"routine": "linear", "urgent": "quadratic", "critical": "exponential", "emergency": "exponential"}


def _parse_time(value):
    if not value:
        return None
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
            return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed
        except ValueError:
            return None
    return value


def _window(patient, now=None):
    now = now or datetime.now()
    legacy_start = None
    if patient.get("preferred_date"):
        legacy_start = f"{patient['preferred_date']}T{patient.get('preferred_start_time') or '08:00'}"
    earliest = _parse_time(patient.get("earliest_start_time")) or _parse_time(legacy_start) or _parse_time(patient.get("arrival_time")) or now
    latest = _parse_time(patient.get("latest_end_time"))
    if not latest:
        legacy_duration = int(patient.get("duration") or 0)
        latest = earliest + timedelta(minutes=max(legacy_duration, 240))
    return earliest, latest


def window_minutes(patient):
    earliest, latest = _window(patient)
    return max(0, (latest - earliest).total_seconds() / 60)


def validate_time_window(patient, now=None):
    earliest, latest = _window(patient, now)
    errors = []
    if latest <= earliest:
        errors.append("Latest end time must be after earliest start time.")
    if (latest - earliest).total_seconds() / 60 < 30:
        errors.append("Time window must be at least 30 minutes.")
    return errors


def wait_minutes(patient, now=None):
    arrival = _parse_time(patient.get("arrival_time")) or _window(patient, now)[0]
    reference = now or datetime.now()
    return max(0, (reference - arrival).total_seconds() / 60)


def effective_priority(patient, now=None):
    base_k = float(patient.get("k", 1.0))
    minutes_waiting = wait_minutes(patient, now)
    divisor = {"routine": 60, "urgent": 90, "critical": 120, "emergency": 180}.get(patient.get("direness"), 60)
    return base_k * (1 + minutes_waiting / divisor)


def cost(patient, wait_time):
    k = float(patient.get("k", 1.0))
    growth_type = patient.get("growth_type") or GROWTH_TYPE.get(patient.get("direness"), "linear")
    if growth_type == "quadratic":
        return k * (wait_time ** 2) / 100
    if growth_type == "exponential":
        return k * (math.exp(wait_time / 30) - 1)
    return k * wait_time


def total_cost(schedule):
    return round(sum(cost(patient, index * 30) for index, patient in enumerate(schedule)), 2)


def greedy_sort(patients):
    return sorted(patients, key=lambda patient: DIRENESS_RANK.get(patient.get("direness"), 1) * effective_priority(patient), reverse=True)


def _planned_duration(patient, earliest, latest):
    estimate = int(patient.get("estimated_min_duration") or patient.get("duration") or 30)
    return min(max(30, estimate), int((latest - earliest).total_seconds() / 60))


def build_schedule(patients, rooms=None, surgeons=None):
    now = datetime.now()
    scheduled = []
    ordered = greedy_sort(patients)
    context = ContextDetector(rooms, surgeons, now).detect_context([], ordered)
    selector = SlotSelector(rooms or [], surgeons or [], now)
    for patient in ordered:
        earliest, latest = _window(patient, now)
        patient["earliest_start_time"] = earliest.isoformat()
        patient["latest_end_time"] = latest.isoformat()
        patient["window_minutes"] = round((latest - earliest).total_seconds() / 60)
        patient["scheduling_context"] = context
        patient["growth_type"] = GROWTH_TYPE.get(patient.get("direness"), "linear")
        patient["k"] = effective_priority(patient, now)
        errors = validate_time_window(patient, now)
        if errors:
            patient["status"] = "unschedulable"
            patient["schedule_error"] = errors[0]
            patient["scheduled_start"] = None
            patient["scheduled_end"] = None
            continue
        selected = selector.find_best_slot_for_procedure(patient, scheduled, context)
        if not selected:
            patient["status"] = "unschedulable"
            patient["schedule_error"] = "No room and surgeon slot fits within this time window."
            patient["scheduled_start"] = None
            patient["scheduled_end"] = None
            continue
        score, _, room, surgeon, slot, decision = selected
        patient["status"] = "scheduled"
        patient["scheduled_start"] = slot["start"].isoformat()
        patient["scheduled_end"] = slot["end"].isoformat()
        patient["scheduled_duration"] = round((slot["end"] - slot["start"]).total_seconds() / 60)
        patient["room_id"] = room.get("id")
        patient["room_name"] = room.get("name")
        patient["room_type"] = room.get("equipment")
        if surgeon:
            patient["surgeon_id"] = surgeon.get("id")
            patient["surgeon_name"] = surgeon.get("name")
        patient["scoring"] = decision
        scheduled.append(patient)
    return scheduled + [patient for patient in ordered if patient.get("status") == "unschedulable"]


def handle_emergency(current_schedule, emergency_patient, rooms=None, surgeons=None):
    now = datetime.now()
    emergency_patient.setdefault("earliest_start_time", now.isoformat())
    emergency_patient.setdefault("latest_end_time", (now + timedelta(hours=4)).isoformat())
    emergency_patient["direness"] = "emergency"
    return build_schedule(current_schedule + [emergency_patient], rooms, surgeons)
