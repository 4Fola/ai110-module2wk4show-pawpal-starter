# tests/test_pawpal_phase4_5.py
from datetime import date
import pytest

from pawpal_system import (
    Owner, Pet, Task, Scheduler, Frequency, Priority,
    TZ_NY, TZ_LAGOS, TZ_UTC_PLUS_5
)

# -----------------------------
# 1) Zone-aware sorting near a DST boundary (New York)
# -----------------------------
def test_zone_aware_sorting_handles_spring_forward_ny():
    """
    On 2026-03-08 in America/New_York, clocks jump from 02:00 -> 03:00.
    We avoid nonexistent 02:xx times; ensure scheduling and sorting still work.
    """
    d = date(2026, 3, 8)  # 2026 DST "spring forward" date in New York
    # Tasks before and after the jump
    t1 = Task(description="Pre-jump task", date=d, start_time="01:30", priority=Priority.MEDIUM)
    t2 = Task(description="Post-jump task", date=d, start_time="03:00", priority=Priority.MEDIUM)

    owner = Owner("Test")
    pet = Pet(name="Buddy", species="Dog", tasks=[t2, t1])  # out of order on purpose
    owner.add_pet(pet)

    # Sort by time in America/New_York; expect 01:30 then 03:00
    ordered = Scheduler.sort_by_time(owner.get_all_tasks(), working_tz=TZ_NY)
    assert [t.description for t in ordered] == ["Pre-jump task", "Post-jump task"]

    # Optional: sanity-check offsets via the internal helper (aware datetime tzname)
    dt1 = Scheduler._aware_dt(t1, TZ_NY)  # 01:30 local -> EST
    dt2 = Scheduler._aware_dt(t2, TZ_NY)  # 03:00 local -> EDT
    assert dt1.tzname() in ("EST", "GMT-05:00")  # tzname representation may vary by platform
    assert dt2.tzname() in ("EDT", "GMT-04:00")

# -----------------------------
# 2) Recurrence logic (daily/weekly/monthly)
# -----------------------------
def test_daily_and_weekly_recurrence():
    today = date(2026, 3, 12)
    daily = Task(description="Daily meds", date=today, start_time="08:00", frequency=Frequency.DAILY)
    weekly = Task(description="Weekly groom", date=today, start_time="10:00", frequency=Frequency.WEEKLY)

    nd = daily.next_occurrence()
    nw = weekly.next_occurrence()

    assert nd is not None and nd.date == date(2026, 3, 13)
    assert nw is not None and nw.date == date(2026, 3, 19)

def test_monthly_recurrence_end_of_month_non_leap():
    # Jan 31, 2025 -> Feb 28, 2025
    jan31 = Task(description="Monthly check", date=date(2025, 1, 31), start_time="09:00", frequency=Frequency.MONTHLY)
    nm = jan31.next_occurrence()
    assert nm is not None and nm.date == date(2025, 2, 28)

def test_monthly_recurrence_end_of_month_leap_year():
    # Jan 31, 2024 -> Feb 29, 2024 (leap year)
    jan31_leap = Task(description="Monthly check", date=date(2024, 1, 31), start_time="09:00", frequency=Frequency.MONTHLY)
    nm = jan31_leap.next_occurrence()
    assert nm is not None and nm.date == date(2024, 2, 29)

# -----------------------------
# 3) Time-window conflict detection toggle
# -----------------------------
def test_window_overlap_conflict_detection_toggle():
    d = date(2026, 3, 15)
    a = Task(description="Walk",  date=d, start_time="08:00", duration_minutes=60)
    b = Task(description="Vets",  date=d, start_time="08:30", duration_minutes=30)

    owner = Owner("Test")
    pet = Pet(name="Mika", species="Cat", tasks=[a, b])
    owner.add_pet(pet)

    # A and B overlap as windows; default mode detects same-time ONLY -> no conflict
    conflicts_default = Scheduler.detect_conflicts(owner.get_all_tasks(), working_tz=TZ_NY, use_time_windows=False)
    assert conflicts_default == []

    # Enable window overlap detection -> should flag one overlap
    conflicts_window = Scheduler.detect_conflicts(owner.get_all_tasks(), working_tz=TZ_NY, use_time_windows=True)
    assert len(conflicts_window) == 1
    (x, y, reason) = conflicts_window[0]
    assert "Overlapping time windows" in reason

# -----------------------------
# 4) Lagos and UTC+05 sanity checks (no DST)
# -----------------------------
def test_no_dst_schedules_are_stable_in_lagos_and_utc_plus5():
    d = date(2026, 3, 8)
    tasks = [
        Task(description="A", date=d, start_time="07:00"),
        Task(description="B", date=d, start_time="07:30"),
        Task(description="C", date=d, start_time="08:00"),
    ]
    # Lagos: UTC+01 year-round; Karachi: UTC+05 year-round.
    lagos = Scheduler.sort_by_time(tasks, working_tz=TZ_LAGOS)
    karachi = Scheduler.sort_by_time(tasks, working_tz=TZ_UTC_PLUS_5)
    assert [t.description for t in lagos] == ["A", "B", "C"]
    assert [t.description for t in karachi] == ["A", "B", "C"]

# Phase 5:
# -----------------------------
# 5) Ambiguous time during "fall back" using fold (zoneinfo behavior)
# -----------------------------
def test_zoneinfo_fold_handles_ambiguous_0130_on_fall_back_ny():
    """
    On 2026-11-01 in New York, clocks fall back at 02:00 -> 01:00.
    01:30 occurs twice (ambiguous). 'fold=0' is the first (DST), 'fold=1' is the second (standard).
    This test uses datetime + ZoneInfo directly to verify the offsets are different and that
    UTC conversions differ by one hour. (Scheduler uses aware datetimes, so this ensures
    the platform's zoneinfo behaves correctly.)
    """
    from datetime import datetime, timezone
    from zoneinfo import ZoneInfo

    tz = ZoneInfo(TZ_NY)
    # First 01:30 (DST, UTC-4)
    dt1 = datetime(2026, 11, 1, 1, 30, tzinfo=tz).replace(fold=0)
    # Second 01:30 (Standard, UTC-5)
    dt2 = datetime(2026, 11, 1, 1, 30, tzinfo=tz).replace(fold=1)

    # Offsets should differ by 1 hour, and UTC instants should differ by 1 hour
    assert dt1.utcoffset() != dt2.utcoffset()
    assert (dt2.astimezone(timezone.utc) - dt1.astimezone(timezone.utc)).total_seconds() == 3600


# -----------------------------
# 6) Scheduler behavior on fall back: same local time conflict
# -----------------------------
def test_conflict_on_fall_back_same_local_time_ny():
    """
    Two tasks at 01:30 local on 2026-11-01 in New York should conflict in default (point-in-time) mode,
    because Scheduler's same-time detection compares local HH:MM strings.
    """
    d = date(2026, 11, 1)
    a = Task(description="First 01:30",  date=d, start_time="01:30")
    b = Task(description="Second 01:30", date=d, start_time="01:30")

    owner = Owner("Owner")
    pet = Pet(name="Buddy", species="Dog", tasks=[a, b])
    owner.add_pet(pet)

    # Default same-time conflict should trigger exactly one "Same start time"
    conflicts = Scheduler.detect_conflicts(owner.get_all_tasks(), working_tz=TZ_NY, use_time_windows=False)
    assert len(conflicts) >= 1
    assert any("Same start time" in reason for _, _, reason in conflicts)   