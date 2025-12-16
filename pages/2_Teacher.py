import streamlit as st
import pandas as pd
import os

st.set_page_config(page_title="Teacher Panel", layout="wide")
st.title("🎓 Teacher Panel")

CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# ----------------------
# LOAD REQUIRED FILES
# ----------------------
missing = False
for f in [CLASSES_FILE, SUBJECTS_FILE]:
    if not os.path.exists(f):
        st.error(f"❌ Missing required file: {f}")
        missing = True

if missing:
    st.stop()

classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)

# ----------------------
# CLASS SELECTION
# ----------------------
st.subheader("📘 Select Class")

class_name = st.selectbox("Class", classes["ClassName"])
class_id = classes.loc[
    classes["ClassName"] == class_name, "ClassID"
].values[0]

# ----------------------
# SUBJECTS FOR CLASS (NO ERROR IF EMPTY)
# ----------------------
st.subheader("📚 Subjects for Selected Class")

filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.info("ℹ️ No subjects are mapped to this class yet.")
else:
    st.dataframe(
        filtered_subjects[["SubjectID", "SubjectName"]],
        use_container_width=True
    )

# ----------------------
# ACTIVE SESSIONS (VIEW ONLY)
# ----------------------
st.divider()
st.subheader("🟢 Active Sessions")

if not os.path.exists(SESSIONS_FILE):
    st.info("No sessions created yet.")
    st.stop()

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

active_sessions = sessions[
    (sessions["Active"] == "True") &
    (sessions["ClassID"] == class_id)
]

if active_sessions.empty:
    st.info("No active sessions for this class.")
else:
    st.dataframe(
        active_sessions[[
            "SessionCode",
            "SubjectName",
            "CreatedAt",
            "ExpiryMinutes"
        ]],
        use_container_width=True
    )
