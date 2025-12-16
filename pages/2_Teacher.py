import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="centered")
st.title("👩‍🏫 Teacher Login")

TEACHERS_FILE = "teachers.csv"
SESSIONS_FILE = "sessions.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"

# ---------------- LOGIN ----------------
if "teacher" not in st.session_state:
    st.session_state.teacher = None

if st.session_state.teacher is None:

    if not os.path.exists(TEACHERS_FILE):
        st.error("teachers.csv not found")
        st.stop()

    teachers = pd.read_csv(TEACHERS_FILE)

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("🔐 Login"):
        match = teachers[
            (teachers["Email"] == email) &
            (teachers["Password"] == password)
        ]

        if match.empty:
            st.error("Invalid credentials")
            st.stop()

        st.session_state.teacher = match.iloc[0].to_dict()
        st.experimental_rerun()

    st.stop()

# ---------------- LOGGED IN ----------------
teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")

if st.button("🚪 Logout"):
    st.session_state.teacher = None
    st.experimental_rerun()

st.divider()
st.subheader("📚 Start New Session")

# ---------------- LOAD DATA ----------------
classes = pd.read_csv(CLASSES_FILE)
subjects = pd.read_csv(SUBJECTS_FILE)

class_name = st.selectbox("Select Class", classes["ClassName"])
class_id = classes[classes["ClassName"] == class_name]["ClassID"].iloc[0]

filtered_subjects = subjects[subjects["ClassID"] == class_id]

subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
subject_id = filtered_subjects[filtered_subjects["SubjectName"] == subject_name]["SubjectID"].iloc[0]

session_code = st.text_input("Session Code")
expiry = st.number_input("Session Validity (minutes)", value=30)

if st.button("🚀 Activate Session"):

    new_session = {
        "SessionID": str(uuid.uuid4())[:8],
        "TeacherID": teacher["TeacherID"],
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
    st.success(f"✅ Session started\nSession Code: {session_code}")

# ---------------- TEACHER'S SESSIONS ----------------
st.divider()
st.subheader("🕒 My Sessions")

sessions = pd.read_csv(SESSIONS_FILE)
my_sessions = sessions[sessions["TeacherID"] == teacher["TeacherID"]]

st.dataframe(my_sessions, use_container_width=True)
