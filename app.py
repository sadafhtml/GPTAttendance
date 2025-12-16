import streamlit as st
import pandas as pd
from datetime import datetime
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

# ---------------- FILE PATHS ----------------
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

# ---------------- SESSION CODE ----------------
entered_code = st.text_input("Enter Session Code")
if not entered_code:
    st.stop()

# ---------------- LOAD SESSIONS ----------------
if not os.path.exists(SESSIONS_FILE):
    st.error("No sessions available")
    st.stop()

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)

# Ensure proper types
sessions["CreatedAt"] = pd.to_datetime(sessions["CreatedAt"], errors="coerce")
sessions["ExpiryMinutes"] = sessions["ExpiryMinutes"].astype(int)

# Filter valid sessions
valid_sessions = sessions[
    (sessions["SessionCode"] == entered_code) &
    (sessions["Active"] == "True") &
    (datetime.now() <= sessions["CreatedAt"] + pd.to_timedelta(sessions["ExpiryMinutes"], unit='m'))
]

if valid_sessions.empty:
    st.error("⛔ Invalid or expired session code")
    st.stop()

session = valid_sessions.iloc[0]

# ---------------- LOAD STUDENTS ----------------
if not os.path.exists(STUDENTS_FILE):
    st.error("Students file missing")
    st.stop()

students = pd.read_excel(STUDENTS_FILE, dtype=str)

# Filter students by class
students = students[students["ClassID"] == session["ClassID"]]

if students.empty:
    st.warning("No students found for this class.")
    st.stop()

# ---------------- STUDENT SELECTION ----------------
roll = st.selectbox("Select Roll Number", students["RollNumber"])
student = students[students["RollNumber"] == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# ---------------- LOAD / INIT ATTENDANCE ----------------
required_cols = ["Date", "SessionID", "RollNumber", "StudentName", "EnrollmentNumber"]

if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE, dtype=str)
else:
    attendance = pd.DataFrame(columns=required_cols)

# Ensure columns exist
for col in required_cols:
    if col not in attendance.columns:
        attendance[col] = ""

attendance = attendance[required_cols]

today = datetime.now().strftime("%Y-%m-%d")

# ---------------- DUPLICATE CHECK ----------------
already = (
    (attendance["SessionID"] == session["SessionID"]) &
    (attendance["RollNumber"] == roll)
).any()

if already:
    st.success("✅ Attendance already submitted")
    st.stop()

# ---------------- SUBMIT ATTENDANCE ----------------
if st.button("✅ Submit Attendance"):

    new_row = {
        "Date": today,
        "SessionID": session["SessionID"],
        "RollNumber": roll,
        "StudentName": student["StudentName"],
        "EnrollmentNumber": student["EnrollmentNumber"]
    }

    attendance = pd.concat([attendance, pd.DataFrame([new_row])], ignore_index=True)
    attendance.to_csv(ATTENDANCE_FILE, index=False)

    st.success("🎉 Attendance marked successfully")
    st.stop()
