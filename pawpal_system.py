"""
Phase 1 Skeleteon:
- Implementation of base classes Owner, Pet, Task and a Scheduler shell.
- Use of @dataclass for Task & Pet as stupilated in intrsuction
- Made *optional features* (prioriy-aware scheduling, JSON persistence, time-window logic,
security/auth guidance).
- Time zones: normalization of IANA zones.
"""
from __future__ import annotations
from dataclasses import dataclass, field   
from enum import Enum
from typing import List, Optional, Dict, Tuple, Any
from datetime import date, datetime, timedelta
import json
import uuid
import pytz

from XXXpawpal_system import Scheduler

# -------------------------------
# Enums
# -------------------------------
class Frequency(str, Enum):
    ONCE = "once"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly" # Not implemented in Phase 1, but reserved for future use.

class Priority(int, Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3

# -------------------------------
# Time zone support (Three zones)
# -------------------------------
# Defined here as constants so UI and scheduler can reference a single source of truth.
# - America/New_York : Eastern Time (EST/EDT)
# - Africa/Lagos     : West Africa Time (UTC+01:00)
# - Asia/Karachi     : Pakistan Standard Time (UTC+05:00)  <-- chosen representative for UTC+5
# If you prefer a different UTC+05:00 locale (e.g., Asia/Tashkent), change the identifier below.

from zoneinfo import ZoneInfo  # stdlib (PEP 615)

TZ_NY = 'America/New_York'
TZ_LAGOS = 'Africa/Lagos'
TZ_UTC_PLUS_5 = 'Asia/Karachi'

# Convenience accessors (lazy ZoneInfo creation performed where needed later)
# Example usage later:
#   ny = ZoneInfo(TZ_NY)
#   lag = ZoneInfo(TZ_LAGOS)
#   u5 = ZoneInfo(TZ_UTC_PLUS_5)

# -------------------------------
# Helpers
# -------------------------------

def _to_minutes(hhmm: str) -> int:
    """
    Convert 'HH:MM' string to minutes since midnight; robust to whitespace.
    """
    h, m = map(int, hhmm.strip().split(":"))
    return h * 60 + m


def _add_month(d: date) -> date:
    """
    Add one calendar month to a date, clamping to end-of-month when necessary.
    Example: Jan 31 -> Feb 28/29, Aug 31 -> Sep 30.
    """
    year = d.year + (1 if d.month == 12 else 0)
    month = 1 if d.month == 12 else d.month + 1
    # Compute last day of target month: next month first day minus one day
    if month == 12:
        next_month_first = date(year + 1, 1, 1)
    else:
        next_month_first = date(year, month + 1, 1)
    last_day = next_month_first - timedelta(days=1)
    day = min(d.day, last_day.day)
    return date(year, month, day)

# -------------------------------
# Data classes
# -------------------------------
@dataclass
class Task:
    description: str
    date: date
    start_time: str # "HH:MM" format (local); basic same-time detection default
    duration_minutes: int = 0
    frequency: Frequency = Frequency.ONCE
    prirority: Priority = Priority.MEDIUM
    completed: bool = False 
    id: str = field(default_factory=lambda: str(uuid.uuid4())) # Unique ID for each task

    # OPTIONAL Feautre (time-window overlap support):
    # To enable window-based conflict detection using start_time + duration_minutes, 
    # toggles the scheduler; detect_conflicts implementation accordingly.

    def mark_complete(self) -> None:
        """"
        This marks the task as completed. Recuurence handling occurs in Scheduler.mark_task_complete
        ().
        """
        self.completed = True
    
    def next_occurrence(self) -> Optional["Task"]:
        """
        Return the occurrence of this task if frequency is recurring; otherwise, we'll return None.
        Actual date arithmetic implemented in phase 4.

        Compute the next occurrence for recurring tasks; return None if ONCE.
        The new task carries over description, start_time, duration, priority, and frequency.
        """
        if self.frequency == Frequency.ONCE:
            return None
        if self.frequency == Frequency.DAILY:
            next_date = self.date + timedelta(days=1)
        elif self.frequency == Frequency.WEEKLY:
            next_date = self.date + timedelta(days=7)
        elif self.frequency == Frequency.MONTHLY:
            next_date = _add_month(self.date)
        else:
            return None
        return Task(
            description=self.description,
            date=next_date,
            start_time=self.start_time,
            duration_minutes=self.duration_minutes,
            frequency=self.frequency,
            priority=self.priority,
            completed=False,
        )

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize to a JSON-safe dict for persistence.
        """
        return {
            "id": self.id,
            "description": self.description,
            "date": self.date.isoformat(),
            "start_time": self.start_time,
            "duration_minutes": self.duration_minutes,
            "frequency": self.frequency.value,
            "priority": int(self.priority),
            "completed": self.completed,
        }
    @staticmethod
    def from_dict(d: Dict[str, any]) -> "Task":
        return Task(
            id = d.get("id", str(uuid.uuid4())),
            description = d["desciption"], 
            date = date.fromisoformat(d["date"]), 
            start_time = d["start_time"],
            duration_minutes=int(d.get("duration_minutes", 0)),
            frequency=Frequency(d.get("frequency", Frequency.ONCE.value)),
            priority=Priority(int(d.get("priority", Priority.MEDIUM))),
            completed=bool(d.get("completed", False)),
        )
    
@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)
    id: str = field(default_factory = lambda: str(uuid.uuid4())) # Unique ID for each pet

    def add_task(self, task: Task) -> None:
        self.tasks.append(task)

    def remove_task(self, task_id: str) -> bool:
        for i, t in enumerate(self.tasks):
            if t.id == task_id:
                del self.tasks[i]
                return True
            return False
        
    def get_tasks(self) -> List[Task]:
        return list(self.tasks)
    
class Owner:
    def __init__(self, name: str) -> None:
        self.id: str = str(uuid.uuid4()) # Unique ID for each owner
        self.name: str = name
        self.pets: List[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        self.id: str = str(uuid.uuid4()) # Unique ID for each pet
        self.pets.append(pet)

    def get_pet(self, name: str) -> Optional[Pet]:
        for p in self.pets:
            if p.name == name:
                return p
        return None

    def get_all_tasks(self) -> List[Task]:
        tasks: List[Task] = []
        for p in self.pets:
            tasks.extend(p.get_tasks())
        return tasks
    
     # OPTIONAL (JSON persistence)
    def save_to_json(self, path: str) -> None:
        """
        Persist owner, pets, and tasks to a JSON file.
        SECURITY NOTE: Avoid storing secrets here. For auth keys etc., use Streamlit st.secrets later.
        """
        payload = {
            "id": self.id,
            "name": self.name,
            "pets": [
                {
                    "id": pet.id,
                    "name": pet.name,
                    "species": pet.species,
                    "tasks": [t.to_dict() for t in pet.tasks],
                }
                for pet in self.pets
            ],
        }
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)

    @staticmethod
    def load_from_json(path: str) -> "Owner":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        owner = Owner(name=data["name"])
        owner.id = data.get("id", owner.id)
        for p in data.get("pets", []):
            pet = Pet(name=p["name"], species=p.get("species", "Unknown"))
            pet.id = p.get("id", pet.id)
            for td in p.get("tasks", []):
                pet.tasks.append(Task.from_dict(td))
            owner.add_pet(pet)
        return owner

# -------------------------------
# Scheduler shell (logic filled later)
# -------------------------------
    """
    Coordinates task organization and simple planning.

    Time handling policy (Phase 1):
    - Default: point-in-time using Task.start_time (HH:MM) for sorting and *same-time* conflict detection.
    - OPTIONAL: time-window overlap using start_time + duration_minutes.

    Time zones policy (Phase 1):
    - Implementation uses local times; in a later phase I will normalize with IANA time zones just for fun e.g.,
      (America/New_York for EDT and Africa/Lagos for Nigeria) using `zoneinfo`.
    """

    @staticmethod
    def sort_by_time(tasks: List[Task]) -> List[Task]:
        """
        Return tasks sorted by HH:MM string.
        """
        return sorted(tasks, key=lambda t: (t.date, t.start_time))
    
    @staticmethod
    def sort_by_priority_then_time(tasks: List[Task]) -> List[Task]:
        """
        Return tasks sorted by priority (High > Med > Low) then time.
        NOTE: Enabled from Phase 1 per requirement for higher-quality scheduling.
        """
        return sorted(tasks, key=lambda t: (-int(t.priority), t.date, t.start_time))
    
    @staticmethod
    def filter_tasks(
        tasks: List[Task],
        pet_name: Optional[str] = None,
        status: Optional[str] = None,
        priority: Optional[Priority] = None,
    ) -> List[Task]:
        """
        Filter tasks by pet name (handled upstream), completion status, and priority.
        """
        def ok(t: Task) -> bool:
            if status is not None:
                if status.lower() == "completed" and not t.completed:
                    return False
                if status.lower() == "pending" and t.completed:
                    return False
            if priority is not None and t.priority != priority:
                return False
            return True
        return [t for t in tasks if ok(t)]
    
    @staticmethod
    def detect_conflicts(tasks: List[Task]) -> List[Tuple[Task, Task, str]]:
        """
        Detect conflicts among tasks for the same date.
        Default: same-time collision only (point-in-time).
        """
        conflicts: List[Tuple[Task, Task, str]] = []
        # --- Default same-time detection ---
        by_day: Dict[date, List[Task]] = {}
        for t in tasks:
            by_day.setdefault(t.date, []).append(t)
        for d, day_tasks in by_day.items():
            seen_times: Dict[str, Task] = {}
            for t in Scheduler.sort_by_time(day_tasks):
                st = t.start_time
                if st in seen_times:
                    conflicts.append((seen_times[st], t, "Same start time"))
                else:
                    seen_times[st] = t
        return conflicts
    
    @staticmethod
    def generate_schedule(
        owner: Owner,
        target_date: date,
        time_budget_minutes: Optional[int] = None,
        priority_first: bool = True,
    ) -> Dict[str, Any]:
        """
        Produce an ordered list of tasks for the given date with basic explanation.
        Implementation will be completed in Phase 4.
        """
        # Gather tasks for the target day
        all_tasks = []
        pet_of: Dict[str, str] = {}
        for p in owner.pets:
            for t in p.tasks:
                pet_of[t.id] = p.name
                if t.date == target_date and not t.completed:
                    all_tasks.append(t)

        # Sort
        ordered = (
            Scheduler.sort_by_priority_then_time(all_tasks)
            if priority_first
            else Scheduler.sort_by_time(all_tasks)
        )

       # Filter by time budget if provided
        out_tasks: List[Task] = []
        total = 0
        explanations: List[str] = []
        for t in ordered:
            dur = max(0, t.duration_minutes)
            if time_budget_minutes is not None and total + dur > time_budget_minutes:
                explanations.append(
                    f"Skip: {t.description} @ {t.start_time} ({dur}m) — exceeds remaining budget"
                )
                continue
            out_tasks.append(t)
            total += dur
            explanations.append(
                f"Add: [{pet_of[t.id]}] {t.description} @ {t.start_time} ({dur}m) prio={t.priority.name}"
            )

        # Conflicts (informational)
        conflicts = Scheduler.detect_conflicts(out_tasks)
        for a, b, reason in conflicts:
            explanations.append(
                f"Warning: Conflict between '{a.description}' and '{b.description}' — {reason}"
            )

        payload = {
            "date": target_date.isoformat(),
            "tasks": [
                {
                    "task_id": t.id,
                    "pet": pet_of[t.id],
                    "description": t.description,
                    "time": t.start_time,
                    "duration": max(0, t.duration_minutes),
                    "priority": t.priority.name,
                    "frequency": t.frequency.value,
                    "completed": t.completed,
                }
                for t in out_tasks
            ],
            "explanations": explanations,
        }
        return payload

    @staticmethod
    def mark_task_complete(owner: Owner, task_id: str) -> Optional[Task]:
        """Mark task complete by id; if recurring, append the next occurrence to the same pet.
        Returns the created next-occurrence Task (if any), else None.
        """
        for p in owner.pets:
            for t in p.tasks:
                if t.id == task_id:
                    t.mark_complete()
                    nxt = t.next_occurrence()
                    if nxt is not None:
                        p.add_task(nxt)
                    return nxt
        return None






