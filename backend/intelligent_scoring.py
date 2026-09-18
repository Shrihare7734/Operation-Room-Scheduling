from datetime import datetime, timedelta


WEIGHT_PROFILES = {
    "NORMAL_OPERATIONS": {"priority": 35, "surgeon_match": 20, "room_efficiency": 20, "equipment": 15, "time_urgency": 10, "context_multiplier": 1.0},
    "EMERGENCY_SURGE": {"priority": 60, "surgeon_match": 10, "room_efficiency": 15, "equipment": 10, "time_urgency": 5, "context_multiplier": 1.5},
    "RESOURCE_SHORTAGE": {"priority": 35, "surgeon_match": 15, "room_efficiency": 10, "equipment": 30, "time_urgency": 10, "context_multiplier": 0.9},
    "END_OF_SHIFT": {"priority": 35, "surgeon_match": 10, "room_efficiency": 5, "equipment": 15, "time_urgency": 35, "context_multiplier": 1.2},
}

PRIORITY_SCORES = {"emergency": 100, "critical": 100, "urgent": 75, "routine": 50, "elective": 25}


def _tokens(value):
    if isinstance(value, list):
        return {str(item).strip().lower() for item in value}
    return {item.strip().lower() for item in str(value or "").replace(";", ",").split(",") if item.strip()}


def _parse(value):
    if isinstance(value, datetime):
        return value
    parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    return parsed.astimezone().replace(tzinfo=None) if parsed.tzinfo else parsed


class ContextDetector:
    def __init__(self, rooms=None, surgeons=None, now=None, shift_end_hour=18):
        self.rooms = rooms or []
        self.surgeons = surgeons or []
        self.now = now or datetime.now()
        self.shift_end = self.now.replace(hour=shift_end_hour, minute=0, second=0, microsecond=0)

    def detect_context(self, schedule=None, waiting=None):
        schedule = schedule or []
        waiting = waiting or []
        busy_rooms = {item.get("room_id") for item in schedule if item.get("status") != "unschedulable"}
        utilization = len(busy_rooms) / max(len(self.rooms), 1)
        emergencies = sum(1 for item in waiting + schedule if item.get("direness") == "emergency")
        available_equipment = set().union(*(_tokens(room.get("equipment")) for room in self.rooms)) if self.rooms else set()
        equipment_missing = any(
            _tokens(item.get("equipment")) - available_equipment
            for item in waiting
            if item.get("equipment")
        )
        hours_left = (self.shift_end - self.now).total_seconds() / 3600
        if hours_left < 2:
            return "END_OF_SHIFT"
        if utilization > 0.6 and emergencies >= 3:
            return "EMERGENCY_SURGE"
        if equipment_missing or not self.surgeons or not self.rooms:
            return "RESOURCE_SHORTAGE"
        return "NORMAL_OPERATIONS"

    def get_weights_for_context(self, context_type):
        return dict(WEIGHT_PROFILES.get(context_type, WEIGHT_PROFILES["NORMAL_OPERATIONS"]))


class PenaltyCalculator:
    def apply(self, base_score, procedure, slot, room, surgeon, schedule):
        penalties = []
        start, end = slot["start"], slot["end"]
        if not self._fits(procedure, start, end):
            penalties.append(("Violates time window", 100))
        if self._overlaps(schedule, "room_id", room.get("id"), start, end):
            penalties.append(("Room double-booked", 50))
        if surgeon and self._overlaps(schedule, "surgeon_id", surgeon.get("id"), start, end):
            penalties.append(("Surgeon double-booked", 50))
        return max(0, base_score - sum(value for _, value in penalties)), penalties

    @staticmethod
    def _fits(procedure, start, end):
        earliest = _parse(procedure["earliest_start_time"])
        latest = _parse(procedure["latest_end_time"])
        return start >= earliest and end <= latest

    @staticmethod
    def _overlaps(schedule, key, value, start, end):
        for item in schedule:
            if item.get(key) != value or not item.get("scheduled_start"):
                continue
            other_start, other_end = _parse(item["scheduled_start"]), _parse(item["scheduled_end"])
            if start < other_end and end > other_start:
                return True
        return False


class ScoringEngine:
    def calculate_priority_score(self, priority):
        return PRIORITY_SCORES.get(str(priority).lower(), 25)

    def calculate_surgeon_match_score(self, procedure_type, specialization):
        procedure = str(procedure_type or "general").lower()
        specialty = str(specialization or "general").lower()
        if procedure in specialty or specialty in procedure:
            return 100
        if any(word in specialty for word in ("general", "trauma")):
            return 50
        return 25

    def calculate_room_efficiency_score(self, slot, room, schedule):
        nearby = []
        for item in schedule:
            if item.get("room_id") != room.get("id") or not item.get("scheduled_start"):
                continue
            nearby.append((_parse(item["scheduled_start"]), _parse(item["scheduled_end"])))
        gaps = [abs((slot["start"] - end).total_seconds() / 60) for start, end in nearby if end <= slot["start"]]
        gaps += [abs((start - slot["end"]).total_seconds() / 60) for start, end in nearby if start >= slot["end"]]
        total_gap = min(sum(gaps), 9999) if gaps else 180
        score = 100 if total_gap == 0 else 85 if total_gap < 30 else 70 if total_gap < 60 else 50 if total_gap < 120 else 25
        if total_gap == 0:
            score += 15
        return min(100, score)

    def calculate_equipment_match_score(self, required, available):
        required_set, available_set = _tokens(required), _tokens(available)
        if not required_set:
            return 100
        ratio = len(required_set & available_set) / len(required_set)
        return 100 if ratio == 1 else 75 if ratio >= .75 else 50 if ratio >= .5 else 0

    def calculate_time_urgency_score(self, procedure, now=None):
        now = now or datetime.now()
        minutes = (_parse(procedure["latest_end_time"]) - now).total_seconds() / 60
        return 100 if minutes < 30 else 90 if minutes < 60 else 75 if minutes < 120 else 50 if minutes < 240 else 25 if minutes < 480 else 10

    def calculate_base_score(self, procedure, slot, room, surgeon, weights, schedule):
        factors = {
            "priority": self.calculate_priority_score(procedure.get("direness")),
            "surgeon_match": self.calculate_surgeon_match_score(procedure.get("procedure_type"), (surgeon or {}).get("specialization")),
            "room_efficiency": self.calculate_room_efficiency_score(slot, room, schedule),
            "equipment": self.calculate_equipment_match_score(procedure.get("equipment"), room.get("equipment")),
            "time_urgency": self.calculate_time_urgency_score(procedure),
        }
        score = sum(factors[key] * weights[key] / 100 for key in factors)
        return score, factors

    def calculate_final_score(self, procedure, slot, room, surgeon, context, schedule):
        weights = ContextDetector().get_weights_for_context(context)
        base, breakdown = self.calculate_base_score(procedure, slot, room, surgeon, weights, schedule)
        penalized, penalties = PenaltyCalculator().apply(base, procedure, slot, room, surgeon, schedule)
        final = min(100, max(0, penalized * weights["context_multiplier"]))
        return {"score": round(final, 2), "base_score": round(base, 2), "penalties": penalties, "context": context, "breakdown": breakdown}


class SlotSelector:
    def __init__(self, rooms, surgeons, now=None):
        self.rooms = rooms or []
        self.surgeons = surgeons or []
        self.now = now or datetime.now()
        self.scoring = ScoringEngine()

    def find_best_slot_for_procedure(self, procedure, schedule, context):
        earliest, latest = _parse(procedure["earliest_start_time"]), _parse(procedure["latest_end_time"])
        duration = int(procedure.get("estimated_min_duration") or procedure.get("duration") or 30)
        candidates = []
        for room in self.rooms:
            for surgeon in self.surgeons or [None]:
                start = max(earliest, self.now.replace(hour=6, minute=0, second=0, microsecond=0))
                while start + timedelta(minutes=duration) <= latest:
                    end = start + timedelta(minutes=duration)
                    room_free = not PenaltyCalculator._overlaps(schedule, "room_id", room.get("id"), start, end)
                    surgeon_free = surgeon is None or not PenaltyCalculator._overlaps(schedule, "surgeon_id", surgeon.get("id"), start, end)
                    if room_free and surgeon_free:
                        slot = {"start": start, "end": end}
                        result = self.scoring.calculate_final_score(procedure, slot, room, surgeon, context, schedule)
                        candidates.append((result["score"], start, room, surgeon, slot, result))
                        break
                    start += timedelta(minutes=15)
        if not candidates:
            return None
        if procedure.get("direness") in ("emergency", "critical"):
            return min(candidates, key=lambda item: item[1])
        return max(candidates, key=lambda item: (item[0], -item[1].timestamp()))
