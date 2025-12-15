import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Teacher Panel", layout="centered")
st.title("👩‍🏫 Teacher Attendance Panel")

CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# ----------------------
# LOAD FILES
# ----------------------
classes = pd.read_csv(CLASSES_FILE)
subjects = pd.read_csv(SUBJECTS_FILE)

classes["ClassID"] = classes["ClassID"].astype(str)
subjects["ClassID"] = subjects["ClassID"].astype(str)
subjects["SubjectID"] = subjects["SubjectID"].astype(str)

# ----------------------
# SELECT CLASS
# ----------------------
class_name = st.selectbox("Select Class", classes["ClassName"].unique())
class_id = classes.loc[classes["ClassName"] == class_name, "ClassID"].iloc[0]

# ----------------------
# SELECT SUBJECT
# ----------------------
filtered_subjects = subjects[subjects["ClassID"] == class_id]

subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"].unique())
subject_id = filtered_subjects.loc[
    filtered_subjects["SubjectName"] == subject_name, "SubjectID"
].iloc[0]

# ----------------------
# SESSION CODE
# ----------------------
session_code = st.text_input("Enter Session Code").strip()

if st.button("🚀 Activate Session"):

    if not session_code:
        st.error("Session code required")
        st.stop()

    # Create sessions file if missing
    if not os.path.exists(SESSIONS_FILE):
        pd.DataFrame(columns=[
            "SessionCode","ClassID","SubjectID","CreatedAt"
        ]).to_csv(SESSIONS_FILE, index=False)

    sessions = pd.read_csv(SESSIONS_FILE)

    # Prevent duplicate session codes
    if session_code in sessions["SessionCode"].astype(str).values:
        st.error("❌ Session code already active")
        st.stop()

    new_session = {
        "SessionCode": session_code,
        "ClassID": class_id,
        "SubjectID": subject_id,
        "CreatedAt": datetime.now().isoformat()
    }

    sessions = pd.concat([sessions, pd.DataFrame([new_session])], ignore_index=True)
    sessions.to_csv(SESSIONS_FILE, index=False)

    st.success("✅ Session activated successfully")
    st.json(new_session)
