import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

SESSION_FILE = "session.json"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"
SESSION_VALIDITY = 30  # minutes

# ----------------------
# SESSION STATE LOCK
# ----------------------
if "blocked" not in st.session_state:
    st.session_state.blocked = False

# ----------------------
# LOAD ACTIVE SESSION
# ----------------------
if not os.path.exists(SESSION_FILE):
    st.error("⛔ No active session.")
    st.stop()

with open(SESSION_FILE, "r") as f:
    session = json.load(f)

created_time = datetime.fromisoformat(session["created_at"])
if datetime.now() > created_time + timedelta(minutes=SESSION_VALIDITY):
    st.error("⛔ Session expired")
    st.stop()

# ----------------------
# SESSION CODE
# ----------------------
entered_code = st.text_input("Enter Session Code")

if entered_code != session["session_code"]:
    st.warning("❗ Invalid session code")
    st.stop()

# ----------------------
# LOAD STUDENTS
# ----------------------
if not os.path.exists(STUDENTS_FILE):
    st.error("❌ Students file missing.")
    st.stop()

students = pd.read_excel(STUDENTS_FILE)
filtered = students[students["ClassID"] == session["class_id"]]

if filtered.empty:
    st.error("No students for this class.")
    st.stop()

# ----------------------
# STUDENT SELECT
# ----------------------
roll = st.selectbox("Select Roll Number", filtered["RollNumber"].astype(str))
student = filtered[filtered["RollNumber"].astype(str) == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

today = datetime.now().strftime("%Y-%m-%d")

# ----------------------
# LOAD ATTENDANCE
# ----------------------
attendance = (
    pd.read_csv(ATTENDANCE_FILE)
    if os.path.exists(ATTENDANCE_FILE)
    else pd.DataFrame(columns=[
        "Date","ClassID","SubjectID","SessionCode",
        "RollNumber","StudentName","EnrollmentNumber"
    ])
)

# ----------------------
# HARD DUPLICATE CHECK (BEFORE BUTTON)
# ----------------------
already_marked = (
    (attendance["Date"] == today) &
    (attendance["ClassID"] == session["class_id"]) &
    (attendance["SubjectID"] == session["subject_id"]) &
    (attendance["SessionCode"] == session["session_code"]) &
    (attendance["RollNumber"].astype(str) == roll)
).any()

if already_marked:
    st.success("✅ Attendance already submitted.")
    st.stop()

# ----------------------
# SUBMIT
# ----------------------
if st.button("✅ Submit Attendance"):

    new_row = {
        "Date": today,
        "ClassID": session["class_id"],
        "SubjectID": session["subject_id"],
        "SessionCode": session["session_code"],
        "RollNumber": roll,
        "StudentName": student["StudentName"],
        "EnrollmentNumber": student["EnrollmentNumber"]
    }

    attendance = pd.concat([attendance, pd.DataFrame([new_row])], ignore_index=True)
    attendance.to_csv(ATTENDANCE_FILE, index=False)

    st.success("🎉 Attendance marked successfully")
    st.stop()
