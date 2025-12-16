import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="centered")
st.title("👩‍🏫 Teacher – Start Session")

SESSIONS_FILE = "sessions.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"

# ---------- Load data ----------
classes = pd.read_csv(CLASSES_FILE)
subjects = pd.read_csv(SUBJECTS_FILE)

class_name = st.selectbox("Select Class", classes["ClassName"])
class_id = classes[classes["ClassName"] == class_name]["ClassID"].iloc[0]

filtered_subjects = subjects[subjects["ClassID"] == class_id]
subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
subject_id = filtered_subjects[filtered_subjects["SubjectName"] == subject_name]["SubjectID"].iloc[0]

session_code = st.text_input("Set Session Code")
expiry = st.number_input("Session Validity (minutes)", value=30)

if st.button("🚀 Activate Session"):

    session_id = str(uuid.uuid4())[:8]

    new_session = {
        "SessionID": session_id,
        "ClassID": class_id,
        "SubjectID": subject_id,
        "SessionCode": session_code,
        "CreatedAt": datetime.now().isoformat(),
        "ExpiryMinutes": expiry,
        "Active": True
    }

    if os.path.exists(SESSIONS_FILE):
        df = pd.read_csv(SESSIONS_FILE)
        df = pd.concat([df, pd.DataFrame([new_session])])
    else:
        df = pd.DataFrame([new_session])

    df.to_csv(SESSIONS_FILE, index=False)

    st.success(f"✅ Session Started\n\nSession Code: {session_code}")
