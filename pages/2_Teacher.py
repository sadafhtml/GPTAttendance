import streamlit as st
import pandas as pd
from datetime import datetime
import uuid
import os

st.set_page_config(page_title="Teacher Panel", layout="wide")
st.title("👩‍🏫 Teacher Panel")

# ---------------- FILE PATHS ----------------
TEACHERS_FILE = "teachers.csv"
CLASSES_FILE = "classes.csv"
SUBJECTS_FILE = "subjects.csv"
SESSIONS_FILE = "sessions.csv"

# ---------------- REQUIRED COLUMNS ----------------
REQUIRED_COLUMNS = [
    "SessionID","TeacherID","ClassID","ClassName",
    "SubjectID","SubjectName","SessionCode",
    "CreatedAt","ExpiryMinutes","Active"
]

# ---------------- ENSURE SESSIONS FILE ----------------
if not os.path.exists(SESSIONS_FILE):
    pd.DataFrame(columns=REQUIRED_COLUMNS).to_csv(SESSIONS_FILE, index=False)

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)
for col in REQUIRED_COLUMNS:
    if col not in sessions.columns:
        sessions[col] = ""

# ---------------- TEACHER LOGIN ----------------
if "teacher" not in st.session_state:
    st.session_state.teacher = None

if st.session_state.teacher is None:
    if not os.path.exists(TEACHERS_FILE):
        st.error("❌ teachers.csv not found")
        st.stop()

    teachers = pd.read_csv(TEACHERS_FILE, dtype=str)
    for col in ["Email", "Password"]:
        teachers[col] = teachers[col].str.strip()

    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("🔐 Login"):
        try:
            match = teachers[
                (teachers["Email"] == email.strip()) &
                (teachers["Password"] == password.strip())
            ]
            if match.empty:
                st.error("❌ Invalid credentials")
            else:
                st.session_state.teacher = match.iloc[0].to_dict()
                st.experimental_rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")

    st.stop()  # stop until login is successful

# ---------------- LOGGED IN ----------------
teacher = st.session_state.teacher
st.success(f"Welcome {teacher['TeacherName']}")

if st.button("🚪 Logout"):
    st.session_state.teacher = None
    st.experimental_rerun()

st.divider()

# ---------------- LOAD MASTER DATA ----------------
for file in [CLASSES_FILE, SUBJECTS_FILE]:
    if not os.path.exists(file):
        st.error(f"❌ Missing required file: {file}")
        st.stop()

classes = pd.read_csv(CLASSES_FILE, dtype=str)
subjects = pd.read_csv(SUBJECTS_FILE, dtype=str)

# ---------------- CREATE NEW SESSION ----------------
st.subheader("📚 Start New Session")

if classes.empty:
    st.warning("No classes available.")
else:
    class_name = st.selectbox("Select Class", classes["ClassName"])
    class_id = classes.loc[classes["ClassName"] == class_name, "ClassID"].values[0]

    # Only subjects mapped to this class
    filtered_subjects = subjects[subjects["ClassID"] == class_id]

    if filtered_subjects.empty:
        st.info("ℹ️ No subjects mapped to this class yet.")
        subject_name = None
        subject_id = None
    else:
        subject_name = st.selectbox("Select Subject", filtered_subjects["SubjectName"])
        subject_id = filtered_subjects.loc[
            filtered_subjects["SubjectName"] == subject_name, "SubjectID"
        ].values[0]

    session_code = st.text_input("Session Code")
    expiry_minutes = st.number_input(
        "Session Validity (minutes)", min_value=5, max_value=180, value=30
    )

    if st.button("🚀 Activate Session"):
        if not session_code.strip():
            st.error("❌ Session code cannot be empty")
            st.stop()
        if filtered_subjects.empty:
            st.error("❌ Cannot activate session without a subject")
            st.stop()

        # Reload sessions and ensure all columns
        sessions = pd.read_csv(SESSIONS_FILE, dtype=str)
        for col in REQUIRED_COLUMNS:
            if col not in sessions.columns:
                sessions[col] = ""

        # Deactivate previous active session for this teacher/class/subject
        sessions.loc[
            (sessions["TeacherID"] == teacher["TeacherID"]) &
            (sessions["ClassID"] == class_id) &
            (sessions["SubjectID"] == subject_id) &
            (sessions["Active"] == "True"),
            "Active"
        ] = "False"

        new_session = {
            "SessionID": str(uuid.uuid4())[:8],
            "TeacherID": teacher["TeacherID"],
            "ClassID": class_id,
            "ClassName": class_name,
            "SubjectID": subject_id,
            "SubjectName": subject_name,
            "SessionCode": session_code.strip(),
            "CreatedAt": datetime.now().isoformat(),
            "ExpiryMinutes": str(expiry_minutes),
            "Active": "True"
        }

        sessions = pd.concat([sessions, pd.DataFrame([new_session])], ignore_index=True)
        sessions.to_csv(SESSIONS_FILE, index=False)

        st.success(f"✅ Session activated successfully\nSession Code: {session_code.strip()}")

# ---------------- VIEW TEACHER'S ACTIVE SESSIONS ----------------
st.divider()
st.subheader("🟢 My Active Sessions")

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)
for col in REQUIRED_COLUMNS:
    if col not in sessions.columns:
        sessions[col] = ""

my_sessions = sessions[
    (sessions["TeacherID"] == teacher["TeacherID"]) &
    (sessions["Active"] == "True")
]

if my_sessions.empty:
    st.info("No active sessions")
else:
    st.dataframe(
        my_sessions[[
            "SessionCode","ClassName","SubjectName","CreatedAt","ExpiryMinutes"
        ]],
        use_container_width=True
    )
