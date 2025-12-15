import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os
import portalocker

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

SESSION_FILE = "session.json"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"
SESSION_VALIDITY = 30  # minutes

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
# SUBMIT (ATOMIC + LOCKED)
# ----------------------
if st.button("✅ Submit Attendance"):

    attendance_key = f"{today}_{session['class_id']}_{session['subject_id']}_{session['session_code']}_{roll}"

    # Ensure file exists with correct schema
    if not os.path.exists(ATTENDANCE_FILE):
        pd.DataFrame(columns=[
            "AttendanceKey","Date","ClassID","SubjectID",
            "SessionCode","RollNumber","StudentName","EnrollmentNumber"
        ]).to_csv(ATTENDANCE_FILE, index=False)

    # 🔒 HARD FILE LOCK
    with portalocker.Lock(ATTENDANCE_FILE, timeout=10):

        attendance = pd.read_csv(ATTENDANCE_FILE)

        if attendance_key in attendance["AttendanceKey"].values:
            st.success("✅ Attendance already submitted.")
            st.stop()

        new_row = {
            "AttendanceKey": attendance_key,
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
