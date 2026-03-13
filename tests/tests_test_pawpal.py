
from datetime import date
import pytest
from pawpal_system import Owner, Pet, Task, Scheduler, Frequency, Priority


def test_task_completion_flag_flips():
    t = Task(description="Test", date=date.today(), start_time="10:00")
    assert t.completed is False
    t.mark_complete()
    assert t.completed is True


def test_adding_task_increases_pet_count():
    p = Pet(name="Buddy", species="Dog")
    assert len(p.get_tasks()) == 0
    p.add_task(Task(description="Walk", date=date.today(), start_time="08:00"))
    assert len(p.get_tasks()) == 1


def test_sort_by_time_orders_chronologically():
    today = date.today()
    tasks = [
        Task(description="C", date=today, start_time="12:00"),
        Task(description="A", date=today, start_time="07:30"),
        Task(description="B", date=today, start_time="09:15"),
    ]
    ordered = Scheduler.sort_by_time(tasks)
    assert [t.description for t in ordered] == ["A", "B", "C"]
