import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Admin – Create Session", layout="centered")
st.title("🛠️ Admin Dashboard – Create Session")

CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# ----------------------
# LOAD MASTER DATA
# ----------------------
if not os.path.exists(CLASSES_FILE) or not os.path.exists(SUBJECTS_FILE):
    st.error("❌ classes.csv or subjects.csv missing")
    st.stop()

classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)

# ----------------------
# SELECT CLASS
# ----------------------
class_name = st.selectbox("Select Class", classes["ClassName"])
class_row = classes[classes["ClassName"] == class_name].iloc[0]
class_id = class_row["ClassID"]

# ----------------------
# SELECT SUBJECT (FILTERED)
# ----------------------
filtered_subjects = subjects[subjects["ClassID"] == class_id]

if filtered_subjects.empty:
    st.error("❌ No subjects mapped to this class")
    st.stop()

subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
subject_row = filtered_subjects[filtered_subjects["SubjectName"] == subject_name].iloc[0]
subject_id = subject_row["SubjectID"]

# ----------------------
# SESSION SETTINGS
# ----------------------
session_code = st.text_input("Session Code (students will enter this)")
expiry = st.number_input("Session Validity (minutes)", min_value=5, max_value=180, value=30)

# ----------------------
# CREATE SESSION
# ----------------------
if st.button("🚀 Activate Session"):

    if not session_code.strip():
        st.error("❌ Session code cannot be empty")
        st.stop()

    # Ensure sessions file exists
    if not os.path.exists(SESSIONS_FILE):
        pd.DataFrame(columns=[
            "SessionID",
            "SessionCode",
            "ClassID",
            "SubjectID",
            "SubjectName",
            "CreatedAt",
            "ExpiryMinutes",
            "Active"
        ]).to_csv(SESSIONS_FILE, index=False)

    sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

    # 🔒 Deactivate existing active session with same code
    sessions.loc[
        (sessions["SessionCode"] == session_code) & (sessions["Active"] == "True"),
        "Active"
    ] = "False"

    # ✅ Create new session row
    new_session = {
        "SessionID": str(uuid.uuid4()),
        "SessionCode": session_code.strip(),
        "ClassID": class_id,
        "SubjectID": subject_id,
        "SubjectName": subject_name,
        "CreatedAt": datetime.now().isoformat(),
        "ExpiryMinutes": str(expiry),
        "Active": "True"
    }

    sessions = pd.concat([sessions, pd.DataFrame([new_session])], ignore_index=True)
    sessions.to_csv(SESSIONS_FILE, index=False)

    st.success("✅ Session activated successfully")
    st.info(f"📌 Session Code: **{session_code}**")
