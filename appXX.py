
from __future__ import annotations
import os
from datetime import date as dt_date, time as dt_time
import streamlit as st
from pawpal_system import (
    Owner, Pet, Task, Scheduler, Frequency, Priority,
    TZ_NY, TZ_LAGOS, TZ_UTC_PLUS_5
)
# -------------------------------
# Session bootstrapping
# -------------------------------
if 'owner' not in st.session_state:
    st.session_state.owner = Owner(name='PawPal Owner')
if 'display_tz' not in st.session_state:
    st.session_state.display_tz = TZ_NY # This should default to America/New_York
owner: Owner = st.session_state.owner
# -------------------------------
# Creating The Sidebar
# -------------------------------
st.sidebar.title('PawPal+')
st.sidebar.caption('Smart pet care scheduler - Phase 3/4 UI')
# Selection of Timezone
label = {
    TZ_NY: 'America/New_York (EST/EDT)',
    TZ_LAGOS: 'Africa/Lagos (UTC+01:00)',
    TZ_UTC_PLUS_5: 'UTC+05:00 (Asia/Karachi)'
}
st.session_state.display_tz = st.sidebar.selectbox(
    'Display time zone (conversion in Phase 4):',
    options=[TZ_NY, TZ_LAGOS, TZ_UTC_PLUS_5],
    format_func=lambda k: label[k],
    index=0,
)
# Persistence Setup Controls
with st.sidebar.expander('Save / Load'):
    c1, c2 = st.columns(2)
    with c1:
        if st.button('💾 Save JSON'):
            owner.save_to_json('data.json')
            st.success('Saved to data.json')
    with c2:
        if st.button('📂 Load JSON'):
            try:
                st.session_state.owner = Owner.load_from_json('data.json')
                owner = st.session_state.owner
                st.success('Loaded from data.json')
            except FileNotFoundError:
                st.warning('data.json not found')
# -------------------------------
# The Main Layout
# -------------------------------
st.title('PawPal+ — Pet Care Scheduler')
# Workflow Tabs
add_pet_tab, add_task_tab, schedule_tab = st.tabs(["➕ Add Pet", "📝 Add Task", "📆 Today's Schedule"])
# -------------------------------
# Tab For Adding Pet(s)
# -------------------------------
with add_pet_tab:
    st.subheader('Add a new pet')
    with st.form('form_add_pet', clear_on_submit=True):
        pet_name = st.text_input('Pet name', placeholder='e.g., Dog', max_chars=60)
        species = st.text_input('Species', placeholder='e.g., Dog', max_chars=60)
        submitted = st.form_submit_button('Add Pet')
        if submitted:
            if not pet_name.strip():
                st.error('Please provide a valid pet name.')
            elif owner.get_pet(pet_name.strip()) is not None:
                st.error('A pet with that name already exists.')
            else:
                owner.add_pet(Pet(name=pet_name.strip(), species=species.strip() or 'Unknown'))
                st.success(f"Added pet: {pet_name.strip()}")
    if owner.pets:
        st.markdown('**Current pets:** ' + ', '.join(p.name for p in owner.pets))
    else:
        st.info('No pets yet - add pne to get started.')
# -------------------------------
# Add Task tab
# -------------------------------
with add_task_tab:
    st.subheader('Add a task')
    if not owner.pets:
        st.warning('Add a pet first.')
    else:
        pet_names = [p.name for p in owner.pets]
        with st.form('form_add_task', clear_on_submit=True):
            pet_name = st.selectbox('Pet', options=pet_names)
            description = st.text_input('Description', placeholder='e.g., Morning walk')
            task_date = st.date_input('Date', value=dt_date.today())
            t = st.time_input('Start time', value=dt_time(8, 0)) # default 08:00
            hhmm = f"{t.hour:02d}:{t.minute:02d}"
            duration = st.number_input('Duration (minutes)', min_value=0, max_value=24*60, value=30, step=5)
            freq = st.selectbox('Frequency', options=list(Frequency), format_func=lambda f: f.value.title())
            prio = st.selectbox('Priority', options=list(Priority), format_func=lambda p: p.name.title(), index=2)
            submitted = st.form_submit_button('Add Task')
            if submitted:
                if not description.strip():
                    st.error('Please provide a description.')
                else:
                    pet = owner.get_pet(pet_name)
                    pet.add_task(Task(
                        description=description.strip(),
                        date=task_date,
                        start_time=hhmm,
                        duration_minutes=int(duration),
                        frequency=freq,
                        priority=prio,
                    ))
                    st.success(f"Task added for {pet_name}: {description.strip()} @ {hhmm}")
# -------------------------------
# Schedule tab
# -------------------------------
with schedule_tab:
    st.subheader("Generate today's schedule")

# --- PHASE6-EXT: Priority legend (UI-only) ---
with st.container():
    st.markdown(
        """
        **Priority Legend:**  
        <span style="background-color:#ffe5e5;padding:3px 8px;border-radius:6px;">🔴 HIGH</span>&nbsp;&nbsp;
        <span style="background-color:#fff7d6;padding:3px 8px;border-radius:6px;">🟡 MEDIUM</span>&nbsp;&nbsp;
        <span style="background-color:#eaffea;padding:3px 8px;border-radius:6px;">🟢 LOW</span>
        """,
        unsafe_allow_html=True,
    )
    
    # Controls
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        day = st.date_input('Date', value=dt_date.today(), key='sched_date')
    with c2:
        priority_first = st.checkbox('Priority first (High→Low, then time)', value=True)
    with c3:
        use_budget = st.checkbox('Use time budget?')
    budget = None
    if use_budget:
        budget = st.number_input('Time budget (minutes)', min_value=1, max_value=24*60, value=120, step=5)
    # Phase 4 toggle
    use_windows = st.checkbox('Detect overlapping time windows (start_time + duration)', value=False)

    # --- PHASE6: Optional quick filters (UI-only post-processing) ---
    with st.expander("Filters (UI-only)"):
        pet_names = [p.name for p in owner.pets]
        pet_filter = st.multiselect("Pets", options=pet_names, default=pet_names)
        status_filter = st.selectbox("Status", options=["All", "Pending only", "Completed only"], index=1)
        prio_filter = st.selectbox("Priority", options=["All", "High", "Medium", "Low"], index=0)

    # Show schedule
    if st.button('Generate schedule'):
        payload = Scheduler.generate_schedule(
            owner,
            target_date=day,
            time_budget_minutes=budget,
            priority_first=priority_first,
            working_tz=st.session_state.display_tz, # use selected IANA zone
            use_time_windows=use_windows, # enable/disable window overlap conflicts
        )
        tasks = payload['tasks']

        # --- PHASE6: Apply filters to payload tasks ---
        def _status_ok(item):
            if status_filter == "All":
                return True
            if status_filter == "Pending only":
                return not item["completed"]
            if status_filter == "Completed only":
                return item["completed"]
            return True

        def _prio_ok(item):
            if prio_filter == "All":
                return True
            return item["priority"].upper() == prio_filter.upper()

        tasks = [t for t in tasks if t["pet"] in pet_filter and _status_ok(t) and _prio_ok(t)]

        if tasks:
            st.success(f"Scheduled {len(tasks)} task(s) for {payload['date']} (TZ={payload['working_tz']})")

# --- PHASE6: Display polish (priority emoji, cleaner columns) ---
            priority_icon = {"HIGH": "🔴 HIGH", "MEDIUM": "🟡 MEDIUM", "LOW": "🟢 LOW"}
            for row in tasks:
                row["priority"] = priority_icon.get(row["priority"], row["priority"])  # mutate display only

            def _pretty(row):
                return {
                    "Pet": row["pet"],
                    "Time": row["time"],
                    "Task": row["description"],
                    "Duration (min)": row["duration"],
                    "Priority": row["priority"],
                    "Freq": row["frequency"].title(),
                }
            _display_rows = [_pretty(r) for r in tasks]
            st.dataframe(_display_rows, use_container_width=True)

            
        else:
            st.info('No tasks scheduled for the selected date.')
        # Explanations / warnings
        with st.expander('Details / Warnings'):
            for line in payload['explanations']:
                if line.lower().startswith('warning:'):
                    st.warning(line)
                elif line.lower().startswith('skip:'):
                    st.info(line)
                else:
                    st.write('• ' + line)
    # Quick controls for marking tasks complete (for the selected date)
    st.divider()
    st.caption('Mark a task as completed (and auto-create next occurrence if recurring).')
    # Build dropdown of pending tasks for the chosen date
    pending = []
    for p in owner.pets:
        for t in p.tasks:
            if t.date == st.session_state.get('sched_date', dt_date.today()) and not t.completed:
                pending.append((p.name, t))
    if pending:
        options = [f"[{pet}] {t.start_time} — {t.description}" for pet, t in pending]
        idx = st.selectbox('Select task', options=list(range(len(options))), format_func=lambda i: options[i])
        if st.button('✅ Mark complete'):
            pet, t = pending[idx]
            nxt = Scheduler.mark_task_complete(owner, t.id)
            if nxt is not None:
                st.success(f"Marked complete and scheduled next occurrence on {nxt.date.isoformat()} @ {nxt.start_time}")
            else:
                st.success('Marked complete.')
    else:
        st.info('No pending tasks for the selected date.')
# st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
# st.title("🐾 PawPal+")
# st.markdown(
# """
# Welcome to the PawPal+ starter app.
# This file is intentionally thin. It gives you a working Streamlit app so you can start quickly,
# but **it does not implement the project logic**. Your job is to design the system and build it.
# Use this app as your interactive demo once your backend classes/functions exist.
# """
# )
# with st.expander("Scenario", expanded=True):
# st.markdown(
# """
# **PawPal+** is a pet care planning assistant. It helps a pet owner plan care tasks
# for their pet(s) based on constraints like time, priority, and preferences.
# You will design and implement the scheduling logic and connect it to this Streamlit UI.
# """
# )
# with st.expander("What you need to build", expanded=True):
# st.markdown(
# """
# At minimum, your system should:
# - Represent pet care tasks (what needs to happen, how long it takes, priority)
# - Represent the pet and the owner (basic info and preferences)
# - Build a plan/schedule for a day that chooses and orders tasks based on constraints
# - Explain the plan (why each task was chosen and when it happens)
# """
# )
# st.divider()
# st.subheader("Quick Demo Inputs (UI only)")
# owner_name = st.text_input("Owner name", value="Jordan")
# pet_name = st.text_input("Pet name", value="Mochi")
# species = st.selectbox("Species", ["dog", "cat", "other"])
# st.markdown("### Tasks")
# st.caption("Add a few tasks. In your final version, these should feed into your scheduler.")
# if "tasks" not in st.session_state:
# st.session_state.tasks = []
# col1, col2, col3 = st.columns(3)
# with col1:
# task_title = st.text_input("Task title", value="Morning walk")
# with col2:
# duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
# with col3:
# priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)
# if st.button("Add task"):
# st.session_state.tasks.append(
# {"title": task_title, "duration_minutes": int(duration), "priority": priority}
# )
# if st.session_state.tasks:
# st.write("Current tasks:")
# st.table(st.session_state.tasks)
# else:
# st.info("No tasks yet. Add one above.")
# st.divider()
# st.subheader("Build Schedule")
# st.caption("This button should call your scheduling logic once you implement it.")
# if st.button("Generate schedule"):
# st.warning(
# "Not implemented yet. Next step: create your scheduling logic (classes/functions) and call it here."
# )
# st.markdown(
# """
# Suggested approach:
# 1. Design your UML (draft).
# 2. Create class stubs (no logic).
# 3. Implement scheduling behavior.
# 4. Connect your scheduler here and display results.
# """
# )
