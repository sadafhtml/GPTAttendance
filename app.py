import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

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

sessions = pd.read_csv(SESSIONS_FILE)

now = datetime.now()
valid_sessions = []

for _, s in sessions.iterrows():
    created = datetime.fromisoformat(s["CreatedAt"])
    if (
        s["SessionCode"] == entered_code
        and s["Active"] == True
        and now <= created + timedelta(minutes=int(s["ExpiryMinutes"]))
    ):
        valid_sessions.append(s)

if not valid_sessions:
    st.error("⛔ Invalid or expired session code")
    st.stop()

session = valid_sessions[0]

# ---------------- LOAD STUDENTS ----------------
if not os.path.exists(STUDENTS_FILE):
    st.error("Students file missing")
    st.stop()

students = pd.read_excel(STUDENTS_FILE)
students = students[students["ClassID"] == session["ClassID"]]

roll = st.selectbox("Select Roll Number", students["RollNumber"].astype(str))
student = students[students["RollNumber"].astype(str) == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# ---------------- LOAD / INIT ATTENDANCE ----------------
required_cols = ["Date", "SessionID", "RollNumber"]

if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE)
else:
    attendance = pd.DataFrame(columns=required_cols)

# 🔒 FORCE COLUMNS (THIS LINE PREVENTS YOUR ERROR)
for col in required_cols:
    if col not in attendance.columns:
        attendance[col] = ""

attendance = attendance[required_cols]

today = datetime.now().strftime("%Y-%m-%d")

# ---------------- DUPLICATE CHECK ----------------
already = (
    (attendance["SessionID"] == session["SessionID"]) &
    (attendance["RollNumber"].astype(str) == roll)
).any()

if already:
    st.success("✅ Attendance already submitted")
    st.stop()

# ---------------- SUBMIT ----------------
if st.button("✅ Submit Attendance"):

    new_row = {
        "Date": today,
        "SessionID": session["SessionID"],
        "RollNumber": roll
    }

    attendance = pd.concat(
        [attendance, pd.DataFrame([new_row])],
        ignore_index=True
    )

    attendance.to_csv(ATTENDANCE_FILE, index=False)
    st.success("🎉 Attendance marked successfully")
    st.stop()
