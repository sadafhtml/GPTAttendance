import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

if "locked_session" not in st.session_state:
    st.session_state.locked_session = None

if "locked_roll" not in st.session_state:
    st.session_state.locked_roll = None

# If this browser has already submitted attendance for this session
if st.session_state.locked_session == session["SessionID"]:
    st.success(
        f"✅ Attendance already submitted for Roll No: {st.session_state.locked_roll}"
    )
    st.stop()

roll = st.selectbox(
    "Select Roll Number",
    students["RollNumber"].astype(str)
)

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

    # 🔐 LOCK THIS DEVICE FOR THIS SESSION
    st.session_state.locked_session = session["SessionID"]
    st.session_state.locked_roll = roll

    st.success("🎉 Attendance marked successfully")
    st.stop()



st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

# ---------------- FILE PATHS ----------------
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"

# ---------------- SESSION CODE INPUT ----------------
entered_code = st.text_input("Enter Session Code")
if not entered_code:
    st.stop()

# ---------------- LOAD SESSIONS ----------------
if not os.path.exists(SESSIONS_FILE):
    st.error("⛔ No sessions available. Contact your teacher.")
    st.stop()

sessions = pd.read_csv(SESSIONS_FILE, dtype=str)
sessions["Active"] = sessions["Active"].astype(str)
sessions["ExpiryMinutes"] = sessions["ExpiryMinutes"].astype(int)

now = datetime.now()
valid_sessions = []
for _, s in sessions.iterrows():
    try:
        created = datetime.fromisoformat(s["CreatedAt"])
    except:
        continue
    if (
        s["SessionCode"].strip() == entered_code.strip()
        and s["Active"].lower()=="true"
        and now <= created + timedelta(minutes=int(s["ExpiryMinutes"]))
    ):
        valid_sessions.append(s)

if not valid_sessions:
    st.error("⛔ Invalid or expired session code")
    st.stop()

session = valid_sessions[0]

# ---------------- LOAD STUDENTS ----------------
students = pd.read_excel(STUDENTS_FILE)
students = students[students["ClassID"].astype(str)==str(session["ClassID"])]
if students.empty:
    st.error("No students found for this class")
    st.stop()

# ---------------- STUDENT SELECTION ----------------
roll = st.selectbox("Select Roll Number", students["RollNumber"].astype(str))
student = students[students["RollNumber"].astype(str)==str(roll)].iloc[0]
st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# ---------------- LOAD / INIT ATTENDANCE ----------------
required_cols = ["Date","SessionID","RollNumber"]
if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE,dtype=str)
else:
    attendance = pd.DataFrame(columns=required_cols)
for col in required_cols:
    if col not in attendance.columns:
        attendance[col] = ""
attendance = attendance[required_cols]

today = datetime.now().strftime("%Y-%m-%d")

# ---------------- DUPLICATE CHECK ----------------
already = ((attendance["SessionID"].astype(str)==str(session["SessionID"])) & (attendance["RollNumber"].astype(str)==str(roll))).any()
if already:
    st.success("✅ Attendance already submitted")
    st.stop()

# ---------------- SUBMIT ----------------
if st.button("✅ Submit Attendance"):
    new_row = {"Date":today,"SessionID":session["SessionID"],"RollNumber":roll}
    attendance = pd.concat([attendance,pd.DataFrame([new_row])],ignore_index=True)
    attendance.to_csv(ATTENDANCE_FILE,index=False)
    st.success("🎉 Attendance marked successfully")
    st.stop()
