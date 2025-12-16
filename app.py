import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

# ---------- Load session code ----------
entered_code = st.text_input("Enter Session Code")

if not entered_code:
    st.stop()

if not os.path.exists(SESSIONS_FILE):
    st.error("No active sessions.")
    st.stop()

sessions = pd.read_csv(SESSIONS_FILE)

# ---------- Validate session ----------
now = datetime.now()

valid_sessions = []
for _, s in sessions.iterrows():
    created = datetime.fromisoformat(s["CreatedAt"])
    if (
        s["SessionCode"] == entered_code and
        s["Active"] and
        now <= created + timedelta(minutes=int(s["ExpiryMinutes"]))
    ):
        valid_sessions.append(s)

if not valid_sessions:
    st.error("⛔ Invalid or expired session code")
    st.stop()

session = valid_sessions[0]

# ---------- Load students ----------
students = pd.read_excel(STUDENTS_FILE)
students = students[students["ClassID"] == session["ClassID"]]

roll = st.selectbox("Select Roll Number", students["RollNumber"].astype(str))
student = students[students["RollNumber"].astype(str) == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment", student["EnrollmentNumber"], disabled=True)

# ---------- Attendance ----------
today = datetime.now().strftime("%Y-%m-%d")

if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE)
else:
    attendance = pd.DataFrame(columns=[
        "Date","SessionID","RollNumber"
    ])

already = (
    (attendance["SessionID"] == session["SessionID"]) &
    (attendance["RollNumber"].astype(str) == roll)
).any()

if already:
    st.success("✅ Attendance already submitted")
    st.stop()

if st.button("✅ Submit Attendance"):

    attendance = pd.concat([
        attendance,
        pd.DataFrame([{
            "Date": today,
            "SessionID": session["SessionID"],
            "RollNumber": roll
        }])
    ])

    attendance.to_csv(ATTENDANCE_FILE, index=False)
    st.success("🎉 Attendance marked")
    st.stop()
