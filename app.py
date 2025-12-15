import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

# ----------------------
# PAGE SETUP
# ----------------------
st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

BASE_DIR = os.getcwd()

SESSION_FILE = os.path.join(BASE_DIR, "session.json")
ATTENDANCE_FILE = os.path.join(BASE_DIR, "attendance.csv")
STUDENTS_FILE = os.path.join(BASE_DIR, "Students.xlsx")

SESSION_VALIDITY = 30  # minutes

# ----------------------
# LOAD SESSION SAFELY
# ----------------------
if not os.path.exists(SESSION_FILE) or os.stat(SESSION_FILE).st_size == 0:
    st.error("⛔ No active session. Please contact your teacher.")
    st.stop()

try:
    with open(SESSION_FILE, "r", encoding="utf-8") as f:
        session = json.load(f)
except Exception:
    st.error("⛔ Session file corrupted. Contact Admin.")
    st.stop()

required_keys = {"session_code", "class_id", "subject_id", "created_at"}
if not required_keys.issubset(session.keys()):
    st.error("⛔ Invalid session data. Contact Admin.")
    st.stop()

created_time = datetime.fromisoformat(session["created_at"])
if datetime.now() > created_time + timedelta(minutes=SESSION_VALIDITY):
    st.error("⛔ Session expired")
    st.stop()

# ----------------------
# SESSION CODE INPUT
# ----------------------
entered_code = st.text_input("Enter Session Code")

if entered_code != session["session_code"]:
    st.stop()

# ----------------------
# LOAD STUDENTS
# ----------------------
if not os.path.exists(STUDENTS_FILE):
    st.error("❌ Students file not found. Contact Admin.")
    st.stop()

students = pd.read_excel(STUDENTS_FILE)

# Normalize column names (VERY IMPORTANT)
students.columns = students.columns.str.strip().str.replace(" ", "")

required_student_cols = {"RollNumber", "StudentName", "EnrollmentNumber", "ClassID"}
if not required_student_cols.issubset(students.columns):
    st.error("❌ Students file columns are incorrect.")
    st.stop()

filtered_students = students[students["ClassID"] == session["class_id"]]

if filtered_students.empty:
    st.warning("No students found for this class.")
    st.stop()

# ----------------------
# STUDENT SELECTION
# ----------------------
roll = st.selectbox(
    "Select Your Roll Number",
    filtered_students["RollNumber"].astype(str)
)

student = filtered_students[
    filtered_students["RollNumber"].astype(str) == roll
].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# ----------------------
# LOAD ATTENDANCE
# ----------------------
if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE)
else:
    attendance = pd.DataFrame(columns=[
        "Date", "ClassID", "SubjectID", "SessionCode",
        "RollNumber", "StudentName", "EnrollmentNumber"
    ])

today = datetime.now().strftime("%Y-%m-%d")

# ----------------------
# CHECK IF ALREADY SUBMITTED (CSV-LEVEL LOCK)
# ----------------------
already_submitted = (
    (attendance["Date"] == today) &
    (attendance["ClassID"] == session["class_id"]) &
    (attendance["SubjectID"] == session["subject_id"]) &
    (attendance["SessionCode"] == session["session_code"]) &
    (attendance["RollNumber"].astype(str) == roll)
).any()

if already_submitted:
    st.success("✅ Attendance already submitted for this session.")
    st.stop()

# ----------------------
# SUBMIT BUTTON (HARD BLOCK)
# ----------------------
submit = st.button("✅ Submit Attendance")

if submit:
    # Reload CSV again (double safety)
    attendance = pd.read_csv(ATTENDANCE_FILE) if os.path.exists(ATTENDANCE_FILE) else attendance

    duplicate = (
        (attendance["Date"] == today) &
        (attendance["ClassID"] == session["class_id"]) &
        (attendance["SubjectID"] == session["subject_id"]) &
        (attendance["SessionCode"] == session["session_code"]) &
        (attendance["RollNumber"].astype(str) == roll)
    ).any()

    if duplicate:
        st.error("❌ Attendance already marked.")
        st.stop()

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
