import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os

# =====================================================
# PAGE CONFIG
# =====================================================
st.set_page_config(page_title="Student Attendance", layout="centered")
st.title("🧑‍🎓 Student Attendance")

# =====================================================
# MOBILE-ONLY CHECK
# =====================================================
def is_mobile_browser():
    try:
        ua = st.context.headers.get("user-agent", "").lower()
        mobile_keywords = ["android", "iphone", "ipad", "ipod", "mobile"]
        return any(k in ua for k in mobile_keywords)
    except:
        return False

if not is_mobile_browser():
    st.error("📵 Attendance can only be marked from a mobile phone.")
    st.info("Please open this link on your Android or iPhone.")
    st.stop()

# =====================================================
# FILE PATHS
# =====================================================
SESSIONS_FILE = "sessions.csv"
ATTENDANCE_FILE = "attendance.csv"
STUDENTS_FILE = "Students.xlsx"
PHOTO_DIR = "attendance_photos"

os.makedirs(PHOTO_DIR, exist_ok=True)

# =====================================================
# SESSION STATE LOCK (DEVICE LEVEL)
# =====================================================
if "locked_session" not in st.session_state:
    st.session_state.locked_session = None

if "locked_roll" not in st.session_state:
    st.session_state.locked_roll = None

# =====================================================
# SESSION CODE INPUT
# =====================================================
entered_code = st.text_input("🔑 Enter Session Code")

if not entered_code:
    st.stop()

# =====================================================
# LOAD SESSIONS
# =====================================================
if not os.path.exists(SESSIONS_FILE):
    st.error("⛔ No sessions available.")
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
        and s["Active"].lower() == "true"
        and now <= created + timedelta(minutes=int(s["ExpiryMinutes"]))
    ):
        valid_sessions.append(s)

if not valid_sessions:
    st.error("⛔ Invalid or expired session code")
    st.stop()

session = valid_sessions[0]

# =====================================================
# DEVICE LOCK CHECK
# =====================================================
if st.session_state.locked_session == session["SessionID"]:
    st.success(
        f"✅ Attendance already submitted for Roll No: {st.session_state.locked_roll}"
    )
    st.stop()

# =====================================================
# LOAD STUDENTS
# =====================================================
if not os.path.exists(STUDENTS_FILE):
    st.error("Students file missing")
    st.stop()

students = pd.read_excel(STUDENTS_FILE)
students = students[students["ClassID"].astype(str) == str(session["ClassID"])]

if students.empty:
    st.error("No students found for this class")
    st.stop()

# =====================================================
# STUDENT SELECTION
# =====================================================
roll = st.selectbox(
    "Select Roll Number",
    students["RollNumber"].astype(str)
)

student = students[students["RollNumber"].astype(str) == roll].iloc[0]

st.text_input("Student Name", student["StudentName"], disabled=True)
st.text_input("Enrollment Number", student["EnrollmentNumber"], disabled=True)

# =====================================================
# CAMERA CAPTURE (MANDATORY)
# =====================================================
st.subheader("📸 Capture Live Photo")
photo = st.camera_input("Take a clear selfie")

if photo is None:
    st.warning("📷 Photo is mandatory to mark attendance.")
    st.stop()

# =====================================================
# LOAD / INIT ATTENDANCE
# =====================================================
required_cols = ["Date", "SessionID", "RollNumber", "PhotoFile"]

if os.path.exists(ATTENDANCE_FILE):
    attendance = pd.read_csv(ATTENDANCE_FILE, dtype=str)
else:
    attendance = pd.DataFrame(columns=required_cols)

for col in required_cols:
    if col not in attendance.columns:
        attendance[col] = ""

attendance = attendance[required_cols]

today = datetime.now().strftime("%Y-%m-%d")

# =====================================================
# DUPLICATE CHECK (SESSION + ROLL)
# =====================================================
already = (
    (attendance["SessionID"].astype(str) == str(session["SessionID"])) &
    (attendance["RollNumber"].astype(str) == roll)
).any()

if already:
    st.success("✅ Attendance already submitted")
    st.stop()

# =====================================================
# SUBMIT ATTENDANCE
# =====================================================
if st.button("✅ Submit Attendance"):

    # Save photo
    photo_filename = (
        f"{session['SessionID']}_{roll}_{datetime.now().strftime('%H%M%S')}.jpg"
    )
    photo_path = os.path.join(PHOTO_DIR, photo_filename)

    with open(photo_path, "wb") as f:
        f.write(photo.getbuffer())

    new_row = {
        "Date": today,
        "SessionID": session["SessionID"],
        "RollNumber": roll,
        "PhotoFile": photo_filename
    }

    attendance = pd.concat(
        [attendance, pd.DataFrame([new_row])],
        ignore_index=True
    )

    attendance.to_csv(ATTENDANCE_FILE, index=False)

    # 🔒 LOCK THIS DEVICE FOR THIS SESSION
    st.session_state.locked_session = session["SessionID"]
    st.session_state.locked_roll = roll

    st.success("🎉 Attendance marked successfully")
    st.info("You cannot mark attendance for another roll from this device.")
    st.stop()
