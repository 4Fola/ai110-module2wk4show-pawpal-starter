"""Seed demo data for PawPal+.

Usage:
    python scripts/seed_demo_data.py [--tasks 80] [--pets 3] [--start YYYY-MM-DD] [--days 30] [--append]

By default, creates ~80 tasks across 3 pets over the next 30 days and writes/updates data.json.
- If --append is omitted and data.json exists, new pets/tasks are merged into the existing Owner.
- If you pass --append, it will append tasks to existing pets; missing pets will be added.

No external dependencies required.
"""
from __future__ import annotations
import argparse
import os
import random
import sys
from datetime import date, datetime, timedelta
from typing import List

# Add parent directory to path to import pawpal_system
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from pawpal_system import Owner, Pet, Task, Frequency, Priority

PET_NAME_POOL = [
    "Buddy","Mika","Max","Luna","Charlie","Bella","Rocky","Daisy","Milo","Coco",
    "Zoe","Oscar","Simba","Nala","Ruby","Leo","Mochi","Poppy","Finn","Piper"
]

DESCRIPTIONS = [
    "Morning walk","Evening walk","Feed breakfast","Feed dinner","Playtime",
    "Training","Grooming","Bath","Nail trim","Brushing","Litter clean",
    "Administer meds","Vet check","Weight check","Teeth cleaning","Flea treatment"
]

PRIORITY_WEIGHTS = [(Priority.HIGH, 0.25), (Priority.MEDIUM, 0.5), (Priority.LOW, 0.25)]
FREQUENCY_WEIGHTS = [
    (Frequency.ONCE, 0.65), (Frequency.DAILY, 0.20), (Frequency.WEEKLY, 0.10), (Frequency.MONTHLY, 0.05)
]

def _weighted_choice(pairs):
    r = random.random()
    cum = 0.0
    for val, w in pairs:
        cum += w
        if r <= cum:
            return val
    return pairs[-1][0]

def _random_start_time():
    # between 06:00 and 21:00 in 5-minute increments
    start_min = 6*60
    end_min = 21*60
    m = random.randrange(start_min, end_min+1, 5)
    return f"{m//60:02d}:{m%60:02d}"

def _random_duration():
    # durations between 5 and 60 minutes (weighted toward 15-30)
    choices = [5,10,15,20,25,30,35,40,45,50,60]
    weights =  [1, 1, 6, 6, 5, 5, 3, 2, 2, 1, 1]
    return random.choices(choices, weights=weights, k=1)[0]

def _ensure_pets(owner: Owner, count: int) -> List[Pet]:
    existing = {p.name for p in owner.pets}
    pets: List[Pet] = owner.pets
    pool = [n for n in PET_NAME_POOL if n not in existing]
    while len(pets) < count and pool:
        name = pool.pop(0)
        species = random.choice(["Dog","Cat"])
        owner.add_pet(Pet(name=name, species=species))
        pets = owner.pets
    return pets

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tasks', type=int, default=80, help='Total number of tasks to create (50–100 recommended)')
    ap.add_argument('--pets', type=int, default=3, help='Number of pets to have (will add if missing)')
    ap.add_argument('--start', type=str, default=date.today().isoformat(), help='Start date YYYY-MM-DD')
    ap.add_argument('--days', type=int, default=30, help='Range of days from start to distribute tasks')
    ap.add_argument('--append', action='store_true', help='Append tasks to existing pets; add pets if missing')
    args = ap.parse_args()

    # Load or create Owner
    if os.path.exists('data.json'):
        owner = Owner.load_from_json('data.json')
    else:
        owner = Owner(name='PawPal Owner')

    # Ensure desired number of pets
    _ensure_pets(owner, max(1, args.pets))

    start_date = datetime.fromisoformat(args.start).date()

    # Generate tasks
    total = max(1, args.tasks)
    rng_days = max(1, args.days)

    for _ in range(total):
        pet = random.choice(owner.pets)
        d = start_date + timedelta(days=random.randrange(rng_days))
        desc = random.choice(DESCRIPTIONS)
        start_time = _random_start_time()
        dur = _random_duration()
        prio = _weighted_choice(PRIORITY_WEIGHTS)
        freq = _weighted_choice(FREQUENCY_WEIGHTS)
        pet.add_task(Task(
            description=desc,
            date=d,
            start_time=start_time,
            duration_minutes=dur,
            priority=prio,
            frequency=freq,
        ))

    owner.save_to_json('data.json')
    print(f"Seed complete. Pets={len(owner.pets)}, Total tasks now={len(owner.get_all_tasks())}")

if __name__ == '__main__':
    main()