import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import json
import os

st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

# ----------------------
# LOAD ACTIVE SESSION
# ----------------------
SESSION_FILE = "session.json"
CLASSES_FILE = os.path.join(os.getcwd(), "classes.csv")
SUBJECTS_FILE = os.path.join(os.getcwd(), "subjects.csv")
ATTENDANCE_FILE = os.path.join(os.getcwd(), "attendance.csv")
STUDENTS_FILE = os.path.join(os.getcwd(), "Students.xlsx")
SESSION_VALIDITY = 30  # minutes

if not os.path.exists(SESSION_FILE):
    st.error("⛔ No active session. Please contact your teacher.")
    st.stop()

with open(SESSION_FILE, "r") as f:
    session = json.load(f)

created_time = datetime.fromisoformat(session["created_at"])
if datetime.now() > created_time + timedelta(minutes=SESSION_VALIDITY):
    st.error("⛔ Session expired")
    st.stop()

# ----------------------
# SESSION CODE VALIDATION
# ----------------------
entered_code = st.text_input("Enter Session Code")
if entered_code != session["session_code"]:
    st.warning("❗ Invalid session code")
    st.stop()

# ----------------------
# LOAD STUDENTS
# ----------------------
if not os.path.exists(STUDENTS_FILE):
    st.error("❌ Students file not found. Contact Admin.")
    st.stop()

students = pd.read_excel(STUDENTS_FILE)

# Filter students by class of the active session
class_id = session["class_id"]
filtered_students = students[students["ClassID"] == class_id]

if filtered_students.empty:
    st.warning("No students found for this class.")
    st.stop()

# ----------------------
# STUDENT SELECTION
# ----------------------
roll = st.selectbox("Select Your Roll Number", filtered_students["RollNumber"])
student = filtered_students[filtered_students["RollNumber"] == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# ----------------------
# LOAD ATTENDANCE
# ----------------------
if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE)
else:
    attendance = pd.DataFrame(columns=[
        "Date","ClassID","SubjectID","SessionCode",
        "RollNumber","StudentName","EnrollmentNumber"
    ])

today = datetime.now().strftime("%Y-%m-%d")

# --- Initialize session_state flag ---
if "submitted" not in st.session_state:
    st.session_state.submitted = False

# --- On submit button ---
if st.button("✅ Submit Attendance") and not st.session_state.submitted:

    # Re-load attendance to prevent duplicates if file changed
    if os.path.exists(ATTENDANCE_FILE):
        attendance = pd.read_csv(ATTENDANCE_FILE)

    # Check for duplicate just before writing
    duplicate = (
        (attendance["Date"] == today) &
        (attendance["ClassID"] == session["class_id"]) &
        (attendance["SubjectID"] == session["subject_id"]) &
        (attendance["SessionCode"] == session["session_code"]) &
        (attendance["RollNumber"] == roll)
    ).any()

    if duplicate:
        st.error("❌ Attendance already marked for this session")
        st.session_state.submitted = True  # mark as submitted
    else:
        new_row = {
            "Date": today,
            "ClassID": session["class_id"],
            "SubjectID": session["subject_id"],
            "SessionCode": session["session_code"],
            "RollNumber": roll,
            "StudentName": student["StudentName"],
            "EnrollmentNumber": student["EnrollmentNumber"]
        }

        # Append row and save
        attendance = pd.concat([attendance, pd.DataFrame([new_row])])
        attendance.to_csv(ATTENDANCE_FILE, index=False)
        st.success("🎉 Attendance marked successfully")
        st.session_state.submitted = True  # mark as submitted

# --- Disable button after submission ---
if st.session_state.submitted:
    st.warning("✅ You have already submitted attendance for this session")
