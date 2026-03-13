
"""CLI demo for PawPal+ (Phase 2)
Run:  python main.py

What it does:
- Builds an Owner with two Pets
- Adds several Tasks (different times, durations, frequencies)
- Generates and prints Today’s schedule (priority -> time)
- Demonstrates JSON save/load roundtrip
"""
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler, Frequency, Priority


def build_sample_owner() -> Owner:
    owner = Owner(name="Demo Owner")

    dog = Pet(name="Buddy", species="Dog")
    cat = Pet(name="Mika", species="Cat")

    today = date.today()

    # Tasks (intentionally out of time order)
    dog.add_task(Task(
        description="Morning walk",
        date=today,
        start_time="08:00",
        duration_minutes=30,
        frequency=Frequency.DAILY,
        priority=Priority.HIGH,
    ))

    dog.add_task(Task(
        description="Feed breakfast",
        date=today,
        start_time="07:30",
        duration_minutes=10,
        frequency=Frequency.DAILY,
        priority=Priority.HIGH,
    ))

    cat.add_task(Task(
        description="Administer meds",
        date=today,
        start_time="09:15",
        duration_minutes=5,
        frequency=Frequency.WEEKLY,
        priority=Priority.HIGH,
    ))

    cat.add_task(Task(
        description="Grooming session",
        date=today,
        start_time="13:00",
        duration_minutes=45,
        frequency=Frequency.MONTHLY,
        priority=Priority.MEDIUM,
    ))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner


def print_schedule(payload: dict) -> None:
    print("=== Today’s Schedule ===")
    for i, item in enumerate(payload["tasks"], 1):
        print(f"{i:02d}. [{item['pet']}] {item['time']}  {item['description']}  "
              f"({item['duration']}m, {item['priority']}, {item['frequency']})")
    if not payload["tasks"]:
        print("(no tasks)")

    print("-- Notes --")
    for line in payload["explanations"]:
        print("-", line)


def main():
    owner = build_sample_owner()

    # Generate prioritized schedule for today with no time budget
    today = date.today()
    schedule = Scheduler.generate_schedule(owner, target_date=today, time_budget_minutes=None, priority_first=True)
    print_schedule(schedule)

    # Persist to JSON, then load and show task count
    owner.save_to_json("data.json")
    loaded = Owner.load_from_json("data.json")
    print(f"Saved + loaded JSON. Owner='{loaded.name}', Pets={len(loaded.pets)}, Tasks={len(loaded.get_all_tasks())}")


if __name__ == "__main__":
    main()
