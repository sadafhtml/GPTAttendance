import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

# =========================
# LOAD SESSION
# =========================
if not os.path.exists("session.json"):
    st.error("⛔ No active session")
    st.stop()

with open("session.json", "r") as f:
    session = json.load(f)

SESSION_VALIDITY = 30  # minutes
created_time = datetime.fromisoformat(session["created_at"])

if datetime.now() > created_time + timedelta(minutes=SESSION_VALIDITY):
    st.error("⛔ Session expired")
    st.stop()

# =========================
# VALIDATE SESSION CODE
# =========================
entered_code = st.text_input("Enter Session Code")

if entered_code != session["session_code"]:
    st.warning("❗ Invalid session code")
    st.stop()

# =========================
# LOAD STUDENTS
# =========================
students = pd.read_excel("students.xlsx")

# OPTIONAL: if later you add ClassID column
# students = students[students["ClassID"] == session["class_id"]]

roll = st.selectbox("Select Roll Number", students["RollNumber"])

student = students[students["RollNumber"] == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# =========================
# LOAD ATTENDANCE
# =========================
if os.path.exists("attendance.csv"):
    attendance = pd.read_csv("attendance.csv")
else:
    attendance = pd.DataFrame(
        columns=["Date","ClassID","SubjectID","SessionCode","RollNumber","StudentName","EnrollmentNumber"]
    )

today = datetime.now().strftime("%Y-%m-%d")

duplicate = (
    (attendance["Date"] == today) &
    (attendance["ClassID"] == session["class_id"]) &
    (attendance["SubjectID"] == session["subject_id"]) &
    (attendance["SessionCode"] == session["session_code"]) &
    (attendance["RollNumber"] == roll)
).any()

if duplicate:
    st.error("❌ Attendance already marked")
    st.stop()

# =========================
# SUBMIT ATTENDANCE
# =========================
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

    attendance = pd.concat([attendance, pd.DataFrame([new_row])])
    attendance.to_csv("attendance.csv", index=False)

    st.success("🎉 Attendance marked successfully")
