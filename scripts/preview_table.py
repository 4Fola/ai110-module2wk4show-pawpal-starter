"""Preview the colored schedule table styling in isolation.

Run: streamlit run scripts/preview_table.py
"""
from __future__ import annotations
import streamlit as st
import pandas as pd

st.set_page_config(page_title="PawPal+ Preview", page_icon="🐾", layout="centered")
st.title("PawPal+ | Styled Schedule Preview")

# Legend
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

# Sample rows
rows = [
    {"Pet":"Buddy","Time":"07:30","Task":"Feed breakfast","Duration (min)":10,"Priority":"🔴 HIGH","Freq":"Daily"},
    {"Pet":"Mika","Time":"08:00","Task":"Morning walk","Duration (min)":30,"Priority":"🟡 MEDIUM","Freq":"Daily"},
    {"Pet":"Luna","Time":"09:15","Task":"Administer meds","Duration (min)":5,"Priority":"🔴 HIGH","Freq":"Weekly"},
    {"Pet":"Buddy","Time":"13:00","Task":"Grooming","Duration (min)":45,"Priority":"🟢 LOW","Freq":"Monthly"},
]
df = pd.DataFrame(rows)

# Styler to color Priority column
def _color_priority(val: str):
    up = str(val).upper()
    if "HIGH" in up:
        return "background-color:#ffe5e5"
    if "MEDIUM" in up:
        return "background-color:#fff7d6"
    if "LOW" in up:
        return "background-color:#eaffea"
    return ""

styled = df.style.applymap(_color_priority, subset=["Priority"])  # color only the Priority column
st.dataframe(styled, use_container_width=True)

st.caption("This preview uses the same styling approach applied in app.py (pandas Styler).")